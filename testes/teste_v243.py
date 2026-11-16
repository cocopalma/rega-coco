# v243: painel › «Reforço entre equipas: responsável e executor» (desenho com dados de exemplo; sem servidor). LING=en / sw.
# Precisa da app servida em localhost:8891 (python3 -m http.server 8891 na raiz do repositório).
import os, sys
from playwright.sync_api import sync_playwright
LG = os.environ.get("LING", "pt"); res = {}
def passo(k, v, extra=""): res[k] = bool(v); print(k, "OK" if v else "FALHOU", extra)
T = {"pt": ("Responsável (dono do campo)", "Executor (quem regou)"), "en": ("Owner (team of the field)", "Executor (who watered)"), "sw": None}[LG]
D = """{regas:[{data:'2026-11-06',campo:'PR1-1',produtor:'Ana',comunidade:'Senga',zona:null,responsavel:'Julia Jaime',executor:'Mariano Tomás',plantas:29,pessoas:8},
{data:'2026-11-07',campo:'PR2-1',produtor:'Bia',comunidade:'Senga',zona:null,responsavel:'Julia Jaime',executor:'Mariano Tomás',plantas:71,pessoas:8}],
activos:[{executor:'Ali',responsavel:'Ibraimo',campos:33,inicio:'2026-11-15T21:10:00+02:00',so_actividade:true}]}"""
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1200, "height": 900})
    ctx.add_init_script(f"try{{localStorage.setItem('rega.lingua','{LG}')}}catch(e){{}}")
    pg = ctx.new_page(); erros = []; pg.on("pageerror", lambda e: erros.append(str(e)))
    pg.route("**/*supabase.co/**", lambda r: r.abort())
    UMD = next(x for x in ["node_modules/@supabase/supabase-js/dist/umd/supabase.js", "/home/claude/rega-test/node_modules/@supabase/supabase-js/dist/umd/supabase.js"] if os.path.exists(x))
    pg.route("**/supabase.js", lambda r: r.fulfill(path=UMD, content_type="application/javascript"))
    pg.goto("http://localhost:8891/painel.html?embutido=1"); pg.wait_for_timeout(2500)
    pg.evaluate("document.querySelectorAll('body > *').forEach(e => e.hidden = false); let x = document.querySelector('#s-apo'); while (x) { x.hidden = false; if (x.style) x.style.display = ''; x = x.parentElement }")
    pg.evaluate(f"DAP = {D}; desenharApoios(); if (window.I18N && I18N.aplicar) I18N.aplicar()"); pg.wait_for_timeout(800)
    t = pg.inner_text("#s-apo")
    passo("1 secção visível com dados", not pg.evaluate("document.querySelector('#s-apo').hidden"))
    passo("2 cartões: 2 regas, 100 plantas, 1 apoio activo", pg.locator("#k-apo .val").all_inner_texts() == ["2", "100", "1"], str(pg.locator("#k-apo .val").all_inner_texts()))
    passo("3 tabela com responsável e executor", "Julia Jaime" in pg.inner_text("#t-apo") and "Mariano Tomás" in pg.inner_text("#t-apo") and pg.locator("#t-apo tbody tr").count() == 2)
    if T: passo("4 cabeçalhos na língua", T[0] in t and T[1] in t, t[:300].replace("\n", " | "))
    passo("5 apoios activos", "Ibraimo" in pg.inner_text("#t-apo-act"))
    pg.evaluate("DAP = null; desenharApoios()")
    passo("6 sem dados a secção esconde-se", pg.evaluate("document.querySelector('#s-apo').hidden"))
    passo("7 sem erros de JS", not [e for e in erros if 'fetch' not in e.lower()], str(erros[:3]))
    pg.evaluate(f"DAP = {D}; desenharApoios()"); pg.locator("#s-apo").screenshot(path=f"/tmp/claude-0/-home-claude/2a67f740-10a3-5b35-b093-4e5b7aa6e992/scratchpad/v243_{LG}.png")
    b.close()
print("RESULTADO", "OK" if all(res.values()) else "FALHOU"); sys.exit(0 if all(res.values()) else 1)
