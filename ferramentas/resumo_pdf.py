#!/usr/bin/env python3
"""PDF do resumo para a equipa: uma página por folha, do tamanho do ecrã do telefone (Valdo, 07/11/2026:
"anexas no email das 22:30 o html e pdf"). Texto em vector (lê-se com zoom).
Uso: python3 resumo_pdf.py Rega_Coco_resumo_AAAAMMDD.html   → Rega_Coco_resumo_AAAAMMDD.pdf"""
import sys, os
from playwright.sync_api import sync_playwright

L, A = 390, 844

def pdf(html_path):
    out = os.path.splitext(html_path)[0] + '.pdf'
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': L, 'height': A})
        pg.goto('file://' + os.path.abspath(html_path))
        alto = pg.evaluate("Math.max(...[...document.querySelectorAll('.folha .dentro')].map(e => e.getBoundingClientRect().height))")
        h = max(A, int(alto) + 8)
        # cada folha numa página; sem a frase «Deslize para o lado» (no PDF passa-se de página)
        pg.add_style_tag(content=f"@page{{size:{L}px {h}px;margin:0}} html,body{{height:auto!important;overflow:visible!important;background:#F6F5F1}}"
                                 f"main.folhas{{display:block!important;height:auto!important;overflow:visible!important}}"
                                 f".folha{{height:{h}px!important;overflow:hidden!important;break-after:page}} .folha:last-child{{break-after:auto}} .desl{{display:none!important}}")
        pg.pdf(path=out, width=f'{L}px', height=f'{h}px', print_background=True, margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
        b.close()
    return out

if __name__ == '__main__':
    print(pdf(sys.argv[1]))
