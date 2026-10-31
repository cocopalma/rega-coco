# Painel › Manutenção (v96, 22/10/2026). CLIENTE=1: null, secção escondida; LING=en / sw.
import json, subprocess, time, sys, os
sys.path.insert(0, "/home/claude/rega-test"); import harvest
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8824", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
D = {"gerado_em": "2026-10-18T19:00:00Z", "inicio": "2026-10-10", "universo": {"areas": 10, "vivas": 1000, "com_activista": 8}, "areas_regadas": 2, "vivas_regadas": 100,
     "plantas_regadas_total": 100, "pessoas_dia_total": 4, "registos": 2, "por_dia": [], "por_comunidade": [], "por_equipa": [], "chegadas_agua": [], "constrangimentos": {}}
R = [{"id": "r1", "area_id": "PR2-1", "pr": "PR2", "produtor": "Produtor Dois", "comunidade": "Farol", "instaladas": 70, "vivas_campo": 47, "motivo": "Queimada de 18/10/2026", "estado": "validada",
      "pedido_em": "2026-10-18T08:00:00Z", "validada_em": "2026-10-18T15:00:00Z", "contada_em": "2026-10-18T12:00:00Z", "oficial": "Assane Ali Saide", "vivas_antes": 60, "vivas": 47, "mortas": 13, "foto_path": "u/r1.jpg", "foto_campo_path": "u/r1-campo.jpg", "lat": -10.68, "lon": 40.63},
     {"id": "r2", "area_id": "PR1-1", "pr": "PR1", "produtor": "Produtor; Um", "comunidade": "Farol", "instaladas": 70, "vivas_campo": 70, "motivo": "Muitas mortas", "estado": "enviada",
      "pedido_em": "2026-10-18T09:00:00Z", "oficial": "Zaruque Momade", "vivas": None, "mortas": None, "foto_path": None},
     {"id": "r3", "area_id": "PR3-1", "pr": "PR3", "produtor": "Produtor Três", "comunidade": "Senga", "instaladas": 50, "vivas_campo": 40, "motivo": "Antiga", "estado": "por_encaminhar", "pedido_em": "2026-09-01T09:00:00Z"}]
sign = []
PL = [{"area_id": "PR228621-1", "pr": "PR228621", "produtor": "Mumino Issa Sumail", "comunidade": "Mondlane", "zona": None, "vivas_base": 820, "instaladas": 820, "marcadas": 290, "vivas": 280, "secas": 6, "mortas": 4, "cavaroda": 100, "mulching": 50, "ultima": "2026-10-16T10:26:06Z", "quem": "Nuro Antonio Culete"},
      {"area_id": "PR228470-1", "pr": "PR228470", "produtor": "Jemusse Ceia Mualia", "comunidade": "Senga", "zona": None, "vivas_base": 122, "instaladas": 140, "marcadas": 5, "vivas": 5, "secas": 0, "mortas": 0, "cavaroda": 0, "mulching": 0, "ultima": "2026-10-19T06:51:51Z", "quem": "Essumaila Carlos Assane"}]
TP = [{"id": "a", "nome": "Nuro Antonio Culete", "papel": "supervisor", "regas": 13, "dias": 5, "campos": 13, "fotos3": 3, "plantas": 1540, "chuva": 2, "ultima": "2026-10-20"},
      {"id": "b", "nome": "Guidion Cristovao", "papel": "tecnico", "regas": 1, "dias": 1, "campos": 1, "fotos3": 1, "plantas": 102, "chuva": 0, "ultima": "2026-10-20"},
      {"id": "c", "nome": "Idelson Anselmo", "papel": "supervisor", "regas": 0, "dias": 0, "campos": 0, "fotos3": 0, "plantas": 0, "chuva": 0, "ultima": None}]
pedidos = []
def mock(route):
    u = route.request.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/rpc/painel_manutencao" in u: return ok(None if os.environ.get("CLIENTE") else {"por_comunidade": [{"comunidade": "Farol", "campos": 72, "plantas": 6213, "cavaroda": 70, "mulching": 70, "feitos": 1, "completos": 0, "em_curso": 0, "por_fazer": 71}, {"comunidade": "Quiwia", "campos": 157, "plantas": 11417, "cavaroda": 0, "mulching": 0, "feitos": 0, "completos": 0, "em_curso": 0, "por_fazer": 157}], "por_dia": [{"data": "2026-10-22", "cavaroda": 70, "mulching": 70, "campos": 1, "pessoas": 24}]})
    if "/rpc/painel_testes" in u: pedidos.append(route.request.post_data); return ok(None if os.environ.get("CLIENTE") else TP)
    if "/rpc/painel_plantas_marcadas" in u: return ok(None if os.environ.get("CLIENTE") else PL)
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
    pg.goto("http://localhost:8824/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "g"); pg.fill("#l-pin", "x"); pg.click("#l-entrar"); pg.wait_for_selector("#s-rec", state="visible"); pg.wait_for_timeout(800)
    print("secção visível:", pg.is_visible("#s-man"))
    if pg.is_visible("#s-man"):
        print("título:", pg.inner_text("#s-man h2"), "| KPIs:", pg.inner_text("#k-man").replace(chr(10), " | "))
        print("comunidades:", pg.inner_text("#t-man-com").split(chr(10)))
        print("dias:", pg.inner_text("#t-man-dia").split(chr(10)))
        pg.locator("#s-man").screenshot(path="/home/claude/rega-test/painel_manut%s.png" % os.environ.get("LING", ""))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
