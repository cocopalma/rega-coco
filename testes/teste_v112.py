# v112 (26/10/2026): equipas no Hoje (comunidade do activista), filtro do activista visível no mapa, respostas às sugestões
# (aprovada/recusada, sem rede na Gestão), estado da app junto da sugestão, câmara bloqueada (ajuda + câmara do telefone),
# "Virar a câmara" por deviceId, aviso do navegador da Xiaomi, Sair com aviso, PIN de 5 algarismos. LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8831", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1, A2 = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"
lat0, lon0 = -10.70, 40.47
def ar(i, act, com): return {"id": f"PR{i}-1", "pr": f"PR{i}", "area_n": 1, "comunidade": com, "produtor": f"Produtor {i}", "instaladas": 100, "vivas": 100, "latitude": lat0 + i * 0.001, "longitude": lon0, "activista_id": act, "activa": True,
                             "poligono": [[lon0 - .0003, lat0 + i * .001 - .0003], [lon0 + .0003, lat0 + i * .001 - .0003], [lon0, lat0 + i * .001 + .0003]]}
areas = [ar(1, A1, "Ncumbi"), ar(2, A2, "Olumbe"), ar(3, A1, "Palma")]
SUG = {"sugestoes": [{"id": "s1", "texto": "Peço acesso aos campos dos colegas", "criada_em": "2026-10-26T07:00:00Z", "estado": "nova", "papel": "supervisor", "quem": "Nuro", "ecra": "mapa", "versao": "111",
                      "diag": {"papel": "tecnico", "f_act": A2, "areas": 715}}], "problemas": []}
rec = []; erros = []; dial = []
PAPEL = {"v": "tecnico"}; PIN_OK = "012345"
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        body = json.loads(r.post_data or "{}")
        if PAPEL["v"] == "activista" and body.get("password") != PIN_OK: return ok({"error": "invalid_grant", "error_description": "Invalid login credentials", "msg": "Invalid login credentials", "code": 400, "error_code": "invalid_credentials"}, 400)
        rec.append(("login", body.get("password")))
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "s@rega-coco.example.com"}})
    if "/auth/v1/logout" in u: return route.fulfill(status=204, body="")
    if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Gelson Teste", "papel": PAPEL["v"], "activista_id": A1 if PAPEL["v"] == "activista" else None, "gere_acessos": True})
    if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Sitambur Issa", "comunidade_principal": "Ncumbi", "supervisor": "Nuro", "tecnico": "Gelson Teste", "activo": True, "equipa_tamanho": None},
                                              {"id": A2, "nome": "Macame Juma", "comunidade_principal": "Olumbe", "supervisor": "Nuro", "tecnico": "Gelson Teste", "activo": True, "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/lista_comunidades" in u: return ok(["Ncumbi", "Olumbe", "Palma"])
    if "/rpc/meus_activistas" in u: return ok([A1, A2])
    if "/rpc/minhas_comunidades" in u: return ok(["Ncumbi", "Olumbe"])
    if "/rpc/minhas_respostas" in u: return ok([{"id": "s9", "texto": "Todos os campos de Olumbe", "estado": "recusada", "nota": "Distribuam os campos pelos 2 activistas com material.", "avaliada_em": "2026-10-26T12:00:00Z"}])
    if "/rpc/sugestoes_lista" in u: return ok(SUG)
    if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
    for f in ["definir_comunidade_activista", "enviar_sugestao2", "avaliar_sugestao", "definir_equipa_tamanho", "definir_sem_telefone"]:
        if f"/rpc/{f}" in u: rec.append((f, json.loads(r.post_data or "{}"))); return ok(None)
    if "/rest/v1/registos_rega" in u and r.method == "HEAD": return route.fulfill(status=200, headers={"content-range": "0-0/3"}, body="")
    return ok([])
CAM = r"""
(() => {
  const fazer = (id) => { const c = document.createElement('canvas'); c.width = 64; c.height = 48; c.getContext('2d').fillRect(0,0,64,48); const st = c.captureStream(5);
    const tr = st.getVideoTracks()[0]; tr.getSettings = () => ({ deviceId: id }); window.__ultima = id; return st; };
  window.__modo = 'ok';
  navigator.mediaDevices.getUserMedia = async (c) => {
    if (window.__modo === 'negado') { const e = new Error('Permission denied'); e.name = 'NotAllowedError'; throw e; }
    const v = c.video || {};
    if (v.deviceId && v.deviceId.exact) return fazer(v.deviceId.exact);
    return fazer('tras');                                   // ignora facingMode (como o telefone do Razaque)
  };
  navigator.mediaDevices.enumerateDevices = async () => [{ kind: 'videoinput', deviceId: 'tras', label: 'camera2 0, facing back' }, { kind: 'videoinput', deviceId: 'frente', label: 'camera2 1, facing front' }];
  window.__cliques = 0; const ck = HTMLInputElement.prototype.click; HTMLInputElement.prototype.click = function () { if (this.type === 'file') { window.__cliques++; return; } return ck.call(this); };
})();
"""
def contexto(b, ua=None):
    k = dict(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": lat0, "longitude": lon0, "accuracy": 5})
    if ua: k["user_agent"] = ua
    ctx = b.new_context(**k)
    for pat, f, ct in [("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", f"{NM}/leaflet/dist/leaflet.js", "application/javascript"), ("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", f"{NM}/leaflet/dist/leaflet.css", "text/css")]:
        ctx.route(pat, (lambda f, ct: (lambda r: r.fulfill(path=f, content_type=ct)))(f, ct))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    ctx.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING); ctx.add_init_script(CAM)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    return ctx, pg
def entrar(pg, modo="tecnico", pin="segredo12"):
    pg.goto("http://localhost:8831/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate(f"modoEntrada('{modo}')")
    pg.fill("#l-user", "gelson")
    if modo == "activista": pg.fill("#l-pin", pin)
    else: pg.fill("#l-senha", pin)
    pg.click("#l-entrar")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx, pg = contexto(b)
    entrar(pg); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    # 1 equipas no Hoje e comunidade do activista
    pg.evaluate("mudar('hoje')"); pg.wait_for_timeout(1000)
    c = pg.locator("#hoje details:has-text('👥')")
    print("1 cartão equipas:", c.count(), c.inner_text().replace("\n", " | ")[:200] if c.count() else "")
    c.locator("summary").click(); pg.wait_for_timeout(200); print("   aberto:", c.inner_text().replace("\n", " | ")[:300])
    c.locator("button").first.click(); pg.wait_for_timeout(300)
    print("2 ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:300])
    pg.select_option("#t-com", "Palma"); pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(1500)
    print("3 enviado:", [x for x in rec if x[0] == "definir_comunidade_activista"], "| no telefone:", pg.evaluate(f"S.activistas.find(t => t.id === '{A1}').comunidade_principal"), "| fila:", pg.evaluate("LS.get('filaAlt', []).length"), "| alertas:", dial[-1:] )
    # 4 respostas no Hoje
    pg.evaluate("carregarSugFeitas()"); pg.wait_for_timeout(500); pg.evaluate("desenharHoje()"); pg.wait_for_timeout(800)
    print("4 resposta:", pg.inner_text("#hoje-sugf").replace("\n", " | ") if pg.locator("#hoje-sugf").count() else "(sem cartão)")
    if pg.locator("#hoje-sugf").count(): pg.click("#hoje-sugf button"); pg.wait_for_timeout(200); print("   depois de OK:", pg.locator("#hoje-sugf").count(), pg.evaluate("LS.get('sugVistas')"))
    # 5 filtro do activista no mapa
    pg.evaluate("mudar('mapa')"); pg.evaluate(f"$('#f-act').value = '{A2}'; desenharMapa()"); pg.wait_for_timeout(300)
    print("5 mapa filtrado:", pg.inner_text("#ronda-info").replace("\n", " ") if pg.is_visible("#ronda-info") else "(nada)")
    pg.screenshot(path=f"/home/claude/rega-test/v112_filtro{LING}.png")
    pg.click("#ronda-info button"); pg.wait_for_timeout(300); print("   depois de Mostrar todos:", pg.is_visible("#ronda-info"), pg.input_value("#f-act") or "(todos)")
    # 6 sugestão com o estado da app
    pg.evaluate("ecraSugestao()"); pg.fill("#sg-txt", "O polígono não aparece"); pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(1500)
    s = [x for x in rec if x[0] == "enviar_sugestao2"]
    print("6 sugestão:", s[-1][1].get("p_diag") if s else "(não enviada)")
    # 7 câmara bloqueada
    pg.evaluate("window.__modo = 'negado'; ecraSugestao()"); pg.wait_for_timeout(200); pg.click("#sg-foto-cambtn"); pg.wait_for_timeout(400)
    print("7 ajuda câmara:", pg.inner_text("#perm-ov").replace("\n", " | ")[:400] if pg.locator("#perm-ov").count() else "(sem ajuda)", "| formulário aberto:", pg.locator("#sg-txt").count())
    pg.locator("#perm-ov").screenshot(path=f"/home/claude/rega-test/v112_camara{LING}.png") if pg.locator("#perm-ov").count() else None
    if pg.locator("#perm-ov").count(): pg.click("#perm-cont"); pg.wait_for_timeout(200)
    print("   câmara do telefone aberta:", pg.evaluate("window.__cliques"))
    pg.click("#sg-foto-cambtn"); pg.wait_for_timeout(300); print("   2.ª vez (sem ajuda, câmara do telefone):", pg.locator("#perm-ov").count(), pg.evaluate("window.__cliques"))
    pg.evaluate("fecharFolha()")
    # 8 virar a câmara
    pg.evaluate("window.__modo = 'ok'; ecraSugestao()"); pg.wait_for_timeout(200); pg.click("#sg-foto-cambtn"); pg.wait_for_timeout(500)
    print("8 câmara aberta:", pg.locator("#cam-ov").count(), "| antes:", pg.evaluate("window.__ultima"))
    pg.click("#cam-virar"); pg.wait_for_timeout(1200); print("   depois de virar:", pg.evaluate("window.__ultima"), "| espelho:", pg.evaluate("document.querySelector('#cam-ov video').style.transform"))
    pg.click("#cam-virar"); pg.wait_for_timeout(1200); print("   virar de novo:", pg.evaluate("window.__ultima"))
    pg.click("#cam-x"); pg.evaluate("fecharFolha()")
    # 9 Gestão sem rede (gestor)
    PAPEL["v"] = "gestor"; ctx.close()
    ctx, pg = contexto(b); entrar(pg, "escritorio") if False else None
    pg.goto("http://localhost:8831/"); pg.wait_for_selector("#l-entrar", state="visible"); pg.evaluate("modoEntrada('escritorio')"); pg.fill("#le-user", "valdo"); pg.fill("#le-senha", "segredo12"); pg.click("#le-entrar")
    pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    pg.evaluate("mudar('gestao')"); pg.wait_for_timeout(1500)
    print("9 gestão html:", pg.evaluate("S.perfil"), pg.inner_text("#e-gestao")[:200]); print("9 gestão:", pg.inner_text("#g-sug").replace("\n", " | ")[:300])
    ctx.set_offline(True); pg.wait_for_timeout(200)
    pg.evaluate("avaliarSugestao('s1', 'recusada')"); pg.wait_for_timeout(300)
    print("   ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:250])
    pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(200); print("   sem texto →", dial[-1:])
    pg.fill("#sf-nota", "Distribuam os campos pelos 2 activistas com material."); pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(400)
    print("   fila:", pg.evaluate("LS.get('filaAlt', []).map(x => x.tipo + ':' + x.estado)"), "|", pg.inner_text("#g-sug").replace("\n", " | ")[:250])
    pg.evaluate("S.sug = null; desenharSugestoes('todas'); cartaoSugestoes()"); pg.wait_for_timeout(800); pg.evaluate("desenharSugestoes('todas')")
    print("   sem rede depois de reabrir:", pg.inner_text("#g-sug").replace("\n", " | ")[:300])
    ctx.set_offline(False); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2000)
    print("   enviado:", [x for x in rec if x[0] == "avaliar_sugestao"], "| fila:", pg.evaluate("LS.get('filaAlt', []).length"))
    # 10 sair com aviso
    dial.clear(); pg.evaluate("sair()"); pg.wait_for_timeout(800); print("10 sair:", dial)
    ctx.close()
    # 11 activista: PIN com 5 algarismos e navegador da Xiaomi
    PAPEL["v"] = "activista"; rec.clear()
    ctx, pg = contexto(b, ua="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36 XiaoMi/MiuiBrowser/18.6.70913")
    entrar(pg, "activista", "12345"); pg.wait_for_selector("#app", state="visible", timeout=15000); pg.wait_for_timeout(1200)
    print("11 PIN 5 → logins:", rec, "| entrou:", pg.is_visible("#app"))
    print("12 Xiaomi:", pg.inner_text("#nav-xiaomi") if pg.locator("#nav-xiaomi").count() else "(sem aviso)")
    pg.screenshot(path=f"/home/claude/rega-test/v112_xiaomi{LING}.png")
    dial.clear(); pg.evaluate("sair()"); pg.wait_for_timeout(500); print("13 sair activista:", dial)
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
