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

import minimos_quadrados as mq
from preco_de_mercado import desnormalize_values, estima_preco

RAIZ = Path(__file__).resolve().parent.parent
PASTA_GRAFICOS = RAIZ / "graficos"
MODELOS = [('lin', 'linear'), ('quad', 'quadrático')]


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
    if tipo == 'lin':
        return np.column_stack((np.ones_like(A), A, K))
    return np.column_stack((np.ones_like(A), A, K, A**2, A * K, K**2))


def depreciacao(ano, km, c, tipo, data):
    """Queda de preço (R$ e %) do carro (ano, km) com +8000 km, +10000 km e 1 ano a mais de idade."""
    atual = estima_preco(ano, km, c, tipo, data)
    quedas = {
        '+8000 km': atual - estima_preco(ano, km + 8000, c, tipo, data),
        '+10000 km': atual - estima_preco(ano, km + 10000, c, tipo, data),
        '1 ano mais velho': atual - estima_preco(ano - 1, km, c, tipo, data),
    }
    return atual, {nome: (queda, 100 * queda / atual) for nome, queda in quedas.items()}


def relatorio(dados, nome='carro', ano_carro=None, km_carro=None, pasta=PASTA_GRAFICOS):
    """
    Roda os itens 2 a 7 do projeto para a matriz `dados` (colunas: ano, km, preco).

    ano_carro, km_carro -> carro avaliado nos itens 6 e 7. Se omitidos, usa o carro médio da amostra.
    Retorna um dicionário com os resultados de cada modelo ('lin' e 'quad').
    """
    dados = np.asarray(dados, dtype=float)
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    prefixo = nome.lower().replace(' ', '_')
    np.set_printoptions(precision=4, suppress=True)

    print("=" * 70)
    print(f"RELATÓRIO: {nome} ({len(dados)} anúncios)")
    print("=" * 70)

    # PASSO 2: normalização
    data = normaliza_matriz(dados)
    preco_real = dados[:, 2]
    print("\n[Passo 2] Normalização: (x - média) / (máx - mín)")
    for coluna in ['ano', 'km', 'preco']:
        mn, mx, md = data[f'{coluna}_stats']
        sep = '' if coluna == 'ano' else ',' 
        print(f"  {coluna:>5}: mín = {mn:{sep}.0f} | máx = {mx:{sep}.0f} | média = {md:{sep}.2f}")

    if ano_carro is None or km_carro is None:
        ano_carro, km_carro = data['ano_stats'][2], data['km_stats'][2]
        descricao_carro = f"carro médio da amostra ({ano_carro:.1f}, {km_carro:,.0f} km)"
    else:
        descricao_carro = f"ano-modelo {ano_carro} com {km_carro:,} km"

    resultados = {}
    for tipo, nome_modelo in MODELOS:
        print(f"\n---------------- Modelo {nome_modelo} ----------------")

        # PASSO 3: sistema linear (equações normais) e solução
        M, b, c = mq.solucao_sistema(data['ano'], data['km'], data['preco'], tipo)
        print("[Passo 3] Sistema (XᵀX) c = Xᵀy")
        print(f"  M = XᵀX =\n{M}")
        print(f"  b = Xᵀy = {b}")
        print(f"  c = {c}")
        mq.plotar_modelo_3d(data['ano'], data['km'], data['preco'], c, tipo, titulo=nome,
                            arquivo=pasta / f"{prefixo}_superficie_{tipo}.png")

        # Preço estimado de cada anúncio, em reais
        X = matriz_planejamento(data['ano'], data['km'], tipo)
        estimado = desnormalize_values(X @ c, data['preco_stats'])

        # PASSO 4: REQM
        reqm = mq.REQM(estimado, preco_real)
        print(f"[Passo 4] REQM = R$ {reqm:,.2f} ({100 * reqm / data['preco_stats'][2]:.1f}% do preço médio)")

        # PASSO 5: ágio, classificação e melhor barganha
        agio = mq.agio_percentual(estimado, preco_real)
        i = int(np.argmin(agio))
        print("[Passo 5] Ágio")
        print(f"  Preço justo (|h| < 10%):        {np.sum(np.abs(agio) < 10)}")
        print(f"  Muito acima (h >= 10%):         {np.sum(agio >= 10)}")
        print(f"  Boas oportunidades (h <= -10%): {np.sum(agio <= -10)}")
        print(f"  Melhor barganha: anúncio #{i + 1} ({dados[i, 0]:.0f}, {dados[i, 1]:,.0f} km) - "
              f"anunciado R$ {preco_real[i]:,.2f}, estimado R$ {estimado[i]:,.2f}, ágio {agio[i]:.2f}%")
        mq.plotar_agio(agio, f'{nome} - modelo {nome_modelo}',
                       arquivo=pasta / f"{prefixo}_agio_{tipo}.png")

        # PASSOS 6 e 7: preço do carro escolhido e depreciação
        atual, quedas = depreciacao(ano_carro, km_carro, c, tipo, data)
        print(f"[Passo 6] Preço estimado do {descricao_carro}: R$ {atual:,.2f}")
        print("[Passo 7] Depreciação:")
        for evento, (queda, pct) in quedas.items():
            print(f"  {evento:<17} R$ {queda:,.2f} ({pct:.2f}%)")

        resultados[tipo] = {'c': c, 'M': M, 'b': b, 'reqm': reqm, 'agio': agio,
                            'estimado': estimado, 'preco_atual': atual, 'depreciacao': quedas}

    melhor = min(resultados, key=lambda t: resultados[t]['reqm'])
    print(f"\n[Passo 4] Menor REQM: modelo {dict(MODELOS)[melhor]}")
    print(f"Gráficos salvos em: {pasta}")

    resultados['data'] = data
    return resultados


def compara_depreciacao(carros):
    """
    PASSO 9: compara a depreciação relativa (modelo linear) de vários carros, cada um no seu
    carro médio (os carros podem não ter anos em comum).

    carros -> lista de (nome, resultados) com os retornos de relatorio().
    """
    print("\n" + "=" * 70)
    print("[Passo 9] Comparação da depreciação (modelo linear, carro médio de cada amostra)")
    print("=" * 70)
    for nome, res in carros:
        data, c = res['data'], res['lin']['c']
        _, quedas = depreciacao(data['ano_stats'][2], data['km_stats'][2], c, 'lin', data)
        km_queda, km_pct = quedas['+10000 km']
        ano_queda, ano_pct = quedas['1 ano mais velho']
        print(f"  {nome:<14} c = {np.round(c, 4)} | +10000 km: R$ {km_queda:,.2f} ({km_pct:.2f}%) | "
              f"1 ano: R$ {ano_queda:,.2f} ({ano_pct:.2f}%)")


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
