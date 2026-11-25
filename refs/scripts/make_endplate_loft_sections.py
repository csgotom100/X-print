# -*- coding: utf-8 -*-
"""为放样层生成「按外环拆分」的上下截面 DXF，保证每份只有一个轮廓。

每层：pick_loops 得到若干外环（各自带孔）。上下截面的外环按包围盒中心匹配配对，
分别写 EP<tag><i>_o<k>_lo.dxf / _hi.dxf。
"""
from __future__ import annotations

import json
import os
import sys

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT_DIR = ROOT + '/refs/tmp/dxf'
LOFT_MAN = ROOT + '/refs/tmp/ep_loft_manifest.json'
MAN = ROOT + '/refs/tmp/ep_dxf_manifest.json'
OUT = ROOT + '/refs/tmp/ep_loft_sections.json'
BREPS = {
    'L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}

sys.path.insert(0, ROOT + '/refs/scripts')
from write_endplate_dxf import pick_loops, wire_entities, write_dxf  # noqa: E402


def key_of(bb):
    return (round((bb.XMin + bb.XMax) / 2, 1), round((bb.YMin + bb.YMax) / 2, 1))


loft_man = json.load(open(LOFT_MAN, encoding='utf-8'))
man = json.load(open(MAN, encoding='utf-8'))
out = {}

for tag, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    rows = []
    for r in loft_man[tag]:
        if not r['loft']:
            continue
        y0, y1, t = r['y0'], r['y1'], r['t']
        eps = min(0.02, t * 0.02)
        ylo, yhi = y0 + eps, y1 - eps
        secs = {}
        for side, y in (('lo', ylo), ('hi', yhi)):
            ws = shape.slice(Vector(0, 1, 0), y)
            groups = pick_loops(ws)
            secs[side] = groups
        # 配对：优先按包围盒重叠面积，其次按中心距离
        def overlap(a, b):
            x0 = max(a.XMin, b.XMin)
            x1 = min(a.XMax, b.XMax)
            y0_ = max(a.YMin, b.YMin)
            y1_ = min(a.YMax, b.YMax)
            if x1 <= x0 or y1_ <= y0_:
                return 0.0
            return (x1 - x0) * (y1_ - y0_)

        pairs = []
        used = set()
        cand = []
        for k, glo in enumerate(secs['lo']):
            for j, ghi in enumerate(secs['hi']):
                ov = overlap(glo['bb'], ghi['bb'])
                c1 = key_of(glo['bb'])
                c2 = key_of(ghi['bb'])
                dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
                cand.append((-ov, dist, k, j))
        cand.sort()
        for negov, dist, k, j in cand:
            if k in used or j in used:
                continue
            ov = -negov
            if ov <= 0.5 and dist > 12.0:
                continue
            used.add(k)
            used.add(j)
            pairs.append((k, j, dist))
        files = []
        for n, (k, j, bd) in enumerate(pairs):
            flo = os.path.join(OUT_DIR, 'EP%s%02d_o%d_lo.dxf' % (tag, r['index'], n))
            fhi = os.path.join(OUT_DIR, 'EP%s%02d_o%d_hi.dxf' % (tag, r['index'], n))
            for f, g in ((flo, secs['lo'][k]), (fhi, secs['hi'][j])):
                ents = wire_entities(g['outer'])
                for h in g['holes']:
                    ents += wire_entities(h)
                write_dxf(f, ents)
            files.append({'lo': flo, 'hi': fhi, 'match': round(bd, 2),
                          'holes_lo': len(secs['lo'][k]['holes']),
                          'holes_hi': len(secs['hi'][j]['holes'])})
        rows.append({'index': r['index'], 'y0': y0, 'y1': y1, 't': t,
                     'ylo': ylo, 'yhi': yhi,
                     'n_lo': len(secs['lo']), 'n_hi': len(secs['hi']),
                     'pairs': files})
    out[tag] = rows

json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
for tag, rows in out.items():
    tot = sum(len(r['pairs']) for r in rows)
    print(tag, 'loft layers', len(rows), 'section pairs', tot)
    for r in rows:
        print('  %s%02d t%5.2f lo %d hi %d pairs %d'
              % (tag, r['index'], r['t'], r['n_lo'], r['n_hi'], len(r['pairs'])))
