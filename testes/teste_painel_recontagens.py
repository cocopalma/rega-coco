# Painel › Recontagens das plantas: indicadores, tabela, fotografia e descarga para Excel (18/10/2026)
import json, subprocess, time, sys, os
sys.path.insert(0, "/home/claude/rega-test"); import harvest
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8813", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
D = {"gerado_em": "2026-10-18T19:00:00Z", "inicio": "2026-10-10", "universo": {"areas": 10, "vivas": 1000, "com_activista": 8}, "areas_regadas": 2, "vivas_regadas": 100,
     "plantas_regadas_total": 100, "pessoas_dia_total": 4, "registos": 2, "por_dia": [], "por_comunidade": [], "por_equipa": [], "chegadas_agua": [], "constrangimentos": {}}
R = [{"id": "r1", "area_id": "PR2-1", "pr": "PR2", "produtor": "Produtor Dois", "comunidade": "Farol", "instaladas": 70, "vivas_campo": 47, "motivo": "Queimada de 18/10/2026", "estado": "validada",
      "pedido_em": "2026-10-18T08:00:00Z", "validada_em": "2026-10-18T15:00:00Z", "contada_em": "2026-10-18T12:00:00Z", "oficial": "Assane Ali Saide", "vivas_antes": 60, "vivas": 47, "mortas": 13, "foto_path": "u/r1.jpg", "foto_campo_path": "u/r1-campo.jpg", "lat": -10.68, "lon": 40.63},
     {"id": "r2", "area_id": "PR1-1", "pr": "PR1", "produtor": "Produtor; Um", "comunidade": "Farol", "instaladas": 70, "vivas_campo": 70, "motivo": "Muitas mortas", "estado": "enviada",
      "pedido_em": "2026-10-18T09:00:00Z", "oficial": "Zaruque Momade", "vivas": None, "mortas": None, "foto_path": None},
     {"id": "r3", "area_id": "PR3-1", "pr": "PR3", "produtor": "Produtor Três", "comunidade": "Senga", "instaladas": 50, "vivas_campo": 40, "motivo": "Antiga", "estado": "por_encaminhar", "pedido_em": "2026-09-01T09:00:00Z"}]
sign = []
def mock(route):
    u = route.request.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/rpc/recontagens_lista" in u: return ok(R)
    if "/rpc/painel_resumo" in u: return ok(D)
    if "/rpc/painel_monitoria" in u: return ok(None)
    if "/storage/v1/object/sign/recontagem-fotos/" in u: sign.append(u.split("recontagem-fotos/")[1]); return ok({"signedURL": "/object/sign/recontagem-fotos/u/r1.jpg?token=t"})
    if "/storage/v1/object/sign/" in u and "token=" in u: return route.fulfill(status=200, content_type="image/jpeg", body=open("/home/claude/rega-test/foto_teste.jpg", "rb").read())
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "g@rega-coco.example.com"}})
    if "/rpc/" in u: return ok([])
    return ok({})
erros = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8813/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "g"); pg.fill("#l-pin", "x"); pg.click("#l-entrar"); pg.wait_for_selector("#s-rec", state="visible"); pg.wait_for_timeout(800)
    print("tudo KPIs:", pg.inner_text("#k-rec").replace("\n", " | "))
    print("tabela:", [l for l in pg.inner_text("#t-rec").split("\n")][:4])
    pg.click("#t-rec .foto-btn"); pg.wait_for_timeout(700); print("foto:", pg.locator("img[src*=token]").count(), sign); pg.mouse.click(10, 10)
    with pg.expect_download() as d: pg.click("#b-rec-csv")
    f = d.value; caminho = f.path(); txt = open(caminho, encoding="utf-8-sig").read()
    print("csv:", f.suggested_filename, "| linhas:", len(txt.strip().split("\n")), "|", txt.split("\n")[0][:80]); print("csv l2:", txt.split("\n")[1][:140]); print("csv aspas:", [l for l in txt.split("\n") if "Um" in l][0][:60])
    pg.click("#filtro [data-p='7']"); pg.wait_for_timeout(800); print("7 dias KPIs:", pg.inner_text("#k-rec").split("\n")[:2])
    pg.locator("#s-rec").screenshot(path=f"/home/claude/rega-test/painel_recontagens{os.environ.get('LING','')}.png")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
