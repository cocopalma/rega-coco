# Dia sem rega / constrangimento da equipa (v116, 26/10/2026, Valdo). LING=en / sw.
# Regas fora da lista sem motivo (v115, 26/10/2026, Valdo: motivo obrigatório). LING=en / sw.
# v112 (26/10/2026): equipas no Hoje (comunidade do activista), filtro do activista visível no mapa, respostas às sugestões
# (aprovada/recusada, sem rede na Gestão), estado da app junto da sugestão, câmara bloqueada (ajuda + câmara do telefone),
# "Virar a câmara" por deviceId, aviso do navegador da Xiaomi, Sair com aviso, PIN de 5 algarismos. LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8842", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1, A2 = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"
lat0, lon0 = -10.70, 40.47
def ar(i, act, com): return {"id": f"PR{i}-1", "pr": f"PR{i}", "area_n": 1, "comunidade": com, "produtor": f"Produtor {i}", "instaladas": 100, "vivas": 100, "latitude": lat0 + i * 0.001, "longitude": lon0, "activista_id": act, "activa": True,
                             "poligono": [[lon0 - .0003, lat0 + i * .001 - .0003], [lon0 + .0003, lat0 + i * .001 - .0003], [lon0, lat0 + i * .001 + .0003]]}
areas = [ar(1, A1, "Ncumbi"), ar(2, A2, "Olumbe"), ar(3, A1, "Palma")]
SUG = {"sugestoes": [{"id": "s1", "texto": "Peço acesso aos campos dos colegas", "criada_em": "2026-10-26T07:00:00Z", "estado": "nova", "papel": "supervisor", "quem": "Nuro", "ecra": "mapa", "versao": "111",
                      "diag": {"papel": "tecnico", "f_act": A2, "areas": 715}}], "problemas": []}
rec = []; erros = []; dial = []
DSR = [{'id': 'd1', 'activista_id': A2, 'activista': 'Macame Juma', 'data': __import__('datetime').date.today().isoformat(), 'motivo': 'sem_agua', 'todo_dia': False, 'descricao': 'Poço secou às 9h', 'quem': 'Nuro', 'meu': False, 'regas': 2}]
SM0 = [{'id': 'r1', 'area_id': 'PR2-1', 'data': '2026-10-26', 'entrada_em': '2026-10-26T07:10:00Z', 'produtor': 'Produtor 2', 'pr': 'PR2', 'comunidade': 'Olumbe', 'dono': 'Macame Juma'}, {'id': 'r2', 'area_id': 'PR3-1', 'data': '2026-10-25', 'entrada_em': None, 'produtor': 'Produtor 3', 'pr': 'PR3', 'comunidade': 'Palma', 'dono': None}]
PAPEL = {"v": "tecnico"}; PIN_OK = "012345"
PEDIDOS = {"n": 0, "contar": False, "urls": []}
def mock(route):
    r = route.request; u = r.url
    if PEDIDOS["contar"]: PEDIDOS["n"] += 1; PEDIDOS["urls"].append(r.method + " " + u.split(".co")[1][:80])
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
    if "/rpc/regas_sem_motivo" in u: return ok([])
    if "/storage/v1/object/sugestoes-fotos/" in u: rec.append(("sugfoto", u.split("sugestoes-fotos/")[1], r.headers.get("authorization", "")[:12])); return ok({"Key": "x"})
    if "/storage/v1/object/rega-fotos/" in u: rec.append(("foto", u.split("rega-fotos/")[1])); return ok({"Key": "x"})
    if "/rpc/dias_sem_rega_lista" in u: return ok(DSR)
    if "/rpc/minhas_respostas" in u: return ok([{"id": "s9", "texto": "Todos os campos de Olumbe", "estado": "recusada", "nota": "Distribuam os campos pelos 2 activistas com material.", "avaliada_em": "2026-10-26T12:00:00Z"}])
    if "/rpc/sugestoes_lista" in u: return ok(SUG)
    if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
    for f in ["definir_comunidade_activista", "justificar_rega", "gravar_dia_sem_rega3", "gravar_dia_sem_rega2", "gravar_dia_sem_rega", "remover_dia_sem_rega", "enviar_sugestao2", "avaliar_sugestao", "definir_equipa_tamanho", "definir_sem_telefone"]:
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
    if os.environ.get("SEMGPS") == "1": k = dict(viewport={"width": 390, "height": 844}, geolocation={"latitude": -25.9655, "longitude": 32.5832, "accuracy": 30})   # v150: em Maputo e sem autorização de localização
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
    pg.goto("http://localhost:8842/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate(f"modoEntrada('{modo}')")
    pg.fill("#l-user", "gelson")
    if modo == "activista": pg.fill("#l-pin", pin)
    else: pg.fill("#l-senha", pin)
    pg.click("#l-entrar")

# Modo apresentação (v124, 28/10/2026, Valdo). LING=en / sw. SEMGPS=1 (v150): sem localização, GPS simulado em Palma
def txt(pg, sel): return pg.inner_text(sel).replace("\n", " | ")
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
    real = pg.evaluate("localStorage.getItem('sb-fgzdqnvobgfzjetbbxcm-auth-token')")
    pg.evaluate("fecharFolha(); mudar('gestao')"); pg.wait_for_timeout(800)
    print("1 cartão:", txt(pg, "#gestao-demo")[:260])
    PEDIDOS["contar"] = True
    pg.click("#gestao-demo .item >> nth=0"); pg.wait_for_selector("#demo-faixa", state="visible", timeout=15000); pg.wait_for_timeout(2500)
    print("2 activista:", txt(pg, "#demo-faixa"), "|", pg.inner_text("#h-nome"), "| campos:", pg.evaluate("S.areas.length"), "| folha:", pg.inner_text("#folha-c")[:60].replace("\n", " ") if pg.is_visible("#folha.on") else "-")
    if pg.is_visible("#folha.on") and pg.locator("#j-pessoas").count(): pg.fill("#j-pessoas", "6"); pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(500)
    if pg.is_visible("#folha.on") and pg.locator("#j-lista").count():   # v135: pessoas da equipa por nome
        for c in pg.locator("#j-lista input").all(): c.check()
        print("   início do dia com nomes:", pg.inner_text("#j-total")); pg.click("#folha-c .btn >> nth=-1"); pg.wait_for_timeout(500)
    pg.evaluate("fecharFolha()"); pg.click("nav button[data-e=lista]"); pg.wait_for_timeout(300)
    print("3 lista:", pg.locator("#lista .item").count(), "|", pg.locator("#lista .item .nome").all_inner_texts()[:5])
    pg.click(".item[data-id='PR900101-1']"); pg.wait_for_selector("#folha.on"); print("   centro:", pg.evaluate("[DEMO.lat, DEMO.lon]"), "| pos:", pg.evaluate("S.pos")); pg.click("text=Cheguei — marcar entrada"); pg.wait_for_selector("text=Entrada marcada", timeout=30000)
    pg.evaluate("(async()=>{for (const t of ['entrada','rega','saida']) await guardarFotoRega(t, new Blob(['x'],{type:'image/jpeg'})); abrirFicha(LS.get('emCurso').area_id)})()"); pg.wait_for_timeout(400)
    pg.click("text=Terminei — marcar saída"); pg.fill("#s-plantas", "150"); pg.click("#s-chips .chip[data-k=mudas_secas]"); pg.click("text=Marcar saída e guardar"); pg.wait_for_selector("text=Rega guardada", timeout=30000); pg.wait_for_timeout(2500)
    print("4 rega:", pg.inner_text("#folha-c")[:200].replace("\n", " | "), "| fila:", pg.evaluate("(LS.get('fila')||[]).length"), "| base:", pg.evaluate("JSON.parse(sessionStorage.getItem('rega.demo.db')).registos.length"))
    pg.evaluate("fecharFolha()")
    for papel in ["tecnico", "oficial_me", "me", "cliente"]:
        pg.evaluate(f"entrarDemo('{papel}')"); pg.wait_for_selector("#demo-faixa", state="visible", timeout=15000); pg.wait_for_timeout(3000)
        if pg.is_visible("#folha.on"): pg.evaluate("fecharFolha()")
        pg.evaluate("mudar(document.querySelector('#nav button[data-e=hoje]').style.display === 'none' ? 'painel' : 'hoje')"); pg.wait_for_timeout(2500)
        hoje = pg.inner_text("#hoje")[:300].replace("\n", " | ") if pg.is_visible("#hoje") else "-"
        print(f"5 {papel}:", pg.inner_text("#h-nome"), "| campos:", pg.evaluate("S.areas.length"), "| nav:", [x.inner_text() for x in pg.locator("#nav button").all() if x.is_visible()], "| hoje:", hoje)
        if papel == "me":
            pg.evaluate("vistaHoje('rec')"); pg.wait_for_timeout(800); print("   M&E recontagens:", pg.inner_text("#hoje")[:400].replace("\n", " | "))
            rid = pg.evaluate("recontagens().find(r => r.estado === 'enviada').id"); pg.evaluate(f"validarRecontagem('{rid}', true)"); pg.wait_for_timeout(2500)
            print("   validada:", pg.evaluate("JSON.parse(sessionStorage.getItem('rega.demo.db')).recontagens.map(r => r.estado)"))
        if papel in ("tecnico", "cliente"):
            pg.evaluate("mudar('painel')"); pg.wait_for_timeout(5000)
            fr = pg.frame_locator("#e-painel iframe") if pg.locator("#e-painel iframe").count() else None
            if fr: print("   painel:", fr.locator("#kpis").inner_text(timeout=15000)[:300].replace("\n", " | "), "| monitoria escondida:", fr.locator("#s-mon").is_hidden())
            pg.screenshot(path=f"/home/claude/rega-test/demo_painel_{papel}.png")
    # sugestão feita na apresentação: vai para o servidor verdadeiro, com a conta do gestor
    rec.clear(); pg.evaluate("ecraSugestao()"); pg.wait_for_timeout(400); pg.fill("#folha-c textarea", "Sugestão feita na apresentação")
    pg.set_input_files("#folha-c input[type=file] >> nth=0", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_timeout(800)
    pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(3000)
    print("5b sugestão:", [(x[0], x[1] if x[0] == "sugfoto" else {k: x[1].get(k) for k in ("p_ecra", "p_foto", "p_texto")}) for x in rec if x[0] in ("sugfoto", "enviar_sugestao2")], "| fila:", pg.evaluate("(LS.get('filaSug')||[]).length"))
    pg.evaluate("mudar('mapa')"); pg.wait_for_timeout(800); pg.screenshot(path=f"/home/claude/rega-test/demo_mapa.png")
    print("6 pedidos ao servidor durante a apresentação:", PEDIDOS["n"], PEDIDOS["urls"][:5])
    pg.evaluate("DEMO.terminar()"); pg.wait_for_selector("#app", state="visible", timeout=15000); pg.wait_for_timeout(2500)
    print("7 voltou:", pg.inner_text("#h-nome"), "| faixa:", pg.is_visible("#demo-faixa"), "| chaves demo:", pg.evaluate("Object.keys(localStorage).filter(k => k.startsWith('demo:')).length"),
          "| sessão real igual:", pg.evaluate("localStorage.getItem('sb-fgzdqnvobgfzjetbbxcm-auth-token')") == real, "| db:", pg.evaluate("sessionStorage.getItem('rega.demo.db')"))
    ctx.close()
    print("DIÁLOGOS:", dial[-5:]); print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
