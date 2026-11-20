# v249: o «O meu dia» só com o que é do dia; o que ficou de outros dias numa linha «Por tratar de dias anteriores»; campos sem equipa,
# nunca receberam água e a lista completa das recontagens em «Mais»; recontagens do dia; ver um dia anterior pela data. Simulação. LING=en / sw.
import os, sys, json
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8883"').replace("localhost:8858", "localhost:8883"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
T = {"pt": ("Por tratar de dias anteriores", "Dia anterior", "só para ver", "Voltar a hoje", "o que mudou hoje"),
     "en": ("To deal with from previous days", "Previous day", "view only", "Back to today", "what changed today"),
     "sw": ("Ya kushughulikia kutoka siku zilizopita", "Siku iliyopita", "ya kuangalia tu", "Rudi leo", "kilichobadilika leo")}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-20T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "tecnico"); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(1500)
    passo("1 «O meu dia» com «Dia anterior» e a data", pg.locator("#md-ant").count() == 1 and pg.locator("#md-data").count() == 1)
    # dados do dia com coisas de hoje e de dias anteriores (o servidor de exemplo não tem tudo)
    hoje = pg.evaluate("hojeISO()")
    pg.evaluate("""(() => { const c = LS.get('meuDia'); const d = c.d, h = hojeISO(), o = '2026-11-17';
      const a = S.areas[0], b = S.areas[1];
      d.alertas = [{ registo_id: 'r-hoje', data: h, area_id: a.id, produtor: 'Prod Hoje', equipa: 'Eq', plantas: 300, base: 100, tipo: 'mais_que_base' },
                   { registo_id: 'r-velho', data: o, area_id: b.id, produtor: 'Prod Antigo', equipa: 'Eq', plantas: 300, base: 100, tipo: 'mais_que_base' }];
      d.por_aprovar = [{ area_id: a.id, produtor: 'Med Hoje', equipa: 'Eq', proposta_em: new Date().toISOString() }, { area_id: b.id, produtor: 'Med Antiga', equipa: 'Eq', proposta_em: '2026-11-15T08:00:00Z' }];
      a.poligono_proposto = b.poligono_proposto = [[0, 0], [0, 1], [1, 1]];
      d.sem_equipa = 3; LS.set('meuDia', c);
      LS.set('motivosAnt', [{ id: 'm1', activista_id: d.equipas[0].id, activista: 'Act', data: o, motivo: 'tuk_tuk', quem: 'Act' }]);
      S.recont = [{ id: 'rc1', area_id: a.id, produtor: 'Rec Hoje', motivo: 'Teste', estado: 'validada', pedido_em: '2026-11-10T08:00:00Z', validada_em: new Date().toISOString(), vivas: 80 },
                  { id: 'rc2', area_id: b.id, produtor: 'Rec Antiga', motivo: 'Teste', estado: 'por_encaminhar', pedido_em: '2026-11-12T08:00:00Z' }];
      window.__TAR_ABERTAS = true; })()""")
    h = pg.evaluate("cartaoMeuDia()"); pg.evaluate("$('#hoje').innerHTML = cartaoMeuDia() + cartaoMaisHoje('')"); pg.wait_for_timeout(500)
    md = pg.inner_text("#meu-dia")
    al = pg.inner_text("#meu-dia details[data-k=al]")
    passo("2 ⚠️ de hoje na linha do dia, a antiga não", "Prod Hoje" in al and "Prod Antigo" not in al)
    ant = pg.inner_text("#meu-dia details[data-k=ant]") if pg.locator("#meu-dia details[data-k=ant]").count() else ""
    passo("3 «Por tratar de dias anteriores» com a ⚠️ antiga, a medição antiga e o motivo", T[0] in ant and "Prod Antigo" in ant and "Med Antiga" in ant and pg.locator("#meu-dia details[data-k=ant] details[data-k=ma]").count() == 1, ant[:200].replace("\n", " | "))
    me = pg.inner_text("#meu-dia details[data-k=me]")
    passo("4 medição de hoje no dia, a antiga não", "Med Hoje" in me and "Med Antiga" not in me)
    n = pg.inner_text("#meu-dia details[data-k=ant] > summary .nb")
    passo("5 número da linha dos dias anteriores = 3", n.strip() == "3", n)
    passo("6 sem «Campos sem equipa» nem «nunca receberam água» no «O meu dia»", pg.locator("#meu-dia details[data-k=se]").count() == 0 and pg.locator("#meu-dia details[data-k=na]").count() == 0)
    passo("7 «Campos sem equipa» e todas as recontagens em «Mais»", pg.locator("#hoje details[data-k=se]").count() == 1 and pg.locator("#hoje details[data-k=m-rc]").count() == 1)
    rc = pg.inner_text("#meu-dia details[data-k=rc]")
    pa_, pb_ = pg.evaluate("[S.areas[0].produtor, S.areas[1].produtor]")
    passo("8 recontagens: só as que mudaram hoje", T[4] in rc and pa_ in rc and pb_ not in rc, rc[:160].replace("\n", " | "))
    pg.screenshot(path=f"/home/claude/rega-test/v249_a_{LG}.png", full_page=True)
    # ver um dia anterior
    pg.evaluate("window.__TAR_ABERTAS = false; desenharHoje()"); pg.wait_for_timeout(1500)
    pg.click("#md-ant"); pg.wait_for_timeout(2500)
    t = pg.inner_text("#meu-dia")
    ontem = pg.evaluate("(() => { const d = new Date(hojeISO() + 'T12:00:00'); d.setDate(d.getDate() - 1); return d.toLocaleDateString('sv-SE') })()")
    passo("9 dia anterior: «só para ver», com a data e «Voltar a hoje»", T[2] in t and pg.input_value("#md-data") == ontem and pg.locator("#md-hoje").count() == 1, t[:200].replace("\n", " | "))
    passo("10 sem «Fechar o dia» no dia anterior", pg.locator("#md-fechar").count() == 0 and "Fechar o dia" not in t.replace("«Fechar o dia»", ""))
    passo("11 guardado no telefone", ontem in pg.evaluate("Object.keys(LS.get('meuDiaHist', {}))"))
    pg.screenshot(path=f"/home/claude/rega-test/v249_b_{LG}.png", full_page=True)
    pg.fill("#md-data", "2026-11-15"); pg.dispatch_event("#md-data", "change"); pg.wait_for_timeout(2000)
    passo("12 escolher uma data qualquer", pg.input_value("#md-data") == "2026-11-15" and "15/11/2026" in pg.inner_text("#meu-dia h2"))
    pg.click("#md-hoje"); pg.wait_for_timeout(2000)
    passo("13 voltar a hoje", pg.locator("#md-hoje").count() == 0 and pg.input_value("#md-data") == hoje)
    passo("14 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']} {PEDIDOS['urls'][:3]}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
