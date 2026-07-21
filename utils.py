from datetime import datetime, timedelta
from banco import listar_registros


# ==========================================
# CONVERTE HH:MM PARA MINUTOS
# ==========================================

def hora_para_minutos(hora):

    try:

        h, m = map(int, hora.split(":"))

        return h * 60 + m

    except:

        return 0


# ==========================================
# CONVERTE MINUTOS PARA HH:MM
# ==========================================

def minutos_para_hora(minutos):

    horas = minutos // 60

    minutos = minutos % 60

    return f"{horas:02d}:{minutos:02d}"


# ==========================================
# TOTAL SEMANAL
# ==========================================

def total_semanal():

    registros = listar_registros()

    hoje = datetime.now()

    semana = hoje - timedelta(days=7)

    totais = {}

    for r in registros:

        try:

            data = datetime.strptime(r["data"], "%d/%m/%Y")

        except:

            continue

        if data < semana:

            continue

        nome = r["nome"]

        minutos = hora_para_minutos(r["total"])

        totais[nome] = totais.get(nome, 0) + minutos

    resultado = []

    for nome, minutos in totais.items():

        resultado.append({

            "nome": nome,

            "minutos": minutos,

            "total": minutos_para_hora(minutos)

        })

    resultado.sort(

        key=lambda x: x["minutos"],

        reverse=True

    )

    return resultado


# ==========================================
# TOP 3
# ==========================================

def ranking_top3():

    ranking = total_semanal()

    medalhas = ["🥇", "🥈", "🥉"]

    top = []

    for i, pessoa in enumerate(ranking[:3]):

        top.append({

            "pos": medalhas[i],

            "nome": pessoa["nome"],

            "total": pessoa["total"]

        })

    return top


# ==========================================
# META DAS 2 HORAS
# ==========================================

def progresso_meta():

    dados = total_semanal()

    resultado = []

    META = 120

    for pessoa in dados:

        porcentagem = int(

            min(

                pessoa["minutos"] / META * 100,

                100

            )

        )

        resultado.append({

            "nome": pessoa["nome"],

            "total": pessoa["total"],

            "porcentagem": porcentagem

        })

    return resultado