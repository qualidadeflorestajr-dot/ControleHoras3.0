import sqlite3

from datetime import datetime

from zoneinfo import ZoneInfo

BANCO = "controle_horas.db"

# ===================================================
# CONEXÃO
# ===================================================

def conectar():

    return sqlite3.connect(BANCO)


# ===================================================
# DATA E HORA DO BRASIL
# ===================================================

def agora():

    return datetime.now(
        ZoneInfo("America/Sao_Paulo")
    )


# ===================================================
# CRIAR BANCO
# ===================================================

def criar_banco():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS registros(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL,

            data TEXT NOT NULL,

            entrada TEXT,

            saida TEXT,

            total TEXT

        )

    """)

    conn.commit()

    conn.close()
    # ===================================================
# REGISTRAR ENTRADA
# ===================================================

def registrar_entrada(nome):

    conn = conectar()

    cursor = conn.cursor()

    data = agora().strftime("%d/%m/%Y")

    hora = agora().strftime("%H:%M")

    cursor.execute("""

        INSERT INTO registros(

            nome,
            data,
            entrada,
            saida,
            total

        )

        VALUES(?,?,?,?,?)

    """, (

        nome,
        data,
        hora,
        "",
        ""

    ))

    conn.commit()

    conn.close()


# ===================================================
# REGISTRAR SAÍDA
# ===================================================

def registrar_saida(nome):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT id, entrada

        FROM registros

        WHERE nome=?

        AND saida=''

        ORDER BY id DESC

        LIMIT 1

    """, (nome,))

    registro = cursor.fetchone()

    if registro is None:

        conn.close()

        return

    id_registro = registro[0]

    entrada = registro[1]

    saida = agora().strftime("%H:%M")

    hora_entrada = datetime.strptime(entrada, "%H:%M")

    hora_saida = datetime.strptime(saida, "%H:%M")

    diferenca = hora_saida - hora_entrada

    horas = diferenca.seconds // 3600

    minutos = (diferenca.seconds % 3600) // 60

    total = f"{horas:02d}:{minutos:02d}"

    cursor.execute("""

        UPDATE registros

        SET

            saida=?,
            total=?

        WHERE id=?

    """, (

        saida,
        total,
        id_registro

    ))

    conn.commit()

    conn.close()


# ===================================================
# LISTAR REGISTROS
# ===================================================

def listar_registros():

    conn = conectar()

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM registros

        ORDER BY id DESC

    """)

    registros = cursor.fetchall()

    conn.close()

    return registros
# ===================================================
# TOTAL POR MEMBRO
# ===================================================

def total_por_membro():

    conn = conectar()

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""

        SELECT nome, total

        FROM registros

        WHERE total <> ''

    """)

    linhas = cursor.fetchall()

    conn.close()

    totais = {}

    for linha in linhas:

        nome = linha["nome"]

        horas, minutos = map(int, linha["total"].split(":"))

        minutos_totais = horas * 60 + minutos

        totais[nome] = totais.get(nome, 0) + minutos_totais

    resultado = []

    for nome, minutos in totais.items():

        h = minutos // 60

        m = minutos % 60

        resultado.append({

            "nome": nome,

            "minutos": minutos,

            "total": f"{h:02d}:{m:02d}"

        })

    resultado.sort(

        key=lambda x: x["minutos"],

        reverse=True

    )

    return resultado


# ===================================================
# TOP 3
# ===================================================

def ranking_top3_bd():

    return total_por_membro()[:3]


# ===================================================
# TOTAL GERAL
# ===================================================

def total_geral():

    totais = total_por_membro()

    minutos = sum(x["minutos"] for x in totais)

    horas = minutos // 60

    resto = minutos % 60

    return f"{horas:02d}:{resto:02d}"


# ===================================================
# BUSCAR REGISTRO
# ===================================================

def buscar_registro(id_registro):

    conn = conectar()

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM registros WHERE id=?",

        (id_registro,)

    )

    registro = cursor.fetchone()

    conn.close()

    return registro


# ===================================================
# EXCLUIR REGISTRO
# ===================================================

def excluir_registro(id_registro):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM registros WHERE id=?",

        (id_registro,)

    )

    conn.commit()

    conn.close()
    # ===================================================
# EXCLUIR UM REGISTRO
# ===================================================

def excluir_registro(id_registro):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM registros WHERE id=?",

        (id_registro,)

    )

    conn.commit()

    conn.close()


# ===================================================
# APAGAR TODOS OS REGISTROS
# ===================================================

def limpar_registros():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(

        "DELETE FROM registros"

    )

    conn.commit()

    conn.close()
        # ==================================================
    # EXCLUIR REGISTRO
    # ==================================================

    @app.route("/excluir/<int:id_registro>")
    def excluir(id_registro):

        if not session.get("admin"):

            return redirect("/")

        excluir_registro(id_registro)

        flash("Registro excluído com sucesso!")

        return redirect("/admin")


    # ==================================================
    # LIMPAR TODOS OS REGISTROS
    # ==================================================

    @app.route("/limpar")
    def limpar():

        if not session.get("admin"):

            return redirect("/")

        limpar_registros()

        flash("Todos os registros foram removidos!")

        return redirect("/admin")
    # ===================================================
# BUSCAR REGISTRO PELO ID
# ===================================================

def buscar_registro(id_registro):

    conn = conectar()

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM registros WHERE id = ?",

        (id_registro,)

    )

    registro = cursor.fetchone()

    conn.close()

    return registro
# ===================================================
# ATUALIZAR REGISTRO
# ===================================================

def atualizar_registro(
    id_registro,
    nome,
    data,
    entrada,
    saida,
    total
):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(

        """
        UPDATE registros
        SET
            nome = ?,
            data = ?,
            entrada = ?,
            saida = ?,
            total = ?
        WHERE id = ?
        """,

        (

            nome,
            data,
            entrada,
            saida,
            total,
            id_registro

        )

    )

    conn.commit()

    conn.close()