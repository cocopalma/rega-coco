# v259 (23/11/2026, Valdo): Gestão em cartões que abrem ao tocar (cascata), um de cada vez, com o número no cartão fechado.
# Servidor simulado (nada sai para o servidor verdadeiro).
# Uso: python3 testes/teste_v259.py   (PAPEIS=gestor,dalmar; LING=en / sw para as outras línguas; SHOT=pasta para capturas)
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

HOJE = datetime.date.today().isoformat()
EQ = {"dia": HOJE, "agora": HOJE + "T10:00:00", "hora_chegada": "06:30", "monitoria_pausa": True,
      "pessoas": [{"id": "p1", "nome": "Tecnico Um", "papel": "tecnico", "equipas": ["Activista Um"], "motivos": [], "alertas": [], "medicoes": [], "sem_equipa": 2,
                   "dias": [{"data": HOJE, "sem_rega": ["Activista Um"], "fecho": None, "chegadas": [], "monitoria": 0, "fora": 0, "acomp": 0}]},
                  {"id": "p2", "nome": "Supervisor Dois", "papel": "supervisor", "equipas": ["Activista Dois"], "motivos": [], "alertas": [], "medicoes": [], "sem_equipa": 0,
                   "dias": [{"data": HOJE, "sem_rega": [], "fecho": "09:00", "chegadas": [], "monitoria": 0, "fora": 0, "acomp": 1}]}]}
SUG = {"sugestoes": [{"id": "s1", "texto": "Sugestão um", "estado": "nova", "criada_em": agora, "quem": "A"}, {"id": "s2", "texto": "Sugestão dois", "estado": "nova", "criada_em": agora, "quem": "B"},
                     {"id": "s3", "texto": "Sugestão três", "estado": "feita", "criada_em": agora, "quem": "C"}], "problemas": []}
GEST = {"activistas": [{"id": A1, "nome": "Activista Um", "tem_login": True, "utilizador": "um", "activo": True}, {"id": "a2", "nome": "Activista Dois", "tem_login": False, "activo": True, "comunidade_principal": "Olumbe"}],
        "utilizadores": [{"id": UID, "nome": "Pessoa Teste", "papel": "gestor", "utilizador": "pt"}], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}}

def correr(caso):
    PAPEL = "gestor"
    erros = []
    def mock(route):
        r = route.request; u = r.url
        ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
        if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
        if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Pessoa Teste", "papel": PAPEL, "activista_id": None, "gere_acessos": caso == "gestor", "ve_tudo": False})
        if "/rest/v1/activistas" in u: return ok([{"id": A1, "nome": "Activista Um", "comunidade_principal": "Olumbe", "tecnico": "Tecnico Um", "supervisor": "Supervisor Dois", "activo": True, "equipa_tamanho": 5}])
        if "/rest/v1/areas" in u: return ok(areas)
        if "/rest/v1/pessoas_acesso" in u: return ok([{"nome": "Cliente Novo", "entidade": "X", "papel": "cliente", "utilizador": None}])
        if "/rpc/minhas_mensagens" in u: return ok([])
        if "/rpc/destinatarios_mensagem" in u: return ok([{"id": VALDO, "nome": "Tecnico Um", "papel": "tecnico"}] if caso == "gestor" else None)
        if "/rpc/mensagens_enviadas" in u: return ok([] if caso == "gestor" else None)
        if "/rpc/gestao_equipa_campo" in u: return ok(EQ if caso == "gestor" else None)
        if "/functions/v1/gestor-activistas" in u: return ok(GEST)
        if "/rpc/estado_ronda" in u: return ok([{"area_id": "PR1-1", "ultima_rega": None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False}])
        if "/rpc/sugestoes_lista" in u: return ok(SUG)
        if "/rpc/meu_dia" in u: return ok(None)
        if "/rpc/" in u: return ok([])
        return ok([])
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
        ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
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
        print(f"--- {caso} ({LING}) ---")
        pg.evaluate("mudar('gestao')"); pg.wait_for_timeout(3000)
        ks = pg.eval_on_selector_all("#gestao-ac > details.gac", "l => l.map(d => d.dataset.k)")
        abertos = pg.eval_on_selector_all("#gestao-ac > details.gac[open]", "l => l.map(d => d.dataset.k)")
        nb = lambda k: pg.inner_text(f"#gac-n-{k}") if pg.locator(f"#gac-n-{k}").count() else None
        foto(pg, f"1_gestao_{caso}_{LING}.png")
        if caso == "gestor":
            verif(ks == ["eq", "msg", "sug", "acessos", "conf", "sim"], f"1 seis cartões pela ordem ({ks})")
            verif(abertos == ["eq"], f"2 só a «Equipa de campo» aberta ao entrar ({abertos})")
            verif(nb("eq") == "1", f"3 número na Equipa de campo = pessoas com coisas por fazer ({nb('eq')})")
            verif(nb("sug") == "2", f"4 número nas Sugestões = novas ({nb('sug')})")
            verif(nb("acessos") == "2", f"5 número nos Acessos = 1 activista sem login + 1 outro acesso por criar ({nb('acessos')})")
            verif(nb("conf") == "" and nb("sim") == "", "6 Configurações e Simulação sem número")
            verif(not pg.locator("#g-act").is_visible(), "7 o conteúdo dos Acessos está escondido com o cartão fechado")
            pg.click("#gac-acessos > summary"); pg.wait_for_timeout(600)
            abertos = pg.eval_on_selector_all("#gestao-ac > details.gac[open]", "l => l.map(d => d.dataset.k)")
            verif(abertos == ["acessos"], f"8 abrir os Acessos fecha a Equipa de campo ({abertos})")
            verif(pg.locator("#g-act").is_visible() and pg.locator("#c-papel").is_visible(), "9 Criar login e Outros acessos dentro dos Acessos")
            foto(pg, f"2_acessos_{LING}.png")
            pg.click("#gac-msg > summary"); pg.wait_for_timeout(1200)
            verif(pg.locator("#gm-para").is_visible() and not pg.locator("#g-act").is_visible(), "10 Mensagens abre e Acessos fecha")
            h2 = pg.eval_on_selector("#g-msg h2", "e => getComputedStyle(e).display")
            verif(h2 == "none", "11 o título repetido do cartão fica escondido")
            pg.click("#gac-sim > summary"); pg.wait_for_timeout(500)
            verif(pg.locator("#gestao-demo .item").count() >= 7, "12 Modo simulação com as funções")
            pg.click("#gac-conf > summary"); pg.wait_for_timeout(500)
            verif(pg.locator("#k-quem").is_visible() and pg.locator("#m-n").is_visible() and pg.locator("#g-visitas").is_visible(), "13 Configurações: coberturas, monitoria, quem viu o painel")
            pg.evaluate("mudar('mapa')"); pg.wait_for_timeout(300); pg.evaluate("mudar('gestao')"); pg.wait_for_timeout(1500)
            abertos = pg.eval_on_selector_all("#gestao-ac > details.gac[open]", "l => l.map(d => d.dataset.k)")
            verif(abertos == ["conf"], f"14 ao voltar à Gestão fica aberto o último cartão ({abertos})")
            pg.click("#gac-conf > summary"); pg.wait_for_timeout(300)
            abertos = pg.eval_on_selector_all("#gestao-ac > details.gac[open]", "l => l.map(d => d.dataset.k)")
            verif(abertos == [], f"15 tocar no cartão aberto fecha-o ({abertos})"); foto(pg, f"3_fechados_{LING}.png")
            if LING != "pt":
                t = pg.inner_text("#gestao-ac")
                verif(not any(x in t for x in ["Equipa de campo", "Sugestões e problemas", "Configurações", "Modo simulação", "Coberturas, monitoria"]), f"16 traduzido ({t[:120]!r})")
        else:
            verif(ks == ["acessos", "conf", "sim"], f"D1 gestor sem acessos (Dalmar): só Acessos, Configurações e Simulação ({ks})")
            verif(abertos == ["acessos"], f"D2 abre os Acessos ({abertos})")
            verif(pg.locator("#g-act").count() == 0 and "gestor principal" in pg.inner_text("#gac-c-acessos") or LING != "pt", "D3 sem criar login, com o aviso")
            verif(nb("acessos") == "", "D4 sem número nos Acessos")
        print("erros JS:", erros)
        if erros: falhas.append(f"{caso}: erros JS")
        b.close()

for caso in os.environ.get("PAPEIS", "gestor,dalmar").split(","): correr(caso)
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)}): {falhas}")
