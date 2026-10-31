# Supervisores vêem todos os campos com a sua lista (v108, 24/10/2026): filtro "As minhas / Todas", ficha só de ver fora da lista,
# "Passar para a minha equipa" com motivo, cartão "campos sem equipa" no Hoje. PAPEL=tecnico (desde v109 igual ao supervisor, com motivo também ao mudar campos da própria equipa); LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; PAPEL = os.environ.get("PAPEL", "supervisor"); LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8815", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1, A2 = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"
lat0, lon0 = -10.70, 40.47
def ar(i, act, com, prop=None): return {"id": f"PR{i}-1", "pr": f"PR{i}", "area_n": 1, "comunidade": com, "produtor": f"Produtor {i}", "instaladas": 100, "vivas": 100, "latitude": lat0 + i * 0.001, "longitude": lon0, "activista_id": act, "activista_proposto": prop, "activa": True}
areas = [ar(1, A1, "Farol"), ar(2, A2, "Senga"), ar(3, None, "Farol", "Activista Meu"), ar(4, None, "Senga")]
rec = []; erros = []; dial = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "s@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Sup Teste", "papel": PAPEL, "activista_id": None})
    if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Meu", "comunidade_principal": "Farol", "supervisor": "Sup Teste", "activo": True}, {"id": A2, "nome": "Activista Outro", "comunidade_principal": "Senga", "supervisor": "Outro Supervisor", "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([A1])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/atribuir_area2" in u: rec.append(json.loads(r.post_data)); return ok(None)
    if "/rest/v1/registos_rega" in u and r.method == "HEAD": return route.fulfill(status=200, headers={"content-range": "0-0/3"}, body="")
    return ok([])
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": lat0, "longitude": lon0, "accuracy": 5})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.goto("http://localhost:8815/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "sup"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1800)
    print("1 botão do mapa:", pg.is_visible("#b-filtro"), pg.inner_text("#b-filtro") if pg.is_visible("#b-filtro") else "", "| no mapa:", pg.evaluate("visiveis().map(a => a.id)"))
    if pg.is_visible("#b-filtro"):
        pg.click("#b-filtro"); pg.wait_for_timeout(300); print("2 depois de tocar:", pg.inner_text("#b-filtro"), pg.evaluate("visiveis().length"), "| guardado:", pg.evaluate("LS.get('filtroSup')"))
        pg.click("#b-filtro"); pg.wait_for_timeout(300)
    pg.evaluate("mudar('hoje')"); pg.wait_for_timeout(800)
    t = pg.locator("#e-hoje .cartao:has-text('⚠️')")
    print("3 Hoje:", t.inner_text().replace("\n", " | ") if t.count() else "(sem cartão)")
    if t.count():
        t.locator("button").click(); pg.wait_for_timeout(500)
        print("4 lista:", pg.input_value("#f-ambito"), pg.input_value("#f-sit"), "|", [x.split("\n")[0] for x in pg.locator("#lista .item").all_inner_texts()])
    pg.evaluate("$('#f-sit').value=''; $('#f-ambito').value='todas'; $('#f-ambito').dispatchEvent(new Event('change'))"); pg.wait_for_timeout(300)
    print("5 todos:", [x.replace("\n", " ")[:80] for x in pg.locator("#lista .item").all_inner_texts()])
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(400)
    print("6 ficha outra equipa:", pg.inner_text("#folha-c").replace("\n", " | ")[:500])
    print("   botões:", pg.locator("#folha-c button").all_inner_texts())
    if pg.locator("#folha-c button:has-text('➡️')").count():
        pg.click("#folha-c button:has-text('➡️')"); pg.wait_for_timeout(300)
        print("7 ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:300])
        pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(200); print("8 sem motivo →", dial[-1] if dial else "")
        pg.fill("#t-motivo", "campo fica em Farol"); pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(300)
        pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(1500)
        print("9 enviado:", rec, "| agora é meu:", pg.evaluate("meuCampo(S.areas.find(a => a.id === 'PR2-1'))"))
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(300)
    print("10 ficha própria, botões:", pg.locator("#folha-c button").all_inner_texts()[:6])
    if PAPEL == "tecnico":
        pg.click("#folha-c button:has-text('👤')"); pg.wait_for_timeout(300)
        print("11 técnico muda activista da própria equipa → motivo:", pg.is_visible("#t-motivo"), "|", pg.inner_text("#folha-c label >> nth=1")[:60] if pg.locator("#folha-c label").count() > 1 else "")
    pg.screenshot(path=f"/home/claude/rega-test/lista_sup{LING}.png")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
