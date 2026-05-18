# Historico de Commits Relevantes

> Ordem cronologica dos principais commits. Para detalhes, ver git log.

## Sessao atual (mais recentes primeiro)

| Commit | Mensagem | O que faz |
|--------|----------|-----------|
| bf3f22f | docs: adiciona CONTEXTO.md | Documento de retomada de contexto |
| aa166aa | fix: corrige state.mensal_.total_geral | Corrige typo que zerava os KPIs |
| a385f87 | fix: remove referencias a paineis removidos | Limpa codigo que apontava para panelEspaco* |
| 911a7c0 | feat: paineis lado a lado mensal/semanal + KPIs por loja | Reorganiza layout principal, adiciona breakdown RS/BS/NS nos KPIs |
| 116e3e8 | fix: usa agora_br() para data_coleta | Corrige timezone UTC->America/Sao_Paulo |
| 47d404e | feat: popula dados/metas.json com 181 marcas + tipos | Persiste metas no repo, dispensa upload por usuario |
| 5fe58c0 | fix: garantir carregarDados ao final do script | Fallback de boot |
| cef94d2 | fix: aguardar DOMContentLoaded antes de inicializar sessao | Race condition fix |
| f1a2b00 | feat: login overlay, userbar, log modal | Sistema de autenticacao no index.html |
| 9dbfaf9 | feat: pagina admin.html | Gerador de hash SHA-256 + visualizador de log |
| f3805d2 | feat: dados/usuarios.json | 4 usuarios com hash de "1234" |
| 7706a29 | feat: consolidado por loja com seletor | Painel agrupado por tipo_espaco com dropdown |
| 266f012 | fix: whitelist de tipos validos + decimais | Filtro nao polui com nomes de marca, R$ sem casas decimais |
| a160634 | chore: workflow run #11 [skip ci] | Auto-commit de vendas |

## Resumo do que cada um deveria saber

- O projeto **funciona** atualmente e esta deployado em https://leonardochor-hash.github.io/relatorio-marcas/
- O ultimo workflow rodou em 2026-05-17 com timezone correto
- Sao 181 marcas com meta (NS=25, RS=83, BS=73)
- 4 usuarios cadastrados ainda com senha 1234 (TROCAR!)
- Layout final: 2 paineis lado a lado (Mensal/Semanal consolidado por loja+tipo) + KPI cards com breakdown RS/BS/NS

## Commits adicionais (2026-05-17 noite)

| Hora | SHA | Descricao |
|------|-----|-----------|
| 20:32 | b4f9d28 | Fix: norm() consistente e fuzzy substring matching em getVenda |
| 20:50 | 116e3e8/aa166aa | (anteriores) Layout 2 paineis + KPI breakdown por loja |
| 20:54 | 6435b57e | Dedup metas.json: remove 21 duplicatas (181 -> 160) |
| 20:58 | 7801c5fa | Fix: filtro tipo de espaco mostra todos os tipos (sem whitelist) |
| 20:48 | (fix anterior) | marcasSemMeta: norm consistente + match exato/global/fuzzy -> 152 -> 60 sem meta |

## Atualizado em 2026-05-17 21:00

- Total: **160 marcas com meta unicas** (era 181 com 21 duplicatas)
- Filtro tipo de espaco: 12 opcoes dinamicas (era 4 fixas hardcoded)
- marcasSemMeta agora usa fuzzy matching (substring bidirecional)
- 60 marcas restantes em "sem meta" sao casos reais de nome divergente Excel vs Moombox
- getVenda tambem usa fuzzy matching - 125 das 160 marcas tem vendas correlacionadas
- KPIs: 92/160 mensal (RS 33/75, BS 47/67, NS 12/18), 155/160 semanal (RS 71/75, BS 66/67, NS 18/18)
