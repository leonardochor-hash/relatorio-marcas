import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import json
import unicodedata

try:
    import pytz
    TZ_BR = pytz.timezone('America/Sao_Paulo')
except Exception:
    TZ_BR = None

MOOMBOX_URL = 'https://expositores.moombox.com.br'
USUARIO = 'moombox'
SENHA = 'admin2020b'
DATA_SIMULADA = os.environ.get('DATA_SIMULADA', '')

SIGLA_PARA_NOME = {'RS': 'Rio Sul', 'BS': 'Barra Shopping', 'NS': 'NorteShopping'}
NOME_PARA_SIGLA = {v: k for k, v in SIGLA_PARA_NOME.items()}
MAX_PAGINAS = 50

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

def agora_br():
    if DATA_SIMULADA:
        return datetime.strptime(DATA_SIMULADA, '%Y-%m-%d')
    if TZ_BR is not None:
        return datetime.now(TZ_BR).replace(tzinfo=None)
    return datetime.now()

def login():
    r = session.get(MOOMBOX_URL + '/user/login', timeout=30)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf_tag = soup.find('input', {'name': '_csrf'}) or soup.find('input', {'name': '_csrf_frontend'})
    if not csrf_tag:
        print('ERRO: csrf nao encontrado', flush=True)
        return False
    csrf = csrf_tag['value']
    resp = session.post(MOOMBOX_URL + '/user/login', data={
        '_csrf': csrf,
        'login-form[login]': USUARIO,
        'login-form[password]': SENHA,
        'login-form[rememberMe]': '0',
    }, timeout=30)
    ok = 'logout' in resp.text.lower()
    if ok:
        print('Login OK', flush=True)
    else:
        print('ERRO: Login falhou', flush=True)
    return ok

def coletar_relatorio(data_ini, data_fim):
    registros = []
    page = 1
    assinatura_anterior = None
    while page <= MAX_PAGINAS:
        url = (MOOMBOX_URL
               + '/relatorios/relatorio-consolidado-expositor/index'
               + f'?RelatorioConsolidadoExpositorForm[data_ini]={data_ini}'
               + f'&RelatorioConsolidadoExpositorForm[data_fim]={data_fim}'
               + f'&per-page=500&page={page}')
        r = session.get(url, timeout=60)
        soup = BeautifulSoup(r.text, 'html.parser')
        tbody = soup.select_one('table tbody')
        if not tbody:
            print(f'Pag{page}: tbody nao encontrado', flush=True)
            break

        rows = tbody.find_all('tr')
        regs_pagina = []
        loja_atual = ''

        for row in rows:
            cells = row.find_all('td')
            num_cells = len(cells)
            if num_cells == 0:
                continue
            if num_cells == 7:
                c0_classes = cells[0].get('class', [])
                if 'kv-grid-group' in c0_classes:
                    loja_atual = cells[0].get_text(strip=True)
                expositor = cells[1].get_text(strip=True)
                total_str = cells[2].get_text(strip=True).replace('R$', '').replace('.', '').replace(',', '.').strip()
                cupons_str = cells[3].get_text(strip=True)
                ticket_str = cells[4].get_text(strip=True).replace('R$', '').replace('.', '').replace(',', '.').strip()
                itens_str = cells[5].get_text(strip=True)
                try:
                    total = float(total_str) if total_str else 0.0
                    cupons = int(cupons_str) if cupons_str.isdigit() else 0
                    ticket = float(ticket_str) if ticket_str else 0.0
                    itens = int(itens_str) if itens_str.isdigit() else 0
                except Exception:
                    total, cupons, ticket, itens = 0.0, 0, 0.0, 0

                if expositor:
                    regs_pagina.append({
                        'loja': loja_atual,
                        'expositor': expositor,
                        'total': total,
                        'cupons': cupons,
                        'ticket_medio': ticket,
                        'itens': itens,
                    })

        assinatura = tuple(sorted((r['loja'], r['expositor']) for r in regs_pagina))
        print(f'Pag{page}: {len(regs_pagina)} regs', flush=True)

        if not regs_pagina:
            break
        if assinatura == assinatura_anterior:
            print(f'Pag{page}: mesma assinatura, encerrando paginacao', flush=True)
            break

        registros.extend(regs_pagina)
        assinatura_anterior = assinatura
        page += 1

    if page > MAX_PAGINAS:
        print(f'AVISO: atingido limite MAX_PAGINAS={MAX_PAGINAS}', flush=True)

    return registros

def normalizar_nome(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()

def sigla_da_loja(nome_loja):
    norm = normalizar_nome(nome_loja)
    for nome_completo, sigla in NOME_PARA_SIGLA.items():
        if normalizar_nome(nome_completo) == norm:
            return sigla
    if 'rio sul' in norm:
        return 'RS'
    if 'barra' in norm:
        return 'BS'
    if 'norte' in norm:
        return 'NS'
    return nome_loja

def agrupar(registros):
    lojas = {}
    marcas = {}
    total_geral = 0.0
    for reg in registros:
        sigla = sigla_da_loja(reg['loja'])
        marca = reg['expositor']
        if sigla not in lojas:
            lojas[sigla] = {'nome': reg['loja'], 'total': 0.0, 'cupons': 0, 'marcas': 0}
        lojas[sigla]['total'] += reg['total']
        lojas[sigla]['cupons'] += reg['cupons']
        chave = (sigla, normalizar_nome(marca))
        if chave not in marcas:
            lojas[sigla]['marcas'] += 1
            marcas[chave] = {
                'loja_sigla': sigla,
                'loja_nome': reg['loja'],
                'marca': marca,
                'marca_normalizada': normalizar_nome(marca),
                'total': 0.0,
                'cupons': 0,
                'itens': 0,
            }
        marcas[chave]['total'] += reg['total']
        marcas[chave]['cupons'] += reg['cupons']
        marcas[chave]['itens'] += reg['itens']
        total_geral += reg['total']
    return lojas, list(marcas.values()), total_geral

def segunda_da_semana(dt):
    return (dt - timedelta(days=dt.weekday())).date()

def salvar_json(caminho, payload):
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f'Salvo: {caminho}', flush=True)

def coletar_e_salvar(data_ini_dt, data_fim_dt, caminho_saida, rotulo):
    data_ini = data_ini_dt.strftime('%Y-%m-%d')
    data_fim = data_fim_dt.strftime('%Y-%m-%d')
    print(f'\n=== {rotulo} ===', flush=True)
    print(f'Coletando de {data_ini} ate {data_fim}', flush=True)
    registros = coletar_relatorio(data_ini, data_fim)
    print(f'Total coletado: {len(registros)} registros', flush=True)
    lojas, marcas, total_geral = agrupar(registros)
    payload = {
        'tipo': rotulo,
        'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'periodo_ini': data_ini,
        'periodo_fim': data_fim,
        'total_geral': round(total_geral, 2),
        'total_marcas': len(marcas),
        'lojas': lojas,
        'marcas': marcas,
    }
    salvar_json(caminho_saida, payload)
    print(f'  total_geral=R$ {total_geral:.2f} | total_marcas={len(marcas)} | lojas={list(lojas.keys())}', flush=True)

def main():
    hoje = agora_br()
    print(f'Hora atual BRT: {hoje.strftime("%Y-%m-%d %H:%M:%S")}', flush=True)

    if not login():
        exit(1)

    primeiro_dia_mes = hoje.replace(day=1)
    caminho_mensal = f'dados/relatorio_mensal_{hoje.strftime("%Y-%m")}.json'
    coletar_e_salvar(primeiro_dia_mes, hoje, caminho_mensal, 'mensal')

    segunda = segunda_da_semana(hoje)
    segunda_dt = datetime.combine(segunda, datetime.min.time())
    caminho_semanal = 'dados/relatorio_semanal_atual.json'
    coletar_e_salvar(segunda_dt, hoje, caminho_semanal, 'semanal')

    print('\nColeta concluida.', flush=True)

if __name__ == '__main__':
    main()
