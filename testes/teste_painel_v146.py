# Painel v112 (26/10/2026): períodos guardados para ver sem rede; chegada da equipa ao 1.º campo (06:00) e atraso. LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8841", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
def D(de, ate): return {"gerado_em": "2026-10-26T12:00:00Z", "periodo": {"de": de, "ate": ate}, "inicio": "2026-10-24", "fim": "2026-10-26", "universo": {"areas": 715, "vivas": 100000},
    "areas_regadas": 30, "vivas_regadas": 3000, "plantas_regadas_total": 3400, "pessoas_dia_total": 60, "registos": 36, "espera_agua_min": 22,
    "chegada_equipa": {"hora_combinada": "06:00", "dias": 17, "hora_media": "09:08", "atraso_min": 188, "depois_hora": 16},
    "por_dia": [], "por_comunidade": [], "por_equipa": [], "constrangimentos": {},
    "chegadas_agua": [{"data": "2026-10-26", "equipa": "Ibraimo Ali Selemane", "comunidade": "Olumbe", "inicio_trabalho": "07:12", "atraso_min": 72, "primeira_agua": "07:40", "horas": "07:40", "campos": 7, "espera_media_min": 20},
                      {"data": "2026-10-26", "equipa": "Rotina Carlos", "comunidade": "Quitunda", "inicio_trabalho": "05:55", "atraso_min": 0, "primeira_agua": "06:10", "horas": "06:10", "campos": 1, "espera_media_min": 15}]}
import datetime
hoje = datetime.date.today(); dd = lambda n: (hoje - datetime.timedelta(days=n)).isoformat()
M = {"mudas": {"vivas": 0, "secas": 0, "mortas": 0}, "lqas_n": 19, "lqas_limiar": 13, "amostrados": 3, "verificados": 1, "nota_media": 9, "solo_regado": 1, "plantas_obs": 20, "plantas_humidas": 18,
     "por_tecnico": [], "por_equipa": [], "por_verificador": [{"nome": "Essumaila Carlos Assane", "papel": "tecnico", "amostrados": 2, "verificados": 1, "nota_media": 9}, {"nome": "Raul Miquilange", "papel": "supervisor", "amostrados": 1, "verificados": 0, "nota_media": None}]}
MC = [{"id": "m1", "verificador": "Essumaila Carlos Assane", "papel": "tecnico", "data_rega": dd(3), "area_id": "PR1-1", "produtor": "Produtor Um", "comunidade": "Palma", "zona": "Incularino", "activista": "Oliveira", "verificado_em": None, "nota": None},
      {"id": "m2", "verificador": "Essumaila Carlos Assane", "papel": "tecnico", "data_rega": dd(2), "area_id": "PR2-1", "produtor": "Produtor Dois", "comunidade": "Olumbe", "zona": None, "activista": "Macame", "verificado_em": dd(1) + "T08:00:00Z", "nota": 9},
      {"id": "m3", "verificador": "Raul Miquilange", "papel": "supervisor", "data_rega": dd(0), "area_id": "PR3-1", "produtor": "Produtor Três", "comunidade": "Senga", "zona": None, "activista": "Martins", "verificado_em": None, "nota": None}]
pedidos = []
def mock(route):
    u = route.request.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/rpc/painel_resumo_periodo" in u: a = json.loads(route.request.post_data); pedidos.append((a.get("p_de"), a.get("p_ate"))); return ok(D(a.get("p_de"), a.get("p_ate")))
    if "/rpc/painel_cumprimento" in u: return ok({"de": "2026-10-29", "ate": "2026-10-29", "inicio": "2026-10-29", "pessoas": [{"nome": "Nuro", "papel": "supervisor", "equipas": 9, "dias": 1, "fechados_a_tempo": 1, "fechados_tarde": 0, "mon_sorteados": 2, "mon_feitos": 0, "acompanhamentos": 3, "alertas": 1, "alertas_tratados": 1, "equipas_dia": 9, "sem_motivo": 0}]})
    if "/rpc/painel_monitoria_campos" in u: return ok(MC)
    if "/rpc/painel_monitoria" in u: return ok(M)
    if "/rpc/painel_testes" in u: return ok([{"nome": "Nuro", "papel": "supervisor", "regas": 13, "dias": 5, "campos": 9, "fotos3": 3, "plantas": 900, "chuva": 2, "ultima": "2026-10-25"}, {"nome": "Idelson", "papel": "supervisor", "regas": 0, "dias": 0, "campos": 0, "fotos3": 0, "plantas": 0, "chuva": 0, "ultima": None}])
    if "/rpc/painel_constrangimentos" in u: return ok([{"data": "2026-10-26", "tipo": "falta_agua", "descricao": "Tuk-tuk só às 10h", "area_id": "PR2467285-1", "produtor": "Sulemane Exemplo", "comunidade": "Palma", "zona": "Incularino", "activista": "Selemane Ali Sumail", "plantas_regadas": 11, "plantas_campo": 67}])
    if "/rpc/dias_sem_rega_lista" in u: return ok([{"id": "d1", "activista": "Gito Armando", "comunidade": "Mondlane", "data": "2026-10-26", "motivo": "tuk_tuk", "todo_dia": True, "descricao": "Esperámos até às 10:00", "regas": 0, "quem": "Manuel Felix Shella", "foto_path": "u/dsr-1.jpg", "area_id": "PR22-1", "produtor": "Fátima Exemplo", "entrada_em": "2026-10-26T05:10:00Z"}, {"id": "d2", "activista": "Macame Juma Abular", "comunidade": "Olumbe", "data": "2026-10-26", "motivo": "sem_agua", "todo_dia": False, "descricao": None, "regas": 3, "quem": "Nuro"}])
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "g@rega-coco.example.com"}})
    if "/rpc/" in u: return ok([])
    return ok({})
erros = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.goto("http://localhost:8841/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "g"); pg.fill("#l-pin", "x"); pg.click("#l-entrar"); pg.wait_for_selector("#kpis .kpi", state="visible"); pg.wait_for_timeout(2500)
    print("1 testes: details aberto?", pg.evaluate("document.querySelector('#d-tp').open"), "| tabela visível?", pg.is_visible("#t-tp"), "| resumo:", pg.inner_text("#d-tp summary"))
    pg.click("#d-tp summary"); pg.wait_for_timeout(200); print("2 depois de tocar: tabela visível?", pg.is_visible("#t-tp"), "| linhas:", pg.locator("#t-tp tr").count())
    print("3 por pessoa:", pg.evaluate("[...document.querySelectorAll('#t-mon-ver tr')].map(r => r.textContent.replace(/\\s+/g,' ').trim())"))
    pg.click("#d-mon-campos summary"); pg.wait_for_timeout(200)
    print("4 campos:", pg.evaluate("[...document.querySelectorAll('#t-mon-campos tr')].map(r => r.textContent.replace(/\\s+/g,' ').trim())"))
    pg.locator("#s-mon").screenshot(path=f"/home/claude/rega-test/v123_mon{os.environ.get('LING','pt')}.png")
    print("C cumprimento:", pg.evaluate("[...document.querySelectorAll('#t-cump tr')].map(r => r.textContent.replace(/\\s+/g,' ').trim())"), "| desc:", pg.inner_text("#s-cump .desc")[-140:])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
