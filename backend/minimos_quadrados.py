import matplotlib.pyplot as plt
import numpy as np

#ARQUIVO PARA DEFINIR AS EQUACOES A SEREM UTILIZADAS

#Para de fato testar com uma base de dados, use 'preco_de_mercado.py'

#PASSO 2:
def normaliza(x):
    """
    Normaliza e adimensionaliza os dados: (x - media) / (max - min).
    O resultado fica centrado em zero, com amplitude 1 (max - min = 1).

    Parâmetros:
    x (array-like): Dados de entrada a serem normalizados.

    Retorna:
    [0] array-like: Dados normalizados.
    [1] list: Lista contendo o valor mínimo, máximo e a média dos dados originais.
    """
    x = np.array(x, dtype=float)
    # float() converte de np.float64 para float do Python (necessário para o jsonify da API)
    min_x = float(np.min(x))
    max_x = float(np.max(x))
    med_x = float(np.mean(x))

    # Evita divisão por zero caso todos os valores sejam iguais
    if max_x - min_x == 0:
        #retorna uma matriz de tamanho x com todos os valores iguais a zero
        return [np.zeros_like(x), [min_x, max_x, med_x]]

    return [(x - med_x) / (max_x - min_x), [min_x, max_x, med_x]]


"""
    3. Formule o problema de ajuste e estime os coeficientes do modelo (linear e quadr ́atico). Apresente o sistema
    linear a ser resolvido, a solu ̧c ̃ao obtida e um gr ́afico mostrando a superf ́ıcie ajustada juntamente com os pontos
    coletados;
"""
#PASSO 3
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

    M = X_approx.T @ X_approx
    b = X_approx.T @ P
    c = np.linalg.solve(M, b)

    return [M, b, c]

def plotar_modelo_3d(A, K, P, c, tipo_solucao, titulo='', arquivo=None):
    """
    Gera um gráfico 3D comparando os dados reais com a superfície ajustada (linear ou quadrática).

    Parâmetros:
        A -> Array com Ano normalizado
        K -> Array com Quilometragem normalizada
        P -> Array com Preço normalizado
        c -> Vetor de coeficientes retornado por solucao_sistema
        tipo_solucao -> 'lin' ou 'quad'
        titulo -> (opcional) texto extra no título, ex.: nome do carro
        arquivo -> (opcional) caminho para salvar a imagem; se omitido, abre a janela do gráfico
    """
    # 1. Criar uma malha (grid) regular de pontos entre os valores mínimos e máximos de A e K
    a_grid = np.linspace(np.min(A), np.max(A), 30)
    k_grid = np.linspace(np.min(K), np.max(K), 30)
    A_mesh, K_mesh = np.meshgrid(a_grid, k_grid)

    # 2. Calcular o Preço estimado (P_hat) para cada ponto da malha usando os coeficientes 'c'
    if tipo_solucao == 'lin':
        # p̂(A,K) = c0 + c1*A + c2*K
        P_mesh = c[0] + c[1]*A_mesh + c[2]*K_mesh
        titulo_modelo = 'Ajuste Linear (Plano)'
    elif tipo_solucao == 'quad':
        # p̂(A,K) = c0 + c1*A + c2*K + c3*A^2 + c4*A*K + c5*K^2
        P_mesh = (c[0] + c[1]*A_mesh + c[2]*K_mesh + 
                  c[3]*(A_mesh**2) + c[4]*(A_mesh * K_mesh) + c[5]*(K_mesh**2))
        titulo_modelo = 'Ajuste Quadrático (Superfície Curva)'
    else:
        raise ValueError("tipo_solucao deve ser 'lin' ou 'quad'")

    # 3. Configurar a figura e o eixo 3D
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Plotar os dados reais (pontos de dispersão)
    ax.scatter(A, K, P, color='crimson', s=40, alpha=0.8, label='Dados Reais')

    # Plotar a superfície do modelo ajustado
    superficie = ax.plot_surface(A_mesh, K_mesh, P_mesh, cmap='viridis', alpha=0.55, edgecolor='none')

    # 4. Rótulos, barra de cores e ajustes visuais
    ax.set_xlabel('Ano Normalizado (A)', labelpad=10)
    ax.set_ylabel('Quilometragem Normalizada (K)', labelpad=10)
    ax.set_zlabel('Preço Normalizado (P)', labelpad=10)
    ax.set_title(f'Regressão por Mínimos Quadrados - {titulo_modelo}', fontsize=13, pad=15)
    
    # Adiciona legenda e barra de escala do preço previsto
    ax.legend(loc='upper left')
    fig.colorbar(superficie, ax=ax, shrink=0.5, aspect=10, label='Preço Estimado')

    # Ajusta o ângulo de visão inicial (elevação, azimute)
    ax.view_init(elev=25, azim=-135)

    if titulo:
        ax.set_title(f'{titulo} - {titulo_modelo}', fontsize=13, pad=15)

    plt.tight_layout()
    mostrar_ou_salvar(fig, arquivo)
    return

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
    Calcula o ágio percentual de cada anúncio: h_i = 100 * (p_i - p(a_i, k_i)) / p(a_i, k_i)

    Parâmetros (em reais, não normalizados):
    valor_aproximado (array-like): Preços aproximados obtidos pelo modelo, p(a_i, k_i).
    valor_real (array-like): Preços reais observados, p_i.

    Retorna:
    array: Ágio percentual de cada anúncio.
    """
    agio = np.zeros(len(valor_real))

    for i in range(len(valor_real)):
        # O denominador é o preço estimado pelo modelo, conforme o enunciado
        agio[i] = 100*(valor_real[i] - valor_aproximado[i]) / valor_aproximado[i]

    return agio


def plotar_agio(agio, titulo='', arquivo=None):
    """
    Gera um gráfico de barras com o ágio percentual de cada anúncio.

    Cores: verde = boa oportunidade (h <= -10%), azul = preço justo (|h| < 10%),
           vermelho = muito acima (h >= 10%).
    A melhor barganha (menor ágio) é destacada com uma seta.

    Parâmetros:
        agio    -> Array com o ágio percentual de cada anúncio (saída de agio_percentual)
        titulo  -> Texto extra para o título (ex.: 'Onix - modelo lin')
        arquivo -> (opcional) caminho para salvar a imagem; se omitido, abre a janela do gráfico
    """
    agio = np.asarray(agio)
    indices = np.arange(1, len(agio) + 1)
    cores = ['#2ecc71' if h <= -10 else '#e74c3c' if h >= 10 else '#3498db' for h in agio]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(indices, agio, color=cores, edgecolor='black', linewidth=0.4)

    # Linha zero e limites de +-10%
    ax.axhline(0, color='black', linewidth=1)
    ax.axhline(10, color='#e74c3c', linestyle='--', linewidth=1.2, label='+10% (muito acima)')
    ax.axhline(-10, color='#2ecc71', linestyle='--', linewidth=1.2, label='-10% (boa oportunidade)')

    # Destaque na melhor barganha
    i = int(np.argmin(agio))
    ax.annotate(f'Melhor barganha\n#{i + 1}: {agio[i]:.1f}%',
                xy=(i + 1, agio[i]), xytext=(i + 1, agio[i] - 9),
                ha='center', fontweight='bold', color='#1e8449',
                arrowprops=dict(arrowstyle='->', color='#1e8449', lw=1.5))
    ax.set_ylim(np.min(agio) - 15, np.max(agio) + 5)

    ax.set_title(f'Ágio percentual por anúncio - {titulo}')
    ax.set_xlabel('Índice do anúncio (i)')
    ax.set_ylabel('Ágio $h_i$ (%)')
    ax.grid(axis='y', linestyle=':', alpha=0.6)
    ax.legend()

    plt.tight_layout()
    mostrar_ou_salvar(fig, arquivo)
    return


def mostrar_ou_salvar(fig, arquivo=None):
    """Salva a figura em `arquivo` (PNG) ou, se não houver arquivo, abre a janela do gráfico."""
    if arquivo:
        fig.savefig(arquivo, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()

