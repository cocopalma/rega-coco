import subprocess, sys, time
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8778", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 700}); erros = []
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8778/painel.html"); pg.wait_for_selector("#l-entrar", state="visible")
    print("PT:", pg.inner_text("#login").replace("\n", " | "))
    pg.click("#lc-lingua"); pg.click("#menu-lingua [data-l='" + pg.evaluate("(()=>{const L=['pt','en','sw'];let c='pt';try{c=localStorage.getItem('rega.lingua')||'pt'}catch(e){};return L[(L.indexOf(c)+1)%3]})()") + "']"); pg.wait_for_selector("#l-entrar", state="visible"); pg.wait_for_timeout(500)
    print("EN:", pg.inner_text("#login").replace("\n", " | ")); pg.screenshot(path="/home/claude/rega-test/painel_login_en.png")
    pg.click("#lc-lingua"); pg.click("#menu-lingua [data-l='pt']"); pg.wait_for_selector("#l-entrar", state="visible"); pg.wait_for_timeout(500)
    print("PT de novo:", pg.inner_text("#l-entrar"), pg.inner_text("#lc-lingua"), "| ERROS:", erros or "nenhum")
    b.close()
srv.terminate()
