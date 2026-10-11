# Rega Coco — notas para o Claude

App PWA de reporte da rega de emergência (Projecto Coco, Palma). Publicada em GitHub Pages: https://cocopalma.github.io/rega-coco/
Servidor: Supabase, projecto `fgzdqnvobgfzjetbbxcm`. Responder sempre em português europeu.

## Ficheiros
- `index.html`, `app.js`, `sw.js`, `manifest.webmanifest`, ícones — a app (activistas, técnicos, supervisores, director, gestor, cliente).
- `painel.html` — painel geral (também aberto dentro da app, separador Painel, com `?embutido=1`).
- `supabase/functions/gestor-activistas/index.ts` — cópia da função de servidor que cria logins (publicar com o conector Supabase).
- Ao mudar a app, subir `VERSAO` em `sw.js` e o `?v=` de `app.js` em `index.html` para os telefones receberem a nova versão.

## Quem vê o quê (regras no servidor, RLS)
- Activista: os seus campos (pode ver todos no mapa); regista regas da sua lista.
- Técnico: campos dos activistas com `activistas.tecnico` = o seu nome (+ colegas que cobre) e campos sem activista dessas comunidades.
- Supervisor: o mesmo por `activistas.supervisor`. Coberturas na tabela `coberturas` (o gestor gere na app).
- Director e M&E (papel `me`): leem tudo, não registam. Cliente / administração: só o painel.

## Atribuir campos sem activista
Desde 11/10/2026 faz-se na app (decisão do Valdo): separador Campos › filtro "Por atribuir" › "✓ Confirmar proposta" (usa `areas.activista_proposto`) ou "Escolher outro". Supervisor e técnico só atribuem a activistas da sua equipa; o gestor a qualquer um. Cada alteração fica em `alteracoes_areas`.
O Excel v3 (colunas AK–AN de validação) e o comando "aplica os activistas propostos" deixaram de ser usados.

## Lista de pessoas para criar acessos
Tabela `pessoas_acesso` (nome, entidade, papel, utilizador; sem senhas), copiada da aba `OUTROS_ACESSOS` do Excel `Plano de rega - base/Logins_activistas_RegaCoco_20261010.xlsx`. Em Gestão › Outros acessos, o nome escolhe-se desta lista conforme a função. Quando o Valdo actualizar o Excel, sincronizar a tabela (ler o Excel; nunca copiar a coluna de senhas).
Funções no Excel → papel: Técnico=tecnico, Supervisor=supervisor, Director (só leitura)=director, M&E (só leitura)=me, Só painel (cliente / administração)=cliente.
