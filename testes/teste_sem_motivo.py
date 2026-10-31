# Regas fora da lista sem motivo (v115, 26/10/2026, Valdo: motivo obrigatório). LING=en / sw.
# v112 (26/10/2026): equipas no Hoje (comunidade do activista), filtro do activista visível no mapa, respostas às sugestões
# (aprovada/recusada, sem rede na Gestão), estado da app junto da sugestão, câmara bloqueada (ajuda + câmara do telefone),
# "Virar a câmara" por deviceId, aviso do navegador da Xiaomi, Sair com aviso, PIN de 5 algarismos. LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8833", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1, A2 = "11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"
lat0, lon0 = -10.70, 40.47
def ar(i, act, com): return {"id": f"PR{i}-1", "pr": f"PR{i}", "area_n": 1, "comunidade": com, "produtor": f"Produtor {i}", "instaladas": 100, "vivas": 100, "latitude": lat0 + i * 0.001, "longitude": lon0, "activista_id": act, "activa": True,
                             "poligono": [[lon0 - .0003, lat0 + i * .001 - .0003], [lon0 + .0003, lat0 + i * .001 - .0003], [lon0, lat0 + i * .001 + .0003]]}
areas = [ar(1, A1, "Ncumbi"), ar(2, A2, "Olumbe"), ar(3, A1, "Palma")]
SUG = {"sugestoes": [{"id": "s1", "texto": "Peço acesso aos campos dos colegas", "criada_em": "2026-10-26T07:00:00Z", "estado": "nova", "papel": "supervisor", "quem": "Nuro", "ecra": "mapa", "versao": "111",
                      "diag": {"papel": "tecnico", "f_act": A2, "areas": 715}}], "problemas": []}
rec = []; erros = []; dial = []
SM = [{'id': 'r1', 'area_id': 'PR2-1', 'data': '2026-10-26', 'entrada_em': '2026-10-26T07:10:00Z', 'produtor': 'Produtor 2', 'pr': 'PR2', 'comunidade': 'Olumbe', 'dono': 'Macame Juma'}, {'id': 'r2', 'area_id': 'PR3-1', 'data': '2026-10-25', 'entrada_em': None, 'produtor': 'Produtor 3', 'pr': 'PR3', 'comunidade': 'Palma', 'dono': None}]
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
    if "/rpc/regas_sem_motivo" in u: return ok(SM)
    if "/rpc/minhas_respostas" in u: return ok([{"id": "s9", "texto": "Todos os campos de Olumbe", "estado": "recusada", "nota": "Distribuam os campos pelos 2 activistas com material.", "avaliada_em": "2026-10-26T12:00:00Z"}])
    if "/rpc/sugestoes_lista" in u: return ok(SUG)
    if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
    for f in ["definir_comunidade_activista", "justificar_rega", "enviar_sugestao2", "avaliar_sugestao", "definir_equipa_tamanho", "definir_sem_telefone"]:
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
    pg.goto("http://localhost:8833/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate(f"modoEntrada('{modo}')")
    pg.fill("#l-user", "gelson")
    if modo == "activista": pg.fill("#l-pin", pin)
    else: pg.fill("#l-senha", pin)
    pg.click("#l-entrar")

# v115: regas fora da lista sem motivo (activista). LING=en / sw
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "activista"
    ctx, pg = contexto(b); entrar(pg, "activista", PIN_OK); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
    print("1 faixa:", pg.inner_text("#sem-motivo") if pg.locator("#sem-motivo").count() else "(sem faixa)")
    pg.evaluate("fecharFolha()"); pg.evaluate("marcarEntrada('PR1-1')"); pg.wait_for_timeout(400); print("1b entrar noutro campo →", pg.inner_text("#folha-c h2"))
    print("2 ecrã aberto:", pg.is_visible("#folha"), "| ✕ escondido:", not pg.is_visible("#folha-x"))
    print("  ", pg.inner_text("#folha-c").replace("\n", " | ")[:400])
    pg.screenshot(path=f"/home/claude/rega-test/v115_motivo{LING}.png")
    pg.fill("#sm-0", "Campo do colega sem material"); pg.click("#folha-c .btn"); pg.wait_for_timeout(200); print("3 só um →", dial[-1:])
    ctx.set_offline(True); pg.fill("#sm-1", "Pedido do técnico"); pg.click("#folha-c .btn"); pg.wait_for_timeout(400)
    print("4 fila:", pg.evaluate("LS.get('filaAlt', []).map(x => x.tipo + ':' + x.motivo)"), "| faixa:", pg.locator("#sem-motivo").count(), "| folha:", pg.is_visible("#folha"))
    ctx.set_offline(False); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2000)
    print("5 enviado:", [x for x in rec if x[0] == "justificar_rega"])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
