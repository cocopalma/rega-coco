# v247: sem rega, cava-roda e mulching logo a seguir (ou o motivo para não fazer); alertas das 08:00 e 10:00; início do dia sozinho
# já não chega para fechar o dia depois das 15:30 (simulação). LING=en / sw.
import os, sys, json
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8881"').replace("localhost:8858", "localhost:8881"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
FOTO = "(async()=>{ await guardarFotoRega('entrada', new Blob(['x'],{type:'image/jpeg'})); abrirFicha(LS.get('emCurso').area_id)})()"
T = {"pt": ("Às 08:00 ainda não começaram", "Às 10:00 sem rega nem cava-roda", "falta o motivo", "Sem cava-roda e mulching:"),
     "en": ("At 08:00 they had not started yet", "At 10:00 with no watering or ring weeding", "reason missing", "No ring weeding and mulching:"),
     "sw": ("Saa 08:00 bado hawajaanza", "Saa 10:00 bila umwagiliaji wala palizi ya duara", "sababu inakosekana", "Bila palizi ya duara na matandazo:")}[LG]
def entrada_e_nao_regou(pg, campo, mot="tuk_tuk"):
    ficha(pg, campo)
    pg.click("button[onclick^=marcarEntrada]"); pg.wait_for_selector("text=/Entrada marcada|Entry recorded|Kuingia kumewekwa/", timeout=30000)
    pg.evaluate(FOTO); pg.wait_for_timeout(600)
    pg.click("button[onclick='ecraNaoRegou()']"); pg.wait_for_selector("input[name=nr-m]")
    pg.check(f"input[name=nr-m][value={mot}]"); pg.click("button[onclick='gravarNaoRegou()']"); pg.wait_for_timeout(800)
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-20T06:40:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "activista")
    if pg.is_visible("#folha.on") and pg.locator("#j-lista").count():
        for c in pg.locator("#j-lista input").all(): c.check()
        pg.click("#folha-c .btn >> nth=-1"); pg.wait_for_timeout(500)
    # 1. «Não houve rega neste campo» → cava-roda ou motivo
    entrada_e_nao_regou(pg, "PR900101-1")
    passo("1 depois de «não houve rega» abre a cava-roda e o mulching", pg.is_visible("#sa-sim") and pg.is_visible("#sa-nao"))
    pg.screenshot(path=f"/home/claude/rega-test/v247_a_{LG}.png")
    pg.click("#sa-nao"); pg.fill("#sa-txt", "ok"); dial.clear(); pg.click("#sa-ok"); pg.wait_for_timeout(300)
    passo("2 não fazer sem motivo: não grava", pg.is_visible("#sa-txt") and pg.evaluate("!!LS.get('emCurso')"))
    pg.fill("#sa-txt", "Não temos enxadas hoje"); pg.click("#sa-ok"); pg.wait_for_timeout(1500)
    d = pg.evaluate("JSON.stringify((LS.get('diasSemRega',[])||[]).find(x=>x.area_id==='PR900101-1')||null)")
    passo("3 não fazer com motivo: fica no dia sem rega (sem_act) e a entrada sai de curso", "enxadas" in d and not pg.evaluate("!!LS.get('emCurso')"), d[:160])
    # 2. fazer: a cava-roda começa logo neste campo, com o motivo do dia sem rega
    entrada_e_nao_regou(pg, "PR900101-1", "avaria_tuk_tuk")
    pg.click("#sa-sim"); pg.wait_for_timeout(3000)
    x = pg.evaluate("JSON.stringify(LS.get('actCurso'))")
    passo("4 fazer agora: cava-roda em curso neste campo com o motivo «avaria do tuk-tuk»", '"area_id":"PR900101-1"' in x and '"motivo":"avaria_tuk_tuk"' in x and not pg.evaluate("!!LS.get('emCurso')"), (x or '')[:160])
    passo("5 abre a fotografia do início da cava-roda", pg.locator("#fa-foto, [id^=fa-foto]").count() > 0)
    pg.evaluate("anularAct ? LS.del('actCurso') : 0; fecharFolha()")
    # 3. dia sem rega registado no Hoje (o dia todo): escolher o campo
    pg.evaluate("ecraDiaSemRega()"); pg.wait_for_selector("input[name=dsr-m]")
    pg.check("input[name=dsr-m][value=tuk_tuk]"); pg.click("button[onclick='gravarDiaSemRega()']"); pg.wait_for_timeout(800)
    passo("6 dia sem rega do activista: pergunta pela cava-roda", pg.is_visible("#sa-sim"))
    pg.click("#sa-sim"); pg.wait_for_timeout(500)
    passo("7 mostra os campos da equipa para escolher", pg.locator("#sa-campos .lin").count() > 0, str(pg.locator("#sa-campos .lin").count()))
    pg.screenshot(path=f"/home/claude/rega-test/v247_b_{LG}.png")
    # 4. «O meu dia»: alertas e fecho
    demo(pg, "tecnico"); pg.evaluate("fecharFolha()")
    eq = lambda **k: dict(dict(id="e1", nome="Equipa Um", regas=0, plantas=0, motivos=[], comecou=None, actividade=None), **k)
    def md(hora, eqs, ini="2026-11-20"):
        d = {"data": pg.evaluate("hojeISO()"), "trabalho_inicio": ini, "equipas": eqs, "alertas": [], "sem_equipa": 0, "por_aprovar": [], "por_terminar": []}
        return pg.evaluate(f"(() => {{ window.__HORA_TESTE = '{hora}'; LS.set('meuDia', {{ em: new Date().toISOString(), d: {json.dumps(d)}, dia: hojeISO() }}); const h = cartaoMeuDia(); window.__HORA_TESTE = null; return h }})()")
    h = md("07:30", [eq()])
    passo("8 antes das 08:00 sem alerta", "data-k=\"h8\"" not in h and "data-k=\"h10\"" not in h)
    h = md("08:20", [eq(), eq(id="e2", nome="Equipa Dois", comecou="2026-11-20T06:05:00Z")])
    passo("9 às 08:00: só a equipa que não começou", 'data-k="h8"' in h and "Equipa Um" in h.split('data-k="h8"')[1][:2500] and "Equipa Dois" not in h.split('data-k="h8"')[1].split("</details>")[0])
    h = md("10:15", [eq(), eq(id="e2", nome="Equipa Dois", comecou="2026-11-20T06:05:00Z"), eq(id="e3", nome="Equipa Tres", actividade={"campos": 1, "cavaroda": 30, "mulching": 20})])
    seg = h.split('data-k="h10"')[1].split("</details>")[0] if 'data-k="h10"' in h else ""
    passo("10 às 10:00: as duas sem rega nem cava-roda (começou ou não), não a da cava-roda", "Equipa Um" in seg and "Equipa Dois" in seg and "Equipa Tres" not in seg)
    passo("11 antes das 15:30 o início do dia ainda deixa fechar", "md-fechar" in md("12:00", [eq(comecou="2026-11-20T06:05:00Z")]))
    h = md("16:00", [eq(comecou="2026-11-20T06:05:00Z")])
    passo("12 depois das 15:30: começou sem rega nem cava-roda tranca o fecho e pede o motivo", "md-fechar" not in h and "disabled" in h)
    passo("13 dias antes de trabalho_inicio: o início do dia ainda chega", "md-fechar" in md("16:00", [eq(comecou="2026-11-20T06:05:00Z")], ini="2026-11-21"))
    passo("14 a cava-roda e o mulching deixam fechar", "md-fechar" in md("16:00", [eq(actividade={"campos": 1, "cavaroda": 30, "mulching": 20})]))
    h = md("16:00", [eq(motivos=[{"id": "m1", "motivo": "tuk_tuk", "sem_act": "Não temos enxadas"}])])
    passo("15 o motivo para não fazer cava-roda aparece", "Não temos enxadas" in h)
    pg.evaluate("mudar('hoje')"); pg.wait_for_timeout(1500)
    h = md("16:00", [eq(comecou="2026-11-20T06:05:00Z")])
    pg.evaluate("(h) => { window.__TAR_ABERTAS = true; const el = document.createElement('div'); el.id = 't16'; el.innerHTML = h; document.querySelector('#e-hoje').prepend(el); }", h.replace('<details', '<details open'))
    pg.wait_for_timeout(1200)
    tx = pg.inner_text("#t16")
    passo("16 traduzido: «falta o motivo» na equipa que só começou", T[2] in tx, tx[:200].replace("\n", " | "))
    pg.screenshot(path=f"/home/claude/rega-test/v247_c_{LG}.png", full_page=True)
    pg.evaluate("window.__HORA_TESTE=null")
    # 5. painel: a razão de não fazer cava-roda na tabela dos dias sem rega
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(7000)
    fr = pg.frame("painel") or [x for x in pg.frames if "painel.html" in x.url][0]
    fr.evaluate("DSR = [{ id: 'x', data: '2026-11-20', activista: 'Equipa A', comunidade: 'X', motivo: 'tuk_tuk', todo_dia: true, descricao: '', sem_act: 'Sem enxadas', regas: 0, quem: 'A' }]; document.getElementById('s-dsr').hidden = false; desenharDiasSemRega()")
    pg.wait_for_timeout(300)
    passo("17 painel: «Sem cava-roda e mulching» na tabela", "Sem enxadas" in fr.evaluate("$('#t-dsr').textContent") and T[3] in fr.evaluate("$('#t-dsr').textContent"))
    passo("18 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']} {PEDIDOS['urls'][:3]}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
