# -*- coding: utf-8 -*-
"""用分层轮廓自身的面积核对：sum(area*t) 是否等于原始 BREP 体积。

轮廓来自 refs/tmp/x_endplate_bands.json（FreeCAD 切片结果）。
面积用 shoelace（圆弧按 32 段离散）计算，外环为正、内环为负。
"""
from __future__ import annotations

import json
import math

ROOT = 'C:/ink'
BANDS = ROOT + '/refs/tmp/x_endplate_bands.json'
OUT = ROOT + '/refs/tmp/x_endplate_band_area_check.json'


def arc_points(c, r, p0, pm, p1, n=48):
    """按 p0->pm->p1 的走向离散圆弧（X-Z 平面）。"""
    def ang(p):
        return math.atan2(p[1] - c[1], p[0] - c[0])

    a0, am, a1 = ang(p0), ang(pm), ang(p1)

    def norm(x):
        while x < 0:
            x += 2 * math.pi
        while x >= 2 * math.pi:
            x -= 2 * math.pi
        return x

    fwd = norm(a1 - a0)
    mid_fwd = norm(am - a0)
    if mid_fwd > fwd:          # 中点不在正向弧上 → 走负向
        fwd = fwd - 2 * math.pi
    pts = []
    for i in range(n + 1):
        a = a0 + fwd * i / n
        pts.append([c[0] + r * math.cos(a), c[1] + r * math.sin(a)])
    return pts


def loop_points(loop):
    pts = []
    for c in loop:
        if c['t'] == 'Line':
            if not pts:
                pts.append(c['p0'])
            pts.append(c['p1'])
        elif c['t'] == 'Circle':
            seg = arc_points(c['c'], c['r'], c['p0'], c['pm'], c['p1'])
            if not pts:
                pts.append(seg[0])
            pts.extend(seg[1:])
        else:
            poly = c['poly']
            if not pts:
                pts.append(poly[0])
            pts.extend(poly[1:])
    # 去掉相邻重复点
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-6 and abs(out[0][1] - out[-1][1]) < 1e-6:
        out.pop()
    return out


def shoelace(pts):
    s = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def area_of_band(band):
    total = 0.0
    detail = []
    for idx, loop in enumerate(band['loops']):
        pts = loop_points(loop)
        if len(pts) < 3:
            continue
        a = shoelace(pts)
        # 第一个环按外环（正），其余按内环（负）；用符号归一
        if idx == 0:
            total += abs(a)
            detail.append(('outer', round(abs(a), 3), len(pts)))
        else:
            total -= abs(a)
            detail.append(('inner', round(abs(a), 3), len(pts)))
    return total, detail


data = json.load(open(BANDS, encoding='utf-8'))
report = {}
for name, rec in data.items():
    rows = []
    vsum = 0.0
    for b in rec['bands']:
        area, detail = area_of_band(b)
        v = area * b['t']
        vsum += v
        rows.append({'y0': b['y0'], 'y1': b['y1'], 't': b['t'],
                     'area': round(area, 3), 'vol': round(v, 3),
                     'loops': b['n_loops'], 'curves': b['n_curves'],
                     'detail': detail})
    actual = rec['volume_mm3']
    report[name] = {
        'actual_volume': actual,
        'layered_volume': round(vsum, 3),
        'error_pct': round((vsum - actual) / actual * 100.0, 3),
        'bands': rows,
    }

json.dump(report, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('WROTE', OUT)
for name, rec in report.items():
    print('===', name)
    print('  actual %.2f   layered %.2f   error %+.3f%%'
          % (rec['actual_volume'], rec['layered_volume'], rec['error_pct']))
    for r in rec['bands']:
        print('  %7.2f..%7.2f t=%5.2f  A %8.2f  V %9.2f  loops %d'
              % (r['y0'], r['y1'], r['t'], r['area'], r['vol'], r['loops']))
