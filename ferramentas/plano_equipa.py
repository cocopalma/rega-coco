#!/usr/bin/env python3
"""Planos da equipa (Rega Coco). v3: 22/11/2026, decisões do Valdo de 21–22/11.

Regras:
- Cada campo conta com as plantas que a equipa regou nele na última ronda (sem passar a base); campo nunca regado: a base.
  (Valdo: "isto é que mostra o que está realmente em campo"; os campos que regam menos de metade da base têm recontagem pedida.)
- O dia de trabalho vai das 06:30 às 14:00 (450 min) para todas as equipas. O tempo de cada dia conta, com o que a equipa fez nos
  últimos 30 dias: a espera pela água (1.º campo e campos seguintes), a rega (min por planta, entre a chegada da água e a saída),
  a deslocação entre campos (velocidade dos percursos curtos e dos longos, acima de 800 m) e as outras esperas (o tempo dos dias
  reais que estas partes não explicam).
- Experimenta vários caminhos pelos campos e, em cada um, os cortes que deixam os dias o mais cheios possível sem passar das 14:00;
  fica com o melhor. O último dia da ronda fica com o resto e continua com o 1.º dia da ronda seguinte (os campos regados há mais
  tempo, a partir de onde a equipa acaba), para não haver dias com um campo pequeno nem horas paradas.
- Cada dia é um grupo de campos vizinhos (23/11/2026, Valdo): conta como custo cada campo a mais de 300 m do centro do seu dia, para
  não haver dias que atravessam os grupos dos outros dias, e cada campo que fica mais perto do centro de outro dia do que do seu;
  os dias seguem-se no terreno de grupo em grupo vizinho. Um campo isolado (nenhum outro a menos de 1,5 km) não faz um dia sozinho:
  entra no início ou no fim do dia com o campo mais perto.
- Gera dois planos: o resto da ronda actual (só os campos que faltam) e a ronda seguinte. Se o da ronda actual já existe, só a seguinte.

Uso:  python3 plano_equipa.py dados.json > planos.json   (dados.json = consulta 2 de plano_dados.sql, uma equipa). Só biblioteca padrão.
"""
import itertools, json, math, sys
from statistics import median

W = 450               # minutos de trabalho por dia (06:30 -> 14:00)
INICIO = 390          # 06:30 em minutos
CUSTO_DIA = 20000     # cada dia a mais pesa como um dia com 2 h 20 paradas
SALTO = 1500          # um salto de mais de 1,5 km entre dois campos seguidos do mesmo dia…
CUSTO_SALTO = 20000   # …pesa como 2 h 20 paradas: só se junta campos longe quando não há outra forma (Valdo, 22/11/2026)
RAIO = 300            # cada campo a mais de 300 m do centro do seu dia…
CUSTO_METRO = 80      # …pesa 80 por metro a mais: os dias ficam em grupos de campos vizinhos, sem misturar grupos (Valdo, 23/11/2026:
                      # no plano do Majula o dia 4 ia de uma ponta à outra da zona, por cima dos grupos dos outros dias)
CUSTO_MISTURA = 40    # cada metro que um campo está mais perto do centro de outro dia do que do seu pesa 40: dias que não se
                      # cruzam (Valdo, 23/11/2026: "o dia 1 e o dia 2 podiam estar melhor organizados")


def metros(a, b):
    r = 6371000.0
    la1, la2 = math.radians(a[0]), math.radians(b[0])
    dla, dlo = la2 - la1, math.radians(b[1] - a[1])
    h = math.sin(dla / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


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


class Equipa:
    def __init__(self, dados):
        self.d = dados
        self.pos = {k: tuple(v) for k, v in (dados.get('pos') or {}).items()}
        for a in dados['areas']:
            if a.get('lat') is not None: self.pos[a['id']] = (a['lat'], a['lon'])
        self.areas = {a['id']: a for a in dados['areas']}
        self.isol = set()
        self.P = self.aprender(dados['regas'])

    def pl(self, i, seguinte=False):
        """plantas a regar: na ronda seguinte, um campo já feito nesta ronda conta com o que regaram nesta ronda"""
        a = self.areas[i]; base = a['plantas'] or 0
        v = a.get('pl_actual') if (seguinte and a.get('feito_ronda') and a.get('pl_actual')) else (a.get('pl_anterior') or base)
        return min(v, base) if base else v

    def desl(self, m):
        P = self.P
        return m / P['vel'] if m <= 800 else 800 / P['vel'] + (m - 800) / max(P['vlon'], P['vel'])

    def partes(self, seq):
        """seq = [(area_id, plantas)] -> minutos por parte"""
        P = self.P
        com = [i for i, _ in seq if i in self.pos]
        return {'espera': P['e1'] + P['en'] * (len(seq) - 1), 'rega': sum(p for _, p in seq) * P['mr'],
                'desloc': sum(self.desl(metros(self.pos[a], self.pos[b])) for a, b in zip(com, com[1:])), 'outras': P.get('bias', 0)}

    def tempo(self, seq):
        return sum(self.partes(seq).values()) if seq else 0

    def aprender(self, regs):
        pos = self.pos
        dias = {}
        for r in regs: dias.setdefault(r['d'], []).append(r)
        e1, en, mr, vel, vlon, pes = [], [], [], [], [], []
        for d, rs in dias.items():
            rs.sort(key=lambda r: r['e'])
            pes.append(max([r.get('n') or 0 for r in rs]))
            for k, r in enumerate(rs):
                if r.get('w'):
                    (e1 if k == 0 else en).append(min(240, (r['w'] - r['e']) / 60))
                    if r.get('p'): mr.append((r['s'] - r['w']) / 60 / r['p'])
            for a, b in zip(rs, rs[1:]):
                if a['a'] in pos and b['a'] in pos:
                    gap = (b['e'] - a['s']) / 60; dist = metros(pos[a['a']], pos[b['a']])
                    if 1 <= gap <= 120 and 30 < dist <= 800: vel.append(dist / gap)
                    if 1 <= gap <= 180 and dist > 800: vlon.append(dist / gap)
        if len(mr) >= 3:
            m = median(mr); mr = [x for x in mr if m / 3 <= x <= 3 * m]
        P = {'e1': median(e1) if e1 else 30, 'en': median(en) if en else 15, 'mr': median(mr) if mr else 0.5,
             'vel': median(vel) if len(vel) >= 5 else 28, 'vlon': median(vlon) if len(vlon) >= 5 else 40,
             'pessoas': median([p for p in pes if p]) if any(pes) else None,
             'n_dias': len(dias), 'n_regas_agua': len(e1) + len(en), 'n_regas_ritmo': len(mr), 'n_deslocacoes': len(vel) + len(vlon)}
        self.P = P
        val = [(self.tempo([(r['a'], r.get('p') or 0) for r in rs]), (rs[-1]['s'] - rs[0]['e']) / 60) for rs in dias.values() if len(rs) >= 2]
        P['bias'] = max(0, median(r - p for p, r in val)) if val else 0
        P['erro'] = median(abs(p + P['bias'] - r) for p, r in val) if val else None
        P['n_dias_validacao'] = len(val)
        return P

    def espalho(self, d):
        """metros dos campos do dia além de RAIO do centro do dia (os campos isolados não contam)"""
        com = [x for x in d if x in self.pos and x not in self.isol]
        if len(com) < 2: return 0
        c = (sum(self.pos[x][0] for x in com) / len(com), sum(self.pos[x][1] for x in com) / len(com))
        return sum(max(0, metros(self.pos[x], c) - RAIO) for x in com)

    def saltos(self, d):
        """saltos longos entre campos seguidos (fora os campos isolados), mais o espalho do dia ao mesmo preço"""
        com = [x for x in d if x in self.pos and x not in self.isol]
        n = sum(1 for a, b in zip(com, com[1:]) if metros(self.pos[a], self.pos[b]) > SALTO)
        return n + self.espalho(d) * CUSTO_METRO / CUSTO_SALTO

    def dp(self, rota, pl, orc1):
        n = len(rota)
        best = [float('inf')] * (n + 1); cut = [0] * (n + 1); best[0] = 0
        for j in range(1, n + 1):
            for i in range(j - 1, -1, -1):
                t = self.tempo([(x, pl(x)) for x in rota[i:j]])
                orc = orc1 if i == 0 else W
                if t > orc and j - i > 1: break
                c = (0 if j == n else ((orc - t) ** 2 if t <= orc else 1e7)) + CUSTO_DIA + CUSTO_SALTO * self.saltos(rota[i:j])
                if best[i] + c < best[j]: best[j] = best[i] + c; cut[j] = i
        dias, j = [], n
        while j > 0: dias.append(rota[cut[j]:j]); j = cut[j]
        return best[n], dias[::-1]

    def cortar(self, ids, pl, de, orc1=W):
        # campo isolado (nenhum outro a menos de SALTO): não faz um dia sozinho; entra no início ou no fim do dia com o campo mais perto
        com0 = [i for i in ids if i in self.pos]
        isol = [i for i in com0 if len(com0) > 1 and min(metros(self.pos[i], self.pos[j]) for j in com0 if j != i) > SALTO]
        self.isol |= set(isol)
        dias = self.cortar_grupo([i for i in ids if i not in isol], pl, de, orc1)
        T = lambda d: self.tempo([(x, pl(x)) for x in d])
        for i in isol:
            perto = sorted([d for d in dias if any(x in self.pos for x in d)],
                           key=lambda d: min(metros(self.pos[i], self.pos[x]) for x in d if x in self.pos))
            alvo = next((d for d in perto if T(d + [i]) <= (orc1 if d is (dias[0] if dias else None) else W)), None)
            if alvo is None: dias.append([i]); continue
            ca = [x for x in alvo if x in self.pos]
            if metros(self.pos[i], self.pos[ca[0]]) < metros(self.pos[i], self.pos[ca[-1]]): alvo.insert(0, i)
            else: alvo.append(i)
        return dias

    def cortar_grupo(self, ids, pl, de, orc1=W):
        com = [i for i in ids if i in self.pos]
        if not com: return []
        # continuação do último dia: o caminho começa onde a equipa está; senão experimenta começar em cada campo
        rotas = [ordenar_de(com, self.pos, de)] + ([ordenar_de(com, self.pos, self.pos[c]) for c in com] if len(com) <= 80 and orc1 == W else [])
        dias = min((self.dp(r, pl, orc1) for r in rotas), key=lambda x: x[0])[1]
        return self.melhorar(dias, pl, de) if orc1 == W else dias

    def centro(self, d):
        com = [x for x in d if x in self.pos and x not in self.isol]
        return (sum(self.pos[x][0] for x in com) / len(com), sum(self.pos[x][1] for x in com) / len(com)) if com else None

    def mistura(self, dias):
        """metros que cada campo está mais perto do centro de outro dia do que do centro do seu (dias que se cruzam)"""
        cs = [self.centro(d) for d in dias]; s = 0
        for k, d in enumerate(dias):
            if cs[k] is None: continue
            for i in d:
                if i not in self.pos or i in self.isol: continue
                outro = min([metros(self.pos[i], c) for j, c in enumerate(cs) if j != k and c] or [1e9])
                s += max(0, metros(self.pos[i], cs[k]) - outro)
        return s

    def melhorar(self, dias, pl, de):
        """passa campos de um dia para outro, ou troca dois campos entre dias, enquanto isso deixar os dias mais cheios e mais
        arrumados (sem se cruzarem); o dia mais curto fica para o fim: é o que continua com a ronda seguinte; nenhum dia passa
        das 14:00"""
        T = lambda d: self.tempo([(x, pl(x)) for x in d])
        def custo(ds):
            ts = sorted(T(d) for d in ds)
            return (CUSTO_DIA * len(ds) + sum((W - t) ** 2 for t in ts[1:]) + CUSTO_SALTO * sum(self.saltos(d) for d in ds)
                    + CUSTO_MISTURA * self.mistura(ds))
        orden = lambda d: ordenar_de(d, self.pos, None) if len(d) > 2 else d
        dias = [orden(d) for d in dias]
        atual = custo(dias)
        for _ in range(300):
            melhor = None
            for a in range(len(dias)):
                for i in dias[a]:
                    for b in range(len(dias)):
                        if a == b: continue
                        nb = ordenar_de(dias[b] + [i], self.pos, None)
                        if T(nb) > W: continue
                        na = orden([x for x in dias[a] if x != i])
                        novo = [d for d in [na if k == a else nb if k == b else d for k, d in enumerate(dias)] if d]
                        c = custo(novo)
                        if c < atual - 1 and (melhor is None or c < melhor[0]): melhor = (c, novo)
            if not melhor:
                for a in range(len(dias)):
                    for b in range(a + 1, len(dias)):
                        for i in dias[a]:
                            for j in dias[b]:
                                na = orden([x for x in dias[a] if x != i] + [j]); nb = orden([x for x in dias[b] if x != j] + [i])
                                if T(na) > W or T(nb) > W: continue
                                novo = [na if k == a else nb if k == b else d for k, d in enumerate(dias)]
                                c = custo(novo)
                                if c < atual - 1 and (melhor is None or c < melhor[0]): melhor = (c, novo)
            if not melhor: break
            atual, dias = melhor
        # ordem dos dias: seguida no terreno (de grupo em grupo vizinho), o mais curto no fim
        curto = min(dias, key=T)
        resto = [d for d in dias if d is not curto]
        cs = {id(d): self.centro(d) or self.pos.get(d[0]) for d in dias}
        def caminho(o):
            seq = list(o) + [curto]
            return sum(metros(cs[id(a)], cs[id(b)]) for a, b in zip(seq, seq[1:]) if cs[id(a)] and cs[id(b)])
        if len(resto) <= 7:
            ordem = list(min(itertools.permutations(resto), key=caminho))
        else:
            ordem, cur = [], de
            while resto:
                n = min(resto, key=lambda d: metros(cur, self.pos[d[0]]) if cur else 0); ordem.append(n); resto.remove(n); cur = self.pos[n[-1]]
        # ordem dos campos em cada dia: o caminho mais curto, a começar perto de onde acabou o dia anterior
        out, cur = [], None
        for d in ordem + [curto]:
            com = [x for x in d if x in self.pos]; sem = [x for x in d if x not in self.pos]
            if len(com) > 1:
                L = lambda r: sum(metros(self.pos[a], self.pos[b]) for a, b in zip(r, r[1:])) + (metros(cur, self.pos[r[0]]) if cur else 0)
                com = min((ordenar_de(com, self.pos, self.pos[c]) for c in com), key=L)
            out.append(com + sem); cur = self.pos[com[-1]] if com else cur
        return out

    def sem_coord(self, dias, ids, pl, fora=None):
        for i in [x for x in ids if x not in self.pos]:
            cabem = [d for d in dias if d is not fora and self.tempo([(x, pl(x)) for x in d + [i]]) <= W]
            outros = [d for d in dias if d is not fora]
            alvo = min(cabem or outros, key=lambda d: self.tempo([(x, pl(x)) for x in d])) if (cabem or outros) else None
            if alvo is None: dias.append([i])
            else: alvo.append(i)
        return dias

    def inicio(self):
        regs = sorted(self.d['regas'], key=lambda r: r['e']); vistos, firsts = set(), []
        for r in regs:
            if r['d'] not in vistos and r['a'] in self.pos: vistos.add(r['d']); firsts.append(self.pos[r['a']])
        return (median(p[0] for p in firsts), median(p[1] for p in firsts)) if firsts else None

    def saida(self, dias, plf, extra=None):
        hm = lambda m: f"{int(INICIO + m) // 60:02d}:{int(INICIO + m) % 60:02d}"
        out = []
        for n, d in enumerate(dias, 1):
            seq = [(x, plf(x)) for x in d]; pa = self.partes(seq) if d else {'espera': 0, 'rega': 0, 'desloc': 0, 'outras': 0}
            com = [x for x in d if x in self.pos]
            dist = sum(metros(self.pos[a], self.pos[b]) for a, b in zip(com, com[1:]))
            t = sum(pa.values())
            dia = {'n': n, 'campos': [{'area_id': x, 'produtor': self.areas[x].get('produtor'), 'plantas': plf(x), 'base': self.areas[x]['plantas'],
                                       'sem_coordenada': x not in self.pos} for x in d],
                   'plantas': sum(p for _, p in seq), 'dist_m': round(dist), 'minutos': round(t),
                   'espera_min': round(pa['espera']), 'rega_min': round(pa['rega']), 'desloc_min': round(pa['desloc']), 'outras_min': round(pa['outras']),
                   'inicio': hm(0), 'fim': hm(t)}
            if extra: dia.update(extra(n, len(dias), t) or {})
            out.append(dia)
        return out

    def planos(self):
        d, P = self.d, self.P
        ronda = d['ronda']
        pessoas = P['pessoas'] or d.get('equipa_tamanho') or 1
        meta = d.get('meta', 140)
        apr = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in P.items()}
        apr.update({'versao': 3, 'agrupamento': '23/11/2026', 'janela': '06:30–14:00', 'ronda': ronda - 1})
        falta = [a['id'] for a in d['areas'] if not a.get('feito_ronda')]
        feitos = sorted([a['id'] for a in d['areas'] if a.get('feito_ronda')], key=lambda i: self.areas[i].get('feito_em') or '')
        res = []
        orc1 = W
        fim = self.inicio()
        if not d.get('tem_plano_actual') and falta:
            pl = lambda i: self.pl(i)
            dias = self.sem_coord(self.cortar(falta, pl, self.inicio()), falta, pl)
            t_ult = self.tempo([(x, pl(x)) for x in dias[-1]])
            orc1 = W - t_ult + P['e1'] + P['bias'] - P['en'] if t_ult < W - 60 else W
            ult = [x for x in dias[-1] if x in self.pos]
            fim = self.pos[ult[-1]] if ult else fim
            seguinte = orc1 < W
            ext = lambda n, tot, t: {'continua': seguinte} if n == tot else None
            notas = [f"Resto da ronda {ronda}: {len(falta)} campos."]
            if seguinte: notas.append(f"No dia {len(dias)} a ronda {ronda} fica feita e a equipa continua com o dia 1 da ronda {ronda + 1}.")
            res.append({'activista_id': d['activista_id'], 'ronda': ronda, 'capacidade': int(round(meta * pessoas)), 'pessoas': pessoas,
                        'dias': self.saida(dias, pl, ext), 'aprendizagem': apr, 'notas': ' '.join(notas)})
        # ronda seguinte: 1.º dia continua o último dia da ronda actual (campos regados há mais tempo), depois o resto
        pl2 = lambda i: self.pl(i, True)
        todos = [a['id'] for a in d['areas']]
        dias2, d1 = [], []
        if orc1 < W and feitos:
            # continuação: a partir de onde a equipa acaba, o campo mais perto, enquanto couber no resto do dia e sem saltos longos
            d1, cur, resto1 = [], fim, [i for i in feitos if i in self.pos]
            while resto1:
                n = min(resto1, key=lambda i: metros(cur, self.pos[i]) if cur else 0)
                if d1 and metros(cur, self.pos[n]) > SALTO: break
                if self.tempo([(y, pl2(y)) for y in d1 + [n]]) > orc1: break
                d1.append(n); resto1.remove(n); cur = self.pos[n]
            d1 = [d1] if d1 else []
            dias2 = d1
        resto = [i for i in todos if not any(i in x for x in dias2)]
        de2 = self.pos.get(([x for x in dias2[0] if x in self.pos] or [None])[-1]) if dias2 else fim
        dias2 += self.cortar(resto, pl2, de2)
        dias2 = self.sem_coord(dias2, resto, pl2, fora=d1[0] if d1 else None)
        cont = bool(res) and orc1 < W and bool(dias2) and bool(d1)
        notas2 = [f"Ronda {ronda + 1}: {len(todos)} campos."]
        out2 = self.saida(dias2, pl2)
        if cont:
            # o dia 1 começa quando acaba o último dia da ronda actual: sem a espera pela 1.ª água nem as outras esperas do dia
            u = res[0]['dias'][-1]; x = out2[0]
            x['espera_min'] = round(P['en'] * len(x['campos'])); x['outras_min'] = 0
            x['minutos'] = x['espera_min'] + x['rega_min'] + x['desloc_min']
            ini = u['minutos']; hm = lambda m: f"{int(INICIO + m) // 60:02d}:{int(INICIO + m) % 60:02d}"
            x['inicio'] = hm(ini); x['fim'] = hm(ini + x['minutos']); x['continuacao'] = True
            u['continua_ate'] = x['fim']
            notas2.append(f"O dia 1 continua o último dia da ronda {ronda} (a partir das {x['inicio']}).")
        res.append({'activista_id': d['activista_id'], 'ronda': ronda + 1, 'capacidade': int(round(meta * pessoas)), 'pessoas': pessoas,
                    'dias': out2, 'aprendizagem': apr, 'notas': ' '.join(notas2)})
        return res


if __name__ == '__main__':
    print(json.dumps(Equipa(json.load(open(sys.argv[1]))).planos(), ensure_ascii=False))
