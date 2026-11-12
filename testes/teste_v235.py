# v235 (12/11/2026, Valdo): «🚰 Fomos buscar água», ⚠️ de ritmo contra a mediana de todas as equipas, motivo «Fonte de água secou»
# ao voltar a pôr um campo na rega e papel «chefe de manutenção». Servidor simulado (nada sai para o servidor verdadeiro).
# Uso: python3 testes/teste_v235.py   (corre os 5 papéis; LING=en / sw para as outras línguas)
import json, subprocess, time, sys, os, datetime
from playwright.sync_api import sync_playwright
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_nm = os.path.join(RAIZ, "testes", "node_modules")
NM = os.environ.get("NM", _nm if os.path.isdir(_nm) else "/home/claude/rega-test/node_modules")
FOTO = os.environ.get("FOTO", "/home/claude/rega-test/foto_teste.jpg")
if not os.path.exists(FOTO):   # no Mac: cria uma fotografia de teste
    import base64, tempfile
    FOTO = os.path.join(tempfile.gettempdir(), "rega_foto_teste_v235.jpg")
    open(FOTO, "wb").write(base64.b64decode("/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIfIiEmKzcvJik0KSEiMEExNDk7Pj4+JS5ESUM8SDc9Pjv/2wBDAQoLCw4NDhwQEBw7KCIoOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozv/wAARCAAwAEADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwCrRRRXinCFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQB//2Q=="))
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8871", "--directory", RAIZ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
A1 = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"; CH1 = "44444444-4444-4444-4444-444444444444"; CH2 = "55555555-5555-5555-5555-555555555555"
hoje = datetime.date.today().isoformat()
LING = os.environ.get("LING", "pt"); falhas = []
def verif(c, txt):
    print(("OK  " if c else "FALHA ") + txt)
    if not c: falhas.append(txt)
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": A1, "activista_proposto": None}]
MAN_TODOS = [
  {"id": "PR7-1", "pr": "PR7", "produtor": "Produtor Sete", "comunidade": "Farol", "latitude": -10.6835, "longitude": 40.6340, "poligono": None, "vivas": 50, "instaladas": 50, "activa": True, "plantas": 50, "activista": None, "cavaroda": 10, "mulching": 5, "n": 1, "feito": False, "chefe_id": CH1, "chefe": "Chefe Farol"},
  {"id": "PR8-1", "pr": "PR8", "produtor": "Produtor Oito", "comunidade": "Quiwia", "latitude": -10.684, "longitude": 40.633, "poligono": None, "vivas": 40, "instaladas": 40, "activa": False, "plantas": 40, "activista": None, "cavaroda": None, "mulching": None, "n": 0, "feito": False, "chefe_id": CH2, "chefe": "Chefe Quiwia"}]
CHEFES = [{"id": CH1, "nome": "Chefe Farol", "comunidade": "Farol"}, {"id": CH2, "nome": "Chefe Quiwia", "comunidade": "Quiwia"}]

def correr(PAPEL):
    rec = {}; erros = []; dial = []
    def guarda(k, v): rec.setdefault(k, []).append(v)
    def mock(route):
        r = route.request; u = r.url
        ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
        if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "t@rega-coco.example.com"}})
        if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": {"activista": "Activista Um", "chefe_manutencao": "Chefe Farol"}.get(PAPEL, "Pessoa Teste"), "papel": PAPEL, "activista_id": A1 if PAPEL == "activista" else None, "gere_acessos": True, "ve_tudo": False})
        if "/rest/v1/activistas" in u: return ok([] if PAPEL == "chefe_manutencao" else [{"id": A1, "nome": "Activista Um", "comunidade_principal": "Farol", "tecnico": "Pessoa Teste", "supervisor": "Pessoa Teste", "activo": True, "equipa_tamanho": 5}])
        if "/rest/v1/areas" in u: return ok([] if PAPEL == "chefe_manutencao" else areas)
        if "/rest/v1/manutencao_comunidades" in u: return ok([{"comunidade": "Farol"}, {"comunidade": "Quiwia"}])
        if "/rest/v1/pessoas_acesso" in u: return ok([])
        if "/rpc/meus_activistas" in u: return ok([A1])
        if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
        if "/rpc/manutencao_campos" in u:
            if PAPEL in ("activista",): return ok(None)
            if PAPEL == "chefe_manutencao": return ok({"acesso": "chefe", "teste": False, "inicio": "2026-11-02", "comunidades": ["Farol"], "chefes": None, "campos": [MAN_TODOS[0]]})
            return ok({"acesso": "regista" if PAPEL == "tecnico" else "escreve", "teste": False, "inicio": "2026-11-02", "comunidades": ["Farol", "Quiwia"], "chefes": CHEFES, "campos": MAN_TODOS})
        if "/rpc/manutencao_registos_campo" in u: return ok([])
        if "/rpc/meu_dia" in u: return ok(None if PAPEL != "tecnico" else {"data": hoje, "hora_chegada": "06:30", "fechado_em": None,
            "equipas": [{"id": A1, "nome": "Activista Um", "comunidade": "Farol", "regas": 2, "plantas": 130, "sem_rega": None, "chegada": hoje + "T06:52:00Z", "agua": hoje + "T04:10:00Z", "comecou": hoje + "T03:24:00Z"}],
            "alertas": [{"registo_id": "r9", "data": hoje, "area_id": "PR1-1", "produtor": "Produtor Um", "equipa": "Activista Um", "plantas": 60, "base": 70, "ritmo": 180, "mediana": 29, "tipo": "ritmo"}],
            "monitoria_hoje": 0, "monitoria_falhas_ontem": 0, "sem_equipa": 0, "por_aprovar": [], "por_terminar": []})
        if "/rpc/gravar_recolha_agua" in u: guarda("agua", json.loads(r.post_data)); return ok(None)
        if "/rpc/atribuir_chefe_manut" in u: guarda("chefe", json.loads(r.post_data)); return ok(None)
        if "/rpc/voltar_a_regar" in u: guarda("vr", json.loads(r.post_data)); return ok({"activista_id": None})
        if "/rpc/areas_fora_plano2" in u: return ok({"na_rega": [], "fora": [{"id": "PR9-1", "pr": "PR9", "produtor": "Produtor Nove", "comunidade": "Senga", "vivas": 80, "instaladas": 90, "agua_origem": "COM", "pode": True, "tem_coord": True}]})
        if "/functions/v1/gestor-activistas" in u:
            d = json.loads(r.post_data or "{}")
            if d.get("accao") == "criar_utilizador": guarda("criar", d); return ok({"ok": True, "utilizador": d.get("utilizador"), "nome": d.get("nome"), "papel": d.get("papel")})
            return ok({"activistas": [], "utilizadores": [], "clientes": [], "nomes": {"tecnico": [], "supervisor": []}})
        if "/storage/v1/object/manutencao-fotos/" in u: guarda("upman", u.split("manutencao-fotos/")[1]); return ok({"Key": "x"})
        if "/rpc/gravar_manutencao" in u: guarda("gm", json.loads(r.post_data)); return ok(None)
        if "/rpc/estado_ronda" in u: return ok([] if PAPEL == "chefe_manutencao" else [{"area_id": "PR1-1", "ultima_rega": None, "regas_app": 0, "ronda_actual": 1, "regada_na_ronda": False}])
        if "/rpc/sugestoes_lista" in u: return ok({"sugestoes": [], "problemas": []})
        if "/rpc/" in u: return ok([])
        if "/rest/v1/registos_rega" in u: return ok([])
        if "/rest/v1/coberturas" in u: return ok([])
        return ok([])
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
        ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
        if PAPEL == "activista":   # início do dia já registado (não abre a folha do início do dia)
            ctx.add_init_script("try{localStorage.setItem('rega.jornada', JSON.stringify({id:'j1', data: new Date().toLocaleDateString('sv-SE'), pessoas: 4}))}catch(e){}")
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
        ctx.route("**/unpkg.com/leaflet-rotate@0.2.8/**", lambda r: r.fulfill(path=f"{NM}/leaflet-rotate/dist/leaflet-rotate-src.js" if r.request.url.endswith(".js") else f"{NM}/leaflet-rotate/dist/leaflet-rotate.css", content_type="application/javascript" if r.request.url.endswith(".js") else "text/css"))
        ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
        ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
        ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
        ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
        ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
        pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e) + " @ " + (e.stack or "")[:300])); pg.on("dialog", lambda d: (dial.append(d.message), d.accept()))
        pg.goto("http://localhost:8871/"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.fill("#l-user", "x"); pg.fill("#l-pin", "123456" if PAPEL == "activista" else "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1800)
        if pg.is_visible("#folha-x"): pg.click("#folha-x"); pg.wait_for_timeout(300)
        vis = lambda q: pg.evaluate(f"(() => {{ const e = document.querySelector('{q}'); return !!e && getComputedStyle(e).display !== 'none'; }})()")
        print(f"--- {PAPEL} ({LING}) ---")

        if PAPEL == "activista":
            pg.evaluate("mudar('hoje')"); pg.wait_for_selector("#b-agua", timeout=8000)
            verif(pg.locator("#b-agua").count() == 1, "A1 botão «Fomos buscar água» no Hoje do activista")
            pg.click("#b-agua"); pg.wait_for_timeout(3500)
            verif(any("água" in m or "water" in m or "maji" in m for m in dial), f"A2 pede confirmação ({dial[-1:]})")
            g = rec.get("agua", [])
            verif(len(g) == 1 and g[0]["p_activista"] == A1 and g[0]["p_lat"] is not None, f"A3 enviado ao servidor com o GPS ({g})")
            linha = pg.inner_text("#hoje")
            verif(any(ch.isdigit() for ch in linha.split("Fomos buscar")[0][-12:]) or ":" in linha, "A4 a hora aparece na linha")
            if LING != "pt": verif("Ida buscar água" not in linha and "Fomos buscar água" not in linha, "A5 traduzido")

        if PAPEL == "tecnico":
            pg.evaluate("mudar('hoje')"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.evaluate("window.__TAR_ABERTAS = true; actHoje()"); pg.wait_for_timeout(800)
            ch = pg.inner_text("#meu-dia details[data-k=ch]") if pg.locator("#meu-dia details[data-k=ch]").count() else ""
            verif("Activista Um" in ch and "06:10" in ch, f"T1 chegada tardia mostra a ida à água (06:10 Maputo): {ch[-160:]!r}")
            al = pg.inner_text("#meu-dia details[data-k=al]") if pg.locator("#meu-dia details[data-k=al]").count() else ""
            verif("29" in al and ("mediana de todas as equipas" in al if LING == "pt" else "habitual" not in al), f"T2 ⚠️ de ritmo com a mediana de todas as equipas: {al[-120:]!r}")
            if LING != "pt": verif("Foi buscar água" not in ch, "T3 traduzido")

        if PAPEL in ("supervisor", "tecnico"):
            pg.evaluate("setModo('manut'); mudar('lista')"); pg.wait_for_timeout(500)
            pg.evaluate("abrirFichaManut('PR7-1')"); pg.wait_for_timeout(400)
            f = pg.inner_text("#folha-c")
            verif("Chefe Farol" in f, "S1 a ficha da manutenção mostra o chefe do campo")
            pg.evaluate("ecraChefeManut('PR7-1')"); pg.wait_for_selector("#cm-chefe")
            pg.select_option("#cm-chefe", CH2); n0 = len(dial); pg.click("#folha-c button.btn:not(.sec)"); pg.wait_for_timeout(300)
            verif(len(dial) > n0, "S2 sem motivo não grava")
            pg.fill("#cm-motivo", "Fica mais perto do grupo de Quiwia"); pg.click("#folha-c button.btn:not(.sec)"); pg.wait_for_timeout(3500)
            c = rec.get("chefe", [])
            verif(len(c) == 1 and c[0]["p_chefe"] == CH2 and c[0]["p_area"] == "PR7-1" and "Quiwia" in c[0]["p_motivo"], f"S3 enviado ao servidor ({c})")
            if PAPEL == "supervisor":   # motivo «Fonte de água secou» ao voltar a pôr na rega
                pg.evaluate("setModo('rega'); fecharFolha(); ecraVoltarRega()"); pg.wait_for_selector("#vr-txt"); pg.fill("#vr-txt", "Nove"); pg.wait_for_timeout(1500)
                pg.wait_for_function("(S.foraPlano||[]).length > 0"); pg.evaluate("confirmarVoltaRega(0)"); pg.wait_for_selector("#vr-motivo")
                verif("secou" in pg.input_value("#vr-motivo"), f"S4 campo com água perto: motivo «Fonte de água secou» já escrito ({pg.input_value('#vr-motivo')!r})")
                pg.click("#vr-ok"); pg.wait_for_timeout(1500)
                v = rec.get("vr", [])
                verif(len(v) == 1 and v[0]["p_motivo"].startswith("Fonte de água secou"), f"S5 voltar_a_regar com o motivo em português ({v})")

        if PAPEL == "chefe_manutencao":
            verif(not vis("#nav button[data-e=hoje]") and not vis("#nav-painel") and not vis("#nav-gestao"), "C1 só Mapa e Campos no menu")
            verif(not vis("#modo-lista") and not vis("#modo-mapa"), "C2 sem o interruptor Rega / Manutenção")
            pg.evaluate("mudar('lista')"); pg.wait_for_timeout(500)
            l = pg.inner_text("#man-lista")
            verif("Produtor Sete" in l and "Produtor Oito" not in l, "C3 a lista mostra só os campos do grupo")
            pg.locator("#man-lista .item[data-mid='PR7-1']").click(); pg.wait_for_timeout(400)
            f = pg.inner_text("#folha-c")
            verif(pg.locator("#folha-c button:has-text('Registar o trabalho')").count() == 1 if LING == "pt" else "ecraRegManut" in pg.inner_html("#folha-c"), "C4 pode registar o trabalho")
            h = pg.inner_html("#folha-c")
            verif("ecraMedir" not in h and "marcarFeitoManut" not in h and "ecraChefeManut" not in h, "C5 sem medir a área, sem «feito» e sem mudar o chefe")
            pg.evaluate("ecraRegManut('PR7-1')"); pg.wait_for_selector("#mn-cav")
            pg.fill("#mn-cav", "30"); pg.fill("#mn-mul", "20")
            pg.set_input_files("#mn-foto", FOTO); pg.wait_for_timeout(1200)
            pg.click("#folha-c .btn >> nth=0"); pg.wait_for_timeout(4000)
            gm = rec.get("gm", [])
            verif(len(gm) == 1 and gm[0]["p_area"] == "PR7-1" and gm[0]["p_cavaroda"] == 30, f"C6 trabalho enviado ({gm})")
            verif(any(x.startswith(UID + "/") for x in rec.get("upman", [])), "C7 fotografia na pasta do chefe")

        if PAPEL == "gestor":
            pg.evaluate("mudar('gestao')"); pg.wait_for_timeout(800); pg.evaluate("typeof abaGestao === 'function' && abaGestao('acessos')"); pg.wait_for_selector("#c-papel", timeout=10000); pg.wait_for_timeout(800)
            o = pg.locator("#c-papel option[value=chefe_manutencao]")
            verif(o.count() == 1 and not o.is_disabled(), "G1 «Chefe de manutenção» nos outros acessos")
            pg.select_option("#c-papel", "chefe_manutencao"); pg.wait_for_timeout(300)
            verif(vis("#c-com-l"), "G2 pede o grupo (comunidade)")
            pg.select_option("#c-nome", "__outro"); pg.fill("#c-nome-outro", "Chefe Novo Farol"); pg.dispatch_event("#c-nome-outro", "input"); pg.fill("#c-senha", "segredo123")
            verif(pg.locator("#c-criar").is_disabled(), "G3 sem a comunidade não deixa criar")
            pg.select_option("#c-com", "Farol"); pg.wait_for_timeout(200)
            pg.click("#c-criar"); pg.wait_for_timeout(1500)
            c = rec.get("criar", [])
            verif(len(c) == 1 and c[0]["papel"] == "chefe_manutencao" and c[0]["comunidade"] == "Farol", f"G4 pedido de criação com o grupo ({c})")

        print("erros JS:", erros)
        if erros: falhas.append(f"{PAPEL}: erros JS")
        b.close()

for papel in os.environ.get("PAPEIS", "activista,tecnico,supervisor,chefe_manutencao,gestor").split(","): correr(papel)
srv.terminate()
print("RESULTADO:", "PASSOU" if not falhas else f"FALHOU ({len(falhas)}): {falhas}")
