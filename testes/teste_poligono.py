import json, subprocess, time, sys, datetime
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8794", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; HOJE = datetime.date.today().isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6865, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None,
           "poligono": [[40.6335, -10.6840], [40.6345, -10.6840], [40.6345, -10.6830], [40.6335, -10.6830], [40.6335, -10.6840]]},
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
    if "/rest/v1/perfis" in u: return ok({"id": "u-act", "nome": "Majula Muemede Bacar", "papel": "activista", "activista_id": ACT})
    if "/storage/v1/object/chuva-fotos/" in u: rec.setdefault("fotos", []).append(u.split("chuva-fotos/")[1]); return ok({"Key": "x"})
    if "/rest/v1/chuva" in u: rec.setdefault("chuva", []).append((r.method, u.split("?")[1] if "?" in u else "", json.loads(r.post_data))); return route.fulfill(status=201, body="")
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
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (print("DIALOGO:", d.message), d.accept()))
    ctx.grant_permissions(["geolocation"]); ctx.set_geolocation({"latitude": -10.6836, "longitude": 40.6341, "accuracy": 8})
    pg.goto("http://localhost:8794/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "majula"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.evaluate("LS.set('jornada', {id:'j', data: hojeISO(), pessoas: 4})"); pg.wait_for_timeout(1500)
    print("0 funções:", pg.evaluate("[Math.round(distPoligono(-10.6836, 40.6341, S.areas[0].poligono)), Math.round(distPoligono(-10.6850, 40.6341, S.areas[0].poligono)), Math.round(metros([-10.6836, 40.6341], [S.areas[0].latitude, S.areas[0].longitude]))]"))
    pg.screenshot(path="/home/claude/rega-test/mapa_poligono.png")
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(400)
    print("1 ficha:", [l for l in pg.inner_text("#folha-c").split("\n") if "Dist" in l or "Limite" in l or "dentro" in l or "polígono" in l][:4])
    pg.click("text=Cheguei — marcar entrada"); pg.wait_for_timeout(2500)
    print("2 entrada:", pg.inner_text("#folha-c .msg")[:120])
    ctx.set_geolocation({"latitude": -10.6870, "longitude": 40.6341, "accuracy": 8})
    pg.evaluate("LS.del('emCurso'); abrirFicha('PR2-1')"); pg.wait_for_timeout(300)
    pg.click("#folha-x"); pg.click("nav button[data-e=lista]"); pg.select_option("#f-sit", "sem"); pg.wait_for_timeout(300)
    print("3 filtro:", pg.inner_text("#lista .msg")[:80]); pg.click("text=← Ver todos os campos"); pg.wait_for_timeout(300); print("   depois:", pg.eval_on_selector("#f-sit", "e => e.value"), "|", pg.inner_text("#lista")[:60].replace("\n"," | "))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
