#!/usr/bin/env python3
"""Uma imagem por folha do resumo para a equipa, do tamanho do ecrã do telefone (390 × 844, escala 2),
para o WhatsApp mostrar cada uma no ecrã inteiro (Valdo, 07/11/2026).
Uso: python3 resumo_imagens.py Rega_Coco_resumo_AAAAMMDD.html   → Rega_Coco_resumo_AAAAMMDD_1.png, _2.png, …"""
import sys, os
from playwright.sync_api import sync_playwright

L, A = 390, 844

def cortar(html_path):
    base = os.path.splitext(html_path)[0]
    saidas = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': L, 'height': A}, device_scale_factor=2)
        pg.goto('file://' + os.path.abspath(html_path))
        n = pg.evaluate("document.querySelectorAll('.folha').length")
        for k in range(1, n + 1):
            alto = pg.evaluate(f"document.querySelector('#f{k} .dentro').getBoundingClientRect().height")
            # mostra só esta folha, com a altura do conteúdo (no mínimo o ecrã)
            pg.evaluate(f"""() => {{ document.querySelectorAll('.folha').forEach(f => f.style.display = f.id === 'f{k}' ? '' : 'none');
                document.querySelectorAll('.desl').forEach(e => e.style.display = 'none'); }}""")
            pg.set_viewport_size({'width': L, 'height': max(A, int(alto) + 4)})
            out = f'{base}_{k}.png'
            pg.screenshot(path=out)
            pg.evaluate("() => document.querySelectorAll('.folha').forEach(f => f.style.display = '')")
            pg.set_viewport_size({'width': L, 'height': A})
            saidas.append(out)
        b.close()
    return saidas

if __name__ == '__main__':
    for s in cortar(sys.argv[1]): print(s)
