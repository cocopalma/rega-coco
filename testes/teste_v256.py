# v256 (22/11/2026): planos da versão 3 (dia das 06:30 às 14:00 com a espera pela água, a rega, a deslocação e as outras esperas;
# último dia da ronda que continua com a ronda seguinte) e o apoio entre equipas sugerido no «O meu dia» do supervisor.
# Simulação, supervisor. LING=en / sw. Dados: dois planos reais do gerador (Oliveira, rondas 3 e 4), em dados_v256_planos.json.
import os, sys, json
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8886"').replace("localhost:8858", "localhost:8886"))
LG = os.environ.get("LING", "pt"); res = {}
PL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados_v256_planos.json")))
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
T = {"pt": ("O que a equipa fez nos últimos 30 dias", "Espera pela água", "fica feita: a equipa continua com o dia 1 da ronda", "Continua o último dia da ronda", "Apoio entre equipas sugerido", "pode ajudar"),
     "en": ("What the team did in the last 30 days", "Waiting for water", "is done: the team carries on with day 1 of round", "Carries on the last day of round", "Help between teams suggested", "can help"),
     "sw": ("Timu ilifanya nini katika siku 30 zilizopita", "Kusubiri maji", "imekamilika: timu inaendelea na siku ya 1 ya mzunguko", "Inaendelea na siku ya mwisho ya mzunguko", "Msaada kati ya timu unaopendekezwa", "anaweza kusaidia")}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-22T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "supervisor"); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(1500)
    pg.evaluate("""(PL) => { const A = S.areas.find((a) => a.activista_id).activista_id, r = rondaEquipa(A) || 1;
      LS.set('planos', PL.map((p, k) => ({ ...p, id: 'pl-' + k, activista_id: A, activista: 'Equipa Teste', ronda: r + k, estado: 'por_supervisor', criado_em: new Date().toISOString() })));
      S.visiveis = [A]; LS.set('avisoPlanos', hojeISO() + '|' + S.perfil.id);
      LS.set('apoioSug', [{ ajuda_id: A, ajuda_nome: 'Equipa Rápida', ajuda_ronda: 3, para_id: A, para_nome: 'Equipa Lenta', para_ronda: 2, para_lista: 59, para_regadas: 33,
        motivo: 'ronda_curta', ajuda_dias: 5, para_dias: 15, campos: 26, nunca: 0, plantas: 2100, dist_min: 683 }]); }""", PL)
    pg.evaluate("ecraPlano('pl-0')"); pg.wait_for_timeout(500)
    t = pg.inner_text("#folha")
    passo("1 plano v3: cartão do que a equipa fez e horário de cada dia", T[0] in t and pg.locator("#pl-apr").count() == 1 and pg.locator(".pl-dia").count() == len(PL[0]["dias"]), t[:160].replace("\n", " | "))
    d0 = PL[0]["dias"][0]
    passo("2 dia com o horário e as partes do tempo", f"{d0['inicio']} – {d0['fim']}" in t and T[1] in t and pg.locator(".pl-partes").count() == len(PL[0]["dias"]))
    passo("3 último dia: continua com a ronda seguinte", T[2] in t and PL[0]["dias"][-1]["continua_ate"] in t)
    passo("4 nomes dos produtores e plantas de cada campo", all(c["produtor"] in t for c in d0["campos"]))
    pg.screenshot(path=f"/home/claude/rega-test/v256_plano_{LG}.png", full_page=True)
    pg.locator(".pl-dia").last.screenshot(path=f"/home/claude/rega-test/v256_dia_{LG}.png")
    pg.evaluate("fecharFolha(); ecraPlano('pl-1')"); pg.wait_for_timeout(500)
    t2 = pg.inner_text("#folha")
    passo("5 plano da ronda seguinte: o dia 1 continua o último dia da ronda anterior", T[3] in t2 and PL[1]["dias"][0]["inicio"] in t2)
    pg.evaluate("fecharFolha(); window.__TAR_ABERTAS = true; $('#hoje').innerHTML = cartaoMeuDia()"); pg.wait_for_timeout(300)
    k = pg.locator("#meu-dia details[data-k=ap]")
    passo("6 «O meu dia» do supervisor: apoio sugerido com «Ver os campos e activar»", k.count() == 1 and T[5] in k.inner_text() and k.locator(".sug-apoio .chip").count() == 1, k.inner_text()[:160].replace("\n", " | ") if k.count() else "")
    pg.screenshot(path=f"/home/claude/rega-test/v256_meudia_{LG}.png", full_page=True)
    pg.evaluate("S.perfil = { ...S.perfil, papel: 'tecnico' }; $('#hoje').innerHTML = cartaoMeuDia()"); pg.wait_for_timeout(300)
    passo("7 técnico não vê a linha do apoio no «O meu dia»", pg.locator("#meu-dia details[data-k=ap]").count() == 0)
    if LG != "pt":
        pg.evaluate("S.perfil = { ...S.perfil, papel: 'supervisor' }; ecraPlano('pl-0')"); pg.wait_for_timeout(500)
        pt = [w for w in ["Espera pela água", "Deslocação", "Outras esperas", "plantas", "da meta", "Dias com rega", "Rega, por planta", "fica feita"] if w in pg.inner_text("#folha")]
        passo("8 sem português no plano", not pt, str(pt))
    passo("9 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
