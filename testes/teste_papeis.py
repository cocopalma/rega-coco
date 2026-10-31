import json, subprocess, time, sys
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8767", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None, "data_plantio": "2026-05-06"}]
D = {"gerado_em": "2026-10-10T20:00:00Z", "inicio": None, "universo": {"areas": 721, "vivas": 94529}, "areas_regadas": 0, "vivas_regadas": 0, "plantas_regadas_total": 0, "pessoas_dia_total": 0, "registos": 0,
     "dias_medios_entre_regas": None, "alertas": 0, "gps_invalido": 0, "espera_agua_min": None, "por_dia": [], "por_comunidade": [], "por_equipa": [], "chegadas_agua": [], "constrangimentos": {}}
pedidos = []
coberturas = []
visitas = []
def fazer_mock(papel):
    def mock(route):
        r = route.request; u = r.url; pedidos.append(u.split('.co')[1][:40])
        ok = lambda b: route.fulfill(status=200, content_type="application/json", body=json.dumps(b))
        if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time())+3600, "refresh_token": "r", "user": {"id": "u", "aud": "authenticated", "role": "authenticated", "email": "x@rega-coco.example.com"}})
        if "/rest/v1/perfis" in u: return ok({"id": "u", "nome": "Pessoa Teste", "papel": papel, "activista_id": None})
        if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Majula Muemede Bacar", "comunidade_principal": "Farol"}])
        if "/rest/v1/areas" in u: return ok(areas)
        if "/rpc/estado_ronda" in u: return ok([])
        if "/rpc/painel_resumo" in u: return ok(D)
        if "/rpc/registar_visita_painel" in u: visitas.append(papel); return route.fulfill(status=204, body="")
        if "/rpc/visitas_painel_resumo" in u: return ok([{"nome": "Ana Exemplo", "papel": "cliente", "utilizador": "ana", "ultima_visita": "2026-10-10T21:30:00Z", "visitas_30_dias": 3, "visitas_total": 3}])
        if "/rest/v1/registos_rega" in u: return ok([])
        if "/rest/v1/pessoas_acesso" in u: return ok([{"nome": "Guidion Cristovao", "entidade": "Projecto", "papel": "tecnico", "utilizador": "guidion"},
            {"nome": "Essumaila Carlos Assane", "entidade": "Projecto", "papel": "tecnico", "utilizador": "essumaila"},
            {"nome": "Kathleen Angulo", "entidade": "M&E", "papel": "me", "utilizador": "kathleen"}, {"nome": "Frederico Paiva", "entidade": "Cliente", "papel": "cliente", "utilizador": "Frederico"}])
        if "/rest/v1/coberturas" in u:
            if r.method == "POST": coberturas.append(json.loads(r.post_data)); return route.fulfill(status=201, body="")
            return ok([{"id": "c1", "perfil_id": "p2", "papel": "tecnico", "cobre_nome": "Essumaila Carlos Assane", "desde": "2026-10-11", "ate": None}] if coberturas else [])
        if "/functions/v1/gestor-activistas" in u:
            corpo = json.loads(r.post_data); print("   FN", corpo)
            if corpo["accao"] == "listar": return ok({"activistas": [], "utilizadores": [{"id": "p1", "nome": "Director X", "papel": "director", "utilizador": "director"}, {"id": "p2", "nome": "Guidion Cristovao", "papel": "tecnico", "utilizador": "guidion"}],
                                                   "nomes": {"tecnico": ["Essumaila Carlos Assane", "Guidion Cristovao"], "supervisor": ["Nuro Antonio Culete", "Raul Miquilange"]}})
            return ok({"ok": True, "nome": corpo.get("nome"), "utilizador": corpo.get("utilizador"), "papel": corpo.get("papel")})
        return ok({})
    return mock
erros = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for papel in ["cliente", "director", "tecnico", "gestor"]:
        ctx = b.new_context(viewport={"width": 390, "height": 800}, geolocation={"latitude": -10.6836, "longitude": 40.6341}, permissions=["geolocation"])
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
        ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
        ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
        ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
        ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", fazer_mock(papel))
        pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(papel + ": " + str(e))); pg.on("dialog", lambda d: d.accept())
        pedidos.clear()
        pg.goto("http://localhost:8767/"); pg.wait_for_selector("#l-entrar", state="visible")
        pg.fill("#l-user", "teste"); pg.fill("#l-pin", "12345678"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1500)
        abas = [x.inner_text() for x in pg.query_selector_all("#nav button") if x.is_visible()]
        linha = f"{papel}: separadores {abas} | cabeçalho '{pg.inner_text('#h-nome')}'"
        if papel == "cliente":
            f = pg.frame_locator("#painel-f"); f.locator("#kpis .kpi").first.wait_for()
            linha += f" | painel no separador: {f.locator('#painel h1').inner_text()} | Sair visível: {pg.is_visible('#h-sair')} | pediu áreas: {any('areas' in x for x in pedidos)}"
            pg.screenshot(path="/home/claude/rega-test/cliente.png")
        else:
            pg.click("nav button[data-e=lista]"); pg.click(".item[data-id='PR1-1']"); pg.wait_for_selector("#folha.on")
            linha += f" | botão de entrada: {pg.is_visible('text=Cheguei — marcar entrada')}"
            pg.click("#folha-x"); pg.click("nav button[data-e=painel]"); pg.frame_locator("#painel-f").locator("#kpis .kpi").first.wait_for()
            linha += " | painel abre: sim"
        if papel == "gestor":
            pg.click("nav button[data-e=gestao]"); pg.wait_for_selector("#c-criar")
            pg.select_option("#c-papel", "tecnico"); tec = pg.eval_on_selector_all("#c-nome option", "o => o.map(x => x.textContent + (x.disabled ? ' (já tem)' : ''))")
            linha += f" | nomes de técnicos: {tec}"
            pg.select_option("#c-papel", "me"); linha += f" | M&E: {pg.eval_on_selector_all('#c-nome option', 'o => o.map(x => x.textContent)')} → utilizador {pg.input_value('#c-user')}"
            pg.select_option("#c-papel", "cliente"); linha += f" | cliente → {pg.input_value('#c-user')}"
            pg.select_option("#c-nome", "__outro"); pg.fill("#c-nome-outro", "Maria Teste"); linha += f" | outra pessoa → {pg.input_value('#c-user')}"
            pg.select_option("#c-papel", "supervisor"); pg.select_option("#c-nome", "Nuro Antonio Culete"); pg.fill("#c-senha", "senha-teste-1")
            linha += f" | cobre: {pg.eval_on_selector_all('#k-cobre option', 'o => o.map(x => x.textContent)')}"
            pg.click("#k-gravar"); pg.wait_for_selector("text=cobre Essumaila"); linha += f" | cobertura gravada: {coberturas}"
            linha += f" | utilizador sugerido: {pg.input_value('#c-user')} | lista: {pg.inner_text('#gestao').split('Acessos criados')[1][:60].strip()}"
            pg.wait_for_selector("#g-visitas table"); linha += " | visitas: " + pg.inner_text("#g-visitas").replace("\n", " ")[:120]
            pg.click("#c-criar"); pg.wait_for_selector("text=Acesso criado")
            pg.click("button:has-text('Nova senha') >> nth=0"); pg.wait_for_selector("#n-cred"); pg.fill("#n-cred", "curta"); pg.click("#n-gravar"); pg.wait_for_timeout(300)
            curta = pg.is_visible("text=pelo menos 8 caracteres"); pg.fill("#n-cred", "senha-nova-123"); pg.click("#n-gravar"); pg.wait_for_selector("text=Senha de Director X alterada")
            linha += f" | nova senha: recusa curta={curta}, gravada=sim"
        print(linha); ctx.close()
    print("visitas registadas por:", visitas)
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
