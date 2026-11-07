# v212 (07/11/2026, Valdo: aprovou as propostas de G1–G3 e H1–H4, para todos): menu em baixo com ícones, topo com ⚙️ Definições
# (língua, senha, sair), Hoje do técnico/supervisor com listas que abrem ao tocar e números, «Mais» no fim. LING=en / sw
import os, sys, runpy
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
corpo = SRC.split("with sync_playwright() as p:")[0]
exec(corpo.replace('"8858"', '"8871"').replace("localhost:8858", "localhost:8871"))
LG = os.environ.get("LING", "pt")
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha()")
    vis = lambda: pg.evaluate("[...document.querySelectorAll('#nav button[data-e]')].filter(b=>b.offsetParent).map(b=>b.textContent.trim())")
    print("1 gestor: menu:", vis(), "| em baixo:", pg.evaluate("document.getElementById('nav').getBoundingClientRect().bottom") >= 840,
          "| ícones:", pg.locator("#nav button svg").count(), "| topo:", pg.evaluate("[...document.querySelectorAll('header button')].filter(b=>b.offsetParent).map(b=>b.id).join(' ')"))
    print("1b sem Sair nem língua no topo:", pg.locator("#h-sair").count() == 0 and pg.locator("#h-lingua").count() == 0)
    pg.click("#h-conf"); pg.wait_for_timeout(300)
    print("2 Definições:", txt(pg, "#folha-c")[:260])
    pg.click("#folha-c .chips button >> nth=1"); pg.wait_for_timeout(800)
    print("2b língua mudou para:", pg.evaluate("localStorage.getItem('rega.lingua')"), "| menu:", vis())
    pg.evaluate(f"escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True
    for papel in ("tecnico", "supervisor"):
        demo(pg, papel); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(3500)
        linhas = pg.evaluate("[...document.querySelectorAll('#meu-dia details.tar')].map(d=>d.dataset.k+':'+((d.querySelector('.nb')||{}).textContent||'-')+(d.open?' (aberta)':''))")
        print(f"3 {papel}: topo do Hoje:", txt(pg, "#meu-dia")[:120])
        print(f"3 {papel}: linhas:", linhas, "| separadores:", pg.locator("#hoje-abas").count())
        r = pg.locator("#meu-dia details.tar summary").first; r.click(); pg.wait_for_timeout(300)
        print(f"3b {papel}: abriu ao tocar:", pg.evaluate("document.querySelector('#meu-dia details.tar').open"), "| conteúdo:", pg.inner_text("#meu-dia details.tar .tc")[:140].replace("\n", " | "))
        fe = pg.evaluate("[...document.querySelectorAll('#meu-dia button')].filter(b=>/Fechar o dia|Close the day|Funga siku/.test(b.textContent)).map(b=>b.textContent.trim()+(b.disabled?' (desactivado)':''))")
        print(f"3c {papel}: fechar o dia:", fe, "| ⓘ:", pg.locator("#meu-dia details.ajuda").count())
        print(f"4 {papel}: Mais:", pg.evaluate("[...document.querySelectorAll('#hoje .mais-tit ~ details.tar, #hoje details.tar[data-k^=m-]')].map(d=>d.dataset.k+':'+(d.querySelector('.tt')||d).textContent.trim().slice(0,40))"))
        pg.screenshot(path=f"/home/claude/rega-test/v212_{papel}_{LG}.png", full_page=True)
        print(f"5 {papel}: menu:", vis(), "| Definições:", (pg.click("#h-conf"), pg.wait_for_timeout(300), txt(pg, "#folha-c"))[2][:160]); pg.evaluate("fecharFolha()")
    demo(pg, "activista"); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(3000)
    print("6 activista: menu:", vis(), "| O meu dia:", pg.locator("#meu-dia").count(), "| Hoje:", txt(pg, "#hoje")[:160])
    pg.screenshot(path=f"/home/claude/rega-test/v212_activista_{LG}.png", full_page=True)
    demo(pg, "cliente"); pg.evaluate("fecharFolha()"); pg.wait_for_timeout(500)
    print("7 cliente: menu:", vis())
    print("pedidos ao servidor:", PEDIDOS["n"])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
