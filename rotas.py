from flask import (
    render_template,
    request,
    redirect,
    send_file,
    session,
    flash
)

from membros import MEMBROS

from banco import (
    listar_registros,
    registrar_entrada,
    registrar_saida,
    excluir_registro,
    limpar_registros,
    buscar_registro,
    atualizar_registro
)

from utils import (
    ranking_top3,
    total_semanal,
    progresso_meta
)

from relatorios.relatorio import criar_relatorio


def registrar_rotas(app):

    # ==========================================
    # PÁGINA INICIAL
    # ==========================================

    @app.route("/")
    def home():

        registros = listar_registros()

        return render_template(
            "index.html",
            membros=MEMBROS,
            registros=registros,
            ranking=ranking_top3(),
            semanal=total_semanal(),
            progresso=progresso_meta()
        )


    # ==========================================
    # EDITAR REGISTRO
    # ==========================================

    @app.route("/editar/<int:id_registro>", methods=["GET", "POST"])
    def editar(id_registro):

        if not session.get("admin"):

            flash("Faça login como administrador.")

            return redirect("/")


        registro = buscar_registro(id_registro)


        if registro is None:

            flash("Registro não encontrado.")

            return redirect("/admin")


        if request.method == "POST":

            nome = request.form.get("nome")
            data = request.form.get("data")
            entrada = request.form.get("entrada")
            saida = request.form.get("saida")
            total = request.form.get("total")
            distancia = request.form.get("distancia")


            atualizar_registro(
                id_registro,
                nome,
                data,
                entrada,
                saida,
                total,
                distancia
            )


            flash("Registro atualizado com sucesso!")

            return redirect("/admin")


        return render_template(
            "editar.html",
            registro=registro
        )


    # ==========================================
    # REGISTRAR ENTRADA
    # ==========================================

    @app.route("/entrada", methods=["POST"])
    def entrada():

        nome = request.form.get("nome")

        if not nome:

            flash("Selecione um membro.")

            return redirect("/")


        distancia = request.form.get("distancia", "")


        registrar_entrada(
            nome,
            distancia
        )


        flash(f"Entrada de {nome} registrada com sucesso!")

        return redirect("/")


    # ==========================================
    # REGISTRAR SAÍDA
    # ==========================================

    @app.route("/saida", methods=["POST"])
    def saida():

        nome = request.form.get("nome")

        if not nome:

            flash("Selecione um membro.")

            return redirect("/")


        registrar_saida(nome)


        flash(f"Saída de {nome} registrada com sucesso!")

        return redirect("/")


    # ==========================================
    # EXPORTAR RELATÓRIO
    # ==========================================

    @app.route("/exportar")
    def exportar():

        arquivo = criar_relatorio()

        return send_file(
            arquivo,
            as_attachment=True,
            download_name="Controle_Horas_Floresta_Jr_2026_2.xlsx"
        )


    # ==========================================
    # ÁREA ADMINISTRATIVA
    # ==========================================

    @app.route("/admin")
    def admin():

        if not session.get("admin"):

            return render_template("login_admin.html")


        registros = listar_registros()


        return render_template(
            "admin.html",
            registros=registros
        )


    # ==========================================
    # LOGIN ADMINISTRADOR
    # ==========================================

    SENHA_ADMIN = "Qualidade2026/2"


    @app.route("/login_admin", methods=["POST"])
    def login_admin():

        senha = request.form.get("senha")


        if senha == SENHA_ADMIN:

            session["admin"] = True

            flash("Login realizado com sucesso!")

            return redirect("/admin")


        flash("Senha incorreta!")

        return redirect("/")


    # ==========================================
    # LOGOUT
    # ==========================================

    @app.route("/logout")
    def logout():

        session.pop("admin", None)

        flash("Logout realizado com sucesso!")

        return redirect("/")


    # ==========================================
    # EXCLUIR REGISTRO
    # ==========================================

    @app.route("/excluir/<int:id_registro>")
    def excluir(id_registro):

        if not session.get("admin"):

            flash("Faça login como administrador.")

            return redirect("/")


        excluir_registro(id_registro)


        flash("Registro excluído com sucesso!")

        return redirect("/admin")


    # ==========================================
    # LIMPAR TODOS OS REGISTROS
    # ==========================================

    @app.route("/limpar")
    def limpar():

        if not session.get("admin"):

            flash("Faça login como administrador.")

            return redirect("/")


        limpar_registros()


        flash("Todos os registros foram removidos!")

        return redirect("/admin")


    # ==========================================
    # EXPORTAR E LIMPAR SEMANA
    # ==========================================

    @app.route("/exportar_limpar")
    def exportar_limpar():

        if not session.get("admin"):

            flash("Faça login como administrador.")

            return redirect("/")


        arquivo = criar_relatorio()


        limpar_registros()


        return send_file(
            arquivo,
            as_attachment=True,
            download_name="Controle_Horas_Floresta_Jr_2026_2.xlsx"
        )