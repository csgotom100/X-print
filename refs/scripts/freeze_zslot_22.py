# -*- coding: utf-8 -*-
"""把「Z 轴限位槽 22.00 保持」写成 FreeCAD 模型内的设计冻结标注。

【已弃用 2026-11-09】本机 freecadcmd 的 App.openDocument 会卡死，本脚本跑出
EXIT=124 且未写入任何属性。正式脚本改用 freeze_zslot_22_xml.py
（XML 精确编辑 + GUI reload_document 验证），本文件仅作诊断记录，不要运行。

只加 App::PropertyString 元数据（DesignFreeze），**不修改任何几何**。
写入后重新打开文档自验：体积/BBox 与 v12 基线一致、槽宽实测仍为 22.00、属性已持久化。

用户原话：「既然Z轴已经是22了，那就不用修改」「z轴保持22.00」「Z 轴保持 22.00」。
"""
import io
import os
import shutil
import sys

import FreeCAD as App

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_zfreeze.FCStd'

NOTE = ('设计冻结（用户 2026-11-09 明确要求）：Z 轴限位开关安装槽净宽 '
        '22.00 mm，位于 Z_EndPlate_L 的 X139.00..161.00；开关本体 19.80，'
        '两侧各留 1.10 mm。禁止修改本端板、槽宽及两个 Z 限位开关安装位。'
        'X 轴端板口袋 20.80 mm 亦为已定稿尺寸，勿回退。')
TARGETS = ['Z_EndPlate_L', 'Z_LimitSwitch_Bot', 'Z_LimitSwitch_Top']

# v12 基线（refs/tmp/audit_struct.log）
BASE = {
    'Z_EndPlate_L':      (41521.447, (105.00, 195.00, -30.00, 19.00, 12.00, 65.00)),
    'Z_LimitSwitch_Bot': (1328.479, (140.10, 159.90, -25.90, -19.40, 50.80, 63.00)),
    'Z_LimitSwitch_Top': (1328.479, (140.10, 159.90, -25.90, -19.40, 211.10, 223.30)),
}
KEYS = ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax')

if not os.path.exists(BAK):
    shutil.copyfile(DOC, BAK)
    print('[backup] %s' % BAK)

print('=' * 88)
print('写入设计冻结标注（仅元数据，几何不动）')
print('=' * 88)
d = App.openDocument(DOC)
for n in TARGETS:
    o = d.getObject(n)
    if 'DesignFreeze' not in o.PropertiesList:
        o.addProperty('App::PropertyString', 'DesignFreeze', 'Design',
                      'Design freeze note (user decision)')
    o.DesignFreeze = NOTE
    print('  %-22s -> DesignFreeze 已写入' % n)
d.recompute()
d.save()
App.closeDocument(d.Name)
print('  [saved] %s' % DOC)


def inside(shape, p):
    return shape.isInside(App.Vector(*p), 0.001, True)


def boundary(shape, make_p, a, b, iters=22):
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
print('重新打开文档自验')
print('=' * 88)
d = App.openDocument(DOC)
all_same = True
for n, (v0, bb0) in BASE.items():
    o = d.getObject(n)
    v, bb = o.Shape.Volume, o.Shape.BoundBox
    dv = abs(v - v0)
    dbb = max(abs(getattr(bb, k) - b0) for k, b0 in zip(KEYS, bb0))
    same = dv < 0.01 and dbb < 0.01
    all_same &= same
    has = 'DesignFreeze' in o.PropertiesList
    print('  %-22s V=%.3f (基线 %.3f)  dBBox=%.4f  几何=%s  冻结标注=%s'
          % (n, v, v0, dbb, '未变' if same else '!!变化', '有' if has else '!!缺失'))
    all_same &= has

plate = d.getObject('Z_EndPlate_L').Shape
mk = lambda x: (x, -22.0, 58.0)
if inside(plate, mk(137.0)) and not inside(plate, mk(150.0)) and inside(plate, mk(163.0)):
    left = boundary(plate, mk, 137.0, 150.0)
    right = boundary(plate, mk, 150.0, 163.0)
    width = right - left
    print()
    print('  Z 轴槽实测 X%.3f..%.3f  净宽 %.3f mm（目标 22.00）'
          % (left, right, width))
    all_same &= abs(width - 22.00) < 0.01
else:
    print('  !! 槽截面探针异常')
    all_same = False

print()
print('  >> %s' % ('全部通过：Z 轴 22.00 已冻结且几何未变'
                   if all_same else '存在异常，需检查'))
