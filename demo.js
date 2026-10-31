/* Rega Coco — modo apresentação (v124, 28/10/2026, Valdo: "posso ter de apresentar o aplicativo a diferentes pessoas…
   seria importante que eu conseguisse mostrar [o que cada utilizador vê]").
   O gestor escolhe em Gestão uma função (activista, técnico, supervisor, oficial de M&E, M&E, director, cliente) e a app passa a
   mostrar os ecrãs dessa função com dados de exemplo. Nada chega ao servidor:
   - todos os pedidos ao Supabase são respondidos aqui, a partir de uma base de exemplo guardada no separador (sessionStorage);
   - o que a app guarda no telefone fica separado (localStorage com o prefixo "demo:", IndexedDB "rega-coco-demo");
   - a sessão verdadeira do gestor não é tocada: ao terminar, a app volta ao gestor.
   Os campos de exemplo ficam à volta do sítio onde o gestor estava ao começar, para a rega poder ser feita ao vivo. */
(function () {
  'use strict';
  let cfg = null;
  try { cfg = JSON.parse(sessionStorage.getItem('rega.demo') || 'null'); } catch {}
  if (!cfg || !cfg.papel) { window.DEMO = null; return; }

  // ---------- 1. o que a app guarda no telefone fica à parte ----------
  const PREF = 'demo:', MANTER = new Set(['rega.lingua']);
  const SP = Storage.prototype, real = { get: SP.getItem, set: SP.setItem, del: SP.removeItem, key: SP.key };
  const ehLocal = (st) => { try { return st === window.localStorage; } catch { return false; } };
  const k = (st, x) => (ehLocal(st) && !MANTER.has(String(x)) ? PREF + x : x);
  SP.getItem = function (x) { return real.get.call(this, k(this, x)); };
  SP.setItem = function (x, v) { return real.set.call(this, k(this, x), v); };
  SP.removeItem = function (x) { return real.del.call(this, k(this, x)); };
  const IDB = 'rega-coco-demo', op = IDBFactory.prototype.open;
  IDBFactory.prototype.open = function (n, v) { return op.call(this, n === 'rega-coco' ? IDB : n, v); };
  try { Object.defineProperty(Navigator.prototype, 'onLine', { get: () => true, configurable: true }); } catch {}
  // GPS simulado (v150, 30/10/2026, Valdo: "no modo de apresentação não importa onde eu vou estar"): a app recebe sempre a
  // posição do centro da base de exemplo (±4 m), venha ou não o GPS do telefone. A entrada no 1.º campo funciona em qualquer sala.
  // v156 (30/10/2026, Valdo, guião da apresentação de 02/11): a posição pode mudar para outro campo («🎬 Pôr-me neste campo») e,
  // ao medir a área, «anda» à volta do campo. Fica no separador (sessionStorage rega.demo.pos).
  let POS = null; try { POS = JSON.parse(sessionStorage.getItem('rega.demo.pos') || 'null'); } catch {}
  const posAct = () => POS || { lat: cfg.lat, lon: cfg.lon };
  const vigCb = new Map(); let nv = 0, andar = null;
  const fixo = () => ({ coords: { latitude: posAct().lat, longitude: posAct().lon, accuracy: 4, altitude: null, altitudeAccuracy: null, heading: null, speed: null }, timestamp: Date.now() });
  const emitir = () => { const f = fixo(); vigCb.forEach((ok) => { try { ok(f); } catch {} }); };
  const porPos = (lat, lon) => { POS = { lat, lon }; try { sessionStorage.setItem('rega.demo.pos', JSON.stringify(POS)); } catch {} emitir(); };
  try {
    const vig = new Map();
    const geo = {
      getCurrentPosition(ok) { setTimeout(() => ok(fixo()), 200); },
      watchPosition(ok) { const id = ++nv; vigCb.set(id, ok); setTimeout(() => ok(fixo()), 200); vig.set(id, setInterval(() => ok(fixo()), 3000)); return id; },
      clearWatch(id) { clearInterval(vig.get(id)); vig.delete(id); vigCb.delete(id); },
    };
    Object.defineProperty(Navigator.prototype, 'geolocation', { get: () => geo, configurable: true });
  } catch {}

  function limparTelefone() {
    try { const ks = []; for (let i = 0; i < localStorage.length; i++) { const x = real.key.call(localStorage, i); if (x && x.startsWith(PREF)) ks.push(x); } ks.forEach((x) => real.del.call(localStorage, x)); } catch {}
    try { indexedDB.deleteDatabase(IDB); } catch {}
  }

  // ---------- 2. base de exemplo ----------
  const ID = (n) => 'd0000000-0000-4000-8000-' + String(n).padStart(12, '0');
  const A1 = ID('a1'.charCodeAt(0) * 100 + 1), A2 = ID(9702), A3 = ID(9703);
  const U = { activista: ID(1), tecnico: ID(2), supervisor: ID(3), me: ID(4), oficial_me: ID(5), director: ID(6), cliente: ID(7), gestor: ID(8) };
  const NOMES = { activista: 'Activista Exemplo', tecnico: 'Técnico Exemplo', supervisor: 'Supervisor Exemplo', me: 'M&E Exemplo', oficial_me: 'Oficial de M&E Exemplo', director: 'Director Exemplo', cliente: 'Cliente Exemplo', gestor: 'Gestor Exemplo' };
  const papel = cfg.papel, EU = U[papel] || U.director;
  const dia = (n) => { const d = new Date(); d.setDate(d.getDate() - n); return d.toLocaleDateString('sv-SE'); };
  const hora = (data, h, m) => { const [y, mo, d] = data.split('-').map(Number); return new Date(y, mo - 1, d, h, m).toISOString(); };
  const uid = () => (crypto.randomUUID ? crypto.randomUUID() : 'x' + Math.random().toString(16).slice(2));

  function construir() {
    const lat0 = cfg.lat, lon0 = cfg.lon, ky = 110540, kx = 111320 * Math.cos(lat0 * Math.PI / 180);
    const p = (dx, dy) => [+(lat0 + dy / ky).toFixed(6), +(lon0 + dx / kx).toFixed(6)];
    // limite do campo: rectângulo de x0..x1, y0..y1 metros a partir do sítio do gestor
    const rect = (x0, y0, x1, y1) => [[x0, y0], [x1, y0], [x1, y1], [x0, y1]].map(([x, y]) => { const [la, lo] = p(x, y); return [lo, la]; });
    const C = (id, prod, com, act, x0, y0, x1, y1, inst, vivas, poli = true, extra = {}) => {
      const [la, lo] = p((x0 + x1) / 2, (y0 + y1) / 2);
      return { id, pr: id.split('-')[0], area_n: +id.split('-')[1], comunidade: com, zona: null, produtor: prod, instaladas: inst, vivas, latitude: la, longitude: lo,
        activista_id: act, activista_proposto: null, data_plantio: '2026-05-12', poligono: poli ? rect(x0, y0, x1, y1) : null, reactivada_em: null,
        area_m2: Math.round((x1 - x0) * (y1 - y0)), limites_abertos: false, poligono_proposto: null, area_m2_proposta: null, proposta_em: null,
        n_regas_origem: null, ultima_rega_origem: null, datas_rega_origem: null, plantas_regadas_origem: null, regas_origem_por_pr: false, activa: true, ...extra };
    };
    const N = 'Exemplo Norte', S = 'Exemplo Sul';
    const areas = [
      C('PR900101-1', 'Ana Exemplo', N, A1, -40, -40, 40, 40, 180, 165),          // o gestor está dentro deste campo
      C('PR900102-1', 'Bento Exemplo', N, A1, -30, 45, 40, 105, 120, 110),       // ao lado: dá para fazer a monitoria ao vivo
      C('PR900103-1', 'Carla Exemplo', N, A1, -280, 60, -200, 130, 150, 140),
      C('PR900104-1', 'Daniel Exemplo', N, A1, 60, -300, 120, -240, 90, 85),
      C('PR900104-2', 'Daniel Exemplo', N, A1, 140, -340, 185, -295, 70, 60),
      C('PR900105-1', 'Olga Exemplo', N, A1, 230, 80, 290, 140, 100, 95, false),   // v156: sem limite, a ~280 m: recusa pela distância e medir a área ao vivo
      C('PR900201-1', 'Elisa Exemplo', N, A2, 620, 490, 690, 560, 200, 180),
      C('PR900202-1', 'Fernando Exemplo', N, A2, 790, 400, 850, 460, 130, 125),
      C('PR900203-1', 'Graça Exemplo', N, A2, 680, 740, 735, 795, 110, 90, false,     // sem limite; v151: área medida pelo activista, por aprovar
        { poligono_proposto: rect(676, 736, 739, 801), area_m2_proposta: 63 * 65, proposta_em: hora(dia(1), 11, 20) }),
      C('PR900204-1', 'Hélio Exemplo', N, A2, 950, 620, 1015, 685, 160, 150),
      C('PR900301-1', 'Inês Exemplo', S, A3, -340, -1140, -265, -1065, 220, 200),
      C('PR900302-1', 'João Exemplo', S, A3, -550, -1280, -490, -1220, 140, 120),
      C('PR900303-1', 'Laura Exemplo', S, A3, -175, -1425, -125, -1375, 100, 95),
      C('PR900304-1', 'Manuel Exemplo', S, A3, -730, -1030, -675, -975, 120, 80),
      C('PR900401-1', 'Nádia Exemplo', N, null, 350, 250, 400, 300, 80, 80, true, { activista_proposto: 'Activista Exemplo' }),
    ];
    const activistas = [
      { id: A1, nome: 'Activista Exemplo', comunidade_principal: N, tecnico: 'Técnico Exemplo', supervisor: 'Supervisor Exemplo', activo: true, equipa_tamanho: 6, sem_telefone: false },
      { id: A2, nome: 'Activista Dois', comunidade_principal: N, tecnico: 'Técnico Exemplo', supervisor: 'Supervisor Exemplo', activo: true, equipa_tamanho: 5, sem_telefone: false },
      { id: A3, nome: 'Activista Três', comunidade_principal: S, tecnico: 'Técnica Sul', supervisor: 'Supervisor Exemplo', activo: true, equipa_tamanho: 7, sem_telefone: false },
    ];
    const userAct = { [A1]: U.activista, [A2]: ID(9802), [A3]: ID(9803) };
    const registos = [], constr = [], jornadas = [];
    // regas de exemplo: [dias atrás, activista, campo, hora de entrada, minutos à espera da água, minutos a regar, plantas, pessoas, ronda, constrangimento]
    const R = [
      [3, A1, 'PR900103-1', 7, 25, 55, 140, 6, 1], [3, A1, 'PR900104-1', 9, 5, 40, 80, 6, 1],
      [1, A1, 'PR900102-1', 7, 15, 45, 110, 5, 1], [1, A1, 'PR900104-2', 8, 10, 30, 60, 5, 1],
      [2, A2, 'PR900201-1', 7, 40, 60, 180, 5, 1], [2, A2, 'PR900202-1', 9, 10, 50, 110, 5, 1, ['agua_acabou', 'A água do tuk-tuk acabou antes das últimas plantas.']],
      [1, A2, 'PR900203-1', 7, 20, 45, 90, 4, 1], [1, A2, 'PR900204-1', 9, 5, 12, 300, 4, 1],   // v156: 300 plantas num campo de 150: rega com ⚠️ para o técnico
      [3, A3, 'PR900301-1', 6, 10, 60, 200, 7, 1], [3, A3, 'PR900302-1', 8, 5, 45, 120, 7, 1],
      [1, A3, 'PR900303-1', 6, 15, 35, 95, 6, 1], [1, A3, 'PR900304-1', 7, 10, 30, 60, 6, 1, ['mudas_secas', 'Parte das plantas morreu na queimada.']],
    ];
    const cont = {};
    for (const [d, act, area, h0, esp, rega, plantas, pessoas, ronda, c] of R) {
      const data = dia(d), k2 = act + data; cont[k2] = (cont[k2] || 0); const m0 = cont[k2]; cont[k2] += 1;
      const e = new Date(hora(data, h0, 15 + m0 * 7)), ag = new Date(+e + esp * 6e4), s = new Date(+ag + rega * 6e4), id = uid(), a = areas.find((x) => x.id === area);
      registos.push({ id, area_id: area, activista_id: act, user_id: userAct[act], data, ronda, entrada_em: e.toISOString(), agua_em: ag.toISOString(), saida_em: s.toISOString(),
        plantas_regadas: plantas, pessoas, teste: false, gps_valido: true, alerta: null, motivo_alerta: null, entrada_lat: a.latitude, entrada_lon: a.longitude, saida_lat: a.latitude, saida_lon: a.longitude,
        foto_entrada: `demo/${id}-entrada.jpg`, foto_rega: `demo/${id}-rega.jpg`, foto_saida: `demo/${id}-saida.jpg`, foto_entrada_em: e.toISOString(), foto_rega_em: new Date(+ag + 6e5).toISOString(), foto_saida_em: s.toISOString(),
        observacao: null, plantas_originais: null, plantas_corrigidas_em: null });
      if (c) constr.push({ id: uid(), registo_id: id, tipo: c[0], descricao: c[1] });
      if (!jornadas.some((j) => j.activista_id === act && j.data === data)) jornadas.push({ id: uid(), activista_id: act, data, pessoas, inicio_em: e.toISOString() });
    }
    // uma rega de teste antiga do técnico e do supervisor (o Hoje deles não mostra o aviso "ainda não fez nenhuma rega de teste")
    for (const [quem, area] of [[U.tecnico, 'PR900102-1'], [U.supervisor, 'PR900301-1']]) { const data = dia(20), e = hora(data, 9, 0);
      registos.push({ id: uid(), area_id: area, activista_id: null, user_id: quem, data, ronda: null, entrada_em: e, agua_em: e, saida_em: hora(data, 9, 30), plantas_regadas: 20, pessoas: 1, teste: true, gps_valido: true }); }
    const OF = U.oficial_me;
    const queimadas = [{ id: uid(), area_id: 'PR900304-1', data: dia(2), observacao: 'Fogo vindo da machamba ao lado.', foto_path: 'demo/queimada.jpg', registada_por: U.tecnico, registada_em: hora(dia(2), 15, 0),
      plantas_afectadas: 40, plantas_mortas: 20, recontagem_em: null, vivas_recontadas: null, recontagem_obs: null }];
    const recontagens = [
      { id: uid(), area_id: 'PR900304-1', queimada_id: queimadas[0].id, motivo: `Queimada de ${dia(2).split('-').reverse().join('/')}`, estado: 'encaminhada', pedido_em: hora(dia(2), 15, 5), pedido_por: U.tecnico,
        oficial_id: OF, encaminhada_em: hora(dia(1), 9, 0), vivas: null, mortas: null },
      { id: uid(), area_id: 'PR900103-1', motivo: 'Muitas plantas secas na monitoria', estado: 'enviada', pedido_em: hora(dia(4), 10, 0), pedido_por: U.me, oficial_id: OF, encaminhada_em: hora(dia(3), 8, 0),
        vivas: 132, mortas: 8, navuna: true, contada_em: hora(dia(1), 10, 30), enviada_em: hora(dia(1), 12, 0), foto_path: 'demo/declaracao.jpg', foto_campo_path: 'demo/campo.jpg',
        lat: areas.find((x) => x.id === 'PR900103-1').latitude, lon: areas.find((x) => x.id === 'PR900103-1').longitude, precisao_m: 6 },
      { id: uid(), area_id: 'PR900201-1', motivo: 'O produtor diz que há mais plantas mortas', estado: 'por_encaminhar', pedido_em: hora(dia(1), 16, 0), pedido_por: U.tecnico, oficial_id: null },
      { id: uid(), area_id: 'PR900301-1', motivo: 'Confirmar as plantas vivas', estado: 'validada', pedido_em: hora(dia(8), 9, 0), pedido_por: U.me, oficial_id: OF, encaminhada_em: hora(dia(8), 10, 0),
        vivas: 200, mortas: 10, vivas_antes: 210, navuna: true, contada_em: hora(dia(7), 9, 0), enviada_em: hora(dia(7), 11, 0), validada_em: hora(dia(6), 8, 0),
        foto_path: 'demo/declaracao2.jpg', foto_campo_path: 'demo/campo2.jpg', lat: areas.find((x) => x.id === 'PR900301-1').latitude, lon: areas.find((x) => x.id === 'PR900301-1').longitude, precisao_m: 4 },
    ];
    const amostras = [
      { id: uid(), data_rega: dia(1), verificador_id: U.tecnico, papel: 'tecnico', area_id: 'PR900102-1', activista_id: A1, criado_em: hora(dia(1), 18, 0) },
      { id: uid(), data_rega: dia(1), verificador_id: U.supervisor, papel: 'supervisor', area_id: 'PR900203-1', activista_id: A2, criado_em: hora(dia(1), 18, 0) },
      { id: uid(), data_rega: dia(2), verificador_id: U.tecnico, papel: 'tecnico', area_id: 'PR900202-1', activista_id: A2, criado_em: hora(dia(2), 18, 0) },
      { id: uid(), data_rega: dia(3), verificador_id: U.supervisor, papel: 'supervisor', area_id: 'PR900302-1', activista_id: A3, criado_em: hora(dia(3), 18, 0) },
    ];
    const monitorias = [
      { amostra_id: amostras[2].id, area_id: 'PR900202-1', verificador_id: U.tecnico, feito_em: hora(dia(1), 9, 30), nota: 9, solo_regado: true, pct_humido: 90, plantas_obs: 20, humidas: 18, n_vivas: 19, n_secas: 1, n_mortas: 0 },
      { amostra_id: amostras[3].id, area_id: 'PR900302-1', verificador_id: U.supervisor, feito_em: hora(dia(2), 10, 0), nota: 6, solo_regado: false, pct_humido: 60, plantas_obs: 20, humidas: 12, n_vivas: 17, n_secas: 2, n_mortas: 1 },
    ];
    const chuva = [
      { data: dia(3), comunidade: N, zona: null, mm: 12.5, activista: 'Activista Exemplo', lida_em: hora(dia(3), 7, 0), foto: 'demo/chuva1.jpg' },
      { data: dia(1), comunidade: S, zona: null, mm: 4, activista: 'Activista Três', lida_em: hora(dia(1), 6, 50), foto: 'demo/chuva2.jpg' },
    ];
    const dsr = [{ id: uid(), activista_id: A2, data: dia(4), motivo: 'avaria_tuk_tuk', todo_dia: true, descricao: 'O tuk-tuk avariou de manhã.', quem: 'Técnico Exemplo', user_id: U.tecnico, criado_em: hora(dia(4), 9, 0), foto_path: null, area_id: null, entrada_em: null }];
    // v156: sugestões de exemplo (a Gestão do gestor aprova ou recusa; quem enviou vê a resposta no Hoje)
    const sugestoes = [
      { id: uid(), texto: 'No mapa, mostrar com outra cor os campos onde houve queimada.', criada_em: hora(dia(2), 16, 40), estado: 'nova', papel: 'activista', quem: NOMES.activista, perfil_id: U.activista, ecra: 'mapa', versao: '155', area_id: null, foto_path: null, fotos_extra: [], nota: null },
      { id: uid(), texto: 'Poder registar a chuva do dia anterior quando não houve rede.', criada_em: hora(dia(1), 18, 5), estado: 'nova', papel: 'tecnico', quem: NOMES.tecnico, perfil_id: U.tecnico, ecra: 'hoje', versao: '155', area_id: null, foto_path: null, fotos_extra: [], nota: null },
    ];
    // v156: manutenção (cava-roda e mulching) nos campos de Exemplo Sul
    const manut = [
      { id: uid(), area_id: 'PR900301-1', data: dia(3), cavaroda: 120, mulching: 80, pessoas: 6, obs: null, foto_path: 'demo/manut1.jpg', feito_por: U.supervisor, feito_em: hora(dia(3), 15, 0) },
      { id: uid(), area_id: 'PR900301-1', data: dia(1), cavaroda: 200, mulching: 200, pessoas: 6, obs: 'Campo terminado.', foto_path: 'demo/manut2.jpg', feito_por: U.supervisor, feito_em: hora(dia(1), 14, 30) },
      { id: uid(), area_id: 'PR900302-1', data: dia(1), cavaroda: 90, mulching: 40, pessoas: 5, obs: null, foto_path: 'demo/manut3.jpg', feito_por: U.tecnico, feito_em: hora(dia(1), 16, 0) },
      { id: uid(), area_id: 'PR900304-1', data: dia(2), cavaroda: 80, mulching: 80, pessoas: 4, obs: null, foto_path: 'demo/manut4.jpg', feito_por: U.supervisor, feito_em: hora(dia(2), 13, 0) },
    ];
    const manutFeitos = [{ area_id: 'PR900301-1', feito: true, marcado_em: hora(dia(1), 15, 0), marcado_por: U.supervisor }];
    return { v: 2, areas, activistas, registos, constr, jornadas, queimadas, recontagens, amostras, monitorias, chuva, dsr, userAct, sugestoes, manut, manutFeitos, fechos: {}, escala: [1] };   // v156: o técnico e o supervisor já escolheram a segunda para a monitoria (sem o ecrã obrigatório)
  }
  let DB = null;
  try { DB = JSON.parse(sessionStorage.getItem('rega.demo.db') || 'null'); } catch {}
  if (!DB || DB.v !== 2) { DB = construir(); guardarDB(); try { sessionStorage.removeItem('rega.demo.pos'); } catch {} POS = null; }
  function guardarDB() { try { sessionStorage.setItem('rega.demo.db', JSON.stringify(DB)); } catch {} }

  // ---------- 3. sessão de exemplo (não mexe na sessão verdadeira) ----------
  const REF = 'fgzdqnvobgfzjetbbxcm', EMAIL = `exemplo.${papel}@rega-coco.example.com`;
  const b64u = (o) => btoa(JSON.stringify(o)).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');
  const exp = Math.floor(Date.now() / 1000) + 10 * 365 * 864e2;
  const USER = { id: EU, aud: 'authenticated', role: 'authenticated', email: EMAIL, app_metadata: {}, user_metadata: {}, created_at: new Date().toISOString() };
  const SESSAO = { access_token: b64u({ alg: 'HS256', typ: 'JWT' }) + '.' + b64u({ sub: EU, role: 'authenticated', exp, email: EMAIL }) + '.demo', token_type: 'bearer', expires_in: exp - Math.floor(Date.now() / 1000), expires_at: exp, refresh_token: 'demo', user: USER };
  try { localStorage.setItem(`sb-${REF}-auth-token`, JSON.stringify(SESSAO)); } catch {}

  // ---------- 4. o que cada função vê ----------
  // pessoas de cada equipa de exemplo (v135): tamanho − 1 nomes inventados, criados na primeira vez
  function membros() {
    if (!DB.membros) { DB.membros = []; DB.activistas.forEach((t, k) => { for (let i = 1; i < (t.equipa_tamanho || 1); i++) DB.membros.push({ id: ID(9900 + k * 20 + i), activista_id: t.id, equipa_rh: t.id, nome: `Sazonal ${['A', 'B', 'C'][k] || k}${i} Exemplo`, contrato: 'Certo', inicio: dia(30), fim: null, activo: true }); }); guardarDB(); }
    return DB.membros;
  }
  const act = () => (papel === 'activista' ? A1 : null);
  const vis = () => (papel === 'tecnico' ? [A1, A2] : papel === 'supervisor' ? [A1, A2, A3] : null);
  const areasDoOficial = () => new Set(DB.recontagens.filter((r) => r.oficial_id === U.oficial_me && ['encaminhada', 'recusada', 'enviada', 'validada'].includes(r.estado)).map((r) => r.area_id));
  function areasVisiveis() {
    if (papel === 'activista') return DB.areas.filter((a) => a.activista_id === A1);
    if (papel === 'oficial_me') { const s = areasDoOficial(); return DB.areas.filter((a) => s.has(a.id)); }
    return DB.areas;
  }
  const nomeAct = (id) => (DB.activistas.find((t) => t.id === id) || {}).nome || null;
  const nomeU = (id) => { const p = Object.entries(U).find(([, v]) => v === id); return p ? NOMES[p[0]] : nomeAct(Object.keys(DB.userAct).find((k2) => DB.userAct[k2] === id)) || null; };
  const area = (id) => DB.areas.find((a) => a.id === id) || {};
  const reais = () => DB.registos.filter((r) => !r.teste && r.plantas_regadas > 0);
  const naData = (d, de, ate) => (!de || d >= de) && (!ate || d <= ate);

  function rondas() {          // ronda de cada equipa: uma ronda acaba quando todos os campos da lista foram regados nessa ronda
    const out = {};
    for (const t of DB.activistas) {
      const lista = DB.areas.filter((a) => a.activista_id === t.id).map((a) => a.id), regs = reais().filter((r) => r.activista_id === t.id);
      let n = 1; const feitas = [];
      while (lista.length && lista.every((id) => regs.some((r) => r.area_id === id && r.ronda === n && r.campo_fechado !== false))) {
        const rr = regs.filter((r) => r.ronda === n).map((r) => r.data).sort(); feitas.push({ ronda: n, inicio: rr[0], fim: rr[rr.length - 1], dias: Math.round((new Date(rr[rr.length - 1]) - new Date(rr[0])) / 864e5) + 1 }); n++;
      }
      const daRonda = regs.filter((r) => r.ronda === n);
      out[t.id] = { lista: lista.length, ronda: n, regadas: new Set(daRonda.filter((r) => r.campo_fechado !== false).map((r) => r.area_id)).size, inicio: daRonda.map((r) => r.data).sort()[0] || null, feitas };
    }
    return out;
  }
  function estadoRonda() {
    const ro = rondas();
    return areasVisiveis().map((a) => {
      const regs = reais().filter((r) => r.area_id === a.id), n = ro[a.activista_id]?.ronda || 1;
      return { area_id: a.id, ultima_rega: regs.map((r) => r.data).sort().pop() || null, regas_app: regs.length, plantas_app: regs.reduce((s, r) => s + r.plantas_regadas, 0), ronda_actual: n, regada_na_ronda: regs.some((r) => r.ronda === n && r.campo_fechado !== false),
        // v154: rega a meio (campo_fechado = false) deixa o campo por terminar
        por_terminar: !regs.some((r) => r.ronda === n && r.campo_fechado !== false) && regs.some((r) => r.ronda === n && r.campo_fechado === false),
        plantas_ronda: regs.filter((r) => r.ronda === n).reduce((s, r) => s + r.plantas_regadas, 0), data_parcial: regs.filter((r) => r.ronda === n && r.campo_fechado === false).map((r) => r.data).sort().pop() || null };
    });
  }
  function recontagensLista() {
    const vistas = new Set(areasVisiveis().map((a) => a.id));
    return DB.recontagens.filter((r) => r.estado !== 'cancelada' && (['me', 'gestor', 'director'].includes(papel) || (papel === 'oficial_me' ? r.oficial_id === U.oficial_me : vistas.has(r.area_id))))
      .sort((x, y) => (y.pedido_em || '').localeCompare(x.pedido_em || '')).map((r) => {
        const a = area(r.area_id), q = DB.queimadas.find((x) => x.id === r.queimada_id), ve = papel === 'me' || r.oficial_id === EU || r.estado === 'validada', perto = papel === 'me' || r.oficial_id === EU;
        return { id: r.id, area_id: r.area_id, pr: a.pr, produtor: a.produtor, comunidade: a.comunidade, instaladas: a.instaladas, vivas_campo: a.vivas, queimada_id: r.queimada_id || null, queimada_data: q?.data || null,
          plantas_afectadas: q?.plantas_afectadas ?? null, queimada_mortas: q?.plantas_mortas ?? null, motivo: r.motivo, estado: r.estado, pedido_em: r.pedido_em, pedido_por_nome: nomeU(r.pedido_por),
          encaminhada_em: r.encaminhada_em || null, enviada_em: r.enviada_em || null, validada_em: r.validada_em || null, oficial_id: r.oficial_id || null, oficial: r.oficial_id ? NOMES.oficial_me : null,
          recusa_motivo: r.recusa_motivo || null, recusada_em: r.recusada_em || null, telefone: perto ? '840000000' : null, telefone2: null, telefone_confirmar: perto ? false : null, vivas_antes: r.vivas_antes ?? null, navuna: r.navuna ?? null, oficial_entrou: ['me', 'gestor', 'director'].includes(papel) && r.oficial_id ? true : null,
          vivas: ve ? r.vivas ?? null : null, mortas: ve ? r.mortas ?? null : null, foto_path: ve ? r.foto_path || null : null, foto_campo_path: ve ? r.foto_campo_path || null : null,
          lat: perto ? r.lat ?? null : null, lon: perto ? r.lon ?? null : null, precisao_m: perto ? r.precisao_m ?? null : null, contada_em: ve ? r.contada_em || null : null };
      });
  }
  const hm = (iso) => new Date(iso).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' });
  const mins = (a, b) => (new Date(b) - new Date(a)) / 6e4;
  const media = (l) => (l.length ? Math.round(l.reduce((s, x) => s + x, 0) / l.length) : null);
  function resumo(de, ate) {
    const reg = reais().filter((r) => naData(r.data, de, ate)), ro = rondas();
    const porArea = {}; reg.forEach((r) => { porArea[r.area_id] = (porArea[r.area_id] || 0) + 1; });
    const eqDia = {}; reg.forEach((r) => { const k2 = r.activista_id + '|' + r.data; eqDia[k2] = Math.max(eqDia[k2] || 0, r.pessoas || 1); });
    const intervalos = []; for (const a of DB.areas) { const ds = reais().filter((r) => r.area_id === a.id).map((r) => r.data).sort(); for (let i = 1; i < ds.length; i++) if (naData(ds[i], de, ate)) intervalos.push((new Date(ds[i]) - new Date(ds[i - 1])) / 864e5); }
    const comAgua = reg.filter((r) => r.agua_em && r.agua_em >= r.entrada_em);
    const primeiras = {}; reg.forEach((r) => { const k2 = r.activista_id + '|' + r.data; if (!primeiras[k2] || r.entrada_em < primeiras[k2].entrada_em) primeiras[k2] = r; });
    const atraso = (iso) => { const d = new Date(iso); return Math.max(0, d.getHours() * 60 + d.getMinutes() - 360); };
    const chegadas = Object.values(primeiras);
    const coms = [...new Set(DB.areas.map((a) => a.comunidade))];
    return {
      gerado_em: new Date().toISOString(), periodo: { de, ate },
      universo: { areas: DB.areas.length, vivas: DB.areas.reduce((s, a) => s + (a.vivas || 0), 0), com_activista: DB.areas.filter((a) => a.activista_id).length },
      inicio: reg.map((r) => r.data).sort()[0] || null, fim: reg.map((r) => r.data).sort().pop() || null,
      areas_regadas: Object.keys(porArea).length, vivas_regadas: Object.keys(porArea).reduce((s, id) => s + (area(id).vivas || 0), 0),
      plantas_regadas_total: reg.reduce((s, r) => s + r.plantas_regadas, 0), pessoas_dia_total: Object.values(eqDia).reduce((s, x) => s + x, 0), registos: reg.length,
      dias_medios_entre_regas: intervalos.length ? +(intervalos.reduce((s, x) => s + x, 0) / intervalos.length).toFixed(1) : null, alertas: 0, gps_invalido: 0,
      espera_agua_min: media(comAgua.map((r) => mins(r.entrada_em, r.agua_em))),
      chegada_equipa: chegadas.length ? { hora_combinada: '06:00', dias: chegadas.length, hora_media: (() => { const m = media(chegadas.map((r) => { const d = new Date(r.entrada_em); return d.getHours() * 60 + d.getMinutes(); })); return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); })(),
        atraso_min: media(chegadas.map((r) => atraso(r.entrada_em))), depois_hora: chegadas.filter((r) => atraso(r.entrada_em) > 0).length } : null,
      por_dia: [...new Set(reg.map((r) => r.data))].sort().map((d) => { const l = reg.filter((r) => r.data === d); return { data: d, plantas: l.reduce((s, r) => s + r.plantas_regadas, 0), campos: l.length, pessoas: Object.entries(eqDia).filter(([k2]) => k2.endsWith('|' + d)).reduce((s, [, v]) => s + v, 0), equipas: new Set(l.map((r) => r.activista_id)).size }; }),
      por_comunidade: coms.sort().map((c) => { const as = DB.areas.filter((a) => a.comunidade === c), rg = as.filter((a) => porArea[a.id]);
        return { comunidade: c, areas: as.length, vivas: as.reduce((s, a) => s + (a.vivas || 0), 0), areas_regadas: rg.length, vivas_regadas: rg.reduce((s, a) => s + (a.vivas || 0), 0), regas: rg.reduce((s, a) => s + porArea[a.id], 0), dias_medios_entre_regas: null }; }),
      por_equipa: DB.activistas.map((t) => { const l = reg.filter((r) => r.activista_id === t.id), o = ro[t.id], ed = Object.entries(eqDia).filter(([k2]) => k2.startsWith(t.id + '|'));
        return { nome: t.nome, comunidade: t.comunidade_principal, lista: o.lista, ronda: o.ronda, regadas_ronda: o.regadas, inicio_ronda: o.inicio, rondas_concluidas: o.feitas.length ? o.feitas : null,
          dias_trabalhados: ed.length, plantas: l.reduce((s, r) => s + r.plantas_regadas, 0), pessoas_dia: ed.reduce((s, [, v]) => s + v, 0),
          espera_agua_min: media(l.filter((r) => r.agua_em >= r.entrada_em).map((r) => mins(r.entrada_em, r.agua_em))), min_por_campo: media(l.map((r) => mins(r.entrada_em, r.saida_em))) }; }).sort((x, y) => x.nome.localeCompare(y.nome)),
      chegadas_agua: Object.keys(primeiras).map((k2) => { const [aid, d] = k2.split('|'), l = reg.filter((r) => r.activista_id === aid && r.data === d).sort((x, y) => x.entrada_em.localeCompare(y.entrada_em)), t = DB.activistas.find((x) => x.id === aid);
        return { data: d, equipa: t.nome, comunidade: t.comunidade_principal, inicio_trabalho: hm(l[0].entrada_em), primeira_agua: hm(l[0].agua_em), chegadas: l.length, horas: l.map((r) => hm(r.agua_em)).join(' · '), campos: l.length,
          atraso_min: atraso(l[0].entrada_em), espera_media_min: media(l.map((r) => mins(r.entrada_em, r.agua_em))) }; }).sort((x, y) => y.data.localeCompare(x.data) || x.equipa.localeCompare(y.equipa)),
      constrangimentos: DB.constr.filter((c) => { const r = DB.registos.find((x) => x.id === c.registo_id); return r && !r.teste && naData(r.data, de, ate); }).reduce((o, c) => { o[c.tipo] = (o[c.tipo] || 0) + 1; return o; }, {}),
    };
  }
  function monitoria(de, ate) {
    if (papel === 'cliente') return null;
    const am = DB.amostras.filter((m) => naData(m.data_rega, de, ate)), mo = (m) => DB.monitorias.find((x) => x.amostra_id === m.id), feitas = am.filter(mo).map(mo);
    const soma = (l, k2) => l.reduce((s, x) => s + (x[k2] || 0), 0), nm = (l) => (l.length ? +(soma(l, 'nota') / l.length).toFixed(1) : null);
    const porTec = {}; for (const m of am) { const t = DB.activistas.find((x) => x.id === m.activista_id)?.tecnico || '—'; (porTec[t] ||= []).push(m); }
    return { amostrados: am.length, verificados: feitas.length, nota_media: nm(feitas), solo_regado: feitas.filter((x) => x.solo_regado).length, plantas_obs: soma(feitas, 'plantas_obs'), plantas_humidas: soma(feitas, 'humidas'),
      mudas: { vivas: soma(feitas, 'n_vivas'), secas: soma(feitas, 'n_secas'), mortas: soma(feitas, 'n_mortas') }, lqas_n: 19, lqas_limiar: 13,
      por_tecnico: Object.entries(porTec).map(([t, l]) => { const f = l.filter(mo).map(mo); return { tecnico: t, verificados: f.length, solo_regado: f.filter((x) => x.solo_regado).length, nota_media: nm(f), lqas_regados: null }; }),
      por_equipa: DB.activistas.map((t) => { const f = am.filter((m) => m.activista_id === t.id && mo(m)).map(mo); return { nome: t.nome, comunidade: t.comunidade_principal, verificados: f.length, nota_media: nm(f), sem_sinais_rega: f.filter((x) => !x.solo_regado).length, plantas_obs: soma(f, 'plantas_obs'), plantas_humidas: soma(f, 'humidas'), mudas_secas_mortas: soma(f, 'n_secas') + soma(f, 'n_mortas') }; }),
      por_verificador: ['tecnico', 'supervisor'].map((p2) => { const l = am.filter((m) => m.verificador_id === U[p2]), f = l.filter(mo).map(mo); return { nome: NOMES[p2], papel: p2, amostrados: l.length, verificados: f.length, nota_media: nm(f) }; }) };
  }
  function percursoDe(data, aid) {
    const l = reais().filter((r) => r.activista_id === aid && r.data === data).sort((x, y) => x.entrada_em.localeCompare(y.entrada_em));
    if (!l.length) return { pontos: [], regas: [] };
    const pts = [], add = (la, lo, t) => pts.push([+lo.toFixed(6), +la.toFixed(6), Math.floor(new Date(t) / 1000), 6]);
    let prev = null;
    for (const r of l) {
      const a = area(r.area_id);
      if (prev) { const b = area(prev.area_id); for (let i = 1; i < 6; i++) { const f = i / 6; add(b.latitude + (a.latitude - b.latitude) * f, b.longitude + (a.longitude - b.longitude) * f, +new Date(prev.saida_em) + (new Date(r.entrada_em) - new Date(prev.saida_em)) * f); } }
      else add(a.latitude - 0.002, a.longitude - 0.001, +new Date(r.entrada_em) - 15 * 6e4);
      for (let i = 0; i < 4; i++) add(a.latitude + (i % 2 ? 0.0002 : -0.0002), a.longitude + (i < 2 ? 0.0002 : -0.0002), +new Date(r.entrada_em) + (new Date(r.saida_em) - new Date(r.entrada_em)) * i / 3);
      prev = r;
    }
    return { pontos: pts, regas: l.map((r) => ({ area_id: r.area_id, plantas: r.plantas_regadas, entrada_em: r.entrada_em, saida_em: r.saida_em })) };
  }

  // ---------- v156: ajudas para a área medida, sugestões e manutenção ----------
  function areaM2(pts) {                       // pts = [[lon, lat], ...]; área em m² (projecção local)
    if (!pts || pts.length < 3) return 0; const la0 = pts[0][1] * Math.PI / 180, kx = 111320 * Math.cos(la0), ky = 110540;
    let s2 = 0; for (let i = 0; i < pts.length; i++) { const [x1, y1] = pts[i], [x2, y2] = pts[(i + 1) % pts.length]; s2 += (x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky); }
    return Math.round(Math.abs(s2) / 2);
  }
  const centro = (pts) => [pts.reduce((x, p) => x + p[0], 0) / pts.length, pts.reduce((x, p) => x + p[1], 0) / pts.length];
  function novaSugestao(a) {
    (DB.sugestoes ||= []).push({ id: a.p_id || uid(), texto: a.p_texto, criada_em: new Date().toISOString(), estado: 'nova', papel, quem: NOMES[papel], perfil_id: EU, ecra: a.p_ecra || null, versao: a.p_versao || null,
      area_id: a.p_area || null, foto_path: a.p_foto || null, fotos_extra: a.p_fotos_extra || [], nota: null, diag: a.p_diag || null });
    return a.p_id || null;
  }
  const MANUT_COM = ['Exemplo Sul'];
  function manutCampos() {
    const acesso = ['gestor', 'supervisor'].includes(papel) ? 'escreve' : papel === 'tecnico' ? 'regista' : ['director', 'me'].includes(papel) ? 'le' : null;
    if (!acesso) return null;
    const campos = DB.areas.filter((a) => MANUT_COM.includes(a.comunidade)).map((a) => {
      const l = (DB.manut || []).filter((x) => x.area_id === a.id && !x.removido).sort((x, y) => y.feito_em.localeCompare(x.feito_em)), u = l[0], f = (DB.manutFeitos || []).find((x) => x.area_id === a.id);
      return { id: a.id, pr: a.pr, produtor: a.produtor, comunidade: a.comunidade, zona: a.zona, latitude: a.latitude, longitude: a.longitude, poligono: a.poligono, vivas: a.vivas, instaladas: a.instaladas, activa: true,
        plantas: (a.vivas > 0 ? a.vivas : a.instaladas) || 0, activista: nomeAct(a.activista_id), cavaroda: u ? u.cavaroda : null, mulching: u ? u.mulching : null, ultima: u ? u.data : null, ultima_em: u ? u.feito_em : null, n: l.length,
        feito: !!f, feito_em: f ? f.marcado_em : null, feito_por: f ? nomeU(f.marcado_por) : null };
    });
    return { acesso, inicio: '2026-11-02', teste: false, comunidades: MANUT_COM, campos };
  }

  // ---------- 5. respostas aos pedidos da app ----------
  const RPC = {
    estado_ronda: () => estadoRonda(), estado_ronda2: () => estadoRonda(), estado_ronda3: () => estadoRonda(), regas_outra_equipa: () => [],
    lista_comunidades: () => [...new Set(DB.areas.map((a) => a.comunidade))].sort(),
    pontos_comunidades: () => (papel === 'oficial_me' ? [] : DB.areas.map((a) => ({ comunidade: a.comunidade, zona: a.zona, lat: a.latitude, lon: a.longitude }))),
    recontagens_lista: () => recontagensLista(),
    oficiais_me: () => [{ id: U.oficial_me, nome: NOMES.oficial_me, entrou: true }],
    meus_activistas: () => vis() || [], minhas_comunidades: () => (papel === 'tecnico' ? ['Exemplo Norte'] : papel === 'supervisor' ? ['Exemplo Norte', 'Exemplo Sul'] : []),
    monitoria_escala_ver: () => (['tecnico', 'supervisor'].includes(papel) ? { n_dias: 1, campos: 2, pausa: false, eu_monitor: true, meus: DB.escala || null, pessoas: [{ id: EU, nome: 'Eu', papel, dias: DB.escala || null, eu: true }, { id: 'x1', nome: 'Técnica Sul', papel: 'tecnico', dias: [1], eu: false }] } : null),
    apoios_lista: () => [], apoio_sugestoes: () => [], apoio_candidatos: () => [], criar_apoio: () => null, terminar_apoio: () => null,
    acompanhamentos_campo: () => [], gravar_acompanhamento: (a) => ({ id: a.p_id }), remover_acompanhamento: () => null,
    gravar_monitoria_escala: (a) => { DB.escala = (a.p_dias || []).slice().sort(); guardarDB(); return { dias: DB.escala }; },
    monitoria_lista: () => { const l = DB.amostras.filter((m) => m.verificador_id === EU), u = l.map((m) => m.data_rega).sort().pop(); return l.filter((m) => m.data_rega === u).map((m) => ({ amostra_id: m.id, data_rega: m.data_rega, area_id: m.area_id, activista_id: m.activista_id, feita: DB.monitorias.some((x) => x.amostra_id === m.id) })); },
    regas_campo: (a) => DB.registos.filter((r) => r.area_id === a.p_area && !r.teste).sort((x, y) => y.saida_em.localeCompare(x.saida_em)).slice(0, 10).map((r) => ({ id: r.id, data: r.data, quem: nomeAct(r.activista_id), teste: false, pessoas: r.pessoas,
      entrada_em: r.entrada_em, saida_em: r.saida_em, plantas_regadas: r.plantas_regadas, foto_entrada: r.foto_entrada, foto_rega: r.foto_rega, foto_saida: r.foto_saida, foto_entrada_em: r.foto_entrada_em, foto_rega_em: r.foto_rega_em, foto_saida_em: r.foto_saida_em,
      fotos_outro: false, corrigido_por: null, motivo_correccao: null, plantas_originais: r.plantas_originais ?? null, plantas_corrigidas_em: r.plantas_corrigidas_em ?? null })),
    monitorias_campo: (a) => DB.monitorias.filter((m) => m.area_id === a.p_area).map((m) => ({ id: m.amostra_id, feito_em: m.feito_em, nota: m.nota, solo_regado: m.solo_regado, pct_humido: m.pct_humido, verificador: nomeU(m.verificador_id), foto_path: 'demo/monitoria.jpg', fotos_outro: false, n_vivas: m.n_vivas, n_secas: m.n_secas, n_mortas: m.n_mortas })),
    percursos_dia: (a) => (['tecnico', 'supervisor', 'gestor', 'director', 'cliente'].includes(papel) ? DB.activistas.filter((t) => !vis() || vis().includes(t.id)).map((t) => { const l = reais().filter((r) => r.activista_id === t.id && r.data === a.p_data).sort((x, y) => x.entrada_em.localeCompare(y.entrada_em));
      return l.length ? { activista_id: t.id, nome: t.nome, teste: false, user_id: null, n: l.length * 5 + 1, primeiro: new Date(+new Date(l[0].entrada_em) - 15 * 6e4).toISOString(), ultimo: l[l.length - 1].saida_em } : null; }).filter(Boolean) : []),
    percurso_dia: (a) => percursoDe(a.p_data, a.p_activista),
    dias_sem_rega_lista: (a) => DB.dsr.filter((d) => !d.removido && naData(d.data, a.p_de, a.p_ate) && (!act() || d.activista_id === A1) && (!vis() || vis().includes(d.activista_id))).map((d) => { const t = DB.activistas.find((x) => x.id === d.activista_id) || {}, ar = d.area_id ? area(d.area_id) : null;
      return { ...d, activista: t.nome, comunidade: ar ? ar.comunidade : t.comunidade_principal, tecnico: t.tecnico, produtor: ar ? ar.produtor : null, meu: d.user_id === EU, regas: reais().filter((r) => r.activista_id === d.activista_id && r.data === d.data).length }; }),
    painel_resumo_periodo: (a) => resumo(a.p_de, a.p_ate), painel_resumo: () => resumo(null, null),
    painel_monitoria: (a) => monitoria(a.p_de, a.p_ate),
    painel_monitoria_campos: (a) => (papel === 'cliente' ? null : DB.amostras.filter((m) => naData(m.data_rega, a.p_de, a.p_ate)).map((m) => { const o = DB.monitorias.find((x) => x.amostra_id === m.id), ar = area(m.area_id);
      return { id: m.id, verificador: NOMES[m.papel], papel: m.papel, data_rega: m.data_rega, sorteado_em: m.criado_em, area_id: m.area_id, produtor: ar.produtor, comunidade: ar.comunidade, zona: null, activista: nomeAct(m.activista_id), verificado_em: o?.feito_em || null, nota: o?.nota ?? null, solo_regado: o?.solo_regado ?? null, pct_humido: o?.pct_humido ?? null }; })),
    painel_plantas_dia_equipa: (a) => { const o = {}; reais().filter((r) => naData(r.data, a.p_de, a.p_ate)).forEach((r) => { const k2 = r.activista_id + '|' + r.data, t = DB.activistas.find((x) => x.id === r.activista_id);
      const x = (o[k2] ||= { data: r.data, equipa: t.nome, comunidade: t.comunidade_principal, plantas: 0, campos: 0, pessoas: 0, tamanho: t.equipa_tamanho }); x.plantas += r.plantas_regadas; x.campos++; x.pessoas = Math.max(x.pessoas, r.pessoas || 1); }); return Object.values(o); },
    painel_tempos_equipa: (a) => DB.activistas.map((t) => { const l = reais().filter((r) => r.activista_id === t.id && naData(r.data, a.p_de, a.p_ate)).sort((x, y) => x.entrada_em.localeCompare(y.entrada_em)); if (!l.length) return null;
      const d = []; for (let i = 1; i < l.length; i++) if (l[i].data === l[i - 1].data) d.push(mins(l[i - 1].saida_em, l[i].entrada_em));
      return { equipa: t.nome, rega_min: media(l.map((r) => mins(r.entrada_em, r.saida_em))), deslocacao_min: media(d), deslocacoes: d.length }; }).filter(Boolean),
    painel_tempos_equipa2: (a) => { const regas = [], eqs = [], med = (v) => { const l = v.filter((x) => x != null).sort((x, y) => x - y); return l.length ? (l.length % 2 ? l[(l.length - 1) / 2] : (l[l.length / 2 - 1] + l[l.length / 2]) / 2) : null; };
      DB.activistas.forEach((t) => { const l = reais().filter((r) => r.activista_id === t.id && naData(r.data, a.p_de, a.p_ate)).sort((x, y) => x.entrada_em.localeCompare(y.entrada_em)); if (!l.length) return;
        const rs = l.map((r, i) => { const ar = area(r.area_id), ok = r.agua_em && r.agua_em > r.entrada_em && r.agua_em <= r.saida_em, esp = ok ? mins(r.entrada_em, r.agua_em) : 0, rg = mins(ok ? r.agua_em : r.entrada_em, r.saida_em), ant = i && l[i - 1].data === r.data ? l[i - 1] : null;
          return { id: r.id, data: r.data, equipa: t.nome, area_id: r.area_id, produtor: ar.produtor, comunidade: ar.comunidade, vivas: ar.vivas, instaladas: ar.instaladas, area_m2: null, plantas: r.plantas_regadas, pessoas: r.pessoas, entrada_em: r.entrada_em, agua_em: r.agua_em, saida_em: r.saida_em,
            espera_min: esp, rega_min: rg, ritmo: r.pessoas > 0 && rg > 0 ? Math.round(r.plantas_regadas / (r.pessoas * rg / 60)) : null, desloc_min: ant ? mins(ant.saida_em, r.entrada_em) : null, dist_m: null }; });
        regas.push(...rs); const d = rs.filter((r) => r.desloc_min != null && r.desloc_min <= 60);
        eqs.push({ equipa: t.nome, regas: rs.length, plantas: rs.reduce((s2, r) => s2 + r.plantas, 0), plantas_campo: Math.round(rs.reduce((s2, r) => s2 + r.plantas, 0) / rs.length), espera_med: med(rs.map((r) => r.espera_min)), rega_med: med(rs.map((r) => r.rega_min)), ritmo_med: med(rs.map((r) => r.ritmo)), desloc_med: med(d.map((r) => r.desloc_min)), desloc_n: d.length, dist_med: null, pausas: rs.filter((r) => r.desloc_min > 60).length }); });
      return { equipas: eqs, regas }; },
    membros_lista: () => (['activista', 'tecnico', 'supervisor', 'gestor', 'director', 'me'].includes(papel) ? membros().filter((m) => m.activo && (act() ? m.activista_id === A1 : !vis() || vis().includes(m.activista_id))).map((m) => {
      const p = (DB.presencas || []).find((x) => x.activista_id === m.activista_id && x.data === dia(0)); return { ...m, presente_hoje: p ? p.presentes.includes(m.id) : null }; }) : null),
    gravar_membro: (a) => { const l = membros(); let m = l.find((x) => x.id === a.p_id); const antes = m ? m.activista_id : null;
      if (!m) { m = { id: a.p_id, activista_id: a.p_activista, equipa_rh: a.p_activista, nome: a.p_nome, contrato: null, inicio: null, fim: null, activo: true }; l.push(m); }
      Object.assign(m, { activista_id: a.p_activista, nome: a.p_nome, activo: a.p_activo !== false });
      [antes, a.p_activista].filter(Boolean).forEach((id) => { const t = DB.activistas.find((x) => x.id === id); if (t) t.equipa_tamanho = 1 + l.filter((x) => x.activo && x.activista_id === id).length; });
      guardarDB(); return { id: m.id }; },
    gravar_presencas: (a) => { DB.presencas ||= []; DB.presencas = DB.presencas.filter((x) => !(x.activista_id === a.p_activista && x.data === a.p_data));
      const ok = (a.p_presentes || []).filter((id) => membros().some((m) => m.id === id && m.activista_id === a.p_activista));
      DB.presencas.push({ id: a.p_id, activista_id: a.p_activista, data: a.p_data, presentes: ok, outros: a.p_outros || 0 }); guardarDB(); return { pessoas: 1 + ok.length + (a.p_outros || 0) }; },
    // v156: «O meu dia» do técnico e do supervisor de exemplo, «Fechar o dia» e confirmar regas com ⚠️
    meu_dia: () => {
      if (!['tecnico', 'supervisor'].includes(papel)) return null;
      const hoje = dia(0), ids = vis(), est = estadoRonda();
      const eqs = DB.activistas.filter((t) => ids.includes(t.id) && DB.areas.some((a) => a.activista_id === t.id)).map((t) => {
        const l = reais().filter((r) => r.activista_id === t.id && r.data === hoje), sr = DB.dsr.filter((d) => !d.removido && d.activista_id === t.id && d.data === hoje).map((d) => d.motivo);
        return { id: t.id, nome: t.nome, comunidade: t.comunidade_principal, sem_telefone: false, regas: l.length, plantas: l.reduce((x, r) => x + r.plantas_regadas, 0),
          chegada: l.map((r) => r.entrada_em).sort()[0] || null, sem_rega: sr.length ? sr.join(', ') : null }; });
      const base = (a) => (a.vivas > 0 ? a.vivas : a.instaladas) || 0;
      const alertas = reais().filter((r) => ids.includes(r.activista_id) && !r.alerta_confirmado_em && !r.plantas_corrigidas_em && r.plantas_regadas > base(area(r.area_id)))
        .map((r) => ({ registo_id: r.id, data: r.data, area_id: r.area_id, produtor: area(r.area_id).produtor, equipa: nomeAct(r.activista_id), plantas: r.plantas_regadas, base: base(area(r.area_id)), ritmo: null, mediana: null, tipo: 'mais_que_base' }));
      const comunidades = papel === 'tecnico' ? ['Exemplo Norte'] : ['Exemplo Norte', 'Exemplo Sul'];
      return { data: hoje, hora_chegada: '06:00', fechado_em: (DB.fechos || {})[EU + hoje] || null, equipas: eqs, alertas,
        monitoria_hoje: DB.amostras.filter((m) => m.verificador_id === EU && m.data_rega === dia(1) && !DB.monitorias.some((o) => o.amostra_id === m.id)).length, monitoria_falhas_ontem: 0,
        sem_equipa: DB.areas.filter((a) => !a.activista_id && comunidades.includes(a.comunidade)).length,
        por_aprovar: DB.areas.filter((a) => a.poligono_proposto && ids.includes(a.activista_id)).map((a) => ({ area_id: a.id, produtor: a.produtor, comunidade: a.comunidade, equipa: nomeAct(a.activista_id), area_m2: a.area_m2_proposta, proposta_em: a.proposta_em, quem: nomeAct(a.activista_id) })),
        por_terminar: est.filter((e) => e.por_terminar && ids.includes(area(e.area_id).activista_id)).map((e) => { const a = area(e.area_id); return { area_id: a.id, produtor: a.produtor, equipa: nomeAct(a.activista_id), base: base(a), regadas: e.plantas_ronda, data: e.data_parcial }; }) };
    },
    fechar_dia: () => { const hoje = dia(0), m = RPC.meu_dia(); const falta = (m?.equipas || []).filter((e) => !e.regas && !e.sem_rega);
      if (falta.length) throw Object.assign(new Error('Ainda sem rega nem motivo: ' + falta.map((e) => e.nome).join(', ')), { erro400: true });
      (DB.fechos ||= {})[EU + hoje] = new Date().toISOString(); return DB.fechos[EU + hoje]; },
    confirmar_rega2: (a) => { const r = DB.registos.find((x) => x.id === a.p_id); if (!r) return null;
      const ar = DB.areas.find((x) => x.id === r.area_id) || {}; const base = ar.vivas > 0 ? ar.vivas : (ar.instaladas || 0); const v = a.p_vivas;
      if (base > 0 && r.plantas_regadas > base && v != null && v < r.plantas_regadas) throw Object.assign(new Error(`Contou ${v} plantas vivas, menos do que as ${r.plantas_regadas} regadas. Corrija as plantas regadas na ficha do campo.`), { erro400: true });
      Object.assign(r, { alerta_confirmado_em: new Date().toISOString(), alerta_confirmado_nota: a.p_nota, alerta_vivas_contadas: v ?? null });
      let rc = 'nao';
      if (v != null && v !== base) { if (DB.recontagens.some((x) => x.area_id === r.area_id && ['por_encaminhar', 'encaminhada', 'enviada', 'recusada'].includes(x.estado))) rc = 'ja_havia';
        else { DB.recontagens.push({ id: uid(), area_id: r.area_id, motivo: `Rega com ${r.plantas_regadas} plantas regadas: contou ${v} plantas vivas; a base tem ${base}.`, estado: 'por_encaminhar', pedido_em: new Date().toISOString(), pedido_por: EU, oficial_id: null }); rc = 'pedida'; } }
      return { recontagem: rc }; },
    confirmar_rega: (a) => { const r = DB.registos.find((x) => x.id === a.p_id); if (r) { r.alerta_confirmado_em = new Date().toISOString(); r.alerta_confirmado_nota = a.p_nota; } return null; },
    // v156: medir a área: o activista deixa a área por aprovar; técnico, supervisor e gestor gravam o limite
    gravar_poligono: (a) => { const ar = area(a.p_area); if (!ar.id || !Array.isArray(a.p_pontos)) return null; const m2 = areaM2(a.p_pontos);
      if (papel === 'activista') Object.assign(ar, { poligono_proposto: a.p_pontos, area_m2_proposta: m2, proposta_em: a.p_medido_em || new Date().toISOString() });
      else { Object.assign(ar, { poligono: a.p_pontos, area_m2: m2, limites_abertos: false }); if (ar.latitude == null) { const c = centro(a.p_pontos); ar.latitude = c[1]; ar.longitude = c[0]; } }
      return null; },
    monitoria_falhas: () => [], painel_cumprimento: () => null,
    // v156: sugestões ficam na base de exemplo (antes iam para o servidor verdadeiro; Valdo, 30/10/2026: o que se faz na apresentação não entra no servidor)
    enviar_sugestao2: (a) => novaSugestao(a), enviar_sugestao3: (a) => novaSugestao(a),
    avaliar_sugestao: (a) => { const x = (DB.sugestoes || []).find((y) => y.id === a.p_id); if (x) Object.assign(x, { estado: a.p_estado, nota: a.p_nota ?? x.nota, avaliada_em: new Date().toISOString() }); return null; },
    // v156: manutenção (cava-roda e mulching) em Exemplo Sul
    manutencao_campos: () => manutCampos(),
    manutencao_registos_campo: (a) => (DB.manut || []).filter((x) => x.area_id === a.p_area && !x.removido).sort((x, y) => y.feito_em.localeCompare(x.feito_em)).map((x) => ({ ...x, quem: nomeU(x.feito_por) })),
    gravar_manutencao: (a) => { (DB.manut ||= []).push({ id: a.p_id, area_id: a.p_area, data: a.p_data, cavaroda: a.p_cavaroda, mulching: a.p_mulching, pessoas: a.p_pessoas ?? null, obs: a.p_obs || null, foto_path: a.p_foto || null, feito_por: EU, feito_em: a.p_em || new Date().toISOString() });
      const ar = area(a.p_area), pl = (ar.vivas > 0 ? ar.vivas : ar.instaladas) || 0; if (a.p_cavaroda < pl || a.p_mulching < pl) DB.manutFeitos = (DB.manutFeitos || []).filter((f) => f.area_id !== a.p_area); return null; },
    remover_manutencao: (a) => { const x = (DB.manut || []).find((y) => y.id === a.p_id); if (x) x.removido = true; return null; },
    marcar_manutencao_feita: (a) => { DB.manutFeitos = (DB.manutFeitos || []).filter((f) => f.area_id !== a.p_area); if (a.p_feito) DB.manutFeitos.push({ area_id: a.p_area, feito: true, marcado_em: a.p_em || new Date().toISOString(), marcado_por: EU }); return null; },
    painel_manutencao: (a) => { const M = manutCampos(); if (!M) return null; const C = M.campos, pl = (c) => c.plantas || 0;
      const por_comunidade = [...new Set(C.map((c) => c.comunidade))].map((com) => { const l = C.filter((c) => c.comunidade === com), e = (c) => (c.feito ? 'feito' : c.cavaroda == null ? 'por' : c.cavaroda >= pl(c) && c.mulching >= pl(c) ? 'completo' : 'curso');
        return { comunidade: com, campos: l.length, feitos: l.filter((c) => e(c) === 'feito').length, completos: l.filter((c) => e(c) === 'completo').length, em_curso: l.filter((c) => e(c) === 'curso').length, por_fazer: l.filter((c) => e(c) === 'por').length,
          plantas: l.reduce((x, c) => x + pl(c), 0), cavaroda: l.reduce((x, c) => x + Math.min(c.cavaroda || 0, pl(c)), 0), mulching: l.reduce((x, c) => x + Math.min(c.mulching || 0, pl(c)), 0) }; });
      const dias = {}; (DB.manut || []).filter((x) => !x.removido && naData(x.data, a.p_de, a.p_ate)).forEach((x) => { const d = (dias[x.data] ||= { data: x.data, campos: new Set(), cavaroda: 0, mulching: 0, pessoas: 0 }); d.campos.add(x.area_id); d.cavaroda += x.cavaroda; d.mulching += x.mulching; d.pessoas += x.pessoas || 0; });
      return { por_comunidade, por_dia: Object.values(dias).sort((x, y) => x.data.localeCompare(y.data)).map((d) => ({ ...d, campos: d.campos.size })) }; },
    painel_zonas: () => [],
    painel_chuva: (a) => DB.chuva.filter((c) => naData(c.data, a.p_de, a.p_ate)).map((c) => ({ data: c.data, comunidade: c.comunidade, zona: c.zona, mm: c.mm, registos: 1, fotos: papel === 'cliente' ? undefined : [{ path: c.foto, mm: c.mm, lida_em: c.lida_em, activista: c.activista }] })),
    painel_constrangimentos: (a) => DB.constr.map((c) => { const r = DB.registos.find((x) => x.id === c.registo_id); if (!r || r.teste || !naData(r.data, a.p_de, a.p_ate)) return null; const ar = area(r.area_id);
      return { data: r.data, tipo: c.tipo, descricao: c.descricao, area_id: r.area_id, produtor: ar.produtor, comunidade: ar.comunidade, zona: null, activista: nomeAct(r.activista_id), plantas_regadas: r.plantas_regadas, plantas_campo: ar.vivas }; }).filter(Boolean),
    painel_testes: () => null, painel_plantas_marcadas: () => null, painel_medicoes: () => null,
    coqueiros_lista: () => null, planos_lista: () => [], testes_equipa: () => [], plantas_por_campo: () => [], regas_sem_motivo: () => [],
    minhas_respostas: () => (DB.sugestoes || []).filter((x) => x.perfil_id === EU && ['feita', 'aprovada', 'recusada'].includes(x.estado)).map((x) => ({ id: x.id, texto: x.texto, estado: x.estado, nota: x.nota, avaliada_em: x.avaliada_em })),
    minhas_sugestoes_feitas: () => [], avisos_monitoria: () => [], visitas_painel_resumo: () => [],
    sugestoes_lista: () => (papel === 'gestor' ? { sugestoes: [...(DB.sugestoes || [])].sort((x, y) => y.criada_em.localeCompare(x.criada_em)), problemas: [] } : null),
    areas_fora_plano2: () => ({ fora: [], na_rega: [] }), areas_fora_plano: () => [], medicoes_alvo: () => [],
    // ---- o que muda a base de exemplo ----
    encaminhar_recontagem2: (a) => { const r = DB.recontagens.find((x) => x.id === a.p_id); if (r) Object.assign(r, { estado: 'encaminhada', oficial_id: a.p_oficial, encaminhada_em: a.p_em || new Date().toISOString() }); return null; },
    enviar_recontagem2: (a) => { const r = DB.recontagens.find((x) => x.id === a.p_id); if (r) Object.assign(r, { estado: 'enviada', vivas: a.p_vivas, mortas: a.p_mortas, foto_path: a.p_foto, foto_campo_path: a.p_foto_campo, lat: a.p_lat, lon: a.p_lon, precisao_m: a.p_precisao, contada_em: a.p_em, enviada_em: new Date().toISOString(), navuna: a.p_navuna ?? null }); return null; },
    validar_recontagem2: (a) => { const r = DB.recontagens.find((x) => x.id === a.p_id); if (!r) return null;
      if (a.p_validar) { const ar = area(r.area_id); Object.assign(r, { estado: 'validada', validada_em: a.p_em || new Date().toISOString(), vivas_antes: ar.vivas }); ar.vivas = r.vivas; }
      else Object.assign(r, { estado: 'recusada', recusa_motivo: a.p_motivo, recusada_em: new Date().toISOString(), navuna: null }); return null; },
    cancelar_recontagem: (a) => { const r = DB.recontagens.find((x) => x.id === a.p_id); if (r) r.estado = 'cancelada'; return null; },
    pedir_recontagem2: (a) => { if (!DB.recontagens.some((x) => x.id === a.p_id)) DB.recontagens.push({ id: a.p_id, area_id: a.p_area, motivo: a.p_motivo, estado: a.p_oficial && ['me', 'gestor'].includes(papel) ? 'encaminhada' : 'por_encaminhar', pedido_em: a.p_em || new Date().toISOString(), pedido_por: EU, oficial_id: ['me', 'gestor'].includes(papel) ? a.p_oficial || null : null }); return null; },
    gravar_queimada2: (a) => { if (!DB.queimadas.some((x) => x.id === a.p_id)) { DB.queimadas.push({ id: a.p_id, area_id: a.p_area, data: a.p_data, observacao: a.p_obs || null, foto_path: a.p_foto || null, registada_por: EU, registada_em: new Date().toISOString(), plantas_afectadas: a.p_afectadas, plantas_mortas: a.p_mortas ?? null });
      DB.recontagens.push({ id: uid(), area_id: a.p_area, queimada_id: a.p_id, motivo: 'Queimada', estado: 'por_encaminhar', pedido_em: new Date().toISOString(), pedido_por: EU, oficial_id: null }); } return null; },
    aprovar_poligono: (a) => { const ar = area(a.p_area); if (ar.id && ar.poligono_proposto) { if (a.p_aprovar) { ar.poligono = ar.poligono_proposto; ar.area_m2 = ar.area_m2_proposta; ar.limites_abertos = false; } ar.poligono_proposto = null; ar.area_m2_proposta = null; ar.proposta_em = null; } return null; },
    atribuir_area2: (a) => { const ar = area(a.p_area); if (ar.id) ar.activista_id = a.p_activista; return null; },
    gravar_dia_sem_rega3: (a) => { DB.dsr.push({ id: a.p_id, activista_id: a.p_activista, data: a.p_data, motivo: a.p_motivo, todo_dia: a.p_todo_dia, descricao: a.p_descricao || null, quem: NOMES[papel], user_id: EU, criado_em: new Date().toISOString(), foto_path: a.p_foto || null, area_id: a.p_area || null, entrada_em: a.p_entrada || null }); return null; },
    remover_dia_sem_rega: (a) => { const d = DB.dsr.find((x) => x.id === a.p_id); if (d) d.removido = true; return null; },
    corrigir_plantas_rega: (a) => { const r = DB.registos.find((x) => x.id === a.p_id); if (r) { if (r.plantas_originais == null) r.plantas_originais = r.plantas_regadas; r.plantas_regadas = a.p_plantas; r.plantas_corrigidas_em = new Date().toISOString(); } return null; },
  };
  const TABELAS = {
    perfis: () => [{ id: EU, nome: NOMES[papel], papel, activista_id: act(), titulo: null, gere_acessos: papel === 'gestor', trocar_senha: false, marca_coqueiros: false, so_teste: false }],
    activistas: () => DB.activistas, areas: () => areasVisiveis(), zonas: () => [], pocos: () => [], coberturas: () => [], pessoas_acesso: () => [], plantas: () => [], config: () => [{ chave: 'monitoria_campos_por_dia', valor: 2 }],
    queimadas: () => DB.queimadas.filter((q) => !q.removida), registos_rega: () => DB.registos.filter((r) => !act() || r.activista_id === A1),
    jornadas: () => DB.jornadas, chuva: () => [], monitorias: () => [], constrangimentos: () => DB.constr,
  };
  function filtrar(linhas, q) {
    let out = linhas;
    for (const [c, v] of q.entries()) {
      if (['select', 'order', 'limit', 'offset', 'on_conflict', 'columns', 'or'].includes(c)) continue;
      const i = v.indexOf('.'), opr = v.slice(0, i), val = v.slice(i + 1);
      const cmp = (x) => { const a = x[c]; if (opr === 'is') return val === 'null' ? a == null : String(a) === val; if (a == null) return false;
        const n1 = +a, n2 = +val, num = !isNaN(n1) && !isNaN(n2) && typeof a !== 'boolean';
        if (opr === 'eq') return String(a) === val; if (opr === 'neq') return String(a) !== val;
        if (opr === 'in') return val.replace(/^\(|\)$/g, '').split(',').includes(String(a));
        const d = num ? n1 - n2 : String(a).localeCompare(val);
        return opr === 'gt' ? d > 0 : opr === 'gte' ? d >= 0 : opr === 'lt' ? d < 0 : opr === 'lte' ? d <= 0 : true; };
      out = out.filter(cmp);
    }
    return out;
  }
  const resp = (b, st = 200, h = {}) => new Response(st === 204 || b === undefined ? null : JSON.stringify(b), { status: st, headers: { 'Content-Type': 'application/json', ...h } });
  const fotosMem = {};
  async function demoFetch(entrada, init = {}) {
    const url = new URL(typeof entrada === 'string' ? entrada : entrada.url), metodo = (init.method || (entrada.method) || 'GET').toUpperCase();
    const h = new Headers(init.headers || (typeof entrada === 'string' ? {} : entrada.headers));
    let corpo = init.body; if (corpo == null && typeof entrada !== 'string') { try { corpo = await entrada.text(); } catch {} }
    const json = () => { try { return typeof corpo === 'string' ? JSON.parse(corpo || '{}') : {}; } catch { return {}; } };
    const c = url.pathname;
    try {
      if (c.startsWith('/auth/v1/')) { if (c.endsWith('/logout')) return resp(undefined, 204); return c.endsWith('/token') ? resp(SESSAO) : resp(USER); }
      if (c.startsWith('/storage/v1/')) {
        if (metodo === 'POST' || metodo === 'PUT') {
          const p = decodeURIComponent(c.split('/object/')[1] || ''), blob = corpo instanceof Blob ? corpo : corpo instanceof FormData ? [...corpo.values()].find((v) => v instanceof Blob) : null;
          if (blob) fotosMem[p.split('/').slice(1).join('/')] = URL.createObjectURL(blob);
          return resp({ Key: p, Id: p });
        }
        return resp([]);
      }
      if (c.startsWith('/functions/v1/')) return resp({ activistas: [], utilizadores: [], clientes: [], nomes: {} });
      if (c.startsWith('/rest/v1/rpc/')) {
        const f = c.slice('/rest/v1/rpc/'.length), a = json();
        if (RPC[f]) { let r; try { r = RPC[f](a); } catch (e) { if (e.erro400) return resp({ code: 'P0001', message: e.message }, 400); throw e; } guardarDB(); return resp(r === undefined ? null : r); }
        return resp(/^(gravar|definir|remover|registar|enviar|aprovar|abrir|justificar|marcar|avaliar|estado_|senha|voltar|validar|encaminhar|pedir|cancelar)/.test(f) ? null : []);
      }
      if (c.startsWith('/rest/v1/')) {
        const t = c.slice('/rest/v1/'.length);
        if (metodo === 'POST' || metodo === 'PATCH' || metodo === 'PUT') {
          let l = json(); l = Array.isArray(l) ? l : [l];
          const alvo = { registos_rega: DB.registos, constrangimentos: DB.constr, jornadas: DB.jornadas }[t];
          if (alvo) for (const x of l) if (!alvo.some((y) => y.id === x.id)) alvo.push(t === 'registos_rega' ? { user_id: EU, ...x } : x);
          if (t === 'monitorias') for (const x of l) DB.monitorias.push({ amostra_id: x.amostra_id, area_id: x.area_id, verificador_id: EU, feito_em: x.feito_em || new Date().toISOString(), nota: x.nota, solo_regado: x.solo_regado, pct_humido: x.pct_humido,
            plantas_obs: x.plantas_obs?.length || 0, humidas: (x.plantas_obs || []).filter((o) => o.humido).length, n_vivas: x.n_vivas, n_secas: x.n_secas, n_mortas: x.n_mortas });
          if (t === 'chuva') for (const x of l) DB.chuva.push({ data: x.data, comunidade: x.comunidade, zona: x.zona || null, mm: x.mm, activista: NOMES[papel], lida_em: x.lida_em, foto: x.foto_path });
          guardarDB(); return resp(undefined, 201);
        }
        if (metodo === 'DELETE') return resp(undefined, 204);
        const linhas = filtrar((TABELAS[t] || (() => []))(), url.searchParams);
        if (metodo === 'HEAD') return new Response(null, { status: 200, headers: { 'Content-Range': `0-${Math.max(0, linhas.length - 1)}/${linhas.length}` } });
        if ((h.get('Accept') || '').includes('vnd.pgrst.object')) return resp(linhas[0] || null);
        return resp(linhas, 200, { 'Content-Range': `0-${Math.max(0, linhas.length - 1)}/${linhas.length}` });
      }
    } catch (e) { console.error('[demo]', e); return resp({ message: 'Erro no modo apresentação: ' + e.message }, 500); }
    return resp([]);
  }
  const fetchReal = window.fetch.bind(window);
  window.fetch = (e, i) => { const u = typeof e === 'string' ? e : e?.url || ''; return u.includes('.supabase.co') ? demoFetch(e, i) : fetchReal(e, i); };
  // fotografias: as tiradas na apresentação aparecem; as outras são uma imagem de exemplo
  const FOTO_EX = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="420"><rect width="640" height="420" fill="#dfe9d8"/><path d="M0 330 Q160 290 320 320 T640 300 V420 H0Z" fill="#b7a07a"/><g fill="#3f7d3a"><path d="M300 330 q-60-80-120-90 q70 0 120 60z"/><path d="M320 330 q50-90 130-100 q-80 10-120 90z"/><path d="M310 330 q0-110 10-150 q10 60-2 150z"/></g><text x="320" y="70" text-anchor="middle" font-family="sans-serif" font-size="30" fill="#2c5228">Fotografia de exemplo</text><text x="320" y="108" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#2c5228">Modo apresentação</text></svg>');
  const sbOrig = window.supabase;
  if (sbOrig && sbOrig.createClient) {
    window.supabase = Object.assign({}, sbOrig, { createClient(u, k3, o = {}) {
      const cl = sbOrig.createClient(u, k3, { ...o, global: { ...(o.global || {}), fetch: demoFetch } });
      const from = cl.storage.from.bind(cl.storage);
      cl.storage.from = (b) => { const s = from(b); s.createSignedUrl = async (p) => ({ data: { signedUrl: fotosMem[p] || FOTO_EX, signedURL: fotosMem[p] || FOTO_EX }, error: null }); return s; };
      return cl;
    } });
  }

  function parar() { if (andar) { clearInterval(andar); andar = null; } }
  function volta(a) {                       // pontos a cada ~4 m à volta de um rectângulo de 60 × 50 m (sentido dos ponteiros), a fechar no início
    const ky = 110540, kx = 111320 * Math.cos(a.latitude * Math.PI / 180), cs = [[-30, -25], [-30, 25], [30, 25], [30, -25], [-30, -25]], out = [];
    for (let j = 0; j < cs.length - 1; j++) { const [x1, y1] = cs[j], [x2, y2] = cs[j + 1], n = Math.round(Math.hypot(x2 - x1, y2 - y1) / 4);
      for (let t = 0; t < n; t++) { const x = x1 + (x2 - x1) * t / n + (Math.random() - 0.5) * 0.6, y = y1 + (y2 - y1) * t / n + (Math.random() - 0.5) * 0.6; out.push([a.latitude + y / ky, a.longitude + x / kx]); } }
    out.push([a.latitude + cs[0][1] / ky, a.longitude + cs[0][0] / kx]); return out;
  }
  window.DEMO = { papel, lat: cfg.lat, lon: cfg.lon, desde: cfg.desde, NOMES,
    limparTelefone,
    // v156: «🎬 Pôr-me neste campo» — a posição passa a ser o centro do campo e a ficha volta a abrir
    irPara(id) { const a = area(id); if (a.latitude == null) return; parar(); porPos(a.latitude, a.longitude);
      setTimeout(() => { if (typeof window.abrirFicha === 'function') window.abrirFicha(id, '<div class="msg ok">🎬 Está agora neste campo (apresentação).</div>'); }, 500); },
    // v156: medir a área ao vivo: vai para um canto do campo (rectângulo de 60 × 50 m à volta do ponto) e, ao «Começar», anda à volta
    cantoMedir(id) { const a = area(id); if (a.latitude == null) return; parar(); const k = volta(a); porPos(k[0][0], k[0][1]); },
    andarMedir(id) { const a = area(id); if (a.latitude == null) return; parar(); const k = volta(a); let i = 0;
      andar = setInterval(() => { i++; if (i >= k.length) { parar(); return; } porPos(k[i][0], k[i][1]); }, 350); },
    pararAndar: () => parar(),
    terminar() { limparTelefone(); try { sessionStorage.removeItem('rega.demo'); sessionStorage.removeItem('rega.demo.db'); sessionStorage.removeItem('rega.demo.pos'); } catch {} location.reload(); },
    recomecar() { limparTelefone(); try { sessionStorage.removeItem('rega.demo.db'); sessionStorage.removeItem('rega.demo.pos'); } catch {} location.reload(); },
  };
})();
