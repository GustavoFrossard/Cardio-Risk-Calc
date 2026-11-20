# Avaliação do preenchimento automático – CardioRisk Periop

Casos avaliados: 60 textos clínicos fictícios (20 de redação direta, 20 com siglas e sinônimos, 20 com negações, tempo e termos ambíguos). Gabarito revisado por um médico. NER desativado (somente regras).

## Campos de sim/não (comorbidades e medicamentos)

| Campo | Presentes | VP | FP | FN | Precisão | Revocação | F1 |
|---|---|---|---|---|---|---|---|
| Diabetes com insulina | 10 | 6 | 2 | 4 | 0,75 | 0,60 | 0,67 |
| Doença cerebrovascular (AVC/AIT) | 7 | 6 | 2 | 1 | 0,75 | 0,86 | 0,80 |
| Doença arterial coronariana | 12 | 10 | 4 | 2 | 0,71 | 0,83 | 0,77 |
| Insuficiência cardíaca | 12 | 9 | 1 | 3 | 0,90 | 0,75 | 0,82 |
| Creatinina > 2,0 mg/dL | 7 | 6 | 1 | 1 | 0,86 | 0,86 | 0,86 |
| Creatinina > 1,8 mg/dL | 10 | 9 | 1 | 1 | 0,90 | 0,90 | 0,90 |
| DPOC | 6 | 6 | 1 | 0 | 0,86 | 1,00 | 0,92 |
| Tabagismo | 7 | 6 | 2 | 1 | 0,75 | 0,86 | 0,80 |
| Betabloqueador crônico | 14 | 10 | 1 | 4 | 0,91 | 0,71 | 0,80 |
| Revascularização miocárdica prévia | 6 | 3 | 2 | 3 | 0,60 | 0,50 | 0,55 |
| Obesidade | 4 | 3 | 0 | 1 | 1,00 | 0,75 | 0,86 |
| Doença valvar conhecida | 8 | 8 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| Valvopatia grave sintomática | 2 | 2 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| Uso de AAS | 19 | 19 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| Uso de clopidogrel | 4 | 4 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| Uso de varfarina | 7 | 7 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| Uso de DOAC | 6 | 6 | 0 | 0 | 1,00 | 1,00 | 1,00 |
| IC classe funcional III/IV (condição ativa) | 1 | 0 | 0 | 1 | – | 0,00 | – |
| Cirurgia de alto risco (critério do RCRI) | 22 | 15 | 0 | 7 | 1,00 | 0,68 | 0,81 |
| TOTAL (micro) | 164 | 135 | 17 | 29 | 0,89 | 0,82 | 0,85 |

F1 macro (média simples dos campos): 0,86

## Por grupo de casos

| Grupo | Precisão | Revocação | F1 | Casos sem nenhum erro | Mesma classe de risco |
|---|---|---|---|---|---|
| A – redação direta | 0,96 | 0,90 | 0,93 | 14/20 (70,0%) | 20/20 (100,0%) |
| B – siglas e sinônimos | 0,88 | 0,76 | 0,81 | 7/20 (35,0%) | 14/20 (70,0%) |
| C – negações e ambiguidades | 0,80 | 0,80 | 0,80 | 6/20 (30,0%) | 16/20 (80,0%) |

## Outros campos

- Idade correta: 58/60 (96,7%)
- METs correto (quando informado em número): 59/59 (100,0%)
- Tipo de cirurgia correto: 51/60 (85,0%); não identificado: 9/60 (15,0%); identificado errado: 0/60 (0,0%)

## Efeito no resultado da calculadora (sem correção manual)

- Casos com preenchimento totalmente correto: 27/60 (45,0%)
- Mesmo índice (RCRI ou VSG-CRI): 56/60 (93,3%)
- Mesma pontuação: 36/60 (60,0%)
- Mesma classe de risco: 50/60 (83,3%)
- Classe de risco menor que a correta (subestimou): 6/60 (10,0%)
- Classe de risco maior que a correta (superestimou): 4/60 (6,7%)
