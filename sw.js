// Service worker: guarda a app e as bibliotecas para funcionar sem rede.
// Os pedidos ao Supabase nunca são guardados aqui (a fila offline está na app).
const VERSAO = 'rega-v20';
const BASE = ['./', 'index.html', 'app.js', 'i18n.js', 'painel.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css', 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
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
  if (u.hostname.endsWith('tile.openstreetmap.org')) {          // mosaicos do mapa já vistos: do telefone primeiro
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
  // app: rede primeiro (para receber actualizações), telefone se não houver rede
  // no-cache: confirma sempre com o servidor (evita ficar com app.js antigo da cache do navegador)
  const pedido = u.origin !== location.origin ? e.request
    : e.request.mode === 'navigate' ? new Request(e.request.url, { cache: 'no-cache', credentials: 'same-origin' })
    : new Request(e.request, { cache: 'no-cache' });
  e.respondWith(fetch(pedido).then((r) => {
    if (r.ok && (u.origin === location.origin || ['unpkg.com', 'cdn.jsdelivr.net', 'fonts.googleapis.com', 'fonts.gstatic.com'].includes(u.hostname))) { const copia = r.clone(); caches.open(VERSAO).then((c) => c.put(e.request, copia)); }
    return r;
  }).catch(() => caches.match(e.request, { ignoreSearch: true }).then((r) => r || caches.match('index.html'))));
});
