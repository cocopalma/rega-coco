# Manutenção (cava-roda e mulching) em Quiwia e Farol, à parte da rega (v96, 22/10/2026). PAPEL=supervisor (padrão) / tecnico; LING=en / sw.
import os
import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8823", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}]
PAPEL = os.environ.get("PAPEL", "supervisor"); NT = int(os.environ.get("NT", "0")); cont = []; rede = {"on": True}
MAN = [{"id": "PR1-1", "pr": "PR1", "produtor": "Produtor Um", "comunidade": "Farol", "latitude": -10.6835, "longitude": 40.6340, "poligono": None, "vivas": 70, "instaladas": 70, "activa": True, "plantas": 70, "activista": "Activista Exemplo", "cavaroda": 20, "mulching": 10, "ultima": "2026-10-21", "ultima_em": "2026-10-21T10:00:00Z", "n": 1, "feito": False},
       {"id": "PR5-1", "pr": "PR5", "produtor": "Produtor Cinco", "comunidade": "Quiwia", "latitude": None, "longitude": None, "poligono": None, "vivas": 40, "instaladas": 50, "activa": False, "plantas": 40, "activista": None, "cavaroda": None, "mulching": None, "n": 0, "feito": False},
       {"id": "PR6-1", "pr": "PR6", "produtor": "Produtor Seis", "comunidade": "Quiwia", "latitude": -10.684, "longitude": 40.633, "poligono": None, "vivas": 30, "instaladas": 30, "activa": True, "plantas": 30, "activista": "Activista Exemplo", "cavaroda": 30, "mulching": 30, "ultima": "2026-10-20", "ultima_em": "2026-10-20T10:00:00Z", "n": 2, "feito": True, "feito_em": "2026-10-20T11:00:00Z", "feito_por": "Raul Miquilange"}]
rec = {"fotos": [], "registos": [], "corr": [], "sug": [], "prob": [], "up": []}; erros = []; dialogos = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Nuro Teste", "papel": PAPEL, "activista_id": ACT if PAPEL == "activista" else None, "gere_acessos": True})
    if "/storage/v1/object/rega-fotos/" in u: rec["fotos"].append((u.split("rega-fotos/")[1], len(r.post_data_buffer or b""))); return ok({"Key": "x"})
    if "/rest/v1/registos_rega" in u and r.method == "HEAD": cont.append(u); return route.fulfill(status=200, headers={"content-range": "*/%d" % NT, "content-type": "application/json", "access-control-allow-origin": "*", "access-control-expose-headers": "Content-Range"}, body="")
    if "/rest/v1/registos_rega" in u:
        if r.method == "POST": rec["registos"] += json.loads(r.post_data) if r.post_data.startswith("[") else [json.loads(r.post_data)]; return route.fulfill(status=201, body="")
        return ok([])
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Farol", "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/estado_ronda" in u: return ok([{"area_id": a["id"], "ultima_rega": None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False} for a in areas])
    if "/storage/v1/object/sugestoes-fotos/" in u:
        if not rede["on"]: return route.abort()
        rec["up"].append((u.split("sugestoes-fotos/")[1], len(r.post_data_buffer or b""))); return ok({"Key": "x"})
    if "/rpc/enviar_sugestao" in u:
        if not rede["on"]: return route.abort()
        rec["sug"].append(json.loads(r.post_data)); return ok(None)
    if "/rpc/registar_problemas" in u:
        if not rede["on"]: return route.abort()
        rec["prob"].append(json.loads(r.post_data)); return ok(None)
    if "/rpc/gravar_poligono" in u: rec.setdefault("gp", []).append(json.loads(r.post_data)["p_area"]); return ok({"id": "x", "area_m2": 1})
    if "/rpc/manutencao_campos" in u: return ok(None if PAPEL == "activista" else {"teste": True, "inicio": "2026-11-02", "acesso": "regista" if PAPEL == "tecnico" else "escreve", "comunidades": ["Farol", "Quiwia"], "campos": MAN})
    if "/rpc/manutencao_registos_campo" in u: return ok([{"id": "m0", "data": "2026-10-21", "cavaroda": 20, "mulching": 10, "pessoas": 8, "obs": None, "foto_path": UID + "/m0.jpg", "feito_em": "2026-10-21T10:00:00Z", "quem": "Raul Miquilange"}] if "PR1-1" in r.post_data else [])
    if "/storage/v1/object/manutencao-fotos/" in u:
        if not rede["on"]: return route.abort()
        rec.setdefault("upman", []).append(u.split("manutencao-fotos/")[1]); return ok({"Key": "x"})
    if "/rpc/gravar_manutencao" in u:
        if not rede["on"]: return route.abort()
        rec.setdefault("gm", []).append(json.loads(r.post_data)); return ok(None)
    if "/rpc/marcar_manutencao_feita" in u:
        if not rede["on"]: return route.abort()
        rec.setdefault("mf", []).append(json.loads(r.post_data)); return ok(None)
    if "/rpc/testes_equipa" in u: return ok([{"area_id": "PR2-1", "data": "2026-10-20", "n": 2, "quem": "Raul Miquilange"}])
    if "/rpc/plantas_por_campo" in u: return ok([{"area_id": "PR1-1", "n": 5, "v": 3, "s": 1, "m": 1}])
    if "/rpc/sugestoes_lista" in u: return ok({"sugestoes": [{"id": "s1", "texto": "A câmara fecha a app", "foto_path": UID + "/s1.jpg", "ecra": "hoje › Chuva", "area_id": None, "versao": "86", "criada_em": "2026-10-20T08:00:00Z", "estado": "nova", "papel": "tecnico", "quem": "Gelson"}, {"id": "s2", "texto": "Feito", "foto_path": None, "ecra": "mapa", "versao": "85", "criada_em": "2026-10-19T08:00:00Z", "estado": "feita", "papel": "supervisor", "quem": "Nuro"}], "problemas": [{"tipo": "camara", "mensagem": "Câmara dentro da app não abriu: NotReadableError", "ecra": "hoje", "vezes": 3, "pessoas": 1, "ultima_em": "2026-10-20T08:00:00Z", "quem": "Gelson"}]})
    if "/rest/v1/coberturas" in u: return ok([])
    if "/rpc/avaliar_sugestao" in u: rec.setdefault("aval", []).append(json.loads(r.post_data)); return ok(None)
    if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
    if "/rpc/corrigir_plantas_rega" in u:
        if not rede["on"]: return route.abort()
        rec["corr"].append(json.loads(r.post_data)); return ok(None)
    if "/rpc/regas_campo" in u: return ok([{"id": "r1", "data": "2026-10-15", "entrada_em": "2026-10-15T07:00:00Z", "saida_em": "2026-10-15T07:40:00Z", "plantas_regadas": 65, "pessoas": 4, "teste": False, "quem": "Activista Exemplo", "foto_entrada": UID + "/r1-entrada.jpg", "foto_entrada_em": "2026-10-15T07:01:00Z", "foto_rega": UID + "/r1-rega.jpg", "foto_rega_em": "2026-10-15T07:20:00Z", "foto_saida": UID + "/r1-saida.jpg", "foto_saida_em": "2026-10-15T07:39:00Z"}, {"id": "r0", "data": "2026-10-12", "entrada_em": "2026-10-12T07:00:00Z", "saida_em": "2026-10-12T07:30:00Z", "plantas_regadas": 50, "pessoas": 3, "teste": True, "quem": "Supervisor", "plantas_originais": 70, "plantas_corrigidas_em": "2026-10-13T08:00:00Z", "corrigido_por": "Raul", "motivo_correccao": "Contou mal", "foto_entrada": None, "foto_rega": None, "foto_saida": None}, {"id": "r9", "data": "2026-10-11", "entrada_em": "2026-10-11T07:00:00Z", "saida_em": "2026-10-11T07:30:00Z", "plantas_regadas": 40, "pessoas": 3, "teste": False, "quem": "Outro", "foto_entrada": None, "foto_rega": None, "foto_saida": None, "fotos_outro": True}, {"id": "r8", "data": "2026-10-10", "entrada_em": "2026-10-10T07:00:00Z", "saida_em": "2026-10-10T07:30:00Z", "plantas_regadas": 40, "pessoas": 3, "teste": False, "quem": "Outro2", "foto_entrada": "outro/r8-entrada.jpg", "foto_rega": None, "foto_saida": None}])
    if "/storage/v1/object/sign/rega-fotos/" in u and "token=" not in u: rec.setdefault("sign", []).append(u.split("rega-fotos/")[1]); return ok({"signedURL": "/object/sign/rega-fotos/u/r1-rega.jpg?token=t"})
    if "/storage/v1/object/sign/" in u and "token=" in u: return route.fulfill(status=200, content_type="image/jpeg", body=open("/home/claude/rega-test/foto_teste.jpg","rb").read())
    if "/rpc/" in u: return ok([])
    if "/rest/v1/zonas" in u: return ok([])
    return route.fulfill(status=201, body="")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.add_init_script("localStorage.setItem('rega.lingua', %r); localStorage.setItem('rega.plantas', JSON.stringify({'PR2-1': [{id:'x', n:1, lat:-10.6842, lon:40.6332, estado:'viva'}]}))" % os.environ.get("LING","pt"))
    pg.goto("http://localhost:8823/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "x"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1200)
    if pg.is_visible("#folha-x"): pg.click("#folha-x"); pg.wait_for_timeout(300)
    vis = lambda q: pg.evaluate(f"(() => {{ const e = document.querySelector('{q}'); return !!e && getComputedStyle(e).display !== 'none'; }})()")
    print("1 interruptor no mapa:", vis("#modo-mapa"), "| na lista:", vis("#modo-lista"))
    if PAPEL == "tecnico":
        pg.evaluate("setModo('manut')"); pg.wait_for_timeout(300)
        pg.click("nav button[data-e=lista]"); pg.wait_for_timeout(300)
        pg.locator("#man-lista .item[data-mid='PR5-1']").click(); pg.wait_for_timeout(500)
        print("T1 ficha técnico:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:500])
        pg.evaluate("abrirFichaManut('PR1-1')"); pg.wait_for_timeout(600)
        pg.locator("#folha-c button", has_text="➕").click(); pg.wait_for_timeout(300)
        pg.fill("#mn-cav", "70"); pg.fill("#mn-mul", "70"); pg.set_input_files("#mn-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_timeout(600)
        pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(2500)
        print("T2 ficha depois:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:600])
        print("T3 enviado:", [(x["p_area"], x["p_cavaroda"]) for x in rec.get("gm", [])], "| botão feito:", pg.locator("#folha-c button", has_text="✓").count())
    if PAPEL != "tecnico":
        pg.click("#modo-mapa button[data-m=manut]"); pg.wait_for_timeout(400)
        print("2 modo:", pg.evaluate("S.modo"), "| camadas no mapa:", pg.evaluate("camada.getLayers().length"), "| legenda manut:", vis("#leg-man"), "| legenda rega:", vis("#leg-rega"))
        pg.click("nav button[data-e=lista]"); pg.wait_for_timeout(300)
        print("3 filtros rega escondidos:", not vis("#e-lista .filtros"), "| lista:", pg.inner_text("#lista").replace(chr(10), " | ")[:600])
        pg.locator("#man-lista .item[data-mid='PR1-1']").click(); pg.wait_for_timeout(800)
        print("4 ficha:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:700])
        pg.locator("#folha-c button", has_text="➕").click(); pg.wait_for_timeout(300)
        rede["on"] = False; ctx.set_offline(True)
        pg.fill("#mn-cav", "80"); pg.fill("#mn-mul", "70"); pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(300)
        print("5 alerta (passa):", dialogos[-1:] )
        pg.fill("#mn-cav", "70"); pg.fill("#mn-pes", "12"); pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(300)
        print("6 alerta (sem foto):", dialogos[-1:])
        pg.set_input_files("#mn-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_timeout(600)
        pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(800)
        print("7 sem rede: fila", pg.evaluate("LS.get('filaMan').map(x => [x.tipo, x.cavaroda, x.mulching, x.pessoas])"), "| sync:", pg.inner_text("#h-sync"))
        print("8 ficha agora:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:400])
        pg.locator("#folha-c button", has_text="✓").click(); pg.wait_for_timeout(500)
        print("9 fila:", pg.evaluate("LS.get('filaMan').map(x => x.tipo)"), "| estado:", pg.evaluate("estadoMan(camposManut().find(c => c.id === 'PR1-1'))"))
        rede["on"] = True; ctx.set_offline(False); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
        print("10 enviados: upload", rec.get("upman"), "| gravar", [(x["p_area"], x["p_cavaroda"], x["p_mulching"], x["p_pessoas"]) for x in rec.get("gm", [])], "| feito", [(x["p_area"], x["p_feito"]) for x in rec.get("mf", [])], "| fila", pg.evaluate("LS.get('filaMan')"))
        pg.click("#folha-x"); pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(1200)
        c = pg.locator("#hoje .cartao", has_text="🌱")
        print("11 Hoje:", c.count() and c.first.inner_text().replace(chr(10), " | "))
        pg.click("nav button[data-e=lista]"); pg.wait_for_timeout(300)
        pg.locator("#lista").screenshot(path="/home/claude/rega-test/manut_lista%s.png" % os.environ.get("LING", ""))
        pg.click("#modo-lista button[data-m=rega]"); pg.wait_for_timeout(300)
        pg.click("#modo-lista button[data-m=manut]"); pg.wait_for_timeout(300)
        pg.select_option("#man-est", "semcoord"); pg.wait_for_timeout(200)
        print("13 sem coordenada:", pg.inner_text("#man-lista").replace(chr(10), " | ")[:200])
        pg.locator("#man-lista .item[data-mid='PR5-1']").click(); pg.wait_for_timeout(500)
        print("14 ficha sem coord:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:420])
        pg.locator("#folha-c button", has_text="📐").click(); pg.wait_for_timeout(500)
        print("15 ecrã medir:", pg.inner_text("#folha-c h2"))
        pg.evaluate("S.medir.pts = [[40.6300,-10.6900],[40.6303,-10.6900],[40.6303,-10.6903],[40.6300,-10.6903],[40.63001,-10.69001]]; S.medir.melhor = 4; terminarMedicao()"); pg.wait_for_timeout(300)
        pg.evaluate("gravarMedicao()"); pg.wait_for_timeout(800)
        print("16 depois de gravar:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:300])
        pg.wait_for_timeout(1500); print("17 polígono enviado:", rec.get("gp"), "| fila:", pg.evaluate("LS.get('filaAlt', []).filter(x => x.tipo === 'poligono').length"), "| coord:", pg.evaluate("[S.manut.campos.find(c => c.id === 'PR5-1').latitude, !!S.manut.campos.find(c => c.id === 'PR5-1').poligono]"))
        pg.select_option("#man-est", ""); pg.wait_for_timeout(200)
        print("12 de volta à rega: filtros", vis("#e-lista .filtros"), "| lista:", pg.inner_text("#lista")[:120].replace(chr(10), " | "))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
