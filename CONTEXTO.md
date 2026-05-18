# Contexto do Projeto - Relatorio de Marcas Moombox

> Documento de retomada de contexto. Cole o link deste arquivo no inicio de uma nova conversa com Claude para retomar o trabalho sem precisar reexplicar tudo.

## URLs

- **Dashboard publico:** https://leonardochor-hash.github.io/relatorio-marcas/
- **Admin (gerenciamento de senhas + log):** https://leonardochor-hash.github.io/relatorio-marcas/admin.html
- **Repositorio:** https://github.com/leonardochor-hash/relatorio-marcas
- **Workflow de coleta:** https://github.com/leonardochor-hash/relatorio-marcas/actions/workflows/coletar.yml
- **Repos relacionados:** alerta-vendas, monitor-vendas

## Arquitetura

GitHub Pages estatico + GitHub Actions agendado.

- `coletar_marcas.py` - script Python que faz login em expositores.moombox.com.br e gera relatorios mensal/semanal
- `.github/workflows/coletar.yml` - roda todo dia as 23h BRT (02h UTC) ou manualmente via workflow_dispatch
- `dados/relatorio_mensal.json` e `dados/relatorio_semanal.json` - vendas coletadas
- `dados/metas.json` - 181 marcas com tipo_espaco e metas (carregadas via upload de Excel)
- `dados/usuarios.json` - 4 usuarios com senhas SHA-256
- `index.html` - dashboard com login, KPIs e paineis consolidados
- `admin.html` - gera hash de senha + visualiza log de acesso

## Usuarios cadastrados

Todos com senha inicial padrao: **1234** (hash SHA-256 ja em `dados/usuarios.json`)

| Login | Tipo | Acesso |
|-------|------|--------|
| admin | admin | todas as lojas |
| gerente_rs | gerente | apenas Rio Sul |
| gerente_bs | gerente | apenas Barra Shopping |
| gerente_ns | gerente | apenas NorteShopping |

**Para trocar senha:** abrir admin.html, digitar a senha desejada no gerador, copiar o hash, editar `dados/usuarios.json` no GitHub e commitar.

## Funcionalidades implementadas

- Login com SHA-256 e filtro automatico por loja conforme tipo de usuario
- KPIs no topo: marcas com meta, abaixo meta MENSAL (com breakdown RS/BS/NS), abaixo meta SEMANAL (idem), vendas total mensal, vendas total semanal
- 2 paineis lado a lado: abaixo da meta por loja Mensal (esquerda) e Semanal (direita), ambos consolidados por tipo_espaco com seletor de loja
- Filtro de tipos validos (whitelist: Arara, Bandeja, Box Inferior, Prateleira, Vitrine) - nao polui com nomes de marca
- Valores monetarios sem decimais (Math.round + maximumFractionDigits:0)
- Upload manual de Excel para sobrescrever metas (localStorage) - opcional, ja existe metas.json no repo
- Timezone America/Sao_Paulo via agora_br() no coletar_marcas.py
- Log de acesso (localStorage chave acesso_log) acessivel via botao "Ver log" e em admin.html

## Comandos uteis

**Rodar coleta de vendas manualmente:**

Abrir https://github.com/leonardochor-hash/relatorio-marcas/actions/workflows/coletar.yml, clicar "Run workflow" > "Run workflow". Demora ~30s. Auto-commita com [skip ci].

**Atualizar metas (181 marcas):**

Usuario faz upload do Excel `modelo_metas_v2.xlsx` no proprio dashboard (area de drag-and-drop), depois para persistir entre browsers/usuarios sem precisar reupload, gravar em `dados/metas.json` no repo.

**Editar arquivos grandes via web:**

GitHub usa CodeMirror; `Ctrl+A` + `Ctrl+V` pode falhar com arquivos grandes. Usar API direta:

```javascript
const el = document.querySelector(".cm-content");
const view = el.cmTile.view;
view.dispatch({ changes:{ from:0, to:view.state.doc.length, insert: newContent } });
```

## Pendencias / proximos passos sugeridos

- [ ] Trocar a senha padrao 1234 dos 4 usuarios (usar admin.html para gerar hash)
- [ ] Adicionar usuarios nomeados (pessoas reais) ao inves de admin/gerente_*
- [ ] Integracao Twilio WhatsApp (pausada antes da compressao da conversa)
- [ ] Considerar exportar relatorios em PDF

## Limitacao de seguranca conhecida

GitHub Pages serve arquivos estaticos. O login eh validado no client (JS). Qualquer pessoa que abrir o DevTools pode ler `dados/usuarios.json`. As senhas estao em hash SHA-256 mas sao vulneraveis a brute force se forem fracas. Para seguranca real seria necessario um backend (ex: Cloudflare Workers + KV).

## Como retomar o trabalho com Claude

No inicio de uma nova conversa, mandar:

> "Le https://github.com/leonardochor-hash/relatorio-marcas/blob/main/CONTEXTO.md e https://github.com/leonardochor-hash/relatorio-marcas/blob/main/HISTORICO.md antes de comecar. Quero continuar de onde paramos."

E depois pedir o que quiser - Claude vai ter todo o contexto necessario.

## Atualizacao 2026-05-17 21:00

### Mudancas recentes

- **metas.json deduplicado**: 181 -> 160 marcas unicas (removidas 21 duplicatas como Oticaevox NS Prateleira repetida 6x). Commit 6435b57e
- **Filtro tipo de espaco dinamico**: combo agora popula todos os tipos encontrados em state.metas + linhas (era hardcoded para 4 tipos: Arara, Bandeja, Box Inferior, Prateleira, Vitrine). Commit 7801c5fa
- **marcasSemMeta com fuzzy matching**: usa norm() consistente em ambos os lados + substring bidirecional + verificacao em qualquer loja. Reduziu falsos positivos de 152 -> 60. Commit anterior
- **getVenda com fuzzy matching**: tenta exato primeiro, depois substring bidirecional. Commit b4f9d28

### Estado atual do dashboard

- 160 marcas com meta (RS 75, BS 67, NS 18)
- Vendas: R$ 271.411 mensal / R$ 80.514 semanal
- KPIs: 92/160 mensal (RS 33, BS 47, NS 12), 155/160 semanal (RS 71, BS 66, NS 18)
- Filtro tipo de espaco: 12 opcoes (Arara, Arara + Manequim, Arara Destaque, Bandeja, Box Gaveta, Box Inferior, Box Inferior Alto, Box Inferior Largo, Box Superior, Box Superior Largo, Prateleira, Rooftop)
- 60 marcas em "sem meta" sao casos reais de nome divergente Excel vs Moombox - lista detalhada na sessao do chat

### Pendencias mantidas

- Trocar senha default "1234" dos 4 usuarios
- Corrigir nomes no Excel para as 60 marcas em "sem meta" (lista com sugestoes ja gerada)
- Twilio WhatsApp integration (pausado)
- Remover credencial "admin2020b" do coletar_marcas.py linha 16 (exposta no repo publico)

## Atualizacao 2026-05-17 21:30

### Export para acerto manual

- Gerado arquivo **marcas_sem_meta_para_acerto.xlsx** com as 60 marcas que nao casam com nenhuma meta
- Distribuicao: 29 NS + 15 RS + 16 BS
- 4 abas: Todas, NS, RS, BS
- Colunas: Loja | Marca no Moombox | Venda Mensal | Venda Semanal | Sugestao de match (automatica) | Nome correto no Excel (em branco para preencher)
- Tamanho do arquivo: ~50KB

### 7 matches certeiros identificados (correcao prioritaria no Excel)

| Loja | Nome no Moombox | Nome no Excel atual |
|------|-----------------|---------------------|
| RS | querida margarida atelie | Atelie Querida Margarida |
| RS | dolce vanilla | Dulce Vanilla |
| RS | corpo em evidencia | corpoevioficial |
| RS | PK arte non corpo | PK artenocorpo |
| BS | corpo em evidencia | corpoevioficial |
| BS | veronica lima velas e aromas | veronicalima_aromas |
| NS | belvera bolsas e acessorios | @belvera26 |

### Como gerar o XLSX de exportacao novamente

No console do dashboard (F12), com sessao admin ativa:

\`\`\`javascript
const sem = marcasSemMeta();
const rows = sem.map(s => ({Loja:s.loja, Marca:s.marca, VendaMensal:s.mensal, VendaSemanal:s.semanal}));
const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rows), 'SemMeta');
XLSX.writeFile(wb, 'sem_meta.xlsx');
\`\`\`
