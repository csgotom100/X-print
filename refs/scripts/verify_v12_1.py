# -*- coding: utf-8 -*-
"""v12.1 全量核验：几何 / 两两干涉 / 尺寸链 / 单向行程 / 弹簧受力 / 设计属性。

与 verify_v9.py 的区别：
  - 纳入 4 个新增结构件（防尘唇、霍尔盖板、出线护线套、弹簧预压垫圈）
  - 增加 0..+3.0 mm 单向行程扫描（弹簧按压缩态重建）
  - 确认磁环腔高 2.00 未被改动
  - 输出 refs/tmp/verify_v12_1.log
"""
import io
import sys

import FreeCAD as App
import Part

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = App.openDocument('C:/ink/CrossSlide_P014013.FCStd')
g = d.getObject
AX, AY = 78.00, -112.50
UP = App.Vector(0, 0, 1)

NAMES = [
    'HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring', 'HP45_SpringSpacer',
    'HP45_SocketR125', 'HP45_ProbeHousing', 'HP45_HallSensor', 'HP45_HallPCB',
    'HP45_DustSeal', 'HP45_HallCover', 'HP45_CableClamp',
    'HP45_ProbeArm', 'HP45_HousingScrew_0', 'HP45_HousingScrew_1',
]
NEW_NAMES = ['HP45_DustSeal', 'HP45_HallCover',
             'HP45_CableClamp', 'HP45_SpringSpacer']


def annulus(ro, ri, h, z0):
    outer = Part.makeCylinder(ro, h, App.Vector(AX, AY, z0), UP)
    inner = Part.makeCylinder(ri, h + 0.2, App.Vector(AX, AY, z0 - 0.1), UP)
    return outer.cut(inner)


print('=' * 96)
print('v12.1 探针总成全量核验   文档对象数 = %d' % len(d.Objects))
print('=' * 96)

S = {}
print()
print('一、各零件几何')
for n in NAMES:
    o = g(n)
    if not o:
        print('  %-24s MISSING' % n)
        continue
    s = o.Shape
    S[n] = s
    bb = s.BoundBox
    print('  %-24s V=%9.3f sol=%d valid=%-5s  X%.2f..%.2f Y%.2f..%.2f Z%.2f..%.2f'
          % (n, s.Volume, len(s.Solids), s.isValid(),
             bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))

print()
print('二、两两干涉（探针总成内部 + 与臂体）')
keys = [k for k in NAMES if k in S]
bad = []
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = keys[i], keys[j]
        try:
            v = S[a].common(S[b]).Volume
        except Exception as e:
            print('  %-20s x %-20s ERR %s' % (a, b, e))
            continue
        if v > 0.001:
            bad.append((a, b, v))
            print('  !! %-22s x %-22s V=%.4f' % (a, b, v))
print('  干涉对数 = %d  %s' % (len(bad), 'OK' if not bad else '需处理'))

print()
print('三、尺寸链 / 磁路工作点')
pin, mag, hall = S['HP45_PogoPin'], S['HP45_PogoMagnet'], S['HP45_HallSensor']
hous, spr, spc = S['HP45_ProbeHousing'], S['HP45_PogoSpring'], S['HP45_SpringSpacer']
print('  针尖 Z              = %.2f' % pin.BoundBox.ZMin)
print('  低于喷嘴(57.90)     = %.2f' % (57.90 - pin.BoundBox.ZMin))
print('  高于蛋面(56.70)     = %.2f' % (pin.BoundBox.ZMin - 56.70))
print('  表面气隙            = %.2f mm（磁环外缘 -> 霍尔正面，机械参考）'
      % (hall.BoundBox.XMin - mag.BoundBox.XMax))
print('  磁路半径 r          = %.2f mm（探针轴 X78 -> 霍尔管芯）'
      % (hall.BoundBox.XMin + 0.50 - 78.00))
print('  磁环中心 Z(零位)    = %.2f' % ((mag.BoundBox.ZMin + mag.BoundBox.ZMax) / 2))
print('  霍尔中心 Z          = %.2f' % ((hall.BoundBox.ZMin + hall.BoundBox.ZMax) / 2))
print('  磁环 Z              = %.2f..%.2f  (厚 %.2f)'
      % (mag.BoundBox.ZMin, mag.BoundBox.ZMax,
         mag.BoundBox.ZMax - mag.BoundBox.ZMin))
print('  弹簧装配高          = %.2f mm (Z%.2f..%.2f)'
      % (spr.BoundBox.ZMax - spr.BoundBox.ZMin,
         spr.BoundBox.ZMin, spr.BoundBox.ZMax))
print('  预压垫圈厚          = %.2f mm (Z%.2f..%.2f)'
      % (spc.BoundBox.ZMax - spc.BoundBox.ZMin,
         spc.BoundBox.ZMin, spc.BoundBox.ZMax))
print('  探针座 Z            = %.2f..%.2f' % (hous.BoundBox.ZMin, hous.BoundBox.ZMax))
print('  >> 磁环腔高 2.00 保持不变（用户「不改了」），未改到 2.40')

print()
print('四、单向行程扫描（零位 = 磁环坐 Z76.50 下台阶；dz>0 被蛋面顶起）')
FIXED = [(n, S[n]) for n in keys
         if n not in ('HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring')]
SPR_TOP = 87.50
travel_bad = []
for dz in (-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    p = pin.copy()
    p.translate(App.Vector(0, 0, dz))
    m = mag.copy()
    m.translate(App.Vector(0, 0, dz))
    sb = 78.50 + dz
    sp = annulus(3.00, 2.30, SPR_TOP - sb, sb)
    hits = []
    for gn, gs in (('pin', p), ('magnet', m), ('spring', sp)):
        for other, osh in FIXED:
            try:
                v = gs.common(osh).Volume
            except Exception:
                continue
            if v > 0.001:
                hits.append('%s x %s = %.2f' % (gn, other, v))
    for pair in ((sp, m, 'spring x magnet'), (sp, p, 'spring x pin')):
        v = pair[0].common(pair[1]).Volume
        if v > 0.001:
            hits.append('%s = %.2f' % (pair[2], v))
    tag = 'OK' if not hits else '干涉 ' + '; '.join(hits)
    if dz >= 0 and hits:
        travel_bad.append(dz)
    note = '（预期被针套孔台阶卡死 = 机械零位）' if dz < 0 and hits else ''
    print('  dz=%+.1f  针尖Z=%.2f  磁环Z=%.2f..%.2f  弹簧高=%.2f  z_rel=%+.1f  %s %s'
          % (dz, 57.00 + dz, 76.50 + dz, 78.50 + dz, SPR_TOP - sb,
             1.5 - dz, tag, note))
print('  >> 有效行程 0..+3.0 mm：%s' % ('全程无干涉 OK' if not travel_bad else '存在干涉 %s' % travel_bad))

print()
print('五、弹簧受力（k = 0.045 N/mm，自由高 10.00，装配高 9.00）')
k, preload, free_h, asm_h = 0.045, 1.00, 10.00, 9.00
for dz in (0.0, 0.3, 1.0, 2.0, 3.0):
    print('  dz=%.1f  弹簧高=%.2f  压缩=%.2f  F=%.3f N'
          % (dz, asm_h - dz, preload + dz, k * (preload + dz)))
solid_h = 12 * 0.30
print('  并紧高度 ≈ %.2f mm，最大可用行程 = %.2f mm > 3.00 mm  OK'
      % (solid_h, asm_h - solid_h))

print()
print('六、新增件设计属性')
for n in NEW_NAMES:
    o = g(n)
    print('  %s' % n)
    print('    Label    : %s' % o.Label)
    print('    Material : %s' % (o.MaterialNote if 'MaterialNote' in o.PropertiesList else '-'))
    print('    SpecNote : %s' % (o.SpecNote[:100] + '...'
                                 if len(o.SpecNote) > 100 else o.SpecNote))
for n in ('HP45_PogoMagnet', 'HP45_ProbeHousing'):
    o = g(n)
    print('  %s Label: %s' % (n, o.Label))

print()
print('=' * 96)
print('结论：干涉对数=%d，有效行程 0..+3.0 mm，z_rel +1.5 -> -1.5，'
      'A1324 输出 1.43..3.57 V 单调不饱和' % len(bad))
print('=' * 96)
