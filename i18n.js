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
  for (const [id, pt, en] of [['h-lingua', 'EN', 'PT'], ['b-lingua', 'EN', 'PT'], ['lc-lingua', 'EN', 'PT'], ['le-lingua', 'EN', 'PT'], ['l-lingua', 'English', 'Português']]) {
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
    'PIN / senha': 'PIN / password',
    'Bom dia.': 'Good morning.', 'Boa tarde.': 'Good afternoon.', 'Boa noite.': 'Good evening.', 'Entre para registar a rega.': 'Sign in to record watering.',
    'Técnico / Supervisor': 'Technician / Supervisor', 'o seu utilizador': 'your username', 'PIN (6 números)': 'PIN (6 digits)', 'Mostrar': 'Show', 'Esconder': 'Hide',
    'O utilizador e o PIN são dados pelo gestor.': 'The username and PIN are given by the manager.', 'O utilizador e a senha são dados pelo gestor.': 'The username and password are given by the manager.',
    'Outros acessos (escritório)': 'Other access (office)', 'Acesso de escritório: entrar com o utilizador e a senha dados pelo gestor.': 'Office access: sign in with the username and password given by the manager.',
    'Esqueceu a senha? Fale com o gestor.': 'Forgot your password? Talk to the manager.', 'Voltar ao acesso de campo': 'Back to field access', 'Entrar': 'Sign in', 'A entrar…': 'Signing in…', 'Senha': 'Password',
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
    '➕ Voltar a pôr um campo na rega': '➕ Put a field back on the watering list', 'Voltar a pôr um campo na rega': 'Put a field back on the watering list',
    'Campos que estão fora do plano de rega. Procure pelo nome do produtor ou pelo PR (pelo menos 3 letras). Precisa de rede.': 'Fields that are out of the watering plan. Search by producer name or PR (at least 3 letters). Needs network.',
    'Nome do produtor ou PR': 'Producer name or PR', 'A procurar…': 'Searching…', 'Sem rede. Esta procura precisa de internet.': 'No network. This search needs internet.',
    'Nenhum campo fora do plano com esse nome ou PR. Se o campo existe, envie o PR ao gestor.': 'No field outside the plan with that name or PR. If the field exists, send the PR to the manager.',
    'Primeiros 40 resultados. Escreva mais letras para afinar.': 'First 40 results. Type more letters to narrow down.', 'Voltar a regar': 'Water again',
    'Este campo volta à lista de rega a partir de agora.': 'This field goes back on the watering list from now on.', 'Motivo (opcional)': 'Reason (optional)', 'Ex.: o poço secou': 'E.g. the well dried up',
    'Novo na rega': 'New on the list', 'Na rega desde': 'On the list since', 'Na base: tinha água': 'In the database: had water', 'Na base: sem água': 'In the database: no water',
    'sem coordenada': 'no coordinate', 'Sem rede. Tente quando houver rede.': 'No network. Try when there is network.',
    'Medir a área (andar à volta do campo)': 'Measure the area (walk around the field)', 'Medir a área de novo (andar à volta)': 'Measure the area again (walk around)',
    'Precisão do GPS': 'GPS accuracy', 'Pontos': 'Points', 'Distância andada': 'Distance walked', 'Área até agora': 'Area so far', 'Área': 'Area', 'Perímetro': 'Perimeter',
    '▶ Começar': '▶ Start', '⏸ Pausar': '⏸ Pause', '▶ Continuar': '▶ Continue', '📍 Marcar canto': '📍 Mark corner', '↶ Desfazer último ponto': '↶ Undo last point', 'Recomeçar': 'Start over',
    '✓ Terminar e gravar a área': '✓ Finish and save the area', 'Sair (os pontos ficam guardados no telefone)': 'Leave (the points stay saved on the phone)',
    'Gravar esta área': 'Save this area', 'Voltar e continuar a medir': 'Go back and keep measuring', 'Plantas vivas na base': 'Live plants in the database',
    '(medida no campo)': '(measured in the field)', 'Ainda sem posição do GPS.': 'No GPS position yet.', 'Apagar os pontos marcados e recomeçar?': 'Delete the marked points and start over?',
    'Como medir:': 'How to measure:', 'sem sinal de GPS': 'no GPS signal', 'sem autorização de localização': 'no location permission',
    '📐 Medir a área (andar à volta do campo)': '📐 Measure the area (walk around the field)', '📐 Medir a área de novo (andar à volta)': '📐 Measure the area again (walk around)',
    '🏘 Mudar a comunidade': '🏘 Change the community', 'Nova comunidade': 'New community', 'A zona volta a ficar por definir.': 'The zone goes back to not set.',
    '🔒 Fechar a correcção da coordenada e da área': '🔒 Close correction of the coordinate and area',
    '🔓 Deixar o supervisor/técnico corrigir a coordenada e medir de novo': '🔓 Let the supervisor/technician correct the coordinate and measure again',
    'O supervisor e o técnico já podem corrigir a coordenada e medir a área deste campo. Fecha de novo depois de gravarem.': 'The supervisor and technician can now correct the coordinate and measure the area of this field. It closes again after they save.',
    'Correcção fechada.': 'Correction closed.',
    '✓ Registado': '✓ Recorded', 'Corrigir ou outra comunidade': 'Correct or another community',
    '📷 Tirar fotografia': '📷 Take photo', '📷 Tirar': '📷 Take', 'A app não tem autorização para usar a câmara. Autorize a câmara no Chrome (cadeado ao lado do endereço) ou use «Escolher da galeria».': 'The app is not allowed to use the camera. Allow the camera in Chrome (padlock next to the address) or use «Choose from gallery».', '🖼️ Escolher da galeria': '🖼️ Choose from gallery',
    'O telefone fechou a app ao abrir a câmara. Os dados foram recuperados. Se voltar a acontecer, tire a fotografia com a câmara do telefone e use «Escolher da galeria».': 'The phone closed the app when the camera opened. Your data was recovered. If it happens again, take the photo with the phone camera and use «Choose from gallery».',
    'Sem rede. O resumo das equipas aparece quando houver rede.': 'No network. The team summary appears when there is network.',
    'Sem rede: painel guardado no telefone. Actualiza quando houver rede.': 'No network: dashboard saved on the phone. It updates when there is network.',
    'Sem rede. O painel aparece quando houver rede; depois fica guardado no telefone.': 'No network. The dashboard appears when there is network; then it is saved on the phone.',
    'Equipas — rondas e produtividade': 'Teams — rounds and productivity', 'Equipas — rondas': 'Teams — rounds', 'A produtividade por equipa está na secção': 'Productivity by team is in the section', ', mais abaixo.': ', further down.',
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
    'Produtores': 'Producers', 'Tuk-tuk': 'Tuk-tuk', 'Início': 'Start', 'Fim': 'End',
    'Produtores = produtores com campos regados hoje. Tuk-tuk = hora da 1.ª chegada da água. Início = entrada no 1.º campo; Fim = saída do último. Alertas = regas fora da lista da equipa.': 'Producers = producers with fields watered today. Tuk-tuk = time of the first water arrival. Start = entry to the first field; End = exit from the last. Alerts = waterings outside the team list.',
    'Plantas regadas por dia, por equipa': 'Plants watered per day, per team', 'Equipas agrupadas por comunidade.': 'Teams grouped by community.',
    // monitoria
    'Monitoria': 'Monitoring', 'Monitoria por amostragem': 'Sample-based monitoring', 'Verificado': 'Checked', 'Por verificar': 'To check',
    'Sem campos para verificar. A lista sai a partir das 18:00, com campos regados nesse dia.': 'No fields to check. The list is issued from 18:00, with fields watered that day.',
    'Monitoria: campo já verificado.': 'Monitoring: field already checked.', '✓ Verificar este campo (monitoria)': '✓ Check this field (monitoring)',
    'O solo mostra sinais de rega?': 'Does the soil show signs of watering?', 'Sim': 'Yes', 'Não': 'No', 'Estado das mudas': 'Seedling condition',
    'Vivas': 'Alive', 'Secas': 'Dry', 'Mortas': 'Dead', 'Nota (0 a 10)': 'Score (0 to 10)', 'Fotografia do campo': 'Photo of the field',
    'Observação (opcional)': 'Note (optional)', 'Gravar verificação': 'Save check', 'Responda às duas perguntas e escolha a nota.': 'Answer both questions and choose the score.',
    'Tire a fotografia do campo.': 'Take the photo of the field.', 'Não foi possível ler a fotografia. Tire outra.': 'Could not read the photo. Take another one.',
    'Verificação guardada.': 'Check saved.', 'Verificação guardada no telefone (será enviada quando houver rede).': 'Check saved on the phone (it will be sent when there is network).',
    'Cada técnico e supervisor recebe, a partir das 18:00, uma lista de campos regados nesse dia para verificar. Listas diferentes para cada pessoa, campos sorteados.': 'From 18:00 each technician and supervisor receives a list of fields watered that day to check. Different lists for each person, fields drawn at random.',
    'Campos por dia, por pessoa': 'Fields per day, per person',
    'Campos sorteados entre os regados em cada dia e verificados no campo por técnicos e supervisores (nota de 0 a 10). Período = dia da rega verificada.': 'Fields drawn from those watered each day and checked on site by technicians and supervisors (score 0 to 10). Period = day of the watering checked.',
    'Por técnico (área de supervisão)': 'By technician (supervision area)', 'Método LQAS: a conclusão sobre cada técnico pede 19 campos verificados.': 'LQAS method: a conclusion on each technician requires 19 checked fields.',
    'Por equipa': 'By team', 'Por pessoa que verificou': 'By person who checked', 'Campos verificados': 'Fields checked', 'Nota média': 'Average score', 'de 0 a 10': 'from 0 to 10',
    'Solo com sinais de rega': 'Soil with signs of watering', 'vivas / secas / mortas': 'alive / dry / dead', 'Verificados': 'Checked', 'Amostra LQAS': 'LQAS sample',
    'Sem sinais de rega': 'No signs of watering', 'Mudas secas ou mortas': 'Dry or dead seedlings', 'Sorteados': 'Drawn', 'Nota média dada': 'Average score given', 'Pessoa': 'Person',
    // 11/10/2026: equipa por número, meta de 140 plantas, deslocação, monitoria por planta
    '% meta': '% target', 'Desloc.': 'Travel', 'Quantas pessoas tem esta equipa (incluindo o activista)?': 'How many people are in this team (including the activist)?',
    'Serve para mostrar as faltas: pessoas presentes no dia comparadas com este número.': 'Used to show absences: people present on the day compared with this number.',
    'Percurso no campo': 'Route through the field', 'Plantas no campo': 'Plants in the field', 'Escolha o percurso.': 'Choose the route.',
    'Escreva o número de plantas no campo.': 'Write the number of plants in the field.', 'Plantas a observar': 'Plants to observe', 'Observadas': 'Observed',
    'Com solo húmido': 'With moist soil', 'Nota': 'Score', 'Vivas / secas / mortas': 'Alive / dry / dead', 'Amostra completa': 'Sample complete',
    'Pode observar mais plantas, se quiser.': 'You can observe more plants if you wish.', 'Solo húmido (rega efectiva)?': 'Moist soil (effective watering)?',
    'Estado da planta': 'Plant condition', 'Viva': 'Alive', 'Seca': 'Dry', 'Morta': 'Dead', 'Desfazer a última planta': 'Undo the last plant',
    'Meta: 140 plantas por pessoa por dia': 'Target: 140 plants per person per day',
    '% da meta = plantas regadas ÷ (140 × pessoas presentes).': '% of target = plants watered ÷ (140 × people present).',
    'Faltas = pessoas da equipa que não estiveram presentes (soma dos dias com rega).': 'Absences = team members who were not present (sum over days with watering).',
    'Por dia': 'By day', 'Por semana': 'By week', 'Dias com rega': 'Days with watering', 'Pessoas-dia': 'Person-days', 'Faltas': 'Absences', 'Meta': 'Target', '% da meta': '% of target',
    'F = faltas nesse dia ou semana. Passe o dedo ou o rato sobre a célula para ver plantas e pessoas.': 'A = absences on that day or week. Hover over or tap the cell to see plants and people.',
    'Tempo por campo e deslocação entre campos': 'Time per field and travel between fields',
    'Médias por equipa no período. Rega = da entrada à saída do campo. Deslocação = da saída de um campo à entrada no seguinte, no mesmo dia.': 'Averages per team in the period. Watering = from field entry to exit. Travel = from leaving one field to entering the next, on the same day.',
    'Rega por campo (min)': 'Watering per field (min)', 'Deslocação entre campos (min)': 'Travel between fields (min)', 'Deslocações medidas': 'Trips measured',
    'Campos regados': 'Fields watered', 'Plantas com solo húmido': 'Plants with moist soil', 'Campos não regados': 'Fields not watered', 'Plantas secas ou mortas': 'Dry or dead plants',
    'Campos sorteados entre os regados em cada dia e verificados no campo por técnicos e supervisores, planta a planta, num percurso (X, W, Z ou diagonal). Nota = % de plantas com solo húmido ÷ 10. Campo regado = pelo menos 80% das plantas observadas com solo húmido. Período = dia da rega verificada.': 'Fields drawn from those watered each day and checked on site by technicians and supervisors, plant by plant, along a route (X, W, Z or diagonal). Score = % of plants with moist soil ÷ 10. Field watered = at least 80% of observed plants with moist soil. Period = day of the checked watering.',
    'Avisos da monitoria': 'Monitoring alerts', 'Campos verificados nos últimos 14 dias com plantas sem solo húmido.': 'Fields checked in the last 14 days with plants without moist soil.',
    'Rever plantas': 'Check plants', 'Campo não regado': 'Field not watered', 'Resultado LQAS': 'LQAS result', 'em curso': 'in progress', 'Aceite': 'Accepted', 'Abaixo do limiar': 'Below threshold',
    'Método LQAS: com 19 campos verificados, a área do técnico é aceite se pelo menos 13 estiverem regados (usa as 19 verificações mais recentes do período).': 'LQAS method: with 19 fields checked, the technician\'s area is accepted if at least 13 are watered (uses the 19 most recent checks in the period).',
    ' Campo considerado regado (≥ 80%), mas reveja as plantas sem rega.': ' Field considered watered (≥ 80%), but check the plants without watering.',
    'Campo considerado regado (≥ 80%), mas reveja as plantas sem rega.': 'Field considered watered (≥ 80%), but check the plants without watering.',
    'Campo considerado não regado (menos de 80% das plantas com solo húmido).': 'Field considered not watered (less than 80% of plants with moist soil).',
    ' Campo considerado não regado (menos de 80% das plantas com solo húmido).': ' Field considered not watered (less than 80% of plants with moist soil).',
    '% da meta por dia (todas as equipas)': '% of target per day (all teams)', '% da meta por equipa no período': '% of target per team in the period',
    'meta 100%': 'target 100%', 'meta': 'target', 'da meta': 'of target', 'Deslocação média entre campos (min)': 'Average travel between fields (min)', 'de deslocação média': 'average travel',
    'Nota média (0 a 10) dos campos verificados de cada equipa.': 'Average score (0 to 10) of each team\'s checked fields.', 'nota 8 (80%)': 'score 8 (80%)', 'nota média': 'average score',
    'A app calcula a amostra a partir deste número.': 'The app calculates the sample from this number.',
    'A base não tem o número de plantas deste campo. Conte as plantas e escreva o número.': 'The database has no plant count for this field. Count the plants and write the number.',
    'Plantas que existem hoje no campo': 'Plants in the field today', 'O número de plantas mudou? Corrigir': 'Has the number of plants changed? Correct it',
    'Corrigido no campo. A app recalcula a amostra.': 'Corrected in the field. The app recalculates the sample.',
    'Regado em teste (por si)': 'Watered in a test (by you)', 'Sem rede. A primeira entrada neste telefone precisa de internet. Depois disso, pode entrar sem rede.': 'No network. The first sign-in on this phone needs internet. After that, you can sign in without network.',
    'Entrou sem rede. Os registos ficam no telefone e são enviados quando houver rede.': 'Signed in without network. Records stay on the phone and are sent when there is network.',
    'A senha ou o PIN mudou. Entre de novo com rede; os registos continuam guardados no telefone.': 'The password or PIN has changed. Sign in again with network; records remain saved on the phone.',
    'A rede caiu durante a entrada. Tente de novo.': 'The network dropped during sign-in. Try again.', 'Escreva o utilizador e o PIN.': 'Write the username and PIN.', 'Escreva o utilizador e a senha.': 'Write the username and password.',
    'Mulching e cava-roda': 'Mulching and planting basin', 'Os dois': 'Both', 'Só mulching': 'Mulching only', 'Só cava-roda': 'Basin only', 'Nenhum': 'Neither',
    'Com mulching / com cava-roda': 'With mulching / with basin', 'Com mulching (cobertura morta), um campo regado na véspera ainda mostra humidade.': 'With mulching, a field watered the day before still shows moisture.',
    'Plantas com cobertura morta': 'Plants with mulch', 'Solo húmido com e sem cobertura morta': 'Moist soil with and without mulch',
    '(equipa por definir)': '(team size not set)',
    'Progresso da ronda actual': 'Current round progress', 'Plantas regadas por comunidade no período': 'Plants watered per community in the period', 'Ver tabela por dia': 'See table by day',
    'Espera média pela água, por equipa (min)': 'Average wait for water, per team (min)', 'da lista regada': 'of the list watered', 'de espera média': 'average wait', 'campos regados': 'fields watered',
    'zona por definir': 'zone not set', '% das plantas vivas da comunidade em campos já regados pela app. Em Palma, por zona (bairro onde fica o campo).': '% of the community\'s live plants in fields already watered through the app. In Palma, by zone (neighbourhood where the field is).',
    'Chuva': 'Rain', 'Chuva (pluviómetro)': 'Rain (rain gauge)', 'Chuva (pluviómetro) · teste': 'Rain (rain gauge) · test', 'Registo de teste: não conta no painel.': 'Test record: does not count in the dashboard.', 'Registar': 'Record', 'Dia da chuva': 'Day of the rain',
    'Leia o pluviómetro da comunidade, escreva os milímetros e tire uma fotografia da leitura. Se não choveu, carregue em "Não choveu".': 'Read the community rain gauge, write the millimetres and take a photo of the reading. If it did not rain, tap "No rain".',
    'Hora da leitura': 'Time of reading', 'Fotografia da leitura do pluviómetro': 'Photo of the rain gauge reading', 'Escreva a hora da leitura.': 'Write the time of the reading.', 'Tire a fotografia da leitura do pluviómetro.': 'Take the photo of the rain gauge reading.',
    'Chuva no pluviómetro (mm)': 'Rain in the gauge (mm)', 'Não choveu (0 mm)': 'No rain (0 mm)', 'Escreva os milímetros (0 a 500).': 'Write the millimetres (0 to 500).',
    'Chuva por comunidade': 'Rain per community', 'Chuva total no período (mm)': 'Total rain in the period (mm)',
    'Milímetros medidos nos pluviómetros e registados pelos activistas. Dias sem registo aparecem com —.': 'Millimetres measured in the rain gauges and recorded by the activists. Days without a record show —.',
    'Ainda sem registos de chuva.': 'No rain records yet.', 'no período': 'in the period',
    'A abrir a fotografia…': 'Opening the photo…', 'A fotografia ainda não chegou ao servidor.': 'The photo has not reached the server yet.', 'Sem acesso a esta fotografia ou sem rede.': 'No access to this photo or no network.',
    'Toque para fechar.': 'Tap to close.', 'Monitoria deste campo': 'Monitoring of this field', 'Ver fotografia': 'See photo', 'não regado': 'not watered',
    '📷 = toque para ver a fotografia da leitura do pluviómetro.': '📷 = tap to see the photo of the rain gauge reading.',
    'Distância (à borda)': 'Distance (to boundary)', 'dentro do campo': 'inside the field', 'Limite do campo': 'Field boundary', 'polígono': 'polygon', 'só ponto (sem polígono)': 'point only (no polygon)', '← Ver todos os campos': '← See all fields',
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
  Object.assign(D, {
    'Tudo': 'All time', 'Ontem': 'Yesterday', '7 dias': '7 days', '30 dias': '30 days', 'Período': 'Period', 'De': 'From', 'Até': 'To', 'Aplicar': 'Apply',
    'Todo o histórico': 'All records', 'A data "De" tem de ser anterior ou igual à data "Até".': 'The "From" date must be on or before the "To" date.',
    'Ronda, progresso e rondas concluídas mostram o estado actual; as restantes colunas referem-se ao período escolhido.': 'Round, progress and completed rounds show the current state; the other columns refer to the chosen period.',
    'No período escolhido. Espera = minutos entre a entrada no campo e a chegada da água.': 'In the chosen period. Wait = minutes between field entry and water arrival.',
  });
  const R = [
    [/^Está a (.+) m do campo \(precisão ±(.+) m\)\. Só pode marcar a entrada até (.+) m da borda do campo\.$/, 'You are $1 m from the field (accuracy ±$2 m). You can only record entry within $3 m of the field boundary.'],
    [/^Está a (.+) m do campo\. Marque a saída ainda no campo \(até (.+) m da borda\)\.$/, 'You are $1 m from the field. Record the exit while still at the field (within $2 m of the boundary).'],
    [/^Está a (.+) m do campo\. A verificação faz-se no campo \(até (.+) m da borda\)\.$/, 'You are $1 m from the field. The check is done at the field (within $2 m of the boundary).'],
    [/^Entrada marcada às (\S+) · dentro do campo\.$/, 'Entry recorded at $1 · inside the field.'], [/^Filtro: (.+)\.$/, (m, a) => `Filter: ${tr(a)}.`],
    [/^(\d+) dias com chuva em (\d+) dias registados$/, '$1 rainy days out of $2 days recorded'], [/^(.+) mm$/, '$1 mm'],
    [/^Sem rede: painel guardado no telefone \((.+)\)\. Actualiza quando houver rede\.$/, 'No network: dashboard saved on the phone ($1). It updates when there is network.'], [/^(\d+) \/ (\d+) de (\d+)$/, '$1 / $2 of $3'], [/^registado hoje \((.+) mm\)$/, 'recorded today ($1 mm)'], [/^Medir a área · (.+)$/, 'Measure the area · $1'], [/^Comunidade mudada para (.+)\.$/, 'Community changed to $1.'], [/^Mude só se o campo fica noutra comunidade\.(.*)$/, (m, r) => `Change only if the field is in another community.${r ? ' The zone goes back to not set.' : ''}`], [/^comunidade actual:$/, 'current community:'], [/^Área medida · (.+)$/, 'Measured area · $1'],
    [/^vá a um canto do campo e carregue em «Começar»\. Ande devagar pela borda, à volta do campo todo, até voltar ao ponto vermelho\. O telefone marca pontos sozinho a cada (\d+) m\. Nos cantos pode carregar em «Marcar canto»\. Mantenha a app aberta e o ecrã ligado\.$/, 'go to a corner of the field and tap «Start». Walk slowly along the edge, all the way around the field, until you are back at the red point. The phone marks points by itself every $1 m. At the corners you can tap «Mark corner». Keep the app open and the screen on.'],
    [/^Medição recuperada: (\d+) pontos já marcados\. Continue de onde parou\.$/, 'Measurement recovered: $1 points already marked. Continue from where you stopped.'],
    [/^Precisão fraca \(±(\d+) m\)\. Espere uns segundos\.$/, 'Weak accuracy (±$1 m). Wait a few seconds.'],
    [/^O último ponto está a (\d+) m do início\. Se não deu a volta completa, volte e continue a medir\.$/, 'The last point is $1 m from the start. If you did not go all the way round, go back and keep measuring.'],
    [/^Área gravada: (.+?)( \(no telefone; é enviada quando houver rede\))?\.$/, (m, a, t) => `Area saved: ${a}${t ? ' (on the phone; sent when there is network)' : ''}.`],
    [/^(.+) \((\d+) por ha\)$/, '$1 ($2 per ha)'], [/^(.+) ha \((.+) m²\)$/, '$1 ha ($2 m²)'], [/^(\d+) campos$/, '$1 fields'], [/^(.+) voltou à rega\.( Falta atribuir o activista\.)?$/, (m, a, f) => `${a} is back on the watering list.${f ? ' The activist still has to be assigned.' : ''}`], [/^Saiu da rega: (.+)$/, 'Left the list: $1'], [/^activista: (.+)$/, 'activist: $1'], [/^(\d+) regas antes(.*)$/, (m, n, r) => `${n} waterings before${r.replace('(última', '(last')}`], [/^Chuva guardada: (.+) mm em (.+)\. \(teste\)$/, 'Rain saved: $1 mm in $2. (test)'], [/^Chuva guardada: (.+) mm em (.+)\.$/, 'Rain saved: $1 mm in $2.'], [/^Chuva não gravada: (.+)$/, 'Rain not saved: $1'], [/^Hoje · (.+)$/, 'Today · $1'], [/^Ontem · (.+)$/, 'Yesterday · $1'],
    [/^› (.+)$/, (m, a) => '› ' + tr(a)], [/^Ronda (\d+): (\d+) de (\d+) campos$/, 'Round $1: $2 of $3 fields'], [/^(\d+) de (\d+) campos verificados$/, '$1 of $2 fields checked'],
    [/^Regado em teste \((.+)\)$/, 'Watered in a test ($1)'],
    [/^Da base \((.+)\)\. A app calcula a amostra a partir deste número\.$/, (m, a) => `From the database (${tr(a)}). The app calculates the sample from this number.`],
    [/^(.+) campos verificados$/, '$1 fields checked'], [/^(.+) não regados$/, '$1 not watered'], [/^(.+) deslocações medidas$/, '$1 trips measured'], [/^Rega por campo: (.+)$/, 'Watering per field: $1'],
    [/^(.+) pessoas$/, '$1 people'],
    [/^(.+) de (.+) plantas sem solo húmido$/, '$1 of $2 plants without moist soil'], [/^nota (.+)$/, 'score $1'], [/^Monitoria \(rega de (.+)\):$/, 'Monitoring (watering of $1):'],
    [/^Observação: (.+)$/, 'Note: $1'],
    [/^(.+) faltas?$/, '$1 absent'], [/^·(\d+)F$/, '·$1A'], [/^Sem\. (.+)$/, 'Wk $1'], [/^(.+) pessoas-dia$/, '$1 person-days'],
    [/^Equipa = pessoas presentes \/ pessoas da equipa \(faltas a vermelho\)(; toque para mudar o número de pessoas da equipa)?\. Produtores = produtores com campos regados hoje\. % meta = plantas regadas ÷ \((\d+) × pessoas presentes\)\. Tuk-tuk = hora da 1\.ª chegada da água\. Início = entrada no 1\.º campo; Fim = saída do último\. Desloc\. = tempo médio entre a saída de um campo e a entrada no seguinte\. Alertas = regas fora da lista da equipa\.$/,
      (m, t, n) => `Team = people present / team size (absences in red)${t ? '; tap to change the team size' : ''}. Producers = producers with fields watered today. % target = plants watered ÷ (${n} × people present). Tuk-tuk = time of the first water arrival. Start = entry to the 1st field; End = exit from the last. Travel = average time between leaving one field and entering the next. Alerts = waterings outside the team list.`],
    [/^Na base: (.+)\. Se no campo há outro número, corrija\.$/, (m, a) => `In the database: ${tr(a)}. If the field has a different number, correct it.`],
    [/^Siga o percurso (\S+) e observe as plantas a intervalos regulares \(cerca de 1 em cada (\d+)\)\.$/, 'Follow the $1 route and observe plants at regular intervals (about 1 in every $2).'],
    [/^Siga o percurso (\S+) e observe as plantas a intervalos regulares \(todas as plantas\)\.$/, 'Follow the $1 route and observe plants at regular intervals (all plants).'],
    [/^(\d+) \(todas\)$/, '$1 (all)'], [/^(\d+) de (\d+)$/, '$1 of $2'], [/^Campo regado \(≥ (\d+)%\)$/, 'Field watered (≥ $1%)'], [/^Planta (\d+)$/, 'Plant $1'],
    [/^Observe (\d+) plantas \(faltam (\d+)\)\.$/, 'Observe $1 plants ($2 left).'],
    [/^(.+) de (.+) verificados \(≥ 80% das plantas com solo húmido\)$/, '$1 of $2 checked (≥ 80% of plants with moist soil)'],
    [/^(.+) de (.+) plantas observadas$/, '$1 of $2 plants observed'], [/^vivas \/ secas \/ mortas: (.+)$/, 'alive / dry / dead: $1'],
    [/^Equipas agrupadas por comunidade\. Últimos 14 dias com registos \(de (\d+)\)\.$/, 'Teams grouped by community. Last 14 days with records (of $1).'],
    [/^Monitoria · regas de (.+)$/, 'Monitoring · waterings of $1'], [/^(\d+) de (\d+) campos verificados\.$/, '$1 of $2 fields checked.'],
    [/^de (.+) sorteados$/, 'of $1 drawn'], [/^(.+) de (.+) campos verificados$/, '$1 of $2 fields checked'], [/^rega de (.+)$/, 'watering of $1'],
    [/^Monitoria: (\d+) campos por dia, por pessoa\.$/, 'Monitoring: $1 fields per day, per person.'],
    [/^Está a (.+) m do campo\. A verificação faz-se no campo \(até (.+) m\)\.$/, 'You are $1 m from the field. The check is done at the field (within $2 m).'],
    [/^Verificação não gravada: (.+)$/, 'Check not saved: $1'],
    [/^Todo o histórico: (.+) a (.+)$/, 'All records: $1 to $2'], [/^Dia: (.+)$/, 'Day: $1'],
    [/^Período: (.+) a (.+)$/, (m, x, y) => `Period: ${x === 'início' ? 'start' : x} to ${y === 'hoje' ? 'today' : y}`],
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
