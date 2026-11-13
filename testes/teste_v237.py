# v237 (13/11/2026, problema registado pela app: «AbortError: signal is aborted without reason» em «Esta rega está certa», 3 vezes, 2 pessoas, v236).
# Desde a v233 um pedido lento é cortado aos 30 s; o corte tem de contar como falta de rede (também ao entrar sem rede: não pode apagar a entrada guardada). LING=en / sw.
import os, json, subprocess, time, sys
from playwright.sync_api import sync_playwright
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8847", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
LING = os.environ.get("LING", "pt"); erros = []; ok = True
INIT = """
const f0 = window.fetch;
window.fetch = function(input, init) {
  const u = typeof input === 'string' ? input : (input && input.url) || '';
  if (/auth\\/v1\\/token|rest\\/v1\\/rpc\\/confirmar/.test(u)) return Promise.reject(new DOMException('signal is aborted without reason', 'AbortError'));
  return f0.apply(this, arguments);
};
try { localStorage.setItem('rega.lingua', '%s'); } catch (e) {}
""" % LING
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.on("pageerror", lambda e: erros.append(str(e)))
        NM = "/home/claude/rega-test/node_modules"
        pg.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
        pg.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
        pg.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(path=f"{NM}/leaflet-rotate/dist/leaflet-rotate-src.js", content_type="application/javascript"))
        pg.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
        pg.route("**/*supabase.co/**", lambda r: r.fulfill(status=200, content_type="application/json", body="[]"))
        pg.add_init_script(INIT)
        pg.goto("http://localhost:8847/index.html"); pg.wait_for_timeout(2500)
        casos = pg.evaluate("""() => ({
          auth: semRede({ name: 'AuthRetryableFetchError', message: 'signal is aborted without reason', status: 0 }),
          rest: semRede({ message: 'AbortError: signal is aborted without reason' }),
          tempo: semRede({ message: 'timeout' }),
          senha: semRede({ name: 'AuthApiError', message: 'Invalid login credentials', status: 400 }),
        })""")
        print("semRede:", casos)
        ok &= casos["auth"] and casos["rest"] and casos["tempo"] and not casos["senha"]
        r = pg.evaluate("""async () => {
          LS.set('acessoOff', { teste: 1 });
          S.credPend = { email: 'a@rega-coco.example.com', segredo: '123456' };
          const v = await autenticarPendente();
          return { v, guardado: !!LS.get('acessoOff'), pend: !!S.credPend };
        }""")
        print("autenticarPendente com o pedido cortado:", r)
        ok &= r["v"] is False and r["guardado"] and r["pend"]
        b.close()
finally:
    srv.terminate()
print("erros JS:", erros)
ok &= not erros
print("OK" if ok else "FALHOU"); sys.exit(0 if ok else 1)
