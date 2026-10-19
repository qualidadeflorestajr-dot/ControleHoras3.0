import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


PASTA_PROJETO = Path(__file__).resolve().parent
BANCO = Path(os.environ.get("CONTROLE_HORAS_DB", PASTA_PROJETO / "controle_horas.db"))
FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")


def conectar():
    BANCO.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(BANCO), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def agora():
    return datetime.now(FUSO_BRASIL)


def criar_banco():
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data TEXT NOT NULL,
                entrada TEXT,
                saida TEXT,
                total TEXT,
                distancia TEXT
            )
        """)


def registrar_entrada(nome, distancia="Não informado"):
    """Registra uma entrada somente se não houver outra jornada aberta."""
    nome = (nome or "").strip()
    if not nome:
        return False

    instante = agora()
    with conectar() as conn:
        conn.execute("BEGIN IMMEDIATE")
        aberta = conn.execute(
            "SELECT id FROM registros WHERE nome = ? AND COALESCE(saida, '') = '' LIMIT 1",
            (nome,),
        ).fetchone()
        if aberta:
            return False

        conn.execute(
            """INSERT INTO registros (nome, data, entrada, saida, total, distancia)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                nome,
                instante.strftime("%d/%m/%Y"),
                instante.strftime("%H:%M"),
                "",
                "",
                (str(distancia or "Não informado")[:40]),
            ),
        )
    return True


def registrar_saida(nome):
    """Finaliza a jornada aberta mais recente; retorna False se não existir."""
    nome = (nome or "").strip()
    if not nome:
        return False

    instante = agora()
    with conectar() as conn:
        conn.execute("BEGIN IMMEDIATE")
        registro = conn.execute(
            """SELECT id, entrada, data FROM registros
               WHERE nome = ? AND COALESCE(saida, '') = ''
               ORDER BY id DESC LIMIT 1""",
            (nome,),
        ).fetchone()

        if registro is None:
            return False

        try:
            entrada_dt = datetime.strptime(
                f"{registro['data']} {registro['entrada']}", "%d/%m/%Y %H:%M"
            )
            saida_dt = datetime.strptime(
                f"{instante.strftime('%d/%m/%Y')} {instante.strftime('%H:%M')}",
                "%d/%m/%Y %H:%M",
            )
        except (TypeError, ValueError):
            return False

        if saida_dt < entrada_dt:
            saida_dt += timedelta(days=1)

        minutos_totais = max(0, int((saida_dt - entrada_dt).total_seconds() // 60))
        total = f"{minutos_totais // 60:02d}:{minutos_totais % 60:02d}"

        conn.execute(
            "UPDATE registros SET saida = ?, total = ? WHERE id = ?",
            (instante.strftime("%H:%M"), total, registro["id"]),
        )
    return True


def listar_registros():
    with conectar() as conn:
        return conn.execute("SELECT * FROM registros ORDER BY id DESC").fetchall()


def total_por_membro():
    with conectar() as conn:
        linhas = conn.execute(
            "SELECT nome, total FROM registros WHERE COALESCE(total, '') <> ''"
        ).fetchall()

    totais = {}
    for linha in linhas:
        try:
            horas, minutos = map(int, linha["total"].split(":"))
            minutos_totais = horas * 60 + minutos
        except (ValueError, AttributeError):
            continue
        nome = linha["nome"]
        totais[nome] = totais.get(nome, 0) + minutos_totais

    resultado = []
    for nome, minutos in totais.items():
        resultado.append({
            "nome": nome,
            "minutos": minutos,
            "total": f"{minutos // 60:02d}:{minutos % 60:02d}",
        })
    return sorted(resultado, key=lambda item: item["minutos"], reverse=True)


def total_geral():
    minutos = sum(item["minutos"] for item in total_por_membro())
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def buscar_registro(id_registro):
    with conectar() as conn:
        return conn.execute(
            "SELECT * FROM registros WHERE id = ?", (id_registro,)
        ).fetchone()


def atualizar_registro(id_registro, nome, data, entrada, saida, total, distancia):
    with conectar() as conn:
        cursor = conn.execute(
            """UPDATE registros
               SET nome = ?, data = ?, entrada = ?, saida = ?, total = ?, distancia = ?
               WHERE id = ?""",
            (nome, data, entrada, saida, total, distancia, id_registro),
        )
        return cursor.rowcount > 0


def excluir_registro(id_registro):
    with conectar() as conn:
        cursor = conn.execute("DELETE FROM registros WHERE id = ?", (id_registro,))
        return cursor.rowcount > 0


def limpar_registros():
    with conectar() as conn:
        cursor = conn.execute("DELETE FROM registros")
        return cursor.rowcount
