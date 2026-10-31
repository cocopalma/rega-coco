import os
import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8784", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
areas = [
  {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None},
  {"id": "PR2-1", "pr": "PR2", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Dois", "instaladas": 60, "vivas": 60, "latitude": -10.6842, "longitude": 40.6332, "activista_id": ACT, "activista_proposto": None},
]
lista = [{"amostra_id": "a1", "data_rega": "2026-10-11", "area_id": "PR1-1", "activista_id": ACT, "feita": False},
         {"amostra_id": "a2", "data_rega": "2026-10-11", "area_id": "PR2-1", "activista_id": ACT, "feita": False}]
rec = {"fotos": [], "mon": [], "n": []}
erros = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u-tec", "aud": "authenticated", "role": "authenticated", "email": "guidion@rega-coco.example.com"}})
    if "/storage/v1/object/monitoria-fotos/" in u: rec["fotos"].append((u.split("monitoria-fotos/")[1], len(r.post_data_buffer or b""))); return ok({"Key": "monitoria-fotos/x"})
    if "/rest/v1/perfis" in u: return ok({"id": "u-tec", "nome": "Guidion Cristovao", "papel": "tecnico", "activista_id": None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol", "equipa_tamanho": None}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/monitoria_lista" in u: return ok(lista)
    if "/rpc/monitorias_campo" in u: return ok([{"id": "m9", "data_rega": "2026-10-10", "feito_em": "2026-10-11T07:00:00Z", "verificador": "Raul", "nota": 6.5, "pct_humido": 65, "solo_regado": False, "metodo": "X", "plantas_obs": 31, "foto_path": "u-tec/m9.jpg"}])
    if "/storage/v1/object/sign/monitoria-fotos/" in u: rec.setdefault("sign", []).append(u); return ok({"signedURL": "/storage/v1/object/sign/monitoria-fotos/u-tec/m9.jpg?token=t"})
    if "/storage/v1/object/sign/" in u and "token=" in u: return route.fulfill(status=200, content_type="image/jpeg", body=open("/home/claude/rega-test/foto_teste.jpg","rb").read())
    if "/rpc/avisos_monitoria" in u: return ok([{"id": "m8", "area_id": "PR1-1", "activista_id": ACT, "data_rega": "2026-10-10", "feito_em": "2026-10-11T07:00:00Z", "verificador": "Raul", "nota": 8.4, "pct_humido": 84, "solo_regado": True, "plantas_obs": 37, "sem_rega": 6, "observacao": None}, {"id": "m7", "area_id": "PR2-1", "activista_id": ACT, "data_rega": "2026-10-10", "feito_em": "2026-10-11T07:00:00Z", "verificador": "Raul", "nota": 9.5, "pct_humido": 95, "solo_regado": True, "plantas_obs": 21, "sem_rega": 1, "observacao": None}])
    if "/rpc/estado_ronda" in u: return ok([])
    if "/rpc/definir_equipa_tamanho" in u: rec["n"].append(json.loads(r.post_data)); return ok(None)
    if "/rest/v1/monitorias" in u and r.method == "POST":
        b = json.loads(r.post_data); rec["mon"].append(b); return route.fulfill(status=201, body="")
    if "/rest/v1/registos_rega" in u: return ok([{"activista_id": ACT, "area_id": "PR1-1", "plantas_regadas": 70, "alerta": None, "gps_valido": True, "teste": False, "entrada_em": "2026-10-11T04:40:00Z", "saida_em": "2026-10-11T05:20:00Z", "pessoas": 5, "agua_em": "2026-10-11T05:05:00Z"},
        {"activista_id": ACT, "area_id": "PR2-1", "plantas_regadas": 60, "alerta": None, "gps_valido": True, "teste": False, "entrada_em": "2026-10-11T05:30:00Z", "saida_em": "2026-10-11T06:15:00Z", "pessoas": 4, "agua_em": None}])
    if "/rest/v1/zonas" in u: return ok([])
    return ok({})
def plantas(sim, nao, morta=0, estado_nao='viva'):
    for i in range(sim): pg.click("#m-h .chip[data-v='1']"); pg.click("#m-e .chip[data-v='viva']"); pg.click(f"#m-c .chip[data-v='{['ambos','mulching','cava','nenhum'][i % 4]}']")
    for _ in range(nao): pg.click("#m-h .chip[data-v='0']"); pg.click(f"#m-e .chip[data-v='{estado_nao}']"); pg.click("#m-c .chip[data-v='nenhum']")
    for _ in range(morta): pg.click("#m-h .chip[data-v='0']"); pg.click("#m-e .chip[data-v='morta']"); pg.click("#m-c .chip[data-v='nenhum']")
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"], viewport={"width": 390, "height": 844})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (print("DIALOGO:", d.message), d.accept()))
    pg.goto("http://localhost:8784/"); (pg.evaluate("l => localStorage.setItem('rega.lingua', l)", os.environ["LING"]), pg.reload()) if os.environ.get("LING") else None; pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "guidion"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("text=/Avisos da monitoria|Monitoring alerts|Tahadhari za ufuatiliaji/", timeout=15000)
    print("0 tabela:", pg.inner_text("#hoje table"))
    print("1a avisos:", pg.inner_text("#hoje .cartao >> nth=0").replace("\n", " | "))
    pg.evaluate("abrirFicha('PR1-1')"); pg.wait_for_timeout(400); print("2 ficha:", [m for m in pg.locator("#folha-c .msg").all_inner_texts() if 'onitori' in m or 'onitoring' in m or 'Ufuatiliaji' in m or 'ufuatiliaji' in m][:1])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
