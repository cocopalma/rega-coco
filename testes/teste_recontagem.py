# Recontagem das plantas pelos oficiais de M&E (18/10/2026, Valdo): oficial regista sem rede, M&E valida, supervisor só vê o estado, gestor pede.
import json, subprocess, time, sys, copy, os
sys.path.insert(0, "/home/claude/rega-test")
import harvest  # recolhe os textos para a tradução
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8811", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"; OF = "33333333-3333-3333-3333-333333333333"
AREAS = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}]
ST = {"papel": "oficial_me", "rec": [{"id": "44444444-0000-0000-0000-000000000001", "area_id": "PR2-1", "pr": "PR2", "produtor": "Produtor Dois", "comunidade": "Farol", "motivo": "Queimada de 18/10/2026", "queimada_id": "q1",
       "estado": "encaminhada", "pedido_em": "2026-10-18T08:00:00Z", "encaminhada_em": "2026-10-18T09:00:00Z", "oficial_id": OF, "oficial": "Oficial Exemplo", "vivas": None, "mortas": None, "foto_path": None, "lat": None, "lon": None}],
      "chamadas": [], "fotos": []}
def lista():
    out = []
    for r in ST["rec"]:
        r = copy.deepcopy(r)
        if ST["papel"] not in ("me", "oficial_me") and r["estado"] != "validada":
            for k in ("vivas", "mortas", "foto_path", "foto_campo_path", "lat", "lon"): r[k] = None
        if ST["papel"] in ("me", "gestor", "director") and r.get("oficial_id"): r["oficial_entrou"] = False  # v121
        if ST["papel"] in ("me", "oficial_me"): r["telefone"] = "840000001"; r["telefone_confirmar"] = True  # v126
        out.append(r)
    return out
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    corpo = lambda: json.loads(r.post_data or "{}")
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": {"oficial_me": "Oficial Exemplo", "me": "Kathleen Exemplo", "supervisor": "Sup Exemplo", "gestor": "Gestor Exemplo"}[ST["papel"]], "papel": ST["papel"], "activista_id": None})
    if "/rpc/recontagens_lista" in u: return ok(lista())
    if "/rpc/oficiais_me" in u: return ok([{"id": OF, "nome": "Oficial Exemplo", "entrou": False}])
    for f in ("pedir_recontagem2", "encaminhar_recontagem2", "enviar_recontagem2", "enviar_recontagem3", "validar_recontagem2", "cancelar_recontagem"):
        if f"/rpc/{f}(" in u + "(" or f"/rpc/{f}?" in u:
            c = corpo(); ST["chamadas"].append((f, c))
            x = next((y for y in ST["rec"] if y["id"] == c.get("p_id")), None)
            if f in ("enviar_recontagem2", "enviar_recontagem3"): x.update(navuna=c.get("p_navuna"), estado="enviada", vivas=c["p_vivas"], mortas=c["p_mortas"], foto_path=c["p_foto"], foto_campo_path=c["p_foto_campo"], lat=c["p_lat"], lon=c["p_lon"], precisao_m=c["p_precisao"], contada_em=c["p_em"])
            if f == "validar_recontagem2":
                if c["p_validar"]: x.update(estado="validada", validada_em="2026-10-18T15:00:00Z", vivas_antes=60); AREAS[1]["vivas"] = x["vivas"]
                else: x.update(estado="recusada", recusa_motivo=c["p_motivo"])
            if f == "pedir_recontagem2": ST["rec"].append({"id": c["p_id"], "area_id": c["p_area"], "motivo": c["p_motivo"], "estado": "encaminhada" if c["p_oficial"] else "por_encaminhar", "oficial_id": c["p_oficial"], "oficial": "Oficial Exemplo" if c["p_oficial"] else None, "pedido_em": "2026-10-18T16:00:00Z"})
            return route.fulfill(status=204, body="")
    if "/storage/v1/object/sign/recontagem-fotos/" in u: ST.setdefault("sign", []).append(u.split("recontagem-fotos/")[1]); return ok({"signedURL": "/object/sign/recontagem-fotos/x.jpg?token=t"})
    if "/storage/v1/object/sign/" in u and "token=" in u: return route.fulfill(status=200, content_type="image/jpeg", body=open("/home/claude/rega-test/foto_teste.jpg","rb").read())
    if "/storage/v1/object/recontagem-fotos/" in u: ST["fotos"].append(u.split("recontagem-fotos/")[1]); return ok({"Key": "x"})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Farol", "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok([a for a in AREAS if ST["papel"] != "oficial_me" or a["id"] == "PR2-1"])
    if "/rest/v1/registos_rega" in u: return ok([])
    if "/rpc/" in u: return ok([])
    if "/rest/v1/" in u and r.method == "GET": return ok([])
    return route.fulfill(status=201, body="")
erros = []; dialogos = []
def abrir(b, papel):
    ST["papel"] = papel
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6843, "longitude": 40.6333, "accuracy": 6})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    import os
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(f"{papel}: {e}")); pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.goto("http://localhost:8811/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate("modoEntrada('tecnico')"); pg.fill("#l-user", "u"); pg.fill("#l-senha", "senha-teste-1"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2000)
    return ctx, pg
linhas = lambda t, *ks: [l for l in t.split("\n") if any(k.lower() in l.lower() for k in ks)]
with sync_playwright() as p:
    b = p.chromium.launch()
    # 1. oficial
    ctx, pg = abrir(b, "oficial_me")
    print("1 nav:", [x.get_attribute("data-e") for x in pg.locator("#nav button").all() if x.is_visible()], "| aviso:", pg.locator("body > .msg").all_inner_texts()[:1])
    print("1 Hoje:", linhas(pg.inner_text("#hoje"), "recontag", "fazer", "Produtor"))
    pg.click("#hoje .item"); pg.wait_for_timeout(400)
    print("1 ficha:", linhas(pg.inner_text("#folha-c"), "Recontagem", "Motivo", "Telefone", "confirmar"), "| ligar:", pg.locator("#folha-c a[href^='tel:']").first.get_attribute("href") if pg.locator("#folha-c a[href^='tel:']").count() else None)
    pg.click("button[onclick^=ecraRecontar]"); pg.wait_for_selector("#ro-vivas")
    pg.click("#ro-ok"); print("1 vazio:", pg.inner_text("#ro-msg"))
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.fill("#ro-vivas", "45"); pg.fill("#ro-mortas", "15"); pg.set_input_files("#ro-decl", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_timeout(800)
    pg.click("#ro-ok"); pg.wait_for_timeout(300); print("1 sem foto do campo:", pg.inner_text("#ro-msg"), "| rascunho:", pg.evaluate("LS.get('rascRec').fotos"))
    pg.evaluate("ecraRecontar(LS.get('rascRec').rid, LS.get('rascRec'))"); pg.wait_for_timeout(600); print("1 rascunho reaberto: vivas", pg.input_value("#ro-vivas"), "| pré-visualização decl:", pg.is_visible("#ro-decl-prev")); os.environ.get("LING") and print("1 form:", pg.inner_text("#folha-c").replace("\n"," | "))
    pg.set_input_files("#ro-campo", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_timeout(800)
    pg.click("#ro-ok"); pg.wait_for_timeout(300); print("1 sem NAVUNA:", pg.inner_text("#ro-msg"))  # v122
    pg.check("#ro-navuna"); pg.click("#ro-ok"); pg.wait_for_timeout(1200)
    print("1 sem rede: fila", pg.evaluate("LS.get('filaRec',[]).map(x=>[x.vivas,x.mortas,x.foto,x.fotoCampo,x.lat!=null])"), "| chamadas:", len(ST["chamadas"]), "| ficha:", linhas(pg.inner_text("#folha-c"), "telefone", "vivas · mortas"))
    pg.evaluate("fecharFolha()"); pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(500); print("1 Hoje sem rede:", linhas(pg.inner_text("#hoje"), "Enviadas", "telefone"))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    print("1 com rede:", [c[0] for c in ST["chamadas"]], "| fotos:", ST["fotos"], "| fila:", pg.evaluate("LS.get('filaRec',[]).length"), "| estado:", ST["rec"][0]["estado"])
    pg.screenshot(path=f"/home/claude/rega-test/recontagem{os.environ.get('LING','')}.png"); ctx.close()
    # 2. supervisor: só o estado
    ctx, pg = abrir(b, "supervisor")
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300); t = pg.inner_text("#folha-c")
    print("2 supervisor:", linhas(t, "Recontagem", "Estado", "vivas · mortas", "Validar", "Telefone"))
    ctx.close()
    # 3. M&E: recusa e depois valida
    ctx, pg = abrir(b, "me")
    print("3 aviso:", pg.locator("body > .msg").all_inner_texts()[:1])
    pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(1200); print("3 abas:", pg.inner_text("#hoje-abas").replace("\n", " | ")); pg.click("#hoje-abas [data-v=rec]"); pg.wait_for_timeout(800); print("3 Hoje:", linhas(pg.inner_text("#hoje"), "validar", "Recontag"))
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300); print("3 ficha:", linhas(pg.inner_text("#folha-c"), "vivas · mortas", "Local da contagem", "Contada", "Declaração", "Campo", "Validar", "NAVUNA"))
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.click("button[onclick^=ecraRecusarRecontagem]"); pg.fill("#rr-m", "A declaração não se lê"); pg.click("#rr-ok"); pg.wait_for_timeout(800)
    print("3 recusa sem rede: fila", pg.evaluate("LS.get('filaRecG',[]).map(x=>x.op)"), "| ficha:", linhas(pg.inner_text("#folha-c"), "Recusada", "No telefone", "telefone"))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2000); pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300)
    print("3 recusa:", ST["chamadas"][-1], "| ficha:", linhas(pg.inner_text("#folha-c"), "Recusada", "recusa"))
    pg.screenshot(path=f"/home/claude/rega-test/recontagem_me{os.environ.get('LING','')}.png"); ctx.close()
    # 4. oficial refaz
    ctx, pg = abrir(b, "oficial_me")
    print("4 Hoje:", linhas(pg.inner_text("#hoje"), "recusada", "fazer"))
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300); print("4 ficha:", linhas(pg.inner_text("#folha-c"), "Recusada"))
    pg.click("button[onclick^=ecraRecontar]"); pg.fill("#ro-vivas", "47"); pg.fill("#ro-mortas", "13"); pg.click("#ro-ok"); pg.wait_for_timeout(300); print("4 sem fotos:", pg.inner_text("#ro-msg"))
    pg.set_input_files("#ro-campo", "/home/claude/rega-test/foto_teste.jpg"); pg.set_input_files("#ro-decl", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_timeout(800); pg.check("#ro-navuna"); pg.click("#ro-ok"); pg.wait_for_timeout(2000)
    print("4 reenvio:", ST["chamadas"][-1][0], "navuna", ST["chamadas"][-1][1].get("p_navuna"), ST["chamadas"][-1][1]["p_vivas"], "fotos", ST["chamadas"][-1][1]["p_foto"], ST["chamadas"][-1][1]["p_foto_campo"]); ctx.close()
    # 5. M&E valida
    ctx, pg = abrir(b, "me")
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300); pg.click("button[onclick^=validarRecontagem]"); pg.wait_for_timeout(800)
    print("5 valida sem rede: fila", pg.evaluate("LS.get('filaRecG',[]).map(x=>x.op+':'+x.sim+':'+x.vivas)"), "| vivas no telefone:", pg.evaluate("S.areas.find(a=>a.id==='PR2-1').vivas"), "| chamadas validar:", sum(1 for c in ST["chamadas"] if c[0]=="validar_recontagem2"))
    pg.evaluate("S.areas = aplicarPendentes(LS.get('areas',[]).map(a => ({...a, vivas: a.id==='PR2-1' ? 60 : a.vivas})))")   # como se viesse do servidor com o valor antigo
    print("5 dados antigos + fila: vivas", pg.evaluate("S.areas.find(a=>a.id==='PR2-1').vivas"), "| estado", pg.evaluate("recontagemDe('PR2-1').estado"))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500); pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300)
    print("5 valida:", ST["chamadas"][-1], "| vivas no telefone:", pg.evaluate("S.areas.find(a=>a.id==='PR2-1').vivas"), "| ficha:", linhas(pg.inner_text("#folha-c"), "Validada", "vivas · mortas", "antes")); ctx.close()
    ctx, pg = abrir(b, "supervisor")
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300); print("5b supervisor validada:", linhas(pg.inner_text("#folha-c"), "Validada", "vivas · mortas", "Declaração", "Campo"))
    pg.click("button[onclick*=recontagem-fotos]"); pg.wait_for_timeout(800); print("5b foto aberta:", pg.locator("#foto-modal img").count(), ST.get("sign")); ctx.close()
    # teste_vazio: gestor sem recontagens vê o cartão na mesma
    guarda = ST["rec"]; ST["rec"] = []
    ctx, pg = abrir(b, "gestor"); pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(1200); pg.click("#hoje-abas [data-v=rec]"); pg.wait_for_timeout(800)
    print("6a gestor sem recontagens:", [l for l in pg.inner_text("#hoje").split("\n") if "econtag" in l][:3]); ctx.close(); ST["rec"] = guarda
    # teste_varias: gestor pede várias recontagens de uma vez, sem rede, pelo botão do Hoje
    ctx, pg = abrir(b, "gestor"); pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(1200); pg.click("#hoje-abas [data-v=rec]"); pg.wait_for_timeout(800)
    pg.click("button[onclick^=ecraPedirVarias]"); pg.wait_for_selector("#pv-lista input")
    print("6v lista:", [l for l in pg.inner_text("#pv-lista").split("\n") if l.strip()][:5])
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.click("#pv-ok"); print("6v sem campo:", pg.inner_text("#pv-msg"))
    pg.fill("#pv-txt", "Um"); pg.wait_for_timeout(200); pg.check("#pv-lista input[data-id='PR1-1']"); pg.fill("#pv-txt", ""); pg.wait_for_timeout(200)
    print("6v escolhidos:", pg.inner_text("#pv-n"), "| PR2 desactivado (em curso):", pg.is_disabled("#pv-lista input[data-id='PR2-1']"))
    pg.fill("#pv-motivo", "Verificação de rotina"); pg.click("#pv-ok"); pg.wait_for_timeout(600)
    print("6v fila:", pg.evaluate("LS.get('filaRecG',[]).map(x=>x.op+':'+x.area_id)"), "| aviso:", pg.locator("body > .msg").all_inner_texts()[:1])
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2000)
    print("6v enviado:", [c[1]["p_area"] for c in ST["chamadas"] if c[0] == "pedir_recontagem2"]); ctx.close()
    ST["rec"] = [r for r in ST["rec"] if r["area_id"] != "PR1-1"]
    # teste_sup: supervisor pede (sem escolher oficial) e vê o estado no Hoje › Recontagens
    ctx, pg = abrir(b, "supervisor"); pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(1200); pg.click("#hoje-abas [data-v=rec]"); pg.wait_for_timeout(800)
    print("6s Hoje sup:", [l for l in pg.inner_text("#hoje").split("\n") if l.strip()][:8])
    pg.click("button[onclick^=ecraPedirVarias]"); pg.wait_for_selector("#pv-lista input")
    print("6s tem escolha de oficial:", pg.locator("#pv-of").count(), "|", pg.inner_text("#folha-c").split("\n")[-4:-2])
    pg.check("#pv-lista input[data-id='PR1-1']"); pg.fill("#pv-motivo", "Plantas secas"); pg.click("#pv-ok"); pg.wait_for_timeout(2000)
    c = [c for c in ST["chamadas"] if c[0] == "pedir_recontagem2"][-1][1]; print("6s pedido:", c["p_area"], "oficial:", c["p_oficial"])
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(300); print("6s ficha sup:", linhas(pg.inner_text("#folha-c"), "Estado", "Encaminhar", "Mudar o oficial")); ctx.close()
    ST["rec"] = [r for r in ST["rec"] if r["area_id"] != "PR1-1"]
    # 6. gestor: vê a validada e pede outra noutro campo
    ctx, pg = abrir(b, "gestor")
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300); print("6 gestor validada:", linhas(pg.inner_text("#folha-c"), "Validada", "vivas · mortas"))
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(300); pg.click("button[onclick^=ecraPedirRecontagem]"); pg.wait_for_selector("#pr-motivo")
    pg.click("#pr-ok"); print("6 sem motivo:", pg.inner_text("#pr-msg"))
    ctx.set_offline(True); pg.evaluate("window.dispatchEvent(new Event('offline'))")
    pg.fill("#pr-motivo", "Muitas plantas mortas na monitoria"); pg.select_option("#pr-of", OF); pg.click("#pr-ok"); pg.wait_for_timeout(800)
    print("6 pedido sem rede: fila", pg.evaluate("LS.get('filaRecG',[]).map(x=>x.op)"), "| ficha:", linhas(pg.inner_text("#folha-c"), "Estado", "telefone"))
    ctx.set_offline(False); pg.evaluate("window.dispatchEvent(new Event('online'))"); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2000)
    print("6 pedido:", ST["chamadas"][-1][0], ST["chamadas"][-1][1]["p_area"], ST["chamadas"][-1][1]["p_oficial"] == OF, "| ficha:", linhas(pg.inner_text("#folha-c"), "Estado", "pedida")); ctx.close()
    # 7. v121: o M&E vê que o oficial ainda não entrou na app
    ST["rec"][-1].update({"estado": "encaminhada", "oficial_id": OF, "oficial": "Oficial Exemplo"})
    ctx, pg = abrir(b, "me")
    pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(1000); pg.click("#hoje-abas [data-v=rec]"); pg.wait_for_timeout(800)
    print("7 Hoje M&E:", [l for l in pg.inner_text("#hoje").split("\n") if "entrou" in l or "opened" in l or "hajaingia" in l])
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(400); print("7 ficha:", linhas(pg.inner_text("#folha-c"), "entrou", "opened", "hajaingia"))
    pg.click("text=Mudar o oficial"); pg.wait_for_selector("#en-of"); pg.wait_for_timeout(300)
    print("7 encaminhar:", pg.inner_text("#en-of"), "|", linhas(pg.inner_text("#folha-c"), "WhatsApp"))
    pg.click("#en-ok"); pg.wait_for_timeout(500); print("7 depois:", linhas(pg.inner_text("#folha-c"), "encaminhada", "forwarded", "imetumwa", "kumetumwa")); ctx.close()
    print("DIÁLOGOS:", dialogos); print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
