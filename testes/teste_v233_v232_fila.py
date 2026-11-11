# Uso: git worktree add <D>/v232 <commit da v232>; mkdir <D>/srv; ln -s <D>/v232 <D>/srv/app; python3 teste_v233_v232_fila.py <D> /home/claude/rega-coco
# Registos gravados na fila pela v232 sem rede são enviados pela v233 depois da actualização (mesmo navegador, mesma origem).
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
D = sys.argv[1]; V233 = sys.argv[2]; NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8877", "--directory", f"{D}/srv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
APP = "http://localhost:8877/app/"
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR3-1", "pr": "PR3", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Tres", "instaladas": 50, "vivas": 48, "latitude": -10.6900, "longitude": 40.6400, "activista_id": ACT, "activista_proposto": None, "wa_ultima": "2026-10-01", "wa_n": 1}]
estado = [{"area_id": a["id"], "ultima_rega": None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False} for a in areas]
rec = {"registos": [], "constr": [], "jornadas": [], "fotos": []}; erros = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    corpo = lambda: (lambda x: x if isinstance(x, list) else [x])(json.loads(r.post_data))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Activista Um", "papel": "activista", "activista_id": ACT})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Um", "comunidade_principal": "Farol"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/estado_ronda" in u: return ok(estado)
    if "/storage/v1/object" in u and r.method in ("POST", "PUT"): rec["fotos"].append(u.split("/")[-1]); return ok({"Key": "x"})
    if "/rest/v1/registos_rega" in u and r.method == "POST": rec["registos"] += corpo(); return route.fulfill(status=201, body="")
    if "/rest/v1/constrangimentos" in u and r.method == "POST": rec["constr"] += corpo(); return route.fulfill(status=201, body="")
    if "/rest/v1/jornadas" in u and r.method == "POST": rec["jornadas"] += corpo(); return route.fulfill(status=201, body="")
    if "/rpc/" in u: return ok([])
    if "/rest/v1/" in u: return ok([])
    return ok({})
falhas = []
def verif(c, t):
    print(("OK  " if c else "FALHA ") + t)
    if not c: falhas.append(t)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(service_workers="block", geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"], viewport={"width": 390, "height": 800})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
    # 1) v232: entra com rede, depois sem rede regista o início do dia e uma rega (com constrangimento e as 3 fotografias)
    pg.goto(APP); pg.wait_for_selector("#l-entrar", state="visible")
    verif(pg.evaluate("versaoApp()") == "232", f"1 a app aberta é a v232 ({pg.evaluate('versaoApp()')})")
    pg.fill("#l-user", "act"); pg.fill("#l-pin", "123987"); pg.click("#l-entrar"); pg.wait_for_selector("text=Início do dia", timeout=10000)
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.fill("#j-pessoas", "4"); pg.click("#folha.on button:has-text('Guardar')"); pg.wait_for_timeout(800)
    pg.evaluate("fecharFolha()")
    pg.evaluate("mudar('lista')"); pg.click(".item[data-id='PR1-1']"); pg.wait_for_selector("#folha.on")
    pg.click("text=Cheguei — marcar entrada"); pg.wait_for_selector("text=Entrada marcada", timeout=15000)
    pg.evaluate("(async()=>{const e=LS.get('emCurso'); e.agua_em=e.entrada_em; LS.set('emCurso',e); for (const t of ['entrada','rega','saida']) await guardarFotoRega(t, new Blob(['x'],{type:'image/jpeg'})); abrirFicha(e.area_id)})()"); pg.wait_for_timeout(400)
    pg.click("text=Terminei — marcar saída"); pg.fill("#s-plantas", "50"); pg.click("#s-chips .chip[data-k=agua_acabou]")
    pg.click("text=Marcar saída e guardar"); pg.wait_for_selector("text=Rega guardada", timeout=15000)
    fila = pg.evaluate("[LS.get('fila',[]).map(x=>[x.area_id,(x.constr||[]).length,Object.keys(x.fotos||{}).length]), LS.get('filaJ',[]).length]")
    verif(fila[0] == [["PR1-1", 1, 3]] and fila[1] == 1, f"2 v232 sem rede: 1 rega (1 constrangimento, 3 fotografias) e 1 início do dia na fila ({fila})")
    verif(not rec["registos"] and not rec["jornadas"], "2b nada chegou ao servidor enquanto sem rede")
    # 2) actualiza para a v233 (mesmo navegador, mesma origem) e volta a rede
    os.remove(f"{D}/srv/app"); os.symlink(V233, f"{D}/srv/app")
    ctx.set_offline(False); pg.reload(); pg.wait_for_selector("#app", state="visible", timeout=15000)
    verif(pg.evaluate("versaoApp()") == "233", f"3 depois de recarregar a app é a v233 ({pg.evaluate('versaoApp()')})")
    pg.evaluate("sincronizar(true)")
    for _ in range(20):
        if not pg.evaluate("LS.get('fila',[]).length + LS.get('filaJ',[]).length"): break
        pg.wait_for_timeout(500)
    r = next((x for x in rec["registos"] if x.get("area_id") == "PR1-1"), None)
    verif(r is not None and r.get("plantas_regadas") == 50, f"4 a rega gravada pela v232 chegou ao servidor ({r and r.get('plantas_regadas')})")
    verif(r is not None and all(r.get('foto_' + t) for t in ('entrada', 'rega', 'saida')) and len(rec["fotos"]) >= 3, f"4b com as 3 fotografias ({len(rec['fotos'])} enviadas)")
    verif(r is not None and "_recusa" not in r and "constr" not in r and "fotos" not in r, "4c sem campos internos na linha enviada")
    verif(any(c.get("tipo") == "agua_acabou" and c.get("registo_id") == (r or {}).get("id") for c in rec["constr"]), "4d o constrangimento chegou")
    verif(rec["jornadas"] and rec["jornadas"][0].get("pessoas") == 4, f"4e o início do dia chegou ({rec['jornadas'][:1]})")
    left = pg.evaluate("[LS.get('fila',[]).length, LS.get('filaJ',[]).length]")
    verif(left == [0, 0], f"5 filas vazias no telefone ({left})")
    cls = pg.get_attribute("#h-sync", "class") or ""
    verif("recusa" not in cls, f"5b botão do topo sem recusas ({cls})")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
