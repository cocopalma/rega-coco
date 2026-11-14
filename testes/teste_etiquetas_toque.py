# Etiquetas dos campos ao tocar (ramo cc-manutencao, Valdo 14/11/2026), na simulação: por defeito sem etiquetas; 1.º toque num campo
# mostra a etiqueta; 2.º toque no mesmo campo abre a ficha; várias abertas ao mesmo tempo; tocar na etiqueta fecha-a; «Esconder
# etiquetas» fecha todas. (O teste faz de conta que a pessoa arrastou o mapa: senão o mapa volta ao ponto azul.) Activista, técnico, supervisor e gestor; telefone (390 px) e computador (1280 px). LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8874"').replace("localhost:8858", "localhost:8874"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
def tocar(pg, id):   # toque verdadeiro no ponto do campo (o mapa desenha em canvas/SVG)
    # aproxima o mapa ao campo (com pouco zoom os ícones 🚱/🔥 de 22 px dos campos vizinhos tapam o ponto)
    x, y = pg.evaluate(f"(() => {{ const a = S.areas.find(z => z.id === '{id}'); S.seguirCentro = false; S.euVisivel = false; mapa.setView([a.latitude, a.longitude], 18, {{ animate: false }}); const p = mapa.latLngToContainerPoint([a.latitude, a.longitude]); const r = document.getElementById('mapa').getBoundingClientRect(); return [r.left + p.x, r.top + p.y]; }})()")
    pg.mouse.click(x, y); pg.wait_for_timeout(400)
etiq = lambda pg: pg.evaluate("[...document.querySelectorAll('.rot-campo')].map(e => e.dataset.id)")
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    for papel in ("activista", "tecnico", "supervisor", "gestor"):
        for larg in (390, 1280):
            pg.set_viewport_size({"width": larg, "height": 844})
            demo(pg, papel); pg.evaluate("fecharFolha(); mudar('mapa')"); pg.wait_for_timeout(800)
            # campos cujo ponto não fica dentro (nem a menos de 25 m) de outro campo à vista: o toque cai mesmo nesse campo
            ids = pg.evaluate("(() => { const V = visiveis().filter(a => a.latitude != null); return V.filter(a => !V.some(o => o !== a && distCampo(o, [a.latitude, a.longitude]) < 25)).map(a => a.id); })()")
            # dois campos afastados no ecrã
            A, B = pg.evaluate("""(ids) => { const L = ids.map(i => S.areas.find(a => a.id === i)); let m = null;
              for (const x of L) for (const y of L) { const d = mapa.distance([x.latitude, x.longitude], [y.latitude, y.longitude]); if (x !== y && (!m || d > m[2])) m = [x.id, y.id, d]; }
              const a = L.find(z => z.id === m[0]), b = L.find(z => z.id === m[1]); mapa.fitBounds([[a.latitude, a.longitude], [b.latitude, b.longitude]], { padding: [90, 90], animate: false }); return [m[0], m[1]]; }""", ids)
            pg.wait_for_timeout(500); k = f"{papel}/{larg}"
            passo(f"1 {k} sem etiquetas por defeito", etiq(pg) == [] and not pg.is_visible("#b-etiq"))
            tocar(pg, A)
            passo(f"2 {k} 1.º toque mostra a etiqueta (ficha fechada)", etiq(pg) == [A] and not pg.is_visible("#folha") and pg.is_visible("#b-etiq"), str(etiq(pg)))
            tocar(pg, B)
            passo(f"3 {k} outra etiqueta sem fechar a primeira", sorted(etiq(pg)) == sorted([A, B]) and "(2)" in pg.inner_text("#b-etiq"), pg.inner_text("#b-etiq"))
            tocar(pg, A)
            passo(f"4 {k} 2.º toque abre a ficha", pg.is_visible("#folha") and pg.evaluate("S.fichaAberta") == A)
            pg.evaluate("fecharFolha()"); pg.wait_for_timeout(200)
            pg.evaluate(f"(() => {{ const a = S.areas.find(z => z.id === '{B}'); S.seguirCentro = false; S.euVisivel = false; mapa.setView([a.latitude, a.longitude], 18, {{ animate: false }}); }})()"); pg.wait_for_timeout(400)
            pg.locator(f".rot-campo[data-id='{B}']").click(); pg.wait_for_timeout(300)
            passo(f"5 {k} tocar na etiqueta fecha-a", etiq(pg) == [A] and not pg.is_visible("#folha"), str(etiq(pg)))
            tocar(pg, B); pg.click("#b-etiq"); pg.wait_for_timeout(300)
            passo(f"6 {k} «Esconder etiquetas» fecha todas", etiq(pg) == [] and not pg.is_visible("#b-etiq"))
    pg.set_viewport_size({"width": 390, "height": 844}); tocar(pg, A); pg.wait_for_timeout(200)
    pg.screenshot(path=f"/home/claude/rega-test/etiquetas_toque_{LG}.png")
    passo("7 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    print("RESULTADO:", "OK" if all(res.values()) and not erros else "FALHOU", f"({sum(res.values())}/{len(res)})")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
