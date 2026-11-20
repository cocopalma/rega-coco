# v248: sobrevivência indicativa (concluir a cava-roda e o mulching, recontagem automática) e motivo dos campos do itinerário que
# ficaram por regar (passam para o dia seguinte do plano). Simulação. LING=en / sw.
import os, sys, json
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8882"').replace("localhost:8858", "localhost:8882"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
T = {"pt": ("Fim do dia do itinerário", "do dia anterior", "Sobrevivência indicativa", "Concluir o campo"),
     "en": ("End of the itinerary day", "from the previous day", "Indicative survival", "Complete the field"),
     "sw": ("Mwisho wa siku ya ratiba", "kutoka siku iliyopita", "Uhai wa kukadiria", "Kamilisha shamba")}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-20T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    # ===== Parte 3: itinerário =====
    demo(pg, "activista")
    if pg.is_visible("#folha.on") and pg.locator("#j-lista").count():
        for c in pg.locator("#j-lista input").all(): c.check()
        pg.click("#folha-c .btn >> nth=-1"); pg.wait_for_timeout(500)
    pg.evaluate("fecharFolha()")
    ids = pg.evaluate("(() => { const ri = rondaInfo(S.perfil.activista_id); return S.areas.filter((a) => a.activista_id === S.perfil.activista_id && !ri.feitas.has(a.id)).map((a) => a.id) })()")
    passo("0 activista com 3+ campos por regar", len(ids) >= 3, str(ids))
    plano = {"id": "pl-teste", "activista_id": None, "estado": "aprovado", "ronda": None,
             "dias": [{"n": 1, "campos": [{"area_id": ids[0]}, {"area_id": ids[1]}]}, {"n": 2, "campos": [{"area_id": ids[2]}]}]}
    pg.evaluate(f"(() => {{ const p = {json.dumps(plano)}; p.activista_id = S.perfil.activista_id; p.ronda = rondaInfo(S.perfil.activista_id).n; LS.set('planos', [p]); LS.set('itTrab', {{ 'pl-teste': {{ 1: hojeISO() }} }}); }})()")
    it = pg.evaluate("(() => { const i = itinerarioHoje(); return i && { dia: i.dia.n, campos: i.campos } })()")
    passo("1 itinerário: dia 1 com 2 campos", it and it["dia"] == 1 and len(it["campos"]) == 2, str(it))
    h = pg.evaluate("(() => { window.__HORA_TESTE = '12:00'; const h = cartaoItinerario(); return h })()")
    passo("2 antes das 15:30 sem o botão do fim do dia", "b-fim-it" not in h)
    h = pg.evaluate("(() => { window.__HORA_TESTE = '16:00'; return cartaoItinerario() })()")
    passo("3 depois das 15:30, com regas hoje no dia do plano: botão do fim do dia", "b-fim-it" in h)
    pg.evaluate("ecraFechoItinerario()"); pg.wait_for_selector("#fi-ok")
    pg.wait_for_timeout(600)
    passo("4 traduzido: título do fim do dia", T[0] in pg.inner_text("#folha"))
    pg.click("#fi-ok"); pg.wait_for_timeout(200)
    passo("5 sem motivo não grava", pg.locator("#fi-msg .erro").count() == 1 and not pg.evaluate("(LS.get('filaAlt',[])||[]).some(x=>x.tipo==='it_fecho')"))
    pg.click("#fi-todos .chip[data-k=material]"); pg.wait_for_timeout(200)
    passo("6 «Faltou material» para todos: pede que material", pg.locator(".fi-txt:visible").count() == 2)
    pg.click("#fi-ok"); pg.wait_for_timeout(200)
    passo("7 sem dizer o material não grava", pg.locator("#fi-msg .erro").count() == 1)
    for el in pg.locator(".fi-txt").all(): el.fill("Faltaram regadores")
    pg.click(f".fi-campo[data-a='{ids[1]}'] .chip[data-k=produtor]"); pg.wait_for_timeout(200)
    pg.click("#fi-ok"); pg.wait_for_timeout(300)
    pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(3000)
    q = DB(pg, "JSON.stringify([D.itF||[], D.itX||[]])")
    passo("8 enviado com um motivo por campo", '"motivo":"material"' in q and '"texto":"Faltaram regadores"' in q and '"motivo":"produtor"' in q and '"dia_n":1' in q, q[:260])
    passo("9 saiu da fila", not pg.evaluate("(LS.get('filaAlt',[])||[]).some(x=>x.tipo==='it_fecho')"))
    # a sincronização volta a ler os planos do servidor de exemplo (sem planos): repor o plano e ler o estado do itinerário
    pg.evaluate(f"(async () => {{ const p = {json.dumps(plano)}; p.activista_id = S.perfil.activista_id; p.ronda = rondaInfo(S.perfil.activista_id).n; LS.set('planos', [p]); await carregarItEstado(); }})()"); pg.wait_for_timeout(1500)
    it = pg.evaluate("(() => { const i = itinerarioHoje(); return i && { dia: i.dia.n, campos: i.campos, atr: [...i.atrasados] } })()")
    passo("10 os 2 campos passam para o dia 2 (3 campos, 2 do dia anterior)", it and it["dia"] == 2 and len(it["campos"]) == 3 and len(it["atr"]) == 2, str(it))
    pg.evaluate("mudar('hoje')"); pg.wait_for_timeout(1200)
    passo("11 Hoje: «do dia anterior» nos campos que passaram", T[1] in pg.inner_text("#hoje-itin"))
    # dia 2 com regas ontem e não fechado: motivo obrigatório ao abrir
    pg.evaluate("(() => { const d = new Date(Date.now() - 864e5).toISOString().slice(0, 10); LS.set('itTrab', { 'pl-teste': { 1: hojeISO(), 2: d } }); fecharFolha(); avisoItPend(true); })()"); pg.wait_for_timeout(500)
    passo("12 dia anterior por fechar: ecrã obrigatório sem ✕", pg.is_visible("#fi-ok") and not pg.is_visible("#folha-x"))
    pg.screenshot(path=f"/home/claude/rega-test/v248_a_{LG}.png")
    pg.evaluate("$('#folha-x').style.display=''; fecharFolha(); window.__HORA_TESTE = null; LS.set('planos', []); LS.del('itTrab')")
    passo("13 o activista não vê «Concluir»", not pg.evaluate("souConclui()"))
    # ===== Parte 2: sobrevivência indicativa =====
    demo(pg, "tecnico"); pg.evaluate("fecharFolha()")
    a = pg.evaluate("(() => { const a = S.areas.filter((x) => meuCampo(x) && x.activista_id && x.instaladas > 0 && x.vivas > 10).sort((x, y) => y.vivas - x.vivas)[0]; return a && { id: a.id, act: a.activista_id, inst: a.instaladas, viv: a.vivas } })()")
    passo("14 técnico com um campo da lista com plantas", bool(a), str(a))
    cav = max(1, a["viv"] - 5)
    pg.evaluate(f"sb.rpc('gravar_actividade', {{ p: {{ id: crypto.randomUUID(), area_id: '{a['id']}', activista_id: '{a['act']}', motivo: 'tuk_tuk', entrada_em: new Date().toISOString(), saida_em: new Date().toISOString(), cavaroda: {cav}, mulching: {cav}, pessoas: 3 }} }})"); pg.wait_for_timeout(500)
    ficha(pg, a["id"]); pg.wait_for_timeout(2500)
    passo("15 ficha: botão «Concluir o campo»", pg.is_visible("#b-concluir") and T[3] in pg.inner_text("#b-concluir"))
    pg.click("#b-concluir"); pg.wait_for_selector("#cc-ok"); pg.wait_for_timeout(500)
    t = pg.inner_text("#folha")
    pct = str(round(1000 * min(cav, a["inst"]) / a["inst"]) / 10).replace(".", ",")
    passo("16 mostra a sobrevivência indicativa (cava-roda ÷ instaladas) e o aviso da recontagem", T[2] in t and (pct in t or pct.replace(",", ".") in t) and "M&E" in t, pct + " | " + t[:160].replace("\n", " | "))
    pg.screenshot(path=f"/home/claude/rega-test/v248_b_{LG}.png")
    pg.click("#cc-ok"); pg.wait_for_timeout(500); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(3000)
    rc = DB(pg, f"(D.recontagens||[]).filter(r=>r.area_id==='{a['id']}' && /pedido automático/.test(r.motivo)).length")
    passo("17 recontagem automática pedida ao M&E (cava-roda < vivas da base)", rc == 1, str(rc))
    viv2 = DB(pg, f"(D.areas.find(x=>x.id==='{a['id']}')||{{}}).vivas")
    passo("18 as vivas da base não mudaram", viv2 == a["viv"], str(viv2))
    ficha(pg, a["id"]); pg.wait_for_timeout(2500)
    t = pg.inner_text("#f-conc") if pg.locator("#f-conc").count() else ""
    passo("19 ficha: sobrevivência indicativa e «Anular a conclusão»", T[2] in t and pg.locator("#f-conc button").count() == 1, t[:200].replace("\n", " | "))
    # anular por engano: a recontagem por encaminhar é cancelada
    pg.click("#f-conc button"); pg.wait_for_selector("#ac-ok"); pg.click("#ac-ok"); pg.wait_for_timeout(300)
    passo("20 anular sem motivo não anula", pg.locator("#ac-msg .erro").count() == 1)
    pg.fill("#ac-mot", "Ainda há plantas por fazer"); pg.click("#ac-ok"); pg.wait_for_timeout(1500)
    est = DB(pg, f"[(D.conc||[]).filter(k=>k.area_id==='{a['id']}' && !k.removido).length, (D.recontagens||[]).filter(r=>r.area_id==='{a['id']}' && /pedido automático/.test(r.motivo)).map(r=>r.estado).join()]")
    passo("21 anulada: conclusão removida e recontagem cancelada", est[0] == 0 and est[1] == "cancelada", str(est))
    # concluir de novo para o painel
    pg.wait_for_timeout(1500)
    if pg.locator("#b-concluir").count():
        pg.click("#b-concluir"); pg.wait_for_selector("#cc-ok"); pg.click("#cc-ok"); pg.wait_for_timeout(500); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    # painel (director)
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(8000)
    fr = pg.frame("painel") or [x for x in pg.frames if "painel.html" in x.url][0]
    vis = fr.evaluate("!document.getElementById('s-sob').hidden")
    tx = fr.inner_text("#s-sob") if vis else ""
    passo("22 painel: secção da sobrevivência indicativa com o campo", vis and a["id"] in tx and T[2] in tx, tx[:240].replace("\n", " | "))
    fr.evaluate("document.getElementById('s-sob').scrollIntoView()"); pg.wait_for_timeout(300)
    pg.screenshot(path=f"/home/claude/rega-test/v248_c_{LG}.png")
    passo("23 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']} {PEDIDOS['urls'][:3]}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
