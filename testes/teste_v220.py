# v220 (09/11/2026, Valdo): técnico e supervisor abrem a correcção da coordenada e da área (mesmo com limite) nos campos da sua lista, com motivo.
# LING=en / sw para as outras línguas.
import json, subprocess, time, sys, datetime, os, math
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8850", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
POL = [[40.6339, -10.6834], [40.6341, -10.6834], [40.6341, -10.6836], [40.6339, -10.6836], [40.6339, -10.6834]]
OUTRO = "22222222-2222-2222-2222-222222222222"
PAPEL = os.environ.get("PAPEL", "tecnico")
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None, "poligono": POL, "limites_abertos": False},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 70, "vivas": 70, "latitude": -10.6845, "longitude": 40.6350, "activista_id": OUTRO, "activista_proposto": None, "poligono": POL, "limites_abertos": False}]
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
    if "/rest/v1/perfis" in u: return ok({"id": "u-sup", "nome": "Gelson", "papel": PAPEL, "activista_id": ACT if PAPEL == "activista" else None})
    if "/storage/v1/object/chuva-fotos/" in u: rec.setdefault("fotos", []).append(u.split("chuva-fotos/")[1]); return ok({"Key": "x"})
    if "/rest/v1/chuva" in u: rec.setdefault("chuva", []).append(json.loads(r.post_data)); return route.fulfill(status=201, body="")
    if "/rest/v1/pluviometros" in u: return ok(PLUV)
    if "/rpc/abrir_limites" in u:
        b = json.loads(r.post_data); rec.setdefault("abrir", []).append(b)
        for x in areas:
            if x["id"] == b["p_area"]: x["limites_abertos"] = b["p_abrir"]
        return ok(None)
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Desteria Raimundo", "comunidade_principal": "Farol", "equipa_tamanho": 5, "tecnico": "Gelson", "supervisor": "Nuro"}, {"id": OUTRO, "nome": "Outro Activista", "comunidade_principal": "Farol", "equipa_tamanho": 5, "tecnico": "Outro", "supervisor": "Outro"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/minhas_comunidades" in u: return ok([])
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
    pg.goto("http://localhost:8850/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "raul"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.wait_for_timeout(1200)
    pg.evaluate("window.__TAR_ABERTAS = true")
    def ficha(id):
        pg.evaluate(f"abrirFicha('{id}')"); pg.wait_for_timeout(700); return pg.inner_text("#folha")
    if PAPEL in ("tecnico", "supervisor"):
        t = ficha("PR1-1")
        verif(pg.locator("#folha button[onclick^='ecraAbrirLimites']").count() == 1, "1 campo da lista com limite: botão para abrir a correcção")
        verif(pg.locator("#folha button[onclick^=\"ecraMedir\"]").count() == 0, "2 sem abrir: não mede de novo")
        pg.click("#folha button[onclick^='ecraAbrirLimites']"); pg.wait_for_selector("#al-mot")
        pg.click("#al-ok"); pg.wait_for_timeout(300)
        verif(pg.locator("#al-msg .msg.erro").count() == 1, "3 sem motivo: não abre")
        pg.screenshot(path=f"/home/claude/rega-test/v220_abrir_{LING}.png", full_page=True)
        pg.fill("#al-mot", "O ponto está fora do campo"); pg.click("#al-ok"); pg.wait_for_timeout(2500)
        a = pg.evaluate("S.areas.find(x=>x.id==='PR1-1').limites_abertos")
        verif(a is True, "4 limites abertos no telefone")
        ab = rec.get("abrir", [])
        verif(any(x.get("p_area") == "PR1-1" and x.get("p_abrir") is True and x.get("p_motivo") == "O ponto está fora do campo" for x in ab), f"5 enviado ao servidor com o motivo ({ab})")
        verif(pg.locator("#folha button[onclick^=\"ecraMedir\"]").count() >= 1, "6 depois de abrir: «Medir a área de novo»")
        verif(pg.locator("#folha button[onclick*='mudarLimites'][onclick*='false']").count() == 1, "7 botão para fechar a correcção")
        pg.screenshot(path=f"/home/claude/rega-test/v220_aberto_{LING}.png", full_page=True)
        if LING != "pt":
            tt = pg.inner_text("#folha"); verif("Abrir a correcção" not in tt and "Fecha sozinho" not in tt, "8 textos traduzidos")
        t = ficha("PR2-1")
        verif(pg.locator("#folha button[onclick^='ecraAbrirLimites']").count() == 0, "9 campo de outra equipa: sem o botão")
    else:
        t = ficha("PR1-1")
        verif(pg.locator("#folha button[onclick^=\"ecraMedir\"]").count() == 0 and pg.locator("#folha button[onclick^='ecraAbrirLimites']").count() == 0, "A1 activista, limite fechado: não mede nem abre")
        pg.evaluate("S.areas.find(x=>x.id==='PR1-1').limites_abertos = true")
        t = ficha("PR1-1")
        verif(pg.locator("#folha button[onclick^=\"ecraMedir\"]").count() == 1, "A2 activista, limite aberto: «Medir a área de novo»")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
