# -*- coding: utf-8 -*-
"""LM6UU / Ø6 导杆改造：几何生成 + 全量验证（FreeCAD BREP 直读，不打开 FCStd）。

用户口径：滑台两端的结构件重新设计、铝型材不变、滑车重新修改参数。
方案：保留上下两半 + M3 合拢；新建独立参数化设计；X+Z 两轴全改。

设计要点（全部为「去料」，因此真实几何的接口与冻结槽位 100% 保真）：
  1) 4 个滑车半体：主座 R5.00×15.60 -> R6.05×19.20，
     保留两端 R4.70 导入段 / R5.10 出口段形成双向轴向挡肩，LM6UU 被明显卡住。
  2) 4 个端板：导杆孔 R2.75 -> R3.05（Ø6 导杆 + 单边 0.05 装配间隙）。
  3) 4 根 Ø6 导杆、4 个 LM6UU（Ø12×Ø6×19）由 SolidCraft 参数化原生体生成。
  4) X_Profile / Z_Profile 铝型材真几何不变。

SolidCraft 的导入体布尔不稳：
  * X_EndPlate_L/R 被 STEP 导入器丢掉 49 个面、判为 open body，在开放体上
    布尔会无限挂起（实测 >165 s）；
  * Z_EndPlate_R（93 面）上做细环形扩孔布尔，实测 180 s 未返回，整段脚本
    报 `boolean Cut: the operation failed: no result`（第 41 步）。
故 4 个端板的 8 处导杆孔全部在本脚本里预先切好；SolidCraft 里只对
4 个滑车半体做 8 处实时参数化切除（这 8 步已实测成功，约 1.8 s/步）。

输出：
  solidcraft/LM6UU_base6.step          6 件（2 个 Z 端板已预切 + 4 滑车未改）
  solidcraft/LM6UU_xplates_lm6.step    2 件 X 端板（已预切 Ø6.10 导杆孔）
  refs/tmp/lm6_geometry_report.json   逐件几何 / 冻结项 / 干涉验证报告
  refs/tmp/build_lm6_geometry.log     fsync 日志（权威）
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Import
import Part

V = App.Vector
ROOT = 'C:/ink'
BRP = ROOT + '/refs/tmp/brp_lm6'
OUT = ROOT + '/solidcraft'
LOGP = ROOT + '/refs/tmp/build_lm6_geometry.log'
REPP = ROOT + '/refs/tmp/lm6_geometry_report.json'

_f = open(LOGP, 'w', encoding='utf-8')


def P(*a):
    s = ' '.join(str(x) for x in a)
    try:
        print(s)
    except Exception:
        pass
    _f.write(s + '\n')
    _f.flush()
    os.fsync(_f.fileno())


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, h, base, axis):
    d = {'X': V(1, 0, 0), 'Y': V(0, 1, 0), 'Z': V(0, 0, 1)}[axis]
    return Part.makeCylinder(r, h, V(*base), d)


# ---------------------------------------------------------------- 参数表
P_ = {
    'BRG_OD': 12.0, 'BRG_ID': 6.0, 'BRG_L': 19.0,
    'ROD_D': 6.0, 'SEAT_R': 6.05, 'SEAT_L': 19.2,
    'ROD_HOLE_R': 3.05, 'PILOT_R': 4.7, 'EXIT_R': 5.1,
    'X_SEAT_X0': 140.4, 'Z_SEAT_Z0': 127.4,
    'Z_SLOT_W': 22.0, 'X_POCKET_W': 20.8,
    'ROD_X_LEN': 215.0, 'ROD_Z_LEN': 165.0,
}

# ---------------------------------------------------------------- 冻结项（几何保护区）
FROZEN = {
    # Z 轴限位槽 22.00：X139.00..161.00
    'Z_SLOT_W_22.00': box(139.0, 161.0, -30.0, 19.0, 12.0, 65.0),
    # X 轴限位开关口袋 20.80：Z120.85..141.65
    'X_POCKET_W_20.80': box(41.50, 53.90, -79.0, -71.0, 120.85, 141.65),
}

PARTS = [
    'X_EndPlate_L', 'X_EndPlate_R', 'Z_EndPlate_L', 'Z_EndPlate_R',
    'X_Carriage_Lower', 'X_Carriage_Upper',
    'Z_Carriage_Lower', 'Z_Carriage_Upper',
]
XPLATES = ('X_EndPlate_L', 'X_EndPlate_R')
BASE6 = [p for p in PARTS if p not in XPLATES]


def load(name):
    s = Part.Shape()
    s.read(os.path.join(BRP, name + '.Shape.brp'))
    return s


# ---------------------------------------------------------------- 全部 16 处去料
def seat_cuts():
    """8 处滑车半圆座扩大：上下两半共用同一整圆刀具，分型面即得半圆。"""
    out = []
    for zc in (122.0, 152.0):
        for body in ('X_Carriage_Lower', 'X_Carriage_Upper'):
            out.append((body, cyl(P_['SEAT_R'], P_['SEAT_L'],
                                  [P_['X_SEAT_X0'], -68.0, zc], 'X'),
                        'X座 Z%.0f %s' % (zc, body[-5:])))
    for xc in (135.0, 165.0):
        for body in ('Z_Carriage_Lower', 'Z_Carriage_Upper'):
            out.append((body, cyl(P_['SEAT_R'], P_['SEAT_L'],
                                  [xc, -12.0, P_['Z_SEAT_Z0']], 'Z'),
                        'Z座 X%.0f %s' % (xc, body[-5:])))
    return out


def rod_cuts():
    """8 处端板导杆孔扩大。

    注意：X_EndPlate_L/R 的 BREP 在 cut 之后调用 removeSplitter() 会退化成
    invalid（实测 valid=False）。本脚本全程不做 removeSplitter，冻结口袋的
    保护改由后面的 FROZEN 几何差集校验把关。
    """
    out = []
    # X_EndPlate_L 的 Z=122 导杆孔与 20.80 冻结口袋仅相距 0.05 mm，
    # 直接用整圆刀具会削掉口袋壁 0.27 mm3。刀具先减去冻结保护区，
    # 使口袋几何零改动（实测 frozenLost=0，且刀具/结果 BREP 均 valid）。
    pocket = FROZEN['X_POCKET_W_20.80']
    for zc in (122.0, 152.0):
        c = cyl(P_['ROD_HOLE_R'], 7.9, [42.4, -68.0, zc], 'X')
        out.append(('X_EndPlate_L', c.cut(pocket),
                    'XL 导杆孔 Z%.0f（冻结口袋遮罩）' % zc))
        out.append(('X_EndPlate_R', cyl(P_['ROD_HOLE_R'], 7.9,
                                        [249.7, -68.0, zc], 'X'),
                    'XR 导杆孔 Z%.0f' % zc))
    for xc in (135.0, 165.0):
        out.append(('Z_EndPlate_L', cyl(P_['ROD_HOLE_R'], 7.9,
                                        [xc, -12.0, 54.4], 'Z'),
                    'ZL 导杆孔 X%.0f' % xc))
        out.append(('Z_EndPlate_R', cyl(P_['ROD_HOLE_R'], 7.9,
                                        [xc, -12.0, 211.9], 'Z'),
                    'ZR 导杆孔 X%.0f' % xc))
    return out


SEATS, RODS = seat_cuts(), rod_cuts()
ALL_CUTS = SEATS + RODS
P('参数', json.dumps(P_, ensure_ascii=False))
P('去料总数', len(ALL_CUTS), '(滑车座 %d / 端板导杆孔 %d)' % (len(SEATS), len(RODS)))

# ---------------------------------------------------------------- 应用 + 逐件验证
orig, modified = {}, {}
for n in PARTS:
    orig[n] = load(n)
    s = orig[n]
    used = [t for b, t, tag in ALL_CUTS if b == n]
    for t in used:
        s = s.cut(t)
    # 关键：X_EndPlate_L/R 切后 removeSplitter() 会把 BREP 退化成 invalid，
    # 实测 valid=False 且 bbox / 体积失真。这里保留布尔原始结果，绝不 refine。
    modified[n] = s

report = {'params': P_, 'parts': {}, 'frozen': {}, 'interference': {},
          'retention': {}, 'profiles': {}, 'conclusion': None}
fails = []

for n in PARTS:
    a, b = orig[n], modified[n]
    added = a.cut(b).Volume          # 纯去料时 = 被切掉的体积
    removed = b.cut(a).Volume       # 必须 = 0
    ba, bb = a.BoundBox, b.BoundBox
    bbox_same = all(abs(x - y) < 1e-6 for x, y in zip(
        (ba.XMin, ba.YMin, ba.ZMin, ba.XMax, ba.YMax, ba.ZMax),
        (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)))
    rec = dict(volume_before=round(a.Volume, 4), volume_after=round(b.Volume, 4),
               delta=round(b.Volume - a.Volume, 4),
               material_added=round(removed, 6), material_removed=round(added, 4),
               closed=bool(b.isClosed()), valid=bool(b.isValid()),
               solids=len(b.Solids), faces=len(b.Faces), bbox_unchanged=bbox_same)
    report['parts'][n] = rec
    P('PART %-20s V %10.3f -> %10.3f  Δ=%9.3f  added=%.6f closed=%s valid=%s bbox_same=%s'
      % (n, a.Volume, b.Volume, b.Volume - a.Volume, removed,
         b.isClosed(), b.isValid(), bbox_same))
    if removed > 1e-4 or not b.isClosed() or not b.isValid() or not bbox_same:
        fails.append('PART ' + n)

# ---------------------------------------------------------------- 冻结项：保护区内零改动
for key, bx in FROZEN.items():
    rows = {}
    for n in PARTS:
        a, b = orig[n], modified[n]
        lost = a.cut(b).common(bx).Volume
        gain = b.cut(a).common(bx).Volume
        if lost + gain > 0:
            rows[n] = dict(lost=round(lost, 8), gained=round(gain, 8))
    ok = not rows
    report['frozen'][key] = dict(unchanged=ok, changes=rows)
    P('FROZEN %-20s %s  %s' % (key, 'OK' if ok else 'FAIL', rows))
    if not ok:
        fails.append('FROZEN ' + key)

# ---------------------------------------------------------------- 新外购件 / 铝型材
def bearing(base, axis):
    o = cyl(P_['BRG_OD'] / 2, P_['BRG_L'], base, axis)
    i = cyl(P_['BRG_ID'] / 2, P_['BRG_L'], base, axis)
    return o.cut(i)


BEARINGS = []
for zc in (122.0, 152.0):
    BEARINGS.append(('X_LM6UU_Z%.0f' % zc, bearing([140.5, -68.0, zc], 'X'), 'X'))
for xc in (135.0, 165.0):
    BEARINGS.append(('Z_LM6UU_X%.0f' % xc, bearing([xc, -12.0, 127.5], 'Z'), 'Z'))

GUIDERODS = []
for zc in (122.0, 152.0):
    GUIDERODS.append(('X_GuideRod_Z%.0f' % zc,
                      cyl(P_['ROD_D'] / 2, P_['ROD_X_LEN'], [42.5, -68.0, zc], 'X')))
for xc in (135.0, 165.0):
    GUIDERODS.append(('Z_GuideRod_X%.0f' % xc,
                      cyl(P_['ROD_D'] / 2, P_['ROD_Z_LEN'], [xc, -12.0, 54.5], 'Z')))

PROFILES = {n: load(n) for n in ('X_Profile', 'Z_Profile')}

# ---------------------------------------------------------------- 干涉：新件 vs 全部改后件
def overlap(a, b):
    try:
        c = a.common(b)
        return 0.0 if c.isNull() else c.Volume
    except Exception as e:
        P('  overlap err', repr(e))
        return -1.0


worst = 0.0
for bn, bs, ax in BEARINGS:
    for pn in PARTS:
        v = overlap(bs, modified[pn])
        worst = max(worst, v)
        if v > 1e-3:
            report['interference']['%s vs %s' % (bn, pn)] = round(v, 5)
            fails.append('INTERFERE bearing %s/%s' % (bn, pn))
for rn, rs in GUIDERODS:
    for pn in PARTS:
        v = overlap(rs, modified[pn])
        if v > 1e-3:
            report['interference']['%s vs %s' % (rn, pn)] = round(v, 5)
            fails.append('INTERFERE rod %s/%s' % (rn, pn))
    for pn, ps in PROFILES.items():
        v = overlap(rs, ps)
        if v > 1e-3:
            report['interference']['%s vs %s' % (rn, pn)] = round(v, 5)
            fails.append('INTERFERE rod %s/%s' % (rn, pn))
for bn, bs, ax in BEARINGS:
    for pn, ps in PROFILES.items():
        v = overlap(bs, ps)
        if v > 1e-3:
            report['interference']['%s vs %s' % (bn, pn)] = round(v, 5)
            fails.append('INTERFERE bearing %s/%s' % (bn, pn))
report['interference']['_max_bearing_vs_part'] = round(worst, 6)
P('INTERFERENCE pairs_over_1e-3 =', len([k for k in report['interference'] if not k.startswith('_')]))

# ---------------------------------------------------------------- 轴向挡肩：LM6UU 必须被明显卡住
# 把轴承沿轴向平移 ±2 mm，若与滑车有实体重叠 => 两端存在挡肩，轴承无法轴向脱出
for bn, bs, ax in BEARINGS:
    d = {'X': V(2, 0, 0), 'Z': V(0, 0, 2)}[ax]
    plus, minus = bs.copy(), bs.copy()
    plus.translate(d)
    minus.translate(-d)
    hit_p = sum(overlap(plus, modified[p]) for p in PARTS)
    hit_m = sum(overlap(minus, modified[p]) for p in PARTS)
    ok = hit_p > 1.0 and hit_m > 1.0
    report['retention'][bn] = dict(shift_plus_overlap=round(hit_p, 3),
                                   shift_minus_overlap=round(hit_m, 3),
                                   shoulders_present=ok)
    P('RETENTION %-16s +2mm=%.3f -2mm=%.3f -> %s' %
      (bn, hit_p, hit_m, 'OK' if ok else 'FAIL'))
    if not ok:
        fails.append('RETENTION ' + bn)

# ---------------------------------------------------------------- 铝型材不变
for n, s in PROFILES.items():
    b = s.BoundBox
    report['profiles'][n] = dict(volume=round(s.Volume, 3),
                                 bbox=[round(v, 2) for v in
                                       (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)],
                                 unchanged=True)
    P('PROFILE %-12s V=%.3f bbox=%s' % (n, s.Volume, report['profiles'][n]['bbox']))

# ---------------------------------------------------------------- 导出两个 STEP
def export(names, path, prebored):
    """prebored: 需要导出「已切除」版本的零件名集合；其余导出原始真几何。

    端板全部预切，滑车半体保留原始几何给 SolidCraft 实时参数化切除。
    """
    d = App.newDocument('LM6Export')
    objs = []
    for n in names:
        s = modified[n] if n in prebored else orig[n]
        solids = [x for x in s.Solids if x.isClosed() and x.isValid()]
        if not solids:
            solids = list(s.Solids)
        clean = solids[0] if len(solids) == 1 else Part.makeCompound(solids)
        o = d.addObject('Part::Feature', n)
        o.Label = n
        o.Shape = clean
        objs.append(o)
        P('  EXPORT %-20s solids=%d closed=%s V=%.3f' %
          (n, len(clean.Solids), clean.isClosed(), clean.Volume))
    d.recompute()
    Import.export(objs, path)
    P('WROTE', path, os.path.getsize(path), 'bytes')
    App.closeDocument(d.Name)


P('--- export base6 (Z 端板已预切 Ø6.10 导杆孔 + 4 滑车未改) ---')
export(BASE6, OUT + '/LM6UU_base6.step',
       {'Z_EndPlate_L', 'Z_EndPlate_R'})
P('--- export xplates (X 端板已预切 Ø6.10 导杆孔) ---')
export(list(XPLATES), OUT + '/LM6UU_xplates_lm6.step', set(XPLATES))

report['conclusion'] = 'PASS' if not fails else 'FAIL'
report['failures'] = fails
P('CONCLUSION', report['conclusion'], 'failures=', len(fails))
for f in fails:
    P('  FAIL', f)
(ROOT + '/refs/tmp/lm6_geometry_report.json').replace('/', os.sep)
with open(REPP, 'w', encoding='utf-8') as fh:
    json.dump(report, fh, ensure_ascii=False, indent=1)
P('WROTE', REPP)
P('LM6 GEOMETRY BUILD DONE')
_f.close()
