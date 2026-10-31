# GPS bloqueado no Chrome (v110, 24/10/2026: Sitambur e Eduardo "User denied Geolocation") e botão "Tirar" da câmara (Dalmar). LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8816", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 100, "vivas": 100, "latitude": -10.70, "longitude": 40.47, "activista_id": ACT, "activista_proposto": None}]
erros = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Activista Teste", "papel": "activista", "activista_id": ACT})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Teste", "comunidade_principal": "Farol"}])
    if "/rest/v1/areas" in u: return ok(areas)
    return ok([])
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
    ctx = b.new_context(viewport={"width": 390, "height": 844})   # sem autorização de localização
    ctx.grant_permissions(["camera"])
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.add_init_script("navigator.geolocation.watchPosition = (ok, falha) => { setTimeout(() => falha({ code: 1, message: 'User denied Geolocation' }), 300); return 1; }; navigator.geolocation.getCurrentPosition = (ok, falha) => setTimeout(() => falha({ code: 1, message: 'User denied Geolocation' }), 100);")
    pg.goto("http://localhost:8816/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "act"); pg.fill("#l-pin", "123987"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2000)
    print("1 folha:", pg.inner_text("#folha-c").replace("\n", " | ")[:600] if pg.is_visible("#folha-c") else "(nenhuma)")
    print("1b faixa:", pg.is_visible("#gps-neg"), pg.inner_text("#gps-neg") if pg.is_visible("#gps-neg") else "")
    pg.evaluate("fecharFolha()"); pg.click("#gps-neg"); pg.wait_for_timeout(300)
    print("1c ajuda:", pg.inner_text("#folha-c").replace("\n", " | ")[:700])
    pg.screenshot(path=f"/home/claude/rega-test/gps_negado{LING}.png")
    pg.evaluate("fecharFolha(); S.ajudaGpsVista = true; LS.set('jornada', {data: hojeISO(), pessoas: 3, id: 'j'})")
    pg.evaluate("marcarEntrada('PR1-1')"); pg.wait_for_timeout(1500)
    print("2 entrada:", pg.inner_text("#folha-c .msg.erro") if pg.locator("#folha-c .msg.erro").count() else pg.inner_text("#folha-c")[:200])
    pg.evaluate("camaraNaApp(() => {})"); pg.wait_for_timeout(1500)
    print("3 câmara:", pg.locator("#cam-ov button").all_inner_texts())
    pg.screenshot(path=f"/home/claude/rega-test/camara_botoes{LING}.png")
    print("ERROS JS:", erros or "nenhum"); b.close()

srv.terminate()
