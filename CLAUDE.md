# Rega Coco — notas para o Claude

App PWA de reporte da rega de emergência (Projecto Coco, Palma). Publicada em GitHub Pages: https://cocopalma.github.io/rega-coco/
Servidor: Supabase, projecto `fgzdqnvobgfzjetbbxcm`. Responder sempre em português europeu.

## Ficheiros
- `index.html`, `app.js`, `sw.js`, `manifest.webmanifest`, ícones — a app (activistas, técnicos, supervisores, director, gestor, cliente).
- `i18n.js` — tradução para inglês e suaíli (botão de língua no cabeçalho e no ecrã de entrada: PT → EN → SW → PT; o botão mostra a língua seguinte; escolha guardada no telefone, `rega.lingua`). Ao acrescentar textos em português na app ou no painel, acrescentar a tradução no dicionário `D` (frase exacta) ou em `R` (frase com números/nomes) do inglês E no `i18n-sw.js` (`I18N_SW_D` com a mesma chave em português; `I18N_SW_R(tr)` com a mesma expressão regular, na mesma ordem que `R`).
- `i18n-sw.js` — suaíli (15/10/2026, pedido do Valdo): 611 frases + 153 expressões, tradução automática (rever com um falante nativo). Carregado antes do `i18n.js`; em suaíli as datas e números usam o formato do inglês (`LOC` = en-GB) para as expressões continuarem a casar. Teste: `rega-test/teste_sw.py`.
- `painel.html` — painel geral, só aberto dentro da app (separador Painel, `?embutido=1`). Aberto directamente, reencaminha para a app: o Valdo quer um só link (11/10/2026). O cliente entra na app e vê Mapa, Campos (só leitura) e Painel (desde 15/10/2026).
- Filtro de período no painel (11/10/2026, pedido do Valdo): Tudo / Hoje / Ontem / 7 dias / 30 dias / Período (de… até…); a escolha fica no telefone (`localStorage rega.painel.periodo`). Dados vêm da RPC `painel_resumo_periodo(p_de, p_ate)` (datas nulas = todo o histórico). A `painel_resumo()` antiga mantém-se para versões em cache. Ronda actual, progresso e rondas concluídas das equipas mostram sempre o estado actual; tudo o resto é filtrado. Frequência entre regas: intervalo calculado sobre todo o histórico, contado no dia da rega que o fecha. Chegada da água: sem período = últimos 14 dias.
- `supabase/functions/gestor-activistas/index.ts` — cópia da função de servidor que cria logins (publicar com o conector Supabase).
- Ao mudar a app, subir `VERSAO` em `sw.js` e o `?v=` de `app.js` e `i18n.js` em `index.html` (e de `i18n.js` em `painel.html`) para os telefones receberem a nova versão.

## Ecrã de entrada (11/10/2026, escolha do Valdo)
Um só link para todos. Ecrã C (campo, fundo areia, letras grandes para o sol): botões Activista (PIN em 6 caixas) e Técnico / Supervisor (senha). Ligação "Outros acessos (escritório)" abre o ecrã B (faixa verde): director, M&E, gestor, cliente, administração. O telefone lembra o último ecrã (`localStorage rega.entrada`, gravado conforme a função de quem entrou). Desenho original: artifact "Rega Coco — ecrã de entrada".

## Quem vê o quê (regras no servidor, RLS)
- Activista: os seus campos (pode ver todos no mapa); regista regas da sua lista.
- Técnico: campos dos activistas com `activistas.tecnico` = o seu nome (+ colegas que cobre) e campos sem activista dessas comunidades.
- Supervisor: o mesmo por `activistas.supervisor`. Coberturas na tabela `coberturas` (o gestor gere na app).
- Director e M&E (papel `me`): leem tudo, não registam. Cliente / administração: desde 15/10/2026 (Valdo) vê Mapa, Campos (fichas só de leitura, com as fotografias da rega e da monitoria) e Painel; não vê Hoje nem Gestão; `ids_visiveis`, `ve_area`, `areas_ler` e `registos_ler` incluem `cliente`; todas as funções que escrevem verificam o papel e recusam o cliente. A secção de monitoria do painel continua escondida ao cliente.

## Atribuir campos sem activista
Desde 11/10/2026 faz-se na app (decisão do Valdo): separador Campos › filtro "Por atribuir" › "✓ Confirmar proposta" (usa `areas.activista_proposto`) ou "Escolher outro". Supervisor e técnico só atribuem a activistas da sua equipa; o gestor a qualquer um. Cada alteração fica em `alteracoes_areas`.
O Excel v3 (colunas AK–AN de validação) e o comando "aplica os activistas propostos" deixaram de ser usados.

## Lista de pessoas para criar acessos
Tabela `pessoas_acesso` (nome, entidade, papel, utilizador; sem senhas), copiada da aba `OUTROS_ACESSOS` do Excel `Plano de rega - base/Logins_activistas_RegaCoco_20261010.xlsx`. Em Gestão › Outros acessos, o nome escolhe-se desta lista conforme a função. Quando o Valdo actualizar o Excel, sincronizar a tabela (ler o Excel; nunca copiar a coluna de senhas).
Funções no Excel → papel: Técnico=tecnico, Supervisor=supervisor, Director (só leitura)=director, M&E (só leitura)=me, Só painel (cliente / administração)=cliente.
Dalmar Santos (utilizador `dalmar`, director do projecto), 15/10/2026 (Valdo: "só não quero que ele crie acessos, o resto pode fazer"): `perfis.papel = 'gestor'`, `gere_acessos = false`, `titulo = 'Director'` (o topo da app mostra "Dalmar Santos · Director"; `perfis.titulo` substitui o nome da função). Com `gere_acessos = false`: a função `gestor-activistas` só aceita "listar" (não cria logins nem muda senha/PIN); a política `perfis_gestor` exige `privado.gere_acessos()` (não altera perfis); a Gestão esconde criar login, outros acessos, Novo PIN e Nova senha. Tudo o resto do gestor fica (coberturas, monitoria, reabrir limites, voltar a regar…). Coberturas que lhe tinham sido dadas por engano foram desactivadas (desde = até = 14/10). Em `pessoas_acesso` continua "director". Idelson Anselmo (`idelson`) = cliente desde 15/10/2026.

## Zonas
Tabela `zonas` (comunidade, zona) e coluna `areas.zona`. Palma: Incularino, Quilaua, Muah, Bagala, Quelimane (11/10/2026, Nuro). Oliveira = Incularino e Quilaua, Sitambur = Muah, Razaque = Bagala e Quelimane; só os campos do Sitambur tinham zona definida a 11/10; os outros ficam para o supervisor (Nuro) definir. A questão do Nuro "faltam reflectir produtores de Bagala, Quelimane" ficou resolvida (Valdo, 12/10/2026). Gestor e supervisor mudam a zona na ficha do campo (RPC `definir_zona`, fica em `alteracoes_areas`). Desde 15/10/2026 (Nuro/Valdo) técnico, supervisor e gestor também mudam a comunidade do campo ("🏘 Mudar a comunidade", RPC `definir_comunidade`, zona volta a null; lista de `lista_comunidades`, guardada no telefone).

## Notas de dados
- `areas.activista_proposto` guarda o NOME do activista (não o id); a app converte com `propostaId()`.
- `activistas.activo = false`: Amisse Dade Ali (era sazonal; campos passaram para Azize Abdala Selemane) e Chafim Abdala Salimo (desligado; 2 campos ficaram por atribuir) — 11/10/2026, informação do Nuro.
- Rotina Carlos → comunidade Quitunda; Martins Joaquim Fernando → Senga (substituiu Aiuba Abdala Aja). Supervisor de ambos: Raul.
- RAL = Replacement Agricultural Land: bloco de produção que vai de Senga a Macala (não é comunidade na base).

## Monitoria por amostragem (11/10/2026, decisões do Valdo)
- Técnicos e supervisores verificam campos regados; listas diferentes por pessoa (`monitoria_amostra`, único por dia+campo). Sorteio feito no servidor (RPC `monitoria_lista`) a partir das 18:00 com as regas desse dia (antes das 18:00: último dia de trabalho anterior). Lista recebida à noite, verificação no dia seguinte.
- Quantos: `config.monitoria_campos_por_dia` (2 por pessoa por dia; o gestor muda em Gestão, RPC `definir_monitoria_campos`). Método LQAS: 19 campos verificados por técnico para concluir (~2 semanas a 2/dia).
- Ficha por planta (11/10/2026, Valdo): o técnico escolhe o percurso (X, W, Z, diagonal; a app mostra o desenho) e regista cada planta: "Solo húmido (rega efectiva)?" sim/não + viva/seca/morta. Nº de plantas a observar = Cochran com correcção para população finita (95%, ±10%, p=80%; `CFG.monZ/monMargem/monP` em app.js), a app usa as plantas vivas da base (ou mudas plantadas) e calcula a amostra; o técnico só corrige o nº se tiver mudado ("O número de plantas mudou? Corrigir"); sem número na base, conta as plantas (12/10/2026, Valdo). Nota = % plantas com solo húmido ÷ 10 (app). Campo regado = ≥ 80% (`CFG.monLimiar`), guardado em `monitorias.solo_regado`. Colunas novas: metodo, plantas_no_campo, plantas_alvo, plantas_obs (jsonb), pct_humido, n_vivas/n_secas/n_mortas. Fotografia obrigatória reduzida no telefone (1024 px, JPEG 60%, ~80–150 KB) guardada em IndexedDB até haver rede; bucket privado `monitoria-fotos/<perfil>/<id>.jpg`. GPS: só no campo (200 m).
- Tabela `monitorias`; painel: secção "Monitoria por amostragem" (RPC `painel_monitoria(p_de,p_ate)`, filtra pelo dia da rega verificada).
- O cliente / administração não vê a secção da monitoria no painel, por enquanto (11/10/2026, Valdo): `painel_monitoria` devolve null ao papel cliente.
- Confirmado pelo Valdo (11/10/2026): amostra por planta com 95% e ±10%; LQAS 13 de 19 (painel: "Resultado LQAS" por técnico com as 19 verificações mais recentes do período; `config.lqas_n`/`lqas_limiar`).
- Avisos à equipa (11/10/2026, Valdo): campos verificados nos últimos 14 dias com plantas sem solo húmido aparecem no Hoje (cartão "Avisos da monitoria") e na ficha do campo, para o activista e para técnico/supervisor/gestor (RPC `avisos_monitoria`). Vermelho = campo não regado (< 80%).

## Equipa, meta e tempos (11/10/2026, Valdo)
- Equipa por número (os nomes virão depois): `activistas.equipa_tamanho` = "Pessoas declaradas a 09/10" do RH (folha EQUIPAS da base de 09/10) para 14 activistas; os outros ficam null = "por definir" (sem faltas) até alguém pôr o número (12/10/2026, Valdo); o activista regista as pessoas presentes no início do dia (Hoje › Pessoas hoje › Alterar) e em cada saída; gestor, técnico e supervisor mudam no Hoje (RPC `definir_equipa_tamanho`). Faltas = tamanho − pessoas presentes (máximo de `registos_rega.pessoas` no dia, senão `jornadas.pessoas`).
- Nesta fase as equipas escolhem os campos; a "% face ao plano" é a meta de 140 plantas por pessoa por dia (`CFG.metaPlantas`, `META` no painel, `config.meta_plantas_pessoa_dia`): % = plantas ÷ (140 × pessoas presentes). Hoje: coluna "% meta"; painel: secção "Meta" por dia / semana / período (RPC `painel_plantas_dia_equipa` devolve pessoas e tamanho).
- Gráficos no painel (11/10/2026, Valdo): % da meta por dia (colunas, linha 100%), % da meta por equipa (barras), deslocação média por equipa (barras), nota média por equipa na monitoria (barras, linha nota 8). Funções `colunas`/`barras` aceitam `ref`/`refTxt` (linha de referência) e `fmt`.
- Secção "Equipas — rondas" (13/10/2026, Valdo: antes "rondas e produtividade", mas só mostrava o progresso): remete para a secção Meta (`#s-meta`) para a produtividade.
- Tempo entre campos: Hoje coluna "Desloc." (média saída → entrada seguinte); painel "Tempo por campo e deslocação" (RPC `painel_tempos_equipa`).

## Feedback do teste de campo (12/10/2026, Nuro, decisões do Valdo)
- Entrada sem rede: quem já entrou no telefone pode voltar a entrar sem rede. O telefone guarda só uma impressão PBKDF2 da senha/PIN (`localStorage rega.acessoOff`, nunca a senha); a senha fica só em memória (`S.credPend`) e a app autentica-se quando houver rede (`autenticarPendente`, chamado no início da sincronização). Primeira entrada no telefone exige rede.
- Regas de teste (técnico/supervisor/gestor): não contam para a ronda nem para o painel, mas o próprio vê os campos com a cor roxa "Regado em teste" (últimos 14 dias, `rega.meusTestes` + fila local).
- Painel: zonas de Palma por baixo da comunidade no gráfico "Plantas vivas regadas por comunidade" (RPC `painel_zonas`, pelo local do campo, `areas.zona`).
- Monitoria: mulching (cobertura morta) e cava-roda agrupados numa só pergunta por planta da amostra (Os dois / Só mulching / Só cava-roda / Nenhum) → `plantas_obs[].cobertura` e `.cavaroda`.
- Campos retirados da rega (12/10/2026, listas do Nuro de 10/10 no grupo de alinhamento, confirmado pelo Valdo): 20 campos de Palma com `areas.activa = false`, motivo em `alteracoes_areas.motivo` (campo 'activa'): Muah sem mudas (5), Muah com acesso a água (2), Incularino sem mudas (8 campos, 7 produtores), Incularino sem acesso de tuk-tuk (5) — estes 5 voltam quando houver caminho para tuk-tuk. A lista de Olumbe de 06/10 (campanha 2025) já não estava na base.
- Gráficos aplicados da pré-visualização: plantas por comunidade, progresso da ronda, espera pela água, monitoria por técnico (linha LQAS). Plantas por pessoa por dia não foi escolhido.

## Chuva e balanço hídrico (12/10/2026, sugestão do Albino, decisões do Valdo)
- Há pluviómetros nas comunidades; o activista regista a chuva (Hoje › Chuva (pluviómetro) › Registar): dia (hoje/ontem), hora da leitura, comunidade (das suas áreas), mm e fotografia obrigatória da leitura (reduzida no telefone, bucket privado `chuva-fotos/<perfil>/<id>.jpg`; colunas `lida_em`, `foto_path`; 12/10/2026, Valdo). Tabela `chuva` (único por dia+comunidade+activista; corrige-se gravando de novo), fila `filaChuva` sem rede.
- Painel: secção "Chuva por comunidade" (RPC `painel_chuva`): total no período por comunidade e tabela por dia.
- Chuva de teste (13/10/2026, Valdo, para o teste dos supervisores): técnico, supervisor e gestor registam no Hoje ("Chuva (pluviómetro) · teste"), comunidades das áreas que vêem; `chuva.teste = true`, `activista_id` null, upsert por `id` (o telefone reutiliza o id por dia+comunidade em `rega.chuvaTesteIds`). `painel_chuva` ignora `teste`. RLS: activista só grava `teste = false`; os outros só `teste = true`.
- Fase 2 EM STANDBY (12/10/2026, decisão do Valdo): balanço hídrico por comunidade para decidir regar ou não e por quantos dias. Faltam os parâmetros agronómicos (ETo, Kc do coqueiro jovem, água útil do solo e profundidade das raízes, chuva efectiva, limite para voltar a regar) — o Valdo vai pedir ao Albino ou ao Paulo. Não inventar estes valores. Pesquisa feita (12/10): FAO-56 areia 50–110 mm/m de água útil; SoilGrids (ISRIC, estimativa de modelo, 250 m) dá franco-argilo-arenoso (~50% areia, ~30% argila) e 110–155 mm/m em 0–30 cm nas 16 comunidades — contradiz "solo arenoso"; proposta: análise de textura em 3–4 comunidades antes de escolher valores.

## Fotografias visíveis (12/10/2026, Valdo: sem tornar a app lenta)
- Só se descarregam quando se toca: o servidor devolve apenas o caminho; a imagem vem por URL assinado (10 min) ao tocar.
- Chuva: painel › Chuva por comunidade › Ver tabela por dia › valores com 📷 (`painel_chuva` devolve `fotos` só a técnico, supervisor, gestor, director e M&E).
- Monitoria: ficha do campo › "Monitoria deste campo" (RPC `monitorias_campo`, carregada depois de abrir a ficha). Desde 13/10/2026 (Valdo) todos os papéis vêem as fotografias (chuva e monitoria), incluindo activista e cliente; desde 15/10/2026 o cliente abre as fichas (só leitura); a secção de monitoria do painel continua escondida ao cliente.

## Polígonos das áreas (13/10/2026, pedido do Dalmar via Valdo)
- `areas.poligono` jsonb [[lon,lat],...] (simplificado ~2 m) e `areas.poligono_fonte`. Fontes (KMZ do Dalmar de 09/10): `A_DIA_A_DIA/06_MAPA_KMZ/Poligonos_Executados_Rega.kmz` e `B_PLANO_DE_REGA/04_MAPAS_KMZ/Plano_Rega_Semanal.kmz` (+ Plano_Rega_Equipa_Hoje), casados pelo PR (no nome do polígono) e pelo ponto da área: 622 de 721 áreas (603 de 701 activas). Sem polígono: 69 áreas cujo PR não está em nenhum KMZ e 30 com o polígono do PR a > 100 m do ponto (não usado).
- App: distância ao campo = 0 dentro do polígono, senão à linha mais próxima (`distCampo`); sem polígono, ao ponto. Margem `CFG.margemPoligono` = 50 m da borda (13/10/2026, Valdo); sem polígono continua `CFG.margemGPS` = 200 m ao ponto. Mapa desenha os polígonos (canvas) e um ponto pequeno.
- Funções temporárias de importação (`tmp_areas_para_poligonos`, `tmp_gravar_poligonos`) e a chave foram apagadas pelo Valdo no SQL Editor (13/10/2026). Para nova importação, criar de novo e apagar no fim.
- "Sair": só o botão do topo; o "Sair desta conta" no fim do Hoje foi retirado (13/10/2026, Valdo).

## Teste do Nuro de 14/10/2026 (WhatsApp) e teste de coerência
- Abrir sem rede ficava em branco: com o token expirado, `sb.auth.getSession()` tenta renovar ~30 s. App e painel esperam no máximo 1,5 s (8 s com rede) e usam a sessão guardada (`sessaoGuardada()`, chave `sb-<ref>-auth-token`). Teste: `rega-test/teste_abrir_sem_rede.py`.
- Hoje (técnico/supervisor/gestor) sem rede: não pede ao servidor; mostra "Sem rede…" e a linha da chuva de teste.
- Painel sem rede: mostra o último painel guardado para o mesmo período (mesmo de outro dia), com aviso "Sem rede: painel guardado no telefone (data)"; sem nenhum guardado, mensagem em vez do ecrã de entrada.
- Chuva por bairro em Palma: `chuva.zona`; locais = comunidade, ou comunidade › zona quando a comunidade tem zonas (tabela `zonas`). Índice único `chuva_dia_local_activista` (data, comunidade, zona, activista_id) NULLS NOT DISTINCT (substituiu a restrição antiga). `painel_chuva` agrupa por zona; o painel mostra "Palma › Incularino".
- Fotografia (chuva e monitoria): o Android fechava o Chrome ao abrir a câmara e perdia o formulário. Agora: botões "📷 Tirar fotografia" e "🖼️ Escolher da galeria" (`campoFoto`/`ligarFoto`); rascunhos `rega.rascChuva` e `rega.rascMon` (3 h, por perfil) voltam a abrir o formulário com aviso (`retomarRascunhos`).
- Captura de ecrã da câmara: o telefone não deixa capturar o ecrã da câmara (não é da app).
- 14/10 09:42 (Nuro): chuva gravada no servidor (Palma › Incularino, 0 mm, com foto) só pela galeria; "Tirar fotografia" não funcionou no telefone dele (causa por confirmar). Pediu que, depois de registada, a chuva apareça como registada: Hoje mostra "✓ Registado …" e "Corrigir ou outra comunidade" (`linhaChuva`); no formulário os locais já registados hoje aparecem marcados e começa no primeiro sem registo (v38).
- Coerência (14/10): RLS `registos_inserir` e `jornadas_inserir` passaram a exigir activista → `teste = false`, técnico/supervisor/gestor → `teste = true` (como a chuva). Todas as RPC usadas existem, com security definer e só para `authenticated`. `estado_areas` existe mas a app já não a usa. Aviso do Supabase "Leaked password protection" desligado (definição de Auth).
- 6 campos de Incularino pedidos pelo Nuro (14/10): Adremane Abdala campo 1 (353 plantadas / 220 vivas) e campo 3 (730/344), Mussa Iassine Imide (143/95), Abdala Salimo Mussa (232/226, poço secou), Salimo Sufiane (101/77, fonte secou), Sumail Amade (479/366, poço secou). Não estão na base; faltam o PR de cada produtor, o activista e a coordenada — não criar sem PR.

## Campos fora do plano e câmara na app (14/10/2026, pedido do Nuro, decisões do Valdo)
- Importadas para `areas` as 1188 linhas com REGA = NÃO da folha AREAS do `Controlo_Rega_Areas.xlsx` (entrega do Dalmar de 09/10; a pasta "COCO_REGA-2 - Dalmar2" de 14/10 é igual, 28 ficheiros com o mesmo md5): `activa = false`, `fonte` "… REGA=NÃO (fora do plano)", `area_n` = seguinte ao maior do PR, `activista_origem`, `agua_origem` (COM/SEM/SEM_GEO), `n_regas_origem`, `ultima_rega_origem`, `situacao_origem`. Sem telefones. Total na base: 1909 (701 activas). Função temporária `tmp_importar_fora_plano` desactivada (corpo só dá erro, sem execute) — apagar quando o Supabase deixar.
- App: Campos › "➕ Voltar a pôr um campo na rega" (supervisor e gestor; precisa de rede): procura por produtor/PR (RPC `areas_fora_plano`, máx. 40, ≥ 3 letras) nos campos com `activa = false` (inclui os 20 retirados a 12/10) → "Voltar a regar" com motivo opcional (RPC `voltar_a_regar`: activa = true, `reactivada_em/por`, activista da origem se estiver activo, registo em `alteracoes_areas`). Etiqueta "Novo na rega" 14 dias. Os campos inactivos não vão para o telefone (a app só carrega `activa = true`); `estado_ronda` passou a filtrar `a.activa`.
- Dos 6 campos do Nuro: Mussa Iassine Imide PR24510014-1, Abdala Salimo Mussa PR396000-1, Sumail Amade PR2457647-1 (sem coordenada), Adremane Abdala PR693305-1…13 (Ncalanga/Ncumbi na base); Salimo Sufiane não está na base.
- `voltar_a_regar` escolhe o activista do outro campo do mesmo PR já na rega; senão o `activista_origem`, se activo (14/10).
- Pedido do Raul (via Valdo, 14/10): 9 áreas voltaram à rega — PR032518-2, PR033764-2, PR400946-2 (Rotina Carlos), PR033806-1…4 e PR2169523-2 (Julia Jaime), PR033832-2 (Biena). Já estavam na rega: PR2274367-1, PR228241-1, PR2277247-1, PR2277248-1, PR228397-1, PR400893-1 (sem activista: era do Chafim). PR401409 (Daniel Severiano Lhiucuto) não existe; na base está Daniel Severino Lhiucuto PR228223-1 (Senga, já na rega). 8 das 9 áreas não têm coordenada.
- Câmara dentro da app (`camaraNaApp`, getUserMedia, vídeo + botão "📷 Tirar"): no telefone do Nuro a câmara do sistema fechava o Chrome ao guardar a foto. Sem getUserMedia, usa a câmara do sistema; sem autorização, avisa e sugere a galeria. Teste: `rega-test/teste_camara_voltar.py`.

## Medir a área no campo (15/10/2026, pedido do Valdo; funciona sem rede)
- Ficha do campo › "📐 Medir a área (andar à volta do campo)": técnico só em campos sem limite; supervisor e gestor também "de novo". A pessoa anda pela borda; o GPS marca um ponto a cada 3 m (`PASSO_MEDIR`) só com precisão ≤ `CFG.precisaoCoord`; "Marcar canto", "Desfazer", "Recomeçar"; ecrã ligado (Wake Lock). Desenho, perímetro e área ao vivo; no fim simplifica (Douglas-Peucker 1 m), avisa se o último ponto ficou a > 20 m do início, mostra plantas/ha.
- Rascunho `rega.rascMedir` (pontos a cada ponto): se a app fechar a meio da volta, reabre e continua; se a pessoa sair, os pontos ficam para quando voltar a medir esse campo.
- Grava pela fila `filaAlt` (tipo 'poligono') → RPC `gravar_poligono(p_area, p_pontos, p_precisao, p_medido_em)`: valida papel/visibilidade, 3–3000 pontos dentro da zona, área 4 m² a 50 ha; grava `poligono`, `area_m2`, `area_medida_em`, `poligono_fonte` "Medido na app dd/mm/aaaa (GPS ±x m)", e a coordenada (centro) se faltava; regista em `alteracoes_areas` (campo 'poligono', constraint alargada). A ficha mostra a área (medida, ou calculada do polígono do KMZ).
- A 15/10: 108 campos activos sem polígono (39 também sem coordenada). Teste: `rega-test/teste_medir.py`.

## Coordenada e área fechadas depois de gravadas (15/10/2026, Nuro/Valdo)
- Primeiras medições reais (Nuro, Mondlane, 15/10): PR394688-1 8156 m² (28 pontos) e PR395335-1 9564 m² (45 pontos), GPS ±2 m.
- Depois de gravadas, a coordenada e a área ficam fechadas para técnico e supervisor (botões escondidos; servidor recusa). Só o gestor corrige, ou carrega em "🔓 Deixar o supervisor/técnico corrigir…" (`areas.limites_abertos`, RPC `abrir_limites`); fecha sozinho depois de gravarem. Vale também para os limites vindos do KMZ.
- O activista também mede (15/10/2026, Valdo): só campos da sua lista sem limite; fica em `areas.poligono_proposto` / `area_m2_proposta` / `proposta_em` / `proposta_por` (não muda o limite nem a regra dos 50 m). Técnico, supervisor ou gestor aprovam/recusam na ficha (cartão "Área medida pelo activista — por aprovar", RPC `aprovar_poligono`; fila `filaAlt` tipo 'aprovar'); aviso "N medições de área por aprovar" na lista. Eles próprios podem medir directamente.

## Pendentes pedidos pelo Valdo
- Documento do RH com o tamanho das 12 equipas "por definir" (o Valdo vai pedir).
- Lista de todos os campos a regar com coordenadas (e polígonos), pedida pelo Valdo ao Dalmar a 13/10/2026: quando chegar, voltar a casar os polígonos e resolver as 69 áreas sem polígono e as 30 com polígono do PR a > 100 m.
- Guia de uma página para os activistas (entrar, registar rega e chuva, sem rede): fica para mais tarde (Valdo, 13/10/2026).
- Nomes dos membros de cada equipa (o Valdo envia) para registar quem trabalhou.
- Painel: frequência de rega (dias entre regas do mesmo campo) por equipa, agrupada por comunidade. Fazer depois da fase de teste dos activistas, quando o agrupamento de campos por equipa estiver confirmado (11/10/2026). Os registos já guardam activista, campo e data, por isso o cálculo cobre também as regas anteriores.
- Salimo Sufiane (Incularino, pedido do Nuro a 14/10): não está na base do Dalmar; falta o PR.
- Teste da v35 no terreno (polígonos, 50 m da borda, entrada sem rede, cor de teste, chuva de teste) pelo Nuro e Raul: marcado para 14/10/2026 (a 13/10 estiveram em reuniões).

## Decisões de 13/10/2026 (Valdo)
- Secção de monitoria do painel continua escondida ao cliente ("não agora").
- Testes só com os supervisores, por agora. Logins de activistas e técnicos ficam para mais tarde; o Valdo cria-os na app (não precisa de passo-a-passo).

## Fotografias da rega (15/10/2026, pedido do Nuro, decisões do Valdo)
- Três fotografias obrigatórias em cada rega (activista e regas de teste): entrada (pedida logo depois de marcar a entrada), evidência da rega (botão na ficha durante a rega) e saída (no formulário da saída). Sem as três a saída não se guarda.
- Cada fotografia é reduzida no telefone (1024 px, JPEG 60%) e guardada logo em IndexedDB com a chave `<registo>-<tipo>`; `emCurso.reg_id` e `emCurso.fotos` (hora de cada uma). Funciona sem rede.
- Envio: antes da linha do registo, para o bucket privado `rega-fotos/<perfil>/<registo>-<tipo>.jpg`; colunas `registos_rega.foto_entrada/_rega/_saida` (caminho) e `foto_*_em` (hora). Leitura do bucket: todos os papéis (como chuva e monitoria).
- Se o Android fechar o Chrome ao abrir a câmara: rascunho `rascFotoRega` volta ao ecrã da fotografia com aviso.
- Ver as fotografias (15/10/2026, v45): ficha do campo › "Regas deste campo" (RPC `regas_campo`, últimas 10 regas, carregada depois de abrir a ficha; todos os papéis, incluindo o cliente desde 15/10) com botões 📷 Entrada / Rega / Saída; a imagem abre por URL assinado (10 min) só ao tocar. Teste: `rega-test/teste_regas_campo.py`.
- Armazenamento: estimativa 0,5–1 GB/mês com todas as equipas. Organização no plano Pro desde 15/10/2026 (confirmado; 25 USD/mês, 100 GB de ficheiros, sem pausa por inactividade).
- Teste: `rega-test/teste_fotos_rega.py`; os testes de fluxo (teste.py, teste_en.py, teste_arranque.py) guardam as três fotografias com `fotos(pg)`.

## Mapa de plantas (15/10/2026, pedido do Dalmar via Valdo; teste do Dalmar, supervisores e técnicos a 16/10)
- Ficha do campo › "🌴 Mapa das plantas · teste" (técnico, supervisor, gestor; o Dalmar é gestor). Parado junto a cada muda, "📍 Marcar planta aqui": média ponderada das leituras do GPS durante 6 s (`PL_MEDIA_MS`), só leituras até ±8 m (`PL_PREC`); avisa se já há planta a < 3 m (`PL_PERTO`). Numeração seguida por campo.
- Desenho (SVG) com o limite do campo, as plantas (verde viva, laranja seca, vermelho morta; anel castanho = cava-roda e mulching, tracejado = só um) e a posição da pessoa. Tocar num ponto ou "Planta mais perto de mim" → estado, cava-roda, mulching, gravar; "Remover este ponto" para enganos.
- Sem rede: plantas no telefone (`rega.plantas` por campo) e fila `filaAlt` tipos 'planta', 'planta_est', 'planta_rem' (se a planta ainda não foi enviada, a mudança altera o próprio pedido de criação).
- Servidor: tabelas `plantas` (id do telefone, area_id, n, lat, lon, precisao_m, estado, cavaroda, mulching, marcada_em/por, actualizada_em/por, removida) e `plantas_eventos` (histórico: marcada / estado / removida). RPC `gravar_planta`, `estado_planta` (só aplica se for mais recente), `remover_planta` (marca removida). Leitura: quem vê o campo. Escrita só técnico, supervisor e gestor (activista fica para depois do teste).
- Contras falados com o Valdo: GPS do telefone ±2–5 m para ~8 m entre mudas (Mondlane: ~140 plantas em 0,8–1 ha); ~1 h por ha a mapear; registo muda a muda pesa para o activista.
- Teste: `rega-test/teste_plantas.py`. Nota: `teste_medir.py` falha agora no reload sem rede (também com a v42; problema do ambiente de teste, não da app).

## Revisão do suaíli (16/10/2026)
- Tabela enviada ao Valdo: `Rega_Coco_revisao_suaili_20261016.xlsx` (cópia em `rega-test/suaili/`). Folhas: 1 Activista (198 frases vistas nos testes do activista), 2 Técnico e supervisor (333), 3 Painel (117), 4 Frases com números (116). Coluna amarela "Kiswahili corrigido"; coluna ID = `D|<frase em português>` (dicionário `I18N_SW_D`) ou `R|<índice>` (expressão `I18N_SW_R`, mesma ordem que `R`). Nas frases variáveis [1], [2] = partes da expressão e { } = parte opcional.
- Quando voltar: para cada linha com correcção, D → substituir o valor em `I18N_SW_D`; R → reescrever a substituição da expressão nesse índice (pôr $1/$2 no lugar de [1]/[2]). Gerado por `rega-test/suaili/tabela.js`.
