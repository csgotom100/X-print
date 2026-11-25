# -*- coding: utf-8 -*-
"""把端板每层截面写成 SolidCraft 可读的二维 DXF。

关键点：
  - SolidCraft 的 DXF 读取只认 10/20 两个二维坐标（不读 30/31 的 Z）；
  - XZ 平面草图坐标：u = 世界 X，v = -世界 Z；
  - DXF ARC 恒为 XY 平面内逆时针（CCW），角度需按 (u, v) 重新计算。
"""
from __future__ import annotations

import json
import math
import os

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
OUT_DIR = ROOT + '/refs/tmp/dxf'
os.makedirs(OUT_DIR, exist_ok=True)
BREPS = {
    'L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}


def uv(p):
    """世界 (x, z) -> 草图 (u, v) = (x, -z)。"""
    return (float(p.x), -float(p.z))


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


def norm2pi(a):
    while a < 0:
        a += 2 * math.pi
    while a >= 2 * math.pi:
        a -= 2 * math.pi
    return a


def dedupe_loops(ws, tol=0.02):
    """去掉 slice 在薄壁处重复返回的同一环（面积与包围盒都相同）。"""
    kept = []
    for w in ws:
        try:
            f = Part.Face(w)
        except Exception:
            continue
        a, b = f.Area, f.BoundBox
        dup = False
        for a2, b2, _w2 in kept:
            if (abs(a - a2) < tol
                    and abs(b.XMin - b2.XMin) < tol and abs(b.XMax - b2.XMax) < tol
                    and abs(b.YMin - b2.YMin) < tol and abs(b.YMax - b2.YMax) < tol):
                dup = True
                break
        if not dup:
            kept.append((a, b, w))
    return [k[2] for k in kept]


def pick_loops(ws):
    """把截面环分成 (外环, 该外环的孔) 配对。

    规则：先去重；按面积降序；一个环若真正落在某个已认定外环的面内，则成为该外环的孔，
    否则它自身是新外环（被中间梁分隔出的独立实体段）。
    返回 [{'outer': wire, 'holes': [wire,...]}, ...]
    """
    if not ws:
        return []
    infos = []
    for w in dedupe_loops(ws):
        try:
            f = Part.Face(w)
            infos.append({'w': w, 'f': f, 'a': f.Area, 'bb': f.BoundBox,
                          'c': f.CenterOfMass})
        except Exception:
            continue
    infos.sort(key=lambda d: -d['a'])
    groups = []
    for d in infos:
        placed = False
        for g in groups:
            o = g['bb']
            b = d['bb']
            # 先做包围盒粗筛，再做点包含精确判定
            if not (b.XMin >= o.XMin - 1e-6 and b.XMax <= o.XMax + 1e-6
                    and b.YMin >= o.YMin - 1e-6 and b.YMax <= o.YMax + 1e-6):
                continue
            try:
                if g['f'].isInside(d['c'], 1e-6, True):
                    g['holes'].append(d['w'])
                    placed = True
                    break
            except Exception:
                continue
        if not placed:
            groups.append({'outer': d['w'], 'f': d['f'], 'bb': d['bb'],
                           'holes': []})
    return groups


def slab_faces(shape, y, thick=0.004):
    """薄片法取截面：返回 -Y 侧平面面列表（slice 在窄条处会退化）。"""
    piece = shape.common(Part.makeBox(600, thick, 600, Vector(-150, y, -100)))
    if piece.Volume < 1e-9:
        return [], 0.0
    faces = []
    for f in piece.Faces:
        if type(f.Surface).__name__ != 'Plane':
            continue
        if abs(f.normalAt(0, 0).y + 1.0) > 1e-6:
            continue
        faces.append(f)
    return faces, piece.Volume / thick


def wire_entities(w):
    ents = []
    for e in w.OrderedEdges:
        c = e.Curve
        t = type(c).__name__
        if t == 'Line':
            u0, v0 = uv(e.Vertexes[0].Point)
            u1, v1 = uv(e.Vertexes[-1].Point)
            if abs(u1 - u0) < 1e-9 and abs(v1 - v0) < 1e-9:
                continue
            ents.append(('LINE', (u0, v0, u1, v1)))
        elif t == 'Circle':
            cu, cv = uv(c.Center)
            r = float(c.Radius)
            p0 = e.Vertexes[0].Point
            p1 = e.Vertexes[-1].Point
            u0, v0 = uv(p0)
            u1, v1 = uv(p1)
            # 整圆（起止点重合且扫角接近 2π）直接写 CIRCLE
            span = abs(e.LastParameter - e.FirstParameter)
            if (abs(u0 - u1) < 1e-6 and abs(v0 - v1) < 1e-6) or span > 2 * math.pi - 1e-3:
                ents.append(('CIRCLE', (cu, cv, r)))
                continue
            pm = e.valueAt((e.FirstParameter + e.LastParameter) / 2.0)
            um, vm = uv(pm)
            a0 = math.atan2(v0 - cv, u0 - cu)
            a1 = math.atan2(v1 - cv, u1 - cu)
            am = math.atan2(vm - cv, um - cu)
            if norm2pi(am - a0) <= norm2pi(a1 - a0):
                start, end = a0, a1
            else:
                start, end = a1, a0
            ents.append(('ARC', (cu, cv, r, math.degrees(norm2pi(start)),
                                 math.degrees(norm2pi(end)))))
        else:
            pts = e.discretize(Number=24)
            uvs = [uv(p) for p in pts]
            for (u0, v0), (u1, v1) in zip(uvs[:-1], uvs[1:]):
                ents.append(('LINE', (u0, v0, u1, v1)))
    return ents


def write_dxf(path, ents):
    L = ['0', 'SECTION', '2', 'ENTITIES']
    for kind, v in ents:
        if kind == 'LINE':
            x1, y1, x2, y2 = v
            L += ['0', 'LINE', '8', '0',
                  '10', '%.6f' % x1, '20', '%.6f' % y1, '30', '0.0',
                  '11', '%.6f' % x2, '21', '%.6f' % y2, '31', '0.0']
        elif kind == 'CIRCLE':
            cu, cv, r = v
            L += ['0', 'CIRCLE', '8', '0',
                  '10', '%.6f' % cu, '20', '%.6f' % cv, '30', '0.0',
                  '40', '%.6f' % r]
        else:
            cu, cv, r, a0, a1 = v
            L += ['0', 'ARC', '8', '0',
                  '10', '%.6f' % cu, '20', '%.6f' % cv, '30', '0.0',
                  '40', '%.6f' % r,
                  '50', '%.6f' % a0, '51', '%.6f' % a1]
    L += ['0', 'ENDSEC', '0', 'EOF']
    open(path, 'w', encoding='ascii').write('\n'.join(L) + '\n')


def layer_area(shape, y, thick=0.02):
    return shape.common(Part.makeBox(600, thick, 600,
                                     Vector(-150, y, -100))).Volume / thick


def slab_faces(shape, y, thick=0.004):
    """薄片法取截面：返回 -Y 侧平面面列表（slice 在窄条处会退化）。"""
    piece = shape.common(Part.makeBox(600, thick, 600, Vector(-150, y, -100)))
    if piece.Volume < 1e-9:
        return [], 0.0
    faces = []
    for f in piece.Faces:
        if type(f.Surface).__name__ != 'Plane':
            continue
        if abs(f.normalAt(0, 0).y + 1.0) > 1e-6:
            continue
        faces.append(f)
    return faces, piece.Volume / thick


def merge_bands(shape, ys, sim=0.03, max_t=8.0):
    """自适应分层：把截面面积相近（<sim）的相邻层合并，避免共面并集失败。

    只在轮廓真正变化处切层；每段在几何中点取样，保证体积误差为二阶小量。
    """
    raw = []
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        t = y1 - y0
        if t < 1e-3:
            continue
        a = layer_area(shape, (y0 + y1) / 2, min(0.02, t * 0.4))
        raw.append({'y0': y0, 'y1': y1, 't': t, 'a': a})

    bands = []
    cur = dict(raw[0])
    for nxt in raw[1:]:
        ref = max(cur['a'], 1e-6)
        close = abs(nxt['a'] - cur['a']) / ref <= sim
        fits = (cur['t'] + nxt['t']) <= max_t
        if close and fits:
            cur['y1'] = nxt['y1']
            cur['t'] = cur['y1'] - cur['y0']
            cur['a'] = layer_area(shape, (cur['y0'] + cur['y1']) / 2,
                                  min(0.02, cur['t'] * 0.4))
        else:
            bands.append(cur)
            cur = dict(nxt)
    bands.append(cur)
    return bands


manifest = {}
for tag, path in BREPS.items():
    shape = Part.Shape()
    shape.read(path)
    ys = y_planes(shape)
    bands = merge_bands(shape, ys)
    rows = []
    for i, b in enumerate(bands):
        y0, y1, t = b['y0'], b['y1'], b['t']
        ym = (y0 + y1) / 2
        # 优先用薄片 -Y 面：slice 在薄壁/窄条/带圆弧外缘处会漏环或只给部分环
        ws = []
        area = None
        for frac in (0.5, 0.25, 0.75, 0.1, 0.9, 0.4, 0.6):
            ytest = y0 + t * frac
            faces, area_t = slab_faces(shape, ytest)
            if faces:
                # 每个薄片面：外环 + 该面的内环（孔）一起收集
                ws = []
                for fc in faces:
                    ws.append(fc.OuterWire)
                    for w2 in fc.Wires:
                        if not w2.isSame(fc.OuterWire):
                            ws.append(w2)
                area = area_t
                ym = ytest
                break
        if not ws:
            # 薄片也失败时才退回 slice
            for frac in (0.5, 0.25, 0.75, 0.1, 0.9):
                ws = shape.slice(Vector(0, 1, 0), y0 + t * frac)
                if ws:
                    ym = y0 + t * frac
                    break
        ents = []
        for w in ws:
            ents.extend(wire_entities(w))
        f = os.path.join(OUT_DIR, 'EP%s_%02d.dxf' % (tag, i))
        write_dxf(f, ents)
        groups = pick_loops(ws)
        # 每个外环一个 DXF；该外环的孔单独一个 DXF（拉伸后 cut 到对应外环体）
        f_outs, f_holes = [], []
        for k, g in enumerate(groups):
            fk = os.path.join(OUT_DIR, 'EP%s_%02d_o%d.dxf' % (tag, i, k))
            write_dxf(fk, wire_entities(g['outer']))
            f_outs.append(fk)
            if g['holes']:
                hk = os.path.join(OUT_DIR, 'EP%s_%02d_o%d_h.dxf' % (tag, i, k))
                write_dxf(hk, [e for w in g['holes'] for e in wire_entities(w)])
                f_holes.append(hk)
            else:
                f_holes.append(None)
        holes_total = sum(len(g['holes']) for g in groups)
        outers = groups
        holes = [h for g in groups for h in g['holes']]
        f_hole = None
        f_out = f_outs[0]
        f = os.path.join(OUT_DIR, 'EP%s_%02d.dxf' % (tag, i))
        write_dxf(f, [e for w in ws for e in wire_entities(w)])
        if area is None:
            area = layer_area(shape, ym, min(0.02, t * 0.2))
        rows.append({'index': i, 'y0': round(y0, 4), 'y1': round(y1, 4),
                     't': round(t, 4), 'area': round(area, 3),
                     'wires': len(ws), 'outers': len(groups),
                     'holes': holes_total, 'entities': len(ents),
                     'dxf': f, 'dxf_out': f_out, 'dxf_outs': f_outs,
                     'dxf_holes': f_holes, 'dxf_hole': f_hole})
    manifest[tag] = rows

json.dump(manifest, open(ROOT + '/refs/tmp/ep_dxf_manifest.json', 'w',
                         encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE manifest')
for tag, rows in manifest.items():
    print(tag, 'bands', len(rows), 'entities', sum(r['entities'] for r in rows))
    for r in rows:
        print('   EP%s_%02d %7.2f..%7.2f t %5.2f A %7.2f wires %d ents %3d'
              % (tag, r['index'], r['y0'], r['y1'], r['t'], r['area'],
                 r['wires'], r['entities']))
