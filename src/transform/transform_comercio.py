import pandas as pd
from pathlib import Path
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def transform_comercio(raw_path: Path, trusted_path: Path) -> None:
    try:
        logging.info(f"Lendo dados RAW: {raw_path}")
        
        # FORÇANDO o separador ';' e o encoding 'utf-8' que identificamos nos seus arquivos
        df = pd.read_csv(raw_path, sep=';', encoding='utf-8')

        # Verificação de segurança: se após ler com ';' ainda houver apenas 1 coluna,
        # tentamos ler com vírgula ','
        if len(df.columns) < 2:
            df = pd.read_csv(raw_path, sep=',', encoding='utf-8')

        if len(df.columns) < 3:
            logging.error(f"Erro: O arquivo {raw_path} não possui colunas suficientes. Verifique o separador.")
            return

        # 1. Padronização de nomes de colunas
        df.columns = [str(col).strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]

        # 2. Identificação da Coluna de Produto (Índice 2)
        col_prod = df.columns[2]
        cols_anos = [c for c in df.columns if c.isdigit()] 

        # 3. Normalização (Unpivot/Melt)
        # O dado de comércio da Embrapa é VOLUME (Litros)
        df_long = df.melt(
            id_vars=[col_prod],
            value_vars=cols_anos,
            var_name="ano",
            value_name="quantidade_litros"
        )

        # 4. Renomear e limpar nomes
        df_long = df_long.rename(columns={col_prod: "nome_entidade"})
        df_long["nome_entidade"] = df_long["nome_entidade"].astype(str).str.strip().str.title()

        # 5. Filtragem de Hierarquia (Evita duplicidade)
        categorias_remover = [
            "Total", "Vinho De Mesa", "Vinho Fino De Mesa", 
            "Suco De Uva", "Derivados", "Outros Produtos Comercializados"
        ]
        
        regex_filtro = "|".join(categorias_remover)
        df_long = df_long[~df_long["nome_entidade"].str.contains(regex_filtro, na=False, case=False)]
        df_long = df_long[df_long["nome_entidade"] != "Nan"]

        # 6. Tipagem e criação da coluna de Valor (zerada para mercado interno)
        df_long["quantidade_litros"] = pd.to_numeric(df_long["quantidade_litros"], errors="coerce").fillna(0)
        df_long["valor_usd"] = 0 
        df_long["ano"] = pd.to_numeric(df_long["ano"]).astype(int)

        # 7. Salvamento
        logging.info(f"Salvando dados TRUSTED: {trusted_path}")
        trusted_path.parent.mkdir(parents=True, exist_ok=True)
        df_long.to_csv(trusted_path, index=False, encoding='utf-8')

        logging.info("Transformação de comércio concluída com sucesso.\n")

    except Exception as e:
        logging.error(f"Erro crítico na transformação: {e}")
        raise

def main():
    script_path = Path(__file__).resolve().parent
    project_root = script_path.parent.parent
    
    raw_file = project_root / "data" / "raw" / "comercio_raw.csv"
    trusted_file = project_root / "data" / "trusted" / "comercio_trusted.csv"

    if not raw_file.exists():
        logging.error(f"Arquivo não encontrado: {raw_file}")
        return

    transform_comercio(raw_file, trusted_file)

if __name__ == "__main__":
    main()