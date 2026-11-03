# v200 (03/11/2026, Valdo: "Corrigir a app"; sugestões do Selemane de 03/11): campo sem plantas vivas (mudas mortas ou secas).
# Ficha › «🥀 Não há plantas vivas para regar» → 2.ª fotografia = plantas mortas (sem água) → saída com 0 plantas,
# «Mudas secas ou mortas» e o número de mortas obrigatórios → campo fechado (constrangimento com plantas). LING=en / sw.
import json, subprocess, time, sys, os, datetime
LING = os.environ.get("LING", "pt")
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; D = "/home/claude/rega-test/v198"
if not os.path.exists(f"{D}/sem_exif.jpg"):
    from PIL import Image
    os.makedirs(D, exist_ok=True); Image.new("RGB", (1600, 1200), (60, 140, 60)).save(f"{D}/sem_exif.jpg")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8899", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 48, "vivas": 48, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None}]
rec = {"registos": [], "constr": []}
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    corpo = lambda: (lambda x: x if isinstance(x, list) else [x])(json.loads(r.post_data))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Activista Um", "papel": "activista", "activista_id": ACT})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Um", "comunidade_principal": "Farol", "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rest/v1/registos_rega" in u:
        if r.method == "POST": rec["registos"] += corpo(); return route.fulfill(status=201, body="")
        return ok([])
    if "/rest/v1/constrangimentos" in u: rec["constr"] += corpo(); return route.fulfill(status=201, body="")
    if "/storage/v1/" in u: return ok({"Key": "x"})
    return ok([])
erros = []
T = {"pt": ("Cheguei — marcar entrada", "Não há plantas vivas", "Terminei — marcar saída", "Mudas secas ou mortas"),
     "en": ("record entry", "no live plants", "record exit", "Dry or dead seedlings"),
     "sw": ("andika kuwasili", "Hakuna mimea hai", "andika kutoka", "Miche iliyokauka au kufa")}[LING]
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    dialogos = []; pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.goto("http://localhost:8899/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "act"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar"); pg.wait_for_timeout(2500)
    if pg.is_visible("#j-pessoas"): pg.fill("#j-pessoas", "3"); pg.click("#folha.on .btn >> nth=0"); pg.wait_for_timeout(800)
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_selector("#folha.on"); pg.wait_for_timeout(300)
    pg.click(f"#folha.on button:has-text('{T[0]}')"); pg.wait_for_timeout(3000)
    pg.set_input_files("#fr-foto", f"{D}/sem_exif.jpg"); pg.wait_for_timeout(1500)        # fotografia da entrada
    print("1 ficha:", pg.inner_text("#folha-c").replace("\n", " | ")[:330])
    pg.click(f"#folha.on button:has-text('{T[1]}')"); pg.wait_for_timeout(500)
    print("2 sem vivas:", pg.inner_text("#folha-c").replace("\n", " | ")[:360], "| diálogo:", dialogos[-1][:60] if dialogos else None)
    pg.evaluate("ecraFotoRega('rega')"); pg.wait_for_selector("#fr-foto", state="attached")
    print("3 ecrã da 2.ª fotografia:", pg.inner_text("#folha-c").replace("\n", " | ")[:160])
    pg.set_input_files("#fr-foto", f"{D}/sem_exif.jpg"); pg.wait_for_timeout(1500)
    pg.click(f"#folha.on button:has-text('{T[2]}')"); pg.wait_for_selector("#s-plantas")
    print("4 saída:", pg.inner_text("#folha-c").replace("\n", " | ")[:260], "| plantas:", pg.input_value("#s-plantas"), "| água:", pg.is_visible("#s-agua"),
          "| mudas secas marcada:", pg.evaluate("!!document.querySelector('#s-chips .chip.on[data-k=mudas_secas]')"))
    pg.set_input_files("#s-foto", f"{D}/sem_exif.jpg"); pg.wait_for_timeout(1500)
    n0 = len(dialogos); pg.evaluate("marcarSaida()"); pg.wait_for_timeout(500); print("5 sem número de mortas:", dialogos[n0:])
    pg.fill("#s-mortas", "48"); pg.evaluate("marcarSaida()")
    pg.wait_for_function("!LS.get('emCurso')", timeout=15000); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    r = rec["registos"][-1] if rec["registos"] else {}
    print("6 enviado: plantas", r.get("plantas_regadas"), "| fechado", r.get("campo_fechado"), "| água", r.get("agua_em"), "| foto rega", bool(r.get("foto_rega")),
          "| constr", [(c["tipo"], c["plantas"]) for c in rec["constr"]])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
