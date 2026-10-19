from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from banco import listar_registros


FUSO_BRASIL = ZoneInfo("America/Sao_Paulo")


def hora_para_minutos(hora):
    try:
        h, m = map(int, hora.split(":"))
        if h < 0 or not 0 <= m < 60:
            return 0
        return h * 60 + m
    except (AttributeError, TypeError, ValueError):
        return 0


def minutos_para_hora(minutos):
    minutos = max(0, int(minutos))
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def total_semanal():
    registros = listar_registros()
    hoje = datetime.now(FUSO_BRASIL).date()
    primeiro_dia = hoje - timedelta(days=6)
    totais = {}

    for registro in registros:
        try:
            data = datetime.strptime(registro["data"], "%d/%m/%Y").date()
        except (TypeError, ValueError):
            continue
        if not primeiro_dia <= data <= hoje:
            continue

        minutos = hora_para_minutos(registro["total"])
        nome = registro["nome"]
        totais[nome] = totais.get(nome, 0) + minutos

    resultado = [
        {"nome": nome, "minutos": minutos, "total": minutos_para_hora(minutos)}
        for nome, minutos in totais.items()
    ]
    return sorted(resultado, key=lambda item: item["minutos"], reverse=True)


def ranking_top3():
    return [
        {
            "pos": str(posicao),
            "nome": pessoa["nome"],
            "total": pessoa["total"],
        }
        for posicao, pessoa in enumerate(total_semanal()[:3], start=1)
    ]


def progresso_meta():
    meta_minutos = 120
    resultado = []
    for pessoa in total_semanal():
        porcentagem = min(int(pessoa["minutos"] / meta_minutos * 100), 100)
        resultado.append({
            "nome": pessoa["nome"],
            "total": pessoa["total"],
            "porcentagem": porcentagem,
        })
    return resultado
