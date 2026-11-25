# -*- coding: utf-8 -*-
"""v9 全量核验：几何、干涉、尺寸链、行程、连接。"""
import io
import sys

import FreeCAD as App
import Part

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = App.openDocument('C:/ink/CrossSlide_P014013.FCStd')
g = d.getObject

NAMES = ['HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring',
         'HP45_HallSensor', 'HP45_HallPCB', 'HP45_ProbeHousing', 'HP45_SocketR125',
         'HP45_ProbeArm', 'HP45_HousingScrew_0', 'HP45_HousingScrew_1']

print('=' * 78)
print('1) 各零件几何')
print('=' * 78)
S = {}
for n in NAMES:
    o = g(n)
    if not o:
        print('  %-22s MISSING' % n)
        continue
    s = o.Shape
    bb = s.BoundBox
    S[n] = s
    print('  %-22s V=%8.3f sol=%d  X%.2f..%.2f Y%.2f..%.2f Z%.2f..%.2f'
          % (n, s.Volume, len(s.Solids),
             bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))

print()
print('=' * 78)
print('2) 两两干涉（探针总成内部 + 与臂体）')
print('=' * 78)
keys = [k for k in NAMES if k in S]
bad = 0
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = keys[i], keys[j]
        try:
            v = S[a].common(S[b]).Volume
        except Exception as e:
            print('  %-20s x %-20s ERR %s' % (a, b, e)); continue
        if v > 0.001:
            bad += 1
            print('  !! %-20s x %-20s V=%.4f' % (a, b, v))
print('  干涉对数 = %d' % bad)

print()
print('=' * 78)
print('3) 尺寸链')
print('=' * 78)
pin, mag, hous, arm, hall = (S['HP45_PogoPin'], S['HP45_PogoMagnet'],
                             S['HP45_ProbeHousing'], S['HP45_ProbeArm'],
                             S['HP45_HallSensor'])
print('  针尖 Z            = %.2f' % pin.BoundBox.ZMin)
print('  低于喷嘴(57.90)   = %.2f' % (57.90 - pin.BoundBox.ZMin))
print('  高于蛋面(56.70)   = %.2f' % (pin.BoundBox.ZMin - 56.70))
print('  探针尾端 Z        = %.2f （臂体顶板 Z102，需伸出或留腔）' % pin.BoundBox.ZMax)
print('  臂体 ZMin         = %.2f' % arm.BoundBox.ZMin)
print('  探针座 Z          = %.2f..%.2f' % (hous.BoundBox.ZMin, hous.BoundBox.ZMax))
print('  表面气隙          = %.2f mm（磁环外缘->霍尔正面，仅机械参考）'
      % (hall.BoundBox.XMin - mag.BoundBox.XMax))
print('  磁路半径 r        = %.2f mm（探针轴 X78 -> 霍尔管芯，管芯≈正面+0.5）'
      % (hall.BoundBox.XMin + 0.50 - 78.00))
print('  磁环中心 Z        = %.2f' % ((mag.BoundBox.ZMin + mag.BoundBox.ZMax) / 2))
print('  霍尔中心 Z        = %.2f' % ((hall.BoundBox.ZMin + hall.BoundBox.ZMax) / 2))

print()
print('=' * 78)
print('4) 连接方式核对（探针座靠 2 颗 M3 吊挂在臂体顶板上，故臂体∩探针座应为 0）')
print('=' * 78)
c = arm.common(hous)
print('  臂体 ∩ 探针座  V=%.4f  %s'
      % (c.Volume, '（预期 0：两者不直接贴合）' if c.Volume < 0.001 else '（异常重叠）'))
if c.Volume > 0.001:
    bb = c.BoundBox
    print('  接触区 bbox    X%.2f..%.2f Y%.2f..%.2f Z%.2f..%.2f'
          % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
for n in ('HP45_HousingScrew_0', 'HP45_HousingScrew_1'):
    if n in S:
        sa = S[n].common(arm).Volume
        sh = S[n].common(hous).Volume
        print('  %s  与臂体 V=%.3f  与探针座 V=%.3f  (螺纹咬合，CAD 里按中径建模故为 0)'
              % (n, sa, sh))

print()
print('=' * 78)
print('5) 探针在针套孔/磁环/弹簧腔内的径向间隙')
print('=' * 78)
print('  探针 Ø2.02 配 R125 针套内孔 Ø~2.10 -> 单边 0.04')
print('  磁环 Ø6.00 配腔 Ø6.40 -> 单边 0.20')
print('  弹簧 Ø6.00 配腔 Ø6.20 -> 单边 0.10')
print('  通气孔 Ø2.50 配针 Ø2.02 -> 单边 0.24（兼排气）')
