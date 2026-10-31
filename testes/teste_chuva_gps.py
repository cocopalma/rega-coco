import json, subprocess, time, sys, datetime
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8797", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; HOJE = datetime.date.today().isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}]
PONTOS = [{"comunidade": "Farol", "zona": None, "lat": -10.6835, "lon": 40.6340}, {"comunidade": "Quitunda", "zona": None, "lat": -10.80, "lon": 40.45},
          {"comunidade": "Palma", "zona": "Incularino", "lat": -10.78, "lon": 40.47}, {"comunidade": "Palma", "zona": "Quilaua", "lat": -10.77, "lon": 40.48}]
rec = {"token": 0, "senhas": []}; erros = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        rec["token"] += 1; b = json.loads(r.post_data or "{}"); rec["senhas"].append(b.get("password"))
        if b.get("password") != "segredo12": return ok({"error": "invalid_grant", "error_description": "Invalid login credentials"}, 400)
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u-tec", "aud": "authenticated", "role": "authenticated", "email": "guidion@rega-coco.example.com"}})
    if "/auth/v1/logout" in u: return route.fulfill(status=204, body="")
    if "/rest/v1/perfis" in u: return ok({"id": "u-sup", "nome": "Raul", "papel": "supervisor", "activista_id": None})
    if "/storage/v1/object/chuva-fotos/" in u: rec.setdefault("fotos", []).append(u.split("chuva-fotos/")[1]); return ok({"Key": "x"})
    if "/rest/v1/chuva" in u: rec.setdefault("chuva", []).append((r.method, u.split("?")[1] if "?" in u else "", json.loads(r.post_data))); return route.fulfill(status=201, body="")
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol", "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/pontos_comunidades" in u: return ok(PONTOS)
    if "/rpc/" in u: return ok([])
    if "/rest/v1/registos_rega" in u and "teste=eq.true" in u: return ok([{"area_id": "PR1-1", "data": HOJE}])
    if "/rest/v1/registos_rega" in u: return ok([])
    if "/rest/v1/zonas" in u: return ok([{"comunidade": "Palma", "zona": "Incularino"}, {"comunidade": "Palma", "zona": "Quilaua"}])
    return ok({})
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, geolocation={"latitude": -10.801, "longitude": 40.451, "accuracy": 8}, permissions=["geolocation"])
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (print("DIALOGO:", d.message), d.accept()))
    pg.goto("http://localhost:8797/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "raul"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    print("0 pontos guardados:", len(pg.evaluate("LS.get('pontosCom')")))
    pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(800)
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.evaluate("S.fix=null"); pg.click("button[onclick=\"ecraChuva()\"]"); pg.wait_for_selector("#c-mm")
    print("1 Quitunda (sem rede): opções", pg.locator("#c-com option").all_inner_texts(), "|", pg.locator("text=Pelo GPS").inner_text())
    pg.fill("#c-mm", "4"); pg.set_input_files("#c-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("#c-prev", state="visible")
    pg.screenshot(path="/home/claude/rega-test/chuva_gps.png", full_page=True)
    pg.click("text=Guardar"); pg.wait_for_timeout(500)
    c = pg.evaluate("LS.get('filaChuva')[0]"); print("2 fila:", {k: c.get(k) for k in ("comunidade", "zona", "mm", "lat", "lon", "precisao_m")})
    ctx.set_geolocation({"latitude": -10.7795, "longitude": 40.4705, "accuracy": 10}); pg.evaluate("S.fix=null")
    pg.click("button[onclick=\"ecraChuva()\"]"); pg.wait_for_selector("#c-mm")
    print("3 Palma: opções", pg.locator("#c-com option").all_inner_texts(), "| escolhido:", pg.evaluate("$('#c-com').selectedOptions[0].text"))
    pg.click("text=Cancelar")
    ctx.set_geolocation({"latitude": -10.60, "longitude": 40.30, "accuracy": 10}); pg.evaluate("S.fix=null")
    pg.click("button[onclick=\"ecraChuva()\"]"); pg.wait_for_selector(".msg.erro")
    print("4 longe:", pg.inner_text(".msg.erro"), "| formulário?", pg.locator("#c-mm").count())
    pg.click("text=Cancelar")
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(2500)
    print("5 enviado:", [{k: b.get(k) for k in ("comunidade", "lat", "lon", "precisao_m", "teste")} for m, q, b in rec.get("chuva", [])])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
