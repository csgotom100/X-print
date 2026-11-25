# -*- coding: utf-8 -*-
"""用截面面积随 Y 的变化做解析积分，评估细分层数与精度。

面积用 slice 得到的环面积（快），不做布尔切薄片。
"""
from __future__ import annotations

import json

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/ep_area_profile.json'
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


def area_slice(shape, y):
    ws = shape.slice(Vector(0, 1, 0), y)
    if not ws:
        return 0.0
    # 外环减内环：按包含关系累计
    infos = []
    for w in ws:
        try:
            f = Part.Face(w)
            infos.append((f.Area, f.BoundBox))
        except Exception:
            pass
    if not infos:
        return 0.0
    infos.sort(key=lambda t: -t[0])
    total = 0.0
    outers = []
    for a, b in infos:
        inside = False
        for oa, ob in outers:
            if (b.XMin >= ob.XMin - 1e-6 and b.XMax <= ob.XMax + 1e-6
                    and b.YMin >= ob.YMin - 1e-6 and b.YMax <= ob.YMax + 1e-6):
                inside = True
                break
        if inside:
            total -= a
        else:
            total += a
            outers.append((a, b))
    return total


result = {}
for tag, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    ys = y_planes(shape)
    prof = []
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if y1 - y0 < 1e-3:
            continue
        # 每段取 9 个采样点
        pts = []
        for k in range(9):
            y = y0 + (y1 - y0) * (k / 8.0)
            if k == 0:
                y = y0 + 1e-3
            elif k == 8:
                y = y1 - 1e-3
            pts.append((round(y, 4), round(area_slice(shape, y), 4)))
        # 梯形积分
        v = 0.0
        for (ya, aa), (yb, ab) in zip(pts[:-1], pts[1:]):
            v += (aa + ab) / 2.0 * (yb - ya)
        prof.append({'y0': y0, 'y1': y1, 't': round(y1 - y0, 4),
                     'samples': pts, 'v': round(v, 3),
                     'a_min': min(p[1] for p in pts),
                     'a_max': max(p[1] for p in pts)})
    vsum = sum(p['v'] for p in prof)
    result[tag] = {'actual': round(shape.Volume, 3), 'integrated': round(vsum, 3),
                   'err_pct': round((vsum - shape.Volume) / shape.Volume * 100, 4),
                   'bands': prof}

json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
for tag, r in result.items():
    print('%s actual %.2f integrated %.2f err %+.4f%%'
          % (tag, r['actual'], r['integrated'], r['err_pct']))
    for p in r['bands']:
        print('  %7.2f..%7.2f t%5.2f A %7.2f..%7.2f  V %9.2f'
              % (p['y0'], p['y1'], p['t'], p['a_min'], p['a_max'], p['v']))
