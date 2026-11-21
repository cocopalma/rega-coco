# v254: inventário de plantas mórbidas — a app diz quantas plantas verificar (amostra de Cochran da monitoria) e pede o percurso
# (X, W, Z, Diagonal); sem percurso não grava; o percurso e as plantas a verificar aparecem na ficha e no painel. Simulação. LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8889"').replace("localhost:8858", "localhost:8889"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
FOTO = "/home/claude/rega-test/foto_teste.jpg"
T = {"pt": ("Inventário de plantas mórbidas", "Plantas a verificar", "Escolha o percurso", "percurso", "Percurso"),
     "en": ("Inventory of weak plants", "Plants to check", "Choose the route", "route", "Route"),
     "sw": ("Hesabu ya mimea dhaifu", "Mimea ya kukagua", "Chagua njia", "njia", "Njia")}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-21T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "tecnico"); pg.evaluate("fecharFolha()")
    a = pg.evaluate("(() => { const a = S.areas.find((x) => x.activista_id && meuCampo(x) && x.latitude != null && plantasN(x) > 30); return { id: a.id, N: plantasN(a), alvo: amostraMorb(plantasN(a)) } })()")
    pg.evaluate(f"DEMO.irPara('{a['id']}')"); pg.wait_for_timeout(1500)
    pg.evaluate(f"abrirFicha('{a['id']}')"); pg.wait_for_timeout(800)
    pg.locator("#folha .fi-q", has_text=T[0]).click(); pg.wait_for_selector("#mb-gravar")
    tx = pg.inner_text("#folha")
    passo("1 diz as plantas a verificar", T[1] in tx and str(a["alvo"]) in pg.inner_text("#mb-alvo"), f"N={a['N']} alvo={a['alvo']} -> {pg.inner_text('#mb-alvo')}")
    passo("2 observadas começa com as plantas a verificar", pg.input_value("#mb-n") == str(a["alvo"]))
    pg.fill("#mb-m", "5"); pg.set_input_files("#mb-fc", FOTO); pg.wait_for_timeout(1200); pg.set_input_files("#mb-fe", FOTO); pg.wait_for_timeout(1200)
    pg.click("#mb-gravar"); pg.wait_for_timeout(800)
    passo("3 sem percurso não grava", T[2] in pg.inner_text("#mb-msg") and pg.evaluate("LS.get('filaMorb', []).length") == 0, pg.inner_text("#mb-msg"))
    pg.click("#mb-metodo .chip[data-v=W]"); pg.wait_for_timeout(300)
    passo("4 desenho do percurso", pg.locator("#mb-desenho svg").count() == 1)
    pg.click("#mb-Nmudar"); pg.fill("#mb-N", "300"); pg.wait_for_timeout(300)
    alvo2 = pg.evaluate("amostraMorb(300)")
    passo("5 corrigir o nº de plantas recalcula", str(alvo2) in pg.inner_text("#mb-alvo") and pg.input_value("#mb-n") == str(alvo2), pg.inner_text("#mb-alvo"))
    pg.fill("#mb-n", "10"); pg.wait_for_timeout(300)
    passo("6 aviso de menos plantas observadas", pg.inner_text("#mb-nmsg").strip() != "")
    pg.fill("#mb-n", str(alvo2)); pg.click("#mb-gravar"); pg.wait_for_timeout(5000)
    d = pg.evaluate("RPC_DEMO_ULT = null, (window.__dbMorb = JSON.parse(sessionStorage.getItem('rega.demo.db')||'{}').morb || [])")
    u = (d or [{}])[-1]
    passo("7 gravado com o percurso e as plantas a verificar", u.get("metodo") == "W" and u.get("plantas_alvo") == alvo2 and u.get("plantas_campo") == 300, str(u)[:300])
    pg.wait_for_timeout(1500); fx = pg.inner_text("#folha") if pg.is_visible("#folha") else ""
    passo("8 ficha mostra o percurso", f"{T[3]} W" in fx, fx[-300:].replace("\n", " | "))
    pg.screenshot(path=f"/home/claude/rega-test/v254_a_{LG}.png")
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(8000)
    fr = pg.frame("painel") or [x for x in pg.frames if "painel.html" in x.url][0]
    tp = fr.inner_text("#t-mrb")
    passo("9 painel: colunas percurso e plantas a verificar", T[4] in tp and T[1] in tp and " W" in tp.replace("\t", " "), tp[:300].replace("\n", " | "))
    passo("10 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
