import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json

MOOMBOX_URL = "https://expositores.moombox.com.br"
USUARIO = "moombox"
SENHA = "admin2020b"
DATA_SIMULADA = os.environ.get("DATA_SIMULADA", "")

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})


def login():
    r = session.get(MOOMBOX_URL + "/user/login", timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    csrf_tag = (soup.find("input", {"name": "_csrf"})
                or soup.find("input", {"name": "_csrf_frontend"}))
    if not csrf_tag:
        print("ERRO: csrf nao encontrado", flush=True)
        return False
    csrf = csrf_tag["value"]
    resp = session.post(MOOMBOX_URL + "/user/login", data={
        "_csrf": csrf,
        "login-form[login]": USUARIO,
        "login-form[password]": SENHA,
        "login-form[rememberMe]": "0",
    }, timeout=30)
    ok = "logout" in resp.text.lower()
    print("Login OK" if ok else "ERRO: Login falhou", flush=True)
    return ok


def parse_num(texto):
    t = texto.strip().replace("\xa0", "").replace(" ", "").replace(",", "")
    if not t or t == "-":
        return 0.0
    try:
        return float(t)
    except ValueError:
        return 0.0


def coletar_relatorio(data_ini, data_fim):
    todos = []
    page = 1
    while True:
        url = (
            MOOMBOX_URL
            + "/relatorios/relatorio-consolidado-expositor/index"
            + "?RelatorioConsolidadoExpositorForm%5Bdata_ini%5D=" + data_ini
            + "&RelatorioConsolidadoExpositorForm%5Bdata_fim%5D=" + data_fim
            + "&per-page=500&page=" + str(page)
        )
        r = session.get(url, timeout=30)
        print("Pagina " + str(page) + ": status=" + str(r.status_code), flush=True)
        soup = BeautifulSoup(r.text, "html.parser")

        tabela = soup.find("table")
        if not tabela:
            print("Pagina " + str(page) + ": nenhuma tabela encontrada", flush=True)
            break

        tbody = tabela.find("tbody")
        rows = tbody.find_all("tr") if tbody else tabela.find_all("tr")
        print("Pagina " + str(page) + ": " + str(len(rows)) + " linhas", flush=True)

        loja_atual = None
        registros_pagina = 0

        for row in rows:
            cells = row.find_all("td")
            if not cells:
                continue
            num_cells = len(cells)

            if num_cells == 7:
                c0_rowspan = cells[0].get("rowspan")
                if c0_rowspan and int(c0_rowspan) > 1:
                    loja_atual = cells[0].get_text(strip=True)
                    expositor = cells[1].get_text(strip=True)
                    if not expositor:
                        continue
                    todos.append({
                        "loja": loja_atual,
                        "expositor": expositor,
                        "total_vendas": parse_num(cells[2].get_text(strip=True)),
                        "cupons_validos": int(parse_num(cells[3].get_text(strip=True))),
                        "ticket_medio": parse_num(cells[4].get_text(strip=True)),
                        "total_itens": int(parse_num(cells[5].get_text(strip=True))),
                    })
                    registros_pagina += 1

            elif num_cells == 6:
                if loja_atual is None:
                    continue
                expositor = cells[0].get_text(strip=True)
                if not expositor:
                    continue
                if "kv-align-right" in cells[0].get("class", []):
                    continue
                todos.append({
                    "loja": loja_atual,
                    "expositor": expositor,
                    "total_vendas": parse_num(cells[1].get_text(strip=True)),
                    "cupons_validos": int(parse_num(cells[2].get_text(strip=True))),
                    "ticket_medio": parse_num(cells[3].get_text(strip=True)),
                    "total_itens": int(parse_num(cells[4].get_text(strip=True))),
                })
                registros_pagina += 1

        print("Pagina " + str(page) + ": " + str(registros_pagina) + " registros (total: " + str(len(todos)) + ")", flush=True)

        if registros_pagina == 0:
            break

        prox = soup.find("li", class_="next")
        if not prox or "disabled" in prox.get("class", []):
            break
        page += 1

    return todos


def main():
    import pytz
    print("=== INICIANDO COLETA ===", flush=True)
    if DATA_SIMULADA:
        hoje = datetime.strptime(DATA_SIMULADA, "%d/%m/%Y")
    else:
        tz_br = pytz.timezone("America/Sao_Paulo")
        hoje = datetime.now(tz_br).replace(tzinfo=None)

    data_ini_db = hoje.strftime("%Y-%m-01")
    data_fim_db = hoje.strftime("%Y-%m-%d")
    mes_ref = hoje.strftime("%Y-%m")
    data_str = hoje.strftime("%d/%m/%Y")

    print("Periodo: " + data_ini_db + " a " + data_fim_db, flush=True)

    if not login():
        print("Abortando: login falhou", flush=True)
        return

    registros = coletar_relatorio(data_ini_db, data_fim_db)
    print("Total coletado: " + str(len(registros)) + " marcas", flush=True)

    por_loja = {}
    total_geral = 0.0
    for rec in registros:
        loja = rec["loja"] or "Desconhecida"
        if loja not in por_loja:
            por_loja[loja] = {"marcas": [], "total_loja": 0.0, "cupons_loja": 0}
        por_loja[loja]["marcas"].append(rec)
        por_loja[loja]["total_loja"] += rec["total_vendas"]
        por_loja[loja]["cupons_loja"] += rec["cupons_validos"]
        total_geral += rec["total_vendas"]

    resultado = {
        "data_coleta": data_str,
        "periodo_ini": data_ini_db,
        "periodo_fim": data_fim_db,
        "mes_ref": mes_ref,
        "total_geral": round(total_geral, 2),
        "total_marcas": len(registros),
        "lojas": por_loja,
    }

    os.makedirs("dados", exist_ok=True)
    nome = "dados/relatorio_" + mes_ref + ".json"
    with open(nome, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print("Arquivo salvo: " + nome, flush=True)

    print("\n=== RESUMO ===", flush=True)
    for loja, d in por_loja.items():
        print("  " + loja + ": R$ " + str(round(d["total_loja"], 2)) + " (" + str(len(d["marcas"])) + " marcas)", flush=True)


if __name__ == "__main__":
    main()
