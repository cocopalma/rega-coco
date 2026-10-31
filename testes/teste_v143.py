# v143 (29/10/2026, Valdo): clique no ponto do coqueiro abre a ficha (W=largura, TOUCH=1, DPR=2, DX=desvio em px).
# Coqueiros v111 (24/10/2026, áudios do Dalmar): círculo/alerta a 2,5 m, estado "Retirado", até 3 fotografias, tratamento/cachos/cocos.
# PAPEL=tecnico com MARCA=1 (perfis.marca_coqueiros, p. ex. Bafana); LING=en / sw.
import json, subprocess, time, sys, math, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; PAPEL = os.environ.get("PAPEL", "gestor"); LING = os.environ.get("LING", "pt"); MARCA = os.environ.get("MARCA", "0") == "1"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8818", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
lat0, lon0 = -10.7000, 40.4700; dy, dx = 1 / 110540, 1 / (111320 * math.cos(math.radians(10.7)))
CQ = "aaaaaaaa-0000-0000-0000-000000000001"
servidor = [{"id": CQ, "n": 1, "lat": lat0, "lon": lon0, "precisao_m": 4, "estado": "viva", "local": "ACE", "observacao": None, "foto_path": "u/a.jpg", "fotos_extra": [], "tratamento": True, "cachos": None, "cocos": None, "marcado_em": "2026-10-24T05:00:00Z", "marcado_por_nome": "Dalmar Santos", "meu": False}]
rec = {"rpc": [], "fotos": []}; erros = []; dial = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "d@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Pessoa", "papel": PAPEL, "activista_id": None, "marca_coqueiros": MARCA})
    if "/rest/v1/areas" in u: return ok([])
    if "/storage/v1/object/coqueiros-fotos" in u: rec["fotos"].append(u.split("coqueiros-fotos/")[-1]); return ok({"Key": "x"})
    if "/rpc/coqueiros_lista" in u: return ok(servidor)
    if "/rpc/gravar_coqueiro2" in u: rec["rpc"].append(json.loads(r.post_data)); return ok(2)
    return ok([])
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": int(os.environ.get("W","1280")), "height": 800}, has_touch=os.environ.get("TOUCH")=="1", device_scale_factor=float(os.environ.get("DPR","1")), permissions=["geolocation"], geolocation={"latitude": lat0 + 300 * dy, "longitude": lon0, "accuracy": 3}, accept_downloads=True)
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    pg.add_init_script("localStorage.setItem('rega.lingua', %r); window.__vib = 0; navigator.vibrate = () => { window.__vib++; return true; };" % LING)
    pg.goto("http://localhost:8818/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "x"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    vis = pg.is_visible("#b-coq"); print("1 botão:", vis)
    if not vis: print("ERROS JS:", erros or "nenhum"); b.close(); srv.terminate(); sys.exit()
    pg.click("#b-coq"); pg.wait_for_timeout(1500)
    pg.evaluate("mapa.setView([%f,%f], 18)" % (lat0, lon0)); pg.wait_for_timeout(1200)
    pt = pg.evaluate("(() => { const p = mapa.latLngToContainerPoint([%f,%f]); const r = document.getElementById('mapa').getBoundingClientRect(); return [p.x + r.left, p.y + r.top]; })()" % (lat0, lon0))
    el = pg.evaluate("(([x,y]) => { const e = document.elementFromPoint(x,y); return e.tagName + '#' + e.id + '.' + e.className; })(%s)" % json.dumps(pt))
    print("ponto no ecrã:", pt, "| elemento por cima:", el)
    if os.environ.get("TOUCH")=="1": pg.touchscreen.tap(pt[0], pt[1])
    else: pg.mouse.click(pt[0] + float(os.environ.get("DX","0")), pt[1])
    pg.wait_for_timeout(1000)
    print("ficha aberta:", pg.is_visible("#folha"), "|", pg.inner_text("#folha-c")[:80].replace(chr(10)," ") if pg.is_visible("#folha") else "")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
