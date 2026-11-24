# SM0300_Trabalho-Final
Repositório para a construção do trabalho final de Calculo Numérico (SM0300). O proposito do trabalho é construir uma analise de preços de carro utilizando o método dos mínimos quadrdos.

## Abrir a interface (jeito rápido)

Com Python (com as dependências de `backend/requirements.txt`) e Node.js instalados, rode na raiz do projeto:

```bash
python iniciar.py
```

O script sobe o backend e o frontend, instala as dependências do frontend na primeira vez e abre o site no navegador. Para encerrar, aperte `Ctrl+C`.

## Gerar os resultados do relatório (item 10)

Só precisa de Python (com as dependências de `backend/requirements.txt`). Na raiz do projeto:

```bash
python backend/relatorio.py                            # Onix (carro do Bob) + Dolphin Mini (item 9)
python backend/relatorio.py dados/onix.csv 2022 48000  # qualquer CSV (ano,km,preco) e, opcionalmente, o carro avaliado
```

Imprime os itens 2 a 7 (e a comparação do item 9) e salva os gráficos da superfície ajustada e do ágio em `graficos/`. Dentro do Python, a função `relatorio(matriz, nome, ano_carro, km_carro)` recebe diretamente uma matriz n×3 com as colunas ano, km e preço.

## Backend

O backend Python está em `backend/` e serve uma API Flask. Os arquivos CSV devem ser colocados na pasta `dados/`.

```bash
python -m pip install -r backend/requirements.txt
python backend/app.py
```

Endpoints:

- `GET /api/test`
- `GET /api/dados`

## Frontend

O frontend Vue foi criado com Vite.

```bash
cd frontend
npm install
npm run dev
```
