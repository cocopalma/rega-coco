# v241: tuk-tuk em cada chegada da água (simulação; nada sai para o servidor). LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8876"').replace("localhost:8858", "localhost:8876"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
DBX = lambda pg, e: pg.evaluate("(() => { const D = JSON.parse(sessionStorage.getItem('rega.demo.db')); return " + e + " })()")
FOTOS = "(async()=>{ for (const t of %s) await guardarFotoRega(t, new Blob(['x'],{type:'image/jpeg'})); abrirFicha(LS.get('emCurso').area_id)})()"
T = {"pt": ("Que tuk-tuk trouxe", "água nova"), "en": ("Which tuk-tuk brought", "new water"), "sw": ("Tuk-tuk gani ilileta", "maji mapya")}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-16T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "activista")
    if pg.is_visible("#folha.on") and pg.locator("#j-lista").count():
        for c in pg.locator("#j-lista input").all(): c.check()
        pg.click("#folha-c .btn >> nth=-1"); pg.wait_for_timeout(500)
    passo("1 lista de tuk-tuks no telefone", pg.evaluate("(S.tuks||[]).length") == 8, str(pg.evaluate("S.tuks")))
    ficha(pg, 'PR900101-1'); pg.click("button[onclick^=marcarEntrada]"); pg.wait_for_selector("text=/Entrada marcada|Entry recorded|Kuingia kumewekwa/", timeout=30000)
    pg.evaluate(FOTOS % "['entrada']"); pg.wait_for_timeout(500)
    pg.click("button[onclick='pedirTuk(false)']"); pg.wait_for_timeout(400)
    passo("2 «Chegou a água» pede o tuk-tuk (lista)", pg.is_visible("#tk-cod") and T[0] in pg.inner_text("#folha-c"), pg.inner_text("#folha-c")[:120].replace("\n", " | "))
    dial.clear(); pg.click("button[onclick='confirmarTuk(false)']"); pg.wait_for_timeout(300)
    passo("3 sem escolher não avança", len(dial) == 1 and not pg.evaluate("!!LS.get('emCurso').agua_em"), str(dial))
    pg.select_option("#tk-cod", "12"); pg.wait_for_timeout(200)
    passo("4 1.ª chegada do dia: não pergunta pela água nem pede texto", pg.evaluate("$('#tk-mesmo').hidden") and not pg.is_visible("#tk-out"))
    pg.click("button[onclick='confirmarTuk(false)']"); pg.wait_for_timeout(500)
    e = pg.evaluate("LS.get('emCurso')")
    passo("5 água marcada com o tuk-tuk 12 (viagem nova)", e.get("agua_em") and e.get("tuk") == {"codigo": "12", "outro": None, "chegada": "nova"} and "12" in pg.inner_text("#folha-c"), str(e.get("tuk")))
    pg.evaluate(FOTOS % "['rega','saida']"); pg.wait_for_timeout(500)
    pg.click("button[onclick='ecraSaida()']"); pg.fill("#s-plantas", str(pg.evaluate("plantasN(S.areas.find(a=>a.id==='PR900101-1'))"))); pg.click("button[onclick='marcarSaida()']"); pg.wait_for_timeout(4000)
    r = DBX(pg, "D.registos.filter(r=>!r.teste && r.area_id==='PR900101-1').map(r=>[r.tuk_codigo,r.tuk_outro,r.tuk_chegada])")
    passo("6 a rega chega ao servidor com o tuk-tuk", r == [["12", None, "nova"]], str(r))
    # 2.º campo, mesmo tuk-tuk: a app pergunta se é água nova
    pg.evaluate("fecharFolha(); DEMO.irPara('PR900103-1')"); pg.wait_for_timeout(3500)
    pg.evaluate("marcarEntrada('PR900103-1', 'teste', 'teste')"); pg.wait_for_timeout(4000)
    ok = pg.evaluate("LS.get('emCurso')?.area_id") == 'PR900103-1'
    if not ok: print("   entrada 2:", pg.inner_text("#folha-c")[:200].replace("\n", " | "))
    pg.evaluate(FOTOS % "['entrada']"); pg.wait_for_timeout(400)
    pg.evaluate("pedirTuk(true)"); pg.wait_for_timeout(300); pg.select_option("#tk-cod", "12")
    passo("7 «a água já estava»: não pergunta e não é viagem", ok and pg.evaluate("$('#tk-mesmo').hidden") and pg.evaluate("lerTuk()") == {"codigo": "12", "outro": None, "chegada": "ja_estava"})
    pg.evaluate("pedirTuk(false)"); pg.wait_for_timeout(300)
    passo("8 os usados pela equipa aparecem primeiro", pg.evaluate("$('#tk-cod optgroup option')?.value") == "12")
    pg.select_option("#tk-cod", "?"); pg.wait_for_timeout(200); dial.clear(); pg.click("button[onclick='confirmarTuk(false)']")
    passo("9 «não sei o código» pede texto", pg.is_visible("#tk-out") and len(dial) == 1)
    pg.select_option("#tk-cod", "12"); pg.wait_for_timeout(200)
    passo("10 mesmo tuk-tuk do campo anterior: pergunta pela água", pg.is_visible("#tk-mesmo") and T[1] in pg.inner_text("#tk-mesmo"), pg.inner_text("#tk-mesmo").replace("\n", " | "))
    dial.clear(); pg.click("button[onclick='confirmarTuk(false)']"); pg.wait_for_timeout(200)
    passo("11 sem responder não avança", len(dial) == 1 and not pg.evaluate("!!LS.get('emCurso').agua_em"))
    pg.click("#tk-mesmo .chip[data-v=mesmo_tanque]"); pg.click("button[onclick='confirmarTuk(false)']"); pg.wait_for_timeout(500)
    passo("12 a mesma água: fica mesmo_tanque", pg.evaluate("LS.get('emCurso').tuk.chegada") == "mesmo_tanque")
    pg.evaluate(FOTOS % "['rega','saida']"); pg.wait_for_timeout(500)
    pg.click("button[onclick='ecraSaida()']"); pg.fill("#s-plantas", str(pg.evaluate("plantasN(S.areas.find(a=>a.id==='PR900103-1'))"))); pg.click("button[onclick='marcarSaida()']"); pg.wait_for_timeout(4000)
    r = DBX(pg, "D.registos.filter(r=>!r.teste && r.tuk_chegada).map(r=>[r.area_id,r.tuk_codigo,r.tuk_chegada])")
    passo("13 duas regas, uma só viagem", r == [["PR900101-1", "12", "nova"], ["PR900103-1", "12", "mesmo_tanque"]], str(r))
    pg.screenshot(path=f"/home/claude/rega-test/v241_a_{LG}.png")
    # técnico: vê e corrige
    demo(pg, "tecnico"); ficha(pg, 'PR900103-1'); pg.wait_for_timeout(1500)
    tx = pg.inner_text("#f-regas") if pg.locator("#f-regas").count() else ""
    passo("14 ficha: água e tuk-tuk em «Regas deste campo»", "12" in tx and pg.locator("#f-regas button[onclick^=ecraCorrigirTuk]").count() == 1, tx[:200].replace("\n", " | "))
    pg.click("#f-regas button[onclick^=ecraCorrigirTuk]"); pg.wait_for_timeout(300)
    pg.select_option("#ct-cod", "VGB1"); pg.select_option("#ct-cheg", "nova"); pg.fill("#ct-mot", "Era outro tuk-tuk"); pg.click("button[onclick^=gravarCorrecaoTuk]"); pg.wait_for_timeout(2500)
    r = DBX(pg, "D.registos.filter(r=>r.area_id==='PR900103-1' && !r.teste).map(r=>[r.tuk_codigo,r.tuk_chegada,!!r.tuk_corrigido_em])")
    passo("15 técnico corrige o tuk-tuk", r == [["VGB1", "nova", True]], str(r))
    demo(pg, "activista"); ficha(pg, 'PR900103-1'); pg.wait_for_timeout(1500)
    passo("16 activista não corrige", pg.locator("#f-regas button[onclick^=ecraCorrigirTuk]").count() == 0 and "VGB1" in pg.inner_text("#f-regas"))
    # painel
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(7000)
    fr = pg.frame_locator("#e-painel iframe")
    k = fr.locator("#k-tuk").inner_text(timeout=15000).replace("\n", " | "); td = fr.locator("#t-tuk-dia").inner_text().replace("\n", " | ")
    passo("17 painel: 2 viagens, 2 tuk-tuks", fr.locator("#s-tuk").is_visible() and fr.locator("#k-tuk .val").first.inner_text() == "2" and "VGB1" in td and "12" in td, k[:160] + " || " + td[:200])
    fr.locator("#s-tuk").screenshot(path=f"/home/claude/rega-test/v241_p_{LG}.png")
    passo("18 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']} {PEDIDOS['urls'][:3]}")
    print("RESULTADO:", "OK" if all(res.values()) and not erros else "FALHOU"); print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
