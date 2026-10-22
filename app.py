import hmac
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, request, session

from banco import criar_banco, encerrar_jornadas_expiradas
from rotas import registrar_rotas


# Carrega configurações locais do .env sem sobrescrever variáveis do ambiente.
# O arquivo .env é ignorado pelo Git e não deve ser publicado.
load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1").lower() not in {"0", "false", "no"},
)

if not app.config["SECRET_KEY"]:
    # Em desenvolvimento, cria uma chave persistente automaticamente para não
    # exigir configuração manual a cada inicialização do Codespaces.
    chave_local = Path(__file__).resolve().parent / ".flask_secret_key"
    try:
        chave = chave_local.read_text(encoding="utf-8").strip() if chave_local.exists() else ""
        if not chave:
            chave = secrets.token_hex(32)
            chave_local.write_text(chave + "\\n", encoding="utf-8")
        app.config["SECRET_KEY"] = chave
    except OSError:
        # Fallback para ambientes sem permissão de gravar arquivos locais.
        app.config["SECRET_KEY"] = secrets.token_hex(32)



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
