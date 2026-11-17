# v244 (17/11/2026, sugestão do Essumaila): cancelar as horas extras activadas por engano. Simulação, 16:00. LING=en / sw.
import os, sys
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8874"').replace("localhost:8858", "localhost:8874"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
with sync_playwright() as p:
    b = p.chromium.launch()
    PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-16T09:00:00+02:00"); pg.add_init_script("delete window.__HORA_TESTE;")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    PEDIDOS["contar"] = True; PEDIDOS["n"] = 0
    pg.evaluate("sessionStorage.setItem('rega.demo.hora', '16:00')")
    demo(pg, "tecnico"); pg.evaluate("fecharFolha(); window.__TAR_ABERTAS = true; mudar('hoje')"); pg.wait_for_timeout(3000)
    pg.locator("#meu-dia .he-btn").first.click(); pg.wait_for_timeout(2500)
    passo("1 activou e aparece «Cancelar»", DB(pg, "(D.he||[]).length") == 1 and pg.locator("#meu-dia .he-cancel").count() >= 1)
    pg.locator("#meu-dia .he-cancel").first.click(); pg.wait_for_timeout(2500)
    passo("2 cancelou", DB(pg, "(D.he||[]).length") == 0 and pg.locator("#meu-dia .he-cancel").count() == 0 and pg.locator("#meu-dia .he-btn").count() >= 1)
    # na ficha do campo
    id = pg.evaluate("S.areas.find(a => a.activista_id && meuCampo(a)).id")
    act = pg.evaluate(f"S.areas.find(a => a.id === '{id}').activista_id")
    pg.evaluate(f"activarHorasExtras('{act}')"); pg.wait_for_timeout(2000); ficha(pg, id); pg.wait_for_timeout(500)
    passo("3 ficha mostra «Cancelar»", pg.locator("#he-ficha .he-cancel").count() == 1)
    pg.locator("#he-ficha .he-cancel").click(); pg.wait_for_timeout(2500)
    passo("4 cancelado na ficha e botão de activar de volta", DB(pg, "(D.he||[]).length") == 0 and pg.locator("#he-ficha.btn, button#he-ficha").count() == 1)
    t = pg.inner_text("body")
    pg.evaluate("sessionStorage.removeItem('rega.demo.hora')")
    passo("6 nada saiu para o servidor", PEDIDOS["n"] == 0, PEDIDOS["n"])
    b.close()
print("TUDO OK" if all(res.values()) else "FALHOU: " + ", ".join(k for k, v in res.items() if not v))
