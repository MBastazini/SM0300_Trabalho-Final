from pathlib import Path

from flask import Flask, jsonify


app = Flask(__name__)

# The data directory is relative to the repository, not the process location.
DATA_DIR = Path(__file__).resolve().parent.parent / "dados"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def list_csv_files():
    """Return the CSV files available in the data directory."""
    return sorted(path.name for path in DATA_DIR.glob("*.csv") if path.is_file())


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


@app.get("/api/dados")
@app.get("/dados")
def dados():
    return jsonify({
        "directory": str(DATA_DIR),
        "csv_files": list_csv_files(),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
