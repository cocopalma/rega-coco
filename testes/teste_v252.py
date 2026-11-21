# v252: campos com inventário de plantas mórbidas — filtro e etiqueta na lista, 🩺 no mapa, colunas vivas/instaladas no painel e
# tocar no produtor da tabela do painel abre a ficha do campo. Simulação (0 pedidos ao servidor). LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8887"').replace("localhost:8858", "localhost:8887"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
FOTO = "/home/claude/rega-test/foto_teste.jpg"
T = {"pt": ("Inventário de plantas mórbidas", "mórbidas", "Plantas vivas no campo", "Plantas instaladas"),
     "en": ("Inventory of weak plants", "weak", "Live plants in the field", "Plants installed"),
     "sw": ("Hesabu ya mimea dhaifu", "dhaifu", "Mimea hai shambani", None)}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-21T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "tecnico"); pg.evaluate("fecharFolha()")
    a = pg.evaluate("(() => { const a = S.areas.find((x) => x.activista_id && meuCampo(x) && x.latitude != null); return { id: a.id, prod: a.produtor } })()")
    pg.evaluate(f"DEMO.irPara('{a['id']}')"); pg.wait_for_timeout(1500)
    pg.evaluate(f"abrirFicha('{a['id']}')"); pg.wait_for_timeout(800)
    pg.locator("#folha .fi-q", has_text=T[0]).click(); pg.wait_for_selector("#mb-gravar")
    pg.click("#mb-metodo .chip[data-v=X]"); pg.fill("#mb-n", "40"); pg.fill("#mb-m", "10")
    pg.set_input_files("#mb-fc", FOTO); pg.wait_for_timeout(1200); pg.set_input_files("#mb-fe", FOTO); pg.wait_for_timeout(1200)
    pg.click("#mb-gravar"); pg.wait_for_timeout(5000)
    passo("1 inventário enviado e contado por campo", pg.evaluate(f"(S.nMorb||{{}})['{a['id']}']?.n") == 1, str(pg.evaluate("S.nMorb")))
    pg.evaluate("fecharFolha(); mudar('lista')"); pg.wait_for_timeout(500)
    passo("2 opção do filtro visível ao técnico", not pg.evaluate("document.querySelector('#f-sit option[value=morb]').hidden"))
    pg.evaluate("document.getElementById('f-sit').value = 'morb'; desenharLista()"); pg.wait_for_timeout(500)
    t = pg.inner_text("#lista") if pg.locator("#lista").count() else pg.inner_text("#e-lista")
    n = pg.evaluate("document.querySelectorAll('#e-lista .item, #lista .item').length")
    passo("3 filtro: só o campo com inventário", a["prod"] in t and "25 %" in t and T[1] in t, f"n={n} " + t[:200].replace("\n", " | "))
    pg.screenshot(path=f"/home/claude/rega-test/v252_a_{LG}.png")
    pg.evaluate("document.getElementById('f-sit').value = ''; desenharLista(); mudar('mapa')"); pg.wait_for_timeout(1500)
    passo("4 mapa: 🩺 no campo", pg.evaluate("[...document.querySelectorAll('#mapa .ic-fogo')].filter((x) => x.textContent.includes('🩺')).length") == 1)
    pg.screenshot(path=f"/home/claude/rega-test/v252_b_{LG}.png")
    # painel do director: colunas e tocar no produtor abre a ficha
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(8000)
    fr = pg.frame("painel") or [x for x in pg.frames if "painel.html" in x.url][0]
    tx = fr.inner_text("#t-mrb")
    passo("5 painel: colunas vivas e instaladas", T[2] in tx and (T[3] is None or T[3] in tx), tx[:200].replace("\n", " | "))
    fr.locator("#t-mrb a", has_text=a["prod"]).first.click(); pg.wait_for_timeout(1500)
    passo("6 tocar no produtor abre a ficha do campo", pg.evaluate("S.fichaAberta") == a["id"] and pg.is_visible("#folha") and a["prod"] in pg.inner_text("#folha"))
    pg.screenshot(path=f"/home/claude/rega-test/v252_c_{LG}.png")
    demo(pg, "activista"); pg.evaluate("fecharFolha()")
    passo("7 activista: sem a opção do filtro", pg.evaluate("document.querySelector('#f-sit option[value=morb]').hidden"))
    passo("8 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
