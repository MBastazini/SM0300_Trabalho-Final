# SM0300_Trabalho-Final
Repositório para a construção do trabalho final de Calculo Numérico (SM0300). O proposito do trabalho é construir uma analise de preços de carro utilizando o método dos mínimos quadrdos.

## Abrir a interface (jeito rápido)

Com Python (com as dependências de `backend/requirements.txt`) e Node.js instalados, rode na raiz do projeto:

```bash
python iniciar.py
```

O script sobe o backend e o frontend, instala as dependências do frontend na primeira vez e abre o site no navegador. Para encerrar, aperte `Ctrl+C`.

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
