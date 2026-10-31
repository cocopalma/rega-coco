# Fotografias obrigatórias na rega: entrada, evidência da rega e saída (15/10/2026). Sem rede e depois com rede.
import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8808", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}]
rec = {"fotos": [], "registos": []}; erros = []; dialogos = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Activista Exemplo", "papel": "activista", "activista_id": ACT})
    if "/storage/v1/object/rega-fotos/" in u: rec["fotos"].append((u.split("rega-fotos/")[1], len(r.post_data_buffer or b""))); return ok({"Key": "x"})
    if "/rest/v1/registos_rega" in u:
        if r.method == "POST": rec["registos"] += json.loads(r.post_data) if r.post_data.startswith("[") else [json.loads(r.post_data)]; return route.fulfill(status=201, body="")
        return ok([])
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Farol", "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/estado_ronda" in u: return ok([{"area_id": a["id"], "ultima_rega": None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False} for a in areas])
    if "/rpc/" in u: return ok([])
    if "/rest/v1/zonas" in u: return ok([])
    return route.fulfill(status=201, body="")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.goto("http://localhost:8808/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "act"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.evaluate("LS.set('jornada', {id:'j', data: hojeISO(), pessoas: 4})")
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.evaluate("abrirFicha('PR1-1')"); pg.click("text=Cheguei — marcar entrada"); pg.wait_for_selector("text=Fotografia da equipa a chegar ao campo", timeout=15000)
    print("1 depois da entrada:", pg.inner_text("#folha-c").split("\n")[:3])
    pg.set_input_files("#fr-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("text=Fotografia da entrada guardada.")
    print("2 ficha:", [l for l in pg.inner_text("#folha-c").split("\n") if "📷" in l or "✓" in l or "Tirar" in l][:4])
    pg.click("text=Terminei — marcar saída"); pg.fill("#s-plantas", "65"); pg.click("text=Marcar saída e guardar"); pg.wait_for_timeout(400)
    print("3 sem foto da rega:", dialogos[-1:], "| ecrã:", pg.inner_text("#folha-c").split("\n")[0])
    pg.set_input_files("#fr-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("text=Fotografia da rega (evidência) guardada.")
    pg.click("text=Terminei — marcar saída"); pg.fill("#s-plantas", "65"); pg.click("text=Marcar saída e guardar"); pg.wait_for_timeout(400)
    print("4 sem foto da saída:", dialogos[-1:])
    pg.set_input_files("#s-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("#s-foto-ok span"); print("5", pg.inner_text("#s-foto-ok"))
    pg.fill("#s-plantas", "65"); pg.click("text=Marcar saída e guardar"); pg.wait_for_selector("text=Rega guardada", timeout=15000)
    print("6 fila:", pg.evaluate("LS.get('fila').map(x => Object.keys(x.fotos||{}).join(','))"), "| IDB:", pg.evaluate("(async()=>{const id=LS.get('fila')[0].id; return [await FOTOS.ler(id+'-entrada'), await FOTOS.ler(id+'-rega'), await FOTOS.ler(id+'-saida')].map(x=>x?x.size:null)})()"))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    r0 = rec["registos"][0] if rec["registos"] else {}
    print("7 enviado: fotos", rec["fotos"], "| registo:", {k: r0.get(k) for k in ("foto_entrada", "foto_rega", "foto_saida")}, "| tem 'fotos'?", "fotos" in r0, "| horas:", bool(r0.get("foto_entrada_em") and r0.get("foto_rega_em") and r0.get("foto_saida_em")))
    print("8 fila depois:", pg.evaluate("LS.get('fila').length"), "| IDB apagado:", pg.evaluate("(async()=>{const id=%r; return await FOTOS.ler(id+'-entrada')})()" % r0.get("id")) is None)
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
