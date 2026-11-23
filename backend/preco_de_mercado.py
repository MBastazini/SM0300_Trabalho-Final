

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

if __name__ == "__main__":
    print("Passo 2 -> Normalizando os valores do onix...")
    onix_data = get_onix_normalizado()

    print("Passo 3 -> Estimando os coeficientes do modelo (linear e quadratico)")
    [M_lin, b_lin, c_lin] = mq.solucao_sistema(onix_data['ano'], onix_data['km'], onix_data['preco'], 'lin')
    print(f"Coeficientes do modelo linear: {M_lin}, {b_lin}, {c_lin}")
    [M_quad, b_quad, c_quad] = mq.solucao_sistema(onix_data['ano'], onix_data['km'], onix_data['preco'], 'quad')
    print(f"Coeficientes do modelo quadratico: {M_quad}, {b_quad}, {c_quad}")

    print("Determinando os valores estimados...")

    ano = onix_data['ano']
    km = onix_data['km']

    X_lin = np.column_stack((np.ones_like(ano), ano, km))
    preco_estimado_lin = X_lin @ c_lin

    X_quad = np.column_stack((np.ones_like(ano), ano, km, ano**2, ano * km, km**2))
    preco_estimado_quad = X_quad @ c_quad

    # Volta os preços (anunciados e estimados) para reais
    preco_real = desnormalize_values(onix_data['preco'], onix_data['preco_stats'])
    preco_estimado_lin_reais = desnormalize_values(preco_estimado_lin, onix_data['preco_stats'])
    preco_estimado_quad_reais = desnormalize_values(preco_estimado_quad, onix_data['preco_stats'])

    print("Passo 4 e 5 -> Determinando o REQM e o agio percentual...")

    reqm_lin = mq.REQM(preco_estimado_lin_reais, preco_real)
    agio_lin = mq.agio_percentual(preco_estimado_lin_reais, preco_real)

    reqm_quad = mq.REQM(preco_estimado_quad_reais, preco_real)
    agio_quad = mq.agio_percentual(preco_estimado_quad_reais, preco_real)

    print(f"REQM linear: R$ {reqm_lin:.2f} | REQM quadratico: R$ {reqm_quad:.2f}")

    #TODO: Analisar agil assim como exigido


    print("Passo 6 - Estimando o preço do carro do Bob")
    #Usar os modelos para estimar o preço do carro do Bob: modelo 2022 com 48000 km
    ano_test = 2022
    km_test = 48000

    preco_estimado_test_lin = estima_preco(ano_test, km_test, c_lin, 'lin', onix_data)
    preco_estimado_test_quad = estima_preco(ano_test, km_test, c_quad, 'quad', onix_data)

    print(f"Preço estimado para o carro com ano {ano_test} e km {km_test} (modelo linear): R$ {preco_estimado_test_lin:.2f}")
    print(f"Preço estimado para o carro com ano {ano_test} e km {km_test} (modelo quadrático): R$ {preco_estimado_test_quad:.2f}")

    print("Passo 7 - Depreciação")
    for tipo, c in [('lin', c_lin), ('quad', c_quad)]:
        atual = estima_preco(2022, 48000, c, tipo, onix_data)

        dep_8000 = atual - estima_preco(2022, 56000, c, tipo, onix_data)
        dep_10000 = atual - estima_preco(2022, 58000, c, tipo, onix_data)
        dep_1ano = atual - estima_preco(2021, 48000, c, tipo, onix_data)

        print(f"[{tipo}] +8000 km: R$ {dep_8000:.2f} ({100*dep_8000/atual:.2f}%)")
        print(f"[{tipo}] +10000 km: R$ {dep_10000:.2f} ({100*dep_10000/atual:.2f}%) | 1 ano mais velho: R$ {dep_1ano:.2f} ({100*dep_1ano/atual:.2f}%)")
