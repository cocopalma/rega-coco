# v165 (31/10/2026, Valdo): confirmação dos motivos, equipa que começou o dia, comentários obrigatórios, repetir até. LING=en / sw.
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8865", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1 = "11111111-1111-1111-1111-111111111111"; A2 = "33333333-3333-3333-3333-333333333333"; A3 = "44444444-4444-4444-4444-444444444444"; A4 = "55555555-5555-5555-5555-555555555555"; UID = "22222222-2222-2222-2222-222222222222"
hoje = datetime.date.today().isoformat(); ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": A2, "activista_proposto": None, "poligono_proposto": [[40.6330,-10.6840],[40.6334,-10.6840],[40.6334,-10.6844],[40.6330,-10.6844],[40.6330,-10.6840]], "area_m2_proposta": 1950, "proposta_em": hoje + "T06:20:00Z"}]
estado = {"fechado": None, "conf": False, "dsr4": False}; rec = []
def md():
    m3 = {"id": "d3", "motivo": "equipa", "descricao": None, "todo_dia": True, "data": hoje, "ate": None, "quem": "Activista Tres", "papel_quem": "activista", "criado_em": hoje + "T07:10:00Z",
          "por_confirmar": not estado["conf"], "confirmado_nome": "Tecnico Um" if estado["conf"] else None}
    return {"data": hoje, "hora_chegada": "06:00", "fechado_em": estado["fechado"],
      "equipas": [{"id": A1, "nome": "Activista Um", "regas": 2, "plantas": 130, "sem_rega": None, "chegada": hoje + "T05:45:00Z", "comecou": hoje + "T05:30:00Z", "motivos": []},
                  {"id": A2, "nome": "Activista Dois", "regas": 0, "plantas": 0, "sem_rega": None, "comecou": hoje + "T04:39:00Z", "motivos": []},
                  {"id": A3, "nome": "Activista Tres", "regas": 0, "plantas": 0, "sem_rega": "equipa", "comecou": None, "motivos": [m3]},
                  {"id": A4, "nome": "Activista Quatro", "regas": 0, "plantas": 0, "sem_rega": "material" if estado["dsr4"] else None, "comecou": None,
                   "motivos": [{"id": "d4", "motivo": "material", "descricao": "regadores", "data": hoje, "ate": None, "quem": "Tecnico Um", "papel_quem": "tecnico", "por_confirmar": False}] if estado["dsr4"] else []}],
      "alertas": [], "monitoria_hoje": 0, "monitoria_falhas_ontem": 0, "sem_equipa": 0, "por_aprovar": [], "por_terminar": []}
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Tecnico Um", "papel": "tecnico", "activista_id": None, "ve_tudo": False})
    if "/rest/v1/activistas" in u: return ok([{"id": x, "nome": n, "comunidade_principal": "Farol", "tecnico": "Tecnico Um", "supervisor": "Sup", "activo": True} for x, n in ((A1, "Activista Um"), (A2, "Activista Dois"), (A3, "Activista Tres"), (A4, "Activista Quatro"))])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([A1, A2, A3, A4])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/meu_dia" in u: return ok(md())
    if "/rpc/monitoria_lista" in u: return ok([{"amostra_id": "m1", "data_rega": ontem, "area_id": "PR1-1", "activista_id": A1, "feita": False}, {"amostra_id": "m2", "data_rega": hoje, "area_id": "PR2-1", "activista_id": A2, "feita": False}])
    if "/rpc/fechar_dia" in u: estado["fechado"] = datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat() + "Z"; rec.append("fechar"); return ok(estado["fechado"])
    if "/rpc/confirmar_dia_sem_rega" in u: estado["conf"] = True; rec.append(("conf", json.loads(r.post_data))); return ok({"estado": "confirmado"})
    if "/rpc/gravar_dia_sem_rega4" in u: estado["dsr4"] = True; d = json.loads(r.post_data); rec.append(("dsr4", d["p_motivo"], d["p_descricao"], d["p_ate"])); return ok({"substituido": False})
    if "/rpc/estado_ronda" in u: return ok([])
    if "/rpc/" in u: return ok([])
    if "/rest/v1/registos_rega" in u: return ok([])
    return ok([])
erros = []; dial = []
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    pg.goto("http://localhost:8865/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "tec"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1800)
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(500)
    pg.screenshot(path="/home/claude/rega-test/v165_meu_dia.png", full_page=True)
    print("1 equipas:", pg.inner_text("#meu-dia").split("2.")[0].replace("\n", " | ")[:900])
    print("1b fechar:", pg.locator("#meu-dia button.btn").count(), "|", pg.inner_text("#meu-dia").split("7.")[1].replace("\n", " | ")[-260:])
    pg.click("#meu-dia button.chip[onclick*=ecraConfirmarDsr]"); pg.wait_for_selector("#cd-ok")
    print("2 ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:400])
    pg.click("#cd-ok"); pg.wait_for_timeout(200); print("2a sem nota:", dial[-1:])
    pg.fill("#cd-nota", "Foi ao hospital com o filho"); pg.click("#cd-ok"); pg.wait_for_timeout(3500)
    print("2b confirmou:", [x for x in rec if x[0] == "conf"], "| linha:", [l for l in pg.inner_text("#meu-dia").split("\n") if "confirm" in l.lower() or "thibitish" in l.lower()][:3])
    pg.click("#meu-dia .lin button.chip"); pg.wait_for_selector("#dsr-act", state="attached"); print("3 equipa:", pg.evaluate("$('#dsr-act').value") == A4)
    pg.check("input[value=material]"); pg.wait_for_timeout(100); print("3a rótulo:", pg.inner_text("#dsr-obs-l"))
    pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(200); print("3b sem obs:", dial[-1:])
    pg.check("input[value=equipa]"); print("3c rótulo equipa (técnico):", pg.inner_text("#dsr-obs-l")); pg.check("input[value=tuk_tuk]"); print("3d rótulo tuk-tuk:", pg.inner_text("#dsr-obs-l"))
    print("3e motivo novo:", pg.locator("input[value=regou_sem_registo]").count())
    pg.check("input[value=material]"); pg.fill("#dsr-obs", "regadores")
    ate = (datetime.date.today() + datetime.timedelta(days=3)).isoformat(); pg.fill("#dsr-ate", ate)
    pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(2500); pg.evaluate("carregarMeuDia().then(actHoje)"); pg.wait_for_timeout(1500)
    print("3f enviado:", [x for x in rec if x[0] == "dsr4"], "esperado até", ate, "| botão fechar:", pg.locator("#meu-dia button.btn").count())
    pg.click("#meu-dia button.btn"); pg.wait_for_timeout(1500); print("4 fechou:", "fechar" in rec)
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
