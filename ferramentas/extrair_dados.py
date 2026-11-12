#!/usr/bin/env python3
"""Tira a coluna «dados» do resultado de ferramentas/relatorio_dia.sql quando o resultado é grande
e o conector o guardou num ficheiro (desde 12/11/2026 o JSON leva a lista completa dos campos, ~0,5 MB).

Uso: python3 ferramentas/extrair_dados.py <ficheiro guardado pelo conector> dados.json

Aceita o texto tal como o conector o guarda ({"result": "...[{\"dados\": {...}}]..."}) ou já só o JSON.
"""
import json
import sys


def extrair(texto):
    try:
        o = json.loads(texto)
        if isinstance(o, dict) and isinstance(o.get('result'), str):
            texto = o['result']
        elif isinstance(o, list) and o and isinstance(o[0], dict) and 'dados' in o[0]:
            return o[0]['dados']
        elif isinstance(o, dict) and 'rega' in o:
            return o
    except ValueError:
        pass
    i = texto.find('[{"dados"')
    if i < 0:
        raise SystemExit('Não encontrei a coluna «dados» no ficheiro.')
    linhas, _ = json.JSONDecoder().raw_decode(texto[i:])
    return linhas[0]['dados']


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    d = extrair(open(sys.argv[1], encoding='utf-8').read())
    json.dump(d, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
    print('ok', sys.argv[2], 'campos:', len(d.get('campos') or []))
