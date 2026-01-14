import streamlit as st
import pandas as pd
from pathlib import Path
import altair as alt

# ======================
# CONFIGURAÇÃO INICIAL
# ======================
st.set_page_config(
    page_title="Exportação de Vinhos Brasileiros",
    layout="wide"
)

st.title("🍷 Exportação de Vinhos Brasileiros")
st.markdown("Dashboard analítico baseado na Camada Analytics")

# ======================
# CAMINHOS
# ======================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "analytics"

# ======================
# CARREGAR DADOS
# ======================
@st.cache_data
def load_data():
    dim_pais = pd.read_csv(DATA_DIR / "dim_pais.csv")
    dim_tempo = pd.read_csv(DATA_DIR / "dim_tempo.csv")
    fato = pd.read_csv(DATA_DIR / "fato_exportacao.csv")
    return dim_pais, dim_tempo, fato

dim_pais, dim_tempo, fato = load_data()

# ======================
# ENRIQUECER FATO
# ======================
df = (
    fato
    .merge(dim_pais, on="id_pais", how="left")
    .merge(dim_tempo, on="id_tempo", how="left")
)

# Garantir ano como inteiro
df["ano"] = df["ano"].astype(int)

# ======================
# FILTROS
# ======================
st.sidebar.header("Filtros")

anos = sorted(df["ano"].unique())
anos_selecionados = st.sidebar.multiselect(
    "Ano",
    options=anos,
    default=anos
)

paises = sorted(df["pais_destino"].unique())
paises_selecionados = st.sidebar.multiselect(
    "País de destino",
    options=paises,
    default=paises
)

df_filtrado = df[
    (df["ano"].isin(anos_selecionados)) &
    (df["pais_destino"].isin(paises_selecionados))
]

# ======================
# KPIs
# ======================
st.subheader("📌 Indicadores Gerais")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Total Exportado (Litros)",
        f"{df_filtrado['quantidade_litros'].sum():,.0f}"
    )

with col2:
    st.metric(
        "Valor Total (US$)",
        f"{df_filtrado['valor_usd'].sum():,.0f}"
    )

# ======================
# GRÁFICO DE EVOLUÇÃO (ALTAR)
# ======================
st.subheader("📈 Evolução ao longo do tempo")

evolucao = (
    df_filtrado
    .groupby("ano", as_index=False)[["quantidade_litros", "valor_usd"]]
    .sum()
)

chart = (
    alt.Chart(evolucao)
    .transform_fold(
        ["quantidade_litros", "valor_usd"],
        as_=["metrica", "valor"]
    )
    .mark_line(point=True)
    .encode(
        x=alt.X("ano:O", title="Ano"),
        y=alt.Y("valor:Q", title="Valor"),
        color=alt.Color("metrica:N", title="Métrica"),
        tooltip=[
            alt.Tooltip("ano:O", title="Ano"),
            alt.Tooltip("metrica:N", title="Métrica"),
            alt.Tooltip("valor:Q", title="Valor", format=",.0f"),
        ],
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)

# ======================
# RANKING POR PAÍS
# ======================
st.subheader("🌍 Ranking por País")

ranking = (
    df_filtrado
    .groupby("pais_destino", as_index=False)[["quantidade_litros", "valor_usd"]]
    .sum()
    .sort_values("valor_usd", ascending=False)
)

st.dataframe(ranking, use_container_width=True)
