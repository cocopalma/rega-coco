# Escolher a língua numa lista (18/10/2026, Valdo): de PT directamente para SW e de SW directamente para PT
import subprocess, sys, time
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8812", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
erros = []
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844})
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8812/"); pg.wait_for_selector("#l-entrar", state="visible")
    print("1 botão:", pg.inner_text("#lc-lingua"))
    pg.click("#lc-lingua"); print("2 lista:", pg.inner_text("#menu-lingua").replace("\n", " | "))
    pg.screenshot(path="/home/claude/rega-test/menu_lingua.png")
    pg.click("#menu-lingua [data-l='sw']"); pg.wait_for_selector("#l-entrar", state="visible"); pg.wait_for_timeout(500)
    print("3 PT→SW directo:", pg.inner_text("#lc-lingua"), "|", pg.inner_text("#l-entrar"), "| lang", pg.evaluate("document.documentElement.lang"))
    pg.click("#lc-lingua"); print("4 lista em SW:", pg.inner_text("#menu-lingua").replace("\n", " | "))
    pg.wait_for_timeout(300); pg.mouse.click(200, 700); pg.wait_for_timeout(300); print("5 toque fora fecha:", pg.locator("#menu-lingua").count() == 0)
    pg.click("#lc-lingua"); pg.click("#menu-lingua [data-l='pt']"); pg.wait_for_selector("#l-entrar", state="visible"); pg.wait_for_timeout(500)
    print("6 SW→PT directo:", pg.inner_text("#lc-lingua"), "|", pg.inner_text("#l-entrar"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
