# -*- coding: utf-8 -*-
"""逐层比较：slab 实际体积 vs area*t，定位偏差层。"""
from __future__ import annotations

import json

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
SECT = ROOT + '/refs/tmp/x_endplate_sections.json'
BREPS = {
    'X_EndPlate_L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'X_EndPlate_R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}

sect = json.load(open(SECT, encoding='utf-8'))
for name, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    print('===', name)
    worst = []
    for b in sect[name]['bands']:
        y0, y1, t = b['y0'], b['y1'], b['t']
        slab = Part.makeBox(600, t, 600, Vector(-150, y0, -100))
        piece = shape.common(slab)
        real = piece.Volume
        est = b['area'] * t
        d = est - real
        worst.append((abs(d), y0, y1, t, real, est, d))
    worst.sort(reverse=True)
    for a, y0, y1, t, real, est, d in worst[:6]:
        print('  %7.2f..%7.2f t=%5.2f  real %9.2f  est %9.2f  diff %+8.2f (%+.2f%%)'
              % (y0, y1, t, real, est, d, (d / real * 100.0) if real > 1e-9 else 0.0))
