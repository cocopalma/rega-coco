# v231 (10/11/2026, Guidion: "não consigo fechar o dia"): «Fechar o dia» mostra «A fechar o dia…» e, sem resposta em 20 s
# (aqui 2 s), diz que não há ligação ao servidor; depois, com resposta, fecha. LING=en / sw.
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8863", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1 = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
hoje = datetime.date.today().isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None}]
estado = {"fechado": None, "pendurar": True}; rec = []
def md():
    return {"data": hoje, "hora_chegada": "06:30", "fechado_em": estado["fechado"],
      "equipas": [{"id": A1, "nome": "Activista Um", "comunidade": "Farol", "regas": 2, "plantas": 130, "sem_rega": None}],
      "alertas": [], "monitoria_hoje": 0, "monitoria_falhas_ontem": 0, "sem_equipa": 0, "por_aprovar": []}
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Tecnico Um", "papel": "tecnico", "activista_id": None, "ve_tudo": False})
    if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Farol", "tecnico": "Tecnico Um", "supervisor": "Sup", "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([A1])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/meu_dia" in u: return ok(md())
    if "/rpc/fechar_dia" in u:
        rec.append("fechar")
        if estado["pendurar"]: return  # sem resposta (rede que não chega ao servidor)
        estado["fechado"] = datetime.datetime.utcnow().isoformat() + "Z"; return ok(estado["fechado"])
    return ok([])
erros = []
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8863/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "tec"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1800)
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("#md-fechar", timeout=10000)
    LING = os.environ.get("LING", "pt"); falhas = []
    def verif(c, txt):
        print(("OK  " if c else "FALHA ") + txt)
        if not c: falhas.append(txt)
    pg.click("#md-fechar"); pg.wait_for_timeout(500)
    bt = pg.inner_text("#md-fechar"); dis = pg.eval_on_selector("#md-fechar", "e => e.disabled")
    verif(dis and "⏳" in bt, f"1 botão fica desactivado a dizer que está a fechar ({bt})")
    if LING == "pt": verif("A fechar o dia" in bt, "1b texto em português")
    else: verif("A fechar o dia" not in bt, "1b traduzido")
    pg.wait_for_timeout(21000)
    av = pg.inner_text("body")
    verif(("Sem resposta do servidor" in av) if LING == "pt" else ("Sem resposta do servidor" not in av and ("No response" in av or "Hakuna jibu" in av)), "2 aviso de falta de ligação ao fim de 20 s")
    verif(not pg.eval_on_selector("#md-fechar", "e => e.disabled") and "⏳" not in pg.inner_text("#md-fechar"), "3 botão volta a ficar activo")
    pg.screenshot(path=f"/home/claude/rega-test/v231_{LING}.png")
    estado["pendurar"] = False
    pg.click("#md-fechar"); pg.wait_for_timeout(2500)
    verif(pg.locator("#md-fechar").count() == 0 and estado["fechado"], "4 com resposta o dia fecha e o botão sai")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
