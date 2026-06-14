"""
CardioRisk Periop - Risk Calculation Engine
============================================
Perioperative cardiovascular risk assessment based on:
  - Diretriz Brasileira de Avaliação Cardiovascular Perioperatória
  - RCRI (Lee Index) for non-vascular surgery
  - VSG Cardiac Risk Index for vascular surgery
"""

from enum import Enum


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class RiscoCirurgia(str, Enum):
    BAIXO = "baixo"
    INTERMEDIARIO = "intermediario"
    ALTO = "alto"


class ClasseRisco(str, Enum):
    BAIXO = "baixo"
    INTERMEDIARIO = "intermediario"
    ALTO = "alto"


class TipoRecomendacao(str, Enum):
    VERDE = "verde"
    AMARELO = "amarelo"
    VERMELHO = "vermelho"


# ---------------------------------------------------------------------------
# RCRI Risk Table (Duceppe et al, CMAJ 2017 / Diretriz SBC)
# ---------------------------------------------------------------------------

def _obter_classe_risco_rcri(pontuacao: int) -> tuple[str, str]:
    if pontuacao >= 3:
        return ClasseRisco.ALTO, "Risco Alto"
    elif pontuacao == 2:
        return ClasseRisco.INTERMEDIARIO, "Risco Intermediário"
    else:
        return ClasseRisco.BAIXO, "Risco Baixo"

# ---------------------------------------------------------------------------
# VSG Cardiac Risk Index Table (Diretriz SBC 2024)
# ---------------------------------------------------------------------------

def _obter_classe_risco_vsg(pontuacao: int) -> tuple[str, str]:
    if pontuacao >= 7:
        return ClasseRisco.ALTO, "Risco Alto"
    elif pontuacao >= 5:
        return ClasseRisco.INTERMEDIARIO, "Risco Intermediário"
    else:
        return ClasseRisco.BAIXO, "Risco Baixo"


# ---------------------------------------------------------------------------
# METs Labels (pt-BR)
# ---------------------------------------------------------------------------

METS_LABELS: dict[float, str] = {
    1:    "Nenhuma atividade / acamado",
    2.7:  "Trabalhos leves em casa (juntar lixo, lavar louça)",
    2.75: "Cuidar de si mesmo / caminhar uma quadra no plano",
    3.5:  "Trabalhos moderados em casa (aspirador, varrer, carregar mantimentos)",
    4.5:  "Trabalhos no jardim/quintal (rastelo, cortar grama)",
    5.25: "Atividade sexual",
    5.5:  "Subir um lance de escadas ou caminhar em subida",
    6:    "Atividades recreacionais moderadas (boliche, dança, tênis em dupla)",
    7.5:  "Esportes (natação, tênis individual, futebol)",
    8:    "Trabalhos pesados em casa / correr distância curta",
}

ROTULOS_CIRURGIA: dict[str, str] = {
    "baixo":        "Baixo Risco",
    "intermediario": "Risco Intermediário",
    "alto":         "Alto Risco",
}


# ---------------------------------------------------------------------------
# RCRI Scoring
# ---------------------------------------------------------------------------

def pontuar_rcri(data: dict) -> tuple[int, list[str]]:
    criterios: list[tuple[bool, str]] = [
        (data.get("rcri_cirurgia_alto_risco", False),
         "Operação intraperitoneal, intratorácica ou vascular suprainguinal"),
        (data.get("rcri_doenca_coronaria", False),
         "Doença arterial coronária (ondas Q, sintomas de isquemia, teste+, uso de nitrato)"),
        (data.get("rcri_ic", False),
         "Insuficiência cardíaca congestiva (clínica, RX tórax com congestão)"),
        (data.get("rcri_cerebrovascular", False),
         "Doença cerebrovascular"),
        (data.get("rcri_diabetes_insulina", False),
         "Diabetes com insulinoterapia"),
        (data.get("rcri_creatinina_acima_2", False),
         "Creatinina pré-operatória > 2,0 mg/dL"),
    ]
    atingidos = [rotulo for ativo, rotulo in criterios if ativo]
    return len(atingidos), atingidos


# ---------------------------------------------------------------------------
# VSG Scoring
# ---------------------------------------------------------------------------

def pontuar_vsg(data: dict) -> tuple[int, list[str]]:
    """VSG-CRI scoring per Tabela 6 — variable points per criterion."""
    total = 0
    atingidos: list[str] = []

    # Faixa etária (pontos variáveis)
    faixa_etaria = data.get("vsg_faixa_etaria", "")
    if faixa_etaria == "gte80":
        total += 4; atingidos.append("Idade ≥ 80 anos (+4)")
    elif faixa_etaria == "70_79":
        total += 3; atingidos.append("Idade 70–79 anos (+3)")
    elif faixa_etaria == "60_69":
        total += 2; atingidos.append("Idade 60–69 anos (+2)")

    # Critérios de 2 pontos
    dois_pt: list[tuple[bool, str]] = [
        (data.get("vsg_dac", False),                "Doença arterial coronariana (+2)"),
        (data.get("vsg_ic", False),                 "Insuficiência cardíaca (+2)"),
        (data.get("vsg_dpoc", False),               "DPOC (+2)"),
        (data.get("vsg_creatinina_acima_1_8", False),"Creatinina > 1,8 mg/dL (+2)"),
    ]
    for ativo, rotulo in dois_pt:
        if ativo:
            total += 2; atingidos.append(rotulo)

    # Critérios de 1 ponto
    um_pt: list[tuple[bool, str]] = [
        (data.get("vsg_tabagismo", False),             "Tabagismo (+1)"),
        (data.get("vsg_diabetes_insulina", False),     "Diabetes com insulina (+1)"),
        (data.get("vsg_betabloqueador_cronico", False),"Uso crônico de betabloqueador (+1)"),
    ]
    for ativo, rotulo in um_pt:
        if ativo:
            total += 1; atingidos.append(rotulo)

    # Critério de -1 ponto
    if data.get("vsg_revasc_previa", False):
        total -= 1; atingidos.append("Revascularização miocárdica prévia (−1)")

    return max(total, 0), atingidos


# ---------------------------------------------------------------------------
# Active Cardiovascular Conditions (Tabela 2)
# ---------------------------------------------------------------------------

def verificar_condicoes_ativas(data: dict) -> list[str]:
    condicoes: list[tuple[bool, str]] = [
        (data.get("cv_coronaria_aguda", False),
         "Síndrome coronariana aguda"),
        (data.get("cv_aorta_instavel", False),
         "Doenças instáveis da aorta torácica"),
        (data.get("cv_edema_pulmonar_agudo", False),
         "Edema agudo dos pulmões"),
        (data.get("cv_choque_cardiogenico", False),
         "Choque cardiogênico"),
        (data.get("cv_ic_nyha_3_4", False),
         "Insuficiência cardíaca classe funcional III/IV (NYHA)"),
        (data.get("cv_angina_ccs_3_4", False),
         "Angina classe funcional CCS III/IV"),
        (data.get("cv_arritmia_grave", False),
         "Bradiarritmias ou taquiarritmias graves (BAVT, TV)"),
        (data.get("cv_has_nao_controlada", False),
         "HAS não controlada (PA > 180 x 110 mmHg)"),
        (data.get("cv_fa_alta_resposta", False),
         "Fibrilação atrial de alta resposta ventricular (FC > 120 bpm)"),
        (data.get("cv_hap_sintomatica", False),
         "Hipertensão arterial pulmonar sintomática"),
        (data.get("cv_valvopatia_grave", False),
         "Estenose aórtica/mitral importante sintomática"),
    ]
    return [rotulo for ativo, rotulo in condicoes if ativo]


# ---------------------------------------------------------------------------
# Medication Advice
# ---------------------------------------------------------------------------

def _determinar_ponte_varfarina(data: dict) -> dict:
    indicacao = data.get("indicacao_varfarina", "")

    if indicacao == "mechanical_valve":
        return {
            "acao": "Suspender + Ponte com heparina",
            "detalhe": "Prótese valvar mecânica: realizar ponte com heparina de baixo peso molecular.",
            "tipo": TipoRecomendacao.VERMELHO,
        }

    if indicacao == "rheumatic":
        return {
            "acao": "Suspender + Ponte com heparina",
            "detalhe": "Doença valvar reumática: realizar ponte com heparina de baixo peso molecular.",
            "tipo": TipoRecomendacao.VERMELHO,
        }

    if indicacao == "af":
        chadsvasc = data.get("chadsvasc_varfarina") or 0
        avc_3m = data.get("avc_3m_varfarina", False)

        if chadsvasc >= 5 or avc_3m:
            extra = " e AVC/AIT < 3 meses" if avc_3m else ""
            return {
                "acao": "Suspender + Ponte com heparina",
                "detalhe": f"FA com CHA₂DS₂-VASc {chadsvasc}{extra}: realizar ponte com heparina.",
                "tipo": TipoRecomendacao.VERMELHO,
            }
        elif chadsvasc >= 3:
            return {
                "acao": "Considerar ponte com heparina",
                "detalhe": f"FA com CHA₂DS₂-VASc {chadsvasc}: considerar ponte com heparina.",
                "tipo": TipoRecomendacao.AMARELO,
            }
        else:
            return {
                "acao": "Suspender sem ponte",
                "detalhe": f"FA com CHA₂DS₂-VASc {chadsvasc} sem AVC/AIT recente: não realizar ponte.",
                "tipo": TipoRecomendacao.VERDE,
            }

    if indicacao == "vte":
        tempo = data.get("tempo_tev_varfarina", "")
        trombofilia = data.get("trombofilia_varfarina", "")
        neoplasia = data.get("neoplasia_ativa_varfarina", False)

        if tempo == "recent":
            return {
                "acao": "Suspender + Ponte com heparina",
                "detalhe": "TEV recente: realizar ponte com heparina.",
                "tipo": TipoRecomendacao.VERMELHO,
            }
        elif tempo == "3_12m":
            partes = []
            if trombofilia == "mild":
                partes.append("trombofilia leve")
            if neoplasia:
                partes.append("neoplasia ativa")
            extra = f" com {' e '.join(partes)}" if partes else ""
            return {
                "acao": "Considerar ponte com heparina",
                "detalhe": f"TEV 3–12 meses{extra}: considerar ponte com heparina.",
                "tipo": TipoRecomendacao.AMARELO,
            }
        else:
            return {
                "acao": "Suspender sem ponte",
                "detalhe": "TEV > 12 meses: não realizar ponte com heparina.",
                "tipo": TipoRecomendacao.VERDE,
            }

    return {
        "acao": "Avaliar individualmente",
        "detalhe": "Varfarina: suspender 5 dias antes. Avaliar necessidade de ponte com heparina.",
        "tipo": TipoRecomendacao.AMARELO,
    }


def montar_orientacoes_medicacao(data: dict) -> list[dict]:
    orientacoes: list[dict] = []
    tipo_cirurgia = data.get("tipo_cirurgia", "")

    # AAS
    if data.get("usa_aas"):
        prevencao = data.get("prevencao_aas", "")
        if prevencao == "primary":
            orientacoes.append({
                "medicamento": "AAS",
                "acao": "Suspender 7 dias antes",
                "detalhe": "Prevenção primária: suspender AAS 7 dias antes do procedimento.",
                "tipo": TipoRecomendacao.AMARELO,
            })
        elif prevencao == "secondary":
            alto_sangramento = tipo_cirurgia in ("neurologic", "urologic_minor", "eye")
            if alto_sangramento:
                orientacoes.append({
                    "medicamento": "AAS",
                    "acao": "Suspender 7 dias antes",
                    "detalhe": "Prevenção secundária: suspender por neurocirurgia, RTU de próstata ou cirurgia de retina.",
                    "tipo": TipoRecomendacao.VERMELHO,
                })
            else:
                orientacoes.append({
                    "medicamento": "AAS",
                    "acao": "Manter",
                    "detalhe": "Prevenção secundária: manter AAS (exceto neurocirurgia, RTU de próstata ou cirurgia de retina).",
                    "tipo": TipoRecomendacao.VERDE,
                })

    # Clopidogrel
    if data.get("usa_clopidogrel"):
        orientacoes.append({
            "medicamento": "Clopidogrel",
            "acao": "Suspender 5 dias antes",
            "detalhe": "Suspender 5 dias antes. Manter apenas se monoterapia em procedimentos de baixo risco de sangramento.",
            "tipo": TipoRecomendacao.AMARELO,
        })

    # Ticagrelor
    if data.get("usa_ticagrelor"):
        orientacoes.append({
            "medicamento": "Ticagrelor",
            "acao": "Suspender 5 dias antes",
            "detalhe": "Suspender ticagrelor 5 dias antes do procedimento.",
            "tipo": TipoRecomendacao.AMARELO,
        })

    # Prasugrel
    if data.get("usa_prasugrel"):
        orientacoes.append({
            "medicamento": "Prasugrel",
            "acao": "Suspender 7 dias antes",
            "detalhe": "Suspender prasugrel 7 dias antes do procedimento.",
            "tipo": TipoRecomendacao.AMARELO,
        })

    # DOACs: Rivaroxabana / Apixabana
    if data.get("uses_rivaroxaban") or data.get("uses_apixaban"):
        nome_med = "Rivaroxabana" if data.get("uses_rivaroxaban") else "Apixabana"
        orientacoes.append({
            "medicamento": nome_med,
            "acao": "Suspender 24-48h antes",
            "detalhe": (
                f"{nome_med}: suspender 24–48 horas antes do procedimento. "
                "Retornar no 1º ou 2º dia pós-operatório conforme risco de sangramento e hemostasia garantida."
            ),
            "tipo": TipoRecomendacao.AMARELO,
        })

    # Dabigatrana
    if data.get("uses_dabigatran"):
        clcr = data.get("clcr")
        alto_sangramento = data.get("high_bleeding_risk", False)
        if isinstance(clcr, (int, float)) and clcr < 50 and alto_sangramento:
            orientacoes.append({
                "medicamento": "Dabigatrana",
                "acao": "Suspender 4 dias antes",
                "detalhe": (
                    "Dabigatrana com ClCr < 50 e alto risco de sangramento: suspender 4 dias antes. "
                    "Retornar no 2º dia pós-operatório se hemostasia garantida."
                ),
                "tipo": TipoRecomendacao.AMARELO,
            })
        else:
            orientacoes.append({
                "medicamento": "Dabigatrana",
                "acao": "Suspender 24-48h antes",
                "detalhe": (
                    "Dabigatrana (ClCr >= 50 ou sem risco aumentado): suspender 24–48 horas antes. "
                    "Retornar no 1º ou 2º dia pós-operatório conforme risco de sangramento e hemostasia garantida."
                ),
                "tipo": TipoRecomendacao.AMARELO,
            })

    # Varfarina
    if data.get("usa_varfarina"):
        ponte = _determinar_ponte_varfarina(data)
        orientacoes.append({
            "medicamento": "Varfarina",
            "acao": ponte["acao"],
            "detalhe": ponte["detalhe"],
            "tipo": ponte["tipo"],
        })

    return orientacoes


# ---------------------------------------------------------------------------
# Recommended Exams
# ---------------------------------------------------------------------------

def montar_recomendacoes_exames(
    data: dict,
    classe_risco: str,
    pontuacao: int,
    tem_condicoes_ativas: bool,
) -> list[str]:
    exames: list[str] = []
    risco_cirurgia = data.get("risco_cirurgia", "")
    mets = data.get("mets", 4)

    if risco_cirurgia != "baixo" or pontuacao > 0:
        exames.append("ECG de 12 derivações")

    necessita_eco_historico = (data.get("ic_conhecida") or data.get("doenca_valvar_conhecida")) and \
                              (not data.get("eco_recente") or data.get("piora_sintomas"))

    if necessita_eco_historico or tem_condicoes_ativas:
        if "Ecocardiograma transtorácico" not in exames:
            exames.append("Ecocardiograma transtorácico")

    eh_vascular = data.get("eh_vascular", False)
    pontuacao_intermediaria = pontuacao >= 5 if eh_vascular else pontuacao >= 2
    if mets < 4 and risco_cirurgia in ("intermediario", "alto") and pontuacao_intermediaria:
        exames.append("Teste funcional (ergometria / cintilografia / eco de estresse)")

    if risco_cirurgia in ("intermediario", "alto"):
        exames.append("Hemograma completo")

    if data.get("usa_varfarina"):
        exames.append("Coagulograma (INR, TAP, TTPa)")

    if pontuacao > 0 or risco_cirurgia == "alto":
        exames.append("Função renal (creatinina, ureia)")

    if classe_risco == ClasseRisco.ALTO or data.get("ic_conhecida"):
        exames.append("BNP ou NT-proBNP")

    if data.get("rcri_diabetes_insulina") or data.get("vsg_diabetes_insulina"):
        exames.append("Glicemia de jejum / HbA1c")

    return exames


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def montar_recomendacoes(
    classe_risco: str,
    pontuacao: int,
    mets: int,
    risco_cirurgia: str,
    tem_condicoes_ativas: bool,
    condicoes_ativas: list[str],
    eh_vascular: bool,
    data: dict,
) -> list[dict]:
    recomendacoes: list[dict] = []

    # Condições ativas têm prioridade
    if tem_condicoes_ativas:
        recomendacoes.append({
            "tipo": TipoRecomendacao.VERMELHO,
            "icone": "🚨",
            "titulo": "Condições cardíacas ativas detectadas",
            "corpo": (
                "Foram identificadas condições cardíacas ativas que requerem "
                "avaliação e tratamento antes do procedimento cirúrgico: "
                + ", ".join(condicoes_ativas) + "."
            ),
        })

    # Atalho para cirurgia de baixo risco
    if risco_cirurgia == RiscoCirurgia.BAIXO and not tem_condicoes_ativas:
        recomendacoes.append({
            "tipo": TipoRecomendacao.VERDE,
            "icone": "✅",
            "titulo": "Cirurgia de baixo risco",
            "corpo": (
                "Risco cardíaco estimado < 1%. Prosseguir com a cirurgia. "
                "Monitorização padrão perioperatória é suficiente."
            ),
        })
        return recomendacoes

    # Recomendação baseada em risco
    if classe_risco == ClasseRisco.BAIXO:
        recomendacoes.append({
            "tipo": TipoRecomendacao.VERDE,
            "icone": "✅",
            "titulo": "Prosseguir com cirurgia",
            "corpo": "Risco cardíaco perioperatório baixo. Monitorização padrão é suficiente.",
        })
    elif classe_risco == ClasseRisco.INTERMEDIARIO:
        recomendacoes.append({
            "tipo": TipoRecomendacao.AMARELO,
            "icone": "⚠️",
            "titulo": "Considerar avaliação adicional",
            "corpo": (
                "Risco intermediário. Avalie benefício de consulta cardiológica. "
                "Solicite ECG pré-operatório e considere dosagem de BNP."
            ),
        })
    else:
        recomendacoes.append({
            "tipo": TipoRecomendacao.VERMELHO,
            "icone": "🚨",
            "titulo": "Avaliação cardiológica indicada",
            "corpo": (
                "Risco elevado. Recomenda-se avaliação cardiológica formal. "
                "Discuta relação risco/benefício com equipe cirúrgica e paciente."
            ),
        })

    # Capacidade funcional
    if mets < 4:
        recomendacoes.append({
            "tipo": TipoRecomendacao.AMARELO,
            "icone": "🏃",
            "titulo": "Capacidade funcional reduzida",
            "corpo": (
                "METs < 4 é preditor independente de eventos. "
                "Considere teste funcional antes de cirurgia eletiva."
            ),
        })

    # Monitorização avançada para risco alto/intermediário
    if classe_risco in (ClasseRisco.ALTO, ClasseRisco.INTERMEDIARIO):
        recomendacoes.append({
            "tipo": TipoRecomendacao.VERMELHO if classe_risco == ClasseRisco.ALTO else TipoRecomendacao.AMARELO,
            "icone": "🏥",
            "titulo": "Monitorização avançada",
            "corpo": "Considere monitorização invasiva e cuidados intensivos (CTI) pós-operatórios."
        })

    # Cirurgia de alto risco
    if risco_cirurgia == RiscoCirurgia.ALTO:
        recomendacoes.append({
            "tipo": TipoRecomendacao.VERMELHO,
            "icone": "🔪",
            "titulo": "Cirurgia de alto risco",
            "corpo": "Procedimento com risco cardíaco intrínseco > 5%.",
        })

    # Otimização para pontuação alta
    if pontuacao >= 3:
        recomendacoes.append({
            "tipo": TipoRecomendacao.VERMELHO,
            "icone": "💊",
            "titulo": "Otimização farmacológica",
            "corpo": (
                "Score >= 3: considere betabloqueadores e estatinas conforme indicação. "
                "Avalie profilaxia antitrombótica."
            ),
        })

    # Comorbidades específicas
    if data.get("ic_conhecida"):
        recomendacoes.append({
            "tipo": TipoRecomendacao.AMARELO,
            "icone": "🫀",
            "titulo": "IC conhecida / suspeita",
            "corpo": "Avaliação ecocardiográfica recomendada. Otimize tratamento da IC antes do procedimento.",
        })

    if data.get("doenca_valvar_conhecida"):
        recomendacoes.append({
            "tipo": TipoRecomendacao.AMARELO,
            "icone": "🫀",
            "titulo": "Doença valvar conhecida / suspeita",
            "corpo": "Solicite ecocardiograma para avaliação da gravidade valvar.",
        })

    if data.get("dac_conhecida"):
        recomendacoes.append({
            "tipo": TipoRecomendacao.AMARELO,
            "icone": "❤️",
            "titulo": "DAC conhecida / suspeita",
            "corpo": "Avalie controle da doença coronariana. Considere teste funcional se indicado.",
        })

    return recomendacoes


# ---------------------------------------------------------------------------
# Risk Factor Tags
# ---------------------------------------------------------------------------

def montar_fatores_risco(data: dict, criterios_atingidos: list[str], mets: int) -> list[str]:
    fatores = list(criterios_atingidos)
    if mets < 4:
        fatores.append("Capacidade funcional reduzida")
    if data.get("obesidade"):
        fatores.append("Obesidade")
    if data.get("ic_conhecida"):
        fatores.append("IC conhecida/suspeita")
    if data.get("doenca_valvar_conhecida"):
        fatores.append("Doença valvar")
    if data.get("dac_conhecida"):
        fatores.append("DAC conhecida/suspeita")
    return fatores


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def calcular_risco(data: dict) -> dict:
    mets: float = data.get("mets", 4)
    risco_cirurgia: str = data.get("risco_cirurgia", "intermediario")
    tipo_cirurgia: str = data.get("tipo_cirurgia", "")
    # Aceita múltiplos indicadores para cirurgia vascular e infere do tipo_cirurgia
    eh_vascular: bool = (
        bool(data.get("eh_vascular", False))
        or bool(data.get("surgery_is_vascular", False))
        or (str(tipo_cirurgia).lower().find("vascular") >= 0)
    )

    # 1. Verificar condições cardiovasculares ativas (Tabela 2)
    condicoes_ativas = verificar_condicoes_ativas(data)
    tem_condicoes_ativas = len(condicoes_ativas) > 0

    # 2. Pontuação usando RCRI ou VSG
    if eh_vascular:
        indice_risco = "vsg"
        pontuacao, criterios_atingidos = pontuar_vsg(data)
        classe_risco, rotulo_risco = _obter_classe_risco_vsg(pontuacao)
    else:
        indice_risco = "rcri"
        pontuacao, criterios_atingidos = pontuar_rcri(data)
        classe_risco, rotulo_risco = _obter_classe_risco_rcri(pontuacao)

    # 3. Override para cirurgia de baixo risco
    if risco_cirurgia == RiscoCirurgia.BAIXO and not tem_condicoes_ativas and classe_risco != ClasseRisco.ALTO:
        classe_risco, rotulo_risco = ClasseRisco.BAIXO, "Risco Baixo"

    # Se condições ativas, sempre risco alto
    if tem_condicoes_ativas:
        classe_risco = ClasseRisco.ALTO
        rotulo_risco = "Risco Alto (Condições Ativas)"

    # 5. Montar recomendações
    recomendacoes = montar_recomendacoes(
        classe_risco=classe_risco,
        pontuacao=pontuacao,
        mets=mets,
        risco_cirurgia=risco_cirurgia,
        tem_condicoes_ativas=tem_condicoes_ativas,
        condicoes_ativas=condicoes_ativas,
        eh_vascular=eh_vascular,
        data=data,
    )

    # 6. Montar orientações de medicação
    orientacoes_medicacao = montar_orientacoes_medicacao(data)

    # 7. Exames recomendados
    exames_recomendados = montar_recomendacoes_exames(
        data=data,
        classe_risco=classe_risco,
        pontuacao=pontuacao,
        tem_condicoes_ativas=tem_condicoes_ativas,
    )

    # 8. Tags de fatores de risco
    fatores_risco = montar_fatores_risco(data, criterios_atingidos, mets)

    return {
        "indice_risco": indice_risco,
        "pontuacao": pontuacao,
        "classe_risco": classe_risco,
        "rotulo_risco": rotulo_risco,
        "tem_condicoes_ativas": tem_condicoes_ativas,
        "condicoes_ativas": condicoes_ativas,
        "criterios_atingidos": criterios_atingidos,
        "fatores_risco": fatores_risco if fatores_risco else ["Sem fatores de risco identificados"],
        "recomendacoes": recomendacoes,
        "orientacoes_medicacao": orientacoes_medicacao,
        "exames_recomendados": exames_recomendados,
        "mets": mets,
        "rotulo_mets": METS_LABELS.get(mets, f"{mets} METs"),
        "tipo_cirurgia": tipo_cirurgia,
        "risco_cirurgia": risco_cirurgia,
        "rotulo_cirurgia": ROTULOS_CIRURGIA.get(risco_cirurgia, "—"),
        "eh_vascular": eh_vascular,
        "capacidade_funcional_adequada": mets >= 4,
    }
