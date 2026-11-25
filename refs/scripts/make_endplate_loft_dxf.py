# -*- coding: utf-8 -*-
"""为层内变截面（锥面）的层生成上下双截面 DXF，供 solid.loft 使用。

判定：层内上下面积差 > 3% 或该层为厚层（t >= 1 mm）且面积差 > 1 mm²。
输出 EP<tag><i>_lo.dxf / EP<tag><i>_hi.dxf 及 loft 清单。
"""
from __future__ import annotations

import json
import os

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT_DIR = ROOT + '/refs/tmp/dxf'
MANIFEST = ROOT + '/refs/tmp/ep_dxf_manifest.json'
OUT = ROOT + '/refs/tmp/ep_loft_manifest.json'
BREPS = {
    'L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}

import sys
sys.path.insert(0, ROOT + '/refs/scripts')
from write_endplate_dxf import (pick_loops, wire_entities, write_dxf,  # noqa: E402
                                layer_area)


def section(shape, y):
    ws = shape.slice(Vector(0, 1, 0), y)
    return ws


man = json.load(open(MANIFEST, encoding='utf-8'))
out = {}
for tag, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    rows = []
    for r in man[tag]:
        y0, y1, t = r['y0'], r['y1'], r['t']
        eps = min(0.02, t * 0.02)
        ylo, yhi = y0 + eps, y1 - eps
        alo = layer_area(shape, ylo, min(0.02, t * 0.2))
        ahi = layer_area(shape, yhi - 0.02, min(0.02, t * 0.2))
        rel = abs(ahi - alo) / max(alo, 1e-6)
        need = (rel > 0.03) or (t >= 1.0 and abs(ahi - alo) > 1.0)
        rec = {'index': r['index'], 'y0': y0, 'y1': y1, 't': t,
               'alo': round(alo, 3), 'ahi': round(ahi, 3),
               'rel': round(rel, 4), 'loft': need}
        if need:
            for tag2, y in (('lo', ylo), ('hi', yhi)):
                ws = section(shape, y)
                groups = pick_loops(ws)
                f = os.path.join(OUT_DIR, 'EP%s%02d_%s.dxf' % (tag, r['index'], tag2))
                # 放样需要单一外环：只写最大外环及其孔（SolidCraft loft 接受带孔轮廓）
                ents = []
                if groups:
                    g = groups[0]
                    ents += wire_entities(g['outer'])
                    for h in g['holes']:
                        ents += wire_entities(h)
                write_dxf(f, ents)
                rec[tag2] = f
        rows.append(rec)
    out[tag] = rows

json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
for tag, rows in out.items():
    lofts = [r for r in rows if r['loft']]
    print(tag, 'layers', len(rows), 'loft layers', len(lofts))
    for r in lofts:
        print('   %s%02d t%5.2f  A %.2f -> %.2f  rel %+.1f%%'
              % (tag, r['index'], r['t'], r['alo'], r['ahi'], r['rel'] * 100))
