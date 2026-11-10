# v230 (10/11/2026, Biena pelo 💡): início do dia — «Outras pessoas» não conta os marcados nem o activista; aviso quando o total passa a equipa. LING=en / sw.
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8873", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1 = "11111111-1111-1111-1111-111111111111"; A2 = "33333333-3333-3333-3333-333333333333"; UID = "22222222-2222-2222-2222-222222222222"
hoje = datetime.date.today().isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Olumbe", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None},
         {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Olumbe", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": A2, "activista_proposto": None}]
M = [{"id": "m1", "activista_id": A1, "nome": "Ana Sazonal", "contrato": "Certo", "inicio": "2026-10-13", "fim": "2026-12-15", "presente_hoje": None},
     {"id": "m2", "activista_id": A1, "nome": "Bento Sazonal", "contrato": "Incerto", "inicio": "2026-02-16", "fim": None, "presente_hoje": None},
     {"id": "m3", "activista_id": A1, "nome": "Carla Sazonal", "contrato": "Incerto", "inicio": "2026-02-16", "fim": None, "presente_hoje": None},
     {"id": "m4", "activista_id": A2, "nome": "Dino Sazonal", "contrato": "Certo", "inicio": "2026-10-13", "fim": "2026-12-15", "presente_hoje": False},
     {"id": "m5", "activista_id": A2, "nome": "Eva Sazonal", "contrato": "Certo", "inicio": "2026-10-13", "fim": "2026-12-15", "presente_hoje": True}]
PAPEL = {"v": "activista"}; rec = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Tecnico Um" if PAPEL["v"] == "tecnico" else "Activista Um", "papel": PAPEL["v"], "activista_id": A1 if PAPEL["v"] == "activista" else None, "ve_tudo": False})
    if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Olumbe", "tecnico": "Tecnico Um", "supervisor": "Sup", "activo": True, "equipa_tamanho": 4}, {"id": A2, "nome": "Activista Dois", "comunidade_principal": "Olumbe", "tecnico": "Tecnico Um", "supervisor": "Sup", "activo": True, "equipa_tamanho": 3}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/membros_lista" in u: return ok([m for m in M if PAPEL["v"] == "tecnico" or m["activista_id"] == A1])
    if "/rpc/meus_activistas" in u: return ok([A1, A2])
    if "/rpc/gravar_presencas" in u: rec.append(("pres", json.loads(r.post_data))); return ok({"pessoas": 4})
    if "/rpc/gravar_membro" in u: rec.append(("membro", json.loads(r.post_data))); return ok({"id": "x"})
    if "/rest/v1/registos_rega" in u and PAPEL["v"] == "tecnico" and "count" not in (r.headers.get("prefer") or ""):
        return ok([{"id": "r1", "activista_id": A2, "area_id": "PR2-1", "plantas_regadas": 50, "pessoas": 2, "data": hoje, "entrada_em": hoje + "T06:00:00Z", "saida_em": hoje + "T07:00:00Z", "teste": False, "alerta": None, "agua_em": None}])
    if "/rest/v1/jornadas" in u: rec.append("jornada"); return ok([])
    if "/rpc/" in u: return ok([])
    return ok([])
erros = []; dial = []
def abrir(p, papel):
    PAPEL["v"] = papel
    ctx = p.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
    pg.goto("http://localhost:8873/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "u"); pg.fill("#l-pin", "123987" if papel == "activista" else "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1800)
    return ctx, pg
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx, pg = abrir(b, "activista")
    pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(800)
    pg.evaluate("ecraJornada()"); pg.wait_for_selector("#j-lista")
    print("1 nota outras:", pg.inner_text("#folha-c label >> nth=-1").split("\n")[:2])
    pg.check("#j-lista input[value=m1]"); pg.check("#j-lista input[value=m3]"); pg.wait_for_timeout(200)
    print("2 total (2 marcadas):", pg.inner_text("#j-total").replace("\n"," | "), "| aviso:", pg.locator("#j-acima").count())
    pg.fill("#j-outros", "3"); pg.wait_for_timeout(200)
    print("3 total (+3 outras, equipa 4):", pg.inner_text("#j-total").replace("\n"," | "), "| aviso:", pg.locator("#j-acima").count())
    pg.screenshot(path="/home/claude/rega-test/v230.png", full_page=True)
    pg.fill("#j-outros", "0"); pg.wait_for_timeout(200)
    print("4 de volta a 0:", pg.inner_text("#j-total").replace("\n"," | "), "| aviso:", pg.locator("#j-acima").count())
    pg.evaluate("guardarJornada('')"); pg.wait_for_timeout(2500)
    print("5 pessoas gravadas:", pg.evaluate("LS.get('jornada').pessoas"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
