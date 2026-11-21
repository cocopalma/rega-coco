# v253: Mapa › Ferramentas › «🩺 Só os campos com inventário»: sem inventários avisa; com um inventário o mapa mostra só esse
# campo, com a faixa «… (1) · Mostrar todos»; «Mostrar todos» repõe; o activista não tem o botão. Simulação. LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8888"').replace("localhost:8858", "localhost:8888"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
FOTO = "/home/claude/rega-test/foto_teste.jpg"
T = {"pt": ("Inventário de plantas mórbidas", "Só os campos com inventário", "Ainda não há campos"),
     "en": ("Inventory of weak plants", "Only fields with", "There are no fields"),
     "sw": ("Hesabu ya mimea dhaifu", "Mashamba yenye hesabu", "Bado hakuna mashamba")}[LG]
NC = "camada.getLayers().filter((l) => l instanceof L.CircleMarker).length"
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-21T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "tecnico"); pg.evaluate("fecharFolha(); mudar('mapa')"); pg.wait_for_timeout(1500)
    pg.click("#b-ferr"); pg.wait_for_timeout(200)
    passo("1 técnico: botão no menu Ferramentas", pg.is_visible("#b-morb"))
    pg.click("#b-morb"); pg.wait_for_timeout(600)
    passo("2 sem inventários: aviso e o mapa fica igual", T[2] in pg.inner_text("body") and not pg.evaluate("S.soMorb"))
    total = pg.evaluate(NC)
    a = pg.evaluate("(() => { const a = S.areas.find((x) => x.activista_id && meuCampo(x) && x.latitude != null); return { id: a.id, prod: a.produtor } })()")
    pg.evaluate(f"DEMO.irPara('{a['id']}')"); pg.wait_for_timeout(1500)
    pg.evaluate(f"abrirFicha('{a['id']}')"); pg.wait_for_timeout(800)
    pg.locator("#folha .fi-q", has_text=T[0]).click(); pg.wait_for_selector("#mb-gravar")
    pg.click("#mb-metodo .chip[data-v=X]"); pg.fill("#mb-n", "40"); pg.fill("#mb-m", "10")
    pg.set_input_files("#mb-fc", FOTO); pg.wait_for_timeout(1200); pg.set_input_files("#mb-fe", FOTO); pg.wait_for_timeout(1200)
    pg.click("#mb-gravar"); pg.wait_for_timeout(5000)
    pg.evaluate("fecharFolha(); mudar('mapa')"); pg.wait_for_timeout(1000)
    pg.click("#b-ferr"); pg.wait_for_timeout(200); pg.click("#b-morb"); pg.wait_for_timeout(1200)
    n = pg.evaluate(NC); ri = pg.inner_text("#ronda-info")
    passo("3 só o campo com inventário no mapa", pg.evaluate("S.soMorb") and n == 1 and total > 1, f"antes={total} agora={n}")
    passo("4 faixa com o número e «Mostrar todos»", T[1] in ri and "(1)" in ri, ri)
    passo("5 Ferramentas marcado", pg.evaluate("document.getElementById('b-ferr').classList.contains('on')"))
    pg.screenshot(path=f"/home/claude/rega-test/v253_a_{LG}.png")
    pg.locator("#ronda-info button").click(); pg.wait_for_timeout(800)
    passo("6 «Mostrar todos» repõe os campos", not pg.evaluate("S.soMorb") and pg.evaluate(NC) == total)
    demo(pg, "activista"); pg.evaluate("fecharFolha(); mudar('mapa')"); pg.wait_for_timeout(1000)
    passo("7 activista: sem o botão", pg.evaluate("document.getElementById('b-morb').style.display") == "none")
    passo("8 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
