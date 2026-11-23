import numpy as np

#ARQUIVO PARA DEFINIR AS EQUACOES A SEREM UTILIZADAS

#Para de fato testar com uma base de dados, use 'preco_de_mercado.py'

#PASSO 2:
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

    med_x = np.mean(x)
    return (x - med_x) / (max_x - min_x)


"""
    3. Formule o problema de ajuste e estime os coeficientes do modelo (linear e quadr ́atico). Apresente o sistema
    linear a ser resolvido, a solu ̧c ̃ao obtida e um gr ́afico mostrando a superf ́ıcie ajustada juntamente com os pontos
    coletados;
"""
#PASSO 3 (Linear)
def solucao_sistema(A, K, P, tipo_solucao):
    """
        A -> Ano normalizado
        K -> Quilometragem normalizada
        P -> Preço normalizado
        tipo_solucao -> 'lin' ou 'quad'

        Retorna Mc = b, retorna [M, b e c (solução)]
    """
    N = len(P)
    ones = np.ones(N)

    # ==========================================
    # 1. MODELO LINEAR: p̂(A,K) = c0 + c1*A + c2*K
    #
    #   c_lin = [c0, c1, c2]^T                         (vetor coluna 3x1)
    #
    #   X_lin = [1 | A | K]                            (matriz de planejamento Nx3) (No caso quadratico essa matriz aumenta)
    #
    #   y = P = [P_1, P_2, ..., P_N]^T                 (vetor de observações Nx1)
    #
    #   Função objetivo (Soma dos Quadrados dos Resíduos):
    #   S(c) = Sum(P_i - p̂(A_i, K_i))^2
    #        = ||y - X c||_2^2
    #        = (y - X c)^T (y - X c)
    #
    #   Expandindo o produto matricial:
    #   S(c) = y^T y - y^T X c - c^T X^T y + c^T X^T X c
    #        = y^T y - 2 c^T X^T y + c^T (X^T X) c       (pois y^T X c é escalar: y^T X c = (y^T X c)^T = c^T X^T y)
    #
    #   Derivando em relação ao vetor c e igualando a zero (condição de mínimo):
    #   ∇S(c) = dS/dc = -2 X^T y + 2 (X^T X) c = 0
    #
    #   Isolando c, chegamos às Equações Normais:
    #   (X^T X) c = X^T y
    #
    #   Mapeamento para as variáveis do código:
    #   M_lin = X_lin^T @ X_lin                        (matriz simétrica 3x3)
    #   b_lin = X_lin^T @ P                            (vetor coluna 3x1)
    #   M_lin @ c_lin = b_lin  =>  c_lin = np.linalg.solve(M_lin, b_lin)
    # ==========================================
    if tipo_solucao == 'lin':
      X_approx = np.column_stack([ones, A, K])
    else:
      X_approx = np.column_stack([ones, A, K, A**2, A * K, K**2])

    M_lin = X_approx.T @ X_approx
    b_lin = X_approx.T @ P
    c_lin = np.linalg.solve(M_lin, b_lin)


    return [M_lin, b_lin, c_lin]

    #print("=== SISTEMA LINEAR (3x3) ===")
    #print("Matriz X^T X:\n", np.round(M_lin, 4))
    #print("Vetor X^T y:\n", np.round(b_lin, 4))
    #print("Coeficientes [c0, c1, c2]:\n", np.round(c_lin, 4))

    #print("\n=== SISTEMA QUADRÁTICO (6x6) ===")
    #print("Matriz X^T X:\n", np.round(M_quad, 4))
    #print("Vetor X^T y:\n", np.round(b_quad, 4))
    #print("Coeficientes [c0, c1, c2, c3, c4, c5]:\n", np.round(c_quad, 4))

    #print("\n=== SISTEMA QUADRÁTICO (6x6) ===")
    #print("Matriz X^T X:\n", np.round(M_quad, 4))
    #print("Vetor X^T y:\n", np.round(b_quad, 4))
    #print("Coeficientes [c0, c1, c2, c3, c4, c5]:\n", np.round(c_quad, 4))



    """
      a_grid = np.linspace(A.min(), A.max(), 30)
      k_grid = np.linspace(K.min(), K.max(), 30)
      AA, KK = np.meshgrid(a_grid, k_grid)

      PP_lin = c_lin[0] + c_lin[1] * AA + c_lin[2] * KK
      PP_quad = (
          c_quad[0]
          + c_quad[1] * AA
          + c_quad[2] * KK
          + c_quad[3] * AA**2
          + c_quad[4] * AA * KK
          + c_quad[5] * KK**2
      )

      fig = plt.figure(figsize=(14, 6))
    """

#PASSO 4
def REQM(valor_aproximado, valor_real): #Raiz erro quadratico médio
    erro2 = 0

    #Somatoria do erro
    for i in range(len(valor_real)):
        erro2 += (valor_real[i] - valor_aproximado[i])**2

    #Retorna a raiz do erro quadratico médio
    return np.sqrt(erro2 / len(valor_real))


#PASSO 5
def agio_percentual(valor_aproximado, valor_real):
    """
    Calcula o ágio percentual entre os preços aproximados e os preços reais.

    Parâmetros:
    valor_aproximado (array-like): Preços aproximados obtidos pelo modelo.
    valor_real (array-like): Preços reais observados.

    Retorna:
    float: Ágio percentual médio.
    """
    agio = np.zeros(len(valor_real))

    for i in range(len(valor_real)):
        agio[i] = 100*(valor_real[i] - valor_aproximado[i]) / valor_real[i]

    return agio