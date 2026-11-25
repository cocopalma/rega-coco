# v260 (25/11/2026): cava-roda já no servidor que ficou no telefone sem as fotografias sai da fila (caso do Sitambur).
# Passo A e B do ponto 1 do MELHORIAS.md (cópia de teste, 10/11/2026; ainda sem número de versão).
# Caso de 02/11: o servidor recusa os constrangimentos de uma rega (23514). As outras regas e o início do dia seguem;
# a recusada fica no telefone, marcada; o botão do topo fica vermelho e abre «Registos por enviar» (sem «Apagar»);
# depois de o servidor aceitar, «Tentar de novo agora» envia-a. LING=en / sw.
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
NM = os.environ.get("NM", "/home/claude/rega-test/node_modules")
APP = os.environ.get("APP", "/home/claude/rega-coco")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8865", "--directory", APP], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
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
    if "/rpc/gravar_actividade" in u:
        b = json.loads(r.post_data)["p"]; rec.setdefault("act", []).append([b["id"], b.get("foto_entrada")])
        if b["id"] in ("a1",): return ok({"id": b["id"], "ja": True})
        if not b.get("foto_entrada"): return ok({"code": "P0001", "details": None, "hint": None, "message": "Faltam fotografias"}, 400)
        return ok({"id": b["id"]})
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
    pg.goto(f"http://localhost:8865/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "act"); pg.fill("#l-pin", "123987"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
    pg.evaluate("""() => { const h = new Date().toISOString(), base = { activista_id: '%s', area_id: 'PR1-1', motivo: 'tuk_tuk', entrada_em: h, saida_em: h, cavaroda: 10, mulching: 10, pessoas: 3, data: hojeISO(), fotos: ['entrada','durante','saida'] };
      LS.set('filaAct', [{ ...base, id: 'a1' }, { ...base, id: 'a2' }]); actSync(); }""" % ACT)
    pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    fila = pg.evaluate("LS.get('filaAct', []).map(x => [x.id, x._recusa && x._recusa.codigo])")
    verif(fila == [["a2", "FOTO"]], f"1 o registo já no servidor sai do telefone; o outro sem fotografias fica recusado ({fila})")
    verif(["a1", ""] in rec.get("act", []), f"2 a app perguntou ao servidor sem as fotografias ({rec.get('act')})")
    print("erros JS:", erros)
    verif(not erros, "3 sem erros JS")
    b.close()
srv.terminate()
print("FALHAS:", falhas) if falhas else print("TUDO OK")
