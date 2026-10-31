# Hoje: os botões "Rega hoje" / "Recontagens das plantas" mudam logo, mesmo com o servidor lento (18/10/2026)
import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8814", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
UID = "22222222-2222-2222-2222-222222222222"
AREAS = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": None}]
REC = [{"id": "r1", "area_id": "PR1-1", "pr": "PR1", "produtor": "Produtor Um", "comunidade": "Farol", "motivo": "Teste", "estado": "por_encaminhar", "pedido_em": "2026-10-18T08:00:00Z"}]
LENTO = {"s": 0}
def mock(route):
    r = route.request; u = r.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "g@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Gestor", "papel": "gestor", "activista_id": None})
    if "/rest/v1/areas" in u: return ok(AREAS)
    if "/rpc/recontagens_lista" in u: return ok(REC)
    if "/rpc/" in u or ("/rest/v1/" in u and r.method == "GET"): return ok([])
    return route.fulfill(status=201, body="")
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    ctx.add_init_script("""(() => { const f0 = window.fetch; window.fetch = async (u, o) => { const s = String(u && u.url || u);
      if (window.__lento && /recontagens_lista|registos_rega|avisos_monitoria/.test(s)) await new Promise((ok) => setTimeout(ok, window.__lento));
      return f0(u, o); }; })();""")
    erros = []; pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8814/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate("modoEntrada('escritorio')"); pg.fill("#le-user", "g"); pg.fill("#le-senha", "x-senha-1"); pg.click("#le-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("#hoje-abas"); pg.wait_for_timeout(1000)
    pg.evaluate("window.__lento = 3000")
    for v, alvo in [("rec", "Por encaminhar a um oficial"), ("rega", "Hoje ·"), ("rec", "Por encaminhar a um oficial"), ("rega", "Hoje ·")]:
        t0 = time.time(); pg.click(f"#hoje-abas [data-v={v}]")
        pg.wait_for_function(f"document.querySelector('#hoje').innerText.includes({json.dumps(alvo)}) && document.querySelector('#hoje-abas [data-v={v}]').classList.contains('on')", timeout=10000)
        print(f"{v}: {int((time.time()-t0)*1000)} ms (servidor a demorar 3 s)")
        pg.wait_for_timeout(300)
    pg.wait_for_timeout(7000); print("depois do servidor:", pg.inner_text("#hoje-abas").replace("\n", " | "), "| vista:", pg.evaluate("vistaActual()"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
