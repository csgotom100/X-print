# -*- coding: utf-8 -*-
"""v13.2：磁环运动通道改 8x8 正公差空间 + 弹簧导向段分离。

用户口径（2026-11-10 确认）
--------------------------------------------------------------------
  1. 磁环直径 6 mm，运动空间要留正公差 -> 8 x 8；
     范围选「全行程 Z76.50..81.50」（磁环 0..+3.0 mm 会走出零位 2 mm 腔）。
  2. 弹簧直径不该是 8，应防偏斜 -> 保持 Ø6 / k=0.045 N/mm / F0=0.045 N 采购规格不变，
     Z81.50..87.50 保留 6.20 窄腔作紧导向。

几何改动（仅 2 件）
--------------------------------------------------------------------
  HP45_ProbeHousing
    磁环通道型芯  T_chan = box(70.30, 82.00, -116.50, -108.50, 76.50, 81.50)
      -> 沿 -X 敞开等截面直棱柱；扣盖板后闭合腔 X74.00..82.00 / Y-116.50..-108.50
         = 真 8.00 x 8.00，以针轴 (78.00, -112.50) 为中心。
      -> +X 止于 82.00，距霍尔传感器 X83.40 尚有 1.40，座体外壁 X85.50 余 3.50。
    弹簧导向型芯  T_guid = box(70.30, 81.10, -115.60, -109.40, 81.50, 87.50)
      -> 保持 v13 的 6.20 净宽，仅把下边界由 Z78.50 抬到 Z81.50。
    顶棚 Z87.50..90.00 / 中心 Ø2.50 / 霍尔窗 / Ø2.37 针套孔 / 2xM3 全部不动。

  HP45_SpringSpacer（-X 侧盖板）
    主板        box(68.60, 70.50, -119.00, -106.00, 76.50, 87.50)   不变
    通道凸台    box(70.50, 74.00, -116.50, -108.50, 76.50, 81.50)   补形到 X74.00
    导向凸台    box(70.50, 75.00, -114.90, -109.40, 81.50, 87.50)   -Y 仍退 0.80 躲 M3

  结果：Z78.50 的 4 个碎错台（0.80 / 0.10 / 0.10 / 0.90）收敛成 Z81.50
  一处近似对称的环形台阶（每边约 0.90 mm），并把 8x8 净空覆盖磁环全行程。

冻结项（全部不动）
--------------------------------------------------------------------
  磁环腔高 2.00 (Z76.50 下台阶) / 霍尔感测面 X83.40 / 中心 Z79.00 / r=5.90
  Z 轴限位槽 22.00 / X 轴口袋 20.80 / 弹簧 F0=0.045 N、满程 0.180 N
  行程 0..+3.0 mm / v14 材质方案

实现通道
--------------------------------------------------------------------
  绕开 App.openDocument（本机 1.1 会卡死）：从当前 FCStd ZIP 逐件提取的
  refs/tmp/brep_v14_baseline/*.Shape.brp 用 Part.Shape().read() 直读，
  布尔后 exportBrep 到 refs/tmp/v13_2out/，由 writeback_v13_2.py 经 GUI
  App.ActiveDocument 赋值 Shape + d.save() 回写（FreeCAD 自行重建 Map/GUI）。

运行：freecadcmd refs/scripts/build_v13_2.py   （只产 BREP，不改主文档）
回滚：refs/CrossSlide_before_v13_2.FCStd
"""
import os
import sys
import shutil
import FreeCAD as App
import Part

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

V = App.Vector
B = 'C:/ink/refs/tmp/brep_v14_baseline/'
OUT = 'C:/ink/refs/tmp/v13_2out/'
LOGP = 'C:/ink/refs/tmp/build_v13_2.log'
os.makedirs(OUT, exist_ok=True)
_fh = open(LOGP, 'w', encoding='utf-8')


def P(*a):
    s = ' '.join(str(x) for x in a)
    _fh.write(s + '\n'); _fh.flush(); os.fsync(_fh.fileno())
    try:
        print(s)
    except Exception:
        pass


def load(n):
    s = Part.Shape(); s.read(B + n + '.Shape.brp'); return s


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def export(shape, name):
    p = OUT + name + '.Shape.brp'
    try:
        shape.exportBrep(p)
    except Exception:
        Part.export([shape], p)
    t = Part.Shape(); t.read(p)
    assert t.isValid() and abs(t.Volume - shape.Volume) < 1e-4, 'BREP 回读不一致: ' + name
    P('  [export] %-24s V=%10.3f sol=%d valid=%s'
      % (name, shape.Volume, len(shape.Solids), shape.isValid()))
    return shape


P('=' * 96)
P('v13.2 构造：8x8 磁环全行程通道 + 6.20 弹簧导向段')
P('=' * 96)

h0 = load('HP45_ProbeHousing')
a0 = load('HP45_ProbeArm')
c0 = load('HP45_SpringSpacer')
P('基线（当前 FCStd）: 座体 V=%.3f  臂体 V=%.3f  盖板 V=%.3f'
  % (h0.Volume, a0.Volume, c0.Volume))

# ---------------------------------------------------------------- 1) 座体
P('')
P('--- 1) 座体：8x8 通道 Z76.50..81.50 + 6.20 导向段 Z81.50..87.50 ---')
T_chan = box(70.30, 82.00, -116.50, -108.50, 76.50, 81.50)
T_guid = box(70.30, 81.10, -115.60, -109.40, 81.50, 87.50)
h1 = h0.cut(T_chan).cut(T_guid).removeSplitter()
P('  T_chan 体积 %.3f / T_guid 体积 %.3f' % (T_chan.Volume, T_guid.Volume))
P('  cut 后 V=%.3f (旧 %.3f, 再挖 %.3f) sol=%d valid=%s'
  % (h1.Volume, h0.Volume, h0.Volume - h1.Volume, len(h1.Solids), h1.isValid()))
assert h1.isValid() and len(h1.Solids) == 1, '座体应为单一有效实体'

# 顶棚下表面 Z87.50 / 中心孔仍然存在的自检
z_stop = h1.BoundBox.ZMax
P('  座体 Z 上界 %.2f（应 90.00，顶棚未动）' % z_stop)
assert abs(z_stop - 90.00) < 1e-6

# ---------------------------------------------------------------- 2) 盖板
P('')
P('--- 2) -X 侧盖板：通道凸台补形到 X74.00，导向凸台 Z81.50 起 ---')
c_main = box(68.60, 70.50, -119.00, -106.00, 76.50, 87.50)
c_chan = box(70.50, 74.00, -116.50, -108.50, 76.50, 81.50)
c_guid = box(70.50, 75.00, -114.90, -109.40, 81.50, 87.50)
c1 = c_main.fuse(c_chan).fuse(c_guid).removeSplitter()
P('  盖板 V=%.3f (旧 %.3f) sol=%d valid=%s'
  % (c1.Volume, c0.Volume, len(c1.Solids), c1.isValid()))
assert c1.isValid() and len(c1.Solids) == 1, '盖板应为单一有效实体'

# ---------------------------------------------------------------- 3) 输出
P('')
P('--- 3) 输出 BREP ---')
export(h1, 'HP45_ProbeHousing')
export(c1, 'HP45_SpringSpacer')
shutil.copyfile(B + 'HP45_ProbeArm.Shape.brp', OUT + 'HP45_ProbeArm.Shape.brp')
P('  [copy]   HP45_ProbeArm.Shape.brp  (臂体未改，原字节复制 V=%.3f)' % a0.Volume)

# ---------------------------------------------------------------- 4) 落地自检
P('')
P('--- 4) 两件新几何的静态干涉自检（对当前 FCStd 全部 139 件）---')
S = {}
for fn in os.listdir(B):
    if fn.endswith('.Shape.brp'):
        n = fn[:-len('.Shape.brp')]
        s = Part.Shape(); s.read(B + fn); S[n] = s
S['HP45_ProbeHousing'] = h1
S['HP45_SpringSpacer'] = c1


def cv(x, y):
    try:
        c = x.common(y)
        return 0.0 if c.isNull() else c.Volume
    except Exception:
        return -1.0


bad = []
for n in sorted(S):
    if n in ('HP45_ProbeHousing', 'HP45_SpringSpacer'):
        continue
    vh = cv(h1, S[n]); vc = cv(c1, S[n])
    if vh > 0.001 or vc > 0.001:
        bad.append((n, round(vh, 4), round(vc, 4)))
P('  静态干涉项 = %d' % len(bad))
for t in bad:
    P('    !! %s  座体 %.4f / 盖板 %.4f' % t)
assert not bad, '新几何与周边件干涉'
P('  座体 x 盖板 = %.4f mm3 (应 0)' % cv(h1, c1))
assert cv(h1, c1) < 0.001

P('')
P('=' * 96)
P('v13.2 BREP 构造完成：座体 %.3f / 盖板 %.3f / 臂体 %.3f'
  % (h1.Volume, c1.Volume, a0.Volume))
P('>>> 下一步：verify_v13_2.py 全量验证，再由 writeback_v13_2.py 经 GUI 回写')
P('=' * 96)
_fh.close()
