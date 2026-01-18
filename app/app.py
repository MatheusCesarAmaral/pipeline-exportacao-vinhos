import streamlit as st
import pandas as pd
from pathlib import Path
import altair as alt

# ======================
# CONFIGURAÇÃO INICIAL
# ======================
st.set_page_config(
    page_title="Analytics Vinicultura Brasileira",
    layout="wide",
    page_icon="🍷"
)

st.title("🍷 Analytics Vinicultura Brasileira")
st.markdown("Dashboard analítico baseado na Camada Analytics (Dados Embrapa)")

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
    dim_entidade = pd.read_csv(DATA_DIR / "dim_entidade.csv")
    dim_tempo = pd.read_csv(DATA_DIR / "dim_tempo.csv")
    fato = pd.read_csv(DATA_DIR / "fato_consolidada.csv")
    return dim_entidade, dim_tempo, fato

try:
    dim_entidade, dim_tempo, fato = load_data()

    # ENRIQUECER FATO
    df = (
        fato
        .merge(dim_entidade, on="id_entidade", how="left")
        .merge(dim_tempo, on="id_tempo", how="left")
    )
    df["ano"] = df["ano"].astype(int)

    # ======================
    # FILTROS (SIDEBAR)
    # ======================
    st.sidebar.header("🕹️ Filtros")
    visao = st.sidebar.radio("Selecione a Visão:", ["EXPORTAÇÃO", "COMÉRCIO LOCAL"])

    anos = sorted(df["ano"].unique())
    anos_selecionados = st.sidebar.multiselect("Ano", options=anos, default=anos)

    label_filtro = "Países" if visao == "EXPORTAÇÃO" else "Produtos"
    opcoes = sorted(df[df["origem_dado"] == visao]["nome_entidade"].unique())
    selecionados = st.sidebar.multiselect(label_filtro, options=opcoes, default=opcoes)

    # APLICAÇÃO DOS FILTROS
    df_filtrado = df[
        (df["origem_dado"] == visao) &
        (df["ano"].isin(anos_selecionados)) &
        (df["nome_entidade"].isin(selecionados))
    ]

    # ======================
    # KPIs
    # ======================
    st.subheader(f"📌 Indicadores Gerais: {visao}")
    col1, col2 = st.columns(2)

    with col1:
        if visao == "EXPORTAÇÃO":
            valor_total = df_filtrado['valor_usd'].sum()
            st.metric("Faturamento Total (US$)", f"US$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            # Em Comércio, mostramos a quantidade de tipos de produtos filtrados
            total_itens = df_filtrado['nome_entidade'].nunique()
            st.metric("Total de Itens Analisados", f"{total_itens} Produtos")

    with col2:
        litros_total = df_filtrado['quantidade_litros'].sum()
        st.metric("Volume Total (Litros)", f"{litros_total:,.0f} L")

    # ======================
    # GRÁFICO DE EVOLUÇÃO
    # ======================
    st.subheader("📈 Evolução ao longo do tempo")

    evolucao = df_filtrado.groupby("ano", as_index=False)[["quantidade_litros", "valor_usd"]].sum()
    metrics = ["quantidade_litros", "valor_usd"] if visao == "EXPORTAÇÃO" else ["quantidade_litros"]

    chart = (
        alt.Chart(evolucao)
        .transform_fold(metrics, as_=["metrica", "valor"])
        .mark_line(point=True)
        .encode(
            x=alt.X("ano:O", title="Ano"),
            y=alt.Y("valor:Q", title="Total"),
            color=alt.Color("metrica:N", title="Métrica"),
            tooltip=[
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("metrica:N", title="Métrica"),
                alt.Tooltip("valor:Q", title="Total", format=",.0f")
            ],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

    # ======================
    # RANKING
    # ======================
    st.subheader(f"🌍 Ranking por {label_filtro}")

    # Ordenação automática: Valor para Exportação, Volume para Comércio
    sort_col = "valor_usd" if visao == "EXPORTAÇÃO" else "quantidade_litros"
    
    ranking = (
        df_filtrado
        .groupby("nome_entidade", as_index=False)[["quantidade_litros", "valor_usd"]]
        .sum()
        .sort_values(sort_col, ascending=False)
    )

    # Ajuste das colunas da tabela conforme a visão
    ranking_display = ranking.copy()
    if visao == "EXPORTAÇÃO":
        ranking_display["valor_usd"] = ranking_display["valor_usd"].map("US$ {:,.2f}".format)
        ranking_display["quantidade_litros"] = ranking_display["quantidade_litros"].map("{:,.0f}".format)
        ranking_display.columns = ["País", "Volume (L)", "Valor Total (US$)"]
    else:
        # Remove a coluna de valor que estaria zerada
        ranking_display = ranking_display.drop(columns=["valor_usd"])
        ranking_display["quantidade_litros"] = ranking_display["quantidade_litros"].map("{:,.0f}".format)
        ranking_display.columns = ["Produto", "Volume Comercializado (L)"]

    st.dataframe(ranking_display, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")