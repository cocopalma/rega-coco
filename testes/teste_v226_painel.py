# v226 (09/11/2026, Valdo): painel › Meta › «Porque não se atingiu a meta». NULO=1: servidor devolve null (bloco escondido). LING=en / sw.
import json, subprocess, time, sys, os, glob
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt"); NULO = os.environ.get("NULO") == "1"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8865", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
D = {"gerado_em": "2026-11-09T19:00:00Z", "periodo": {"de": None, "ate": None}, "inicio": "2026-10-24", "fim": "2026-11-09", "universo": {"areas": 713, "vivas": 100000},
     "areas_regadas": 600, "vivas_regadas": 70000, "plantas_regadas_total": 90000, "pessoas_dia_total": 900, "registos": 1500, "por_dia": [], "por_comunidade": [], "por_equipa": [], "constrangimentos": {}, "chegadas_agua": []}
MX = {"limiar": 70, "espera_min": 60, "mortas_pct": 20, "hora_chegada": "06:30", "motivo_inicio": "2026-11-10", "dias": [
  {"activista_id": "a", "equipa": "Majula Exemplo", "data": "2026-11-09", "plantas": 64, "meta": 700, "pct": 9.1, "pessoas": 5, "vivas_havia": 64, "cobertura": 100, "ini": "08:23", "fim": "14:13", "espera_min": 9, "causas": ["tarde", "mortas"], "precisa_motivo": False, "motivo": None},
  {"activista_id": "b", "equipa": "Biena Exemplo", "data": "2026-11-09", "plantas": 164, "meta": 700, "pct": 23.4, "pessoas": 5, "vivas_havia": 164, "cobertura": 100, "ini": "06:05", "fim": "10:49", "espera_min": 174, "causas": ["espera"], "precisa_motivo": False, "motivo": None},
  {"activista_id": "c", "equipa": "Rotina Exemplo", "data": "2026-11-09", "plantas": 100, "meta": 700, "pct": 14.3, "pessoas": 5, "vivas_havia": 120, "cobertura": 83.3, "ini": "06:10", "fim": "10:00", "espera_min": 0, "causas": [], "precisa_motivo": True, "motivo": None},
  {"activista_id": "d", "equipa": "Gito Exemplo", "data": "2026-11-08", "plantas": 150, "meta": 700, "pct": 21.4, "pessoas": 5, "vivas_havia": 150, "cobertura": 100, "ini": "06:10", "fim": "10:00", "espera_min": 0, "causas": [], "precisa_motivo": True, "motivo": "Funeral na comunidade", "motivo_por": "Tecnico X"},
  {"activista_id": "e", "equipa": "Oliveira Exemplo", "data": "2026-11-09", "plantas": 401, "meta": 280, "pct": 143.2, "pessoas": 2, "vivas_havia": 724, "cobertura": 55.4, "ini": "07:10", "fim": "14:08", "espera_min": 11, "causas": ["tarde", "agua"], "precisa_motivo": False, "motivo": None}]}
def mock(route):
    u = route.request.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/rpc/painel_resumo_periodo" in u: return ok(D)
    if "/rpc/painel_meta_causas" in u: return ok(None if NULO else MX)
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
    pg.goto("http://localhost:8865/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "g"); pg.fill("#l-pin", "x"); pg.click("#l-entrar"); pg.wait_for_selector("#kpis .kpi", state="visible"); pg.wait_for_timeout(2500)
    if NULO:
        verif(not pg.is_visible("#meta-causas"), "N1 sem dados do servidor: bloco escondido")
    else:
        verif(pg.is_visible("#meta-causas"), "1 bloco visível")
        k = pg.inner_text("#k-meta-causas")
        verif("4" in k and "5" in k, "2 cartão: 4 de 5 dias abaixo do limite")
        verif(pg.locator("#g-meta-causas .marca-dados").count() == 4, "3 barras: tarde, espera, mortas, sem explicação")
        pg.evaluate("document.querySelectorAll('#meta-causas details').forEach(d=>d.open=true)"); pg.wait_for_timeout(300)
        verif(pg.locator("#t-meta-causas tbody tr").count() == 5, "4 tabela com 5 dias")
        t = pg.inner_text("#meta-causas")
        verif("Funeral na comunidade" in t, "5 motivo registado aparece")
        if LING == "pt":
            verif("Sem explicação" in t and "Esperou pela água" in t, "6 explicações")
        else:
            for x in ["Porque não se atingiu", "Sem explicação", "Esperou pela água", "Plantas vivas que havia", "Ver por equipa", "Explicação", "Cada dia de equipa", "acabar cedo"]:
                verif(x not in t, f"6 traduzido: «{x}»")
        pg.locator("#meta-causas").screenshot(path=f"/home/claude/rega-test/v226_{LING}.png")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
