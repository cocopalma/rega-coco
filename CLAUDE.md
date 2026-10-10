# Rega Coco — notas para o Claude

App PWA de reporte da rega de emergência (Projecto Coco, Palma). Publicada em GitHub Pages: https://cocopalma.github.io/rega-coco/
Servidor: Supabase, projecto `fgzdqnvobgfzjetbbxcm`. Responder sempre em português europeu.

## Ficheiros
- `index.html`, `app.js`, `sw.js`, `manifest.webmanifest`, ícones — a app (activistas, técnicos, supervisores, director, gestor, cliente).
- `painel.html` — painel geral (também aberto dentro da app, separador Painel, com `?embutido=1`).
- `supabase/functions/gestor-activistas/index.ts` — cópia da função de servidor que cria logins (publicar com o conector Supabase).
- Ao mudar a app, subir `VERSAO` em `sw.js` para os telefones receberem a nova versão.

## Quem vê o quê (regras no servidor, RLS)
- Activista: os seus campos (pode ver todos no mapa); regista regas da sua lista.
- Técnico: campos dos activistas com `activistas.tecnico` = o seu nome (+ colegas que cobre) e campos sem activista dessas comunidades.
- Supervisor: o mesmo por `activistas.supervisor`. Coberturas na tabela `coberturas` (o gestor gere na app).
- Director: lê tudo, não regista. Cliente / administração: só o painel.

## Comando "aplica os activistas propostos"
Fonte: Drive do Valdo › `Projecto de plantio de coco/Rega de emergencia _2026/Plano de rega - base/Base_721_areas_REGA_SIM_20261009_v3_proposta_activistas.xlsx`, aba `AREAS_721`.
1. Antes de gravar no Excel: avisar o Valdo e esperar que confirme que está fechado; copiar para `_anterior/`.
2. Aplicar só linhas com `Sem activista` = SIM, `Validado pelo supervisor (SIM/NÃO)` (coluna AK) = SIM e `Activista proposto` (coluna AA, lista na aba oculta LISTAS) preenchido com um nome que exista em `activistas`.
3. Não sobrepor: se o campo já tiver activista no servidor (atribuído na app), não mudar — listar como conflito.
4. Gravar no servidor (update `areas.activista_id` + linha em `alteracoes_areas`), marcar a data em "Aplicado na app em" (coluna AN) no Excel e responder com: aplicados, conflitos, recusados (nome desconhecido).
