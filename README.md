# SM0300_Trabalho-Final
Repositório para a construção do trabalho final de Calculo Numérico (SM0300). O proposito do trabalho é construir uma analise de preços de carro utilizando o método dos mínimos quadrdos.

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
