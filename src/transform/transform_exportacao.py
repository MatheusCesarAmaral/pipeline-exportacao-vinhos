import pandas as pd
from pathlib import Path
import logging

# adicionando Logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# transformando o arquivo exportacao_raw.csv
def transform_exportacao(raw_path: Path, trusted_path: Path) -> None:
    """
    Transforma os dados de exportação da Embrapa.
    Aplica limpeza, unpivot e conversão de KG para Litros.
    """
    try:
        logging.info(f"Lendo dados RAW: {raw_path}")
        
        # o sep=None detecta se o arquivo usa vírgula ou ponto e vírgula automaticamente
        df = pd.read_csv(raw_path, sep=None, engine='python', encoding='utf-8')

        # padronização de Colunas
        df.columns = [str(col).strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]

        # identificação Dinâmica
        col_pais = df.columns[0]
        # pega colunas que representam anos
        cols_anos = [c for c in df.columns if c.replace('_', '').isdigit()]

        # normalização (Unpivot/Melt)
        df_long = df.melt(
            id_vars=[col_pais],
            value_vars=cols_anos,
            var_name="ano",
            value_name="quantidade_kg"
        )

        # renomear e limpar strings
        df_long = df_long.rename(columns={col_pais: "pais_destino"})
        df_long["pais_destino"] = df_long["pais_destino"].astype(str).str.strip().str.upper()

        # conversão de tipos e Regra de Negócio
        df_long["ano"] = pd.to_numeric(df_long["ano"], errors="coerce")

        df_long["quantidade_kg"] = pd.to_numeric(df_long["quantidade_kg"], errors="coerce").fillna(0)
        
        # regra de negócio: 1kg = 1 Litro
        df_long["quantidade_litros"] = df_long["quantidade_kg"]

        # filtragem final
        df_long = df_long.dropna(subset=["ano"])
        df_long["ano"] = df_long["ano"].astype(int)
        
        # remove totais e linhas vazias que viraram string 'NAN'
        df_long = df_long[~df_long["pais_destino"].str.contains("TOTAL", na=False)]
        df_long = df_long[df_long["pais_destino"] != "NAN"]

        # salvando o arquivo na camada TRUSTED
        logging.info(f"Salvando dados TRUSTED: {trusted_path}")
        trusted_path.parent.mkdir(parents=True, exist_ok=True)
        df_long.to_csv(trusted_path, index=False, encoding='utf-8')

        logging.info("Transformação de exportação concluída com sucesso.\n")

    except Exception as e:
        logging.error(f"Erro na transformação de exportação: {e}")
        raise

def main():
    # caminhos dinâmicos baseados na estrutura do projeto
    script_path = Path(__file__).resolve().parent
    project_root = script_path.parent.parent
    
    raw_file = project_root / "data" / "raw" / "exportacao_raw.csv"
    trusted_file = project_root / "data" / "trusted" / "exportacao_trusted.csv"

    if not raw_file.exists():
        logging.error(f"Arquivo não encontrado: {raw_file}")
        return

    transform_exportacao(raw_file, trusted_file)

if __name__ == "__main__":
    main()