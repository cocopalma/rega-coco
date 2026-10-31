import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
M = {"amostrados": 24, "verificados": 21, "nota_media": 7.4, "solo_regado": 19, "plantas_obs": 720, "plantas_humidas": 610, "mudas": {"vivas": 17, "secas": 3, "mortas": 1},
  "por_verificador": [{"nome": "Guidion Cristovao", "papel": "tecnico", "amostrados": 12, "verificados": 11, "nota_media": 7.8}, {"nome": "Raul Miquilange", "papel": "supervisor", "amostrados": 12, "verificados": 10, "nota_media": 6.9}],
  "por_tecnico": [{"tecnico": "Guidion Cristovao", "verificados": 19, "solo_regado": 12, "nota_media": 7.6, "lqas_regados": 12}, {"tecnico": "Essumaila Carlos Assane", "verificados": 20, "solo_regado": 17, "nota_media": 7.1, "lqas_regados": 16}],
  "por_equipa": [{"nome": "Activista 01", "comunidade": "Farol", "verificados": 4, "nota_media": 8.0, "sem_sinais_rega": 0, "mudas_secas_mortas": 0, "plantas_obs": 140, "plantas_humidas": 131}, {"nome": "Activista 02", "comunidade": "Senga", "verificados": 3, "nota_media": 5.3, "sem_sinais_rega": 1, "mudas_secas_mortas": 2}]}
erros = []; rec_sign = []
OFF = [False]
def mock(route):
    if OFF[0]: return route.abort('internetdisconnected')
    u = route.request.url
    if "/rpc/painel_plantas_dia_equipa" in u: return route.fulfill(status=200, content_type="application/json", body=json.dumps([{"data": d, "equipa": f"Activista {i+1:02d}", "comunidade": coms[i % 3], "plantas": 300 + 37 * i + 11 * k, "campos": 3, "pessoas": 4 + (i + k) % 2, "tamanho": 5} for k, d in enumerate(dias) for i in range(5) if (i + k) % 4]))
    if "/rpc/painel_tempos_equipa" in u: return route.fulfill(status=200, content_type="application/json", body=json.dumps([{"equipa": f"Activista {i+1:02d}", "rega_min": 30 + i, "deslocacao_min": 8 + 2 * i, "deslocacoes": 12 + i} for i in range(5)]))
    if "/storage/v1/object/sign/chuva-fotos/" in u: rec_sign.append(u); return route.fulfill(status=200, content_type="application/json", body=json.dumps({"signedURL": "/storage/v1/object/sign/chuva-fotos/u1/f.jpg?token=t"}))
    if "/storage/v1/object/sign/" in u and "token=" in u: return route.fulfill(status=200, content_type="image/jpeg", body=open("/home/claude/rega-test/foto_teste.jpg","rb").read())
    if "/rpc/painel_chuva" in u: return route.fulfill(status=200, content_type="application/json", body=json.dumps([{"data": d, "comunidade": c, "mm": [0, 0, 12.5, 3, 0, 22][(k + i) % 6], "registos": 1, "fotos": [{"path": "u1/f.jpg", "mm": 12.5, "lida_em": "2026-10-20T05:15:00Z", "activista": "Activista 01"}]} for k, d in enumerate(dias[-8:]) for i, c in enumerate(["Olumbe", "Senga", "Farol", "Quionga"])]))
    if "/rpc/painel_zonas" in u: return route.fulfill(status=200, content_type="application/json", body=json.dumps([{"comunidade": "Palma Sede", "zona": "Incularino", "areas": 40, "vivas": 6000, "areas_regadas": 10, "vivas_regadas": 1500}, {"comunidade": "Palma Sede", "zona": "Muah", "areas": 19, "vivas": 3269, "areas_regadas": 9, "vivas_regadas": 1600}, {"comunidade": "Palma Sede", "zona": None, "areas": 53, "vivas": 7666, "areas_regadas": 0, "vivas_regadas": 0}]))
    if "/rpc/painel_monitoria" in u: return route.fulfill(status=200, content_type="application/json", body=json.dumps(M))
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
        pg.goto("http://localhost:8766/painel.html?embutido=1"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.fill("#l-user", "cliente"); pg.fill("#l-pin", "segredo123"); pg.click("#l-entrar"); pg.wait_for_selector("#kpis .kpi")
        pg.hover("#g-dia .marca-dados >> nth=4"); pg.wait_for_timeout(200)
        print(nome, "dica:", pg.inner_text("#dica").replace("\n", " | "), "| largura doc:", pg.evaluate("document.documentElement.scrollWidth"))
        print(nome, "pde:", pg.inner_text("#s-pde")[:300].replace("\n", " | "))
        print(nome, "meta dia:", pg.inner_text("#s-meta")[:260].replace("\n", " | "))
        pg.click("#v-meta button[data-v=semana]"); print(nome, "meta semana:", pg.inner_text("#t-meta")[:200].replace("\n", " | "))
        pg.click("#v-meta button[data-v=periodo]"); print(nome, "meta período:", pg.inner_text("#t-meta")[:300].replace("\n", " | "))
        print(nome, "tempos:", pg.eval_on_selector("#t-tempos","e=>[...e.querySelectorAll(\"tr\")].map(r=>r.textContent.trim()).join(\"\\n\")")[:160].replace("\n", " | "))
        pg.click("#v-meta button[data-v=dia]")
        n_antes = len(rec_sign); pg.click("#s-chuva summary"); pg.click("#t-chuva .foto-btn >> nth=0"); pg.wait_for_timeout(1200)
        print(nome, "foto chuva: pedidos de assinatura antes do toque:", n_antes, "| depois:", len(rec_sign), "| img:", pg.locator("body > div img").count())
        pg.mouse.click(10, 10); pg.wait_for_timeout(200)
        pg.locator("#s-chuva").screenshot(path=f"/home/claude/rega-test/fin_chuva_{nome}.png")
        print(nome, "com+zonas:", pg.eval_on_selector("#t-com","e=>[...e.querySelectorAll(\"tr\")].map(r=>r.textContent.trim()).join(\"\\n\")").replace("\n", " | ")[:400])
        for sel, nf in [("#t-equipa", "eq"), ("#s-pde", "com"), ("#t-agua", "agua"), ("#t-mon-tec", "mon"), ("#t-com", "zonas")]:
            pg.locator(sel).locator("xpath=ancestor-or-self::*[contains(@class,'card')][1]").screenshot(path=f"/home/claude/rega-test/fin_{nf}_{nome}.png")
        print(nome, "lqas:", pg.eval_on_selector("#t-mon-tec","e=>[...e.querySelectorAll(\"tr\")].map(r=>r.textContent.trim()).join(\"\\n\")").replace("\n", " | "))
        print(nome, "monitoria:", pg.inner_text("#s-mon")[:400].replace("\n", " | ") if pg.is_visible("#s-mon") else "ESCONDIDA")
        pg.hover("#g-meta-eq .marca-dados >> nth=0"); pg.wait_for_timeout(150); print(nome, "dica meta:", pg.inner_text("#dica").replace("\n", " | "))
        for g in ["g-meta-dia", "g-meta-eq", "g-tempos", "g-mon-eq"]: pg.locator("#" + g).screenshot(path=f"/home/claude/rega-test/{g}_{nome}.png")
        pg.screenshot(path=f"/home/claude/rega-test/painel_{nome}.png", full_page=True)
        if nome == "telefone":   # sem rede (14/10/2026, Nuro): painel guardado de ontem, e sem painel guardado
            pg.evaluate("""(() => { const k = Object.keys(localStorage).find((x) => x.startsWith('rega.painel.cache.')); const v = localStorage.getItem(k); localStorage.removeItem(k); localStorage.setItem(k.replace(/cache\.\d{4}-\d{2}-\d{2}/, 'cache.2026-01-01'), v); })()""")
            OFF[0] = True
            for modo, init in [("falha de rede", ""), ("telefone sem rede", "Object.defineProperty(navigator, 'onLine', { get: () => false });")]:
                p2 = ctx.new_page(); p2.on("pageerror", lambda e: erros.append(str(e)))
                if init: p2.add_init_script(init)
                t0 = time.time(); p2.goto("http://localhost:8766/painel.html?embutido=1"); p2.wait_for_timeout(2500)
                print("sem rede (" + modo + "):", round(time.time() - t0, 1), "s | aviso:", p2.inner_text("#aviso-rede") if p2.is_visible("#aviso-rede") else "—", "| kpis:", p2.locator("#kpis .kpi").count(), "| login visível:", p2.is_visible("#l-entrar"))
                p2.close()
            pg.evaluate("Object.keys(localStorage).filter((k) => k.startsWith('rega.painel.cache.')).forEach((k) => localStorage.removeItem(k))")
            p3 = ctx.new_page(); p3.add_init_script("Object.defineProperty(navigator, 'onLine', { get: () => false });"); p3.goto("http://localhost:8766/painel.html?embutido=1"); p3.wait_for_timeout(2500)
            print("sem rede e sem painel guardado:", p3.inner_text("#aviso-rede") if p3.is_visible("#aviso-rede") else "—", "| login visível:", p3.is_visible("#l-entrar")); p3.close()
            OFF[0] = False
        ctx.close()
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
