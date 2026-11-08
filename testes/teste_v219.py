# v219 (08/11/2026, Valdo): os 20 pluviómetros na app; a chuva só se regista a 50 m de um pluviómetro, com a fotografia da marca da água.
# LING=en / sw para as outras línguas.
import json, subprocess, time, sys, datetime, os, math
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8849", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None}]
PLUV = [{"id": "farol", "nome": "Farol", "comunidade": "Farol", "zona": None, "lat": -10.686025, "lon": 40.587217, "ultima_leitura_origem": "2026-10-21"},
        {"id": "incularino-quilaua", "nome": "Incularino e Quilaua", "comunidade": "Palma", "zona": "Incularino e Quilaua", "lat": -10.764703, "lon": 40.455237, "ultima_leitura_origem": "2026-10-29"},
        {"id": "senga-vb", "nome": "Senga VB", "comunidade": "Senga", "zona": "VB", "lat": -10.848113, "lon": 40.45026, "ultima_leitura_origem": "2026-10-29"}]
rec = {}; erros = []; falhas = []
def verif(c, txt):
    print(("OK  " if c else "FALHA ") + txt)
    if not c: falhas.append(txt)
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u-sup", "aud": "authenticated", "role": "authenticated", "email": "raul@rega-coco.example.com"}})
    if "/auth/v1/logout" in u: return route.fulfill(status=204, body="")
    if "/rest/v1/perfis" in u: return ok({"id": "u-sup", "nome": "Raul", "papel": "supervisor", "activista_id": None})
    if "/storage/v1/object/chuva-fotos/" in u: rec.setdefault("fotos", []).append(u.split("chuva-fotos/")[1]); return ok({"Key": "x"})
    if "/rest/v1/chuva" in u: rec.setdefault("chuva", []).append(json.loads(r.post_data)); return route.fulfill(status=201, body="")
    if "/rest/v1/pluviometros" in u: return ok(PLUV)
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol", "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/" in u: return ok([])
    if "/rest/v1/registos_rega" in u: return ok([])
    if "/rest/v1/zonas" in u: return ok([{"comunidade": "Palma", "zona": "Incularino"}, {"comunidade": "Palma", "zona": "Quilaua"}])
    return ok({})
def pos(pg, ctx, lat, lon):             # o mapa recebe a posição nova (S.fix) e a chuva usa-a
    ctx.set_geolocation({"latitude": lat, "longitude": lon, "accuracy": 8})
    pg.wait_for_function(f"S.fix && Math.abs(S.fix.coords.latitude - ({lat})) < 1e-6", timeout=20000)
def desloca(lat, lon, m_norte):          # ponto m metros a norte
    return lat + m_norte / 111320.0, lon
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, geolocation={"latitude": -10.686025, "longitude": 40.587217}, permissions=["geolocation"])
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (print("DIALOGO:", d.message), d.accept()))
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.goto("http://localhost:8849/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "raul"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.wait_for_timeout(1200)
    verif(len(pg.evaluate("LS.get('pluvs')") or []) == 3, "1 pluviómetros guardados no telefone (3)")
    pg.evaluate("mudar('mapa')"); pg.wait_for_timeout(800)
    n = pg.evaluate("[...document.querySelectorAll('.ic-poco')].filter(e=>e.textContent.includes('🌧')).length")
    verif(n == 3, f"2 mapa: {n} pluviómetros 🌧")
    pg.evaluate("mudar('hoje')"); pg.wait_for_timeout(600); pos(pg, ctx, -10.686025, 40.587217)
    # junto do pluviómetro de Farol
    pg.evaluate("ecraChuva()")
    try: pg.wait_for_selector("#c-mm", timeout=25000)
    except Exception: print("DEBUG", pg.evaluate("document.querySelector('.folha, #folha, #fl')?.innerText || document.body.innerText.slice(0,800)")); raise
    t = pg.inner_text("#folha")
    verif("Farol" in t, "3 formulário mostra o pluviómetro Farol")
    verif(("marca da água" in t) if LING == "pt" else ("water mark" in t if LING == "en" else "alama ya maji" in t), "4 fotografia com a marca da água")
    pg.fill("#c-mm", "3.5"); pg.set_input_files("#c-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("#c-prev", state="visible")
    pg.screenshot(path=f"/home/claude/rega-test/v219_form_{LING}.png", full_page=True)
    pg.click("#folha .btn:not(.sec)"); pg.wait_for_timeout(2500)
    ch = rec.get("chuva", [])
    verif(any(c.get("pluviometro_id") == "farol" and c.get("comunidade") == "Farol" and c.get("zona") is None for c in ch), f"5 chuva enviada com o pluviómetro farol ({[ (c.get('pluviometro_id'), c.get('comunidade')) for c in ch]})")
    # a 120 m: recusa
    lat, lon = desloca(-10.686025, 40.587217, 120)
    pos(pg, ctx, lat, lon)
    pg.evaluate("ecraChuva()"); pg.wait_for_selector("#folha .msg.erro", timeout=25000)
    t = pg.inner_text("#folha .msg.erro")
    verif("120 m" in t and "Farol" in t and pg.locator("#c-mm").count() == 0, f"6 a 120 m recusa: {t!r}")
    verif(pg.locator("#folha button[onclick^='navegarPonto']").count() == 1, "7 botão para navegar até ao pluviómetro")
    if LING != "pt": verif(not any(w in t for w in ("Está a", "pluviómetro mais perto", "regista-se")), "8 texto da recusa traduzido")
    pg.screenshot(path=f"/home/claude/rega-test/v219_longe_{LING}.png", full_page=True)
    pg.evaluate("fecharFolha()")
    # Palma: zona do pluviómetro
    pos(pg, ctx, -10.764703, 40.455237)
    pg.evaluate("ecraChuva()"); pg.wait_for_selector("#c-mm", timeout=25000)
    pg.fill("#c-mm", "0"); pg.set_input_files("#c-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("#c-prev", state="visible")
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.click("#folha .btn:not(.sec)"); pg.wait_for_timeout(800)
    f = pg.evaluate("LS.get('filaChuva')") or []
    verif(any(c.get("pluviometro_id") == "incularino-quilaua" and c.get("comunidade") == "Palma" and c.get("zona") == "Incularino e Quilaua" for c in f), "9 Palma: comunidade Palma, zona do pluviómetro, na fila sem rede")
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))")
    # sem pluviómetros no telefone
    pg.evaluate("S.pluvs=[]"); pg.evaluate("ecraChuva()"); pg.wait_for_selector("#folha .msg.erro")
    verif(pg.locator("#c-mm").count() == 0, "10 sem pluviómetros no telefone: não abre o formulário")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
