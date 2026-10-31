import subprocess, sys, time
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8779", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(); erros = []
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8779/painel.html"); pg.wait_for_selector("#l-entrar", state="visible")
    print("painel.html directo →", pg.url, "| ecrã:", pg.is_visible("#login"))
    pg.goto("http://localhost:8779/painel.html?embutido=1"); pg.wait_for_timeout(1500)
    print("embutido fica:", pg.url.endswith("embutido=1"), "| erros:", erros or "nenhum")
    b.close()
srv.terminate()
