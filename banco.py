import os
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from membros import MEMBROS


BANCO = Path(os.environ.get("CONTROLE_HORAS_DB", "controle_horas.db"))
FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")


def conectar():
    BANCO.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(BANCO), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def transacao():
    conn = conectar()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def agora():
    return datetime.now(FUSO_BRASIL)


def criar_banco():
    with transacao() as conn:
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS membros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE COLLATE NOCASE,
                ativo INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.executemany(
            "INSERT OR IGNORE INTO membros (nome, ativo) VALUES (?, 1)",
            [(nome.strip(),) for nome in MEMBROS if nome.strip()],
        )


def listar_membros():
    """Lista membros ativos em ordem alfabética, ignorando acentos na ordenação."""
    with transacao() as conn:
        nomes = [linha["nome"] for linha in conn.execute(
            "SELECT nome FROM membros WHERE ativo = 1"
        ).fetchall()]
    def chave_alfabetica(nome):
        sem_acentos = unicodedata.normalize("NFKD", nome)
        return "".join(caractere for caractere in sem_acentos
                       if not unicodedata.combining(caractere)).casefold()
    return sorted(nomes, key=chave_alfabetica)


def adicionar_membro(nome):
    nome = " ".join((nome or "").split())
    if not nome or len(nome) > 100:
        return False, "Informe um nome de até 100 caracteres."
    with transacao() as conn:
        existente = conn.execute(
            "SELECT id, ativo FROM membros WHERE nome = ? COLLATE NOCASE", (nome,)
        ).fetchone()
        if existente:
            if existente["ativo"]:
                return False, "Esse membro já está cadastrado."
            conn.execute("UPDATE membros SET ativo = 1, nome = ? WHERE id = ?", (nome, existente["id"]))
            return True, "Membro reativado com sucesso."
        conn.execute("INSERT INTO membros (nome, ativo) VALUES (?, 1)", (nome,))
    return True, "Membro adicionado com sucesso."


def excluir_membro(nome):
    nome = (nome or "").strip()
    with transacao() as conn:
        aberta = conn.execute(
            "SELECT 1 FROM registros WHERE nome = ? AND COALESCE(saida, '') = '' LIMIT 1",
            (nome,),
        ).fetchone()
        if aberta:
            return False, "Este membro possui uma jornada aberta. Registre a saída antes de desativá-lo."
        cursor = conn.execute(
            "UPDATE membros SET ativo = 0 WHERE nome = ? COLLATE NOCASE AND ativo = 1",
            (nome,),
        )
        if cursor.rowcount == 0:
            return False, "Membro não encontrado ou já desativado."
    return True, "Membro desativado. O histórico de registros foi preservado."


def encerrar_jornadas_expiradas():
    """Após oito horas sem saída, encerra o registro e fixa o total em duas horas."""
    instante = agora().replace(tzinfo=None)
    atualizados = 0
    with transacao() as conn:
        abertas = conn.execute(
            """SELECT id, data, entrada FROM registros
               WHERE COALESCE(saida, '') = '' AND COALESCE(entrada, '') <> ''"""
        ).fetchall()
        for registro in abertas:
            try:
                inicio = datetime.strptime(
                    f"{registro['data']} {registro['entrada']}", "%d/%m/%Y %H:%M"
                )
            except (TypeError, ValueError):
                continue
            encerramento = inicio + timedelta(hours=8)
            if instante >= encerramento:
                conn.execute(
                    "UPDATE registros SET saida = ?, total = '02:00' WHERE id = ? AND COALESCE(saida, '') = ''",
                    (encerramento.strftime("%H:%M"), registro["id"]),
                )
                atualizados += 1
    return atualizados


def registrar_entrada(nome, distancia="Não informado"):
    nome = (nome or "").strip()
    if not nome:
        return False
    instante = agora()
    with transacao() as conn:
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
            (nome, instante.strftime("%d/%m/%Y"), instante.strftime("%H:%M"), "", "", str(distancia or "Não informado")[:40]),
        )
    return True


def registrar_saida(nome):
    nome = (nome or "").strip()
    if not nome:
        return False
    encerrar_jornadas_expiradas()
    instante = agora()
    with transacao() as conn:
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
                f"{instante.strftime('%d/%m/%Y')} {instante.strftime('%H:%M')}", "%d/%m/%Y %H:%M"
            )
        except (TypeError, ValueError):
            return False
        if saida_dt < entrada_dt:
            saida_dt += timedelta(days=1)
        minutos_totais = max(0, int((saida_dt - entrada_dt).total_seconds() // 60))
        if minutos_totais >= 8 * 60:
            saida_final = entrada_dt + timedelta(hours=8)
            saida_texto, total = saida_final.strftime("%H:%M"), "02:00"
        else:
            saida_texto = instante.strftime("%H:%M")
            total = f"{minutos_totais // 60:02d}:{minutos_totais % 60:02d}"
        conn.execute(
            "UPDATE registros SET saida = ?, total = ? WHERE id = ?",
            (saida_texto, total, registro["id"]),
        )
    return True


def listar_registros():
    with transacao() as conn:
        return conn.execute("SELECT * FROM registros ORDER BY id DESC").fetchall()


def total_por_membro():
    with transacao() as conn:
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
        resultado.append({"nome": nome, "minutos": minutos, "total": f"{minutos // 60:02d}:{minutos % 60:02d}"})
    return sorted(resultado, key=lambda item: item["minutos"], reverse=True)


def total_geral():
    minutos = sum(item["minutos"] for item in total_por_membro())
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def buscar_registro(id_registro):
    with transacao() as conn:
        return conn.execute("SELECT * FROM registros WHERE id = ?", (id_registro,)).fetchone()


def atualizar_registro(id_registro, nome, data, entrada, saida, total, distancia):
    with transacao() as conn:
        cursor = conn.execute(
            """UPDATE registros
               SET nome = ?, data = ?, entrada = ?, saida = ?, total = ?, distancia = ?
               WHERE id = ?""",
            (nome, data, entrada, saida, total, distancia, id_registro),
        )
        return cursor.rowcount > 0


def excluir_registro(id_registro):
    with transacao() as conn:
        cursor = conn.execute("DELETE FROM registros WHERE id = ?", (id_registro,))
        return cursor.rowcount > 0


def limpar_registros():
    with transacao() as conn:
        cursor = conn.execute("DELETE FROM registros")
        return cursor.rowcount
