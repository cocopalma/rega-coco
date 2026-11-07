# Corre um teste antigo com o novo visual (v212–v213): abre todas as linhas do «O meu dia» (window.__TAR_ABERTAS) e,
# como os filtros dos Campos (#f-ambito, #f-com, #f-act, #f-sit) passaram para a folha «Filtros» (escondidos), escolhe-os por código.
import sys, runpy
from playwright.sync_api._generated import Browser, Page
_orig = Browser.new_context
def _nc(self, *a, **k):
    ctx = _orig(self, *a, **k); ctx.add_init_script("window.__TAR_ABERTAS = true;"); return ctx
Browser.new_context = _nc
_sel = Page.select_option
def _so(self, selector, value=None, **k):
    if isinstance(selector, str) and selector in ("#f-ambito", "#f-com", "#f-act", "#f-sit"):
        lab = k.get("label")
        return self.evaluate("""([s, v, l]) => { const e = document.querySelector(s); const o = [...e.options].find(o => l != null ? o.textContent.trim() === l : o.value === v);
          if (!o) throw new Error('opção não encontrada: ' + (l ?? v)); e.value = o.value; e.dispatchEvent(new Event('change')); return [o.value]; }""", [selector, value, lab])
    return _sel(self, selector, value, **k)
Page.select_option = _so
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
