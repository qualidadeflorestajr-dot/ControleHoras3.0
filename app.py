from flask import Flask

from banco import criar_banco
from rotas import registrar_rotas

app = Flask(__name__)

app.secret_key = "FlorestaJr2026"

criar_banco()

registrar_rotas(app)

if __name__ == "__main__":
    app.run(debug=True)