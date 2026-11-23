

from pathlib import Path
import numpy as np

from minimos_quadrados import normaliza, solucao_sistema, REQM, agio_percentual

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
    print("Passo 2 -> Normalizando os valores do onix...")
    onix_data = get_onix_normalizado()

    print("Passo 3 -> Estimando os coeficientes do modelo (linear e quadratico)")
    [M_lin, b_lin, c_lin] = solucao_sistema(onix_data['ano'], onix_data['km'], onix_data['preco'], 'lin')
    print(f"Coeficientes do modelo linear: {M_lin}, {b_lin}, {c_lin}")
    [M_quad, b_quad, c_quad] = solucao_sistema(onix_data['ano'], onix_data['km'], onix_data['preco'], 'quad')
    print(f"Coeficientes do modelo quadratico: {M_quad}, {b_quad}, {c_quad}")

    print("Determinando os valores estimados...")

    ano = onix_data['ano']
    km = onix_data['km']

    X_lin = np.column_stack((np.ones_like(ano), ano, km))
    preco_estimado_lin = X_lin @ c_lin

    X_quad = np.column_stack((np.ones_like(ano), ano, km, ano**2, ano * km, km**2))
    preco_estimado_quad = X_quad @ c_quad

    print("Passo 4 e 5 -> Determinando o REQM e o agio percentual...")

    reqm_lin = REQM(onix_data['preco'], preco_estimado_lin)
    agio_lin = agio_percentual(onix_data['preco'], preco_estimado_lin)

    reqm_quad = REQM(onix_data['preco'], preco_estimado_quad)
    agio_quad = agio_percentual(onix_data['preco'], preco_estimado_quad)

    #TODO: Analisar agil assim como exigido
