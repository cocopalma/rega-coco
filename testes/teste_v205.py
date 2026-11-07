# v205 (05/11/2026, Valdo): técnico/supervisor retiram um campo da rega (todas as mudas mortas / sem acesso). Baseado no teste da v204.
# v204 (05/11/2026, Valdo): primeiro os campos que nunca receberam água (nem na app, nem no WhatsApp). Enquanto a equipa tiver
# campos destes, um campo que já recebeu água só se rega com autorização do supervisor, para o dia de rega seguinte.
# Activista: cartão no Hoje, ordem da lista, etiqueta, bloqueio da entrada, entrada com autorização de hoje.
# Supervisor: cartão por equipa, «Autorizar a rega deste campo» (motivo obrigatório) → RPC autorizar_rega. LING=en / sw.
import json, subprocess, time, sys, os, datetime
LING = os.environ.get("LING", "pt")
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8899", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
HOJE = datetime.date.today().isoformat()
def A(i, lat, **k):
    b = {"id": f"PR{i}-1", "pr": f"PR{i}", "area_n": 1, "comunidade": "Farol", "produtor": f"Produtor {i}", "instaladas": 50, "vivas": 50, "latitude": lat, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None}
    b.update(k); return b
areas = [A(1, -10.6835, wa_ultima="2026-10-20", wa_n=3, wa_por_pr=False),      # regado no WhatsApp
         A(2, -10.6900),                                                # nunca regado
         A(3, -10.6950, wa_ultima="2026-10-25", wa_por_pr=True),       # WhatsApp só por produtor → nunca
         A(4, -10.6840, wa_ultima="2026-09-01", wa_por_pr=False)]      # regado há mais tempo
estado = [{"area_id": a["id"], "ultima_rega": None, "regas_app": 0, "plantas_app": 0, "ronda_actual": 1, "regada_na_ronda": False} for a in areas]
PAPEL = {"v": "activista"}; AUT = {"v": []}; rec = {"aut": []}
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Pessoa Teste", "papel": PAPEL["v"], "activista_id": ACT if PAPEL["v"] == "activista" else None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Um", "comunidade_principal": "Farol", "tecnico": "Tec", "supervisor": "Pessoa Teste", "activo": True}])
    if "/rest/v1/areas" in u: return ok([x for x in areas if x["id"] not in [r["p_area"] for r in rec.get("ret", [])]])
    if "/rpc/estado_ronda" in u: return ok(estado)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/autorizacoes_rega_lista" in u: return ok(AUT["v"])
    if "/rpc/retirar_da_rega" in u:
        rec.setdefault("ret", []).append(json.loads(r.post_data)); return ok("retirado")
    if "/rpc/autorizar_rega" in u:
        rec["aut"].append(json.loads(r.post_data)); return ok({"id": "33333333-3333-3333-3333-333333333333", "para_data": "2026-11-06"})
    return ok([])
erros = []
T = {"pt": ("Cheguei — marcar entrada", "Autorizar a rega deste campo", "Autorizar"),
     "en": ("record entry", "Authorise watering of this field", "Authorise"),
     "sw": ("andika kuwasili", "Idhinisha umwagiliaji wa shamba hili", "Idhinisha")}[LING]
def abrir(b, papel):
    PAPEL["v"] = papel
    ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate@0.2.8/**", lambda r: r.fulfill(path=f"{NM}/leaflet-rotate/dist/leaflet-rotate.js", content_type="application/javascript"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto("http://localhost:8899/"); pg.wait_for_selector("#l-entrar", state="visible")
    if papel != "activista": pg.evaluate("modoEntrada('tecnico')"); pg.fill("#l-user", "sup"); pg.fill("#l-senha", "12345678")
    else: pg.fill("#l-user", "act"); pg.fill("#l-pin", "123456")
    pg.click("#l-entrar"); pg.wait_for_timeout(2500)
    if pg.is_visible("#j-pessoas"): pg.fill("#j-pessoas", "3"); pg.click("#folha.on .btn >> nth=0"); pg.wait_for_timeout(800)
    if pg.is_visible("#folha.on"): pg.evaluate("fecharFolha()")
    return ctx, pg
txt = lambda pg, s="#folha-c": pg.inner_text(s).replace("\n", " | ")
T2 = {"pt": ("Retirar da rega (mudas mortas", "Todas as mudas mortas", "Retirar da rega"), "en": ("Remove from watering (dead", "All seedlings dead", "Remove from watering"), "sw": ("Ondoa kwenye umwagiliaji (miche", "Miche yote imekufa", "Ondoa kwenye umwagiliaji")}[LING]
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx, pg = abrir(b, "supervisor")
    pg.evaluate("abrirFicha('PR4-1')"); pg.wait_for_selector("#folha.on"); pg.wait_for_timeout(300)
    pg.click("#folha.on .fi-g.vermelho"); pg.wait_for_timeout(300)
    print("1 ecrã:", txt(pg)[:330])
    pg.screenshot(path=f"/home/claude/rega-test/v205_retirar{LING}.png", full_page=True)
    pg.click("#rt-ok"); pg.wait_for_timeout(200); print("2 sem motivo:", txt(pg, "#rt-msg"))
    pg.click(f"#rt-mot .chip:has-text('{T2[1]}')"); pg.fill("#rt-obs", "Secaram todas"); pg.click("#rt-ok"); pg.wait_for_timeout(50); print("3a logo a seguir:", pg.evaluate("S.areas.map(a=>a.id)"), txt(pg, "#aviso")[:60] if pg.query_selector("#aviso") else ""); pg.wait_for_timeout(1500)
    print("3 na lista do telefone:", pg.evaluate("S.areas.map(a=>a.id)"))
    pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    print("4 servidor recebeu:", rec.get("ret"), "| fila:", pg.evaluate("LS.get('filaAlt',[]).length"))
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(300)
    print("5 botão noutro campo:", pg.is_visible("#folha.on .fi-g.vermelho"))
    ctx.close()
    ctx, pg = abrir(b, "activista")
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_selector("#folha.on"); pg.wait_for_timeout(300)
    print("6 activista vê o botão:", pg.is_visible("#folha.on .fi-g.vermelho"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
