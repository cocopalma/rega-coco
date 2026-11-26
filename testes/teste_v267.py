import json, subprocess, time, sys, os
LING = os.environ.get("LING", "pt")
from playwright.sync_api import sync_playwright
# v266 (26/11/2026): tocar num campo dentro da área de expansão abre o campo (o limite não responde); campos fora do plano em pontos cinzentos; área por plantar. Base: v211 (07/11/2026, Valdo): área de expansão 2027 (KMZ) no mapa, com os campos da base dentro; desde a v265 todos os papéis menos o activista. PAPEL=activista / cliente / me; LING=en / sw
APP = "http://localhost:8767/"
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8767", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
PROP = [[40.6336,-10.6831],[40.6346,-10.6831],[40.6346,-10.6841],[40.6336,-10.6841]]
areas = [{"id": "PR9-1", "pr": "PR9", "area_n": 1, "comunidade": "Senga", "produtor": "Produtor Nove", "instaladas": 97, "vivas": 97, "latitude": None, "longitude": None, "poligono": None, "limites_abertos": True, "poligono_proposto": PROP, "area_m2_proposta": 5595.9, "proposta_em": "2026-11-07T06:22:22Z", "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-02-11"}]
PAPEL = os.environ.get("PAPEL", "supervisor")
POL = [[40.5810674,-10.6857676],[40.5827412,-10.6827865],[40.5855598,-10.6859502],[40.5851765,-10.6882276],[40.5810324,-10.688033],[40.5810674,-10.6857676]]
areas = [{"id": "PR396327-1", "pr": "PR396327", "area_n": 1, "comunidade": "Quiwia", "produtor": "Sufo Muemede Nfaume", "instaladas": 140, "vivas": 140, "latitude": -10.685376, "longitude": 40.584116, "poligono": None, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-02-11"}]
EXP = [{"id": "exp2027-quiwia", "nome": "Área de expansão 2027", "ano": 2027, "comunidade": "Quiwia", "area_m2": 170800, "nota": "O Paulo informou que antigamente este espaço era uma plantação de coco de uma companhia alemã.", "poligono": POL,
        "campos": [{"id": "PR396327-1", "pr": "PR396327", "area_n": 1, "produtor": "Sufo Muemede Nfaume", "comunidade": "Quiwia", "activa": True, "nao_existe": False, "vivas": 140, "instaladas": 140, "activista": "Alafo Arlindo Jose", "lat": -10.685376, "lon": 40.584116, "area_m2": 6813},
                   {"id": "PR693502-1", "pr": "PR693502", "area_n": 1, "produtor": "Amido Saide Amurane", "comunidade": "Quiwia", "activa": False, "nao_existe": False, "vivas": 0, "instaladas": 140, "activista": None, "lat": -10.686209, "lon": 40.581303, "area_m2": None}]}]
erros = []
def mock(route):
    r = route.request; u = r.url
    def ok(b, st=200): route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r",
                   "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "raul@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Raul Miquilange", "papel": PAPEL, "activista_id": ACT if PAPEL == "activista" else None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Alafo Arlindo Jose", "comunidade_principal": "Quiwia", "supervisor": "Raul Miquilange"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/areas_expansao_lista" in u: return ok(EXP if PAPEL != "activista" else [])
    if "/rpc/" in u and any(k in u for k in ("estado_ronda", "regas_", "lista", "meu_dia")): return ok([])
    return ok({}) if r.method != "GET" else ok([])
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"], viewport={"width": 390, "height": 800})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
    pg.goto(APP); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate("document.querySelectorAll('button').forEach(b=>{if(/Técnico|Technician|Fundi/.test(b.textContent)&&b.offsetParent)b.click()})")
    pg.fill("#l-user", "raul"); pg.fill("#l-senha" if pg.is_visible("#l-senha") else "#l-pin", "abcdef1"); pg.click("#l-entrar")
    pg.wait_for_function("S.areas && S.areas.length", timeout=15000); pg.wait_for_timeout(2500)
    if pg.is_visible("#folha.on"): pg.evaluate("fecharFolha()")
    pg.click("nav button[data-e=mapa]"); pg.wait_for_timeout(800)
    nexp = pg.evaluate("camada.getLayers().filter(l => l.options && l.options.color === '#ad1457').length"); et = pg.locator(".ic-exp").count()
    print("1 mapa: limite", nexp, "etiqueta", et, pg.inner_text(".ic-exp") if et else "")
    if PAPEL == "activista":
        print("RESULTADO", "OK" if nexp == 0 and et == 0 and not erros else "FALHA", erros); b.close(); srv.terminate(); sys.exit()
    ok0 = pg.evaluate("camada.getLayers().filter(l => l.options && l.options.color === '#ad1457').every(l => l.options.interactive === false)")
    pg.evaluate("mapa.setView([-10.685376, 40.584116], 18)"); pg.wait_for_timeout(800)
    pt = pg.evaluate("(() => { const p = mapa.latLngToContainerPoint([-10.685376, 40.584116]), r = mapa.getContainer().getBoundingClientRect(); return [r.left + p.x, r.top + p.y]; })()")
    pg.mouse.click(pt[0], pt[1]); pg.wait_for_timeout(500)
    if not pg.is_visible("#folha.on"): pg.mouse.click(pt[0], pt[1]); pg.wait_for_timeout(700)   # 1.º toque mostra a etiqueta (v239)
    tf = pg.inner_text("#folha-c") if pg.is_visible("#folha.on") else ""
    okA = ok0 and "Sufo Muemede Nfaume" in tf and "Área de expansão 2027" not in tf.split("\n")[0]
    print("4 tocar no campo dentro da área abre o campo:", okA, "| limite sem toque:", ok0, "|", tf[:120].replace("\n", " | "))
    pg.evaluate("fecharFolha()"); pg.wait_for_timeout(300)
    pg.evaluate("mudar('mapa'); mapa.setView([-10.686209, 40.581303], 13)"); pg.wait_for_timeout(800)
    n13 = pg.evaluate("mapa.hasLayer(expPts) ? expPts.getLayers().length : 0"); leg2 = pg.evaluate("getComputedStyle(document.querySelector('#leg-exp2')).display !== 'none'")
    print("7 zoom 13: pontos cinzentos no mapa", n13, "| linha na legenda", leg2)
    pg.evaluate("mapa.setView([-10.686209, 40.581303], 18)"); pg.wait_for_timeout(800)
    n18 = pg.evaluate("mapa.hasLayer(expPts) ? expPts.getLayers().length : 0"); print("8 zoom 18: pontos cinzentos no mapa", n18)
    okZ = n13 == 0 and n18 > 0 and leg2
    pt2 = pg.evaluate("(() => { const p = mapa.latLngToContainerPoint([-10.686209, 40.581303]), r = mapa.getContainer().getBoundingClientRect(); return [r.left + p.x, r.top + p.y]; })()")
    pg.mouse.click(pt2[0], pt2[1]); pg.wait_for_timeout(700)
    tg = pg.inner_text("#folha-c") if pg.is_visible("#folha.on") else ""
    okB = "Amido Saide Amurane" in tg and ("fora do plano" in tg or "outside" in tg or "nje ya" in tg)
    print("5 ponto cinzento do campo fora do plano abre a ficha curta:", okB, "|", tg[:140].replace("\n", " | "))
    pg.evaluate("fecharFolha()"); pg.wait_for_timeout(300)
    pg.locator(".ic-exp").first.click(); pg.wait_for_selector("#folha.on"); pg.wait_for_timeout(400)
    t = pg.inner_text("#folha-c").replace(chr(10), " | "); print("2 ficha:", t[:400])
    tp = pg.inner_text("#exp-plantada") + " / " + pg.inner_text("#exp-resta"); print("6 área:", tp)
    okC = "0,7" in tp.split("/")[0] or "0.7" in tp.split("/")[0]
    okC = okC and ("16,4" in tp or "16.4" in tp)
    ok1 = nexp == 1 and "Sufo Muemede Nfaume" in t and "Amido Saide Amurane" in t
    pg.screenshot(path="/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad/v267_%s.png" % LING)
    print("RESULTADO", "OK" if okA and okB and okC and ok1 and okZ and not erros else "FALHA", erros)
    b.close()
srv.terminate()
