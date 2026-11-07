#!/usr/bin/env python3
"""Corta o resumo para a equipa em imagens do tamanho do ecrã do telefone (390 × 844, escala 2),
para o WhatsApp mostrar cada uma no ecrã inteiro (Valdo, 07/11/2026: "ocupe o ecrã inteiro do telefone…
depois podem ir fazendo scroll"). Junta secções inteiras por imagem, sem as cortar a meio.
Uso: python3 resumo_imagens.py Rega_Coco_resumo_AAAAMMDD.html   → Rega_Coco_resumo_AAAAMMDD_1.png, _2.png, …"""
import sys, os
from playwright.sync_api import sync_playwright

L, A = 390, 844          # ecrã de telefone (proporção 9:19,5)

def cortar(html_path):
    base = os.path.splitext(html_path)[0]
    saidas = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': L, 'height': A}, device_scale_factor=2)
        pg.goto('file://' + os.path.abspath(html_path))
        # blocos = cabeçalho + números grandes (juntos) e cada secção
        alturas = pg.evaluate("""() => { const m = document.querySelector('main'); const filhos = [...m.children];
            filhos.forEach((e, i) => e.dataset.i = i);
            return filhos.map(e => { const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
              return r.height + parseFloat(cs.marginTop) + parseFloat(cs.marginBottom); }); }""")
        n = len(alturas)
        # grupos gananciosos: o cabeçalho (0) vai sempre com o bloco seguinte (1)
        livre = int(A * 1.05) - 40   # espaço para a etiqueta «… 1/N» e margens; aceita até 5 % mais alto do que o ecrã
        grupos, g, h = [], [0, 1], alturas[0] + alturas[1]
        for i in range(2, n):
            if h + alturas[i] <= livre: g.append(i); h += alturas[i]
            else: grupos.append(g); g, h = [i], alturas[i]
        grupos.append(g)
        titulo = pg.evaluate("document.querySelector('header h1').textContent")
        for k, g in enumerate(grupos, 1):
            pg.evaluate("""([g, k, n, t]) => { const m = document.querySelector('main');
                [...m.children].forEach(e => { if (e.dataset.i != null) e.style.display = g.includes(+e.dataset.i) ? '' : 'none'; });
                let et = document.getElementById('pag'); if (!et) { et = document.createElement('div'); et.id = 'pag';
                  et.style.cssText = 'font-size:12px;color:#5F5E5A;text-align:right;margin:0 0 4px'; m.prepend(et); }
                et.textContent = (g.includes(0) ? '' : 'Rega Coco · ' + t + ' · ') + k + '/' + n; }""", [g, k, len(grupos), titulo])
            alto = pg.evaluate("document.querySelector('main').getBoundingClientRect().height")
            pg.set_viewport_size({'width': L, 'height': max(A, int(alto) + 4)})
            out = f'{base}_{k}.png'
            pg.screenshot(path=out)
            pg.set_viewport_size({'width': L, 'height': A})
            saidas.append(out)
        b.close()
    return saidas

if __name__ == '__main__':
    for s in cortar(sys.argv[1]): print(s)
