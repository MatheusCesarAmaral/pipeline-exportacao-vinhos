import pandas as pd
from pathlib import Path


def extract_embrapa_online(url: str, output_path: Path) -> None:
    print(f"Lendo dados da URL: {url}")

    df = pd.read_csv(url, sep=";", encoding="latin1")

    print(f"Salvando dados brutos em: {output_path}")
    df.to_csv(output_path, index=False)

    print("Ingestão concluída.\n")


def main():
    urls = {
        "producao": "https://vitibrasil.cnpuv.embrapa.br/download/Producao.csv",
        "comercio": "https://vitibrasil.cnpuv.embrapa.br/download/Comercio.csv",
        "exportacao": "https://vitibrasil.cnpuv.embrapa.br/download/ExpVinho.csv",
    }

    raw_dir = Path("data/raw")
    raw_dir.mkdir(exist_ok=True, parents=True)

    for name, url in urls.items():
        output_file = raw_dir / f"{name}_raw.csv"
        extract_embrapa_online(url, output_file)


if __name__ == "__main__":
    main()