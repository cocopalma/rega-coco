#!/usr/bin/env python3
"""Teste de coerência do relatório do dia (Valdo, 08/11/2026: "Sempre que fizeres o relatório, corre depois
um teste de coerência de dados e de coerência de informação dentro do próprio relatório").

Uso: python3 ferramentas/verificar_relatorio.py dados.json Rega_Coco_relatorio_AAAAMMDD
     (lê dados.json, Rega_Coco_relatorio_AAAAMMDD.html/.pdf e Rega_Coco_dados.json da mesma pasta)
Sai com código 1 se alguma verificação falhar; escreve a lista das verificações.

1. Dados: os totais do JSON batem uns com os outros (equipas, regas, campos, plantas, pessoas, comunidades,
   ronda, manutenção, cumprimento) e os valores fazem sentido (horas, datas, limites).
2. Informação: o que o HTML e o PDF mostram é o que está no JSON (cartões, títulos, frases, gráficos,
   tabela, datas) e o JSON de nome fixo é igual ao que vai dentro do HTML.
3. Segurança: sem números de telefone.
"""
import html as H
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date

RES = []


def ver(ok, txt):
    RES.append((bool(ok), txt))


def n(x):
    return f'{int(x or 0):,}'.replace(',', ' ')


def pct(a, b):
    return round(100 * a / b) if b else 0


def texto(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S)
    return ' '.join(H.unescape(re.sub(r'<[^>]+>', ' ', h)).split())


def main(dados, base):
    d = json.load(open(dados, encoding='utf-8'))
    if 'dados' in d and 'rega' not in d:
        d = d['dados']
    r, m, c = d['rega'], d['manutencao'], d.get('cumprimento') or {}
    eq = r['por_equipa']
    dia = date.fromisoformat(d['data'])
    hc = r.get('hora_combinada_chegada') or '06:00'
    com = [x for x in eq if x['regas'] > 0]
    sem = [x for x in eq if x['regas'] == 0]

    # ---------- 1. Coerência dos dados ----------
    ver(len(eq) == r['equipas_total'], f'equipas: {len(eq)} na lista = {r["equipas_total"]} no total')
    ver(len(com) == r['equipas_com_rega'], f'equipas que regaram: {len(com)} = {r["equipas_com_rega"]}')
    ver(sum(x['regas'] for x in eq) == r['regas'], f'regas: soma das equipas = {r["regas"]}')
    ver(sum(x['campos'] for x in eq) == r['campos_regados'], f'campos regados: soma das equipas = {r["campos_regados"]}')
    ver(sum(x['plantas'] for x in eq) == r['plantas_regadas'], f'plantas regadas: soma das equipas = {r["plantas_regadas"]}')
    ver(sum(x['pessoas'] or 0 for x in com) == r['pessoas'], f'pessoas: soma das equipas que regaram = {r["pessoas"]}')
    pc = r['por_comunidade']
    ver(sum(x['plantas'] for x in pc) == r['plantas_regadas'], 'plantas por comunidade = plantas regadas')
    ver(sum(x['campos'] for x in pc) == r['campos_regados'], 'campos por comunidade = campos regados')
    ver(sum(x['regados_na_ronda'] or 0 for x in eq) == r['campos_ronda_regados'], 'ronda: campos regados = soma das equipas')
    ver(sum(x['campos_na_lista'] or 0 for x in eq) == r['campos_ronda_lista'], 'ronda: campos na lista = soma das equipas')
    ver(r['campos_ronda_lista'] + (r.get('campos_sem_equipa') or 0) == r['campos_na_rega'],
        f'campos na rega {r["campos_na_rega"]} = campos com equipa {r["campos_ronda_lista"]} + sem equipa {r.get("campos_sem_equipa") or 0}')
    ver(sum(x['nunca_receberam_agua'] or 0 for x in eq) <= r['campos_nunca_receberam_agua'], 'nunca receberam água: soma das equipas ≤ total')
    ver(r['plantas_acumuladas_app'] >= r['plantas_regadas'], 'plantas desde o início ≥ plantas do dia')
    for x in eq:
        a = x['activista']
        ver((x['regados_na_ronda'] or 0) <= (x['campos_na_lista'] or 0), f'{a}: regados na ronda ≤ campos na lista')
        if x['regas']:
            ver(x['campos'] >= 1 and x['campos'] <= x['regas'], f'{a}: 1 ≤ campos ≤ regas')
            ver(bool(re.fullmatch(r'[0-2]\d:[0-5]\d', x['chegada_1o_campo'] or '')), f'{a}: hora do 1.º campo válida ({x["chegada_1o_campo"]})')
            ver(not x['motivos_sem_rega'], f'{a}: regou e não tem motivo de dia sem rega')
        else:
            ver(x['plantas'] == 0 and x['campos'] == 0 and not x['chegada_1o_campo'], f'{a}: sem rega, sem plantas nem campos')
            ver(not x['constrangimentos'], f'{a}: sem rega, sem constrangimentos da saída')
    for x in m.get('por_comunidade') or []:
        k = x['comunidade']
        ver(0 <= x['cavaroda'] <= x['plantas'] and 0 <= x['mulching'] <= x['plantas'], f'manutenção {k}: cava-roda e mulching ≤ plantas')
        ver(x['feitos'] + x['completos'] + x['em_curso'] + x['por_fazer'] + x['sem_plantas'] == x['campos'],
            f'manutenção {k}: situações somam {x["campos"]} campos')
    if c.get('pessoas'):
        nomes_sem = {x['activista'] for x in sem if not x['motivos_sem_rega']}
        sem_inicio = {x['activista']: x for x in sem if not x['motivos_sem_rega'] and not x['inicio_dia']}
        tarde = {x['activista'] for x in com if (x['chegada_1o_campo'] or '') > hc}
        r1, r5 = set(), set()
        for p in c['pessoas']:
            ds = [x['data'] for x in p['dias']]
            ver(ds == sorted(ds) and all(date.fromisoformat(z).weekday() < 6 for z in ds), f'cumprimento {p["nome"]}: dias por ordem, sem domingos')
            if dia.weekday() < 6:
                ver(ds and ds[-1] == d['data'], f'cumprimento {p["nome"]}: último dia = {d["data"]}')
            hoje = p['dias'][-1] if ds and ds[-1] == d['data'] else None
            if hoje:
                r1 |= set(hoje['r1'])
                r5 |= {z['nome'] for z in hoje['r5']}
                ver(all(z['hora'] > (c.get('hora_chegada') or hc) for z in hoje['r5']), f'cumprimento {p["nome"]}: chegadas tardias depois de {hc}')
                ver(not hoje['fecho'] or re.fullmatch(r'[0-2]\d:[0-5]\d', hoje['fecho']), f'cumprimento {p["nome"]}: hora do fecho válida')
        if dia.weekday() < 6:
            ver(r1 <= nomes_sem, 'cumprimento: equipas sem rega nem motivo estão no grupo «Sem motivo registado»')
            monit = {p['nome'] for p in c['pessoas']}
            falta = [a for a, x in sem_inicio.items() if (x['tecnico'] in monit or x['supervisor'] in monit) and a not in r1]
            ver(not falta, 'cumprimento: todas as equipas sem rega, sem início e sem motivo contam como falha' + (f' (faltam: {", ".join(falta)})' if falta else ''))
            ver(r5 <= tarde, 'cumprimento: chegadas tardias são equipas que regaram depois da hora')
            falta5 = [a for a in tarde if a not in r5 and any(x['activista'] == a and (x['tecnico'] in monit or x['supervisor'] in monit) for x in com)]
            ver(not falta5, 'cumprimento: todas as equipas que chegaram tarde contam' + (f' (faltam: {", ".join(falta5)})' if falta5 else ''))
    ver(d['gerado_em'][:10] >= d['data'], f'dados lidos ({d["gerado_em"]}) no dia do relatório ou depois')

    # ---------- 2. Coerência da informação no relatório ----------
    hpath, ppath = base + '.html', base + '.pdf'
    h = open(hpath, encoding='utf-8').read()
    t = texto(h)
    emb = json.loads(re.search(r'id="rega-coco-dados">(.*?)</script>', h, re.S).group(1).replace('<\\/', '</'))
    ver(emb == d, 'JSON dentro do HTML = dados')
    fx = os.path.join(os.path.dirname(os.path.abspath(base)), 'Rega_Coco_dados.json')
    if os.path.exists(fx):
        ver(json.load(open(fx, encoding='utf-8')) == d, 'Rega_Coco_dados.json = dados')
    else:
        ver(False, 'Rega_Coco_dados.json existe')
    ver(f'{dia:%d/%m/%Y}' in t.split('·')[0], f'cabeçalho com o dia {dia:%d/%m/%Y}')
    lido = f'{d["gerado_em"][8:10]}/{d["gerado_em"][5:7]}/{d["gerado_em"][:4]} às {d["gerado_em"][11:16]}'
    ver(t.count(f'dados lidos da app a {lido}') == 1 and f'quando os dados foram lidos ({lido})' in t, f'cabeçalho e rodapé com a leitura {lido}')
    ver(f'{r["equipas_com_rega"]} /{r["equipas_total"]} equipas regaram' in t, 'cartão: equipas que regaram')
    ver(f'{n(r["campos_regados"])} campos regados {n(r["regas"])} regas' in t, 'cartão: campos regados e regas')
    ver(f'{n(r["plantas_regadas"])} plantas regadas {n(r["pessoas"])} pessoas' in t, 'cartão: plantas e pessoas')
    ver(f'{n(r["plantas_acumuladas_app"])} plantas regadas na app' in t, 'cartão: plantas desde o início')
    ver(f'{pct(r["campos_ronda_regados"], r["campos_ronda_lista"])}% progresso da ronda {n(r["campos_ronda_regados"])} de {n(r["campos_ronda_lista"])}' in t, 'cartão: progresso da ronda')
    ver(f'{n(r["campos_nunca_receberam_agua"])} campos nunca receberam água' in t, 'cartão: nunca receberam água')
    ver(f'Equipas que regaram ({len(com)})' in t and f'Equipas sem rega na app ({len(sem)})' in t, 'títulos: equipas com e sem rega')
    for x in com:
        ver(f'{n(x["plantas"])} pl. · {x["campos"]} campos' in t, f'gráfico das equipas: {x["activista"]}')
    ver(len(re.findall(r'<tr><td><b>', h)) == len(eq), f'tabela: {len(eq)} linhas')
    tot_ok = sum(1 for x in com)
    ver(f'{tot_ok} de {len(eq)} equipas regaram' in t, 'resumo da tabela: frase = equipas que regaram')
    ver(f'{len([x for x in sem if x["motivos_sem_rega"]])} sem rega com motivo; {len([x for x in sem if not x["motivos_sem_rega"]])} sem rega e sem motivo' in t,
        'resumo da tabela: frase = equipas sem rega')
    rs = re.search(r'class="resumo">(.*)', h.split('<footer')[0], re.S)
    if rs:
        barras = re.findall(r'<div class="b-val">(\d+) equipas</div>', rs.group(1))
        ver(barras and int(barras[0]) == len(eq) and sum(map(int, barras[1:])) == len(eq), 'resumo da tabela: barras por técnico somam as equipas')
    else:
        ver(False, 'resumo da tabela existe')
    for x in m.get('por_comunidade') or []:
        ver(f'{x["comunidade"]} · {x["campos"]} campos · {n(x["plantas"])} plantas' in t, f'manutenção: {x["comunidade"]}')
    if ppath and os.path.exists(ppath) and shutil.which('pdftotext'):
        pt = ' '.join(subprocess.run(['pdftotext', ppath, '-'], capture_output=True, text=True).stdout.split())
        for k in (f'{dia:%d/%m/%Y}', n(r['plantas_regadas']), f'{tot_ok} de {len(eq)} equipas regaram', 'Todas as equipas', 'Fonte: app Rega Coco'):
            ver(k in pt, f'PDF contém «{k}»')
    else:
        ver(os.path.exists(ppath), 'PDF existe')

    # ---------- 3. Segurança ----------
    ver(not re.search(r'(?<!\d)8[2-7] ?\d{3} ?\d{4}(?!\d)', t), 'sem números de telefone no HTML')

    falhas = [x for x in RES if not x[0]]
    for ok, txt in RES:
        if not ok:
            print('FALHA:', txt)
    print(f'{len(RES) - len(falhas)} de {len(RES)} verificações certas.' + (' Relatório coerente.' if not falhas else ' NÃO ENVIAR.'))
    return 1 if falhas else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], os.path.abspath(sys.argv[2])))
