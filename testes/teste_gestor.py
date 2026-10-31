import json, subprocess, time, sys
from playwright.sync_api import sync_playwright

APP = "http://localhost:8765/"
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/rega-coco"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
UID = "22222222-2222-2222-2222-222222222222"
areas = [
  {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-05-06"},
  {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 0, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-05-19"},
  {"id": "PR3-1", "pr": "PR3", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Tres", "instaladas": 50, "vivas": 48, "latitude": -10.6900, "longitude": 40.6400, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-04-01"},
]
hoje = time.strftime("%Y-%m-%d")
estado = [{"area_id": "PR3-1", "ultima_rega": hoje, "regas_app": 0}]  # PR3 regada hoje -> alerta
recebidos = {"registos": [], "constr": []}
erros = []

def mock(route):
  try:
    _mock(route)
  except Exception as e:
    print("MOCK ERRO", e, route.request.url, route.request.post_data); route.fulfill(status=500, body="{}")
def _mock(route):
    r = route.request; u = r.url
    def ok(body, status=200): route.fulfill(status=status, content_type="application/json", body=json.dumps(body))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600,
                   "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "majula@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Majula Muemede Bacar", "papel": "gestor", "activista_id": None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol", "tecnico": "", "supervisor": ""}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/estado_ronda" in u: return ok(estado)
    if "/rest/v1/registos_rega" in u:
        if r.method == "POST": recebidos["registos"] += json.loads(r.post_data) if r.post_data.startswith("[") else [json.loads(r.post_data)]; return route.fulfill(status=201, body="")
        return ok([])
    if "/rest/v1/constrangimentos" in u:
        recebidos["constr"] += json.loads(r.post_data); return route.fulfill(status=201, body="")
    if "/functions/v1/gestor-activistas" in u:
        b=json.loads(r.post_data); print("FN", b)
        if b["accao"]=="listar": return ok({"activistas":[{"id":ACT,"nome":"Majula Muemede Bacar","comunidade_principal":"Farol","activo":True,"utilizador":None,"tem_login":False}]})
        return ok({"ok":True,"utilizador":b.get("utilizador"),"activista":"Majula Muemede Bacar"})
    return ok({})

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"], viewport={"width": 390, "height": 800})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept("654321"))
    pg.goto(APP); pg.fill("#l-user","etevaldo.cheveia@jfs.co.mz"); pg.fill("#l-pin","x"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    print("G1", pg.inner_text("#h-nome"), "| gestão visível:", pg.is_visible("#nav-gestao"))
    pg.click("#nav-gestao"); pg.wait_for_selector("#g-user"); print("G2 utilizador sugerido:", pg.input_value("#g-user"))
    pg.fill("#g-pin","123456"); pg.click("#g-criar"); pg.wait_for_timeout(1500); print("G3", pg.inner_text("#gestao")[:120].replace(chr(10)," | "))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
