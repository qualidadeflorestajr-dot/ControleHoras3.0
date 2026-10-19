import hmac
import logging
import os
from functools import wraps

from flask import (
    abort, current_app, flash, redirect, render_template, request,
    send_file, session, url_for
)

from membros import MEMBROS
from banco import (
    atualizar_registro, buscar_registro, excluir_registro, limpar_registros,
    listar_registros, registrar_entrada, registrar_saida,
)
from relatorios.relatorio import criar_relatorio, nome_arquivo_relatorio
from utils import progresso_meta, ranking_top3, total_semanal


logger = logging.getLogger(__name__)


def registrar_rotas(app):
    senha_admin = os.environ.get("ADMIN_PASSWORD")

    def admin_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("admin"):
                flash("Faça login como administrador.")
                return redirect(url_for("admin"))
            return view(*args, **kwargs)
        return wrapped

    @app.route("/")
    def home():
        return render_template(
            "index.html",
            membros=MEMBROS,
            registros=listar_registros(),
            ranking=ranking_top3(),
            semanal=total_semanal(),
            progresso=progresso_meta(),
        )

    @app.route("/entrada", methods=["POST"])
    def entrada():
        nome = request.form.get("nome", "").strip()
        if nome not in MEMBROS:
            flash("Selecione um membro válido.")
            return redirect(url_for("home"))

        distancia = request.form.get("distancia", "Não informado")
        if len(distancia) > 40:
            distancia = "Não informado"

        if registrar_entrada(nome, distancia):
            flash(f"Entrada de {nome} registrada com sucesso.")
        else:
            flash(f"{nome} já possui uma entrada sem saída registrada.")
        return redirect(url_for("home"))

    @app.route("/saida", methods=["POST"])
    def saida():
        nome = request.form.get("nome", "").strip()
        if nome not in MEMBROS:
            flash("Selecione um membro válido.")
            return redirect(url_for("home"))

        if registrar_saida(nome):
            flash(f"Saída de {nome} registrada com sucesso.")
        else:
            flash(f"Não foi encontrada uma entrada aberta para {nome}.")
        return redirect(url_for("home"))

    @app.route("/exportar", methods=["GET"])
    @admin_required
    def exportar():
        try:
            arquivo = criar_relatorio()
            return send_file(
                arquivo,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=nome_arquivo_relatorio(),
            )
        except Exception:
            logger.exception("Falha ao gerar relatório Excel")
            flash("Não foi possível gerar o relatório. Consulte o log do servidor.")
            return redirect(url_for("admin"))

    @app.route("/admin")
    def admin():
        if not session.get("admin"):
            return render_template("login_admin.html")
        return render_template("admin.html", registros=listar_registros())

    @app.route("/login_admin", methods=["POST"])
    def login_admin():
        if not senha_admin:
            current_app.logger.error("A variável ADMIN_PASSWORD não está configurada.")
            flash("A área administrativa ainda não foi configurada pelo responsável.")
            return redirect(url_for("admin"))

        senha = request.form.get("senha", "")
        if hmac.compare_digest(senha, senha_admin):
            session.clear()
            session["admin"] = True
            flash("Login realizado com sucesso.")
            return redirect(url_for("admin"))

        flash("Senha incorreta.")
        return redirect(url_for("admin"))

    @app.route("/logout", methods=["POST"])
    @admin_required
    def logout():
        session.clear()
        flash("Sessão encerrada.")
        return redirect(url_for("home"))

    @app.route("/editar/<int:id_registro>", methods=["GET", "POST"])
    @admin_required
    def editar(id_registro):
        registro = buscar_registro(id_registro)
        if registro is None:
            flash("Registro não encontrado.")
            return redirect(url_for("admin"))

        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            data_iso = request.form.get("data", "")
            entrada = request.form.get("entrada", "")
            saida = request.form.get("saida", "")
            total = request.form.get("total", "").strip()
            distancia = request.form.get("distancia", "Não informado").strip()

            from datetime import datetime
            try:
                data = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
                datetime.strptime(entrada, "%H:%M")
                if saida:
                    datetime.strptime(saida, "%H:%M")
                if total and (len(total.split(":")) != 2 or any(int(x) < 0 for x in total.split(":"))):
                    raise ValueError
                if nome not in MEMBROS:
                    raise ValueError
            except (ValueError, TypeError):
                flash("Confira o nome, a data e os horários informados.")
                return render_template("editar.html", registro=registro)

            if saida:
                from datetime import timedelta
                inicio = datetime.strptime(entrada, "%H:%M")
                fim = datetime.strptime(saida, "%H:%M")
                if fim < inicio:
                    fim += timedelta(days=1)
                minutos = int((fim - inicio).total_seconds() // 60)
                total = f"{minutos // 60:02d}:{minutos % 60:02d}"
            else:
                total = ""

            atualizar_registro(
                id_registro, nome, data, entrada, saida, total,
                distancia[:40] or "Não informado",
            )
            flash("Registro atualizado com sucesso.")
            return redirect(url_for("admin"))

        return render_template("editar.html", registro=registro)

    @app.route("/excluir/<int:id_registro>", methods=["POST"])
    @admin_required
    def excluir(id_registro):
        if excluir_registro(id_registro):
            flash("Registro excluído com sucesso.")
        else:
            flash("Registro não encontrado.")
        return redirect(url_for("admin"))

    @app.route("/limpar", methods=["POST"])
    @admin_required
    def limpar():
        quantidade = limpar_registros()
        flash(f"Registros removidos: {quantidade}.")
        return redirect(url_for("admin"))

    # A rota antiga que exportava e apagava dados foi deliberadamente removida:
    # exportar um relatório nunca deve apagar os dados automaticamente.
