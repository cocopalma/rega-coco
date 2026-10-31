import json, subprocess, time, sys, datetime
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8799", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; HOJE = datetime.date.today().isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}]
rec = {"token": 0, "senhas": []}; erros = []; EST = {"voltou": False}
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
    if "/rpc/lista_comunidades" in u: return ok(["Farol", "Mondlane", "Namanengo", "Palma"])
    if "/rpc/definir_comunidade" in u: rec.setdefault("com", []).append(json.loads(r.post_data)); return ok(None)
    if "/rpc/gravar_poligono" in u: rec.setdefault("pol", []).append(json.loads(r.post_data)); return ok({"id": "PR1-1", "area_m2": 900})
    if "/rpc/areas_fora_plano" in u: rec.setdefault("procura", []).append(json.loads(r.post_data)); return ok([{"id": "PR396000-1", "pr": "PR396000", "comunidade": "Palma", "zona": None, "produtor": "Abdala Salimo Mussa", "instaladas": 232, "vivas": 232, "data_plantio": "2026-04-09", "agua_origem": "COM", "n_regas_origem": 2, "ultima_rega_origem": "2026-09-26", "activista_origem": "Oliveira Camilo Adolfo", "tem_coord": True, "fonte": "x", "motivo_saida": None}])
    if "/rpc/voltar_a_regar" in u: rec.setdefault("voltar", []).append(json.loads(r.post_data)); EST["voltou"] = True; return ok({"id": "PR396000-1", "activista_id": None})
    if "/rest/v1/areas" in u: return ok(areas + ([{"id": "PR396000-1", "pr": "PR396000", "area_n": 1, "comunidade": "Farol", "produtor": "Abdala Salimo Mussa", "instaladas": 232, "vivas": 232, "latitude": -10.684, "longitude": 40.633, "activista_id": None, "activista_proposto": None, "reactivada_em": datetime.datetime.utcnow().isoformat() + "Z"}] if EST["voltou"] else []))
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/" in u: return ok([])
    if "/rest/v1/registos_rega" in u and "teste=eq.true" in u: return ok([{"area_id": "PR1-1", "data": HOJE}])
    if "/rest/v1/registos_rega" in u: return ok([])
    if "/rest/v1/zonas" in u: return ok([])
    return ok({})
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["camera", "geolocation"], geolocation={"latitude": -10.6835, "longitude": 40.6340, "accuracy": 4})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (print("DIALOGO:", d.message), d.accept()))
    pg.goto("http://localhost:8799/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "raul"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    import math
    lat0, lon0 = -10.6835, 40.6340
    dy, dx = 1 / 110540, 1 / (111320 * math.cos(math.radians(10.6835)))
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(400)
    print("1 botão:", [b for b in pg.locator("#folha-c button").all_inner_texts() if "Medir" in b])
    pg.click("text=Medir a área (andar à volta do campo)"); pg.wait_for_selector("#md-ir"); pg.wait_for_timeout(500)
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.click("#md-ir"); pg.wait_for_timeout(300)
    lado = 30; pts = []
    for (ax, ay, bx, by) in [(0,0,lado,0),(lado,0,lado,lado),(lado,lado,0,lado),(0,lado,0,0)]:
        for k in range(1, 7):
            t = k / 6; pts.append((ax + (bx-ax)*t, ay + (by-ay)*t))
    for n, (x, y) in enumerate(pts):
        ctx.set_geolocation({"latitude": lat0 + y*dy, "longitude": lon0 + x*dx, "accuracy": 4}); pg.wait_for_timeout(250)
        if n == 10:   # a app fecha a meio da volta
            pg.reload(wait_until="domcontentloaded"); pg.wait_for_selector("#md-n", timeout=8000); pg.wait_for_timeout(500)
            print("2 depois de a app fechar a meio:", pg.inner_text("#folha-c").split("\n")[1][:80], "| pontos:", pg.inner_text("#md-n"))
    print("3 durante:", pg.inner_text("#md-n"), "pontos |", pg.inner_text("#md-per"), "|", pg.inner_text("#md-area"))
    pg.screenshot(path="/home/claude/rega-test/medir.png")
    pg.click("#md-fim"); pg.wait_for_timeout(300)
    print("4 resumo:", pg.inner_text("#folha-c").replace("\n", " | ")[:220])
    pg.click("text=Gravar esta área"); pg.wait_for_timeout(500)
    print("5 ficha:", [l for l in pg.inner_text("#folha-c").split("\n") if "Área" in l or "Limite" in l or "gravada" in l][:4], "| fila:", pg.evaluate("LS.get('filaAlt').map(x=>x.tipo+':'+x.pontos.length+':'+x.area_m2)"))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(2500)
    print("5b botões depois de medir:", [b for b in pg.locator("#folha-c button").all_inner_texts() if "Medir" in b or "coordenada" in b or "comunidade" in b])
    pg.click("text=Mudar a comunidade"); pg.wait_for_selector("#cm-com"); print("7 comunidades:", pg.locator("#cm-com option").all_inner_texts())
    pg.select_option("#cm-com", "Namanengo"); pg.click("#folha-c >> text=Gravar"); pg.wait_for_timeout(300)
    print("8 ficha:", [l for l in pg.inner_text("#folha-c").split("\n") if "Comunidade" in l or "mudada" in l][:3])
    print("6 enviado:", [(x["p_area"], len(x["p_pontos"]), x["p_precisao"]) for x in rec.get("pol", [])], "| comunidade:", rec.get("com"), "| fila:", pg.evaluate("LS.get('filaAlt').length"), "| rascunho:", pg.evaluate("LS.get('rascMedir')"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
