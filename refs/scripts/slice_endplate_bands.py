# -*- coding: utf-8 -*-
"""在相邻 Y 特征层的中点切片，得到每层的完整闭合截面（wire 集合）。

逐面复刻端板：每个 Y 区间截面恒定（侧面为垂直 Y 的拉伸面或圆柱），
所以「区间中点切片 + 拉伸整段厚度」可精确还原原始 BREP。
"""
from __future__ import annotations

import json
import os

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/x_endplate_bands.json'
BREPS = {
    'X_EndPlate_L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'X_EndPlate_R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}


def p2(v):
    return [round(float(v.x), 5), round(float(v.z), 5)]


def p3(v):
    return [round(float(v.x), 5), round(float(v.y), 5), round(float(v.z), 5)]


def y_planes(shape):
    ys = set()
    for f in shape.Faces:
        s = f.Surface
        if type(s).__name__ != 'Plane':
            continue
        n = s.Axis
        if abs(abs(n.y) - 1.0) > 1e-6:
            continue
        ys.add(round(s.Position.y, 4))
    return sorted(ys)


def cut_plane(y):
    # 法向 +Y 的平面，位于 X-Z 平面内
    return Part.makePlane(600, 600, Vector(-150, y, 100), Vector(0, 1, 0))


def band_slice(shape, y0, y1, eps=0.02):
    """取 [y0+eps, y1-eps] 的薄片，返回其 -Y 端面（闭合环集合）。"""
    lo = y0 + eps
    hi = y1 - eps
    if hi <= lo:
        lo, hi = y0 + 1e-3, y1 - 1e-3
    slab = Part.makeBox(600, hi - lo, 600, Vector(-150, lo, -100))
    piece = shape.common(slab)
    if piece.Volume < 1e-9:
        return None, 0.0
    # 取法向 -Y 的平面面（靠 lo 一侧）
    best = None
    for f in piece.Faces:
        s = f.Surface
        if type(s).__name__ != 'Plane':
            continue
        n = f.normalAt(0, 0)
        if abs(n.y + 1.0) > 1e-6:
            continue
        y = f.CenterOfMass.y
        if best is None or abs(y - lo) < abs(best[0] - lo):
            best = (y, f)
    if best is None:
        return None, piece.Volume
    return best[1], piece.Volume


def loops_of(face):
    """把一个平面面拆成闭合环：外环 + 内环，各自输出有序曲线。"""
    loops = []
    wires = [face.OuterWire] + [w for w in face.Wires if not w.isSame(face.OuterWire)]
    for w in wires:
        curves = []
        for e in w.OrderedEdges:
            c = e.Curve
            t = type(c).__name__
            rec = {'t': t}
            vs = e.Vertexes
            rec['p0'] = p2(vs[0].Point)
            rec['p1'] = p2(vs[-1].Point)
            if t == 'Line':
                pass
            elif t == 'Circle':
                rec['c'] = p2(c.Center)
                rec['r'] = round(float(c.Radius), 5)
                mid = e.valueAt((e.FirstParameter + e.LastParameter) / 2.0)
                rec['pm'] = p2(mid)
                rec['cw'] = bool(_is_cw(rec['c'], rec['p0'], rec['pm'], rec['p1']))
            else:
                rec['poly'] = [p2(p) for p in e.discretize(Number=10)]
            curves.append(rec)
        loops.append(curves)
    return loops


def _is_cw(c, a, m, b):
    """三点圆弧方向：叉积 < 0 视为顺时针（X-Z 平面，右手系以 +Y 为法向）。"""
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    # 用圆心到三点的角度序列判断
    import math
    def ang(p):
        return math.atan2(p[1] - c[1], p[0] - c[0])
    a0, am, a1 = ang(a), ang(m), ang(b)
    # 归一化到 [0, 2pi)
    def norm(x):
        while x < 0:
            x += 2 * math.pi
        return x
    d1 = norm(am - a0)
    d2 = norm(a1 - am)
    return (d1 + d2) > math.pi


result = {}
for name, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    ys = y_planes(shape)
    bands = []
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if y1 - y0 < 1e-3:
            continue
        ym = (y0 + y1) / 2.0
        face, vol = band_slice(shape, y0, y1)
        loops = loops_of(face) if face is not None else []
        ncurves = sum(len(l) for l in loops)
        area = face.Area if face is not None else 0.0
        bands.append({
            'y0': y0, 'y1': y1, 't': round(y1 - y0, 4),
            'loops': loops, 'n_loops': len(loops), 'n_curves': ncurves,
            'area': round(area, 4), 'slab_volume': round(vol, 4),
        })
    result[name] = {
        'bbox': [round(v, 4) for v in
                 (shape.BoundBox.XMin, shape.BoundBox.YMin, shape.BoundBox.ZMin,
                  shape.BoundBox.XMax, shape.BoundBox.YMax, shape.BoundBox.ZMax)],
        'volume_mm3': round(shape.Volume, 4),
        'face_count': len(shape.Faces),
        'ys': ys,
        'bands': bands,
    }

with open(OUT, 'w', encoding='utf-8') as fp:
    json.dump(result, fp, ensure_ascii=False, indent=1)

print('WROTE', OUT)
for name, rec in result.items():
    print('===', name, 'V', rec['volume_mm3'], 'faces', rec['face_count'])
    tot_c = 0
    tot_est = 0.0
    for b in rec['bands']:
        tot_c += b['n_curves']
        tot_est += b['area'] * b['t']
        print('  %8.2f..%8.2f  t=%6.2f  loops %2d  curves %3d  area %8.2f'
              % (b['y0'], b['y1'], b['t'], b['n_loops'], b['n_curves'], b['area']))
    print('  total curves', tot_c, ' est volume', round(tot_est, 2),
          ' actual', rec['volume_mm3'])
