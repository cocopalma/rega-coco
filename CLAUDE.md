# Rega Coco — notas para o Claude

App PWA de reporte da rega de emergência (Projecto Coco, Palma). Publicada em GitHub Pages: https://cocopalma.github.io/rega-coco/
Servidor: Supabase, projecto `fgzdqnvobgfzjetbbxcm`. Responder sempre em português europeu.

## Ficheiros
- `index.html`, `app.js`, `sw.js`, `manifest.webmanifest`, ícones — a app (activistas, técnicos, supervisores, director, gestor, cliente).
- `i18n.js` — tradução para inglês (botão EN/PT no cabeçalho e no ecrã de entrada; escolha guardada no telefone). Ao acrescentar textos em português na app ou no painel, acrescentar a tradução no dicionário `D` (frase exacta) ou em `R` (frase com números/nomes).
- `painel.html` — painel geral, só aberto dentro da app (separador Painel, `?embutido=1`). Aberto directamente, reencaminha para a app: o Valdo quer um só link (11/10/2026). O cliente entra na app e só vê o Painel.
- `supabase/functions/gestor-activistas/index.ts` — cópia da função de servidor que cria logins (publicar com o conector Supabase).
- Ao mudar a app, subir `VERSAO` em `sw.js` e o `?v=` de `app.js` e `i18n.js` em `index.html` (e de `i18n.js` em `painel.html`) para os telefones receberem a nova versão.

## Ecrã de entrada (11/10/2026, escolha do Valdo)
Um só link para todos. Ecrã C (campo, fundo areia, letras grandes para o sol): botões Activista (PIN em 6 caixas) e Técnico / Supervisor (senha). Ligação "Outros acessos (escritório)" abre o ecrã B (faixa verde): director, M&E, gestor, cliente, administração. O telefone lembra o último ecrã (`localStorage rega.entrada`, gravado conforme a função de quem entrou). Desenho original: artifact "Rega Coco — ecrã de entrada".

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

## Zonas
Tabela `zonas` (comunidade, zona) e coluna `areas.zona`. Palma: Incularino, Quilaua, Muah, Bagala, Quelimane (11/10/2026, Nuro). Oliveira = Incularino e Quilaua, Sitambur = Muah, Razaque = Bagala e Quelimane; só os campos do Sitambur têm zona definida, os outros ficam para o supervisor (Nuro) definir. Gestor e supervisor mudam a zona na ficha do campo (RPC `definir_zona`, fica em `alteracoes_areas`). A comunidade do campo não muda.

## Notas de dados
- `areas.activista_proposto` guarda o NOME do activista (não o id); a app converte com `propostaId()`.
- `activistas.activo = false`: Amisse Dade Ali (era sazonal; campos passaram para Azize Abdala Selemane) e Chafim Abdala Salimo (desligado; 2 campos ficaram por atribuir) — 11/10/2026, informação do Nuro.
- Rotina Carlos → comunidade Quitunda; Martins Joaquim Fernando → Senga (substituiu Aiuba Abdala Aja). Supervisor de ambos: Raul.
- RAL = Replacement Agricultural Land: bloco de produção que vai de Senga a Macala (não é comunidade na base).

## Pendentes pedidos pelo Valdo
- Painel: frequência de rega (dias entre regas do mesmo campo) por equipa, agrupada por comunidade. Fazer depois da fase de teste dos activistas, quando o agrupamento de campos por equipa estiver confirmado (11/10/2026). Os registos já guardam activista, campo e data, por isso o cálculo cobre também as regas anteriores.
