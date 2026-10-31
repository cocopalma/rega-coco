import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8776", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
coms = ["Farol","Quitunda","Senga","Olumbe","Maganja","Mute","Nhica do Rovuma","Quionga","Palma Sede","Pundanhar","Ngueo","Malinde","Mangala","Milamba","Ncumbi","Manguna"]
dias = [f"2026-10-{d:02d}" for d in range(12, 24)]
D = {"gerado_em": "2026-10-23T16:05:00Z", "inicio": dias[0], "universo": {"areas": 721, "vivas": 94529, "com_activista": 574},
  "areas_regadas": 402, "vivas_regadas": 51820, "plantas_regadas_total": 63410, "pessoas_dia_total": 1410, "registos": 690,
  "dias_medios_entre_regas": 8.6, "alertas": 7, "gps_invalido": 3, "espera_agua_min": 22,
  "por_dia": [{"data": d, "plantas": 4200 + (i*373 % 2100), "campos": 45 + i % 9, "equipas": 24 + i % 4, "pessoas": 110 + i*3} for i, d in enumerate(dias)],
  "por_comunidade": [{"comunidade": c, "areas": 30 + i*3, "vivas": 4000 + i*450, "areas_regadas": 15 + i, "vivas_regadas": int((4000 + i*450) * (0.25 + (i*37 % 70)/100)), "regas": 30 + i*4, "dias_medios_entre_regas": None if i % 5 == 0 else 6 + i % 6} for i, c in enumerate(coms)],
  "por_equipa": [{"nome": f"Activista {i+1:02d}", "comunidade": coms[i % 16], "lista": 18 + i % 9, "ronda": 1 + (i % 3 == 0), "regadas_ronda": (i*5) % 18, "inicio_ronda": dias[3],
     "rondas_concluidas": [{"ronda": 1, "inicio": dias[0], "fim": dias[8], "dias": 9}] if i % 3 == 0 else None, "dias_trabalhados": 10, "plantas": 2300 + i*40, "pessoas_dia": 48, "espera_agua_min": 10 + i % 30, "min_por_campo": 35 + i % 20} for i in range(28)],
  "chegadas_agua": [{"data": dias[-1 - k], "equipa": f"Activista {i+1:02d}", "comunidade": coms[i % 16], "inicio_trabalho": "06:40", "primeira_agua": None if i == 3 else f"07:{(i*7)%60:02d}", "chegadas": 2, "horas": f"07:{(i*7)%60:02d} · 10:15", "campos": 3, "espera_media_min": 15 + i} for k in range(2) for i in range(6)],
  "constrangimentos": {"falta_agua": 41, "mudas_secas": 17, "acesso_dificil": 9, "avaria": 4, "outro": 2}}
erros = []
def mock(route):
    u = route.request.url
    if "/rpc/painel_resumo" in u: return route.fulfill(status=200, content_type="application/json", body=json.dumps(D))
    if "/auth/v1/token" in u: return route.fulfill(status=200, content_type="application/json", body=json.dumps({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time())+3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "cliente@rega-coco.example.com"}}))
    route.fulfill(status=200, content_type="application/json", body="{}")
with sync_playwright() as p:
    b = p.chromium.launch()
    for nome, vp, esquema in [("desktop", {"width": 1280, "height": 900}, "light"), ("telefone", {"width": 390, "height": 844}, "light"), ("escuro", {"width": 1280, "height": 900}, "dark")]:
        ctx = b.new_context(viewport=vp, color_scheme=esquema)
        ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
        ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
        pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e)))
        pg.evaluate("1") if False else None; pg.add_init_script("try{localStorage.setItem('rega.lingua','en')}catch(e){}"); pg.goto("http://localhost:8776/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.fill("#l-user", "cliente"); pg.fill("#l-pin", "segredo123"); pg.click("#l-entrar"); pg.wait_for_selector("#kpis .kpi")
        pg.hover("#g-dia .marca-dados >> nth=4"); pg.wait_for_timeout(200)
        print(nome, "dica:", pg.inner_text("#dica").replace("\n", " | "), "| largura doc:", pg.evaluate("document.documentElement.scrollWidth"))
        pg.screenshot(path=f"/home/claude/rega-test/painel_{nome}.png", full_page=True)
        import re
        t = pg.inner_text("body"); pt = [l for l in t.split("\n") if re.search(r"[ãõçáéíóú]|\b(de|do|da|das|campos|plantas|ronda|equipa|regad|dias)\b", l, re.I)]
        print("linhas com PT:", pt[:30]); pg.screenshot(path="/home/claude/rega-test/en_painel.png", full_page=True)
        ctx.close()
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
