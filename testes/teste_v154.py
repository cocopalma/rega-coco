# Dia sem rega / constrangimento da equipa (v116, 26/10/2026, Valdo). LING=en / sw.
# Regas fora da lista sem motivo (v115, 26/10/2026, Valdo: motivo obrigatório). LING=en / sw.
# v112 (26/10/2026): equipas no Hoje (comunidade do activista), filtro do activista visível no mapa, respostas às sugestões
# (aprovada/recusada, sem rede na Gestão), estado da app junto da sugestão, câmara bloqueada (ajuda + câmara do telefone),
# "Virar a câmara" por deviceId, aviso do navegador da Xiaomi, Sair com aviso, PIN de 5 algarismos. LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8854", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1, A2 = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"
lat0, lon0 = -10.70, 40.47
def ar(i, act, com): return {"id": f"PR{i}-1", "pr": f"PR{i}", "area_n": 1, "comunidade": com, "produtor": f"Produtor {i}", "instaladas": 100, "vivas": 100, "latitude": lat0 + i * 0.001, "longitude": lon0, "activista_id": act, "activa": True,
                             "poligono": [[lon0 - .0003, lat0 + i * .001 - .0003], [lon0 + .0003, lat0 + i * .001 - .0003], [lon0, lat0 + i * .001 + .0003]]}
areas = [ar(1, A1, "Ncumbi"), ar(2, A2, "Olumbe"), ar(3, A1, "Palma")]
SUG = {"sugestoes": [{"id": "s1", "texto": "Peço acesso aos campos dos colegas", "criada_em": "2026-10-26T07:00:00Z", "estado": "nova", "papel": "supervisor", "quem": "Nuro", "ecra": "mapa", "versao": "111",
                      "diag": {"papel": "tecnico", "f_act": A2, "areas": 715}}], "problemas": []}
rec = []; erros = []; dial = []; EST = {'v': []}; MD = {'v': None}
DSR = [{'id': 'd1', 'activista_id': A2, 'activista': 'Macame Juma', 'data': __import__('datetime').date.today().isoformat(), 'motivo': 'sem_agua', 'todo_dia': False, 'descricao': 'Poço secou às 9h', 'quem': 'Nuro', 'meu': False, 'regas': 2}]
SM0 = [{'id': 'r1', 'area_id': 'PR2-1', 'data': '2026-10-26', 'entrada_em': '2026-10-26T07:10:00Z', 'produtor': 'Produtor 2', 'pr': 'PR2', 'comunidade': 'Olumbe', 'dono': 'Macame Juma'}, {'id': 'r2', 'area_id': 'PR3-1', 'data': '2026-10-25', 'entrada_em': None, 'produtor': 'Produtor 3', 'pr': 'PR3', 'comunidade': 'Palma', 'dono': None}]
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
    if "/rpc/regas_sem_motivo" in u: return ok([])
    if "/storage/v1/object/rega-fotos/" in u: rec.append(("foto", u.split("rega-fotos/")[1])); return ok({"Key": "x"})
    if "/rpc/dias_sem_rega_lista" in u: return ok(DSR)
    if "/rpc/minhas_respostas" in u: return ok([{"id": "s9", "texto": "Todos os campos de Olumbe", "estado": "recusada", "nota": "Distribuam os campos pelos 2 activistas com material.", "avaliada_em": "2026-10-26T12:00:00Z"}])
    if "/rpc/sugestoes_lista" in u: return ok(SUG)
    if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
    for f in ["definir_comunidade_activista", "justificar_rega", "gravar_dia_sem_rega3", "gravar_dia_sem_rega2", "gravar_dia_sem_rega", "remover_dia_sem_rega", "enviar_sugestao2", "avaliar_sugestao", "definir_equipa_tamanho", "definir_sem_telefone"]:
        if f"/rpc/{f}" in u: rec.append((f, json.loads(r.post_data or "{}"))); return ok(None)
    if "/rpc/estado_ronda3" in u: return ok(EST["v"])
    if "/rpc/meu_dia" in u: return ok(MD["v"])
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
    pg.goto("http://localhost:8854/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate(f"modoEntrada('{modo}')")
    pg.fill("#l-user", "gelson")
    if modo == "activista": pg.fill("#l-pin", pin)
    else: pg.fill("#l-senha", pin)
    pg.click("#l-entrar")


# v154 (30/10/2026, Valdo): rega a meio por água/avaria deixa o campo por terminar; mudas secas fecha. LING=en / sw
import datetime
SAIDA = """async (x) => { const c = document.createElement('canvas'); c.width = 8; c.height = 8; const b = await new Promise(r => c.toBlob(r, 'image/jpeg'));
   for (const t of ['entrada','rega','saida']) await FOTOS.guardar(x.id + '-' + t, b);
   LS.set('emCurso', { area_id: x.area, entrada_em: new Date(Date.now() - 3600e3).toISOString(), entrada_lat: -10.699, entrada_lon: 40.47, reg_id: x.id, fotos: { entrada: 'x', rega: 'x', saida: 'x' } }); }"""
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "activista"
    ctx, pg = contexto(b); pg.clock.install(time=datetime.datetime(2026, 10, 31, 9, 0))
    entrar(pg, "activista", PIN_OK); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2000); pg.evaluate("fecharFolha()")
    print("0 hoje:", pg.evaluate("hojeISO()"))
    pg.evaluate(SAIDA, {"id": "regA", "area": "PR1-1"}); ctx.set_geolocation({"latitude": lat0 + 0.001, "longitude": lon0, "accuracy": 5})
    pg.evaluate("ecraSaida()"); pg.wait_for_timeout(300)
    print("1 opções:", pg.evaluate("[...document.querySelectorAll('#s-chips .chip')].map(b => b.dataset.k)"))
    pg.fill("#s-plantas", "60"); pg.fill("#s-pessoas", "4"); pg.click("#s-chips .chip[data-k=agua_acabou]"); pg.wait_for_timeout(200)
    print("2 aviso:", pg.inner_text("#s-falta").replace("\n", " | "))
    ctx.set_offline(True); pg.evaluate("marcarSaida()"); pg.wait_for_timeout(4000)
    print("3 fila:", pg.evaluate("(LS.get('fila')||[]).map(x => [x.area_id, x.plantas_regadas, x.campo_fechado])"), "|", pg.inner_text("#folha-c").replace("\n", " | ")[:220])
    print("4 situação PR1-1:", pg.evaluate("situacao(S.areas.find(a => a.id === 'PR1-1')).txt"), "| ronda feitas:", pg.evaluate("[...rondaInfo(S.perfil.activista_id).feitas]"))
    pg.evaluate("fecharFolha(); LS.del('sugestao')"); pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(800)
    print("5 Hoje:", pg.inner_text("#hoje-terminar").replace("\n", " | ") if pg.locator("#hoje-terminar").count() else "(sem cartão)")
    print("5b sugestão (sem sugestão de hoje):", pg.evaluate("sugActual()?.id"))
    pg.screenshot(path=f"/home/claude/rega-test/v154_hoje_{LING}.png", full_page=True)
    pg.click("nav button[data-e=lista]"); pg.select_option("#f-sit", "terminar"); pg.wait_for_timeout(300)
    print("6 filtro:", pg.inner_text("#lista").replace("\n", " | ")[:200])
    # 2.ª visita no mesmo campo: faltam 40; rega 30 e as outras 10 estão mortas → fecha
    pg.evaluate(SAIDA, {"id": "regB", "area": "PR1-1"}); pg.evaluate("ecraSaida()"); pg.wait_for_timeout(300)
    print("7 2.ª visita:", pg.inner_text("#folha-c").split("Pessoas")[0].replace("\n", " | ")[-260:])
    pg.fill("#s-plantas", "30"); pg.fill("#s-pessoas", "4"); pg.click("#s-chips .chip[data-k=mudas_secas]"); pg.wait_for_timeout(200)
    print("8 aviso:", pg.inner_text("#s-falta").replace("\n", " | "))
    pg.evaluate("marcarSaida()"); pg.wait_for_timeout(4000)
    print("9 fila:", pg.evaluate("(LS.get('fila')||[]).map(x => [x.area_id, x.plantas_regadas, x.campo_fechado])"), "| situação:", pg.evaluate("situacao(S.areas.find(a => a.id === 'PR1-1')).txt"))
    # regou todas (100 de 100) noutro campo: fecha
    pg.evaluate("fecharFolha()"); pg.evaluate(SAIDA, {"id": "regC", "area": "PR3-1"}); ctx.set_geolocation({"latitude": lat0 + 0.003, "longitude": lon0, "accuracy": 5})
    pg.evaluate("ecraSaida()"); pg.fill("#s-plantas", "100"); pg.fill("#s-pessoas", "4"); pg.evaluate("marcarSaida()"); pg.wait_for_timeout(4000)
    print("10 fila:", pg.evaluate("(LS.get('fila')||[]).map(x => [x.area_id, x.plantas_regadas, x.campo_fechado])"))
    ctx.close()
    # técnico: estado do servidor com PR2-1 por terminar e «O meu dia»
    PAPEL["v"] = "tecnico"
    EST["v"] = [{"area_id": "PR2-1", "ultima_rega": "2026-10-30", "regas_app": 1, "plantas_app": 45, "ronda_actual": 1, "regada_na_ronda": False, "por_terminar": True, "plantas_ronda": 45, "data_parcial": "2026-10-30"}]
    MD["v"] = {"data": "2026-10-31", "hora_chegada": "06:00", "fechado_em": None, "equipas": [], "alertas": [], "monitoria_hoje": 0, "monitoria_falhas_ontem": 0, "sem_equipa": 0, "por_aprovar": [],
               "por_terminar": [{"area_id": "PR2-1", "produtor": "Produtor 2", "equipa": "Macame Juma", "base": 100, "regadas": 45, "data": "2026-10-30"}]}
    ctx, pg = contexto(b); pg.clock.install(time=datetime.datetime(2026, 10, 31, 9, 0))
    entrar(pg); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2000); pg.evaluate("fecharFolha()")
    print("11 técnico situação PR2-1:", pg.evaluate("situacao(S.areas.find(a => a.id === 'PR2-1')).txt"))
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(500)
    t = pg.inner_text("#meu-dia"); print("12 meu dia:", t.split("7.")[1].split("Para fechar")[0].replace("\n", " | ")[:260] if "7." in t else "(sem secção 7)")
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(500)
    print("13 ficha:", [l for l in pg.inner_text("#folha-c").split("\n") if "⏳" in l or "terminar" in l.lower() or "finish" in l.lower() or "maliz" in l.lower()][:3])
    ctx.close()
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
