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
def solucao_sistema(A, K, P, grau):
    """
    Monta e resolve o sistema normal (X^T X) c = X^T P para um polinômio 2D de grau n.

    Parâmetros:
        A (array-like): Ano normalizado
        K (array-like): Quilometragem normalizada
        P (array-like): Preço normalizado
        grau (int): Grau n do polinômio de aproximação (ex: 1 para linear, 2 para quadrático, etc.)

    Retorna:
        list: [M, b, c] onde M = X^T X, b = X^T P e c é o vetor de coeficientes.
    """
    A = np.asarray(A, dtype=float)
    K = np.asarray(K, dtype=float)
    P = np.asarray(P, dtype=float)

    if grau == "lin":
        grau = 1
    elif grau == "quad":
        grau = 2

    if not isinstance(grau, int) or grau < 0:
        raise ValueError("O parâmetro 'grau' deve ser um número inteiro maior ou igual a 0.")

    # Gera dinamicamente as colunas [1, A, K, A^2, A*K, K^2, ..., A^n, ..., K^n]
    colunas = []
    for d in range(grau + 1):           # d percorre cada grau de 0 até n
        for j in range(d + 1):          # j é o expoente de K (de 0 até d)
            i = d - j                   # i é o expoente de A (de d até 0)
            colunas.append((A ** i) * (K ** j))

    X_approx = np.column_stack(colunas)

    M = X_approx.T @ X_approx
    b = X_approx.T @ P
    c = np.linalg.solve(M, b)

    return [M, b, c]


def plotar_modelo_3d(A, K, P, c, grau, titulo='', arquivo=None):
    """
    Gera um gráfico 3D comparando os dados reais com a superfície polinomial ajustada de grau n.

    Parâmetros:
        A -> Array com Ano normalizado
        K -> Array com Quilometragem normalizada
        P -> Array com Preço normalizado
        c -> Vetor de coeficientes retornado por solucao_sistema
        grau -> Grau n do polinômio de aproximação (ex: 1, 2, 3, ...)
        titulo -> (opcional) texto extra no título, ex.: nome do carro
        arquivo -> (opcional) caminho para salvar a imagem; se omitido, abre a janela do gráfico
    """
    if grau == "lin":
        grau = 1
    elif grau == "quad":
        grau = 2

    if not isinstance(grau, int) or grau < 0:
        raise ValueError("O parâmetro 'grau' deve ser um número inteiro maior ou igual a 0.")

    c = np.asarray(c, dtype=float)
    n_coef_esperado = (grau + 1) * (grau + 2) // 2
    if len(c) != n_coef_esperado:
        raise ValueError(
            f"Para grau {grau}, o vetor 'c' deve ter {n_coef_esperado} coeficientes, mas recebeu {len(c)}."
        )

    # 1. Criar uma malha (grid) regular de pontos entre os valores mínimos e máximos de A e K
    a_grid = np.linspace(np.min(A), np.max(A), 30)
    k_grid = np.linspace(np.min(K), np.max(K), 30)
    A_mesh, K_mesh = np.meshgrid(a_grid, k_grid)

    # 2. Calcular o Preço estimado (P_hat) para cada ponto da malha usando os coeficientes 'c'
    P_mesh = np.zeros_like(A_mesh, dtype=float)
    idx = 0
    for d in range(grau + 1):
        for j in range(d + 1):
            i = d - j
            P_mesh += c[idx] * (A_mesh ** i) * (K_mesh ** j)
            idx += 1

    # Define rótulo amigável para graus clássicos ou genérico para graus maiores
    nomes_grau = {
        0: 'Ajuste Constante (Grau 0)',
        1: 'Ajuste Linear (Plano)',
        2: 'Ajuste Quadrático (Superfície Curva)',
        3: 'Ajuste Cúbico (Grau 3)'
    }
    titulo_modelo = nomes_grau.get(grau, f'Ajuste Polinomial (Grau {grau})')

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

    prefixo = titulo if titulo else 'Regressão por Mínimos Quadrados'
    ax.set_title(f'{prefixo} - {titulo_modelo}', fontsize=13, pad=15)

    # Adiciona legenda e barra de escala do preço previsto
    ax.legend(loc='upper left')
    fig.colorbar(superficie, ax=ax, shrink=0.5, aspect=10, label='Preço Estimado')

    # Ajusta o ângulo de visão inicial (elevação, azimute)
    ax.view_init(elev=25, azim=-135)

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

