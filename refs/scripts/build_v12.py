# -*- coding: utf-8 -*-
"""v12：磁路工作点修正（结构不动，只挪霍尔 + PCB）

[v11 遗留问题]
  p125_calc.py 把「磁环表面->霍尔感测面 2.0 mm 气隙」当成了偶极子公式的
  径向距离 r，导致算出 ±5651 G「严重饱和」的错误结论。
  正确 r 应为「探针轴 X78 -> 霍尔管芯」的距离 = 5.0~6.0 mm。

[体元积分结果 magcalc_v12.py]（磁环内孔 Ø2.10 / 厚 2.00，霍尔中心 Z79.00）
  r=5.0 mm : 峰值 431 G，A1324 输出 0.34..4.66 V，超 ±400G 且贴轨 -> 弃用
  r=5.5 mm : 峰值 288 G，输出 1.06..3.94 V，单调
  r=6.0 mm : 峰值 199 G，输出 1.51..3.50 V，单调，余量最大

[v12 修正]
  1) 霍尔平面朝 -X，管芯约在正面后方 0.5 mm。
     把霍尔正面从 X83.00 移到 X83.40 -> 管芯 r = 83.40+0.50-78.00 = 5.90 mm
     PCB 随之移到 X84.90..85.50（仍在霍尔窗 X81.0..85.5 内）
  2) 霍尔中心 Z 从 79.50 移到 79.00，使磁环中心在 3 mm 行程里
     从 z_rel=+1.5 扫到 -1.5，零点落在行程中点，输出对称。
     霍尔体 Z 76.90..81.09，PCB Z 76.80..81.20（仍在窗 Z76.5..82.0 内）
  3) 霍尔窗保留 X81.0..85.5，可用 0.2~0.5 mm 垫片微调 r 做实物标定。

[v12 设计点] r=5.9 / Z79.00 / A1324 5 mV/G
  峰值 213.8 G -> 输出 1.431..3.569 V，全程单调，不饱和
  零点斜率 182 G/mm -> 0.911 V/mm；12bit ADC 约 0.0013 mm/LSB
"""
import io
import shutil
import sys

import FreeCAD as App
import Part

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_v12.FCStd'
shutil.copyfile(DOC, BAK)
print('[backup]', BAK)

AY = -112.5
HX = 83.40                 # 霍尔正面（感测面），朝 -X
PCB_X = HX + 1.50          # 84.90
HALL_Z0 = 76.90            # 中心 79.00（体高 4.19）
PCB_Z0 = 76.80             # 中心 79.00（板高 4.40）

d = App.openDocument(DOC)
g = d.getObject

hall = g('HP45_HallSensor')
pcb = g('HP45_HallPCB')

# ---- 霍尔 A1324：TO-92 1.50 x 3.05 x 4.19 ----
hs = Part.makeBox(1.50, 3.05, 4.19,
                  App.Vector(HX, AY - 1.525, HALL_Z0))
hall.Shape = hs
hall.Label = 'A1324 线性霍尔 感测面X83.40 管芯r5.9 中心Z79.00'
d.recompute()
print('[hall] V=%.3f  X%.2f..%.2f  Z%.2f..%.2f  valid=%s'
      % (hall.Shape.Volume, hall.Shape.BoundBox.XMin, hall.Shape.BoundBox.XMax,
         hall.Shape.BoundBox.ZMin, hall.Shape.BoundBox.ZMax, hall.Shape.isValid()))

# ---- 霍尔 PCB 0.60 x 2.60 x 4.40 ----
ps = Part.makeBox(0.60, 2.60, 4.40,
                  App.Vector(PCB_X, AY - 1.30, PCB_Z0))
pcb.Shape = ps
pcb.Label = '霍尔转接 PCB 0.6x2.6x4.4（可加垫片调 r）'
d.recompute()
print('[pcb ] V=%.3f  X%.2f..%.2f  Z%.2f..%.2f  valid=%s'
      % (pcb.Shape.Volume, pcb.Shape.BoundBox.XMin, pcb.Shape.BoundBox.XMax,
         pcb.Shape.BoundBox.ZMin, pcb.Shape.BoundBox.ZMax, pcb.Shape.isValid()))

d.recompute()
print('objects', len(d.Objects))
d.save()
print('SAVED')
