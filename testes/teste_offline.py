import subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8769", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context()
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"))
    pg = ctx.new_page(); erros = []; pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8769/"); pg.wait_for_function("navigator.serviceWorker.controller !== null", timeout=15000)
    pg.reload(); pg.wait_for_selector("#l-entrar", state="visible"); print("online: novo código =", pg.evaluate("typeof ecraNovaCredencial"))
    ctx.set_offline(True); pg.reload(); pg.wait_for_selector("#l-entrar", state="visible", timeout=15000)
    print("sem rede: página abre =", pg.is_visible("#l-entrar"), "| código =", pg.evaluate("typeof ecraNovaCredencial"), "| erros:", erros or "nenhum")
    b.close()
srv.terminate()
