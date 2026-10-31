# v168 (01/11/2026): espaço do aparelho cheio. Painel: uma cópia por período; app: liberta as cópias do painel e as sobras da apresentação antes de avisar. LING=en / sw.
import json, subprocess, time, sys, os
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8868", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
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
    if "/rpc/painel_monitoria_campos" in u: return ok(MC)
    if "/rpc/painel_monitoria" in u: return ok(M)
    if "/rpc/painel_testes" in u: return ok([{"nome": "Nuro", "papel": "supervisor", "regas": 13, "dias": 5, "campos": 9, "fotos3": 3, "plantas": 900, "chuva": 2, "ultima": "2026-10-25"}, {"nome": "Idelson", "papel": "supervisor", "regas": 0, "dias": 0, "campos": 0, "fotos3": 0, "plantas": 0, "chuva": 0, "ultima": None}])
    if "/rpc/painel_constrangimentos" in u: return ok([{"data": "2026-10-26", "tipo": "falta_agua", "descricao": "Tuk-tuk só às 10h", "area_id": "PR2467285-1", "produtor": "Sulemane Exemplo", "comunidade": "Palma", "zona": "Incularino", "activista": "Selemane Ali Sumail", "plantas_regadas": 11, "plantas_campo": 67}])
    if "/rpc/dias_sem_rega_lista" in u: return ok([{"id": "d1", "activista": "Gito Armando", "comunidade": "Mondlane", "data": "2026-10-26", "motivo": "tuk_tuk", "todo_dia": True, "descricao": "Esperámos até às 10:00", "regas": 0, "quem": "Manuel Felix Shella", "foto_path": "u/dsr-1.jpg", "area_id": "PR22-1", "produtor": "Fátima Exemplo", "entrada_em": "2026-10-26T05:10:00Z"}, {"id": "d2", "activista": "Macame Juma Abular", "comunidade": "Olumbe", "data": "2026-10-26", "motivo": "sem_agua", "todo_dia": False, "descricao": None, "regas": 3, "quem": "Nuro"}])
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "g@rega-coco.example.com"}})
    if "/rpc/" in u: return ok([])
    return ok({})
erros = []; dialogos = []
JUNK = "x" * 400000
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    if os.environ.get("LING"): ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{os.environ['LING']}')}}catch(e){{}}")
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.goto("http://localhost:8868/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
    # cópias antigas: 'tudo' de 3 dias, '7' de 2 dias, dois períodos escolhidos à mão, e sobras da apresentação
    pg.evaluate("""(j) => { const k = (d, p) => 'rega.painel.cache.' + d + JSON.stringify(p);
      ['2026-10-25','2026-10-28','2026-10-30'].forEach((d) => localStorage.setItem(k(d, {tipo:'tudo',de:null,ate:null}), j));
      ['2026-10-29','2026-10-31'].forEach((d) => localStorage.setItem(k(d, {tipo:'7',de:null,ate:null}), j));
      localStorage.setItem(k('2026-10-27', {tipo:'periodo',de:'2026-10-20',ate:'2026-10-22'}), j);
      localStorage.setItem(k('2026-10-31', {tipo:'periodo',de:'2026-10-24',ate:'2026-10-30'}), j);
      localStorage.setItem('demo:rega.areas', j); localStorage.setItem('demo:rega.painel.cache.x', j); localStorage.setItem('rega.lingua2', 'fica'); }""", JUNK)
    pg.fill("#l-user", "g"); pg.fill("#l-pin", "x"); pg.click("#l-entrar"); pg.wait_for_selector("#kpis .kpi", state="visible"); pg.wait_for_timeout(4000)
    ks = pg.evaluate("Object.keys(localStorage).filter(k => k.startsWith('rega.painel.cache.')).map(k => k.slice(18)).sort()")
    print("1 cópias do painel depois de abrir:"); [print("   ", k) for k in ks]
    print("2 sobras da apresentação continuam (só se apagam quando falta espaço):", pg.evaluate("[localStorage.getItem('demo:rega.areas') != null, localStorage.getItem('rega.lingua2')]"))
    # espaço cheio: enche com lixo da apresentação até ao limite e grava uma cópia grande do painel
    n = pg.evaluate("""(j) => { let i = 0; try { for (;;) { localStorage.setItem('demo:lixo' + i, j); i++; } } catch {} return i; }""", JUNK)
    print("3 lixo da apresentação até encher:", n, "× 0,4 MB")
    print("4 guardarCache com o espaço cheio:", pg.evaluate("guardarCache({tipo:'30',de:null,ate:null}, {grande: 'y'.repeat(1500000)})"), "| sobras demo:", pg.evaluate("Object.keys(localStorage).filter(k => k.startsWith('demo:')).length"))
    pg.close()
    # app: o mesmo com LS.set
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: (dialogos.append(d.message), d.accept()))
    pg.goto("http://localhost:8868/"); pg.wait_for_selector("#l-entrar", state="visible")
    n = pg.evaluate("""(j) => { let i = 0; try { for (;;) { localStorage.setItem((i % 2 ? 'demo:lixo' : 'rega.painel.cache.2026-10-01x') + i, j); i++; } } catch {} return i; }""", JUNK)
    print("5 app: cópias do painel + sobras até encher:", n)
    print("6 LS.set grande:", pg.evaluate("LS.set('teste', 'z'.repeat(1500000))"), "| avisos:", dialogos)
    n = pg.evaluate("""(j) => { let i = 0; try { for (;;) { localStorage.setItem('rega.outro' + i, j); i++; } } catch {} return i; }""", JUNK)
    print("7 cheio com dados da app (não se apagam):", n, "| LS.set:", pg.evaluate("LS.set('teste2', 'z'.repeat(1500000))"), "| 2.ª vez:", pg.evaluate("LS.set('teste3', 'z'.repeat(1500000))"))
    print("8 avisos:", dialogos)
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
