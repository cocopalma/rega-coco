# v163 (31/10/2026, Valdo: "Sim"): a rega fica com o campo. Campo regado por outra equipa antes de passar para esta
# conta na ronda desta equipa (RPC regas_outra_equipa). PAPEL=activista (padrão) / tecnico; LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
LING = os.environ.get("LING", "pt"); PAPEL = os.environ.get("PAPEL", "activista")
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8863", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
def ar(i): return {"id": f"PR{i}-1", "pr": f"PR{i}", "area_n": 1, "comunidade": "Olumbe", "produtor": f"Produtor {i}", "instaladas": 60, "vivas": 60, "latitude": -10.68 - i * .001, "longitude": 40.63, "activista_id": ACT}
areas = [ar(1), ar(2), ar(3)]
estado = [{"area_id": "PR1-1", "ultima_rega": "2026-10-30", "regas_app": 1, "ronda_actual": 1, "regada_na_ronda": True},
          {"area_id": "PR2-1", "ultima_rega": "2026-10-29", "regas_app": 1, "ronda_actual": 1, "regada_na_ronda": True},
          {"area_id": "PR3-1", "ultima_rega": None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False}]
meus = [{"id": "r1", "area_id": "PR1-1", "activista_id": ACT, "apoio_para": None, "data": "2026-10-30", "ronda": 1, "plantas_regadas": 60, "teste": False, "campo_fechado": True}]
outras = [{"area_id": "PR2-1", "ronda": 1, "data": "2026-10-29", "campo_fechado": None, "plantas": 60, "quem": "Ibraimo Ali Selemane"}]
erros = []
def mock(route):
    r = route.request; u = r.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Atoquei Teste" if PAPEL == "activista" else "Manuel Teste", "papel": PAPEL, "activista_id": ACT if PAPEL == "activista" else None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Atoquei Abudo Jamardine", "comunidade_principal": "Olumbe", "tecnico": "Manuel Teste", "supervisor": "Nuro", "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/estado_ronda" in u: return ok(estado)
    if "/rpc/regas_outra_equipa" in u: return ok(outras)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/minhas_comunidades" in u: return ok(["Olumbe"])
    if "/rest/v1/registos_rega" in u and r.method == "HEAD": return route.fulfill(status=200, headers={"content-range": "0-0/3"}, body="")
    if "/rest/v1/registos_rega" in u: return ok(meus)
    if "/rpc/" in u: return ok([])
    return ok({})
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(geolocation={"latitude": -10.681, "longitude": 40.63}, permissions=["geolocation"], viewport={"width": 390, "height": 800})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate@0.2.8/**", lambda r: r.fulfill(path=f"{NM}/leaflet-rotate/dist/leaflet-rotate-src.js", content_type="application/javascript"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.add_init_script("localStorage.setItem('rega.lingua', %r)" % LING); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8863/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "x"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar"); pg.wait_for_timeout(3500)
    pg.evaluate("fecharFolha && fecharFolha()")
    print("1 situação:", pg.evaluate("S.areas.map(a => a.id + ': ' + situacao(a).txt).join(' | ')"))
    if PAPEL == "activista": print("2 ronda:", pg.evaluate("JSON.stringify((({n, feitas, total}) => ({n, feitas: [...feitas], total}))(rondaInfo(S.perfil.activista_id)))"))
    pg.evaluate("abrirFicha('PR2-1')"); pg.wait_for_selector("#folha.on"); pg.wait_for_timeout(400)
    t = pg.inner_text("#folha-c"); i = t.find("🔁"); print("3 ficha PR2:", t[i:i + 200].replace("\n", " ") if i >= 0 else "SEM LINHA")
    pg.evaluate("fecharFolha()"); pg.evaluate("abrirFicha('PR3-1')"); pg.wait_for_timeout(400)
    print("4 ficha PR3 sem linha:", "🔁" not in pg.inner_text("#folha-c"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
