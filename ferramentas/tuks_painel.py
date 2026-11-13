#!/usr/bin/env python3
"""Tuk-tuks operacionais no painel operacional do Dalmar (13/11/2026, Valdo: "vais buscar informação sempre que
fizeres relatório para saber quantos tuk-tuks operacionais estão em cada dia").

Uso: python3 ferramentas/tuks_painel.py <html do painel> [AAAA-MM-DD]
O HTML vem de Artifact read de https://claude.ai/artifact/XobTtKkeAPgV3VoSbeiTQo (o resultado diz onde o guardou).
Só leitura. Devolve JSON: gerado (hora dos dados do painel), total, activos (sem sucata nem inactivos),
operacionais (estado OK no controlo mecânico), parados, sem_info, sucata, sairam (tuk-tuks com saída no Controle de
Frota nesse dia; null se o painel não tem saídas desse dia).
Limite: conta o estado que vem nos dados do painel; as mudanças feitas à mão no painel depois de gerado
(base de dados do artefacto) não entram.
"""
import json, sys, collections


def ler(caminho):
    for linha in open(caminho, encoding='utf-8'):
        if linha.lstrip().startswith('const D={') and '"tuks"' in linha[:400]:
            s = linha[linha.index('{'):]
            d, _ = json.JSONDecoder().raw_decode(s)
            return d
    raise SystemExit('Não encontrei os dados dos tuk-tuks no painel (a estrutura mudou?)')


def contar(d, dia=None):
    t = [x for x in d.get('tuks', []) if x.get('tipo') == 'TUK']
    est = collections.Counter(x.get('est') for x in t)
    dias_saida = {s.get('d') for x in t for s in (x.get('saidas_dia') or [])}
    dia = dia or (max(dias_saida) if dias_saida else None)
    sairam = None
    if dia in dias_saida:
        sairam = sum(1 for x in t if any(s.get('d') == dia for s in (x.get('saidas_dia') or [])))
    return {
        'gerado': d.get('gerado'), 'dia_saidas': dia, 'total': len(t),
        'activos': sum(v for k, v in est.items() if k not in ('BAIXADO', 'INATIVO')),
        'operacionais': est.get('OK', 0), 'parados': est.get('PARADO', 0) + est.get('RESTRICAO', 0),
        'sem_info': est.get('SEMINFO', 0), 'sucata': est.get('BAIXADO', 0), 'sairam': sairam,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    print(json.dumps(contar(ler(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None), ensure_ascii=False))
