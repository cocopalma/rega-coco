# Medição com a vara de 1 m na fotografia (v104, 23/10/2026): planta do Mapa das plantas e coqueiro; crescimento penúltimo → último.
# PAPEL=gestor / director (padrão supervisor: desde v106 não tem o botão, o teste pára no passo 1); LING=en / sw.
import json, subprocess, time, sys, math, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; PAPEL = os.environ.get("PAPEL", "supervisor"); LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8814", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; PL = "22222222-0000-0000-0000-000000000001"; CQ = "aaaaaaaa-0000-0000-0000-000000000001"
lat0, lon0 = -10.6835, 40.6340
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 140, "vivas": 140, "latitude": lat0, "longitude": lon0, "activista_id": ACT, "activista_proposto": None}]
anterior = [{"id": "m0", "altura_cm": 350, "diametro_cm": 8, "copa_cm": 120, "foto_path": "u/m0.jpg", "medido_em": "2026-09-23T08:00:00Z", "medido_por_nome": "Nuro", "meu": False}]
rec = {"rpc": [], "fotos": []}; erros = []; dial = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "d@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Teste Pessoa", "papel": PAPEL, "activista_id": None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Farol"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rest/v1/plantas" in u: return ok([{"id": PL, "n": 1, "lat": lat0, "lon": lon0, "precisao_m": 3, "estado": "viva", "cavaroda": False, "mulching": False, "marcada_em": "2026-10-20T08:00:00Z"}])
    if "/storage/v1/object/medicoes-fotos" in u: rec["fotos"].append(u.split("medicoes-fotos/")[-1]); return ok({"Key": "x"})
    if "/rpc/medicoes_alvo" in u: return ok(anterior)
    if "/rpc/coqueiros_lista" in u: return ok([{"id": CQ, "n": 1, "lat": lat0 + 0.0003, "lon": lon0, "precisao_m": 4, "estado": "viva", "local": "ACE", "observacao": None, "foto_path": "u/c.jpg", "marcado_em": "2026-10-23T10:00:00Z", "marcado_por_nome": "Dalmar Santos", "meu": False}] if PAPEL in ("gestor", "director") else None)
    if "/rpc/gravar_medicao" in u: rec["rpc"].append(json.loads(r.post_data)); return ok(None)
    return ok([])
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, permissions=["geolocation"], geolocation={"latitude": lat0, "longitude": lon0, "accuracy": 3})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.goto("http://localhost:8814/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "teste"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    if PAPEL == "director":
        pg.click("#b-coq"); pg.wait_for_timeout(800); pg.evaluate(f"verCoq('{CQ}')"); pg.wait_for_timeout(300)
        bt = [x for x in pg.locator("#folha-c button").all_inner_texts() if "📏" in x]; print("D1 botão no coqueiro:", bt)
        pg.click("#folha-c button:has-text('📏')"); pg.wait_for_timeout(800)
        print("D2 ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:300], "| campo foto:", pg.is_visible("#vr-foto-cambtn"))
        print("ERROS JS:", erros or "nenhum"); b.close(); srv.terminate(); sys.exit()
    pg.evaluate("ecraPlantas('PR1-1')"); pg.wait_for_timeout(1200); pg.evaluate(f"selPlanta('{PL}')"); pg.wait_for_timeout(300)
    bt = [x for x in pg.locator("#pl-sel button").all_inner_texts() if "📏" in x]; print("1 botão na planta:", bt)
    pg.click("#pl-sel button:has-text('📏')"); pg.wait_for_timeout(1000)
    print("2 ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:260])
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    # fotografia de teste (400 x 800) desenhada no navegador
    pg.evaluate("""(async () => { const c = document.createElement('canvas'); c.width = 400; c.height = 800; const g = c.getContext('2d'); g.fillStyle = '#8bc34a'; g.fillRect(0, 0, 400, 800);
      const b = await new Promise((ok) => c.toBlob(ok, 'image/jpeg', 0.8)); S.vara.foto = b; carregarImgVara(b); })()"""); pg.wait_for_timeout(800)
    print("3 passo:", pg.inner_text("#vr-passo"))
    cv = pg.locator("#vr-cv"); bb = cv.bounding_box()
    def toque(x, y):
        c = pg.locator("#vr-cv"); q = c.bounding_box(); c.click(position={"x": x * q["width"], "y": y * q["height"]})
    for (x, y) in [(0.3, 0.9), (0.3, 0.7), (0.5, 0.9), (0.5, 0.1)]: toque(x, y); pg.wait_for_timeout(120)
    print("4 passo:", pg.inner_text("#vr-passo"), "| saltar visível:", pg.is_visible("#vr-saltar"))
    pg.click("#vr-gravar"); pg.wait_for_timeout(200); print("5 sem diâmetro/copa →", dial[-1] if dial else "")
    for (x, y) in [(0.48, 0.6), (0.52, 0.6), (0.2, 0.15), (0.8, 0.15)]: toque(x, y); pg.wait_for_timeout(120)
    print("6 resultado:", pg.inner_text("#vr-res").replace("\n", " | "), "| passo:", pg.inner_text("#vr-passo"))
    # arrastar o topo da planta um pouco para cima
    pg.evaluate("document.querySelector('#vr-cv').scrollIntoView({block: 'center'})"); pg.wait_for_timeout(200)
    bb = cv.bounding_box(); sx, sy = bb["x"] + 0.5 * bb["width"], bb["y"] + 0.12 * bb["height"]
    pg.mouse.move(sx, sy); pg.mouse.down(); pg.mouse.move(sx, sy - 0.04 * bb["height"], steps=5); pg.mouse.up(); pg.wait_for_timeout(200)
    print("7 depois de arrastar:", pg.inner_text("#vr-res").split("\n")[0:2])
    pg.screenshot(path=f"/home/claude/rega-test/vara{LING}.png")
    pg.click("#vr-gravar"); pg.wait_for_timeout(800)
    print("8 fila:", pg.evaluate("filaMed().map(m => [m.tipo, m.altura_cm, m.diametro_cm, m.copa_cm])"))
    print("9 ecrã depois:", pg.inner_text("#folha-c").replace("\n", " | ")[:420])
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    print("10 enviado:", [(a["p_tipo"], a["p_area"], a["p_altura"], a["p_diametro"], a["p_copa"], bool(a["p_foto"]), len(a["p_pontos"] or [])) for a in rec["rpc"]], "| fotos:", len(rec["fotos"]), "| fila:", pg.evaluate("filaMed().length"))
    # saltar a copa numa 2.ª medição
    pg.evaluate("""(async () => { const c = document.createElement('canvas'); c.width = 400; c.height = 800; const b = await new Promise((ok) => c.toBlob(ok, 'image/jpeg', 0.8)); S.vara.foto = b; carregarImgVara(b); })()"""); pg.wait_for_timeout(800)
    bb = pg.locator("#vr-cv").bounding_box()
    for (x, y) in [(0.3, 0.9), (0.3, 0.7), (0.5, 0.9), (0.5, 0.05)]: toque(x, y); pg.wait_for_timeout(100)
    pg.click("#vr-saltar"); pg.wait_for_timeout(100); pg.click("#vr-saltar"); pg.wait_for_timeout(100)
    print("11 saltou diâmetro e copa:", pg.inner_text("#vr-passo"), "|", pg.inner_text("#vr-res").replace("\n", " | "))
    pg.click("#vr-desf"); pg.wait_for_timeout(100); print("12 desfazer volta ao passo:", pg.inner_text("#vr-passo"))
    pg.click("#vr-saltar"); pg.wait_for_timeout(100)
    pg.click("#folha-c .btn.sec >> nth=-1"); pg.wait_for_timeout(1200)
    print("13 voltou ao mapa das plantas:", pg.is_visible("#pl-marcar"), "| planta seleccionada:", pg.is_visible("#pl-sel .cartao"))
    if PAPEL == "gestor":
        pg.evaluate("fecharFolha()"); pg.click("#b-coq"); pg.wait_for_timeout(800); pg.evaluate(f"verCoq('{CQ}')"); pg.wait_for_timeout(300)
        print("14 coqueiro (gestor):", [x for x in pg.locator("#folha-c button").all_inner_texts() if "📏" in x])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
