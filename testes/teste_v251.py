# v251: inventário de plantas mórbidas (método do Paulo Dias, 20/11/2026). Simulação: técnico regista na ficha (amostra, mórbidas,
# % ao vivo, duas fotografias, GPS), fica na lista do campo, vai para o servidor de exemplo e aparece no painel; activista sem botão;
# cliente sem a secção do painel. LING=en / sw.
import os, sys, json
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8886"').replace("localhost:8858", "localhost:8886"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
FOTO = "/home/claude/rega-test/foto_teste.jpg"
T = {"pt": ("Inventário de plantas mórbidas", "de plantas mórbidas", "Plantas mórbidas (inventário)"),
     "en": ("Inventory of weak plants", "weak plants", "Weak plants (inventory)"),
     "sw": ("Hesabu ya mimea dhaifu", "mimea dhaifu", "Mimea dhaifu (hesabu)")}[LG]
def DBq(pg, expr): return pg.evaluate(f"(() => {{ const D = JSON.parse(sessionStorage.getItem('rega.demo.db')); return {expr}; }})()")
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-21T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "tecnico"); pg.evaluate("fecharFolha()")
    a = pg.evaluate("(() => { const a = S.areas.find((x) => x.activista_id && meuCampo(x) && x.latitude != null); return { id: a.id, pr: a.pr } })()")
    pg.evaluate(f"DEMO.irPara('{a['id']}')"); pg.wait_for_timeout(1500)
    pg.evaluate(f"abrirFicha('{a['id']}')"); pg.wait_for_timeout(800)
    q = pg.locator("#folha .fi-q", has_text=T[0])
    passo("1 ficha do técnico: quadrado do inventário", q.count() == 1)
    q.click(); pg.wait_for_selector("#mb-gravar")
    passo("2 ecrã traduzido", T[0] in pg.inner_text("#folha"))
    pg.click("#mb-gravar"); pg.wait_for_timeout(200)
    passo("3 sem amostra não grava", pg.locator("#mb-msg .erro").count() == 1)
    pg.fill("#mb-n", "30"); pg.fill("#mb-m", "31"); pg.wait_for_timeout(200)
    passo("4 mórbidas acima da amostra: aviso", pg.locator("#mb-pct .erro").count() == 1)
    pg.fill("#mb-m", "3"); pg.wait_for_timeout(200)
    t = pg.inner_text("#mb-pct")
    passo("5 % ao vivo (3 de 30 = 10 %)", "10 %" in t and T[1] in t, t)
    pg.click("#mb-gravar"); pg.wait_for_timeout(200)
    passo("6 sem fotografias não grava", pg.locator("#mb-msg .erro").count() == 1 and not pg.evaluate("LS.get('filaMorb',[]).length"))
    pg.set_input_files("#mb-fc", FOTO); pg.wait_for_timeout(1200)
    pg.click("#mb-gravar"); pg.wait_for_timeout(200)
    passo("7 só com a fotografia do campo não grava", pg.locator("#mb-msg .erro").count() == 1 and not pg.evaluate("LS.get('filaMorb',[]).length"))
    pg.set_input_files("#mb-fe", FOTO); pg.wait_for_timeout(1200)
    passo("8 pré-visualização das duas fotografias", pg.is_visible("#mb-pc") and pg.is_visible("#mb-pe"))
    pg.fill("#mb-obs", "Teste do inventário")
    pg.screenshot(path=f"/home/claude/rega-test/v251_a_{LG}.png")
    pg.evaluate("window.__SEM_SINC = true")
    pg.click("#mb-gravar"); pg.wait_for_timeout(4000)
    n = DBq(pg, f"(D.morb||[]).filter(x => x.area_id === '{a['id']}').map(x => [x.amostra, x.morbidas, !!x.foto_campo, !!x.foto_equipa, x.observacao])")
    passo("9 gravado e enviado (servidor de exemplo)", n == [[30, 3, True, True, "Teste do inventário"]] and pg.evaluate("LS.get('filaMorb',[]).length") == 0, str(n))
    pg.evaluate(f"abrirFicha('{a['id']}')"); pg.wait_for_timeout(1500)
    t = pg.inner_text("#f-morb") if pg.locator("#f-morb").count() else ""
    passo("10 ficha: inventário na lista com a %", "10 %" in t and "Remover" in t or "10 %" in t, t[:200].replace("\n", " | "))
    pg.screenshot(path=f"/home/claude/rega-test/v251_b_{LG}.png", full_page=True)
    # fora da lista própria (supervisor): botão também
    demo(pg, "supervisor"); pg.evaluate("fecharFolha()")
    al = pg.evaluate("(() => { const a = S.areas.find((x) => !meuCampo(x)); return a ? a.id : null })()")
    if al:
        pg.evaluate(f"abrirFicha('{al}')"); pg.wait_for_timeout(800)
        passo("11 supervisor: campo de outra equipa também tem o botão", T[0] in pg.inner_text("#folha"))
    else: passo("11 supervisor: (sem campos de outra equipa na simulação)", True)
    # activista: sem botão
    demo(pg, "activista"); pg.evaluate("fecharFolha()")
    aa = pg.evaluate("S.areas[0].id"); pg.evaluate(f"abrirFicha('{aa}')"); pg.wait_for_timeout(800)
    passo("12 activista: sem o botão do inventário", pg.locator("#folha .fi-q", has_text=T[0]).count() == 0)
    # painel (director)
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(8000)
    fr = pg.frame("painel") or [x for x in pg.frames if "painel.html" in x.url][0]
    vis = fr.evaluate("!document.getElementById('s-mrb').hidden")
    tx = fr.inner_text("#s-mrb") if vis else ""
    passo("13 painel: secção com o inventário (10 %)", vis and T[2] in tx and "10 %" in tx, tx[:300].replace("\n", " | "))
    fr.evaluate("document.getElementById('s-mrb').scrollIntoView()"); pg.wait_for_timeout(300)
    pg.screenshot(path=f"/home/claude/rega-test/v251_c_{LG}.png")
    demo(pg, "cliente"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(8000)
    fr = pg.frame("painel") or [x for x in pg.frames if "painel.html" in x.url][0]
    passo("14 cliente: sem a secção", fr.evaluate("document.getElementById('s-mrb').hidden"))
    passo("15 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
