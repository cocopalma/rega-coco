# v194: «🛤 Trilho» (gravar trilho), corte dos pontos dentro dos campos, rasto guardado se a app fechar; navegação continua. LING=en / sw.
# Coqueiros fora de campo (v101, 23/10/2026): marcar sem rede com fotografia, mudar o estado, remover, enviar com rede, Excel.
# PAPEL=gestor (padrão) / director / supervisor; LING=en / sw.
import json, subprocess, time, sys, math, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; PAPEL = os.environ.get("PAPEL", "gestor"); LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8813", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
lat0, lon0 = -10.7000, 40.4700; dy, dx = 1 / 110540, 1 / (111320 * math.cos(math.radians(10.7)))
areas = [{"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Palma", "produtor": "Produtor Dois", "instaladas": 100, "vivas": 100, "latitude": lat0 + 30*dy, "longitude": lon0 + 30*dx, "activista_id": ACT, "activista_proposto": None, "poligono": [[lon0 + 20*dx, lat0 + 20*dy], [lon0 + 40*dx, lat0 + 20*dy], [lon0 + 40*dx, lat0 + 40*dy], [lon0 + 20*dx, lat0 + 40*dy]]}, {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Palma", "produtor": "Produtor Um", "instaladas": 140, "vivas": 140, "latitude": lat0 + 60*dy, "longitude": lon0 + 60*dx, "activista_id": ACT, "activista_proposto": None}]
servidor = [{"id": f"aaaaaaaa-0000-0000-0000-00000000000{i+2}", "n": i+2, "lat": lat0 + 40*dy, "lon": lon0 + (60+i*14)*dx, "precisao_m": 4, "estado": e, "local": "ACE", "observacao": None, "foto_path": "u/a.jpg", "marcado_em": "2026-10-23T10:00:00Z", "marcado_por_nome": "Dalmar Santos", "meu": False, "tratamento": i == 0, "cachos": i == 0} for i, e in enumerate(["seca", "morta", "retirado"])] + [{"id": "aaaaaaaa-0000-0000-0000-000000000001", "n": 1, "lat": lat0 + 40*dy, "lon": lon0 + 40*dx, "precisao_m": 4, "estado": "viva", "local": "ACE", "observacao": None, "foto_path": "u/aaaa.jpg", "marcado_em": "2026-10-23T10:00:00Z", "marcado_por_nome": "Dalmar Santos", "meu": False}]
rec = {"rpc": [], "fotos": []}; erros = []; dial = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "d@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Dalmar Santos", "papel": PAPEL, "activista_id": None, "titulo": "Director", "gere_acessos": False})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Palma"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/storage/v1/object/coqueiros-fotos" in u: rec["fotos"].append(u.split("coqueiros-fotos/")[-1]); return ok({"Key": "x"})
    if "/functions/v1/" in u: return ok({"activistas": [], "outros": [], "perfis": []})
    if "/rpc/trilhos" in u: rec["rpc"].append(("trilhos", r.post_data)); return ok({"agora": "2026-11-02T08:00:00Z", "fontes": {"pX": [[[lon0 + 0*dx, lat0 + 0*dy], [lon0 + 0*dx, lat0 + 15*dy], [lon0 + 0*dx, lat0 + 30*dy], [lon0 + 20*dx, lat0 + 35*dy], [lon0 + 40*dx, lat0 + 40*dy]]]}})
    if "/rpc/gravar_trilho" in u: rec["rpc"].append(("gravar_trilho", json.loads(r.post_data))); return ok(None)
    if "/rpc/coqueiros_lista" in u: return ok(servidor if PAPEL in ("gestor", "director", "supervisor", "tecnico") else None)
    for f in ("gravar_coqueiro", "remover_coqueiro"):
        if f"/rpc/{f}" in u:
            a = json.loads(r.post_data); rec["rpc"].append((f, a))
            if f == "gravar_coqueiro" and not any(x["id"] == a["p_id"] for x in servidor):
                servidor.append({"id": a["p_id"], "n": len(servidor) + 1, "lat": a["p_lat"], "lon": a["p_lon"], "precisao_m": a["p_precisao"], "estado": a["p_estado"], "local": a["p_local"], "observacao": a["p_obs"], "foto_path": a["p_foto"], "marcado_em": a["p_em"], "marcado_por_nome": "Nuro", "meu": True})
            elif f == "gravar_coqueiro": [x.update(estado=a["p_estado"]) for x in servidor if x["id"] == a["p_id"]]
            if f == "remover_coqueiro": servidor[:] = [x for x in servidor if x["id"] != a["p_id"]]
            return ok(1)
    return ok([])
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, permissions=["geolocation"], geolocation={"latitude": lat0, "longitude": lon0, "accuracy": 3}, accept_downloads=True)
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    osm = []
    def rota_osm(route):   # caminho do OSM que dá uma volta grande (não deve ser escolhido)
        osm.append(route.request.url)
        route.fulfill(status=200, content_type="application/json", headers={"Access-Control-Allow-Origin": "*"}, body=json.dumps({"code": "Ok", "routes": [{"distance": 900, "geometry": {"type": "LineString", "coordinates": [[lon0, lat0], [lon0 - 300*dx, lat0], [lon0 - 300*dx, lat0 + 300*dy], [lon0 + 40*dx, lat0 + 40*dy]]}}]}))
    ctx.route("**/routing.openstreetmap.de/**", rota_osm)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e) + " @ " + (e.stack or "")[:400])); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.goto("http://localhost:8813/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "dalmar"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    vis = pg.is_visible("#b-coq"); print("1 botão no mapa:", vis, "|", pg.inner_text("#b-coq") if vis else "")
    if not vis: print("ERROS JS:", erros or "nenhum"); b.close(); srv.terminate(); sys.exit()
    print("1 botão trilho:", pg.is_visible("#b-trilho"), pg.inner_text("#b-trilho"))
    pg.click("#b-trilho"); pg.wait_for_timeout(600)
    print("2 painel:", pg.is_visible("#trilho-cx"), "|", pg.inner_text("#trilho-cx").replace("\n", " | "))
    # anda para leste pela linha y=0 (fora), depois entra no campo (y=30, x=25..35) e sai para x=60
    for y, x in [(0, 15), (0, 30), (0, 45), (10, 50), (30, 25), (30, 30), (30, 35), (50, 50), (55, 60), (60, 75)]:
        ctx.set_geolocation({"latitude": lat0 + y*dy, "longitude": lon0 + x*dx, "accuracy": 3}); pg.wait_for_timeout(700)
    print("3 a gravar:", pg.inner_text("#tr-info"), "| guardado no telefone:", pg.evaluate("(LS.get('rastoAct')||{}).pontos?.length"))
    pg.screenshot(path="/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad/trilho1_%s.png" % LING)
    pg.click("#trilho-cx >> text=■"); pg.wait_for_timeout(900)
    tr = [x for x in rec["rpc"] if x[0] == "gravar_trilho"]
    print("4 parar: painel", pg.is_visible("#trilho-cx"), "| enviado:", [(len(x[1]["p_pontos"]), x[1].get("p_origem")) for x in tr][-1:], "| cópia local (linhas, pontos):", pg.evaluate("(() => { const k = Object.keys(trilhosMem).find(k => k[0]==='l'); return k ? [trilhosMem[k].length, trilhosMem[k].map(l=>l.length)] : null; })()"))
    # app fecha a meio: o que ficou é guardado ao abrir
    pg.click("#b-trilho"); pg.wait_for_timeout(300)
    for y, x in [(80, 0), (80, 20), (80, 40), (80, 60), (80, 80), (80, 100)]:
        ctx.set_geolocation({"latitude": lat0 + y*dy, "longitude": lon0 + x*dx, "accuracy": 3}); pg.wait_for_timeout(600)
    n0 = len([x for x in rec["rpc"] if x[0] == "gravar_trilho"])
    pg.reload(); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
    print("5 depois de recarregar: rasto em curso", pg.evaluate("!!LS.get('rastoAct')"), "| enviados a mais:", len([x for x in rec["rpc"] if x[0] == "gravar_trilho"]) - n0, "| fila:", pg.evaluate("(LS.get('filaTrilho',[])||[]).length"))
    # navegação continua a funcionar (rasto da navegação)
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(300); pg.evaluate("navegarCampo('PR1-1')"); pg.wait_for_timeout(1200)
    print("6 navegação:", pg.inner_text("#nv-dist"), "| rasto:", pg.evaluate("S.rasto && S.rasto.origem"))
    # gravar trilho a meio da navegação: a navegação pára
    pg.click("#b-trilho"); pg.wait_for_timeout(500)
    print("7 trilho durante navegação: nav", pg.is_visible("#nav-cx"), "| trilho", pg.is_visible("#trilho-cx"), "| origem", pg.evaluate("S.rasto && S.rasto.origem"))
    pg.evaluate("pararGravarTrilho(true)"); pg.wait_for_timeout(300)
    # nome do modo
    pg.evaluate("mudar('gestao')"); pg.wait_for_timeout(1200)
    print("8 Gestão:", pg.evaluate("[...document.querySelectorAll('#gestao-demo h2')].map(h=>h.innerText)"))
    print("ERROS JS:", erros or "nenhum"); b.close(); srv.terminate()
