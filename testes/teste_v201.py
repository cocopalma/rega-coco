# v201 (03/11/2026, Valdo): anular a aprovação de um plano da equipa (gestor: aprovado → por_gestor; supervisor: por_gestor →
# por_supervisor), motivo obrigatório; «Tempo da equipa por planta» em segundos. PAPEL=gestor|supervisor|tecnico; LING=en / sw.
import json, subprocess, time, sys, os
LING = os.environ.get("LING", "pt"); PAPEL = os.environ.get("PAPEL", "gestor")
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8901", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1 = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None}]
plano = {"id": "p1", "activista_id": A1, "activista": "Activista Um", "ronda": 2, "estado": "aprovado" if PAPEL == "gestor" else "por_gestor", "capacidade": 700, "pessoas": 5,
         "dias": [{"n": 1, "campos": [{"area_id": "PR1-1", "plantas": 70, "sem_coordenada": False}], "plantas": 70, "dist_m": 500, "minutos": 60}],
         "aprendizagem": {"ronda": 1, "pessoas": 5, "plantas_por_dia": 515, "dias_trabalhados": 3, "hora_inicio": "06:30", "hora_fim": "11:00", "min_por_planta": 0.2311},
         "supervisor_nome": "Sup Um", "gestor_nome": "Gestor" if PAPEL == "gestor" else None}
rec = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "g@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Pessoa Teste", "papel": PAPEL, "activista_id": None, "ve_tudo": False, "gere_acessos": True})
    if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Farol", "tecnico": "Tec", "supervisor": "Sup Um", "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([A1])
    if "/rpc/planos_lista" in u: return ok([plano])
    if "/rpc/anular_aprovacao_plano" in u:
        d = json.loads(r.post_data); rec.append(d); plano["estado"] = "por_gestor" if plano["estado"] == "aprovado" else "por_supervisor"; plano["gestor_nome"] = None; return ok(plano["estado"])
    if "/rpc/" in u: return ok([])
    return ok([])
erros = []
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    dialogos = []; pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.goto("http://localhost:8901/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "x"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
    pg.evaluate("ecraPlano('p1')"); pg.wait_for_timeout(400)
    t = pg.inner_text("#folha-c").replace("\n", " | ")
    print(f"1 {PAPEL} ({plano['estado']}):", t[:520])
    if pg.query_selector("#pl-anul"):
        n0 = len(dialogos); pg.evaluate("anularAprovacaoPlano('p1')"); pg.wait_for_timeout(300); print("2 sem motivo:", dialogos[n0:], "| pedidos:", len(rec))
        pg.fill("#pl-anul", "Tempo previsto irreal"); pg.evaluate("anularAprovacaoPlano('p1')"); pg.wait_for_timeout(1500)
        print("3 anulado:", rec, "| ecrã:", pg.inner_text("#folha-c").replace("\n"," | ")[:140], "| aviso:", pg.evaluate("(document.querySelector('#aviso')||{}).innerText||''"))
    else: print("2 sem botão de anular")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
