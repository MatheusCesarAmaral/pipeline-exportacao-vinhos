# pipeline-exportacao-vinhos

Pipeline de engenharia de dados para análise de exportação de vinhos brasileiros,
desde ingestão de dados brutos até consumo via dashboard.

## Arquitetura
O pipeline é composto pelas seguintes camadas:
- Ingestão (CSV e API)
- Raw
- Trusted
- Analytics (modelo estrela)
- Consumo (Streamlit)

## Stack
- Python
- Pandas
- SQL
- Streamlit

## Consumo
Os dados da camada Analytics são consumidos por um dashboard interativo em Streamlit.