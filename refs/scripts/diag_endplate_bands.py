# -*- coding: utf-8 -*-
"""诊断：每个 Y 层是否等截面（上下两端面积一致），找出需要细分的层。"""
from __future__ import annotations

import json

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/x_endplate_band_diag.json'
BREPS = {
    'X_EndPlate_L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'X_EndPlate_R': ROOT + '/refs/orig_X_EndPlate_R.brep',
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


def face_at(shape, y, side, thick=0.03):
    """在 y 处切厚 thick 的薄片，返回 side 侧的平面面面积与面数。"""
    lo, hi = y, y + thick
    slab = Part.makeBox(600, thick, 600, Vector(-150, lo, -100))
    piece = shape.common(slab)
    if piece.Volume < 1e-9:
        return 0.0, 0
    want = -1.0 if side == 'lo' else 1.0
    area = 0.0
    cnt = 0
    for f in piece.Faces:
        if type(f.Surface).__name__ != 'Plane':
            continue
        n = f.normalAt(0, 0)
        if abs(n.y - want) > 1e-6:
            continue
        area += f.Area
        cnt += 1
    return area, cnt


out = {}
for name, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    ys = y_planes(shape)
    rows = []
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if y1 - y0 < 1e-3:
            continue
        a0, c0 = face_at(shape, y0, 'lo')
        a1, c1 = face_at(shape, y1 - 0.03, 'hi')
        t = y1 - y0
        rows.append({
            'y0': y0, 'y1': y1, 't': round(t, 4),
            'area_lo': round(a0, 3), 'area_hi': round(a1, 3),
            'faces_lo': c0, 'faces_hi': c1,
            'ratio': round((a1 / a0) if a0 > 1e-6 else 0.0, 4),
            'prismatic': abs(a1 - a0) < 1e-3,
            'vol_lo': round(a0 * t, 3), 'vol_hi': round(a1 * t, 3),
        })
    out[name] = {'volume': round(shape.Volume, 3), 'rows': rows}

with open(OUT, 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, indent=1)

print('WROTE', OUT)
for name, rec in out.items():
    print('===', name, 'actual V', rec['volume'])
    s_lo = sum(r['vol_lo'] for r in rec['rows'])
    s_hi = sum(r['vol_hi'] for r in rec['rows'])
    print('  sum(lo*t) %.1f   sum(hi*t) %.1f' % (s_lo, s_hi))
    for r in rec['rows']:
        flag = '' if r['prismatic'] else '  <-- 非等截面'
        print('  %7.2f..%7.2f t=%5.2f  lo %8.2f  hi %8.2f  ratio %5.2f%s'
              % (r['y0'], r['y1'], r['t'], r['area_lo'], r['area_hi'],
                 r['ratio'], flag))
