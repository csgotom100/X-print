# -*- coding: utf-8 -*-
"""列出 X_EndPlate_L/R 的面类型，定位 SolidCraft STEP 导入丢弃的 49 个面。"""
from __future__ import annotations
import collections
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import Part

ROOT = 'C:/ink'
BRP = ROOT + '/refs/tmp/brp_lm6'
LOGP = ROOT + '/refs/tmp/diag_xendplate_faces.log'
_f = open(LOGP, 'w', encoding='utf-8')


def P(*a):
    s = ' '.join(str(x) for x in a)
    try:
        print(s)
    except Exception:
        pass
    _f.write(s + '\n')
    _f.flush()
    os.fsync(_f.fileno())


for name in ('X_EndPlate_L', 'X_EndPlate_R', 'Z_EndPlate_L'):
    s = Part.Shape()
    s.read(os.path.join(BRP, name + '.Shape.brp'))
    cnt = collections.Counter()
    small = []
    for i, f in enumerate(s.Faces):
        t = type(f.Surface).__name__
        cnt[t] += 1
        if t not in ('Plane', 'Cylinder'):
            b = f.BoundBox
            small.append((i, t, round(f.Area, 4),
                          [round(v, 2) for v in (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)]))
    P('===', name, 'faces', len(s.Faces), dict(cnt))
    P('  non-analytic count', len(small))
    for row in small[:12]:
        P('   ', row)

P('DIAG DONE')
_f.close()
