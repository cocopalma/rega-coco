#!/usr/bin/env python3
"""Relatório do dia da Rega Coco para a pasta partilhada com o Dalmar (tarefa das 20:00).

Uso: python3 ferramentas/relatorio_dia.py dados.json Rega_Coco_relatorio_AAAAMMDD
     -> Rega_Coco_relatorio_AAAAMMDD.html, Rega_Coco_relatorio_AAAAMMDD.pdf
        e Rega_Coco_dados.json (na mesma pasta; nome fixo, para o painel do Dalmar)

dados.json = resultado de ferramentas/relatorio_dia.sql (coluna «dados»).
O HTML leva os mesmos dados dentro de <script type="application/json" id="rega-coco-dados">,
para o painel da operação os ler sem interpretar a página.
"""
import html
import json
import sys
from datetime import date, datetime

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


# 08/11/2026 (Valdo): com a monitoria parada (config.monitoria_pausa) a regra r3 não conta nem aparece
MON_PAUSA = False


def regras():
    return tuple(k for k in ('r1', 'r2', 'r3', 'r5', 'r6') if not (k == 'r3' and MON_PAUSA))


def falhas_dia(x):
    f = {'r1': len(x['r1']), 'r2': 0 if (x['fecho'] and x['fecho'] <= '18:00') else 1,
         'r3': 0 if MON_PAUSA else x['r3'], 'r5': len(x['r5']), 'r6': x['r6']}
    f['total'] = sum(f.values())
    return f


DIAS_C = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']
CORES_R = {'r1': '#b3261e', 'r2': '#e8710a', 'r3': '#8e44ad', 'r5': '#f2c94c', 'r6': '#5f5e5a'}
NOMES_R = {'r1': 'Equipa sem rega, sem início do dia e sem motivo', 'r2': 'Dia não fechado na app até às 18:00',
           'r3': 'Campo da monitoria não verificado no dia', 'r5': 'Equipa chegou ao 1.º campo depois da hora combinada',
           'r6': 'Rega fora da lista sem motivo'}


def colunas_dias(dias, alt=60):
    mx = max([falhas_dia(x)['total'] for x in dias] or [0]) or 1
    out = ''
    for x in dias:
        f = falhas_dia(x)
        d = date.fromisoformat(x['data'])
        seg = ''.join(f'<div style="height:{alt * f[k] / mx:.1f}px;background:{CORES_R[k]}"></div>' for k in ('r6', 'r5', 'r3', 'r2', 'r1') if f[k])
        out += (f'<div class="cd"><div class="cd-n">{f["total"]}</div><div class="cd-b" style="height:{alt}px">{seg}</div>'
                f'<div class="cd-l">{DIAS_C[d.weekday()]}<br>{d:%d/%m}</div></div>')
    return f'<div class="cds">{out}</div>'


def bloco_cumprimento(c):
    if not c or not c.get('pessoas'):
        return '<p>Sem dados do cumprimento.</p>'
    global MON_PAUSA
    MON_PAUSA = bool(c.get('monitoria_pausa'))
    ps = c['pessoas']
    hc = c.get('hora_chegada') or '06:00'
    # total de todos por dia
    datas = [x['data'] for x in ps[0]['dias']]
    tot = []
    for i, dt in enumerate(datas):
        agg = {'data': dt, 'r1': [], 'fecho': '00:00', 'r3': 0, 'r5': [], 'r6': 0, '_r2': 0}
        for p_ in ps:
            x = p_['dias'][i]
            agg['r1'] += x['r1']; agg['r3'] += x['r3']; agg['r5'] += x['r5']; agg['r6'] += x['r6']
            agg['_r2'] += falhas_dia(x)['r2']
        tot.append(agg)
    # colunas do total (r2 somado à parte)
    mx = max([len(a['r1']) + a['_r2'] + (0 if MON_PAUSA else a['r3']) + len(a['r5']) + a['r6'] for a in tot] or [0]) or 1
    cols = ''
    for a in tot:
        v = {'r1': len(a['r1']), 'r2': a['_r2'], 'r3': 0 if MON_PAUSA else a['r3'], 'r5': len(a['r5']), 'r6': a['r6']}
        t = sum(v.values())
        d = date.fromisoformat(a['data'])
        seg = ''.join(f'<div style="height:{80 * v[k] / mx:.1f}px;background:{CORES_R[k]}"></div>' for k in ('r6', 'r5', 'r3', 'r2', 'r1') if v[k])
        cols += f'<div class="cd"><div class="cd-n">{t}</div><div class="cd-b" style="height:80px">{seg}</div><div class="cd-l">{DIAS_C[d.weekday()]}<br>{d:%d/%m}</div></div>'
    leg = ' · '.join(f'<span class="sq" style="background:{CORES_R[k]}"></span>{e(NOMES_R[k])}' for k in regras())
    out = (f'<h3>Todos os técnicos e supervisores, por dia</h3><div class="cds">{cols}</div>'
           f'<div class="leg">{leg}</div>')
    for p_ in ps:
        hoje = p_['dias'][-1]
        f = falhas_dia(hoje)
        ant = [falhas_dia(x)['total'] for x in p_['dias'][:-1]]
        med = round(sum(ant) / len(ant), 1) if ant else None
        if med is None:
            tend = ''
        elif f['total'] < med:
            tend = f'<span class="ok">▼ melhor do que a média dos dias anteriores ({str(med).replace(".", ",")})</span>'
        elif f['total'] > med:
            tend = f'<span class="verm">▲ pior do que a média dos dias anteriores ({str(med).replace(".", ",")})</span>'
        else:
            tend = f'= igual à média dos dias anteriores ({str(med).replace(".", ",")})'
        seguidos = 0
        for x in reversed(p_['dias']):
            if falhas_dia(x)['total'] == 0:
                seguidos += 1
            else:
                break
        itens = []
        if hoje['fecho'] and hoje['fecho'] <= '18:00':
            itens.append(f'<li class="ok">Fechou o dia às {e(hoje["fecho"])} (limite: 18:00)</li>')
        elif hoje['fecho']:
            itens.append(f'<li class="verm">Fechou o dia às {e(hoje["fecho"])} (limite: 18:00)</li>')
        else:
            itens.append('<li class="verm">Não fechou o dia na app</li>')
        if hoje['r1']:
            itens.append(f'<li class="verm">{len(hoje["r1"])} equipa(s) sem rega, sem início do dia e sem motivo: {e(", ".join(pnome(n) for n in hoje["r1"]))}</li>')
        if hoje['r3'] and not MON_PAUSA:
            itens.append(f'<li class="verm">{hoje["r3"]} campo(s) da monitoria não verificados no dia</li>')
        if hoje['r5']:
            itens.append(f'<li class="amar">{len(hoje["r5"])} equipa(s) chegaram ao 1.º campo depois das {e(hc)} (hora combinada): '
                         + e(', '.join(f'{pnome(z["nome"])} às {z["hora"]}' + (f' (foi buscar água às {z["agua"]})' if z.get('agua') else '') for z in sorted(hoje['r5'], key=lambda z: z['hora']))) + '</li>')
        if hoje['r6']:
            itens.append(f'<li class="verm">{hoje["r6"]} rega(s) fora da lista sem motivo</li>')
        if p_.get('r4_por_tratar'):
            itens.append(f'<li class="amar">⚠️ {p_["r4_por_tratar"]} rega(s) com aviso por confirmar ou corrigir (desde o início)</li>')
        if p_.get('r8_por_confirmar'):
            itens.append(f'<li class="amar">{p_["r8_por_confirmar"]} motivo(s) do activista por confirmar</li>')
        cor = 'ok' if f['total'] == 0 else 'verm'
        seq = f' · {seguidos} dia(s) seguidos sem falhas' if seguidos > 1 else ''
        out += (f'<div class="pess"><div class="pess-t"><b>{e(p_["nome"])}</b> <span class="cinz">· {e({"tecnico": "técnico", "supervisor": "supervisor"}.get(p_["papel"], p_["papel"]))} · {p_["equipas"]} equipas</span>'
                f'<span class="pess-n {cor}">{f["total"]}</span></div>'
                f'<div class="cinz">Falhas hoje: {f["total"]}{seq}. {tend}</div>'
                f'<ul>{"".join(itens)}</ul>{colunas_dias(p_["dias"])}</div>')
    ini = date.fromisoformat(c['inicio'])
    out += (f'<p class="cinz">Conta de segunda a sábado, desde {ini:%d/%m/%Y}, com as equipas que cada pessoa tem hoje. '
            'Uma falha por equipa sem rega nem motivo, por dia não fechado até às 18:00, '
            + ('' if MON_PAUSA else 'por campo da monitoria não verificado, ')
            + f'por equipa que chegou ao 1.º campo depois das {e(hc)} (hora combinada) e por rega fora da lista sem motivo. '
            + ('A monitoria está parada: não conta. ' if MON_PAUSA else '')
            +
            'As regas com aviso e os motivos por confirmar são o que está por tratar hoje.</p>')
    return out


CAT_EQ = [('ok', '#2f7d4f', 'Regou · chegou a horas'), ('tarde', '#f2c94c', 'Regou · chegou depois da hora'),
          ('motivo', '#c8c6bd', 'Sem rega · com motivo'), ('sem', '#b3261e', 'Sem rega · sem motivo')]


def resumo_equipas(eqs, hc):
    """Resumo da tabela «Todas as equipas»: por técnico, quantas equipas em cada situação (Valdo, 08/11/2026)."""
    hc = hc or '06:00'

    def cat(x):
        if x['regas']:
            return 'tarde' if (x.get('chegada_1o_campo') or '') > hc else 'ok'
        return 'motivo' if x['motivos_sem_rega'] else 'sem'

    grupos = {}
    for x in eqs:
        grupos.setdefault(x.get('tecnico') or 'Sem técnico', []).append(cat(x))
    todos = [cat(x) for x in eqs]
    mx = max([len(v) for v in grupos.values()] + [1])

    def linha(rot, cats, larg):
        v = {k: cats.count(k) for k, _, _ in CAT_EQ}
        seg = ''.join(f'<div style="width:{100 * v[k] / larg:.2f}%;background:{cor}" title="{t}: {v[k]}">{v[k]}</div>'
                      for k, cor, t in CAT_EQ if v[k])
        return (f'<div class="b"><div class="b-nome">{rot}</div><div class="b-trilho rs">{seg}</div>'
                f'<div class="b-val">{len(cats)} equipas</div></div>')

    ordem = sorted(grupos, key=lambda t: (t == 'Sem técnico', -len(grupos[t]), t))
    leg = ' · '.join(f'<span class="sq" style="background:{cor}"></span>{e(t)}' for k, cor, t in CAT_EQ)
    tot = {k: todos.count(k) for k, _, _ in CAT_EQ}
    frase = (f"{tot['ok'] + tot['tarde']} de {len(todos)} equipas regaram ({tot['tarde']} chegaram ao 1.º campo depois das {e(hc)}); "
             f"{tot['motivo']} sem rega com motivo; {tot['sem']} sem rega e sem motivo.")
    return (f'<div class="resumo"><h3>Resumo da tabela</h3><p class="cinz">{frase}</p>'
            + linha('<b>Todas</b>', todos, len(todos))
            + '<div class="cinz" style="margin:8px 0 2px">Por técnico</div>'
            + ''.join(linha(e(t), grupos[t], mx) for t in ordem)
            + f'<div class="leg">{leg}</div></div>')


def gerar(d):
    r, m = d['rega'], d['manutencao']
    dia = date.fromisoformat(d['data'])
    titulo_dia = f'{DIAS[dia.weekday()]}, {dia:%d/%m/%Y}'
    lido = datetime.fromisoformat(d['gerado_em'][:16])
    lido_txt = f'{lido:%d/%m/%Y} às {lido:%H:%M}'
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
.rs{{display:flex;height:18px}} .rs div{{color:#fff;font-size:11px;font-weight:700;text-align:center;line-height:18px;overflow:hidden}} .rs div[style*='#f2c94c'],.rs div[style*='#c8c6bd']{{color:#1f2a24}}
.grupo{{background:var(--f);border:1px solid var(--b);border-radius:10px;padding:8px 12px;margin:8px 0}} .grupo.vermelho{{background:#fcebeb;border-color:#e9b8b8}}
.g-t{{font-weight:700}} .g-n{{background:#fff;border:1px solid var(--b);border-radius:9px;padding:0 7px;font-size:12px}}
ul{{margin:6px 0 0;padding-left:18px}} li{{margin:2px 0;font-size:13.5px}}
.cinz{{color:var(--c);font-size:12.5px}} .verm{{color:#791f1f;font-weight:600}}
.man{{border:1px solid var(--b);border-radius:10px;padding:10px 12px;margin:10px 0}} .man-t{{font-weight:700;margin-bottom:4px}}
.pilha{{display:flex;height:16px;border-radius:5px;overflow:hidden;margin-top:8px}} .leg{{font-size:12px;color:var(--c);margin-top:4px}}
.sq{{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}}
.tab{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:12.5px}} th,td{{border-bottom:1px solid var(--b);padding:6px 5px;text-align:left;vertical-align:top}}
th{{background:var(--f);font-size:12px}} td.c{{text-align:center;white-space:nowrap}}
.cds{{display:flex;gap:6px;align-items:flex-end;overflow-x:auto;margin:8px 0}} .cd{{flex:1;min-width:30px;text-align:center}}
.cd-n{{font-size:12px;font-weight:700}} .cd-b{{display:flex;flex-direction:column-reverse;justify-content:flex-start;background:#f3f2ee;border-radius:4px;overflow:hidden}}
.cd-l{{font-size:10.5px;color:var(--c);line-height:1.2;margin-top:3px}}
.pess{{border:1px solid var(--b);border-radius:10px;padding:10px 12px;margin:10px 0}} .pess-t{{display:flex;align-items:center;gap:6px}}
.pess-n{{margin-left:auto;font-size:20px;font-weight:700;border-radius:8px;padding:0 10px}} .pess-n.ok{{background:#eaf3de;color:#27500a}} .pess-n.verm{{background:#fcebeb;color:#791f1f}}
li.ok,span.ok{{color:#27500a}} li.verm{{color:#791f1f}} li.amar{{color:#633806}}
footer{{color:var(--c);font-size:12px;margin-top:24px;border-top:1px solid var(--b);padding-top:8px}}
@media (max-width:560px){{.kpis{{grid-template-columns:repeat(2,1fr)}} .b{{grid-template-columns:42% 1fr auto}} h1{{font-size:20px}}}}
@media print{{body{{font-size:11.5px;font-family:"DejaVu Sans","Liberation Sans",sans-serif}} main{{max-width:none;padding:0}} h2,h3{{break-after:avoid}} .man,.grupo,.k,tr,.pess,.resumo{{break-inside:avoid}} .tab{{overflow:visible}}}}
@page{{size:A4;margin:12mm}}
</style></head><body><main>
<header><h1>Rega Coco — relatório do dia</h1>
<div class="sub">{titulo_dia} · dados lidos da app a {lido_txt} · regas reais (sem testes) · Projeto de Desenvolvimento da Cadeia de Valor do Coco · Palma</div></header>

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

<h2>Técnicos e supervisores — incumprimentos e progresso</h2>
{bloco_cumprimento(d.get('cumprimento'))}

<h2>Todas as equipas</h2>
<div class="tab"><table><thead><tr><th>Equipa (activista)</th><th>Hoje</th><th>Pessoas</th><th>1.º campo</th><th>Ronda · campos</th><th>Dificuldades</th><th>Técnico / supervisor</th></tr></thead>
<tbody>{linhas}</tbody></table></div>
{resumo_equipas(eqs, r.get('hora_combinada_chegada'))}

<footer>Fonte: app Rega Coco (servidor). Só regas reais; as regas de teste não contam. Regas do dia {dia:%d/%m/%Y} que já tinham chegado ao servidor quando os dados foram lidos ({lido_txt}). Uma rega deste dia que chegue depois (telefone sem rede) não entra neste relatório; fica na app e no painel. Os dados deste relatório estão também em JSON dentro do ficheiro (elemento «rega-coco-dados») e no Rega_Coco_dados.json, com a lista completa dos campos (na rega e retirados, chave «campos»).</footer>
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
    # Os mesmos dados que vão dentro do HTML, num ficheiro de nome fixo (Valdo, 08/11/2026).
    js = os.path.join(os.path.dirname(base), 'Rega_Coco_dados.json')
    with open(js, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(base + '.html', base + '.pdf', js)
