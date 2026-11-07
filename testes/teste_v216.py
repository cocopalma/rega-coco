# v216 (07/11/2026, Valdo): número da versão da app no ⚙️ Definições. LING=en / sw
import os
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8875"').replace("localhost:8858", "localhost:8875"))
LG = os.environ.get("LING", "pt")
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha()")
    PEDIDOS["contar"] = True
    for papel in ("gestor", "activista", "cliente"):
        if papel != "gestor": demo(pg, papel)
        pg.evaluate("fecharFolha()"); pg.click("#h-conf"); pg.wait_for_timeout(300)
        print(f"{papel}: versão:", pg.inner_text("#def-versao"))
        pg.screenshot(path=f"/home/claude/rega-test/v216_{papel}_{LG}.png")
    print("pedidos ao servidor:", PEDIDOS["n"])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
