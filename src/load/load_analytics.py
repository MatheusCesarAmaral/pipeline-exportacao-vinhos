import pandas as pd
from pathlib import Path
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_analytics(exportacao_path: Path, comercio_path: Path, output_dir: Path) -> None:
    """
    Transforma os dados da camada TRUSTED para a camada ANALYTICS (Star Schema).
    Garante a união correta de métricas de Volume (Comércio) e Valor (Exportação).
    """
    try:
        logging.info("Lendo dados da camada TRUSTED...")
        # Lendo em UTF-8 já que padronizamos os scripts de transformação
        df_export = pd.read_csv(exportacao_path, encoding='utf-8')
        df_comercio = pd.read_csv(comercio_path, encoding='utf-8')

        # ==========================================================
        # PADRONIZAÇÃO DE COLUNAS
        # ==========================================================
        # Garante que 'nome_entidade' seja o padrão, não importa a origem
        df_export = df_export.rename(columns={"pais_destino": "nome_entidade"})
        df_comercio = df_comercio.rename(columns={
            "item_comercializado": "nome_entidade", 
            "pais_destino": "nome_entidade"
        })

        df_export["origem_dado"] = "EXPORTAÇÃO"
        df_comercio["origem_dado"] = "COMÉRCIO LOCAL"

        # ==========================================================
        # TRATAMENTO DE MÉTRICAS (Crucial para não gerar NaNs)
        # ==========================================================
        # Garante que as colunas de métricas existam em ambos os DataFrames
        for df in [df_export, df_comercio]:
            if "quantidade_litros" not in df.columns:
                df["quantidade_litros"] = 0
            if "valor_usd" not in df.columns:
                df["valor_usd"] = 0
            
            # Preenche nulos caso algum valor tenha vindo vazio
            df["quantidade_litros"] = df["quantidade_litros"].fillna(0)
            df["valor_usd"] = df["valor_usd"].fillna(0)

        # ==========================================================
        # DIMENSÃO ENTIDADE (País ou Produto)
        # ==========================================================
        dim_entidade = pd.concat([
            df_export[["nome_entidade"]],
            df_comercio[["nome_entidade"]]
        ]).drop_duplicates().sort_values("nome_entidade").reset_index(drop=True)
        
        dim_entidade["id_entidade"] = dim_entidade.index + 1

        # ==========================================================
        # DIMENSÃO TEMPO
        # ==========================================================
        dim_tempo = pd.concat([
            df_export[["ano"]], 
            df_comercio[["ano"]]
        ]).drop_duplicates().sort_values("ano").reset_index(drop=True)
        
        dim_tempo["id_tempo"] = dim_tempo.index + 1

        # ==========================================================
        # FATO CONSOLIDADA (Star Schema)
        # ==========================================================
        # Unificamos apenas as colunas necessárias para a Fato
        cols_base = ["nome_entidade", "ano", "origem_dado", "quantidade_litros", "valor_usd"]
        fato = pd.concat([df_export[cols_base], df_comercio[cols_base]], ignore_index=True)
        
        # Merge para trocar nomes textuais pelos IDs das Dimensões
        fato = fato.merge(dim_entidade, on="nome_entidade", how="left")
        fato = fato.merge(dim_tempo, on="ano", how="left")

        # ==========================================================
        # SALVAMENTO
        # ==========================================================
        output_dir.mkdir(parents=True, exist_ok=True)
        
        dim_entidade.to_csv(output_dir / "dim_entidade.csv", index=False, encoding='utf-8')
        dim_tempo.to_csv(output_dir / "dim_tempo.csv", index=False, encoding='utf-8')
        
        # Salvamos a fato apenas com as chaves estrangeiras (FKs) e métricas
        colunas_fato = ["id_entidade", "id_tempo", "origem_dado", "quantidade_litros", "valor_usd"]
        fato[colunas_fato].to_csv(output_dir / "fato_consolidada.csv", index=False, encoding='utf-8')

        logging.info(f"Sucesso! Camada Analytics gerada em: {output_dir}")

    except Exception as e:
        logging.error(f"Erro crítico no Analytics: {e}")
        raise

def main():
    script_path = Path(__file__).resolve().parent
    project_root = script_path.parent.parent
    
    exportacao_trusted = project_root / "data" / "trusted" / "exportacao_trusted.csv"
    comercio_trusted = project_root / "data" / "trusted" / "comercio_trusted.csv"
    analytics_dir = project_root / "data" / "analytics"

    if not exportacao_trusted.exists() or not comercio_trusted.exists():
        logging.error("Arquivos TRUSTED não encontrados. Rode as transformações primeiro.")
        return

    load_analytics(exportacao_trusted, comercio_trusted, analytics_dir)

if __name__ == "__main__":
    main()