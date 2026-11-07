# v217 (07/11/2026, Valdo): 🚱 no mapa nos campos que nunca receberam água + linha na legenda. LING=en / sw
import os
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8876"').replace("localhost:8858", "localhost:8876"))
LG = os.environ.get("LING", "pt")
CONTA = "[...document.querySelectorAll('.ic-fogo')].filter(e=>e.textContent.includes('🚱')).length"
ESPERADO = "visiveis().filter(a=>a.latitude!=null && a.activista_id && nuncaAgua(a)).length"
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha()")
    PEDIDOS["contar"] = True
    for papel in ("supervisor", "activista", "cliente"):
        demo(pg, papel)
        pg.evaluate("fecharFolha(); mudar('mapa')"); pg.wait_for_timeout(1200)
        print(f"1 {papel}: 🚱 no mapa:", pg.evaluate(CONTA), "| campos nunca regados com coordenada:", pg.evaluate(ESPERADO))
        pg.click("#leg-btn"); pg.wait_for_timeout(200)
        print(f"2 {papel}: legenda:", [t for t in pg.evaluate("[...document.querySelectorAll('#legenda div')].filter(d=>!d.children.length).map(d=>d.textContent.trim())") if '🚱' in t])
        pg.screenshot(path=f"/home/claude/rega-test/v217_{papel}_{LG}.png")
        pg.evaluate("verLegenda && verLegenda(false)")
    print("pedidos ao servidor:", PEDIDOS["n"])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
