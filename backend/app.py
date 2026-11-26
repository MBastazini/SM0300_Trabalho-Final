from pathlib import Path
import csv
from threading import RLock
import numpy as np

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

import minimos_quadrados as mq

from preco_de_mercado import (
    DATA_DIR,
    estima_valor,
    list_csv_files,
    normalize_values,
)


app = Flask(__name__)

SUPPORTED_MODEL_DEGREES = (0, 1, 2, 3)


class CalculationCache:
    """Guarda resultados calculados por CSV e invalida quando o arquivo muda."""

    def __init__(self):
        self._normalized = {}
        self._models = {}
        self._reqm_curves = {}
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
            for key in [key for key in self._models if key[0] == csv_name]:
                self._models.pop(key, None)
            self._reqm_curves.pop(csv_name, None)
            return normalized

    def get_models(self, csv_name, grau=2):
        normalized = self.get_normalized(csv_name)
        if normalized is None:
            return None

        signature = self._file_signature(csv_name)
        cache_key = (csv_name, grau)
        with self._lock:
            cached = self._models.get(cache_key)
            if cached is not None and cached["signature"] == signature:
                return cached["value"]

            ano = np.asarray(normalized["ano"], dtype=float).reshape(-1)
            km = np.asarray(normalized["km"], dtype=float).reshape(-1)
            preco = np.asarray(normalized["preco"], dtype=float).reshape(-1)

            if not (len(ano) == len(km) == len(preco)) or len(preco) == 0:
                return None

            if grau < 0:
                return None

            try:
                matrix, vector, coefficients = mq.solucao_sistema(
                    [ano, km], preco, grau
                )
            except np.linalg.LinAlgError:
                return None

            x_polynomial = mq.montar_matriz_X([ano, km], grau)
            estimated_normalized = x_polynomial @ coefficients

            price_stats = normalized["preco_stats"]
            real_price = mq.desnormalize_test_values(preco, price_stats)
            estimated_price = mq.desnormalize_test_values(
                estimated_normalized,
                price_stats,
            )

            reqm = float(mq.REQM(estimated_price, real_price))
            agio = mq.agio_percentual(estimated_price, real_price)

            models = {
                "ano": ano,
                "km": km,
                "preco": preco,
                "degree": grau,
                "reqm": reqm,
                "agio": agio,
                "polynomial": (
                    matrix,
                    vector,
                    coefficients,
                ),
            }
            self._models[cache_key] = {
                "signature": signature,
                "value": models,
            }
            return models

    def get_reqm_curve(self, csv_name):
        normalized = self.get_normalized(csv_name)
        if normalized is None:
            return None

        signature = self._file_signature(csv_name)
        with self._lock:
            cached = self._reqm_curves.get(csv_name)
            if cached is not None and cached["signature"] == signature:
                return cached["value"]

            ano = np.asarray(normalized["ano"], dtype=float).reshape(-1)
            km = np.asarray(normalized["km"], dtype=float).reshape(-1)
            preco = np.asarray(normalized["preco"], dtype=float).reshape(-1)
            if not (len(ano) == len(km) == len(preco)) or len(preco) == 0:
                return None

            columns = [
                (ano ** (degree - km_exponent)) * (km ** km_exponent)
                for degree in range(31)
                for km_exponent in range(degree + 1)
            ]
            design = np.column_stack(columns)
            real_price = mq.desnormalize_test_values(preco, normalized["preco_stats"])
            reqm_values = []

            for degree in range(31):
                feature_count = (degree + 1) * (degree + 2) // 2
                coefficients = np.linalg.lstsq(
                    design[:, :feature_count],
                    preco,
                    rcond=None,
                )[0]
                estimated_price = mq.desnormalize_test_values(
                    design[:, :feature_count] @ coefficients,
                    normalized["preco_stats"],
                )
                reqm_values.append(float(mq.REQM(estimated_price, real_price)))

            curve = {
                "degrees": list(range(31)),
                "values": reqm_values,
            }
            self._reqm_curves[csv_name] = {
                "signature": signature,
                "value": curve,
            }
            return curve

    def clear(self):
        with self._lock:
            self._normalized.clear()
            self._models.clear()
            self._reqm_curves.clear()


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
        normalized = normalize_values("onix_bruto.csv", ["ano", "preco", "km"])
    return jsonify(to_json_compatible(normalized))


@app.get("/api/dados/dolphin")
def dados_dolphin():
    normalized = calculation_cache.get_normalized("dolphin_mini.csv")
    if normalized is None:
        normalized = normalize_values("dolphin_mini_bruto.csv", ["ano", "preco", "km"])
    return jsonify(to_json_compatible(normalized))


@app.get("/api/dados")
def dados_csv():
    return jsonify({"csv_files": list_csv_files()})


@app.post("/api/dados/upload")
def upload_csv():
    uploaded_file = request.files.get("file")

    if uploaded_file is None or uploaded_file.filename == "":
        return jsonify({"error": "Selecione um arquivo CSV."}), 400

    filename = secure_filename(uploaded_file.filename)
    if not filename or not filename.lower().endswith(".csv"):
        return jsonify({"error": "O arquivo deve ter extensao .csv."}), 400

    try:
        uploaded_file.stream.seek(0)
        text = uploaded_file.stream.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return jsonify({"error": "O CSV deve estar codificado em UTF-8."}), 400

    import io
    reader = csv.DictReader(io.StringIO(text))
    required_columns = {"ano", "km", "preco"}
    headers = {
        (header or "").strip().lower()
        for header in (reader.fieldnames or [])
    }

    if not required_columns.issubset(headers):
        missing = sorted(required_columns - headers)
        return jsonify({
            "error": "Colunas obrigatorias ausentes.",
            "missing": missing,
        }), 400

    valid_rows = 0
    for row in reader:
        try:
            normalized_row = {
                str(key).strip().lower(): value
                for key, value in row.items()
                if key is not None
            }
            year = float(normalized_row["ano"])
            km = float(normalized_row["km"])
            price = float(normalized_row["preco"])
        except (KeyError, TypeError, ValueError):
            return jsonify({
                "error": "Todas as linhas devem conter ano, km e preco numericos."
            }), 400

        if year < 1886 or km < 0 or price <= 0:
            return jsonify({
                "error": "Ano deve ser valido, quilometragem nao negativa e preco positivo."
            }), 400
        valid_rows += 1

    if valid_rows == 0:
        return jsonify({"error": "O CSV nao possui linhas de dados."}), 400

    file_path = DATA_DIR / filename
    file_path.write_text(text, encoding="utf-8")
    calculation_cache.clear()

    return jsonify({
        "message": "CSV adicionado com sucesso.",
        "csv_file": filename,
        "row_count": valid_rows,
    }), 201


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

    try:
        grau = int(request.args.get("grau", 2))
    except (TypeError, ValueError):
        return jsonify({"error": "O grau deve ser um inteiro entre 0 e 3."}), 400
    if grau not in SUPPORTED_MODEL_DEGREES:
        return jsonify({"error": "O grau deve ser um inteiro entre 0 e 3."}), 400

    models = calculation_cache.get_models(csv_name, grau)
    if models is None:
        normalized = calculation_cache.get_normalized(csv_name)
        if normalized is None:
            return jsonify({"error": "Nao foi possivel normalizar os dados do arquivo."}), 422
        return jsonify({"error": "Os dados normalizados possuem tamanhos invalidos."}), 422

    reqm_curve = calculation_cache.get_reqm_curve(csv_name)
    if reqm_curve is None:
        return jsonify({"error": "Nao foi possivel calcular a REQM por grau."}), 422

    ano = models["ano"]
    km = models["km"]
    preco = models["preco"]
    matrix, vector, coefficients = models["polynomial"]

    return jsonify({
        "csv_file": csv_name,
        "degree": models["degree"],
        "reqm_curve": reqm_curve,
        "points": {
            "ano": ano.tolist(),
            "km": km.tolist(),
            "preco": preco.tolist(),
        },
        "polynomial": {
            "coefficients": coefficients.tolist(),
            "normal_matrix": matrix.tolist(),
            "normal_vector": vector.tolist(),
            "reqm": models["reqm"],
            "agio": models["agio"].tolist(),
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
    try:
        grau = int(payload.get("grau", 2))
    except (TypeError, ValueError):
        return jsonify({"error": "O grau deve ser um inteiro entre 0 e 3."}), 400

    if ano < 1886 or km < 0:
        return jsonify({
            "error": "Informe um ano valido e uma quilometragem igual ou superior a zero."
        }), 400

    normalized = calculation_cache.get_normalized(csv_name)
    if normalized is None:
        return jsonify({"error": "Nao foi possivel normalizar os dados."}), 422

    if grau not in SUPPORTED_MODEL_DEGREES:
        return jsonify({"error": "O grau deve ser um inteiro entre 0 e 3."}), 400

    models = calculation_cache.get_models(csv_name, grau)
    if models is None:
        return jsonify({"error": "Nao foi possivel calcular o modelo."}), 422
    _, _, coefficients = models["polynomial"]

    polynomial_price = estima_valor(
        {"ano": ano, "km": km},
        grau,
        normalized,
        coefficients,
    )

    return jsonify({
        "csv_file": csv_name,
        "ano": ano,
        "km": km,
        "degree": grau,
        "polynomial": float(polynomial_price),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
