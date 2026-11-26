# v263 (26/11/2026): mudar o plano da equipa na app (gestor principal e supervisor da equipa): passar campos entre dias, mudar a ordem,
# tirar e acrescentar campos, dia novo, ver no mapa com as mudanças, gravar com motivo; pedir um plano novo. O técnico não muda.
# Simulação (supervisor); editar_plano / pedir_plano_novo / planos_lista respondidos na página. LING=en / sw.
import os, sys, json
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8887"').replace("localhost:8858", "localhost:8887"))
LG = os.environ.get("LING", "pt"); res = {}; SHOT = "/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad"
PL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados_v256_planos.json")))
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-26T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "supervisor"); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(1500)
    n = pg.evaluate("""(PL) => { const A = S.areas.find((a) => a.activista_id).activista_id, r = rondaEquipa(A) || 1;
      const L = S.areas.filter((a) => a.activista_id === A && a.latitude != null); window.__A = A; window.__L = L.map((a) => a.id);
      const c = (a) => ({ area_id: a.id, produtor: a.produtor, plantas: plantasN(a), base: plantasN(a), sem_coordenada: false });
      const dias = [{ n: 1, campos: L.slice(0, 2).map(c) }, { n: 2, campos: L.slice(2, 3).map(c), continua: true, continua_ate: '12:00' }];
      LS.set('planos', [{ ...PL[0], id: 'pl-0', activista_id: A, activista: 'Equipa Teste', ronda: r, estado: 'aprovado', dias, pode_mudar: true, criado_em: new Date().toISOString(),
        n_alteracoes: 1, alterado_nome: 'Raul Exemplo', alterado_em: '2026-11-25T10:00:00Z', alterado_motivo: 'Campo longe' }]);
      S.visiveis = [A]; LS.set('avisoPlanos', hojeISO() + '|' + S.perfil.id);
      window.__ED = null; window.__PED = null; window.__AL = []; window.alert = (m) => window.__AL.push(String(m)); const o = sb.rpc.bind(sb);
      sb.rpc = (nm, a) => nm === 'editar_plano' ? (window.__ED = a, Promise.resolve({ data: 'aprovado', error: null }))
        : nm === 'pedir_plano_novo' ? (window.__PED = a, Promise.resolve({ data: 'pedido', error: null }))
        : nm === 'planos_lista' ? Promise.resolve({ data: LS.get('planos').map((p) => ({ ...p, ...(window.__ED ? { dias: window.__ED.p_dias, n_alteracoes: 2 } : {}), ...(window.__PED ? { pedido_novo_em: new Date().toISOString() } : {}) })), error: null })
        : nm === 'itinerario_estado' ? Promise.resolve({ data: { fechos: [], falhas: [] }, error: null }) : o(nm, a);
      return L.length; }""", PL)
    print("campos da equipa com coordenada:", n)
    pg.evaluate("ecraPlano('pl-0')"); pg.wait_for_timeout(500)
    t = pg.inner_text("#folha")
    passo("1 ficha do plano: «Mudar o plano», pedir plano novo e histórico das mudanças", pg.locator("#pl-editar").count() == 1 and pg.locator("#pl-pedir").count() == 1 and pg.locator("#pl-hist").count() == 1, pg.inner_text("#pl-hist") if pg.locator("#pl-hist").count() else "")
    pg.screenshot(path=f"{SHOT}/v263_plano_{LG}.png", full_page=True)
    pg.click("#pl-editar"); pg.wait_for_selector(".ep-dia"); pg.wait_for_timeout(300)
    passo("2 editor: um cartão por dia com os campos", pg.locator(".ep-dia").count() == 2 and pg.locator(".ep-c").count() == 3)
    fim0 = pg.inner_text(".ep-dia >> nth=1").split("\n")[0]
    pg.locator(".ep-c[data-dia='0'][data-k='0'] select.ep-sel").select_option("1"); pg.wait_for_timeout(300)
    passo("3 passar o 1.º campo do dia 1 para o dia 2: horas recalculadas", pg.locator(".ep-c[data-dia='0']").count() == 1 and pg.locator(".ep-c[data-dia='1']").count() == 2 and pg.inner_text(".ep-dia >> nth=1").split("\n")[0] != fim0, pg.inner_text(".ep-dia >> nth=1").split("\n")[0])
    antes = pg.evaluate("S.edPlano.dias[1].campos.map((c) => c.area_id)")
    pg.locator(".ep-c[data-dia='1'][data-k='1'] .ep-sobe").click(); pg.wait_for_timeout(200)
    passo("4 ↑ muda a ordem no dia", pg.evaluate("S.edPlano.dias[1].campos.map((c) => c.area_id)") == [antes[1], antes[0]])
    pg.locator(".ep-dia >> nth=0").locator(".ep-mais").click(); pg.wait_for_timeout(300)
    na = pg.locator(".ep-add").count()
    if na: pg.locator(".ep-add .chip").first.click(); pg.wait_for_timeout(300)
    passo("5 acrescentar um campo da equipa que não estava no plano", na > 0 and pg.locator(".ep-c[data-dia='0']").count() == 2, f"para escolher: {na}")
    pg.locator(".ep-c[data-dia='0'][data-k='1'] .ep-tira").click(); pg.wait_for_timeout(200)
    passo("6 ✕ tira o campo do plano", pg.locator(".ep-c[data-dia='0']").count() == 1)
    pg.locator(".ep-c[data-dia='1'][data-k='0'] select.ep-sel").select_option("novo"); pg.wait_for_timeout(300)
    passo("7 passar para um dia novo", pg.locator(".ep-dia").count() == 3)
    pg.screenshot(path=f"{SHOT}/v263_editor_{LG}.png", full_page=True)
    pg.click("text=" + {"pt": "Ver no mapa (com as mudanças)", "en": "See on the map (with the changes)", "sw": "Ona kwenye ramani (pamoja na mabadiliko)"}[LG]); pg.wait_for_timeout(800)
    passo("8 mapa com as mudanças e «Voltar às mudanças»", pg.locator("#pm-voltar-ed").count() == 1 and pg.evaluate("S.planoIds && S.planoIds.size") == 3)
    pg.screenshot(path=f"{SHOT}/v263_mapa_{LG}.png")
    pg.click("#pm-voltar-ed"); pg.wait_for_selector(".ep-dia"); pg.wait_for_timeout(300)
    passo("9 de volta ao editor, com as mudanças guardadas", pg.locator(".ep-dia").count() == 3)
    pg.click("#ep-gravar"); pg.wait_for_timeout(400)
    passo("10 sem motivo não grava", pg.evaluate("window.__ED") is None and len(pg.evaluate("window.__AL")) > 0)
    pg.fill("#ep-mot", "Campos de Quiwia juntos no mesmo dia"); pg.click("#ep-gravar"); pg.wait_for_timeout(800)
    ed = pg.evaluate("window.__ED")
    ok = ed and [d["n"] for d in ed["p_dias"]] == [1, 2, 3] and [len(d["campos"]) for d in ed["p_dias"]] == [1, 1, 1] and ed["p_dias"][-1].get("continua") and not ed["p_dias"][1].get("continua") and all(d.get("fim") for d in ed["p_dias"]) and ed["p_motivo"].startswith("Campos")
    passo("11 grava: dias 1..3, a continuação no último dia, horas de cada dia e o motivo", ok, json.dumps([(d["n"], len(d["campos"]), d.get("inicio"), d.get("fim")) for d in (ed or {}).get("p_dias", [])]))
    passo("12 volta à ficha do plano com o plano novo", pg.locator(".pl-dia").count() == 3)
    pg.locator("#pl-mudar details.ajuda summary").click(); pg.fill("#pl-novo-mot", "Equipa mudou de comunidade"); pg.click("#pl-pedir"); pg.wait_for_timeout(600)
    passo("13 pedir um plano novo: pedido enviado e aviso na ficha", (pg.evaluate("window.__PED") or {}).get("p_motivo") == "Equipa mudou de comunidade" and pg.locator("#pl-pedido").count() == 1)
    if LG != "pt":
        pg.click("#pl-editar"); pg.wait_for_selector(".ep-dia"); pg.wait_for_timeout(300)
        txt = pg.inner_text("#folha")
        pt = [w for w in ["Mudar o plano", "Passar para", "Acrescentar", "plantas", "da meta", "Dia novo", "Gravar", "Porque muda", "Dia 1", "Ver no mapa"] if w in txt]
        passo("14 sem português no editor", not pt, str(pt)); pg.screenshot(path=f"{SHOT}/v263_editor2_{LG}.png", full_page=True)
    pg.evaluate("S.edPlano = null; LS.set('planos', LS.get('planos').map((p) => ({ ...p, pode_mudar: false }))); S.perfil = { ...S.perfil, papel: 'tecnico' }; ecraPlano('pl-0')"); pg.wait_for_timeout(400)
    passo("15 técnico (sem permissão) não vê «Mudar o plano»", pg.locator("#pl-editar").count() == 0 and pg.locator("#pl-hist").count() == 1)
    passo("16 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
