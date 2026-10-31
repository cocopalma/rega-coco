import json, subprocess, time, sys, os
LING = os.environ.get("LING", "pt")
from playwright.sync_api import sync_playwright

APP = "http://localhost:8765/"
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/rega-coco"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
OUTRO = "33333333-3333-3333-3333-333333333333"
UID = "22222222-2222-2222-2222-222222222222"
areas = [
  {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-05-06"},
  {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 0, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-05-19"},
  {"id": "PR3-1", "pr": "PR3", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Tres", "instaladas": 50, "vivas": 48, "latitude": -10.6900, "longitude": 40.6400, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-04-01"},
  {"id": "PR4-1", "pr": "PR4", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Quatro", "instaladas": 40, "vivas": 40, "latitude": -10.6838, "longitude": 40.6343, "activista_id": OUTRO, "activista_proposto": None, "data_plantio": "2026-04-01"},
]
estado = [{"area_id": a["id"], "ultima_rega": "2026-10-01" if a["id"] == "PR3-1" else None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False} for a in areas]
recebidos = {"registos": [], "constr": [], "jornadas": [], "sugprox": []}
erros = []

def mock(route):
  try: _mock(route)
  except Exception as e: print("MOCK ERRO", e, route.request.url); route.fulfill(status=500, body="{}")
def _mock(route):
    r = route.request; u = r.url
    def ok(body, status=200): route.fulfill(status=status, content_type="application/json", body=json.dumps(body))
    corpo = lambda: (lambda x: x if isinstance(x, list) else [x])(json.loads(r.post_data))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600,
                   "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "majula@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Majula Muemede Bacar", "papel": "activista", "activista_id": ACT})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol"}, {"id": OUTRO, "nome": "Outro Activista", "comunidade_principal": "Farol"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/estado_ronda" in u: return ok(estado)
    if "/rest/v1/registos_rega" in u:
        if r.method == "POST": recebidos["registos"] += corpo(); return route.fulfill(status=201, body="")
        return ok([x for x in recebidos["registos"] if x["plantas_regadas"] > 0])   # o servidor devolve o que recebeu
    if "/rpc/registar_sugestoes_proximo" in u: recebidos["sugprox"] += json.loads(r.post_data)["p_lista"]; return ok(1)
    if "/rest/v1/constrangimentos" in u: recebidos["constr"] += corpo(); return route.fulfill(status=201, body="")
    if "/rest/v1/jornadas" in u: recebidos["jornadas"] += corpo(); return route.fulfill(status=201, body="")
    return ok({})

def fechar_sugestao(pg):
    if pg.is_visible("button:has-text('Escolher outro campo')"): pg.click("button:has-text('Escolher outro campo')")
    elif pg.is_visible("#folha.on button:has-text('Fechar')"): pg.click("#folha.on button:has-text('Fechar')")

def regar(pg, area, plantas=None, agua=None, hora_agua=None):
    pg.click("nav button[data-e=lista]"); pg.click(f".item[data-id='{area}']"); pg.wait_for_selector("#folha.on")
    pg.click("text=Cheguei — marcar entrada"); pg.wait_for_selector("text=Entrada marcada", timeout=15000); fotos(pg)
    if agua == "agora": pg.click("text=Chegou a água (tuk-tuk) agora"); pg.wait_for_selector("text=Água (tuk-tuk) no campo")
    pg.click("text=Terminei — marcar saída")
    if plantas is None: plantas = pg.evaluate("(id) => plantasN(S.areas.find((a) => a.id === id))", area)   # o campo vem vazio desde a v85
    pg.fill("#s-plantas", str(plantas))
    if hora_agua: pg.fill("#s-agua", hora_agua)
    pg.click("text=Marcar saída e guardar"); pg.wait_for_selector("text=Rega guardada", timeout=15000)

def fotos(pg):   # fotografias obrigatórias da rega (15/10/2026): no teste guardam-se directamente
    pg.evaluate("(async()=>{for (const t of ['entrada','rega','saida']) await guardarFotoRega(t, new Blob(['x'],{type:'image/jpeg'})); abrirFicha(LS.get('emCurso').area_id)})()"); pg.wait_for_timeout(300)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"], viewport={"width": 390, "height": 800})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page()
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.on("pageerror", lambda e: erros.append(str(e)))
    dialogos = []; pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.goto(APP); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "majula"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar")
    pg.wait_for_selector("#j-pessoas", timeout=10000); print("1 login → pede pessoas do dia: OK")
    pg.fill("#j-pessoas", "4"); pg.click("#folha.on .btn >> nth=0"); pg.wait_for_timeout(1200)
    print("2 jornada enviada:", recebidos["jornadas"][0]["pessoas"] if recebidos["jornadas"] else "NÃO", "| mapa:", pg.inner_text("#ronda-info"))

    T = {"pt": ("Próximo campo sugerido", "Escolher outro campo", "Abrir a ficha", "Cheguei — marcar entrada", "Fica no Mapa e no Hoje"),
         "en": ("Suggested next field", "Choose another field", "Open the record", "record entry", "stays on the Map"),
         "sw": ("Shamba linalopendekezwa kufuata", "Chagua shamba jingine", None, "andika kuwasili", "Litabaki kwenye Ramani")}[LING]
    def regar2(area, plantas):
        pg.evaluate("(id) => abrirFicha(id)", area); pg.wait_for_selector("#folha.on"); pg.wait_for_timeout(500)
        if LING != "pt" and not pg.is_visible(f"#folha.on button:has-text('{T[3]}')"): print("  FOLHA:", pg.inner_text("#folha-c")[:300])
        pg.evaluate("marcarEntrada(S.fichaAberta || LS.get('ultimaFicha'))") if False else None
        pg.click(f"#folha.on button:has-text('{T[3]}')"); pg.wait_for_timeout(2500); fotos(pg)
        pg.evaluate("ecraSaida()"); pg.wait_for_selector("#s-plantas"); pg.fill("#s-plantas", str(plantas))
        res = pg.evaluate("marcarSaida().then(()=>'ok').catch(e=>'ERR '+e.message)")
        if res != 'ok': print("  marcarSaida:", res)
        if pg.evaluate("!!LS.get('emCurso')"): pg.wait_for_timeout(1500); pg.evaluate("ecraSaida()"); pg.fill("#s-plantas", str(plantas)); pg.evaluate("marcarSaida()")   # GPS do navegador de teste às vezes falha
        print("  msgs:", pg.evaluate("[...document.querySelectorAll('body > .msg')].map(e=>e.innerText).join(' | ')"), "| emCurso:", pg.evaluate("!!LS.get('emCurso')"))
        try: pg.wait_for_function("!LS.get('emCurso')", timeout=12000)
        except Exception: print("  saída não gravou:", pg.inner_text("#folha-c")[:150], pg.evaluate("[...document.querySelectorAll('.toast,#toast,.aviso')].map(e=>e.innerText).join(' | ')"), dialogos)
        pg.wait_for_timeout(800)
    regar2("PR1-1", 70)
    sug = pg.evaluate("LS.get('sugestao')?.area_id"); print("1 sugerido:", sug)
    if pg.is_visible(f"#folha.on button:has-text('{T[1]}')"): pg.click(f"#folha.on button:has-text('{T[1]}')")
    outro = "PR3-1" if sug != "PR3-1" else "PR2-1"
    ctx.set_geolocation({"latitude": -10.6900, "longitude": 40.6400} if outro == "PR3-1" else {"latitude": -10.6842, "longitude": 40.6332}); pg.wait_for_timeout(1500)
    pg.evaluate("(id) => abrirFicha(id)", outro); pg.wait_for_selector("#folha.on"); pg.wait_for_timeout(400)
    pg.click(f"#folha.on button:has-text('{T[3]}')"); pg.wait_for_timeout(800)
    print("2 ecrã:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:260])
    pg.click("#sg-ok"); pg.wait_for_timeout(200); print("3 sem motivo:", dialogos[-1:] )
    pg.click("#sg-mot .chip >> nth=4"); pg.click("#sg-ok"); pg.wait_for_timeout(200); print("4 outro sem texto:", dialogos[-1:])
    pg.click("#sg-mot .chip >> nth=3"); pg.click("#sg-ok"); pg.wait_for_timeout(3000)
    print("5 em curso:", pg.evaluate("JSON.stringify((({area_id, area_sugerida_id, seguiu_sugestao, motivo_sugestao}) => ({area_id, area_sugerida_id, seguiu_sugestao, motivo_sugestao}))(LS.get('emCurso') || {}))"))
    fotos(pg); pg.evaluate("ecraSaida()"); pg.wait_for_selector("#s-plantas"); pg.fill("#s-plantas", "48"); pg.evaluate("marcarSaida()")
    try: pg.wait_for_function("!LS.get('emCurso')", timeout=15000)
    except Exception: pass
    pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(3000)
    print("6 servidor:", [(x["area_id"], x.get("seguiu_sugestao"), x.get("motivo_sugestao")) for x in recebidos["registos"]])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
