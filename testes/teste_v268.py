# v268 (27/11/2026, Valdo): campos fora da rega (retirados e fora do plano), só para o gestor principal.
# GERE=0: perfil sem perfis.ve_campos_projecto: não vê nada disto nem pede os campos. PAPEL=gestor/supervisor (perfil a testar). LING=en / sw para as outras línguas.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt"); GERE = os.environ.get("GERE", "1") == "1"; PAPEL = os.environ.get("PAPEL", "gestor")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8868", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
AREAS = [{"id": "PR100-1", "pr": "PR100", "area_n": 1, "comunidade": "Senga", "produtor": "Activo Um", "instaladas": 100, "vivas": 90, "latitude": -10.835, "longitude": 40.454, "activista_id": None},
         {"id": "PR101-1", "pr": "PR101", "area_n": 1, "comunidade": "Senga", "produtor": "Activo Dois", "instaladas": 80, "vivas": 80, "latitude": -10.836, "longitude": 40.455, "activista_id": None}]
POL = [[40.4537, -10.8350], [40.4540, -10.8350], [40.4540, -10.8353], [40.4537, -10.8353], [40.4537, -10.8350]]
PROJ = [
  {"id": "PR2034331-1", "pr": "PR2034331", "area_n": 1, "comunidade": "Senga", "zona": None, "produtor": "Pita Constancio Tiago", "instaladas": 172, "vivas": 172, "latitude": -10.835085, "longitude": 40.453773,
   "activista_id": "a1", "activista": "Julia Jaime", "poligono": POL, "area_m2": 6639, "area_medida": False, "wa_n": 2, "wa_ultima": "2026-10-15", "wa_por_pr": False, "nao_existe": False,
   "situacao": "retirado", "retirado_em": "2026-11-16T09:31:07+00:00", "retirado_motivo": "mudas_mortas", "retirado_texto": "Retirado da rega na app: Todas as mudas mortas: O campo não dispõe nenhuma planta.",
   "retirado_por": "Essumaila Carlos Assane", "regas_app": 1, "dias_app": 0, "ultima_app": "2026-11-16", "plantas_app": 0},
  {"id": "PR900-2", "pr": "PR900", "area_n": 2, "comunidade": "Olumbe", "produtor": "Campo Que Nao Existe", "instaladas": 80, "vivas": 0, "latitude": -10.96, "longitude": 40.45,
   "activista_id": None, "activista_origem": "Fulano", "nao_existe": True, "situacao": "retirado", "retirado_em": "2026-10-31T10:00:00+00:00", "retirado_texto": "Não existe", "regas_app": 0},
  {"id": "PR800-1", "pr": "PR800", "area_n": 1, "comunidade": "Quiwia", "produtor": "Fora Do Plano", "instaladas": 50, "vivas": 40, "latitude": -10.70, "longitude": 40.52,
   "activista_id": None, "activista_origem": "Beltrano", "agua_origem": "COM", "nao_existe": False, "situacao": "fora", "regas_app": 0, "n_regas_origem": 3, "ultima_rega_origem": "2026-09-20"}]
REGAS = [{"id": "r1", "data": "2026-11-16", "entrada_em": "2026-11-16T05:07:18Z", "saida_em": "2026-11-16T07:47:34Z", "plantas_regadas": 0, "quem": "Julia Jaime", "teste": False}]
rec = {}; erros = []; falhas = []
def verif(c, txt):
    print(("OK  " if c else "FALHA ") + txt)
    if not c: falhas.append(txt)
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u-g", "aud": "authenticated", "role": "authenticated", "email": "valdo@rega-coco.example.com"}})
    if "/auth/v1/logout" in u: return route.fulfill(status=204, body="")
    if "/rest/v1/perfis" in u: return ok({"id": "u-g", "nome": "Valdo", "papel": PAPEL, "gere_acessos": PAPEL == "gestor", "ve_campos_projecto": GERE, "activista_id": None})
    if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
    if "/rpc/campos_projecto" in u: rec["proj"] = rec.get("proj", 0) + 1; return ok(PROJ if GERE else None)
    if "/rpc/regas_campo" in u: rec["regas"] = json.loads(r.post_data or "{}").get("p_area"); return ok(REGAS)
    if "/rpc/sugestoes_lista" in u: return ok({"sugestoes": [], "problemas": []})
    if "/rpc/" in u: return ok([])
    if "/rest/v1/areas" in u: return ok(AREAS)
    if "/rest/v1/activistas" in u or "/rest/v1/registos_rega" in u: return ok([])
    return ok({})
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, timezone_id="Africa/Maputo", geolocation={"latitude": -10.835, "longitude": 40.454}, permissions=["geolocation"])
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(path=f"{NM}/leaflet-rotate/dist/leaflet-rotate-src.js", content_type="application/javascript"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e) + " | " + (e.stack or "")[:300])); pg.on("dialog", lambda d: d.accept())
    pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING)
    pg.goto("http://localhost:8868/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "valdo"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.wait_for_timeout(2000)
    pg.evaluate("fecharFolha && fecharFolha(); mudar('mapa')"); pg.wait_for_timeout(500)
    pg.click("#b-ferr"); pg.wait_for_timeout(200)
    if not GERE:
        verif(not pg.is_visible("#b-proj"), "G1 perfil sem ve_campos_projecto: sem «Campos fora da rega» nas Ferramentas")
        pg.evaluate("mudar('lista')"); pg.wait_for_timeout(300); pg.click("#f-btn"); pg.wait_for_timeout(300)
        verif(not pg.is_visible("#f-proj-c"), "G2 sem «Campos do projecto» nos filtros")
        verif(rec.get("proj", 0) == 0, "G3 não pede os campos fora da rega ao servidor")
        pg.evaluate("setProj('ret')"); pg.wait_for_timeout(400)
        verif(pg.locator('#lista .item[data-id="PR2034331-1"]').count() == 0 and pg.locator("#proj-msg").count() == 0, "G4 mesmo chamando à força, nenhum campo fora da rega")
    else:
        verif(pg.is_visible("#b-proj"), "1 Ferramentas › «🗂 Campos fora da rega»")
        verif(rec.get("proj", 0) == 1, "2 pede os campos fora da rega uma vez ao abrir")
        pg.click("#b-proj"); pg.wait_for_timeout(400)
        t = pg.inner_text("#folha-c")
        verif(pg.locator("#folha-c [id^=pj-]").count() == 4 and "(2)" in t and "(1)" in t and "(5)" in t, "3 escolha com 4 opções e os números (na rega 2, retirados 2, fora do plano 1, todos 5)")
        pg.click("#pj-ret"); pg.wait_for_timeout(600)
        n_mapa = pg.evaluate("(()=>{let n=0;camada.eachLayer(l=>{if(l instanceof L.CircleMarker)n++});return n})()")
        verif(n_mapa == 2, f"4 mapa: só os 2 retirados ({n_mapa})")
        verif(pg.is_visible("#ronda-info") and "(2)" in pg.inner_text("#ronda-info"), "5 faixa no mapa com o número e «Só os campos na rega»")
        verif(pg.is_visible("#leg-proj") or pg.evaluate("$('#leg-proj').style.display===''"), "6 legenda dos retirados")
        pg.evaluate("mudar('lista')"); pg.wait_for_timeout(400)
        verif(pg.locator("#lista .item").count() == 2 and pg.is_visible("#proj-msg"), "7 lista: os 2 retirados, com o aviso «só para ver»")
        it = pg.locator('#lista .item[data-id="PR2034331-1"]')
        verif(it.count() == 1 and "16/11/2026" in it.inner_text() and "Essumaila" in it.inner_text(), "8 etiqueta com a data e quem retirou")
        verif(pg.locator('#lista .item[data-id="PR900-2"] .tag').filter(has_text="❓").count() == 1, "9 campo que não existe com ❓")
        it.click(); pg.wait_for_timeout(800)
        f = pg.inner_text("#folha-c")
        verif("Pita Constancio Tiago" in f and pg.locator("#fp-sit").count() == 1 and pg.locator("#fp-motivo").count() == 1, "10 ficha do campo retirado com a situação e o motivo")
        verif("6" in f and "639" in f and "Julia Jaime" in f, "11 ficha com a área e o activista")
        verif(pg.locator("#folha-c button", has_text="Cheguei").count() == 0 and pg.locator("#folha-c button", has_text="Retirar").count() == 0, "12 só para ver: sem entrada nem «Retirar»")
        pg.wait_for_timeout(600)
        verif(rec.get("regas") == "PR2034331-1" and pg.locator("#f-regas .cartao").count() == 1, "13 regas do campo carregadas")
        verif(pg.locator("#f-regas button", has_text="Corrigir").count() == 0, "14 sem «Corrigir as plantas regadas»")
        pg.screenshot(path=f"/home/claude/rega-test/v268_ficha_{LING}.png", full_page=True)
        pg.evaluate("fecharFolha(); setProj('fora')"); pg.wait_for_timeout(400)
        verif(pg.locator("#lista .item").count() == 1, "15 «Fora do plano de rega»: 1")
        pg.locator('#lista .item[data-id="PR800-1"]').click(); pg.wait_for_timeout(500)
        f2 = pg.inner_text("#folha-c")
        verif("Beltrano" in f2 and "COM" in f2, "16 ficha fora do plano: activista da lista de 09/10 e água")
        pg.evaluate("fecharFolha(); setProj('proj')"); pg.wait_for_timeout(400)
        verif(pg.locator("#lista .item").count() == 5, "17 «Todos os campos do projecto»: 2 + 3")
        pg.screenshot(path=f"/home/claude/rega-test/v268_lista_{LING}.png", full_page=True)
        pg.fill("#f-txt", "pita"); pg.dispatch_event("#f-txt", "input"); pg.wait_for_timeout(400)
        verif(pg.locator("#lista .item").count() == 1, "18 procura por nome encontra o campo retirado")
        pg.evaluate("$('#f-txt').value='';setProj('rega')"); pg.wait_for_timeout(400)
        verif(pg.locator("#lista .item").count() == 2 and pg.locator("#proj-msg").count() == 0, "19 de volta: só os campos na rega")
        pg.evaluate("mudar('mapa')"); pg.wait_for_timeout(300)
        n2 = pg.evaluate("(()=>{let n=0;camada.eachLayer(l=>{if(l instanceof L.CircleMarker)n++});return n})()")
        verif(n2 == 2 and not pg.is_visible("#ronda-info"), f"20 mapa de volta aos campos na rega ({n2})")
        pg.evaluate("abrirFicha('PR2034331-1')"); pg.wait_for_timeout(300)
        verif("Pita" in pg.inner_text("#folha-c"), "21 abrir a ficha de um retirado com a vista normal")
        pg.click("#folha-c button:has-text('📍')"); pg.wait_for_timeout(600)
        n3 = pg.evaluate("(()=>{let n=0;camada.eachLayer(l=>{if(l instanceof L.CircleMarker)n++});return n})()")
        verif(n3 == 5, f"22 «Ver no mapa» mostra os campos fora da rega ({n3})")
        if LING != "pt":
            pg.evaluate("setProj('ret'); mudar('lista')"); pg.wait_for_timeout(300); pg.locator('#lista .item[data-id="PR2034331-1"]').click(); pg.wait_for_timeout(400)
            t2 = pg.inner_text("#folha-c") + pg.inner_text("#lista")
            for pt in ["Retirado da rega", "só para ver", "Regas na app", "Registo do WhatsApp", "Para o pôr de volta", "Campo fora da rega", "Retirado a"]:
                verif(pt not in t2, f"T traduzido: «{pt}»")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("FALHAS:", falhas if falhas else "nenhuma")
sys.exit(1 if falhas else 0)
