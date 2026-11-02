# v198 (02/11/2026, Valdo: "Sim" às opções 1 e 3): origem e data de cada fotografia da rega (câmara da app / câmara do telefone /
# galeria; data do EXIF lida antes da redução), carimbo com data, hora e GPS na fotografia, e ⚠️ «Fotografia de outro dia»
# no «O meu dia» (não bloqueia; «Está certo» → confirmar_foto_rega). LING=en / sw.
import json, subprocess, time, sys, os, datetime
LING = os.environ.get("LING", "pt")
from playwright.sync_api import sync_playwright
NM = "/home/claude/rega-test/node_modules"; D = "/home/claude/rega-test/v198"
if not os.path.exists(f"{D}/com_exif.jpg"):   # fotografias de teste: uma com data no EXIF (28/10/2026 07:10), outra sem
    from PIL import Image
    os.makedirs(D, exist_ok=True); im = Image.new("RGB", (1600, 1200), (60, 140, 60)); ex = Image.Exif(); ex[0x0132] = "2026:10:29 09:00:00"
    ex.get_ifd(0x8769)[0x9003] = "2026:10:28 07:10:00"; im.save(f"{D}/com_exif.jpg", exif=ex.tobytes()); im.save(f"{D}/sem_exif.jpg")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8898", "--directory", "/home/claude/rega-coco"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
ACT = "11111111-1111-1111-1111-111111111111"; UID = "22222222-2222-2222-2222-222222222222"
hoje = datetime.date.today().isoformat()
areas = [{"id": "PR1-1", "pr": "PR1", "area_n": 1, "comunidade": "Farol", "produtor": "Produtor Um", "instaladas": 70, "vivas": 70, "latitude": -10.6835, "longitude": 40.6340, "activista_id": ACT, "activista_proposto": None}]
papel = {"p": "activista"}; rec = {"registos": [], "conf": [], "confrega": []}
md = {"data": hoje, "hora_chegada": "06:00", "fechado_em": None, "equipas": [{"id": ACT, "nome": "Activista Um", "regas": 1, "plantas": 70}], "monitoria_hoje": 0, "monitoria_falhas_ontem": 0, "sem_equipa": 0, "por_aprovar": [], "por_terminar": [],
      "alertas": [{"registo_id": "33333333-3333-3333-3333-333333333333", "data": hoje, "area_id": "PR1-1", "produtor": "Produtor Um", "equipa": "Activista Um", "plantas": 70, "base": 70, "ritmo": 50, "mediana": None, "tipo": "foto_data",
                   "fotos": {"entrada": {"origem": "galeria", "tirada": "2026-10-28T07:10:00", "fonte": "exif"}, "rega": {"origem": "camara_app", "tirada": hoje + "T08:00:00", "fonte": "agora"}}}]}
def mock(route):
    r = route.request; u = r.url
    ok = lambda b, st=200: route.fulfill(status=st, content_type="application/json", body=json.dumps(b))
    if "/auth/v1/token" in u: return ok({"access_token": "x.y.z", "token_type": "bearer", "expires_in": 3600, "expires_at": int(time.time()) + 3600, "refresh_token": "r", "user": {"id": UID, "aud": "authenticated", "role": "authenticated", "email": "a@rega-coco.example.com"}})
    if "/rest/v1/perfis" in u: return ok({"id": UID, "nome": "Activista Um" if papel["p"] == "activista" else "Tecnico Um", "papel": papel["p"], "activista_id": ACT if papel["p"] == "activista" else None, "ve_tudo": False})
    if "/rest/v1/activistas" in u: return ok([{"id": ACT, "nome": "Activista Um", "comunidade_principal": "Farol", "tecnico": "Tecnico Um", "supervisor": "Sup Um", "activo": True}])
    if "/rest/v1/areas" in u: return ok(areas)
    if "/rest/v1/registos_rega" in u:
        if r.method == "POST": rec["registos"] += (lambda x: x if isinstance(x, list) else [x])(json.loads(r.post_data)); return route.fulfill(status=201, body="")
        return ok([])
    if "/storage/v1/" in u: return ok({"Key": "x"})
    if "/rpc/meus_activistas" in u: return ok([ACT])
    if "/rpc/minhas_comunidades" in u: return ok(["Farol"])
    if "/rpc/meu_dia" in u: return ok(md)
    if "/rpc/confirmar_foto_rega" in u: rec["conf"].append(json.loads(r.post_data)); md["alertas"] = []; return ok(None)
    if "/rpc/confirmar_rega" in u: rec["confrega"].append(json.loads(r.post_data)); return ok(None)
    return ok([])
erros = []
def contexto(p):
    ctx = p.chromium.launch().new_context(viewport={"width": 390, "height": 844}, permissions=["geolocation"], geolocation={"latitude": -10.6836, "longitude": 40.6341, "accuracy": 5})
    ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua', '{LING}')}}catch(e){{}}")
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.js", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.js", content_type="application/javascript"))
    ctx.route("**/unpkg.com/leaflet@1.9.4/dist/leaflet.css", lambda r: r.fulfill(path=f"{NM}/leaflet/dist/leaflet.css", content_type="text/css"))
    ctx.route("**/unpkg.com/leaflet-rotate**", lambda r: r.fulfill(path=f"{NM}/leaflet-rotate/dist/leaflet-rotate-src.js", content_type="application/javascript") if os.path.exists(f"{NM}/leaflet-rotate/dist/leaflet-rotate-src.js") else r.fulfill(status=204, body=""))
    ctx.route("**/cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/*", lambda r: r.fulfill(path=f"{NM}/@supabase/supabase-js/dist/umd/" + r.request.url.split("/")[-1], content_type="application/javascript"))
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    ctx.route("**/*.tile.openstreetmap.org/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/server.arcgisonline.com/**", lambda r: r.fulfill(status=204, body=""))
    ctx.route("**/fgzdqnvobgfzjetbbxcm.supabase.co/**", mock)
    pg = ctx.new_page(); pg.on("pageerror", lambda e: erros.append(str(e))); pg.on("dialog", lambda d: d.accept())
    return ctx, pg
with sync_playwright() as p:
    # ---------- 1. activista: fotografias pela galeria e com a «câmara do telefone» ----------
    ctx, pg = contexto(p)
    pg.goto("http://localhost:8898/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "act"); pg.fill("#l-pin", "123456"); pg.click("#l-entrar"); pg.wait_for_timeout(2500)
    if pg.is_visible("#j-pessoas"): pg.fill("#j-pessoas", "4"); pg.click("#folha.on .btn >> nth=0"); pg.wait_for_timeout(800)
    pg.evaluate("(()=>{LS.set('emCurso',{area_id:'PR1-1',entrada_em:new Date().toISOString(),agua_em:new Date().toISOString(),entrada_lat:-10.6836,entrada_lon:40.6341,gps_precisao_m:5,reg_id:crypto.randomUUID()})})()")
    for nome, ficheiro, campo, tipo in (("galeria (EXIF 28/10)", "com_exif.jpg", "#fr-foto", "entrada"), ("câmara do telefone (sem EXIF)", "sem_exif.jpg", "#fr-foto-cam", "rega")):
        pg.evaluate(f"ecraFotoRega('{tipo}')"); pg.wait_for_selector("#fr-foto", state="attached")
        pg.set_input_files(campo, f"{D}/{ficheiro}"); pg.wait_for_timeout(1800)
        print(f"1 {nome}:", pg.evaluate(f"JSON.stringify(LS.get('emCurso').fotos_meta.{tipo})"))
    # carimbo: a faixa escura em baixo da fotografia guardada
    cor = pg.evaluate("""async () => { const k = LS.get('emCurso').reg_id + '-entrada'; const b = await FOTOS.ler(k); const im = await createImageBitmap(b);
      const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d'); g.drawImage(im, 0, 0);
      const cima = g.getImageData(5, 5, 1, 1).data, baixo = g.getImageData(3, im.height - 3, 1, 1).data; return [im.width, im.height, Array.from(cima).slice(0,3), Array.from(baixo).slice(0,3)] }""")
    print("2 carimbo (tamanho, cor em cima, cor na faixa de baixo):", cor)
    # imagem do carimbo para ver
    png = pg.evaluate("""async () => { const b = await FOTOS.ler(LS.get('emCurso').reg_id + '-entrada'); const r = new FileReader(); return await new Promise((ok) => { r.onload = () => ok(r.result); r.readAsDataURL(b) }) }""")
    import base64; open(f"{D}/carimbo_{LING}.jpg", "wb").write(base64.b64decode(png.split(",")[1]))
    # saída e envio: fotos_origem vai com o registo
    pg.evaluate("ecraSaida()"); pg.wait_for_selector("#s-plantas"); pg.fill("#s-plantas", "70")
    pg.set_input_files("#s-foto", f"{D}/sem_exif.jpg"); pg.wait_for_timeout(1500)
    pg.evaluate("marcarSaida()"); pg.wait_for_function("!LS.get('emCurso')", timeout=15000); pg.evaluate("sincronizar(true)"); pg.wait_for_timeout(2500)
    r = rec["registos"][-1] if rec["registos"] else {}
    print("3 enviado fotos_origem:", json.dumps(r.get("fotos_origem")), "| foto_entrada:", bool(r.get("foto_entrada")))
    ctx.browser.close()
    # ---------- 2. técnico: «O meu dia» mostra a fotografia de outro dia ----------
    papel["p"] = "tecnico"; ctx, pg = contexto(p)
    pg.goto("http://localhost:8898/"); pg.wait_for_selector("#l-entrar", state="visible")
    pg.fill("#l-user", "tec"); pg.fill("#l-pin", "segredo12"); pg.click("#l-entrar"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(1800)
    pg.click("nav button[data-e=hoje]"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(600)
    t = pg.inner_text("#meu-dia"); s3 = t.split("3.")[1].split("4.")[0] if "3." in t else "(sem 3)"
    print("4 secção 3:", s3.replace("\n", " | ")[:400])
    pg.click("#meu-dia button[onclick*=\"'foto_data'\"]"); pg.wait_for_timeout(400)
    print("5 ecrã:", pg.inner_text("#folha-c").replace("\n", " | ")[:300])
    pg.fill("#cr-nota", "A data do telefone estava errada"); pg.click("#cr-ok"); pg.wait_for_timeout(1500)
    print("6 confirmar_foto_rega:", rec["conf"], "| confirmar_rega (não deve):", rec["confrega"])
    print("ERROS JS:", erros or "nenhum"); ctx.browser.close()
srv.terminate()
