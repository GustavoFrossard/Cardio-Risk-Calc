# Avaliação com os modelos de NER – CardioRisk Periop

Casos: 60 textos clínicos fictícios, os mesmos de `python avaliar_pln.py`. As regras preenchem os campos; uma entidade dos modelos que nenhuma regra usou preenche o campo a que se liga (`ner_autofill`) ou vira aviso (`ner_review`).

Modelos: `pucpr/clinicalnerpt-disorder`, `pucpr/clinicalnerpt-chemical`, `pucpr/clinicalnerpt-procedure`. Score mínimo: 0,60.

## Preenchimento pelo modelo

Entidade que nenhuma regra usou preenche o campo a que se liga pela escrita (trigramas de caracteres contra descrições canônicas de cada campo). Os limiares são escolhidos só nos casos de número ímpar; os casos pares servem de conferência.

| Casos | Configuração | VP | FP | FN | Precisão | Revocação | F1 | Mesma classe de risco | Classe errada | Cirurgia certa | Cirurgia não identificada | Cirurgia errada |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Total (60) | Só regras | 135 | 17 | 29 | 0,89 | 0,82 | 0,85 | 50/60 | 10 | 51 | 9 | 0 |
| Total (60) | Regras + modelo (campos) | 147 | 17 | 17 | 0,90 | 0,90 | 0,90 | 53/60 | 7 | 51 | 9 | 0 |
| Total (60) | Regras + modelo (campos e cirurgia) | 149 | 17 | 15 | 0,90 | 0,91 | 0,90 | 53/60 | 7 | 54 | 5 | 1 |
| Ímpares (30) | Só regras | 83 | 10 | 16 | 0,89 | 0,84 | 0,86 | 20/30 | 10 | 25 | 5 | 0 |
| Ímpares (30) | Regras + modelo (campos) | 91 | 10 | 8 | 0,90 | 0,92 | 0,91 | 23/30 | 7 | 25 | 5 | 0 |
| Ímpares (30) | Regras + modelo (campos e cirurgia) | 92 | 10 | 7 | 0,90 | 0,93 | 0,92 | 24/30 | 6 | 27 | 3 | 0 |
| Pares (30) | Só regras | 52 | 7 | 13 | 0,88 | 0,80 | 0,84 | 30/30 | 0 | 26 | 4 | 0 |
| Pares (30) | Regras + modelo (campos) | 56 | 7 | 9 | 0,89 | 0,86 | 0,88 | 30/30 | 0 | 26 | 4 | 0 |
| Pares (30) | Regras + modelo (campos e cirurgia) | 57 | 7 | 8 | 0,89 | 0,88 | 0,88 | 29/30 | 1 | 27 | 2 | 1 |

### Limiares (escolhidos nos casos ímpares)

- Campos: limiar 0,75 e folga 0,20 (ímpares: 8 ligações certas e 0 erradas; pares, com os mesmos valores: 4 certas e 0 erradas). Em uso em `core/clinical_nlp.py`: 0,75 e 0,20.
- Tipo de cirurgia: limiar 0,45 e folga 0,05 (ímpares: 2 ligações certas e 0 erradas; pares, com os mesmos valores: 1 certas e 1 erradas). Em uso em `core/clinical_nlp.py`: 0,45 e 0,05.

### O que o modelo preencheu

| Caso | Campo | Termo | Resultado |
|---|---|---|---|
| 13 | Betabloqueador crônico | bisoprolol | certo |
| 21 | Diabetes com insulina | DM2 insulino-requerente | certo |
| 21 | Revascularização miocárdica prévia | ATC | certo |
| 22 | Insuficiência cardíaca | ICFEr | certo |
| 22 | Betabloqueador crônico | bisoprolol | certo |
| 23 | Doença arterial coronariana | coronariopata | certo |
| 23 | Revascularização miocárdica prévia | CRM | certo |
| 24 | Doença cerebrovascular (AVC/AIT) | AVE isquêmico | certo |
| 27 | Diabetes com insulina | DM insulinodependente | certo |
| 55 | Diabetes com insulina | DM2 insulinizado | certo |
| 57 | Betabloqueador crônico | propranolol | certo |
| 58 | usa_ticagrelor | Brilinta | sem gabarito |
| 58 | Betabloqueador crônico | bisoprolol | certo |

- Campos preenchidos pelo modelo: 13 (12 certos, 0 errados, 1 sem gabarito)

### Tipo de cirurgia pelo modelo (`CARDIORISK_NER_AUTOFILL_CIRURGIA=true`)

| Caso | Cirurgia ligada | Termo | Esperado | Resultado |
|---|---|---|---|---|
| 6 | intraperitoneal | Hemicolectomia | intraperitoneal | certo |
| 16 | orthopedic_major | Gastroplastia redutora | intraperitoneal | ERRADO |
| 39 | intraperitoneal | Gastrectomia subtotal | intraperitoneal | certo |
| 55 | peripheral_angioplasty | artéria ilíaca | peripheral_angioplasty | certo |

- Cirurgias que o modelo passou a identificar: 3 certas e 1 erradas

## Modelos só na conferência (`CARDIORISK_NER_AUTOFILL=false`)

As seções abaixo medem os avisos quando os modelos não preenchem nada.

- Casos com `autofill` idêntico ao das regras: 60/60 (100,0%)

## Volume

- Entidades devolvidas pelos modelos: 296
- Termos que coincidem com o que as regras reconheceram (`confirmados`): 161
- Avisos (`nao_reconhecidos` sem negação): 100 (média de 1,7 por caso)
- Avisos de termos negados (`nao_reconhecidos` com `negado`): 13
- Casos com pelo menos um aviso (negado ou não): 53/60 (88,3%)

## Campos que as regras deixaram de preencher (falsos negativos)

- Casos com pelo menos um campo de sim/não não preenchido: 23 (29 campos)
- Desses casos, com pelo menos um aviso: 19/23 (82,6%)
- Desses casos, com aviso que aponta o termo de pelo menos um campo que faltou: 16/23 (69,6%)
- Campos que faltaram com aviso apontando o termo: 22/29 (75,9%)
- Casos com cirurgia não identificada pelas regras: 9; com aviso que aponta o procedimento: 8/9 (88,9%)

A conferência "aponta o termo" é automática, por palavras-chave de cada campo (dicionário `PISTAS` em `avaliar_pln.py`); o `avaliacao_ner.csv` lista os campos e os avisos de cada caso.

## Alarmes falsos

- Casos sem nenhum erro das regras: 27
- Desses, com pelo menos um aviso (negado ou não): 25/27 (92,6%)
- Avisos nesses casos: 28 sem negação (média de 1,0 por caso) e 8 de termos negados

## Campos preenchidos indevidamente (falsos positivos) e negação

- Casos com pelo menos um campo de sim/não preenchido a mais: 11 (17 campos)
- Desses casos, com o termo do campo marcado como `negado`: 7/11 (63,6%)
- Campos a mais com o termo marcado como `negado`: 7/17 (41,2%)

## Tempo e memória

- Tempo médio por texto, só regras: 1,52 ms
- Tempo médio por texto, regras + 3 modelos (CPU): 120,4 ms
- Carga dos modelos (já baixados): 4,5 s (clinicalnerpt-disorder 1,8 s; clinicalnerpt-chemical 1,4 s; clinicalnerpt-procedure 1,4 s)
- Memória de um processo Python só com as regras, sem transformers/torch carregados (sem contar o servidor web): 20 MB
- Memória deste processo antes de carregar os modelos (transformers e torch importados): 404 MB
- Memória com os 3 modelos carregados, após os 60 casos: 1493 MB (pico: 1494 MB)
