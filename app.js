/* Rega Coco — app de reporte de rega (fase de aprendizagem)
   Funciona offline: as áreas ficam guardadas no telefone e os registos ficam numa fila
   até haver rede. Nada é apagado do telefone antes de o servidor confirmar. */
'use strict';
const CFG = {
  url: 'https://fgzdqnvobgfzjetbbxcm.supabase.co',
  chave: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZnemRxbnZvYmdmempldGJieGNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE2NDgyMzUsImV4cCI6MjEwNzIyNDIzNX0.1bSDbPLWMvhIG2fzu_Ta2vm1qV1NutzMEmii3wbN7mY',
  dominio: 'rega-coco.example.com', // utilizadores dos activistas: <utilizador>@este-dominio
  margemGPS: 200,      // metros: distância máxima ao centro do campo para validar (a afinar no terreno)
  precisaoCoord: 10,   // metros: pior precisão aceite para gravar a coordenada de um campo (a afinar no terreno)
  precisaoIdeal: 5,    // metros: precisão recomendada
};
/* Regra da fase de aprendizagem (1–2 semanas): cada equipa rega a sua lista em "rondas".
   Um campo da lista não pode ser regado de novo enquanto a equipa não regar todos os campos da lista.
   A duração de cada ronda concluída é o ciclo provisório da comunidade. */
const sb = supabase.createClient(CFG.url, CFG.chave, { auth: { persistSession: true, autoRefreshToken: true } });
const $ = (s) => document.querySelector(s);
const hojeISO = () => new Date().toLocaleDateString('sv-SE');
const fmtData = (d) => d ? new Date(d + (d.length === 10 ? 'T12:00:00' : '')).toLocaleDateString('pt-PT') : '—';
const fmtHora = (t) => t ? new Date(t).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' }) : '—';
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const num = (n) => (n ?? 0).toLocaleString('pt-PT');

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
  tecnico: { nome: 'Técnico', desc: 'vê todos os campos, a rega do dia de todas as equipas e o painel; pode fazer regas de teste.' },
  supervisor: { nome: 'Supervisor', desc: 'o mesmo que o técnico.' },
  director: { nome: 'Director (só leitura)', desc: 'vê todos os campos, a rega do dia e o painel; não regista regas.' },
  me: { nome: 'M&E (só leitura)', desc: 'o mesmo que o director.' },
  cliente: { nome: 'Só painel (cliente / administração)', desc: 'vê apenas o painel geral.' },
};
const PODE_REGAR = ['activista', 'tecnico', 'supervisor', 'gestor'];
const VER_PAINEL = ['tecnico', 'supervisor', 'gestor', 'director', 'me', 'cliente'];
function situacao(a) {
  const u = ultimaRega(a);
  if (!a.activista_id) return { cod: 'sem', txt: 'Sem activista', u };
  let feita, n;
  if (souActivista() && a.activista_id === S.perfil.activista_id) { const ri = rondaInfo(a.activista_id); feita = ri.feitas.has(a.id); n = ri.n; }
  else { const e = S.estado[a.id] || {}; feita = !!e.feita; n = e.ronda || 1; }
  return feita ? { cod: 'feita', txt: `Regada na ronda ${n}`, u, n } : { cod: 'por', txt: `Por regar (ronda ${n})`, u, n };
}
const COR = { por: '#d84315', feita: '#2e7d32', sem: '#8a8f8b' };
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
  let enviados = 0, erro = null;
  for (const reg of f) {
    const { constr, ...linha } = reg;
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
      const r4 = x.tipo === 'coord'
        ? await sb.rpc('gravar_coordenada', { p_area: x.area_id, p_lat: x.lat, p_lon: x.lon, p_precisao: x.precisao })
        : await sb.rpc('atribuir_area', { p_area: x.area_id, p_activista: x.activista_id });
      if (r4.error && !r4.error.code) { erro = r4.error.message; break; }   // sem rede: fica na fila
      if (r4.error) aviso(`Não foi gravado (${x.area_id}): ${r4.error.message}`, 'erro');   // recusado pelo servidor: sai da fila
      LS.set('filaAlt', LS.get('filaAlt', []).filter((y) => y.id !== x.id)); alteradas++;
    }
  }
  if (!erro) { LS.set('ultimaSync', new Date().toISOString()); if (alteradas) await recarregarAreas(); await carregarEstado(); }
  actSync();
  if (!silencioso) aviso(erro ? 'Falhou o envio: ' + erro : enviados ? `${enviados} registo(s) enviados.` : 'Tudo sincronizado.', erro ? 'erro' : 'ok');
}
function actSync() {
  const n = filaRegistos().length + LS.get('filaJ', []).length + LS.get('filaAlt', []).length, b = $('#h-sync'), u = LS.get('ultimaSync');
  b.textContent = n ? `${n} por enviar` : (u ? 'Sinc. ' + fmtHora(u) : 'Sincronizar');
  b.classList.toggle('pend', n > 0);
}

// ---------- dados ----------
async function carregarTudo() {
  const p = await sb.from('perfis').select('id,nome,papel,activista_id').eq('id', S.user.id).maybeSingle();
  if (p.error) throw new Error(p.error.message);
  if (!p.data) throw new Error('Este utilizador não tem perfil na app. Fale com o gestor.');
  if (p.data.papel === 'cliente') { S.perfil = p.data; LS.set('perfil', S.perfil); return; }   // o cliente só vê o painel
  const [ac, ar] = await Promise.all([
    sb.from('activistas').select('id,nome,comunidade_principal,tecnico,supervisor').order('nome'),
    sb.from('areas').select('id,pr,area_n,comunidade,produtor,instaladas,vivas,latitude,longitude,activista_id,activista_proposto,data_plantio').eq('activa', true).order('comunidade').range(0, 4999),
  ]);
  if (ac.error || ar.error) throw new Error((ac.error || ar.error).message);
  S.perfil = p.data; S.activistas = ac.data; S.areas = aplicarPendentes(ar.data);
  S.visiveis = null;
  if (['tecnico', 'supervisor'].includes(S.perfil.papel)) { const v = await sb.rpc('meus_activistas'); S.visiveis = v.error ? null : v.data; LS.set('visiveis', S.visiveis); }
  LS.set('perfil', S.perfil); LS.set('activistas', S.activistas); LS.set('areas', S.areas);
  await carregarEstado();
}
async function carregarEstado() {
  const { data, error } = await sb.rpc('estado_ronda');
  if (error) return;
  S.estado = {}; for (const e of data) S.estado[e.area_id] = { u: e.ultima_rega, ronda: e.ronda_actual, feita: e.regada_na_ronda };
  LS.set('estado', S.estado); LS.set('estadoEm', new Date().toISOString());
  if (souActivista() && S.perfil.activista_id) {        // registos da minha equipa (para a ronda funcionar sem rede)
    const r = await sb.from('registos_rega').select('id,area_id,activista_id,data,ronda,plantas_regadas,teste')
      .eq('activista_id', S.perfil.activista_id).eq('teste', false).gt('plantas_regadas', 0).range(0, 9999);
    if (!r.error) LS.set('meusRegs', r.data);
  }
  desenharMapa(); desenharLista();
}
function carregarDoTelefone() {
  S.perfil = LS.get('perfil'); S.visiveis = LS.get('visiveis'); S.activistas = LS.get('activistas', []); S.areas = LS.get('areas', []); S.estado = LS.get('estado', {});
  return !!(S.perfil && (S.areas.length || S.perfil.papel === 'cliente'));
}

// ---------- login ----------
async function entrar() {
  const u = $('#l-user').value.trim().toLowerCase(), pin = $('#l-pin').value;
  const email = u.includes('@') ? u : `${u}@${CFG.dominio}`;
  $('#l-msg').innerHTML = '<div class="msg info">A entrar…</div>';
  const { data, error } = await sb.auth.signInWithPassword({ email, password: pin });
  if (error) { $('#l-msg').innerHTML = `<div class="msg erro">${/Invalid login/i.test(error.message) ? 'Utilizador ou PIN errado.' : esc(error.message)}</div>`; return; }
  S.user = data.user;
  try { await carregarTudo(); } catch (e) { $('#l-msg').innerHTML = `<div class="msg erro">${esc(e.message)}</div>`; return; }
  mostrarApp();
}
async function sair() {
  if (filaRegistos().length && !confirm('Há registos por enviar. Se sair agora, ficam no telefone e são enviados no próximo login deste utilizador. Sair?')) return;
  await sb.auth.signOut(); ['perfil', 'emCurso', 'sugestao', 'meusRegs', 'jornada'].forEach(LS.del); location.reload();
}

// ---------- mapa ----------
let mapa, camada, eu;
function iniciarMapa() {
  mapa = L.map('mapa', { zoomControl: true }).setView([-10.75, 40.45], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(mapa);
  camada = L.layerGroup().addTo(mapa);
  if (navigator.geolocation) navigator.geolocation.watchPosition((p) => {
    S.pos = [p.coords.latitude, p.coords.longitude]; S.fix = { coords: p.coords, t: Date.now() };
    if (!eu) eu = L.circleMarker(S.pos, { radius: 9, color: '#fff', weight: 3, fillColor: '#1565c0', fillOpacity: 1 }).addTo(mapa);
    else eu.setLatLng(S.pos);
  }, () => {}, { enableHighAccuracy: true, maximumAge: 10000 });
}
function desenharMapa(enquadrar = false) {
  if (!camada) return;
  camada.clearLayers();
  const pts = [];
  for (const a of visiveis()) {
    if (a.latitude == null) continue;
    const s = situacao(a);
    L.circleMarker([a.latitude, a.longitude], { radius: 8, color: '#fff', weight: 2, fillColor: COR[s.cod], fillOpacity: .95 })
      .on('click', () => abrirFicha(a.id)).addTo(camada);
    pts.push([a.latitude, a.longitude]);
  }
  if (enquadrar && pts.length) mapa.fitBounds(pts, { padding: [30, 30], maxZoom: 15 });
  $('#b-filtro').textContent = S.filtro === 'meus' ? 'As minhas' : 'Todas';
  $('#b-filtro').style.display = S.perfil?.papel === 'activista' ? '' : 'none';
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
function linhaAtribuir(a) {
  const prop = a.activista_proposto, ok = prop && daMinhaEquipa(prop);
  return `<div class="atrib">${prop ? `Proposta: <b>${esc(nomeAct(prop))}</b>${ok ? '' : ' <span class="pequeno">(fora da sua equipa)</span>'}` : '<span class="pequeno">Sem proposta</span>'}
    <div class="chips">${ok ? `<button class="chip on" data-acc="confirmar" data-id="${esc(a.id)}">✓ Confirmar proposta</button>` : ''}
    <button class="chip" data-acc="outro" data-id="${esc(a.id)}">Escolher outro</button></div></div>`;
}
function confirmarProposta(id) {
  const a = S.areas.find((x) => x.id === id); if (!a || !a.activista_proposto) return;
  a.activista_id = a.activista_proposto; LS.set('areas', S.areas);
  porNaFilaAlt({ tipo: 'atrib', area_id: id, activista_id: a.activista_id });
  aviso(`${a.produtor}: atribuído a ${nomeAct(a.activista_id)}.`, 'ok'); desenharMapa(); desenharLista();
}
function desenharLista() {
  const amb = $('#f-ambito').value, com = $('#f-com').value, sit = $('#f-sit').value, txt = $('#f-txt').value.trim().toLowerCase();
  let L2 = (amb === 'meus' && S.perfil?.papel === 'activista') ? minhas() : S.areas;
  if (com) L2 = L2.filter((a) => a.comunidade === com);
  if (txt) L2 = L2.filter((a) => (a.produtor || '').toLowerCase().includes(txt) || a.pr.toLowerCase().includes(txt));
  let linhas = L2.map((a) => ({ a, s: situacao(a), d: S.pos && a.latitude != null ? metros(S.pos, [a.latitude, a.longitude]) : null }));
  if (sit) linhas = linhas.filter((x) => x.s.cod === sit);
  linhas.sort((x, y) => (x.s.cod === 'feita') - (y.s.cod === 'feita') || (x.d ?? 1e12) - (y.d ?? 1e12));   // por regar primeiro
  $('#lista').innerHTML = (souActivista() && S.perfil.activista_id ? `<div class="msg info">${textoRonda()}</div>` : '') +
    (porAtribuir().length && sit !== 'sem' ? `<div class="msg info">${porAtribuir().length} campos por atribuir. <button class="chip" onclick="$('#f-sit').value='sem';desenharLista()">Ver</button></div>` : '') +
    `<p class="pequeno">${linhas.length} campos${S.pos ? ' · ordenados pela distância' : ''}</p>` +
    linhas.slice(0, 300).map(({ a, s, d }) => `<div class="item" data-id="${esc(a.id)}"><div>
      <div class="nome">${esc(a.produtor)}</div><div class="sub">${esc(a.pr)} · ${esc(a.comunidade)} · ${plantasTxt(a)}${d != null ? ' · ' + (d < 1000 ? Math.round(d) + ' m' : (d / 1000).toFixed(1) + ' km') : ''}</div>
      </div><span class="tag t-${s.cod}">${s.txt}</span>${s.cod === 'sem' && podeAtribuir(a) ? linhaAtribuir(a) : ''}</div>`).join('') + (linhas.length > 300 ? '<p class="pequeno">Mostra os 300 mais próximos. Use os filtros.</p>' : '');
}

// ---------- ficha do campo ----------
function folha(html) { $('#folha-c').innerHTML = html; $('#folha').classList.add('on'); }
function fecharFolha() { pararVigia(); $('#folha').classList.remove('on'); }
// ---------- coordenada e atribuição de campos (técnico, supervisor, gestor) ----------
const PODE_COORD = ['tecnico', 'supervisor', 'gestor'];
const podeAtribuir = (a) => ['gestor', 'supervisor'].includes(S.perfil.papel) || (S.perfil.papel === 'tecnico' && !a.activista_id);
function botoesCampo(a) {
  let h = '';
  if (PODE_COORD.includes(S.perfil.papel) && (a.latitude == null || ['gestor', 'supervisor'].includes(S.perfil.papel)))
    h += `<button class="btn sec" onclick="ecraCoordenada('${esc(a.id)}')">📍 ${a.latitude == null ? 'Gravar a coordenada deste campo' : 'Corrigir a coordenada (estou no campo)'}</button>`;
  if (podeAtribuir(a)) h += `<button class="btn sec" onclick="ecraAtribuir('${esc(a.id)}')">👤 ${a.activista_id ? 'Mudar o activista deste campo' : 'Atribuir a um activista'}</button>`;
  return h;
}
function porNaFilaAlt(x) { const f = LS.get('filaAlt', []); f.push({ id: crypto.randomUUID(), ...x }); LS.set('filaAlt', f); actSync(); sincronizar(true); }
// leitura contínua do GPS: mostra a precisão a melhorar e só deixa gravar abaixo do limite
let vigiaCoord = null;
function pararVigia() { if (vigiaCoord != null) { navigator.geolocation.clearWatch(vigiaCoord); vigiaCoord = null; } }
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
  a.latitude = x.lat; a.longitude = x.lon; LS.set('areas', S.areas);    // aparece já no mapa deste telefone
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
  const resto = S.activistas.filter((t) => daEquipa(t.id) && !prox.some((p) => p.id === t.id));
  folha(`${nota}<h2>${esc(a.produtor)}</h2><p class="pequeno">${esc(a.pr)} · ${esc(a.comunidade)} · activista actual: <b>${esc(nomeAct(a.activista_id))}</b></p>
    ${a.activista_proposto ? `<div class="msg info">Proposta da base: <b>${esc(nomeAct(a.activista_proposto))}</b></div>` : ''}
    <label>Atribuir a<select id="t-act">
      ${prox.length ? `<optgroup label="Mais próximos (campo da lista mais perto)">${prox.map((p) => `<option value="${p.id}">${esc(nomeAct(p.id))} — ${km(p.d)} (${esc(p.com)})</option>`).join('')}</optgroup>` : ''}
      <optgroup label="Todos">${resto.map((t) => `<option value="${t.id}">${esc(t.nome)} — ${esc(t.comunidade_principal || '')}</option>`).join('')}</optgroup>
    </select></label>
    <p class="pequeno">Regra: rega o activista da comunidade onde o campo está. Confirme antes de gravar.</p>
    <button class="btn" onclick="gravarAtribuicao('${esc(id)}')">Gravar</button>
    <button class="btn sec" onclick="abrirFicha('${esc(id)}')">Cancelar</button>`);
  if (a.activista_proposto && daEquipa(a.activista_proposto)) $('#t-act').value = a.activista_proposto;
}
function gravarAtribuicao(id) {
  const a = S.areas.find((x) => x.id === id), novo = $('#t-act').value;
  if (!novo) return;
  a.activista_id = novo; LS.set('areas', S.areas);
  porNaFilaAlt({ tipo: 'atrib', area_id: id, activista_id: novo }); desenharMapa(); desenharLista();
  abrirFicha(id, `<div class="msg ok">Campo atribuído a ${esc(nomeAct(novo))}.${navigator.onLine ? '' : ' Será enviado quando houver rede.'}</div>`);
}
async function recarregarAreas() {
  const ar = await sb.from('areas').select('id,pr,area_n,comunidade,produtor,instaladas,vivas,latitude,longitude,activista_id,activista_proposto,data_plantio').eq('activa', true).order('comunidade').range(0, 4999);
  if (ar.error) return;
  S.areas = aplicarPendentes(ar.data); LS.set('areas', S.areas);
}
function aplicarPendentes(lista) {                          // o que ainda não foi enviado continua a valer neste telefone
  for (const x of LS.get('filaAlt', [])) { const a = lista.find((y) => y.id === x.area_id); if (!a) continue; if (x.tipo === 'coord') { a.latitude = x.lat; a.longitude = x.lon; } else a.activista_id = x.activista_id; }
  return lista;
}

function abrirFicha(id, nota = '') {
  const a = S.areas.find((x) => x.id === id); if (!a) return;
  const s = situacao(a), emCurso = LS.get('emCurso');
  const d = S.pos && a.latitude != null ? metros(S.pos, [a.latitude, a.longitude]) : null;
  const podeRegar = PODE_REGAR.includes(S.perfil.papel) && (S.perfil.papel === 'activista' || a.activista_id);
  let acc = '';
  if (emCurso && emCurso.area_id === a.id) acc = (emCurso.agua_em
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
    <div class="lin"><span>Activista</span><b>${esc(nomeAct(a.activista_id))}</b></div>
    <div class="lin"><span>Plantas</span><b>${plantasTxt(a)}</b></div>
    <div class="lin"><span>Última rega</span><b>${fmtData(s.u)}</b></div>
    <div class="lin"><span>Ronda da equipa</span><span class="tag t-${s.cod}">${s.txt}</span></div>
    ${d != null ? `<div class="lin"><span>Distância</span><b>${d < 1000 ? Math.round(d) + ' m' : (d / 1000).toFixed(1) + ' km'} · ${rumo(S.pos, [a.latitude, a.longitude])}</b></div>` : ''}
    ${a.latitude == null ? '<div class="msg erro">Este campo não tem coordenada na base. A entrada fica registada sem validação de GPS.</div>' : ''}
   </div>${acc}${botoesCampo(a)}`);
}

// ---------- entrada ----------
async function validarPosicao(a) {
  const c = await lerGPS();
  const precisao = Math.round(c.accuracy);
  if (a.latitude == null) return { lat: c.latitude, lon: c.longitude, precisao, dist: null, valido: null };
  const dist = Math.round(metros([c.latitude, c.longitude], [a.latitude, a.longitude]));
  const valido = dist <= CFG.margemGPS + Math.min(precisao, 50);
  return { lat: c.latitude, lon: c.longitude, precisao, dist, valido };
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
  if (g.valido === false) return abrirFicha(id, `<div class="msg erro">Está a ${g.dist} m do campo (precisão ±${g.precisao} m). Só pode marcar a entrada até ${CFG.margemGPS} m do campo.</div>`);
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
  LS.set('emCurso', ent); abrirFicha(id, `<div class="msg ok">Entrada marcada às ${fmtHora(ent.entrada_em)}${g.dist != null ? ` · a ${g.dist} m do campo` : ''}.</div>`);
}
function confirmarAlerta() {
  const m = $('#a-motivo').value.trim();
  if (m.length < 3) { alert('Escreva o motivo.'); return; }
  const ent = LS.get('pendenteAlerta'); ent.alerta = 'fora_da_lista'; ent.motivo_alerta = m;
  LS.del('pendenteAlerta'); LS.set('emCurso', ent);
  abrirFicha(ent.area_id, `<div class="msg ok">Entrada marcada às ${fmtHora(ent.entrada_em)} (campo fora da lista).</div>`);
}
function marcarAgua(jaEstava) {
  const ent = LS.get('emCurso'); if (!ent) return;
  ent.agua_em = jaEstava ? ent.entrada_em : new Date().toISOString(); LS.set('emCurso', ent);
  abrirFicha(ent.area_id);
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
   <button class="btn" onclick="marcarSaida()">Marcar saída e guardar</button>
   <button class="btn sec" onclick="abrirFicha('${esc(a.id)}')">Voltar</button>`);
  document.querySelectorAll('#s-chips .chip').forEach((b) => b.onclick = () => b.classList.toggle('on'));
}
async function marcarSaida() {
  const ent = LS.get('emCurso'), a = S.areas.find((x) => x.id === ent.area_id);
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
  if (g.valido === false) { ecraSaida(); return aviso(`Está a ${g.dist} m do campo. Marque a saída ainda no campo (até ${CFG.margemGPS} m).`, 'erro'); }
  const actId = S.perfil.activista_id || a.activista_id;
  const antes = actId ? rondaInfo(actId) : null;
  const reg = {
    ronda: antes ? antes.n : null, pessoas, agua_em: ent.agua_em || null,
    id: crypto.randomUUID(), area_id: a.id, activista_id: S.perfil.activista_id || a.activista_id, data: hojeISO(),
    entrada_em: ent.entrada_em, saida_em: new Date().toISOString(), entrada_lat: ent.entrada_lat, entrada_lon: ent.entrada_lon,
    saida_lat: g.lat, saida_lon: g.lon, gps_precisao_m: Math.max(ent.gps_precisao_m || 0, g.precisao),
    distancia_area_m: ent.distancia_area_m, gps_valido: ent.gps_valido, plantas_regadas: plantas,
    alerta: ent.alerta || null, motivo_alerta: ent.motivo_alerta || null,
    area_sugerida_id: ent.area_sugerida_id || null, seguiu_sugestao: ent.seguiu_sugestao ?? null,
    criado_no_telefone_em: new Date().toISOString(), teste: S.perfil.papel !== 'activista', observacao: obs || null,
    constr: tipos.map((t) => ({ id: crypto.randomUUID(), tipo: t, descricao: obs || null })),
  };
  porNaFila(reg); LS.del('emCurso'); actSync(); desenharMapa(); desenharLista();
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

// ---------- hoje ----------
async function desenharHoje() {
  const h = hojeISO(), local = filaRegistos().filter((r) => r.data === h);
  let html = `<div class="cartao"><h2>Hoje · ${fmtData(h)}</h2>`;
  if (S.perfil.papel === 'activista') {
    let serv = [];
    if (navigator.onLine) { const r = await sb.from('registos_rega').select('id,area_id,entrada_em,saida_em,plantas_regadas,alerta,agua_em').eq('data', h).order('entrada_em'); serv = r.data || []; }
    const ids = new Set(serv.map((x) => x.id)), todos = [...serv, ...local.filter((x) => !ids.has(x.id))];
    const tot = todos.reduce((s, x) => s + (x.plantas_regadas || 0), 0);
    const j = jornadaHoje();
    html += `<div class="lin"><span>Ronda</span><b>${textoRonda()}</b></div>
      <div class="lin"><span>Pessoas hoje</span><b>${j ? j.pessoas : '—'} <button class="chip" onclick="ecraJornada()">${j ? 'Alterar' : 'Registar'}</button></b></div>
      <div class="lin"><span>Campos regados hoje</span><b>${todos.length}</b></div><div class="lin"><span>Plantas regadas hoje</span><b>${num(tot)}</b></div><div class="lin"><span>Por enviar</span><b>${local.length}</b></div></div>`;
    html += todos.map((x) => { const a = S.areas.find((y) => y.id === x.area_id) || {}; return `<div class="item"><div><div class="nome">${esc(a.produtor)}</div><div class="sub">${fmtHora(x.entrada_em)}–${fmtHora(x.saida_em)} · ${num(x.plantas_regadas)} plantas${x.agua_em ? ' · água ' + fmtHora(x.agua_em) : ''}${x.alerta ? ' · fora da lista' : ''}</div></div></div>`; }).join('');
  } else {
    const r = await sb.from('registos_rega').select('activista_id,area_id,plantas_regadas,alerta,gps_valido,teste,entrada_em,saida_em,pessoas,agua_em').eq('data', h);
    if (r.error) html += `<div class="msg erro">${esc(r.error.message)}</div></div>`;
    else {
      const g = {}; for (const x of r.data) { const k = x.activista_id; g[k] ??= { campos: 0, plantas: 0, alertas: 0, teste: 0, ini: null, fim: null, pessoas: 0, agua: null };
        const o = g[k]; o.campos++; o.plantas += x.plantas_regadas || 0; if (x.alerta) o.alertas++; if (x.teste) o.teste++;
        o.pessoas = Math.max(o.pessoas, x.pessoas || 0); if (x.agua_em && (!o.agua || x.agua_em < o.agua)) o.agua = x.agua_em;
        if (!o.ini || x.entrada_em < o.ini) o.ini = x.entrada_em; if (!o.fim || x.saida_em > o.fim) o.fim = x.saida_em; }
      html += `<div class="lin"><span>Registos recebidos</span><b>${r.data.length}</b></div><button class="btn sec" onclick="mudar('painel')">Abrir painel geral</button></div>
        <div style="overflow-x:auto"><table><tr><th>Activista</th><th class="n">Pessoas</th><th class="n">Campos</th><th class="n">Plantas</th><th>1.ª água</th><th>Horas</th><th class="n">Alertas</th></tr>` +
        Object.entries(g).map(([k, o]) => `<tr><td>${esc(nomeAct(k))}${o.teste ? ' <span class="pequeno">(teste)</span>' : ''}</td><td class="n">${o.pessoas || '—'}</td><td class="n">${o.campos}</td><td class="n">${num(o.plantas)}</td><td>${fmtHora(o.agua)}</td><td>${fmtHora(o.ini)}–${fmtHora(o.fim)}</td><td class="n">${o.alertas}</td></tr>`).join('') + '</table></div>';
    }
  }
  html += `<button class="btn sec" onclick="sair()">Sair desta conta</button>`;
  $('#hoje').innerHTML = html;
}

// ---------- gestão (gestor) ----------
async function chamarGestor(corpo) {
  const { data, error } = await sb.functions.invoke('gestor-activistas', { body: corpo });
  if (error) { let m = error.message; try { m = (await error.context.json()).erro || m; } catch {} throw new Error(m); }
  return data;
}
const sugerirUtilizador = (nome) => nome.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().split(/\s+/)[0].replace(/[^a-z0-9]/g, '');
async function desenharGestao(msg = '') {
  $('#gestao').innerHTML = '<p>A carregar…</p>';
  let d; try { d = await chamarGestor({ accao: 'listar' }); } catch (e) { $('#gestao').innerHTML = `<div class="msg erro">${esc(e.message)}</div>`; return; }
  const sem = d.activistas.filter((a) => !a.tem_login), com = d.activistas.filter((a) => a.tem_login);
  $('#gestao').innerHTML = `${msg}<div class="cartao"><h2>Criar login de activista</h2>
    <label>Activista<select id="g-act">${sem.map((a) => `<option value="${a.id}" data-u="${sugerirUtilizador(a.nome)}">${esc(a.nome)} — ${esc(a.comunidade_principal || '')}</option>`).join('')}</select></label>
    <label>Utilizador<input id="g-user" autocapitalize="none"></label>
    <label>PIN (6 dígitos)<input id="g-pin" inputmode="numeric" maxlength="6"></label>
    <p class="pequeno">Anote o PIN e entregue-o ao activista. A app não volta a mostrá-lo.</p>
    <button class="btn" id="g-criar" ${sem.length ? '' : 'disabled'}>Criar login</button></div>
    <div class="cartao"><h2>Activistas com login (${com.length} de ${d.activistas.length})</h2>
    ${com.map((a) => `<div class="item"><div><div class="nome">${esc(a.nome)}</div><div class="sub">utilizador: <b>${esc(a.utilizador || '')}</b></div></div><button class="chip" onclick="reporPin('${a.id}','${esc(a.nome)}')">Novo PIN</button></div>`).join('') || '<p class="pequeno">Ainda nenhum.</p>'}</div>
    <div class="cartao"><h2>Outros acessos</h2>
    <p class="pequeno">${Object.entries(FUNCOES).map(([k, f]) => `<b>${f.nome}</b>: ${f.desc}`).join('<br>')}</p>
    <label>Função<select id="c-papel">${Object.entries(FUNCOES).map(([k, f]) => `<option value="${k}">${f.nome}</option>`).join('')}</select></label>
    <label>Nome<span id="c-nome-caixa"></span></label>
    <label>Utilizador<input id="c-user" autocapitalize="none"></label>
    <label>Senha (8 ou mais caracteres)<input id="c-senha"></label>
    <button class="btn" id="c-criar">Criar acesso</button></div>
    <div class="cartao"><h2>Coberturas (ausências)</h2>
    <p class="pequeno">Quando um técnico ou supervisor está ausente, um colega passa a ver e gerir as equipas dele durante o período indicado.</p>
    <label>Quem cobre<select id="k-quem">${(d.utilizadores || []).filter((u) => u.papel === 'tecnico' || u.papel === 'supervisor').map((u) => `<option value="${u.id}" data-p="${u.papel}" data-n="${esc(u.nome)}">${esc(u.nome)} — ${esc(FUNCOES[u.papel].nome)}</option>`).join('')}</select></label>
    <label>Cobre as equipas de<select id="k-cobre"></select></label>
    <label>Desde<input id="k-desde" type="date" value="${hojeISO()}"></label>
    <label>Até (vazio = até terminar)<input id="k-ate" type="date"></label>
    <button class="btn" id="k-gravar">Gravar cobertura</button>
    <div id="k-lista"><p class="pequeno">A carregar…</p></div></div>
    <div class="cartao"><h2>Quem viu o painel</h2><div id="g-visitas"><p class="pequeno">A carregar…</p></div></div>
    <div class="cartao"><h2>Acessos criados (${(d.utilizadores || []).length})</h2>
    ${(d.utilizadores || []).map((c) => `<div class="item"><div><div class="nome">${esc(c.nome)}</div><div class="sub">${esc(FUNCOES[c.papel]?.nome || c.papel)} · utilizador: <b>${esc(c.utilizador || '')}</b></div></div><button class="chip" onclick="reporSenha('${c.id}','${esc(c.nome)}')">Nova senha</button></div>`).join('') || '<p class="pequeno">Ainda nenhum.</p>'}</div>`;
  desenharVisitas(); desenharCoberturas(d);
  const comLogin = new Set((d.utilizadores || []).map((u) => u.papel + '|' + u.nome));
  // lista de pessoas por função (tabela pessoas_acesso, vinda do Excel de logins); quem já tem acesso aparece desactivado
  const pessoas = (await sb.from('pessoas_acesso').select('nome,entidade,papel,utilizador').order('nome')).data || [];
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
    data.map((v) => `<tr><td>${esc(v.nome)}<div class="pequeno">${esc(FUNCOES[v.papel]?.nome || (v.papel === 'gestor' ? 'Gestor' : v.papel))} · ${esc(v.utilizador || '')}</div></td><td>${new Date(v.ultima_visita).toLocaleString('pt-PT', { dateStyle: 'short', timeStyle: 'short' })}</td><td class="n">${v.visitas_30_dias}</td><td class="n">${v.visitas_total}</td></tr>`).join('') + '</table></div>' +
    '<p class="pequeno">Conta no máximo uma visita por pessoa a cada 30 minutos.</p>'
    : '<p class="pequeno">Ainda ninguém abriu o painel.</p>';
}
async function reporSenha(id, nome) {
  const s = prompt(`Nova senha (8 ou mais caracteres) para ${nome}:`); if (!s) return;
  try { await chamarGestor({ accao: 'repor_senha', perfil_id: id, senha: s }); aviso('Senha alterada.', 'ok'); } catch (e) { aviso(e.message, 'erro'); }
}
async function reporPin(id, nome) {
  const pin = prompt(`Novo PIN de 6 dígitos para ${nome}:`); if (!pin) return;
  try { await chamarGestor({ accao: 'repor_pin', activista_id: id, pin: pin.trim() }); aviso('PIN alterado.', 'ok'); } catch (e) { aviso(e.message, 'erro'); }
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
  $('#h-nome').textContent = `${S.perfil.nome}${['activista', 'cliente'].includes(papel) ? '' : ' · ' + (papel === 'gestor' ? 'Gestor' : FUNCOES[papel]?.nome || papel)}`;
  $('#nav-gestao').style.display = papel === 'gestor' ? '' : 'none';
  $('#nav-painel').style.display = VER_PAINEL.includes(papel) ? '' : 'none';
  if (papel === 'cliente') {                               // o cliente só vê o painel
    document.querySelectorAll('#nav button').forEach((b) => { if (b.dataset.e !== 'painel') b.style.display = 'none'; });
    $('#h-sync').style.display = 'none'; $('#h-sair').style.display = '';
    mudar('painel'); return;
  }
  if (papel !== 'activista') { S.filtro = 'todas'; $('#f-ambito').value = 'todas'; }
  const coms = [...new Set(S.areas.map((a) => a.comunidade))].sort();
  $('#f-com').innerHTML = '<option value="">Todas as comunidades</option>' + coms.map((c) => `<option>${esc(c)}</option>`).join('');
  if (!mapa) iniciarMapa();
  desenharMapa(true); desenharLista(); actSync();
  const emCurso = LS.get('emCurso');
  if (emCurso) abrirFicha(emCurso.area_id, '<div class="msg info">Tem uma rega em curso.</div>');
  else if (souActivista() && S.perfil.activista_id && !jornadaHoje()) ecraJornada();
}
document.addEventListener('DOMContentLoaded', async () => {
  $('#l-entrar').onclick = entrar;
  $('#l-pin').addEventListener('keydown', (e) => { if (e.key === 'Enter') entrar(); });
  $('#nav').onclick = (e) => { if (e.target.dataset.e) mudar(e.target.dataset.e); };
  $('#h-sync').onclick = () => sincronizar();
  $('#h-sair').onclick = () => sair();
  $('#folha-x').onclick = fecharFolha;
  $('#b-centrar').onclick = () => { if (S.pos) mapa.setView(S.pos, 16); else lerGPS().then(() => mapa.setView(S.pos, 16)).catch((e) => aviso(e.message, 'erro')); };
  $('#b-filtro').onclick = () => { S.filtro = S.filtro === 'meus' ? 'todas' : 'meus'; desenharMapa(true); };
  ['#f-ambito', '#f-com', '#f-sit'].forEach((s) => $(s).onchange = desenharLista);
  $('#f-txt').oninput = desenharLista;
  $('#lista').onclick = (e) => {
    const b = e.target.closest('button[data-acc]');
    if (b) { if (b.dataset.acc === 'confirmar') confirmarProposta(b.dataset.id); else ecraAtribuir(b.dataset.id); return; }
    const it = e.target.closest('.item'); if (it) abrirFicha(it.dataset.id);
  };
  window.addEventListener('online', () => sincronizar(true));
  window.addEventListener('offline', actSync);
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});

  const { data: { session } } = await sb.auth.getSession();
  if (session) {
    S.user = session.user;
    const temLocal = carregarDoTelefone();
    if (navigator.onLine) { try { await carregarTudo(); } catch (e) { if (!temLocal) { $('#login').style.display = 'flex'; $('#l-msg').innerHTML = `<div class="msg erro">${esc(e.message)}</div>`; return; } } }
    if (S.perfil) { mostrarApp(); sincronizar(true); return; }
  }
  $('#login').style.display = 'flex';
});
