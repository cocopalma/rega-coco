# v275 (28/11/2026, Valdo: "As 2."): som e vibração das mensagens com a app aberta e avisos (Web Push) com a app fechada.
# Servidor simulado (nada sai para o servidor verdadeiro).
# Uso: python3 testes/teste_v275.py   ( LING=en / sw para as outras línguas)
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_nm = os.path.join(RAIZ, "testes", "node_modules")
NM = os.environ.get("NM", _nm if os.path.isdir(_nm) else "/home/claude/rega-test/node_modules")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8876", "--directory", RAIZ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
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
    PAPEL = "activista" if caso == "nao" else caso
    rec = {}; erros = []
    def guarda(k, v): rec.setdefault(k, []).append(v)
    NOVA = [False]
    def mock(route):
        r = route.request; u = r.url
        ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
        if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
        if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Pessoa Teste", "papel": PAPEL, "activista_id": A1 if PAPEL == "activista" else None, "gere_acessos": caso == "gestor", "ve_tudo": False})
        if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Olumbe", "tecnico": "Pessoa Teste", "supervisor": "Pessoa Teste", "activo": True, "equipa_tamanho": 5}])
        if "/rest/v1/areas" in u: return ok(areas)
        if "/rpc/meus_activistas" in u: return ok([A1])
        if "/rpc/minhas_comunidades" in u: return ok(["Olumbe"])
        if "/rpc/minhas_mensagens" in u: return ok(MSGS + ([M3D] if NOVA[0] else []))
        if "/rpc/push_chave_publica" in u: return ok("BPo_5BAqmBpR36th1IfQbXS7uCQIP4pfRIj2_rQPOm4wvMY--aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"[:87])
        if "/rpc/gravar_push" in u: guarda("gravar", json.loads(r.post_data)); return ok({"ok": True})
        if "/rpc/remover_push" in u: guarda("remover", json.loads(r.post_data)); return ok({"ok": True})
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
        ctx.add_init_script(INIT)
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
        pg.goto("http://localhost:8876/"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.fill("#l-user", "x"); pg.fill("#l-pin", "123456" if PAPEL == "activista" else "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
        print(f"--- {caso} ({LING}) ---")
        if caso == "nao":
            pg.evaluate("fecharFolha()"); pg.evaluate("mudar('hoje')"); pg.wait_for_selector("#hoje-push", timeout=8000)
            pg.click("#hoje-push .chip"); pg.wait_for_timeout(500)
            verif(pg.locator("#hoje-push").count() == 0, "N1 «Agora não» tira o cartão")
            pg.reload(); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha()"); pg.evaluate("mudar('hoje')"); pg.wait_for_timeout(1500)
            verif(pg.locator("#hoje-push").count() == 0, "N2 e não volta ao abrir outra vez")
            pg.evaluate("ecraDefinicoes()"); pg.wait_for_selector("#def-push")
            verif(pg.locator("#def-push .btn").count() == 1, "N3 Definições: botão «Ligar os avisos das mensagens»")
            pg.evaluate("window.__resp = 'denied'"); pg.click("#def-push .btn"); pg.wait_for_timeout(800)
            t = pg.inner_text("#folha-c"); foto(pg, f"3_bloqueado_{LING}.png")
            verif("cocopalma.github.io" in t and len(rec.get("gravar", [])) == 0, "N4 recusado: mostra como desbloquear e não grava nada")
            if LING != "pt": verif("avisos" not in t and "Notificações" not in t and "Abra o Chrome" not in t, f"N4b traduzido ({t[:90]!r})")
            verif(not erros, f"N5 sem erros de JavaScript {erros[:2]}")
            b.close(); return
        v0 = pg.evaluate("window.__vib || 0")
        verif(v0 == 1, f"1 ao abrir, as mensagens novas tocam/vibram uma vez ({v0})")
        verif(pg.evaluate("(JSON.parse(localStorage.getItem('rega.msgSom')||'[]')).length") == 2, "1b as 2 mensagens ficam marcadas como já avisadas")
        pg.evaluate("fecharFolha()"); pg.reload(); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
        verif(pg.evaluate("window.__vib || 0") == 0, "2 ao abrir outra vez, as mesmas mensagens não tocam de novo")
        pg.evaluate("fecharFolha()"); pg.evaluate("mudar('hoje')"); pg.wait_for_selector("#hoje-push", timeout=8000)
        t = pg.inner_text("#hoje-push"); foto(pg, f"1_cartao_{caso}.png")
        verif(pg.locator("#hoje-push button").count() == 2, "3 Hoje: cartão «Ligar os avisos das mensagens» com 2 botões")
        if LING != "pt": verif("avisos" not in t and "Agora não" not in t, f"3b traduzido ({t[:70]!r})")
        # «Ligar os avisos»: autorização dada e subscrição guardada no servidor
        pg.click("#hoje-push .btn"); pg.wait_for_timeout(1500)
        g = rec.get("gravar", [])
        verif(len(g) == 1 and g[0]["p_endpoint"].startswith("https://") and g[0]["p_p256dh"] and g[0]["p_auth"] and g[0]["p_lingua"] == LING, f"4 subscrição gravada no servidor ({g[:1]})")
        verif(pg.locator("#hoje-push").count() == 0, "5 o cartão sai depois de ligar os avisos")
        verif(pg.evaluate("window.__vib") == 1, "5b toca o som ao ligar (para a pessoa o conhecer)")
        # ⚙️ Definições
        pg.evaluate("ecraDefinicoes()"); pg.wait_for_selector("#def-push"); d = pg.inner_text("#def-push"); foto(pg, f"2_definicoes_{caso}.png")
        verif(("ligados" in d) if LING == "pt" else ("on" in d or "zimewashwa" in d), f"6 Definições: avisos ligados ({d!r})")
        pg.evaluate("fecharFolha()")
        # abrir outra vez no mesmo dia: não volta a gravar
        pg.reload(); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
        verif(len(rec.get("gravar", [])) == 1, "7 no mesmo dia não grava a subscrição outra vez")
        pg.evaluate("localStorage.removeItem('rega.pushEm')"); pg.reload(); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500)
        verif(len(rec.get("gravar", [])) == 2, "7b noutro dia (sem rega.pushEm) renova em silêncio")
        # mensagem nova chega por push com a app aberta (o service worker avisa a app)
        pg.evaluate("fecharFolha()"); NOVA[0] = True; v1 = pg.evaluate("window.__vib || 0")
        pg.evaluate(f"navigator.serviceWorker.dispatchEvent(new MessageEvent('message', {{data: {{tipo: 'mensagem', id: '{M3}'}}}}))"); pg.wait_for_timeout(1500)
        verif(pg.evaluate("window.__vib || 0") == v1 + 1, "8 mensagem nova por push com a app aberta: toca/vibra")
        verif(pg.locator("#msg-aviso").count() == 1 and "Nova mensagem" in pg.inner_text("#msg-aviso"), "8b e mostra a mensagem nova")
        pg.evaluate("fecharFolha()")
        # Sair: os avisos deixam de vir para este telefone
        pg.evaluate("sair()"); pg.wait_for_timeout(2500)
        verif(len(rec.get("remover", [])) == 1, "9 ao sair, a subscrição sai do servidor")
        verif(not erros, f"10 sem erros de JavaScript {erros[:2]}")
        b.close()

def correr_nao(caso):
    pass

INIT = """
(() => {
  Object.defineProperty(Navigator.prototype, 'vibrate', { value: function () { window.__vib = (window.__vib || 0) + 1; return true; }, configurable: true });
  const sub = { endpoint: 'https://fcm.googleapis.com/fcm/send/teste123', toJSON() { return { endpoint: this.endpoint, keys: { p256dh: 'BPo_5BAqmBpR36th1IfQbXS7uCQIP4pfRIj2_rQPOm4w', auth: 'aaaaaaaaaaaaaaaaaaaaaa' } }; }, unsubscribe() { window.__unsub = 1; return Promise.resolve(true); } };
  window.__perm = 'default';
  Object.defineProperty(Notification, 'permission', { get: () => window.__perm, configurable: true });
  Notification.requestPermission = () => { window.__perm = window.__resp || 'granted'; sessionStorage.setItem('__perm', window.__perm); return Promise.resolve(window.__perm); };
  window.__perm = sessionStorage.getItem('__perm') || 'default';
  if (window.PushManager) {
    PushManager.prototype.getSubscription = function () { return Promise.resolve(sessionStorage.getItem('__sub') ? sub : null); };
    PushManager.prototype.subscribe = function (o) { window.__subOpts = !!o.applicationServerKey; sessionStorage.setItem('__sub', '1'); return Promise.resolve(sub); };
  }
})();
"""
M3 = "aaaaaaaa-0000-0000-0000-000000000003"
M3D = {"id": M3, "texto": "Nova mensagem por push.", "criada_em": agora, "vista_em": None, "de": "Etevaldo Cheveia (Valdo)", "resposta_a": None, "resposta_a_texto": None}
for c in os.environ.get("PAPEIS", "activista,tecnico,nao").split(","):
    correr(c)
srv.terminate()
print("FALHAS:", len(falhas)); [print(" -", f) for f in falhas]
sys.exit(1 if falhas else 0)
