

from pathlib import Path
import numpy as np

from minimos_quadrados import normaliza

# The data directory is relative to the repository, not the process location.
DATA_DIR = Path(__file__).resolve().parent.parent / "dados"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def list_csv_files():
    """Return the CSV files available in the data directory."""
    return sorted(path.name for path in DATA_DIR.glob("*.csv") if path.is_file())

def normalize_values(csv_file, parameter_list):
    """
    Normaliza os valores de cada arquivo CSV na lista fornecida.
    parameter_list é uma lista de strings que representa os nomes das colunas a serem normalizadas.
    Ex. ['ano', 'preco', 'km']
    """

    #Inicia um dicionario vazio
    normalized_data = {}

    #Define o caminho dos CSV's
    file_path = DATA_DIR / csv_file

    #Ve se o CSV entregue existe
    if file_path.is_file():
        # Carrega os dados do arquivo CSV
        #Divide os parametros por ','. 
        #O dtype=None faz com que o numpy tente adivinhar o tipo de cada coluna. 
        #O encoding='utf-8' garante que os caracteres especiais sejam lidos corretamente.
        data = np.genfromtxt(file_path, delimiter=',', names=True, dtype=None, encoding='utf-8')

        # Normaliza os valores para cada parâmetro na lista
        for parameter in parameter_list:
            #Checa se o parametro que queremos normalizar existe no CSV.
            if parameter in data.dtype.names:
                #Usa a funcao normalizar programada em outro arquivo.
                normalized_data[parameter] = normaliza(data[parameter])
            else:
                print(f"Parameter '{parameter}' not found in {csv_file}.")
    else:
        print(f"File {csv_file} does not exist in the data directory.")
    
    return normalized_data

#Funcao pra testar a API
def get_onix_normalizado():
    """
    Retorna os valores normalizados do arquivo 'onix.csv' para os parâmetros 'ano', 'preco' e 'km'.
    """
    return normalize_values('onix.csv', ['ano', 'preco', 'km'])

def get_dolphin_normalizado():
    """
    Retorna os valores normalizados do arquivo 'dolphin.csv' para os parâmetros 'ano', 'preco' e 'km'.
    """
    return normalize_values('dolphin_mini.csv', ['ano', 'preco', 'km'])

if __name__ == "__main__":
    print("CSV files in the data directory:")
    for i, csv_file in enumerate(list_csv_files(), start=1):
        print(f"{i}: {csv_file}")



    print("\nAno normalizado onix")
    print(get_onix_normalizado().get('ano', []))

    print("\nPreco normalizado onix")
    print(get_onix_normalizado().get('preco', []))

    print("\nKm normalizado onix")
    print(get_onix_normalizado().get('km', []))

    print("\nAno normalizado dolphin")
    print(get_dolphin_normalizado().get('ano', []))

    print("\nPreco normalizado dolphin")
    print(get_dolphin_normalizado().get('preco', []))

    print("\nKm normalizado dolphin")
    print(get_dolphin_normalizado().get('km', []))