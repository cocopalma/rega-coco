# v136 (29/10/2026): o técnico põe campos fora do plano na rega (só os da comunidade das suas equipas; motivo obrigatório). LING=en / sw.
import os
import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8836", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}]
PAPEL = os.environ.get("PAPEL", "tecnico"); NT = int(os.environ.get("NT", "0")); cont = []; rede = {"on": True}
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
    if "/rpc/areas_fora_plano2" in u: return ok({"fora": [{"id": "PR7-5", "pr": "PR7", "comunidade": "Farol", "produtor": "Produtor Sete", "vivas": 52, "instaladas": 420, "tem_coord": True, "pode": True}, {"id": "PR7-12", "pr": "PR7", "comunidade": "Farol", "produtor": "Produtor Sete", "vivas": 210, "instaladas": 420, "tem_coord": True, "pode": True}, {"id": "PR8-1", "pr": "PR8", "comunidade": "Quiwia", "produtor": "Produtor Oito", "vivas": 40, "instaladas": 50, "tem_coord": True, "pode": False}], "na_rega": []})
    if "/rpc/voltar_a_regar" in u: rec.setdefault("vr", []).append(json.loads(r.post_data)); areas.append({"id": "PR7-12", "pr": "PR7", "area_n": 12, "comunidade": "Farol", "produtor": "Produtor Sete", "instaladas": 420, "vivas": 210, "latitude": None, "longitude": None, "activista_id": ACT, "activista_proposto": None}); return ok({"id": "PR7-12", "activista_id": ACT})
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
    pg.goto("http://localhost:8836/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "x"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1200)
    if pg.is_visible("#folha-x"): pg.click("#folha-x"); pg.wait_for_timeout(300)
    pg.click("nav button[data-e=lista]"); pg.wait_for_timeout(300)
    print("0 botão na lista:", pg.locator("button", has_text="Voltar a pôr um campo na rega").count() if os.environ.get("LING","pt")=="pt" else pg.locator("button[onclick='ecraVoltarRega()']").count())
    pg.evaluate("ecraVoltarRega()"); pg.wait_for_timeout(200)
    pg.fill("#vr-txt", "Produtor"); pg.wait_for_timeout(1200)
    print("1 resultado:", pg.inner_text("#vr-res").replace(chr(10), " | "))
    pg.locator("#vr-res").screenshot(path="/home/claude/rega-test/v136_tecnico%s.png" % os.environ.get("LING", ""))
    print("1b botões:", pg.locator("#vr-res button.chip").count())
    pg.locator("#vr-res button.chip").nth(1).click(); pg.wait_for_timeout(300)
    print("2 confirmar:", pg.inner_text("#folha-c").replace(chr(10), " | "))
    pg.click("#vr-ok"); pg.wait_for_timeout(500)
    print("3 sem motivo, pedidos:", rec.get("vr"), "| aviso:", pg.locator("body > .msg.erro").last.inner_text() if pg.locator("body > .msg.erro").count() else "?")
    pg.fill("#vr-motivo", "A Desteria confirmou que é este campo"); pg.click("#vr-ok"); pg.wait_for_timeout(1500)
    print("4 pedido:", rec.get("vr"))
    print("5 depois:", pg.inner_text("#folha h2") if pg.is_visible("#folha") else "folha fechada")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
