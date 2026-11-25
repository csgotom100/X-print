# -*- coding: utf-8 -*-
"""导出 2040 型材横截面的有序 BREP 几何，供 SolidCraft 原生草图 1:1 复刻。

从 FCStd 裸 BREP 直读，取轴向中点 0.2 mm 薄板与实体求交，端面即截面。

2026-11-13 修正：
  旧版用 Part.sortEdges + 圆弧中点输出折线，错误地把两个 Ø5 圆孔（各
  π·2.5² = 19.635 mm²）退化成 3 点零面积缝隙，也把外轮廓 4 个 R1.5
  真实圆弧拆成折线。结果 490.57 - 149.20 = 341.37 mm²，与 BREP 端面
  302.808 mm² 不符。
  本版改用 Wire.OrderedEdges / OrderedVertexes，按真实曲线类型输出：
    outer : 286 条 Line + 4 条 R1.5 圆弧
    hole1 : 整圆 Ø5
    hole2 : 52 条 Line 的中心异型腔
    hole3 : 整圆 Ø5
  校验：491.272842 - 19.634954 - 149.195 - 19.634954 = 302.807934 mm²。

输出 refs/tmp/profile_contours.json：几何按 wire 顺序保存，供
refs/scripts/build_profile_exact.py 生成 sketch.line / sketch.arc.three_point /
sketch.circle.center 命令，不再是近似折线。
"""
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import FreeCAD as App
import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
BRP = ROOT + '/refs/tmp/brp_lm6/'
OUT = ROOT + '/refs/tmp/profile_contours.json'
LOG = ROOT + '/refs/tmp/profile_contours.log'
_lf = open(LOG, 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    try:
        print(s)
    except Exception:
        pass
    _lf.write(s + '\n')
    _lf.flush()
    os.fsync(_lf.fileno())


PROFILES = [
    ('X_Profile', 'X', 'Y', 'Z', [50.0, -57.0, 117.0, 250.0, -37.0, 157.0]),
    ('Z_Profile', 'Z', 'X', 'Y', [130.0, -1.0, 62.0, 170.0, 19.0, 212.0]),
]
TOL = 1e-5


def uv(p, uax, vax):
    return [round(float(getattr(p, uax.lower())), 6),
            round(float(getattr(p, vax.lower())), 6)]


def near(a, b):
    return (Vector(a.x, a.y, a.z) - Vector(b.x, b.y, b.z)).Length < TOL


def curve_kind(edge):
    return str(type(edge.Curve)).split('.')[-1].strip("'>")


def shoelace(points):
    """points 为按顺序经过的 2D 点，闭合边由首尾自动连接。"""
    q = list(points)
    if len(q) > 1 and math.hypot(q[0][0] - q[-1][0], q[0][1] - q[-1][1]) < TOL:
        q = q[:-1]
    return 0.5 * sum(q[i][0] * q[(i + 1) % len(q)][1] -
                     q[(i + 1) % len(q)][0] * q[i][1]
                     for i in range(len(q)))


def full_circle_wire(wire, uax, vax):
    edges = list(wire.OrderedEdges)
    if len(edges) != 1 or curve_kind(edges[0]) != 'Circle':
        return None
    e = edges[0]
    if len(list(e.Vertexes)) != 1:
        return None
    c = e.Curve.Center
    return {
        'kind': 'circle',
        'center': uv(c, uax, vax),
        'radius': round(float(e.Curve.Radius), 6),
        'area_abs': round(math.pi * float(e.Curve.Radius) ** 2, 6),
        'curve_types': ['Circle'],
    }


def chain_wire(wire, uax, vax):
    """按 wire 方向输出 line / arc 基元，保留圆弧中点，保证可闭合。"""
    verts = list(wire.OrderedVertexes)
    edges = list(wire.OrderedEdges)
    if not verts or not edges:
        raise RuntimeError('empty ordered wire')
    start = verts[0].Point
    cur = start
    prims = []
    path = [uv(start, uax, vax)]
    kinds = []

    for i, e in enumerate(edges):
        kind = curve_kind(e)
        vs = list(e.Vertexes)
        if len(vs) < 2:
            raise RuntimeError('non-circle edge with <2 vertices at %d: %s' % (i, kind))
        a, b = vs[0].Point, vs[-1].Point
        if near(a, cur):
            p0, p1 = a, b
        elif near(b, cur):
            p0, p1 = b, a
        else:
            raise RuntimeError('edge %d does not connect to current point: %s / %s / %s'
                               % (i, uv(p0 if 'p0' in locals() else a, uax, vax),
                                  uv(cur, uax, vax), kind))
        if kind == 'Line':
            prims.append({'type': 'line',
                          'start': uv(p0, uax, vax),
                          'end': uv(p1, uax, vax)})
            path.append(uv(p1, uax, vax))
        elif kind in ('Circle', 'Ellipse'):
            mid = e.valueAt((e.FirstParameter + e.LastParameter) / 2.0)
            prims.append({'type': 'arc',
                          'start': uv(p0, uax, vax),
                          'end': uv(p1, uax, vax),
                          'through': uv(mid, uax, vax),
                          'radius': round(float(e.Curve.Radius), 6)
                          if hasattr(e.Curve, 'Radius') else None})
            path.append(uv(mid, uax, vax))
            path.append(uv(p1, uax, vax))
        else:
            raise RuntimeError('unexpected curve %s at edge %d' % (kind, i))
        kinds.append(kind)
        cur = p1

    if not near(cur, start):
        raise RuntimeError('wire is not closed: %s -> %s'
                           % (uv(cur, uax, vax), uv(start, uax, vax)))
    # 折线路径只用于判定绕向；圆弧的真实面积必须由 BREP 精确给出。
    # 若用「起点-弧中点-终点」折线代替 R1.5 圆弧，4 个角合计会少
    # 0.704628 mm²（实测），因此 area_abs 不能用 shoelace(path)。
    poly_area = shoelace(path)
    exact_area = abs(float(Part.Face(wire).Area))
    return {
        'kind': 'chain',
        'primitives': prims,
        'start': uv(start, uax, vax),
        'end': uv(cur, uax, vax),
        'area_signed': round(math.copysign(exact_area, poly_area), 6),
        'area_abs': round(exact_area, 6),
        'curve_types': kinds,
    }


res = {'source': BRP, 'profiles': {}}
for name, axis, uax, vax, bb in PROFILES:
    log('===', name, 'axis', axis, 'section', uax + vax)
    s = Part.Shape()
    s.read(BRP + name + '.Shape.brp')
    idx = {'X': 0, 'Y': 1, 'Z': 2}
    ai, ui, vi = idx[axis], idx[uax], idx[vax]
    amid = (bb[ai] + bb[ai + 3]) / 2.0
    lo, hi = [0.0] * 3, [0.0] * 3
    lo[ai], hi[ai] = amid - 0.1, amid + 0.1
    lo[ui], hi[ui] = bb[ui] - 1.0, bb[ui + 3] + 1.0
    lo[vi], hi[vi] = bb[vi] - 1.0, bb[vi + 3] + 1.0
    slab = Part.makeBox(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2], Vector(*lo))
    cut = s.common(slab)
    log('  slab vol', round(cut.Volume, 6), 'faces', len(cut.Faces))

    end_faces = []
    for f in cut.Faces:
        try:
            n = f.normalAt(0, 0)
            if abs(getattr(n, axis.lower())) > 0.999:
                end_faces.append(f)
        except Exception:
            pass
    face = max(end_faces, key=lambda x: x.Area)
    log('  chosen face area', round(face.Area, 6), 'wires', len(face.Wires))

    wires_out = []
    area_sum = 0.0
    for i, w in enumerate(face.Wires):
        circ = full_circle_wire(w, uax, vax)
        rec = circ if circ is not None else chain_wire(w, uax, vax)
        rec['index'] = i
        rec['role'] = 'outer' if i == 0 else 'hole'
        wires_out.append(rec)
        if i == 0:
            area_sum += rec['area_abs']
        else:
            area_sum -= rec['area_abs']
        log('   wire', i, rec['role'], rec['kind'],
            'nprims', len(rec.get('primitives', [])),
            'area_abs', rec['area_abs'],
            'curve_types', {k: rec['curve_types'].count(k)
                            for k in sorted(set(rec['curve_types']))})

    log('  rebuilt area', round(area_sum, 6),
        'BREP area', round(face.Area, 6),
        'delta', round(area_sum - face.Area, 6))
    res['profiles'][name] = {
        'axis': axis,
        'section_axes': [uax, vax],
        'bbox': bb,
        'section_at': amid,
        'u_range': [bb[ui], bb[ui + 3]],
        'v_range': [bb[vi], bb[vi + 3]],
        'face_area': round(face.Area, 9),
        'rebuilt_area': round(area_sum, 9),
        'wires': wires_out,
    }

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
log('WROTE', OUT)
log('DONE')
_lf.close()
