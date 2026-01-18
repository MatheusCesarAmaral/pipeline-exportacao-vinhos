import pandas as pd
from pathlib import Path
import logging

# adicionando Logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# criando modelo Estrela
def load_analytics(
    exportacao_path: Path,
    comercio_path: Path,
    output_dir: Path
) -> None:
    """
    Transforma os dados da camada TRUSTED para a camada ANALYTICS
    seguindo o modelo dimensional (Star Schema).
    """
    try:
        logging.info("Lendo dados da camada TRUSTED...")
        df_export = pd.read_csv(exportacao_path)
        df_comercio = pd.read_csv(comercio_path)

        # ==========================================================
        # DIMENSÃO PAÍS (Garante IDs únicos para cada país)
        # ==========================================================
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

        # ==========================================================
        # DIMENSÃO TEMPO (Garante IDs únicos para cada ano)
        # ==========================================================
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

        # ==========================================================
        # FATO EXPORTACAO (Une métricas de volume e valor)
        # ==========================================================
        fato = pd.merge(
            df_export,
            df_comercio,
            on=["pais_destino", "ano"],
            how="outer"
        ).fillna(0) 

        # substituímos os nomes (texto) pelos IDs das dimensões
        fato = fato.merge(dim_pais, on="pais_destino", how="left")
        fato = fato.merge(dim_tempo, on="ano", how="left")

        # selecionamos apenas as chaves (FKs) e as métricas
        fato_exportacao = fato[
            [
                "id_pais",
                "id_tempo",
                "quantidade_litros",
                "valor_usd"
            ]
        ]

        # ==========================================================
        # SALVAR CAMADA ANALYTICS
        # ==========================================================
        output_dir.mkdir(parents=True, exist_ok=True)

        dim_pais.to_csv(output_dir / "dim_pais.csv", index=False)
        dim_tempo.to_csv(output_dir / "dim_tempo.csv", index=False)
        fato_exportacao.to_csv(output_dir / "fato_exportacao.csv", index=False)

        logging.info(f"Camada Analytics salva com sucesso em: {output_dir}")

    except Exception as e:
        logging.error(f"Erro ao processar camada Analytics: {e}")
        raise

def main():
    # localização dinâmica baseada na posição deste script
    script_path = Path(__file__).resolve().parent
    project_root = script_path.parent.parent
    
    exportacao_trusted = project_root / "data" / "trusted" / "exportacao_trusted.csv"
    comercio_trusted = project_root / "data" / "trusted" / "comercio_trusted.csv"
    analytics_dir = project_root / "data" / "analytics"

    # verifica se os arquivos de entrada existem
    if not exportacao_trusted.exists() or not comercio_trusted.exists():
        logging.error("Arquivos da camada TRUSTED não encontrados. Rode as transformações primeiro.")
        return

    load_analytics(
        exportacao_trusted,
        comercio_trusted,
        analytics_dir
    )

if __name__ == "__main__":
    main()