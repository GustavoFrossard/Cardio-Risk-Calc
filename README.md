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
  anticoagulantes, além de relatório em PDF (gerado no navegador na versão web).
- Módulo experimental que extrai campos do formulário a partir de texto clínico livre
  (`/nlp/analyze`).

## Estrutura

```
cardiorisk/
├── backend/     # API FastAPI (cálculo dos escores, recomendações, NLP)
├── frontend/    # Aplicação web em React + Vite
├── mobile/      # Aplicativo React Native (Expo)
└── diagramas/   # Arquitetura, classes e casos de uso (PlantUML)
```

## Como executar

Backend (Python 3.11+):

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Web:

```bash
cd frontend
cp .env.example .env.local   # defina VITE_API_URL (ex.: http://localhost:8000)
npm install
npm run dev
```

Mobile:

```bash
cd mobile
npm install
npm start
```

## Limitações conhecidas

- Há 51 testes automatizados do motor de cálculo (`backend/tests`); as regras de exames e o módulo de texto livre não têm cobertura sistemática.
- Não houve validação clínica, de usabilidade nem de acurácia.
- O módulo de texto livre não foi verificado e envia texto clínico ao servidor; avalie
  implicações da LGPD antes de qualquer uso com dados reais.

## Referências

- Gualandro DM et al. Diretriz de Avaliação Cardiovascular Perioperatória da SBC – 2024.
  Arq Bras Cardiol. 2024;121(9):e20240590.
- Lee TH et al. Circulation. 1999;100(10):1043-1049 (RCRI).
- Bertges DJ et al. J Vasc Surg. 2010;52(3):674-683 (VSG-CRI).
