// Service worker: guarda a app e as bibliotecas para funcionar sem rede.
// Os pedidos ao Supabase nunca são guardados aqui (a fila offline está na app).
const VERSAO = 'rega-v156';
const V = VERSAO.split('-v')[1];   // o ?v= de index.html e painel.html é sempre o número da VERSAO
const BASE = ['./', 'index.html', `app.js?v=${V}`, `demo.js?v=${V}`, `i18n.js?v=${V}`, `i18n-sw.js?v=${V}`, 'painel.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css', 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', 'https://unpkg.com/leaflet-rotate@0.2.8/dist/leaflet-rotate.js',
  'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js'];
const MAX_MOSAICOS = 3000;

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(BASE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSAO && k !== 'mosaicos').map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.hostname.endsWith('supabase.co')) return;
  if (u.hostname.endsWith('tile.openstreetmap.org') || u.hostname === 'server.arcgisonline.com') {   // + satélite (v102)          // mosaicos do mapa já vistos: do telefone primeiro
    e.respondWith(caches.open('mosaicos').then(async (c) => {
      const hit = await c.match(e.request); if (hit) return hit;
      try {
        const r = await fetch(e.request);
        if (r.ok) { c.put(e.request, r.clone()); c.keys().then((ks) => { if (ks.length > MAX_MOSAICOS) ks.slice(0, ks.length - MAX_MOSAICOS).forEach((k) => c.delete(k)); }); }
        return r;
      } catch { return new Response('', { status: 504 }); }
    }));
    return;
  }
  // v155 (30/10/2026, Valdo: "a app está lenta a carregar"). Antes: tudo da rede primeiro; com rede fraca (mas não sem rede)
  // a app esperava pela rede em cada ficheiro (~1 MB). Agora:
  // - ficheiros com versão (app.js?v=…, i18n.js?v=…) e bibliotecas com versão fixa (unpkg, jsdelivr): do telefone primeiro;
  //   uma versão nova da app tem outro ?v=, por isso vem da rede;
  // - páginas (index.html, painel.html) e o resto: rede primeiro, mas no máximo 4 s; depois usa a do telefone (e guarda a da rede
  //   quando chegar, para a próxima vez).
  const guardar = (r) => { if (r.ok && (u.origin === location.origin || ['unpkg.com', 'cdn.jsdelivr.net', 'fonts.googleapis.com', 'fonts.gstatic.com'].includes(u.hostname))) { const copia = r.clone(); caches.open(VERSAO).then((c) => c.put(e.request, copia)); } return r; };
  const fixo = (u.origin === location.origin && u.searchParams.has('v')) || ['unpkg.com', 'cdn.jsdelivr.net', 'fonts.gstatic.com'].includes(u.hostname);
  if (fixo) {
    e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).then(guardar)
      .catch(() => caches.match(e.request, { ignoreSearch: true }))));
    return;
  }
  // no-cache: confirma sempre com o servidor (evita ficar com uma página antiga da cache do navegador)
  const pedido = u.origin !== location.origin ? e.request
    : e.request.mode === 'navigate' ? new Request(e.request.url, { cache: 'no-cache', credentials: 'same-origin' })
    : new Request(e.request, { cache: 'no-cache' });
  const daRede = fetch(pedido).then(guardar);
  const doTelefone = () => caches.match(e.request, { ignoreSearch: true }).then((r) => r || (e.request.mode === 'navigate' ? caches.match('index.html') : null));
  e.respondWith(new Promise((ok) => {
    let feito = false; const fim = (r) => { if (!feito && r) { feito = true; ok(r); } };
    const t = setTimeout(() => doTelefone().then(fim), 4000);
    daRede.then((r) => { clearTimeout(t); fim(r); }).catch(() => { clearTimeout(t); doTelefone().then((r) => { fim(r); if (!feito) { feito = true; ok(new Response('', { status: 504 })); } }); });
    e.waitUntil(daRede.catch(() => {}));
  }));
});
