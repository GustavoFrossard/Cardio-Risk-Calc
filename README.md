# CardioRisk Periop

Protótipo de apoio à decisão clínica para estratificação do risco cardiovascular
perioperatório, baseado na **Diretriz de Avaliação Cardiovascular Perioperatória da
Sociedade Brasileira de Cardiologia – 2024** (Gualandro et al., Arq Bras Cardiol 2024;
121(9):e20240590).

> **Aviso:** ferramenta acadêmica, em desenvolvimento, não regularizada como dispositivo
> médico (Anvisa RDC 657/2022) e **não destinada a uso assistencial**. Não substitui o
> julgamento clínico.

## O que faz

- Coleta, em quatro etapas, dados do paciente e comorbidades, cirurgia e condições
  cardíacas ativas, critérios do escore aplicável e resultado.
- Seleciona o índice pelo tipo de cirurgia: **VSG-CRI** para cirurgias vasculares
  (a diretriz recomenda para cirurgias vasculares arteriais) e **RCRI** para as demais.
- Classifica o risco em baixo, intermediário ou alto (Tabelas 5 e 7 da diretriz).
  **Não estima probabilidade absoluta de MACE**, pois a diretriz não fornece percentuais.
- Aplica regras adicionais: cirurgia de baixo risco sem condição ativa resulta em risco
  baixo; qualquer condição cardíaca ativa resulta em risco alto.
- Gera recomendações, exames complementares e orientações sobre antiagregantes e
  anticoagulantes, além de relatório em PDF (gerado no navegador).
- Módulo experimental que extrai campos do formulário a partir de texto clínico livre
  (`/nlp/analyze`). Regras cuidam de números, negação e dos termos mais comuns; modelos de NER
  clínico em português (`pucpr/clinicalnerpt-disorder`, `-chemical` e `-procedure`) preenchem o
  campo ligado a um termo que nenhuma regra usou (por exemplo "coronariopata") e avisam o
  médico dos termos sem campo. O que o modelo preenche aparece na tela para conferência. O NER
  é opcional (`backend/requirements-ner.txt`) e precisa de um servidor com cerca de 2 GB de
  memória; sem ele, o módulo funciona só com as regras.

## Estrutura

```
cardiorisk/
├── backend/     # API FastAPI (cálculo dos escores, recomendações, NLP)
├── frontend/    # Aplicação web em React + Vite
└── diagramas/   # Arquitetura, classes e casos de uso (PlantUML)
```

## Como executar

Backend (Python 3.11+):

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend (Node 18+):

```bash
cd frontend
cp .env.example .env.local   # defina VITE_API_URL (ex.: http://localhost:8000)
npm install
npm run dev
```

## Limitações conhecidas

- Há 151 testes automatizados (`backend/tests`): 53 do motor de cálculo e 98 do módulo de texto livre (45 deles dos modelos de NER); as regras de exames não têm cobertura sistemática.
- Não houve validação clínica, de usabilidade nem de acurácia.
- O módulo de texto livre não foi verificado e envia texto clínico ao servidor; avalie
  implicações da LGPD antes de qualquer uso com dados reais.

## Referências

- Gualandro DM et al. Diretriz de Avaliação Cardiovascular Perioperatória da SBC – 2024.
  Arq Bras Cardiol. 2024;121(9):e20240590.
- Lee TH et al. Circulation. 1999;100(10):1043-1049 (RCRI).
- Bertges DJ et al. J Vasc Surg. 2010;52(3):674-683 (VSG-CRI).
