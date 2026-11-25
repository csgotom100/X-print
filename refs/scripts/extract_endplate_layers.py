# -*- coding: utf-8 -*-
"""把 X_EndPlate_L/R 按 Y 特征面分层，提取每层的有序闭合轮廓（外环 + 内环）。

用途：逐面复刻端板。输出每层的 Line / Arc / Circle 序列，可直接转成
SolidCraft 的 sketch.line / sketch.arc.three_point / sketch.circle.center + solid.extrude。
"""
from __future__ import annotations

import json
import os

import Part

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/x_endplate_layers.json'
BREPS = {
    'X_EndPlate_L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'X_EndPlate_R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}


def p3(v):
    return [round(float(v.x), 5), round(float(v.y), 5), round(float(v.z), 5)]


def wire_loops(wire, tol=1e-4):
    """把一条 wire 拆成有序的边描述。"""
    out = []
    for e in wire.OrderedEdges:
        c = e.Curve
        t = type(c).__name__
        rec = {'type': t, 'len': round(e.Length, 5),
               'p0': p3(e.Vertexes[0].Point), 'p1': p3(e.Vertexes[-1].Point)}
        if t == 'Line':
            pass
        elif t == 'Circle':
            rec['center'] = p3(c.Center)
            rec['axis'] = p3(c.Axis)
            rec['r'] = round(float(c.Radius), 5)
            # 取圆弧中点，用于 arc.three_point
            mid = e.valueAt((e.FirstParameter + e.LastParameter) / 2.0)
            rec['pm'] = p3(mid)
            rec['start_ang'] = round(float(e.FirstParameter), 6)
            rec['end_ang'] = round(float(e.LastParameter), 6)
        else:
            pts = [p3(p) for p in e.discretize(Number=8)]
            rec['poly'] = pts
        out.append(rec)
    return out


def face_loops(face):
    """返回该面的外环与所有内环（各自有序边序列）。"""
    outer = wire_loops(face.OuterWire)
    inners = [wire_loops(w) for w in face.Wires if not w.isSame(face.OuterWire)]
    return outer, inners


def plane_frame(face):
    """平面面的局部坐标系（原点 + 法向），用于判断分层方向。"""
    s = face.Surface
    if type(s).__name__ != 'Plane':
        return None
    n = s.Axis
    return {'origin': p3(s.Position), 'normal': p3(n)}


def bbox(b):
    return [round(b.XMin, 4), round(b.YMin, 4), round(b.ZMin, 4),
            round(b.XMax, 4), round(b.YMax, 4), round(b.ZMax, 4)]


result = {}
for name, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    # 收集所有 ±Y 法向的平面面，按其 Y 位置分组
    yplanes = {}
    for i, f in enumerate(shape.Faces):
        fr = plane_frame(f)
        if not fr:
            continue
        nx, ny, nz = fr['normal']
        if abs(abs(ny) - 1.0) > 1e-6:
            continue
        y = round(fr['origin'][1], 3)
        outer, inners = face_loops(f)
        rec = {
            'face': i, 'y': y, 'normal_y': round(ny, 3),
            'area': round(f.Area, 4), 'bbox': bbox(f.BoundBox),
            'outer': outer, 'inners': inners,
        }
        yplanes.setdefault(y, []).append(rec)
    result[name] = {
        'bbox': bbox(shape.BoundBox),
        'volume_mm3': round(shape.Volume, 4),
        'face_count': len(shape.Faces),
        'layers': {str(k): v for k, v in sorted(yplanes.items())},
    }

with open(OUT, 'w', encoding='utf-8') as fp:
    json.dump(result, fp, ensure_ascii=False, indent=1)

print('WROTE', OUT)
for name, rec in result.items():
    print('===', name, 'V', rec['volume_mm3'], 'bbox', rec['bbox'], 'faces', rec['face_count'])
    for y, faces in rec['layers'].items():
        tot = sum(len(f['outer']) for f in faces)
        print('  Y=%-8s faces %d  outer_edges %d  area %.1f'
              % (y, len(faces), tot, sum(f['area'] for f in faces)))
