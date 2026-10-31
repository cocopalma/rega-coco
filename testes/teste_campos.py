import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8768", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
A1, A2 = "11111111-1111-1111-1111-111111111111", "44444444-4444-4444-4444-444444444444"
def areas():
    return [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None},
            {"id": "PR9-1", "pr": "PR9", "area_n": 1, "comunidade": "Senga", "produtor": "Produtor Nove", "instaladas": 50, "vivas": 40, "latitude": -10.7500, "longitude": 40.5000, "activista_id": A2, "activista_proposto": None},
            {"id": "PRX-1", "pr": "PRX", "area_n": 1, "comunidade": "Farol", "produtor": "Sem Coordenada", "instaladas": 30, "vivas": 30, "latitude": None, "longitude": None, "activista_id": None, "activista_proposto": "Julia Jaime"},
            {"id": "PRY-1", "pr": "PRY", "area_n": 1, "comunidade": "Farol", "produtor": "Proposta Um", "instaladas": 20, "vivas": 20, "latitude": -10.6837, "longitude": 40.6342, "activista_id": None, "activista_proposto": "Majula Muemede Bacar"}]
rpcs = []; erros = []; ESTADO = {}
def fazer_mock(papel):
    def mock(route):
        r = route.request; u = r.url
        ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
        if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time())+3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "x@rega-coco.example.com"}})
        if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Pessoa Teste", "papel": papel, "activista_id": None})
        if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol"}, {"id": A2, "nome": "Julia Jaime", "comunidade_principal": "Senga"}])
        if "/rest/v1/areas" in u: return ok([dict(a, activista_id=ESTADO.get(a["id"], a["activista_id"])) for a in areas()])
        if "/rpc/estado_ronda" in u: return ok([])
        if "/rest/v1/zonas" in u: return ok([{"comunidade": "Farol", "zona": "Norte"}, {"comunidade": "Farol", "zona": "Sul"}])
        if "/rpc/definir_zona" in u: rpcs.append(("definir_zona", json.loads(r.post_data))); return route.fulfill(status=204, body="")
        if "/rpc/meus_activistas" in u: return ok([A1, A2] if papel == "supervisor" else [A1])
        if "/rpc/gravar_coordenada" in u or "/rpc/atribuir_area" in u:
            corpo = json.loads(r.post_data); rpcs.append((u.split("/rpc/")[1], corpo))
            if "atribuir" in u: ESTADO[corpo["p_area"]] = corpo["p_activista"]
            return route.fulfill(status=204, body="")
        return ok([])
    return mock
with sync_playwright() as p:
    b = p.chromium.launch()
    def contexto(papel):
        ctx = b.new_context(viewport={"width": 390, "height": 800}, geolocation={"latitude": -10.6839, "longitude": 40.6345, "accuracy": 8}, permissions=["geolocation"])
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
        ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
        ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
        ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", fazer_mock(papel))
        pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(papel + ": " + str(e))); pg.on("dialog", lambda d: d.accept())
        pg.goto("http://localhost:8768/"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.fill("#l-user", "t"); pg.fill("#l-pin", "12345678"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(800)
        return ctx, pg
    def ficha(pg, id):
        if pg.is_visible("#folha.on"): pg.click("#folha-x")
        pg.click("nav button[data-e=lista]"); pg.click(f".item[data-id='{id}']"); pg.wait_for_selector("#folha.on")
        return pg.inner_text("#folha-c")
    # supervisor, sem rede: grava coordenada e atribui; depois volta a rede
    ctx, pg = contexto("supervisor")
    t = ficha(pg, "PRX-1"); print("1 supervisor, campo sem coordenada → botões:", [x for x in ["Gravar a coordenada", "Atribuir a um activista"] if x in t])
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.click("text=Gravar a coordenada deste campo"); pg.wait_for_timeout(500); ctx.set_geolocation({"latitude": -10.68391, "longitude": 40.63451, "accuracy": 8})
    pg.wait_for_selector("#c-gravar:not([disabled])", timeout=15000)
    print("2 leitura:", pg.inner_text("#folha-c .cartao").replace("\n", " "), "| nota:", pg.inner_text("#folha-c .msg.info")[:60])
    pg.click("#c-gravar"); pg.wait_for_selector("#t-act")
    opcoes = pg.eval_on_selector_all("#t-act optgroup:first-child option", "o => o.map(x => x.textContent)")
    print("3 atribuir — mais próximos:", opcoes[:2], "| proposta da base mostrada:", pg.is_visible("text=Proposta da base"))
    pg.click("#folha-c button:has-text('Gravar')"); pg.wait_for_selector("text=Campo atribuído")
    print("4 sem rede: fila =", pg.evaluate("JSON.parse(localStorage.getItem('rega.filaAlt')).length"), "| botão:", pg.inner_text("#h-sync"), "| RPCs enviados:", len(rpcs))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.wait_for_timeout(2500)
    print("5 com rede: fila =", pg.evaluate("JSON.parse(localStorage.getItem('rega.filaAlt')).length"), "| enviados:", rpcs)
    print("   campo continua com coordenada e activista após recarregar:", pg.evaluate("(()=>{const a=JSON.parse(localStorage.getItem('rega.areas')).find(x=>x.id==='PRX-1');return [a.latitude!=null, a.activista_id]})()"))
    ctx.close()
    ESTADO.clear()
    # precisão fraca: botão fica bloqueado
    ctx, pg = contexto("supervisor"); ctx.set_geolocation({"latitude": -10.6839, "longitude": 40.6345, "accuracy": 25})
    ficha(pg, "PRX-1"); pg.click("text=Gravar a coordenada deste campo"); pg.wait_for_timeout(500); ctx.set_geolocation({"latitude": -10.68392, "longitude": 40.63452, "accuracy": 25}); pg.wait_for_function("document.querySelector('#c-prec').textContent.includes('±')")
    print("2b precisão 25 m:", pg.inner_text("#c-prec"), "| gravar bloqueado:", pg.is_disabled("#c-gravar")); ctx.close()
    # técnico: campo com activista e coordenada → nenhum botão; campo sem activista → pode atribuir
    ctx, pg = contexto("tecnico")
    t1 = ficha(pg, "PR1-1"); t2 = ficha(pg, "PRX-1")
    print("6 técnico — campo com activista e coordenada:", [x for x in ["coordenada", "activista deste", "Atribuir"] if x in t1] or "sem botões",
          "| campo sem coordenada nem activista:", [x for x in ["Gravar a coordenada", "Atribuir a um activista"] if x in t2])
    ctx.close()
    ctx, pg = contexto("tecnico"); ficha(pg, "PRX-1"); pg.click("text=Atribuir a um activista"); pg.wait_for_selector("#t-act")
    print("6b técnico — activistas na lista:", pg.eval_on_selector_all("#t-act option", "o => o.map(x => x.textContent.split(' —')[0])")); ctx.close()
    ctx, pg = contexto("director"); t = ficha(pg, "PRX-1"); print("7 director:", "sem botões" if "📍" not in t and "👤" not in t else "TEM BOTÕES"); ctx.close()
    # lista "Por atribuir": confirmar proposta com um toque
    rpcs.clear(); ESTADO.clear(); ctx, pg = contexto("supervisor"); pg.click("nav button[data-e=lista]")
    print("8 aviso na lista:", pg.inner_text("#lista .msg.info")[:40])
    pg.select_option("#f-sit", "sem"); pg.wait_for_timeout(300)
    print("  supervisor por atribuir:", [x.inner_text().split("\n")[0] for x in pg.query_selector_all("#lista .item")], "| botões confirmar:", len(pg.query_selector_all("button[data-acc=confirmar]")))
    pg.click("button[data-acc=confirmar][data-id='PRY-1']"); pg.wait_for_timeout(1500)
    print("  confirmado:", rpcs, "| restam:", [x.inner_text().split("\n")[0] for x in pg.query_selector_all("#lista .item")]); ctx.close()
    ctx, pg = contexto("tecnico"); pg.click("nav button[data-e=lista]"); pg.select_option("#f-sit", "sem"); pg.wait_for_timeout(300)
    print("9 técnico:", [x.inner_text().replace("\n", " / ")[:120] for x in pg.query_selector_all("#lista .item")])
    pg.click("button[data-acc=outro][data-id='PRX-1']"); pg.wait_for_selector("#t-act"); print("  escolher outro abre ecrã de atribuição, escolhido:", pg.eval_on_selector("#t-act", "s => s.selectedOptions[0].textContent")); ctx.close()
    # zonas
    rpcs.clear(); ESTADO.clear(); ctx, pg = contexto("supervisor"); t = ficha(pg, "PR1-1")
    print("10 ficha mostra zona:", "Zona" in t and "por definir" in t, "| botão:", "Definir a zona" in t)
    pg.click("text=Definir a zona"); pg.select_option("#z-zona", "Norte"); pg.click("#folha-c button:has-text('Gravar')"); pg.wait_for_selector("text=Zona definida"); pg.wait_for_timeout(1200)
    print("   gravada:", [x for x in rpcs if x[0] == "definir_zona"])
    pg.click("#folha-x"); pg.click("nav button[data-e=lista]")
    print("   filtro tem zonas:", pg.eval_on_selector_all("#f-com option", "o => o.map(x => x.textContent.trim())"))
    ctx.close()
    ctx, pg = contexto("tecnico"); t = ficha(pg, "PR1-1"); print("11 técnico vê zona mas não muda:", "Zona" in t, "Definir a zona" not in t); ctx.close()
    ctx, pg = contexto("supervisor"); pg.click("nav button[data-e=lista]")
    pg.select_option("#f-act", label="Majula Muemede Bacar"); pg.wait_for_timeout(300)
    print("12 filtro activista Majula:", [x.inner_text().split("\n")[0] for x in pg.query_selector_all("#lista .item")])
    pg.select_option("#f-act", "__sem"); pg.wait_for_timeout(300)
    print("   sem activista:", [x.inner_text().split("\n")[0] for x in pg.query_selector_all("#lista .item")]); ctx.close()
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
