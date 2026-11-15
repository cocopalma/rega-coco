# Capturas para o vídeo das novidades da v239 (simulação; nada sai para o servidor)
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8874"').replace("localhost:8858", "localhost:8874").replace('k = dict(viewport={"width": 390, "height": 844}, permissions', 'k = dict(device_scale_factor=2, viewport={"width": 390, "height": 844}, permissions'))
FOTO = "/home/claude/rega-test/foto_teste.jpg"; OUT = "/home/claude/rega-test/video/v239/cap/"
def cap(pg, n, sel=None):
    pg.wait_for_timeout(500)
    if sel:
        try: pg.locator(sel).first.scroll_into_view_if_needed(timeout=3000)
        except Exception as e: print("sem", sel)
        pg.wait_for_timeout(300)
    pg.screenshot(path=OUT + n + ".png"); print("cap", n)
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-16T09:00:00+02:00"); pg.add_init_script("delete window.__HORA_TESTE;")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate("fecharFolha(); escolherLingua('pt')"); pg.wait_for_timeout(800)
    demo(pg, "activista"); pg.evaluate("fecharFolha()")
    # etiquetas ao toque
    pg.evaluate("mudar('mapa')"); pg.wait_for_timeout(2500); cap(pg, "a8_mapa")
    try:
        pg.evaluate("(() => { const a = S.areas.find(a => a.latitude != null); mapa.setView([a.latitude, a.longitude], 17); })()"); pg.wait_for_timeout(1500)
        pg.evaluate("(() => { const a = S.areas.find(a => a.latitude != null); tocarCampo(a, abrirFicha); })()"); cap(pg, "a8_etiqueta")
    except Exception as e: print("etiqueta:", str(e)[:200])
    id = pg.evaluate("S.areas.find(a => a.activista_id === S.perfil.activista_id && a.latitude != null).id")
    pg.evaluate(f"DEMO.irPara('{id}')"); pg.wait_for_timeout(500); ficha(pg, id); cap(pg, "a1_ficha", "#b-act")
    pg.click("#b-act"); cap(pg, "a2_motivo")
    pg.click("#ac-mot .chip[data-k=tuk_tuk]"); cap(pg, "a2_motivo_ok", "#ac-ok"); pg.click("#ac-ok"); pg.wait_for_timeout(600)
    if pg.is_visible("#j-pessoas"): pg.fill("#j-pessoas", "5"); cap(pg, "a3_inicio"); pg.click("#folha-c button.btn")
    elif pg.locator("#j-lista").count(): cap(pg, "a3_inicio"); pg.click("#folha-c button.btn")
    pg.wait_for_selector("#fa-foto", state="attached", timeout=30000); cap(pg, "a4_foto_entrada")
    pg.set_input_files("#fa-foto", FOTO); pg.wait_for_selector("#act-curso", timeout=10000); cap(pg, "a5_curso", "#act-curso")
    pg.locator("#act-curso + .cartao button.chip").nth(1).click(); pg.wait_for_timeout(300)
    pg.set_input_files("#fa-foto", FOTO); pg.wait_for_selector("#act-curso", timeout=10000); cap(pg, "a5_curso2", "#b-act-fim")
    pg.click("#b-act-fim"); pg.wait_for_selector("#af-ok")
    pg.fill("#af-cav", "25"); pg.fill("#af-mul", "10"); pg.set_input_files("#af-foto", FOTO); pg.wait_for_timeout(800)
    if not pg.input_value("#af-pess"): pg.fill("#af-pess", "5")
    cap(pg, "a6_fim", "#af-cav"); cap(pg, "a6_fim2", "#af-ok")
    pg.click("#af-ok"); pg.wait_for_timeout(3500); cap(pg, "a7_ficha_depois", "#f-cav")
    demo(pg, "tecnico"); pg.evaluate("fecharFolha(); window.__TAR_ABERTAS = true; mudar('hoje')"); pg.wait_for_timeout(3500)
    cap(pg, "t1_meudia"); pg.evaluate("(() => { const e = [...document.querySelectorAll('#meu-dia *')].find(x => x.children.length === 0 && x.textContent.includes('🌱')); if (e) e.scrollIntoView({block:'center'}); })()"); cap(pg, "t1_meudia_act")
    idt = pg.evaluate("S.areas.find(a => a.activista_id && a.latitude != null && meuCampo(a)).id")
    pg.evaluate(f"DEMO.irPara('{idt}')"); ficha(pg, idt); cap(pg, "t2_ficha_tec", "#b-act")
    try:
        pg.click("#b-act"); cap(pg, "t2_pela_equipa"); pg.evaluate("fecharFolha()")
    except Exception as e: print("t2:", str(e)[:200])
    # 16:00
    pg.evaluate("sessionStorage.setItem('rega.demo.hora', '16:00')"); demo(pg, "activista"); pg.evaluate("fecharFolha()")
    id2 = pg.evaluate(f"S.areas.find(a => a.activista_id === S.perfil.activista_id && a.latitude != null && a.id !== '{id}').id")
    pg.evaluate(f"DEMO.irPara('{id2}')"); ficha(pg, id2); cap(pg, "a9_depois_1530", "#aviso-depois")
    demo(pg, "tecnico"); pg.evaluate("fecharFolha(); window.__TAR_ABERTAS = true; mudar('hoje')"); pg.wait_for_timeout(3000)
    cap(pg, "t3_he_btn", "#meu-dia .he-btn")
    pg.locator("#meu-dia .he-btn").first.click(); pg.wait_for_timeout(2500); cap(pg, "t4_he_ok", "#meu-dia .he-ok")
    demo(pg, "activista"); pg.evaluate(f"fecharFolha(); DEMO.irPara('{id2}')"); ficha(pg, id2); cap(pg, "a10_com_he", "#b-act")
    print("ERROS JS:", erros or "nenhum"); b.close()
srv.terminate()
