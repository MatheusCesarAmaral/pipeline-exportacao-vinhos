import pandas as pd
from pathlib import Path


def transform_comercio(raw_path: Path, trusted_path: Path) -> None:
    """
    Transforma os dados de comércio (valor em US$) da Embrapa:
    - padroniza colunas
    - normaliza anos (colunas -> linhas)
    - garante tipos corretos
    - salva na camada TRUSTED
    """

    print(f"Lendo dados RAW: {raw_path}")
    df = pd.read_csv(raw_path)

    # =========================
    # PADRONIZAÇÃO DE COLUNAS
    # =========================
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    # Primeira coluna representa o país
    col_pais = df.columns[0]

    # =========================
    # NORMALIZAÇÃO (UNPIVOT)
    # =========================
    df_long = df.melt(
        id_vars=col_pais,
        var_name="ano",
        value_name="valor_usd"
    )

    # Renomear coluna de país
    df_long = df_long.rename(columns={col_pais: "pais_destino"})

    # =========================
    # CONVERSÃO DE TIPOS
    # =========================
    df_long["ano"] = pd.to_numeric(df_long["ano"], errors="coerce")
    df_long["valor_usd"] = pd.to_numeric(df_long["valor_usd"], errors="coerce")

    # Remover registros inválidos
    df_long = df_long.dropna(subset=["ano", "pais_destino"])

    # Ano é dimensão temporal → manter como inteiro
    df_long["ano"] = df_long["ano"].astype(int)

    # =========================
    # SALVAR CAMADA TRUSTED
    # =========================
    print(f"Salvando dados TRUSTED em: {trusted_path}")
    trusted_path.parent.mkdir(parents=True, exist_ok=True)
    df_long.to_csv(trusted_path, index=False)

    print("Transformação de comércio concluída com sucesso.\n")


def main():
    raw_file = Path("data/raw/comercio_raw.csv")
    trusted_file = Path("data/trusted/comercio_trusted.csv")

    transform_comercio(raw_file, trusted_file)


if __name__ == "__main__":
    main()
