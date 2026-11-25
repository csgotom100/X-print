# -*- coding: utf-8 -*-
"""导出每层截面的 DXF（XZ 平面，Y 归零），供 SolidCraft sketch.insert_dxf 使用。"""
from __future__ import annotations

import json
import os

import Part
from FreeCAD import Vector
import importDXF

ROOT = 'C:/ink'
OUT_DIR = ROOT + '/refs/tmp/dxf'
os.makedirs(OUT_DIR, exist_ok=True)
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


manifest = {}
for tag, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    ys = y_planes(shape)
    rows = []
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        t = y1 - y0
        if t < 1e-3:
            continue
        # 层内取样（避开边界）
        ylo = y0 + min(0.01, t * 0.02)
        yhi = y1 - min(0.01, t * 0.02)
        if yhi - ylo < 0.005:
            ylo, yhi = (y0 + y1) / 2 - 0.002, (y0 + y1) / 2 + 0.002
        a0 = shape.common(Part.makeBox(600, 0.02, 600, Vector(-150, ylo, -100))).Volume / 0.02
        a1 = shape.common(Part.makeBox(600, 0.02, 600, Vector(-150, yhi - 0.02, -100))).Volume / 0.02
        prismatic = abs(a0 - a1) < 0.3
        row = {'index': i, 'y0': round(y0, 4), 'y1': round(y1, 4),
               't': round(t, 4), 'a0': round(a0, 3), 'a1': round(a1, 3),
               'prismatic': prismatic}
        if prismatic:
            ws = shape.slice(Vector(0, 1, 0), (y0 + y1) / 2)
            comp = Part.Compound([Part.Face(w) for w in ws])
            comp.translate(Vector(0, -(y0 + y1) / 2, 0))
            f = os.path.join(OUT_DIR, 'EP%s_%02d.dxf' % (tag, i))
            importDXF.export([comp], f)
            row['dxf'] = f
            row['wires'] = len(ws)
        rows.append(row)
    manifest[tag] = rows

json.dump(manifest, open(ROOT + '/refs/tmp/ep_dxf_manifest.json', 'w',
                         encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE manifest')
for tag, rows in manifest.items():
    prism = [r for r in rows if r['prismatic']]
    print(tag, 'bands', len(rows), 'prismatic', len(prism),
          'loft', len(rows) - len(prism))
    for r in prism:
        print('   EP%s_%02d  %.2f..%.2f  t %.2f  A %.2f  wires %d'
              % (tag, r['index'], r['y0'], r['y1'], r['t'], r['a0'], r['wires']))
