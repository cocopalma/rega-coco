import json, subprocess, time, sys, os
LING = os.environ.get("LING", "pt"); PAPEL = os.environ.get("PAPEL", "activista")
from playwright.sync_api import sync_playwright

APP = "http://localhost:8766/"
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "--directory", "/home/claude/rega-coco"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
OUTRO = "33333333-3333-3333-3333-333333333333"
UID = "22222222-2222-2222-2222-222222222222"
areas = [
  {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-05-06"},
  {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 0, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-05-19"},
  {"id": "PR3-1", "pr": "PR3", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Tres", "instaladas": 50, "vivas": 48, "latitude": -10.6900, "longitude": 40.6400, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-04-01"},
  {"id": "PR4-1", "pr": "PR4", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Quatro", "instaladas": 40, "vivas": 40, "latitude": -10.6838, "longitude": 40.6343, "activista_id": OUTRO, "activista_proposto": None, "data_plantio": "2026-04-01"},
]
estado = [{"area_id": a["id"], "ultima_rega": "2026-10-01" if a["id"] == "PR3-1" else None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False} for a in areas]
recebidos = {"registos": [], "constr": [], "jornadas": [], "sugprox": [], "aprovar": []}
PLANO = {"id": "p1", "activista_id": ACT, "activista": "Majula Muemede Bacar", "supervisor": "Raul", "ronda": 1, "estado": "aprovado" if PAPEL == "activista" else "por_supervisor",
  "capacidade": 560, "pessoas": 4, "notas": "1 campo sem coordenada.", "criado_em": "2026-10-30T18:00:00Z",
  "aprendizagem": {"ronda": 0, "dias_trabalhados": 3, "pessoas": 4, "plantas_por_dia": 520, "hora_inicio": "07:20", "hora_fim": "13:10", "min_por_planta": 0.42},
  "dias": [{"n": 1, "campos": [{"area_id": "PR2-1", "plantas": 60}, {"area_id": "PR1-1", "plantas": 70}], "plantas": 130, "dist_m": 150, "minutos": 70},
           {"n": 2, "campos": [{"area_id": "PR3-1", "plantas": 48}], "plantas": 48, "dist_m": 0, "minutos": 20}]}
erros = []

def mock(route):
  try: _mock(route)
  except Exception as e: print("MOCK ERRO", e, route.request.url); route.fulfill(status=500, body="{}")
def _mock(route):
    r = route.request; u = r.url
    def ok(body, status=200): route.fulfill(status=status, content_type="application/json", body=json.dumps(body))
    corpo = lambda: (lambda x: x if isinstance(x, list) else [x])(json.loads(r.post_data))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600,
                   "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "majula@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Majula Muemede Bacar" if PAPEL == "activista" else "Raul Miquilange", "papel": PAPEL, "activista_id": ACT if PAPEL == "activista" else None, "gere_acessos": PAPEL == "gestor"})
    if "/rpc/registar_sugestoes_proximo" in u: recebidos["sugprox"] += json.loads(r.post_data)["p_lista"]; return ok(1)
    if "/rpc/planos_lista" in u: return ok([PLANO])
    if "/rpc/aprovar_plano" in u: recebidos["aprovar"].append(json.loads(r.post_data)); PLANO["estado"] = "por_gestor" if json.loads(r.post_data)["p_aprovar"] else "recusado"; PLANO["supervisor_nome"] = "Raul Miquilange"; return ok(PLANO["estado"])
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol"}, {"id": OUTRO, "nome": "Outro Activista", "comunidade_principal": "Farol"}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/estado_ronda" in u: return ok(estado)
    if "/rest/v1/registos_rega" in u:
        if r.method == "POST": recebidos["registos"] += corpo(); return route.fulfill(status=201, body="")
        return ok([x for x in recebidos["registos"] if x["plantas_regadas"] > 0])   # o servidor devolve o que recebeu
    if "/rpc/registar_sugestoes_proximo" in u: recebidos["sugprox"] += json.loads(r.post_data)["p_lista"]; return ok(1)
    if "/rest/v1/constrangimentos" in u: recebidos["constr"] += corpo(); return route.fulfill(status=201, body="")
    if "/rest/v1/jornadas" in u: recebidos["jornadas"] += corpo(); return route.fulfill(status=201, body="")
    return ok({})

def fechar_sugestao(pg):
    if pg.is_visible("button:has-text('Escolher outro campo')"): pg.click("button:has-text('Escolher outro campo')")
    elif pg.is_visible("#folha.on button:has-text('Fechar')"): pg.click("#folha.on button:has-text('Fechar')")

def regar(pg, area, plantas=None, agua=None, hora_agua=None):
    pg.click("nav button[data-e=lista]"); pg.click(f".item[data-id='{area}']"); pg.wait_for_selector("#folha.on")
    pg.click("text=Cheguei — marcar entrada"); pg.wait_for_selector("text=Entrada marcada", timeout=15000); fotos(pg)
    if agua == "agora": pg.click("text=Chegou a água (tuk-tuk) agora"); pg.wait_for_selector("text=Água (tuk-tuk) no campo")
    pg.click("text=Terminei — marcar saída")
    if plantas is None: plantas = pg.evaluate("(id) => plantasN(S.areas.find((a) => a.id === id))", area)   # o campo vem vazio desde a v85
    pg.fill("#s-plantas", str(plantas))
    if hora_agua: pg.fill("#s-agua", hora_agua)
    pg.click("text=Marcar saída e guardar"); pg.wait_for_selector("text=Rega guardada", timeout=15000)

def fotos(pg):   # fotografias obrigatórias da rega (15/10/2026): no teste guardam-se directamente
    pg.evaluate("(async()=>{for (const t of ['entrada','rega','saida']) await guardarFotoRega(t, new Blob(['x'],{type:'image/jpeg'})); abrirFicha(LS.get('emCurso').area_id)})()"); pg.wait_for_timeout(300)
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"], viewport={"width": 390, "height": 800})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page()
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.on("pageerror", lambda e: erros.append(str(e)))
    dialogos = []; pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.goto(APP); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "majula"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar")
    if PAPEL == "activista":
        pg.wait_for_selector("#j-pessoas", timeout=10000); pg.fill("#j-pessoas", "4"); pg.click("#folha.on .btn >> nth=0"); pg.wait_for_timeout(1200)
    else: pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)

    if PAPEL == "activista":
        pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(2000)
        print("1 itinerário no Hoje:", pg.inner_text("#hoje-itin").replace(chr(10), " | ") if pg.is_visible("#hoje-itin") else "NÃO")
        pg.click("nav button[data-e=mapa]"); pg.wait_for_timeout(500)
        print("2 números no mapa:", pg.evaluate("[...document.querySelectorAll('.leaflet-marker-icon div')].map(e=>e.innerText).join(',')"))
        ctx.set_geolocation({"latitude": -10.6900, "longitude": 40.6400}); pg.wait_for_timeout(1200)
        pg.evaluate("abrirFicha('PR3-1')"); pg.wait_for_timeout(300)
        pg.evaluate("marcarEntrada('PR3-1')"); pg.wait_for_timeout(500)
        print("3 fora do itinerário:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:260])
        pg.click("#it-ok"); pg.wait_for_timeout(200); print("   sem motivo →", dialogos[-1] if dialogos else "")
        pg.click("#it-mot .chip >> nth=4"); pg.click("#it-ok"); pg.wait_for_timeout(200); print("   outro sem texto →", dialogos[-1])
        pg.click("#it-mot .chip >> nth=0"); pg.click("#it-ok"); pg.wait_for_timeout(3000)
        print("4 emCurso:", pg.evaluate("(() => { const e = LS.get('emCurso'); return e && [e.area_id, e.plano_id, e.plano_dia, e.fora_itinerario, e.motivo_itinerario]; })()"))
        pg.evaluate("LS.del('emCurso')")
        # rega do 1.º campo do itinerário (PR2-1, a 119 m) → sugestão = PR1-1 (o seguinte do itinerário)
        ctx.set_geolocation({"latitude": -10.6842, "longitude": 40.6332}); pg.wait_for_timeout(1200)
        pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_timeout(300); pg.evaluate("marcarEntrada('PR2-1')"); pg.wait_for_timeout(3000)
        print("5 dentro do itinerário:", pg.evaluate("(() => { const e = LS.get('emCurso'); return e && [e.area_id, e.plano_dia, e.fora_itinerario]; })()"))
        fotos(pg); pg.evaluate("ecraSaida()"); pg.wait_for_selector("#s-plantas"); pg.fill("#s-plantas", "60"); pg.evaluate("marcarSaida()")
        try: pg.wait_for_function("!LS.get('emCurso')", timeout=12000)
        except Exception: pg.evaluate("ecraSaida()"); pg.fill("#s-plantas", "60"); pg.evaluate("marcarSaida()"); pg.wait_for_timeout(4000)
        pg.wait_for_timeout(800)
        print("6 sugestão:", pg.evaluate("LS.get('sugestao')?.area_id"), "| motivo registado:", [x.get("motivo") for x in recebidos["sugprox"]] or pg.evaluate("LS.get('filaSugProx', []).map(x=>x.motivo)"), "| registos enviados:", [(x["area_id"], x.get("plano_dia"), x.get("fora_itinerario")) for x in recebidos["registos"]])
    else:
        pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(2500)
        print("1 cartão dos planos:", pg.inner_text("#hoje-planos").replace(chr(10), " | ") if pg.is_visible("#hoje-planos") else "NÃO")
        pg.click("#hoje-planos .chip"); pg.wait_for_timeout(400)
        print("2 plano:", pg.inner_text("#folha-c").replace(chr(10), " | ")[:700])
        print("   botões:", [x for x in pg.locator("#folha-c .btn").all_inner_texts()])
        if pg.is_visible("text=✗ Recusar") or pg.locator("#folha-c .btn.aviso").count():
            pg.click("#folha-c .btn.aviso"); pg.wait_for_timeout(200); print("3 recusar sem motivo →", dialogos[-1] if dialogos else "")
            pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(1500); print("4 aprovar →", recebidos["aprovar"], "|", pg.inner_text("#folha-c").split(chr(10))[1])
        pg.evaluate("verPlanoMapa('p1')"); pg.wait_for_timeout(600)
        print("5 mapa do plano:", pg.evaluate("[...document.querySelectorAll('.leaflet-marker-icon div')].map(e=>e.innerText).join(',')"), "|", pg.inner_text("#sug-mapa").replace(chr(10), " | "))
        pg.screenshot(path="/home/claude/rega-test/plano_mapa.png")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate() if 'srv' in dir() else None
