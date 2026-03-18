#!/usr/bin/env python3
"""
generate_calculator_knowledge.py
=================================
Gera knowledge/calculator_logic.json a partir das regras reais do calculator.py.

Execute sempre que as regras da calculadora mudarem:
  python generate_calculator_knowledge.py
"""

import json
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
OUT = KNOWLEDGE_DIR / "calculator_logic.json"

chunks = [
    # -----------------------------------------------------------------------
    # RCRI
    # -----------------------------------------------------------------------
    {
        "page": 1,
        "text": (
            "RCRI (Revised Cardiac Risk Index / Índice de Lee) — Cirurgias NÃO vasculares\n\n"
            "Instrumento de estratificação de risco cardíaco perioperatório para cirurgias não vasculares. "
            "Composto por 6 critérios, cada um valendo 1 ponto:\n\n"
            "1. Cirurgia de alto risco: procedimento intraperitoneal, intratorácico ou vascular suprainguinal.\n"
            "2. Doença arterial coronariana (DAC): histórico de IAM, ondas Q no ECG, uso de nitrato, "
            "angina, teste de esforço positivo, ou angioplastia/cirurgia de revascularização prévia.\n"
            "3. Insuficiência cardíaca congestiva (ICC): histórico de IC, edema pulmonar, dispneia "
            "paroxística noturna, crepitações bilaterais, cardiomegalia ao RX.\n"
            "4. Doença cerebrovascular: AVC ou AIT prévio.\n"
            "5. Diabetes com insulinoterapia: paciente diabético em uso de insulina.\n"
            "6. Creatinina pré-operatória > 2,0 mg/dL: insuficiência renal significativa.\n\n"
            "Fonte: Lee TH et al., Circulation 1999. Recomendado pela Diretriz SBC 2024."
        )
    },
    {
        "page": 2,
        "text": (
            "RCRI — Tabela de Risco de MACE (Eventos Cardiovasculares Adversos Maiores)\n\n"
            "A pontuação total do RCRI determina o risco estimado de MACE perioperatório "
            "(infarto, parada cardíaca, morte cardiovascular):\n\n"
            "  Score 0  → Classe I   → MACE ~3,9%\n"
            "  Score 1  → Classe II  → MACE ~6,0%\n"
            "  Score 2  → Classe III → MACE ~10,1%\n"
            "  Score ≥3 → Classe IV  → MACE ~15,0%\n\n"
            "Classificação de risco final:\n"
            "  MACE < 5%   → Risco BAIXO\n"
            "  MACE 5–10%  → Risco INTERMEDIÁRIO\n"
            "  MACE > 10%  → Risco ALTO\n\n"
            "Atenção: cirurgia de baixo risco intrínseco ( < 1% de MACE) é tratada como risco baixo "
            "independentemente da pontuação, desde que não haja condições cardiovasculares ativas.\n\n"
            "Referência: Duceppe et al., CMAJ 2017; ESC Guidelines 2022; Diretriz SBC 2024."
        )
    },
    # -----------------------------------------------------------------------
    # VSG-CRI
    # -----------------------------------------------------------------------
    {
        "page": 3,
        "text": (
            "VSG-CRI (Vascular Surgery Group Cardiac Risk Index) — Cirurgias VASCULARES\n\n"
            "Utilizado exclusivamente para cirurgias vasculares (não aplica o RCRI nesses casos). "
            "Pontuação variável por critério:\n\n"
            "IDADE:\n"
            "  60–69 anos → +2 pontos\n"
            "  70–79 anos → +3 pontos\n"
            "  ≥ 80 anos  → +4 pontos\n\n"
            "COMORBIDADES (2 pontos cada):\n"
            "  • Doença arterial coronariana (DAC)\n"
            "  • Insuficiência cardíaca (ICC)\n"
            "  • DPOC (doença pulmonar obstrutiva crônica)\n"
            "  • Creatinina > 1,8 mg/dL\n\n"
            "OUTROS FATORES (1 ponto cada):\n"
            "  • Tabagismo ativo\n"
            "  • Diabetes com insulinoterapia\n"
            "  • Uso crônico de betabloqueador\n\n"
            "FATOR PROTETOR:\n"
            "  • Revascularização miocárdica prévia → −1 ponto\n\n"
            "Pontuação mínima: 0 (não pode ser negativa).\n\n"
            "Referência: Bertges et al., J Vasc Surg 2010; Diretriz SBC 2024 Tabela 6."
        )
    },
    {
        "page": 4,
        "text": (
            "VSG-CRI — Classificação de Risco\n\n"
            "  Score 0–4  → Classe I  (Baixo risco)         → MACE estimado ~3,5%\n"
            "  Score 5–6  → Classe II (Risco intermediário) → MACE estimado ~8,0%\n"
            "  Score ≥ 7  → Classe III (Alto risco)         → MACE estimado ~15,0%\n\n"
            "Classificação de risco final (mesmos limiares do RCRI):\n"
            "  MACE < 5%   → Risco BAIXO\n"
            "  MACE 5–10%  → Risco INTERMEDIÁRIO\n"
            "  MACE > 10%  → Risco ALTO\n\n"
            "Na prática: VSG-CRI ≥ 5 já indica risco intermediário-alto. "
            "Pacientes com score ≥ 7 devem receber avaliação cardiológica formal antes de cirurgia eletiva.\n\n"
            "Referência: Diretriz SBC 2024 Tabela 7."
        )
    },
    # -----------------------------------------------------------------------
    # Condições ativas
    # -----------------------------------------------------------------------
    {
        "page": 5,
        "text": (
            "Condições Cardiovasculares Ativas — Tabela 2 (Diretriz SBC 2024)\n\n"
            "Se QUALQUER UMA das condições abaixo estiver presente, a cirurgia eletiva deve ser "
            "ADIADA para avaliação e tratamento cardiovascular:\n\n"
            "1. Síndrome coronariana aguda (IAM recente, angina instável)\n"
            "2. Doenças instáveis da aorta torácica\n"
            "3. Edema agudo dos pulmões\n"
            "4. Choque cardiogênico\n"
            "5. Insuficiência cardíaca classe funcional III ou IV (NYHA)\n"
            "6. Angina classe funcional CCS III ou IV\n"
            "7. Bradiarritmias ou taquiarritmias graves (BAVT, TV)\n"
            "8. Hipertensão arterial não controlada (PA > 180 × 110 mmHg)\n"
            "9. Fibrilação atrial com alta resposta ventricular (FC > 120 bpm)\n"
            "10. Hipertensão arterial pulmonar sintomática\n"
            "11. Estenose aórtica ou mitral importante sintomática\n\n"
            "Presença de condições ativas classifica automaticamente o paciente como RISCO ALTO, "
            "independentemente do score RCRI ou VSG-CRI.\n\n"
            "Referência: Diretriz SBC 2024, Tabela 2."
        )
    },
    # -----------------------------------------------------------------------
    # Risco cirúrgico
    # -----------------------------------------------------------------------
    {
        "page": 6,
        "text": (
            "Classificação do Risco Cirúrgico Intrínseco (Diretriz SBC 2024)\n\n"
            "O tipo de cirurgia tem risco cardíaco próprio, independente do paciente:\n\n"
            "BAIXO RISCO (MACE < 1%):\n"
            "  Superficial, mama, oftalmológica, odontológica, tireoide, carótida assintomática "
            "eletiva, ortopédica menor (joelho/quadril), urológica endoscópica.\n\n"
            "RISCO INTERMEDIÁRIO (MACE 1–5%):\n"
            "  Intraperitoneal, intratorácica, ortopédica maior (coluna, quadril aberto), "
            "cabeça e pescoço, próstata aberta, neurológica/ortopédica.\n\n"
            "ALTO RISCO (MACE > 5%):\n"
            "  Aórtica e grandes vasos, vascular periférica, duodenal-pancreática, "
            "ressecção hepática, esofagectomia, pneumonectomia.\n\n"
            "Regra especial: cirurgias de BAIXO risco intrínseco → prosseguir sem necessidade "
            "de investigação cardíaca adicional (exceto se condições ativas presentes).\n\n"
            "Referência: Diretriz SBC 2024, Tabela 3."
        )
    },
    # -----------------------------------------------------------------------
    # Capacidade funcional / METs
    # -----------------------------------------------------------------------
    {
        "page": 7,
        "text": (
            "Capacidade Funcional Perioperatória — Escala de METs\n\n"
            "A capacidade funcional é medida em Equivalentes Metabólicos (METs). "
            "O limiar de 4 METs é o ponto crítico: abaixo dele, o risco perioperatório é maior.\n\n"
            "REFERÊNCIA DE ATIVIDADES (METs aproximados):\n"
            "  1,0 MET  — Nenhuma atividade / acamado\n"
            "  2,7 METs — Trabalhos leves em casa (juntar lixo, lavar louça)\n"
            "  2,75 METs — Cuidar de si mesmo / caminhar uma quadra no plano\n"
            "  3,5 METs — Trabalhos moderados em casa (aspirador, varrer, carregar mantimentos)\n"
            "  4,5 METs — Trabalhos no jardim/quintal (rastelo, cortar grama)\n"
            "  5,25 METs — Atividade sexual\n"
            "  5,5 METs — Subir um lance de escadas ou caminhar em subida\n"
            "  6,0 METs — Atividades recreacionais moderadas (boliche, dança, tênis em dupla)\n"
            "  7,5 METs — Esportes (natação, tênis individual, futebol)\n"
            "  8,0 METs — Trabalhos pesados em casa / correr distância curta\n\n"
            "INTERPRETAÇÃO CLÍNICA:\n"
            "  METs ≥ 4 → Capacidade funcional ADEQUADA — menor risco perioperatório\n"
            "  METs < 4 → Capacidade funcional REDUZIDA — fator de risco independente; "
            "considerar teste funcional antes de cirurgia de risco intermediário/alto.\n\n"
            "Referência: Diretriz SBC 2024; AHA/ACC perioperative guidelines."
        )
    },
    # -----------------------------------------------------------------------
    # AAS
    # -----------------------------------------------------------------------
    {
        "page": 8,
        "text": (
            "Manejo Perioperatório do AAS (Ácido Acetilsalicílico)\n\n"
            "A conduta depende diretamente da INDICAÇÃO do AAS:\n\n"
            "PREVENÇÃO PRIMÁRIA (sem evento cardiovascular prévio):\n"
            "  → Suspender AAS 7 dias antes da cirurgia.\n"
            "  Justificativa: benefício marginal versus risco de sangramento.\n\n"
            "PREVENÇÃO SECUNDÁRIA (IAM, AVC, DAC, doença periférica estabelecida):\n"
            "  → MANTER AAS na maioria das cirurgias (risco trombótico supera risco hemorrágico).\n"
            "  EXCEÇÕES — suspender 7 dias antes nas cirurgias:\n"
            "    • Neurocirurgia (intracraniana)\n"
            "    • RTU de próstata (ressecção transuretral)\n"
            "    • Cirurgia de retina (oftalmológica posterior)\n"
            "  Nessas cirurgias o risco de sangramento em local crítico é inaceitável.\n\n"
            "RESUMO:\n"
            "  Prevenção primária → sempre suspender 7 dias antes\n"
            "  Prevenção secundária → manter, exceto neuro/RTU próstata/retina\n\n"
            "Referência: Diretriz SBC 2024, Tabela 8."
        )
    },
    # -----------------------------------------------------------------------
    # Antiplaquetários P2Y12
    # -----------------------------------------------------------------------
    {
        "page": 9,
        "text": (
            "Manejo Perioperatório de Antiplaquetários P2Y12\n"
            "(Clopidogrel, Ticagrelor, Prasugrel)\n\n"
            "CLOPIDOGREL:\n"
            "  → Suspender 5 dias antes da cirurgia.\n"
            "  Pode manter em monoterapia apenas em procedimentos de baixo risco de sangramento.\n\n"
            "TICAGRELOR:\n"
            "  → Suspender 5 dias antes da cirurgia.\n"
            "  Meia-vida mais curta, mas efeito intenso; 5 dias é o padrão seguro.\n\n"
            "PRASUGREL:\n"
            "  → Suspender 7 dias antes da cirurgia.\n"
            "  Inibição plaquetária mais potente e irreversível; exige 7 dias.\n\n"
            "CONSIDERAÇÃO ESPECIAL — Dupla antiagregação (DAA) após stent coronariano:\n"
            "  Se o paciente tem stent recente (< 3 meses stent metálico; < 6 meses stent farmacológico), "
            "a suspensão precoce aumenta risco de trombose do stent. "
            "Adiar cirurgia eletiva sempre que possível. Se urgente, discutir com cardiologista.\n\n"
            "Referência: Diretriz SBC 2024; ESC 2022."
        )
    },
    # -----------------------------------------------------------------------
    # Varfarina — FA
    # -----------------------------------------------------------------------
    {
        "page": 10,
        "text": (
            "Manejo Perioperatório da Varfarina — Indicação: Fibrilação Atrial (FA)\n\n"
            "A decisão sobre ponte com heparina baseia-se no score CHA₂DS₂-VASc:\n\n"
            "CHA₂DS₂-VASc ≥ 5 OU AVC/AIT nos últimos 3 meses:\n"
            "  → Suspender varfarina 5 dias antes + PONTE COM HEPARINA de baixo peso molecular.\n"
            "  (Risco tromboembólico muito alto — ponte obrigatória)\n\n"
            "CHA₂DS₂-VASc 3–4:\n"
            "  → Suspender varfarina 5 dias antes + CONSIDERAR ponte com heparina.\n"
            "  (Risco intermediário — decisão individualizada)\n\n"
            "CHA₂DS₂-VASc 0–2 sem AVC/AIT recente:\n"
            "  → Suspender varfarina 5 dias antes SEM ponte.\n"
            "  (Risco baixo — ponte não indicada e aumenta sangramento)\n\n"
            "Referência: Diretriz SBC 2024, Tabela 9; Douketis et al. NEJM 2015 (BRIDGE trial)."
        )
    },
    # -----------------------------------------------------------------------
    # Varfarina — TEV
    # -----------------------------------------------------------------------
    {
        "page": 11,
        "text": (
            "Manejo Perioperatório da Varfarina — Indicação: Tromboembolismo Venoso (TEV)\n\n"
            "A decisão sobre ponte com heparina depende do TEMPO desde o último episódio de TEV:\n\n"
            "TEV RECENTE (< 3 meses):\n"
            "  → Suspender varfarina + PONTE COM HEPARINA obrigatória.\n"
            "  (Risco muito alto de recorrência — cirurgia eletiva deve ser adiada se possível)\n\n"
            "TEV ENTRE 3–12 MESES:\n"
            "  → CONSIDERAR ponte com heparina, especialmente se:\n"
            "    • Trombofilia leve (fator V Leiden heterozigoto, etc.)\n"
            "    • Neoplasia ativa (câncer)\n\n"
            "TEV > 12 MESES:\n"
            "  → Suspender varfarina SEM ponte.\n"
            "  (Risco baixo de recorrência precoce)\n\n"
            "Referência: Diretriz SBC 2024; Thrombosis guidelines."
        )
    },
    # -----------------------------------------------------------------------
    # Varfarina — Prótese valvar e reumática
    # -----------------------------------------------------------------------
    {
        "page": 12,
        "text": (
            "Manejo Perioperatório da Varfarina — Prótese Valvar Mecânica e Doença Valvar Reumática\n\n"
            "PRÓTESE VALVAR MECÂNICA:\n"
            "  → Suspender varfarina + PONTE COM HEPARINA de baixo peso molecular SEMPRE.\n"
            "  Justificativa: risco muito alto de trombose de prótese mecânica sem anticoagulação.\n"
            "  Próteses biológicas geralmente não necessitam de ponte.\n\n"
            "DOENÇA VALVAR REUMÁTICA:\n"
            "  → Suspender varfarina + PONTE COM HEPARINA SEMPRE.\n"
            "  (Estenose mitral reumática com FA tem risco trombótico especialmente elevado)\n\n"
            "PROTOCOLO GERAL PARA PONTE COM HEPARINA:\n"
            "  1. Suspender varfarina 5 dias antes da cirurgia\n"
            "  2. Iniciar HBPM terapêutica 3 dias antes\n"
            "  3. Última dose de HBPM 24h antes da cirurgia\n"
            "  4. Reiniciar anticoagulação oral 12–24h após hemostasia segura\n\n"
            "Referência: Diretriz SBC 2024; ESC Valvular Heart Disease Guidelines."
        )
    },
    # -----------------------------------------------------------------------
    # Exames recomendados
    # -----------------------------------------------------------------------
    {
        "page": 13,
        "text": (
            "Recomendação de Exames Pré-Operatórios — Lógica da Calculadora\n\n"
            "A calculadora recomenda exames com base nos seguintes critérios:\n\n"
            "ECG DE 12 DERIVAÇÕES:\n"
            "  → Indicado se: cirurgia de risco não-baixo OU score > 0.\n\n"
            "ECOCARDIOGRAMA TRANSTORÁCICO:\n"
            "  → Indicado se: IC conhecida/suspeita, doença valvar conhecida/suspeita, "
            "condições cardiovasculares ativas, EAP ou choque cardiogênico.\n\n"
            "TESTE FUNCIONAL (ergometria / cintilografia / eco de estresse):\n"
            "  → Indicado se: METs < 4 + cirurgia de risco intermediário/alto + "
            "score intermediário/alto (RCRI ≥ 2 ou VSG ≥ 5).\n\n"
            "HEMOGRAMA COMPLETO:\n"
            "  → Indicado em cirurgias de risco intermediário ou alto.\n\n"
            "COAGULOGRAMA (INR, TAP, TTPa):\n"
            "  → Indicado se o paciente usa varfarina.\n\n"
            "FUNÇÃO RENAL (creatinina, ureia):\n"
            "  → Indicado se: score > 0 ou cirurgia de alto risco.\n\n"
            "BNP ou NT-proBNP:\n"
            "  → Indicado se: risco alto ou IC conhecida.\n\n"
            "GLICEMIA / HbA1c:\n"
            "  → Indicado se: diabetes com insulinoterapia (RCRI ou VSG).\n\n"
            "Referência: Diretriz SBC 2024, Tabelas 11–13."
        )
    },
    # -----------------------------------------------------------------------
    # Comorbidades e fatores indiretos
    # -----------------------------------------------------------------------
    {
        "page": 14,
        "text": (
            "Comorbidades e Fatores Indiretos que Afetam o Risco Perioperatório\n\n"
            "Além dos critérios formais do RCRI e VSG-CRI, as seguintes condições "
            "influenciam o manejo e as recomendações:\n\n"
            "OBESIDADE:\n"
            "  Aumenta risco de dificuldade ventilatória, TEV, infecção de ferida e "
            "hipoxemia pós-operatória. Não é critério do RCRI, mas é registrado como fator de risco.\n\n"
            "INSUFICIÊNCIA CARDÍACA (IC) CONHECIDA/SUSPEITA:\n"
            "  → Indica ecocardiograma. → Recomenda otimização do tratamento antes da cirurgia.\n"
            "  Critério do RCRI (ICC descompensada). NYHA III/IV = condição ativa (cirurgia adiada).\n\n"
            "DOENÇA VALVAR CONHECIDA/SUSPEITA:\n"
            "  → Indica ecocardiograma. Estenose aórtica/mitral grave sintomática = condição ativa.\n\n"
            "DOENÇA ARTERIAL CORONARIANA (DAC) CONHECIDA/SUSPEITA:\n"
            "  → Considerar controle da DAC. Teste funcional se indicado.\n"
            "  Critério do RCRI (doença isquêmica cardíaca ativa).\n\n"
            "TABAGISMO (VSG-CRI +1):\n"
            "  Aumenta risco pulmonar pós-operatório, cicatrização e eventos CV.\n\n"
            "DPOC (VSG-CRI +2 em vasculares):\n"
            "  Aumenta risco respiratório e cardiovascular. Otimizar broncodilatação antes da cirurgia.\n\n"
            "Referência: Diretriz SBC 2024, seções 3–5."
        )
    },
    # -----------------------------------------------------------------------
    # Fluxo diagnóstico geral
    # -----------------------------------------------------------------------
    {
        "page": 15,
        "text": (
            "Fluxo de Avaliação Cardiovascular Perioperatória — Algoritmo Geral (SBC 2024)\n\n"
            "PASSO 1: Urgência cirúrgica?\n"
            "  Se emergência → cirurgia imediata com monitorização (não há tempo para investigação).\n\n"
            "PASSO 2: Condições cardiovasculares ativas? (Tabela 2)\n"
            "  Se SIM → adiar cirurgia eletiva, tratar a condição primeiro.\n\n"
            "PASSO 3: Risco cirúrgico intrínseco?\n"
            "  Se BAIXO (< 1%) → prosseguir sem investigação cardíaca adicional.\n\n"
            "PASSO 4: Capacidade funcional?\n"
            "  Se METs ≥ 4 (escada, jardinagem) → para a maioria das cirurgias, prosseguir.\n\n"
            "PASSO 5: Calcular RCRI (não vascular) ou VSG-CRI (vascular).\n"
            "  Score baixo + risco cirúrgico baixo/intermediário → prosseguir.\n"
            "  Score alto ou risco cirúrgico alto → considerar investigação adicional.\n\n"
            "PASSO 6: Para cirurgias vasculares com alto risco VSG-CRI:\n"
            "  Avaliar se revascularização pré-operatória muda o prognóstico.\n\n"
            "Referência: Diretriz SBC 2024, Algoritmo 1 (Figura 2)."
        )
    },
    # -----------------------------------------------------------------------
    # Recomendações finais por classe de risco
    # -----------------------------------------------------------------------
    {
        "page": 16,
        "text": (
            "Recomendações Finais por Classe de Risco — Calculadora CardioRisk\n\n"
            "RISCO BAIXO (MACE < 5%):\n"
            "  → Prosseguir com cirurgia. Monitorização padrão perioperatória é suficiente.\n"
            "  → Cirurgia de baixo risco intrínseco: risco cardíaco < 1%.\n\n"
            "RISCO INTERMEDIÁRIO (MACE 5–10%):\n"
            "  → Considerar consulta cardiológica. Solicitar ECG pré-operatório.\n"
            "  → Considerar dosagem de BNP/NT-proBNP.\n"
            "  → Avaliar necessidade de teste funcional se METs < 4.\n\n"
            "RISCO ALTO (MACE > 10%) ou CONDIÇÕES ATIVAS:\n"
            "  → Avaliação cardiológica formal RECOMENDADA antes da cirurgia eletiva.\n"
            "  → Discutir relação risco/benefício com equipe cirúrgica e com o paciente.\n"
            "  → Considerar monitorização invasiva e cuidados intensivos pós-operatórios.\n"
            "  → Score ≥ 3: considerar betabloqueadores e estatinas conforme indicação.\n"
            "  → Avaliar profilaxia antitrombótica.\n\n"
            "CAPACIDADE FUNCIONAL REDUZIDA (METs < 4) em qualquer classe de risco:\n"
            "  → Considerar teste funcional (ergometria, cintilografia, eco de estresse) "
            "antes de cirurgia eletiva de risco intermediário ou alto.\n\n"
            "Referência: Diretriz SBC 2024; ESC/ESA Guidelines 2022."
        )
    },
]

if __name__ == "__main__":
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"✔ Gerado: {OUT}  ({len(chunks)} chunks)")
    print("\nConteúdo gerado:")
    for c in chunks:
        titulo = c["text"].split("\n")[0]
        print(f"  Chunk {c['page']:>2}: {titulo[:70]}")
