import pandas as pd
from pathlib import Path
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def transform_exportacao(raw_path: Path, trusted_path: Path) -> None:
    try:
        logging.info(f"Lendo dados RAW: {raw_path}")
        
        # Tenta ler com UTF-8-SIG (ignora o caractere invisível do Excel)
        # Se falhar, tenta Latin-1
        try:
            df = pd.read_csv(raw_path, sep=';', encoding='utf-8-sig')
            # Verifica se o nome da coluna 'País' veio quebrado
            if "PaÃ" in str(df.columns):
                df = pd.read_csv(raw_path, sep=';', encoding='latin1')
        except:
            df = pd.read_csv(raw_path, sep=';', encoding='latin1')

        # Caso o arquivo use vírgula em vez de ponto e vírgula
        if len(df.columns) < 2:
            df = pd.read_csv(raw_path, sep=',', encoding='utf-8-sig')

        # No arquivo da Embrapa: Id (col 0), País (col 1)
        col_pais = df.columns[1] 
        
        # Lógica de colunas pares (Litros) e ímpares (Valor US$)
        cols_dados = df.columns[2:]
        cols_litros = [cols_dados[i] for i in range(0, len(cols_dados), 2)]
        cols_valor = [cols_dados[i] for i in range(1, len(cols_dados), 2)]

        # Unpivot (Melt) das métricas
        df_litros = df.melt(id_vars=[col_pais], value_vars=cols_litros, var_name="ano", value_name="quantidade_litros")
        df_valor = df.melt(id_vars=[col_pais], value_vars=cols_valor, var_name="ano_v", value_name="valor_usd")
        
        # Une as tabelas
        df_litros["valor_usd"] = df_valor["valor_usd"]
        df_long = df_litros.rename(columns={col_pais: "nome_entidade"})

        # Limpeza do ano (remove o .1 das colunas duplicadas)
        df_long["ano"] = df_long["ano"].astype(str).str.split('.').str[0]
        
        # --- FUNÇÃO DE LIMPEZA DE CARACTERES (Anti-Mojibake) ---
        def fix_text(text):
            if not isinstance(text, str): return text
            try:
                # Tenta consertar nomes que foram lidos errado (Ex: RepãƒÂºblica -> República)
                return text.encode('latin1').decode('utf-8').encode('latin1').decode('utf-8').strip().title()
            except:
                try:
                    return text.encode('latin1').decode('utf-8').strip().title()
                except:
                    return text.strip().title()

        df_long["nome_entidade"] = df_long["nome_entidade"].apply(fix_text)
        
        # Filtro de Hierarquia (Remove Totais e Continentes)
        termos_remover = ["Total", "África", "América", "Ásia", "Europa", "Oceania", "Outros", "Uniao Europeia"]
        regex_filtro = "|".join(termos_remover)
        df_long = df_long[~df_long["nome_entidade"].str.contains(regex_filtro, na=False, case=False)]

        # Tipagem final
        df_long["ano"] = pd.to_numeric(df_long["ano"], errors="coerce").fillna(0).astype(int)
        df_long["quantidade_litros"] = pd.to_numeric(df_long["quantidade_litros"], errors="coerce").fillna(0)
        df_long["valor_usd"] = pd.to_numeric(df_long["valor_usd"], errors="coerce").fillna(0)

        # Salva em UTF-8 limpo
        logging.info(f"Salvando dados TRUSTED: {trusted_path}")
        trusted_path.parent.mkdir(parents=True, exist_ok=True)
        df_long.to_csv(trusted_path, index=False, encoding='utf-8')

        logging.info("Transformação de exportação concluída com sucesso.")

    except Exception as e:
        logging.error(f"Erro crítico na exportação: {e}")
        raise

def main():
    script_path = Path(__file__).resolve().parent
    project_root = script_path.parent.parent
    
    # Verifique se o nome do arquivo na sua pasta data/raw é 'exportacao_raw.csv'
    raw_file = project_root / "data" / "raw" / "exportacao_raw.csv"
    trusted_file = project_root / "data" / "trusted" / "exportacao_trusted.csv"
    
    transform_exportacao(raw_file, trusted_file)

if __name__ == "__main__":
    main()