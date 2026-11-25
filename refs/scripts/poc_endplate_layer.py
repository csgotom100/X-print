# -*- coding: utf-8 -*-
"""逐面复刻端板 POC：单层 DXF -> SolidCraft sketch.insert_dxf -> extrude -> 量体积。

用薄片真实体积/厚度作为该层截面积（最可靠，避开 Face 构造退化）。
"""
from __future__ import annotations

import json
import os

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT_DIR = ROOT + '/refs/tmp/dxf'
os.makedirs(OUT_DIR, exist_ok=True)
BREP = ROOT + '/refs/orig_X_EndPlate_L.brep'


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


def area_via_slab(shape, y, thick=0.02):
    slab = Part.makeBox(600, thick, 600, Vector(-150, y, -100))
    return shape.common(slab).Volume / thick


shape = Part.Shape()
shape.read(BREP)
ys = y_planes(shape)
print('planes', ys)

# 列出每层用薄片法测得的上下面积
rows = []
for i in range(len(ys) - 1):
    y0, y1 = ys[i], ys[i + 1]
    t = y1 - y0
    if t < 1e-3:
        continue
    a0 = area_via_slab(shape, y0 + min(0.01, t * 0.02))
    a1 = area_via_slab(shape, y1 - min(0.01, t * 0.02) - 0.02)
    rows.append({'y0': y0, 'y1': y1, 't': round(t, 4),
                 'a0': round(a0, 3), 'a1': round(a1, 3),
                 'prismatic': abs(a0 - a1) < 0.3})
    print('%8.2f..%8.2f t=%5.2f  a0 %8.2f  a1 %8.2f  %s'
          % (y0, y1, t, a0, a1, 'PRISM' if abs(a0 - a1) < 0.3 else 'loft'))

vsum = sum((r['a0'] + r['a1']) / 2 * r['t'] for r in rows)
print('layered (avg) %.2f  actual %.2f  err %+.3f%%'
      % (vsum, shape.Volume, (vsum - shape.Volume) / shape.Volume * 100))

json.dump({'ys': ys, 'rows': rows, 'actual': shape.Volume,
           'layered': vsum}, open(ROOT + '/refs/tmp/ep_L_bands.json', 'w',
                                  encoding='utf-8'), ensure_ascii=False, indent=1)
