import hmac
import os
import secrets
from pathlib import Path

from flask import Flask, abort, request, session

from banco import criar_banco, encerrar_jornadas_expiradas


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
ENV_FILE = BASE_DIR / ".env"


def carregar_arquivo_env():
    """Carrega .env sem dependência externa; variáveis do servidor têm prioridade."""
    if not ENV_FILE.is_file():
        return
    for linha in ENV_FILE.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        nome, valor = linha.split("=", 1)
        nome = nome.strip()
        valor = valor.strip().strip('"').strip("'")
        if nome and nome not in os.environ:
            os.environ[nome] = valor


def obter_chave_secreta():
    """Usa variável configurada ou uma chave persistente local, nunca uma chave temporária."""
    chave = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY")
    if chave:
        return chave

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    arquivo_chave = INSTANCE_DIR / "flask_secret_key"
    try:
        if arquivo_chave.is_file():
            chave = arquivo_chave.read_text(encoding="utf-8").strip()
            if chave:
                return chave

        chave = secrets.token_hex(32)
        # Criação exclusiva evita substituir a chave se dois processos iniciarem juntos.
        try:
            with arquivo_chave.open("x", encoding="utf-8") as arquivo:
                arquivo.write(chave)
            try:
                arquivo_chave.chmod(0o600)
            except OSError:
                pass
            return chave
        except FileExistsError:
            chave = arquivo_chave.read_text(encoding="utf-8").strip()
            if chave:
                return chave
            raise RuntimeError("O arquivo instance/flask_secret_key está vazio.")
    except OSError as erro:
        raise RuntimeError(
            "Não foi possível salvar a chave secreta. Configure FLASK_SECRET_KEY "
            "nas variáveis de ambiente do servidor."
        ) from erro


# Lê .env local/servidor antes de importar as rotas que leem ADMIN_PASSWORD.
carregar_arquivo_env()

from rotas import registrar_rotas  # noqa: E402


app = Flask(__name__)
app.config.update(
    SECRET_KEY=obter_chave_secreta(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1").lower()
    not in {"0", "false", "no"},
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
