#!/usr/bin/env python3
"""Resumo do dia para a equipa (técnicos e supervisores): curto, simples, com gráficos.
Aprovado pelo Valdo a 07/11/2026 ("para a minha equipa… simples, concisa e curta… gráficos").
Uso: python3 resumo_equipa.py dados.json saida.html   (só biblioteca padrão; o HTML não precisa de internet)
Esquema do JSON: ver ferramentas/RELATORIO_DIARIO.md, secção «RESUMO PARA A EQUIPA»."""
import json, sys, html

esc = html.escape
fmt = lambda v: f"{int(v):,}".replace(',', ' ')
VERDE, AZUL, AMBAR, VERMELHO, WA = '#3B6D11', '#185FA5', '#BA7517', '#A32D2D', '#0F6E56'
CSS = """:root{color-scheme:light}*{box-sizing:border-box}
body{margin:0;background:#F6F5F1;color:#1f2421;font:16px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:560px;margin:0 auto;padding:12px 16px 32px}
header{display:flex;align-items:baseline;gap:10px;margin:4px 0 10px}header b{color:#1d4d2b;font-size:14px;text-transform:uppercase;letter-spacing:.05em}header h1{margin:0;font-size:22px}
section{background:#fff;border:1px solid #D3D1C7;border-radius:14px;padding:12px 14px;margin:10px 0}
h2{margin:0 0 10px;font-size:16px}h3{font-size:14px;margin:14px 0 6px;color:#5F5E5A}
.big{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.big div{background:#fff;border:1px solid #D3D1C7;border-radius:14px;padding:10px;text-align:center}
.big b{display:block;font-size:30px;line-height:1.1}.big b small{font-size:15px;color:#5F5E5A;font-weight:600}.big span{font-size:12px;color:#5F5E5A}
.trofeu{display:grid;grid-template-columns:1fr 1fr;gap:8px;background:#FAEEDA;border-color:#ead9b8}.trofeu div{display:flex;flex-direction:column}.trofeu span{font-size:12px;color:#633806;font-weight:700}.trofeu b{font-size:20px}.trofeu em{font-style:normal;font-size:13px;color:#633806}
.stk{display:flex;gap:2px;height:38px}.sg{border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;min-width:26px}.sg b{font-size:15px}
.lgs{margin-top:10px;display:flex;flex-direction:column;gap:7px}.lg{display:grid;grid-template-columns:14px 1fr;gap:8px;align-items:start}.lg i{width:14px;height:14px;border-radius:4px;margin-top:3px}
.lg b{display:block;font-size:14px}.lg span{display:block;font-size:13px;color:#5F5E5A}
.cmp{display:flex;flex-direction:column;gap:6px}.cr{display:grid;grid-template-columns:76px 1fr 56px;align-items:center;gap:8px}.cr span{font-size:14px}.cr b{text-align:right;font-variant-numeric:tabular-nums}
.tr{height:22px;background:#F1EFE8;border-radius:4px}.tr i{display:block;height:100%;border-radius:0 4px 4px 0}
.nt{margin:0 0 6px;font-size:13px;color:#5F5E5A}
.ax{position:relative;height:16px;margin-left:78px;font-size:11px;color:#5F5E5A;border-left:2px solid #3B6D11}.ax span{position:absolute;transform:translateX(-50%)}.ax span:first-child{transform:none;padding-left:3px;color:#27500A;font-weight:700}
.ch{display:grid;grid-template-columns:72px 1fr;gap:6px;align-items:center;height:24px}.cn{font-size:13px;text-align:right}
.ct{position:relative;height:14px;border-left:2px solid #3B6D11}.ct i{display:block;height:100%;background:#BA7517;border-radius:0 4px 4px 0;opacity:.85}.ct em{position:absolute;top:-1px;margin-left:5px;font-style:normal;font-size:12px;font-weight:600;white-space:nowrap}
.ct em.dentro{transform:translateX(-100%);margin-left:-5px;color:#fff}.ct em.cedo{color:#27500A}
.fz{display:grid;grid-template-columns:28px 1fr;gap:8px;padding:7px 0;border-top:1px solid #eeece6}.fz:first-of-type{border-top:0}.fi{font-size:20px}.fz b{display:block;font-size:15px}.fz span{display:block;font-size:13px;color:#5F5E5A}
.alerta{border:2px solid #A32D2D}.frase{margin:0 0 10px;font-size:16px}.frase b{color:#A32D2D;font-size:20px}
.tq{padding:7px 0;border-top:1px solid #eeece6}.tqh{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap}.tqh b{font-size:16px}.tqh span{font-size:12px;color:#5F5E5A}.tqh em{margin-left:auto;font-style:normal;font-weight:700;color:#791F1F}
.tqb{height:10px;background:#F1EFE8;border-radius:4px;margin:4px 0}.tqb i{display:block;height:100%;background:#A32D2D;border-radius:0 4px 4px 0}
.tqe{font-size:13px;color:#5F5E5A}.tqe b{color:#1f2421}
.pedido{margin:12px 0;background:#FCEBEB;color:#791F1F;border-radius:10px;padding:10px 12px;font-size:14px}
.ok{margin:0;font-size:15px;color:#27500A;font-weight:600}"""

def mn(h): return int(h[:2]) * 60 + int(h[3:5])

def gerar(d):
    nomes = lambda L: ', '.join(L)
    reg, mot, srg, smo = d['regaram'], d.get('com_motivo', []), d.get('regou_sem_registo', []), d.get('sem_motivo', [])
    n_mot = sum(len(m['equipas']) for m in mot)
    tot = d['equipas_total']
    assert len(reg) + n_mot + len(srg) + len(smo) == tot, 'os grupos têm de somar o total de equipas'
    # 1) números grandes
    ch = sorted(d.get('chegadas', []), key=lambda c: c['hora'])
    hc = d.get('hora_combinada', '06:00')
    tarde = [c for c in ch if mn(c['hora']) > mn(hc)]
    big = (f'<div class=big><div><b>{len(reg)}<small>/{tot}</small></b><span>equipas regaram</span></div>'
           f'<div><b>{fmt(d["plantas_app"])}</b><span>plantas regadas (app)</span></div>'
           f'<div><b>{len(tarde)}<small>/{len(ch)}</small></b><span>chegaram tarde ao 1.º campo</span></div></div>')
    # 2) WhatsApp × app
    wa = d.get('whatsapp')
    if wa is None:
        sec_wa = '<section><h2>📲 WhatsApp × app</h2><p class=nt>O relatório do Dalmar de hoje ainda não chegou: sem comparação.</p></section>'
    else:
        falT, waT = sum(e['faltam'] for t in wa['por_tecnico'] for e in t['equipas']), wa['campos_com_telefone']
        okT = waT - falT
        mx = max(wa['plantas_whatsapp'], d['plantas_app'], 1)
        barras = (f'<div class=cmp><div class=cr><span>WhatsApp</span><div class=tr><i style="width:{wa["plantas_whatsapp"]/mx*100:.1f}%;background:{WA}"></i></div><b>{fmt(wa["plantas_whatsapp"])}</b></div>'
                  f'<div class=cr><span>App</span><div class=tr><i style="width:{d["plantas_app"]/mx*100:.1f}%;background:{AZUL}"></i></div><b>{fmt(d["plantas_app"])}</b></div></div>')
        if falT == 0:
            sec_wa = f'<section><h2>📲 WhatsApp × app</h2><p class=ok>✓ Tudo o que entrou no WhatsApp está igual na app.</p>{barras}</section>'
        else:
            pt = sorted(wa['por_tecnico'], key=lambda t: -sum(e['faltam'] for e in t['equipas']))
            mxt = max(sum(e['faltam'] for e in t['equipas']) for t in pt)
            linhas = ''
            for t in pt:
                n = sum(e['faltam'] for e in t['equipas'])
                eqs = ' · '.join(f"<b>{esc(e['nome'])}</b>: {'falta' if e['faltam']==1 else 'faltam'} {e['faltam']} de {e['de']}{(' (' + esc(e['nota']) + ')') if e.get('nota') else ''}"
                                 for e in sorted(t['equipas'], key=lambda e: -e['faltam']))
                linhas += (f'<div class=tq><div class=tqh><b>{esc(t["tecnico"])}</b><span>técnico · supervisor {esc(t["supervisor"])}</span><em>{n} {"campo" if n==1 else "campos"}</em></div>'
                           f'<div class=tqb><i style="width:{n/mxt*100:.0f}%"></i></div><div class=tqe>{eqs}</div></div>')
            sec_wa = (f'<section class=alerta><h2>📲 Regaram, mas não puseram tudo na app</h2>'
                      f'<p class=frase><b>{falT} de {waT}</b> campos regados no WhatsApp não estão iguais na app.</p>'
                      f'<div class=stk>' + (f'<div class=sg style="flex:{okT};background:{VERDE}"><b>{okT}</b></div>' if okT else '') +
                      f'<div class=sg style="flex:{falT};background:{VERMELHO}"><b>{falT}</b></div></div>'
                      f'<div class=lgs style="flex-direction:row;gap:14px"><div class=lg><i style="background:{VERDE}"></i><div><b>iguais na app</b></div></div><div class=lg><i style="background:{VERMELHO}"></i><div><b>em falta ou diferentes</b></div></div></div>'
                      f'<h3>Quem tem de ir ter com estas equipas</h3>{linhas}'
                      f'<div class=pedido><b>Técnico e supervisor:</b> ir ter com estas equipas, perceber porque não registam na app e registar com elas. O que entra no WhatsApp tem de entrar igual na app.</div>{barras}</section>')
    # 3) melhor equipa
    md, ms = d.get('melhor_dia'), d.get('melhor_semana')
    tro = ''
    if md or ms:
        tro = '<section class=trofeu>'
        if md: tro += f'<div><span>🏆 Hoje</span><b>{esc(md["nome"])}</b><em>{md["ppp"]:.0f} plantas por pessoa</em></div>'
        if ms: tro += f'<div><span>🏆 Semana</span><b>{esc(ms["nome"])}</b><em>{ms["ppp"]:.0f} plantas por pessoa por dia</em></div>'
        tro += '</section>'
    # 4) as equipas hoje
    if len(mot) == 1:
        tmot = mot[0]['motivo'].lower()
    else:
        tmot = 'não regaram, com motivo'
    G = [('regaram', reg, VERDE, ''), (tmot, [e for m in mot for e in m['equipas']], AZUL,
          '' if len(mot) <= 1 else '<br>'.join(f"{esc(m['motivo'])}: {esc(nomes(m['equipas']))}" for m in mot)),
         ('regaram, mas não registaram na app', srg, AMBAR, ''), ('sem motivo', smo, VERMELHO, '')]
    seg = ''.join(f'<div class=sg style="flex:{len(L)};background:{c}" title="{esc(t)}: {len(L)}"><b>{len(L)}</b></div>' for t, L, c, _ in G if L)
    leg = ''.join(f'<div class=lg><i style="background:{c}"></i><div><b>{len(L)} {esc(t)}</b><span>{sub or esc(nomes(L))}</span></div></div>' for t, L, c, sub in G if L)
    sec_eq = f'<section><h2>As {tot} equipas hoje</h2><div class=stk>{seg}</div><div class=lgs>{leg}</div></section>'
    # 5) chegadas
    sec_ch = ''
    if ch:
        T0 = mn(hc); T1 = max(T0 + 300, ((max(mn(c['hora']) for c in ch) // 60) + 1) * 60)
        ticks = ''.join(f'<span style="left:{(h*60-T0)/(T1-T0)*100:.2f}%">{h:02d}:00</span>' for h in range(T0 // 60, T1 // 60 + 1, 2))
        rows = ''
        for c in ch:
            f = max(0, (mn(c['hora']) - T0) / (T1 - T0))
            cls = 'cedo' if f == 0 else ('dentro' if f > 0.8 else '')
            rows += (f'<div class=ch><span class=cn>{esc(c["nome"])}</span><div class=ct><i style="width:{f*100:.1f}%" title="{esc(c["nome"])}: {c["hora"]}"></i>'
                     f'<em class="{cls}" style="left:{f*100:.1f}%">{c["hora"]}</em></div></div>')
        sec_ch = f'<section><h2>Chegada ao 1.º campo</h2><p class=nt>Combinado: {hc}. A barra é o atraso.</p><div class=ax>{ticks}</div>{rows}</section>'
    # 6) a fazer
    faz = ''.join(f'<div class=fz><span class=fi>{f["icone"]}</span><div><b>{esc(f["titulo"])}</b><span>{esc(f["detalhe"])}</span></div></div>' for f in d.get('a_fazer', []))
    sec_faz = f'<section><h2>{esc(d.get("proximo_dia", "Amanhã"))}</h2>{faz}</section>' if faz else ''
    return (f'<!doctype html><html lang=pt><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>Rega Coco — {esc(d["titulo_data"])}</title><style>{CSS}</style></head><body><main>'
            f'<header><b>Rega Coco</b><h1>{esc(d["titulo_data"])}</h1></header>{big}{sec_wa}{tro}{sec_eq}{sec_ch}{sec_faz}</main></body></html>')

if __name__ == '__main__':
    d = json.load(open(sys.argv[1], encoding='utf-8'))
    open(sys.argv[2], 'w', encoding='utf-8').write(gerar(d))
    print('ok', sys.argv[2])
