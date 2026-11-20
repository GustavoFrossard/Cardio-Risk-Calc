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
| `CARDIORISK_NER_AUTOFILL` | `false` deixa os modelos só na conferência (`ner_review`), sem preencher campos (padrão: `true`) |
| `CARDIORISK_NER_AUTOFILL_CIRURGIA` | `true` permite ao modelo preencher o tipo de cirurgia quando as regras não o identificam (padrão: `false`) |
| `HF_TOKEN` | Token opcional do Hugging Face |
| `CARDIORISK_SUPPRESS_MODEL_WARNINGS` | `true` oculta avisos de requisição não autenticada ao Hub |

## Texto livre: regras e modelos de NER

O `/nlp/analyze` preenche os campos em duas etapas:

1. **Regras** (listas de termos e expressões regulares) cuidam de idade, creatinina, METs,
   CHADS₂, negação, eventos recentes, tipo de cirurgia e dos termos mais comuns de cada campo.
   Funcionam sozinhas quando os modelos estão desligados.
2. **Modelos de NER** marcam os termos clínicos do texto. Um termo que nenhuma regra usou é
   comparado, pela escrita (trigramas de caracteres), com descrições canônicas de cada campo. Se a
   semelhança com um campo passa do limiar (0,75) e fica com folga (0,20) sobre o segundo campo
   mais parecido, o campo é preenchido. Exemplos: "coronariopata" marca doença arterial
   coronariana; "ICFEr", insuficiência cardíaca; "bisoprolol", betabloqueador.

Proteções do preenchimento pelo modelo:

- termo negado ("sem coronariopatia") não preenche;
- o que as regras preencheram e o que já veio marcado no formulário não é trocado;
- campos com critério específico exigem o qualificador no próprio termo: diabetes só marca o
  campo de insulina se o termo citar insulina; revascularização só marca revascularização
  miocárdica se o termo citar miocárdio, coronária, CRM ou ATC.

Campos da resposta:

- `autofill`: campos preenchidos pelas regras e pelo modelo.
- `ner_autofill`: o que o modelo preencheu, como lista de `campo`, `valor`, `termo`, `label` e
  `score`. A tela mostra cada item como "preenchido a partir de …" e pede conferência.
- `ner_review.nao_reconhecidos`: entidades com score ≥ 0,60, com mais de 2 letras e sem
  duplicatas, que nenhuma regra usou e que não se ligaram a campo nenhum. Cada item traz `text`,
  `label`, `score` e `negado` (o termo vem depois de "nega", "sem" ou "não" na frase).
- `ner_review.confirmados`: entidades que coincidem com algo que as regras reconheceram ou com um
  campo já marcado. Um item com `negado: true` indica um campo que pode ter sido marcado
  indevidamente (as regras não tratam negação em todos os campos).
- `entities`: tudo o que os modelos devolveram (`text`, `label`, `score`, `start`, `end`, `model`).

Modelos padrão (BioBERTpt ajustado com o SemClinBr, um rótulo cada): `clinicalnerpt-disorder`
(doenças, sinais e sintomas), `clinicalnerpt-chemical` (medicamentos) e `clinicalnerpt-procedure`
(procedimentos).

O tipo de cirurgia só é preenchido pelo modelo com `CARDIORISK_NER_AUTOFILL_CIRURGIA=true`. A
opção vem desligada porque, nos casos de avaliação, a ligação de procedimento a tipo de cirurgia
acerta 3 cirurgias e erra 1, e um tipo errado muda o índice aplicado.

O NER exige `transformers` e `torch` (`pip install -r requirements-ner.txt`). Sem essas
bibliotecas, ou com `CARDIORISK_ENABLE_NER=false`, o `/nlp/analyze` funciona apenas com as regras
e `ner_autofill` e `ner_review` vêm vazios.

**Avaliação** com 60 casos clínicos fictícios (`python avaliar_pln.py` para as regras e
`python avaliar_pln.py --ner` com os modelos). Os limiares da ligação são escolhidos nos casos de
número ímpar e conferidos nos pares:

| Casos | Configuração | Precisão | Revocação | F1 | Mesma classe de risco |
|---|---|---|---|---|---|
| Todos (60) | Só regras | 0,89 | 0,82 | 0,85 | 50/60 |
| Todos (60) | Regras + modelo | 0,90 | 0,90 | 0,90 | 53/60 |
| Pares (30) | Só regras | 0,88 | 0,80 | 0,84 | 30/30 |
| Pares (30) | Regras + modelo | 0,89 | 0,86 | 0,88 | 30/30 |

**Memória:** com os três modelos carregados o processo ocupa cerca de 1,5 GB de RAM (medição em
CPU com `python avaliar_pln.py --ner`; só as regras ocupam cerca de 20 MB). Por isso o
`requirements.txt` do servidor não inclui essas bibliotecas e, em produção, o NER só roda em um
servidor com pelo menos 2 GB de memória. A análise de um texto leva cerca de 0,12 s com os
modelos e 2 ms sem eles.

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
│   └── clinical_nlp.py      # Extração de campos a partir de texto livre: regras e
│                            # modelos de NER (opcionais)
├── tests/                   # 151 testes (pytest)
├── avaliar_pln.py           # Avaliação com 60 casos fictícios (--ner liga os modelos)
├── requirements.txt         # fastapi, uvicorn, pydantic
├── requirements-ner.txt     # transformers, torch, sentencepiece (NER, opcional)
└── Procfile                 # uvicorn main:app
```

## Limitações

- Há 151 testes automatizados (`python -m pytest tests -v`): 53 do motor de cálculo e 98 do
  módulo de texto livre, dos quais 45 dos modelos de NER (com um modelo falso, sem baixar
  nada). As regras de exames não têm cobertura sistemática.
- A ligação de um termo a um campo é por semelhança de escrita: não reconhece sinônimos sem
  letras em comum com as descrições do campo, e foi medida só nos 60 casos fictícios. Todo
  campo preenchido pelo modelo aparece na tela para conferência.
- Termos clínicos sem campo na calculadora (como "hipertenso") geram avisos também em textos
  preenchidos corretamente; os avisos orientam a revisão, não a substituem.
- Sem validação clínica. Não substitui o julgamento médico.
- Dados do paciente não são armazenados pela API, mas o texto enviado ao
  `/nlp/analyze` pode conter dados sensíveis (LGPD): não o use com dados reais sem
  avaliação de segurança.

## Referências

- Gualandro DM et al. Diretriz de Avaliação Cardiovascular Perioperatória da SBC – 2024.
  Arq Bras Cardiol. 2024;121(9):e20240590.
- Lee TH et al. Circulation. 1999;100(10):1043-1049.
- Bertges DJ et al. J Vasc Surg. 2010;52(3):674-683.
