// v275: eventos push e notificationclick do sw.js, com um service worker simulado. Uso: node testes/teste_v275_sw.mjs
import fs from 'node:fs'; import vm from 'node:vm';
const src = fs.readFileSync(new URL('../sw.js', import.meta.url), 'utf8');
let falhas = 0; const ok = (c, t) => { console.log((c ? 'OK  ' : 'FALHA ') + t); if (!c) falhas++; };
function correr(clientes) {
  const L = {}, notas = [], abertos = [], msgs = [];
  const self = { addEventListener: (t, f) => (L[t] = f), registration: { scope: 'https://cocopalma.github.io/rega-coco/', showNotification: (t, o) => { notas.push([t, o]); return Promise.resolve(); } },
    clients: { matchAll: async () => clientes.map((c) => ({ ...c, postMessage: (m) => msgs.push(m), focus: async () => (c.focado = 1) })), openWindow: async (u) => abertos.push(u), claim: () => {} }, skipWaiting: () => {} };
  vm.runInNewContext(src, { self, caches: {}, fetch: () => {}, location: { origin: 'https://cocopalma.github.io' }, URL, Request, Response, setTimeout, clearTimeout, Promise, console });
  return { L, notas, abertos, msgs };
}
const ev = (d) => { let p; return { e: { data: { json: () => d }, waitUntil: (x) => (p = x) }, fim: () => p }; };
// 1 app fechada: notificação
let r = correr([]); let x = ev({ tipo: 'mensagem', id: 'm1', titulo: '✉️ Mensagem de Valdo', texto: 'Olá' }); r.L.push(x.e); await x.fim();
ok(r.notas.length === 1 && r.notas[0][0] === '✉️ Mensagem de Valdo' && r.notas[0][1].body === 'Olá' && r.notas[0][1].tag === 'msg-m1' && r.notas[0][1].vibrate, '1 app fechada: mostra a notificação com título, texto e vibração');
// 2 app aberta e à vista: não mostra; avisa a app
r = correr([{ url: 'https://cocopalma.github.io/rega-coco/', visibilityState: 'visible' }]); x = ev({ tipo: 'mensagem', id: 'm2', titulo: 't', texto: 'x' }); r.L.push(x.e); await x.fim();
ok(r.notas.length === 0 && r.msgs.length === 1 && r.msgs[0].tipo === 'mensagem', '2 app à vista: sem notificação, a app recebe o aviso');
// 3 app aberta em segundo plano: notificação e aviso à app
r = correr([{ url: 'https://cocopalma.github.io/rega-coco/', visibilityState: 'hidden' }]); x = ev({ tipo: 'mensagem', id: 'm3' }); r.L.push(x.e); await x.fim();
ok(r.notas.length === 1 && r.msgs.length === 1, '3 app em segundo plano: notificação e aviso à app');
// 4 toque na notificação: com a app aberta, foca-a; sem app, abre-a
r = correr([{ url: 'https://cocopalma.github.io/rega-coco/', visibilityState: 'hidden' }]); let fechou = 0; let p;
r.L.notificationclick({ notification: { close: () => (fechou = 1), data: { id: 'm3' } }, waitUntil: (q) => (p = q) }); await p;
ok(fechou && r.msgs.some((m) => m.abrir) && r.abertos.length === 0, '4 toque com a app aberta: fecha a notificação e mostra a mensagem');
r = correr([]); r.L.notificationclick({ notification: { close: () => {}, data: {} }, waitUntil: (q) => (p = q) }); await p;
ok(r.abertos[0] === 'https://cocopalma.github.io/rega-coco/', '5 toque com a app fechada: abre a app');
// 6 push de outro tipo: ignorado
r = correr([]); x = ev({ tipo: 'outro' }); r.L.push(x.e); ok(r.notas.length === 0, '6 push que não é mensagem: ignorado');
console.log('FALHAS:', falhas); process.exit(falhas ? 1 : 0);
