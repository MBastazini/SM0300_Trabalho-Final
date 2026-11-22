from pathlib import Path

from flask import Flask, jsonify

from preco_de_mercado import get_onix_normalizado, get_dolphin_normalizado


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
