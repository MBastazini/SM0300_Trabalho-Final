from pathlib import Path
import csv
from threading import RLock
import numpy as np

from flask import Flask, jsonify, request

import minimos_quadrados as mq

from preco_de_mercado import (
    DATA_DIR,
    desnormalize_values,
    get_dolphin_normalizado,
    get_onix_normalizado,
    list_csv_files,
    normalize_values,
)


app = Flask(__name__)


class CalculationCache:
    """Guarda resultados calculados por CSV e invalida quando o arquivo muda."""

    def __init__(self):
        self._normalized = {}
        self._models = {}
        self._lock = RLock()

    @staticmethod
    def _file_signature(csv_name):
        file_path = (DATA_DIR / csv_name).resolve()
        if not file_path.is_file():
            return None
        return (file_path.stat().st_mtime_ns, file_path.stat().st_size)

    def get_normalized(self, csv_name):
        signature = self._file_signature(csv_name)
        if signature is None:
            return None

        with self._lock:
            cached = self._normalized.get(csv_name)
            if cached is not None and cached["signature"] == signature:
                return cached["value"]

            normalized = normalize_values(csv_name, ["ano", "km", "preco"])
            self._normalized[csv_name] = {
                "signature": signature,
                "value": normalized,
            }
            self._models.pop(csv_name, None)
            return normalized

    def get_models(self, csv_name):
        normalized = self.get_normalized(csv_name)
        if normalized is None:
            return None

        signature = self._file_signature(csv_name)
        with self._lock:
            cached = self._models.get(csv_name)
            if cached is not None and cached["signature"] == signature:
                return cached["value"]

            ano = np.asarray(normalized["ano"], dtype=float).reshape(-1)
            km = np.asarray(normalized["km"], dtype=float).reshape(-1)
            preco = np.asarray(normalized["preco"], dtype=float).reshape(-1)

            if not (len(ano) == len(km) == len(preco)) or len(preco) == 0:
                return None

            matrix_linear, vector_linear, coefficients_linear = mq.solucao_sistema(
                ano, km, preco, "lin"
            )
            matrix_quadratic, vector_quadratic, coefficients_quadratic = mq.solucao_sistema(
                ano, km, preco, "quad"
            )

            x_linear = np.column_stack((np.ones_like(ano), ano, km))
            estimated_linear_normalized = x_linear @ coefficients_linear

            x_quadratic = np.column_stack((
                np.ones_like(ano),
                ano,
                km,
                ano ** 2,
                ano * km,
                km ** 2,
            ))
            estimated_quadratic_normalized = x_quadratic @ coefficients_quadratic

            price_stats = normalized["preco_stats"]
            real_price = desnormalize_values(preco, price_stats)
            estimated_linear_price = desnormalize_values(
                estimated_linear_normalized,
                price_stats,
            )
            estimated_quadratic_price = desnormalize_values(
                estimated_quadratic_normalized,
                price_stats,
            )

            reqm_linear = float(mq.REQM(estimated_linear_price, real_price))
            reqm_quadratic = float(mq.REQM(estimated_quadratic_price, real_price))
            agio_linear = mq.agio_percentual(estimated_linear_price, real_price)
            agio_quadratic = mq.agio_percentual(estimated_quadratic_price, real_price)

            models = {
                "ano": ano,
                "km": km,
                "preco": preco,
                "reqm_linear": reqm_linear,
                "reqm_quadratic": reqm_quadratic,
                "agio_linear": agio_linear,
                "agio_quadratic": agio_quadratic,
                "linear": (
                    matrix_linear,
                    vector_linear,
                    coefficients_linear,
                ),
                "quadratic": (
                    matrix_quadratic,
                    vector_quadratic,
                    coefficients_quadratic,
                ),
            }
            self._models[csv_name] = {
                "signature": signature,
                "value": models,
            }
            return models

    def clear(self):
        with self._lock:
            self._normalized.clear()
            self._models.clear()


calculation_cache = CalculationCache()




#Isso evita um erro bem comum de cors, que é o erro de cross origin request.
#Basicamente, o navegador bloqueia requisições de origens diferentes por questões de segurança. 
#Com isso, o backend permite que qualquer origem faça requisições para ele.
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.get("/api/test")
@app.get("/test")
def test_connection():
    return jsonify({
        "status": "ok",
        "message": "Conexao entre frontend e backend funcionando",
    })



def to_json_compatible(normalized_data):
    """Converte arrays NumPy em estruturas aceitas por jsonify()."""
    return {
        key: value.tolist() if hasattr(value, "tolist") else value
        for key, value in normalized_data.items()
    }


@app.get("/api/dados/onix")
def dados():
    normalized = calculation_cache.get_normalized("onix.csv")
    if normalized is None:
        normalized = get_onix_normalizado()
    return jsonify(to_json_compatible(normalized))


@app.get("/api/dados/dolphin")
def dados_dolphin():
    normalized = calculation_cache.get_normalized("dolphin_mini.csv")
    if normalized is None:
        normalized = get_dolphin_normalizado()
    return jsonify(to_json_compatible(normalized))


@app.get("/api/dados")
def dados_csv():
    return jsonify({"csv_files": list_csv_files()})


@app.get("/api/dados/<path:csv_name>")
def dados_csv_selecionado(csv_name):
    file_path = (DATA_DIR / csv_name).resolve()

    if DATA_DIR.resolve() not in file_path.parents or not file_path.is_file():
        return jsonify({"error": "Arquivo CSV nao encontrado."}), 404

    rows = []
    with file_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            try:
                rows.append({
                    "ano": int(float(row["ano"])),
                    "km": int(float(row["km"])),
                    "preco": float(row["preco"]),
                })
            except (KeyError, TypeError, ValueError):
                continue

    return jsonify({"csv_file": csv_name, "rows": rows})


@app.get("/api/funcoes/normaliza/<path:csv_name>")
def normalizar_csv_selecionado(csv_name):
    file_path = (DATA_DIR / csv_name).resolve()

    if DATA_DIR.resolve() not in file_path.parents or not file_path.is_file():
        return jsonify({"error": "Arquivo CSV nao encontrado."}), 404

    normalized = calculation_cache.get_normalized(csv_name)
    if normalized is None:
        return jsonify({"error": "Arquivo CSV nao encontrado."}), 404

    def json_compatible(value):
        if hasattr(value, "tolist"):
            return value.tolist()
        if isinstance(value, (list, tuple)):
            return [
                json_compatible(item)
                for item in value
            ]
        return value

    payload = {}
    for parameter in ("ano", "km", "preco"):
        values = json_compatible(normalized.get(parameter, []))
        if isinstance(values, list) and len(values) == 1 and isinstance(values[0], list):
            values = values[0]

        stats = json_compatible(normalized.get(f"{parameter}_stats", []))
        payload[parameter] = {
            "values": values,
            "stats": stats,
        }

    return jsonify({"csv_file": csv_name, "normalized": payload})


@app.get("/api/funcoes/modelos/<path:csv_name>")
def calcular_modelos_csv(csv_name):
    file_path = (DATA_DIR / csv_name).resolve()

    if DATA_DIR.resolve() not in file_path.parents or not file_path.is_file():
        return jsonify({"error": "Arquivo CSV nao encontrado."}), 404

    models = calculation_cache.get_models(csv_name)
    if models is None:
        normalized = calculation_cache.get_normalized(csv_name)
        if normalized is None:
            return jsonify({"error": "Nao foi possivel normalizar os dados do arquivo."}), 422
        return jsonify({"error": "Os dados normalizados possuem tamanhos invalidos."}), 422

    ano = models["ano"]
    km = models["km"]
    preco = models["preco"]
    matrix_linear, vector_linear, coefficients_linear = models["linear"]
    matrix_quadratic, vector_quadratic, coefficients_quadratic = models["quadratic"]

    return jsonify({
        "csv_file": csv_name,
        "points": {
            "ano": ano.tolist(),
            "km": km.tolist(),
            "preco": preco.tolist(),
        },
        "linear": {
            "coefficients": coefficients_linear.tolist(),
            "normal_matrix": matrix_linear.tolist(),
            "normal_vector": vector_linear.tolist(),
            "reqm": models["reqm_linear"],
            "agio": models["agio_linear"].tolist(),
        },
        "quadratic": {
            "coefficients": coefficients_quadratic.tolist(),
            "normal_matrix": matrix_quadratic.tolist(),
            "normal_vector": vector_quadratic.tolist(),
            "reqm": models["reqm_quadratic"],
            "agio": models["agio_quadratic"].tolist(),
        },
    })


@app.post("/api/funcoes/estima/<path:csv_name>")
def estimar_preco_csv(csv_name):
    file_path = (DATA_DIR / csv_name).resolve()

    if DATA_DIR.resolve() not in file_path.parents or not file_path.is_file():
        return jsonify({"error": "Arquivo CSV nao encontrado."}), 404

    payload = request.get_json(silent=True) or {}
    try:
        ano = float(payload["ano"])
        km = float(payload["km"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Ano e quilometragem sao obrigatorios."}), 400

    if ano < 1886 or km < 0:
        return jsonify({
            "error": "Informe um ano valido e uma quilometragem igual ou superior a zero."
        }), 400

    normalized = calculation_cache.get_normalized(csv_name)
    models = calculation_cache.get_models(csv_name)
    if normalized is None or models is None:
        return jsonify({"error": "Nao foi possivel calcular os modelos."}), 422

    ano_stats = normalized["ano_stats"]
    km_stats = normalized["km_stats"]
    price_stats = normalized["preco_stats"]

    ano_normalized = (ano - ano_stats[2]) / (ano_stats[1] - ano_stats[0])
    km_normalized = (km - km_stats[2]) / (km_stats[1] - km_stats[0])

    _, _, coefficients_linear = models["linear"]
    _, _, coefficients_quadratic = models["quadratic"]

    linear_vector = np.array([1, ano_normalized, km_normalized])
    quadratic_vector = np.array([
        1,
        ano_normalized,
        km_normalized,
        ano_normalized ** 2,
        ano_normalized * km_normalized,
        km_normalized ** 2,
    ])

    linear_price = desnormalize_values(
        linear_vector @ coefficients_linear,
        price_stats,
    )
    quadratic_price = desnormalize_values(
        quadratic_vector @ coefficients_quadratic,
        price_stats,
    )

    return jsonify({
        "csv_file": csv_name,
        "ano": ano,
        "km": km,
        "linear": float(linear_price),
        "quadratic": float(quadratic_price),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
