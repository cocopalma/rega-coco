# v214 (07/11/2026, Valdo, novo visual parte 3: ficha do campo F1–F5): 4 dados + «Ver todos os dados», acção principal grande,
# «Regar pela equipa» e «Navegar» lado a lado, registos em quadrados, «Gerir o campo» numa lista com «Retirar da rega» a vermelho. LING=en / sw
import os
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8873"').replace("localhost:8858", "localhost:8873"))
LG = os.environ.get("LING", "pt")
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha()")
    PEDIDOS["contar"] = True
    for papel in ("tecnico", "supervisor", "gestor", "activista", "cliente"):
        demo(pg, papel); pg.evaluate("fecharFolha()"); pg.wait_for_timeout(800)
        pg.evaluate("abrirFicha('PR900101-1')"); pg.wait_for_timeout(500)
        f = "#folha-c"
        print(f"1 {papel}: cabeça:", pg.inner_text(f"{f} h2"), "|", pg.inner_text(f"{f} > p.pequeno").strip()[:60], "| etiquetas:", pg.inner_text(f"{f} > .it-tags").replace("\n", " | "))
        print(f"2 {papel}: resumo:", pg.evaluate("[...document.querySelectorAll('#folha-c .fi-res > .lin')].map(l=>l.innerText.replace(/\\n/g,': '))"),
              "| mais fechado:", not pg.evaluate("document.querySelector('#folha-c .fi-mais').open"))
        pg.click(f"{f} .fi-mais summary"); pg.wait_for_timeout(200)
        print(f"2b {papel}: ao tocar abre:", pg.evaluate("document.querySelector('#folha-c .fi-mais').open"), "|", pg.inner_text(f"{f} .fi-mais").replace("\n", " | ")[:220])
        print(f"3 {papel}: principal:", pg.evaluate("[...document.querySelectorAll('#folha-c .btn.principal')].map(b=>b.textContent.trim()+' '+b.offsetHeight+'px')"),
              "| lado a lado:", pg.evaluate("[...document.querySelectorAll('#folha-c .fi-par .btn')].map(b=>b.textContent.trim())"))
        print(f"4 {papel}: Registar:", pg.evaluate("[...document.querySelectorAll('#folha-c .fi-q')].map(b=>b.innerText.replace(/\\n/g,' '))"))
        print(f"5 {papel}: Gerir:", pg.evaluate("[...document.querySelectorAll('#folha-c .fi-g')].map(b=>(b.classList.contains('vermelho')?'[vermelho] ':'')+b.innerText.trim())"))
        pg.screenshot(path=f"/home/claude/rega-test/v214_{papel}_{LG}.png", full_page=True)
        if papel == "tecnico":
            pg.click("#folha-c .fi-q:has-text('🌴')"); pg.wait_for_timeout(500); print("6 tecnico: quadrado Mapa das plantas abre:", txt(pg, "#folha-c")[:60])
            pg.evaluate("abrirFicha('PR900101-1')"); pg.wait_for_timeout(300)
            pg.click("#folha-c .fi-q:has-text('🔥')"); pg.wait_for_timeout(500); print("6b tecnico: quadrado queimada abre:", txt(pg, "#folha-c")[:60])
            pg.evaluate("abrirFicha('PR900101-1')"); pg.wait_for_timeout(300)
            if pg.locator("#folha-c .fi-g.vermelho").count(): pg.click("#folha-c .fi-g.vermelho"); pg.wait_for_timeout(400); print("6c tecnico: retirar abre:", txt(pg, "#folha-c")[:60])
        pg.evaluate("fecharFolha()")
    print("pedidos ao servidor:", PEDIDOS["n"])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
