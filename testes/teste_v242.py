# v242: «Chegou mais água», última chegada do tuk-tuk lida do servidor, apoio só de cava-roda e mulching (simulação). LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8877"').replace("localhost:8858", "localhost:8877"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
DBX = lambda pg, e: pg.evaluate("(() => { const D = JSON.parse(sessionStorage.getItem('rega.demo.db')); return " + e + " })()")
FOTOS = "(async()=>{ for (const t of %s) await guardarFotoRega(t, new Blob(['x'],{type:'image/jpeg'})); abrirFicha(LS.get('emCurso').area_id)})()"
T = {"pt": ("Chegou mais água", "Mais água", "só para a cava-roda", "não tem campos", "água nova"),
     "en": ("More water arrived", "More water", "only for ring weeding", "has no fields", "new water"),
     "sw": ("Maji zaidi yamefika", "Maji zaidi", "kupalilia kuzunguka mche na matandazo tu", "haina mashamba", "maji mapya")}[LG]
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-16T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    demo(pg, "activista")
    if pg.is_visible("#folha.on") and pg.locator("#j-lista").count():
        for c in pg.locator("#j-lista input").all(): c.check()
        pg.click("#folha-c .btn >> nth=-1"); pg.wait_for_timeout(500)
    ficha(pg, 'PR900101-1')
    passo("1 antes da água não há «Chegou mais água»", pg.locator("#b-mais-agua").count() == 0)
    pg.click("button[onclick^=marcarEntrada]"); pg.wait_for_selector("text=/Entrada marcada|Entry recorded|Kuingia kumewekwa/", timeout=30000)
    pg.evaluate(FOTOS % "['entrada']"); pg.wait_for_timeout(500)
    passo("2 com a entrada e sem água: ainda não", pg.locator("#b-mais-agua").count() == 0)
    pg.click("button[onclick='pedirTuk(false)']"); pg.wait_for_selector("#tk-cod"); pg.select_option("#tk-cod", "12"); pg.click("button[onclick='confirmarTuk(false)']"); pg.wait_for_timeout(500)
    passo("3 depois da água aparece o botão", pg.is_visible("#b-mais-agua") and T[0] in pg.inner_text("#b-mais-agua"), pg.inner_text("#b-mais-agua"))
    pg.click("#b-mais-agua"); pg.wait_for_timeout(300)
    passo("4 pede o tuk-tuk, com o último já escolhido", pg.input_value("#tk-cod") == "12" and T[0] in pg.inner_text("#folha-c"), pg.inner_text("#folha-c")[:140].replace("\n", " | "))
    pg.select_option("#tk-cod", ""); dial.clear(); pg.click("button[onclick='confirmarMaisAgua()']"); pg.wait_for_timeout(200)
    passo("5 sem tuk-tuk não grava", len(dial) == 1 and not pg.evaluate("(LS.get('emCurso').tuk_extra||[]).length"))
    pg.select_option("#tk-cod", "VGB1"); pg.click("button[onclick='confirmarMaisAgua()']"); pg.wait_for_timeout(400)
    e = pg.evaluate("LS.get('emCurso').tuk_extra")
    passo("6 volta registada e mostrada na ficha", len(e) == 1 and e[0]["codigo"] == "VGB1" and pg.is_visible("#tk-voltas") and T[1] in pg.inner_text("#tk-voltas") and "VGB1" in pg.inner_text("#tk-voltas"), pg.inner_text("#tk-voltas").replace("\n", " | "))
    pg.click("#b-mais-agua"); pg.wait_for_timeout(200); pg.select_option("#tk-cod", "?"); pg.fill("#tk-out", "azul"); pg.click("button[onclick='confirmarMaisAgua()']"); pg.wait_for_timeout(300)
    passo("7 2.ª volta com «não sei o código»", pg.evaluate("LS.get('emCurso').tuk_extra.map(x=>x.codigo||x.outro).join()") == "VGB1,azul")
    pg.screenshot(path=f"/home/claude/rega-test/v242_a_{LG}.png")
    dial.clear(); pg.click("#tk-voltas button"); pg.wait_for_timeout(300)
    passo("8 apagar a última (engano)", pg.evaluate("LS.get('emCurso').tuk_extra.length") == 1 and len(dial) == 1)
    pg.evaluate(FOTOS % "['rega','saida']"); pg.wait_for_timeout(500)
    pg.click("button[onclick='ecraSaida()']"); pg.fill("#s-plantas", str(pg.evaluate("plantasN(S.areas.find(a=>a.id==='PR900101-1'))"))); pg.click("button[onclick='marcarSaida()']"); pg.wait_for_timeout(4000)
    r = DBX(pg, "D.registos.filter(r=>!r.teste && r.area_id==='PR900101-1').map(r=>[r.tuk_codigo,r.tuk_chegada,(r.tuk_extra||[]).map(x=>x.codigo)])")
    passo("9 a rega chega ao servidor com a volta", r == [["12", "nova", ["VGB1"]]], str(r))
    # apoio só de cava-roda e mulching (activista que ajuda): sem botão de entrada, com o botão da cava-roda
    pg.evaluate("fecharFolha(); LS.set('apoios', [{id:'ap1', ajuda_activista_id:S.perfil.activista_id, ajuda_nome:'Eu', para_activista_id:'x', para_nome:'Outra', area_ids:['PR900103-1'], inicio:hojeISO(), so_actividade:true, campos_actividade:0}]); DEMO.irPara('PR900103-1')")
    pg.wait_for_timeout(3000); pg.evaluate("abrirFicha('PR900103-1')"); pg.wait_for_timeout(500)
    tx = pg.inner_text("#folha-c")
    passo("10 apoio só de cava-roda: sem «Cheguei», com a cava-roda", pg.locator("button[onclick^=marcarEntrada]").count() == 0 and pg.is_visible("#ap-so-ficha") and T[2] in tx and pg.is_visible("#b-act"), pg.inner_text("#ap-so-ficha"))
    pg.evaluate("marcarEntrada('PR900103-1')"); pg.wait_for_timeout(600)
    passo("11 a entrada da rega é recusada", pg.evaluate("!LS.get('emCurso')") and pg.locator("#folha-c .msg.erro").count() >= 1)
    pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_timeout(800)
    passo("12 Hoje do activista diz que o apoio é de cava-roda", pg.locator("#ap-so").count() == 1, pg.inner_text("#ap-so")[:140] if pg.locator("#ap-so").count() else "")
    pg.evaluate("LS.set('apoios', [])")
    # técnico: regista pela equipa noutro telefone — a última chegada vem do servidor
    demo(pg, "tecnico"); pg.wait_for_timeout(1500)
    h = pg.evaluate("carregarTuksHoje().then(()=>LS.get('tuksHoje'))")
    passo("13 tuks_hoje: última chegada da equipa = VGB1 (a outra volta)", h and len(h["l"]) == 1 and h["l"][0]["codigo"] == "VGB1" and not pg.evaluate("LS.get('tukUlt')"), str(h)[:200])
    passo("14 tukDeHoje usa o servidor", pg.evaluate("tukDeHoje(LS.get('tuksHoje').l[0].activista_id)") == "VGB1")
    pg.evaluate("LS.set('emCurso', {area_id:'PR900104-1', reg_id:'x', entrada_em:new Date().toISOString(), fotos:{}, motivo_tecnico:'telemóvel avariado'}); pedirTuk(false)"); pg.wait_for_selector("#tk-cod", timeout=6000)
    pg.select_option("#tk-cod", "VGB1"); pg.wait_for_timeout(200)
    passo("15 no telefone do técnico a pergunta «água nova ou a mesma» aparece", pg.is_visible("#tk-mesmo") and T[4] in pg.inner_text("#tk-mesmo"), pg.inner_text("#tk-mesmo")[:120].replace("\n", " | "))
    pg.select_option("#tk-cod", "03"); pg.wait_for_timeout(200)
    passo("16 com outro tuk-tuk não pergunta", pg.evaluate("$('#tk-mesmo').hidden"))
    pg.evaluate("LS.del ? LS.del('emCurso') : localStorage.removeItem('demo:rega.emCurso'); fecharFolha()")
    # técnico: activar um apoio de uma equipa sem campos (resposta do servidor simulada)
    pg.evaluate("""(() => { const o = sb.rpc.bind(sb); window.__ap = null; sb.rpc = (n, a) => n === 'apoio_candidatos2' ? Promise.resolve({ data: { so_actividade: true, mesma_comunidade: true, campos: [
      { area_id: 'PR1-1', produtor: 'Produtor Um', comunidade: 'Olumbe', plantas: 100, dist_m: null, nunca: false, sem_coordenada: false },
      { area_id: 'PR2-1', produtor: 'Produtor Dois', comunidade: 'Olumbe', plantas: 50, dist_m: null, nunca: false, sem_coordenada: true }] }, error: null })
      : n === 'criar_apoio' ? (window.__ap = a, Promise.resolve({ data: 'id', error: null })) : o(n, a); })()""")
    ids = pg.evaluate("S.activistas.slice(0,2).map(x=>x.id)")
    pg.evaluate(f"ecraApoio('{ids[0]}','{ids[1]}')"); pg.wait_for_selector("#ap-lista", timeout=6000)
    tx = pg.inner_text("#folha-c")
    passo("17 ecrã do apoio: só cava-roda e mulching, sem «nunca regados», nada escolhido", pg.is_visible("#ap-so-msg") and T[3] in tx and pg.locator("#ap-nunca").count() == 0 and pg.locator("#ap-lista input:checked").count() == 0, pg.inner_text("#ap-so-msg")[:150])
    pg.screenshot(path=f"/home/claude/rega-test/v242_b_{LG}.png")
    pg.click("#ap-todos"); pg.click("#ap-ok"); pg.wait_for_timeout(800)
    passo("18 activa com os campos escolhidos", pg.evaluate("window.__ap && window.__ap.p_areas.join()") == "PR1-1,PR2-1", str(pg.evaluate("window.__ap")))
    pg.evaluate("""(() => { sb.rpc = ((o) => (n, a) => n === 'apoio_candidatos2' ? Promise.resolve({ data: { so_actividade: true, mesma_comunidade: false, campos: [] }, error: null }) : o(n, a))(sb.rpc.bind(sb)); })()""")
    pg.evaluate(f"ecraApoio('{ids[0]}','{ids[1]}')"); pg.wait_for_timeout(800)
    passo("19 outra comunidade: recusa com explicação", pg.locator("#ap-outra-com").count() == 1, pg.inner_text("#folha-c")[:140].replace("\n", " | "))
    # painel: a outra volta conta como viagem
    demo(pg, "director"); pg.evaluate("fecharFolha(); mudar('painel')"); pg.wait_for_timeout(7000)
    fr = pg.frame_locator("#e-painel iframe")
    td = fr.locator("#t-tuk").text_content(timeout=15000)
    passo("20 painel: 2 viagens (a rega e a outra volta)", fr.locator("#k-tuk .val").first.inner_text() == "2" and "VGB1" in td, fr.locator("#k-tuk").inner_text()[:120].replace("\n"," | ") + " // " + td[-260:])
    passo("21 nada saiu para o servidor", PEDIDOS["n"] == 0, f"pedidos={PEDIDOS['n']} {PEDIDOS['urls'][:3]}")
    if LG != "pt":
        import re
        falta = pg.evaluate("[...document.querySelectorAll('#folha-c, #e-hoje')].map(x=>x.innerText).join(' ')")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
