# v148 (30/10/2026): monitoria recomeça a 02/11; regas de sábado verificam-se na segunda. LING=en / sw. LING=en / sw; PAPEL=tecnico / gestor.
import os
import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8848", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
areas = [{"id": "PR5-1", "pr": "PR5", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Cinco", "instaladas": 50, "vivas": 50, "latitude": None, "longitude": None, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR6-1", "pr": "PR6", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Seis", "instaladas": 50, "vivas": 50, "latitude": -10.6836, "longitude": 40.6339, "activista_id": ACT, "activista_proposto": None, "poligono": [[40.6335,-10.6832],[40.6343,-10.6832],[40.6343,-10.6840],[40.6335,-10.6840],[40.6335,-10.6832]]},
         {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None}]
PAPEL = os.environ.get("PAPEL", "tecnico"); NADA = False; esc = {"meus": [1], "n": 0}; NT = int(os.environ.get("NT", "0")); cont = []; rede = {"on": True}
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
    if "/rpc/monitoria_escala_ver" in u: return ok({"n_dias": 1, "campos": 2, "pausa": False, "retoma": "2026-11-02", "eu_monitor": PAPEL != "gestor", "meus": esc["meus"], "pessoas": [{"id": UID, "nome": "Nuro Teste", "papel": "tecnico", "dias": esc["meus"], "eu": True}, {"id": "p2", "nome": "Gelson Manuel", "papel": "tecnico", "dias": [1], "eu": False}, {"id": "p3", "nome": "Raul Miquilange", "papel": "supervisor", "dias": [3], "eu": False}, {"id": "p4", "nome": "Guidion Cristovao", "papel": "tecnico", "dias": None, "eu": False}]})
    if "/rpc/gravar_monitoria_escala" in u:
        esc["n"] += 1; d = json.loads(r.post_data)["p_dias"]; rec.setdefault("esc", []).append(d)
        if esc["n"] == 1: return route.fulfill(status=400, content_type="application/json", body=json.dumps({"code": "P0001", "message": "Sem verificação: quinta, sexta. Todos os colegas já escolheram os seus dias: inclua estes dias na sua escolha."}))
        esc["meus"] = sorted(d); return ok({"dias": esc["meus"]})
    if "/rpc/monitoria_lista" in u: return ok([{"amostra_id": "a1", "data_rega": "2026-10-29", "area_id": "PR1-1", "activista_id": ACT, "feita": False}, {"amostra_id": "a2", "data_rega": "2026-10-31", "area_id": "PR2-1", "activista_id": ACT, "feita": False}])
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/testes_equipa" in u: return ok([{"area_id": "PR2-1", "data": "2026-10-20", "n": 2, "quem": "Raul Miquilange"}])
    if "/rpc/plantas_por_campo" in u: return ok([{"area_id": "PR1-1", "n": 5, "v": 3, "s": 1, "m": 1}])
    if "/rpc/sugestoes_lista" in u: return ok({"sugestoes": [{"id": "s1", "texto": "A câmara fecha a app", "foto_path": UID + "/s1.jpg", "ecra": "hoje › Chuva", "area_id": None, "versao": "86", "criada_em": "2026-10-20T08:00:00Z", "estado": "nova", "papel": "tecnico", "quem": "Gelson"}, {"id": "s2", "texto": "Feito", "foto_path": None, "ecra": "mapa", "versao": "85", "criada_em": "2026-10-19T08:00:00Z", "estado": "feita", "papel": "supervisor", "quem": "Nuro"}], "problemas": [{"tipo": "camara", "mensagem": "Câmara dentro da app não abriu: NotReadableError", "ecra": "hoje", "vezes": 3, "pessoas": 1, "ultima_em": "2026-10-20T08:00:00Z", "quem": "Gelson"}]})
    if "/rest/v1/coberturas" in u: return ok([])
    if "/rpc/avaliar_sugestao" in u: rec.setdefault("aval", []).append(json.loads(r.post_data)); return ok(None)
    if "/functions/v1/gestor-activistas" in u:
        corpo = json.loads(r.post_data or "{}"); rec.setdefault("gest", []).append(corpo)
        if corpo.get("accao") != "listar": return ok({"nome": corpo.get("nome"), "utilizador": corpo.get("utilizador"), "activista": "Activista Novo"})
        uts = [{"id": "u1", "papel": "tecnico", "nome": "Técnico Um", "utilizador": "tum"}, {"id": "u3", "papel": "director", "nome": "Director Um", "utilizador": "dum"}]
        if NADA: uts += [{"id": "u2", "papel": "tecnico", "nome": "Técnico Dois", "utilizador": "tdois"}, {"id": "u4", "papel": "supervisor", "nome": "Supervisor Um", "utilizador": "sum"}, {"id": "u5", "papel": "me", "nome": "ME Um", "utilizador": "meum"}, {"id": "u6", "papel": "cliente", "nome": "Cliente Um", "utilizador": "cum"}, {"id": "u7", "papel": "oficial_me", "nome": "Oficial Um", "utilizador": "oum"}]
        acts = [{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Farol", "tem_login": True, "utilizador": "aex"}] + ([] if NADA else [{"id": "a2", "nome": "Activista Novo", "comunidade_principal": "Farol", "tem_login": False}])
        return ok({"activistas": acts, "utilizadores": uts, "clientes": [], "nomes": {"tecnico": ["Técnico Um", "Técnico Dois"], "supervisor": ["Supervisor Um"]}})
    if "/rest/v1/pessoas_acesso" in u: return ok([{"nome": "Técnico Um", "entidade": "JFS", "papel": "tecnico", "utilizador": "tum"}, {"nome": "Técnico Dois", "entidade": "JFS", "papel": "tecnico", "utilizador": "tdois"}, {"nome": "Supervisor Um", "entidade": "JFS", "papel": "supervisor", "utilizador": "sum"}, {"nome": "Director Um", "entidade": "JFS", "papel": "director", "utilizador": "dum"}, {"nome": "ME Um", "entidade": "JFS", "papel": "me", "utilizador": "meum"}, {"nome": "Cliente Um", "entidade": "SAN", "papel": "cliente", "utilizador": "cum"}, {"nome": "Oficial Um", "entidade": "M&E", "papel": "oficial_me", "utilizador": "oum"}])
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
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % os.environ.get("LING","pt"))
    pg.goto("http://localhost:8848/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "x"); pg.fill("#l-pin", "12345678"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1200)
    L = os.environ.get("LING","pt")
    print("O1 folha aberta:", pg.is_visible("#folha"))
    pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(1500)
    mon = pg.locator(".cartao", has=pg.locator("button[onclick='ecraEscalaMon()']")).first
    print("H cartão:", mon.inner_text().replace(chr(10), " | ")[:600])
    pg.click("button[onclick='ecraEscalaMon()']"); pg.wait_for_timeout(400)
    print("E texto:", pg.inner_text("#folha-c").split(chr(10))[2][:200])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
