import pandas as pd
from pathlib import Path
import logging

# adicionando Logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# funcao para extrair os CSVs da Embrapa
def extract_embrapa_online(url: str, output_path: Path, sep: str = ";", encoding: str = "latin1") -> bool:
    """
    extrai os dados da URL e salva localmente.
    retorna True se tiver sucesso, False caso contrário.
    """
    try:
        logging.info(f"Lendo dados da URL: {url}")
        
        # leitura dos dados
        df = pd.read_csv(url, sep=sep, encoding=encoding)
        
        # garante que a pasta pai existe antes de salvar
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False, encoding='utf-8')
        logging.info(f"Dados salvos com sucesso em: {output_path}")
        return True

    except Exception as e:
        logging.error(f"Erro ao processar {url}: {e}")
        return False

def main():
    # identifica a pasta onde este script está
    script_path = Path(__file__).resolve().parent
    
    project_root = script_path.parent.parent 
    
    raw_dir = project_root / "data" / "raw"

    urls = {
        "comercio": "https://vitibrasil.cnpuv.embrapa.br/download/Comercio.csv",
        "exportacao": "https://vitibrasil.cnpuv.embrapa.br/download/ExpVinho.csv",
    }

    for name, url in urls.items():
        output_file = raw_dir / f"{name}_raw.csv"
        
        logging.info(f"Iniciando extração de: {name}")
        sucesso = extract_embrapa_online(url, output_file)
        
        if sucesso:
            logging.info(f"Item '{name}' finalizado com sucesso.\n")
        else:
            logging.warning(f"Falha ao processar item '{name}'.\n")

if __name__ == "__main__":
    main()