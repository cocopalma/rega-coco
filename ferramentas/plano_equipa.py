#!/usr/bin/env python3
"""Plano da equipa para a ronda seguinte (Rega Coco; pedido do Valdo, 23/10/2026).

Aprende com a ronda que a equipa acabou de fazer (regas, horas, pessoas e percurso GPS) e propõe os dias da ronda
seguinte, partindo dos grupos de campos que o activista fez e da meta de 140 plantas por pessoa por dia.

Uso:  python3 plano_equipa.py dados.json > plano.json
dados.json vem da consulta em plano_dados.sql (uma equipa). Só biblioteca padrão.
"""
import json, math, sys
from datetime import datetime
from statistics import median

FOLGA_MAX = 1.15      # um dia pode passar a capacidade até 15 %
FOLGA_MIN = 0.75      # um dia com menos de 75 % da capacidade junta-se ao vizinho mais perto
FACTOR_CAMINHO = 1.3  # caminho / linha recta, quando o GPS não chega para o calcular
VEL_PE = 50.0         # m/min (3 km/h) quando não há deslocações medidas
MIN_PLANTA = 0.5      # min por planta quando não há regas medidas


def metros(a, b):
    r = 6371000.0
    la1, la2 = math.radians(a[0]), math.radians(b[0])
    dla, dlo = la2 - la1, math.radians(b[1] - a[1])
    h = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def t(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


def med(v, d=None):
    v = [x for x in v if x is not None]
    return median(v) if v else d


def aprender(dados):
    """O que a equipa fez na ronda: grupos por dia, pessoas, ritmo e deslocações."""
    ronda = dados['ronda']
    pos = {a['id']: (a['lat'], a['lon']) for a in dados['areas'] if a.get('lat') is not None}
    regas = sorted([r for r in dados['regas'] if (r.get('ronda') or 1) == ronda], key=lambda r: r['entrada_em'])
    por_dia = {}
    for r in regas:
        por_dia.setdefault(r['data'], []).append(r)
    grupos, min_planta, vel, fac, pessoas, ini, fim, janelas, plantas_dia = [], [], [], [], [], [], [], [], []
    jorn = {j['data']: j.get('pessoas') for j in dados.get('jornadas', [])}
    perc = {p['data']: p.get('pontos') or [] for p in dados.get('percursos', [])}
    for d in sorted(por_dia):
        rs = por_dia[d]
        grupos.append([r['area_id'] for r in rs])
        p = max([r.get('pessoas') or 0 for r in rs] + [jorn.get(d) or 0])
        if p: pessoas.append(p)
        plantas_dia.append(sum(r.get('plantas_regadas') or 0 for r in rs))
        e0, s1 = t(rs[0]['entrada_em']), t(rs[-1].get('saida_em') or rs[-1]['entrada_em'])
        mz = lambda x: (x.hour * 60 + x.minute + 120) % 1440   # hora de Maputo (UTC+2)
        ini.append(mz(e0)); fim.append(mz(s1)); janelas.append((s1 - e0).total_seconds() / 60)
        for r in rs:
            if r.get('saida_em') and (r.get('plantas_regadas') or 0) > 0:
                min_planta.append((t(r['saida_em']) - t(r['entrada_em'])).total_seconds() / 60 / r['plantas_regadas'])
        for a, b in zip(rs, rs[1:]):
            if not a.get('saida_em') or a['area_id'] not in pos or b['area_id'] not in pos: continue
            gap = (t(b['entrada_em']) - t(a['saida_em'])).total_seconds() / 60
            dist = metros(pos[a['area_id']], pos[b['area_id']])
            if 1 <= gap <= 120 and dist > 30:
                vel.append(dist / gap)
                pts = [q for q in perc.get(d, []) if t(a['saida_em']).timestamp() <= q[2] <= t(b['entrada_em']).timestamp()]
                if len(pts) >= 2:
                    cam = sum(metros((p1[1], p1[0]), (p2[1], p2[0])) for p1, p2 in zip(pts, pts[1:]))
                    if cam > dist * 0.8: fac.append(min(3.0, cam / dist))
    primeiro = [por_dia[d][0] for d in sorted(por_dia)]
    inicio_pt = None
    lats = [r['entrada_lat'] for r in primeiro if r.get('entrada_lat') is not None]
    if lats:
        inicio_pt = (med(lats), med([r['entrada_lon'] for r in primeiro if r.get('entrada_lon') is not None]))
    hm = lambda m: None if m is None else f"{int(m) // 60:02d}:{int(m) % 60:02d}"
    return {
        'ronda': ronda, 'dias_trabalhados': len(grupos), 'grupos': grupos,
        'pessoas': med(pessoas), 'plantas_por_dia': med(plantas_dia),
        'min_por_planta': med(min_planta), 'vel_m_min': med(vel), 'factor_caminho': med(fac),
        'hora_inicio': hm(med(ini)), 'hora_fim': hm(med(fim)), 'minutos_dia': med(janelas),
        'n_deslocacoes': len(vel), 'n_caminhos_gps': len(fac), 'inicio': inicio_pt,
    }


def comprimento(rota, pos, de=None):
    d = sum(metros(pos[a], pos[b]) for a, b in zip(rota, rota[1:]))
    return d + (metros(de, pos[rota[0]]) if de and rota else 0)


def ordenar(ids, pos, de):
    """Percurso aberto mais curto (vizinho mais perto + 2-opt). Sem ponto de partida, experimenta começar em cada campo."""
    com = [i for i in ids if i in pos]
    sem = [i for i in ids if i not in pos]
    if not com: return sem
    if not de and len(com) > 2:
        rotas = [ordenar_de(com, pos, pos[c]) for c in com]
        return min(rotas, key=lambda r: comprimento(r, pos)) + sem
    return ordenar_de(com, pos, de) + sem


def ordenar_de(com, pos, de):
    cur = de or pos[com[0]]
    rota, resto = [], set(com)
    while resto:
        n = min(resto, key=lambda i: metros(cur, pos[i])); rota.append(n); resto.remove(n); cur = pos[n]
    melhorou = True
    while melhorou and len(rota) > 3:
        melhorou = False
        for i in range(len(rota) - 2):
            for j in range(i + 2, len(rota)):
                a, b = pos[rota[i]], pos[rota[i + 1]]
                c = pos[rota[j]]; dd = pos[rota[j + 1]] if j + 1 < len(rota) else None
                antes = metros(a, b) + (metros(c, dd) if dd else 0)
                depois = metros(a, c) + (metros(b, dd) if dd else 0)
                if depois + 0.5 < antes:
                    rota[i + 1:j + 1] = reversed(rota[i + 1:j + 1]); melhorou = True
    return rota


def centro(ids, pos):
    p = [pos[i] for i in ids if i in pos]
    return (sum(x[0] for x in p) / len(p), sum(x[1] for x in p) / len(p)) if p else None


AFINIDADE = 0.7       # campos que a equipa regou no mesmo dia "ficam mais perto" (a distância conta 70 %)


def planear(dados):
    """Dias da ronda seguinte: começa onde a equipa costuma começar e enche cada dia com os campos mais perto até à
    capacidade (140 × pessoas) e ao tempo de trabalho que a equipa costuma fazer. Os campos que a equipa juntou no mesmo
    dia contam como mais perto, para o plano seguir a forma de trabalhar dela."""
    meta = dados.get('meta', 140)
    ap = aprender(dados)
    areas = {a['id']: a for a in dados['areas']}
    pos = {a['id']: (a['lat'], a['lon']) for a in dados['areas'] if a.get('lat') is not None}
    pl = lambda i: areas[i].get('plantas') or 0
    pessoas = ap['pessoas'] or dados.get('equipa_tamanho') or 1
    cap = int(round(meta * pessoas))
    fac = ap['factor_caminho'] or FACTOR_CAMINHO
    vel = ap['vel_m_min'] or VEL_PE
    mpp = ap['min_por_planta'] or MIN_PLANTA
    janela = ap['minutos_dia']
    notas = []
    juntos, dia_de = set(), {}
    for k, g in enumerate(ap['grupos']):
        for a in g:
            dia_de.setdefault(a, k)
            for b in g:
                if a != b: juntos.add((a, b))
    ef = lambda a, b: metros(pos[a], pos[b]) * (AFINIDADE if (a, b) in juntos else 1)
    # 1. dias com os campos com coordenada
    resto, dias, de = set(pos), [], ap['inicio']
    while resto:
        primeiro = min(resto, key=lambda i: metros(de, pos[i])) if de else min(resto, key=lambda i: dia_de.get(i, 99))
        dia, soma, mins = [primeiro], pl(primeiro), pl(primeiro) * mpp
        resto.remove(primeiro)
        while resto:
            n = min(resto, key=lambda i: ef(dia[-1], i))
            d = metros(pos[dia[-1]], pos[n]) * fac
            m2 = mins + d / vel + pl(n) * mpp
            cabe = soma + pl(n) <= cap * FOLGA_MAX and (not janela or m2 <= janela * 1.1)
            if not cabe and soma >= cap * FOLGA_MIN: break
            if not cabe and soma + pl(n) > cap * 1.5: break
            dia.append(n); soma += pl(n); mins = m2; resto.remove(n)
        dia = ordenar(dia, pos, de)
        dias.append(dia); de = pos[dia[-1]]
    # 2. dias pequenos (menos de 75 %): os campos passam para o dia onde acrescentam menos caminho, se couberem
    carga = lambda d: sum(map(pl, d))
    def custo_inserir(d, i):
        if not d: return 0
        melhor = min(metros(pos[d[0]], pos[i]), metros(pos[d[-1]], pos[i]))
        for a2, b2 in zip(d, d[1:]):
            melhor = min(melhor, metros(pos[a2], pos[i]) + metros(pos[i], pos[b2]) - metros(pos[a2], pos[b2]))
        return melhor
    for d in sorted([d for d in dias if carga(d) < cap * FOLGA_MIN and len(d) > 0], key=carga):
        if d not in dias: continue
        outros = [o for o in dias if o is not d]
        plano_mov = []
        for i in sorted(d, key=lambda i: -pl(i)):
            cands = [o for o in outros if carga(o) + pl(i) + sum(pl(x) for x, oo in plano_mov if oo is o) <= cap * FOLGA_MAX]
            if not cands: plano_mov = None; break
            plano_mov.append((i, min(cands, key=lambda o: custo_inserir(o, i))))
        if plano_mov:
            for i, o in plano_mov: o.append(i)
            dias.remove(d)
    dias = [ordenar(d, pos, None) for d in dias]
    # 3. campos sem coordenada: no dia que tem mais campos do dia em que a equipa os regou e onde ainda cabem; senão no dia com menos plantas
    sem = [i for i in areas if i not in pos]
    for i in sorted(sem, key=lambda i: -pl(i)):
        k = dia_de.get(i)
        irmaos = set(ap['grupos'][k]) - {i} if k is not None else set()
        cabem = [d for d in dias if carga(d) + pl(i) <= cap * 1.25]   # sem coordenada: até 25 % acima, para não fazer um dia só com eles
        cands = [d for d in cabem if irmaos & set(d)]
        if cands: alvo = max(cands, key=lambda d: len(irmaos & set(d)))
        elif cabem: alvo = min(cabem, key=carga)
        else: dias.append([]); alvo = dias[-1]
        alvo.append(i)
    if sem: notas.append(f"{len(sem)} campos sem coordenada: ficam no fim do dia em que a equipa os regou, se couberem, ou no dia com menos plantas.")
    falta = [i for i in areas if i not in dia_de]
    if falta: notas.append(f"{len(falta)} campos da lista não foram regados na ronda {ap['ronda']}; entram no plano.")
    out = []
    for n, r in enumerate(dias, 1):
        com = [i for i in r if i in pos]
        dist = sum(metros(pos[a], pos[b]) for a, b in zip(com, com[1:])) * fac
        pl_d = sum(map(pl, r))
        out.append({'n': n, 'campos': [{'area_id': i, 'plantas': pl(i), 'sem_coordenada': i not in pos} for i in r],
                    'plantas': pl_d, 'dist_m': round(dist), 'minutos': round(pl_d * mpp + dist / vel)})
    if any(d['plantas'] > cap * FOLGA_MAX for d in out):
        notas.append('Há campos com mais plantas do que a capacidade de um dia: ficam sozinhos nesse dia.')
    if janela and any(d['minutos'] > janela * 1.2 for d in out):
        notas.append('Há dias com mais tempo estimado do que a equipa costuma trabalhar.')
    ap.pop('grupos'); ap['inicio'] = list(ap['inicio']) if ap['inicio'] else None
    # comparação com a ronda feita
    ap['dias_plano'] = len(out)
    return {'activista_id': dados['activista_id'], 'ronda': ap['ronda'] + 1, 'capacidade': cap, 'pessoas': pessoas,
            'dias': out, 'aprendizagem': ap, 'notas': ' '.join(notas) or None}


if __name__ == '__main__':
    print(json.dumps(planear(json.load(open(sys.argv[1]))), ensure_ascii=False))
