# v155: service worker — ficheiros com versão do telefone primeiro; páginas: rede no máximo 4 s, depois do telefone; sem rede abre.
import subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; T = "/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad"
FLAG, LOG = f"{T}/lento", f"{T}/pedidos.log"
for f in (FLAG, LOG):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "srv_lento.py", "/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad/swapp", "8857", FLAG, LOG]); time.sleep(1)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}); ctx.set_default_timeout(30000)
    for pat, f, ct in [("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", f"{NM}/leaflet/dist/leaflet.js", "application/javascript"), ("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", f"{NM}/leaflet/dist/leaflet.css", "text/css")]:
        ctx.route(pat, (lambda f, ct: (lambda r: r.fulfill(path=f, content_type=ct)))(f, ct))
    ctx.route("**/unpkg.com/leaflet-rotate@0.2.8/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body="/* rotate */"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", lambda r: r.fulfill(status=200, content_type="application/json", body="[]"))
    pg = ctx.new_page(); erros = []; pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8857/"); pg.wait_for_selector("#l-entrar", state="visible")
    print("1 caches:", pg.evaluate("Promise.race([navigator.serviceWorker.ready.then(() => new Promise(r => setTimeout(r, 2500))).then(() => caches.keys()), new Promise(r => setTimeout(() => r('sem SW'), 15000))])"))
    pg.reload(); pg.wait_for_selector("#l-entrar", state="visible"); print("1b SW controla:", pg.evaluate("!!navigator.serviceWorker.controller"))
    open(LOG, 'w').close(); pg.reload(); pg.wait_for_selector("#l-entrar", state="visible"); pg.wait_for_timeout(800)
    print("2 pedidos à rede ao reabrir:", sorted(set(open(LOG).read().split())))
    open(FLAG, 'w').close(); t0 = time.time(); pg.reload(wait_until="commit"); pg.wait_for_selector("#l-entrar", state="visible")
    print("3 rede lenta (página 8 s): abriu em %.1f s" % (time.time() - t0)); os.remove(FLAG); pg.wait_for_timeout(5000)
    ctx.set_offline(True); t0 = time.time(); pg.reload(wait_until="commit"); pg.wait_for_selector("#l-entrar", state="visible")
    print("4 sem rede: abriu em %.1f s" % (time.time() - t0))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
