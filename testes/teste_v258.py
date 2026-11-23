# v258 (23/11/2026, Valdo): mensagens do gestor principal a uma pessoa, com resposta.
# Servidor simulado (nada sai para o servidor verdadeiro).
# Uso: python3 testes/teste_v258.py   (PAPEIS=tecnico,activista,cliente,gestor,dalmar; LING=en / sw para as outras línguas)
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_nm = os.path.join(RAIZ, "testes", "node_modules")
NM = os.environ.get("NM", _nm if os.path.isdir(_nm) else "/home/claude/rega-test/node_modules")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8872", "--directory", RAIZ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
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

def correr(caso):
    PAPEL = "gestor" if caso == "dalmar" else caso
    rec = {}; erros = []
    def guarda(k, v): rec.setdefault(k, []).append(v)
    def mock(route):
        r = route.request; u = r.url
        ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
        if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
        if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Pessoa Teste", "papel": PAPEL, "activista_id": A1 if PAPEL == "activista" else None, "gere_acessos": caso == "gestor", "ve_tudo": False})
        if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Olumbe", "tecnico": "Pessoa Teste", "supervisor": "Pessoa Teste", "activo": True, "equipa_tamanho": 5}])
        if "/rest/v1/areas" in u: return ok(areas)
        if "/rpc/meus_activistas" in u: return ok([A1])
        if "/rpc/minhas_comunidades" in u: return ok(["Olumbe"])
        if "/rpc/minhas_mensagens" in u: return ok([] if PAPEL == "gestor" else MSGS)
        if "/rpc/mensagem_vista" in u: guarda("vista", json.loads(r.post_data)); return ok(True)
        if "/rpc/responder_mensagem" in u: guarda("resp", json.loads(r.post_data)); return ok({"id": "x", "repetido": False})
        if "/rpc/destinatarios_mensagem" in u: return ok([{"id": VALDO, "nome": "Manuel Felix Shella", "papel": "tecnico"}, {"id": A1, "nome": "Activista Um", "papel": "activista"}] if caso == "gestor" else None)
        if "/rpc/mensagens_enviadas" in u: return ok(ENVIADAS if caso == "gestor" else None)
        if "/rpc/enviar_mensagem" in u: guarda("env", json.loads(r.post_data)); return ok({"id": "y", "repetido": False})
        if "/functions/v1/gestor-activistas" in u: return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
        if "/rpc/estado_ronda" in u: return ok([{"area_id": "PR1-1", "ultima_rega": None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False}])
        if "/rpc/sugestoes_lista" in u: return ok({"sugestoes": [], "problemas": []})
        if "/rpc/meu_dia" in u: return ok(None)
        if "/rpc/" in u: return ok([])
        return ok([])
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
        ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
        if PAPEL == "activista":
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
        pg.goto("http://localhost:8872/"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.fill("#l-user", "x"); pg.fill("#l-pin", "123456" if PAPEL == "activista" else "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
        print(f"--- {caso} ({LING}) ---")

        if PAPEL != "gestor":
            foto(pg, f"1_aviso_{caso}.png")
            verif(pg.locator("#msg-aviso").count() == 1, "1 ao abrir a app aparecem as mensagens por ver")
            t = pg.inner_text("#folha-c") if pg.locator("#folha-c").count() else ""
            verif("Namanengo" in t and "Etevaldo" in t, "2 mostra o texto e quem mandou")
            if LING != "pt": verif("Mensagem para si" not in t and "Mensagens para si" not in t and "Responder" not in t, f"2b traduzido ({t[:80]!r})")
            pg.evaluate("fecharFolha()"); pg.wait_for_timeout(300)
        if PAPEL in ("tecnico", "activista"):
            pg.evaluate("mudar('hoje')"); pg.wait_for_selector("#hoje-msg", timeout=8000)
            verif(pg.locator("#hoje-msg .lin").count() == 2, "3 o Hoje mostra as 2 mensagens por ver")
            pg.evaluate(f"ecraResponder('{M1}')"); pg.wait_for_selector("#mr-txt")
            verif(pg.is_disabled("#mr-env"), "4 «Enviar a resposta» desactivado sem texto")
            pg.fill("#mr-txt", "Fica em Olumbe."); foto(pg, f"2_responder_{caso}.png"); pg.click("#mr-env"); pg.wait_for_timeout(2500)
            rs = rec.get("resp", [])
            verif(len(rs) == 1 and rs[0]["p_msg"] == M1 and rs[0]["p_texto"] == "Fica em Olumbe.", f"5 resposta enviada ao servidor ({rs})")
            verif(pg.locator("#hoje-msg .lin").count() == 1, "6 a mensagem respondida sai do Hoje")
            pg.evaluate(f"mensagemVista('{M2}')"); pg.wait_for_timeout(2500)
            vs = rec.get("vista", [])
            verif(len(vs) == 1 and vs[0]["p_id"] == M2, f"7 «OK» marca a mensagem como vista no servidor ({vs})")
            verif(pg.locator("#hoje-msg").count() == 0, "8 sem mensagens por ver, o cartão sai")
            pg.evaluate("carregarMensagens()"); pg.wait_for_timeout(800)
            verif(pg.locator("#hoje-msg").count() == 0, "9 ao voltar a ler do servidor, as mensagens vistas no telefone não voltam")
        if PAPEL == "gestor":
            pg.evaluate("mudar('gestao')"); pg.wait_for_timeout(800); pg.evaluate("typeof abaGestao === 'function' && abaGestao('acessos')"); pg.wait_for_timeout(2500)
            if caso == "gestor":
                verif(pg.locator("#gm-para").count() == 1, "G1 Gestão › Mensagens para o gestor principal")
                g = pg.inner_text("#g-msg")
                verif("Fica em Olumbe." in g and ("✓" in g), f"G2 lista das enviadas com a resposta e «Vista» ({g[-160:]!r})")
                pg.select_option("#gm-para", VALDO); pg.fill("#gm-txt", "Obrigado, Shella."); pg.evaluate("document.querySelector('#g-msg').scrollIntoView()"); foto(pg, "3_gestao.png")
                verif(not pg.is_disabled("#gm-env"), "G3 «Enviar» activo com pessoa e texto")
                pg.click("#gm-env"); pg.wait_for_timeout(1500)
                e = rec.get("env", [])
                verif(len(e) == 1 and e[0]["p_para"] == VALDO and e[0]["p_texto"] == "Obrigado, Shella.", f"G4 mensagem enviada ({e})")
                if LING != "pt": verif("Enviadas" not in g and "Escolha a pessoa" not in pg.inner_text("#g-msg"), "G5 traduzido")
            else:
                verif(pg.locator("#g-msg").count() == 0, "D1 gestor sem acessos (Dalmar) não vê Mensagens")
        print("erros JS:", erros)
        if erros: falhas.append(f"{caso}: erros JS")
        b.close()

for caso in os.environ.get("PAPEIS", "tecnico,activista,cliente,gestor,dalmar").split(","): correr(caso)
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)}): {falhas}")
