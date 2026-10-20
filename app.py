import hmac
import os
import secrets

from flask import Flask, abort, request, session

from banco import criar_banco, encerrar_jornadas_expiradas
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


@app.context_processor
def fornecer_token_csrf():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["_csrf_token"]}


@app.before_request
def validar_csrf():
    # Verifica jornadas vencidas em toda requisição recebida pela aplicação.
    encerrar_jornadas_expiradas()
    if request.method == "POST":
        esperado = session.get("_csrf_token", "")
        recebido = request.form.get("csrf_token", "")
        if not esperado or not recebido or not hmac.compare_digest(esperado, recebido):
            abort(400, description="Token de segurança inválido. Atualize a página e tente novamente.")


criar_banco()
registrar_rotas(app)


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "").lower() == "true")
