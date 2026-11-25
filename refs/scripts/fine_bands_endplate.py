# -*- coding: utf-8 -*-
"""细分层方案：把每个 Y 区间按面积变化自适应细分，使每层近似等截面。

对线性锥面，用中点截面拉伸的阶梯近似，误差随层厚趋于零。
本脚本只做体积精度评估，先确认方案可行再生成 DXF。
"""
from __future__ import annotations

import json

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/ep_fine_bands.json'
BREPS = {
    'L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}


def y_planes(shape):
    ys = set()
    for f in shape.Faces:
        if type(f.Surface).__name__ != 'Plane':
            continue
        n = f.normalAt(0, 0)
        if abs(abs(n.y) - 1.0) > 1e-6:
            continue
        ys.add(round(f.CenterOfMass.y, 4))
    return sorted(ys)


def area_at(shape, y, thick=0.02):
    piece = shape.common(Part.makeBox(600, thick, 600, Vector(-150, y, -100)))
    return piece.Volume / thick


def subdivide(shape, y0, y1, tol_rel=0.004, max_t=1.2, min_t=0.02):
    """把 [y0,y1] 细分到每段内面积相对变化 < tol_rel（或达到 min_t）。"""
    out = []
    stack = [(y0, y1)]
    while stack:
        a, b = stack.pop()
        t = b - a
        if t < 1e-6:
            continue
        eps = min(0.01, t * 0.05)
        a0 = area_at(shape, a + eps, min(0.01, t * 0.1))
        a1 = area_at(shape, b - eps - 0.01, min(0.01, t * 0.1))
        ref = max(a0, a1, 1e-6)
        rel = abs(a1 - a0) / ref
        if (rel <= tol_rel and t <= max_t) or t <= min_t * 2:
            out.append({'y0': round(a, 4), 'y1': round(b, 4), 't': round(t, 4),
                        'a0': round(a0, 3), 'a1': round(a1, 3),
                        'rel': round(rel, 5)})
        else:
            mid = (a + b) / 2.0
            stack.append((mid, b))
            stack.append((a, mid))
    out.sort(key=lambda r: r['y0'])
    return out


result = {}
for tag, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    ys = y_planes(shape)
    bands = []
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if y1 - y0 < 1e-3:
            continue
        for b in subdivide(shape, y0, y1):
            mid = (b['y0'] + b['y1']) / 2.0
            am = area_at(shape, mid - 0.01, 0.02)
            b['am'] = round(am, 3)
            b['v'] = round(am * b['t'], 3)
            bands.append(b)
    vsum = sum(b['v'] for b in bands)
    result[tag] = {
        'actual': round(shape.Volume, 3),
        'fine_sum': round(vsum, 3),
        'err_pct': round((vsum - shape.Volume) / shape.Volume * 100.0, 4),
        'n_layers': len(bands),
        'bands': bands,
    }

json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
for tag, r in result.items():
    print('%s  layers %3d  actual %.2f  fine %.2f  err %+.4f%%'
          % (tag, r['n_layers'], r['actual'], r['fine_sum'], r['err_pct']))
