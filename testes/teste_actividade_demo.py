# Cava-roda e mulching na simulação (ramo cc-manutencao): o activista regista (motivo, início do dia, 3 fotografias, fim) e o
# técnico vê a 🌱 no «O meu dia» e na ficha do campo. Nada sai para o servidor. LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8873"').replace("localhost:8858", "localhost:8873"))
LG = os.environ.get("LING", "pt"); FOTO = "/home/claude/rega-test/foto_teste.jpg"; res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-16T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "activista"); pg.evaluate("fecharFolha()")
    id = pg.evaluate("S.areas.find(a => a.activista_id === S.perfil.activista_id && a.latitude != null).id")
    pg.evaluate(f"DEMO.irPara('{id}')"); pg.wait_for_timeout(500); ficha(pg, id)
    passo("1 botão na ficha (simulação)", pg.is_visible("#b-act"), id)
    pg.click("#b-act"); pg.click("#ac-mot .chip[data-k=tuk_tuk]"); pg.click("#ac-ok"); pg.wait_for_timeout(600)
    if pg.is_visible("#j-pessoas"): pg.fill("#j-pessoas", "5"); pg.click("#folha-c button.btn")
    elif pg.locator("#j-lista").count(): pg.click("#folha-c button.btn")
    pg.wait_for_selector("#fa-foto", state="attached", timeout=30000)
    pg.set_input_files("#fa-foto", FOTO); pg.wait_for_selector("#act-curso", timeout=10000)
    pg.locator("#act-curso + .cartao button.chip").nth(1).click(); pg.wait_for_timeout(300)
    pg.set_input_files("#fa-foto", FOTO); pg.wait_for_selector("#act-curso", timeout=10000)
    pg.click("#b-act-fim"); pg.wait_for_selector("#af-ok")
    pg.fill("#af-cav", "25"); pg.fill("#af-mul", "10"); pg.set_input_files("#af-foto", FOTO); pg.wait_for_timeout(800)
    if not pg.input_value("#af-pess"): pg.fill("#af-pess", "5")
    pg.click("#af-ok"); pg.wait_for_timeout(3500)
    n = DB(pg, "(D.act||[]).length")
    passo("2 gravada na base de exemplo", n == 1, f"actividades={n}")
    pg.wait_for_timeout(800); passo("3 ficha mostra a actividade", "25" in pg.inner_text("#f-act"), pg.inner_text("#f-act")[:100].replace("\n", " | "))
    demo(pg, "tecnico"); pg.evaluate("fecharFolha(); window.__TAR_ABERTAS = true; mudar('hoje')"); pg.wait_for_timeout(3500)
    t = pg.inner_text("#meu-dia")
    passo("4 técnico: «O meu dia» mostra a 🌱", "🌱" in t, [l for l in t.split("\n") if "🌱" in l][:2])
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(6000)
    fr = next((f for f in pg.frames if "painel.html" in f.url), None)
    tp = fr.inner_text("#s-act") if fr and fr.locator("#s-act").count() and fr.is_visible("#s-act") else ""
    passo("4b painel: secção da cava-roda", "25" in tp, tp[:160].replace("\n", " | "))
    passo("5 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    pg.screenshot(path=f"/home/claude/rega-test/actividade_demo_{LG}.png")
    print("RESULTADO:", "OK" if all(res.values()) and not erros else "FALHOU")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
