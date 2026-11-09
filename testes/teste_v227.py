# v227 (09/11/2026, Valdo): painel › cartão «Plantas regadas das vivas que havia» e gráfico por dia com as vivas na base. NULO=1: servidor devolve null (cartões antigos). LING=en / sw.
import json, subprocess, time, sys, os, glob
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt"); NULO = os.environ.get("NULO") == "1"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8866", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
D = {"gerado_em": "2026-11-09T19:00:00Z", "periodo": {"de": None, "ate": None}, "inicio": "2026-10-24", "fim": "2026-11-09", "universo": {"areas": 713, "vivas": 100000},
     "areas_regadas": 600, "vivas_regadas": 70000, "plantas_regadas_total": 90000, "pessoas_dia_total": 900, "registos": 1500, "por_dia": [], "por_comunidade": [], "por_equipa": [], "constrangimentos": {}, "chegadas_agua": []}
PV = {"total": {"regas": 49, "plantas": 2733, "vivas": 4959, "mortas": 1835, "por_terminar": 354, "outras": 37},
      "dias": [{"data": "2026-11-07", "regas": 22, "plantas": 1914, "vivas": 2520, "mortas": 606, "por_terminar": 0, "outras": 0},
               {"data": "2026-11-09", "regas": 49, "plantas": 2733, "vivas": 4959, "mortas": 1835, "por_terminar": 354, "outras": 37}]}
D["por_dia"] = [{"data": "2026-11-07", "plantas": 1914, "campos": 22, "equipas": 6, "pessoas": 30}, {"data": "2026-11-09", "plantas": 2733, "campos": 45, "equipas": 10, "pessoas": 57}]
D["plantas_regadas_total"] = 4647; D["vivas_regadas"] = 6000
def mock(route):
    u = route.request.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/rpc/painel_resumo_periodo" in u: return ok(D)
    if "/rpc/painel_plantas_vivas" in u: return ok(None if NULO else PV)
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "g@rega-coco.example.com"}})
    if "/rpc/painel_monitoria" in u or "/rpc/painel_plantas_marcadas" in u or "/rpc/painel_cumprimento" in u or "/rpc/painel_manutencao" in u or "/rpc/painel_medicoes" in u: return ok(None)
    if "/rpc/" in u: return ok([])
    return ok({})
erros = []; falhas = []
def verif(c, t):
    print(("OK  " if c else "FALHA ") + t)
    if not c: falhas.append(t)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
    ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8866/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "g"); pg.fill("#l-pin", "x"); pg.click("#l-entrar"); pg.wait_for_selector("#kpis .kpi", state="visible"); pg.wait_for_timeout(2500)
    k = pg.inner_text("#kpis")
    if NULO:
        verif("Plantas regadas (total)" in k or LING != "pt", "N1 sem dados: cartões antigos")
        verif(pg.locator("#leg-dia").is_hidden(), "N2 sem legenda das vivas")
    else:
        if LING == "pt":
            verif("Plantas regadas das vivas que havia" in k and "55 %" in k and "Plantas regadas (total)" not in k and "Plantas vivas em campos regados" not in k, "1 um só cartão com a % (2733/4959 = 55 %)")
            verif("1835" in k.replace(" ", "").replace("\u202f","") and "354" in k, "2 secas ou mortas e por terminar no cartão")
        verif(pg.locator("#g-dia svg path[opacity]").count() == 2, "3 duas colunas claras (vivas) no gráfico")
        verif(pg.is_visible("#leg-dia"), "4 legenda visível")
        nf = pg.locator('#g-dia text.valor[style*="ink2"]').count()
        verif(nf == 1, f"4b valor das vivas por cima da coluna clara ({nf})")
        pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)"); pg.wait_for_timeout(300)
        t = pg.inner_text("#t-dia")
        verif("4959" in t.replace(" ", "").replace("\u202f","").replace(",","") and "55 %" in t, "5 tabela com vivas e %")
        if LING != "pt":
            for x in ["Plantas regadas das vivas", "vivas na base", "secas ou mortas", "Faltaram", "outras razões", "Plantas vivas na base", "Secas ou mortas", "Em cada rega"]:
                verif(x not in k and x not in t and x not in pg.inner_text("#g-dia").__str__() and x not in pg.inner_text("body"), f"6 traduzido: «{x}»")
        pg.locator("#kpis").screenshot(path=f"/home/claude/rega-test/v227_kpis_{LING}.png")
        pg.locator("#g-dia").evaluate("e=>e.closest('.card').scrollIntoView()"); pg.locator("#g-dia").evaluate("e=>e")
        pg.locator("#g-dia >> xpath=..").screenshot(path=f"/home/claude/rega-test/v227_dia_{LING}.png")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
