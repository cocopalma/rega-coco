# v215 (07/11/2026, Valdo, novo visual parte 4: mapa M1–M3): à direita só «◎ Eu», «As minhas» e «Ferramentas»; Rodar, Medir,
# Percursos, Trilho, Satélite e Coqueiros no menu. LING=en / sw
import os
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8874"').replace("localhost:8858", "localhost:8874"))
LG = os.environ.get("LING", "pt")
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha()")
    PEDIDOS["contar"] = True
    vis = lambda: pg.evaluate("[...document.querySelectorAll('.flutua > button')].filter(b=>b.offsetParent).map(b=>b.textContent.trim())")
    menu = lambda: pg.evaluate("[...document.querySelectorAll('#ferr-menu button')].filter(b=>b.style.display!=='none').map(b=>b.textContent.trim()+(b.classList.contains('on')?' [ligado]':''))")
    for papel in ("gestor", "supervisor", "activista", "cliente"):
        if papel != "gestor": demo(pg, papel)
        pg.evaluate("fecharFolha(); mudar('mapa')"); pg.wait_for_timeout(1200)
        print(f"1 {papel}: à direita:", vis(), "| menu fechado:", pg.evaluate("document.getElementById('ferr-menu').hidden"), "| botão satélite do Leaflet visível:", pg.is_visible("#b-fundo"))
        pg.click("#b-ferr"); pg.wait_for_timeout(200)
        print(f"2 {papel}: menu:", menu())
        pg.screenshot(path=f"/home/claude/rega-test/v215_{papel}_{LG}.png")
        pg.click("#ferr-menu #b-sat"); pg.wait_for_timeout(400)
        print(f"3 {papel}: satélite: fundo:", pg.evaluate("LS.get('fundo')"), "| menu fechou:", pg.evaluate("document.getElementById('ferr-menu').hidden"))
        pg.click("#b-ferr"); pg.click("#ferr-menu #b-sat"); pg.wait_for_timeout(300)
        pg.click("#b-ferr"); pg.click("#ferr-menu #b-regua"); pg.wait_for_timeout(300)
        print(f"4 {papel}: medir ligado:", pg.is_visible("#regua"), "| ponto no Ferramentas:", pg.evaluate("document.getElementById('b-ferr').classList.contains('on')"))
        pg.click("#rg-fechar"); pg.wait_for_timeout(200)
        print(f"4b {papel}: medir fechado, ponto:", pg.evaluate("document.getElementById('b-ferr').classList.contains('on')"))
        pg.click("#b-ferr"); pg.wait_for_timeout(100); pg.mouse.click(150, 500); pg.wait_for_timeout(200)
        print(f"5 {papel}: tocar no mapa fecha o menu:", pg.evaluate("document.getElementById('ferr-menu').hidden"))
    print("pedidos ao servidor:", PEDIDOS["n"])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
