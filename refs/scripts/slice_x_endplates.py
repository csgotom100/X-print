# -*- coding: utf-8 -*-
"""切片原始 X 端板，输出截面边离散点，供原生草图重建参考。"""
from __future__ import annotations

import json
import os

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/x_endplate_slices.json'
BREPS = {
    'X_EndPlate_L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'X_EndPlate_R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}
PLANES = {
    'X_EndPlate_L': [
        ('Y', -82.0), ('Y', -79.0), ('Y', -72.2), ('Y', -71.4),
        ('Y', -65.0), ('Y', -64.8), ('Y', -62.0), ('Y', -58.0),
        ('Y', -57.0), ('Y', -50.0), ('Y', -38.0), ('Y', -37.0),
        ('X', 0.0), ('X', 42.5), ('X', 49.9), ('X', 50.0), ('X', 53.0),
    ],
    'X_EndPlate_R': [
        ('Y', -82.0), ('Y', -79.0), ('Y', -72.2), ('Y', -71.4),
        ('Y', -65.0), ('Y', -64.8), ('Y', -61.5), ('Y', -58.0),
        ('Y', -57.0), ('Y', -50.0), ('Y', -38.0), ('Y', -37.0),
        ('X', 249.0), ('X', 250.0), ('X', 257.5), ('X', 258.0), ('X', 300.0),
    ],
}


def plane(axis, value):
    if axis == 'Y':
        return Part.makePlane(400, 400, Vector(-100, value, 80), Vector(0, 1, 0))
    return Part.makePlane(400, 400, Vector(value, -120, 280), Vector(1, 0, 0))


def pt(p):
    return [round(float(p.x), 4), round(float(p.y), 4), round(float(p.z), 4)]


out = {}
for name, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    rec = {}
    for axis, value in PLANES[name]:
        sec = shape.section(plane(axis, value))
        edges = []
        for e in sec.Edges:
            pts = [pt(p) for p in e.discretize(Number=24)]
            edges.append({'type': type(e.Curve).__name__, 'points': pts})
        rec['%s=%.2f' % (axis, value)] = edges
    out[name] = rec

with open(OUT, 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, indent=1)
print('WROTE', OUT)
for name, rec in out.items():
    print(name, {k: len(v) for k, v in rec.items()})
