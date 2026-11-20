"""Avaliação quantitativa do preenchimento automático (módulo de texto livre) do CardioRisk Periop.

Uso (a partir da pasta backend/ do projeto):
    set CARDIORISK_ENABLE_NER=false        (Windows)  |  export CARDIORISK_ENABLE_NER=false  (Linux/Mac)
    python avaliar_pln.py

Gera: resultados_por_caso.csv, metricas_por_campo.csv e relatorio_avaliacao_pln.md

Com a opção --ner (exige transformers e torch: pip install -r requirements-ner.txt):
    python avaliar_pln.py --ner
roda os mesmos casos com os modelos de NER ligados e mede o que a conferência (`ner_review`)
acrescenta. Gera: avaliacao_ner.csv e resumo_avaliacao_ner.md. Não regrava os três arquivos acima.

Cada caso tem um texto clínico fictício e um gabarito (o que um profissional marcaria no formulário).
O gabarito foi revisado por um médico em 19/11/2026 (casos 8, 9, 35, 47, 49, 53 e 56 corrigidos).
O script compara o gabarito com o que `analisar_texto_clinico` preenche, campo a campo.
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
import time

MODO_NER = "--ner" in sys.argv[1:]
if MODO_NER:
    os.environ["CARDIORISK_ENABLE_NER"] = "true"
else:
    os.environ.setdefault("CARDIORISK_ENABLE_NER", "false")
sys.path.insert(0, os.getcwd())

from core import clinical_nlp  # noqa: E402
from core.calculator import calcular_risco  # noqa: E402
from core.clinical_nlp import SURGERY_TYPE_MAP, analisar_texto_clinico  # noqa: E402

# Abreviações usadas no gabarito -> campo do formulário
CAMPOS = {
    "ins": "rcri_diabetes_insulina",
    "avc": "rcri_cerebrovascular",
    "dac": "rcri_doenca_coronaria",
    "ic": "rcri_ic",
    "dpoc": "vsg_dpoc",
    "tab": "vsg_tabagismo",
    "bb": "vsg_betabloqueador_cronico",
    "revasc": "vsg_revasc_previa",
    "obes": "obesidade",
    "valv": "doenca_valvar_conhecida",
    "valvgrave": "cv_valvopatia_grave",
    "aas": "usa_aas",
    "clopi": "usa_clopidogrel",
    "varf": "usa_varfarina",
    "doac": "usa_doac",
    "icativa": "cv_ic_nyha_3_4",
    "cirintra": "rcri_cirurgia_alto_risco",
}
ROTULOS = {
    "rcri_diabetes_insulina": "Diabetes com insulina",
    "rcri_cerebrovascular": "Doença cerebrovascular (AVC/AIT)",
    "rcri_doenca_coronaria": "Doença arterial coronariana",
    "rcri_ic": "Insuficiência cardíaca",
    "rcri_creatinina_acima_2": "Creatinina > 2,0 mg/dL",
    "vsg_creatinina_acima_1_8": "Creatinina > 1,8 mg/dL",
    "vsg_dpoc": "DPOC",
    "vsg_tabagismo": "Tabagismo",
    "vsg_betabloqueador_cronico": "Betabloqueador crônico",
    "vsg_revasc_previa": "Revascularização miocárdica prévia",
    "obesidade": "Obesidade",
    "doenca_valvar_conhecida": "Doença valvar conhecida",
    "cv_valvopatia_grave": "Valvopatia grave sintomática",
    "usa_aas": "Uso de AAS",
    "usa_clopidogrel": "Uso de clopidogrel",
    "usa_varfarina": "Uso de varfarina",
    "usa_doac": "Uso de DOAC",
    "cv_ic_nyha_3_4": "IC classe funcional III/IV (condição ativa)",
    "rcri_cirurgia_alto_risco": "Cirurgia de alto risco (critério do RCRI)",
}
BOOLEANOS = list(ROTULOS)

# (grupo, texto, idade, mets, tipo_cirurgia, achados presentes, creatinina em mg/dL ou None)
# Grupo A: redação direta | B: siglas e sinônimos | C: negações, tempo e termos ambíguos
CASOS = [
    ("A", "Paciente de 67 anos, hipertenso e diabético em uso de insulina NPH. Nega dor torácica. Creatinina 1,1 mg/dL. Capacidade funcional de 6 METs. Será submetido a colecistectomia videolaparoscópica.", 67, 6, "intraperitoneal", "ins", 1.1),
    ("A", "Mulher, 72 anos, portadora de insuficiência cardíaca e fibrilação atrial, em uso de varfarina e carvedilol. Creatinina 0,9. 4 METs. Programada artroplastia total de quadril.", 72, 4, "orthopedic_major", "ic varf bb", 0.9),
    ("A", "Homem de 58 anos, tabagista, com DPOC. Infarto agudo do miocárdio há 2 anos, tratado com angioplastia coronária. Usa AAS e atenolol. Creatinina 1,0 mg/dL. 5 METs. Cirurgia proposta: correção endovascular de aneurisma de aorta abdominal.", 58, 5, "endovascular_aortic", "tab dpoc dac revasc aas bb", 1.0),
    ("A", "Paciente de 45 anos, sem comorbidades, 10 METs, função renal normal. Tireoidectomia total por bócio.", 45, 10, "thyroid", "", None),
    ("A", "Paciente de 80 anos, com AVC isquêmico há 5 anos, hipertensa. Usa clopidogrel. Creatinina 2,4 mg/dL. Capacidade funcional de 3 METs. Cirurgia de catarata.", 80, 3, "eye", "avc clopi", 2.4),
    ("A", "Homem, 63 anos, obeso, diabético em uso de metformina. Sem uso de insulina. Creatinina 1,2. 7 METs. Hemicolectomia direita por neoplasia.", 63, 7, "intraperitoneal", "obes", 1.2),
    ("A", "Paciente de 70 anos, DAC com cirurgia de revascularização miocárdica em 2018, IC com fração de ejeção de 35%. Em uso de AAS, metoprolol e rivaroxabana por FA. Creatinina 1,9 mg/dL. 4 METs. Endarterectomia de carótida esquerda.", 70, 4, "carotid_endarterectomy", "dac revasc ic aas bb doac", 1.9),
    ("A", "Mulher de 55 anos, hipertensa. Nega tabagismo e etilismo. Função renal preservada. 8 METs. Histerectomia total abdominal.", 55, 8, "gynecologic_major", "cirintra", None),
    ("A", "Paciente de 77 anos com estenose aórtica importante sintomática, dispneia aos pequenos esforços. Creatinina 1,3. 3 METs. Fratura de fêmur, aguardando osteossíntese.", 77, 3, "orthopedic_major", "valv valvgrave ic", 1.3),
    ("A", "Homem, 66 anos, tabagista ativo, DPOC em uso de broncodilatador, diabético insulinodependente, doença arterial periférica. Usa AAS. Creatinina 2,1 mg/dL. 4 METs. Bypass femoropoplíteo.", 66, 4, "peripheral_open", "tab dpoc ins aas", 2.1),
    ("A", "Paciente de 49 anos, prótese valvar mitral mecânica, em uso de Marevan. Sem outras comorbidades. Creatinina 0,8. 9 METs. Mastectomia radical.", 49, 9, "breast", "valv varf", 0.8),
    ("A", "Paciente de 82 anos, acamado, com sequela de AVC, insuficiência renal crônica com creatinina de 3,1 mg/dL. Usa AAS. Amputação de membro inferior por isquemia.", 82, None, "peripheral_open", "avc aas", 3.1),
    ("A", "Homem de 60 anos, hipertenso, dislipidêmico. Angina estável. Usa AAS, sinvastatina e bisoprolol. Creatinina 1,0. 6 METs. Prostatectomia radical.", 60, 6, "urologic_major", "dac aas bb", 1.0),
    ("A", "Mulher, 68 anos, FA em uso de apixabana, hipotireoidismo. TFG 75 mL/min. 5 METs. Artroscopia de joelho.", 68, 5, "orthopedic_minor", "doac", None),
    ("A", "Paciente de 74 anos, IAM prévio, ICC, DM em uso de insulina glargina, creatinina 2,2 mg/dL. Usa AAS, clopidogrel e carvedilol. 3 METs. Correção aberta de aneurisma de aorta abdominal.", 74, 3, "aortic_vascular_major", "dac ic ins aas clopi bb", 2.2),
    ("A", "Paciente de 52 anos, obesidade grau III, apneia do sono, hipertenso. Função renal normal. 6 METs. Gastroplastia redutora (cirurgia bariátrica) por videolaparoscopia.", 52, 6, "intraperitoneal", "obes", None),
    ("A", "Homem de 71 anos, ex-etilista, cirrose. Sem cardiopatia conhecida. Creatinina 1,4. 5 METs. Hepatectomia parcial.", 71, 5, "liver_biliary", "", 1.4),
    ("A", "Mulher de 64 anos, hipertensa, AIT há 1 mês, em uso de AAS. Creatinina 0,9. 7 METs. Endarterectomia de carótida direita.", 64, 7, "carotid_endarterectomy", "avc aas", 0.9),
    ("A", "Paciente de 59 anos, tabagista, neoplasia de pulmão. DPOC moderado. Creatinina 1,0. 5 METs. Lobectomia pulmonar superior direita.", 59, 5, "pneumectomy", "tab dpoc", 1.0),
    ("A", "Paciente de 38 anos, hígida, 10 METs, creatinina 0,7. Curetagem uterina.", 38, 10, "gynecologic_minor", "", 0.7),

    ("B", "Masc, 69a, HAS, DM2 insulino-requerente, DRC (Cr 2,3). IAM em 2019 c/ ATC + stent. Em uso de AAS, clopidogrel, enalapril. CF 4 METs. Proposta: colectomia esquerda.", 69, 4, "intraperitoneal", "ins dac revasc aas clopi", 2.3),
    ("B", "Fem, 75 anos, ICFEr (FE 30%), FA crônica, em uso de varfarina, bisoprolol e furosemida. Cr 1,5 mg/dL. 3 METs. ATQ à direita por coxartrose.", 75, 3, "orthopedic_major", "ic varf bb", 1.5),
    ("B", "Paciente 61 anos, coronariopata, CRM há 6 anos, tabagista 40 anos-maço. AAS e metoprolol de uso contínuo. Creatinina 1,2. 5 METs. EVAR.", 61, 5, "endovascular_aortic", "dac revasc tab aas bb", 1.2),
    ("B", "Paciente de 79 anos, AVE isquêmico prévio, HAS, DLP. Usa ácido acetilsalicílico. Creatinina 1,1. 4 METs. Facoemulsificação com implante de lente.", 79, 4, "eye", "avc aas", 1.1),
    ("B", "Homem, 57 anos, DPOC, fumante, DAOP com claudicação. Usa cilostazol e AAS. Creat 1,0. 4 METs. Angioplastia de artéria femoral superficial.", 57, 4, "peripheral_angioplasty", "dpoc tab aas", 1.0),
    ("B", "Mulher de 66 anos, estenose mitral reumática, FA, anticoagulada com Marevan. Creatinina 0,9. 5 METs. Colecistectomia.", 66, 5, "intraperitoneal", "valv varf", 0.9),
    ("B", "Paciente de 73 anos, insuficiência cardíaca congestiva, doença renal crônica (creatinina 2,6), DM insulinodependente. Usa carvedilol. 3 METs. Amputação transtibial.", 73, 3, "peripheral_open", "ic ins bb", 2.6),
    ("B", "Homem de 62 anos, HAS, sem DAC conhecida, teste ergométrico normal. Betabloqueador: não usa. Creatinina 0,9. 9 METs. RTU de próstata.", 62, 9, "urologic_minor", "", 0.9),
    ("B", "Paciente de 85 anos, FA permanente em uso de Xarelto, IC, marcapasso. Clearance de creatinina 40 mL/min, creatinina 1,7. 3 METs. Fratura de colo de fêmur, artroplastia parcial de quadril.", 85, 3, "orthopedic_major", "ic doac", 1.7),
    ("B", "Paciente de 54 anos, TEP há 4 meses, em uso de rivaroxabana. Sem outras doenças. Creatinina 0,8. 8 METs. Herniorrafia incisional.", 54, 8, "intraperitoneal", "doac", 0.8),
    ("B", "Mulher, 70 anos, DM2 em insulinoterapia, HAS, obesa. Nega IAM ou AVC prévios. Creatinina 1,3. 5 METs. Artroplastia total de joelho.", 70, 5, "orthopedic_major", "ins obes", 1.3),
    ("B", "Homem de 65 anos, angioplastia coronária com 2 stents em 2021, dupla antiagregação com AAS e ticagrelor. Atenolol. Creatinina 1,0. 6 METs. Parotidectomia.", 65, 6, "head_neck", "dac revasc aas bb", 1.0),
    ("B", "Paciente de 76 anos, estenose aórtica moderada assintomática, HAS. Creatinina 1,2. 5 METs. Colectomia por diverticulite.", 76, 5, "intraperitoneal", "valv", 1.2),
    ("B", "Paciente de 48 anos, fuma 1 maço/dia, sem outras comorbidades. Creatinina 0,9. 10 METs. Laminectomia lombar.", 48, 10, "neurologic", "tab", 0.9),
    ("B", "Homem, 68 anos, IRC dialítica, DM com insulina, DAC. AAS. Creatinina 6,8 mg/dL. 3 METs. Transplante renal.", 68, 3, "renal_transplant", "ins dac aas cirintra", 6.8),
    ("B", "Mulher de 81 anos, demência, AVC há 2 meses, FA em uso de varfarina. Creatinina 1,0. 2 METs. Osteossíntese de fratura transtrocanteriana.", 81, 2, "orthopedic_major", "avc varf", 1.0),
    ("B", "Paciente de 56 anos, etilista, pancreatite crônica. Sem cardiopatia. Creatinina 0,8. 7 METs. Duodenopancreatectomia.", 56, 7, "pancreatic", "", 0.8),
    ("B", "Paciente de 67 anos, DPOC grave em uso de oxigênio domiciliar, IC direita. Creatinina 1,1. 2 METs. Toracotomia para ressecção de nódulo.", 67, 2, "intrathoracic", "dpoc ic", 1.1),
    ("B", "Homem de 72 anos, portador de marca-passo, DAC, IAM há 4 meses, em uso de AAS, prasugrel e metoprolol. Creatinina 1,4. 4 METs. Gastrectomia subtotal.", 72, 4, "intraperitoneal", "dac aas bb", 1.4),
    ("B", "Paciente de 43 anos, sem comorbidades. Função renal preservada. 9 METs. Exérese de lipoma em dorso.", 43, 9, "superficial", "", None),

    ("C", "Paciente de 78 anos, hipertenso, diabético em uso de gliclazida (não usa insulina). Oclusão arterial aguda de membro inferior direito. Creatinina 1,6. 4 METs. Revascularização de artéria poplítea.", 78, 4, "peripheral_open", "", 1.6),
    ("C", "Mulher de 60 anos, pai faleceu de infarto aos 50 anos. Sem doença cardíaca pessoal. Creatinina 0,8. 8 METs. Quadrantectomia de mama.", 60, 8, "breast", "", 0.8),
    ("C", "Homem de 69 anos, AVC negado, nega angina, nega dispneia. HAS e DLP. Creatinina 1,1. 7 METs. Prostatectomia radical robótica.", 69, 7, "urologic_major", "", 1.1),
    ("C", "Paciente de 71 anos, insuficiência mitral leve ao ecocardiograma, sem repercussão. HAS. Creatinina 1,0. 6 METs. Vitrectomia.", 71, 6, "eye", "valv", 1.0),
    ("C", "Paciente de 64 anos, sem valvopatia, sem insuficiência cardíaca, sem coronariopatia. DM tipo 2 com insulina NPH à noite. Creatinina 1,2. 6 METs. Esplenectomia.", 64, 6, "intraperitoneal", "ins", 1.2),
    ("C", "Mulher de 58 anos, IMC 38 kg/m², hipertensa, DM em uso de insulina. Creatinina 0,9. 5 METs. Histerectomia vaginal.", 58, 5, "gynecologic_major", "obes ins", 0.9),
    ("C", "Homem de 75 anos, DAC triarterial, recusou revascularização. Mantém tratamento clínico com AAS, atorvastatina e carvedilol. Creatinina 1,5. 4 METs. Cistectomia radical.", 75, 4, "total_cystectomy", "dac aas bb cirintra", 1.5),
    ("C", "Paciente de 66 anos, IC com fração de ejeção preservada, FA em uso de dabigatrana. Creatinina 1,3. 4 METs. Esofagectomia.", 66, 4, "esophagectomy", "ic doac", 1.3),
    ("C", "Paciente de 83 anos, estenose aórtica grave, sintomática (síncope e dispneia). Creatinina 1,4. 2 METs. Artroplastia de quadril.", 83, 2, "orthopedic_major", "valv valvgrave ic", 1.4),
    ("C", "Homem de 62 anos, AVCi em 2015 sem sequelas, tabagista, DPOC. Usa AAS e sinvastatina. Creatinina 1,9 mg/dL. 5 METs. Stent de carótida.", 62, 5, "carotid_angioplasty", "avc tab dpoc aas", 1.9),
    ("C", "IAM há 3 anos. Homem de 67 anos, em uso de AAS e atenolol. Creatinina 1,1. 6 METs. Colecistectomia.", 67, 6, "intraperitoneal", "dac aas bb", 1.1),
    ("C", "Mulher de 74 anos, valva aórtica mecânica, anticoagulada com varfarina, INR 2,8. Creatinina 1,0. 5 METs. Mastectomia simples.", 74, 5, "breast", "valv varf", 1.0),
    ("C", "Paciente de 68 anos, ICC classe funcional III, edema de membros inferiores, ortopneia. Usa furosemida e espironolactona. Creatinina 2,0 mg/dL. 2 METs. Laparotomia exploradora.", 68, 2, "intraperitoneal", "ic icativa", 2.0),
    ("C", "Homem de 59 anos, asmático (não tem DPOC), não fumante. Creatinina 0,9. 8 METs. Tireoidectomia parcial.", 59, 8, "thyroid", "", 0.9),
    ("C", "Paciente de 70 anos, DAP, DM2 insulinizado, HAS. Angioplastia de artéria ilíaca programada. Usa AAS e clopidogrel. Creatinina 1,7. 4 METs.", 70, 4, "peripheral_angioplasty", "ins aas clopi", 1.7),
    ("C", "Mulher de 63 anos, trombose venosa profunda há 2 meses, em uso de Eliquis. Creatinina 0,7. 7 METs. Ooforectomia bilateral.", 63, 7, "gynecologic_major", "doac cirintra", 0.7),
    ("C", "Paciente de 77 anos, HAS, DM, dislipidemia. Em uso de losartana, metformina e propranolol. Creatinina 1,2. 5 METs. Hernioplastia umbilical.", 77, 5, "intraperitoneal", "bb", 1.2),
    ("C", "Homem de 65 anos, infarto prévio com implante de stent farmacológico, IC, em uso de AAS, Brilinta e bisoprolol. Creatinina 1,3. 4 METs. Colectomia total.", 65, 4, "intraperitoneal", "dac revasc ic aas bb", 1.3),
    ("C", "Paciente de 50 anos, sem queixas, pratica corrida. Função renal sem alterações. Capacidade funcional acima de 10 METs. Postectomia.", 50, 10, "urologic_minor", "", None),
    ("C", "Mulher de 79 anos, FA valvar por estenose mitral, em uso de varfarina, AVC há 6 semanas. Creatinina 1,1. 3 METs. Fixação de fratura de fêmur.", 79, 3, "orthopedic_major", "valv avc varf", 1.1),
]


def faixa_etaria(idade):
    if idade is None:
        return ""
    return "gte80" if idade >= 80 else "70_79" if idade >= 70 else "60_69" if idade >= 60 else ""


def gabarito_para_formulario(idade, mets, cirurgia, achados, creat):
    """Monta os campos do formulário como um profissional preencheria."""
    d = {"idade": idade, "tipo_cirurgia": cirurgia}
    if mets is not None:
        d["mets"] = mets
    info = SURGERY_TYPE_MAP[cirurgia]
    d.update(risco_cirurgia=info["risco"], eh_vascular=info["vascular"],
             rcri_cirurgia_alto_risco=info.get("intracavitaria", False))
    for campo in BOOLEANOS:
        if campo != "rcri_cirurgia_alto_risco":
            d[campo] = False
    for a in achados.split():
        d[CAMPOS[a]] = True
    if creat is not None:
        d["rcri_creatinina_acima_2"] = creat > 2.0
        d["vsg_creatinina_acima_1_8"] = creat > 1.8
    return d


def completar(d):
    """Campos derivados que o formulário mantém em sincronia."""
    d = dict(d)
    d["vsg_faixa_etaria"] = faixa_etaria(d.get("idade"))
    d["vsg_diabetes_insulina"] = bool(d.get("rcri_diabetes_insulina"))
    d["vsg_dac"] = d["dac_conhecida"] = bool(d.get("rcri_doenca_coronaria"))
    d["vsg_ic"] = d["ic_conhecida"] = bool(d.get("rcri_ic"))
    return d


def prf(vp, fp, fn):
    p = vp / (vp + fp) if vp + fp else None
    r = vp / (vp + fn) if vp + fn else None
    f = 2 * p * r / (p + r) if p and r else (0.0 if (p is not None and r is not None) else None)
    return p, r, f


def fmt(x):
    return "–" if x is None else f"{x:.2f}".replace(".", ",")


def main():
    cont = {c: {"vp": 0, "fp": 0, "fn": 0, "vn": 0} for c in BOOLEANOS}
    por_grupo = {g: {"vp": 0, "fp": 0, "fn": 0} for g in "ABC"}
    linhas = []
    tot = {"idade": 0, "mets": 0, "mets_n": 0, "cir_ok": 0, "cir_errada": 0, "cir_ausente": 0,
           "perfeito": 0, "indice": 0, "pontos": 0, "classe": 0, "subestima": 0, "superestima": 0}
    grupo_n = {g: {"n": 0, "perfeito": 0, "classe": 0} for g in "ABC"}

    for i, (grupo, texto, idade, mets, cirurgia, achados, creat) in enumerate(CASOS, 1):
        ouro = gabarito_para_formulario(idade, mets, cirurgia, achados, creat)
        pred = analisar_texto_clinico(texto)["autofill"]
        erros = []

        for campo in BOOLEANOS:
            g, p = bool(ouro[campo]), bool(pred.get(campo, False))
            chave = "vp" if g and p else "fp" if p else "fn" if g else "vn"
            cont[campo][chave] += 1
            if chave in ("vp", "fp", "fn"):
                por_grupo[grupo][chave] += 1
            if chave == "fp":
                erros.append(f"+{ROTULOS[campo]}")
            if chave == "fn":
                erros.append(f"-{ROTULOS[campo]}")

        idade_ok = pred.get("idade") == idade
        tot["idade"] += idade_ok
        if not idade_ok:
            erros.append(f"idade lida como {pred.get('idade')}")
        if mets is not None:
            tot["mets_n"] += 1
            mets_ok = pred.get("mets") == mets
            tot["mets"] += mets_ok
            if not mets_ok:
                erros.append(f"METs lido como {pred.get('mets')}")
        cir_pred = pred.get("tipo_cirurgia")
        if cir_pred == cirurgia:
            tot["cir_ok"] += 1
        elif cir_pred is None:
            tot["cir_ausente"] += 1
            erros.append("cirurgia não identificada")
        else:
            tot["cir_errada"] += 1
            erros.append(f"cirurgia lida como {cir_pred} (esperado {cirurgia})")

        perfeito = not erros
        tot["perfeito"] += perfeito

        # Efeito no resultado final: calculadora com o gabarito x com o preenchimento automático
        r_ouro = calcular_risco(completar(ouro))
        r_pred = calcular_risco(completar(pred))
        mesmo_indice = r_ouro["indice_risco"] == r_pred["indice_risco"]
        mesma_pont = mesmo_indice and r_ouro["pontuacao"] == r_pred["pontuacao"]
        mesma_classe = str(r_ouro["classe_risco"]) == str(r_pred["classe_risco"])
        tot["indice"] += mesmo_indice
        tot["pontos"] += mesma_pont
        tot["classe"] += mesma_classe
        ordem = {"baixo": 0, "intermediario": 1, "alto": 2}
        co = ordem.get(str(getattr(r_ouro["classe_risco"], "value", r_ouro["classe_risco"])), None)
        cp = ordem.get(str(getattr(r_pred["classe_risco"], "value", r_pred["classe_risco"])), None)
        if co is not None and cp is not None and cp < co:
            tot["subestima"] += 1
        if co is not None and cp is not None and cp > co:
            tot["superestima"] += 1
        grupo_n[grupo]["n"] += 1
        grupo_n[grupo]["perfeito"] += perfeito
        grupo_n[grupo]["classe"] += mesma_classe

        linhas.append({
            "caso": i, "grupo": grupo, "texto": texto,
            "indice_esperado": r_ouro["indice_risco"], "pontos_esperados": r_ouro["pontuacao"],
            "classe_esperada": getattr(r_ouro["classe_risco"], "value", r_ouro["classe_risco"]),
            "indice_obtido": r_pred["indice_risco"], "pontos_obtidos": r_pred["pontuacao"],
            "classe_obtida": getattr(r_pred["classe_risco"], "value", r_pred["classe_risco"]),
            "preenchimento_sem_erros": "sim" if perfeito else "não",
            "erros (+ = preencheu a mais, - = deixou de preencher)": "; ".join(erros),
        })

    n = len(CASOS)
    with open("resultados_por_caso.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";")
        w.writeheader(); w.writerows(linhas)

    metricas = []
    VP = FP = FN = 0
    f1s = []
    for campo in BOOLEANOS:
        c = cont[campo]
        p, r, f = prf(c["vp"], c["fp"], c["fn"])
        VP += c["vp"]; FP += c["fp"]; FN += c["fn"]
        if f is not None:
            f1s.append(f)
        metricas.append({"campo": ROTULOS[campo], "presentes_no_gabarito": c["vp"] + c["fn"], "VP": c["vp"],
                         "FP": c["fp"], "FN": c["fn"], "precisao": fmt(p), "revocacao": fmt(r), "F1": fmt(f)})
    P, R, F = prf(VP, FP, FN)
    macro = sum(f1s) / len(f1s)
    metricas.append({"campo": "TOTAL (micro)", "presentes_no_gabarito": VP + FN, "VP": VP, "FP": FP, "FN": FN,
                     "precisao": fmt(P), "revocacao": fmt(R), "F1": fmt(F)})
    with open("metricas_por_campo.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(metricas[0]), delimiter=";")
        w.writeheader(); w.writerows(metricas)

    pct = lambda a, b: f"{a}/{b} ({100 * a / b:.1f}%)".replace(".", ",")
    md = ["# Avaliação do preenchimento automático – CardioRisk Periop", "",
          f"Casos avaliados: {n} textos clínicos fictícios (20 de redação direta, 20 com siglas e sinônimos, "
          "20 com negações, tempo e termos ambíguos). Gabarito revisado por um médico. NER desativado (somente regras).", "",
          "## Campos de sim/não (comorbidades e medicamentos)", "",
          "| Campo | Presentes | VP | FP | FN | Precisão | Revocação | F1 |", "|---|---|---|---|---|---|---|---|"]
    for m in metricas:
        md.append(f"| {m['campo']} | {m['presentes_no_gabarito']} | {m['VP']} | {m['FP']} | {m['FN']} | "
                  f"{m['precisao']} | {m['revocacao']} | {m['F1']} |")
    md += ["", f"F1 macro (média simples dos campos): {fmt(macro)}", "",
           "## Por grupo de casos", "", "| Grupo | Precisão | Revocação | F1 | Casos sem nenhum erro | Mesma classe de risco |",
           "|---|---|---|---|---|---|"]
    nomes = {"A": "A – redação direta", "B": "B – siglas e sinônimos", "C": "C – negações e ambiguidades"}
    for g in "ABC":
        p, r, f = prf(**por_grupo[g])
        md.append(f"| {nomes[g]} | {fmt(p)} | {fmt(r)} | {fmt(f)} | {pct(grupo_n[g]['perfeito'], grupo_n[g]['n'])} | "
                  f"{pct(grupo_n[g]['classe'], grupo_n[g]['n'])} |")
    md += ["", "## Outros campos", "",
           f"- Idade correta: {pct(tot['idade'], n)}",
           f"- METs correto (quando informado em número): {pct(tot['mets'], tot['mets_n'])}",
           f"- Tipo de cirurgia correto: {pct(tot['cir_ok'], n)}; não identificado: {pct(tot['cir_ausente'], n)}; "
           f"identificado errado: {pct(tot['cir_errada'], n)}", "",
           "## Efeito no resultado da calculadora (sem correção manual)", "",
           f"- Casos com preenchimento totalmente correto: {pct(tot['perfeito'], n)}",
           f"- Mesmo índice (RCRI ou VSG-CRI): {pct(tot['indice'], n)}",
           f"- Mesma pontuação: {pct(tot['pontos'], n)}",
           f"- Mesma classe de risco: {pct(tot['classe'], n)}",
           f"- Classe de risco menor que a correta (subestimou): {pct(tot['subestima'], n)}",
           f"- Classe de risco maior que a correta (superestimou): {pct(tot['superestima'], n)}", ""]
    open("relatorio_avaliacao_pln.md", "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(md))


# ---------------------------------------------------------------------------
# Avaliação da conferência com o NER (opção --ner)
# ---------------------------------------------------------------------------

# Palavras que, em um aviso, apontam para o campo que as regras erraram. Servem para a conferência
# automática "o aviso apontava o termo?"; o CSV traz os avisos por extenso para a revisão manual.
PISTAS = {
    "rcri_diabetes_insulina": r"insulin|nph|glargina",
    "rcri_cerebrovascular": r"\bavc|\bave\b|\bait\b|cerebr",
    "rcri_doenca_coronaria": r"coronari|\biam\b|infarto|angina|\bdac\b|\batc\b|stent|\bcrm\b|revasculariza",
    "rcri_ic": r"\bic\b|\bicc\b|icfe|insuficiencia cardiaca|dispneia|fracao de ejecao",
    "rcri_creatinina_acima_2": r"creat|renal|\bdrc\b|\birc\b|clearance",
    "vsg_creatinina_acima_1_8": r"creat|renal|\bdrc\b|\birc\b|clearance",
    "vsg_dpoc": r"dpoc|pulmonar obstrutiva",
    "vsg_tabagismo": r"tabag|fum|maco",
    "vsg_betabloqueador_cronico": r"olol\b|betabloq|beta-bloq|beta bloq",
    "vsg_revasc_previa": r"revasculariza|\bcrm\b|\batc\b|stent|angioplastia|safena",
    "obesidade": r"obes|\bimc\b",
    "doenca_valvar_conhecida": r"valv|estenose|protese|insuficiencia (?:mitral|aortica)",
    "cv_valvopatia_grave": r"valv|estenose",
    "usa_aas": r"\baas\b|acetilsalicilico|aspirina",
    "usa_clopidogrel": r"clopidogrel",
    "usa_varfarina": r"varfarina|marevan",
    "usa_doac": r"xabana|dabigatrana|xarelto|eliquis|pradaxa|lixiana|\bdoac\b",
    "cv_ic_nyha_3_4": r"classe funcional|nyha|ortopneia|edema|\bicc?\b|insuficiencia cardiaca",
    "rcri_cirurgia_alto_risco": r"tomia|plastia|rafia|transplante|exerese|resseccao|cirurgia|bariatrica",
}
PISTA_CIRURGIA = (r"tomia|plastia|rafia|transplante|exerese|resseccao|cirurgia|bariatrica|facoemulsificacao"
                  r"|amputacao|bypass|revascularizacao|\batq\b|\batj\b")


def _aponta(campo_ou_padrao, itens):
    padrao = PISTAS.get(campo_ou_padrao, campo_ou_padrao)
    return [i["text"] for i in itens if re.search(padrao, clinical_nlp._normalizar(i["text"]))]


def _memoria_mb():
    """(memória em uso, pico) do processo, em MB."""
    import psutil

    info = psutil.Process().memory_info()
    return info.rss / 2**20, getattr(info, "peak_wset", info.rss) / 2**20


def _memoria_so_regras_mb():
    """Memória de um processo Python só com as regras, sem transformers/torch carregados."""
    codigo = (
        "import sys, os; sys.modules['transformers'] = None; os.environ['CARDIORISK_ENABLE_NER'] = 'false';"
        "sys.path.insert(0, os.getcwd()); import psutil;"
        "from core.calculator import calcular_risco; from core.clinical_nlp import analisar_texto_clinico;"
        "analisar_texto_clinico('Paciente de 67 anos, em uso de AAS. Colecistectomia.');"
        "print(psutil.Process().memory_info().rss / 2**20)"
    )
    saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, check=True)
    return float(saida.stdout.strip().splitlines()[-1])


def _tempo_medio_ms(textos, repeticoes):
    t0 = time.perf_counter()
    for _ in range(repeticoes):
        for texto in textos:
            analisar_texto_clinico(texto)
    return 1000 * (time.perf_counter() - t0) / (repeticoes * len(textos))


def main_ner():
    n = len(CASOS)
    textos = [c[1] for c in CASOS]
    num = lambda x, casas=1: f"{x:.{casas}f}".replace(".", ",")
    lista = lambda itens: ", ".join(a["text"] for a in itens)

    # 1) Só regras: preenchimento de referência e tempo.
    clinical_nlp.ENABLE_NER = False
    so_regras = [analisar_texto_clinico(t) for t in textos]
    tempo_regras = _tempo_medio_ms(textos, 20)
    mem_regras = _memoria_so_regras_mb()
    mem_antes, _ = _memoria_mb()

    # 2) Com os modelos: carga, tempo e memória.
    clinical_nlp.ENABLE_NER = True
    t0 = time.perf_counter()
    cargas = []
    for nome in clinical_nlp.MODEL_NAMES:
        t1 = time.perf_counter()
        modelo, erro = clinical_nlp._obter_pipeline_ner(nome)
        if modelo is None:
            sys.exit(f"Não foi possível carregar {nome}: {erro}")
        cargas.append((nome, time.perf_counter() - t1))
    carga_total = time.perf_counter() - t0
    com_ner = [analisar_texto_clinico(t) for t in textos]  # também serve de aquecimento
    tempo_ner = _tempo_medio_ms(textos, 3)
    mem_ner, mem_pico = _memoria_mb()

    preenchimento_igual = sum(a["autofill"] == b["autofill"] for a, b in zip(so_regras, com_ner))

    linhas = []
    t = {"fn_casos": 0, "fn_campos": 0, "fn_com_aviso": 0, "fn_aponta_caso": 0, "fn_aponta_campo": 0,
         "cir_ausente": 0, "cir_aponta": 0, "limpos": 0, "limpos_com_aviso": 0, "avisos_limpos": 0,
         "avisos_limpos_negados": 0, "fp_casos": 0, "fp_campos": 0, "fp_negado_caso": 0, "fp_negado_campo": 0,
         "avisos": 0, "avisos_negados": 0, "confirmados": 0, "casos_com_aviso": 0, "entidades": 0}

    for i, (caso, resposta) in enumerate(zip(CASOS, com_ner), 1):
        grupo, texto, idade, mets, cirurgia, achados, creat = caso
        ouro = gabarito_para_formulario(idade, mets, cirurgia, achados, creat)
        pred = resposta["autofill"]
        fns = [c for c in BOOLEANOS if ouro[c] and not pred.get(c, False)]
        fps = [c for c in BOOLEANOS if pred.get(c, False) and not ouro[c]]
        cir_ausente = pred.get("tipo_cirurgia") is None
        outros = []
        if pred.get("idade") != idade:
            outros.append(f"idade lida como {pred.get('idade')}")
        if mets is not None and pred.get("mets") != mets:
            outros.append(f"METs lido como {pred.get('mets')}")
        if cir_ausente:
            outros.append("cirurgia não identificada")
        elif pred.get("tipo_cirurgia") != cirurgia:
            outros.append(f"cirurgia lida como {pred.get('tipo_cirurgia')}")
        sem_erro = not (fns or fps or outros)

        revisao = resposta["ner_review"]
        avisos = [a for a in revisao["nao_reconhecidos"] if not a["negado"]]
        avisos_neg = [a for a in revisao["nao_reconhecidos"] if a["negado"]]
        conf_neg = [a for a in revisao["confirmados"] if a["negado"]]
        todos_avisos = revisao["nao_reconhecidos"]
        todos_negados = avisos_neg + conf_neg

        t["entidades"] += len(resposta["entities"])
        t["avisos"] += len(avisos)
        t["avisos_negados"] += len(avisos_neg)
        t["confirmados"] += len(revisao["confirmados"])
        t["casos_com_aviso"] += bool(todos_avisos)

        # Falsos negativos: o aviso (não negado) aponta o termo que faltou?
        fn_apontados = {c: _aponta(c, avisos) for c in fns}
        if fns:
            t["fn_casos"] += 1
            t["fn_campos"] += len(fns)
            t["fn_com_aviso"] += bool(avisos)
            t["fn_aponta_caso"] += any(fn_apontados.values())
            t["fn_aponta_campo"] += sum(bool(v) for v in fn_apontados.values())
        cir_apontada = _aponta(PISTA_CIRURGIA, avisos) if cir_ausente else []
        if cir_ausente:
            t["cir_ausente"] += 1
            t["cir_aponta"] += bool(cir_apontada)

        # Alarmes falsos: avisos em casos em que as regras acertaram tudo.
        if sem_erro:
            t["limpos"] += 1
            t["limpos_com_aviso"] += bool(todos_avisos)
            t["avisos_limpos"] += len(avisos)
            t["avisos_limpos_negados"] += len(avisos_neg)

        # Falsos positivos: o termo que a regra usou indevidamente saiu marcado como negado?
        fp_negados = {c: _aponta(c, todos_negados) for c in fps}
        if fps:
            t["fp_casos"] += 1
            t["fp_campos"] += len(fps)
            t["fp_negado_caso"] += any(fp_negados.values())
            t["fp_negado_campo"] += sum(bool(v) for v in fp_negados.values())

        linhas.append({
            "caso": i, "grupo": grupo, "texto": texto,
            "preenchimento_sem_erros": "sim" if sem_erro else "não",
            "campos_que_faltaram (falso negativo)": "; ".join(ROTULOS[c] for c in fns),
            "campos_a_mais (falso positivo)": "; ".join(ROTULOS[c] for c in fps),
            "outros_erros": "; ".join(outros),
            "avisos (termos não usados no preenchimento)": lista(avisos),
            "avisos_negados (mencionados como ausentes)": lista(avisos_neg),
            "termos_das_regras_marcados_como_negados": lista(conf_neg),
            "aviso_aponta_campo_que_faltou": "; ".join(
                f"{ROTULOS[c]}: {', '.join(v) if v else 'não'}" for c, v in fn_apontados.items()),
            "aviso_aponta_cirurgia_nao_identificada": (", ".join(cir_apontada) or "não") if cir_ausente else "",
            "negacao_aponta_campo_a_mais": "; ".join(
                f"{ROTULOS[c]}: {', '.join(v) if v else 'não'}" for c, v in fp_negados.items()),
            "preenchimento_igual_ao_sem_ner": "sim" if so_regras[i - 1]["autofill"] == pred else "não",
        })

    with open("avaliacao_ner.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";")
        w.writeheader(); w.writerows(linhas)

    pct = lambda a, b: f"{a}/{b} ({100 * a / b:.1f}%)".replace(".", ",") if b else f"{a}/{b}"
    modelos = clinical_nlp.MODEL_NAMES
    md = ["# Avaliação da conferência com o NER – CardioRisk Periop", "",
          f"Casos: {n} textos clínicos fictícios, os mesmos de `python avaliar_pln.py`. As regras continuam "
          "sendo as únicas que preenchem campos; os modelos só geram avisos (`ner_review`).", "",
          "Modelos: " + ", ".join(f"`{m}`" for m in modelos)
          + f". Score mínimo: {num(clinical_nlp.NER_SCORE_MINIMO, 2)}.", "",
          "## O preenchimento não muda", "",
          f"- Casos com `autofill` idêntico com e sem os modelos: {pct(preenchimento_igual, n)}", "",
          "## Volume", "",
          f"- Entidades devolvidas pelos modelos: {t['entidades']}",
          f"- Termos que coincidem com o que as regras reconheceram (`confirmados`): {t['confirmados']}",
          f"- Avisos (`nao_reconhecidos` sem negação): {t['avisos']} (média de {num(t['avisos'] / n)} por caso)",
          f"- Avisos de termos negados (`nao_reconhecidos` com `negado`): {t['avisos_negados']}",
          f"- Casos com pelo menos um aviso (negado ou não): {pct(t['casos_com_aviso'], n)}", "",
          "## Campos que as regras deixaram de preencher (falsos negativos)", "",
          f"- Casos com pelo menos um campo de sim/não não preenchido: {t['fn_casos']} ({t['fn_campos']} campos)",
          f"- Desses casos, com pelo menos um aviso: {pct(t['fn_com_aviso'], t['fn_casos'])}",
          "- Desses casos, com aviso que aponta o termo de pelo menos um campo que faltou: "
          f"{pct(t['fn_aponta_caso'], t['fn_casos'])}",
          f"- Campos que faltaram com aviso apontando o termo: {pct(t['fn_aponta_campo'], t['fn_campos'])}",
          f"- Casos com cirurgia não identificada pelas regras: {t['cir_ausente']}; "
          f"com aviso que aponta o procedimento: {pct(t['cir_aponta'], t['cir_ausente'])}", "",
          "A conferência \"aponta o termo\" é automática, por palavras-chave de cada campo (dicionário "
          "`PISTAS` em `avaliar_pln.py`); o `avaliacao_ner.csv` lista os campos e os avisos de cada caso.", "",
          "## Alarmes falsos", "",
          f"- Casos sem nenhum erro das regras: {t['limpos']}",
          f"- Desses, com pelo menos um aviso (negado ou não): {pct(t['limpos_com_aviso'], t['limpos'])}",
          f"- Avisos nesses casos: {t['avisos_limpos']} sem negação "
          f"(média de {num(t['avisos_limpos'] / t['limpos'] if t['limpos'] else 0)} por caso) "
          f"e {t['avisos_limpos_negados']} de termos negados", "",
          "## Campos preenchidos indevidamente (falsos positivos) e negação", "",
          f"- Casos com pelo menos um campo de sim/não preenchido a mais: {t['fp_casos']} ({t['fp_campos']} campos)",
          f"- Desses casos, com o termo do campo marcado como `negado`: {pct(t['fp_negado_caso'], t['fp_casos'])}",
          f"- Campos a mais com o termo marcado como `negado`: {pct(t['fp_negado_campo'], t['fp_campos'])}", "",
          "## Tempo e memória", "",
          f"- Tempo médio por texto, só regras: {num(tempo_regras, 2)} ms",
          f"- Tempo médio por texto, regras + {len(modelos)} modelos (CPU): {num(tempo_ner)} ms",
          f"- Carga dos modelos (já baixados): {num(carga_total)} s ("
          + "; ".join(f"{nome.split('/')[-1]} {num(seg)} s" for nome, seg in cargas) + ")",
          "- Memória de um processo Python só com as regras, sem transformers/torch carregados "
          f"(sem contar o servidor web): {num(mem_regras, 0)} MB",
          "- Memória deste processo antes de carregar os modelos (transformers e torch importados): "
          f"{num(mem_antes, 0)} MB",
          f"- Memória com os {len(modelos)} modelos carregados, após os {n} casos: "
          f"{num(mem_ner, 0)} MB (pico: {num(mem_pico, 0)} MB)", ""]
    open("resumo_avaliacao_ner.md", "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main_ner() if MODO_NER else main()
