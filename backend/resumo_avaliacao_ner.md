# Avaliação da conferência com o NER – CardioRisk Periop

Casos: 60 textos clínicos fictícios, os mesmos de `python avaliar_pln.py`. As regras continuam sendo as únicas que preenchem campos; os modelos só geram avisos (`ner_review`).

Modelos: `pucpr/clinicalnerpt-disorder`, `pucpr/clinicalnerpt-chemical`, `pucpr/clinicalnerpt-procedure`. Score mínimo: 0,60.

## O preenchimento não muda

- Casos com `autofill` idêntico com e sem os modelos: 60/60 (100,0%)

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

- Tempo médio por texto, só regras: 1,77 ms
- Tempo médio por texto, regras + 3 modelos (CPU): 126,5 ms
- Carga dos modelos (já baixados): 4,9 s (clinicalnerpt-disorder 1,9 s; clinicalnerpt-chemical 1,4 s; clinicalnerpt-procedure 1,6 s)
- Memória de um processo Python só com as regras, sem transformers/torch carregados (sem contar o servidor web): 20 MB
- Memória deste processo antes de carregar os modelos (transformers e torch importados): 403 MB
- Memória com os 3 modelos carregados, após os 60 casos: 1488 MB (pico: 1489 MB)
