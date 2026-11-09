# v223 (09/11/2026, Valdo pelo 💡): Gestão › «👷 Equipa de campo», só para o gestor principal (gere_acessos).
# GERE=0: gestor sem gere_acessos (não vê o separador). LING=en / sw para as outras línguas.
import json, subprocess, time, sys, os, datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt"); GERE = os.environ.get("GERE", "1") == "1"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8852", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
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
         "motivos": [{"activista": "Bruno Dois", "data": iso(dias[1]), "motivo": "tuk_tuk"}],
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
    pg.goto("http://localhost:8852/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "valdo"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.wait_for_timeout(1500)
    pg.evaluate("window.__TAR_ABERTAS = true; fecharFolha && fecharFolha(); mudar('gestao')"); pg.wait_for_timeout(1800)
    if not GERE:
        verif(pg.locator("#gestao-tabs .chip").count() == 0, "G1 gestor sem gere_acessos: sem separadores")
        verif(not pg.is_visible("#gestao-eq") and pg.is_visible("#gestao"), "G2 vê a Gestão como antes")
        verif(rec.get("eq", 0) == 0, "G3 não pede o painel ao servidor")
    else:
        verif(pg.locator("#gestao-tabs .chip").count() == 2, "1 dois separadores")
        verif(pg.is_visible("#gestao-eq") and not pg.is_visible("#gestao"), "2 abre em «Equipa de campo»")
        t = pg.inner_text("#gestao-eq")
        cards = pg.locator("#gestao-eq .eqc")
        verif(cards.count() == 2, "3 um cartão por pessoa")
        verif(cards.nth(0).get_attribute("data-p") == "p1", "4 quem tem coisas por fazer aparece primeiro")
        c1 = cards.nth(0).inner_text(); c2 = cards.nth(1).inner_text()
        verif("Bruno Dois" in c1 and "PR111-1" in c1 and "PR222-1" in c1, "5 lista do que falta com nomes e campos")
        verif("15:10" in c2 and cards.nth(1).locator(".nb.ok").count() == 1, "6 supervisor sem nada por fazer: ✓ e hora do fecho")
        verif(cards.nth(0).locator(".faixa-eq .cel").count() == len(dias), "7 faixa com os dias da semana")
        verif("19:40" in c1, "8 dias anteriores com o fecho depois das 18:00")
        if LING == "pt":
            verif("Ainda não fechou o dia" in c1 and "Equipas ainda sem rega nem motivo" in c1, "9 hoje antes das 18:00: pode fechar, equipas ainda sem rega")
        else:
            for pt in ["O que falta", "Fecho do dia", "Motivos por confirmar", "Regas com", "Ver os dias anteriores", "fecharam o dia", "Equipa de campo", "Não fechou o dia", "Ainda não fechou"]:
                verif(pt not in t, f"9 traduzido: «{pt}»")
        pg.screenshot(path=f"/home/claude/rega-test/v223_{LING}.png", full_page=True)
        pg.click("#gestao-tabs .chip >> nth=1"); pg.wait_for_timeout(500)
        verif(pg.is_visible("#gestao") and not pg.is_visible("#gestao-eq"), "10 separador «Acessos e configurações» mostra a Gestão de antes")
        pg.click("#gestao-tabs .chip >> nth=0"); pg.wait_for_timeout(500)
        verif(pg.is_visible("#gestao-eq"), "11 volta ao painel")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
