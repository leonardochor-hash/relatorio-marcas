import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json

# Configuracoes
MOOMBOX_URL = "https://expositores.moombox.com.br"
USUARIO     = "moombox"
SENHA       = "admin2020b"
DATA_SIMULADA = os.environ.get("DATA_SIMULADA", "")

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def login():
    r = session.get(MOOMBOX_URL + "/user/login", timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    csrf_tag = soup.find("input", {"name": "_csrf"})
    if not csrf_tag:
        print("ERRO: csrf nao encontrado")
        return False
    csrf = csrf_tag["value"]
    resp = session.post(MOOMBOX_URL + "/user/login", data={
        "_csrf": csrf,
        "login-form[login]": USUARIO,
        "login-form[password]": SENHA,
        "login-form[rememberMe]": "0",
    }, timeout=30)
    ok = "logout" in resp.text.lower()
    print("Login OK" if ok else "ERRO: Login falhou")
    return ok

def coletar_relatorio(data_ini, data_fim):
    todos = []
    page = 1
    while True:
        url = (
            MOOMBOX_URL + "/relatorios/relatorio-consolidado-expositor/index"
            f"?RelatorioConsolidadoExpositorForm%5Bdata_ini%5D={data_ini}"
            f"&RelatorioConsolidadoExpositorForm%5Bdata_fim%5D={data_fim}"
            f"&per-page=500&page={page}"
        )
        r = session.get(url, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        loja_atual = None
        tabela = soup.find("table")
        if not tabela:
            break
        encontrou = False
        for row in tabela.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            if cells[0].get("rowspan"):
                loja_atual = cells[0].get_text(strip=True)
                cells = cells[1:]
            if len(cells) < 5:
                continue
            expositor = cells[0].get_text(strip=True)
            if not expositor or expositor in ("Total", "Loja", "Expositor"):
                continue
            try:
                tv = float(cells[1].get_text(strip=True).replace(",", ".").replace("\\xa0", ""))
                cv = int(cells[2].get_text(strip=True) or 0)
                tm = float(cells[3].get_text(strip=True).replace(",", ".") or 0)
                ti = int(cells[4].get_text(strip=True) or 0)
            except Exception:
                continue
            todos.append({
                "loja": loja_atual, "expositor": expositor,
                "total_vendas": tv, "cupons_validos": cv,
                "ticket_medio": tm, "total_itens": ti,
            })
            encontrou = True
        print(f"  Pagina {page}: {len(todos)} registros")
        prox = soup.find("li", class_="next")
        if not prox or "disabled" in prox.get("class", []) or not encontrou:
            break
        page += 1
    return todos

def main():
    import pytz
    if DATA_SIMULADA:
        hoje = datetime.strptime(DATA_SIMULADA, "%d/%m/%Y")
    else:
        tz_br = pytz.timezone("America/Sao_Paulo")
        hoje  = datetime.now(tz_br).replace(tzinfo=None)

    data_str    = hoje.strftime("%d/%m/%Y")
    data_ini_db = hoje.strftime("%Y-%m-01")
    data_fim_db = hoje.strftime("%Y-%m-%d")
    mes_ref     = hoje.strftime("%Y-%m")

    print(f"Coletando: {data_ini_db} ate {data_fim_db}")
    if not login():
        return

    registros = coletar_relatorio(data_ini_db, data_fim_db)
    print(f"Total: {len(registros)} marcas")

    por_loja = {}
    total_geral = 0.0
    for rec in registros:
        loja = rec["loja"] or "Desconhecida"
        if loja not in por_loja:
            por_loja[loja] = {"marcas": [], "total_loja": 0.0, "cupons_loja": 0}
        por_loja[loja]["marcas"].append(rec)
        por_loja[loja]["total_loja"]  += rec["total_vendas"]
        por_loja[loja]["cupons_loja"] += rec["cupons_validos"]
        total_geral += rec["total_vendas"]

    resultado = {
        "data_coleta": data_str, "periodo_ini": data_ini_db,
        "periodo_fim": data_fim_db, "mes_ref": mes_ref,
        "total_geral": round(total_geral, 2),
        "total_marcas": len(registros), "lojas": por_loja,
    }

    os.makedirs("dados", exist_ok=True)
    nome = f"dados/relatorio_{mes_ref}.json"
    with open(nome, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"Salvo: {nome}")

    print("\n=== RESUMO ===")
    print(f"Periodo: {data_ini_db} a {data_fim_db} | Total: R$ {total_geral:,.2f}")
    for loja, d in por_loja.items():
        print(f"  {loja}: R$ {d['total_loja']:,.2f} ({len(d['marcas'])} marcas)")

if __name__ == "__main__":
    main()
