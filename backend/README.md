# CardioRisk Periop — Backend API

API em FastAPI para estratificação do risco cardiovascular perioperatório conforme a
Diretriz SBC 2024. Ferramenta acadêmica, não destinada a uso assistencial.

## Executar

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Documentação interativa: http://localhost:8000/docs

Variáveis de ambiente (opcionais):

| Variável | Efeito |
|----------|--------|
| `CORS_ALLOW_ORIGINS` | Origens permitidas, separadas por vírgula (padrão: localhost:3000, localhost:5173 e o site de produção) |
| `CARDIORISK_ENABLE_NER` | `false` desativa o NER do Hugging Face no `/nlp/analyze` (recomendado com pouca RAM) |
| `CARDIORISK_NER_MODELS` | Modelos de NER, separados por vírgula (padrão: `pucpr/clinicalnerpt-disorder,pucpr/clinicalnerpt-chemical,pucpr/clinicalnerpt-procedure`) |
| `CARDIORISK_NER_MODEL` | Um único modelo; mantida por compatibilidade e usada só se `CARDIORISK_NER_MODELS` não estiver definida |
| `HF_TOKEN` | Token opcional do Hugging Face |
| `CARDIORISK_SUPPRESS_MODEL_WARNINGS` | `true` oculta avisos de requisição não autenticada ao Hub |

## Texto livre: regras e conferência com NER

O `/nlp/analyze` preenche os campos **somente com regras** (listas de termos e expressões
regulares). Os modelos de NER não preenchem nada: servem de conferência das regras. Quando um
modelo encontra um termo clínico que nenhuma regra reconheceu (por exemplo "coronariopata" ou
"ICFEr"), a resposta traz esse termo em `ner_review.nao_reconhecidos` e a tela pede que o médico
confira o campo manualmente.

- `ner_review.nao_reconhecidos`: entidades com score ≥ 0,60, com mais de 2 letras e sem
  duplicatas, cujo texto não coincide com nenhum termo reconhecido pelas regras. Cada item traz
  `text`, `label`, `score` e `negado` (o termo vem depois de "nega", "sem" ou "não" na frase).
- `ner_review.confirmados`: entidades que coincidem com algo que as regras reconheceram, com os
  mesmos campos. Um item com `negado: true` indica um campo que pode ter sido marcado
  indevidamente (as regras não tratam negação em todos os campos).
- `entities`: tudo o que os modelos devolveram (`text`, `label`, `score`, `start`, `end`, `model`).

Modelos padrão (BioBERTpt ajustado com o SemClinBr, um rótulo cada): `clinicalnerpt-disorder`
(doenças, sinais e sintomas), `clinicalnerpt-chemical` (medicamentos) e `clinicalnerpt-procedure`
(procedimentos).

O NER exige `transformers` e `torch` (`pip install -r requirements-ner.txt`). Sem essas
bibliotecas, ou com `CARDIORISK_ENABLE_NER=false`, o `/nlp/analyze` funciona apenas com as regras:
o preenchimento é o mesmo e `ner_review` vem vazio.

**Memória:** com os três modelos carregados o processo ocupou cerca de 1,5 GB de RAM (medição
em CPU com `python avaliar_pln.py --ner`; só as regras ocupam cerca de 20 MB). Por isso o
`requirements.txt` do servidor não inclui essas bibliotecas e, em produção, o NER só roda em um
servidor com pelo menos 2 GB de memória. A análise de um texto leva cerca de 0,13 s com os
modelos e 2 ms sem eles.

Avaliação com 60 casos clínicos fictícios: `python avaliar_pln.py` (só regras) e
`python avaliar_pln.py --ner` (conferência com os modelos).

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET/HEAD | `/` | Informações da API |
| GET/HEAD | `/health` | Verificação de saúde |
| POST | `/calculate` | Calcula pontuação, classe de risco, recomendações, exames e orientações de medicação |
| POST | `/nlp/analyze` | Extrai campos da calculadora de um texto clínico livre (experimental) |

O `/calculate` **não retorna probabilidade de MACE**: a diretriz usa classificação
semiquantitativa (baixo, intermediário e alto).

Exemplo de retorno (campos principais): `indice_risco` (`rcri` ou `vsg`), `pontuacao`,
`classe_risco`, `rotulo_risco`, `condicoes_ativas`, `criterios_atingidos`,
`recomendacoes`, `exames_recomendados`, `orientacoes_medicacao`.

## Regras de cálculo

- **Índice:** VSG-CRI se a cirurgia é vascular (`eh_vascular`, `surgery_is_vascular` ou
  tipo de cirurgia contendo "vascular"); caso contrário, RCRI.
- **RCRI** (Tabela 5): 0–1 baixo, 2 intermediário, 3–6 alto.
- **VSG-CRI** (Tabelas 6 e 7): idade 60–69 (+2), 70–79 (+3), ≥ 80 (+4); DAC, IC, DPOC e
  creatinina > 1,8 mg/dL (+2 cada); tabagismo, diabetes com insulina e betabloqueador
  crônico (+1 cada); revascularização miocárdica prévia (−1). Classes: 0–4 baixo,
  5–6 intermediário, ≥ 7 alto.
- **Ajustes:** cirurgia de baixo risco sem condição cardíaca ativa e com classe não alta
  resulta em risco baixo; qualquer condição cardíaca ativa resulta em risco alto.
- **Otimização farmacológica:** recomendada com pontuação ≥ 3 (RCRI) ou ≥ 7 (VSG-CRI).

## Estrutura

```
backend/
├── main.py                  # Rotas FastAPI e modelo de entrada (DadosPaciente)
├── core/
│   ├── calculator.py        # pontuar_rcri, pontuar_vsg, classes de risco,
│   │                        # recomendações, exames e orientações de medicação
│   └── clinical_nlp.py      # Extração de campos a partir de texto livre (regras) e
│                            # conferência das regras com NER (opcional)
├── tests/                   # 124 testes (pytest)
├── avaliar_pln.py           # Avaliação com 60 casos fictícios (--ner liga os modelos)
├── requirements.txt         # fastapi, uvicorn, pydantic
├── requirements-ner.txt     # transformers, torch, sentencepiece (NER, opcional)
└── Procfile                 # uvicorn main:app
```

## Limitações

- Há 124 testes automatizados (`python -m pytest tests -v`): 53 do motor de cálculo e 71 do
  módulo de texto livre, dos quais 18 da conferência com NER (com um modelo falso, sem baixar
  nada). As regras de exames não têm cobertura sistemática.
- A conferência com NER gera avisos também em textos que as regras preencheram corretamente
  (termos sem campo na calculadora, como "hipertenso"); ela orienta a revisão, não a substitui.
- Sem validação clínica. Não substitui o julgamento médico.
- Dados do paciente não são armazenados pela API, mas o texto enviado ao
  `/nlp/analyze` pode conter dados sensíveis (LGPD): não o use com dados reais sem
  avaliação de segurança.

## Referências

- Gualandro DM et al. Diretriz de Avaliação Cardiovascular Perioperatória da SBC – 2024.
  Arq Bras Cardiol. 2024;121(9):e20240590.
- Lee TH et al. Circulation. 1999;100(10):1043-1049.
- Bertges DJ et al. J Vasc Surg. 2010;52(3):674-683.
