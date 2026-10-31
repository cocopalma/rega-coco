import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8783", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
areas = [
  {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
  {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None},
]
lista = [{"amostra_id": "a1", "data_rega": "2026-10-11", "area_id": "PR1-1", "activista_id": ACT, "feita": False},
         {"amostra_id": "a2", "data_rega": "2026-10-11", "area_id": "PR2-1", "activista_id": ACT, "feita": False}]
rec = {"fotos": [], "mon": [], "n": []}
erros = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u-tec", "aud": "authenticated", "role": "authenticated", "email": "guidion@rega-coco.example.com"}})
    if "/storage/v1/object/monitoria-fotos/" in u: rec["fotos"].append((u.split("monitoria-fotos/")[1], len(r.post_data_buffer or b""))); return ok({"Key": "monitoria-fotos/x"})
    if "/rest/v1/perfis" in u: return ok({"id": "u-tec", "nome": "Guidion Cristovao", "papel": "tecnico", "activista_id": None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol", "equipa_tamanho": None}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/monitoria_lista" in u: return ok(lista)
    if "/rpc/monitorias_campo" in u: return ok([{"id": "m9", "data_rega": "2026-10-10", "feito_em": "2026-10-11T07:00:00Z", "verificador": "Raul", "nota": 6.5, "pct_humido": 65, "solo_regado": False, "metodo": "X", "plantas_obs": 31, "foto_path": "u-tec/m9.jpg"}])
    if "/storage/v1/object/sign/monitoria-fotos/" in u: rec.setdefault("sign", []).append(u); return ok({"signedURL": "/storage/v1/object/sign/monitoria-fotos/u-tec/m9.jpg?token=t"})
    if "/storage/v1/object/sign/" in u and "token=" in u: return route.fulfill(status=200, content_type="image/jpeg", body=open("/home/claude/rega-test/foto_teste.jpg","rb").read())
    if "/rpc/avisos_monitoria" in u: return ok([{"id": "m9", "area_id": "PR2-1", "activista_id": ACT, "data_rega": "2026-10-10", "feito_em": "2026-10-11T07:00:00Z", "verificador": "Raul", "nota": 6.5, "pct_humido": 65, "solo_regado": False, "plantas_obs": 31, "sem_rega": 11, "observacao": "solo seco junto ao caminho"}])
    if "/rpc/estado_ronda" in u: return ok([])
    if "/rpc/definir_equipa_tamanho" in u: rec["n"].append(json.loads(r.post_data)); return ok(None)
    if "/rest/v1/monitorias" in u and r.method == "POST":
        b = json.loads(r.post_data); rec["mon"].append(b); return route.fulfill(status=201, body="")
    if "/rest/v1/registos_rega" in u: return ok([{"activista_id": ACT, "area_id": "PR1-1", "plantas_regadas": 70, "alerta": None, "gps_valido": True, "teste": False, "entrada_em": "2026-10-11T04:40:00Z", "saida_em": "2026-10-11T05:20:00Z", "pessoas": 5, "agua_em": "2026-10-11T05:05:00Z"},
        {"activista_id": ACT, "area_id": "PR2-1", "plantas_regadas": 60, "alerta": None, "gps_valido": True, "teste": False, "entrada_em": "2026-10-11T05:30:00Z", "saida_em": "2026-10-11T06:15:00Z", "pessoas": 4, "agua_em": None}])
    if "/rest/v1/zonas" in u: return ok([])
    return ok({})
def plantas(sim, nao, morta=0, estado_nao='viva'):
    for i in range(sim): pg.click("#m-h .chip[data-v='1']"); pg.click("#m-e .chip[data-v='viva']"); pg.click(f"#m-c .chip[data-v='{['ambos','mulching','cava','nenhum'][i % 4]}']")
    for _ in range(nao): pg.click("#m-h .chip[data-v='0']"); pg.click(f"#m-e .chip[data-v='{estado_nao}']"); pg.click("#m-c .chip[data-v='nenhum']")
    for _ in range(morta): pg.click("#m-h .chip[data-v='0']"); pg.click("#m-e .chip[data-v='morta']"); pg.click("#m-c .chip[data-v='nenhum']")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"], viewport={"width": 390, "height": 844})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (print("DIALOGO:", d.message), d.accept()))
    pg.goto("http://localhost:8783/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "guidion"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("text=Monitoria · regas de", timeout=10000)
    print("0 tabela:", pg.inner_text("#hoje table"))
    print("1a avisos:", pg.inner_text("#hoje .cartao >> nth=0").replace("\n", " | "))
    print("1 hoje:", pg.inner_text("#hoje").split("Hoje ·")[0].replace("\n", " | "))
    pg.screenshot(path="/home/claude/rega-test/mon_hoje.png", full_page=True)
    pg.click("#hoje table .chip"); pg.fill("#t-n", "6"); pg.click("text=Guardar"); pg.wait_for_timeout(800)
    print("0b tamanho:", rec["n"], "|", pg.inner_text("#hoje table").split("\n")[1])
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_selector("text=Verificar este campo")
    pg.click("text=Verificar este campo"); pg.wait_for_selector("#m-metodo")
    pg.click("#m-gravar"); pg.wait_for_timeout(300)   # sem percurso → aviso
    pg.click("#m-metodo .chip[data-v='X']"); print("1b alvo:", pg.inner_text("#m-planta").split("\n")[:2]); plantas(3, 1); pg.screenshot(path="/home/claude/rega-test/mon_metodo.png"); pg.click("text=Desfazer a última planta"); pg.click("text=Desfazer a última planta"); pg.click("text=Desfazer a última planta"); pg.click("text=Desfazer a última planta")
    plantas(28, 5, 0); pg.click("#m-gravar"); pg.wait_for_timeout(300)   # 33 de 33? ver
    pg.click("text=Desfazer a última planta"); pg.click("#m-gravar"); pg.wait_for_timeout(300)   # falta 1 → aviso
    plantas(0, 1, 1); pg.click("#m-gravar"); pg.wait_for_timeout(300)   # sem foto → aviso
    print("1c resumo:", pg.inner_text("#m-planta").replace("\n", " | ")[:260])
    pg.set_input_files("#m-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("#m-prev", state="visible")
    pg.screenshot(path="/home/claude/rega-test/mon_ficha.png", full_page=True)
    pg.fill("#m-obs", "teste"); pg.click("#m-gravar"); pg.wait_for_selector("text=Verificação guardada", timeout=15000); pg.wait_for_timeout(2500)
    print("2 enviado: fotos", rec["fotos"], "| monitorias", [{k: m[k] for k in ("amostra_id", "solo_regado", "nota", "metodo", "plantas_no_campo", "plantas_alvo", "pct_humido", "n_vivas", "n_secas", "n_mortas", "foto_path", "gps_valido")} | {"obs": len(m["plantas_obs"]), "cob": sum(1 for o in m["plantas_obs"] if o.get("cobertura")), "cava": sum(1 for o in m["plantas_obs"] if o.get("cavaroda"))} for m in rec["mon"]])
    print("   fila:", pg.evaluate("JSON.parse(localStorage.getItem('rega.filaMon')).length"), "| ficha:", pg.inner_text("#folha-c")[:60].replace("\n", " "))
    # segundo campo sem rede
    pg.click("#folha-x"); ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.evaluate("abrirFicha('PR2-1')"); pg.click("text=Verificar este campo"); pg.wait_for_selector("#m-metodo")
    pg.click("#m-metodo .chip[data-v='W']"); pg.click("#m-Nmudar"); pg.fill("#m-N", "40"); pg.dispatch_event("#m-N", "input")
    print("3a alvo N=40:", pg.inner_text("#m-planta").split("\n")[:2]); plantas(20, 7, 0, 'seca')
    pg.set_input_files("#m-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("#m-prev", state="visible")
    pg.click("#m-gravar"); pg.wait_for_selector("text=Verificação guardada", timeout=15000); pg.wait_for_timeout(800)
    print("3 sem rede: fila", pg.evaluate("JSON.parse(localStorage.getItem('rega.filaMon')).length"), "| botão:", pg.inner_text("#h-sync"))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(3000)
    print("   2.º:", {k: rec["mon"][-1][k] for k in ("solo_regado", "nota", "metodo", "plantas_alvo", "pct_humido", "n_secas")})
    print("4 com rede: fila", pg.evaluate("JSON.parse(localStorage.getItem('rega.filaMon')).length"), "| enviados", len(rec["mon"]), "| fotos", [f[1] for f in rec["fotos"]])
    pg.click("#folha-x"); pg.click("nav button[data-e=mapa]"); pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(1000)
    print("5 hoje:", pg.inner_text("#hoje").split("Hoje ·")[0].replace("\n", " | "))
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300); print("6 ficha aviso:", pg.inner_text("#folha-c .msg")[:250].replace("\n", " | "))
    pg.wait_for_timeout(800); print("7 ficha monitoria:", pg.inner_text("#f-mon").replace("\n", " | ")[:200], "| assinaturas antes:", len(rec.get("sign", [])))
    pg.click("#f-mon .chip"); pg.wait_for_timeout(1000); print("   foto aberta:", pg.locator("#foto-modal img").count(), "| assinaturas:", len(rec.get("sign", [])))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
