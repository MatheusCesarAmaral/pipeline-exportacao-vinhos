import pandas as pd
from pathlib import Path


def load_analytics(
    exportacao_path: Path,
    comercio_path: Path,
    output_dir: Path
) -> None:
    print("Lendo dados TRUSTED...")

    df_export = pd.read_csv(exportacao_path)
    df_comercio = pd.read_csv(comercio_path)

    # =========================
    # DIMENSÃO PAÍS
    # =========================
    dim_pais = (
        pd.concat([
            df_export[["pais_destino"]],
            df_comercio[["pais_destino"]]
        ])
        .drop_duplicates()
        .sort_values("pais_destino")
        .reset_index(drop=True)
    )

    dim_pais["id_pais"] = dim_pais.index + 1
    dim_pais = dim_pais[["id_pais", "pais_destino"]]

    # =========================
    # DIMENSÃO TEMPO
    # =========================
    dim_tempo = (
        pd.concat([
            df_export[["ano"]],
            df_comercio[["ano"]]
        ])
        .drop_duplicates()
        .sort_values("ano")
        .reset_index(drop=True)
    )

    dim_tempo["id_tempo"] = dim_tempo.index + 1
    dim_tempo = dim_tempo[["id_tempo", "ano"]]

    # =========================
    # FATO EXPORTAÇÃO
    # =========================
    fato = pd.merge(
        df_export,
        df_comercio,
        on=["pais_destino", "ano"],
        how="inner"
    )

    # Join com dimensões
    fato = fato.merge(dim_pais, on="pais_destino", how="left")
    fato = fato.merge(dim_tempo, on="ano", how="left")

    fato_exportacao = fato[
        [
            "id_pais",
            "id_tempo",
            "quantidade_litros",
            "valor_usd"
        ]
    ]

    # =========================
    # SALVAR CAMADA ANALYTICS
    # =========================
    output_dir.mkdir(parents=True, exist_ok=True)

    dim_pais.to_csv(output_dir / "dim_pais.csv", index=False)
    dim_tempo.to_csv(output_dir / "dim_tempo.csv", index=False)
    fato_exportacao.to_csv(output_dir / "fato_exportacao.csv", index=False)

    print("Camada Analytics criada com sucesso.\n")


def main():
    exportacao_trusted = Path("data/trusted/exportacao_trusted.csv")
    comercio_trusted = Path("data/trusted/comercio_trusted.csv")
    analytics_dir = Path("data/analytics")

    load_analytics(
        exportacao_trusted,
        comercio_trusted,
        analytics_dir
    )


if __name__ == "__main__":
    main()