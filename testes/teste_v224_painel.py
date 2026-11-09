# v224 (09/11/2026, Valdo: "Sim"): painel «Equipa de campo» não conta como falta um motivo registado depois do próprio dia.
# (teste_v224_meudia.py: o técnico confirma motivos de dias anteriores no «O meu dia»). LING=en / sw.
import json, subprocess, time, sys, os, datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt"); GERE = os.environ.get("GERE", "1") == "1"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8853", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
hoje = datetime.datetime.now(ZoneInfo("Africa/Maputo")).date()
dias = [hoje - datetime.timedelta(days=i) for i in range(0, 9) if (hoje - datetime.timedelta(days=i)).isoweekday() < 7][:6]
iso = lambda d: d.isoformat()
def dia(d, fecho=None, sem=None, cheg=None, mon=0, fora=0, acomp=0):
    return {"data": iso(d), "fecho": fecho, "sem_rega": sem or [], "monitoria": mon, "chegadas": cheg or [], "fora": fora, "acomp": acomp}
EQ = {"dia": iso(hoje), "agora": iso(hoje) + "T12:00", "limite": "18:00", "hora_chegada": "06:30", "monitoria_pausa": True, "inicio": "2026-10-29",
      "pessoas": [
        {"id": "p1", "nome": "Técnico Atrasado", "papel": "tecnico", "equipas": ["Ana Um", "Bruno Dois"],
         "dias": [dia(dias[0], None, ["Bruno Dois"], [{"nome": "Ana Um", "hora": "07:10"}], acomp=1)] + [dia(d, None if i % 2 else "19:40", ["Ana Um"] if i == 1 else []) for i, d in enumerate(dias[1:], 1)],
         "alertas": [{"activista": "Ana Um", "pr": "PR111-1", "data": iso(dias[2]), "tipo": "mais_que_base", "plantas": 300, "base": 150}],
         "motivos": [{"activista": "Bruno Dois", "data": iso(dias[1]), "motivo": "tuk_tuk", "registado": iso(dias[0])}],
         "medicoes": [{"activista": "Ana Um", "pr": "PR222-1", "produtor": "Produtor X", "em": iso(hoje) + "T09:35"}], "sem_equipa": 2},
        {"id": "p2", "nome": "Supervisor Cumpridor", "papel": "supervisor", "equipas": ["Ana Um"],
         "dias": [dia(dias[0], "15:10")] + [dia(d, "16:00") for d in dias[1:]], "alertas": [], "motivos": [], "medicoes": [], "sem_equipa": 0}]}
rec = {}; erros = []; falhas = []
def verif(c, txt):
    print(("OK  " if c else "FALHA ") + txt)
    if not c: falhas.append(txt)
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u-g", "aud": "authenticated", "role": "authenticated", "email": "valdo@rega-coco.example.com"}})
    if "/auth/v1/logout" in u: return route.fulfill(status=204, body="")
    if "/rest/v1/perfis" in u: return ok({"id": "u-g", "nome": "Valdo", "papel": "gestor", "gere_acessos": GERE, "activista_id": None})
    if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
    if "/rpc/gestao_equipa_campo" in u: rec["eq"] = rec.get("eq", 0) + 1; return ok(EQ if GERE else None)
    if "/rpc/sugestoes_lista" in u: return ok({"sugestoes": [], "problemas": []})
    if "/rpc/" in u: return ok([])
    if "/rest/v1/areas" in u or "/rest/v1/activistas" in u or "/rest/v1/registos_rega" in u: return ok([])
    return ok({})
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, timezone_id="Africa/Maputo", geolocation={"latitude": -10.7353, "longitude": 40.4684}, permissions=["geolocation"])
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(path=f"{NM}/leaflet-rotate/dist/leaflet-rotate-src.js", content_type="application/javascript"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e) + " | " + (e.stack or "")[:300])); pg.on("dialog", lambda d: d.accept())
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.goto("http://localhost:8853/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "valdo"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.wait_for_timeout(1500)
    pg.evaluate("window.__TAR_ABERTAS = true; fecharFolha && fecharFolha(); mudar('gestao')"); pg.wait_for_timeout(1800)
    c1 = pg.locator("#gestao-eq .eqc").nth(0)
    ln = c1.locator("details[data-k=\"eq-p1-1\"]")
    t = ln.inner_text()
    verif(ln.locator(".nb").inner_text().strip() == "0", "1 motivo registado depois do dia: número 0 (não conta como falta)")
    if LING == "pt": verif("não conta como falta" in t and "registado a" in t, "2 diz que foi registado depois e não conta")
    else: verif("não conta" not in t and "registado a" not in t, "2 traduzido")
    pg.screenshot(path=f"/home/claude/rega-test/v224_painel_{LING}.png", full_page=True)
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
