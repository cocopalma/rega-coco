# Uso: python3 i18n_add.py vNNN ficheiro.json   (json: {"pt": ["en", "sw"], ...})
# Acrescenta no topo dos dicionários D (i18n.js) e I18N_SW_D (i18n-sw.js) as chaves que ainda não existem.
import json, re, sys
ver, fj = sys.argv[1], sys.argv[2]
novas = json.load(open(fj))
R = "/home/claude/rega-coco/"
import ast
def chaves(txt):
    r = set()
    for m in re.finditer(r"""(["'])((?:\\.|(?!\1).)*?)\1\s*:""", txt):
        try: r.add(ast.literal_eval(m.group(1) + m.group(2) + m.group(1)))
        except Exception: pass
    return r
for f, marca, idx in [("i18n.js", "  const D = {\n", 0), ("i18n-sw.js", "window.I18N_SW_D = {\n", 1)]:
    s = open(R + f).read(); i = s.index(marca) + len(marca)
    fim = s.index("\n  };", i) if f == "i18n.js" else s.index("\n};", i)
    ex = chaves(s[i:fim])
    falta = {k: v[idx] for k, v in novas.items() if k not in ex}
    if not falta: print(f, "nada a acrescentar"); continue
    linha = "    // " + ver + "\n    " + ", ".join(json.dumps(k, ensure_ascii=False) + ": " + json.dumps(v, ensure_ascii=False) for k, v in falta.items()) + ",\n"
    s = s[:i] + linha + s[i:]; open(R + f, "w").write(s); print(f, "+", len(falta), "| já existiam:", [k for k in novas if k in ex])
