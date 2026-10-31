# Percurso do dia (19/10/2026, Dalmar/Valdo): o activista grava com o GPS que a app já lê; o gestor vê no mapa.
import json, subprocess, time, sys, os
sys.path.insert(0, "/home/claude/rega-test")
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8812", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; ACT2 = "11111111-1111-1111-1111-111111111112"; UID = "22222222-2222-2222-2222-222222222222"
AREAS = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6800, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}] + \
        [{"id": f"PRX{i}-1", "pr": f"PRX{i}", "area_n": 1, "comunidade": "Farol", "produtor": f"Produtor Vizinho {i}", "instaladas": 50, "vivas": 50, "latitude": -10.6870 + (i % 5) * 0.0012, "longitude": 40.6300 + (i // 5) * 0.0015, "activista_id": ACT, "activista_proposto": None} for i in range(20)]
ST = {"papel": "activista", "grav": []}
T0 = int(time.time()) - 4 * 3600
import datetime
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
PONTOS = [[40.6340, -10.6860 + i * 0.0004, T0 + i * 120, 6] for i in range(10)] + [[40.6340, -10.6800 + i * 0.0004, T0 + 3600 + i * 120, 6] for i in range(5)]
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    corpo = lambda: json.loads(r.post_data or "{}")
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": {"activista": "Activista Exemplo", "gestor": "Gestor Exemplo", "cliente": "Cliente Exemplo"}[ST["papel"]], "papel": ST["papel"], "activista_id": ACT if ST["papel"] == "activista" else None})
    if "/rpc/gravar_percurso" in u: ST["grav"].append(corpo()); return route.fulfill(status=204, body="")
    if "/rpc/percursos_dia" in u: return ok([{"activista_id": ACT, "user_id": None, "nome": "Activista Exemplo", "teste": False, "n": len(PONTOS), "primeiro": "2026-10-19T06:00:00Z", "ultimo": "2026-10-19T08:00:00Z"},
        {"activista_id": ACT2, "user_id": None, "nome": "Segundo Activista Silva", "teste": False, "n": 8, "primeiro": "2026-10-19T06:30:00Z", "ultimo": "2026-10-19T09:00:00Z"},
        {"activista_id": None, "user_id": UID, "nome": "Sup Teste", "teste": True, "n": 5, "primeiro": "2026-10-19T07:00:00Z", "ultimo": "2026-10-19T07:30:00Z"}])
    if "/rpc/percurso_dia" in u:
        c = corpo(); ST["pedido"] = c
        if c.get("p_activista") == ACT2: return ok({"pontos": [[40.6300 + i * 0.0006, -10.6850, T0 + i * 300, 8] for i in range(8)], "regas": [{"area_id": "PR1-1", "entrada_em": "2026-10-19T07:00:00Z", "saida_em": "2026-10-19T07:30:00Z", "plantas": 70}]})
        if c.get("p_user"): return ok({"pontos": [[40.6370, -10.6870 + i * 0.0005, T0 + i * 200, 5] for i in range(5)], "regas": []})
        return ok({"pontos": PONTOS, "regas": [{"area_id": "PR1-1", "entrada_em": iso(T0 + 300), "saida_em": iso(T0 + 900), "plantas": 70}, {"area_id": "PR2-1", "entrada_em": iso(T0 + 3700), "saida_em": iso(T0 + 4000), "plantas": 60}]})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Farol", "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok(AREAS)
    if "/rpc/" in u: return ok([])
    if "/rest/v1/" in u and r.method == "GET": return ok([])
    return route.fulfill(status=201, body="")
erros = []
def abrir(b, papel):
    ST["papel"] = papel
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6860, "longitude": 40.6340, "accuracy": 6})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(f"{papel}: {e}")); pg.on("dialog", lambda d: d.accept())
    pg.goto("http://localhost:8812/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate("modoEntrada('tecnico')"); pg.fill("#l-user", "u"); pg.fill("#l-senha", "senha-teste-1"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2000)
    return ctx, pg
linhas = lambda t, *ks: [l for l in t.split("\n") if any(k.lower() in l.lower() for k in ks)]
def andar(ctx, pg, n, de=-10.6860):
    for i in range(n): ctx.set_geolocation({"latitude": de + i * 0.0005, "longitude": 40.6340, "accuracy": 6}); pg.wait_for_timeout(500)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx, pg = abrir(b, "activista")
    print("0 botão percursos (activista):", pg.is_visible("#b-perc"))
    andar(ctx, pg, 3); print("1 antes de começar o dia: pontos", pg.evaluate("pontosPercursoHoje()"))
    pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(800)
    pg.evaluate("LS.set('jornada', { id: crypto.randomUUID(), data: hojeISO(), pessoas: 4 }); desenharHoje()"); pg.wait_for_timeout(500)
    andar(ctx, pg, 6); pg.wait_for_timeout(300)
    print("2 a andar 6 × 55 m: pontos", pg.evaluate("pontosPercursoHoje()"))
    ctx.set_geolocation({"latitude": -10.6860 + 5 * 0.0005 + 0.00005, "longitude": 40.6340, "accuracy": 6}); pg.wait_for_timeout(500)
    print("3 parado (5 m): pontos", pg.evaluate("pontosPercursoHoje()"))
    ctx.set_geolocation({"latitude": -10.6700, "longitude": 40.6340, "accuracy": 120}); pg.wait_for_timeout(500)
    print("4 GPS fraco (±120 m): pontos", pg.evaluate("pontosPercursoHoje()"))
    pg.evaluate("desenharHoje()"); pg.wait_for_timeout(500); print("5 activista não vê o percurso no Hoje:", pg.locator("#perc-n").count() == 0 and "ercurso" not in pg.inner_text("#hoje"))
    pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(1500)
    g = ST["grav"]; print("6 enviado:", len(g), "chamada(s) |", [(len(x["p_pontos"]), x["p_teste"], x["p_data"]) for x in g], "| por enviar:", pg.evaluate("percursoPorEnviar()"))
    pg.evaluate("LS.set('percursoFim', hojeISO())")   # como às 18:00
    andar(ctx, pg, 3, -10.6750); print("7 depois de terminar: pontos", pg.evaluate("pontosPercursoHoje()"), )
    ctx.close()
    ctx, pg = abrir(b, "gestor")
    print("8 botão percursos (gestor):", pg.is_visible("#b-perc"), pg.inner_text("#b-perc"))
    pg.click("#b-perc"); pg.wait_for_timeout(800); print("9 lista:", pg.inner_text("#pc-lista").replace("\n", " | "))
    pg.click("#pc-lista .item >> nth=0"); pg.wait_for_timeout(1200)
    print("10 pedido:", ST.get("pedido"), "| painel:", pg.inner_text("#percurso").replace("\n", " | "))
    print("11 camadas do percurso:", pg.evaluate("percCamada.getLayers().length"), "| legenda escondida:", not pg.is_visible(".legenda"), "| campos e etiquetas escondidos:", pg.evaluate("!mapa.hasLayer(camada) && !mapa.hasLayer(rotulos)"))
    pg.screenshot(path=f"/home/claude/rega-test/percurso{os.environ.get('LING','')}.png")
    print("11b quadrados 1-9:", pg.locator(".ic-perc-n").count(), "| legenda:", pg.inner_text("#pc-leg")[:90])
    pg.click("#percurso button:has-text('Esconder'), #percurso button:has-text('Hide'), #percurso button:has-text('Ficha')"); pg.wait_for_timeout(300)
    print("11c escondido:", not pg.is_visible("#percurso"), "| botão para voltar:", pg.is_visible("#pc-mostrar"), pg.inner_text("#pc-mostrar"))
    pg.click("#pc-mostrar"); pg.wait_for_timeout(300); print("11d de volta:", pg.is_visible("#percurso"), "| botão:", pg.is_visible("#pc-mostrar"))
    print("11e tracejado pelo campo regado no buraco:", pg.evaluate("""(() => { const a = S.areas.find(x => x.latitude != null); const n0 = percCamada.getLayers().length;
      const P = [{ll:[-10.68,40.63], t:1000}, {ll:[-10.681,40.631], t:1000+3600}];
      tracarPercurso(P, '#000', '#555', null, [{area_id: a.id, entrada_em: new Date((1000+1800)*1000).toISOString()}]);
      return percCamada.getLayers().slice(n0).filter(l => l.getLatLngs && l.getLatLngs().length === 3).length; })()"""))
    pg.click("#pc-fechar"); print("12 fechar: camadas", pg.evaluate("percCamada.getLayers().length"), "| legenda:", pg.is_visible(".legenda"), "| campos de volta:", pg.evaluate("mapa.hasLayer(camada) && mapa.hasLayer(rotulos)"))
    print("12b guardado no telefone: dias", pg.evaluate("Object.keys(LS.get('percDias',{}))"), "| percurso no IndexedDB:", pg.evaluate("FOTOS.ler(chavePerc(hojeISO(), S.percLista[0])).then(g => !!(g && g.dados && g.dados.pontos.length))"))
    pg.click("#b-perc"); pg.wait_for_timeout(1000); pg.click("button[onclick^=verTodasEquipas]"); pg.wait_for_timeout(1500)
    print("14 todas:", pg.inner_text("#percurso").replace("\n", " | "), "| camadas:", pg.evaluate("percCamada.getLayers().length"))
    pg.screenshot(path=f"/home/claude/rega-test/percurso_todas{os.environ.get('LING','')}.png")
    pg.click("#pc-info div >> nth=1"); pg.wait_for_timeout(1000); print("15 tocar na 2.ª equipa:", pg.inner_text("#pc-total"), "|", pg.inner_text("#pc-info"))
    pg.click("#pc-fechar")
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.click("#b-perc"); pg.wait_for_timeout(800); pg.click("button[onclick^=verTodasEquipas]"); pg.wait_for_timeout(1200)
    print("16 todas sem rede:", pg.inner_text("#pc-info").replace("\n", " | ")); pg.click("#pc-fechar")
    pg.click("#b-perc"); pg.wait_for_timeout(800); print("12c sem rede, lista:", pg.inner_text("#pc-lista").replace("\n", " | "))
    pg.click("#pc-lista .item"); pg.wait_for_timeout(1000); print("12d sem rede, percurso:", pg.inner_text("#pc-info").replace("\n", " | "), "| linhas:", pg.evaluate("percCamada.getLayers().length"))
    pg.evaluate("ecraPercursos('2026-10-01')"); pg.wait_for_timeout(500); print("12e sem rede, dia sem dados:", pg.inner_text("#pc-lista"))
    ctx.close()
    ctx, pg = abrir(b, "cliente"); pg.click("nav button[data-e=mapa]"); pg.wait_for_timeout(600); print("13 botão percursos (cliente, no Mapa):", pg.is_visible("#b-perc"), pg.evaluate("[S.perfil.papel, podeVerPercursos(), document.querySelector('#b-perc').style.display, document.querySelector('#e-mapa').className]")); ctx.close()
    print("ERROS JS:", erros or "nenhum")
    b.close()
srv.terminate()
