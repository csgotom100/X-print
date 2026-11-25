# -*- coding: utf-8 -*-
"""按 Y 层切片，取该层完整的横截面（所有 -Y 面的并集），并核对体积。

逐面复刻路径：每层横截面 -> DXF -> SolidCraft sketch.insert_dxf -> solid.extrude。
本脚本负责第一步与体积核对。
"""
from __future__ import annotations

import json
import math

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/x_endplate_sections.json'
BREPS = {
    'X_EndPlate_L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'X_EndPlate_R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}


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


def loops_from_face(face):
    """一个平面面的外环 + 内环，各自有序曲线。"""
    loops = []
    wires = [face.OuterWire] + [w for w in face.Wires if not w.isSame(face.OuterWire)]
    for wi, w in enumerate(wires):
        curves = []
        for e in w.OrderedEdges:
            c = e.Curve
            t = type(c).__name__
            rec = {'t': t, 'p0': p2(e.Vertexes[0].Point), 'p1': p2(e.Vertexes[-1].Point)}
            if t == 'Circle':
                rec['c'] = p2(c.Center)
                rec['r'] = round(float(c.Radius), 5)
                mid = e.valueAt((e.FirstParameter + e.LastParameter) / 2.0)
                rec['pm'] = p2(mid)
            elif t != 'Line':
                rec['poly'] = [p2(p) for p in e.discretize(Number=12)]
            curves.append(rec)
        loops.append({'outer': wi == 0, 'curves': curves})
    return loops


def section_at(shape, y, eps=0.02):
    """在 y 处取薄片，收集其 -Y 侧所有平面面，合并成完整横截面。"""
    lo = y
    hi = y + eps
    slab = Part.makeBox(600, eps, 600, Vector(-150, lo, -100))
    piece = shape.common(slab)
    if piece.Volume < 1e-6:
        return None
    faces = []
    for f in piece.Faces:
        if type(f.Surface).__name__ != 'Plane':
            continue
        n = f.normalAt(0, 0)
        if abs(n.y + 1.0) > 1e-6:
            continue
        faces.append(f)
    if not faces:
        return None
    loops = []
    area = 0.0
    for f in faces:
        area += f.Area
        loops.extend(loops_from_face(f))
    return {'y': round(y, 4), 'area': round(area, 4),
            'n_faces': len(faces), 'loops': loops}


result = {}
for name, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    ys = y_planes(shape)
    bands = []
    vsum = 0.0
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        if y1 - y0 < 1e-3:
            continue
        t = y1 - y0
        # 在层内部取样（两端各让 5% 且至少 0.02 mm），避免落在边界零厚度处
        inset = max(0.02, t * 0.05)
        ys_probe = y0 + inset
        if y1 - inset <= ys_probe:
            ys_probe = (y0 + y1) / 2.0
        sec = section_at(shape, ys_probe, eps=min(0.02, t * 0.1))
        if sec is None:
            bands.append({'y0': y0, 'y1': y1, 't': round(t, 4), 'area': 0.0,
                          'n_loops': 0, 'n_curves': 0, 'loops': []})
            continue
        ncurves = sum(len(l['curves']) for l in sec['loops'])
        vsum += sec['area'] * t
        bands.append({'y0': y0, 'y1': y1, 't': round(t, 4),
                      'area': sec['area'], 'n_loops': len(sec['loops']),
                      'n_curves': ncurves, 'loops': sec['loops']})
    result[name] = {
        'bbox': [round(v, 4) for v in
                 (shape.BoundBox.XMin, shape.BoundBox.YMin, shape.BoundBox.ZMin,
                  shape.BoundBox.XMax, shape.BoundBox.YMax, shape.BoundBox.ZMax)],
        'actual_volume': round(shape.Volume, 4),
        'layered_volume': round(vsum, 4),
        'error_pct': round((vsum - shape.Volume) / shape.Volume * 100.0, 3),
        'face_count': len(shape.Faces),
        'ys': ys, 'bands': bands,
    }

json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
for name, rec in result.items():
    print('===', name, 'actual %.2f  layered %.2f  error %+.3f%%'
          % (rec['actual_volume'], rec['layered_volume'], rec['error_pct']))
    tc = 0
    for b in rec['bands']:
        tc += b['n_curves']
        print('  %7.2f..%7.2f t=%5.2f  A %8.2f  V %9.2f  loops %2d curves %3d'
              % (b['y0'], b['y1'], b['t'], b['area'], b['area'] * b['t'],
                 b['n_loops'], b['n_curves']))
    print('  total curves', tc)
