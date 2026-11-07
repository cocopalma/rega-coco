# v197 (02/11/2026, Valdo: "Muda, mas o técnico e supervisor devem confirmar. Cria esta confirmação obrigatória"):
# «O meu dia» › 8. Nomes de produtores por confirmar; o nome só muda quando o técnico E o supervisor confirmam. LING=en / sw.
import json, subprocess, time, sys, os, datetime
SEC = lambda pg, k: (pg.inner_text(f"#meu-dia details[data-k={k}]") if pg.locator(f"#meu-dia details[data-k={k}]").count() else "(sem linha "+k+")")
NB = lambda pg, k: (pg.inner_text(f"#meu-dia details[data-k={k}] .nb") if pg.locator(f"#meu-dia details[data-k={k}] .nb").count() else "(sem linha)")
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8897", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1 = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
hoje = datetime.date.today().isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Chane Velho", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None}]
est = {"tec": None, "sup": "2026-11-02T10:00:00Z", "estado": "por_confirmar"}; rec = []
def lista():
    return [{"id": "c1", "area_id": "PR1-1", "pr": "PR1", "nome_antigo": "Chane Velho", "nome_novo": "Chane Novo", "motivo": "Pedido do activista", "estado": est["estado"],
             "equipa": "Activista Um", "comunidade": "Farol", "tecnico_em": est["tec"], "tecnico_nome": "Tecnico Um" if est["tec"] else None,
             "supervisor_em": est["sup"], "supervisor_nome": "Sup Um" if est["sup"] else None, "posso": est["tec"] is None and est["estado"] == "por_confirmar"}]
md = {"data": hoje, "hora_chegada": "06:00", "fechado_em": None, "equipas": [{"id": A1, "nome": "Activista Um", "regas": 1, "plantas": 70}], "alertas": [], "monitoria_hoje": 0, "monitoria_falhas_ontem": 0, "sem_equipa": 0, "por_aprovar": [], "por_terminar": []}
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Tecnico Um", "papel": "tecnico", "activista_id": None, "ve_tudo": False})
    if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Farol", "tecnico": "Tecnico Um", "supervisor": "Sup Um", "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([A1])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/meu_dia" in u: return ok(md)
    if "/rpc/correccoes_nome_lista" in u: return ok(lista())
    if "/rpc/confirmar_correccao_nome" in u:
        d = json.loads(r.post_data); rec.append(d)
        if not d["p_confirmar"]: est["estado"] = "recusada"; return ok({"estado": "recusada"})
        est["tec"] = "2026-11-02T11:00:00Z"; est["estado"] = "aplicada"; areas[0]["produtor"] = "Chane Novo"; return ok({"estado": "aplicada"})
    if "/rpc/" in u: return ok([])
    return ok([])
erros = []
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8897/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "tec"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1800)
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(600)
    s8 = SEC(pg, "cn")
    print("1 secção 8:", s8.replace("\n", " | ")[:300])
    pg.click("#meu-dia button[onclick*=ecraCorrNome]"); pg.wait_for_timeout(500)
    print("2 ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:400])
    pg.click("#cn-nao"); pg.wait_for_timeout(300)
    print("3 recusar sem motivo:", pg.inner_text("#cn-msg"), "| pedidos:", len(rec))
    pg.click("#cn-ok"); pg.wait_for_timeout(1500)
    print("4 confirmar:", rec[-1] if rec else None, "| aviso:", pg.evaluate("(document.querySelector('#aviso')||{}).innerText||''"))
    print("5 nome no telefone:", pg.evaluate("S.areas.find(a=>a.id==='PR1-1').produtor"))
    print("6 secção 8 depois:", "sem secção 8 (OK)" if pg.locator("#meu-dia details[data-k=cn]").count() == 0 or NB(pg, "cn") == "0" else SEC(pg, "cn")[:120])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
