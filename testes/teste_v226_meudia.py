# v226 (09/11/2026, Valdo: "Sim"): «O meu dia» › meta muito abaixo sem explicação: o técnico escreve o motivo. LING=en / sw.
import json, subprocess, time, sys, os, datetime
SEC = lambda pg, k: (pg.inner_text(f"#meu-dia details[data-k={k}]") if pg.locator(f"#meu-dia details[data-k={k}]").count() else "(sem linha "+k+")")
NB = lambda pg, k: (pg.inner_text(f"#meu-dia details[data-k={k}] .nb") if pg.locator(f"#meu-dia details[data-k={k}] .nb").count() else "(sem linha)")
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8864", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1 = "11111111-1111-1111-1111-111111111111"; A2 = "33333333-3333-3333-3333-333333333333"; UID = "22222222-2222-2222-2222-222222222222"
hoje = datetime.date.today().isoformat(); ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": A2, "activista_proposto": None, "poligono_proposto": [[40.6330,-10.6840],[40.6334,-10.6840],[40.6334,-10.6844],[40.6330,-10.6844],[40.6330,-10.6840]], "area_m2_proposta": 1950, "proposta_em": hoje + "T06:20:00Z"}]
estado = {"fechado": None, "dsr": False, "conf": False}; rec = []
def md():
    return {"data": hoje, "hora_chegada": "06:00", "fechado_em": estado["fechado"],
      "equipas": [{"id": A1, "nome": "Activista Um", "comunidade": "Farol", "regas": 2, "plantas": 130, "sem_rega": None, "chegada": hoje + "T05:45:00Z"},
                  {"id": A2, "nome": "Activista Dois", "comunidade": "Farol", "regas": 0, "plantas": 0, "sem_rega": "avaria_camiao" if estado["dsr"] else None}],
      "alertas": [] if estado["conf"] else [{"registo_id": "r9", "data": hoje, "area_id": "PR1-1", "produtor": "Produtor Um", "equipa": "Activista Um", "plantas": 300, "base": 70, "ritmo": 270, "mediana": 40, "tipo": "mais_que_base"}],
      "monitoria_hoje": 1, "monitoria_falhas_ontem": 2, "sem_equipa": 3,
      "por_aprovar": [{"area_id": "PR2-1", "produtor": "Produtor Dois", "comunidade": "Farol", "equipa": "Activista Dois", "area_m2": 1950, "proposta_em": hoje + "T06:20:00Z", "quem": "Activista Dois"}]}
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Tecnico Um", "papel": "tecnico", "activista_id": None, "ve_tudo": False})
    if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Farol", "tecnico": "Tecnico Um", "supervisor": "Sup", "activo": True}, {"id": A2, "nome": "Activista Dois", "comunidade_principal": "Farol", "tecnico": "Tecnico Um", "supervisor": "Sup", "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([A1, A2])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/meu_dia" in u: return ok(md())
    if "/rpc/motivos_anteriores" in u: return ok([] if estado.get("conf_ant") else [{"id": "dsr-old", "activista_id": A2, "activista": "Activista Dois", "data": "2026-11-02", "ate": None, "motivo": "tuk_tuk", "descricao": None, "area_id": "PR2-1", "produtor": "Produtor Dois", "quem": "Activista Dois", "criado_em": "2026-11-06T10:06:00Z"}])
    if "/rpc/meta_por_explicar" in u: return ok([] if estado.get("mm") else [{"activista_id": A1, "equipa": "Activista Um", "data": ontem, "plantas": 120, "meta": 700, "pct": 17.1, "pessoas": 5, "ini": "06:10", "fim": "10:40", "espera_min": 5}])
    if "/rpc/gravar_meta_motivo" in u: estado["mm"] = True; rec.append(("mm", json.loads(r.post_data))); return ok({"ok": True})
    if "/rpc/confirmar_dia_sem_rega" in u: estado["conf_ant"] = True; rec.append(("conf_dsr", json.loads(r.post_data))); return ok({"estado": "confirmado"})
    if "/rpc/monitoria_lista" in u: return ok([{"amostra_id": "m1", "data_rega": ontem, "area_id": "PR1-1", "activista_id": A1, "feita": False}, {"amostra_id": "m2", "data_rega": hoje, "area_id": "PR2-1", "activista_id": A2, "feita": False}])
    if "/rpc/fechar_dia" in u:
        if not estado["dsr"]: return ok({"code": "P0001", "message": "Ainda sem rega nem motivo: Activista Dois"}, 400)
        estado["fechado"] = datetime.datetime.utcnow().isoformat() + "Z"; rec.append("fechar"); return ok(estado["fechado"])
    if "/rpc/confirmar_rega" in u:
        d = json.loads(r.post_data)
        if d.get("p_vivas") is not None and d["p_vivas"] < 300: return r.fulfill(status=400, content_type="application/json", body=json.dumps({"code": "P0001", "message": "Contou %d plantas vivas, menos do que as 300 regadas. Corrija as plantas regadas na ficha do campo." % d["p_vivas"]}))
        estado["conf"] = True; rec.append(("conf", d)); return ok({"recontagem": "pedida"} if "confirmar_rega2" in u else None)
    if "/rpc/gravar_dia_sem_rega" in u: estado["dsr"] = True; rec.append(("dsr", json.loads(r.post_data)["p_motivo"], json.loads(r.post_data)["p_activista"])); return ok(None)
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
    pg.goto("http://localhost:8864/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "tec"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1800)
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(500)
    pg.evaluate("window.__TAR_ABERTAS = true; actHoje()"); pg.wait_for_timeout(600)
    LING = os.environ.get("LING", "pt"); falhas = []
    def verif(c, txt):
        print(("OK  " if c else "FALHA ") + txt)
        if not c: falhas.append(txt)
    sec = SEC(pg, "mt")
    verif("Activista Um" in sec and NB(pg, "mt").strip() == "1", "1 linha da meta sem explicação com 1")
    verif("06:10" in sec and "10:40" in sec, "2 mostra as horas do dia")
    if LING != "pt":
        for x in ["Meta muito abaixo", "Pergunte à equipa", "plantas da meta", "Escrever o motivo"]: verif(x not in sec, f"2b traduzido: «{x}»")
    pg.screenshot(path=f"/home/claude/rega-test/v226_meudia_{LING}.png", full_page=True)
    pg.click("#meu-dia details[data-k=mt] button.chip"); pg.wait_for_selector("#mm-ok")
    if LING != "pt":
        f = pg.inner_text("#folha-c")
        for x in ["Porque não se atingiu", "Motivo (obrigatório)", "Guardar o motivo", "última saída"]: verif(x not in f, f"2c traduzido: «{x}»")
    pg.click("#mm-ok"); pg.wait_for_timeout(300)
    verif(pg.locator("#mm-msg .erro").count() == 1, "3 sem motivo não grava")
    pg.fill("#mm-mot", "Equipa saiu cedo para o funeral na comunidade"); pg.click("#mm-ok"); pg.wait_for_timeout(4500)
    verif(any(x[0] == "mm" and x[1].get("p_activista") == A1 and x[1].get("p_data") == ontem for x in rec if isinstance(x, tuple)), f"4 enviado ao servidor ({[x for x in rec if isinstance(x, tuple) and x[0]=='mm']})")
    pg.evaluate("carregarMeuDia().then(actHoje)"); pg.wait_for_timeout(1500)
    verif(pg.locator("#meu-dia details[data-k=mt]").count() == 0, "5 depois de gravar, a linha sai")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
