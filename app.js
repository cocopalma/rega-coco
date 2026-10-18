/* Rega Coco — app de reporte de rega (fase de aprendizagem)
   Funciona offline: as áreas ficam guardadas no telefone e os registos ficam numa fila
   até haver rede. Nada é apagado do telefone antes de o servidor confirmar. */
'use strict';
const CFG = {
  url: 'https://fgzdqnvobgfzjetbbxcm.supabase.co',
  chave: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZnemRxbnZvYmdmempldGJieGNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE2NDgyMzUsImV4cCI6MjEwNzIyNDIzNX0.1bSDbPLWMvhIG2fzu_Ta2vm1qV1NutzMEmii3wbN7mY',
  dominio: 'rega-coco.example.com', // utilizadores dos activistas: <utilizador>@este-dominio
  margemGPS: 200,      // metros: distância máxima ao centro do campo para validar (campos sem polígono; a afinar no terreno)
  margemPoligono: 50,  // metros: distância máxima à borda do polígono (13/10/2026, Valdo)
  litrosPlanta: 5,     // litros por planta em cada rega (16/10/2026, Valdo)
  dataOrigem: '16/10/2026', // último dia dos dados de rega do Dalmar importados (Controlo_Rega_Areas.xlsx)
  precisaoCoord: 10,   // metros: pior precisão aceite para gravar a coordenada de um campo (a afinar no terreno)
  precisaoIdeal: 5,    // metros: precisão recomendada
  metaPlantas: 140,    // plantas por pessoa por dia (meta do Valdo, 11/10/2026)
  // monitoria por planta (11/10/2026): amostra de Cochran com correcção para população finita
  monZ: 1.96, monMargem: 0.10, monP: 0.80,   // 95% de confiança, ±10%, proporção esperada 80%
  monLimiar: 80,       // % mínima de plantas com solo húmido para o campo contar como regado
};
/* Regra da fase de aprendizagem (1–2 semanas): cada equipa rega a sua lista em "rondas".
   Um campo da lista não pode ser regado de novo enquanto a equipa não regar todos os campos da lista.
   A duração de cada ronda concluída é o ciclo provisório da comunidade. */
const sb = supabase.createClient(CFG.url, CFG.chave, { auth: { persistSession: true, autoRefreshToken: true } });
const $ = (s) => document.querySelector(s);
const LOC = typeof LINGUA !== 'undefined' && LINGUA !== 'pt' ? 'en-GB' : 'pt-PT';
const hojeISO = () => new Date().toLocaleDateString('sv-SE');
const fmtData = (d) => d ? new Date(d + (d.length === 10 ? 'T12:00:00' : '')).toLocaleDateString(LOC) : '—';
const fmtHora = (t) => t ? new Date(t).toLocaleTimeString(LOC, { hour: '2-digit', minute: '2-digit' }) : '—';
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const num = (n) => (n ?? 0).toLocaleString(LOC);

// ---------- guardar no telefone ----------
const LS = {
  get(k, d = null) { try { const v = localStorage.getItem('rega.' + k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('rega.' + k, JSON.stringify(v)); } catch (e) { alert('Memória do telefone cheia: ' + e.message); } },
  del(k) { try { localStorage.removeItem('rega.' + k); } catch {} },
};
let S = { perfil: null, areas: [], activistas: [], estado: {}, meus: [], filtro: 'meus', pos: null, user: null };

// ---------- distância ----------
function metros(a, b) {
  const R = 6371000, r = Math.PI / 180;
  const dLat = (b[0] - a[0]) * r, dLon = (b[1] - a[1]) * r;
  const x = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}
// Distância ao campo (13/10/2026, pedido do Dalmar): com polígono, 0 dentro e, fora, a distância à linha mais próxima do polígono;
// sem polígono, a distância ao ponto do campo (centroide).
function dentroPoligono(lat, lon, pol) {
  let d = false;
  for (let i = 0, j = pol.length - 1; i < pol.length; j = i++) {
    const [xi, yi] = pol[i], [xj, yj] = pol[j];
    if ((yi > lat) !== (yj > lat) && lon < ((xj - xi) * (lat - yi)) / (yj - yi + 1e-15) + xi) d = !d;
  }
  return d;
}
function distPoligono(lat, lon, pol) {
  if (dentroPoligono(lat, lon, pol)) return 0;
  const kx = 111320 * Math.cos(lat * Math.PI / 180), ky = 110540; let best = Infinity;
  for (let i = 0; i < pol.length; i++) {
    const [x1, y1] = pol[i], [x2, y2] = pol[(i + 1) % pol.length];
    const ax = (x1 - lon) * kx, ay = (y1 - lat) * ky, bx = (x2 - lon) * kx, by = (y2 - lat) * ky, dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy;
    const t = L2 ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / L2)) : 0;
    best = Math.min(best, Math.hypot(ax + t * dx, ay + t * dy));
  }
  return best;
}
const temPoligono = (a) => Array.isArray(a.poligono) && a.poligono.length >= 3;
function distCampo(a, pos) {
  if (temPoligono(a)) return distPoligono(pos[0], pos[1], a.poligono);
  return a.latitude != null ? metros(pos, [a.latitude, a.longitude]) : null;
}
function rumo(a, b) {
  const r = Math.PI / 180, y = Math.sin((b[1] - a[1]) * r) * Math.cos(b[0] * r);
  const x = Math.cos(a[0] * r) * Math.sin(b[0] * r) - Math.sin(a[0] * r) * Math.cos(b[0] * r) * Math.cos((b[1] - a[1]) * r);
  const g = (Math.atan2(y, x) / r + 360) % 360;
  return ['Norte', 'Nordeste', 'Este', 'Sudeste', 'Sul', 'Sudoeste', 'Oeste', 'Noroeste'][Math.round(g / 45) % 8];
}
function lerGPS() {
  return new Promise((ok, falha) => {
    if (!navigator.geolocation) return falha(new Error('Este telefone não tem GPS disponível no navegador.'));
    if (S.fix && Date.now() - S.fix.t < 15000) return ok(S.fix.coords);   // leitura recente do GPS contínuo
    navigator.geolocation.getCurrentPosition(
      (p) => { S.pos = [p.coords.latitude, p.coords.longitude]; S.fix = { coords: p.coords, t: Date.now() }; ok(p.coords); },
      (e) => falha(new Error(e.code === 1 ? 'A app não tem autorização para usar a localização. Autorize nas definições do telefone.' : 'Não foi possível obter o GPS. Vá para céu aberto e tente de novo.')),
      { enableHighAccuracy: true, timeout: 30000, maximumAge: 5000 });
  });
}

// ---------- estado das áreas e rondas ----------
// registos válidos da minha equipa: os que o servidor já tem + os que estão na fila do telefone
function meusRegistos() {
  const vistos = new Set(), out = [];
  for (const r of [...LS.get('meusRegs', []), ...filaRegistos()]) {
    if (vistos.has(r.id) || r.teste || !(r.plantas_regadas > 0)) continue;
    vistos.add(r.id); out.push(r);
  }
  return out;
}
function ultimaRega(a) {
  let u = S.estado[a.id]?.u || null;
  for (const r of meusRegistos()) if (r.area_id === a.id && (!u || r.data > u)) u = r.data;
  return u;
}
// ronda actual de uma equipa: mesma regra do servidor (privado.rondas)
function rondaInfo(actId) {
  const lista = S.areas.filter((a) => a.activista_id === actId), ids = new Set(lista.map((a) => a.id));
  const porRonda = {};
  for (const r of meusRegistos()) {
    if (r.activista_id !== actId || !ids.has(r.area_id)) continue;
    const n = r.ronda || 1; (porRonda[n] ??= { areas: new Set(), ini: r.data, fim: r.data });
    const o = porRonda[n]; o.areas.add(r.area_id); if (r.data < o.ini) o.ini = r.data; if (r.data > o.fim) o.fim = r.data;
  }
  const mr = Math.max(1, ...Object.keys(porRonda).map(Number));
  const cur = porRonda[mr] || { areas: new Set() };
  if (lista.length && cur.areas.size >= lista.length) return { n: mr + 1, feitas: new Set(), total: lista.length, anterior: { n: mr, ...cur } };
  return { n: mr, feitas: cur.areas, total: lista.length, ini: cur.ini };
}
const souActivista = () => S.perfil?.papel === 'activista';
// o que cada função pode fazer na app
const FUNCOES = {
  tecnico: { nome: 'Técnico', desc: 'vê os campos e a rega das equipas dos seus activistas (e das que cobre) e o painel geral; grava coordenadas, atribui campos e pode fazer regas de teste.' },
  supervisor: { nome: 'Supervisor', desc: 'o mesmo que o técnico, para as equipas dos seus técnicos; também muda a zona dos campos.' },
  director: { nome: 'Director (só leitura)', desc: 'vê todos os campos, a rega do dia e o painel; não regista regas.' },
  me: { nome: 'M&E (só leitura)', desc: 'o mesmo que o director.' },
  cliente: { nome: 'Só painel (cliente / administração)', desc: 'vê o painel geral, o mapa e as fichas dos campos com as fotografias; não regista nada.' },
  oficial_me: { nome: 'Oficial de M&E (recontagens)', desc: 'vê só os campos que o M&E lhe encaminha para recontagem e regista as plantas vivas e mortas, com a fotografia da declaração. Sem recontagens, a app fica vazia.' },
};
const PODE_REGAR = ['activista', 'tecnico', 'supervisor', 'gestor'];
const VER_PAINEL = ['tecnico', 'supervisor', 'gestor', 'director', 'me', 'cliente'];
function situacao(a) {
  const u = ultimaRega(a);
  if (!a.activista_id) return { cod: 'sem', txt: 'Sem activista', u };
  let feita, n;
  if (souActivista() && a.activista_id === S.perfil.activista_id) { const ri = rondaInfo(a.activista_id); feita = ri.feitas.has(a.id); n = ri.n; }
  else { const e = S.estado[a.id] || {}; feita = !!e.feita; n = e.ronda || 1; }
  if (!feita && !souActivista()) { const t = testeEm(a.id); if (t) return { cod: 'teste', txt: `Regado em teste (${fmtData(t).slice(0, 5)})`, u, n }; }
  return feita ? { cod: 'feita', txt: `Regada na ronda ${n}`, u, n } : { cod: 'por', txt: `Por regar (ronda ${n})`, u, n };
}
// regas de teste do próprio técnico/supervisor (12/10/2026, Valdo): não contam para a ronda, mas o campo aparece com a cor "Teste"
function testeEm(id) {
  let d = (LS.get('meusTestes', {}) || {})[id] || null;
  for (const r of filaRegistos()) if (r.teste && r.area_id === id && (!d || r.data > d)) d = r.data;
  return d;
}
const COR = { por: '#d84315', feita: '#2e7d32', sem: '#8a8f8b', teste: '#6a1b9a' };
// borda do campo no mapa (16/10/2026, Dalmar via Valdo): azul = já recebeu rega nesta ronda, vermelho = ainda não (ver bordaAzul)
const BORDA = { regado: '#1e5bd8', nunca: '#c62828' };
const COLS_AREAS = 'id,pr,area_n,comunidade,zona,produtor,instaladas,vivas,latitude,longitude,activista_id,activista_proposto,data_plantio,poligono,reactivada_em,area_m2,limites_abertos,poligono_proposto,area_m2_proposta,proposta_em,n_regas_origem,ultima_rega_origem,datas_rega_origem,plantas_regadas_origem,regas_origem_por_pr';
// regas do campo: antes da app (ficheiro do Dalmar, dados até CFG.dataOrigem) + na app (servidor e as que ainda estão no telefone)
function regasDoCampoInfo(a) {
  const e = S.estado[a.id] || {}, fila = filaRegistos().filter((r) => r.area_id === a.id && !r.teste && r.plantas_regadas > 0);
  const app = (e.n || 0) + fila.length, plApp = (e.pl || 0) + fila.reduce((t, r) => t + (r.plantas_regadas || 0), 0);
  // regas antes da app registadas para o produtor (iguais em várias áreas do PR): não se sabe que campo foi regado,
  // por isso não contam neste campo (18/10/2026, Valdo: "as regas devem ser por campo e não por produtor")
  const orig = a.regas_origem_por_pr ? 0 : (a.n_regas_origem || 0), plOrig = a.regas_origem_por_pr ? 0 : (a.plantas_regadas_origem || 0);
  return { orig, app, total: orig + app, plOrig, plApp, litros: (plOrig + plApp) * CFG.litrosPlanta };
}
const jaRegado = (a) => regasDoCampoInfo(a).total > 0;
// borda azul = já recebeu rega NESTA ronda (16/10/2026, Valdo: "zera em cada ronda"). Na 1.ª ronda contam também as regas
// de antes da app (ficheiro do Dalmar); a partir da 2.ª ronda só conta a rega da ronda (interior verde).
const bordaAzul = (a, s = situacao(a)) => s.cod === 'feita' || ((s.n || 1) === 1 && jaRegado(a));
const plantasTxt = (a) => (a.vivas > 0 ? `${num(a.vivas)} plantas vivas` : `${num(a.instaladas)} mudas plantadas`);
const plantasN = (a) => (a.vivas > 0 ? a.vivas : a.instaladas) || 0;
const nomeAct = (id) => (S.activistas.find((x) => x.id === id) || {}).nome || '(por atribuir)';
const minhas = () => S.areas.filter((a) => a.activista_id && a.activista_id === S.perfil?.activista_id);
const visiveis = () => (S.filtro === 'meus' && S.perfil?.papel === 'activista' ? minhas() : S.areas);

// ---------- fila offline ----------
const filaRegistos = () => LS.get('fila', []);
function porNaFila(reg) { const f = filaRegistos(); f.push(reg); LS.set('fila', f); }
let aSincronizar = false;
async function sincronizar(silencioso = false) {
  if (aSincronizar) return; aSincronizar = true;
  try { await sincronizarAgora(silencioso); } finally { aSincronizar = false; }
}
async function sincronizarAgora(silencioso) {
  const f = filaRegistos();
  if (!navigator.onLine) { actSync(); if (!silencioso) aviso('Sem rede. Os registos ficam guardados no telefone.', 'info'); return; }
  if (S.credPend && !(await autenticarPendente())) { actSync(); return; }
  let enviados = 0, erro = null;
  envio: for (const reg of f) {
    const { constr, fotos, ...linha } = reg;
    for (const [tipo, em] of Object.entries(fotos || {})) {   // fotografias da rega (entrada, rega, saída) primeiro
      const k = `${reg.id}-${tipo}`, caminho = `${S.perfil.id}/${k}.jpg`;
      let b = null; try { b = await FOTOS.ler(k); } catch {} b = b || S.fotosMem?.[k] || null;
      if (b) { const up = await sb.storage.from('rega-fotos').upload(caminho, b, { contentType: 'image/jpeg', upsert: true }); if (up.error) { erro = up.error.message; break envio; } }
      linha['foto_' + tipo] = b ? caminho : null; linha['foto_' + tipo + '_em'] = em;
    }
    const r1 = await sb.from('registos_rega').upsert(linha, { onConflict: 'id', ignoreDuplicates: true });
    if (r1.error) { erro = r1.error.message; break; }
    if (constr?.length) {
      const r2 = await sb.from('constrangimentos').upsert(constr.map((c) => ({ ...c, registo_id: reg.id })), { onConflict: 'id', ignoreDuplicates: true });
      if (r2.error) { erro = r2.error.message; break; }
    }
    // já está no servidor: passa da fila para "meus registos" no mesmo passo (não se perde nem se conta duas vezes)
    const m = LS.get('meusRegs', []); if (!m.some((x) => x.id === reg.id)) m.push({ id: reg.id, area_id: reg.area_id, activista_id: reg.activista_id, data: reg.data, ronda: reg.ronda, plantas_regadas: reg.plantas_regadas, teste: reg.teste });
    LS.set('meusRegs', m);
    LS.set('fila', filaRegistos().filter((x) => x.id !== reg.id));
    for (const tipo of Object.keys(fotos || {})) { try { await FOTOS.apagar(`${reg.id}-${tipo}`); } catch {} }
    enviados++;
  }
  if (!erro) {                                           // início do dia (pessoas presentes)
    for (const j of LS.get('filaJ', [])) {
      const r3 = await sb.from('jornadas').upsert(j, { onConflict: 'id', ignoreDuplicates: true });
      if (r3.error) { erro = r3.error.message; break; }
      LS.set('filaJ', LS.get('filaJ', []).filter((x) => x.id !== j.id));
    }
  }
  let alteradas = 0;
  if (!erro) {                                           // coordenadas e atribuições feitas no terreno
    for (const x of LS.get('filaAlt', [])) {
      // recontagem directa do M&E (v64–v66) deixou de existir: passa a ser feita pelos oficiais de M&E (18/10/2026, Valdo)
      if (x.tipo === 'recontagem') { LS.set('filaAlt', LS.get('filaAlt', []).filter((y) => y.id !== x.id)); aviso('A recontagem passou a ser feita pelos oficiais de M&E: a recontagem guardada neste telefone não foi enviada.', 'erro'); continue; }
      const r4 = x.tipo === 'coord'
        ? await sb.rpc('gravar_coordenada', { p_area: x.area_id, p_lat: x.lat, p_lon: x.lon, p_precisao: x.precisao })
        : x.tipo === 'zona' ? await sb.rpc('definir_zona', { p_area: x.area_id, p_zona: x.zona })
        : x.tipo === 'comunidade' ? await sb.rpc('definir_comunidade', { p_area: x.area_id, p_comunidade: x.comunidade })
        : x.tipo === 'limites' ? await sb.rpc('abrir_limites', { p_area: x.area_id, p_abrir: x.abrir })
        : x.tipo === 'aprovar' ? await sb.rpc('aprovar_poligono', { p_area: x.area_id, p_aprovar: x.aprovar })
        : x.tipo === 'poligono' ? await sb.rpc('gravar_poligono', { p_area: x.area_id, p_pontos: x.pontos, p_precisao: x.precisao, p_medido_em: x.medido_em })
        : x.tipo === 'planta' ? await sb.rpc('gravar_planta', { p_id: x.planta.id, p_area: x.area_id, p_n: x.planta.n, p_lat: x.planta.lat, p_lon: x.planta.lon, p_precisao: x.planta.precisao_m, p_em: x.planta.marcada_em, p_estado: x.planta.estado, p_cavaroda: x.planta.cavaroda, p_mulching: x.planta.mulching })
        : x.tipo === 'planta_est' ? await sb.rpc('estado_planta', { p_id: x.planta_id, p_estado: x.estado, p_cavaroda: x.cavaroda, p_mulching: x.mulching, p_em: x.em })
        : x.tipo === 'planta_rem' ? await sb.rpc('remover_planta', { p_id: x.planta_id, p_em: x.em })
        : await sb.rpc('atribuir_area', { p_area: x.area_id, p_activista: x.activista_id });
      if (r4.error && !r4.error.code) { erro = r4.error.message; break; }   // sem rede: fica na fila
      if (r4.error) aviso(`Não foi gravado (${x.area_id}): ${r4.error.message}`, 'erro');   // recusado pelo servidor: sai da fila
      LS.set('filaAlt', LS.get('filaAlt', []).filter((y) => y.id !== x.id)); alteradas++;
    }
  }
  if (!erro) erro = await enviarMonitorias();
  if (!erro) {                                           // chuva medida no pluviómetro
    for (const c of LS.get('filaChuva', [])) {
      let foto = null; try { foto = await FOTOS.ler(c.id); } catch {} foto = foto || S.fotosMem?.[c.id] || null;
      const caminho = `${S.perfil.id}/${c.id}.jpg`;
      if (foto) { const up = await sb.storage.from('chuva-fotos').upload(caminho, foto, { contentType: 'image/jpeg', upsert: true }); if (up.error) { erro = up.error.message; break; } }
      const r5 = await sb.from('chuva').upsert({ ...c, zona: c.zona ?? null, teste: !!c.teste, foto_path: foto ? caminho : null }, { onConflict: c.teste ? 'id' : 'data,comunidade,zona,activista_id' });
      if (r5.error && !r5.error.code) { erro = r5.error.message; break; }
      if (r5.error) aviso(`Chuva não gravada: ${r5.error.message}`, 'erro');
      LS.set('filaChuva', LS.get('filaChuva', []).filter((y) => y.id !== c.id));
      try { await FOTOS.apagar(c.id); } catch {}
    }
  }
  if (!erro) erro = await enviarQueimadas();
  if (!erro) erro = await enviarGestaoRecontagens();
  if (!erro) erro = await enviarRecontagens();
  if (!erro) { LS.set('ultimaSync', new Date().toISOString()); if (alteradas) await recarregarAreas(); await carregarEstado(); }
  actSync();
  if (!silencioso) aviso(erro ? 'Falhou o envio: ' + erro : enviados ? `${enviados} registo(s) enviados.` : 'Tudo sincronizado.', erro ? 'erro' : 'ok');
}
function actSync() {
  const n = filaRegistos().length + LS.get('filaJ', []).length + LS.get('filaAlt', []).length + LS.get('filaMon', []).length + LS.get('filaChuva', []).length + LS.get('filaQueim', []).length + LS.get('filaRec', []).length + LS.get('filaRecG', []).length, b = $('#h-sync'), u = LS.get('ultimaSync');
  b.textContent = n ? `${n} por enviar` : (u ? 'Sinc. ' + fmtHora(u) : 'Sincronizar');
  b.classList.toggle('pend', n > 0);
}

// ---------- dados ----------
// todos os pedidos saem ao mesmo tempo (antes eram uns atrás dos outros)
async function carregarTudo() {
  const [p, ac, ar, zs, est, lc, pc, qm, po, rc] = await Promise.all([
    sb.from('perfis').select('id,nome,papel,activista_id,titulo,gere_acessos,trocar_senha').eq('id', S.user.id).maybeSingle(),
    sb.from('activistas').select('id,nome,comunidade_principal,tecnico,supervisor,activo,equipa_tamanho').order('nome'),
    sb.from('areas').select(COLS_AREAS).eq('activa', true).order('comunidade').range(0, 4999),
    sb.from('zonas').select('comunidade,zona').order('zona'),
    sb.rpc('estado_ronda2'),
    sb.rpc('lista_comunidades'),
    sb.rpc('pontos_comunidades'),
    sb.from('queimadas').select('id,area_id,data,observacao,foto_path,registada_por,registada_em,plantas_afectadas,plantas_mortas,recontagem_em,vivas_recontadas,recontagem_obs').eq('removida', false).range(0, 9999),
    sb.from('pocos').select('id,codigo,comunidade,fonte,lat,lon,foto_path,observacao').range(0, 4999),
    sb.rpc('recontagens_lista'),
  ]);
  if (p.error) throw new Error(p.error.message);
  if (!p.data) throw new Error('Este utilizador não tem perfil na app. Fale com o gestor.');
  if (ac.error || ar.error) throw new Error((ac.error || ar.error).message);
  S.perfil = p.data; S.activistas = ac.data; S.areas = aplicarPendentes(ar.data);
  if (!zs.error) { S.zonas = zs.data; LS.set('zonas', S.zonas); }
  if (!lc.error && Array.isArray(lc.data)) { S.comunidades = lc.data; LS.set('comunidades', S.comunidades); }
  if (!po.error && Array.isArray(po.data)) { S.pocos = po.data; LS.set('pocos', S.pocos); }
  if (!qm.error && Array.isArray(qm.data)) { S.queimadas = qm.data; LS.set('queimadas', S.queimadas); }
  if (!rc.error && Array.isArray(rc.data)) { S.recont = rc.data; LS.set('recont', S.recont); }
  if (['me', 'gestor'].includes(p.data.papel)) oficiais().catch(() => {});   // lista dos oficiais no telefone (encaminhar sem rede)
  if (!pc.error && Array.isArray(pc.data)) { S.pontosCom = pc.data.map((x) => [x.comunidade, x.zona, +(+x.lat).toFixed(5), +(+x.lon).toFixed(5)]); LS.set('pontosCom', S.pontosCom); }
  // senha/PIN provisório dado pelo gestor: a pessoa escolhe outro (18/10/2026, Valdo)
  if (S.perfil.trocar_senha && !S.trocaAberta) setTimeout(() => ecraTrocarSenha(true), 400);
  // aviso ao entrar: ao M&E, recontagens por encaminhar e por validar; ao oficial, recontagens para fazer
  if (['me', 'oficial_me'].includes(S.perfil.papel) && !S.avisouRecontagem) {
    S.avisouRecontagem = true;
    const l = recontagens(), n = souOficial() ? recPorFazer().length : l.filter((r) => ['por_encaminhar', 'enviada'].includes(r.estado)).length;
    if (n) setTimeout(() => aviso(souOficial() ? `📋 ${n} ${n === 1 ? 'recontagem para fazer' : 'recontagens para fazer'}: veja no Hoje.` : `📋 ${n} ${n === 1 ? 'recontagem por encaminhar ou validar' : 'recontagens por encaminhar ou validar'}: veja no Hoje.`, 'info'), 1500);
  }
  S.visiveis = null;
  if (['tecnico', 'supervisor'].includes(S.perfil.papel)) {
    const [v] = await Promise.all([sb.rpc('meus_activistas'), carregarMonitoria()]);
    S.visiveis = v.error ? null : v.data; LS.set('visiveis', S.visiveis);
  }
  LS.set('perfil', S.perfil); LS.set('activistas', S.activistas); LS.set('areas', S.areas);
  await carregarEstado(est);
}
async function carregarEstado(pronto) {
  const { data, error } = pronto || await sb.rpc('estado_ronda2');
  if (error) return;
  S.estado = {}; for (const e of data) S.estado[e.area_id] = { u: e.ultima_rega, ronda: e.ronda_actual, feita: e.regada_na_ronda, n: e.regas_app || 0, pl: e.plantas_app || 0 };
  LS.set('estado', S.estado); LS.set('estadoEm', new Date().toISOString());
  if (souActivista() && S.perfil.activista_id) {        // registos da minha equipa (para a ronda funcionar sem rede)
    const r = await sb.from('registos_rega').select('id,area_id,activista_id,data,ronda,plantas_regadas,teste')
      .eq('activista_id', S.perfil.activista_id).eq('teste', false).gt('plantas_regadas', 0).range(0, 9999);
    if (!r.error) LS.set('meusRegs', r.data);
  } else if (PODE_REGAR.includes(S.perfil?.papel) && S.perfil?.id) {   // as minhas regas de teste dos últimos 14 dias
    const desde = new Date(Date.now() - 14 * 864e5).toLocaleDateString('sv-SE');
    const r = await sb.from('registos_rega').select('area_id,data').eq('teste', true).eq('user_id', S.perfil.id).gte('data', desde).range(0, 999);
    if (!r.error) { const t = {}; for (const x of r.data) if (!t[x.area_id] || x.data > t[x.area_id]) t[x.area_id] = x.data; LS.set('meusTestes', t); }
  }
  desenharMapa(); desenharLista();
}
function carregarDoTelefone() {
  S.perfil = LS.get('perfil'); S.visiveis = LS.get('visiveis'); S.zonas = LS.get('zonas', []); S.comunidades = LS.get('comunidades', []); S.pontosCom = LS.get('pontosCom', []); S.queimadas = LS.get('queimadas', []); S.recont = LS.get('recont', []); S.pocos = LS.get('pocos', []); S.activistas = LS.get('activistas', []); S.areas = LS.get('areas', []); S.estado = LS.get('estado', {}); S.mon = LS.get('mon', []); S.avisos = LS.get('avisos', []);
  return !!(S.perfil && S.areas.length);
}

// ---------- login ----------
// ---------- ecrã de entrada ----------
// C (campo): activista com PIN, técnico/supervisor com senha; B (escritório): restantes funções. O telefone lembra o último usado.
function modoEntrada(m) {
  if (m) { try { localStorage.setItem('rega.entrada', m); } catch {} } else { try { m = localStorage.getItem('rega.entrada'); } catch {} }
  m = ['activista', 'tecnico', 'escritorio'].includes(m) ? m : 'activista';
  S.modoEntrada = m;
  $('#l-campo').style.display = m === 'escritorio' ? 'none' : '';
  $('#l-escr').style.display = m === 'escritorio' ? '' : 'none';
  document.querySelectorAll('.l-seg button').forEach((b) => b.classList.toggle('on', b.dataset.m === m));
  $('#l-pinbox').style.display = m === 'activista' ? '' : 'none';
  $('#l-senhabox').style.display = m === 'tecnico' ? '' : 'none';
  $('#l-nota').textContent = m === 'tecnico' ? 'O utilizador e a senha são dados pelo gestor.' : 'O utilizador e o PIN são dados pelo gestor.';
  const h = new Date().getHours();
  $('#l-saud').textContent = h < 12 ? 'Bom dia.' : h < 18 ? 'Boa tarde.' : 'Boa noite.';
  msgEntrada('');
}
function msgEntrada(html) {
  const escr = S.modoEntrada === 'escritorio';
  $('#l-msg').innerHTML = escr ? '' : html; $('#le-msg').innerHTML = escr ? html : '';
}
function pinCaixas() {
  const v = $('#l-pin').value, foco = document.activeElement === $('#l-pin');
  document.querySelectorAll('.l-pin i').forEach((c, i) => { c.textContent = i < v.length ? '•' : ''; c.classList.toggle('cur', foco && i === Math.min(v.length, 5)); });
}
// Entrada sem rede (12/10/2026, Valdo): quem já entrou neste telefone pode voltar a entrar sem rede.
// O telefone guarda só uma impressão da senha/PIN (PBKDF2), nunca a senha. A ligação ao servidor faz-se quando houver rede.
const b64 = (u8) => btoa(String.fromCharCode(...u8)), deB64 = (t) => Uint8Array.from(atob(t), (c) => c.charCodeAt(0));
async function impressao(segredo, sal) {
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode(segredo), 'PBKDF2', false, ['deriveBits']);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt: sal, iterations: 150000 }, k, 256));
}
async function guardarAcessoOff(email, segredo) {
  try { const sal = crypto.getRandomValues(new Uint8Array(16)); LS.set('acessoOff', { email, sal: b64(sal), imp: b64(await impressao(segredo, sal)), perfil: S.perfil }); } catch {}
}
async function entrarSemRede(email, segredo) {
  const a = LS.get('acessoOff');
  if (!a || a.email !== email) return 'Sem rede. A primeira entrada neste telefone precisa de internet. Depois disso, pode entrar sem rede.';
  let ok = false; try { ok = b64(await impressao(segredo, deB64(a.sal))) === a.imp; } catch {}
  if (!ok) return S.modoEntrada === 'activista' ? 'Utilizador ou PIN errado.' : 'Utilizador ou senha errados.';
  S.perfil = a.perfil; LS.set('perfil', S.perfil); carregarDoTelefone(); S.perfil = a.perfil;
  S.credPend = { email, segredo };                        // só em memória: serve para ligar ao servidor quando houver rede
  mostrarApp(); aviso('Entrou sem rede. Os registos ficam no telefone e são enviados quando houver rede.', 'info');
  return null;
}
// liga ao servidor depois de uma entrada sem rede
async function autenticarPendente() {
  if (!S.credPend) return true;
  const { data, error } = await sb.auth.signInWithPassword({ email: S.credPend.email, password: S.credPend.segredo });
  if (error && /fetch|network|Failed/i.test(error.message)) return false;          // ainda sem rede
  if (error) { S.credPend = null; LS.del('acessoOff'); aviso('A senha ou o PIN mudou. Entre de novo com rede; os registos continuam guardados no telefone.', 'erro'); setTimeout(() => location.reload(), 4000); return false; }
  S.user = data.user; S.credPend = null;
  carregarTudo().then(() => { if ($('#e-hoje').classList.contains('on')) desenharHoje(); }).catch(() => {});
  return true;
}
const semRede = (e) => !navigator.onLine || /Failed to fetch|NetworkError|Load failed|network/i.test(e?.message || '');
async function entrar() {
  const m = S.modoEntrada || 'activista';
  const u = (m === 'escritorio' ? $('#le-user') : $('#l-user')).value.trim().toLowerCase();
  const pin = m === 'escritorio' ? $('#le-senha').value : m === 'tecnico' ? $('#l-senha').value : $('#l-pin').value;
  const email = u.includes('@') ? u : `${u}@${CFG.dominio}`;
  if (!u || !pin) { msgEntrada(`<div class="msg erro">${m === 'activista' ? 'Escreva o utilizador e o PIN.' : 'Escreva o utilizador e a senha.'}</div>`); return; }
  msgEntrada('<div class="msg info">A entrar…</div>');
  if (!navigator.onLine) { const e = await entrarSemRede(email, pin); if (e) msgEntrada(`<div class="msg erro">${esc(e)}</div>`); return; }
  const { data, error } = await sb.auth.signInWithPassword({ email, password: pin });
  if (error && semRede(error)) { const e = await entrarSemRede(email, pin); if (e) msgEntrada(`<div class="msg erro">${esc(e)}</div>`); return; }
  if (error) { msgEntrada(`<div class="msg erro">${/Invalid login/i.test(error.message) ? (m === 'activista' ? 'Utilizador ou PIN errado.' : 'Utilizador ou senha errados.') : esc(error.message)}</div>`); return; }
  S.user = data.user;
  try { await carregarTudo(); } catch (e) { msgEntrada(`<div class="msg erro">${esc(semRede(e) ? 'A rede caiu durante a entrada. Tente de novo.' : e.message)}</div>`); return; }
  if (S.perfil?.papel !== 'cliente') guardarAcessoOff(email, pin);
  const papel = S.perfil?.papel;                          // da próxima vez abre o ecrã desta função
  try { localStorage.setItem('rega.entrada', papel === 'activista' ? 'activista' : ['tecnico', 'supervisor', 'oficial_me'].includes(papel) ? 'tecnico' : 'escritorio'); } catch {}
  mostrarApp();
}
async function sair() {
  if (filaRegistos().length && !confirm('Há registos por enviar. Se sair agora, ficam no telefone e são enviados no próximo login deste utilizador. Sair?')) return;
  try { await sb.auth.signOut(); } catch {} ['perfil', 'emCurso', 'sugestao', 'meusRegs', 'jornada', 'hojeHtml', 'gestaoListar', 'mon', 'avisos', 'visiveis', 'meusTestes', 'chuvaTesteIds', 'chuvaFeita', 'rascChuva', 'rascMon', 'rascMedir', 'rascFotoRega', 'plantas', 'hojeEquipas', 'queimadas', 'rascQueim', 'recont', 'rascRec', 'oficiais'].forEach(LS.del); try { Object.keys(localStorage).filter((k) => k.startsWith('rega.painel.cache.')).forEach((k) => localStorage.removeItem(k)); } catch {}; location.reload();
}

// ---------- a minha senha / o meu PIN (18/10/2026, Valdo) ----------
// O gestor dá uma senha ou PIN provisório; ao entrar, a pessoa escolhe outro e o gestor deixa de o saber.
// No servidor fica só uma impressão cifrada (ninguém a consegue ler); no telefone também só uma impressão.
const PIN_FRACO = (v) => /^(\d)\1{5}$/.test(v) || ['123456', '654321', '012345', '123123'].includes(v);
function ecraTrocarSenha(obrig = false) {
  const pin = S.perfil?.papel === 'activista', o = pin ? 'PIN' : 'senha';
  const campo = (id, rot) => `<label>${rot}<input id="${id}" type="password" autocomplete="new-password" ${pin ? 'inputmode="numeric" maxlength="6"' : ''}></label>`;
  folha(`<h2>${pin ? (obrig ? 'Escolha o seu PIN' : 'Mudar o meu PIN') : (obrig ? 'Escolha a sua senha' : 'Mudar a minha senha')}</h2>
    ${obrig ? `<p>${pin ? 'O PIN que recebeu do gestor é provisório. Escolha agora um PIN só seu: o gestor deixa de o saber.' : 'A senha que recebeu do gestor é provisória. Escolha agora uma senha só sua: o gestor deixa de a saber.'}</p>` : `<p class="pequeno">${pin ? 'Só você vai saber o novo PIN. Se o esquecer, o gestor dá-lhe um provisório.' : 'Só você vai saber a nova senha. Se a esquecer, o gestor dá-lhe uma provisória.'}</p>`}
    <div class="msg info"><b>${pin ? 'Não use o PIN do banco, do telemóvel ou de outras contas.' : 'Não use a senha do banco, do e-mail ou de outras contas.'}</b></div>
    ${obrig ? '' : campo('ts-actual', pin ? 'PIN actual' : 'Senha actual')}
    ${campo('ts-nova', pin ? 'Novo PIN (6 números)' : 'Nova senha (8 ou mais caracteres)')}
    ${campo('ts-rep', pin ? 'Repetir o novo PIN' : 'Repetir a nova senha')}
    <button class="chip" id="ts-ver" type="button">Mostrar</button>
    <div id="ts-msg"></div>
    <button class="btn" id="ts-gravar">Gravar</button>${obrig ? '' : '<button class="btn sec" id="ts-cancelar">Cancelar</button>'}`);
  S.trocaAberta = true; S.trocaObrig = obrig; $('#folha-x').style.display = obrig ? 'none' : '';
  const sai = () => { S.trocaAberta = false; S.trocaObrig = false; $('#folha-x').style.display = ''; fecharFolha(); };
  if (!obrig) $('#ts-cancelar').onclick = sai;
  $('#ts-ver').onclick = () => { const t = $('#ts-nova').type === 'password' ? 'text' : 'password'; document.querySelectorAll('#folha-c input[type="password"], #folha-c input[data-v]').forEach((i) => { i.type = t; i.dataset.v = 1; }); $('#ts-ver').textContent = t === 'password' ? 'Mostrar' : 'Esconder'; };
  const erro = (t) => { $('#ts-msg').innerHTML = `<div class="msg erro">${esc(t)}</div>`; $('#ts-gravar').disabled = false; };
  $('#ts-gravar').onclick = async () => {
    const actual = obrig ? null : $('#ts-actual').value, nova = $('#ts-nova').value, rep = $('#ts-rep').value;
    if (pin ? !/^\d{6}$/.test(nova) : nova.length < 8) return erro(pin ? 'O PIN tem de ter 6 números.' : 'A senha tem de ter pelo menos 8 caracteres.');
    if (pin && PIN_FRACO(nova)) return erro('Esse PIN é fácil de adivinhar. Escolha outro.');
    if (nova !== rep) return erro(pin ? 'Os dois PIN não são iguais.' : 'As duas senhas não são iguais.');
    if (!obrig && !actual) return erro(pin ? 'Escreva o PIN actual.' : 'Escreva a senha actual.');
    if (!obrig && actual === nova) return erro(pin ? 'O novo PIN é igual ao actual.' : 'A nova senha é igual à actual.');
    if (!navigator.onLine) return erro(`Precisa de rede para mudar ${pin ? 'o PIN' : 'a senha'}.`);
    $('#ts-gravar').disabled = true; $('#ts-msg').innerHTML = '<div class="msg info">A gravar…</div>';
    try {
      const { data: u } = await sb.auth.getUser(); const email = u?.user?.email;
      if (!email) return erro('Sem sessão. Saia e entre de novo.');
      if (!obrig) {                                        // confirma o actual (e renova a sessão)
        const r = await sb.auth.signInWithPassword({ email, password: actual });
        if (r.error) return erro(semRede(r.error) ? 'Sem rede. Tente de novo.' : (pin ? 'O PIN actual está errado.' : 'A senha actual está errada.'));
      }
      const { error } = await sb.auth.updateUser({ password: nova });
      if (error) return erro(/different|same/i.test(error.message) ? (pin ? 'O novo PIN tem de ser diferente do anterior.' : 'A nova senha tem de ser diferente da anterior.') : semRede(error) ? 'Sem rede. Tente de novo.' : error.message);
      await sb.rpc('senha_trocada');
      S.perfil.trocar_senha = false; LS.set('perfil', S.perfil);
      if (S.perfil.papel !== 'cliente') await guardarAcessoOff(email, nova);   // a entrada sem rede passa a usar o novo
      sai(); aviso(pin ? 'PIN mudado. Só você o sabe.' : 'Senha mudada. Só você a sabe.', 'ok');
    } catch (e) { erro(semRede(e) ? 'Sem rede. Tente de novo.' : e.message); }
  };
}

// ---------- mapa ----------
let mapa, camada, rotulos, eu;
function iniciarMapa() {
  // rotate: o mapa pode rodar com a direcção (leaflet-rotate; sem o complemento fica como antes, norte em cima)
  mapa = L.map('mapa', { zoomControl: true, preferCanvas: true, rotate: true, rotateControl: false, touchRotate: false, compassBearing: false }).setView([-10.75, 40.45], 11);
  mapa.on('dragstart', () => { S.seguirCentro = false; S.euVisivel = false; });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(mapa);
  camada = L.layerGroup().addTo(mapa);
  rotulos = L.layerGroup().addTo(mapa);
  mapa.on('zoomend moveend', desenharRotulos);
  mapa.on('click', (e) => { if (S.regua) pontoRegua([e.latlng.lat, e.latlng.lng]); });
  if (navigator.geolocation) navigator.geolocation.watchPosition((p) => {
    S.pos = [p.coords.latitude, p.coords.longitude]; S.fix = { coords: p.coords, t: Date.now() };
    if (!eu) eu = L.circleMarker(S.pos, { radius: 9, color: '#fff', weight: 3, fillColor: '#1565c0', fillOpacity: 1 }).addTo(mapa);
    else eu.setLatLng(S.pos);
    // o ponto saiu do ecrã (a andar ou de carro): o mapa acompanha (16/10/2026, Dalmar). Se a pessoa arrastou o mapa
    // para outro lado (o ponto já estava fora), não puxa de volta.
    if (!S.seguir && $('#e-mapa').classList.contains('on')) {
      const dentro = mapa.getBounds().pad(-0.08).contains(S.pos);
      if (!dentro && S.euVisivel) mapa.panTo(S.pos, { animate: true });
      else S.euVisivel = dentro;
    }
    if (S.seguir) {
      if (S.seguirCentro) mapa.panTo(S.pos, { animate: true });
      // sem bússola (ou parada há 3 s): roda com a direcção do GPS quando a pessoa anda
      const h = p.coords.heading;
      if (Date.now() - (S.bussolaEm || 0) > 3000 && h != null && !isNaN(h) && (p.coords.speed || 0) > 0.5) rodarPara(h);
    }
  }, () => {}, { enableHighAccuracy: true, maximumAge: 10000 });
}
// ---------- mapa a rodar com a direcção, como no Google Maps (16/10/2026, Dalmar "M3" via Valdo) ----------
// Liga no botão 🧭: o mapa segue a pessoa e roda com a bússola do telefone (a direcção para onde aponta fica para cima).
// No iPhone a bússola precisa de autorização (pedida no toque). Sem bússola usa a direcção do GPS quando a pessoa anda.
const EV_ORI = 'ondeviceorientationabsolute' in window ? 'deviceorientationabsolute' : 'deviceorientation';
const podeRodar = () => !!(mapa && typeof mapa.setBearing === 'function');
function rodarPara(h) {
  if (!podeRodar() || h == null || isNaN(h)) return;
  const b = (360 - h) % 360, d = Math.abs(((b - (S.rumoMapa ?? 0)) + 540) % 360 - 180);
  if (d < 2) return;                                   // evita tremer com variações pequenas
  S.rumoMapa = b; mapa.setBearing(b);
}
function aoOrientar(e) {
  let h = null;
  if (e.webkitCompassHeading != null && !isNaN(e.webkitCompassHeading)) h = e.webkitCompassHeading;   // iPhone: graus a partir do norte, sentido horário
  else if (e.absolute && e.alpha != null) h = 360 - e.alpha;                                          // Android: alpha é anti-horário
  if (h == null) return;
  const ang = (screen.orientation && screen.orientation.angle) || window.orientation || 0;
  const t = Date.now(); if (t - (S.oriEm || 0) < 100) return; S.oriEm = t;
  S.bussolaEm = t; rodarPara((h + ang + 360) % 360);
}
async function alternarRodar() {
  if (!podeRodar()) { aviso('Este telefone não deixa rodar o mapa.', 'erro'); return; }
  if (S.seguir) {
    S.seguir = false; window.removeEventListener(EV_ORI, aoOrientar); S.rumoMapa = 0; mapa.setBearing(0); botaoRodar(); return;
  }
  if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
    try { if ((await DeviceOrientationEvent.requestPermission()) !== 'granted') aviso('Sem autorização para a bússola: o mapa roda com a direcção do GPS quando andar.', 'info'); }
    catch { aviso('Sem autorização para a bússola: o mapa roda com a direcção do GPS quando andar.', 'info'); }
  }
  S.seguir = true; S.seguirCentro = true; window.addEventListener(EV_ORI, aoOrientar);
  if (S.pos) mapa.setView(S.pos, Math.max(mapa.getZoom(), 16)); else lerGPS().then(() => mapa.setView(S.pos, 16)).catch((e) => aviso(e.message, 'erro'));
  botaoRodar();
}
function botaoRodar() { const b = $('#b-rodar'); if (!b) return; b.textContent = S.seguir ? '🧭 Norte' : '🧭 Rodar'; b.classList.toggle('on', !!S.seguir); }
// etiqueta em cada campo à vista (zoom ≥ 15): nome do produtor, código do campo e plantas vivas, sem tocar (16/10/2026, Dalmar; 18/10 Valdo: nome completo e PR)
const ZOOM_ROTULOS = 15, MAX_ROTULOS = 80;
function desenharRotulos() {
  if (!rotulos) return; rotulos.clearLayers();
  if (mapa.getZoom() < ZOOM_ROTULOS) return;
  const b = mapa.getBounds(), fa = $('#f-act')?.value, c = mapa.getCenter();
  // os campos mais perto do centro do ecrã primeiro; uma etiqueta que tapasse outra já posta não aparece
  // (aparece ao aproximar o mapa) — 18/10/2026, Valdo
  const L2 = visiveis().filter((a) => a.latitude != null && b.contains([a.latitude, a.longitude]) && !(fa && (fa === '__sem' ? a.activista_id : a.activista_id !== fa)))
    .sort((x, y) => mapa.distance(c, [x.latitude, x.longitude]) - mapa.distance(c, [y.latitude, y.longitude]));
  const postas = []; let n = 0;
  const tapa = (r) => postas.some((p) => r.left < p.right + 2 && r.right > p.left - 2 && r.top < p.bottom + 2 && r.bottom > p.top - 2);
  for (const a of L2) {
    if (n >= MAX_ROTULOS) break;
    const nome = String(a.produtor || '').trim() || '—';   // nome completo e código do campo (18/10/2026, Valdo)
    const pl = a.vivas > 0 ? `${num(a.vivas)} vivas` : `${num(a.instaladas || 0)} mudas`;
    const t = L.tooltip({ permanent: true, direction: 'top', offset: [0, -6], className: 'rot-campo', interactive: false })
      .setLatLng([a.latitude, a.longitude]).setContent(`${esc(nome)}<br><span class="rot-id">${esc(a.id)}</span> · <span>${pl}</span>`).addTo(rotulos);
    const el = t.getElement(), r = el && el.getBoundingClientRect();
    if (!r || !r.width) { n++; continue; }
    if (tapa(r)) { rotulos.removeLayer(t); continue; }
    postas.push(r); n++;
  }
}
// medir a distância entre campos, como no Google Maps (18/10/2026, Valdo): linha recta, funciona sem rede
let regua;
const fmtDist = (m) => (m < 1000 ? `${Math.round(m)} m` : `${(m / 1000).toLocaleString(LOC, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} km`);
function alternarRegua() {
  if (S.regua) return fecharRegua();
  S.regua = []; if (!regua) regua = L.layerGroup().addTo(mapa);
  $('#b-regua').classList.add('on'); $('#regua').style.display = ''; $('.legenda').style.display = 'none';
  desenharRegua();
}
function fecharRegua() {
  S.regua = null; if (regua) regua.clearLayers();
  $('#b-regua').classList.remove('on'); $('#regua').style.display = 'none'; $('.legenda').style.display = '';
}
function pontoRegua(ll, nome = '') { if (!S.regua) return false; S.regua.push({ ll, nome }); desenharRegua(); return true; }
function clicarCampo(e, a) {
  if (S.regua) { L.DomEvent.stopPropagation(e); pontoRegua([a.latitude, a.longitude], a.id); return; }
  abrirFicha(a.id);
}
function desenharRegua() {
  if (!regua || !S.regua) return;
  regua.clearLayers(); const P = S.regua; let tot = 0;
  if (P.length > 1) L.polyline(P.map((p) => p.ll), { color: '#111', weight: 3, dashArray: '6 6', interactive: false }).addTo(regua);
  P.forEach((p, i) => {
    if (i) tot += metros(P[i - 1].ll, p.ll);
    L.circleMarker(p.ll, { radius: 6, color: '#111', weight: 2, fillColor: '#fff', fillOpacity: 1, interactive: false }).addTo(regua);
    if (i) L.tooltip({ permanent: true, direction: 'right', offset: [8, 0], className: 'rot-regua', interactive: false }).setLatLng(p.ll).setContent(fmtDist(tot)).addTo(regua);
  });
  $('#rg-total').innerHTML = P.length < 2 ? `<b>${P.length ? 'Marque o segundo ponto' : 'Marque o primeiro ponto'}</b>`
    : `<b>Distância total</b> <b style="font-size:20px">${fmtDist(tot)}</b>`;
  $('#rg-pontos').textContent = P.some((p) => p.nome) ? P.map((p) => p.nome || '•').join(' → ') : '';
  $('#rg-desf').disabled = !P.length; $('#rg-limpar').disabled = !P.length;
}
function desenharMapa(enquadrar = false) {
  if (!camada) return;
  camada.clearLayers();
  const pts = [];
  const fa = $('#f-act')?.value;
  for (const a of visiveis()) {
    if (a.latitude == null) continue;
    if (fa && (fa === '__sem' ? a.activista_id : a.activista_id !== fa)) continue;
    const s = situacao(a);
    const borda = bordaAzul(a, s) ? BORDA.regado : BORDA.nunca;
    if (temPoligono(a)) L.polygon(a.poligono.map(([x, y]) => [y, x]), { color: borda, weight: 3, fillColor: COR[s.cod], fillOpacity: .25 })
      .on('click', (e) => clicarCampo(e, a)).addTo(camada);
    L.circleMarker([a.latitude, a.longitude], { radius: temPoligono(a) ? 5 : 8, color: temPoligono(a) ? '#fff' : borda, weight: temPoligono(a) ? 2 : 3, fillColor: COR[s.cod], fillOpacity: .95 })
      .on('click', (e) => clicarCampo(e, a)).addTo(camada);
    if (queimadaDe(a.id)) L.marker([a.latitude, a.longitude], { icon: L.divIcon({ className: 'ic-fogo', html: '🔥', iconSize: [22, 22], iconAnchor: [11, 26] }) })
      .on('click', (e) => clicarCampo(e, a)).addTo(camada);
    pts.push([a.latitude, a.longitude]);
  }
  // poços de água (18/10/2026, Valdo): em princípio estão em campos de produtores que regam sozinhos (fora do plano)
  for (const q of S.pocos || []) {
    L.marker([q.lat, q.lon], { icon: L.divIcon({ className: 'ic-poco', html: '💧', iconSize: [20, 20], iconAnchor: [10, 10] }) })
      .bindPopup(`<b>Poço ${esc(q.codigo)}</b><br>${esc(q.comunidade || '')}${q.fonte ? ' · ' + esc(q.fonte) : ''}${q.observacao ? '<br>' + esc(q.observacao) : ''}`)
      .on('click', () => { if (pontoRegua([q.lat, q.lon], q.codigo)) setTimeout(() => mapa.closePopup(), 0); }).addTo(camada);
  }
  if (enquadrar && pts.length) mapa.fitBounds(pts, { padding: [30, 30], maxZoom: 15 });
  desenharRotulos();
  $('#b-filtro').textContent = S.filtro === 'meus' ? 'As minhas' : 'Todas';
  $('#b-filtro').style.display = 'none';
  const ri = $('#ronda-info');
  if (souActivista() && S.perfil.activista_id) { ri.style.display = ''; ri.innerHTML = textoRonda(); } else ri.style.display = 'none';
}
function textoRonda() {
  const r = rondaInfo(S.perfil.activista_id);
  return `<b>Ronda ${r.n}</b> · ${r.feitas.size} de ${r.total} campos${r.total - r.feitas.size ? ` · faltam ${r.total - r.feitas.size}` : ''}`;
}

// ---------- lista ----------
// campos sem activista que este utilizador pode atribuir (supervisor e técnico: só os que vê; gestor: todos)
const porAtribuir = () => (S.perfil && ['gestor', 'supervisor', 'tecnico'].includes(S.perfil.papel) ? S.areas.filter((a) => !a.activista_id) : []);
const daMinhaEquipa = (id) => !S.visiveis || S.visiveis.includes(id);
// a proposta vem da base com o NOME do activista; devolve o id (null se não existir ou estiver desactivado)
function propostaId(a) {
  const p = a.activista_proposto; if (!p) return null;
  const t = S.activistas.find((x) => x.id === p || x.nome === p);
  return t && t.activo !== false ? t.id : null;
}
const activo = (t) => t.activo !== false;
function linhaAtribuir(a) {
  const prop = propostaId(a), ok = prop && daMinhaEquipa(prop);
  return `<div class="atrib">${prop ? `Proposta: <b>${esc(nomeAct(prop))}</b>${ok ? '' : ' <span class="pequeno">(fora da sua equipa)</span>'}` : '<span class="pequeno">Sem proposta</span>'}
    <div class="chips">${ok ? `<button class="chip on" data-acc="confirmar" data-id="${esc(a.id)}">✓ Confirmar proposta</button>` : ''}
    <button class="chip" data-acc="outro" data-id="${esc(a.id)}">Escolher outro</button></div></div>`;
}
function confirmarProposta(id) {
  const a = S.areas.find((x) => x.id === id), prop = a && propostaId(a); if (!prop) return;
  a.activista_id = prop; LS.set('areas', S.areas);
  porNaFilaAlt({ tipo: 'atrib', area_id: id, activista_id: a.activista_id });
  aviso(`${a.produtor}: atribuído a ${nomeAct(a.activista_id)}.`, 'ok'); desenharMapa(); desenharLista();
}
function desenharLista() {
  const amb = $('#f-ambito').value, com = $('#f-com').value, sit = $('#f-sit').value, txt = $('#f-txt').value.trim().toLowerCase();
  let L2 = (amb === 'meus' && S.perfil?.papel === 'activista') ? minhas() : S.areas;
  const fa = $('#f-act').value; if (fa) L2 = L2.filter((a) => (fa === '__sem' ? !a.activista_id : a.activista_id === fa));
  if (com) { const [c, z] = com.split('|'); L2 = L2.filter((a) => a.comunidade === c && (z === undefined || (a.zona || '') === z)); }
  if (txt) L2 = L2.filter((a) => (a.produtor || '').toLowerCase().includes(txt) || a.pr.toLowerCase().includes(txt));
  let linhas = L2.map((a) => ({ a, s: situacao(a), d: S.pos ? distCampo(a, S.pos) : null }));
  if (sit === 'nunca') linhas = linhas.filter((x) => !jaRegado(x.a));
  else if (sit === 'queimada') linhas = linhas.filter((x) => queimadaDe(x.a.id));
  else if (sit) linhas = linhas.filter((x) => x.s.cod === sit);
  linhas.sort((x, y) => (x.s.cod === 'feita') - (y.s.cod === 'feita') || (x.d ?? 1e12) - (y.d ?? 1e12));   // por regar primeiro
  $('#lista').innerHTML = (souActivista() && S.perfil.activista_id ? `<div class="msg info">${textoRonda()}</div>` : '') +
    (porAprovar().length ? `<div class="msg info">${porAprovar().length} medições de área por aprovar. <button class="chip" onclick="ecraPorAprovar()">Ver</button></div>` : '') +
    (porAtribuir().length && sit !== 'sem' ? `<div class="msg info">${porAtribuir().length} campos por atribuir. <button class="chip" onclick="$('#f-sit').value='sem';desenharLista()">Ver</button></div>` : '') +
    (sit ? `<div class="msg info">Filtro: ${esc($('#f-sit').selectedOptions[0]?.textContent || '')}. <button class="chip" onclick="$('#f-sit').value='';desenharLista()">← Ver todos os campos</button></div>` : '') +
    (['supervisor', 'gestor'].includes(S.perfil?.papel) ? `<button class="btn sec" onclick="ecraVoltarRega()">➕ Voltar a pôr um campo na rega</button>` : '') +
    `<p class="pequeno">${linhas.length} campos${S.pos ? ' · ordenados pela distância' : ''}</p>` +
    linhas.slice(0, 300).map(({ a, s, d }) => `<div class="item" data-id="${esc(a.id)}"><div>
      <div class="nome">${esc(a.produtor)}</div><div class="sub">${esc(a.pr)} · ${esc(a.comunidade)}${a.zona ? ' › ' + esc(a.zona) : ''} · ${plantasTxt(a)}${d != null ? ' · ' + (d < 1000 ? Math.round(d) + ' m' : (d / 1000).toFixed(1) + ' km') : ''}</div>
      </div>${eNovo(a) ? '<span class="tag t-novo">Novo na rega</span>' : ''}${queimadaDe(a.id) ? '<span class="tag t-fogo">🔥 Queimada</span>' : ''}<span class="tag t-${s.cod}">${s.txt}</span>${s.cod === 'sem' && podeAtribuir(a) ? linhaAtribuir(a) : ''}</div>`).join('') + (linhas.length > 300 ? '<p class="pequeno">Mostra os 300 mais próximos. Use os filtros.</p>' : '');
}

// ---------- mapa de plantas (15/10/2026, pedido do Dalmar; teste com gestor/director, supervisores e técnicos) ----------
// Cada muda fica com a sua coordenada (média das leituras do GPS durante uns segundos) e o estado: viva / seca / morta,
// cava-roda, mulching. Funciona sem rede: as plantas ficam no telefone (rega.plantas) e vão pela fila de alterações.
const PL_MEDIA_MS = 3000, PL_PREC = 10, PL_PERTO = 3;  // 3 s de leituras; aceita leituras até ±10 m; aviso se já há planta a < 3 m (16/10/2026, Nuro: estava lento)
const COR_PLANTA = { viva: '#2e7d32', seca: '#ef8f00', morta: '#c62828' };
let vigiaPlantas = null, travaPlantas = null;
const plantasLocais = (id) => ((LS.get('plantas', {}) || {})[id] || []);
function guardarPlantasLocais(id, lista) { const t = LS.get('plantas', {}) || {}; t[id] = lista; LS.set('plantas', t); }
function pararPlantas() {
  if (vigiaPlantas != null) { navigator.geolocation.clearWatch(vigiaPlantas); vigiaPlantas = null; }
  if (travaPlantas) { travaPlantas.release().catch(() => {}); travaPlantas = null; }
}
async function carregarPlantas(id) {
  if (!navigator.onLine) return;
  const r = await sb.from('plantas').select('id,n,lat,lon,precisao_m,estado,cavaroda,mulching,marcada_em,actualizada_em').eq('area_id', id).eq('removida', false).order('n').range(0, 4999);
  if (r.error || !Array.isArray(r.data)) return;
  let lista = r.data;                                       // o que ainda está na fila do telefone fica por cima do servidor
  for (const x of LS.get('filaAlt', [])) {
    if (x.area_id !== id) continue;
    if (x.tipo === 'planta' && !lista.some((p) => p.id === x.planta.id)) lista.push(x.planta);
    if (x.tipo === 'planta_est') lista = lista.map((p) => (p.id === x.planta_id ? { ...p, estado: x.estado, cavaroda: x.cavaroda, mulching: x.mulching } : p));
    if (x.tipo === 'planta_rem') lista = lista.filter((p) => p.id !== x.planta_id);
  }
  guardarPlantasLocais(id, lista);
}
function ecraPlantas(id) {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  pararVigia();
  S.pl = { id, pos: null, sel: null, lendo: false, leituras: [] };
  // começa com a última posição do GPS da app (se for recente), para não esperar por uma leitura nova
  if (S.fix && Date.now() - S.fix.t < 20000) S.pl.pos = { lat: S.fix.coords.latitude, lon: S.fix.coords.longitude, prec: Math.round(S.fix.coords.accuracy) };
  folha(`<h2>Mapa das plantas · ${esc(a.produtor)}</h2>
    <div class="msg info"><b>Teste.</b> Pare junto a cada muda e carregue em «Marcar planta aqui»: o telefone faz a média do GPS durante uns segundos. Para mudar o estado de uma muda, toque no ponto do desenho ou em «Planta mais perto de mim».</div>
    <div class="cartao"><div class="lin"><span>Precisão do GPS</span><b id="pl-prec">—</b></div><div id="pl-resumo"></div></div>
    <div id="pl-des" style="margin:8px 0"></div>
    <p class="pequeno" style="margin:0 0 6px"><span style="color:${COR_PLANTA.viva}">●</span> viva &nbsp; <span style="color:${COR_PLANTA.seca}">●</span> seca &nbsp; <span style="color:${COR_PLANTA.morta}">●</span> morta &nbsp; ◎ anel castanho = cava-roda e mulching (tracejado = só um) &nbsp; <span style="color:#1565c0">●</span> eu</p>
    <button class="btn" id="pl-marcar">📍 Marcar planta aqui</button>
    <button class="btn sec" id="pl-perto">Planta mais perto de mim</button>
    <div id="pl-sel"></div>
    <button class="btn sec" onclick="pararPlantas();abrirFicha('${esc(id)}')">Voltar à ficha</button>`);
  $('#pl-marcar').onclick = marcarPlanta;
  $('#pl-perto').onclick = () => {
    const p = S.pl.pos; if (!p) return aviso('Ainda sem posição do GPS.', 'erro');
    const l = plantasLocais(id); if (!l.length) return aviso('Ainda não há plantas marcadas neste campo.', 'info');
    let m = null, dm = Infinity; for (const x of l) { const d = metros([p.lat, p.lon], [x.lat, x.lon]); if (d < dm) { dm = d; m = x; } }
    selPlanta(m.id);
  };
  desenharPlantas(); mostrarGpsPlantas();
  carregarPlantas(id).then(() => { if (S.pl?.id === id && $('#pl-des')) desenharPlantas(); });
  (async () => { try { if (navigator.wakeLock) travaPlantas = await navigator.wakeLock.request('screen'); } catch {} })();
  if (!navigator.geolocation) return aviso('Este telefone não tem GPS disponível no navegador.', 'erro');
  vigiaPlantas = navigator.geolocation.watchPosition((p) => {
    if (!$('#pl-prec')) return pararPlantas();
    S.pl.pos = { lat: p.coords.latitude, lon: p.coords.longitude, prec: Math.round(p.coords.accuracy) };
    if (S.pl.lendo) S.pl.leituras.push(S.pl.pos);
    mostrarGpsPlantas();
    desenharPlantas();
  }, (e) => { const el = $('#pl-prec'); if (el) el.textContent = e.code === 1 ? 'sem autorização de localização' : 'sem sinal de GPS'; },
  { enableHighAccuracy: true, maximumAge: 0, timeout: 60000 });
}
// precisão do GPS e estado do botão: enquanto a precisão não chega a ±10 m, o botão diz que está a preparar o GPS
function mostrarGpsPlantas() {
  const p = S.pl?.pos, el = $('#pl-prec'), b = $('#pl-marcar'); if (!el || !p) return;
  el.textContent = `±${p.prec} m`; el.style.color = p.prec <= CFG.precisaoIdeal ? '#1b5e20' : p.prec <= PL_PREC ? '#ef8f00' : '#c62828';
  if (b && !S.pl.lendo) { const pronto = p.prec <= PL_PREC; b.disabled = !pronto; b.textContent = pronto ? '📍 Marcar planta aqui' : `A preparar o GPS… (±${p.prec} m)`; }
}
function desenharPlantas() {
  const P = S.pl; if (!P || !$('#pl-des')) return;
  const a = S.areas.find((x) => x.id === P.id) || {}, l = plantasLocais(P.id);
  const pol = temPoligono(a) ? a.poligono : [], todos = [...pol, ...l.map((x) => [x.lon, x.lat]), ...(P.pos ? [[P.pos.lon, P.pos.lat]] : [])];
  const v = { viva: 0, seca: 0, morta: 0 }; let cr = 0, mu = 0; for (const x of l) { v[x.estado] = (v[x.estado] || 0) + 1; if (x.cavaroda) cr++; if (x.mulching) mu++; }
  $('#pl-resumo').innerHTML = `<div class="lin"><span>Plantas marcadas</span><b>${num(l.length)}${a.instaladas ? ` <span class="pequeno">(base: ${num(a.instaladas)} plantadas)</span>` : ''}</b></div>
    <div class="lin"><span>Vivas · secas · mortas</span><b>${num(v.viva)} · ${num(v.seca)} · ${num(v.morta)}</b></div>
    <div class="lin"><span>Com cava-roda · com mulching</span><b>${num(cr)} · ${num(mu)}</b></div>`;
  if (!todos.length) { $('#pl-des').innerHTML = '<p class="pequeno">À espera do GPS…</p>'; return; }
  const m = emMetros(todos), xs = m.map((q) => q[0]), ys = m.map((q) => q[1]);
  const x0 = Math.min(...xs), y0 = Math.min(...ys), w = Math.max(20, Math.max(...xs) - x0), h = Math.max(20, Math.max(...ys) - y0), k = 280 / Math.max(w, h);
  const W = Math.round(20 + w * k), H = Math.round(20 + h * k);
  const pt = (q) => [10 + (q[0] - x0) * k, H - 10 - (q[1] - y0) * k];
  const mp = m.slice(pol.length, pol.length + l.length), r = Math.max(3, Math.min(7, k * 1.2));
  const poly = pol.length ? `<polygon points="${m.slice(0, pol.length).map((q) => pt(q).map((z) => z.toFixed(1)).join(',')).join(' ')}" fill="rgba(46,125,50,.12)" stroke="#1f5130" stroke-width="1.5"/>` : '';
  const pts = l.map((x, i) => { const [cx, cy] = pt(mp[i]), sel = P.sel === x.id, cuid = x.cavaroda && x.mulching ? 'stroke="#5d4037" stroke-width="2.5"' : x.cavaroda || x.mulching ? 'stroke="#5d4037" stroke-width="2" stroke-dasharray="2 2"' : '';
    return `<g onclick="selPlanta('${x.id}')" style="cursor:pointer"><circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${(r + 7).toFixed(1)}" fill="transparent"/>
      ${cuid ? `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${(r + 2.5).toFixed(1)}" fill="none" ${cuid}/>` : ''}
      <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r.toFixed(1)}" fill="${COR_PLANTA[x.estado] || '#777'}" ${sel ? 'stroke="#000" stroke-width="2"' : ''}/>
      ${sel ? `<text x="${(cx + r + 3).toFixed(1)}" y="${(cy - r - 2).toFixed(1)}" font-size="11" font-weight="700">${x.n}</text>` : ''}</g>`; }).join('');
  const eu = P.pos ? (() => { const [cx, cy] = pt(m[m.length - 1]); return `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="5" fill="#1565c0" stroke="#fff" stroke-width="1.5"/>`; })() : '';
  $('#pl-des').innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-height:340px;background:#eef4ea;border-radius:10px">${poly}${pts}${eu}</svg>`;
}
async function marcarPlanta() {
  const P = S.pl; if (!P || P.lendo) return;
  if (!P.pos) return aviso('Ainda sem posição do GPS. Espere uns segundos.', 'erro');
  P.lendo = true; P.leituras = [P.pos]; const b = $('#pl-marcar'); b.disabled = true; b.textContent = 'A ler o GPS… fique parado';
  await new Promise((ok) => setTimeout(ok, PL_MEDIA_MS));
  P.lendo = false; mostrarGpsPlantas(); if (b && !b.disabled) b.textContent = '📍 Marcar planta aqui';
  const boas = P.leituras.filter((x) => x.prec <= PL_PREC);
  if (!boas.length) return aviso(`Precisão fraca (±${P.pos.prec} m). Espere uns segundos e tente de novo.`, 'erro');
  let sw = 0, la = 0, lo = 0; for (const x of boas) { const wgt = 1 / Math.max(1, x.prec) ** 2; sw += wgt; la += x.lat * wgt; lo += x.lon * wgt; }
  const pos = { lat: la / sw, lon: lo / sw, prec: Math.min(...boas.map((x) => x.prec)) };
  const l = plantasLocais(P.id);
  let perto = null, dp = Infinity; for (const x of l) { const d = metros([pos.lat, pos.lon], [x.lat, x.lon]); if (d < dp) { dp = d; perto = x; } }
  if (perto && dp < PL_PERTO && !confirm(`Já há a planta nº ${perto.n} a ${Math.round(dp)} m. Marcar outra planta aqui?`)) { selPlanta(perto.id); return; }
  const pl = { id: crypto.randomUUID(), n: l.reduce((mx, x) => Math.max(mx, x.n || 0), 0) + 1, lat: pos.lat, lon: pos.lon, precisao_m: pos.prec,
    estado: 'viva', cavaroda: false, mulching: false, marcada_em: new Date().toISOString() };
  l.push(pl); guardarPlantasLocais(P.id, l);
  porNaFilaAlt({ tipo: 'planta', area_id: P.id, planta: pl });
  P.sel = pl.id; desenharPlantas(); mostrarPlanta();
  aviso(`Planta nº ${pl.n} marcada (±${pl.precisao_m} m).`, 'ok');
}
function selPlanta(pid) { if (!S.pl) return; S.pl.sel = pid; desenharPlantas(); mostrarPlanta(); }
function mostrarPlanta() {
  const P = S.pl, x = plantasLocais(P.id).find((y) => y.id === P.sel), el = $('#pl-sel'); if (!el) return;
  if (!x) { el.innerHTML = ''; return; }
  const d = P.pos ? metros([P.pos.lat, P.pos.lon], [x.lat, x.lon]) : null;
  el.innerHTML = `<div class="cartao" style="margin:8px 0"><h2 style="margin:0">Planta nº ${x.n}</h2>
    <p class="pequeno">Marcada ${fmtData(x.marcada_em.slice(0, 10))} ${fmtHora(x.marcada_em)} · ±${x.precisao_m ?? '?'} m${d != null ? ` · a ${Math.round(d)} m de si` : ''}</p>
    <label>Estado</label><div class="chips" id="ps-est">${['viva', 'seca', 'morta'].map((e) => `<button class="chip${x.estado === e ? ' on' : ''}" data-v="${e}">${{ viva: 'Viva', seca: 'Seca', morta: 'Morta' }[e]}</button>`).join('')}</div>
    <label>Cuidados</label><div class="chips" id="ps-cuid"><button class="chip${x.cavaroda ? ' on' : ''}" data-k="cavaroda">Cava-roda</button><button class="chip${x.mulching ? ' on' : ''}" data-k="mulching">Mulching</button></div>
    <button class="btn" onclick="gravarPlanta()">Gravar o estado desta planta</button>
    <button class="chip" onclick="removerPlanta()">Remover este ponto (marcado por engano)</button></div>`;
  document.querySelectorAll('#ps-est .chip').forEach((b) => b.onclick = () => document.querySelectorAll('#ps-est .chip').forEach((c) => c.classList.toggle('on', c === b)));
  document.querySelectorAll('#ps-cuid .chip').forEach((b) => b.onclick = () => b.classList.toggle('on'));
}
// muda a planta no telefone e na fila: se a planta ainda não foi enviada, muda o próprio pedido de criação
function mudarPlantaFila(pid, fn, tipoNovo) {
  const f = LS.get('filaAlt', []), cria = f.find((x) => x.tipo === 'planta' && x.planta.id === pid);
  if (cria) { const r = fn(cria); LS.set('filaAlt', r === null ? f.filter((x) => x !== cria && x.planta_id !== pid) : f); actSync(); return; }
  porNaFilaAlt(tipoNovo);
}
function gravarPlanta() {
  const P = S.pl, l = plantasLocais(P.id), x = l.find((y) => y.id === P.sel); if (!x) return;
  x.estado = document.querySelector('#ps-est .chip.on')?.dataset.v || 'viva';
  x.cavaroda = !!document.querySelector('#ps-cuid .chip.on[data-k=cavaroda]'); x.mulching = !!document.querySelector('#ps-cuid .chip.on[data-k=mulching]');
  const em = new Date().toISOString(); x.actualizada_em = em; guardarPlantasLocais(P.id, l);
  mudarPlantaFila(x.id, (c) => { Object.assign(c.planta, { estado: x.estado, cavaroda: x.cavaroda, mulching: x.mulching }); },
    { tipo: 'planta_est', area_id: P.id, planta_id: x.id, estado: x.estado, cavaroda: x.cavaroda, mulching: x.mulching, em });
  desenharPlantas(); mostrarPlanta(); aviso(`Planta nº ${x.n} gravada.`, 'ok');
}
function removerPlanta() {
  const P = S.pl, l = plantasLocais(P.id), x = l.find((y) => y.id === P.sel); if (!x) return;
  if (!confirm(`Remover o ponto da planta nº ${x.n}?`)) return;
  guardarPlantasLocais(P.id, l.filter((y) => y.id !== x.id));
  mudarPlantaFila(x.id, () => null, { tipo: 'planta_rem', area_id: P.id, planta_id: x.id, em: new Date().toISOString() });
  P.sel = null; desenharPlantas(); mostrarPlanta();
}

// ---------- medir a área andando à volta do campo (15/10/2026, Valdo) ----------
// Técnico (campos sem limite), supervisor e gestor. O GPS marca um ponto a cada 3 m andados (só com precisão até
// CFG.precisaoCoord); também se pode marcar à mão. Os pontos ficam no telefone (rascunho) e a medição envia-se
// pela fila de alterações quando houver rede.
const PASSO_MEDIR = 3;               // metros entre pontos automáticos
let vigiaMedir = null, travaEcra = null;
function pararMedicao() {
  if (vigiaMedir != null) { navigator.geolocation.clearWatch(vigiaMedir); vigiaMedir = null; }
  if (travaEcra) { travaEcra.release().catch(() => {}); travaEcra = null; }
}
const centroPontos = (P) => [P.reduce((s, p) => s + p[0], 0) / P.length, P.reduce((s, p) => s + p[1], 0) / P.length];
function emMetros(P) { const lat0 = centroPontos(P)[1] * Math.PI / 180; return P.map(([lo, la]) => [lo * Math.cos(lat0) * 111320, la * 110540]); }
function areaPontos(P) {
  if (!Array.isArray(P) || P.length < 3) return 0;
  const m = emMetros(P); let s = 0;
  for (let i = 0; i < m.length; i++) { const [x1, y1] = m[i], [x2, y2] = m[(i + 1) % m.length]; s += x1 * y2 - x2 * y1; }
  return Math.abs(s) / 2;
}
function perimetroPontos(P, fechar) {
  const m = emMetros(P); let s = 0;
  for (let i = 1; i < m.length; i++) s += Math.hypot(m[i][0] - m[i - 1][0], m[i][1] - m[i - 1][1]);
  if (fechar && m.length > 2) s += Math.hypot(m[0][0] - m[m.length - 1][0], m[0][1] - m[m.length - 1][1]);
  return s;
}
const textoArea = (m2) => m2 >= 10000 ? `${(m2 / 10000).toLocaleString(LOC, { maximumFractionDigits: 2 })} ha (${num(Math.round(m2))} m²)` : `${num(Math.round(m2))} m²`;
// simplifica o traçado (Douglas-Peucker, tolerância em metros) para não guardar milhares de pontos
function simplificar(P, tol = 1) {
  if (P.length < 4) return P;
  const m = emMetros(P), manter = new Array(P.length).fill(false); manter[0] = manter[P.length - 1] = true;
  const pilha = [[0, P.length - 1]];
  while (pilha.length) {
    const [i, j] = pilha.pop(); let dmax = 0, k = -1;
    const [x1, y1] = m[i], [x2, y2] = m[j], L = Math.hypot(x2 - x1, y2 - y1) || 1e-9;
    for (let t = i + 1; t < j; t++) { const d = Math.abs((x2 - x1) * (y1 - m[t][1]) - (x1 - m[t][0]) * (y2 - y1)) / L; if (d > dmax) { dmax = d; k = t; } }
    if (dmax > tol) { manter[k] = true; pilha.push([i, k], [k, j]); }
  }
  return P.filter((_, i) => manter[i]);
}
function desenhoPontos(P, pos) {
  const todos = pos ? [...P, pos] : P; if (!todos.length) return '';
  const m = emMetros(todos), xs = m.map((p) => p[0]), ys = m.map((p) => p[1]);
  const x0 = Math.min(...xs), y0 = Math.min(...ys), w = Math.max(10, Math.max(...xs) - x0), h = Math.max(10, Math.max(...ys) - y0), k = 180 / Math.max(w, h);
  const pt = ([x, y]) => `${(10 + (x - x0) * k).toFixed(1)},${(190 - (y - y0) * k).toFixed(1)}`;
  const linha = m.slice(0, P.length).map(pt).join(' ');
  return `<svg viewBox="0 0 200 200" width="100%" style="max-height:220px;background:#eef4ea;border-radius:10px" aria-hidden="true">
    ${P.length > 2 ? `<polygon points="${linha}" fill="rgba(46,125,50,.25)" stroke="#1f5130" stroke-width="2"/>` : `<polyline points="${linha}" fill="none" stroke="#1f5130" stroke-width="2"/>`}
    ${P.length ? `<circle cx="${pt(m[0]).split(',')[0]}" cy="${pt(m[0]).split(',')[1]}" r="5" fill="#d84315"/>` : ''}
    ${pos ? `<circle cx="${pt(m[m.length - 1]).split(',')[0]}" cy="${pt(m[m.length - 1]).split(',')[1]}" r="5" fill="#1565c0"/>` : ''}</svg>`;
}
function ecraMedir(id, r) {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  pararVigia();
  const rr = r && r.area_id === id ? r : (rascLer('rascMedir')?.area_id === id && rascLer('rascMedir')?.perfil === S.perfil?.id ? rascLer('rascMedir') : null);
  S.medir = { id, pts: rr?.pts || [], prec: null, pos: null, a_andar: false, melhor: rr?.melhor || null };
  const continuar = !!(r && r.a_andar);
  folha(`<h2>Medir a área · ${esc(a.produtor)}</h2>
    ${rr?.pts?.length ? `<div class="msg info">Medição recuperada: ${rr.pts.length} pontos já marcados. Continue de onde parou.</div>` : ''}
    <div class="msg info"><b>Como medir:</b> vá a um canto do campo e carregue em «Começar». Ande devagar pela borda, à volta do campo todo, até voltar ao ponto vermelho. O telefone marca pontos sozinho a cada ${PASSO_MEDIR} m. Nos cantos pode carregar em «Marcar canto». Mantenha a app aberta e o ecrã ligado.</div>
    <div class="cartao"><div class="lin"><span>Precisão do GPS</span><b id="md-prec">—</b></div>
      <div class="lin"><span>Pontos</span><b id="md-n">0</b></div>
      <div class="lin"><span>Distância andada</span><b id="md-per">0 m</b></div>
      <div class="lin"><span>Área até agora</span><b id="md-area">—</b></div></div>
    <div id="md-des" style="margin:8px 0"></div>
    <button class="btn" id="md-ir">▶ Começar</button>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin:6px 0"><button class="chip" id="md-canto">📍 Marcar canto</button><button class="chip" id="md-desf">↶ Desfazer último ponto</button><button class="chip" id="md-limpar">Recomeçar</button></div>
    <button class="btn" id="md-fim" disabled>✓ Terminar e gravar a área</button>
    <button class="btn sec" onclick="pausarMedicao();pararMedicao();abrirFicha('${esc(id)}')">Sair (os pontos ficam guardados no telefone)</button>`);
  $('#md-ir').onclick = () => (S.medir.a_andar ? pausarMedicao() : comecarMedicao());
  $('#md-canto').onclick = () => { const p = S.medir.pos; if (!p) return aviso('Ainda sem posição do GPS.', 'erro'); if (p.prec > CFG.precisaoCoord) return aviso(`Precisão fraca (±${p.prec} m). Espere uns segundos.`, 'erro'); juntarPonto(p, true); };
  $('#md-desf').onclick = () => { S.medir.pts.pop(); guardarMedicao(); mostrarMedicao(); };
  $('#md-limpar').onclick = () => { if (S.medir.pts.length && !confirm('Apagar os pontos marcados e recomeçar?')) return; S.medir.pts = []; S.medir.melhor = null; guardarMedicao(); mostrarMedicao(); };
  $('#md-fim').onclick = terminarMedicao;
  mostrarMedicao();
  if (!navigator.geolocation) return aviso('Este telefone não tem GPS disponível no navegador.', 'erro');
  if (continuar) comecarMedicao();
  vigiaMedir = navigator.geolocation.watchPosition((p) => {
    if (!$('#md-prec')) return pararMedicao();
    const ponto = { lon: p.coords.longitude, lat: p.coords.latitude, prec: Math.round(p.coords.accuracy) };
    S.medir.pos = ponto;
    if (S.medir.a_andar && ponto.prec <= CFG.precisaoCoord) {
      const u = S.medir.pts[S.medir.pts.length - 1];
      if (!u || metros([u[1], u[0]], [ponto.lat, ponto.lon]) >= PASSO_MEDIR) juntarPonto(ponto, false);
    }
    mostrarMedicao();
  }, (e) => { const el = $('#md-prec'); if (el) el.textContent = e.code === 1 ? 'sem autorização de localização' : 'sem sinal de GPS'; },
  { enableHighAccuracy: true, maximumAge: 0, timeout: 60000 });
}
async function comecarMedicao() {
  S.medir.a_andar = true; guardarMedicao(); $('#md-ir').textContent = '⏸ Pausar';
  try { if (navigator.wakeLock) travaEcra = await navigator.wakeLock.request('screen'); } catch {}
  const p = S.medir.pos; if (p && p.prec <= CFG.precisaoCoord && !S.medir.pts.length) juntarPonto(p, true);
}
function pausarMedicao() { S.medir.a_andar = false; guardarMedicao(); $('#md-ir').textContent = '▶ Continuar'; if (travaEcra) { travaEcra.release().catch(() => {}); travaEcra = null; } }
function juntarPonto(p, manual) {
  S.medir.pts.push([+p.lon.toFixed(7), +p.lat.toFixed(7)]);
  S.medir.melhor = Math.max(S.medir.melhor || 0, p.prec);         // pior precisão usada (para registo)
  guardarMedicao(); mostrarMedicao();
  if (manual && navigator.vibrate) navigator.vibrate(60);
}
const guardarMedicao = () => rascGuardar('rascMedir', { area_id: S.medir.id, perfil: S.perfil?.id, pts: S.medir.pts, melhor: S.medir.melhor, a_andar: !!S.medir.a_andar });
function mostrarMedicao() {
  const M = S.medir; if (!M || !$('#md-n')) return;
  const el = $('#md-prec');
  if (M.pos) { el.textContent = `±${M.pos.prec} m`; el.style.color = M.pos.prec <= CFG.precisaoIdeal ? '#1b5e20' : M.pos.prec <= CFG.precisaoCoord ? '#ef8f00' : '#c62828'; }
  $('#md-n').textContent = M.pts.length;
  $('#md-per').textContent = `${num(Math.round(M.pts.length > 1 ? perimetroPontos(M.pts, false) : 0))} m`;
  $('#md-area').textContent = M.pts.length >= 3 ? textoArea(areaPontos(M.pts)) : '—';
  $('#md-des').innerHTML = desenhoPontos(M.pts, M.pos ? [M.pos.lon, M.pos.lat] : null);
  $('#md-fim').disabled = M.pts.length < 4;
}
function terminarMedicao() {
  const M = S.medir; if (M.pts.length < 4) return;
  pausarMedicao();
  const P = simplificar(M.pts, 1), area = areaPontos(P), a = S.areas.find((x) => x.id === M.id);
  const fim = M.pts[M.pts.length - 1], dFecho = metros([fim[1], fim[0]], [M.pts[0][1], M.pts[0][0]]);
  folha(`<h2>Área medida · ${esc(a.produtor)}</h2>
    ${dFecho > 20 ? `<div class="msg erro">O último ponto está a ${Math.round(dFecho)} m do início. Se não deu a volta completa, volte e continue a medir.</div>` : ''}
    <div class="cartao"><div class="lin"><span>Área</span><b>${textoArea(area)}</b></div>
      <div class="lin"><span>Perímetro</span><b>${num(Math.round(perimetroPontos(P, true)))} m</b></div>
      <div class="lin"><span>Pontos</span><b>${P.length}</b></div>
      ${a.vivas ? `<div class="lin"><span>Plantas vivas na base</span><b>${num(a.vivas)} (${(a.vivas / (area / 10000)).toLocaleString(LOC, { maximumFractionDigits: 0 })} por ha)</b></div>` : ''}</div>
    ${desenhoPontos(P)}
    <button class="btn" onclick="gravarMedicao()">Gravar esta área</button>
    <button class="btn sec" onclick="ecraMedir('${esc(M.id)}')">Voltar e continuar a medir</button>`);
  S.medir.final = P;
}
function gravarMedicao() {
  const M = S.medir, P = M.final, a = S.areas.find((x) => x.id === M.id); if (!P || !a) return;
  const area = Math.round(areaPontos(P) * 10) / 10, proposta = S.perfil.papel === 'activista', quando = new Date().toISOString();
  if (proposta) { a.poligono_proposto = P; a.area_m2_proposta = area; a.proposta_em = quando; }   // activista: fica por aprovar
  else { a.poligono = P; a.area_m2 = area; a.limites_abertos = false; a.poligono_proposto = null; if (a.latitude == null) { const c = centroPontos(P); a.latitude = c[1]; a.longitude = c[0]; } }
  LS.set('areas', S.areas);
  porNaFilaAlt({ tipo: 'poligono', area_id: a.id, pontos: P, area_m2: area, precisao: M.melhor || null, medido_em: quando, proposta });
  LS.del('rascMedir'); S.medir = null;
  desenharMapa(true); desenharLista();
  abrirFicha(a.id, `<div class="msg ok">${proposta ? 'Área enviada para aprovação' : 'Área gravada'}: ${textoArea(area)}${navigator.onLine ? '' : ' (no telefone; é enviada quando houver rede)'}.</div>`);
}
// ---------- campos fora do plano que voltam à rega (14/10/2026, Nuro / Valdo) ----------
// O servidor tem as áreas do Controlo_Rega_Areas com REGA = NÃO (e as retiradas a 12/10) com activa = false.
// Não vêm para o telefone: só se procuram quando o supervisor ou o gestor abre este ecrã (precisa de rede).
const eNovo = (a) => a.reactivada_em && Date.now() - new Date(a.reactivada_em) < 14 * 864e5;
function ecraVoltarRega() {
  folha(`<h2>Voltar a pôr um campo na rega</h2>
    <p class="pequeno">Campos que estão fora do plano de rega. Procure pelo nome do produtor ou pelo PR (pelo menos 3 letras). Precisa de rede.</p>
    <input id="vr-txt" type="search" placeholder="Nome do produtor ou PR" autocomplete="off">
    <div id="vr-res" style="margin-top:8px"></div>
    <button class="btn sec" onclick="fecharFolha()">Fechar</button>`);
  let t; $('#vr-txt').oninput = () => { clearTimeout(t); t = setTimeout(procurarForaPlano, 400); };
  $('#vr-txt').focus();
}
async function procurarForaPlano() {
  const q = $('#vr-txt').value.trim(), el = $('#vr-res'); if (!el) return;
  if (q.length < 3) { el.innerHTML = ''; return; }
  if (!navigator.onLine) { el.innerHTML = '<div class="msg info">Sem rede. Esta procura precisa de internet.</div>'; return; }
  el.innerHTML = '<p class="pequeno">A procurar…</p>';
  const r = await sb.rpc('areas_fora_plano', { p_txt: q });
  if ($('#vr-txt')?.value.trim() !== q) return;
  if (r.error) { el.innerHTML = `<div class="msg erro">${esc(r.error.message)}</div>`; return; }
  const L = r.data || [];
  if (!L.length) { el.innerHTML = '<div class="msg info">Nenhum campo fora do plano com esse nome ou PR. Se o campo existe, envie o PR ao gestor.</div>'; return; }
  S.foraPlano = L;
  el.innerHTML = `<p class="pequeno">${L.length === 40 ? 'Primeiros 40 resultados. Escreva mais letras para afinar.' : L.length + ' campos'}</p>` + L.map((a, i) => `<div class="cartao" style="margin:6px 0;padding:10px 12px">
    <div class="nome"><b>${esc(a.produtor || '—')}</b></div>
    <div class="sub pequeno">${esc(a.pr)} · ${esc(a.comunidade)}${a.zona ? ' › ' + esc(a.zona) : ''} · ${a.vivas != null ? num(a.vivas) + ' vivas' : '—'}${a.instaladas != null ? ' de ' + num(a.instaladas) + ' plantadas' : ''}${a.data_plantio ? ' · plantio ' + fmtData(a.data_plantio) : ''}</div>
    <div class="sub pequeno">${a.agua_origem === 'COM' ? 'Na base: tinha água' : a.agua_origem === 'SEM' ? 'Na base: sem água' : ''}${a.n_regas_origem ? ` · ${a.n_regas_origem} regas antes${a.ultima_rega_origem ? ' (última ' + fmtData(a.ultima_rega_origem) + ')' : ''}` : ''}${a.activista_origem ? ' · activista: ' + esc(a.activista_origem) : ''}${a.tem_coord ? '' : ' · <b>sem coordenada</b>'}</div>
    ${a.motivo_saida ? `<div class="sub pequeno">Saiu da rega: ${esc(a.motivo_saida)}</div>` : ''}
    <button class="chip" style="margin-top:6px" onclick="confirmarVoltaRega(${i})">Voltar a regar</button></div>`).join('');
}
function confirmarVoltaRega(i) {
  const a = S.foraPlano[i];
  folha(`<h2>${esc(a.produtor || a.pr)}</h2><p class="pequeno">${esc(a.pr)} · ${esc(a.comunidade)} · ${a.vivas != null ? num(a.vivas) + ' vivas' : '—'}</p>
    <p>Este campo volta à lista de rega a partir de agora.</p>
    <label>Motivo (opcional)<textarea id="vr-motivo" rows="2" placeholder="Ex.: o poço secou"></textarea></label>
    <button class="btn" id="vr-ok" onclick="voltarRega(${i})">Voltar a regar</button><button class="btn sec" onclick="ecraVoltarRega()">Cancelar</button>`);
}
async function voltarRega(i) {
  const a = S.foraPlano[i]; if (!navigator.onLine) return aviso('Sem rede. Tente quando houver rede.', 'erro');
  $('#vr-ok').disabled = true;
  const r = await sb.rpc('voltar_a_regar', { p_area: a.id, p_motivo: $('#vr-motivo').value.trim() || null });
  if (r.error) { $('#vr-ok').disabled = false; return aviso(r.error.message, 'erro'); }
  await recarregarAreas(); await carregarEstado().catch(() => {});
  aviso(`${a.produtor || a.pr} voltou à rega.${r.data?.activista_id ? '' : ' Falta atribuir o activista.'}`, 'ok');
  if (S.areas.some((x) => x.id === a.id)) abrirFicha(a.id); else fecharFolha();
  desenharLista(); desenharMapa(true);
}
// ---------- ficha do campo ----------
function folha(html) {
  if (S.trocaObrig && !html.includes('id="ts-nova"')) return;   // escolher a senha/PIN vem primeiro (18/10/2026)
  S.trocaAberta = false; $('#folha-x').style.display = ''; $('#folha-c').innerHTML = html; $('#folha').classList.add('on');
}
function fecharFolha() { pararVigia(); $('#folha').classList.remove('on'); }
// ---------- coordenada e atribuição de campos (técnico, supervisor, gestor) ----------
const PODE_COORD = ['tecnico', 'supervisor', 'gestor'];
const podeAtribuir = (a) => ['gestor', 'supervisor'].includes(S.perfil.papel) || (S.perfil.papel === 'tecnico' && !a.activista_id);
function botoesCampo(a) {
  let h = '';
  // depois de gravadas, coordenada e área ficam fechadas; só o gestor corrige ou volta a abrir (15/10/2026, Nuro/Valdo)
  const gestor = S.perfil.papel === 'gestor', aberto = gestor || a.limites_abertos;
  // área medida pelo activista à espera de aprovação (técnico, supervisor ou gestor aprovam; 15/10/2026, Valdo)
  if (a.poligono_proposto && PODE_COORD.includes(S.perfil.papel)) h += cartaoProposta(a);
  if (S.perfil.papel === 'activista' && a.activista_id === S.perfil.activista_id && (!temPoligono(a) || a.limites_abertos || a.poligono_proposto))
    h += a.poligono_proposto ? `<div class="msg info">Área medida: ${textoArea(a.area_m2_proposta || areaPontos(a.poligono_proposto))}. À espera de aprovação do técnico ou do supervisor.</div>`
      : `<button class="btn sec" onclick="ecraMedir('${esc(a.id)}')">📐 ${temPoligono(a) ? 'Medir a área de novo (andar à volta)' : 'Medir a área (andar à volta do campo)'}</button>`;
  if (PODE_COORD.includes(S.perfil.papel) && (a.latitude == null || aberto))
    h += `<button class="btn sec" onclick="ecraCoordenada('${esc(a.id)}')">📍 ${a.latitude == null ? 'Gravar a coordenada deste campo' : 'Corrigir a coordenada (estou no campo)'}</button>`;
  if (PODE_COORD.includes(S.perfil.papel)) { const np = plantasLocais(a.id).length;
    h += `<button class="btn sec" onclick="ecraPlantas('${esc(a.id)}')">🌴 Mapa das plantas${np ? ` (${np})` : ''} · teste</button>`; }
  if (PODE_COORD.includes(S.perfil.papel) && (!temPoligono(a) || aberto))
    h += `<button class="btn sec" onclick="ecraMedir('${esc(a.id)}')">📐 ${temPoligono(a) ? 'Medir a área de novo (andar à volta)' : 'Medir a área (andar à volta do campo)'}</button>`;
  if (PODE_REGAR.includes(S.perfil.papel)) h += `<button class="btn sec" onclick="ecraQueimada('${esc(a.id)}')">🔥 ${queimadaDe(a.id) ? 'Registar outra queimada' : 'Marcar queimada nesta machamba'}</button>`;
  if (podeAtribuir(a)) h += `<button class="btn sec" onclick="ecraAtribuir('${esc(a.id)}')">👤 ${a.activista_id ? 'Mudar o activista deste campo' : 'Atribuir a um activista'}</button>`;
  if (['gestor', 'supervisor', 'tecnico'].includes(S.perfil.papel)) h += `<button class="btn sec" onclick="ecraComunidade('${esc(a.id)}')">🏘 Mudar a comunidade</button>`;
  if (['gestor', 'supervisor'].includes(S.perfil.papel) && zonasDe(a.comunidade).length) h += `<button class="btn sec" onclick="ecraZona('${esc(a.id)}')">🗂 ${a.zona ? 'Mudar a zona' : 'Definir a zona'}</button>`;
  if (gestor && (a.latitude != null || temPoligono(a)))
    h += a.limites_abertos ? `<button class="btn sec" onclick="mudarLimites('${esc(a.id)}', false)">🔒 Fechar a correcção da coordenada e da área</button>`
      : `<button class="btn sec" onclick="mudarLimites('${esc(a.id)}', true)">🔓 Deixar o supervisor/técnico corrigir a coordenada e medir de novo</button>`;
  return h;
}
function cartaoProposta(a) {
  return `<div class="cartao" style="border-left:4px solid #0b6e8a"><h3 style="margin:0 0 6px;font-size:15px">Área medida pelo activista — por aprovar</h3>
    <div class="lin"><span>Área</span><b>${textoArea(a.area_m2_proposta || areaPontos(a.poligono_proposto))}</b></div>
    ${a.proposta_em ? `<div class="lin"><span>Medida em</span><b>${fmtData(String(a.proposta_em).slice(0, 10))}</b></div>` : ''}
    ${a.vivas ? `<div class="lin"><span>Plantas vivas na base</span><b>${num(a.vivas)} (${(a.vivas / ((a.area_m2_proposta || areaPontos(a.poligono_proposto)) / 10000)).toLocaleString(LOC, { maximumFractionDigits: 0 })} por ha)</b></div>` : ''}
    ${desenhoPontos(a.poligono_proposto)}
    <div style="display:flex;gap:8px;margin-top:8px"><button class="btn" style="margin:0" onclick="aprovarMedicao('${esc(a.id)}', true)">✓ Aprovar</button><button class="btn sec" style="margin:0" onclick="aprovarMedicao('${esc(a.id)}', false)">✗ Recusar</button></div>
    ${temPoligono(a) && !a.limites_abertos ? '<p class="pequeno">Este campo já tem limite: só o gestor pode substituí-lo.</p>' : ''}</div>`;
}
function aplicarAprovacao(a, sim) {
  if (sim && a.poligono_proposto) {
    a.poligono = a.poligono_proposto; a.area_m2 = a.area_m2_proposta || areaPontos(a.poligono_proposto); a.limites_abertos = false;
    if (a.latitude == null) { const c = centroPontos(a.poligono); a.latitude = c[1]; a.longitude = c[0]; }
  }
  a.poligono_proposto = null; a.area_m2_proposta = null; a.proposta_em = null;
}
function aprovarMedicao(id, sim) {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  if (sim && temPoligono(a) && !a.limites_abertos && S.perfil.papel !== 'gestor') return aviso('Este campo já tem limite. Só o gestor pode substituí-lo.', 'erro');
  if (!sim && !confirm('Recusar esta medição? O activista terá de medir de novo.')) return;
  aplicarAprovacao(a, sim); LS.set('areas', S.areas);
  porNaFilaAlt({ tipo: 'aprovar', area_id: id, aprovar: sim });
  desenharMapa(true); desenharLista();
  abrirFicha(id, `<div class="msg ok">${sim ? 'Medição aprovada: o limite do campo já vale.' : 'Medição recusada.'}</div>`);
}
const porAprovar = () => (S.perfil && PODE_COORD.includes(S.perfil.papel) ? S.areas.filter((a) => a.poligono_proposto) : []);
function ecraPorAprovar() {
  const L = porAprovar();
  folha(`<h2>Medições de área por aprovar</h2>${L.length ? L.map((a) => `<div class="item" onclick="abrirFicha('${esc(a.id)}')"><div><div class="nome">${esc(a.produtor)}</div>
    <div class="sub">${esc(a.pr)} · ${esc(a.comunidade)} · ${esc(nomeAct(a.activista_id))} · ${textoArea(a.area_m2_proposta || areaPontos(a.poligono_proposto))}</div></div></div>`).join('') : '<p class="pequeno">Nada por aprovar.</p>'}
    <button class="btn sec" onclick="fecharFolha()">Fechar</button>`);
}
function mudarLimites(id, abrir) {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  a.limites_abertos = abrir; LS.set('areas', S.areas); porNaFilaAlt({ tipo: 'limites', area_id: id, abrir });
  abrirFicha(id, `<div class="msg ok">${abrir ? 'O supervisor e o técnico já podem corrigir a coordenada e medir a área deste campo. Fecha de novo depois de gravarem.' : 'Correcção fechada.'}</div>`);
}
// mudar a comunidade do campo (15/10/2026, Nuro/Valdo): técnico, supervisor e gestor; a zona volta a "por definir"
function ecraComunidade(id) {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  const lista = [...new Set([...(S.comunidades || []), ...S.areas.map((x) => x.comunidade)].filter(Boolean))].sort((x, y) => x.localeCompare(y));
  folha(`<h2>${esc(a.produtor)}</h2><p class="pequeno">${esc(a.pr)} · comunidade actual: <b>${esc(a.comunidade)}</b>${a.zona ? ' › ' + esc(a.zona) : ''}</p>
    <label>Nova comunidade<select id="cm-com">${lista.map((c) => `<option ${c === a.comunidade ? 'selected' : ''}>${esc(c)}</option>`).join('')}</select></label>
    <p class="pequeno">Mude só se o campo fica noutra comunidade. ${zonasDe(a.comunidade).length || lista.some((c) => zonasDe(c).length) ? 'A zona volta a ficar por definir.' : ''}</p>
    <button class="btn" onclick="gravarComunidade('${esc(id)}')">Gravar</button><button class="btn sec" onclick="abrirFicha('${esc(id)}')">Cancelar</button>`);
}
function gravarComunidade(id) {
  const a = S.areas.find((x) => x.id === id), c = $('#cm-com').value; if (!a || !c) return;
  if (c === a.comunidade) return abrirFicha(id);
  a.comunidade = c; a.zona = null; LS.set('areas', S.areas);
  porNaFilaAlt({ tipo: 'comunidade', area_id: id, comunidade: c });
  desenharLista(); desenharMapa(true);
  if (zonasDe(c).length) return ecraZona(id);
  abrirFicha(id, `<div class="msg ok">Comunidade mudada para ${esc(c)}.</div>`);
}
// zonas dentro de uma comunidade (ex.: Palma › Incularino)
const zonasDe = (com) => (Array.isArray(S.zonas) ? S.zonas : []).filter((z) => z.comunidade === com).map((z) => z.zona);
function ecraZona(id) {
  const a = S.areas.find((x) => x.id === id);
  folha(`<h2>${esc(a.produtor)}</h2><p class="pequeno">${esc(a.pr)} · ${esc(a.comunidade)} · activista: <b>${esc(nomeAct(a.activista_id))}</b></p>
    <label>Zona<select id="z-zona"><option value="">(por definir)</option>${zonasDe(a.comunidade).map((z) => `<option ${z === a.zona ? 'selected' : ''}>${esc(z)}</option>`).join('')}</select></label>
    <button class="btn" onclick="gravarZona('${esc(id)}')">Gravar</button><button class="btn sec" onclick="abrirFicha('${esc(id)}')">Cancelar</button>`);
}
function gravarZona(id) {
  const a = S.areas.find((x) => x.id === id), z = $('#z-zona').value || null;
  a.zona = z; LS.set('areas', S.areas);
  porNaFilaAlt({ tipo: 'zona', area_id: id, zona: z }); desenharLista();
  abrirFicha(id, `<div class="msg ok">Zona ${z ? 'definida: ' + esc(z) : 'retirada'}.${navigator.onLine ? '' : ' Será enviada quando houver rede.'}</div>`);
}
function porNaFilaAlt(x) { const f = LS.get('filaAlt', []); f.push({ id: crypto.randomUUID(), ...x }); LS.set('filaAlt', f); actSync(); sincronizar(true); }
// leitura contínua do GPS: mostra a precisão a melhorar e só deixa gravar abaixo do limite
let vigiaCoord = null;
function pararVigia() { if (vigiaCoord != null) { navigator.geolocation.clearWatch(vigiaCoord); vigiaCoord = null; } pararMedicao(); pararPlantas(); }
function ecraCoordenada(id) {
  const a = S.areas.find((x) => x.id === id);
  pararVigia(); S.coordPendente = null;
  folha(`<h2>${esc(a.produtor)}</h2>
    <div class="msg info"><b>Onde ficar:</b> no centro do campo, longe de árvores grandes, casas e viaturas.
      Telefone parado, à altura do peito, ecrã para cima. Espere 30 a 60 segundos até a precisão baixar.</div>
    <div class="cartao"><div class="lin"><span>Precisão agora</span><b id="c-prec">a ler…</b></div>
      <div class="lin"><span>Coordenada</span><b id="c-pos">—</b></div></div>
    <p class="pequeno">Só pode gravar com precisão de ${CFG.precisaoCoord} m ou melhor. O ideal é ${CFG.precisaoIdeal} m ou menos.</p>
    <button class="btn" id="c-gravar" disabled onclick="gravarCoordenada()">Gravar esta coordenada</button>
    <button class="btn sec" onclick="pararVigia();abrirFicha('${esc(id)}')">Cancelar</button>`);
  if (!navigator.geolocation) return aviso('Este telefone não tem GPS disponível no navegador.', 'erro');
  vigiaCoord = navigator.geolocation.watchPosition((p) => {
    const prec = Math.round(p.coords.accuracy), el = $('#c-prec');
    if (!el) return pararVigia();                                    // saiu do ecrã
    const melhor = S.coordPendente && S.coordPendente.precisao <= prec ? S.coordPendente : { area_id: id, lat: p.coords.latitude, lon: p.coords.longitude, precisao: prec };
    S.coordPendente = melhor;                                       // guarda a melhor leitura até agora
    el.textContent = `±${prec} m` + (melhor.precisao < prec ? ` (melhor até agora: ±${melhor.precisao} m)` : '');
    el.style.color = melhor.precisao <= CFG.precisaoIdeal ? '#1b5e20' : melhor.precisao <= CFG.precisaoCoord ? '#ef8f00' : '#c62828';
    $('#c-pos').textContent = `${melhor.lat.toFixed(6)}, ${melhor.lon.toFixed(6)}`;
    $('#c-gravar').disabled = melhor.precisao > CFG.precisaoCoord;
  }, (e) => { const el = $('#c-prec'); if (el) el.textContent = e.code === 1 ? 'sem autorização de localização' : 'sem sinal de GPS'; },
  { enableHighAccuracy: true, maximumAge: 1000, timeout: 60000 });
}
function gravarCoordenada() {
  const x = S.coordPendente; if (!x || x.precisao > CFG.precisaoCoord) return;
  pararVigia();
  const a = S.areas.find((y) => y.id === x.area_id);
  a.latitude = x.lat; a.longitude = x.lon; a.limites_abertos = false; LS.set('areas', S.areas);    // aparece já no mapa deste telefone
  porNaFilaAlt({ tipo: 'coord', ...x }); S.coordPendente = null; desenharMapa(); desenharLista();
  if (!a.activista_id && podeAtribuir(a)) return ecraAtribuir(a.id, '<div class="msg ok">Coordenada gravada. Agora atribua o campo a um activista.</div>');
  abrirFicha(a.id, '<div class="msg ok">Coordenada gravada.</div>');
}
// activistas ordenados pela distância do campo mais próximo que já têm na lista
function activistasProximos(a) {
  if (a.latitude == null) return [];
  const melhor = {};
  for (const b of S.areas) {
    if (!b.activista_id || b.id === a.id || b.latitude == null) continue;
    const d = metros([a.latitude, a.longitude], [b.latitude, b.longitude]);
    if (!(b.activista_id in melhor) || d < melhor[b.activista_id].d) melhor[b.activista_id] = { d, com: b.comunidade };
  }
  return Object.entries(melhor).map(([id, o]) => ({ id, ...o })).sort((x, y) => x.d - y.d);
}
function ecraAtribuir(id, nota = '') {
  const a = S.areas.find((x) => x.id === id), daEquipa = (t) => !S.visiveis || S.visiveis.includes(t);
  const prox = activistasProximos(a).filter((p) => daEquipa(p.id)).slice(0, 3);
  const km = (d) => d < 1000 ? Math.round(d) + ' m' : (d / 1000).toFixed(1) + ' km';
  const resto = S.activistas.filter((t) => activo(t) && daEquipa(t.id) && !prox.some((p) => p.id === t.id));
  folha(`${nota}<h2>${esc(a.produtor)}</h2><p class="pequeno">${esc(a.pr)} · ${esc(a.comunidade)} · activista actual: <b>${esc(nomeAct(a.activista_id))}</b></p>
    ${propostaId(a) ? `<div class="msg info">Proposta da base: <b>${esc(nomeAct(propostaId(a)))}</b></div>` : ''}
    <label>Atribuir a<select id="t-act">
      ${prox.length ? `<optgroup label="Mais próximos (campo da lista mais perto)">${prox.map((p) => `<option value="${p.id}">${esc(nomeAct(p.id))} — ${km(p.d)} (${esc(p.com)})</option>`).join('')}</optgroup>` : ''}
      <optgroup label="Todos">${resto.map((t) => `<option value="${t.id}">${esc(t.nome)} — ${esc(t.comunidade_principal || '')}</option>`).join('')}</optgroup>
    </select></label>
    <p class="pequeno">Regra: rega o activista da comunidade onde o campo está. Confirme antes de gravar.</p>
    <button class="btn" onclick="gravarAtribuicao('${esc(id)}')">Gravar</button>
    <button class="btn sec" onclick="abrirFicha('${esc(id)}')">Cancelar</button>`);
  if (propostaId(a) && daEquipa(propostaId(a))) $('#t-act').value = propostaId(a);
}
function gravarAtribuicao(id) {
  const a = S.areas.find((x) => x.id === id), novo = $('#t-act').value;
  if (!novo) return;
  a.activista_id = novo; LS.set('areas', S.areas);
  porNaFilaAlt({ tipo: 'atrib', area_id: id, activista_id: novo }); desenharMapa(); desenharLista();
  abrirFicha(id, `<div class="msg ok">Campo atribuído a ${esc(nomeAct(novo))}.${navigator.onLine ? '' : ' Será enviado quando houver rede.'}</div>`);
}
async function recarregarAreas() {
  const ar = await sb.from('areas').select(COLS_AREAS).eq('activa', true).order('comunidade').range(0, 4999);
  if (ar.error) return;
  S.areas = aplicarPendentes(ar.data); LS.set('areas', S.areas);
}
function aplicarPendentes(lista) {                          // o que ainda não foi enviado continua a valer neste telefone
  for (const x of LS.get('filaAlt', [])) { const a = lista.find((y) => y.id === x.area_id); if (!a) continue; if (x.tipo === 'coord') { a.latitude = x.lat; a.longitude = x.lon; } else if (x.tipo === 'zona') a.zona = x.zona;
    else if (x.tipo === 'comunidade') { a.comunidade = x.comunidade; a.zona = null; }
    else if (x.tipo === 'limites') a.limites_abertos = x.abrir;
    else if (x.tipo === 'recontagem') {}                            // tipo antigo (v64–v66): já não muda nada
    else if (x.tipo === 'aprovar') aplicarAprovacao(a, x.aprovar);
    else if (x.tipo === 'poligono' && x.proposta) { a.poligono_proposto = x.pontos; a.area_m2_proposta = x.area_m2; a.proposta_em = x.medido_em; }
    else if (x.tipo === 'poligono') { a.limites_abertos = false; a.poligono = x.pontos; a.area_m2 = x.area_m2; if (a.latitude == null) { const c = centroPontos(x.pontos); a.latitude = c[1]; a.longitude = c[0]; } }
    else if (!String(x.tipo).startsWith('planta')) a.activista_id = x.activista_id; }
  for (const x of LS.get('filaRecG', [])) if (x.op === 'validar' && x.sim) { const a = lista.find((y) => y.id === x.area_id); if (a) a.vivas = x.vivas; }   // validação por enviar
  return lista;
}

function abrirFicha(id, nota = '') {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  const s = situacao(a), emCurso = LS.get('emCurso');
  const d = S.pos ? distCampo(a, S.pos) : null;
  const podeRegar = PODE_REGAR.includes(S.perfil.papel) && (S.perfil.papel === 'activista' || a.activista_id);
  let acc = '';
  if (emCurso && emCurso.area_id === a.id) acc = cartaoFotosRega(emCurso) + (emCurso.agua_em
      ? `<div class="msg ok">Água (tuk-tuk) no campo às ${fmtHora(emCurso.agua_em)}.</div>`
      : `<button class="btn sec" onclick="marcarAgua(false)">💧 Chegou a água (tuk-tuk) agora</button>
         <button class="btn sec" onclick="marcarAgua(true)">A água já estava no campo quando chegámos</button>`) +
    `<button class="btn aviso" onclick="ecraSaida()">Terminei — marcar saída</button>`;
  else if (emCurso) acc = `<div class="msg info">Tem a rega de outro campo em curso. Termine-a primeiro.</div><button class="btn sec" onclick="abrirFicha('${esc(emCurso.area_id)}')">Abrir o campo em curso</button>`;
  else if (podeRegar) acc = `<button class="btn" onclick="marcarEntrada('${esc(a.id)}')">Cheguei — marcar entrada</button>`;
  folha(`${nota}<h2 style="margin-top:0">${esc(a.produtor)}</h2>
   <div class="cartao" style="margin:8px 0">
    <div class="lin"><span>PR · área</span><b>${esc(a.pr)} · ${a.area_n ?? '—'}</b></div>
    <div class="lin"><span>Comunidade</span><b>${esc(a.comunidade)}</b></div>
    ${zonasDe(a.comunidade).length ? `<div class="lin"><span>Zona</span><b>${a.zona ? esc(a.zona) : '<span class="pequeno">por definir</span>'}</b></div>` : ''}
    <div class="lin"><span>Activista</span><b>${esc(nomeAct(a.activista_id))}</b></div>
    ${a.instaladas != null ? `<div class="lin"><span>Plantas instaladas</span><b>${num(a.instaladas)}</b></div>` : ''}<div class="lin"><span>Plantas vivas</span><b>${a.vivas != null ? num(a.vivas) : '—'}</b></div>${a.instaladas != null && a.vivas != null && a.instaladas >= a.vivas ? `<div class="lin"><span>Plantas mortas</span><b>${num(a.instaladas - a.vivas)}</b></div>` : ''}
    <div class="lin"><span>Última rega</span><b>${fmtData(s.u)}</b></div>
    ${linhasRegasCampo(a)}
    <div class="lin"><span>Ronda da equipa</span><span class="tag t-${s.cod}">${s.txt}</span></div>
    ${d != null ? `<div class="lin"><span>Distância${temPoligono(a) ? ' (à borda)' : ''}</span><b>${d === 0 ? 'dentro do campo' : (d < 1000 ? Math.round(d) + ' m' : (d / 1000).toFixed(1) + ' km') + (a.latitude != null ? ' · ' + rumo(S.pos, [a.latitude, a.longitude]) : '')}</b></div>` : ''}
    ${eNovo(a) ? `<div class="lin"><span>Na rega desde</span><b>${fmtData(a.reactivada_em.slice(0, 10))} <span class="tag t-novo">Novo na rega</span></b></div>` : ''}
    <div class="lin"><span>Limite do campo</span><b>${temPoligono(a) ? 'polígono' : '<span class="pequeno">só ponto (sem polígono)</span>'}</b></div>
    ${temPoligono(a) ? `<div class="lin"><span>Área</span><b>${textoArea(a.area_m2 || areaPontos(a.poligono))}${a.area_m2 ? ' <span class="pequeno">(medida no campo)</span>' : ''}</b></div>` : ''}
    ${a.latitude == null ? '<div class="msg erro">Este campo não tem coordenada na base. A entrada fica registada sem validação de GPS.</div>' : ''}
   </div>${cartaoQueimada(a)}${cartaoRecontagem(a)}${avisoCampo(a.id)}${acc}${botaoMonitoria(a)}${botoesCampo(a)}<div id="f-regas"></div><div id="f-mon"></div>`);
  if (navigator.onLine) { regasDoCampo(a.id); monitoriasDoCampo(a.id); }   // a pedido, não atrasa a ficha
}

// ---------- entrada ----------
async function validarPosicao(a) {
  const c = await lerGPS();
  const precisao = Math.round(c.accuracy);
  if (a.latitude == null && !temPoligono(a)) return { lat: c.latitude, lon: c.longitude, precisao, dist: null, valido: null };
  const dist = Math.round(distCampo(a, [c.latitude, c.longitude]));
  const valido = dist <= (temPoligono(a) ? CFG.margemPoligono : CFG.margemGPS) + Math.min(precisao, 50);
  return { lat: c.latitude, lon: c.longitude, precisao, dist, valido, poligono: temPoligono(a) };
}
// ---------- início do dia: pessoas presentes na equipa ----------
const jornadaHoje = () => { const j = LS.get('jornada'); return j && j.data === hojeISO() ? j : null; };
function ecraJornada(depois = '') {
  const j = jornadaHoje();
  folha(`<h2>${j ? 'Alterar pessoas presentes' : 'Início do dia'}</h2>
    <label>Quantas pessoas estão hoje na rega com a equipa (incluindo o activista)?
      <input id="j-pessoas" type="number" inputmode="numeric" min="1" max="30" value="${j ? j.pessoas : ''}"></label>
    <button class="btn" onclick="guardarJornada(${JSON.stringify(depois).replace(/"/g, '&quot;')})">Guardar</button>`);
}
function guardarJornada(depois) {
  const n = parseInt($('#j-pessoas').value, 10);
  if (!(n >= 1 && n <= 30)) { alert('Escreva um número entre 1 e 30.'); return; }
  const j = jornadaHoje();
  if (j) { j.pessoas = n; LS.set('jornada', j); }                 // vale para os próximos campos de hoje
  else {
    const nova = { id: crypto.randomUUID(), activista_id: S.perfil.activista_id, data: hojeISO(), pessoas: n, inicio_em: new Date().toISOString(), teste: !souActivista() };
    LS.set('jornada', nova); const f = LS.get('filaJ', []); f.push(nova); LS.set('filaJ', f); actSync(); sincronizar(true);
  }
  if (depois) marcarEntrada(depois); else { fecharFolha(); if ($('#e-hoje').classList.contains('on')) desenharHoje(); }
}

async function marcarEntrada(id) {
  const a = S.areas.find((x) => x.id === id);
  const minha = souActivista() && a.activista_id === S.perfil.activista_id;
  if (souActivista() && minha) {                                // regra da ronda: não repetir antes de acabar a lista
    const ri = rondaInfo(S.perfil.activista_id);
    if (ri.feitas.has(id)) return abrirFicha(id, `<div class="msg erro">Este campo já foi regado na ronda ${ri.n}. Só pode voltar a regá-lo depois de regar todos os campos da sua lista (faltam ${ri.total - ri.feitas.size} de ${ri.total}).</div>`);
  }
  if (souActivista() && S.perfil.activista_id && !jornadaHoje()) return ecraJornada(id);
  folha('<h2>A ler o GPS…</h2><p class="pequeno">Pode levar até 30 segundos. Fique em céu aberto.</p>');
  let g; try { g = await validarPosicao(a); } catch (e) { return abrirFicha(id, `<div class="msg erro">${esc(e.message)}</div>`); }
  if (g.valido === false) return abrirFicha(id, `<div class="msg erro">Está a ${g.dist} m do campo (precisão ±${g.precisao} m). Só pode marcar a entrada até ${g.poligono ? CFG.margemPoligono + ' m da borda' : CFG.margemGPS + ' m'} do campo.</div>`);
  const ent = { area_id: id, entrada_em: new Date().toISOString(), entrada_lat: g.lat, entrada_lon: g.lon, gps_precisao_m: g.precisao, distancia_area_m: g.dist, gps_valido: g.valido };
  const sug = LS.get('sugestao');
  if (sug) { ent.area_sugerida_id = sug.area_id; ent.seguiu_sugestao = sug.area_id === id; LS.del('sugestao'); }
  if (souActivista() && !minha) {                               // campo de outra equipa ou sem activista
    LS.set('pendenteAlerta', ent);
    return folha(`<h2>Atenção: campo fora da sua lista</h2>
      <div class="msg erro">Este campo é de ${esc(nomeAct(a.activista_id))}. Não conta para a sua ronda.</div>
      <label>Porque vai regar este campo?<textarea id="a-motivo" rows="3" placeholder="Escreva o motivo"></textarea></label>
      <button class="btn aviso" onclick="confirmarAlerta()">Regar mesmo assim</button>
      <button class="btn sec" onclick="LS.del('pendenteAlerta');abrirFicha('${esc(id)}')">Não regar este campo</button>`);
  }
  ent.reg_id = crypto.randomUUID();
  LS.set('emCurso', ent); ecraFotoRega('entrada', `<div class="msg ok">Entrada marcada às ${fmtHora(ent.entrada_em)}${g.dist === 0 ? ' · dentro do campo' : g.dist != null ? ` · a ${g.dist} m do campo` : ''}.</div>`);
}
function confirmarAlerta() {
  const m = $('#a-motivo').value.trim();
  if (m.length < 3) { alert('Escreva o motivo.'); return; }
  const ent = LS.get('pendenteAlerta'); ent.alerta = 'fora_da_lista'; ent.motivo_alerta = m;
  ent.reg_id ||= crypto.randomUUID();
  LS.del('pendenteAlerta'); LS.set('emCurso', ent);
  ecraFotoRega('entrada', `<div class="msg ok">Entrada marcada às ${fmtHora(ent.entrada_em)} (campo fora da lista).</div>`);
}
function marcarAgua(jaEstava) {
  const ent = LS.get('emCurso'); if (!ent) return;
  ent.agua_em = jaEstava ? ent.entrada_em : new Date().toISOString(); LS.set('emCurso', ent);
  abrirFicha(ent.area_id);
}

// ---------- fotografias da rega (15/10/2026, Valdo): entrada, evidência da rega e saída, todas obrigatórias ----------
// Cada fotografia fica logo no telefone (IndexedDB) com o id do registo; vai para o bucket rega-fotos com o registo.
const FOTOS_REGA = { entrada: 'Fotografia da entrada', rega: 'Fotografia da rega (evidência)', saida: 'Fotografia da saída' };
const FALTA_FOTO = { entrada: 'Tire a fotografia da entrada.', rega: 'Tire a fotografia da rega (evidência).', saida: 'Tire a fotografia da saída.' };
async function guardarFotoRega(tipo, foto) {
  const ent = LS.get('emCurso'); if (!ent || !foto) return false;
  ent.reg_id ||= crypto.randomUUID();
  const k = `${ent.reg_id}-${tipo}`;
  try { await FOTOS.guardar(k, foto); } catch { S.fotosMem = { ...(S.fotosMem || {}), [k]: foto }; }
  ent.fotos = { ...(ent.fotos || {}), [tipo]: new Date().toISOString() }; LS.set('emCurso', ent); LS.del('rascFotoRega');
  return true;
}
function cartaoFotosRega(ent) {
  const f = ent.fotos || {};
  return `<div class="cartao" style="margin:8px 0"><div class="lin"><span><b>Fotografias</b></span><span class="pequeno">obrigatórias</span></div>` +
    ['entrada', 'rega'].map((t) => `<div class="lin"><span>📷 ${FOTOS_REGA[t]}</span><b>${f[t]
      ? `<span style="color:var(--ok,#2e7d32)">✓ ${fmtHora(f[t])}</span> <button class="chip" onclick="ecraFotoRega('${t}')">Tirar outra</button>`
      : `<button class="chip" onclick="ecraFotoRega('${t}')">Tirar</button>`}</b></div>`).join('') +
    `<p class="pequeno" style="margin:4px 0 0">A fotografia da saída tira-se ao marcar a saída.</p></div>`;
}
function ecraFotoRega(tipo, nota = '', r = null) {
  const ent = LS.get('emCurso'); if (!ent) return;
  const ajuda = { entrada: 'Fotografia da equipa a chegar ao campo.', rega: 'Fotografia da equipa a regar as plantas.', saida: 'Fotografia do campo regado, ao sair.' }[tipo];
  folha(`${nota}${r?.camara ? AVISO_CAMARA : ''}<h2>${FOTOS_REGA[tipo]}</h2><p class="pequeno">${ajuda} Obrigatória.</p>
    ${campoFoto('fr-foto', FOTOS_REGA[tipo])}
    <button class="btn sec" onclick="LS.del('rascFotoRega');abrirFicha('${esc(ent.area_id)}')">${tipo === 'entrada' ? 'Tirar depois' : 'Voltar'}</button>`);
  rascGuardar('rascFotoRega', { perfil: S.perfil?.id, tipo, camara: false });
  ligarFoto('fr-foto', 'rascFotoRega', async (foto) => {
    if (!foto) return;
    await guardarFotoRega(tipo, foto);
    abrirFicha(ent.area_id, `<div class="msg ok">${FOTOS_REGA[tipo]} guardada.</div>`);
  });
}

// ---------- saída ----------
const TIPOS = [['falta_agua', 'Falta de água'], ['mudas_secas', 'Mudas secas'], ['acesso_dificil', 'Acesso difícil'], ['avaria', 'Avaria'], ['outro', 'Outro']];
function ecraSaida() {
  const ent = LS.get('emCurso'), a = S.areas.find((x) => x.id === ent.area_id);
  folha(`<h2>${esc(a.produtor)}</h2><p class="pequeno">Entrada às ${fmtHora(ent.entrada_em)}</p>
   <label>Plantas regadas neste campo<input id="s-plantas" type="number" inputmode="numeric" min="0" value="${plantasN(a)}"></label>
   <p class="pequeno">Na base: ${plantasTxt(a)}. Se regou menos, escreva o número real.</p>
   <label>Pessoas que regaram este campo<input id="s-pessoas" type="number" inputmode="numeric" min="1" max="30" value="${jornadaHoje()?.pessoas ?? ''}"></label>
   ${ent.agua_em ? `<p class="pequeno">Água no campo às ${fmtHora(ent.agua_em)}.</p>`
     : `<label>Hora a que chegou a água (tuk-tuk)<input id="s-agua" type="time"></label><p class="pequeno">Deixe vazio se não chegou água.</p>`}
   <label>Constrangimentos</label><div class="chips" id="s-chips">${TIPOS.map(([k, t]) => `<button class="chip" data-k="${k}">${t}</button>`).join('')}</div>
   <textarea id="s-obs" rows="2" placeholder="Explique (opcional)"></textarea>
   ${campoFoto('s-foto', 'Fotografia da saída (obrigatória)')}
   <p class="pequeno" id="s-foto-ok">${ent.fotos?.saida ? `<span style="color:var(--ok,#2e7d32)">✓ Fotografia da saída às ${fmtHora(ent.fotos.saida)}</span>` : ''}</p>
   <button class="btn" onclick="marcarSaida()">Marcar saída e guardar</button>
   <button class="btn sec" onclick="abrirFicha('${esc(a.id)}')">Voltar</button>`);
  document.querySelectorAll('#s-chips .chip').forEach((b) => b.onclick = () => b.classList.toggle('on'));
  rascGuardar('rascFotoRega', { perfil: S.perfil?.id, tipo: 'saida', camara: false });
  ligarFoto('s-foto', 'rascFotoRega', async (foto) => {
    if (!foto || !(await guardarFotoRega('saida', foto))) return;
    $('#s-foto-ok').innerHTML = `<span style="color:var(--ok,#2e7d32)">✓ Fotografia da saída às ${fmtHora(LS.get('emCurso').fotos.saida)}</span>`;
  });
}
async function marcarSaida() {
  const ent = LS.get('emCurso'), a = S.areas.find((x) => x.id === ent.area_id);
  const semFoto = ['entrada', 'rega', 'saida'].find((t) => !ent.fotos?.[t]);
  if (semFoto) { alert(FALTA_FOTO[semFoto]); if (semFoto !== 'saida') ecraFotoRega(semFoto); return; }
  const plantas = parseInt($('#s-plantas').value, 10);
  if (!(plantas >= 0)) { alert('Escreva o número de plantas regadas.'); return; }
  if (plantas > plantasN(a) * 1.2 && !confirm(`Escreveu ${plantas}, mas a base diz ${plantasTxt(a)}. Confirma?`)) return;
  const pessoas = parseInt($('#s-pessoas').value, 10);
  if (!(pessoas >= 1 && pessoas <= 30)) { alert('Escreva o número de pessoas (1 a 30).'); return; }
  const hAgua = $('#s-agua')?.value;
  if (hAgua) { const t = new Date(); const [hh, mm] = hAgua.split(':'); t.setHours(+hh, +mm, 0, 0); ent.agua_em = t.toISOString(); }
  const j = jornadaHoje(); if (j && j.pessoas !== pessoas) { j.pessoas = pessoas; LS.set('jornada', j); }
  const tipos = [...document.querySelectorAll('#s-chips .chip.on')].map((b) => b.dataset.k), obs = $('#s-obs').value.trim();
  folha('<h2>A ler o GPS…</h2><p class="pequeno">A confirmar que ainda está no campo.</p>');
  let g; try { g = await validarPosicao(a); } catch (e) { ecraSaida(); return aviso(e.message, 'erro'); }
  if (g.valido === false) { ecraSaida(); return aviso(`Está a ${g.dist} m do campo. Marque a saída ainda no campo (até ${g.poligono ? CFG.margemPoligono + ' m da borda' : CFG.margemGPS + ' m'}).`, 'erro'); }
  const actId = S.perfil.activista_id || a.activista_id;
  const antes = actId ? rondaInfo(actId) : null;
  const reg = {
    ronda: antes ? antes.n : null, pessoas, agua_em: ent.agua_em || null,
    id: ent.reg_id || crypto.randomUUID(), fotos: ent.fotos, area_id: a.id, activista_id: S.perfil.activista_id || a.activista_id, data: hojeISO(),
    entrada_em: ent.entrada_em, saida_em: new Date().toISOString(), entrada_lat: ent.entrada_lat, entrada_lon: ent.entrada_lon,
    saida_lat: g.lat, saida_lon: g.lon, gps_precisao_m: Math.max(ent.gps_precisao_m || 0, g.precisao),
    distancia_area_m: ent.distancia_area_m, gps_valido: ent.gps_valido, plantas_regadas: plantas,
    alerta: ent.alerta || null, motivo_alerta: ent.motivo_alerta || null,
    area_sugerida_id: ent.area_sugerida_id || null, seguiu_sugestao: ent.seguiu_sugestao ?? null,
    criado_no_telefone_em: new Date().toISOString(), teste: S.perfil.papel !== 'activista', observacao: obs || null,
    constr: tipos.map((t) => ({ id: crypto.randomUUID(), tipo: t, descricao: obs || null })),
  };
  porNaFila(reg); LS.del('emCurso'); LS.del('rascFotoRega'); actSync(); desenharMapa(); desenharLista();
  sincronizar(true);
  let nota = '';
  if (souActivista() && antes && plantas > 0) {
    const depois = rondaInfo(actId);
    if (depois.n > antes.n) nota = `<div class="msg ok"><b>Ronda ${antes.n} concluída!</b> Os ${antes.total} campos da lista foram regados de ${fmtData(depois.anterior.ini)} a ${fmtData(depois.anterior.fim)}. A ronda ${depois.n} começa agora.</div>`;
  }
  sugerirProximo(a, nota);
}

// ---------- próximo campo (sugestão opcional) ----------
function sugerirProximo(feito, nota = '') {
  const de = S.pos || (feito.latitude != null ? [feito.latitude, feito.longitude] : null);
  const cand = (S.perfil.papel === 'activista' ? minhas() : S.areas.filter((a) => a.comunidade === feito.comunidade))
    .filter((a) => a.id !== feito.id && a.latitude != null && situacao(a).cod === 'por');
  if (!de || !cand.length) return folha(`<div class="msg ok">Rega guardada.</div>${nota}<p>Não há sugestão de próximo campo.</p><button class="btn" onclick="fecharFolha()">Fechar</button>`);
  cand.sort((x, y) => metros(de, [x.latitude, x.longitude]) - metros(de, [y.latitude, y.longitude]));
  const p = cand[0], d = metros(de, [p.latitude, p.longitude]), s = situacao(p);
  LS.set('sugestao', { area_id: p.id, em: new Date().toISOString() });
  folha(`<div class="msg ok">Rega guardada${navigator.onLine ? '' : ' no telefone (será enviada quando houver rede)'}.</div>${nota}
    <h2>Próximo campo sugerido</h2>
    <div class="cartao"><div class="lin"><span>Produtor</span><b>${esc(p.produtor)}</b></div>
     <div class="lin"><span>PR</span><b>${esc(p.pr)}</b></div><div class="lin"><span>Plantas</span><b>${plantasTxt(p)}</b></div>
     <div class="lin"><span>Última rega</span><b>${fmtData(s.u)}</b></div><div class="lin"><span>Ronda</span><span class="tag t-${s.cod}">${s.txt}</span></div>
     <div class="lin"><span>Distância</span><b>${d < 1000 ? Math.round(d) + ' m' : (d / 1000).toFixed(1) + ' km'} · ${rumo(de, [p.latitude, p.longitude])}</b></div></div>
    <p class="pequeno">É só uma sugestão. Pode escolher outro campo.</p>
    <button class="btn" onclick="fecharFolha();mapa.setView([${p.latitude},${p.longitude}],16);mudar('mapa')">Ver no mapa</button>
    <button class="btn sec" onclick="fecharFolha()">Escolher outro campo</button>`);
}

// ---------- regas do campo e queimadas (16/10/2026, Dalmar via Valdo) ----------
function linhasRegasCampo(a) {
  const r = regasDoCampoInfo(a);
  const datas = (a.datas_rega_origem || []).map(fmtData).join(', ');
  return `<div class="lin"><span>Regas recebidas</span><b>${num(r.total)}${r.total ? ` <span class="pequeno">(${num(r.orig)} antes da app · ${num(r.app)} na app)</span>` : ''}</b></div>
    ${r.total ? `<div class="lin"><span>Água (${CFG.litrosPlanta} L por planta)</span><b>${num(r.litros)} L</b></div>` : ''}
    ${datas && !a.regas_origem_por_pr ? `<p class="pequeno" style="margin:2px 0 6px">Regas antes da app (até ${CFG.dataOrigem}): ${datas}</p>` : ''}
    ${datas && a.regas_origem_por_pr ? `<p class="pequeno" style="margin:2px 0 6px">Antes da app o produtor tem ${num(a.n_regas_origem || 0)} regas registadas (${datas}), mas o registo não diz em que campo: não contam neste campo.</p>` : ''}`;
}
const queimadasLocais = () => LS.get('filaQueim', []);
// a queimada mais recente do campo (as que estão no telefone por enviar contam)
function queimadaDe(id) {
  const l = [...(S.queimadas || []), ...queimadasLocais()].filter((q) => q.area_id === id && !q.removida);
  return l.sort((x, y) => (y.data || '').localeCompare(x.data || ''))[0] || null;
}
function cartaoQueimada(a) {
  const q = queimadaDe(a.id); if (!q) return '';
  const meu = q.registada_por === S.perfil?.id || q.local, pode = meu || ['supervisor', 'gestor'].includes(S.perfil?.papel);
  const pl = q.plantas_afectadas != null ? `<div>${num(q.plantas_afectadas)} plantas afectadas${q.plantas_mortas != null ? ` · ${num(q.plantas_mortas)} mortas` : ''}</div>` : '';
  // a recontagem (pedida sozinha pela queimada) aparece no cartão "Recontagem das plantas" da ficha
  const rec = q.local || recontagemDe(a.id) ? '' : q.recontagem_em
    ? `<div>✓ Recontagem a ${fmtData(String(q.recontagem_em).slice(0, 10))}: <b>${num(q.vivas_recontadas)} plantas vivas</b>${q.recontagem_obs ? ` — ${esc(q.recontagem_obs)}` : ''}</div>` : '';
  return `<div class="msg erro" style="background:#fff3e0;color:#7a3300;border-color:#ffb74d">🔥 <b>Queimada</b> a ${fmtData(q.data)}${q.observacao ? ` — ${esc(q.observacao)}` : ''}${q.local ? ' <span class="pequeno">(no telefone; é enviada quando houver rede)</span>' : ''}
    ${pl}${rec}
    <div class="chips" style="margin-top:6px">${q.foto_path && fotoVisivel(q.foto_path) ? `<button class="chip" onclick="verFoto('rega-fotos','${esc(q.foto_path)}','Queimada ${fmtData(q.data)}')">📷 Ver fotografia</button>` : ''}${pode ? `<button class="chip" onclick="removerQueimada('${esc(q.id)}','${esc(a.id)}')">Remover (engano)</button>` : ''}</div></div>`;
}
// ---------- recontagem das plantas pelos oficiais de M&E (18/10/2026, Valdo) ----------
// O M&E (Edilson, Kathleen) e o gestor pedem a recontagem de um campo, com o motivo (cada queimada pede uma sozinha),
// e encaminham-na a um oficial de M&E. O oficial só vê os campos que lhe foram encaminhados (sem nenhum, a app fica vazia)
// e regista as plantas vivas e mortas, com a fotografia da declaração (opcional) e o GPS; funciona sem rede (fila filaRec).
// O M&E valida (só então mudam as plantas vivas do campo e todos vêem os números) ou recusa com o motivo (volta ao oficial).
// Antes de validar, os outros só vêem o estado. O M&E e o gestor não fazem a contagem (não vão ao campo).
const souOficial = () => S.perfil?.papel === 'oficial_me';
const gereRecont = () => ['me', 'gestor'].includes(S.perfil?.papel);
const filaRec = () => LS.get('filaRec', []);
async function carregarRecontagens() {
  const r = await sb.rpc('recontagens_lista');
  if (!r.error && Array.isArray(r.data)) { S.recont = r.data; LS.set('recont', S.recont); }
}
// Pedir, encaminhar, validar, recusar e cancelar também sem rede (18/10/2026, Valdo): ficam na fila filaRecG, pela ordem,
// e são enviadas quando houver rede (com a hora do telefone). Até lá a app mostra-as como feitas, com a nota "no telefone".
const filaRecG = () => LS.get('filaRecG', []);
function porNaFilaRecG(x) { LS.set('filaRecG', [...filaRecG(), { ...x, em: new Date().toISOString() }]); actSync(); sincronizar(true); }
// o que ainda está no telefone (do M&E/gestor e do oficial) conta, neste telefone, como já feito
function recontagens() {
  const l = (S.recont || []).map((r) => ({ ...r }));
  for (const x of filaRecG()) {
    let r = l.find((y) => y.id === x.id);
    if (x.op === 'pedir' && !r) { const a = S.areas.find((y) => y.id === x.area_id) || {};
      l.push({ id: x.id, area_id: x.area_id, pr: a.pr, produtor: a.produtor, comunidade: a.comunidade, motivo: x.motivo, estado: x.oficial ? 'encaminhada' : 'por_encaminhar',
        oficial_id: x.oficial, oficial: x.oficial_nome, pedido_em: x.em, encaminhada_em: x.oficial ? x.em : null, localG: true }); continue; }
    if (!r) continue;
    if (x.op === 'encaminhar') Object.assign(r, { estado: 'encaminhada', oficial_id: x.oficial, oficial: x.oficial_nome, encaminhada_em: x.em, localG: true });
    else if (x.op === 'validar' && x.sim) Object.assign(r, { estado: 'validada', validada_em: x.em, vivas_antes: r.vivas_antes ?? x.vivas_antes, localG: true });
    else if (x.op === 'validar') Object.assign(r, { estado: 'recusada', recusa_motivo: x.motivo, recusada_em: x.em, localG: true });
    else if (x.op === 'cancelar') r.estado = 'cancelada';
  }
  const f = filaRec();
  return l.filter((r) => r.estado !== 'cancelada').map((r) => { const x = f.find((y) => y.id === r.id);
    return x ? { ...r, estado: 'enviada', vivas: x.vivas, mortas: x.mortas, contada_em: x.em, lat: x.lat, lon: x.lon, precisao_m: x.precisao, foto_local: x.foto, local: true } : r; });
}
const recontagemDe = (id) => recontagens().filter((r) => r.area_id === id).sort((x, y) => (y.pedido_em || '').localeCompare(x.pedido_em || ''))[0] || null;
const recPorFazer = () => recontagens().filter((r) => ['encaminhada', 'recusada'].includes(r.estado));
const dataCurta = (t) => t ? fmtData(String(t).slice(0, 10)) : '—';
function localContagem(r, a) {
  if (r.lat == null) return 'sem GPS';
  const d = a ? distCampo(a, [r.lat, r.lon]) : null, p = r.precisao_m != null ? ` (±${Math.round(r.precisao_m)} m)` : '';
  return d == null ? 'campo sem coordenada' + p : d === 0 ? 'dentro do campo' + p : (d < 1000 ? Math.round(d) + ' m' : (d / 1000).toFixed(1) + ' km') + ' do campo' + p;
}
function cartaoRecontagem(a) {
  const r = recontagemDe(a.id), papel = S.perfil?.papel;
  const pedir = gereRecont() ? `<button class="btn sec" onclick="ecraPedirRecontagem('${esc(a.id)}')">📋 Pedir recontagem das plantas</button>` : '';
  if (!r) return pedir;
  const foto = r.foto_path && papel !== 'activista' ? `<button class="chip" onclick="verFoto('recontagem-fotos','${esc(r.foto_path)}','Declaração · ${esc(a.pr)} · ${esc(dataCurta(r.contada_em))}')">📷 Declaração</button>` : '';
  const nums = `<div class="lin"><span>Plantas vivas · mortas</span><b>${num(r.vivas)} · ${num(r.mortas)}</b></div>`;
  let h = `<div class="cartao" style="border-left:4px solid #6d4c41;margin:8px 0"><h3 style="margin:0 0 6px;font-size:15px">📋 Recontagem das plantas</h3>
    <div class="lin"><span>Motivo</span><b>${esc(r.motivo)}</b></div><div class="lin"><span>Pedida a</span><b>${dataCurta(r.pedido_em)}</b></div>
    ${r.localG && !souOficial() ? '<p class="pequeno">No telefone: é enviado quando houver rede.</p>' : ''}`;
  if (r.estado === 'validada') {
    h += `<div class="msg ok">✓ Validada pelo M&E a ${dataCurta(r.validada_em)}.</div>${nums}${r.vivas_antes != null ? `<div class="lin"><span>Plantas vivas antes</span><b>${num(r.vivas_antes)}</b></div>` : ''}<div class="chips">${foto}</div></div>${pedir}`;
    return h;
  }
  if (souOficial()) {
    if (r.estado === 'enviada') h += `<div class="msg info">${r.local ? 'Guardada no telefone: é enviada quando houver rede.' : `Enviada a ${dataCurta(r.contada_em)}. À espera da validação do M&E.`}</div>${nums}
      <div class="lin"><span>Local da contagem</span><b>${localContagem(r, a)}</b></div>${r.local ? `<button class="btn sec" onclick="ecraRecontar('${esc(r.id)}')">Corrigir</button>` : ''}`;
    else h += `${r.estado === 'recusada' ? `<div class="msg erro">Recusada pelo M&E: ${esc(r.recusa_motivo || '')}. Faça a contagem de novo.</div>` : ''}
      <button class="btn" onclick="ecraRecontar('${esc(r.id)}')">📋 Registar a recontagem</button>`;
    return h + '</div>';
  }
  const oficial = r.oficial ? esc(r.oficial) : '—';
  if (r.estado === 'por_encaminhar') h += `<div class="lin"><span>Estado</span><b>Por encaminhar a um oficial</b></div>`;
  else if (r.estado === 'encaminhada') h += `<div class="lin"><span>Estado</span><b>Encaminhada a ${oficial} (${dataCurta(r.encaminhada_em)})</b></div>`;
  else if (r.estado === 'recusada') h += `<div class="lin"><span>Estado</span><b>Recusada pelo M&E: à espera de nova contagem de ${oficial}</b></div>${papel === 'me' ? `<p class="pequeno">Motivo da recusa: ${esc(r.recusa_motivo || '')}</p>` : ''}`;
  else if (r.estado === 'enviada' && papel === 'me') h += `<div class="lin"><span>Contada por</span><b>${oficial} a ${dataCurta(r.contada_em)}</b></div>${nums}
      ${a.vivas != null ? `<div class="lin"><span>Plantas vivas na base</span><b>${num(a.vivas)}</b></div>` : ''}
      <div class="lin"><span>Local da contagem</span><b>${localContagem(r, a)}</b></div>
      <div class="chips">${foto || '<span class="pequeno">Sem fotografia da declaração.</span>'}</div>
      <div style="display:flex;gap:8px;margin-top:8px"><button class="btn" style="margin:0" onclick="validarRecontagem('${esc(r.id)}', true)">✓ Validar</button><button class="btn sec" style="margin:0" onclick="ecraRecusarRecontagem('${esc(r.id)}')">✗ Recusar</button></div>
      <p class="pequeno">Ao validar, as plantas vivas do campo passam a ${num(r.vivas)}.</p>`;
  else if (r.estado === 'enviada') h += `<div class="lin"><span>Estado</span><b>Recontagem feita, em validação pelo M&E</b></div>`;
  if (gereRecont() && r.estado !== 'enviada') h += `<div class="chips" style="margin-top:6px"><button class="chip" onclick="ecraEncaminhar('${esc(r.id)}')">${r.oficial_id ? 'Mudar o oficial' : 'Encaminhar a um oficial'}</button><button class="chip" onclick="cancelarRecontagem('${esc(r.id)}')">Cancelar o pedido</button></div>`;
  return h + '</div>';
}
// lista dos oficiais de M&E (para encaminhar); fica no telefone para funcionar sem rede
async function oficiais() {
  if (navigator.onLine) { const r = await sb.rpc('oficiais_me'); if (!r.error && Array.isArray(r.data)) { S.oficiais = r.data; LS.set('oficiais', r.data); } }
  return S.oficiais || LS.get('oficiais', []) || [];
}
const nomeOficial = (id) => ((S.oficiais || LS.get('oficiais', []) || []).find((o) => o.id === id) || {}).nome || null;
async function opcoesOficiais(sel, comVazio) {
  const l = await oficiais();
  return (comVazio ? '<option value="">(encaminhar depois)</option>' : '') + (l.length ? l.map((o) => `<option value="${o.id}" ${o.id === sel ? 'selected' : ''}>${esc(o.nome)}</option>`).join('')
    : (comVazio ? '' : `<option value="">${navigator.onLine ? 'Ainda não há oficiais de M&E com acesso' : 'Sem a lista dos oficiais no telefone: abra com rede uma vez'}</option>`));
}
const notaFila = () => (navigator.onLine ? '' : '<br><span class="pequeno">Guardado no telefone: é enviado quando houver rede.</span>');
async function ecraPedirRecontagem(id) {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  folha(`<h2>📋 Pedir recontagem</h2><p class="pequeno">${esc(a.produtor)} · ${esc(a.pr)} · ${esc(a.comunidade)}</p>
    <label>Motivo da recontagem<textarea id="pr-motivo" rows="2" placeholder="Ex.: muitas plantas mortas na monitoria"></textarea></label>
    <label>Oficial de M&E<select id="pr-of">${await opcoesOficiais(null, true)}</select></label>
    <div id="pr-msg"></div><button class="btn" id="pr-ok">Pedir</button><button class="btn sec" onclick="abrirFicha('${esc(id)}')">Cancelar</button>`);
  $('#pr-ok').onclick = () => {
    const m = $('#pr-motivo').value.trim(); if (m.length < 3) { $('#pr-msg').innerHTML = '<div class="msg erro">Escreva o motivo da recontagem.</div>'; return; }
    if (recontagemDe(id) && recontagemDe(id).estado !== 'validada') { $('#pr-msg').innerHTML = '<div class="msg erro">Já há uma recontagem em curso neste campo</div>'; return; }
    const of = $('#pr-of').value || null;
    porNaFilaRecG({ op: 'pedir', id: crypto.randomUUID(), area_id: id, motivo: m, oficial: of, oficial_nome: of ? nomeOficial(of) : null });
    abrirFicha(id, `<div class="msg ok">${of ? 'Recontagem pedida e encaminhada.' : 'Recontagem pedida.'}${notaFila()}</div>`); actHoje();
  };
}
async function ecraEncaminhar(rid) {
  const r = recontagens().find((x) => x.id === rid); if (!r) return;
  const a = S.areas.find((x) => x.id === r.area_id) || {};
  folha(`<h2>Encaminhar a recontagem</h2><p class="pequeno">${esc(a.produtor || r.produtor || '')} · ${esc(r.pr || a.pr || '')} · ${esc(r.motivo)}</p>
    <label>Oficial de M&E<select id="en-of">${await opcoesOficiais(r.oficial_id, false)}</select></label>
    <div id="en-msg"></div><button class="btn" id="en-ok">Encaminhar</button><button class="btn sec" onclick="abrirFicha('${esc(r.area_id)}')">Cancelar</button>`);
  $('#en-ok').onclick = () => {
    const of = $('#en-of').value; if (!of) return;
    porNaFilaRecG({ op: 'encaminhar', id: rid, oficial: of, oficial_nome: nomeOficial(of) });
    abrirFicha(r.area_id, `<div class="msg ok">Recontagem encaminhada.${notaFila()}</div>`); actHoje();
  };
}
function cancelarRecontagem(rid) {
  const r = recontagens().find((x) => x.id === rid); if (!r) return;
  if (!confirm('Cancelar este pedido de recontagem?')) return;
  porNaFilaRecG({ op: 'cancelar', id: rid });
  abrirFicha(r.area_id, `<div class="msg ok">Pedido cancelado.${notaFila()}</div>`); actHoje();
}
// validar ou recusar: vai com os números que o M&E viu (se a recontagem mudar entretanto, o servidor não aceita)
function validarRecontagem(rid, sim, motivo = null) {
  const r = recontagens().find((x) => x.id === rid); if (!r) return;
  if (sim && !confirm(`Validar: as plantas vivas do campo passam a ${num(r.vivas)}.`)) return;
  const a = S.areas.find((x) => x.id === r.area_id);
  porNaFilaRecG({ op: 'validar', id: rid, area_id: r.area_id, sim, motivo, vivas: r.vivas, mortas: r.mortas, vivas_antes: a ? a.vivas : null });
  if (sim && a) { a.vivas = r.vivas; LS.set('areas', S.areas); }        // as plantas vivas mudam logo neste telefone
  desenharMapa(); desenharLista(); abrirFicha(r.area_id, `<div class="msg ok">${sim ? 'Recontagem validada: as plantas vivas do campo já mudaram.' : 'Recontagem recusada: volta ao oficial.'}${notaFila()}</div>`); actHoje();
}
// envia as acções do M&E/gestor pela ordem em que foram feitas
async function enviarGestaoRecontagens() {
  let mudouVivas = false, fez = false;
  for (const x of filaRecG()) {
    const r = x.op === 'pedir' ? await sb.rpc('pedir_recontagem2', { p_id: x.id, p_area: x.area_id, p_motivo: x.motivo, p_oficial: x.oficial, p_em: x.em })
      : x.op === 'encaminhar' ? await sb.rpc('encaminhar_recontagem2', { p_id: x.id, p_oficial: x.oficial, p_em: x.em })
      : x.op === 'validar' ? await sb.rpc('validar_recontagem2', { p_id: x.id, p_validar: x.sim, p_motivo: x.motivo, p_vivas: x.vivas, p_mortas: x.mortas, p_em: x.em })
      : await sb.rpc('cancelar_recontagem', { p_id: x.id });
    if (r.error && !r.error.code) return r.error.message;                 // sem rede: fica na fila
    if (r.error) aviso(`Recontagem: ${r.error.message}`, 'erro');           // recusado pelo servidor: sai da fila
    else if (x.op === 'validar' && x.sim) mudouVivas = true;
    LS.set('filaRecG', filaRecG().filter((y) => !(y.id === x.id && y.op === x.op && y.em === x.em))); fez = true;
  }
  if (fez) { await carregarRecontagens(); if (mudouVivas) await recarregarAreas(); }
  return null;
}
function ecraRecusarRecontagem(rid) {
  const r = recontagens().find((x) => x.id === rid); if (!r) return;
  folha(`<h2>Recusar a recontagem</h2><p class="pequeno">${esc(r.produtor || '')} · ${esc(r.pr || '')} · ${esc(r.oficial || '')}</p>
    <label>Motivo da recusa (o oficial vai ler)<textarea id="rr-m" rows="3"></textarea></label><div id="rr-msg"></div>
    <button class="btn aviso" id="rr-ok">Recusar</button><button class="btn sec" onclick="abrirFicha('${esc(r.area_id)}')">Cancelar</button>`);
  $('#rr-ok').onclick = () => { const m = $('#rr-m').value.trim(); if (m.length < 3) { $('#rr-msg').innerHTML = '<div class="msg erro">Escreva o motivo da recusa.</div>'; return; } validarRecontagem(rid, false, m); };
}
// formulário do oficial (sem rede: fica na fila filaRec com a fotografia no telefone)
function ecraRecontar(rid, rasc) {
  const r = recontagens().find((x) => x.id === rid); if (!r) return;
  const a = S.areas.find((x) => x.id === r.area_id) || {}, ant = filaRec().find((x) => x.id === rid);
  S.recFoto = null; S.recFotoAnt = !!ant?.foto; if (!rasc) LS.del('rascRec');
  folha(`<h2>📋 Recontagem das plantas</h2>${rasc?.camara ? AVISO_CAMARA : ''}<p class="pequeno">${esc(a.produtor || r.produtor || '')} · ${esc(a.pr || r.pr || '')} · ${esc(a.comunidade || r.comunidade || '')}</p>
    <div class="cartao"><div class="lin"><span>Motivo</span><b>${esc(r.motivo)}</b></div>${r.estado === 'recusada' ? `<div class="msg erro">Recusada pelo M&E: ${esc(r.recusa_motivo || '')}</div>` : ''}</div>
    <label>Plantas vivas contadas<input id="ro-vivas" type="number" inputmode="numeric" min="0" value="${ant?.vivas ?? ''}"></label>
    <label>Plantas mortas contadas<input id="ro-mortas" type="number" inputmode="numeric" min="0" value="${ant?.mortas ?? ''}"></label>
    ${campoFoto('ro-foto', 'Fotografia ou digitalização da declaração de contagem (opcional)')}
    <p class="pequeno" id="ro-foto-ok">${ant?.foto ? '✓ Fotografia guardada no telefone.' : ''}</p>
    <img id="ro-prev" alt="" style="display:none;width:100%;max-height:200px;object-fit:contain;border-radius:10px;margin-top:8px">
    <p class="pequeno">A app guarda também o local (GPS) onde regista. Funciona sem rede: é enviada quando houver rede.</p>
    <div id="ro-msg"></div><button class="btn" id="ro-ok">Guardar</button><button class="btn sec" onclick="LS.del('rascRec');abrirFicha('${esc(r.area_id)}')">Cancelar</button>`);
  if (rasc) { if (rasc.vivas != null) $('#ro-vivas').value = rasc.vivas; if (rasc.mortas != null) $('#ro-mortas').value = rasc.mortas; }
  const guardar = () => rascGuardar('rascRec', { perfil: S.perfil?.id, rid, camara: false, vivas: $('#ro-vivas').value, mortas: $('#ro-mortas').value });
  ['#ro-vivas', '#ro-mortas'].forEach((q) => $(q).addEventListener('input', guardar)); guardar();
  ligarFoto('ro-foto', 'rascRec', (foto) => { S.recFoto = foto; const img = $('#ro-prev'); if (foto) { img.src = URL.createObjectURL(foto); img.style.display = ''; $('#ro-foto-ok').textContent = ''; } else img.style.display = 'none'; });
  $('#ro-ok').onclick = () => gravarRecontagem(rid);
}
async function gravarRecontagem(rid) {
  const r = recontagens().find((x) => x.id === rid); if (!r) return;
  const v = $('#ro-vivas').value, m = $('#ro-mortas').value, erro = (t) => { $('#ro-msg').innerHTML = `<div class="msg erro">${esc(t)}</div>`; };
  if (v === '' || !(+v >= 0) || !Number.isInteger(+v)) return erro('Escreva quantas plantas vivas contou.');
  if (m === '' || !(+m >= 0) || !Number.isInteger(+m)) return erro('Escreva quantas plantas mortas contou (0 se nenhuma).');
  $('#ro-ok').disabled = true; $('#ro-msg').innerHTML = '<div class="msg info">A ler o GPS…</div>';
  let g = null; try { g = await lerGPS(); } catch {}
  const k = 'rec-' + rid;
  if (S.recFoto) { try { await FOTOS.guardar(k, S.recFoto); } catch { S.fotosMem = { ...(S.fotosMem || {}), [k]: S.recFoto }; } }
  const x = { id: rid, area_id: r.area_id, vivas: +v, mortas: +m, em: new Date().toISOString(), foto: !!S.recFoto || !!S.recFotoAnt,
    lat: g ? g.latitude : null, lon: g ? g.longitude : null, precisao: g && g.accuracy != null ? Math.round(g.accuracy) : null };
  LS.set('filaRec', [...filaRec().filter((y) => y.id !== rid), x]); LS.del('rascRec');
  actSync(); sincronizar(true);
  abrirFicha(r.area_id, `<div class="msg ok">Recontagem guardada${navigator.onLine ? '' : ' no telefone: é enviada quando houver rede'}.${g ? '' : ' Sem GPS.'}</div>`); actHoje();
}
async function enviarRecontagens() {
  for (const x of filaRec()) {
    const k = 'rec-' + x.id; let foto = null;
    if (x.foto) { try { foto = await FOTOS.ler(k); } catch {} foto = foto || S.fotosMem?.[k] || null; }
    const caminho = `${S.perfil.id}/${x.id}.jpg`;
    if (foto) { const up = await sb.storage.from('recontagem-fotos').upload(caminho, foto, { contentType: 'image/jpeg', upsert: true }); if (up.error) return up.error.message; }
    const r = await sb.rpc('enviar_recontagem', { p_id: x.id, p_vivas: x.vivas, p_mortas: x.mortas, p_foto: foto ? caminho : null, p_lat: x.lat, p_lon: x.lon, p_precisao: x.precisao, p_em: x.em });
    if (r.error && !r.error.code) return r.error.message;
    if (r.error) aviso(`Recontagem não gravada: ${r.error.message}`, 'erro');
    LS.set('filaRec', filaRec().filter((y) => y.id !== x.id));
    try { await FOTOS.apagar(k); } catch {}
  }
  if (souOficial() || gereRecont()) await carregarRecontagens();
  return null;
}
const actHoje = () => { if ($('#e-hoje').classList.contains('on')) desenharHoje(); };
// cartões do Hoje
function cartaoRecontagensHoje() {
  // extra: texto simples a seguir ao motivo; a linha vermelha (recusada) vai à parte para a tradução apanhar cada texto
  const l = recontagens(), item = (r, extra = '') => { const a = S.areas.find((x) => x.id === r.area_id) || {};
    return `<div class="item" onclick="abrirFicha('${esc(r.area_id)}')"><div><div class="nome">${esc(a.produtor || r.produtor || '')}</div><div class="sub">${esc(a.pr || r.pr || '')} · ${esc(a.comunidade || r.comunidade || '')} · ${esc(r.motivo)}${extra}</div>${r.estado === 'recusada' ? `<div class="sub" style="color:#b42318;font-weight:700">${souOficial() ? 'Recusada pelo M&E: fazer de novo' : 'Recusada pelo M&E'}</div>` : ''}</div></div>`; };
  const sec = (tit, rs, f) => rs.length ? `<h3 style="margin:10px 0 4px;font-size:15px">${tit} (${rs.length})</h3>${rs.map((r) => item(r, f ? f(r) : '')).join('')}` : '';
  if (souOficial()) {
    const fazer = l.filter((r) => ['encaminhada', 'recusada'].includes(r.estado)), env = l.filter((r) => r.estado === 'enviada');
    if (!fazer.length && !env.length) return '<div class="cartao"><h2>Recontagens</h2><p>Sem recontagens para fazer.</p></div>';
    return `<div class="cartao" style="border-left:4px solid #6d4c41"><h2>📋 Recontagens</h2>${sec('Para fazer', fazer)}
      ${sec('Enviadas, à espera da validação do M&E', env, (r) => r.local ? ' · no telefone, por enviar' : '')}</div>`;
  }
  if (!gereRecont()) return '';
  const por = l.filter((r) => r.estado === 'por_encaminhar'), val = l.filter((r) => r.estado === 'enviada'), curso = l.filter((r) => ['encaminhada', 'recusada'].includes(r.estado));
  if (!por.length && !val.length && !curso.length)   // o cartão aparece sempre ao M&E e ao gestor, mesmo sem pedidos (18/10/2026, Valdo não o via)
    return '<div class="cartao" style="border-left:4px solid #6d4c41"><h2>📋 Recontagens das plantas</h2><p>Sem recontagens em curso.</p><p class="pequeno">Para pedir uma recontagem: abra o campo no Mapa ou em Campos › 📋 Pedir recontagem das plantas. Cada queimada registada também pede uma.</p></div>';
  return `<div class="cartao" style="border-left:4px solid #6d4c41"><h2>📋 Recontagens das plantas</h2>
    ${sec('Por encaminhar a um oficial', por)}
    ${S.perfil.papel === 'me' ? sec('Por validar', val, (r) => ' · ' + esc(r.oficial || '')) : sec('Feitas, em validação pelo M&E', val)}
    ${sec('Com o oficial', curso, (r) => ' · ' + esc(r.oficial || ''))}</div>`;
}
function ecraQueimada(id, r) {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  const h = hojeISO();
  S.queimFoto = null; if (!r) LS.del('rascQueim');
  folha(`<h2>🔥 Queimada</h2>${r?.camara ? AVISO_CAMARA : ''}<p class="pequeno">${esc(a.produtor)} · ${esc(a.pr)} · ${esc(a.comunidade)}</p>
    <label>Data da queimada<input id="q-data" type="date" max="${h}" value="${h}"></label>
    <label>Plantas afectadas pelo fogo<input id="q-afect" type="number" inputmode="numeric" min="0" placeholder="${a.vivas > 0 ? 'de ' + num(a.vivas) + ' vivas' : ''}"></label>
    <label>Destas, plantas mortas<input id="q-mortas" type="number" inputmode="numeric" min="0"></label>
    <textarea id="q-obs" rows="2" placeholder="Observação (opcional): parte do campo atingida…"></textarea>
    ${campoFoto('q-foto', 'Fotografia da queimada (obrigatória)')}
    <img id="q-prev" alt="" style="display:none;width:100%;max-height:180px;object-fit:cover;border-radius:10px;margin-top:8px">
    <button class="btn" onclick="gravarQueimada('${esc(id)}')">Guardar</button><button class="btn sec" onclick="LS.del('rascQueim');abrirFicha('${esc(id)}')">Cancelar</button>`);
  if (r) { if (r.data) $('#q-data').value = r.data; if (r.obs) $('#q-obs').value = r.obs; if (r.afect != null) $('#q-afect').value = r.afect; if (r.mortas != null) $('#q-mortas').value = r.mortas; }
  const guardar = () => rascGuardar('rascQueim', { perfil: S.perfil?.id, area: id, camara: false, data: $('#q-data').value, obs: $('#q-obs').value, afect: $('#q-afect').value, mortas: $('#q-mortas').value });
  ['#q-data', '#q-obs', '#q-afect', '#q-mortas'].forEach((q) => $(q).addEventListener('input', guardar)); guardar();
  ligarFoto('q-foto', 'rascQueim', (foto) => { S.queimFoto = foto; const img = $('#q-prev'); if (foto) { img.src = URL.createObjectURL(foto); img.style.display = ''; } else img.style.display = 'none'; });
}
async function gravarQueimada(id) {
  const data = $('#q-data').value;
  if (!data || data > hojeISO()) { alert('Escolha a data da queimada (hoje ou antes).'); return; }
  const nAf = $('#q-afect').value === '' ? null : Math.round(+$('#q-afect').value), nMo = $('#q-mortas').value === '' ? null : Math.round(+$('#q-mortas').value);
  if (nAf == null) { alert('Escreva quantas plantas foram afectadas pelo fogo (0 se nenhuma).'); return; }
  if (nAf < 0 || (nMo != null && nMo < 0)) { alert('O número de plantas não pode ser negativo.'); return; }
  if (nMo != null && nMo > nAf) { alert('As plantas mortas não podem ser mais do que as afectadas.'); return; }
  const a0 = S.areas.find((x) => x.id === id), lim = a0 ? (a0.instaladas || a0.vivas || 0) : 0;
  if (lim && nAf > lim && !confirm(`O campo tem ${num(lim)} plantas na base e escreveu ${num(nAf)} afectadas. Gravar mesmo assim?`)) return;
  if (!S.queimFoto) { alert('Tire a fotografia da queimada.'); return; }
  const q = { id: crypto.randomUUID(), area_id: id, data, observacao: $('#q-obs').value.trim() || null, registada_por: S.perfil.id, local: true, lat: null, lon: null, precisao_m: null, plantas_afectadas: nAf, plantas_mortas: nMo };
  if (S.fix && Date.now() - S.fix.t < 60000) { q.lat = S.fix.coords.latitude; q.lon = S.fix.coords.longitude; q.precisao_m = Math.round(S.fix.coords.accuracy); }
  try { await FOTOS.guardar(q.id, S.queimFoto); } catch { S.fotosMem = { ...(S.fotosMem || {}), [q.id]: S.queimFoto }; }
  const f = queimadasLocais(); f.push(q); LS.set('filaQueim', f); LS.del('rascQueim');
  actSync(); aviso('Queimada registada.', 'ok'); abrirFicha(id); desenharMapa(); sincronizar(true);
}
async function removerQueimada(qid, areaId) {
  if (!confirm('Remover esta queimada (registo feito por engano)?')) return;
  const loc = queimadasLocais();
  if (loc.some((x) => x.id === qid)) { LS.set('filaQueim', loc.filter((x) => x.id !== qid)); try { await FOTOS.apagar(qid); } catch {} }
  else {
    if (!navigator.onLine) { aviso('Precisa de rede para remover uma queimada já enviada.', 'erro'); return; }
    const r = await sb.rpc('remover_queimada', { p_id: qid }); if (r.error) { aviso(r.error.message, 'erro'); return; }
    S.queimadas = (S.queimadas || []).filter((x) => x.id !== qid); LS.set('queimadas', S.queimadas);
  }
  actSync(); abrirFicha(areaId); desenharMapa();
}
async function enviarQueimadas() {
  for (const q of queimadasLocais()) {
    let foto = null; try { foto = await FOTOS.ler(q.id); } catch {} foto = foto || S.fotosMem?.[q.id] || null;
    const caminho = `${S.perfil.id}/queimada-${q.id}.jpg`;
    if (foto) { const up = await sb.storage.from('rega-fotos').upload(caminho, foto, { contentType: 'image/jpeg', upsert: true }); if (up.error) return up.error.message; }
    const r = await sb.rpc('gravar_queimada2', { p_id: q.id, p_area: q.area_id, p_data: q.data, p_obs: q.observacao, p_foto: foto ? caminho : null, p_lat: q.lat, p_lon: q.lon, p_precisao: q.precisao_m, p_afectadas: q.plantas_afectadas ?? null, p_mortas: q.plantas_mortas ?? null });
    if (r.error && !r.error.code) return r.error.message;
    if (r.error) aviso(`Queimada não gravada: ${r.error.message}`, 'erro');
    else { S.queimadas = [...(S.queimadas || []), { id: q.id, area_id: q.area_id, data: q.data, observacao: q.observacao, foto_path: foto ? caminho : null, registada_por: S.perfil.id, plantas_afectadas: q.plantas_afectadas ?? null, plantas_mortas: q.plantas_mortas ?? null }]; LS.set('queimadas', S.queimadas); }
    LS.set('filaQueim', queimadasLocais().filter((y) => y.id !== q.id));
    try { await FOTOS.apagar(q.id); } catch {}
  }
  return null;
}
// ---------- chuva (12/10/2026, Valdo; sugestão do Albino) ----------
// O activista lê o pluviómetro da comunidade e regista os milímetros. Funciona sem rede (fila "filaChuva").
// Técnico, supervisor e gestor registam chuva só em teste (13/10/2026, Valdo): não conta no painel.
const chuvaTeste = () => S.perfil?.papel !== 'activista';
// A comunidade da chuva é a do sítio onde a pessoa está (16/10/2026, Valdo: em Quitunda não pode registar outra comunidade).
// A app lê o GPS e escolhe a comunidade do campo activo mais perto (todos os campos, guardados no telefone: funciona sem rede).
// Nas comunidades com bairros (Palma) a pessoa escolhe o bairro dessa comunidade; começa no bairro do campo mais perto.
const CHUVA_MAX_M = 3000;          // mais longe do que isto de qualquer campo: não deixa registar
const pontosChuva = () => (S.pontosCom?.length ? S.pontosCom : S.areas.filter((a) => a.latitude != null && a.longitude != null).map((a) => [a.comunidade, a.zona, a.latitude, a.longitude]));
function localDaChuva(pos) {
  const pts = pontosChuva(); let p0 = null, d0 = Infinity;
  for (const p of pts) { const m = metros(pos, [p[2], p[3]]); if (m < d0) { d0 = m; p0 = p; } }
  if (!p0) return null;
  const com = p0[0], zs = zonasDe(com); let zona = null, dz = Infinity;
  if (zs.length) for (const p of pts) if (p[0] === com && p[1] && zs.includes(p[1])) { const m = metros(pos, [p[2], p[3]]); if (m < dz) { dz = m; zona = p[1]; } }
  return { com, dist: d0, zona };
}
// locais de leitura: a comunidade onde a pessoa está, ou os bairros dessa comunidade (Palma; 14/10/2026, Nuro)
function locaisChuva(com) { const zs = zonasDe(com); return zs.length ? zs.map((z) => ({ com, zona: z })) : [{ com, zona: null }]; }
const nomeLocal = (com, zona) => zona ? `${com} › ${zona}` : com;
function textoChuvaHoje() {
  const h = hojeISO(), g = LS.get('chuvaFeita', {}) || {}, v = Object.entries(g).filter(([k]) => k.startsWith(h + '|'));
  return v.length ? v.map(([k, mm]) => `${num(mm)} mm (${esc(k.split('|').slice(1).join('|'))})`).join(', ') : '—';
}
// linha da chuva no Hoje: depois de registada mostra "✓ Registado" em vez de pedir outra vez (14/10/2026, Nuro)
function linhaChuva(rotulo) {
  const h = hojeISO(), feita = Object.keys(LS.get('chuvaFeita', {}) || {}).some((k) => k.startsWith(h + '|'));
  return feita
    ? `<div class="lin"><span>${rotulo}</span><b><span style="color:var(--ok,#2e7d32)">✓ Registado</span> ${textoChuvaHoje()}</b></div>
       <p class="pequeno" style="margin:2px 0 6px;text-align:right"><button class="chip" onclick="ecraChuva()">Corrigir</button></p>`
    : `<div class="lin"><span>${rotulo}</span><b>— <button class="chip" onclick="ecraChuva()">Registar</button></b></div>`;
}
// ---------- fotografia e rascunhos (14/10/2026, Nuro) ----------
// Em telefones com pouca memória, o Android fecha o Chrome quando a câmara abre e o formulário perdia-se.
// O formulário fica guardado no telefone enquanto se preenche e volta a abrir; e há a opção de escolher a
// fotografia da galeria (tirada antes com a câmara do telefone).
const RASC_MAX = 3 * 3600e3;
const rascLer = (k) => { const r = LS.get(k); return r && Date.now() - (r.ts || 0) < RASC_MAX ? r : null; };
const rascGuardar = (k, v) => LS.set(k, { ...(LS.get(k) || {}), ...v, ts: Date.now() });
function campoFoto(id, rotulo) {
  return `<label>${rotulo}</label><div class="foto-esc" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px">
    <button type="button" class="chip" id="${id}-cambtn">📷 Tirar fotografia</button><label class="chip" for="${id}">🖼️ Escolher da galeria</label>
    <input id="${id}-cam" type="file" accept="image/*" capture="environment" hidden><input id="${id}" type="file" accept="image/*" hidden></div>`;
}
// Câmara dentro da app (14/10/2026, Nuro): com a câmara do sistema o Android fechava o Chrome ao guardar a foto.
// Aqui a imagem vem do vídeo da câmara, sem sair da página. Se o telefone não deixar, usa a câmara do sistema.
async function camaraNaApp(aoFoto) {
  if (!navigator.mediaDevices?.getUserMedia) return false;
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' }, width: { ideal: 1600 }, height: { ideal: 1200 } }, audio: false }); }
  catch (e) {
    if (e && e.name === 'NotAllowedError') { aviso('A app não tem autorização para usar a câmara. Autorize a câmara no Chrome (cadeado ao lado do endereço) ou use «Escolher da galeria».', 'erro'); return true; }
    return false;
  }
  const ov = document.createElement('div'); ov.id = 'cam-ov';
  ov.style.cssText = 'position:fixed;inset:0;background:#000;z-index:9999;display:flex;flex-direction:column';
  ov.innerHTML = `<video autoplay playsinline muted style="flex:1;min-height:0;width:100%;object-fit:contain;background:#000"></video>
    <div style="display:flex;gap:12px;justify-content:center;padding:16px 16px calc(16px + env(safe-area-inset-bottom));background:#000">
      <button type="button" class="btn sec" id="cam-x" style="width:auto;margin:0">Cancelar</button><button type="button" class="btn" id="cam-ok" style="width:auto;margin:0;min-width:140px">📷 Tirar</button></div>`;
  document.body.appendChild(ov);
  const v = ov.querySelector('video'); v.srcObject = stream;
  const fechar = () => { stream.getTracks().forEach((t) => t.stop()); ov.remove(); };
  ov.querySelector('#cam-x').onclick = fechar;
  ov.querySelector('#cam-ok').onclick = () => {
    if (!v.videoWidth) return;
    const k = Math.min(1, 1600 / Math.max(v.videoWidth, v.videoHeight)), c = document.createElement('canvas');
    c.width = Math.round(v.videoWidth * k); c.height = Math.round(v.videoHeight * k); c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
    fechar(); c.toBlob((b) => aoFoto(b), 'image/jpeg', 0.85);
  };
  return true;
}
function ligarFoto(id, rasc, aoLer) {
  const abrir = () => { if (rasc) rascGuardar(rasc, { camara: true }); };
  document.querySelectorAll(`label[for="${id}"]`).forEach((l) => l.addEventListener('click', abrir));
  $(`#${id}-cambtn`).onclick = async () => {
    const ok = await camaraNaApp(async (b) => { if (!b) return aviso('Não foi possível ler a fotografia. Tire outra.', 'erro');
      try { await aoLer(await reduzirFoto(b)); } catch { aoLer(null); aviso('Não foi possível ler a fotografia. Tire outra.', 'erro'); } });
    if (!ok) { abrir(); $(`#${id}-cam`).click(); }               // sem câmara na página: câmara do sistema
  };
  for (const i of [$(`#${id}-cam`), $(`#${id}`)]) i.onchange = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    if (rasc) rascGuardar(rasc, { camara: false });
    try { await aoLer(await reduzirFoto(f)); } catch { aoLer(null); aviso('Não foi possível ler a fotografia. Tire outra.', 'erro'); }
  };
}
const AVISO_CAMARA = '<div class="msg info">O telefone fechou a app ao abrir a câmara. Os dados foram recuperados. Se voltar a acontecer, tire a fotografia com a câmara do telefone e use «Escolher da galeria».</div>';
// primeiro o GPS: só depois se sabe a comunidade
async function ecraChuva(r) {
  folha(`<h2>Chuva</h2><p id="c-gps">A ler o GPS para saber em que comunidade está…</p><button class="btn sec" onclick="LS.del('rascChuva');fecharFolha()">Cancelar</button>`);
  let c;
  try { c = await lerGPS(); }
  catch (e) { if (!$('#c-gps')) return; return folha(`<h2>Chuva</h2><div class="msg erro">${esc(e.message)}</div><p class="pequeno">A chuva só se regista no local do pluviómetro: a app usa o GPS para saber a comunidade.</p>
    <button class="btn" onclick="ecraChuva()">Tentar de novo</button><button class="btn sec" onclick="LS.del('rascChuva');fecharFolha()">Cancelar</button>`); }
  if (!$('#c-gps')) return;                             // cancelou enquanto lia o GPS
  const pos = [c.latitude, c.longitude], loc = localDaChuva(pos);
  if (!loc || loc.dist > CHUVA_MAX_M) return folha(`<h2>Chuva</h2><div class="msg erro">${loc ? `Está a ${num(Math.round(loc.dist / 100) / 10)} km do campo mais perto (${esc(loc.com)}).` : 'Não há campos com coordenada no telefone.'} Registe a chuva junto ao pluviómetro, na comunidade.</div>
    <button class="btn" onclick="ecraChuva()">Tentar de novo</button><button class="btn sec" onclick="LS.del('rascChuva');fecharFolha()">Cancelar</button>`);
  S.chuvaPos = { lat: c.latitude, lon: c.longitude, precisao: c.accuracy != null ? Math.round(c.accuracy) : null };
  const locais = locaisChuva(loc.com), h = hojeISO(), ontem = new Date(Date.now() - 864e5).toLocaleDateString('sv-SE');
  const agora = new Date().toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' });
  S.chuvaFoto = null; if (!r) LS.del('rascChuva');
  folha(`<h2>Chuva</h2>${r?.camara ? AVISO_CAMARA : ''}${chuvaTeste() ? '<div class="msg info">Registo de teste: não conta no painel.</div>' : ''}<p class="pequeno">Leia o pluviómetro da comunidade, escreva os milímetros e tire uma fotografia da leitura. Se não choveu, carregue em "Não choveu".</p>
    <label>Dia da chuva<select id="c-data"><option value="${h}">Hoje · ${fmtData(h)}</option><option value="${ontem}">Ontem · ${fmtData(ontem)}</option></select></label>
    <label>Hora da leitura<input id="c-hora" type="time" value="${agora}"></label>
    <p class="pequeno">Pelo GPS está em <b>${esc(loc.com)}</b>. Só pode registar a chuva da comunidade onde está.</p>
    <label>${locais.length > 1 ? 'Bairro' : 'Comunidade'}<select id="c-com">${locais.map((l, i) => { const feito = (LS.get('chuvaFeita', {}) || {})[h + '|' + nomeLocal(l.com, l.zona)];
      return `<option value="${i}">${esc(nomeLocal(l.com, l.zona))}${feito != null ? ` · registado hoje (${num(feito)} mm)` : ''}</option>`; }).join('')}</select></label>
    <label>Chuva no pluviómetro (mm)<input id="c-mm" type="number" inputmode="decimal" min="0" max="500" step="0.1"></label>
    <button class="chip" onclick="$('#c-mm').value='0';$('#c-mm').dispatchEvent(new Event('input'))">Não choveu (0 mm)</button>
    ${campoFoto('c-foto', 'Fotografia da leitura do pluviómetro')}
    <img id="c-prev" alt="" style="display:none;width:100%;max-height:180px;object-fit:cover;border-radius:10px;margin-top:8px">
    <textarea id="c-obs" rows="2" placeholder="Observação (opcional)"></textarea>
    <button class="btn" onclick="gravarChuva()">Guardar</button><button class="btn sec" onclick="LS.del('rascChuva');fecharFolha()">Cancelar</button>`);
  S.chuvaLocais = locais;
  if (r) {                                              // repõe o rascunho
    if (r.data && [...$('#c-data').options].some((o) => o.value === r.data)) $('#c-data').value = r.data;
    if (r.hora) $('#c-hora').value = r.hora; if (r.mm != null) $('#c-mm').value = r.mm; if (r.obs) $('#c-obs').value = r.obs;
    const i = locais.findIndex((l) => nomeLocal(l.com, l.zona) === r.local); if (i >= 0) $('#c-com').value = String(i);
  }
  else if (loc.zona) { const i = locais.findIndex((l) => l.zona === loc.zona); if (i >= 0) $('#c-com').value = String(i); }   // bairro do campo mais perto
  const guardar = () => rascGuardar('rascChuva', { perfil: S.perfil?.id, camara: false, data: $('#c-data').value, hora: $('#c-hora').value, mm: $('#c-mm').value, obs: $('#c-obs').value,
    local: (() => { const l = S.chuvaLocais?.[+$('#c-com').value]; return l ? nomeLocal(l.com, l.zona) : ''; })() });
  ['#c-data', '#c-hora', '#c-com', '#c-mm', '#c-obs'].forEach((q) => $(q).addEventListener('input', guardar));
  ['#c-data', '#c-com'].forEach((q) => $(q).addEventListener('change', guardar));
  if (r?.camara) setTimeout(guardar, 0); else guardar();
  ligarFoto('c-foto', 'rascChuva', (foto) => { S.chuvaFoto = foto; const img = $('#c-prev'); if (foto) { img.src = URL.createObjectURL(foto); img.style.display = ''; } else img.style.display = 'none'; });
}
async function gravarChuva() {
  const mm = parseFloat(String($('#c-mm').value).replace(',', '.'));
  if (!(mm >= 0 && mm <= 500)) { alert('Escreva os milímetros (0 a 500).'); return; }
  const hora = $('#c-hora').value; if (!hora) { alert('Escreva a hora da leitura.'); return; }
  if (!S.chuvaFoto) { alert('Tire a fotografia da leitura do pluviómetro.'); return; }
  const data = $('#c-data').value, [hh, mi] = hora.split(':'), t = new Date(data + 'T00:00:00'); t.setHours(+hh, +mi, 0, 0);
  const teste = chuvaTeste(), loc = S.chuvaLocais[+$('#c-com').value], com = loc.com, zona = loc.zona, chave = data + '|' + nomeLocal(com, zona);
  // no teste não há activista: o mesmo dia+local reutiliza o id para corrigir em vez de duplicar
  const ids = LS.get('chuvaTesteIds', {}) || {}, id = (teste && ids[chave]) || crypto.randomUUID();
  if (teste) { ids[chave] = id; LS.set('chuvaTesteIds', ids); }
  const c = { id, data, comunidade: com, zona, mm, lida_em: t.toISOString(), activista_id: teste ? null : S.perfil.activista_id, user_id: S.perfil.id, observacao: $('#c-obs').value.trim() || null, teste,
    lat: S.chuvaPos?.lat ?? null, lon: S.chuvaPos?.lon ?? null, precisao_m: S.chuvaPos?.precisao ?? null };
  try { await FOTOS.guardar(c.id, S.chuvaFoto); } catch { S.fotosMem = { ...(S.fotosMem || {}), [c.id]: S.chuvaFoto }; }
  const f = LS.get('filaChuva', []).filter((x) => !(x.data === c.data && x.comunidade === c.comunidade && (x.zona || null) === zona)); f.push(c); LS.set('filaChuva', f);
  const g = LS.get('chuvaFeita', {}) || {}; g[chave] = mm; LS.set('chuvaFeita', g);
  LS.del('rascChuva');
  fecharFolha(); actSync(); sincronizar(true); if ($('#e-hoje').classList.contains('on')) desenharHoje();
  aviso(`Chuva guardada: ${num(mm)} mm em ${nomeLocal(com, zona)}.` + (teste ? ' (teste)' : ''), 'ok');
}
// ---------- hoje ----------
const tamanhoEquipa = (id) => (S.activistas.find((t) => t.id === id) || {}).equipa_tamanho || null;   // null = por definir
// "4/5 · 1 falta" (faltas a vermelho)
function textoEquipa(presentes, tamanho) {
  if (!tamanho) return `${presentes} <span class="pequeno">(equipa por definir)</span>`;
  const f = tamanho - presentes;
  return `${presentes}/${tamanho}` + (f > 0 ? ` <span style="color:var(--crit,#b42318);font-weight:700">· ${f} ${f === 1 ? 'falta' : 'faltas'}</span>` : '');
}
// tempo médio (min) entre a saída de um campo e a entrada no seguinte, no mesmo dia
function deslocacao(regs) {
  const o = regs.filter((x) => x.entrada_em && x.saida_em).sort((a, b) => a.entrada_em.localeCompare(b.entrada_em)), m = [];
  for (let i = 1; i < o.length; i++) { const d = (new Date(o[i].entrada_em) - new Date(o[i - 1].saida_em)) / 60000; if (d >= 0) m.push(d); }
  return m.length ? Math.round(m.reduce((a, b) => a + b, 0) / m.length) : null;
}
function ecraTamanho(id) {
  folha(`<h2>${esc(nomeAct(id))}</h2>
    <label>Quantas pessoas tem esta equipa (incluindo o activista)?<input id="t-n" type="number" inputmode="numeric" min="1" max="30" value="${tamanhoEquipa(id) ?? ''}"></label>
    <p class="pequeno">Serve para mostrar as faltas: pessoas presentes no dia comparadas com este número.</p>
    <button class="btn" onclick="gravarTamanho('${esc(id)}')">Guardar</button><button class="btn sec" onclick="fecharFolha()">Cancelar</button>`);
}
async function gravarTamanho(id) {
  const n = parseInt($('#t-n').value, 10);
  if (!(n >= 1 && n <= 30)) { alert('Escreva um número entre 1 e 30.'); return; }
  const r = await sb.rpc('definir_equipa_tamanho', { p_activista: id, p_n: n });
  if (r.error) return aviso(r.error.message, 'erro');
  const t = S.activistas.find((x) => x.id === id); if (t) t.equipa_tamanho = n; LS.set('activistas', S.activistas);
  fecharFolha(); desenharHoje();
}
async function desenharHoje() {
  const h = hojeISO(), local = filaRegistos().filter((r) => r.data === h);
  const guardado = LS.get('hojeHtml');
  if (guardado && guardado.d === h && guardado.p === S.perfil.papel && !$('#hoje').innerHTML.trim()) $('#hoje').innerHTML = guardado.html;
  let html = `<div class="cartao"><h2>Hoje · ${fmtData(h)}</h2>`;
  if (['activista', 'tecnico', 'supervisor', 'gestor'].includes(S.perfil.papel)) { if (navigator.onLine) await carregarAvisos(); }
  if (souOficial()) {                                    // oficial de M&E: só as recontagens (18/10/2026, Valdo)
    if (navigator.onLine) await carregarRecontagens();
    $('#hoje').innerHTML = cartaoRecontagensHoje(); return;
  }
  if (S.perfil.papel === 'activista') {
    let serv = [];
    if (navigator.onLine) { const r = await sb.from('registos_rega').select('id,area_id,entrada_em,saida_em,plantas_regadas,alerta,agua_em').eq('data', h).order('entrada_em'); serv = r.data || []; }
    const ids = new Set(serv.map((x) => x.id)), todos = [...serv, ...local.filter((x) => !ids.has(x.id))];
    const tot = todos.reduce((s, x) => s + (x.plantas_regadas || 0), 0);
    const j = jornadaHoje();
    html += `<div class="lin"><span>Ronda</span><b>${textoRonda()}</b></div>
      <div class="lin"><span>Pessoas hoje</span><b>${j ? textoEquipa(j.pessoas, tamanhoEquipa(S.perfil.activista_id)) : '—'} <button class="chip" onclick="ecraJornada()">${j ? 'Alterar' : 'Registar'}</button></b></div>
      ${linhaChuva('Chuva (pluviómetro)')}
      <div class="lin"><span>Campos regados hoje</span><b>${todos.length}</b></div><div class="lin"><span>Plantas regadas hoje</span><b>${num(tot)}</b></div><div class="lin"><span>Por enviar</span><b>${local.length}</b></div></div>`;
    html += todos.map((x) => { const a = S.areas.find((y) => y.id === x.area_id) || {}; return `<div class="item"><div><div class="nome">${esc(a.produtor)}</div><div class="sub">${fmtHora(x.entrada_em)}–${fmtHora(x.saida_em)} · ${num(x.plantas_regadas)} plantas${x.agua_em ? ' · água ' + fmtHora(x.agua_em) : ''}${x.alerta ? ' · fora da lista' : ''}</div></div></div>`; }).join('');
  } else {
    if (['tecnico', 'supervisor'].includes(S.perfil.papel)) { if (navigator.onLine) await carregarMonitoria(); html = cartaoMonitoria() + html; }
    if (gereRecont()) { if (navigator.onLine) await carregarRecontagens(); html = cartaoRecontagensHoje() + html; }   // recontagens das plantas (18/10/2026, Valdo)
    const podeMudar = ['gestor', 'tecnico', 'supervisor'].includes(S.perfil.papel);
    if (podeMudar) html += linhaChuva('Chuva (pluviómetro) · teste');
    // sem rede: não pede ao servidor (14/10/2026, Nuro: aparecia "Failed to fetch")
    const r = navigator.onLine ? await sb.from('registos_rega').select('activista_id,area_id,plantas_regadas,alerta,gps_valido,teste,entrada_em,saida_em,pessoas,agua_em').eq('data', h) : { error: { semRede: true } };
    if (r.error && (r.error.semRede || /fetch|network|rede/i.test(r.error.message || ''))) {
      // sem rede: mostra o último resumo das equipas guardado no telefone (16/10/2026, Nuro)
      const ult = LS.get('hojeEquipas');
      if (ult && ult.d === h) html += `<div class="msg info">Sem rede. Resumo das equipas guardado às ${fmtHora(ult.em)}; pode não ter as últimas regas.</div>${ult.html}`;
      else html += `<div class="msg info">Sem rede. O resumo das equipas de hoje aparece quando houver rede.</div></div>`;
    }
    else if (r.error) html += `<div class="msg erro">${esc(r.error.message)}</div></div>`;
    else {
      // uma linha por equipa: produtores com rega, pessoas (faltas), campos, plantas, tuk-tuk, início, fim e deslocação entre campos
      const g = {}; for (const x of r.data) { const k = x.activista_id; g[k] ??= { campos: 0, plantas: 0, alertas: 0, teste: 0, ini: null, fim: null, prod: new Set(), agua: null, pessoas: 0, regs: [] };
        const o = g[k]; o.campos++; o.plantas += x.plantas_regadas || 0; if (x.alerta) o.alertas++; if (x.teste) o.teste++; o.regs.push(x);
        o.prod.add((S.areas.find((a) => a.id === x.area_id) || {}).produtor || x.area_id); if (x.agua_em && (!o.agua || x.agua_em < o.agua)) o.agua = x.agua_em;
        if (x.pessoas > o.pessoas) o.pessoas = x.pessoas;
        if (!o.ini || x.entrada_em < o.ini) o.ini = x.entrada_em; if (!o.fim || x.saida_em > o.fim) o.fim = x.saida_em; }
      let eqHtml = `<div class="lin"><span>Registos recebidos</span><b>${r.data.length}</b></div><button class="btn sec" onclick="mudar('painel')">Abrir painel geral</button></div>
        <div style="overflow-x:auto"><table><tr><th>Activista</th><th>Equipa</th><th class="n">Produtores</th><th class="n">Campos</th><th class="n">Plantas</th><th class="n">% meta</th><th>Tuk-tuk</th><th>Início</th><th>Fim</th><th class="n">Desloc.</th><th class="n">Alertas</th></tr>` +
        Object.entries(g).map(([k, o]) => { const tam = tamanhoEquipa(k), d = deslocacao(o.regs);
          const eq = o.pessoas ? textoEquipa(o.pessoas, tam) : '—';
          return `<tr><td>${esc(nomeAct(k))}${o.teste ? ' <span class="pequeno">(teste)</span>' : ''}</td>
          <td>${podeMudar && S.activistas.some((t) => t.id === k) ? `<button class="chip" onclick="ecraTamanho('${esc(k)}')">${eq}</button>` : eq}</td>
          <td class="n">${o.prod.size}</td><td class="n">${o.campos}</td><td class="n">${num(o.plantas)}</td><td class="n">${o.pessoas ? Math.round(100 * o.plantas / (CFG.metaPlantas * o.pessoas)) + '%' : '—'}</td>
          <td>${fmtHora(o.agua)}</td><td>${fmtHora(o.ini)}</td><td>${fmtHora(o.fim)}</td><td class="n">${d != null ? d + ' min' : '—'}</td><td class="n">${o.alertas}</td></tr>`; }).join('') + '</table></div>' +
        `<p class="pequeno">Equipa = pessoas presentes / pessoas da equipa (faltas a vermelho)${podeMudar ? '; toque para mudar o número de pessoas da equipa' : ''}. Produtores = produtores com campos regados hoje. % meta = plantas regadas ÷ (${CFG.metaPlantas} × pessoas presentes). Tuk-tuk = hora da 1.ª chegada da água. Início = entrada no 1.º campo; Fim = saída do último. Desloc. = tempo médio entre a saída de um campo e a entrada no seguinte. Alertas = regas fora da lista da equipa.</p>`;
      LS.set('hojeEquipas', { d: h, em: new Date().toISOString(), html: eqHtml }); html += eqHtml;
    }
  }
  html = cartaoAvisos() + html;   // "Sair" fica só no botão do topo (13/10/2026, Valdo)
  $('#hoje').innerHTML = html;
  if (navigator.onLine) LS.set('hojeHtml', { d: h, p: S.perfil.papel, html });
}

// ---------- fotografias (12/10/2026, Valdo): só se descarregam quando se toca em "Ver fotografia" ----------
// o activista só vê as fotografias que ele próprio tirou (18/10/2026, Valdo); o servidor também recusa as outras
function fotoVisivel(caminho) {
  return !!caminho && (S.perfil?.papel !== 'activista' || String(caminho).startsWith((S.perfil?.id || '-') + '/'));
}
async function verFoto(balde, caminho, legenda = '') {
  const m = document.createElement('div');
  m.id = 'foto-modal'; m.style.cssText = 'position:fixed;inset:0;z-index:3000;background:rgba(0,0,0,.88);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px;color:#fff;text-align:center';
  m.innerHTML = '<p>A abrir a fotografia…</p>'; m.onclick = () => m.remove(); document.body.appendChild(m);
  const r = await sb.storage.from(balde).createSignedUrl(caminho, 600);
  if (r.error) { m.innerHTML = `<p>${esc(/not found|Object/i.test(r.error.message) ? 'A fotografia ainda não chegou ao servidor.' : 'Sem acesso a esta fotografia ou sem rede.')}</p><p class="pequeno">Toque para fechar.</p>`; return; }
  m.innerHTML = `<img src="${esc(r.data.signedUrl)}" alt="" style="max-width:100%;max-height:80vh;border-radius:8px"><p style="margin-top:10px">${esc(legenda)}</p><p class="pequeno" style="color:#ddd">Toque para fechar.</p>`;
}
// últimas regas do campo com as fotografias (15/10/2026, Valdo): a imagem só se descarrega ao tocar
async function regasDoCampo(id) {
  const r = await sb.rpc('regas_campo', { p_area: id }); const el = $('#f-regas');
  if (r.error || !el || !Array.isArray(r.data) || !r.data.length) return;
  const bt = (v, t, rot) => fotoVisivel(v['foto_' + t]) ? `<button class="chip" onclick="verFoto('rega-fotos', '${esc(v['foto_' + t])}', '${esc(rot)} · ${esc(fmtData(v.data))} ${esc(fmtHora(v['foto_' + t + '_em'] || v.entrada_em))} · ${esc(v.quem || '')}')">📷 ${rot}</button>` : '';
  el.innerHTML = `<div class="cartao" style="margin-top:10px"><h2>Regas deste campo</h2>` + r.data.map((v) => `<div style="padding:6px 0;border-bottom:1px solid var(--linha,#e5e5e5)">
      <div class="lin" style="border:0;padding:0"><span>${fmtData(v.data)} · ${fmtHora(v.entrada_em)}–${v.saida_em ? fmtHora(v.saida_em) : '…'}${v.teste ? ' <span class="tag t-teste">teste</span>' : ''}</span><b>${num(v.plantas_regadas)} plantas</b></div>
      <div class="pequeno">${esc(v.quem || '')}</div>
      ${['entrada', 'rega', 'saida'].some((t) => fotoVisivel(v['foto_' + t])) ? `<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px">${bt(v, 'entrada', 'Entrada')}${bt(v, 'rega', 'Rega')}${bt(v, 'saida', 'Saída')}</div>` : `<div class="pequeno">${v.foto_entrada || v.foto_rega || v.foto_saida || v.fotos_outro ? 'Fotografias tiradas por outra pessoa.' : 'Sem fotografias.'}</div>`}</div>`).join('') + '</div>';
}
async function monitoriasDoCampo(id) {
  const r = await sb.rpc('monitorias_campo', { p_area: id }); const el = $('#f-mon');
  if (r.error || !el || !Array.isArray(r.data) || !r.data.length) return;
  el.innerHTML = `<div class="cartao" style="margin-top:10px"><h2>Monitoria deste campo</h2>` + r.data.map((v) => `<div class="lin"><span>${fmtData(v.data_rega)} · ${esc(v.verificador || '')}</span><b>nota ${Number(v.nota).toLocaleString(LOC)}${v.solo_regado === false ? ' · <span style="color:#b42318">não regado</span>' : ''}
      ${fotoVisivel(v.foto_path) ? ` <button class="chip" onclick="verFoto('monitoria-fotos', '${esc(v.foto_path)}', 'Monitoria · rega de ${esc(fmtData(v.data_rega))} · nota ${esc(String(v.nota))}')">Ver fotografia</button>` : ''}</b></div>`).join('') + '</div>';
}

// ---------- avisos da monitoria à equipa (11/10/2026, Valdo) ----------
// Campos verificados nos últimos 14 dias com plantas sem solo húmido. Vermelho = campo não regado (< 80%).
async function carregarAvisos() {
  const r = await sb.rpc('avisos_monitoria');
  if (!r.error && Array.isArray(r.data)) { S.avisos = r.data; LS.set('avisos', S.avisos); }
}
const avisos = () => (Array.isArray(S.avisos) ? S.avisos : LS.get('avisos', []) || []);
const textoAviso = (v) => `${v.sem_rega} de ${v.plantas_obs} plantas sem solo húmido · nota ${Number(v.nota).toLocaleString(LOC)}`;
function cartaoAvisos() {
  const L = avisos(); if (!L.length) return '';
  const varias = S.perfil.papel !== 'activista';
  return `<div class="cartao"><h2>Avisos da monitoria</h2><p class="pequeno">Campos verificados nos últimos 14 dias com plantas sem solo húmido.</p>` +
    L.map((v) => { const a = S.areas.find((x) => x.id === v.area_id) || { produtor: v.area_id };
      return `<div class="item" onclick="abrirFicha('${esc(v.area_id)}')"><div><div class="nome">${esc(a.produtor)}</div>
        <div class="sub">${esc(a.pr || '')}${varias ? ' · ' + esc(nomeAct(v.activista_id)) : ''} · rega de ${fmtData(v.data_rega)} · ${textoAviso(v)}</div></div>
        <span class="tag ${v.solo_regado ? 't-por' : 't-alerta'}">${v.solo_regado ? 'Rever plantas' : 'Campo não regado'}</span></div>`; }).join('') + '</div>';
}
function avisoCampo(id) {
  const v = avisos().find((x) => x.area_id === id); if (!v) return '';
  return `<div class="msg ${v.solo_regado ? 'info' : 'erro'}"><b>Monitoria (rega de ${fmtData(v.data_rega)}):</b> <span>${v.sem_rega} de ${v.plantas_obs} plantas sem solo húmido</span> · <span>nota ${Number(v.nota).toLocaleString(LOC)}</span>.<span>${v.solo_regado ? ' Campo considerado regado (≥ 80%), mas reveja as plantas sem rega.' : ' Campo considerado não regado (menos de 80% das plantas com solo húmido).'}</span>${v.observacao ? `<br><span>Observação: ${esc(v.observacao)}</span>` : ''}</div>`;
}

// ---------- monitoria por amostragem (técnico e supervisor) ----------
// A partir das 18:00 o servidor sorteia campos regados nesse dia; cada pessoa recebe a sua lista (sem campos repetidos entre pessoas).
// A verificação faz-se no campo (GPS), com nota de 0 a 10 e uma fotografia reduzida no telefone (~150 KB). Funciona sem rede.
async function carregarMonitoria() {
  const r = await sb.rpc('monitoria_lista');
  if (!r.error && Array.isArray(r.data)) { S.mon = r.data; LS.set('mon', S.mon); }
}
const monFeita = (m) => m.feita || LS.get('filaMon', []).some((x) => x.amostra_id === m.amostra_id) || (LS.get('monFeitas', [])).includes(m.amostra_id);
function cartaoMonitoria() {
  const lista = Array.isArray(S.mon) ? S.mon : [];
  if (!lista.length) return '<div class="cartao"><h2>Monitoria</h2><p class="pequeno">Sem campos para verificar. A lista sai a partir das 18:00, com campos regados nesse dia.</p></div>';
  const feitas = lista.filter(monFeita).length;
  return `<div class="cartao"><h2>Monitoria · regas de ${fmtData(lista[0].data_rega)}</h2><p class="pequeno">${feitas} de ${lista.length} campos verificados.</p>` +
    lista.map((m) => { const a = S.areas.find((x) => x.id === m.area_id) || { produtor: m.area_id };
      const d = S.pos ? distCampo(a, S.pos) : null;
      return `<div class="item" onclick="abrirFicha('${esc(m.area_id)}')"><div><div class="nome">${esc(a.produtor)}</div><div class="sub">${esc(a.pr || '')} · ${esc(a.comunidade || '')} · ${esc(nomeAct(m.activista_id))}${d != null ? ' · ' + (d < 1000 ? Math.round(d) + ' m' : (d / 1000).toFixed(1) + ' km') : ''}</div></div>
        ${monFeita(m) ? '<span class="tag t-feita">Verificado</span>' : '<span class="tag t-por">Por verificar</span>'}</div>`; }).join('') + '</div>';
}
function botaoMonitoria(a) {
  const m = (Array.isArray(S.mon) ? S.mon : []).find((x) => x.area_id === a.id);
  if (!m) return '';
  return monFeita(m) ? '<div class="msg ok">Monitoria: campo já verificado.</div>'
    : `<button class="btn" onclick="ecraMonitoria('${esc(m.amostra_id)}')">✓ Verificar este campo (monitoria)</button>`;
}
const escolha = (id, ops) => `<div class="chips" id="${id}">${ops.map(([v, t]) => `<button class="chip" data-v="${v}">${t}</button>`).join('')}</div>`;
// Monitoria por planta (11/10/2026, Valdo): o técnico escolhe o percurso (X, W, Z, diagonal) e regista cada planta observada:
// solo húmido (rega efectiva) sim/não + viva/seca/morta. Nota = % de plantas com solo húmido ÷ 10. Campo regado se ≥ 80%.
// Número de plantas a observar: amostra de Cochran (95%, ±10%, p = 80%) com correcção para população finita.
// Nos campos pequenos a amostra aproxima-se do total de plantas (até 6 plantas: todas).
function tamanhoAmostra(N) {
  if (!(N > 0)) return 0;
  const n0 = CFG.monZ ** 2 * CFG.monP * (1 - CFG.monP) / CFG.monMargem ** 2;
  return Math.min(N, Math.ceil(n0 / (1 + (n0 - 1) / N)));
}
const METODOS = { X: 'M12 12L88 88M88 12L12 88', W: 'M10 12L30 88L50 30L70 88L90 12', Z: 'M12 12L88 12L12 88L88 88', Diagonal: 'M12 12L88 88' };
const desenhoMetodo = (m) => `<svg viewBox="0 0 100 100" width="96" height="96" aria-hidden="true" style="flex:none"><rect x="4" y="4" width="92" height="92" rx="6" fill="#eef4ea" stroke="#9fb59a"/><path d="${METODOS[m]}" fill="none" stroke="#1f5130" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1 9"/><path d="${METODOS[m]}" fill="none" stroke="#1f5130" stroke-width="1.5" opacity=".5"/></svg>`;
function ecraMonitoria(amostraId, r) {
  const m = S.mon.find((x) => x.amostra_id === amostraId), a = S.areas.find((x) => x.id === m.area_id) || {};
  S.monFoto = null;
  if (r && r.amostraId === amostraId && r.P) S.monP = r.P;   // rascunho guardado no telefone (14/10/2026)
  else { LS.del('rascMon'); r = null; S.monP = { amostraId, metodo: null, N: plantasN(a) || 0, obs: [], h: null, e: null, c: null }; }
  folha(`<h2>${esc(a.produtor)}</h2>${r?.camara ? AVISO_CAMARA : ''}<p class="pequeno">${esc(a.pr || '')} · ${esc(a.comunidade || '')} · ${esc(nomeAct(m.activista_id))} · rega de ${fmtData(m.data_rega)}</p>
    <label>Percurso no campo</label>${escolha('m-metodo', Object.keys(METODOS).map((k) => [k, k]))}
    <div id="m-desenho" style="display:flex;gap:12px;align-items:center;margin-top:8px"></div>
    <div class="cartao" style="margin-top:10px"><div class="lin"><span>Plantas no campo</span><b id="m-Nv">${S.monP.N ? num(S.monP.N) : '—'}</b></div>
      <p class="pequeno" id="m-Nfonte" style="margin:4px 0 0">${S.monP.N ? `Da base (${plantasTxt(a)}). A app calcula a amostra a partir deste número.` : 'A base não tem o número de plantas deste campo. Conte as plantas e escreva o número.'}</p>
      <div id="m-Nedit" ${S.monP.N ? 'hidden' : ''}><label>Plantas que existem hoje no campo<input id="m-N" type="number" inputmode="numeric" min="1" value="${S.monP.N || ''}"></label></div>
      ${S.monP.N ? `<button class="chip" id="m-Nmudar" style="margin-top:6px">O número de plantas mudou? Corrigir</button>` : ''}</div>
    <div id="m-planta"></div>
    ${campoFoto('m-foto', 'Fotografia do campo')}
    <img id="m-prev" alt="" style="display:none;width:100%;max-height:180px;object-fit:cover;border-radius:10px;margin-top:8px">
    <textarea id="m-obs" rows="2" placeholder="Observação (opcional)"></textarea>
    <button class="btn" id="m-gravar" onclick="gravarMonitoria('${esc(amostraId)}')">Gravar verificação</button>
    <button class="btn sec" onclick="LS.del('rascMon');abrirFicha('${esc(m.area_id)}')">Voltar</button>`);
  document.querySelectorAll('#m-metodo .chip').forEach((b) => b.onclick = () => {
    document.querySelectorAll('#m-metodo .chip').forEach((x) => x.classList.toggle('on', x === b)); S.monP.metodo = b.dataset.v; desenharPlantaMon(); });
  $('#m-N').oninput = () => { S.monP.N = parseInt($('#m-N').value, 10) || 0; S.monP.Ncorrigido = true; $('#m-Nv').textContent = S.monP.N ? num(S.monP.N) : '—';
    $('#m-Nfonte').textContent = 'Corrigido no campo. A app recalcula a amostra.'; desenharPlantaMon(); };
  if ($('#m-Nmudar')) $('#m-Nmudar').onclick = () => { $('#m-Nedit').hidden = false; $('#m-Nmudar').remove(); $('#m-N').focus(); };
  ligarFoto('m-foto', 'rascMon', (foto) => { S.monFoto = foto; const img = $('#m-prev'); if (foto) { img.src = URL.createObjectURL(foto); img.style.display = ''; } else img.style.display = 'none'; });
  if (r) {
    if (r.obsTxt) $('#m-obs').value = r.obsTxt;
    if (S.monP.metodo) document.querySelectorAll('#m-metodo .chip').forEach((x) => x.classList.toggle('on', x.dataset.v === S.monP.metodo));
    if (S.monP.Ncorrigido) { $('#m-Nv').textContent = S.monP.N ? num(S.monP.N) : '—'; $('#m-Nfonte').textContent = 'Corrigido no campo. A app recalcula a amostra.'; $('#m-N').value = S.monP.N || ''; }
  }
  $('#m-obs').addEventListener('input', () => rascGuardar('rascMon', { obsTxt: $('#m-obs').value }));
  if (r?.camara) rascGuardar('rascMon', { camara: false });
  desenharPlantaMon();
}
function resumoMon(obs) {
  const n = obs.length, h = obs.filter((o) => o.humido).length, pc = n ? Math.round(1000 * h / n) / 10 : 0;
  return { n, h, pct: pc, nota: Math.round(pc) / 10, regado: n > 0 && pc >= CFG.monLimiar,
    vivas: obs.filter((o) => o.estado === 'viva').length, secas: obs.filter((o) => o.estado === 'seca').length, mortas: obs.filter((o) => o.estado === 'morta').length,
    cob: obs.filter((o) => o.cobertura).length, cava: obs.filter((o) => o.cavaroda).length };
}
function desenharPlantaMon() {
  if (S.monP && $('#m-planta')) rascGuardar('rascMon', { amostraId: S.monP.amostraId, perfil: S.perfil?.id, P: S.monP });
  const P = S.monP, alvo = tamanhoAmostra(P.N), r = resumoMon(P.obs), el = $('#m-planta'); if (!el) return;
  $('#m-desenho').innerHTML = P.metodo ? desenhoMetodo(P.metodo) + `<p class="pequeno" style="margin:0">Siga o percurso ${esc(P.metodo)} e observe as plantas a intervalos regulares${alvo && P.N > alvo ? ` (cerca de 1 em cada ${Math.max(1, Math.round(P.N / alvo))})` : ' (todas as plantas)'}.</p>` : '';
  if (!P.metodo || !alvo) { el.innerHTML = `<p class="pequeno">${!P.metodo ? 'Escolha o percurso.' : 'Escreva o número de plantas no campo.'}</p>`; return; }
  const feito = r.n >= alvo;
  el.innerHTML = `<div class="cartao" style="margin-top:10px">
      <div class="lin"><span>Plantas a observar</span><b>${alvo}${alvo === P.N ? ' (todas)' : ` de ${P.N}`}</b></div>
      <div class="lin"><span>Observadas</span><b>${r.n} de ${alvo}</b></div>
      <div class="lin"><span>Com solo húmido</span><b>${r.n ? r.pct.toLocaleString(LOC) + '%' : '—'}</b></div>
      <div class="lin"><span>Nota</span><b>${r.n ? r.nota.toLocaleString(LOC) : '—'}</b></div>
      <div class="lin"><span>Campo regado (≥ ${CFG.monLimiar}%)</span><b>${r.n ? (r.regado ? 'Sim' : '<span style="color:#b42318">Não</span>') : '—'}</b></div>
      <div class="lin"><span>Vivas / secas / mortas</span><b>${r.vivas} / ${r.secas} / ${r.mortas}</b></div>
      <div class="lin"><span>Com mulching / com cava-roda</span><b>${r.n ? `${r.cob} / ${r.cava} de ${r.n}` : '—'}</b></div></div>
    <h3 style="margin:14px 0 4px">${feito ? 'Amostra completa' : `Planta ${r.n + 1}`}</h3>
    ${feito ? '<p class="pequeno">Pode observar mais plantas, se quiser.</p>' : ''}
    <label>Solo húmido (rega efectiva)?</label>${escolha('m-h', [['1', 'Sim'], ['0', 'Não']])}
    <label>Estado da planta</label>${escolha('m-e', [['viva', 'Viva'], ['seca', 'Seca'], ['morta', 'Morta']])}
    <label>Mulching e cava-roda</label>${escolha('m-c', [['ambos', 'Os dois'], ['mulching', 'Só mulching'], ['cava', 'Só cava-roda'], ['nenhum', 'Nenhum']])}
    <p class="pequeno">Com mulching (cobertura morta), um campo regado na véspera ainda mostra humidade.</p>
    ${r.n ? '<button class="btn sec" onclick="desfazerPlantaMon()">Desfazer a última planta</button>' : ''}`;
  for (const [g, k] of [['m-h', 'h'], ['m-e', 'e'], ['m-c', 'c']]) document.querySelectorAll(`#${g} .chip`).forEach((b) => b.onclick = () => {
    P[k] = b.dataset.v; document.querySelectorAll(`#${g} .chip`).forEach((x) => x.classList.toggle('on', x === b));
    if (P.h != null && P.e != null && P.c != null) { P.obs.push({ humido: P.h === '1', estado: P.e, cobertura: ['ambos', 'mulching'].includes(P.c), cavaroda: ['ambos', 'cava'].includes(P.c) }); P.h = P.e = P.c = null; desenharPlantaMon(); }
  });
}
function desfazerPlantaMon() { S.monP.obs.pop(); desenharPlantaMon(); }
const escolhido = (g) => document.querySelector(`#${g} .chip.on`)?.dataset.v;
// reduz a fotografia no telefone: lado maior 1024 px, JPEG 60% (≈150 KB em vez de 3–5 MB)
async function reduzirFoto(f) {
  let img;
  try { img = await createImageBitmap(f, { imageOrientation: 'from-image' }); }
  catch { img = await new Promise((ok, falha) => { const i = new Image(); i.onload = () => ok(i); i.onerror = falha; i.src = URL.createObjectURL(f); }); }
  const k = Math.min(1, 1024 / Math.max(img.width, img.height)), c = document.createElement('canvas');
  c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
  c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
  return await new Promise((ok, falha) => c.toBlob((b) => (b ? ok(b) : falha(new Error('foto'))), 'image/jpeg', 0.6));
}
// fotografias à espera de envio: ficam na base de dados do telefone (IndexedDB)
const FOTOS = {
  db: null,
  abrir() { return (this.db ||= new Promise((ok, falha) => { const r = indexedDB.open('rega-coco', 1); r.onupgradeneeded = () => r.result.createObjectStore('fotos'); r.onsuccess = () => ok(r.result); r.onerror = () => falha(r.error); })); },
  async op(modo, fn) { const db = await this.abrir(); return new Promise((ok, falha) => { const t = db.transaction('fotos', modo), q = fn(t.objectStore('fotos')); t.oncomplete = () => ok(q?.result); t.onerror = () => falha(t.error); }); },
  guardar(k, v) { return this.op('readwrite', (st) => st.put(v, k)); },
  ler(k) { return this.op('readonly', (st) => st.get(k)); },
  apagar(k) { return this.op('readwrite', (st) => st.delete(k)); },
};
async function gravarMonitoria(amostraId) {
  const m = S.mon.find((x) => x.amostra_id === amostraId), a = S.areas.find((x) => x.id === m.area_id) || {};
  const P = S.monP, alvo = tamanhoAmostra(P.N), r = resumoMon(P.obs);
  if (!P.metodo) { alert('Escolha o percurso.'); return; }
  if (!alvo || r.n < alvo) { alert(`Observe ${alvo} plantas (faltam ${Math.max(0, alvo - r.n)}).`); return; }
  if (!S.monFoto) { alert('Tire a fotografia do campo.'); return; }
  const foto = S.monFoto, obs = $('#m-obs').value.trim();
  $('#m-gravar').disabled = true;
  let g; try { g = await validarPosicao(a); } catch (e) { $('#m-gravar').disabled = false; return aviso(e.message, 'erro'); }
  if (g.valido === false) { $('#m-gravar').disabled = false; return aviso(`Está a ${g.dist} m do campo. A verificação faz-se no campo (até ${g.poligono ? CFG.margemPoligono + ' m da borda' : CFG.margemGPS + ' m'}).`, 'erro'); }
  const reg = { id: crypto.randomUUID(), amostra_id: amostraId, verificador_id: S.perfil.id, area_id: m.area_id, data_rega: m.data_rega, feito_em: new Date().toISOString(),
    lat: g.lat, lon: g.lon, gps_precisao_m: g.precisao, distancia_m: g.dist, gps_valido: g.valido,
    solo_regado: r.regado, mudas_estado: null, nota: r.nota, observacao: obs || null,
    metodo: P.metodo, plantas_no_campo: P.N, plantas_alvo: alvo, plantas_obs: P.obs, pct_humido: r.pct, n_vivas: r.vivas, n_secas: r.secas, n_mortas: r.mortas };
  try { await FOTOS.guardar(reg.id, foto); } catch { reg.sem_foto_local = true; S.fotosMem = { ...(S.fotosMem || {}), [reg.id]: foto }; }
  const f = LS.get('filaMon', []); f.push(reg); LS.set('filaMon', f); LS.del('rascMon'); actSync();
  abrirFicha(m.area_id, `<div class="msg ok">Verificação guardada${navigator.onLine ? '' : ' no telefone (será enviada quando houver rede)'}.</div>`);
  sincronizar(true);
}
async function enviarMonitorias() {
  for (const x of LS.get('filaMon', [])) {
    let foto = null; try { foto = await FOTOS.ler(x.id); } catch {} foto = foto || S.fotosMem?.[x.id] || null;
    const caminho = `${S.perfil.id}/${x.id}.jpg`;
    if (foto) { const up = await sb.storage.from('monitoria-fotos').upload(caminho, foto, { contentType: 'image/jpeg', upsert: true }); if (up.error) return up.error.message; }
    const { sem_foto_local, ...linha } = x;
    const r = await sb.from('monitorias').insert({ ...linha, foto_path: foto ? caminho : null });
    if (r.error && !r.error.code) return r.error.message;                         // sem rede: fica na fila
    if (r.error && r.error.code !== '23505') aviso(`Verificação não gravada: ${r.error.message}`, 'erro');   // 23505 = já estava no servidor
    LS.set('monFeitas', [...LS.get('monFeitas', []), x.amostra_id].slice(-50));
    LS.set('filaMon', LS.get('filaMon', []).filter((y) => y.id !== x.id));
    try { await FOTOS.apagar(x.id); } catch {}
  }
  return null;
}

// ---------- gestão (gestor) ----------
async function chamarGestor(corpo) {
  const { data, error } = await sb.functions.invoke('gestor-activistas', { body: corpo });
  if (error) { let m = error.message; try { m = (await error.context.json()).erro || m; } catch {} throw new Error(m); }
  return data;
}
const sugerirUtilizador = (nome) => nome.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().split(/\s+/)[0].replace(/[^a-z0-9]/g, '');
async function desenharGestao(msg = '') {
  const guardado = LS.get('gestaoListar');
  if (guardado) montarGestao(guardado, msg); else $('#gestao').innerHTML = '<p>A carregar…</p>';
  let d; try { d = await chamarGestor({ accao: 'listar' }); } catch (e) { if (!guardado) $('#gestao').innerHTML = `<div class="msg erro">${esc(e.message)}</div>`; return; }
  LS.set('gestaoListar', d);
  if (!guardado || JSON.stringify(guardado) !== JSON.stringify(d)) montarGestao(d, msg);
}
async function montarGestao(d, msg = '') {
  const sem = d.activistas.filter((a) => !a.tem_login && a.activo !== false), com = d.activistas.filter((a) => a.tem_login);
  const gere = S.perfil?.gere_acessos !== false;   // false: gestor que não cria acessos nem muda senhas/PIN (15/10/2026)
  $('#gestao').innerHTML = `${msg}${gere ? `<div class="cartao"><h2>Criar login de activista</h2>
    <label>Activista<select id="g-act">${sem.map((a) => `<option value="${a.id}" data-u="${sugerirUtilizador(a.nome)}">${esc(a.nome)} — ${esc(a.comunidade_principal || '')}</option>`).join('')}</select></label>
    <label>Utilizador<input id="g-user" autocapitalize="none"></label>
    <label>PIN provisório (6 dígitos)<input id="g-pin" type="password" inputmode="numeric" maxlength="6" autocomplete="new-password"></label><p class="pequeno">Ao entrar pela primeira vez, o activista escolhe um PIN só dele.</p>
    <p class="pequeno">Anote o PIN e entregue-o ao activista. A app não volta a mostrá-lo.</p>
    <button class="btn" id="g-criar" ${sem.length ? '' : 'disabled'}>Criar login</button></div>` : '<div class="msg info">Criar acessos e mudar senhas ou PIN é só com o gestor principal.</div>'}
    <div class="cartao"><h2>Activistas com login (${com.length} de ${d.activistas.length})</h2>
    ${com.map((a) => `<div class="item"><div><div class="nome">${esc(a.nome)}</div><div class="sub">utilizador: <b>${esc(a.utilizador || '')}</b></div></div>${gere ? `<button class="chip" onclick="reporPin('${a.id}','${esc(a.nome)}')">Novo PIN</button>` : ''}</div>`).join('') || '<p class="pequeno">Ainda nenhum.</p>'}</div>
    ${gere ? `<div class="cartao"><h2>Outros acessos</h2>
    <p class="pequeno">${Object.entries(FUNCOES).map(([k, f]) => `<b>${f.nome}</b>: ${f.desc}`).join('<br>')}</p>
    <label>Função<select id="c-papel">${Object.entries(FUNCOES).map(([k, f]) => `<option value="${k}">${f.nome}</option>`).join('')}</select></label>
    <label>Nome<span id="c-nome-caixa"></span></label>
    <label>Utilizador<input id="c-user" autocapitalize="none"></label>
    <label>Senha provisória (8 ou mais caracteres)<input id="c-senha" type="password" autocomplete="new-password"></label><p class="pequeno">Ao entrar pela primeira vez, a pessoa escolhe uma senha só dela.</p>
    <button class="btn" id="c-criar">Criar acesso</button></div>` : ''}
    <div class="cartao"><h2>Coberturas (ausências)</h2>
    <p class="pequeno">Quando um técnico ou supervisor está ausente, um colega passa a ver e gerir as equipas dele durante o período indicado.</p>
    <label>Quem cobre<select id="k-quem">${(d.utilizadores || []).filter((u) => u.papel === 'tecnico' || u.papel === 'supervisor').map((u) => `<option value="${u.id}" data-p="${u.papel}" data-n="${esc(u.nome)}">${esc(u.nome)} — ${esc(FUNCOES[u.papel].nome)}</option>`).join('')}</select></label>
    <label>Cobre as equipas de<select id="k-cobre"></select></label>
    <label>Desde<input id="k-desde" type="date" value="${hojeISO()}"></label>
    <label>Até (vazio = até terminar)<input id="k-ate" type="date"></label>
    <button class="btn" id="k-gravar">Gravar cobertura</button>
    <div id="k-lista"><p class="pequeno">A carregar…</p></div></div>
    <div class="cartao"><h2>Monitoria por amostragem</h2>
    <p class="pequeno">Cada técnico e supervisor recebe, a partir das 18:00, uma lista de campos regados nesse dia para verificar. Listas diferentes para cada pessoa, campos sorteados.</p>
    <label>Campos por dia, por pessoa<input id="m-n" type="number" inputmode="numeric" min="1" max="10"></label>
    <button class="btn sec" id="m-gravar-n">Gravar</button></div>
    <div class="cartao"><h2>Quem viu o painel</h2><div id="g-visitas"><p class="pequeno">A carregar…</p></div></div>
    <div class="cartao"><h2>Acessos criados (${(d.utilizadores || []).length})</h2>
    ${(d.utilizadores || []).map((c) => `<div class="item"><div><div class="nome">${esc(c.nome)}</div><div class="sub">${esc(FUNCOES[c.papel]?.nome || c.papel)} · utilizador: <b>${esc(c.utilizador || '')}</b></div></div>${gere ? `<button class="chip" onclick="reporSenha('${c.id}','${esc(c.nome)}')">Nova senha</button>` : ''}</div>`).join('') || '<p class="pequeno">Ainda nenhum.</p>'}</div>`;
  desenharVisitas(); desenharCoberturas(d);
  sb.from('config').select('valor').eq('chave', 'monitoria_campos_por_dia').maybeSingle().then(({ data }) => { if (data && $('#m-n')) $('#m-n').value = data.valor; });
  $('#m-gravar-n').onclick = async () => {
    const n = parseInt($('#m-n').value, 10);
    const { error } = await sb.rpc('definir_monitoria_campos', { p_n: n });
    aviso(error ? error.message : `Monitoria: ${n} campos por dia, por pessoa.`, error ? 'erro' : 'ok');
  };
  if (!gere) return;
  const comLogin = new Set((d.utilizadores || []).map((u) => u.papel + '|' + u.nome));
  // lista de pessoas por função (tabela pessoas_acesso, vinda do Excel de logins); quem já tem acesso aparece desactivado
  const rp = await sb.from('pessoas_acesso').select('nome,entidade,papel,utilizador').order('nome');
  const pessoas = Array.isArray(rp.data) ? rp.data : [];
  const caixaNome = () => {
    const papel = $('#c-papel').value, fixo = ['tecnico', 'supervisor'].includes(papel);
    let lista = pessoas.filter((x) => x.papel === papel);
    if (fixo) {                                               // técnico/supervisor: o nome tem de ser igual ao da lista de activistas
      const validos = (d.nomes || {})[papel] || [];
      lista = validos.map((n) => lista.find((x) => x.nome === n) || { nome: n, utilizador: null });
    }
    $('#c-nome-caixa').innerHTML = `<select id="c-nome">${lista.map((x) => `<option value="${esc(x.nome)}" data-u="${esc((x.utilizador || '').toLowerCase())}" ${comLogin.has(papel + '|' + x.nome) ? 'disabled' : ''}>${esc(x.nome)}${x.entidade ? ' — ' + esc(x.entidade) : ''}${comLogin.has(papel + '|' + x.nome) ? ' (já tem acesso)' : ''}</option>`).join('')}
      ${fixo ? '' : '<option value="__outro">Outra pessoa (escrever o nome)…</option>'}</select><input id="c-nome-outro" placeholder="Nome completo" style="display:none">`;
    const sel = $('#c-nome'), outro = $('#c-nome-outro');
    const livre = [...sel.options].find((o) => !o.disabled && o.value !== '__outro');
    if (livre) sel.value = livre.value;
    else if (lista.length) outro.insertAdjacentHTML('afterend', '<div class="msg info" id="c-todos">Todas as pessoas desta função na lista já têm acesso (ver "Acessos criados" abaixo).</div>');
    const sug = () => {
      const o = sel.selectedOptions[0], escrever = sel.value === '__outro';
      outro.style.display = escrever ? '' : 'none';
      $('#c-user').value = escrever ? sugerirUtilizador(outro.value || ' ') : (o?.dataset.u || sugerirUtilizador(sel.value || ' '));
    };
    sel.onchange = sug; outro.oninput = sug; sug();
  };
  const nomeEscolhido = () => ($('#c-nome').value === '__outro' ? $('#c-nome-outro').value : $('#c-nome').value).trim();
  $('#c-papel').onchange = caixaNome; caixaNome();
  $('#c-criar').onclick = async () => {
    const corpo = { accao: 'criar_utilizador', nome: nomeEscolhido(), papel: $('#c-papel').value, utilizador: $('#c-user').value.trim().toLowerCase(), senha: $('#c-senha').value };
    try { const r = await chamarGestor(corpo); desenharGestao(`<div class="msg ok">Acesso criado: ${esc(r.nome)} → utilizador <b>${esc(r.utilizador)}</b>.</div>`); }
    catch (e) { aviso(e.message, 'erro'); }
  };
  const sel = $('#g-act'), user = $('#g-user');
  if (sel) { const pre = () => user.value = sel.selectedOptions[0]?.dataset.u || ''; sel.onchange = pre; pre(); }
  $('#g-criar').onclick = async () => {
    const corpo = { accao: 'criar', activista_id: sel.value, utilizador: user.value.trim().toLowerCase(), pin: $('#g-pin').value.trim() };
    try { const r = await chamarGestor(corpo); desenharGestao(`<div class="msg ok">Login criado: ${esc(r.activista)} → utilizador <b>${esc(r.utilizador)}</b>.</div>`); }
    catch (e) { aviso(e.message, 'erro'); }
  };
}
// ---------- coberturas ----------
async function desenharCoberturas(d) {
  const quem = $('#k-quem'), cobre = $('#k-cobre');
  const opcoes = () => { const o = quem.selectedOptions[0]; if (!o) { cobre.innerHTML = ''; return; }
    cobre.innerHTML = ((d.nomes || {})[o.dataset.p] || []).filter((n) => n !== o.dataset.n).map((n) => `<option>${esc(n)}</option>`).join(''); };
  quem.onchange = opcoes; opcoes();
  $('#k-gravar').onclick = async () => {
    const o = quem.selectedOptions[0]; if (!o || !cobre.value) return aviso('Escolha quem cobre e quem é coberto.', 'erro');
    const linha = { perfil_id: o.value, papel: o.dataset.p, cobre_nome: cobre.value, desde: $('#k-desde').value || hojeISO(), ate: $('#k-ate').value || null };
    const { error } = await sb.from('coberturas').insert(linha);
    if (error) return aviso(error.message, 'erro');
    aviso('Cobertura gravada.', 'ok'); desenharCoberturas(d);
  };
  const { data, error } = await sb.from('coberturas').select('id,perfil_id,papel,cobre_nome,desde,ate').or(`ate.is.null,ate.gte.${hojeISO()}`).order('desde');
  const el = $('#k-lista'); if (!el) return;
  if (error) { el.innerHTML = `<div class="msg erro">${esc(error.message)}</div>`; return; }
  const nome = (id) => ((d.utilizadores || []).find((u) => u.id === id) || {}).nome || '?';
  el.innerHTML = data.length ? data.map((c) => `<div class="item"><div><div class="nome">${esc(nome(c.perfil_id))} cobre ${esc(c.cobre_nome)}</div>
      <div class="sub">${fmtData(c.desde)} → ${c.ate ? fmtData(c.ate) : 'até terminar'}${c.desde > hojeISO() ? ' · ainda não começou' : ''}</div></div>
      <button class="chip" onclick="terminarCobertura('${c.id}','${c.desde}')">${c.desde > hojeISO() ? 'Anular' : 'Terminar hoje'}</button></div>`).join('')
    : '<p class="pequeno">Nenhuma cobertura activa.</p>';
}
async function terminarCobertura(id, desde) {
  const r = desde > hojeISO() ? await sb.from('coberturas').delete().eq('id', id) : await sb.from('coberturas').update({ ate: hojeISO() }).eq('id', id);
  if (r.error) return aviso(r.error.message, 'erro');
  aviso(desde > hojeISO() ? 'Cobertura anulada.' : 'Cobertura termina hoje.', 'ok'); desenharGestao();
}
async function desenharVisitas() {
  const { data, error } = await sb.rpc('visitas_painel_resumo');
  const el = $('#g-visitas'); if (!el) return;
  if (error) { el.innerHTML = `<div class="msg erro">${esc(error.message)}</div>`; return; }
  el.innerHTML = data.length ? `<div style="overflow-x:auto"><table><tr><th>Pessoa</th><th>Última visita</th><th class="n">Visitas (30 dias)</th><th class="n">Total</th></tr>` +
    data.map((v) => `<tr><td>${esc(v.nome)}<div class="pequeno">${esc(FUNCOES[v.papel]?.nome || (v.papel === 'gestor' ? 'Gestor' : v.papel))} · ${esc(v.utilizador || '')}</div></td><td>${new Date(v.ultima_visita).toLocaleString(LOC, { dateStyle: 'short', timeStyle: 'short' })}</td><td class="n">${v.visitas_30_dias}</td><td class="n">${v.visitas_total}</td></tr>`).join('') + '</table></div>' +
    '<p class="pequeno">Conta no máximo uma visita por pessoa a cada 30 minutos.</p>'
    : '<p class="pequeno">Ainda ninguém abriu o painel.</p>';
}
// nova senha / novo PIN num ecrã da app (alguns navegadores não mostram a janela "prompt")
function reporSenha(id, nome) { ecraNovaCredencial('senha', id, nome); }
function reporPin(id, nome) { ecraNovaCredencial('pin', id, nome); }
function ecraNovaCredencial(tipo, id, nome) {
  const pin = tipo === 'pin';
  folha(`<h2>${pin ? 'Novo PIN' : 'Nova senha'}</h2><p>${esc(nome)}</p>
    <label>${pin ? 'PIN provisório (6 dígitos)' : 'Senha provisória (8 ou mais caracteres)'}<input id="n-cred" type="password" ${pin ? 'inputmode="numeric" maxlength="6"' : ''} autocomplete="new-password"></label>
    <button class="chip" type="button" onclick="const i=$('#n-cred');i.type=i.type==='password'?'text':'password';this.textContent=i.type==='password'?'Mostrar':'Esconder'">Mostrar</button>
    <p class="pequeno">${pin ? 'É provisório: ao entrar, a pessoa escolhe um PIN só dela e o senhor deixa de o saber.' : 'É provisória: ao entrar, a pessoa escolhe uma senha só dela e o senhor deixa de a saber.'}</p>
    <button class="btn" id="n-gravar">Gravar</button><button class="btn sec" onclick="fecharFolha()">Cancelar</button>`);
  $('#n-cred').focus();
  $('#n-gravar').onclick = async () => {
    const v = $('#n-cred').value.trim();
    if (pin ? !/^\d{6}$/.test(v) : v.length < 8) return aviso(pin ? 'O PIN tem de ter 6 dígitos.' : 'A senha tem de ter pelo menos 8 caracteres.', 'erro');
    $('#n-gravar').disabled = true;
    try {
      await chamarGestor(pin ? { accao: 'repor_pin', activista_id: id, pin: v } : { accao: 'repor_senha', perfil_id: id, senha: v });
      fecharFolha(); aviso(pin ? `PIN de ${nome} alterado.` : `Senha de ${nome} alterada.`, 'ok');
    } catch (e) { $('#n-gravar').disabled = false; aviso(e.message, 'erro'); }
  };
}

// ---------- navegação e arranque ----------
function aviso(t, tipo = 'info') {
  const el = document.createElement('div'); el.className = 'msg ' + tipo; el.textContent = t;
  Object.assign(el.style, { position: 'fixed', left: '12px', right: '12px', top: '64px', zIndex: 2000, boxShadow: '0 2px 10px rgba(0,0,0,.2)' });
  document.body.appendChild(el); setTimeout(() => el.remove(), 4500);
}
function mudar(e) {
  document.querySelectorAll('#nav button').forEach((b) => b.classList.toggle('on', b.dataset.e === e));
  document.querySelectorAll('.ecra').forEach((s) => s.classList.toggle('on', s.id === 'e-' + e));
  if (e === 'mapa') setTimeout(() => mapa.invalidateSize(), 50);
  if (e === 'lista') desenharLista();
  if (e === 'hoje') desenharHoje();
  if (e === 'gestao') desenharGestao();
  if (e === 'painel') { const f = $('#painel-f'); if (!f.src) f.src = 'painel.html?embutido=1'; else f.contentWindow?.postMessage('actualizar', location.origin); }
}
function mostrarApp() {
  const papel = S.perfil.papel;
  $('#login').style.display = 'none'; $('#app').style.display = 'flex';
  $('#h-nome').textContent = `${S.perfil.nome}${['activista', 'cliente'].includes(papel) ? '' : ' · ' + (S.perfil.titulo || (papel === 'gestor' ? 'Gestor' : FUNCOES[papel]?.nome || papel))}`;
  $('#h-nome').title = S.perfil.papel === 'activista' ? 'Mudar o meu PIN' : 'Mudar a minha senha';
  $('#h-nome').onclick = () => ecraTrocarSenha(false);
  $('#nav-gestao').style.display = papel === 'gestor' ? '' : 'none';
  $('#nav-painel').style.display = VER_PAINEL.includes(papel) ? '' : 'none';
  const cliente = papel === 'cliente';                     // cliente: Mapa, Campos e Painel, só para ver (15/10/2026, Valdo)
  document.querySelectorAll('#nav button').forEach((b) => { if (b.dataset.e === 'hoje') b.style.display = cliente ? 'none' : ''; });
  $('#h-sync').style.display = cliente ? 'none' : '';
  // desde 18/10/2026 (Valdo) o servidor só manda ao activista os seus campos: o filtro "As minhas / Todas" deixa de ter sentido
  S.filtro = 'todas'; $('#f-ambito').value = 'todas'; $('#f-ambito').style.display = 'none';
  $('#leg-teste').style.display = PODE_REGAR.includes(papel) && papel !== 'activista' ? '' : 'none';
  const tOpt = document.querySelector('#f-sit option[value="teste"]'); if (tOpt) tOpt.hidden = papel === 'activista';
  const coms = [...new Set(S.areas.map((a) => a.comunidade))].sort();
  if (!souActivista()) {                                  // filtro por activista (supervisor, técnico, gestor…)
    const comCampos = new Set(S.areas.map((a) => a.activista_id).filter(Boolean));
    const acts = S.activistas.filter((t) => comCampos.has(t.id)).sort((x, y) => x.nome.localeCompare(y.nome));
    $('#f-act').innerHTML = '<option value="">Todos os activistas</option>' + acts.map((t) => `<option value="${t.id}">${esc(t.nome)}</option>`).join('') + '<option value="__sem">(sem activista)</option>';
    $('#f-act').style.display = '';
  }
  $('#f-com').innerHTML = '<option value="">Todas as comunidades</option>' + coms.map((c) => `<option value="${esc(c)}">${esc(c)}</option>` +
    zonasDe(c).map((z) => `<option value="${esc(c)}|${esc(z)}">&nbsp;&nbsp;${esc(c)} › ${esc(z)}</option>`).join('') +
    (zonasDe(c).length ? `<option value="${esc(c)}|">&nbsp;&nbsp;${esc(c)} › zona por definir</option>` : '')).join('');
  if (!mapa) iniciarMapa();
  desenharMapa(true); desenharLista(); actSync();
  const emCurso = LS.get('emCurso');
  if (cliente) { mudar('painel'); return; }
  if (souOficial()) { mudar('hoje'); return; }           // oficial de M&E: abre nas recontagens
  if (emCurso) abrirFicha(emCurso.area_id, '<div class="msg info">Tem uma rega em curso.</div>');
  else if (souActivista() && S.perfil.activista_id && !jornadaHoje()) ecraJornada();
}
// formulário que estava aberto quando o telefone fechou a app (ex.: ao abrir a câmara) volta a abrir
function retomarRascunhos() {
  try {
    const rd = rascLer('rascMedir');
    if (rd && rd.a_andar && rd.perfil === S.perfil?.id && rd.pts?.length && S.areas.some((x) => x.id === rd.area_id)) return ecraMedir(rd.area_id, rd);
    const rm = rascLer('rascMon');
    if (rm && rm.perfil === S.perfil?.id && (S.mon || []).some((x) => x.amostra_id === rm.amostraId)) return ecraMonitoria(rm.amostraId, rm);
    const rf = rascLer('rascFotoRega'), ec = LS.get('emCurso');
    if (rf && rf.camara && rf.perfil === S.perfil?.id && ec && S.areas.some((x) => x.id === ec.area_id)) {
      if (rf.tipo === 'saida') { ecraSaida(); $('#folha-c').insertAdjacentHTML('afterbegin', AVISO_CAMARA); return; }
      return ecraFotoRega(rf.tipo, '', rf);
    }
    const rq = rascLer('rascQueim');
    if (rq && rq.camara && rq.perfil === S.perfil?.id && S.areas.some((x) => x.id === rq.area)) return ecraQueimada(rq.area, rq);
    const rr = rascLer('rascRec');
    if (rr && rr.camara && rr.perfil === S.perfil?.id && recontagens().some((x) => x.id === rr.rid)) return ecraRecontar(rr.rid, rr);
    const rc = rascLer('rascChuva');
    if (rc && rc.perfil === S.perfil?.id && (rc.camara || rc.mm !== '')) { mudar('hoje'); return ecraChuva(rc); }
  } catch {}
}
// sessão do Supabase guardada no telefone (sem pedir nada à rede)
function sessaoGuardada() {
  try { const s = JSON.parse(localStorage.getItem(`sb-${new URL(CFG.url).hostname.split('.')[0]}-auth-token`) || 'null'); return s && s.user ? s : null; }
  catch { return null; }
}
document.addEventListener('DOMContentLoaded', async () => {
  document.querySelectorAll('#login [data-m]').forEach((b) => { b.onclick = () => modoEntrada(b.dataset.m); });
  ['input', 'focus', 'blur'].forEach((ev) => $('#l-pin').addEventListener(ev, pinCaixas));
  $('#l-mostrar').onclick = () => { const i = $('#l-senha'); i.type = i.type === 'password' ? 'text' : 'password'; $('#l-mostrar').textContent = i.type === 'password' ? 'Mostrar' : 'Esconder'; };
  modoEntrada();
  $('#nav').onclick = (e) => { if (e.target.dataset.e) mudar(e.target.dataset.e); };
  $('#h-sync').onclick = () => sincronizar();
  $('#h-sair').onclick = () => sair();
  $('#folha-x').onclick = fecharFolha;
  $('#b-rodar').onclick = alternarRodar; botaoRodar();
  $('#b-regua').onclick = alternarRegua;
  $('#rg-fechar').onclick = fecharRegua;
  $('#rg-desf').onclick = () => { if (S.regua?.length) { S.regua.pop(); desenharRegua(); } };
  $('#rg-limpar').onclick = () => { if (S.regua) { S.regua = []; desenharRegua(); } };
  $('#rg-eu').onclick = () => { if (!S.pos) return aviso('Ainda sem posição do GPS. Espere uns segundos.'); pontoRegua([...S.pos], 'Eu'); };
  $('#b-centrar').onclick = () => { S.seguirCentro = true; if (S.pos) mapa.setView(S.pos, 16); else lerGPS().then(() => mapa.setView(S.pos, 16)).catch((e) => aviso(e.message, 'erro')); };
  $('#b-filtro').onclick = () => { S.filtro = S.filtro === 'meus' ? 'todas' : 'meus'; desenharMapa(true); };
  ['#f-ambito', '#f-com', '#f-sit'].forEach((s) => $(s).onchange = desenharLista);
  $('#f-act').onchange = () => { desenharLista(); desenharMapa(true); };
  $('#f-txt').oninput = desenharLista;
  $('#lista').onclick = (e) => {
    const b = e.target.closest('button[data-acc]');
    if (b) { if (b.dataset.acc === 'confirmar') confirmarProposta(b.dataset.id); else ecraAtribuir(b.dataset.id); return; }
    const it = e.target.closest('.item'); if (it) abrirFicha(it.dataset.id);
  };
  window.addEventListener('online', () => sincronizar(true));
  window.addEventListener('offline', actSync);
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});

  // Sem rede e com a sessão expirada, getSession() fica ~30 s a tentar renovar o token e o ecrã fica branco
  // (Nuro, 14/10/2026). Espera no máximo 1,5 s (8 s com rede) e, se não responder, usa a sessão guardada no telefone;
  // o token renova-se sozinho quando houver rede.
  const pedidoSessao = sb.auth.getSession().then((r) => r.data.session).catch(() => null);
  let session = await Promise.race([pedidoSessao, new Promise((ok) => setTimeout(() => ok(undefined), navigator.onLine ? 8000 : 1500))]);
  if (session === undefined) session = sessaoGuardada();
  if (session) {
    S.user = session.user;
    const temLocal = carregarDoTelefone();
    if (temLocal && S.perfil) {                           // abre logo com os dados do telefone; o servidor actualiza por trás
      mostrarApp(); retomarRascunhos();
      if (navigator.onLine) carregarTudo().then(() => { if ($('#e-hoje').classList.contains('on')) desenharHoje(); }).catch(() => {}).finally(() => sincronizar(true));
      return;
    }
    if (navigator.onLine) { try { await carregarTudo(); } catch (e) { if (!temLocal) { $('#login').style.display = 'block'; msgEntrada(`<div class="msg erro">${esc(e.message)}</div>`); return; } } }
    if (S.perfil) { mostrarApp(); retomarRascunhos(); sincronizar(true); return; }
  }
  $('#login').style.display = 'block';
});
