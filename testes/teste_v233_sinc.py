# Passo A e B do ponto 1 do MELHORIAS.md (cópia de teste, 10/11/2026; ainda sem número de versão).
# Caso de 02/11: o servidor recusa os constrangimentos de uma rega (23514). As outras regas e o início do dia seguem;
# a recusada fica no telefone, marcada; o botão do topo fica vermelho e abre «Registos por enviar» (sem «Apagar»);
# depois de o servidor aceitar, «Tentar de novo agora» envia-a. LING=en / sw.
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
NM = os.environ.get("NM", "/home/claude/rega-test/node_modules")
APP = os.environ.get("APP", "/home/claude/rega-coco")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8864", "--directory", APP], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; HOJE = datetime.date.today().isoformat()
areas = [{"id": f"PR{i}-1", "pr": f"PR{i}", "area_n": 1, "comunidade": "Farol", "produtor": f"Produtor {i}", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340 + i / 1000, "activista_id": ACT, "activista_proposto": None} for i in (1, 2, 3)]
estado = {"recusar": True}; rec = {"regas": [], "constr": [], "jornadas": [], "problemas": []}; erros = []
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": "u-act", "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": "u-act", "nome": "Activista Um", "papel": "activista", "activista_id": ACT})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Um", "comunidade_principal": "Farol", "equipa_tamanho": 3, "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rest/v1/registos_rega" in u and r.method == "POST":
        b = json.loads(r.post_data); b = b if isinstance(b, list) else [b]
        rec["regas"] += [x["id"] for x in b]
        if any("_recusa" in x for x in b): rec.setdefault("fuga", True)
        return route.fulfill(status=201, body="")
    if "/rest/v1/constrangimentos" in u and r.method == "POST":
        b = json.loads(r.post_data)
        if estado["recusar"] and any(x.get("tipo") == "sem_agua_fonte" for x in b):
            return ok({"code": "23514", "details": None, "hint": None, "message": 'new row for relation "constrangimentos" violates check constraint "constrangimentos_tipo_check"'}, 400)
        rec["constr"] += [x["registo_id"] for x in b]; return route.fulfill(status=201, body="")
    if "/rest/v1/jornadas" in u and r.method == "POST": rec["jornadas"].append(1); return route.fulfill(status=201, body="")
    if "/rpc/registar_problemas" in u: rec["problemas"] += [x.get("tipo") for x in json.loads(r.post_data).get("p_lista", [])]; return ok(None)
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/" in u: return ok([])
    if "/rest/v1/" in u: return ok([])
    return ok({})
falhas = []
def verif(c, txt):
    print(("OK  " if c else "FALHA ") + txt)
    if not c: falhas.append(txt)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    LING = os.environ.get("LING", "pt")
    if LING != "pt": ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
    pg.goto(f"http://localhost:8864/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "act"); pg.fill("#l-pin", "123987"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    # três regas e um início do dia no telefone; a 2.ª tem o constrangimento que o servidor ainda não aceita
    pg.evaluate("""() => { const h = hojeISO(), base = { activista_id: '%s', data: h, ronda: 1, teste: false, pessoas: 3, campo_fechado: true };
      LS.set('fila', [{ ...base, id: 'r1', area_id: 'PR1-1', plantas_regadas: 70 },
                      { ...base, id: 'r2', area_id: 'PR2-1', plantas_regadas: 40, campo_fechado: false, constr: [{ id: 'c2', tipo: 'sem_agua_fonte' }] },
                      { ...base, id: 'r3', area_id: 'PR3-1', plantas_regadas: 70 }]);
      LS.set('filaJ', [{ id: 'j1', activista_id: '%s', data: h, pessoas: 3 }]); actSync(); }""" % (ACT, ACT))
    pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    fila = pg.evaluate("LS.get('fila', []).map(x => [x.id, x._recusa && x._recusa.codigo])")
    verif(fila == [["r2", "23514"]], f"1 só a rega recusada fica no telefone, marcada ({fila})")
    verif("r1" in rec["regas"] and "r3" in rec["regas"] and rec["jornadas"], "1b a 1.ª e a 3.ª rega e o início do dia chegaram ao servidor")
    verif(not rec.get("fuga"), "1c a marca da recusa não vai para o servidor")
    verif("envio_recusado" in rec["problemas"], f"1d o problema chega ao servidor ({rec['problemas']})")
    bt = pg.inner_text("#h-sync"); cls = pg.get_attribute("#h-sync", "class")
    verif("recusa" in cls and "pend" not in cls, f"2 botão do topo vermelho ({cls})")
    if LING == "pt": verif(bt == "1 por enviar · 1 recusado(s)", f"2b texto do botão ({bt})")
    else: verif("recusado" not in bt and ("refused" in bt or "zimekataliwa" in bt), f"2b texto do botão traduzido ({bt})")
    pg.click("#h-sync"); pg.wait_for_selector("#pe-lista", timeout=5000); txt = pg.inner_text("#folha-c")
    verif("Produtor 2" in txt and "23514" in txt, "3 o ecrã mostra o campo e o código do servidor")
    if LING == "pt": verif("Recusados pelo servidor" in txt and "tipo de constrangimento novo" in txt and "Mostre este ecrã ao técnico" in txt, "3b explicação em palavras simples")
    else: verif("Recusados pelo servidor" not in txt and "Mostre este ecrã" not in txt, "3b ecrã traduzido")
    verif(pg.locator("#folha-c button", has_text="Apagar").count() == 0 and pg.locator("#folha-c button").count() == 1, "3c sem botão para apagar (só «Tentar de novo agora»)")
    pg.screenshot(path=f"{os.environ.get('SAIDA', '/home/claude/rega-test')}/v233_sinc_{LING}.png")
    estado["recusar"] = False
    pg.click("#pe-tentar"); pg.wait_for_timeout(2500)
    verif(pg.evaluate("LS.get('fila', []).length") == 0 and "r2" in rec["constr"], "4 com o servidor corrigido, «Tentar de novo agora» envia a rega presa")
    verif("recusa" not in pg.get_attribute("#h-sync", "class"), "4b botão volta ao normal")
    verif(pg.locator("#pe-lista .msg.ok").count() == 1, "4c o ecrã diz que tudo foi enviado")
    print("erros JS:", erros)
    if erros: falhas.append("erros JS")
    b.close()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)})")
