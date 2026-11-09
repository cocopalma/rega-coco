# v225 (09/11/2026, Valdo): painel › «💧 Campos que nunca receberam água» (lista, evolução por dia, por equipa, .csv). NULO=1: servidor devolve null (secção escondida). LING=en / sw.
import json, subprocess, time, sys, os, glob
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; LING = os.environ.get("LING", "pt"); NULO = os.environ.get("NULO") == "1"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8863", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
D = {"gerado_em": "2026-11-09T19:00:00Z", "periodo": {"de": None, "ate": None}, "inicio": "2026-10-24", "fim": "2026-11-09", "universo": {"areas": 713, "vivas": 100000},
     "areas_regadas": 600, "vivas_regadas": 70000, "plantas_regadas_total": 90000, "pessoas_dia_total": 900, "registos": 1500, "por_dia": [], "por_comunidade": [], "por_equipa": [], "constrangimentos": {}, "chegadas_agua": []}
NA = {"hoje": "2026-11-09", "de": None, "ate": None, "inicio_app": "2026-10-24", "whatsapp": "2026-11-07",
      "campos": [{"area_id": "a1", "pr": "PR1-1", "produtor": "Produtor Um", "comunidade": "Palma", "zona": "Muah", "equipa": "Azize Exemplo", "tecnico": "Técnico A", "supervisor": "Sup A", "vivas": 120, "instaladas": 140, "coord": True, "wa_por_pr": False},
                 {"area_id": "a2", "pr": "PR2-1", "produtor": "Produtor; Dois", "comunidade": "Macala", "zona": None, "equipa": "Azize Exemplo", "tecnico": "Técnico A", "supervisor": "Sup A", "vivas": 80, "instaladas": 80, "coord": False, "wa_por_pr": True},
                 {"area_id": "a3", "pr": "PR3-1", "produtor": "Produtor Três", "comunidade": "Senga", "zona": None, "equipa": "Samugi Exemplo", "tecnico": "Técnico B", "supervisor": "Sup B", "vivas": 50, "instaladas": 60, "coord": True, "wa_por_pr": False}],
      "primeira": [{"area_id": "a4", "pr": "PR4-1", "produtor": "Produtor Quatro", "comunidade": "Farol", "zona": None, "equipa": "Majula Exemplo", "tecnico": "T", "supervisor": "S", "vivas": 60, "data": "2026-11-09"},
                   {"area_id": "a5", "pr": "PR5-1", "produtor": "Produtor Cinco", "comunidade": "Farol", "zona": None, "equipa": "Majula Exemplo", "tecnico": "T", "supervisor": "S", "vivas": 30, "data": "2026-11-07"}],
      "retirados": [{"area_id": "a6", "pr": "PR6-1", "produtor": "Produtor Seis", "comunidade": "Quiwia", "zona": None, "equipa": "Alafo Exemplo", "vivas": 70, "instaladas": 70, "data": "2026-11-09", "motivo_cod": "mudas_mortas", "motivo": "Retirado da rega na app: Todas as mudas mortas: O campo não tem nenhuma muda", "por": "Guidion", "nunca": True},
                    {"area_id": "a7", "pr": "PR7-1", "produtor": "Produtor Sete", "comunidade": "Palma", "zona": "Incularino", "equipa": None, "vivas": 10, "instaladas": 40, "data": "2026-10-12", "motivo_cod": None, "motivo": "Incularino: sem mudas (Nuro, 10/10)", "por": None, "nunca": False}],
      "dias": [{"data": "2026-11-0%d" % i, "restam": 200 - i * 12, "prim": i, "ret": 1} for i in range(1, 10)]}
def mock(route):
    u = route.request.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/rpc/painel_resumo_periodo" in u: return ok(D)
    if "/rpc/painel_nunca_agua" in u: return ok(None if NULO else NA)
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
    pg.goto("http://localhost:8863/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "g"); pg.fill("#l-pin", "x"); pg.click("#l-entrar"); pg.wait_for_selector("#kpis .kpi", state="visible"); pg.wait_for_timeout(2500)
    if NULO:
        verif(not pg.is_visible("#s-nunca"), "N1 sem dados do servidor: secção escondida")
    else:
        verif(pg.is_visible("#s-nunca"), "1 secção visível")
        k = pg.inner_text("#k-nunca")
        verif("3" in k and "250" in k, "2 cartão: 3 campos, 250 plantas")
        verif(pg.locator("#g-nunca-dia svg path.vis").count() == 9, "3 gráfico com 9 dias")
        verif(pg.locator("#g-nunca-eq .marca-dados").count() == 2, "4 barras: 2 equipas")
        pg.evaluate("document.querySelectorAll('#s-nunca details').forEach(d=>d.open=true)"); pg.wait_for_timeout(300)
        verif(pg.locator("#t-nunca tbody tr").count() == 3 and pg.locator("#t-nunca-prim tbody tr").count() == 2 and pg.locator("#t-nunca-ret tbody tr").count() == 2, "5 tabelas 3 / 2 / 2")
        t = pg.inner_text("#s-nunca")
        if LING == "pt":
            verif("Todas as mudas mortas" in t and "Sem mudas" in t and "O campo não tem nenhuma muda" in t, "6 motivo e justificação dos retirados")
        else:
            for x in ["Campos que nunca receberam", "Nunca receberam água", "Retirados da rega", "Ver os campos", "Descarregar a lista", "Por equipa", "Sem registo", "Todas as mudas mortas", "Justificação", "Tem coordenada"]:
                verif(x not in t, f"6 traduzido: «{x}»")
        with pg.expect_download() as dl: pg.click("#b-nunca-csv")
        f = dl.value; caminho = f"/home/claude/rega-test/{f.suggested_filename}"; f.save_as(caminho)
        csv = open(caminho, encoding="utf-8-sig").read().splitlines()
        verif(f.suggested_filename.startswith("Rega_Coco_campos_nunca_regados_") and f.suggested_filename.endswith(".csv"), "7 nome do ficheiro")
        verif(len(csv) == 1 + 3 + 2 + 2, f"8 csv com 7 linhas de dados ({len(csv) - 1})")
        verif('"Produtor; Dois"' in "\n".join(csv), "9 ponto e vírgula dentro do nome fica entre aspas")
        pg.locator("#s-nunca").screenshot(path=f"/home/claude/rega-test/v225_{LING}.png")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
