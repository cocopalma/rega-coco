# v191: navegar até ao coqueiro dentro da app (seta, distância que diminui ao andar, aviso ao chegar). LING=en / sw. Baseado em teste_v185.py.
# Coqueiros fora de campo (v101, 23/10/2026): marcar sem rede com fotografia, mudar o estado, remover, enviar com rede, Excel.
# PAPEL=gestor (padrão) / director / supervisor; LING=en / sw.
import json, subprocess, time, sys, math, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; PAPEL = os.environ.get("PAPEL", "gestor"); LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8813", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
lat0, lon0 = -10.7000, 40.4700; dy, dx = 1 / 110540, 1 / (111320 * math.cos(math.radians(10.7)))
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Palma", "produtor": "Produtor Um", "instaladas": 140, "vivas": 140, "latitude": lat0 + 60*dy, "longitude": lon0 + 60*dx, "activista_id": ACT, "activista_proposto": None}]
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
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.goto("http://localhost:8813/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "dalmar"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    vis = pg.is_visible("#b-coq"); print("1 botão no mapa:", vis, "|", pg.inner_text("#b-coq") if vis else "")
    if not vis: print("ERROS JS:", erros or "nenhum"); b.close(); srv.terminate(); sys.exit()
    pg.click("#b-coq"); pg.wait_for_timeout(1200)
    vivo = "aaaaaaaa-0000-0000-0000-000000000001"
    pg.evaluate("(id) => verCoq(id)", vivo); pg.wait_for_timeout(300)
    print("1 ficha:", pg.evaluate("[...document.querySelectorAll('#folha-c .chips')][0].innerText.replace(/\\n/g,' | ')"), "| links externos:", pg.evaluate("document.querySelectorAll('#folha-c a[href*=google]').length"))
    pg.click("#folha-c .cq-nav"); pg.wait_for_timeout(600)
    print("2 painel:", pg.is_visible("#cq-nav"), "| cartão coq:", pg.is_visible("#coq"), "| folha:", pg.evaluate("document.querySelector('#folha').className"))
    print("  ", pg.inner_text("#cq-nav").replace("\n", " | "))
    print("   linha:", pg.evaluate("!!navLinha"), "| ponto azul e coqueiro no ecrã:", pg.evaluate("[mapa.getBounds().contains(S.pos), mapa.getBounds().contains([coqLista().find(c=>c.id===S.coq.nav.id).lat, coqLista().find(c=>c.id===S.coq.nav.id).lon])]"))
    pg.screenshot(path="/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad/nav1_%s.png" % LING)
    ds = []
    for k in [10, 20, 30, 38, 40]:
        ctx.set_geolocation({"latitude": lat0 + k*dy, "longitude": lon0 + k*dx, "accuracy": 3}); pg.wait_for_timeout(1500)
        ds.append(pg.inner_text("#nv-dist"))
    print("3 distâncias ao andar:", ds, "| chegou:", pg.is_visible("#nv-chegou"), pg.inner_text("#nv-chegou") if pg.is_visible("#nv-chegou") else "")
    pg.screenshot(path="/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad/nav2_%s.png" % LING)
    pg.evaluate("verCoq = (id) => window._ab = id"); pg.click("#nv-ficha"); print("4 abrir a ficha:", pg.evaluate("window._ab"))
    pg.click("#cq-nav >> text=■"); pg.wait_for_timeout(300)
    print("5 parar: painel", pg.is_visible("#cq-nav"), "| linha", pg.evaluate("!!navLinha"), "| cartão coq", pg.is_visible("#coq"))
    pg.evaluate("listaCoq('viva')"); pg.wait_for_timeout(200)
    print("6 lista:", pg.evaluate("[...document.querySelectorAll('#folha-c .cq-item .chip')].map(b=>b.innerText)"))
    pg.click("#folha-c .cq-item .chip >> nth=2"); pg.wait_for_timeout(400); print("   navegar pela lista:", pg.is_visible("#cq-nav"))
    pg.click("#b-coq"); pg.wait_for_timeout(300); print("7 fechar 🥥: painel", pg.is_visible("#cq-nav"), "| linha", pg.evaluate("!!navLinha"))
    print("ERROS JS:", erros or "nenhum"); b.close(); srv.terminate()
