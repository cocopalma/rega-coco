# v249: menos espera ao abrir a app e ao passar de separador. Simulação, técnico.
# 1) o Hoje pede ao servidor tudo ao mesmo tempo (com 600 ms por pedido, o desenho demora ~1 pedido, não a soma);
# 2) voltar ao Hoje no mesmo minuto não repete os pedidos; 3) as sugestões de apoio e os trilhos não fazem esperar o carregamento;
# 4) o painel não recarrega ao voltar ao separador no mesmo 2 min; 5) a lista com 750 campos desenha-se depressa. LING=en / sw.
import os, sys, json, time
sys.argv = ["teste_v178.py"]
SRC = open("/home/claude/rega-test/teste_v178.py").read()
exec(SRC.split("with sync_playwright() as p:")[0].replace('"8858"', '"8884"').replace("localhost:8858", "localhost:8884"))
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
with sync_playwright() as p:
    b = p.chromium.launch(); PAPEL["v"] = "gestor"
    ctx, pg = contexto(b); pg.clock.install(time="2026-11-20T09:00:00+02:00")
    entrar(pg, "tecnico", "segredo12"); pg.wait_for_selector("#app", state="visible"); pg.wait_for_timeout(2500); pg.evaluate(f"fecharFolha(); escolherLingua('{LG}')"); pg.wait_for_timeout(800)
    demo(pg, "tecnico"); pg.evaluate("fecharFolha(); mudar('hoje')"); pg.wait_for_selector("#meu-dia", timeout=10000); pg.wait_for_timeout(1500)
    # cada pedido ao servidor passa a demorar 600 ms; contam-se os pedidos
    pg.evaluate("""(() => { window.__N = []; const r0 = sb.rpc.bind(sb);
      sb.rpc = (f, a) => { window.__N.push(f); return new Promise((ok) => setTimeout(ok, 600)).then(() => r0(f, a)); }; })()""")
    pg.clock.run_for(70000)
    t = pg.evaluate("(async () => { const t0 = performance.now(); await desenharHoje(); return [performance.now() - t0, window.__N.slice()] })()")
    ms, fs = t
    passo("1 Hoje (depois de uma acção) com os pedidos ao mesmo tempo", ms < 2500 and len(fs) >= 3, f"{ms:.0f} ms, {len(fs)} pedidos: {fs}")
    pg.evaluate("window.__N = []; mudar('mapa')"); pg.wait_for_timeout(300)
    pg.evaluate("mudar('hoje')"); pg.wait_for_timeout(1500)
    n2 = pg.evaluate("window.__N.slice()")
    passo("2 voltar ao Hoje no mesmo minuto não repete os pedidos", len(n2) == 0, str(n2))
    passo("2b o Hoje continua com «O meu dia»", pg.locator("#meu-dia").count() == 1)
    pg.clock.run_for(65000); pg.evaluate("window.__N = []; mudar('mapa')"); pg.wait_for_timeout(200)
    pg.evaluate("mudar('hoje')"); pg.wait_for_timeout(2500)
    n3 = pg.evaluate("window.__N.slice()")
    passo("3 depois de 1 minuto volta a pedir", len(n3) >= 2, str(n3))
    passo("3b as recontagens não se pedem de novo antes de 3 min", "recontagens_lista" not in n3, str(n3))
    # carregarEstado não espera pelos trilhos nem pelas sugestões de apoio
    pg.evaluate("""(() => { const r0 = sb.rpc; sb.rpc = (f, a) => (f === 'apoio_sugestoes' || f === 'trilhos') ? new Promise((ok) => setTimeout(ok, 8000)).then(() => r0(f, a)) : r0(f, a); })()""")
    pg.evaluate("_apoioSugEm = 0; LS.del('trilhosEm2')")
    t = pg.evaluate("(async () => { const t0 = performance.now(); await carregarEstado(); return performance.now() - t0 })()")
    passo("4 carregar o estado não espera pelos trilhos nem pelas sugestões de apoio", t < 5000, f"{t:.0f} ms")
    # painel: abrir, sair e voltar no mesmo 2 min não recarrega
    pg.evaluate("window.__msgs = 0; mudar('painel')"); pg.wait_for_timeout(2500)
    pg.evaluate("""(() => { const w = document.querySelector('#painel-f').contentWindow; const p0 = w.postMessage.bind(w); w.postMessage = (...a) => { window.__msgs++; return p0(...a); }; })()""")
    pg.evaluate("mudar('mapa')"); pg.wait_for_timeout(200); pg.evaluate("mudar('painel')"); pg.wait_for_timeout(300)
    m1 = pg.evaluate("window.__msgs")
    pg.clock.run_for(125000); pg.evaluate("mudar('mapa')"); pg.wait_for_timeout(200); pg.evaluate("mudar('painel')"); pg.wait_for_timeout(300)
    m2 = pg.evaluate("window.__msgs")
    passo("5 painel: não recarrega no mesmo 2 min, recarrega depois", m1 == 0 and m2 == 1, f"{m1} {m2}")
    # lista com 750 campos
    t = pg.evaluate("""(() => { const base = S.areas.slice(); const L = [];
      for (let i = 0; L.length < 750; i++) { const a = base[i % base.length]; L.push({ ...a, id: a.id + '-x' + i, produtor: a.produtor + ' ' + i }); }
      S.areas = L; mudar('lista'); const t0 = performance.now(); desenharLista(); const t1 = performance.now(); desenharMapa(); return [t1 - t0, performance.now() - t1]; })()""")
    passo("6 lista e mapa com 750 campos", t[0] < 800 and t[1] < 1500, f"lista {t[0]:.0f} ms, mapa {t[1]:.0f} ms")
    b.close()
print("TUDO OK" if all(res.values()) else "FALHAS: " + ", ".join(k for k, v in res.items() if not v))
