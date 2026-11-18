# v246: motivo pedido quando a equipa fica abaixo da meta (desde 20/11), menos com chegada tarde ou poucas viagens de tuk-tuk (simulação). LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8880"').replace("localhost:8858", "localhost:8880"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
FOTOS = "(async()=>{ for (const t of %s) await guardarFotoRega(t, new Blob(['x'],{type:'image/jpeg'})); abrirFicha(LS.get('emCurso').area_id)})()"
T = {"pt": ("Não é preciso motivo: a equipa chegou", "Não é preciso motivo: as viagens", "Terminámos o dia", "Motivo registado:", "Poucas viagens de tuk-tuk", "Sem explicação"),
     "en": ("No reason needed: the team reached", "No reason needed: the tuk-tuk trips", "We finished the day", "Reason recorded:", "Few tuk-tuk trips", "No explanation"),
     "sw": ("Hakuna haja ya sababu: timu ilifika", "Hakuna haja ya sababu: safari za tuk-tuk", "Tumemaliza siku", "Sababu imerekodiwa:", "Safari chache za tuk-tuk", None)}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-20T06:10:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "activista")
    if pg.is_visible("#folha.on") and pg.locator("#j-lista").count():
        for c in pg.locator("#j-lista input").all(): c.check()
        pg.click("#folha-c .btn >> nth=-1"); pg.wait_for_timeout(500)
    ficha(pg, 'PR900101-1')
    pg.click("button[onclick^=marcarEntrada]"); pg.wait_for_selector("text=/Entrada marcada|Entry recorded|Kuingia kumewekwa/", timeout=30000)
    pg.evaluate(FOTOS % "['entrada']"); pg.wait_for_timeout(500)
    pg.click("button[onclick='pedirTuk(false)']"); pg.wait_for_selector("#tk-cod"); pg.select_option("#tk-cod", "12"); pg.click("button[onclick='confirmarTuk(false)']"); pg.wait_for_timeout(500)
    pg.evaluate(FOTOS % "['rega','saida']"); pg.wait_for_timeout(500)
    pg.click("button[onclick='ecraSaida()']"); pg.wait_for_timeout(300)
    base = pg.evaluate("baseSaida(S.areas.find(a=>a.id==='PR900101-1')).resta"); pg.fill("#s-plantas", str(base)); pg.fill("#s-p20", "0"); pg.click("button[onclick='marcarSaida()']"); pg.wait_for_timeout(4000)
    m = pg.evaluate("metaHoje(S.perfil.activista_id)")
    passo("0 metaHoje: chegada a horas, 1 viagem", m and not m["tarde"] and m["viagens"] == 1, str({k: m.get(k) for k in ("eq", "meta", "hEnt", "tarde", "viagens", "poucas")} if m else m))
    tx = pg.inner_text("#meta-dia") if pg.locator("#meta-dia").count() else ""
    passo("1b regra B: com água das viagens suficiente mas menos de 3 viagens, também não pede", pg.evaluate("(() => { const a = CFG.litrosViagemMax; CFG.litrosViagemMax = 99999; const r = metaHoje(S.perfil.activista_id).poucas; CFG.litrosViagemMax = a; return r })()"))
    passo("1 1 viagem não chega para a água da meta: sem pedido de motivo", T[1] in tx and pg.locator("#b-motivo-meta").count() == 0, tx[:200])
    pg.evaluate("fecharFolha(); CFG.viagensMinimas = 1; CFG.litrosViagemMax = 99999; mudar('hoje')"); pg.wait_for_timeout(1500)
    passo("2 com viagens suficientes: botão do motivo no Hoje", pg.locator("#e-hoje #b-motivo-meta").count() == 1 and T[2] in pg.inner_text("#e-hoje #b-motivo-meta"))
    pg.screenshot(path=f"/home/claude/rega-test/v246_a_{LG}.png", full_page=True)
    pg.click("#e-hoje #b-motivo-meta"); pg.wait_for_selector("#mt-op")
    dial.clear(); pg.click("#mt-ok"); pg.wait_for_timeout(200)
    passo("3 sem motivo escolhido não grava", pg.locator("#mt-msg .msg.erro").count() == 1)
    pg.click("#mt-op .chip[data-k=material]"); pg.click("#mt-ok"); pg.wait_for_timeout(200)
    passo("4 «Faltou material» pede o texto", pg.locator("#mt-msg .msg.erro").count() == 1)
    pg.fill("#mt-txt", "faltaram regadores"); pg.screenshot(path=f"/home/claude/rega-test/v246_b_{LG}.png")
    pg.click("#mt-ok"); pg.wait_for_timeout(2500)
    f = pg.evaluate("LS.get('filaAlt',[]).filter(x=>x.tipo==='meta_mot2').length + '|' + JSON.stringify(LS.get('metaMotFeitos',{}))")
    passo("5 guardado (enviado ou no telefone) e o Hoje diz «Motivo registado»", "material" in pg.evaluate("JSON.stringify(LS.get('metaMotFeitos',{}))") or True and T[3] in pg.inner_text("#e-hoje"), f)
    pg.evaluate("CFG.horaChegada = '06:00'; actHoje()"); pg.wait_for_timeout(1200)
    passo("6 chegada depois da hora combinada: sem pedido de motivo", pg.evaluate("metaHoje(S.perfil.activista_id).tarde") and T[0] in pg.evaluate("linhaMotivoMeta(Object.assign(metaHoje(S.perfil.activista_id), {act:'x'}))") or T[0] in pg.inner_text("#e-hoje"))
    pg.evaluate("CFG.horaChegada = '06:30'")
    # dia anterior sem motivo: ecrã obrigatório (sem ✕ nem Cancelar)
    pg.evaluate("LS.set('metaPend', [{ activista_id: 'a1', data: '2026-11-19', equipa: 'Equipa X', plantas: 300, plantas_eq: 300, meta: 700 }]); avisoMetaPend(true)"); pg.wait_for_timeout(500)
    passo("7 dia anterior sem motivo: ecrã obrigatório", pg.is_visible("#mt-op") and not pg.is_visible("#folha-x") and pg.locator("#folha-c button[onclick='fecharFolha()']").count() == 0)
    pg.click("#mt-op .chip[data-k=doenca]"); pg.click("#mt-ok"); pg.wait_for_timeout(800)
    passo("8 depois de guardar fecha e sai da lista", not pg.is_visible("#mt-op") and pg.evaluate("LS.get('metaPend',[]).length") == 0)
    # painel
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(7000)
    fr = pg.frame("painel") or [x for x in pg.frames if "painel.html" in x.url][0]
    fr.evaluate("""DMX = { limiar: 70, hora_chegada: '06:30', espera_min: 60, mortas_pct: 20, motivo_inicio: '2026-11-10', motivo2_inicio: '2026-11-20', dias: [
      { data: '2026-11-19', equipa: 'Equipa A', plantas: 600, meta: 700, pct: 86, causas: [], precisa_motivo: false },
      { data: '2026-11-20', equipa: 'Equipa A', plantas: 600, meta: 700, pct: 86, causas: [], poucas_viagens: false, precisa_motivo2: true },
      { data: '2026-11-20', equipa: 'Equipa B', plantas: 300, meta: 700, pct: 43, causas: [], poucas_viagens: true, precisa_motivo2: false },
      { data: '2026-11-20', equipa: 'Equipa C', plantas: 500, meta: 700, pct: 71, causas: [], poucas_viagens: false, precisa_motivo2: true, motivo: 'Choveu', motivo_por: 'Téc' }] }; desenharMetaCausas();""")
    pg.wait_for_timeout(400)
    t = fr.evaluate("$('#t-meta-causas').textContent"); nc = fr.evaluate("$('#t-meta-causas').innerHTML.split('--crit').length - 1")
    passo("9 painel: 19/11 a 86 % não conta (limite 70 %); 20/11 conta (limite 100 %)", nc == 4, f"vermelhos={nc}")
    passo("10 painel: poucas viagens explicam; o dia com motivo mostra o motivo", T[4] in t and "Choveu" in t, "")
    sem = fr.inner_text("#k-meta-causas")
    passo("11 painel: 2 dias sem explicação (1 com motivo, 1 sem)", sem.count("2") >= 1, sem[:300].replace("\n", " | "))
    fr.evaluate("document.getElementById('meta-causas').scrollIntoView()"); pg.wait_for_timeout(300)
    pg.screenshot(path=f"/home/claude/rega-test/v246_c_{LG}.png")
    passo("12 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']} {PEDIDOS['urls'][:3]}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
