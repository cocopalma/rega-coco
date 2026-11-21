# v250: planos de rondas que a equipa já passou não aparecem; o supervisor vê ao abrir a app, uma vez por dia, os planos das suas
# equipas por aprovar; também no «O meu dia». Simulação, supervisor. LING=en / sw.
import os, sys, json
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8885"').replace("localhost:8858", "localhost:8885"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
T = {"pt": ("Planos das equipas por aprovar", "Ver e aprovar", "Por aprovar por si"),
     "en": ("Team plans to approve", "View and approve", "To be approved by you"),
     "sw": ("Mipango ya timu ya kuidhinisha", "Tazama na uidhinishe", None)}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-21T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "supervisor"); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(1500)
    info = pg.evaluate("""(() => { const eq = [...new Set(S.areas.filter((a) => a.activista_id).map((a) => a.activista_id))];
      const A = eq[0], B = eq[1], r = rondaEquipa(A) || 1;
      const nome = (i) => (S.activistas.find((x) => x.id === i) || {}).nome || i;
      const dias = [{ n: 1, campos: [{ area_id: S.areas[0].id, plantas: 50 }], plantas: 50 }];
      LS.set('planos', [
        { id: 'pl-ok', activista_id: A, activista: nome(A), ronda: r, estado: 'por_supervisor', dias, criado_em: new Date().toISOString() },
        { id: 'pl-velho', activista_id: A, activista: nome(A) + ' VELHO', ronda: r - 1, estado: 'por_supervisor', dias, criado_em: new Date().toISOString() },
        { id: 'pl-outra', activista_id: B, activista: nome(B) + ' OUTRA', ronda: rondaEquipa(B) || 1, estado: 'por_supervisor', dias, criado_em: new Date().toISOString() }]);
      S.visiveis = [A]; LS.del('avisoPlanos');
      return { A, B, r, rb: rondaEquipa(B) } })()""")
    passo("0 rondas das equipas conhecidas", info["r"] and info["r"] >= 1, json.dumps(info))
    h = pg.evaluate("cartaoPlanos()")
    passo("1 plano da ronda já passada não aparece", "VELHO" not in h and "pl-ok" in h, "")
    passo("2 «por aprovar por si» só no plano da sua equipa", pg.evaluate("[planosPorMim().map(p => p.id)]")[0] == ["pl-ok"])
    pg.evaluate("window.__DM = window.DEMO; window.DEMO = null; avisoPlanos(); window.DEMO = window.__DM"); pg.wait_for_timeout(600)
    t = pg.inner_text("#folha") if pg.locator("#folha.on").count() else ""
    passo("3 ao abrir: ecrã com os planos por aprovar", T[0] in t and T[1] in t and pg.locator("#pl-aviso").count() == 1 and "VELHO" not in t and "OUTRA" not in t, t[:200].replace("\n", " | "))
    pg.screenshot(path=f"/home/claude/rega-test/v250_a_{LG}.png")
    pg.click("#folha .chip"); pg.wait_for_timeout(600)
    passo("4 «Ver e aprovar» abre o plano com o motivo de recusa", pg.locator("#pl-mot").count() == 1)
    pg.evaluate("fecharFolha(); window.DEMO = null; avisoPlanos(); window.DEMO = window.__DM"); pg.wait_for_timeout(500)
    passo("5 no mesmo dia não volta a aparecer", pg.locator("#folha.on").count() == 0)
    pg.evaluate("window.__TAR_ABERTAS = true; $('#hoje').innerHTML = cartaoMeuDia()"); pg.wait_for_timeout(300)
    k = pg.locator("#meu-dia details[data-k=pl]")
    passo("6 «O meu dia» com a linha dos planos por aprovar", k.count() == 1 and "VELHO" not in k.inner_text(), k.inner_text()[:120].replace("\n", " | ") if k.count() else "")
    # técnico: sem ecrã
    pg.evaluate("S.perfil = { ...S.perfil, papel: 'tecnico' }; LS.del('avisoPlanos'); window.DEMO = null; avisoPlanos(); window.DEMO = window.__DM"); pg.wait_for_timeout(400)
    passo("7 técnico não recebe o ecrã", pg.locator("#folha.on").count() == 0)
    passo("8 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']}")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
