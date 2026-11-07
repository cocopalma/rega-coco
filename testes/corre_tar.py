# Corre um teste antigo com todas as linhas do Hoje abertas (v212: o Hoje do técnico/supervisor passou a ter linhas que abrem ao tocar).
import sys, runpy
from playwright.sync_api._generated import Browser
_orig = Browser.new_context
def _nc(self, *a, **k):
    ctx = _orig(self, *a, **k); ctx.add_init_script("window.__TAR_ABERTAS = true;"); return ctx
Browser.new_context = _nc
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
