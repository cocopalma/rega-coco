# v271 (28/11/2026, Valdo): Gestão › Mensagens › Enviadas agrupada, texto encolhido, só 7 dias, respostas por ver primeiro.
# Servidor simulado (nada sai para o servidor verdadeiro).
# Uso: python3 testes/teste_v271.py   ( LING=en / sw para as outras línguas)
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_nm = os.path.join(RAIZ, "testes", "node_modules")
NM = os.environ.get("NM", _nm if os.path.isdir(_nm) else "/home/claude/rega-test/node_modules")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8873", "--directory", RAIZ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1 = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"; VALDO = "33333333-3333-3333-3333-333333333333"
M1 = "aaaaaaaa-0000-0000-0000-000000000001"; M2 = "aaaaaaaa-0000-0000-0000-000000000002"
agora = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).replace(microsecond=0).isoformat() + "Z"
LING = os.environ.get("LING", "pt"); falhas = []; SHOT = os.environ.get("SHOT")
def foto(pg, n):
    if SHOT: pg.screenshot(path=os.path.join(SHOT, n))
def verif(c, txt):
    print(("OK  " if c else "FALHA ") + txt)
    if not c: falhas.append(txt)
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Olumbe", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None}]
MSGS = [{"id": M1, "texto": "Bom dia. O campo PR25810452-1 fica em Namanengo ou em Olumbe?", "criada_em": agora, "vista_em": None, "de": "Etevaldo Cheveia (Valdo)", "resposta_a": None, "resposta_a_texto": None},
        {"id": M2, "texto": "Segunda mensagem de teste.", "criada_em": agora, "vista_em": None, "de": "Etevaldo Cheveia (Valdo)", "resposta_a": None, "resposta_a_texto": None}]
ENVIADAS = [{"id": M1, "texto": "Bom dia. O campo fica em Namanengo ou em Olumbe?", "criada_em": agora, "vista_em": agora, "para": "Manuel Felix Shella", "papel": "tecnico", "resposta_a_texto": None,
             "respostas": [{"id": "r1", "texto": "Fica em Olumbe.", "criada_em": agora, "vista_em": None}]}]


import datetime as _d
def ha(dias): return (_d.datetime.now(_d.timezone.utc).replace(tzinfo=None, microsecond=0) - _d.timedelta(days=dias)).isoformat() + "Z"
TXT = "Lembrete: o inventário de plantas mórbidas é para fazer em todos os campos que visitam (pedido do Paulo Dias). Na app: ficha do campo › Inventário de plantas mórbidas. Escolha o percurso, verifique o número de plantas e tire as duas fotografias. Obrigado."
ENVIADAS = [
  {"id": "e1", "texto": TXT, "criada_em": ha(1), "vista_em": None, "para": "Nuro Antonio Culete", "papel": "supervisor", "resposta_a_texto": None, "respostas": []},
  {"id": "e2", "texto": TXT, "criada_em": ha(1), "vista_em": ha(1), "para": "Guidion Cristovao", "papel": "tecnico", "resposta_a_texto": None, "respostas": []},
  {"id": "e3", "texto": TXT, "criada_em": ha(1), "vista_em": None, "para": "Gelson Manuel", "papel": "tecnico", "resposta_a_texto": None, "respostas": []},
  {"id": "e4", "texto": TXT, "criada_em": ha(1), "vista_em": ha(0), "para": "Manuel Felix Shella", "papel": "tecnico", "resposta_a_texto": None, "respostas": [{"id": "r4", "texto": "Feito em 3 campos.", "criada_em": ha(0), "vista_em": None}]},
  {"id": "e5", "texto": "Mensagem só ao Raul.", "criada_em": ha(3), "vista_em": ha(3), "para": "Raul Miquilage", "papel": "supervisor", "resposta_a_texto": None, "respostas": [{"id": "r5", "texto": "Ok.", "criada_em": ha(3), "vista_em": ha(3)}]},
  {"id": "e6", "texto": "Mensagem antiga.", "criada_em": ha(12), "vista_em": ha(12), "para": "Raul Miquilage", "papel": "supervisor", "resposta_a_texto": None, "respostas": []},
]
MINHAS = [{"id": "r4", "texto": "Feito em 3 campos.", "criada_em": ha(0), "vista_em": None, "de": "Manuel Felix Shella", "resposta_a": "e4", "resposta_a_texto": TXT[:160]}]
def correr():
    rec = {}; erros = []
    def guarda(k, v): rec.setdefault(k, []).append(v)
    def mock(route):
        r = route.request; u = r.url
        ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
        if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
        if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Pessoa Teste", "papel": "gestor", "activista_id": None, "gere_acessos": True, "ve_tudo": False})
        if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Olumbe", "tecnico": "Pessoa Teste", "supervisor": "Pessoa Teste", "activo": True, "equipa_tamanho": 5}])
        if "/rest/v1/areas" in u: return ok(areas)
        if "/rpc/minhas_mensagens" in u: return ok(MINHAS)
        if "/rpc/mensagem_vista" in u: guarda("vista", json.loads(r.post_data)); return ok(True)
        if "/rpc/destinatarios_mensagem" in u: return ok([{"id": VALDO, "nome": "Manuel Felix Shella", "papel": "tecnico"}])
        if "/rpc/mensagens_enviadas" in u: return ok(ENVIADAS)
        if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
        if "/rpc/sugestoes_lista" in u: return ok({"sugestoes": [], "problemas": []})
        if "/rpc/meu_dia" in u: return ok(None)
        return ok([])
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
        ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
        if False:
            ctx.add_init_script("try{localStorage.setItem('rega.jornada', JSON.stringify({id:'j1', data: new Date().toLocaleDateString('sv-SE'), pessoas: 4}))}catch(e){}")
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
        ctx.route("**/unpkg.com/leaflet-rotate@0.2.8/**", lambda r: r.fulfill(path=f"{NM}/leaflet-rotate/dist/leaflet-rotate-src.js" if r.request.url.endswith(".js") else f"{NM}/leaflet-rotate/dist/leaflet-rotate.css", content_type="application/javascript" if r.request.url.endswith(".js") else "text/css"))
        ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
        ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
        ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
        ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
        ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
        pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e) + " @ " + (e.stack or "")[:300])); pg.on("dialog", lambda d: d.accept())
        pg.goto("http://localhost:8873/"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.fill("#l-user", "x"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
        print(f"--- gestor ({LING}) ---")
        pg.evaluate("document.querySelector('#folha.on') && fecharFolha()"); pg.wait_for_timeout(300)
        pg.evaluate("mudar('gestao')"); pg.wait_for_timeout(2300); pg.evaluate("document.querySelector('#gac-msg') && (document.querySelector('#gac-msg').open = true)"); pg.wait_for_timeout(1500)
        G = pg.locator("#gm-lista details.gm-g")
        verif(G.count() == 2, f"1 só 2 cartões nos últimos 7 dias (a mesma mensagem a 4 pessoas num só; a de 12 dias escondida) ({G.count()})")
        g0 = G.nth(0)
        verif(g0.get_attribute("open") is not None and "nova" in (g0.get_attribute("class") or ""), "2 o cartão com resposta por ver vem primeiro e aberto")
        t0 = g0.inner_text()
        verif(("4 pessoas" in t0 or "4 people" in t0 or "4 watu" in t0) and "2/4" in t0, f"3 «Para 4 pessoas» e «Vistas: 2/4» ({t0[:200]!r})")
        verif("Feito em 3 campos." in t0, "4 a resposta aparece no cartão aberto")
        verif(g0.locator(".gm-p").count() == 4, "5 dentro, uma linha por pessoa")
        g1 = G.nth(1)
        verif(g1.get_attribute("open") is None, "6 o cartão sem respostas por ver fica fechado")
        h = pg.evaluate("(() => { const e = document.querySelectorAll('#gm-lista .gm-g')[1].querySelector('.gm-txt'); return getComputedStyle(e).webkitLineClamp })()")
        verif(str(h) == "2", f"7 texto encolhido a 2 linhas no cartão fechado ({h})")
        verif(pg.locator("#gm-mais").count() == 1, "8 botão «Ver mais antigas (1)»")
        pg.evaluate("document.querySelector('#gm-lista').scrollIntoView()"); foto(pg, "v271_1.png")
        pg.click("#gm-mais"); pg.wait_for_timeout(300)
        verif(pg.locator("#gm-lista details.gm-g").count() == 3, "9 «Ver mais antigas» mostra a de 12 dias")
        pg.locator("#gm-lista details.gm-g").nth(0).locator("button[onclick^=vistaRespGestao]").first.click(); pg.wait_for_timeout(1500)
        vs = rec.get("vista", [])
        verif(len(vs) == 1 and vs[0]["p_id"] == "r4", f"10 «OK» na resposta marca-a como vista ({vs})")
        verif("nova" not in (pg.locator("#gm-lista details.gm-g").nth(0).get_attribute("class") or ""), "11 o cartão deixa de ter respostas por ver")
        if LING != "pt":
            tt = pg.inner_text("#gm-lista")
            verif("pessoas" not in tt and "Vistas:" not in tt and "Ver mais antigas" not in tt and "Esconder as mais antigas" not in tt, f"12 traduzido ({tt[:160]!r})")
        foto(pg, "v271_2.png")
        print("erros JS:", erros)
        if erros: falhas.append("erros JS")
        b.close()

correr()
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)}): {falhas}")
