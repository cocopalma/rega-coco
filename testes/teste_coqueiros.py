# Coqueiros fora de campo (v101, 23/10/2026): marcar sem rede com fotografia, mudar o estado, remover, enviar com rede, Excel.
# PAPEL=gestor (padrão) / director / supervisor; LING=en / sw.
import json, subprocess, time, sys, math, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; PAPEL = os.environ.get("PAPEL", "gestor"); LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8813", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
lat0, lon0 = -10.7000, 40.4700; dy, dx = 1 / 110540, 1 / (111320 * math.cos(math.radians(10.7)))
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Palma", "produtor": "Produtor Um", "instaladas": 140, "vivas": 140, "latitude": lat0 + 0.01, "longitude": lon0, "activista_id": ACT, "activista_proposto": None}]
servidor = [{"id": "aaaaaaaa-0000-0000-0000-000000000001", "n": 1, "lat": lat0 + 40*dy, "lon": lon0 + 40*dx, "precisao_m": 4, "estado": "viva", "local": "ACE", "observacao": None, "foto_path": "u/aaaa.jpg", "marcado_em": "2026-10-23T10:00:00Z", "marcado_por_nome": "Dalmar Santos", "meu": False}]
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
    print("2 painel:", pg.inner_text("#cq-total"), "|", pg.inner_text("#cq-gps"), "| marcar visível:", pg.is_visible("#cq-marcar"), "| pontos:", pg.evaluate("camadaCoq.getLayers().length"))
    print("1b satélite:", pg.inner_text("#b-fundo")); pg.click("#b-fundo"); pg.wait_for_timeout(300); print("   depois:", pg.inner_text("#b-fundo"), "| guardado:", pg.evaluate("LS.get('fundo')"), "| camada:", pg.evaluate("Object.values(mapa._layers).some(l => l._url && l._url.includes('arcgis'))"))
    pg.click("#b-fundo"); pg.wait_for_timeout(200)
    if PAPEL not in ("gestor", "supervisor", "tecnico"):
        print("ERROS JS:", erros or "nenhum"); b.close(); srv.terminate(); sys.exit()
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    for i, (x, y) in enumerate([(10, 10), (20, 10), (20.5, 10.5)]):
        ctx.set_geolocation({"latitude": lat0 + y*dy, "longitude": lon0 + x*dx, "accuracy": 3}); pg.wait_for_timeout(1200)
        t0 = time.time(); pg.click("#cq-marcar")
        pg.wait_for_selector("#cq-foto-cambtn", timeout=8000) if i < 2 else pg.wait_for_timeout(800)
        if i == 2: print("3 perto (<3 m):", [d for d in dial][-1:] );
        if not pg.is_visible("#cq-foto-cambtn"): continue
        print(f"3.{i} segundos até ao formulário:", round(time.time() - t0, 1), "| título:", pg.inner_text("#folha-c h2"))
        pg.click("#folha.on .btn >> nth=0"); pg.wait_for_timeout(200); print("   sem foto →", dial[-1] if dial else "")
        if i == 1: pg.click("#cq-est .chip >> nth=1")
        pg.fill("#cq-local", "Acampamento ACE") if i == 0 else None
        pg.evaluate("S.coqFoto = new Blob(['x'], {type: 'image/jpeg'})")
        pg.click("#folha.on .btn >> nth=0"); pg.wait_for_timeout(400)
    print("4 locais:", pg.evaluate("coqLista().map(c => [c.n || 'novo', c.estado, c.local, !!c.porEnviar])"), "| fila:", pg.evaluate("filaCoq().map(x => x.op)"))
    print("  painel:", pg.inner_text("#cq-total"), "| apagar:", pg.inner_text("#cq-desf"))
    novo = pg.evaluate("coqLista().filter(c => c.porEnviar)[0].id")
    pg.evaluate("(id) => verCoq(id)", novo); pg.wait_for_timeout(200); print("5 ficha:", pg.inner_text("#folha-c").replace("\n", " | ")[:200])
    pg.evaluate("(id) => estadoCoq(id, 'morta')", novo); pg.wait_for_timeout(200)
    print("6 estado mudado na fila (sem pedido novo):", pg.evaluate("filaCoq().map(x => x.op + ':' + x.c.estado)"))
    pg.evaluate("verCoq('aaaaaaaa-0000-0000-0000-000000000001')"); pg.wait_for_timeout(200)
    print("7 ficha do servidor:", pg.inner_text("#folha-c").replace("\n", " | ")[:220])
    pg.evaluate("estadoCoq('aaaaaaaa-0000-0000-0000-000000000001', 'seca')"); pg.wait_for_timeout(200)
    print("  fila:", pg.evaluate("filaCoq().map(x => x.op + ':' + x.c.estado + (x.foto ? ':foto' : ''))"))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(3000)
    print("8 enviado:", [(f, a.get("p_estado"), a.get("p_local"), bool(a.get("p_foto"))) for f, a in rec["rpc"]], "| fotos:", len(rec["fotos"]), "| fila:", pg.evaluate("filaCoq().length"))
    print("  depois:", pg.evaluate("coqLista().map(c => [c.n, c.estado, !!c.porEnviar])"), "| apagar:", pg.inner_text("#cq-desf"))
    pg.evaluate("fecharFolha()"); pg.click("#cq-desf"); pg.wait_for_timeout(300); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2000)
    print("9 apagar último:", [f for f, a in rec["rpc"]][-1], "| ficaram:", pg.evaluate("coqLista().map(c => c.n)"))
    with pg.expect_download() as d: pg.click("#cq-csv")
    caminho = d.value.path(); txt = open(caminho, encoding="utf-8-sig").read()
    print("10 Excel:", d.value.suggested_filename, "|", txt.splitlines()[0], "|", txt.splitlines()[1][:90])
    # rascunho: o Android fecha o Chrome ao abrir a câmara → volta ao formulário
    pg.click("#cq-marcar"); pg.wait_for_selector("#cq-foto-cambtn", timeout=8000); pg.fill("#cq-obs", "perto do portão")
    pg.evaluate("rascGuardar('rascCoq', {camara: true})"); pg.reload(); pg.wait_for_timeout(2500)
    print("11 depois de reabrir:", pg.is_visible("#cq-foto-cambtn"), "| obs:", pg.input_value("#cq-obs") if pg.is_visible("#cq-obs") else "")
    pg.screenshot(path=f"/home/claude/rega-test/coqueiros{LING}.png")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
