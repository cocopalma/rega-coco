import json, subprocess, time, sys, os
LING = os.environ.get("LING", "pt")
from playwright.sync_api import sync_playwright
# v210 (07/11/2026, Valdo): recusar a medição da área pede o motivo; o activista vê-o na ficha
APP = "http://localhost:8765/"
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
PROP = [[40.6336,-10.6831],[40.6346,-10.6831],[40.6346,-10.6841],[40.6336,-10.6841]]
areas = [{"id": "PR9-1", "pr": "PR9", "area_n": 1, "comunidade": "Senga", "produtor": "Produtor Nove", "instaladas": 97, "vivas": 97, "latitude": None, "longitude": None, "poligono": None, "limites_abertos": True, "poligono_proposto": PROP, "area_m2_proposta": 5595.9, "proposta_em": "2026-11-07T06:22:22Z", "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-02-11"}]
rpc = []; erros = []
def mock(route):
    r = route.request; u = r.url
    def ok(b, st=200): route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r",
                   "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "raul@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Raul Miquilange", "papel": "supervisor"})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Rotina Carlos", "comunidade_principal": "Senga", "supervisor": "Raul Miquilange"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/aprovar_poligono" in u: rpc.append(json.loads(r.post_data)); areas[0].update(poligono_proposto=None, area_m2_proposta=None, proposta_em=None, recusa_medicao_motivo=rpc[-1]["p_motivo"], recusa_medicao_em="2026-11-07T08:20:00Z", recusa_medicao_por="Raul Miquilange"); return ok({"id": "PR9-1", "aprovado": False})
    if "/rpc/" in u and any(k in u for k in ("estado_ronda", "regas_", "lista", "meu_dia")): return ok([])
    return ok({}) if r.method != "GET" else ok([])
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"], viewport={"width": 390, "height": 800})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
    pg.goto(APP); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate("document.querySelectorAll('button').forEach(b=>{if(/Técnico|Technician|Fundi/.test(b.textContent)&&b.offsetParent)b.click()})")
    pg.fill("#l-user", "raul"); pg.fill("#l-senha" if pg.is_visible("#l-senha") else "#l-pin", "abcdef1"); pg.click("#l-entrar")
    pg.wait_for_function("S.areas && S.areas.length", timeout=15000); pg.wait_for_timeout(1500)
    pg.evaluate("fecharFolha(); abrirFicha('PR9-1')"); pg.wait_for_selector("#folha.on"); pg.wait_for_timeout(300)
    pg.click("#folha.on button.sec:has-text('✗')"); pg.wait_for_selector("#rm-mot")
    print("1 ecrã:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:300])
    pg.click("#rm-ok"); m1 = pg.inner_text("#rm-msg"); print("2 sem motivo:", m1)
    ok1 = bool(m1.strip()) and pg.evaluate("!!S.areas[0].poligono_proposto")
    pg.fill("#rm-mot", "O limite não é deste produtor"); pg.click("#rm-ok"); pg.wait_for_timeout(2500)
    t = pg.inner_text("#folha-c").replace(chr(10), " | "); print("3 depois:", t[:300])
    print("4 enviado:", rpc)
    ok2 = rpc and rpc[-1].get("p_motivo") == "O limite não é deste produtor" and rpc[-1].get("p_aprovar") is False
    ok3 = "O limite não é deste produtor" in t
    pg.evaluate("S.perfil.papel='activista'; S.perfil.activista_id='%s'; abrirFicha('PR9-1')" % ACT); pg.wait_for_timeout(400)
    ta = pg.inner_text("#folha-c").replace(chr(10), " | "); print("5 activista:", ta[:300])
    print("5b linha:", pg.evaluate("[...document.querySelectorAll('#folha-c .msg.erro')].map(e=>e.innerText).join(' || ')").replace(chr(10)," "))
    ok4 = "O limite não é deste produtor" in ta
    print("RESULTADO", "OK" if ok1 and ok2 and ok3 and ok4 and not erros else "FALHA", erros)
    b.close()
srv.terminate()
