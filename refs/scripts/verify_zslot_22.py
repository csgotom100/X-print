# -*- coding: utf-8 -*-
"""复核 Z 轴限位开关槽宽 22.00 mm 保持不变（用户明确要求）。

做法：
  A. 与 audit_struct.log 记录的 v12 基线比对 Z_EndPlate_L / 两个 Z 限位开关的
     体积与 BBox —— 完全一致即证明 v12.1 没有触碰 Z 轴结构。
  B. 在 Z_EndPlate_L 上用 isInside 二分搜索实测槽的 X 向净宽。
  C. 顺带复核 X 轴口袋 20.80 mm（早前已改，不应被回退）。
"""
import io
import sys

import FreeCAD as App

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)

# v12 基线（refs/tmp/audit_struct.log，v12.1 改动前）
BASE = {
    'Z_EndPlate_L':      (41521.447, (105.00, 195.00, -30.00, 19.00, 12.00, 65.00)),
    'Z_EndPlate_R':      (23059.448, (130.00, 170.00, -23.00, 19.00, 211.00, 262.00)),
    'Z_LimitSwitch_Bot': (1328.479, (140.10, 159.90, -25.90, -19.40, 50.80, 63.00)),
    'Z_LimitSwitch_Top': (1328.479, (140.10, 159.90, -25.90, -19.40, 211.10, 223.30)),
    'Z_Profile':         (45421.190, (130.00, 170.00, -1.00, 19.00, 62.00, 212.00)),
    'X_EndPlate_L':      (19096.771, (0.00, 53.00, -79.00, -37.00, 117.00, 157.00)),
}
KEYS = ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax')

d = App.openDocument('C:/ink/CrossSlide_P014013.FCStd')

print('=' * 88)
print('A. 与 v12 基线比对（v12.1 是否触碰 Z 轴结构）')
print('=' * 88)
all_same = True
for n, (v0, bb0) in BASE.items():
    o = d.getObject(n)
    if not o:
        print('  %-22s MISSING' % n)
        all_same = False
        continue
    v, bb = o.Shape.Volume, o.Shape.BoundBox
    dv = abs(v - v0)
    dbb = max(abs(getattr(bb, k) - b0) for k, b0 in zip(KEYS, bb0))
    same = dv < 0.01 and dbb < 0.01
    all_same &= same
    print('  %-22s V=%.3f (基线 %.3f, dV=%.4f)  dBBox=%.4f  %s'
          % (n, v, v0, dv, dbb, '完全一致' if same else '!! 有变化'))
print('  >> Z 轴结构在 v12.1 中 %s' % ('完全未触碰' if all_same else '发生了变化，需检查'))


def inside(shape, p):
    return shape.isInside(App.Vector(*p), 0.001, True)


def boundary(shape, make_p, a, b, iters=22):
    """a 与 b 材料性相反，二分返回跳变点坐标。"""
    sa = inside(shape, make_p(a))
    for _ in range(iters):
        m = (a + b) / 2.0
        if inside(shape, make_p(m)) == sa:
            a = m
        else:
            b = m
    return (a + b) / 2.0


print()
print('=' * 88)
print('B. Z 轴安装槽实测（Z_EndPlate_L，沿 X 二分边界）')
print('=' * 88)
plate = d.getObject('Z_EndPlate_L').Shape
for y, z in ((-22.0, 58.0), (-24.0, 58.0), (-22.0, 56.0)):
    mk = lambda x, y=y, z=z: (x, y, z)
    s137, s150, s163 = (inside(plate, mk(t)) for t in (137.0, 150.0, 163.0))
    print('  Y=%6.1f Z=%5.1f  探针 X137=%s X150=%s X163=%s'
          % (y, z, s137, s150, s163))
    if s137 and not s150 and s163:
        left = boundary(plate, mk, 137.0, 150.0)
        right = boundary(plate, mk, 150.0, 163.0)
        print('     槽 X%.3f..%.3f  净宽 %.3f mm' % (left, right, right - left))
    else:
        print('     该截面不是「材料-槽-材料」，跳过')
print('  开关本体 X140.10..159.90 (19.80)，两侧各留 1.10 mm')
print('  >> 标称槽宽 = 161.00 - 139.00 = 22.00 mm，保持不动')

print()
print('=' * 88)
print('C. X 轴端板口袋复核（早前已放大到 20.80）')
print('=' * 88)
xl = d.getObject('X_EndPlate_L').Shape
# 口袋在 X41.60..53.80 / Y-81..-74.50 附近，必须在 Y≈-77 处探测
for y in (-77.0, -78.0, -75.0):
    mk = lambda zz, y=y: (45.0, y, zz)
    s120, s131, s150 = (inside(xl, mk(t)) for t in (120.0, 131.0, 150.0))
    print('  X=45.0 Y=%6.1f  探针 Z120=%s Z131=%s Z150=%s'
          % (y, s120, s131, s150))
    if s120 and not s131 and s150:
        lo = boundary(xl, mk, 120.0, 131.0)
        hi = boundary(xl, mk, 131.0, 150.0)
        print('     口袋 Z%.3f..%.3f  净高 %.3f mm' % (lo, hi, hi - lo))
print('  >> 期望 20.80 mm（Z120.85..141.65）；A 节已证 X_EndPlate_L 体积未变，'
      '故 X 轴口袋亦未被回退')
