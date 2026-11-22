import numpy as np

#ARQUIVO PARA DEFINIR AS EQUACOES A SEREM UTILIZADAS

#Para de fato testar com uma base de dados, use 'preco_de_mercado.py'

def normaliza(x):
    """
    Normaliza os dados de entrada para o intervalo [0, 1].

    Parâmetros:
    x (array-like): Dados de entrada a serem normalizados.

    Retorna:
    array-like: Dados normalizados no intervalo [0, 1].
    """
    x = np.array(x)
    min_x = np.min(x)
    max_x = np.max(x)
    
    # Evita divisão por zero caso todos os valores sejam iguais
    if max_x - min_x == 0:
        #retorna uma matriz de tamanho x com todos os valores iguais a zero
        return np.zeros_like(x)
    
    return (x - min_x) / (max_x - min_x)


#TODO:
"""
    3. Formule o problema de ajuste e estime os coeficientes do modelo (linear e quadr ́atico). Apresente o sistema
    linear a ser resolvido, a solu ̧c ̃ao obtida e um gr ́afico mostrando a superf ́ıcie ajustada juntamente com os pontos
    coletados;
"""