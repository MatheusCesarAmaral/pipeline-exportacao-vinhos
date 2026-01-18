import pandas as pd
from pathlib import Path
import logging

# adicionando Logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(levelname)s: %(message)s'
)

# transformando o arquivo comercio_raw.csv
def transform_comercio(raw_path: Path, trusted_path: Path) -> None:
    """
    Lê os dados de comércio da Embrapa, realiza o unpivot dos anos,
    trata tipos de dados e salva na camada Trusted.
    """
    try:
        logging.info(f"Lendo dados RAW: {raw_path}")
        
        # O sep=None com engine='python' detecta automaticamente se é vírgula ou ponto e vírgula
        df = pd.read_csv(raw_path, sep=None, engine='python', encoding='utf-8')

        # padronização dos nomes de colunas
        df.columns = [str(col).strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]

        # identificar dinamicamente a coluna de País e as colunas de Anos
        col_pais = df.columns[0]
        cols_anos = [c for c in df.columns if c.replace('_', '').isdigit()] 

        logging.info(f"Colunas de anos detectadas: {len(cols_anos)}")

        # normalização (Unpivot/Melt)
        df_long = df.melt(
            id_vars=[col_pais],
            value_vars=cols_anos,
            var_name="ano",
            value_name="valor_usd"
        )

        # renomear e limpar strings da coluna de destino
        df_long = df_long.rename(columns={col_pais: "pais_destino"})
        df_long["pais_destino"] = df_long["pais_destino"].astype(str).str.strip().str.upper()

        # conversão de tipos robusta
        df_long["valor_usd"] = pd.to_numeric(df_long["valor_usd"], errors="coerce").fillna(0)
        df_long["ano"] = pd.to_numeric(df_long["ano"], errors="coerce")

        # limpeza final de registros inválidos
        df_long = df_long.dropna(subset=["ano"])
        df_long["ano"] = df_long["ano"].astype(int)
        
        df_long = df_long[~df_long["pais_destino"].str.contains("TOTAL", na=False)]
        
        df_long = df_long[df_long["pais_destino"] != "NAN"]

        # salvando o arquivo na camada TRUSTED
        logging.info(f"Salvando dados TRUSTED em: {trusted_path}")
        trusted_path.parent.mkdir(parents=True, exist_ok=True)
        df_long.to_csv(trusted_path, index=False, encoding='utf-8')

        logging.info("Transformação de comércio concluída com sucesso.\n")

    except Exception as e:
        logging.error(f"Erro crítico na transformação: {e}")
        raise

def main():
    # localização dinâmica baseada na posição deste script
    script_path = Path(__file__).resolve().parent
    project_root = script_path.parent.parent
    
    # definição dos caminhos conforme sua estrutura
    raw_file = project_root / "data" / "raw" / "comercio_raw.csv"
    trusted_file = project_root / "data" / "trusted" / "comercio_trusted.csv"

    # verifica se o arquivo de origem existe antes de começar
    if not raw_file.exists():
        logging.error(f"Arquivo não encontrado: {raw_file}")
        return

    transform_comercio(raw_file, trusted_file)

if __name__ == "__main__":
    main()