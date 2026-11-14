# Cava-roda e mulching quando não há rega (ramo cc-manutencao, decisões do Valdo de 13–14/11/2026). Servidor simulado.
# PAPEL=activista (por defeito), tecnico ou gestor (registam pela equipa; o gestor activa as horas extras na ficha); LING=en / sw.
# 17 «O meu dia» (técnico): equipa sem nada a cinzento até às 15:30 («pode começar até às 15:30»), a vermelho depois.
# Passos: 1 motivo obrigatório; 2 início do dia (activista); 3 entrada com GPS e fotografia do início; 4 rega bloqueada com a
# actividade em curso; 5 fim sem a fotografia durante recusado; 6 mais plantas do que as vivas recusado; 7 fim sem rede fica na fila;
# 8 com rede vai para o servidor (3 fotografias + gravar_actividade); 9 depois das 15:30 o botão não aparece; 10 rega em curso
# depois das 15:30 continua (não muda nada na rega); 11 «O meu dia» mostra a 🌱 (técnico).
# 14 depois das 15:30 a entrada da rega é recusada sem horas extras (app); 15 técnico activa as horas extras no «O meu dia» (fica quem e
# a hora); 16 com horas extras a rega e a cava-roda podem começar depois das 15:30.
# 12 o que falta no campo conta os dias anteriores (servidor: 10 cava-roda e 5 mulching já feitos): na ficha e na saída.
import os
import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; FOTO = "/home/claude/rega-test/foto_teste.jpg"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8847", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
POL = [[40.6335, -10.6832], [40.6343, -10.6832], [40.6343, -10.6840], [40.6335, -10.6840], [40.6335, -10.6832]]
areas = [{"id": "PR6-1", "pr": "PR6", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Seis", "instaladas": 50, "vivas": 50, "latitude": -10.6836, "longitude": 40.6339, "activista_id": ACT, "activista_proposto": None, "poligono": POL},
         {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6935, "longitude": 40.6440, "activista_id": ACT, "activista_proposto": None}]
PAPEL = os.environ.get("PAPEL", "activista"); LING = os.environ.get("LING", "pt"); rede = {"on": True}
rec = {"fotos": [], "act": [], "jornadas": [], "he": []}; HE = []; erros = []; dialogos = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if not rede["on"] and ("/rpc/" in u or "/storage/" in u or "/rest/" in u): return route.abort()
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Pessoa Teste", "papel": PAPEL, "activista_id": ACT if PAPEL == "activista" else None, "gere_acessos": False})
    if "/storage/v1/object/rega-fotos/" in u: rec["fotos"].append(u.split("rega-fotos/")[1]); return ok({"Key": "x"})
    if "/rest/v1/registos_rega" in u and r.method == "HEAD": return route.fulfill(status=200, headers={"content-range": "*/3", "content-type": "application/json", "access-control-allow-origin": "*", "access-control-expose-headers": "Content-Range"}, body="")
    if "/rest/v1/jornadas" in u and r.method == "POST": rec["jornadas"].append(r.post_data); return route.fulfill(status=201, body="")
    if "/rest/v1/registos_rega" in u: return ok([]) if r.method == "GET" else route.fulfill(status=201, body="")
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Exemplo", "comunidade_principal": "Farol", "equipa_tamanho": 5, "tecnico": "Pessoa Teste", "supervisor": "Sup"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/estado_ronda" in u: return ok([{"area_id": a["id"], "ultima_rega": None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False} for a in areas])
    if "/rpc/horas_extras_lista" in u: return ok(HE)
    if "/rpc/activar_horas_extras" in u: rec["he"].append(json.loads(r.post_data)); HE.append({"id": rec["he"][-1]["p_id"], "activista_id": ACT, "data": rec["he"][-1]["p_data"], "por": "Pessoa Teste", "em": rec["he"][-1]["p_em"]}); return ok({"id": rec["he"][-1]["p_id"], "ja": False})
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/gravar_actividade" in u: rec["act"].append(json.loads(r.post_data)); return ok({"id": json.loads(r.post_data)["p"]["id"], "manutencao": True, "excedente": {"cavaroda": 0, "mulching": 0}})
    if "/rpc/actividades_campo_lista" in u: return ok({"cavaroda": 10 + sum(a["p"]["cavaroda"] for a in rec["act"]), "mulching": 5 + sum(a["p"]["mulching"] for a in rec["act"]), "lista": [{"id": a["p"]["id"], "data": "2026-11-16", "motivo": a["p"]["motivo"], "entrada_em": a["p"]["entrada_em"], "saida_em": a["p"]["saida_em"], "pessoas": a["p"]["pessoas"], "cavaroda": a["p"]["cavaroda"], "mulching": a["p"]["mulching"], "equipa": "Activista Exemplo", "quem": "Pessoa Teste", "foto_entrada": a["p"]["foto_entrada"], "foto_durante": a["p"]["foto_durante"], "foto_saida": a["p"]["foto_saida"], "excedente": 0} for a in rec["act"]]})
    if "/rpc/meu_dia" in u: return ok({"data": "2026-11-16", "hora_chegada": "06:30", "fechado_em": None, "alertas": [], "monitoria_hoje": 0, "monitoria_falhas_ontem": 0, "sem_equipa": 0, "por_aprovar": [], "por_terminar": [],
        "equipas": [{"id": "33333333-3333-3333-3333-333333333333", "nome": "Equipa Parada", "comunidade": "Farol", "regas": 0, "plantas": 0, "chegada": None, "sem_rega": None, "comecou": None, "motivos": [], "actividade": None}, {"id": ACT, "nome": "Activista Exemplo", "comunidade": "Farol", "regas": 0, "plantas": 0, "chegada": None, "sem_rega": None, "comecou": "2026-11-16T07:00:00Z", "motivos": [], "actividade": {"campos": 1, "cavaroda": 30, "mulching": 20} if rec["act"] else None}]})
    if "/rpc/" in u: return ok([])
    if "/rest/v1/" in u: return ok([]) if r.method == "GET" else route.fulfill(status=201, body="")
    return route.fulfill(status=201, body="")
res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6340, "accuracy": 5})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.clock.install(time="2026-11-16T09:00:00+02:00")    # segunda-feira, 09:00 de Maputo
    pg.add_init_script("delete window.__HORA_TESTE; localStorage.setItem('rega.lingua', %r)" % LING)   # a hora vem do relógio do teste
    pg.goto("http://localhost:8847/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "x"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    if pg.is_visible("#folha-x"): pg.click("#folha-x"); pg.wait_for_timeout(300)
    folha = lambda: pg.inner_text("#folha-c") if pg.is_visible("#folha") else ""
    pg.evaluate("abrirFicha('PR6-1')"); pg.wait_for_timeout(400)
    passo("1a botão na ficha", pg.is_visible("#b-act"))
    pg.wait_for_selector("#act-tot", timeout=5000); tt = pg.inner_text("#act-tot")
    passo("12a ficha: feitas 10 de 50 · faltam 40 / 5 de 50 · faltam 45", "10" in tt and "40" in tt and "45" in tt, tt.replace("\n", " | "))
    pg.click("#b-act"); pg.wait_for_timeout(300)
    pg.click("#ac-ok"); pg.wait_for_timeout(200)
    passo("1b sem motivo recusado", any("rega" in d.lower() or "watering" in d.lower() or "umwagiliaji" in d.lower() for d in dialogos), str(dialogos[-1:]))
    pg.click("#ac-mot .chip[data-k=avaria_tuk_tuk]")
    if PAPEL != "activista":
        pg.click("#ac-ok"); pg.wait_for_timeout(200); n0 = len(dialogos)
        passo("1c técnico sem motivo pela equipa recusado", pg.is_visible("#ac-tec"))
        pg.click("#ac-tec .chip[data-k='0']")
    pg.click("#ac-ok"); pg.wait_for_timeout(500)
    if PAPEL == "activista":
        passo("2 início do dia pedido", pg.is_visible("#j-pessoas"))
        pg.fill("#j-pessoas", "4"); pg.click("#folha-c button.btn"); pg.wait_for_timeout(300)
    pg.wait_for_selector("#fa-foto", state="attached", timeout=30000)
    curso = pg.evaluate("JSON.parse(localStorage.getItem('rega.actCurso'))")
    passo("3a entrada marcada com GPS", curso and curso.get("entrada_lat") and curso.get("motivo") == "avaria_tuk_tuk", str(curso and curso.get("entrada_dist_m")))
    pg.set_input_files("#fa-foto", FOTO); pg.wait_for_selector("#act-curso", timeout=10000)
    passo("3b fotografia do início guardada", pg.evaluate("!!JSON.parse(localStorage.getItem('rega.actCurso')).fotos.entrada"))
    pg.evaluate("marcarEntrada('PR6-1')"); pg.wait_for_timeout(300)
    passo("4 rega bloqueada com a actividade em curso", pg.evaluate("!localStorage.getItem('rega.emCurso')") and pg.is_visible("#act-curso"))
    nd = len(dialogos); pg.click("#b-act-fim"); pg.wait_for_timeout(300)
    passo("5 fim sem a fotografia durante recusado", len(dialogos) > nd and not pg.is_visible("#af-ok"))
    pg.locator("#act-curso + .cartao button.chip").nth(1).click(); pg.wait_for_timeout(300)
    pg.set_input_files("#fa-foto", FOTO); pg.wait_for_selector("#act-curso", timeout=10000)
    pg.click("#b-act-fim"); pg.wait_for_selector("#af-ok")
    pg.fill("#af-cav", "30"); pg.fill("#af-mul", "20"); pg.wait_for_timeout(100); fa = pg.inner_text("#af-falta")
    passo("12b saída: faltam 10 (cava-roda) e 25 (mulching), contando os dias anteriores", "10" in fa and "25" in fa and "✓" not in fa, fa.replace("\n", " | "))
    pg.fill("#af-cav", "40"); pg.wait_for_timeout(100); fa = pg.inner_text("#af-falta")
    passo("12c saída: cava-roda completa", "✓" in fa and "25" in fa, fa.replace("\n", " | "))
    pg.fill("#af-cav", "60"); pg.fill("#af-mul", "20"); pg.wait_for_timeout(100)
    aviso = pg.inner_text("#af-aviso")
    pg.set_input_files("#af-foto", FOTO); pg.wait_for_timeout(800)
    if not pg.input_value("#af-pess"): pg.fill("#af-pess", "4")
    pg.click("#af-ok"); pg.wait_for_timeout(300)
    passo("6 mais plantas do que as vivas recusado", "50" in pg.inner_text("#af-msg") and len(aviso) > 0, pg.inner_text("#af-msg")[:80])
    pg.fill("#af-cav", "30")
    rede["on"] = False; ctx.set_offline(True); pg.click("#af-ok"); pg.wait_for_timeout(2500)
    fila = pg.evaluate("JSON.parse(localStorage.getItem('rega.filaAct')||'[]')")
    passo("7 sem rede fica na fila", len(fila) == 1 and not rec["act"] and pg.evaluate("!localStorage.getItem('rega.actCurso')"), f"fila={len(fila)}")
    rede["on"] = True; ctx.set_offline(False); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(3000)
    a = rec["act"][0]["p"] if rec["act"] else {}
    passo("8 enviado: 3 fotografias e gravar_actividade", len([f for f in rec["fotos"] if "/act-" in f]) == 3 and a.get("cavaroda") == 30 and a.get("mulching") == 20 and a.get("foto_durante") and (a.get("motivo_tecnico") if PAPEL != "activista" else True),
          f"fotos={len(rec['fotos'])} p={ {k: a.get(k) for k in ['cavaroda', 'mulching', 'pessoas', 'motivo', 'motivo_tecnico']} }")
    passo("8b fila vazia", pg.evaluate("JSON.parse(localStorage.getItem('rega.filaAct')||'[]').length") == 0)
    pg.evaluate("abrirFicha('PR6-1')"); pg.wait_for_timeout(1200)
    passo("8c ficha mostra a actividade", "30" in pg.inner_text("#f-cav"), pg.inner_text("#f-cav")[:120].replace("\n", " | "))
    tt = pg.inner_text("#act-tot")
    passo("12d ficha depois: feitas 40 · faltam 10 / 25 · faltam 25", "40" in tt and "10" in tt and "25" in tt, tt.replace("\n", " | "))
    # 9: 15:31 — o botão desaparece
    pg.clock.set_system_time("2026-11-16T15:31:00+02:00"); pg.evaluate("abrirFicha('PR6-1')"); pg.wait_for_timeout(300)
    passo("9 depois das 15:30 não se começa", not pg.is_visible("#b-act") and "15:30" in folha())
    # 10: rega em curso às 15:31 continua (nada muda na rega)
    pg.evaluate("localStorage.setItem('rega.emCurso', JSON.stringify({area_id:'PR6-1', produtor:'Produtor Seis', entrada_em:'2026-11-16T13:10:00Z', reg_id:'rz'}))")
    pg.evaluate("abrirFicha('PR6-1')"); pg.wait_for_timeout(300)
    passo("13 filtro do activista intacto", pg.evaluate("document.querySelector('#f-act').tagName === 'SELECT' && document.querySelectorAll('#f-act option').length >= 1"))
    passo("10 rega em curso continua", pg.locator("#folha-c button", has_text="Terminei").count() + pg.locator("#folha-c button", has_text="Finished").count() + pg.locator("#folha-c button.aviso").count() > 0)
    pg.evaluate("localStorage.removeItem('rega.emCurso')")
    # 14: 16:00 sem horas extras — rega e cava-roda não começam (a rega «pela equipa» do técnico também não)
    pg.clock.set_system_time("2026-11-16T16:00:00+02:00"); pg.evaluate("abrirFicha('PR6-1')"); pg.wait_for_timeout(300)
    if PAPEL == "activista":
        passo("14a às 16:00 sem «Cheguei» nem cava-roda", pg.locator("#aviso-depois").count() == 1 and not pg.is_visible("#b-act") and pg.locator("#folha-c button.principal").count() == 0)
        ta = pg.inner_text("#aviso-depois"); passo("14c o aviso diz técnico, supervisor ou gestor", any(w in ta for w in ("pelo gestor", "the manager", "meneja")), ta)
    pg.evaluate("S.motTec = {id:'PR6-1', m:'O telemóvel do activista está avariado ou sem bateria'}; marcarEntrada('PR6-1')"); pg.wait_for_timeout(800)
    passo("14b entrada da rega recusada às 16:00", pg.locator("#msg-depois").count() == 1 and pg.evaluate("!localStorage.getItem('rega.emCurso')"))
    if PAPEL == "gestor":
        # 15: o gestor activa as horas extras na ficha do campo (não tem «O meu dia»)
        pg.evaluate("abrirFicha('PR6-1')"); pg.wait_for_timeout(300); pg.click("#he-ficha"); pg.wait_for_timeout(2500)
        pg.evaluate("abrirFicha('PR6-1')"); pg.wait_for_timeout(300)
        passo("15 gestor activou horas extras na ficha (quem e a hora)", len(rec["he"]) == 1 and rec["he"][0]["p_em"] and "⏰" in pg.inner_text("#he-ficha"), pg.inner_text("#he-ficha"))
    elif PAPEL != "activista":
        # 15: o técnico activa as horas extras no «O meu dia»
        pg.evaluate("fecharFolha(); window.__TAR_ABERTAS = true; mudar('hoje')"); pg.wait_for_timeout(1500)
        pg.locator(f"#meu-dia .he-btn[onclick*='{ACT}']").click(); pg.wait_for_timeout(2500)
        passo("15 horas extras activadas e enviadas (quem e a hora)", len(rec["he"]) == 1 and rec["he"][0]["p_activista"] == ACT and rec["he"][0]["p_em"] and pg.locator("#meu-dia .he-ok").count() == 1,
              pg.inner_text("#meu-dia .he-ok") if pg.locator("#meu-dia .he-ok").count() else "")
    else:
        HE.append({"id": "he1", "activista_id": ACT, "data": "2026-11-16", "por": "Técnico Dois", "em": "2026-11-16T13:40:00Z"})
        pg.evaluate("carregarHorasExtras()"); pg.wait_for_timeout(800)
    # 16: com horas extras, às 16:00 a cava-roda e a rega podem começar
    pg.evaluate("abrirFicha('PR6-1')"); pg.wait_for_timeout(300)
    passo("16a com horas extras: botão da cava-roda", pg.is_visible("#b-act"))
    if PAPEL == "activista": passo("16b com horas extras: «Cheguei» e quem activou", pg.locator("#folha-c button.principal").count() == 1 and "15:40" in folha())
    pg.evaluate("S.motTec = {id:'PR6-1', m:'O telemóvel do activista está avariado ou sem bateria'}; marcarEntrada('PR6-1')"); pg.wait_for_timeout(1500)
    # (o GPS falso do teste pode falhar depois de mexer no relógio; aqui só interessa que a regra das 15:30 já não recusa)
    passo("16c entrada da rega já não é recusada pela hora", pg.locator("#msg-depois").count() == 0 and "15:30" not in folha())
    if PAPEL == "tecnico":
        # 17: «O meu dia» às 15:00 e às 15:40
        pg.clock.set_system_time("2026-11-16T15:00:00+02:00"); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(1500)
        t1 = pg.inner_text("#meu-dia")
        pg.clock.set_system_time("2026-11-16T15:40:00+02:00"); pg.evaluate("desenharHoje()"); pg.wait_for_timeout(1500)
        t2 = pg.inner_text("#meu-dia")
        passo("17 equipa sem rega: 15:30 a cinzento, depois falta o motivo", "15:30" in t1 and "18:00" not in t1.split("Equipa Parada")[1][:80] and "15:30" not in t2.split("Equipa Parada")[1][:60],
              (t1.split("Equipa Parada")[1][:60] + " || " + t2.split("Equipa Parada")[1][:60]).replace("\n", " "))
    if PAPEL == "tecnico":
        pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(1500)
        t = pg.inner_text("#e-hoje")
        passo("11 «O meu dia» mostra a 🌱", "🌱" in t, [l for l in t.split("\n") if "🌱" in l][:2])
    pg.screenshot(path=f"/home/claude/rega-test/actividade_{PAPEL}_{LING}.png")
    ok = all(res.values()) and not erros
    print("RESULTADO:", "OK" if ok else "FALHOU")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
