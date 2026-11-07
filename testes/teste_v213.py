# v213 (07/11/2026, Valdo, novo visual parte 2: Campos C1–C5): procura + «Filtros» numa folha, filtros rápidos com o número,
# avisos numa só linha, «Voltar a pôr na rega» e «Retirar vários» no menu ⋯, nome numa linha e etiquetas por baixo. LING=en / sw
import os, sys
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8872"').replace("localhost:8858", "localhost:8872"))
LG = os.environ.get("LING", "pt")
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha()")
    PEDIDOS["contar"] = True
    rap = lambda: pg.evaluate("[...document.querySelectorAll('#f-rap button')].map(b=>(b.classList.contains('on')?'*':'')+b.textContent.trim())")
    for papel in ("tecnico", "supervisor", "activista"):
        demo(pg, papel); pg.evaluate("fecharFolha(); mudar('lista')"); pg.wait_for_timeout(1500)
        print(f"1 {papel}: filtros visíveis:", pg.evaluate("[...document.querySelectorAll('#e-lista select')].filter(s=>s.offsetParent).length"), "| procura:", pg.is_visible("#f-txt"), "| Filtros:", pg.is_visible("#f-btn"), "| ⋯:", pg.is_visible("#f-acc"))
        print(f"2 {papel}: rápidos:", rap())
        print(f"3 {papel}: avisos:", pg.inner_text("#av-lista").replace("\n", " ") if pg.locator("#av-lista").count() else "(nenhum)")
        it = pg.locator("#lista .item").first
        print(f"4 {papel}: 1.º campo: cabeça:", it.locator(".it-cab").inner_text().replace("\n", " | "), "| sub:", it.locator(".sub").inner_text(), "| etiquetas:", it.locator(".it-tags").inner_text().replace("\n", " | "))
        pg.screenshot(path=f"/home/claude/rega-test/v213_{papel}_{LG}.png")
        n0 = pg.locator("#lista .item").count()
        pg.click("#f-rap button:nth-child(3)"); pg.wait_for_timeout(300)
        print(f"5 {papel}: depois de tocar no 3.º rápido:", rap(), "| campos:", pg.locator("#lista .item").count(), "de", n0, "| f-sit:", pg.input_value("#f-sit"))
        pg.click("#f-rap button:nth-child(1)"); pg.wait_for_timeout(300)
        pg.click("#f-btn"); pg.wait_for_timeout(300)
        print(f"6 {papel}: folha Filtros:", txt(pg, "#folha-c")[:200], "| selects visíveis:", pg.evaluate("[...document.querySelectorAll('#folha-c select')].filter(s=>s.offsetParent).map(s=>s.id)"))
        coms = pg.evaluate("[...document.querySelectorAll('#f-com option')].map(o=>o.value).filter(Boolean)")
        if coms: pg.select_option("#f-com", coms[0]); pg.wait_for_timeout(300)
        print(f"6b {papel}: comunidade {coms[:1]}: botão:", pg.inner_text("#f-ver"), "| lista atrás:", pg.locator("#lista .item").count())
        pg.click("#f-ver"); pg.wait_for_timeout(300)
        print(f"6c {papel}: folha fechada:", not pg.is_visible("#folha"), "| nº de filtros:", pg.inner_text("#f-n"), "| selects de volta ao sítio:", pg.evaluate("document.getElementById('f-guarda').contains(document.getElementById('f-sit'))"))
        pg.click("#f-btn"); pg.click("#folha-c button:has-text('Limpar'), #folha-c button:has-text('Clear'), #folha-c button:has-text('Futa')"); pg.wait_for_timeout(300); pg.evaluate("fecharFolha()")
        print(f"6d {papel}: limpar: nº de filtros:", repr(pg.inner_text("#f-n")), "| campos:", pg.locator("#lista .item").count())
        if pg.locator("#av-lista").count():
            pg.click("#av-lista"); pg.wait_for_timeout(300); print(f"7 {papel}: folha dos avisos:", txt(pg, "#folha-c")[:260]); pg.evaluate("fecharFolha()")
        if pg.is_visible("#f-acc"):
            pg.click("#f-acc"); pg.wait_for_timeout(300); print(f"8 {papel}: menu ⋯:", txt(pg, "#folha-c"))
            pg.click("#folha-c button[onclick*=retirarVarios]"); pg.wait_for_timeout(400)
            print(f"8b {papel}: retirar vários:", pg.is_visible("#sel-ret"), "| caixas:", pg.locator("#lista .cx-ret").count()); pg.evaluate("retirarVarios(false)")
        pg.evaluate("$('#f-sit').value='queimada'; desenharLista()"); pg.wait_for_timeout(200)
        print(f"9 {papel}: filtro fora dos rápidos:", rap()[-1:], "| nº de filtros:", pg.inner_text("#f-n")); pg.evaluate("filtroRapido('')")
    # recontagens por comunidade (Valdo, 07/11: "Aqui deve estar apresentado por comunidade")
    for papel in ("me", "gestor"):
        demo(pg, papel); pg.evaluate("DEMO.recomecar('exemplos')"); pg.wait_for_selector("#demo-faixa", state="visible", timeout=15000); pg.wait_for_timeout(3000)
        pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(1500)
        if pg.locator("#hoje-abas [data-v=rec]").count(): pg.click("#hoje-abas [data-v=rec]"); pg.wait_for_timeout(800)
        print(f"11 {papel}: recontagens:", pg.evaluate("[...document.querySelectorAll('#hoje h3, #hoje details.tar[data-k^=rc-] > summary')].map(e=>e.textContent.trim().replace(/\\s+/g,' '))"))
        d = pg.locator("#hoje details.tar[data-k^=rc-]").first
        if d.count(): d.locator("summary").click(); pg.wait_for_timeout(200); print(f"11b {papel}: aberta:", d.inner_text().replace("\n", " | ")[:200])
        pg.screenshot(path=f"/home/claude/rega-test/v213_rec_{papel}_{LG}.png")
    # selects escondidos: o select_option dos testes antigos ainda funciona?
    try: pg.select_option("#f-sit", "nunca", timeout=3000); print("10 select_option escondido: OK", pg.input_value("#f-sit"))
    except Exception as e: print("10 select_option escondido: FALHA", str(e)[:120])
    print("pedidos ao servidor:", PEDIDOS["n"])
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
