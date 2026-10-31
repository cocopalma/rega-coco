# Dia sem rega / constrangimento da equipa (v116, 26/10/2026, Valdo). LING=en / sw.
# Regas fora da lista sem motivo (v115, 26/10/2026, Valdo: motivo obrigatório). LING=en / sw.
# v112 (26/10/2026): equipas no Hoje (comunidade do activista), filtro do activista visível no mapa, respostas às sugestões
# (aprovada/recusada, sem rede na Gestão), estado da app junto da sugestão, câmara bloqueada (ajuda + câmara do telefone),
# "Virar a câmara" por deviceId, aviso do navegador da Xiaomi, Sair com aviso, PIN de 5 algarismos. LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8836", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
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
    pg.goto("http://localhost:8836/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.evaluate(f"modoEntrada('{modo}')")
    pg.fill("#l-user", "gelson")
    if modo == "activista": pg.fill("#l-pin", pin)
    else: pg.fill("#l-senha", pin)
    pg.click("#l-entrar")

# v118 (27/10/2026): "Não houve rega neste campo" (entrada feita, sem rega), dia sem rega até 7 dias, saída com o motivo no ecrã. LING=en / sw
import datetime
with sync_playwright() as p:
    b = p.chromium.launch()
    for papel in ["activista", "tecnico"]:
        PAPEL["v"] = papel; rec.clear(); dial.clear()
        ctx, pg = contexto(b); entrar(pg, "activista" if papel == "activista" else "tecnico", PIN_OK if papel == "activista" else "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2000)
        pg.evaluate("fecharFolha()")
        pg.evaluate("""async () => { const c = document.createElement('canvas'); c.width = 8; c.height = 8; const b = await new Promise(r => c.toBlob(r, 'image/jpeg'));
           await FOTOS.guardar('reg1-entrada', b); LS.set('emCurso', { area_id: 'PR1-1', entrada_em: new Date(Date.now() - 3600e3).toISOString(), entrada_lat: -10.699, entrada_lon: 40.47, reg_id: 'reg1', fotos: { entrada: new Date().toISOString() } }); }""")
        pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(400)
        print(f"[{papel}] 1 ficha em curso:", [t for t in pg.locator("#folha-c .btn").all_inner_texts()])
        if papel == "activista":   # v119: entrada no campo errado
            pg.evaluate("entradaEngano()"); pg.wait_for_timeout(500)
            print(f"[{papel}] 1b engano:", dial[-1:], "| em curso:", pg.evaluate("LS.get('emCurso')"), "|", pg.inner_text("#folha-c")[:60].replace("\n", " | "), "| problema:", pg.evaluate("LS.get('problemas', []).filter(x => x.tipo === 'entrada_anulada').map(x => x.mensagem)"))
            pg.evaluate("""async () => { const c = document.createElement('canvas'); c.width = 8; c.height = 8; const b = await new Promise(r => c.toBlob(r, 'image/jpeg'));
               await FOTOS.guardar('reg1-entrada', b); LS.set('emCurso', { area_id: 'PR1-1', entrada_em: new Date(Date.now() - 3600e3 + 60e3).toISOString(), entrada_lat: -10.699, entrada_lon: 40.47, reg_id: 'reg1', fotos: { entrada: new Date().toISOString() } }); }""")
            pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(300)
        pg.evaluate("ecraNaoRegou()"); pg.wait_for_timeout(300)
        if papel == "tecnico":
            print(f"[{papel}] 2 teste → confirm:", dial[-1:], "| em curso:", pg.evaluate("LS.get('emCurso')"), "| fila:", pg.evaluate("LS.get('filaAlt', []).length"), "|", pg.inner_text("#folha-c")[:80].replace("\n", " | "))
            ctx.close(); continue
        print(f"[{papel}] 2 ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:600]); pg.screenshot(path=f"/home/claude/rega-test/v118_naoregou{LING}.png")
        pg.click("#folha-c .btn.aviso"); pg.wait_for_timeout(200); print(f"[{papel}] 3 sem motivo →", dial[-1:])
        pg.check("input[name=nr-m][value=tuk_tuk]"); pg.fill("#nr-obs", "Esperámos até às 9:00"); ctx.set_offline(True); pg.click("#folha-c .btn.aviso"); pg.wait_for_timeout(800)
        print(f"[{papel}] 4 depois:", pg.inner_text("#folha-c")[:120].replace("\n", " | "), "| em curso:", pg.evaluate("LS.get('emCurso')"))
        print(f"[{papel}]   fila:", pg.evaluate("LS.get('filaAlt', []).map(x => x.tipo + ':' + JSON.stringify({m: x.d.motivo, a: x.d.area_id, f: x.d.foto, t: x.d.todo_dia, e: !!x.d.entrada_em}))"))
        pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(800)
        print(f"[{papel}]   Hoje:", pg.locator("#hoje .cartao:has(button:has-text('⚠️'))").last.inner_text().replace("\n", " | ")[:300])
        ctx.set_offline(False); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
        print(f"[{papel}] 5 enviado:", [(x[0], x[1].get('p_area'), bool(x[1].get('p_entrada')), x[1].get('p_motivo'), (x[1].get('p_foto') or '')[-12:]) for x in rec if x[0].startswith("gravar_dia_sem_rega")], "| fotos:", [x[1] for x in rec if x[0] == "foto"])
        pg.evaluate("ecraDiaSemRega()"); pg.wait_for_timeout(300)
        print(f"[{papel}] 6 dias:", pg.locator("#dsr-dia option").all_inner_texts())
        # saída longe do campo: o motivo fica escrito e o que escreveu também
        pg.evaluate("""() => { LS.set('emCurso', { area_id: 'PR1-1', entrada_em: new Date(Date.now() - 3600e3).toISOString(), reg_id: 'reg2', fotos: { entrada: 'x', rega: 'x', saida: 'x' } }); }""")
        ctx.set_geolocation({"latitude": lat0 + 0.05, "longitude": lon0, "accuracy": 140})
        pg.wait_for_timeout(1500); print("   S.fix:", pg.evaluate("S.fix && Math.round(S.fix.coords.accuracy)")); pg.evaluate("ecraSaida()"); pg.wait_for_timeout(300)
        pg.fill("#s-plantas", "80"); pg.fill("#s-pessoas", "4"); pg.click("#s-chips .chip >> nth=0"); pg.fill("#s-obs", "Pouca água")
        pg.evaluate("marcarSaida()"); pg.wait_for_timeout(1500)
        print(f"[{papel}] 7 a ler GPS:", pg.inner_text("#folha-c")[:200].replace("\n", " | "))
        pg.wait_for_timeout(21000)
        print(f"[{papel}] 8 saída recusada:", pg.inner_text("#folha-c")[:520].replace("\n", " | "))
        print(f"[{papel}]   valores:", pg.evaluate("[$('#s-plantas').value, $('#s-pessoas').value, $('#s-obs').value, document.querySelectorAll('#s-chips .chip.on').length]"))
        pg.screenshot(path=f"/home/claude/rega-test/v118_saida{LING}.png")
        ctx.close()
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
