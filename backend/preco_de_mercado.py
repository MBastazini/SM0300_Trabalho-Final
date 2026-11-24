

from pathlib import Path
import numpy as np

import minimos_quadrados as mq
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
                normalized = mq.normaliza(data[parameter])
                normalized_data[parameter] = normalized[0]  # Armazena apenas os valores normalizados
                normalized_data[f"{parameter}_stats"] = normalized[1]  # Armazena os valores min, max e media
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
    Retorna os valores normalizados do arquivo 'dolphin_mini.csv' para os parâmetros 'ano', 'preco' e 'km'.
    """
    return normalize_values('dolphin_mini.csv', ['ano', 'preco', 'km'])

def normalize_test_values(ano, km, data):
    """
    Normaliza os valores de ano e km fornecidos com base nos valores normalizados do arquivo 'onix.csv'.
    Retorna os valores normalizados de ano e km.
    """
    
    # Normaliza os valores fornecidos com base nos valores min, max e media do onix
    ano_stats = data['ano_stats']
    km_stats = data['km_stats']
    
    ano_normalized = (ano - ano_stats[2]) / (ano_stats[1] - ano_stats[0])
    km_normalized = (km - km_stats[2]) / (km_stats[1] - km_stats[0])
    
    return ano_normalized, km_normalized

def desnormalize_values(valor_normalizado, stats):
    """
    Desfaz a normalização: converte um valor normalizado de volta para a escala original.
    stats é a lista [min, max, media] guardada em data['<parametro>_stats'].

    Inverte X = (x - media) / (max - min)  =>  x = media + X * (max - min)
    """
    return stats[2] + valor_normalizado * (stats[1] - stats[0])

def estima_preco(ano, km, c, tipo, data):
    """Preço em R$ estimado pelo modelo para um carro (ano-modelo, km)."""
    A, K = normalize_test_values(ano, km, data)
    if tipo == 'lin':
        X = np.array([1, A, K])
    else:
        X = np.array([1, A, K, A**2, A*K, K**2])
    return desnormalize_values(X @ c, data['preco_stats'])