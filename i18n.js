/* Rega Coco — tradução para inglês.
   A app é escrita em português; com o inglês escolhido, este ficheiro traduz os textos à medida que aparecem no ecrã.
   Os dados (nomes, comunidades, PR) não são traduzidos. A escolha fica guardada no telefone. */
'use strict';
const LINGUA = (() => { try { return localStorage.getItem('rega.lingua') || 'pt'; } catch { return 'pt'; } })();
function mudarLingua() {
  try { localStorage.setItem('rega.lingua', LINGUA === 'en' ? 'pt' : 'en'); } catch {}
  location.reload();
}
// botões de língua: mostram a língua para onde se muda
document.addEventListener('DOMContentLoaded', () => {
  for (const [id, pt, en] of [['h-lingua', 'EN', 'PT'], ['b-lingua', 'EN', 'PT'], ['l-lingua', 'English', 'Português']]) {
    const b = document.getElementById(id); if (b) b.textContent = LINGUA === 'en' ? en : pt;
  }
});
(() => {
  if (LINGUA !== 'en') return;
  document.documentElement.lang = 'en';
  const D = {
    // navegação e cabeçalho
    'Mapa': 'Map', 'Campos': 'Fields', 'Hoje': 'Today', 'Painel': 'Dashboard', 'Gestão': 'Admin',
    'Sair': 'Log out', 'Sair desta conta': 'Log out of this account', 'Sincronizar': 'Sync', '◎ Eu': '◎ Me',
    'As minhas': 'Mine', 'Todas': 'All', 'Rega Coco': 'Rega Coco', 'Rega Coco — Palma': 'Rega Coco — Palma',
    // funções
    'Gestor': 'Manager', 'Técnico': 'Technician', 'Supervisor': 'Supervisor', 'Director (só leitura)': 'Director (read-only)',
    'M&E (só leitura)': 'M&E (read-only)', 'Só painel (cliente / administração)': 'Dashboard only (client / management)',
    'Activista': 'Activist', 'Projecto': 'Project', 'Cliente': 'Client', 'Administração': 'Management board',
    // login
    'Entrar com o utilizador e o PIN dados pelo gestor.': 'Sign in with the username and PIN given by the manager.',
    'Utilizador (ou email do gestor)': 'Username (or manager email)', 'Utilizador (ou email)': 'Username (or email)',
    'PIN / senha': 'PIN / password', 'Entrar': 'Sign in', 'A entrar…': 'Signing in…', 'Senha': 'Password',
    'Utilizador ou PIN errado.': 'Wrong username or PIN.', 'Utilizador ou senha errados.': 'Wrong username or password.',
    'Este utilizador não tem perfil na app. Fale com o gestor.': 'This user has no profile in the app. Talk to the manager.',
    'Este utilizador não tem acesso ao painel.': 'This user has no access to the dashboard.',
    // mapa, lista, filtros
    'Por regar nesta ronda': 'Not yet watered this round', 'Regada nesta ronda': 'Watered this round', 'Sem activista': 'No activist',
    'As minhas áreas': 'My fields', 'Todas as áreas': 'All fields', 'Todas as comunidades': 'All communities',
    'Todas as situações': 'All statuses', 'Todos os activistas': 'All activists', '(sem activista)': '(no activist)',
    'Por atribuir (sem activista)': 'To assign (no activist)', 'Procurar produtor ou PR': 'Search producer or PR',
    'Mostra os 300 mais próximos. Use os filtros.': 'Showing the 300 nearest. Use the filters.', 'Ver': 'View',
    'zona por definir': 'zone to be defined', 'por definir': 'to be defined', '(por definir)': '(to be defined)',
    // ficha do campo
    'PR · área': 'PR · plot', 'Comunidade': 'Community', 'Zona': 'Zone', 'Plantas': 'Plants', 'Última rega': 'Last watering',
    'Ronda da equipa': 'Team round', 'Distância': 'Distance', 'Produtor': 'Producer', 'PR': 'PR', 'Ronda': 'Round',
    '(por atribuir)': '(to assign)', 'Coordenada': 'Coordinate',
    'Este campo não tem coordenada na base. A entrada fica registada sem validação de GPS.': 'This field has no coordinate in the database. The entry is recorded without GPS validation.',
    'Cheguei — marcar entrada': 'Arrived — record entry', 'Terminei — marcar saída': 'Finished — record exit',
    'Tem a rega de outro campo em curso. Termine-a primeiro.': 'Another field is being watered. Finish it first.',
    'Abrir o campo em curso': 'Open the field in progress', 'Tem uma rega em curso.': 'A watering is in progress.',
    '💧 Chegou a água (tuk-tuk) agora': '💧 Water (tuk-tuk) arrived now', 'A água já estava no campo quando chegámos': 'The water was already at the field when we arrived',
    '📍 Gravar a coordenada deste campo': '📍 Record this field’s coordinate', '📍 Corrigir a coordenada (estou no campo)': '📍 Correct the coordinate (I am at the field)',
    '👤 Atribuir a um activista': '👤 Assign to an activist', '👤 Mudar o activista deste campo': '👤 Change this field’s activist',
    '🗂 Definir a zona': '🗂 Set the zone', '🗂 Mudar a zona': '🗂 Change the zone',
    // entrada / saída
    'A ler o GPS…': 'Reading GPS…', 'Pode levar até 30 segundos. Fique em céu aberto.': 'It can take up to 30 seconds. Stay under open sky.',
    'A confirmar que ainda está no campo.': 'Confirming you are still at the field.',
    'Atenção: campo fora da sua lista': 'Warning: field outside your list', 'Porque vai regar este campo?': 'Why are you watering this field?',
    'Escreva o motivo': 'Write the reason', 'Escreva o motivo.': 'Write the reason.', 'Regar mesmo assim': 'Water anyway', 'Não regar este campo': 'Do not water this field',
    'Plantas regadas neste campo': 'Plants watered in this field', 'Pessoas que regaram este campo': 'People who watered this field',
    'Hora a que chegou a água (tuk-tuk)': 'Time the water (tuk-tuk) arrived', 'Deixe vazio se não chegou água.': 'Leave empty if no water arrived.',
    'Constrangimentos': 'Constraints', 'Explique (opcional)': 'Explain (optional)', 'Marcar saída e guardar': 'Record exit and save', 'Voltar': 'Back',
    'Falta de água': 'Lack of water', 'Mudas secas': 'Dry seedlings', 'Acesso difícil': 'Difficult access', 'Avaria': 'Breakdown', 'Outro': 'Other',
    'Escreva o número de plantas regadas.': 'Write the number of plants watered.', 'Escreva o número de pessoas (1 a 30).': 'Write the number of people (1 to 30).',
    'Rega guardada.': 'Watering saved.', 'Rega guardada no telefone (será enviada quando houver rede).': 'Watering saved on the phone (it will be sent when there is network).',
    'Próximo campo sugerido': 'Suggested next field', 'É só uma sugestão. Pode escolher outro campo.': 'It is only a suggestion. You can choose another field.',
    'Ver no mapa': 'View on map', 'Escolher outro campo': 'Choose another field', 'Não há sugestão de próximo campo.': 'No next-field suggestion.', 'Fechar': 'Close',
    // início do dia
    'Início do dia': 'Start of the day', 'Alterar pessoas presentes': 'Change people present', 'Guardar': 'Save',
    'Quantas pessoas estão hoje na rega com a equipa (incluindo o activista)?': 'How many people are watering with the team today (including the activist)?',
    'Escreva um número entre 1 e 30.': 'Write a number between 1 and 30.',
    // hoje
    'Pessoas hoje': 'People today', 'Alterar': 'Change', 'Registar': 'Record', 'Campos regados hoje': 'Fields watered today',
    'Plantas regadas hoje': 'Plants watered today', 'Por enviar': 'To send', 'Registos recebidos': 'Records received',
    'Abrir painel geral': 'Open general dashboard', 'Pessoas': 'People', '1.ª água': '1st water', 'Horas': 'Hours', 'Alertas': 'Alerts',
    // GPS
    'Este telefone não tem GPS disponível no navegador.': 'This phone has no GPS available in the browser.',
    'A app não tem autorização para usar a localização. Autorize nas definições do telefone.': 'The app is not allowed to use location. Allow it in the phone settings.',
    'Não foi possível obter o GPS. Vá para céu aberto e tente de novo.': 'Could not get GPS. Go under open sky and try again.',
    'Onde ficar:': 'Where to stand:', 'Precisão agora': 'Accuracy now', 'a ler…': 'reading…', 'sem sinal de GPS': 'no GPS signal',
    'sem autorização de localização': 'no location permission',
    'no centro do campo, longe de árvores grandes, casas e viaturas. Telefone parado, à altura do peito, ecrã para cima. Espere 30 a 60 segundos até a precisão baixar.': 'in the centre of the field, away from large trees, houses and vehicles. Phone still, at chest height, screen up. Wait 30 to 60 seconds for the accuracy to improve.',
    'Gravar esta coordenada': 'Save this coordinate', 'Cancelar': 'Cancel', 'Gravar': 'Save', 'Coordenada gravada.': 'Coordinate saved.',
    'Coordenada gravada. Agora atribua o campo a um activista.': 'Coordinate saved. Now assign the field to an activist.',
    // atribuir / zona
    'Atribuir a': 'Assign to', 'Proposta da base:': 'Database proposal:', 'Proposta:': 'Proposal:', 'Sem proposta': 'No proposal',
    '(fora da sua equipa)': '(outside your team)', '✓ Confirmar proposta': '✓ Confirm proposal', 'Escolher outro': 'Choose another',
    'Regra: rega o activista da comunidade onde o campo está. Confirme antes de gravar.': 'Rule: the activist of the community where the field is waters it. Check before saving.',
    'activista actual:': 'current activist:', 'activista:': 'activist:', 'Zona retirada.': 'Zone removed.',
    // sincronização
    'Tudo sincronizado.': 'Everything is synced.', 'Sem rede. Os registos ficam guardados no telefone.': 'No network. Records stay on the phone.',
    'Há registos por enviar. Se sair agora, ficam no telefone e são enviados no próximo login deste utilizador. Sair?': 'There are records to send. If you log out now, they stay on the phone and are sent at this user’s next login. Log out?',
    // gestão
    'Criar login de activista': 'Create activist login', 'Utilizador': 'Username', 'PIN (6 dígitos)': 'PIN (6 digits)',
    'Anote o PIN e entregue-o ao activista. A app não volta a mostrá-lo.': 'Write down the PIN and give it to the activist. The app will not show it again.',
    'Criar login': 'Create login', 'Ainda nenhum.': 'None yet.', 'Novo PIN': 'New PIN', 'Nova senha': 'New password',
    'Outros acessos': 'Other access', 'Função': 'Role', 'Nome': 'Name', 'Nome completo': 'Full name', 'Senha (8 ou mais caracteres)': 'Password (8 or more characters)',
    'Criar acesso': 'Create access', 'Outra pessoa (escrever o nome)…': 'Another person (type the name)…',
    'o mesmo que o técnico, para as equipas dos seus técnicos; também muda a zona dos campos.': 'same as the technician, for the teams of their technicians; also changes the field zone.', 'o mesmo que o director.': 'same as the director.', 'vê apenas o painel geral.': 'sees only the general dashboard.',
    'vê os campos e a rega das equipas dos seus activistas (e das que cobre) e o painel geral; grava coordenadas, atribui campos e pode fazer regas de teste.': 'sees the fields and watering of their activists’ teams (and those they cover) and the general dashboard; records coordinates, assigns fields and can do test waterings.',
    'vê todos os campos, a rega do dia e o painel; não regista regas.': 'sees all fields, the day’s watering and the dashboard; does not record waterings.',
    'Coberturas (ausências)': 'Cover (absences)', 'Quem cobre': 'Who covers', 'Cobre as equipas de': 'Covers the teams of', 'Desde': 'From',
    'Até (vazio = até terminar)': 'Until (empty = until ended)', 'Gravar cobertura': 'Save cover', 'Nenhuma cobertura activa.': 'No active cover.',
    'Quando um técnico ou supervisor está ausente, um colega passa a ver e gerir as equipas dele durante o período indicado.': 'When a technician or supervisor is absent, a colleague sees and manages their teams for the period set.',
    'Terminar hoje': 'End today', 'Anular': 'Cancel', 'ainda não começou': 'not started yet', 'até terminar': 'until ended',
    'Cobertura gravada.': 'Cover saved.', 'Cobertura anulada.': 'Cover cancelled.', 'Cobertura termina hoje.': 'Cover ends today.',
    'Escolha quem cobre e quem é coberto.': 'Choose who covers and who is covered.',
    'Quem viu o painel': 'Who viewed the dashboard', 'Pessoa': 'Person', 'Última visita': 'Last visit', 'Visitas (30 dias)': 'Visits (30 days)', 'Total': 'Total',
    'Conta no máximo uma visita por pessoa a cada 30 minutos.': 'Counts at most one visit per person every 30 minutes.', 'Ainda ninguém abriu o painel.': 'Nobody has opened the dashboard yet.',
    'A senha tem de ter pelo menos 8 caracteres.': 'The password must have at least 8 characters.', 'O PIN tem de ter 6 dígitos.': 'The PIN must have 6 digits.',
    'A carregar…': 'Loading…', '(já tem acesso)': '(already has access)', '(teste)': '(test)',
    // painel
    'Painel de Rega': 'Watering dashboard', 'Painel de rega': 'Watering dashboard', 'Painel geral': 'General dashboard', 'Projecto Coco · Palma': 'Coco Project · Palma',
    'Rega de emergência': 'Emergency watering', 'Actualizar': 'Refresh', 'Utilizador (ou email)': 'Username (or email)',
    'Plantas vivas em campos regados': 'Live plants in watered fields', 'Campos regados': 'Fields watered', 'Frequência média': 'Average frequency',
    'entre duas regas do mesmo campo': 'between two waterings of the same field', 'Espera pela água': 'Wait for water',
    'média, da entrada no campo à chegada do tuk-tuk': 'average, from field entry to tuk-tuk arrival', 'Plantas regadas (total)': 'Plants watered (total)',
    'Pessoas-dia': 'Person-days', 'soma das pessoas presentes por equipa e dia': 'sum of people present per team and day', 'Plantas por pessoa-dia': 'Plants per person-day',
    'produtividade média': 'average productivity', 'Equipas activas': 'Active teams', 'Plantas regadas por dia': 'Plants watered per day',
    'Registos da app com plantas regadas (exclui testes).': 'App records with plants watered (tests excluded).', 'Ver tabela': 'View table',
    'Plantas vivas regadas por comunidade': 'Live plants watered per community', '% das plantas vivas da comunidade em campos já regados pela app.': '% of the community’s live plants in fields already watered through the app.',
    'Equipas — rondas e produtividade': 'Teams — rounds and productivity',
    'Cada equipa rega toda a sua lista antes de repetir um campo. A duração de cada ronda concluída é o ciclo provisório da comunidade.': 'Each team waters its whole list before repeating a field. The length of each completed round is the community’s provisional cycle.',
    'Chegada da água (tuk-tuk) por equipa': 'Water (tuk-tuk) arrival per team', 'Últimos 14 dias. Espera = minutos entre a entrada no campo e a chegada da água.': 'Last 14 days. Wait = minutes between field entry and water arrival.',
    'Constrangimentos registados': 'Constraints recorded', 'Número de registos com cada constrangimento.': 'Number of records with each constraint.',
    'Qualidade dos registos': 'Record quality', 'Controlo dos dados recebidos.': 'Check of the data received.', 'Ainda sem registos.': 'No records yet.',
    'Data': 'Date', 'Equipas': 'Teams', 'Regados': 'Watered', 'Vivas': 'Live', 'Vivas regadas': 'Live watered', 'Regas': 'Waterings', 'Dias entre regas': 'Days between waterings',
    'Equipa (activista)': 'Team (activist)', 'Progresso da ronda': 'Round progress', 'Rondas concluídas (dias)': 'Completed rounds (days)', 'Dias trab.': 'Days worked',
    'Plantas/pessoa-dia': 'Plants/person-day', 'Min/campo': 'Min/field', 'Espera água (min)': 'Water wait (min)', 'Equipa': 'Team', 'Início do trabalho': 'Work start',
    'Chegadas da água': 'Water arrivals', 'Espera média (min)': 'Average wait (min)', 'sem registo': 'not recorded', 'Regas de campo recebidas': 'Field waterings received',
    'Fora da lista da equipa (com motivo)': 'Outside the team list (with reason)', 'GPS fora do campo': 'GPS outside the field', 'plantas regadas': 'plants watered',
    'das plantas vivas': 'of live plants', 'registos': 'records', 'frequência: ainda sem repetições': 'frequency: no repeats yet', 'Gráfico de colunas': 'Column chart', 'Gráfico de barras': 'Bar chart',
    // direcções
    'Norte': 'North', 'Nordeste': 'North-east', 'Este': 'East', 'Sudeste': 'South-east', 'Sul': 'South', 'Sudoeste': 'South-west', 'Oeste': 'West', 'Noroeste': 'North-west',
    'fora da lista': 'outside list',
    // erros do servidor (criação de logins)
    'Sessão inválida': 'Invalid session', 'Só o gestor pode gerir logins': 'Only the manager can manage logins', 'Pedido inválido': 'Invalid request',
    'Função inválida': 'Invalid role', 'Escreva o nome': 'Write the name', "Esta pessoa já tem acesso. Use 'Nova senha'.": "This person already has access. Use 'New password'.",
    'Utilizador: 3 a 30 letras minúsculas, números, ponto, hífen ou _': 'Username: 3 to 30 lowercase letters, numbers, dot, hyphen or _',
    'A senha tem de ter pelo menos 8 caracteres': 'The password must have at least 8 characters', 'Esse utilizador já existe': 'That username already exists',
    'Utilizador não encontrado': 'User not found', 'O PIN tem de ter 6 dígitos': 'The PIN must have 6 digits', 'Activista não encontrado': 'Activist not found',
    "Este activista já tem login. Use 'repor PIN'.": "This activist already has a login. Use 'New PIN'.", 'Este activista ainda não tem login': 'This activist has no login yet',
    'Acção desconhecida': 'Unknown action', 'Método não permitido': 'Method not allowed',
  };
  // textos com partes variáveis (números, horas, nomes)
  const R = [
    [/^(.+) de (.+) campos regados$/, '$1 of $2 fields watered'], [/^(.+) dias entre regas$/, (m, a) => `${a.replace(',', '.')} days between waterings`],
    [/^(.+) de (.+) campos$/, '$1 of $2 fields'], [/^(.+) de (.+) plantas vivas$/, '$1 of $2 live plants'], [/^(.+) campos$/, '$1 fields'], [/^(.+) campos por atribuir\.$/, '$1 fields to assign.'], [/^(.+) campos · ordenados pela distância$/, '$1 fields · sorted by distance'],
    [/^(\d+) por enviar$/, '$1 to send'], [/^Sinc\. (.+)$/, 'Sync $1'], [/^(.+) plantas$/, '$1 plants'], [/^(.+) plantas vivas$/, '$1 live plants'],
    [/^(.+) mudas plantadas$/, '$1 seedlings planted'], [/^água (.+)$/, 'water $1'], [/^(.+) de (.+) campos$/, '$1 of $2 fields'], [/^(.+) de (.+) plantas vivas$/, '$1 of $2 live plants'],
    [/^(.+) mil$/, '$1k'], [/^(.+) dias$/, '$1 days'], [/^(\d+) equipas$/, '$1 teams'], [/^(\d+) pessoas$/, '$1 people'],
    [/^Acesso criado: (.+) → utilizador$/, 'Access created: $1 → username'], [/^Login criado: (.+) → utilizador$/, 'Login created: $1 → username'],
    [/^Acessos criados \((\d+)\)$/, 'Accesses created ($1)'], [/^Activistas com login \((\d+) de (\d+)\)$/, 'Activists with login ($1 of $2)'],
    [/^Actualizado (.+)$/, 'Updated $1'], [/^desde (.+)$/, 'since $1'], [/^Campo atribuído a (.+)\. Será enviado quando houver rede\.$/, 'Field assigned to $1. It will be sent when there is network.'],
    [/^Campo atribuído a (.+)\.$/, 'Field assigned to $1.'], [/^(.+) cobre (.+)$/, '$1 covers $2'],
    [/^Entrada marcada às (\S+) \(campo fora da lista\)\.$/, 'Entry recorded at $1 (field outside the list).'], [/^Entrada marcada às (\S+) · a (.+) m do campo\.$/, 'Entry recorded at $1 · $2 m from the field.'],
    [/^Entrada marcada às (\S+)\.$/, 'Entry recorded at $1.'], [/^Entrada às (.+)$/, 'Entry at $1'],
    [/^Este campo já foi regado na ronda (\d+)\. Só pode voltar a regá-lo depois de regar todos os campos da sua lista \(faltam (\d+) de (\d+)\)\.$/, 'This field was already watered in round $1. You can water it again only after watering all fields on your list ($2 of $3 left).'],
    [/^Este campo é de (.+)\. Não conta para a sua ronda\.$/, 'This field belongs to $1. It does not count for your round.'],
    [/^Está a (.+) m do campo \(precisão ±(.+) m\)\. Só pode marcar a entrada até (.+) m do campo\.$/, 'You are $1 m from the field (accuracy ±$2 m). You can only record entry within $3 m of the field.'],
    [/^Está a (.+) m do campo\. Marque a saída ainda no campo \(até (.+) m\)\.$/, 'You are $1 m from the field. Record the exit while still at the field (within $2 m).'],
    [/^Hoje · (.+)$/, 'Today · $1'], [/^Na base: (.+)\. Se regou menos, escreva o número real\.$/, (m, a) => `In the database: ${tr(a)}. If you watered fewer, write the real number.`],
    [/^Os (\d+) campos da lista foram regados de (.+) a (.+)\. A ronda (\d+) começa agora\.$/, 'The $1 fields on the list were watered from $2 to $3. Round $4 starts now.'],
    [/^Por regar \(ronda (\d+)\)$/, 'Not yet watered (round $1)'], [/^Regada na ronda (\d+)$/, 'Watered in round $1'], [/^Ronda (\d+)$/, 'Round $1'], [/^Ronda (\d+) concluída!$/, 'Round $1 completed!'],
    [/^(\d+) de (\d+) campos$/, '$1 of $2 fields'], [/^faltam (\d+)$/, '$1 left'],
    [/^Senha de (.+) alterada\.$/, 'Password for $1 changed.'], [/^PIN de (.+) alterado\.$/, 'PIN for $1 changed.'], [/^(.+): atribuído a (.+)\.$/, '$1: assigned to $2.'],
    [/^Zona definida: (.+)\.(.*)$/, (m, z, r) => `Zone set: ${z}.${r ? ' It will be sent when there is network.' : ''}`],
    [/^(\d+) registo\(s\) enviados\.$/, '$1 record(s) sent.'], [/^Falhou o envio: (.+)$/, 'Sending failed: $1'], [/^Não foi gravado \((.+)\): (.+)$/, 'Not saved ($1): $2'],
    [/^de (\d+) equipas com lista$/, 'of $1 teams with a list'], [/^em (.+) regas de campo$/, 'in $1 field waterings'],
    [/^Água \(tuk-tuk\) no campo às (.+)\.$/, 'Water (tuk-tuk) at the field at $1.'], [/^Água no campo às (.+)\.$/, 'Water at the field at $1.'],
    [/^Escreveu (.+), mas a base diz (.+)\. Confirma\?$/, (m, a, b) => `You wrote ${a}, but the database says ${tr(b)}. Confirm?`],
    [/^Só pode gravar com precisão de (.+) m ou melhor\. O ideal é (.+) m ou menos\.$/, 'You can only save with an accuracy of $1 m or better. Ideally $2 m or less.'],
    [/^(±.+ m) \(melhor até agora: (±.+ m)\)$/, '$1 (best so far: $2)'],
    [/^Todas as pessoas desta função na lista já têm acesso \(ver "Acessos criados" abaixo\)\.$/, 'Everyone in this role on the list already has access (see "Accesses created" below).'],
    [/^(.+) \(já tem acesso\)$/, (m, a) => `${tr(a)} (already has access)`], [/^(.+) \(fora da sua equipa\)$/, (m, a) => `${tr(a)} (outside your team)`],
    [/^Memória do telefone cheia: (.+)$/, 'Phone memory full: $1'], [/^Escolha o nome da lista de técnicos$/, 'Choose the name from the technicians list'],
    [/^Escolha o nome da lista de supervisores$/, 'Choose the name from the supervisors list'],
  ];
  const SEP = / (·|—|›|→) /;
  function tr(s) {
    if (!s || !/[A-Za-zÀ-ú]/.test(s)) return s;
    const m = s.match(/^(\s*)([\s\S]*?)(\s*)$/), t = m[2];
    if (D[t]) return m[1] + D[t] + m[3];
    for (const [re, sub] of R) if (re.test(t)) return m[1] + t.replace(re, sub) + m[3];
    const pre = t.match(/^([·:—›→]\s+)([\s\S]+)$/); if (pre) return m[1] + pre[1] + tr(pre[2]) + m[3];
    if (SEP.test(t)) { const partes = t.split(SEP); const out = partes.map((p, i) => (i % 2 ? p : tr(p))); return m[1] + rejuntar(out) + m[3]; }
    return s;
  }
  function rejuntar(out) { let r = ''; for (let i = 0; i < out.length; i++) r += i % 2 ? ` ${out[i]} ` : out[i]; return r; }
  window.trEN = tr;
  const feito = new WeakSet();
  function traduzNo(n) {
    if (n.nodeType === 3) {
      if (['SCRIPT', 'STYLE'].includes(n.parentNode?.nodeName)) return;
      const v = tr(n.nodeValue); if (v !== n.nodeValue) n.nodeValue = v; return;
    }
    if (n.nodeType !== 1) return;
    for (const a of ['placeholder', 'title', 'aria-label']) { const v = n.getAttribute(a); if (v) { const t = tr(v); if (t !== v) n.setAttribute(a, t); } }
    n.childNodes.forEach(traduzNo);
  }
  const obs = new MutationObserver((ms) => { for (const m of ms) { if (m.type === 'characterData') traduzNo(m.target); else m.addedNodes.forEach(traduzNo); } });
  const ini = () => { document.title = tr(document.title); traduzNo(document.body); obs.observe(document.body, { childList: true, subtree: true, characterData: true }); };
  if (document.body) ini(); else document.addEventListener('DOMContentLoaded', ini);
  const a0 = window.alert.bind(window), c0 = window.confirm.bind(window);
  window.alert = (msg) => a0(tr(String(msg))); window.confirm = (msg) => c0(tr(String(msg)));
})();
