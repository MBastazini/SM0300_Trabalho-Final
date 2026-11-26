"""
passo 10: gera todas as informações e gráficos do relatório a partir de uma matriz de dados.

A matriz tem n linhas (anúncios) e 3 colunas: [ano, km, preco].

Uso pelo terminal:
python backend/relatorio.py -> Onix + Dolphin Mini (itens 2 a 7 e 9)
python backend/relatorio.py dados/onix.csv -> só esse arquivo
python backend/relatorio.py dados/onix.csv 2022 48000 -> escolhendo o carro dos itens 6 e 7

Uso dentro do Python:
    relatorio(matriz, 'Onix', ano_carro=2022, km_carro=48000)

Os gráficos são salvos como PNG na pasta 'graficos/' da raiz do projeto.
"""

import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import minimos_quadrados as mq
from preco_de_mercado import estima_valor

RAIZ = Path(__file__).resolve().parent.parent
PASTA_GRAFICOS = RAIZ / "graficos"
# (grau do polinômio, sufixo dos arquivos de gráfico, nome do modelo)
MODELOS = [(1, 'lin', 'linear'), (2, 'quad', 'quadrático')]


def moeda(valor):
    """Formata valores monetários de maneira uniforme no relatório."""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def inteiro(valor):
    """Formata valores inteiros com separador de milhares."""
    return f"{valor:,.0f}".replace(',', '.')


def ano_formatado(valor):
    """Formata anos sem separador de milhares."""
    return f"{valor:.0f}"


def percentual(valor):
    """Formata porcentagens com duas casas decimais."""
    return f"{valor:.2f}".replace('.', ',') + '%'


def vetor_matriz(matriz):
    """Devolve uma matriz ou vetor com números alinhados e legíveis."""
    matriz = np.asarray(matriz)
    if matriz.ndim == 1:
        return '[' + '  '.join(f'{valor:10.4f}' for valor in matriz) + ']'

    linhas = []
    for linha in matriz:
        linhas.append('[ ' + '  '.join(f'{valor:10.4f}' for valor in linha) + ' ]')
    return '\n'.join(linhas)


def carrega_csv(caminho):
    """Lê um CSV com colunas ano, km, preco e devolve a matriz n x 3."""
    tabela = np.genfromtxt(caminho, delimiter=',', names=True, encoding='utf-8')
    return np.column_stack((tabela['ano'], tabela['km'], tabela['preco']))


def normaliza_matriz(dados):
    """
    Normaliza cada coluna da matriz e devolve o mesmo dicionário usado no resto do projeto:
    data['ano'], data['km'], data['preco'] (normalizados) e data['<coluna>_stats'] = [min, max, media].
    """
    data = {}
    for i, coluna in enumerate(['ano', 'km', 'preco']):
        data[coluna], data[f'{coluna}_stats'] = mq.normaliza(dados[:, i])
    return data


def matriz_planejamento(A, K, tipo):
    """Matriz X do ajuste: [1 | A | K] no linear e [1 | A | K | A² | AK | K²] no quadrático."""
    return mq.montar_matriz_X([A, K], tipo)


def depreciacao(ano, km, c, grau, data):
    """Queda de preço (R$ e %) do carro (ano, km) com +8000 km, +10000 km e 1 ano a mais de idade."""
    atual = estima_valor({'ano': ano, 'km': km}, tipo, data, c)
    quedas = {
        '+8000 km': atual - estima_valor({'ano': ano, 'km': km + 8000}, tipo, data, c),
        '+10000 km': atual - estima_valor({'ano': ano, 'km': km + 10000}, tipo, data, c),
        '1 ano mais velho': atual - estima_valor({'ano': ano - 1, 'km': km}, tipo, data, c),
    }
    return atual, {nome: (queda, 100 * queda / atual) for nome, queda in quedas.items()}


def relatorio(dados, nome='carro', ano_carro=None, km_carro=None, pasta=PASTA_GRAFICOS):
    """
    Roda os itens 2 a 7 do projeto para a matriz `dados` (colunas: ano, km, preco).

    ano_carro, km_carro -> carro avaliado nos itens 6 e 7. Se omitidos, usa o carro médio da amostra.
    Retorna um dicionário com os resultados de cada modelo, indexado pelo grau (1 e 2).
    """
    dados = np.asarray(dados, dtype=float)
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    prefixo = nome.lower().replace(' ', '_')
    np.set_printoptions(precision=4, suppress=True)

    largura = 72
    print("\n" + "=" * largura)
    print(f"{'RELATÓRIO':^72}")
    print(f"{nome} - {len(dados)} anúncios")
    print("=" * largura)

    # PASSO 2: normalização
    data = normaliza_matriz(dados)
    preco_real = dados[:, 2]
    print("\n" + "-" * largura)
    print("PASSO 2 - NORMALIZAÇÃO")
    print("Fórmula: (x - média) / (máximo - mínimo)")
    print("-" * largura)
    for coluna in ['ano', 'km', 'preco']:
        mn, mx, md = data[f'{coluna}_stats']
        if coluna == 'ano':
            minimo, maximo, media = ano_formatado(mn), ano_formatado(mx), ano_formatado(md)
        elif coluna == 'km':
            minimo, maximo = inteiro(mn), inteiro(mx)
            media = inteiro(md)
        else:
            minimo, maximo, media = moeda(mn), moeda(mx), moeda(md)
        print(f"  {coluna.upper():<8}  mín: {minimo:>14}  |  máx: {maximo:>14}  |  média: {media:>14}")

    if ano_carro is None or km_carro is None:
        ano_carro, km_carro = data['ano_stats'][2], data['km_stats'][2]
        descricao_carro = f"carro médio da amostra ({ano_formatado(ano_carro)}, {inteiro(km_carro)} km)"
    else:
        descricao_carro = f"ano-modelo {ano_formatado(ano_carro)} com {inteiro(km_carro)} km"

    resultados = {}
    for grau, sufixo, nome_modelo in MODELOS:
        print("\n" + "-" * largura)
        print(f"{'MODELO ' + nome_modelo.upper():^72}")
        print("-" * largura)

        # PASSO 3: sistema linear (equações normais) e solução
        M, b, c = mq.solucao_sistema([data['ano'], data['km']], data['preco'], tipo)
        print("\nPASSO 3 - SISTEMA DE EQUAÇÕES NORMAIS")
        print("  (X^T X) c = X^T y")
        print("  M = X^T X")
        print(vetor_matriz(M))
        print("\n  b = X^T y")
        print(f"  {vetor_matriz(b)}")
        print(f"\n  Coeficientes c")
        print(f"  {vetor_matriz(c)}")
        mq.plotar_modelo_3d(data['ano'], data['km'], data['preco'], c, grau, titulo=nome,
                            arquivo=pasta / f"{prefixo}_superficie_{sufixo}.png")

        # Preço estimado de cada anúncio, em reais
        X = matriz_planejamento(data['ano'], data['km'], tipo)
        estimado = mq.desnormalize_test_values(X @ c, data['preco_stats'])

        # PASSO 4: REQM
        reqm = mq.REQM(estimado, preco_real)
        print("\nPASSO 4 - RAIZ DO ERRO QUADRÁTICO MÉDIO")
        print(f"  REQM = {moeda(reqm)}")
        print(f"  Representa {percentual(100 * reqm / data['preco_stats'][2])} do preço médio")

        # PASSO 5: ágio, classificação e melhor barganha
        agio = mq.agio_percentual(estimado, preco_real)
        i = int(np.argmin(agio))
        print("\nPASSO 5 - CLASSIFICAÇÃO PELO ÁGIO")
        print(f"  {'Preço justo (|ágio| < 10%):':<34}{np.sum(np.abs(agio) < 10):>4}")
        print(f"  {'Muito acima (ágio >= 10%):':<34}{np.sum(agio >= 10):>4}")
        print(f"  {'Boas oportunidades (ágio <= -10%):':<34}{np.sum(agio <= -10):>4}")
        print("\n  Melhor barganha")
        print(f"    Anúncio: #{i + 1}")
        print(f"    Veículo: ano {ano_formatado(dados[i, 0])} / {inteiro(dados[i, 1])} km")
        print(f"    Anunciado: {moeda(preco_real[i])}")
        print(f"    Estimado:  {moeda(estimado[i])}")
        print(f"    Ágio:      {percentual(agio[i])}")
        mq.plotar_agio(agio, f'{nome} - modelo {nome_modelo}',
                       arquivo=pasta / f"{prefixo}_agio_{sufixo}.png")

        # PASSOS 6 e 7: preço do carro escolhido e depreciação
        atual, quedas = depreciacao(ano_carro, km_carro, c, grau, data)
        print("\nPASSO 6 - ESTIMATIVA DO VEÍCULO")
        print(f"  {descricao_carro}")
        print(f"  Preço estimado: {moeda(atual)}")
        print("\nPASSO 7 - DEPRECIAÇÃO")
        for evento, (queda, pct) in quedas.items():
            print(f"  {evento:<17} queda de {moeda(queda):>16}  ({percentual(pct)})")

        resultados[grau] = {'c': c, 'M': M, 'b': b, 'reqm': reqm, 'agio': agio,
                            'estimado': estimado, 'preco_atual': atual, 'depreciacao': quedas}

    melhor = min(resultados, key=lambda t: resultados[t]['reqm'])
    print("\n" + "=" * largura)
    print("RESUMO")
    nomes = {g: nome_modelo for g, _, nome_modelo in MODELOS}
    print(f"  Menor REQM: modelo {nomes[melhor]}")
    print(f"  Gráficos salvos em: {pasta}")
    print("=" * largura)

    resultados['data'] = data
    return resultados


def compara_depreciacao(carros):
    """
    PASSO 9: compara a depreciação relativa (modelo linear) de vários carros, cada um no seu
    carro médio (os carros podem não ter anos em comum).

    carros -> lista de (nome, resultados) com os retornos de relatorio().
    """
    largura = 72
    print("\n" + "=" * largura)
    print(f"{'PASSO 9 - COMPARAÇÃO DA DEPRECIAÇÃO':^72}")
    print("Modelo linear - carro médio de cada amostra")
    print("=" * largura)
    for nome, res in carros:
        data, c = res['data'], res[1]['c']
        _, quedas = depreciacao(data['ano_stats'][2], data['km_stats'][2], c, 1, data)
        km_queda, km_pct = quedas['+10000 km']
        ano_queda, ano_pct = quedas['1 ano mais velho']
        print(f"\n  {nome}")
        print(f"    Coeficientes c: {vetor_matriz(c)}")
        print(f"    Mais 10.000 km: queda de {moeda(km_queda)} ({percentual(km_pct)})")
        print(f"    1 ano mais velho: queda de {moeda(ano_queda)} ({percentual(ano_pct)})")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Um arquivo qualquer: python backend/relatorio.py dados/arquivo.csv [ano km]
        caminho = Path(sys.argv[1])
        ano = int(sys.argv[2]) if len(sys.argv) > 3 else None
        km = int(sys.argv[3]) if len(sys.argv) > 3 else None
        relatorio(carrega_csv(caminho), caminho.stem, ano, km)
    else:
        # Projeto completo: Onix (carro do Bob) e Dolphin Mini (veículo elétrico)
        onix = relatorio(carrega_csv(RAIZ / "dados" / "onix.csv"), 'Onix', ano_carro=2022, km_carro=48000)
        dolphin = relatorio(carrega_csv(RAIZ / "dados" / "dolphin_mini.csv"), 'Dolphin Mini')
        compara_depreciacao([('Onix', onix), ('Dolphin Mini', dolphin)])
