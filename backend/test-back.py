import preco_de_mercado
import minimos_quadrados as mq
import numpy as np

print("Passo 2 -> Normalizando os valores do onix...")
onix_data = preco_de_mercado.get_onix_normalizado()

print("Passo 3 -> Estimando os coeficientes do modelo (linear e quadratico)")
[M_lin, b_lin, c_lin] = mq.solucao_sistema(onix_data['ano'], onix_data['km'], onix_data['preco'], 1)
print(f"Coeficientes do modelo linear: {M_lin}, {b_lin}, {c_lin}")
mq.plotar_modelo_3d(onix_data['ano'], onix_data['km'], onix_data['preco'], c_lin, 1)
[M_quad, b_quad, c_quad] = mq.solucao_sistema(onix_data['ano'], onix_data['km'], onix_data['preco'], 2)
print(f"Coeficientes do modelo quadratico: {M_quad}, {b_quad}, {c_quad}")
mq.plotar_modelo_3d(onix_data['ano'], onix_data['km'], onix_data['preco'], c_quad, 2)

print("Determinando os valores estimados...")

ano = onix_data['ano']
km = onix_data['km']

X_lin = np.column_stack((np.ones_like(ano), ano, km))
preco_estimado_lin = X_lin @ c_lin

X_quad = np.column_stack((np.ones_like(ano), ano, km, ano**2, ano * km, km**2))
preco_estimado_quad = X_quad @ c_quad

# Volta os preços (anunciados e estimados) para reais
preco_real = preco_de_mercado.desnormalize_values(onix_data['preco'], onix_data['preco_stats'])
preco_estimado_lin_reais = preco_de_mercado.desnormalize_values(preco_estimado_lin, onix_data['preco_stats'])
preco_estimado_quad_reais = preco_de_mercado.desnormalize_values(preco_estimado_quad, onix_data['preco_stats'])

print("Passo 4 e 5 -> Determinando o REQM e o agio percentual...")

reqm_lin = mq.REQM(preco_estimado_lin_reais, preco_real)
agio_lin = mq.agio_percentual(preco_estimado_lin_reais, preco_real)

reqm_quad = mq.REQM(preco_estimado_quad_reais, preco_real)
agio_quad = mq.agio_percentual(preco_estimado_quad_reais, preco_real)

print(f"REQM linear: R$ {reqm_lin:.2f} | REQM quadratico: R$ {reqm_quad:.2f}")

print("Passo 5 -> Classificando os anúncios pelo ágio")
for tipo, agio, estimado in [('lin', agio_lin, preco_estimado_lin_reais), ('quad', agio_quad, preco_estimado_quad_reais)]:
    justos = np.sum(np.abs(agio) < 10)
    acima = np.sum(agio >= 10)
    oportunidades = np.sum(agio <= -10)

    # Melhor barganha: anúncio com o menor ágio (maior desconto em relação ao estimado)
    i = int(np.argmin(agio))
    ano_i = preco_de_mercado.desnormalize_values(onix_data['ano'][i], onix_data['ano_stats'])
    km_i = preco_de_mercado.desnormalize_values(onix_data['km'][i], onix_data['km_stats'])

    print(f"[{tipo}] Preço justo: {justos} | Muito acima: {acima} | Boas oportunidades: {oportunidades}")
    print(f"[{tipo}] Melhor barganha: anúncio #{i + 1} ({ano_i:.0f}, {km_i:.0f} km) - "
          f"anunciado R$ {preco_real[i]:.2f}, estimado R$ {estimado[i]:.2f}, ágio {agio[i]:.2f}%")

    mq.plotar_agio(agio, f'Onix - modelo {tipo}')


print("Passo 6 -> Estimando o preço do carro do Bob")
#Usar os modelos para estimar o preço do carro do Bob: modelo 2022 com 48000 km
ano_test = 2022
km_test = 48000

preco_estimado_test_lin = preco_de_mercado.estima_preco(ano_test, km_test, c_lin, 1, onix_data)
preco_estimado_test_quad = preco_de_mercado.estima_preco(ano_test, km_test, c_quad, 2, onix_data)

print(f"Preço estimado para o carro com ano {ano_test} e km {km_test} (modelo linear): R$ {preco_estimado_test_lin:.2f}")
print(f"Preço estimado para o carro com ano {ano_test} e km {km_test} (modelo quadrático): R$ {preco_estimado_test_quad:.2f}")

print("Passo 7 -> Depreciação")
for grau, c in [(1, c_lin), (2, c_quad)]:
    atual = preco_de_mercado.estima_preco(2022, 48000, c, grau, onix_data)

    dep_8000 = atual - preco_de_mercado.estima_preco(2022, 56000, c, grau, onix_data)
    dep_10000 = atual - preco_de_mercado.estima_preco(2022, 58000, c, grau, onix_data)
    dep_1ano = atual - preco_de_mercado.estima_preco(2021, 48000, c, grau, onix_data)
    print(f"[grau {grau}] +8000 km: R$ {dep_8000:.2f} ({100*dep_8000/atual:.2f}%)")
    print(f"[grau {grau}] +10000 km: R$ {dep_10000:.2f} ({100*dep_10000/atual:.2f}%) | 1 ano mais velho: R$ {dep_1ano:.2f} ({100*dep_1ano/atual:.2f}%)")

print("Passo 9 -> Veículo elétrico (Dolphin Mini)")
dolphin_data = preco_de_mercado.get_dolphin_normalizado()
[M_dol, b_dol, c_dol] = mq.solucao_sistema(dolphin_data['ano'], dolphin_data['km'], dolphin_data['preco'], 1)
print(f"Coeficientes do Dolphin (linear): {c_dol}")

X_dol = np.column_stack((np.ones_like(dolphin_data['ano']), dolphin_data['ano'], dolphin_data['km']))
preco_real_dol = preco_de_mercado.desnormalize_values(dolphin_data['preco'], dolphin_data['preco_stats'])
preco_estimado_dol = preco_de_mercado.desnormalize_values(X_dol @ c_dol, dolphin_data['preco_stats'])

reqm_dol = mq.REQM(preco_estimado_dol, preco_real_dol)
agio_dol = mq.agio_percentual(preco_estimado_dol, preco_real_dol)
print(f"REQM Dolphin: R$ {reqm_dol:.2f}")

# Depreciação no carro médio de cada amostra (os dois carros não têm anos em comum)
for nome, data, c in [('Onix', onix_data, c_lin), ('Dolphin Mini', dolphin_data, c_dol)]:
    ano_ref = data['ano_stats'][2]
    km_ref = data['km_stats'][2]
    atual = preco_de_mercado.estima_preco(ano_ref, km_ref, c, 1, data)

    dep_10000 = atual - preco_de_mercado.estima_preco(ano_ref, km_ref + 10000, c, 1, data)
    dep_1ano = atual - preco_de_mercado.estima_preco(ano_ref - 1, km_ref, c, 1, data)

    print(f"[{nome}] +10000 km: R$ {dep_10000:.2f} ({100*dep_10000/atual:.2f}%) | 1 ano mais velho: R$ {dep_1ano:.2f} ({100*dep_1ano/atual:.2f}%)")