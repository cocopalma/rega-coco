import json, subprocess, time, sys, datetime
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8792", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; HOJE = datetime.date.today().isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}]
rec = {"token": 0, "senhas": []}; erros = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        rec["token"] += 1; b = json.loads(r.post_data or "{}"); rec["senhas"].append(b.get("password"))
        if b.get("password") != "segredo12": return ok({"error": "invalid_grant", "error_description": "Invalid login credentials"}, 400)
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u-tec", "aud": "authenticated", "role": "authenticated", "email": "guidion@rega-coco.example.com"}})
    if "/auth/v1/logout" in u: return route.fulfill(status=204, body="")
    if "/rest/v1/perfis" in u: return ok({"id": "u-tec", "nome": "Guidion Cristovao", "papel": "tecnico", "activista_id": None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol", "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/" in u: return ok([])
    if "/rest/v1/registos_rega" in u and "teste=eq.true" in u: return ok([{"area_id": "PR1-1", "data": HOJE}])
    if "/rest/v1/registos_rega" in u: return ok([])
    if "/rest/v1/zonas" in u: return ok([])
    return ok({})
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
    pg.goto("http://localhost:8792/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.click("#login [data-m=tecnico]"); pg.fill("#l-user", "guidion"); pg.fill("#l-senha", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.wait_for_timeout(1500)
    pg.click("nav button[data-e=lista]"); pg.wait_for_timeout(500)
    print("1 cor teste:", [t for t in pg.locator("#lista .tag").all_inner_texts()], "| legenda:", pg.evaluate("document.querySelector('#leg-teste').style.display"))
    print("  guardado:", {k: (v[:12] + '…') for k, v in pg.evaluate("JSON.parse(localStorage.getItem('rega.acessoOff'))").items() if k in ("email",)}, "| tem senha em claro:", "segredo12" in pg.evaluate("localStorage.getItem('rega.acessoOff')"))
    pg.click("#h-sair"); pg.wait_for_selector("#l-entrar", state="visible")
    ctx.set_offline(True)
    pg.click("#login [data-m=tecnico]"); pg.fill("#l-user", "guidion"); pg.fill("#l-senha", "errada99"); pg.click("#l-entrar"); pg.wait_for_timeout(2500)
    print("2 senha errada sem rede:", pg.inner_text("#l-msg"))
    pg.fill("#l-user", "outro"); pg.fill("#l-senha", "segredo12"); pg.click("#l-entrar"); pg.wait_for_timeout(1500)
    print("3 outro utilizador sem rede:", pg.inner_text("#l-msg"))
    t0 = rec["token"]
    pg.fill("#l-user", "guidion"); pg.fill("#l-senha", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible", timeout=10000)
    print("4 entrou sem rede:", pg.inner_text("#h-nome"), "| campos:", pg.evaluate("S.areas.length"), "| pedidos de token:", rec["token"] - t0)
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(3000)
    print("5 com rede: pedidos de token:", rec["token"] - t0, "| credPend:", pg.evaluate("S.credPend"), "| user:", pg.evaluate("S.user && S.user.id"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
