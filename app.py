import os
from pathlib import Path

from flask import Flask
from banco import criar_banco
from rotas import registrar_rotas


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1").lower() not in {"0", "false", "no"},
)

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "Configure a variável de ambiente FLASK_SECRET_KEY antes de iniciar a aplicação."
    )

criar_banco()
registrar_rotas(app)


if __name__ == "__main__":
    # Para desenvolvimento local, configure FLASK_SECRET_KEY no ambiente.
    app.run(debug=os.environ.get("FLASK_DEBUG", "").lower() == "true")
