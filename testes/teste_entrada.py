import json, subprocess, sys, time
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8780", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
PAPEL = {"papel": "cliente"}
def mock(route):
    u = route.request.url
    ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time())+3600, "refresh_token": "r", "user": {"id": "u1", "aud": "authenticated", "role": "authenticated", "email": "c@rega-coco.example.com"}})
    if "/auth/v1/logout" in u: return route.fulfill(status=204, body="")
    if "/rest/v1/perfis" in u: return ok({"id": "u1", "nome": "Pessoa Teste", "papel": PAPEL["papel"], "activista_id": None})
    if "/rest/v1/" in u or "/rpc/" in u: return ok([])
    return ok({})
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}); erros = []
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
    pg.goto("http://localhost:8780/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.click("#l-pin"); pg.keyboard.type("123"); vis = lambda s: pg.is_visible(s)
    print("1 activista: PIN visível", vis("#l-pinbox"), "| senha visível", vis("#l-senhabox"), "| caixas:", pg.eval_on_selector_all(".l-pin i", "e=>e.map(x=>x.textContent||'_').join('')"))
    pg.screenshot(path="/home/claude/rega-test/entrada_activista.png")
    pg.click(".l-seg button[data-m=tecnico]"); print("2 técnico: PIN", vis("#l-pinbox"), "| senha", vis("#l-senhabox"), "| nota:", pg.inner_text("#l-nota"))
    pg.fill("#l-senha", "abc12345"); pg.click("#l-mostrar"); print("   mostrar →", pg.get_attribute("#l-senha", "type")); pg.screenshot(path="/home/claude/rega-test/entrada_tecnico.png")
    pg.click("text=Outros acessos (escritório)"); print("3 escritório:", vis("#l-escr"), "| campo:", vis("#l-campo")); pg.screenshot(path="/home/claude/rega-test/entrada_escritorio.png")
    pg.fill("#le-user", "cliente1"); pg.fill("#le-senha", "segredo123"); pg.click("#le-entrar"); pg.wait_for_selector("#app", state="visible")
    print("4 cliente entrou: separadores visíveis =", [x for x in pg.eval_on_selector_all("#nav button", "e=>e.filter(b=>b.offsetParent).map(b=>b.textContent)")])
    pg.click("#h-sair"); pg.wait_for_selector("#le-entrar", state="visible", timeout=10000); print("5 depois de sair abre no escritório:", vis("#l-escr"))
    pg.click("text=Voltar ao acesso de campo"); PAPEL["papel"] = "supervisor"; pg.click(".l-seg button[data-m=tecnico]")
    pg.fill("#l-user", "nuro"); pg.fill("#l-senha", "abc12345"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.click("#h-sair"); pg.wait_for_selector("#l-entrar", state="visible", timeout=10000)
    print("6 supervisor: depois de sair abre no campo/técnico:", vis("#l-campo"), vis("#l-senhabox"))
    pg.click("#lc-lingua"); pg.click("#menu-lingua [data-l='" + pg.evaluate("(()=>{const L=['pt','en','sw'];let c='pt';try{c=localStorage.getItem('rega.lingua')||'pt'}catch(e){};return L[(L.indexOf(c)+1)%3]})()") + "']"); pg.wait_for_selector("#l-entrar", state="visible"); pg.wait_for_timeout(500)
    print("7 EN:", pg.inner_text("#l-campo").replace("\n", " | ")); pg.screenshot(path="/home/claude/rega-test/entrada_en.png")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
