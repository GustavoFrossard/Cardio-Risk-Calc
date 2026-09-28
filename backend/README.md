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
| `CARDIORISK_NER_MODEL` | Modelo NER (padrão: `pucpr/clinicalnerpt-medical`) |
| `HF_TOKEN` | Token opcional do Hugging Face |
| `CARDIORISK_SUPPRESS_MODEL_WARNINGS` | `true` oculta avisos de requisição não autenticada ao Hub |

O NER exige `transformers` e `torch` (`pip install -r requirements-train.txt`). Sem essas
bibliotecas, o `/nlp/analyze` funciona apenas com as regras de extração.

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
│   └── clinical_nlp.py      # Extração de campos a partir de texto livre (NER + regras)
├── requirements.txt         # fastapi, uvicorn, pydantic
├── requirements-train.txt   # transformers, torch, sentencepiece (NER)
└── Procfile                 # uvicorn main:app
```

## Limitações

- Testes automatizados cobrem o motor de cálculo (`python -m pytest tests -v`); exames e texto livre não têm cobertura sistemática.
- Sem validação clínica. Não substitui o julgamento médico.
- Dados do paciente não são armazenados pela API, mas o texto enviado ao
  `/nlp/analyze` pode conter dados sensíveis (LGPD): não o use com dados reais sem
  avaliação de segurança.

## Referências

- Gualandro DM et al. Diretriz de Avaliação Cardiovascular Perioperatória da SBC – 2024.
  Arq Bras Cardiol. 2024;121(9):e20240590.
- Lee TH et al. Circulation. 1999;100(10):1043-1049.
- Bertges DJ et al. J Vasc Surg. 2010;52(3):674-683.
