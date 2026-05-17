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
    if ok:
        print("Login OK", flush=True)
    else:
        print("ERRO: Login falhou", flush=True)
    return ok


def coletar_relatorio(data_ini, data_fim):
    registros = []
    page = 1
    while True:
        url = (MOOMBOX_URL
               + "/relatorios/relatorio-consolidado-expositor/index"
               + f"?RelatorioConsolidadoExpositorForm[data_ini]={data_ini}"
               + f"&RelatorioConsolidadoExpositorForm[data_fim]={data_fim}"
               + f"&per-page=500&page={page}")
        r = session.get(url, timeout=60)
        soup = BeautifulSoup(r.text, "html.parser")
        tbody = soup.select_one("table tbody")
        if not tbody:
            print(f"Pag{page}: tbody nao encontrado", flush=True)
            break

        rows = tbody.find_all("tr")
        regs_pagina = 0
        loja_atual = ""

        for row in rows:
            cells = row.find_all("td")
            num_cells = len(cells)

            if num_cells == 0:
                continue

            if num_cells == 7:
                c0_classes = cells[0].get("class", [])
                if "kv-grid-group" in c0_classes:
                    loja_atual = cells[0].get_text(strip=True)
                    expositor = cells[1].get_text(strip=True)
                    total_str = cells[2].get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip()
                    cupons_str = cells[3].get_text(strip=True)
                    ticket_str = cells[4].get_text(strip=True).replace("R$", "").replace(".", "").replace(",", ".").strip()
                    itens_str = cells[5].get_text(strip=True)
                    try:
                        total = float(total_str) if total_str else 0.0
                        cupons = int(cupons_str) if cupons_str.isdigit() else 0
                        ticket = float(ticket_str) if ticket_str else 0.0
                        itens = int(itens_str) if itens_str.isdigit() else 0
                    except Exception:
                        total, cupons, ticket, itens = 0.0, 0, 0.0, 0

                    if expositor:
                        registros.append({
                            "loja": loja_atual,
                            "expositor": expositor,
                            "total": total,
                            "cupons": cupons,
                            "ticket_medio": ticket,
                            "itens": itens,
                        })
                        regs_pagina += 1

        print(f"Pag{page}: {regs_pagina} regs", flush=True)
        if regs_pagina == 0:
            break
        page += 1

    return registros


def salvar(registros, data_ref):
    mes = data_ref[:7]
    caminho = f"dados/relatorio_{mes}.json"
    os.makedirs("dados", exist_ok=True)

    existente = {}
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            existente = json.load(f)

    lojas = {}
    for reg in registros:
        loja = reg["loja"]
        if loja not in lojas:
            lojas[loja] = {"total": 0.0, "cupons": 0, "expositores": []}
        lojas[loja]["total"] += reg["total"]
        lojas[loja]["cupons"] += reg["cupons"]
        lojas[loja]["expositores"].append(reg["expositor"])

    total_geral = sum(r["total"] for r in registros)
    total_marcas = len(set(r["expositor"] for r in registros))

    existente["data_coleta"] = datetime.now().isoformat()
    existente["data_ini"] = data_ref
    existente["total_marcas"] = total_marcas
    existente["total_geral"] = total_geral
    existente["lojas"] = lojas
    existente["registros"] = registros

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(existente, f, ensure_ascii=False, indent=2)

    print(f"Salvo: {caminho} ({len(registros)} registros, {total_marcas} marcas, total R$ {total_geral:.2f})", flush=True)


def main():
    if DATA_SIMULADA:
        hoje = datetime.strptime(DATA_SIMULADA, "%Y-%m-%d")
        print(f"Data simulada: {hoje.date()}", flush=True)
    else:
        hoje = datetime.now()

    data_ini = hoje.strftime("%Y-%m-01")
    data_fim = hoje.strftime("%Y-%m-%d")

    print(f"Coletando de {data_ini} ate {data_fim}", flush=True)

    if not login():
        exit(1)

    registros = coletar_relatorio(data_ini, data_fim)
    print(f"Total coletado: {len(registros)} registros", flush=True)

    if registros:
        salvar(registros, data_ini)
    else:
        print("Nenhum registro coletado", flush=True)


if __name__ == "__main__":
    main()
