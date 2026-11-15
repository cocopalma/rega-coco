# v240: «Resumo por» na lista dos Campos (simulação; nada sai para o servidor). LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8875"').replace("localhost:8858", "localhost:8875"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
T = {"pt": ("Resumo por", "plantas vivas"), "en": ("Summary by", "live plants"), "sw": ("Muhtasari kwa", "mimea hai")}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-16T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "supervisor"); pg.evaluate("fecharFolha(); mudar('lista'); $('#f-ambito').value='todas'; S.filtro='todas'; desenharLista()"); pg.wait_for_timeout(1200)
    passo("1 supervisor vê «Resumo por»", pg.is_visible("#res-por") and T[0].lower() in pg.inner_text("#res-por").lower(), pg.inner_text("#res-por").replace("\n", " | "))
    n0 = pg.locator("#lista .item").count(); passo("2 começa em lista", n0 > 0 and pg.locator("#lista .res-g").count() == 0, f"campos={n0}")
    pg.click("#res-por button:has-text('" + {"pt": "Técnico", "en": "Technician", "sw": "Fundi"}[LG] + "')"); pg.wait_for_timeout(400)
    g = pg.locator("#lista .res-g"); tot = pg.inner_text("#res-tot")
    soma = pg.evaluate("[...document.querySelectorAll('#lista .res-c')].reduce((t, e) => t + +e.textContent, 0)")
    passo("3 por técnico: grupos e soma = total", g.count() >= 2 and soma == n0 and pg.locator("#lista .item").count() == 0 and T[1] in tot, f"grupos={g.count()} soma={soma} | {tot} | {g.first.inner_text()[:90]!r}")
    g.first.click(); pg.wait_for_timeout(400)
    v1 = pg.inner_text("#res-volta"); n1 = pg.locator("#lista .res-g").count()
    passo("4 desce para as comunidades (ou salta)", pg.is_visible("#res-volta"), f"{v1} | grupos={n1} campos={pg.locator('#lista .item').count()}")
    desc = 0
    while pg.locator("#lista .res-g").count() and desc < 4: pg.locator("#lista .res-g").first.click(); pg.wait_for_timeout(300); desc += 1
    nf = pg.locator("#lista .item").count(); tt = pg.evaluate("+document.querySelector('#res-tot b').textContent")
    passo("5 chega aos campos e o total bate", nf > 0 and nf == tt, f"{pg.inner_text('#res-volta')} | campos={nf} total={tt}")
    pg.locator("#lista .item").first.click(); pg.wait_for_timeout(700)
    passo("6 tocar no campo abre a ficha", pg.evaluate("!!S.fichaAberta"))
    pg.evaluate("fecharFolha()")
    k = 0
    while pg.locator("#res-volta").count() and k < 6: pg.click("#res-volta"); pg.wait_for_timeout(250); k += 1
    passo("7 voltar regressa ao 1.º nível", pg.locator("#res-volta").count() == 0 and pg.locator("#lista .res-g").count() >= 2, f"toques={k}")
    pg.evaluate("filtroRapido('por')"); pg.wait_for_timeout(300)
    s2 = pg.evaluate("[...document.querySelectorAll('#lista .res-c')].reduce((t, e) => t + +e.textContent, 0)"); np_ = pg.evaluate("S.nLista")
    passo("8 com filtro «Por regar» o resumo segue o filtro", s2 == np_ and np_ <= n0, f"soma={s2} lista={np_}")
    pg.evaluate("filtroRapido('')")
    for m, nome in [("com", "comunidade"), ("act", "activista"), ("sup", "supervisor")]:
        pg.evaluate(f"setResumo('{m}')"); pg.wait_for_timeout(250)
        sm = pg.evaluate("[...document.querySelectorAll('#lista .res-c')].reduce((t, e) => t + +e.textContent, 0)")
        passo(f"9 por {nome}: soma = total", sm == n0 and pg.locator('#lista .res-g').count() >= 1, f"grupos={pg.locator('#lista .res-g').count()} soma={sm}")
    pg.screenshot(path=f"/home/claude/rega-test/v240_{LG}.png")
    pg.evaluate("setResumo('tec')"); pg.reload(); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha(); mudar('lista')"); pg.wait_for_timeout(800)
    passo("10 a escolha fica no telefone", pg.evaluate("S.resumo") == "tec" and pg.locator("#lista .res-g").count() >= 1)
    pg.evaluate("setResumo('')")
    demo(pg, "activista"); pg.evaluate("fecharFolha(); mudar('lista')"); pg.wait_for_timeout(1000)
    passo("11 activista não vê o resumo", pg.locator("#res-por").count() == 0 and pg.locator("#lista .item").count() > 0)
    demo(pg, "cliente"); pg.evaluate("fecharFolha(); mudar('lista')"); pg.wait_for_timeout(1000)
    passo("12 cliente vê o resumo", pg.locator("#res-por").count() == 1)
    passo("13 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    print("RESULTADO:", "OK" if all(res.values()) and not erros else "FALHOU"); print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
