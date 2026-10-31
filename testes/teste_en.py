import json, subprocess, time, sys
from playwright.sync_api import sync_playwright

APP = "http://localhost:8775/"
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8775", "--directory", "/home/claude/rega-coco"],
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
recebidos = {"registos": [], "constr": [], "jornadas": []}
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
    pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(APP); pg.wait_for_selector("#l-entrar", state="visible"); print("PT inicial:", pg.inner_text("#l-entrar"), pg.inner_text("#lc-lingua"))
    pg.click("#lc-lingua"); pg.click("#menu-lingua [data-l='" + pg.evaluate("(()=>{const L=['pt','en','sw'];let c='pt';try{c=localStorage.getItem('rega.lingua')||'pt'}catch(e){};return L[(L.indexOf(c)+1)%3]})()") + "']"); pg.wait_for_selector("#l-entrar", state="visible"); pg.wait_for_timeout(500)
    print("login:", pg.inner_text("#l-campo")[:200].replace("\n"," | "))
    pg.fill("#l-user", "majula"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar")
    pg.wait_for_selector("#j-pessoas", timeout=10000); print("jornada:", pg.inner_text("#folha-c")[:200].replace("\n"," | "))
    pg.fill("#j-pessoas", "4"); pg.click("#folha.on .btn"); pg.wait_for_timeout(1200)
    print("cabeçalho:", pg.inner_text("header").replace("\n"," | "), "| nav:", pg.inner_text("nav").replace("\n"," | "))
    print("mapa:", pg.inner_text("#ronda-info"), "|", pg.inner_text(".legenda").replace("\n"," | "))
    pg.click("nav button[data-e=lista]"); pg.wait_for_timeout(500); print("lista:", pg.inner_text("#lista")[:300].replace("\n"," | "))
    pg.click(".item[data-id='PR1-1']"); pg.wait_for_selector("#folha.on"); print("ficha:", pg.inner_text("#folha-c")[:400].replace("\n"," | "))
    pg.screenshot(path="/home/claude/rega-test/en_ficha.png")
    pg.click("#folha .btn"); pg.wait_for_timeout(3000); print("entrada:", pg.inner_text("#folha-c")[:300].replace("\n"," | "))
    pg.click("#folha-x"); pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(800); print("hoje:", pg.inner_text("#hoje")[:400].replace("\n"," | "))
    pg.screenshot(path="/home/claude/rega-test/en_hoje.png")
    pg.click("#h-lingua"); pg.click("#menu-lingua [data-l='pt']"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    print("depois de PT:", pg.inner_text("header").replace("\n"," | "), "| lingua:", pg.evaluate("localStorage.getItem('rega.lingua')"), "| nav:", pg.inner_text("nav").replace("\n"," | "))
    print("ERROS JS:", erros or "nenhum")
    b.close()
srv.terminate()
