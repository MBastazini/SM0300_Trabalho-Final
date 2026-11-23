from pathlib import Path
import csv

from flask import Flask, jsonify

from preco_de_mercado import (
    DATA_DIR,
    get_dolphin_normalizado,
    get_onix_normalizado,
    list_csv_files,
    normalize_values,
)


app = Flask(__name__)




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
    return jsonify(to_json_compatible(get_onix_normalizado()))


@app.get("/api/dados/dolphin")
def dados_dolphin():
    return jsonify(to_json_compatible(get_dolphin_normalizado()))


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

    normalized = normalize_values(csv_name, ["ano", "km", "preco"])

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
