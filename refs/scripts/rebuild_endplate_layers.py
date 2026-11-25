# -*- coding: utf-8 -*-
"""逐面复刻端板：按 Y 特征层取上下精确截面，等截面拉伸 / 变截面放样。

输出：
  refs/tmp/x_endplate_rebuild.json  每层的截面曲线（世界 XZ 坐标）
  refs/tmp/dxf/EP_<name>_bandNN.dxf 每层截面的 DXF（供 SolidCraft 参考）
  控制台：逐层体积与总误差
"""
from __future__ import annotations

import json
import math
import os

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/x_endplate_rebuild.json'
DXF_DIR = ROOT + '/refs/tmp/dxf'
BREPS = {
    'X_EndPlate_L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'X_EndPlate_R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}
os.makedirs(DXF_DIR, exist_ok=True)

EPS = 0.006


def p2(v):
    return [round(float(v.x), 5), round(float(v.z), 5)]


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


def wires_at(shape, y):
    return shape.slice(Vector(0, 1, 0), y)


def wire_curves(w):
    """一条闭合 wire 的有序曲线（XZ 平面）。"""
    out = []
    for e in w.OrderedEdges:
        c = e.Curve
        t = type(c).__name__
        rec = {'t': t, 'p0': p2(e.Vertexes[0].Point), 'p1': p2(e.Vertexes[-1].Point)}
        if t == 'Circle':
            rec['c'] = p2(c.Center)
            rec['r'] = round(float(c.Radius), 5)
            mid = e.valueAt((e.FirstParameter + e.LastParameter) / 2.0)
            rec['pm'] = p2(mid)
        elif t == 'Line':
            pass
        else:
            rec['poly'] = [p2(p) for p in e.discretize(Number=12)]
        out.append(rec)
    return out


def wires_area(ws):
    """带孔截面面积：按面积降序，首个为外环，其余为孔。"""
    if not ws:
        return 0.0
    ordered = sorted(ws, key=lambda w: -Part.Face(w).Area)
    try:
        return Part.Face(ordered).Area
    except Exception:
        return sum(Part.Face(w).Area for w in ordered)


def build_band(shape, y0, y1):
    """返回该层的建模方案与体积。"""
    t = y1 - y0
    lo_y = y0 + min(EPS, t * 0.02)
    hi_y = y1 - min(EPS, t * 0.02)
    if hi_y <= lo_y:
        lo_y, hi_y = y0 + t * 0.3, y0 + t * 0.7
    wa = wires_at(shape, lo_y)
    wb = wires_at(shape, hi_y)
    aa, ab = wires_area(wa), wires_area(wb)
    # 等截面判断：面积差 < 0.5 mm² 且 wire 数一致
    prismatic = abs(aa - ab) < 0.5 and len(wa) == len(wb)
    if prismatic:
        vol = aa * t
        mode = 'extrude'
    else:
        # 棱柱体近似（A0+A1)/2 * t，仅作体积预估
        vol = (aa + ab) / 2.0 * t
        mode = 'loft'
    return {
        'y0': round(y0, 4), 'y1': round(y1, 4), 't': round(t, 4),
        'mode': mode,
        'area_lo': round(aa, 4), 'area_hi': round(ab, 4),
        'est_volume': round(vol, 4),
        'loops_lo': len(wa), 'loops_hi': len(wb),
        'sec_lo': [wire_curves(w) for w in wa],
        'sec_hi': [wire_curves(w) for w in wb],
    }


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
        bands.append(build_band(shape, y0, y1))
    vsum = sum(b['est_volume'] for b in bands)
    result[name] = {
        'bbox': [round(v, 4) for v in
                 (shape.BoundBox.XMin, shape.BoundBox.YMin, shape.BoundBox.ZMin,
                  shape.BoundBox.XMax, shape.BoundBox.YMax, shape.BoundBox.ZMax)],
        'actual_volume': round(shape.Volume, 4),
        'layered_volume': round(vsum, 4),
        'error_pct': round((vsum - shape.Volume) / shape.Volume * 100.0, 3),
        'face_count': len(shape.Faces),
        'ys': ys,
        'bands': bands,
    }

json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
for name, rec in result.items():
    print('===', name, 'actual %.2f  layered %.2f  error %+.3f%%'
          % (rec['actual_volume'], rec['layered_volume'], rec['error_pct']))
    for b in rec['bands']:
        print('  %7.2f..%7.2f t=%5.2f %-8s A %7.2f/%7.2f  V %9.2f'
              % (b['y0'], b['y1'], b['t'], b['mode'],
                 b['area_lo'], b['area_hi'], b['est_volume']))
