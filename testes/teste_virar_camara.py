import json, subprocess, time, sys, datetime
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8798", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
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
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["camera"])
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (print("DIALOGO:", d.message), d.accept()))
    pg.goto("http://localhost:8798/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "raul"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.evaluate("camaraNaApp((b) => { window._foto = b && b.size; })"); pg.wait_for_selector("#cam-ov video"); pg.wait_for_timeout(1500)
    print("1 câmara aberta:", pg.is_visible("#cam-ov"), "| botão:", pg.is_visible("#cam-virar"), pg.inner_text("#cam-virar"), "(escondido: o navegador de teste só tem 1 câmara)")
    pg.evaluate("document.querySelector('#cam-virar').style.display=''")   # como num telefone com 2 câmaras
    pg.click("#cam-virar"); pg.wait_for_timeout(1200)
    print("2 virada (frente): vídeo", pg.evaluate("document.querySelector('#cam-ov video').videoWidth"), "| espelho:", pg.evaluate("document.querySelector('#cam-ov video').style.transform"), "| avisos:", pg.locator("body > .msg").all_inner_texts()[:1])
    pg.screenshot(path="/home/claude/rega-test/camara_virar.png")
    pg.click("#cam-virar"); pg.wait_for_timeout(1200); print("3 de novo atrás: espelho", repr(pg.evaluate("document.querySelector('#cam-ov video').style.transform")))
    pg.click("#cam-virar"); pg.wait_for_timeout(1200); pg.click("#cam-ok"); pg.wait_for_timeout(1200)
    print("4 foto tirada com a da frente:", pg.evaluate("window._foto"), "bytes | câmara fechada:", not pg.is_visible("#cam-ov"))
    print("ERROS JS:", erros or "nenhum")
    b.close()
srv.terminate()
