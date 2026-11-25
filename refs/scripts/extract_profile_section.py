# -*- coding: utf-8 -*-
"""从 FCStd 裸 BREP 提取 2040 铝型材的真实横截面，供 SolidCraft 原生重建。

不调用 App.openDocument（本机 2026-11-09 后一律卡死），直接 Part.Shape().read()。
输出：
  refs/tmp/profile_sections.json   每根型材的截面实体/空腔点阵 + 轮廓顶点
  refs/tmp/profile_section.log     运行日志（fsync，避免 timeout 强杀丢输出）
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import Part
from FreeCAD import Vector

ROOT = 'C:/ink'
BRP = ROOT + '/refs/tmp/brp_lm6/'
OUT = ROOT + '/refs/tmp/profile_sections.json'
LOG = ROOT + '/refs/tmp/profile_section.log'

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


def read_brep(name):
    p = BRP + name + '.Shape.brp'
    s = Part.Shape()
    s.read(p)
    return s


# 型材：X_Profile 沿 X，截面在 YZ；Z_Profile 沿 Z，截面在 XY
# 在每个轴向中点取一片 0.2 mm 薄板与实体求交，再在截面平面内做 2D 点阵，
# 用薄板实体的 isInside 判定「该点是材料还是空腔」。
PROFILES = [
    # name, axis, cross-section plane axes (u,v), bbox from interfaces
    ('X_Profile', 'X', 'Y', 'Z', [50.0, -57.0, 117.0, 250.0, -37.0, 157.0]),
    ('Z_Profile', 'Z', 'X', 'Y', [130.0, -1.0, 62.0, 170.0, 19.0, 212.0]),
]

result = {'source': BRP, 'profiles': {}}
for name, axis, uax, vax, bb in PROFILES:
    log('===', name, 'axis', axis, 'section in', uax + vax, 'bbox', bb)
    s = read_brep(name)
    idx = {'X': 0, 'Y': 1, 'Z': 2}
    ai, ui, vi = idx[axis], idx[uax], idx[vax]
    amid = (bb[ai] + bb[ai + 3]) / 2.0
    umin, umax = bb[ui], bb[ui + 3]
    vmin, vmax = bb[vi], bb[vi + 3]
    log('  section at', axis, '=', amid, '|', uax, umin, '..', umax, '|', vax, vmin, '..', vmax)

    # 薄板（沿轴向 0.2 mm）
    lo = [0.0, 0.0, 0.0]
    hi = [0.0, 0.0, 0.0]
    lo[ai], hi[ai] = amid - 0.1, amid + 0.1
    lo[ui], hi[ui] = umin - 1.0, umax + 1.0
    lo[vi], hi[vi] = vmin - 1.0, vmax + 1.0
    slab = Part.makeBox(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2],
                        Vector(lo[0], lo[1], lo[2]))
    try:
        cut = s.common(slab)
        vol = cut.Volume
        solids = len(cut.Solids)
    except Exception as e:
        log('  common FAILED', repr(e))
        cut, vol, solids = None, 0.0, 0
    log('  slab common volume', round(vol, 4), 'solids', solids,
        '=> area approx', round(vol / 0.2, 2), 'mm2')

    # 2D 点阵（1 mm 网格）判定材料/空腔
    N = 44
    grid = []
    for j in range(N):
        v = vmax - (j + 0.5) * (vmax - vmin) / N   # 从上到下
        row = ''
        for i in range(N):
            u = umin + (i + 0.5) * (umax - umin) / N
            p = [0.0, 0.0, 0.0]
            p[ai], p[ui], p[vi] = amid, u, v
            try:
                solid_here = cut is not None and cut.isInside(Vector(*p), 1e-5, True)
            except Exception:
                solid_here = False
            row += '#' if solid_here else '.'
        grid.append(row)
    log('  section ASCII (# material / . void), 1mm-ish grid:')
    for r in grid:
        log('   ', r)

    # 截面外轮廓：把薄板实体在截面平面投影后的所有顶点收集起来
    pts = set()
    if cut is not None:
        for vx in cut.Vertexes:
            q = vx.Point
            pts.add((round(getattr(q, uax.lower()), 3), round(getattr(q, vax.lower()), 3)))
    contour = sorted(pts)
    log('  distinct section vertices:', len(contour))
    log('  first 40:', contour[:40])

    result['profiles'][name] = {
        'axis': axis, 'section_axes': [uax, vax],
        'bbox': bb, 'section_at': amid,
        'u_range': [umin, umax], 'v_range': [vmin, vmax],
        'slab_volume': vol, 'section_area_approx': vol / 0.2,
        'ascii': grid, 'vertices': [list(x) for x in contour],
        'closed': s.isClosed(), 'valid': s.isValid(),
        'faces': len(s.Faces), 'volume': s.Volume,
    }

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
log('WROTE', OUT)
log('DONE')
_lf.close()
