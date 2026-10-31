# Mapa de plantas (15/10/2026): marcar sem rede, mudar o estado, remover, enviar com rede.
import json, subprocess, time, sys, math
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8812", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
lat0, lon0 = -10.6835, 40.6340; dy, dx = 1 / 110540, 1 / (111320 * math.cos(math.radians(10.6835)))
pol = [[lon0, lat0], [lon0 + 60*dx, lat0], [lon0 + 60*dx, lat0 + 50*dy], [lon0, lat0 + 50*dy]]
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 140, "vivas": 140, "latitude": lat0 + 25*dy, "longitude": lon0 + 30*dx, "activista_id": ACT, "activista_proposto": None, "poligono": pol}]
rec = {"rpc": []}; erros = []; dial = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "d@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Dalmar Santos", "papel": "gestor", "activista_id": None, "titulo": "Director", "gere_acessos": False})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Farol"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rest/v1/plantas" in u: return ok([])
    for f in ("gravar_planta", "estado_planta", "remover_planta"):
        if f"/rpc/{f}" in u: rec["rpc"].append((f, json.loads(r.post_data))); return ok(None)
    if "/rpc/" in u: return ok([])
    return ok([])
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, permissions=["geolocation"], geolocation={"latitude": lat0 + 10*dy, "longitude": lon0 + 10*dx, "accuracy": 3})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    pg.add_init_script("window.__PL_TESTE = true")
    pg.goto("http://localhost:8812/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "dalmar"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(300)
    print("1 botão:", [x for x in pg.locator("#folha-c button").all_inner_texts() if "plantas" in x])
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.click("text=Mapa das plantas"); pg.wait_for_selector("#pl-marcar"); pg.wait_for_timeout(500)
    tempos = []
    for i, (x, y) in enumerate([(10, 10), (18, 10), (26, 10), (26.5, 10.5)]):
        ctx.set_geolocation({"latitude": lat0 + y*dy, "longitude": lon0 + x*dx, "accuracy": 3}); pg.wait_for_timeout(300)
        n0 = pg.evaluate("plantasLocais('PR1-1').length"); t0 = time.time(); pg.click("#pl-marcar")
        pg.wait_for_function(f"plantasLocais('PR1-1').length > {n0} || document.querySelectorAll('#pl-sel .cartao').length && {i} == 3", timeout=8000); tempos.append(round(time.time() - t0, 1)); pg.wait_for_timeout(300)
    print("2a segundos por planta (GPS ±3 m):", tempos)
    # GPS fraco (±25 m): marca no máximo em ~4 s, com aviso
    ctx.set_geolocation({"latitude": lat0 + 30*dy, "longitude": lon0 + 40*dx, "accuracy": 25}); pg.wait_for_timeout(3500)
    n0 = pg.evaluate("plantasLocais('PR1-1').length"); t0 = time.time(); pg.click("#pl-marcar")
    pg.wait_for_function(f"plantasLocais('PR1-1').length > {n0}", timeout=8000)
    print("2b GPS fraco: segundos", round(time.time() - t0, 1), "| precisão gravada", pg.evaluate("plantasLocais('PR1-1').slice(-1)[0].precisao_m"), "| aviso:", pg.locator("body > .msg").all_inner_texts()[-1:], "| botão bloqueado?", pg.is_disabled("#pl-marcar"))
    print("2c botão apagar:", pg.inner_text("#pl-desfazer")); pg.click("#pl-desfazer"); pg.wait_for_timeout(300)
    print("2d depois de apagar: plantas", pg.evaluate("plantasLocais('PR1-1').map(p=>p.n)"), "| botão:", pg.inner_text("#pl-desfazer"))
    print("2 marcadas:", pg.evaluate("plantasLocais('PR1-1').map(p=>p.n)"), "| aviso perto:", [d for d in dial if "Já há" in d])
    pg.evaluate("selPlanta(plantasLocais('PR1-1')[1].id)"); pg.click("#ps-est >> text=Morta"); pg.click("#ps-cuid >> text=Cava-roda"); pg.click("text=Gravar o estado desta planta"); pg.wait_for_timeout(200)
    pg.evaluate("selPlanta(plantasLocais('PR1-1')[3].id)"); pg.click("button:has-text(\"Remover este ponto\")"); pg.wait_for_timeout(200)
    print("3 locais:", pg.evaluate("plantasLocais('PR1-1').map(p=>[p.n,p.estado,p.cavaroda])"), "| fila:", pg.evaluate("LS.get('filaAlt').map(x=>x.tipo+(x.planta?':'+x.planta.estado:''))"))
    print("4 resumo:", pg.inner_text("#pl-resumo").replace("\n", " | "))
    pg.screenshot(path="/home/claude/rega-test/plantas.png")
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    print("5 enviado:", [(f, {k: v for k, v in a.items() if k in ("p_n", "p_estado", "p_cavaroda", "p_precisao")}) for f, a in rec["rpc"]], "| fila:", pg.evaluate("LS.get('filaAlt').length"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
