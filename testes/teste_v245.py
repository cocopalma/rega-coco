# v245: plantas mórbidas a 20 L na saída, meta equivalente (1 planta a 20 L = 4, desde 19/11) e meta do dia depois da saída (simulação). LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8879"').replace("localhost:8858", "localhost:8879"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
DBX = lambda pg, e: pg.evaluate("(() => { const D = JSON.parse(sessionStorage.getItem('rega.demo.db')); return " + e + " })()")
FOTOS = "(async()=>{ for (const t of %s) await guardarFotoRega(t, new Blob(['x'],{type:'image/jpeg'})); abrirFicha(LS.get('emCurso').area_id)})()"
T = {"pt": ("mórbidas receberam 20 L", "A 5 L:", "Meta de hoje", "Meta do dia atingida", "contam como 4"),
     "en": ("sickly plants received 20 L", "At 5 L:", "Today's target", "Today's target reached", "count as 4"),
     "sw": ("dhaifu ilipewa lita 20", "Kwa lita 5:", "Lengo la leo", "Lengo la leo limefikiwa", "kama 4")}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-19T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "activista")
    if pg.is_visible("#folha.on") and pg.locator("#j-lista").count():
        for c in pg.locator("#j-lista input").all(): c.check()
        pg.click("#folha-c .btn >> nth=-1"); pg.wait_for_timeout(500)
    pes = pg.evaluate("jornadaHoje() && jornadaHoje().pessoas")
    passo("0 equivalente: 18/11 sem peso, 19/11 com peso", pg.evaluate("[plEq(100,10,'2026-11-18'), plEq(100,10,'2026-11-19'), plEq(5,9,'2026-11-19')].join()") == "100,130,20")
    ficha(pg, 'PR900101-1')
    pg.click("button[onclick^=marcarEntrada]"); pg.wait_for_selector("text=/Entrada marcada|Entry recorded|Kuingia kumewekwa/", timeout=30000)
    pg.evaluate(FOTOS % "['entrada']"); pg.wait_for_timeout(500)
    pg.click("button[onclick='pedirTuk(false)']"); pg.wait_for_selector("#tk-cod"); pg.select_option("#tk-cod", "12"); pg.click("button[onclick='confirmarTuk(false)']"); pg.wait_for_timeout(500)
    pg.evaluate(FOTOS % "['rega','saida']"); pg.wait_for_timeout(500)
    pg.evaluate("delete window.__P20_TESTE"); pg.click("button[onclick='ecraSaida()']"); pg.wait_for_timeout(300)
    base = pg.evaluate("baseSaida(S.areas.find(a=>a.id==='PR900101-1')).resta")
    passo("1 saída tem o campo das plantas a 20 L, vazio", pg.is_visible("#s-p20") and pg.input_value("#s-p20") == "" and T[0] in pg.inner_text("#folha-c"))
    pg.fill("#s-plantas", str(base)); dial.clear(); pg.click("button[onclick='marcarSaida()']"); pg.wait_for_timeout(300)
    passo("2 sem o número a 20 L não grava", len(dial) == 1 and pg.evaluate("!!LS.get('emCurso')"), dial[:1])
    pg.fill("#s-p20", str(base + 1)); pg.wait_for_timeout(100)
    passo("3 mais a 20 L do que regadas: aviso no ecrã", pg.locator("#s-agua-decl .msg.erro").count() == 1)
    dial.clear(); pg.click("button[onclick='marcarSaida()']"); pg.wait_for_timeout(300)
    passo("4 e não grava", len(dial) == 1 and pg.evaluate("!!LS.get('emCurso')"))
    pg.fill("#s-p20", "10"); pg.wait_for_timeout(100)
    ag = pg.inner_text("#s-agua-decl")
    litros = 5 * (base - 10) + 20 * 10
    passo("5 mostra 5 L / 20 L / água", T[1] in ag and f"{litros:,}".replace(",", " ") in ag.replace(" ", " ").replace("\xa0", " ") or str(litros) in ag.replace(" ", "").replace(" ", "").replace("\xa0", "").replace(",", "").replace(".", ""), ag)
    pg.screenshot(path=f"/home/claude/rega-test/v245_a_{LG}.png")
    pg.click("button[onclick='marcarSaida()']"); pg.wait_for_timeout(4000)
    r = DBX(pg, "D.registos.filter(r=>!r.teste && r.area_id==='PR900101-1').map(r=>[r.plantas_regadas, r.plantas_20l])")
    passo("6 a rega chega com plantas_20l", r == [[base, 10]], str(r))
    tx = pg.inner_text("#folha-c") if pg.locator("#meta-dia").count() else ""
    eq, meta = base + 30, 140 * (pes or 0)
    passo("7 depois da saída: meta do dia com as plantas equivalentes", pg.locator("#meta-dia").count() == 1 and (T[2] in tx or T[3] in tx) and T[4] in tx, (pg.inner_text("#meta-dia") if pg.locator("#meta-dia").count() else "sem #meta-dia") + f" // eq={eq} meta={meta}")
    pg.screenshot(path=f"/home/claude/rega-test/v245_b_{LG}.png")
    pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(1500)
    passo("8 Hoje do activista mostra a meta de hoje", pg.locator("#e-hoje #meta-dia").count() == 1, pg.inner_text("#e-hoje #meta-dia") if pg.locator("#e-hoje #meta-dia").count() else "")
    pg.screenshot(path=f"/home/claude/rega-test/v245_c_{LG}.png", full_page=True)
    # meta atingida (meta pequena simulada)
    pg.evaluate("CFG.metaPlantas = 1; actHoje()"); pg.wait_for_timeout(1200)
    passo("9 meta atingida", pg.locator("#e-hoje #meta-dia.ok").count() == 1 and T[3] in pg.inner_text("#e-hoje #meta-dia"))
    pg.evaluate("CFG.metaPlantas = 140")
    # painel: secção da água (dados simulados) e meta com plantas_eq
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(7000)
    fr = pg.frame("painel") or [f for f in pg.frames if "painel.html" in f.url][0]
    fr.evaluate("""DAG = { inicio: '2026-11-15', viagem_min: 300, viagem_max: 350, dias: [
      { data: '2026-11-19', equipa: 'Equipa A', tecnico: 'Téc', plantas: 200, plantas_20l: 10, regas_sem_20l: 0, litros_declarados: 1150, viagens: 2, outras_voltas: 0, regas_sem_tuk: 0, litros_viagens_min: 600, litros_viagens_max: 700 },
      { data: '2026-11-19', equipa: 'Equipa B', tecnico: 'Téc', plantas: 100, plantas_20l: 0, regas_sem_20l: 1, litros_declarados: 500, viagens: 2, outras_voltas: 0, regas_sem_tuk: 0, litros_viagens_min: 600, litros_viagens_max: 700 }] };
      desenharAgua(); DP = [{ data: '2026-11-19', equipa: 'Equipa A', comunidade: 'X', plantas: 200, plantas_20l: 10, plantas_eq: 230, pessoas: 2, tamanho: 2, campos: 2 }]; desenharMeta();""")
    pg.wait_for_timeout(500)
    passo("11 painel: secção da água com a equipa acima das viagens", not fr.evaluate("$('#s-agu').hidden") and fr.locator("#t-agu .falta").count() == 1, fr.inner_text("#k-agu")[:200].replace("\n", " | "))
    passo("12 painel: % da meta usa as plantas equivalentes (230 / 280 = 82%)", "82%" in fr.inner_text("#t-meta"), fr.inner_text("#t-meta")[:160].replace("\n", " | "))
    fr.evaluate("document.getElementById('s-agu').scrollIntoView()"); pg.wait_for_timeout(300)
    pg.screenshot(path=f"/home/claude/rega-test/v245_d_{LG}.png")
    passo("10 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']} {PEDIDOS['urls'][:3]}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
