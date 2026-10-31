# Abrir a app sem rede depois de já ter entrado (14/10/2026, Nuro: ecrã branco). Sessão expirada e válida.
import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8797", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
areas = [{"id": "PR9-1", "pr": "PR9", "area_n": 1, "comunidade": "Palma", "zona": "Incularino", "produtor": "Produtor Palma", "instaladas": 50, "vivas": 50, "latitude": -10.77, "longitude": 40.47, "activista_id": ACT, "activista_proposto": None},
         {"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None}]
EST = {"offline": False, "dur": 3600}
def mock(route):
    if EST["offline"]: return route.abort("internetdisconnected")
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u:
        return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": EST["dur"], "expires_at": int(time.time()) + EST["dur"], "refresh_token": "r", "user": {"id": "u-sup", "aud": "authenticated", "role": "authenticated", "email": "nuro@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": "u-sup", "nome": "Nuro", "papel": "supervisor", "activista_id": None})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol", "equipa_tamanho": 5}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rest/v1/zonas" in u: return ok([{"comunidade": "Palma", "zona": z} for z in ["Bagala", "Incularino", "Muah", "Quelimane", "Quilaua"]])
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/" in u: return ok([])
    if "/rest/v1/" in u: return ok([])
    return ok({})
def ficheiro(caminho, tipo):
    return lambda r: r.abort("internetdisconnected") if EST["offline"] else r.fulfill(path=caminho, content_type=tipo)
for caso, dur in [("sessão válida", 3600), ("sessão expirada", 5)]:
    EST.update(offline=False, dur=dur)
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}); erros = []
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", ficheiro(f"{NM}/leaflet/dist/leaflet.js", "application/javascript"))
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", ficheiro(f"{NM}/leaflet/dist/leaflet.css", "text/css"))
        ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.abort("internetdisconnected") if EST["offline"] else r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
        ctx.route("**/fonts.googleapis.com/**", lambda r: r.abort("internetdisconnected") if EST["offline"] else r.fulfill(status=200, content_type="text/css", body=""))
        ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.abort("internetdisconnected"))
        ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
        pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
        pg.goto("http://localhost:8797/"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.click("#login [data-m=tecnico]"); pg.fill("#l-user", "nuro"); pg.fill("#l-senha", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible")
        pg.wait_for_timeout(2500)   # service worker instalado e dados no telefone
        print(caso, "| SW activo:", pg.evaluate("navigator.serviceWorker.controller ? 'sim' : 'não'"))
        if dur < 60: pg.wait_for_timeout(6000)   # deixa o token expirar
        EST["offline"] = True; ctx.set_offline(True)
        t0 = time.time(); pg.reload(wait_until="domcontentloaded")
        visto = None
        for _ in range(60):
            if pg.is_visible("#app"): visto = "app"; break
            if pg.is_visible("#login"): visto = "entrada"; break
            pg.wait_for_timeout(500)
        print(caso, "| sem rede, depois de", round(time.time() - t0, 1), "s:", visto or "ECRÃ BRANCO", "| erros:", erros or "nenhum")
        if visto == "app" and dur < 60:
            pg.click("nav button[data-e=hoje]"); pg.wait_for_timeout(800)
            print("  hoje sem rede:", " | ".join(l for l in pg.inner_text("#hoje").split("\n") if l.strip())[:300])
            pg.click("button[onclick=\"ecraChuva()\"]"); pg.wait_for_selector("#c-mm")
            print("  locais da chuva:", pg.locator("#c-com option").all_inner_texts())
            pg.select_option("#c-com", label="Palma › Quilaua"); pg.fill("#c-mm", "7.5"); pg.fill("#c-obs", "teste rascunho")
            pg.evaluate("document.querySelector('label[for=c-foto]').dispatchEvent(new MouseEvent('click', {bubbles: true}))")   # abre a câmara…
            pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(3000)            # …e o telefone fecha a app
            print("  depois de fechar:", pg.inner_text("#folha")[:200].replace("\n", " | ") if pg.is_visible("#c-mm") else "FORMULÁRIO PERDIDO",
                  "| mm:", pg.input_value("#c-mm") if pg.is_visible("#c-mm") else "-", "| local:", pg.eval_on_selector("#c-com", "e=>e.selectedOptions[0].textContent") if pg.is_visible("#c-com") else "-")
            pg.set_input_files("#c-foto", "/home/claude/rega-test/foto_teste.jpg"); pg.wait_for_selector("#c-prev", state="visible"); pg.click("text=Guardar"); pg.wait_for_timeout(800)
            print("  guardado:", [(x["comunidade"], x["zona"], x["mm"]) for x in pg.evaluate("LS.get('filaChuva')")], "| rascunho apagado:", pg.evaluate("LS.get('rascChuva')") is None)
        b.close()
srv.terminate()
