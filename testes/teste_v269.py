# v269 (27/11/2026): mudar o plano da equipa no mapa. Escolhe-se o dia em baixo e cada campo tocado passa para esse dia,
# no lugar que acrescenta menos caminho; tocar num campo do mesmo dia tira-o; campos fora do plano a cinzento entram no dia;
# «Ordem mais curta», «Desfazer», dia novo, «Ver na lista», gravar com motivo (editar_plano). Simulação (supervisor). LING=en / sw.
import os, sys, json
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8889"').replace("localhost:8858", "localhost:8889"))
LG = os.environ.get("LING", "pt"); res = {}; SHOT = "/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad"
PL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados_v256_planos.json")))
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
def ids(pg): return pg.evaluate("S.edPlano.dias.map((d) => d.campos.map((c) => c.area_id))")
def toca(pg, area): pg.evaluate("(a) => tocarCampoPlano(a)", area); pg.wait_for_timeout(250)
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.set_viewport_size({"width": 400, "height": 820}); pg.clock.install(time="2026-11-27T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "supervisor"); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(1500)
    n = pg.evaluate("""(PL) => { const A = S.areas.find((a) => a.activista_id).activista_id, r = rondaEquipa(A) || 1;
      const L = S.areas.filter((a) => a.activista_id === A && a.latitude != null); window.__A = A; window.__L = L.map((a) => a.id);
      const c = (a) => ({ area_id: a.id, produtor: a.produtor, plantas: plantasN(a), base: plantasN(a), sem_coordenada: false });
      const dias = [{ n: 1, campos: L.slice(0, 2).map(c) }, { n: 2, campos: L.slice(2, 3).map(c), continua: true }];
      LS.set('planos', [{ ...PL[0], id: 'pl-0', activista_id: A, activista: 'Equipa Teste', ronda: r, estado: 'aprovado', dias, pode_mudar: true, criado_em: new Date().toISOString() }]);
      S.visiveis = [A]; LS.set('avisoPlanos', hojeISO() + '|' + S.perfil.id);
      window.__ED = null; window.__AL = []; window.alert = (m) => window.__AL.push(String(m)); window.confirm = () => true; const o = sb.rpc.bind(sb);
      sb.rpc = (nm, a) => nm === 'editar_plano' ? (window.__ED = a, Promise.resolve({ data: 'aprovado', error: null }))
        : nm === 'planos_lista' ? Promise.resolve({ data: LS.get('planos').map((p) => ({ ...p, ...(window.__ED ? { dias: window.__ED.p_dias } : {}) })), error: null })
        : nm === 'itinerario_estado' ? Promise.resolve({ data: { fechos: [], falhas: [] }, error: null }) : o(nm, a);
      return L.length; }""", PL)
    L = pg.evaluate("window.__L"); print("campos da equipa com coordenada:", n)
    pg.evaluate("ecraPlano('pl-0')"); pg.wait_for_timeout(500)
    passo("1 ficha do plano: «Mudar o plano no mapa» e «na lista»", pg.locator("#pl-editar-mapa").count() == 1 and pg.locator("#pl-editar").count() == 1)
    pg.click("#pl-editar-mapa"); pg.wait_for_selector("#pm-dias"); pg.wait_for_timeout(800)
    np = pg.locator(".pm-pt").count(); cinz = pg.locator(".pm-pt", has_text="+").count()
    passo("2 mapa: um ponto por campo da equipa, os fora do plano a cinzento (+), 2 dias em baixo", np == n and cinz == n - 3 and pg.locator(".pm-dia").count() == 2, f"pontos={np} cinzentos={cinz}")
    pg.screenshot(path=f"{SHOT}/v269_mapa_{LG}.png")
    fim0 = pg.inner_text(".pm-dia >> nth=0")
    toca(pg, L[2])
    passo("3 dia 1 escolhido: tocar num campo do dia 2 passa-o para o dia 1", ids(pg)[0].count(L[2]) == 1 and L[2] not in ids(pg)[1] and pg.inner_text(".pm-dia >> nth=0") != fim0, str(ids(pg)))
    if n > 3:
        toca(pg, L[3])
        d0 = ids(pg)[0]
        passo("4 campo fora do plano (cinzento) entra no dia 1, no lugar mais curto", L[3] in d0 and len(d0) == 4, str(d0))
    toca(pg, L[0])
    passo("5 tocar num campo do mesmo dia tira-o do plano", L[0] not in sum(ids(pg), []))
    pg.click("#pm-desf"); pg.wait_for_timeout(250)
    passo("6 «Desfazer» repõe", L[0] in ids(pg)[0])
    pg.click("#pm-novo"); pg.wait_for_timeout(250)
    passo("7 dia novo fica escolhido", pg.locator(".pm-dia").count() == 3 and pg.evaluate("S.edPlano.diaAct") == 2)
    toca(pg, L[1])
    passo("8 com o dia 3 escolhido, um campo do dia 1 passa para o dia 3", ids(pg)[2] == [L[1]])
    pg.evaluate("escolherDiaPlanoMapa(0)"); pg.wait_for_timeout(200)
    antes = pg.evaluate("(() => { const d = S.edPlano.dias[0]; const P = d.campos.map((c) => posPl(c.area_id)); return P.reduce((t, q, i) => t + (i ? metros(P[i - 1], q) : 0), 0); })()")
    if pg.locator("#pm-ordem").is_enabled():
        pg.click("#pm-ordem"); pg.wait_for_timeout(250)
    depois = pg.evaluate("(() => { const d = S.edPlano.dias[0]; const P = d.campos.map((c) => posPl(c.area_id)); return P.reduce((t, q, i) => t + (i ? metros(P[i - 1], q) : 0), 0); })()")
    passo("9 «Ordem mais curta» não aumenta o caminho do dia", depois <= antes + 1, f"{round(antes)} → {round(depois)} m")
    pg.screenshot(path=f"{SHOT}/v269_mapa2_{LG}.png")
    pg.click("#pm-lista"); pg.wait_for_selector(".ep-dia"); pg.wait_for_timeout(300)
    passo("10 «Ver na lista» abre o editor com as mesmas mudanças", pg.locator(".ep-dia").count() == 3 and pg.locator("#ep-mapa").count() == 1)
    pg.click("#ep-mapa"); pg.wait_for_selector("#pm-dias"); pg.wait_for_timeout(500)
    passo("11 e volta ao mapa sem perder nada", pg.locator(".pm-dia").count() == 3)
    pg.click("#pm-gravar"); pg.wait_for_selector("#ep-mot"); pg.click("#ep-gravar"); pg.wait_for_timeout(400)
    passo("12 sem motivo não grava", pg.evaluate("window.__ED") is None and len(pg.evaluate("window.__AL")) > 0)
    pg.fill("#ep-mot", "Campos de perto no mesmo dia"); pg.click("#ep-gravar"); pg.wait_for_timeout(900)
    ed = pg.evaluate("window.__ED") or {}
    ok = ed and [d["n"] for d in ed["p_dias"]] == list(range(1, len(ed["p_dias"]) + 1)) and ed["p_dias"][-1].get("continua") and all(d.get("fim") for d in ed["p_dias"])
    passo("13 grava pelo editar_plano: dias numerados, horas e continuação no último dia", ok, json.dumps([(d["n"], len(d["campos"]), d.get("fim")) for d in ed.get("p_dias", [])]))
    passo("14 sai do mapa do plano e volta à ficha", not pg.evaluate("!!S.planoEdMapa") and pg.locator(".pl-dia").count() >= 2 and pg.locator(".pm-pt").count() == 0)
    if LG != "pt":
        pg.click("#pl-editar-mapa"); pg.wait_for_selector("#pm-dias"); pg.wait_for_timeout(600)
        txt = pg.inner_text("#sug-mapa")
        pt = [w for w in ["Mudar o plano", "Toque num campo", "Dia novo", "Ordem mais curta", "Desfazer", "Ver na lista", "Gravar", "Dia 1", "Cinzento"] if w in txt]
        passo("15 sem português no painel do mapa", not pt, str(pt)); pg.screenshot(path=f"{SHOT}/v269_mapa3_{LG}.png")
        pg.click("#pm-sair"); pg.wait_for_timeout(300)
    passo("16 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
