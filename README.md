# Risco de inundação na bacia do Rio Tubarão (SC)

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lucaswsiviero/tubarao-flood/blob/main/notebooks/01_dados_bacia.ipynb)

Projeto experimental de análise de dados hidrometeorológicos históricos para estimar a
frequência e a probabilidade de cheias em Tubarão (SC).

> **Aviso:** projeto experimental. Não substitui os alertas oficiais da Defesa Civil,
> do SGB/CPRM e da ANA.

## Estrutura

```
notebooks/   análises (abrem no Google Colab)
src/tubarao/ código reutilizável (acesso aos dados da ANA etc.)
data/        dados baixados (não versionados; ficam no Google Drive)
```

## Fases

1. **Dados da bacia + análise de frequência** — [`01_dados_bacia`](https://colab.research.google.com/github/lucaswsiviero/tubarao-flood/blob/main/notebooks/01_dados_bacia.ipynb)
2. **Catálogo de cheias + chuva antecedente + primeiro gatilho** — [`02_catalogo_cheias`](https://colab.research.google.com/github/lucaswsiviero/tubarao-flood/blob/main/notebooks/02_catalogo_cheias.ipynb)
3. Chuva em grade (ERA5 / CHIRPS), eventos anteriores a 1985 e índices climáticos
4. Modelo preditivo nível/vazão
5. Rotina agendada e painel público

## Como rodar

Clique no botão **Abrir no Colab** acima e use `Ambiente de execução > Executar tudo`.
O notebook clona este repositório, baixa os dados da ANA e salva o cache no seu Google Drive.

## Notas metodológicas (fase 1)

- Máximos anuais de vazão/cota diária, com ajuste GEV por momentos-L e intervalo de confiança por bootstrap.
- Anos com mudança de referência da régua (cota) são excluídos automaticamente.
- Picos acima do já medido vêm da extrapolação da curva-chave das estações.

- Evento de cheia = alguma estação acima de um tempo de retorno mínimo (padrão 5 anos); eventos com
  dado incompleto ou extrapolado são marcados como suspeitos.
- Limitação conhecida: a série de cota de Tubarão (cidade) termina em 2021 no serviço público da ANA.

## Código

```
src/tubarao/ana.py       acesso ao serviço público da ANA
src/tubarao/dados.py     estações-chave e cache das séries
src/tubarao/extremos.py  GEV por momentos-L, tempo de retorno, bootstrap
```

## Fonte dos dados

ANA — Hidroweb (serviço público `ServiceANA.asmx`, sem login).
