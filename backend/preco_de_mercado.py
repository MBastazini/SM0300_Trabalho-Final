

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


def estima_valor(variaveis, grau, data, c, variavel_alvo="preco"):
    """
    Estima o valor da variável variavel_alvo (por padrão, 'preco') usando o modelo polinomial ajustado.

    Parâmetros:
        variaveis (dict): Dicionário {nome_da_variavel: valor_ou_array} na mesma ordem usada em solucao_sistema.
                          Ex.: {'ano': 2022, 'km': 48000} ou {'ano': [2022, 2023], 'km': [48000, 10000]}.
        grau (int ou str): Grau do polinômio a ser usado na estimativa ('lin', 'quad' ou inteiro >= 0).
        data (dict): Dados normalizados contendo '<variavel>_stats' para cada variável e para o variavel_alvo.
        c (array-like): Coeficientes do modelo obtidos em solucao_sistema.
        variavel_alvo (str): Nome da variável dependente a ser desnormalizada (padrão: 'preco').

    Retorna:
        float ou np.ndarray: Valor estimado na escala original (float para entrada escalar,
                             ou np.ndarray quando as entradas forem listas/arrays).
    """
    if not isinstance(variaveis, dict) or len(variaveis) == 0:
        raise ValueError("'variaveis' deve ser um dicionário não vazio (ex.: {'ano': 2022, 'km': 48000}).")

    if f"{variavel_alvo}_stats" not in data:
        raise ValueError(f"Missing normalization stats for target '{variavel_alvo}' in data.")

    entrada_escalar = all(np.ndim(v) == 0 for v in variaveis.values())

    variaveis_normalizadas = []
    for nome, valor in variaveis.items():
        if f"{nome}_stats" not in data:
            raise ValueError(f"Missing normalization stats for variable '{nome}' in data.")
        variaveis_normalizadas.append(mq.normalize_test_values(valor, data[f"{nome}_stats"]))

    matriz_X = mq.montar_matriz_X(variaveis_normalizadas, grau)

    # Confere se os coeficientes c têm o tamanho correto para a matriz_X
    if matriz_X.shape[1] != len(c):
        raise ValueError(f"Mismatch between number of coefficients ({len(c)}) and number of features ({matriz_X.shape[1]}).")

    estimativa = mq.desnormalize_test_values(matriz_X @ c, data[f"{variavel_alvo}_stats"])

    if entrada_escalar:
        return float(estimativa[0])
    return estimativa