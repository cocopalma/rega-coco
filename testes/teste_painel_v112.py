# Painel v112 (26/10/2026): períodos guardados para ver sem rede; chegada da equipa ao 1.º campo (06:00) e atraso. LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8832", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
def D(de, ate): return {"gerado_em": "2026-10-26T12:00:00Z", "periodo": {"de": de, "ate": ate}, "inicio": "2026-10-24", "fim": "2026-10-26", "universo": {"areas": 715, "vivas": 100000},
    "areas_regadas": 30, "vivas_regadas": 3000, "plantas_regadas_total": 3400, "pessoas_dia_total": 60, "registos": 36, "espera_agua_min": 22,
    "chegada_equipa": {"hora_combinada": "06:00", "dias": 17, "hora_media": "09:08", "atraso_min": 188, "depois_hora": 16},
    "por_dia": [], "por_comunidade": [], "por_equipa": [], "constrangimentos": {},
    "chegadas_agua": [{"data": "2026-10-26", "equipa": "Ibraimo Ali Selemane", "comunidade": "Olumbe", "inicio_trabalho": "07:12", "atraso_min": 72, "primeira_agua": "07:40", "horas": "07:40", "campos": 7, "espera_media_min": 20},
                      {"data": "2026-10-26", "equipa": "Rotina Carlos", "comunidade": "Quitunda", "inicio_trabalho": "05:55", "atraso_min": 0, "primeira_agua": "06:10", "horas": "06:10", "campos": 1, "espera_media_min": 15}]}
pedidos = []
def mock(route):
    u = route.request.url; ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
    if "/rpc/painel_resumo_periodo" in u: a = json.loads(route.request.post_data); pedidos.append((a.get("p_de"), a.get("p_ate"))); return ok(D(a.get("p_de"), a.get("p_ate")))
    if "/rpc/painel_monitoria" in u: return ok(None)
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
    pg.goto("http://localhost:8832/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "g"); pg.fill("#l-pin", "x"); pg.click("#l-entrar"); pg.wait_for_selector("#kpis .kpi", state="visible"); pg.wait_for_timeout(3500)
    print("1 períodos pedidos:", pedidos)
    print("1b guardados:", pg.evaluate("Object.keys(localStorage).filter(k => k.startsWith('rega.painel.cache.')).map(k => k.slice(28))"))
    k = [x for x in pg.locator("#kpis .kpi").all_inner_texts() if "06:00" in x or "tuk" in x.lower()]
    print("2 KPIs:", [x.replace("\n", " | ") for x in k])
    print("3 texto:", pg.inner_text("#d-agua"))
    print("4 tabela:", pg.evaluate("[...document.querySelectorAll('#t-agua tr')].slice(0,3).map(r => r.textContent.replace(/\\s+/g,' ').trim())"))
    print("4c período nas secções:", pg.evaluate("[...document.querySelectorAll('.per-tag')].slice(0,3).map(e => e.textContent)"), pg.locator(".per-tag").count())
    pg.evaluate("document.querySelector('#t-constr').closest('details').open = true")
    print("4d constrangimentos:", pg.evaluate("[...document.querySelectorAll('#t-constr tr')].map(r => r.textContent.replace(/\\s+/g,' ').trim())"))
    print("4e equipas:", pg.inner_text("#d-equipa") if pg.locator("#d-equipa").is_visible() else "(escondido)")
    print("4b dias sem rega:", pg.inner_text("#k-dsr").replace("\n", " | "), "||", pg.evaluate("[...document.querySelectorAll('#t-dsr tr')].map(r => r.textContent.replace(/\\s+/g,' ').trim())"))
    ctx.set_offline(True); n0 = len(pedidos)
    pg.click("#filtro [data-p='7']"); pg.wait_for_timeout(800)
    print("5 sem rede › 7 dias:", pg.inner_text("#f-legenda"), "|", pg.inner_text("#aviso-rede") if pg.locator("#aviso-rede").count() else "(sem aviso)", "| pedidos novos:", len(pedidos) - n0)
    pg.click("#filtro [data-p='hoje']"); pg.wait_for_timeout(800); print("6 sem rede › Hoje:", pg.inner_text("#f-legenda"))
    pg.click("#filtro [data-p='periodo']"); pg.fill("#f-de", "2026-10-01"); pg.fill("#f-ate", "2026-10-05"); pg.click("#f-aplicar"); pg.wait_for_timeout(800)
    print("7 sem rede › período não guardado:", pg.inner_text("#aviso-rede"), "|", pg.inner_text("#f-legenda"))
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
