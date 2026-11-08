#!/usr/bin/env python3
"""Relatório do dia da Rega Coco para a pasta partilhada com o Dalmar (tarefa das 19:00).

Uso: python3 ferramentas/relatorio_dia.py dados.json Rega_Coco_relatorio_AAAAMMDD
     -> Rega_Coco_relatorio_AAAAMMDD.html e Rega_Coco_relatorio_AAAAMMDD.pdf

dados.json = resultado de ferramentas/relatorio_dia.sql (coluna «dados»).
O HTML leva os mesmos dados dentro de <script type="application/json" id="rega-coco-dados">,
para o painel da operação os ler sem interpretar a página.
"""
import html
import json
import sys
from datetime import date

DIAS = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
MOTIVOS = {
    'tuk_tuk': 'Tuk-tuk não chegou ou insuficiente',
    'avaria_tuk_tuk': 'Tuk-tuk avariado',
    'avaria_camiao': 'Camião avariado',
    'sem_agua': 'Sem água na fonte',
    'chuva': 'Chuva',
    'material': 'Falta de material',
    'equipa': 'Equipa não compareceu',
    'regou_sem_registo': 'Regou, mas não registou na app',
}
CONS = {
    'mudas_secas': 'Mudas secas ou mortas',
    'agua_acabou': 'A água acabou',
    'sem_agua_fonte': 'Não havia água na fonte',
    'agua_atrasada': 'Esperámos pela água',
    'avaria': 'Avaria',
    'acesso_dificil': 'Acesso difícil',
    'falta_agua': 'Falta de água',
    'outro': 'Outro',
}


def e(t):
    return html.escape('' if t is None else str(t))


def n(x):
    return f'{int(x or 0):,}'.replace(',', ' ')


def pct(a, b):
    return round(100 * a / b) if b else 0


def pnome(nome):
    return (nome or '').split(' ')[0]


def curto(t, m=70):
    t = ' '.join((t or '').split())
    return t if len(t) <= m else t[:m - 1].rstrip() + '…'


def barra(rotulo, valor, maximo, txt, cor='#2f7d4f', sub=''):
    w = 0 if not maximo else max(2, round(100 * valor / maximo)) if valor else 0
    s = f'<div class="b-sub">{sub}</div>' if sub else ''
    return (f'<div class="b"><div class="b-nome">{rotulo}{s}</div>'
            f'<div class="b-trilho"><div class="b-enc" style="width:{w}%;background:{cor}"></div></div>'
            f'<div class="b-val">{txt}</div></div>')


def cartao(valor, titulo, sub='', cls=''):
    s = f'<div class="k-sub">{sub}</div>' if sub else ''
    return f'<div class="k {cls}"><div class="k-v">{valor}</div><div class="k-t">{titulo}</div>{s}</div>'


def gerar(d):
    r, m = d['rega'], d['manutencao']
    dia = date.fromisoformat(d['data'])
    titulo_dia = f'{DIAS[dia.weekday()]}, {dia:%d/%m/%Y}'
    hora = d['gerado_em'][11:16]
    eqs = r['por_equipa']
    com = [x for x in eqs if x['regas'] > 0]
    sem = [x for x in eqs if x['regas'] == 0]
    assert len(com) == r['equipas_com_rega'] and len(eqs) == r['equipas_total'], 'equipas não batem'
    assert sum(x['plantas'] for x in eqs) == r['plantas_regadas'], 'plantas não batem'
    ppp = round(r['plantas_regadas'] / r['pessoas']) if r['pessoas'] else None
    rp = pct(r['campos_ronda_regados'], r['campos_ronda_lista'])
    desde = date.fromisoformat(r['desde'])

    k = [
        cartao(f"{r['equipas_com_rega']}<small>/{r['equipas_total']}</small>", 'equipas regaram'),
        cartao(n(r['campos_regados']), 'campos regados', f"{n(r['regas'])} regas"),
        cartao(n(r['plantas_regadas']), 'plantas regadas', f"{n(r['pessoas'])} pessoas · {ppp} por pessoa" if ppp else ''),
        cartao(n(r['plantas_acumuladas_app']), 'plantas regadas na app', f'desde {desde:%d/%m}'),
        cartao(f'{rp}%', 'progresso da ronda', f"{n(r['campos_ronda_regados'])} de {n(r['campos_ronda_lista'])} campos"),
        cartao(n(r['campos_nunca_receberam_agua']), 'campos nunca receberam água', 'nem na app nem no WhatsApp', 'alerta'),
    ]

    # Equipas que regaram: plantas
    mx = max([x['plantas'] for x in com] or [0])
    bar_com = ''.join(barra(e(x['activista']), x['plantas'], mx,
                            f"{n(x['plantas'])} pl. · {x['campos']} campos",
                            sub=e(f"1.º campo às {x['chegada_1o_campo']}" + (f" · {x['pessoas']} pessoas" if x['pessoas'] else '')
                                  + (' · sem telefone' if x['sem_telefone'] else '')))
                      for x in com)

    # Equipas sem rega, por motivo
    grupos = {}
    for x in sem:
        if x['motivos_sem_rega']:
            mo = x['motivos_sem_rega'][0]
            rot = MOTIVOS.get(mo['motivo']) or ('Outro: ' + curto(mo.get('descricao'), 60) if mo.get('descricao') else 'Outro')
        else:
            rot = 'Sem motivo registado'
        nota = ''
        if not x['motivos_sem_rega'] and x['inicio_dia']:
            nota = f"início do dia às {x['inicio_dia']}"
        elif x['motivos_sem_rega'] and x['motivos_sem_rega'][0].get('descricao') and x['motivos_sem_rega'][0]['motivo'] != 'outro':
            nota = curto(x['motivos_sem_rega'][0]['descricao'], 90)
        grupos.setdefault(rot, []).append((x, nota))
    ordem = sorted(grupos, key=lambda g: (g == 'Sem motivo registado', -len(grupos[g]), g))
    sem_html = ''
    for g in ordem:
        cls = ' vermelho' if g == 'Sem motivo registado' else ''
        itens = ''.join(f"<li><b>{e(x['activista'])}</b> <span class='cinz'>· técnico {e(pnome(x['tecnico']))} · supervisor {e(pnome(x['supervisor']))}"
                        + (f' · {e(nota)}' if nota else '') + '</span></li>' for x, nota in grupos[g])
        sem_html += f'<div class="grupo{cls}"><div class="g-t">{e(g)} <span class="g-n">{len(grupos[g])}</span></div><ul>{itens}</ul></div>'
    if not sem:
        sem_html = '<p>Todas as equipas regaram.</p>'

    # Constrangimentos na saída da rega
    ct = {}
    for x in com:
        for c in x['constrangimentos']:
            t = ct.setdefault(c['tipo'], {'campos': set(), 'plantas': 0})
            t['campos'].add(c['pr'])
            t['plantas'] += c.get('plantas') or 0
    cons_html = ''.join(f"<li><b>{e(CONS.get(t, t))}</b>: {len(v['campos'])} campos"
                        + (f" · {n(v['plantas'])} plantas" if t == 'mudas_secas' and v['plantas'] else '') + '</li>'
                        for t, v in sorted(ct.items(), key=lambda i: -len(i[1]['campos'])))

    # Progresso da ronda por equipa
    eq_r = sorted(eqs, key=lambda x: (-(x['ronda_actual'] or 0), -pct(x['regados_na_ronda'] or 0, x['campos_na_lista'] or 0)))
    bar_ronda = ''.join(barra(e(x['activista']), x['regados_na_ronda'] or 0, x['campos_na_lista'] or 0,
                              f"{x['regados_na_ronda'] or 0}/{x['campos_na_lista'] or 0}", '#1f6f8b',
                              sub=e(f"Ronda {x['ronda_actual']}" + (f" · {x['nunca_receberam_agua']} campos nunca receberam água" if x['nunca_receberam_agua'] else '')))
                        for x in eq_r)

    # Plantas por comunidade
    pc = r['por_comunidade']
    mxc = max([c['plantas'] for c in pc] or [0])
    bar_com_c = ''.join(barra(e(c['comunidade']), c['plantas'], mxc, f"{n(c['plantas'])} pl. · {c['campos']} campos", '#7a5c2e') for c in pc)

    # Manutenção
    man_html = ''
    if m['por_comunidade']:
        tot_p = sum(c['plantas'] for c in m['por_comunidade'])
        tot_c = sum(c['cavaroda'] for c in m['por_comunidade'])
        tot_m = sum(c['mulching'] for c in m['por_comunidade'])
        h = m.get('hoje') or {}
        hoje_txt = (f"Hoje: {h.get('campos', 0)} campos com trabalho registado · +{n(h.get('cavaroda'))} plantas com cava-roda · +{n(h.get('mulching'))} com mulching"
                    + (' (' + ', '.join(f"{e(c['comunidade'])}: {c['campos']} campos" for c in m.get('hoje_por_comunidade') or []) + ')' if m.get('hoje_por_comunidade') else '')
                    if h.get('campos') else 'Hoje: sem trabalho de manutenção registado na app.')
        man_html += f'<p class="cinz">{hoje_txt}</p>'
        man_html += '<div class="kpis">' + cartao(f'{pct(tot_c, tot_p)}%', 'plantas com cava-roda', f'{n(tot_c)} de {n(tot_p)}') + cartao(f'{pct(tot_m, tot_p)}%', 'plantas com mulching', f'{n(tot_m)} de {n(tot_p)}') + '</div>'
        for c in m['por_comunidade']:
            seg = [('feitos', c['feitos'], '#5b3a1e', 'Feito'), ('completos', c['completos'], '#c9a26b', 'Completo, por confirmar'),
                   ('em_curso', c['em_curso'], '#f2c94c', 'Em curso'), ('por_fazer', c['por_fazer'], '#c8c6bd', 'Por fazer'),
                   ('sem_plantas', c['sem_plantas'], '#e8e6df', 'Sem plantas')]
            total = sum(s[1] for s in seg) or 1
            st = ''.join(f'<div style="width:{100 * v / total:.2f}%;background:{cor}" title="{t}: {v}"></div>' for _, v, cor, t in seg if v)
            leg = ' · '.join(f'<span class="sq" style="background:{cor}"></span>{t} {v}' for _, v, cor, t in seg if v)
            man_html += (f'<div class="man"><div class="man-t">{e(c["comunidade"])} <span class="cinz">· {c["campos"]} campos · {n(c["plantas"])} plantas</span></div>'
                         + barra('Cava-roda', c['cavaroda'], c['plantas'], f"{pct(c['cavaroda'], c['plantas'])}%", '#5b3a1e')
                         + barra('Mulching', c['mulching'], c['plantas'], f"{pct(c['mulching'], c['plantas'])}%", '#8a6a3b')
                         + f'<div class="pilha">{st}</div><div class="leg">{leg}</div></div>')
    else:
        man_html = '<p>Sem dados de manutenção.</p>'

    # Tabela completa por equipa
    linhas = ''
    for x in eqs:
        if x['regas']:
            sit = f"{x['campos']} campos · {n(x['plantas'])} pl."
        elif x['motivos_sem_rega']:
            mo = x['motivos_sem_rega'][0]
            sit = e('Sem rega: ' + (MOTIVOS.get(mo['motivo']) or curto(mo.get('descricao'), 50) or 'outro'))
        else:
            sit = '<span class="verm">Sem rega · sem motivo</span>'
        cs = '; '.join(sorted({CONS.get(c['tipo'], c['tipo']) for c in x['constrangimentos']}))
        linhas += (f"<tr><td><b>{e(x['activista'])}</b><div class='cinz'>{e(x['comunidade'])}{' · sem telefone' if x['sem_telefone'] else ''}</div></td>"
                   f"<td>{sit}</td><td class='c'>{e(x['pessoas'] or '—')}</td>"
                   f"<td class='c'>{e(x['chegada_1o_campo'] or '—')}</td><td class='c'>{x['ronda_actual']} · {x['regados_na_ronda']}/{x['campos_na_lista']}</td>"
                   f"<td>{e(cs) or '—'}</td><td>{e(pnome(x['tecnico']))} / {e(pnome(x['supervisor']))}</td></tr>")

    dados_json = json.dumps(d, ensure_ascii=False).replace('</', '<\\/')
    return f'''<!doctype html>
<html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rega Coco — relatório do dia {dia:%d/%m/%Y}</title>
<style>
:root{{--t:#1f2a24;--c:#5f5e5a;--b:#d3d1c7;--f:#f6f5f1;--v:#2f7d4f}}
*{{box-sizing:border-box}} body{{margin:0;background:#fff;color:var(--t);font:15px/1.4 -apple-system,"Segoe UI",Roboto,Arial,"Liberation Sans","DejaVu Sans",sans-serif}}
main{{max-width:900px;margin:0 auto;padding:16px}}
header{{border-bottom:3px solid var(--v);padding-bottom:10px;margin-bottom:6px}}
h1{{font-size:22px;margin:0}} .sub{{color:var(--c);font-size:13px;margin-top:4px}}
h2{{font-size:18px;margin:26px 0 8px;padding-top:8px;border-top:1px solid var(--b)}} h3{{font-size:15px;margin:18px 0 8px}}
.kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.k{{background:var(--f);border:1px solid var(--b);border-radius:10px;padding:10px}} .k.alerta{{background:#fcebeb;border-color:#e9b8b8}}
.k-v{{font-size:26px;font-weight:700}} .k-v small{{font-size:15px;color:var(--c)}} .k-t{{font-size:13px}} .k-sub{{font-size:12px;color:var(--c)}}
.b{{display:grid;grid-template-columns:minmax(120px,34%) 1fr auto;gap:8px;align-items:center;margin:6px 0}}
.b-nome{{font-size:13px;font-weight:600}} .b-sub{{font-weight:400;color:var(--c);font-size:11.5px}}
.b-trilho{{background:#ecebe5;border-radius:5px;height:14px;overflow:hidden}} .b-enc{{height:100%}}
.b-val{{font-size:12.5px;white-space:nowrap;text-align:right}}
.grupo{{background:var(--f);border:1px solid var(--b);border-radius:10px;padding:8px 12px;margin:8px 0}} .grupo.vermelho{{background:#fcebeb;border-color:#e9b8b8}}
.g-t{{font-weight:700}} .g-n{{background:#fff;border:1px solid var(--b);border-radius:9px;padding:0 7px;font-size:12px}}
ul{{margin:6px 0 0;padding-left:18px}} li{{margin:2px 0;font-size:13.5px}}
.cinz{{color:var(--c);font-size:12.5px}} .verm{{color:#791f1f;font-weight:600}}
.man{{border:1px solid var(--b);border-radius:10px;padding:10px 12px;margin:10px 0}} .man-t{{font-weight:700;margin-bottom:4px}}
.pilha{{display:flex;height:16px;border-radius:5px;overflow:hidden;margin-top:8px}} .leg{{font-size:12px;color:var(--c);margin-top:4px}}
.sq{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}}
.tab{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:12.5px}} th,td{{border-bottom:1px solid var(--b);padding:6px 5px;text-align:left;vertical-align:top}}
th{{background:var(--f);font-size:12px}} td.c{{text-align:center;white-space:nowrap}}
footer{{color:var(--c);font-size:12px;margin-top:24px;border-top:1px solid var(--b);padding-top:8px}}
@media (max-width:560px){{.kpis{{grid-template-columns:repeat(2,1fr)}} .b{{grid-template-columns:42% 1fr auto}} h1{{font-size:20px}}}}
@media print{{body{{font-size:11.5px;font-family:"DejaVu Sans","Liberation Sans",sans-serif}} main{{max-width:none;padding:0}} h2,h3{{break-after:avoid}} .man,.grupo,.k,tr{{break-inside:avoid}} .tab{{overflow:visible}}}}
@page{{size:A4;margin:12mm}}
</style></head><body><main>
<header><h1>Rega Coco — relatório do dia</h1>
<div class="sub">{titulo_dia} · dados da app às {hora} · regas reais (sem testes) · Projeto de Desenvolvimento da Cadeia de Valor do Coco · Palma</div></header>

<h2>Rega</h2>
<div class="kpis">{''.join(k)}</div>

<h3>Equipas que regaram ({len(com)})</h3>
{bar_com or '<p>Nenhuma rega registada na app.</p>'}
<p class="cinz">Hora combinada de chegada ao 1.º campo: {e(r.get('hora_combinada_chegada'))}.</p>

<h3>Equipas sem rega na app ({len(sem)})</h3>
{sem_html}

{'<h3>O que dificultou a rega (registado na saída)</h3><ul>' + cons_html + '</ul>' if cons_html else ''}

<h3>Plantas regadas por comunidade</h3>
{bar_com_c or '<p>—</p>'}

<h3>Progresso da ronda por equipa (estado de hoje)</h3>
{bar_ronda}

<h2>Manutenção — Quiwia e Farol</h2>
{man_html}

<h2>Todas as equipas</h2>
<div class="tab"><table><thead><tr><th>Equipa (activista)</th><th>Hoje</th><th>Pessoas</th><th>1.º campo</th><th>Ronda · campos</th><th>Dificuldades</th><th>Técnico / supervisor</th></tr></thead>
<tbody>{linhas}</tbody></table></div>

<footer>Fonte: app Rega Coco (servidor). Só regas reais; as regas de teste não contam. Números do dia {dia:%d/%m/%Y} até às {hora}; regas enviadas mais tarde entram no relatório seguinte do mesmo dia, se houver. Os dados deste relatório estão também em JSON dentro do ficheiro (elemento «rega-coco-dados»).</footer>
</main>
<script type="application/json" id="rega-coco-dados">{dados_json}</script>
</body></html>'''


def pdf(html_path, pdf_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto('file://' + html_path)
        pg.pdf(path=pdf_path, format='A4', print_background=True, margin={'top': '12mm', 'bottom': '12mm', 'left': '10mm', 'right': '10mm'})
        b.close()


if __name__ == '__main__':
    import os
    d = json.load(open(sys.argv[1], encoding='utf-8'))
    if 'dados' in d and 'rega' not in d:
        d = d['dados']
    base = os.path.abspath(sys.argv[2])
    open(base + '.html', 'w', encoding='utf-8').write(gerar(d))
    pdf(base + '.html', base + '.pdf')
    print(base + '.html', base + '.pdf')
