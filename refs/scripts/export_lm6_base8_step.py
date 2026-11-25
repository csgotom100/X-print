# -*- coding: utf-8 -*-
"""导出 LM6UU 改造所需的 8 件「真实几何」基座 STEP（闭合实体、带零件名）。

用户口径：滑台两端的结构件要重新设计、铝型材不变、滑车重新修改参数。
本脚本只导出将被重设计的 8 件（4 端板 + 4 滑车半体）的真几何基座，
供 SolidCraft 用 file.insert_step 插入后，再叠加参数化布尔特征：
  - 滑车半圆座 R5.00×15.60 -> R6.05×19.20
  - 端板导杆孔 R2.75 -> R3.05
全部修改为「去料」，因此原几何的其余接口 / 冻结槽位 100% 保真。

不打开 FCStd 文档（本机 freecadcmd 的 App.openDocument 会卡死），
从 refs/tmp/brp_lm6/ 的裸 BREP 直读；沿用 export_named_step_clean.py
的「只保留闭合 Solid + removeSplitter」净化口径。
"""
from __future__ import annotations

import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Import
import Part

ROOT = 'C:/ink'
BRP = ROOT + '/refs/tmp/brp_lm6'
OUT = ROOT + '/solidcraft/LM6UU_base8.step'
LOGP = ROOT + '/refs/tmp/export_lm6_base8_step.log'

TARGETS = [
    'X_EndPlate_L', 'X_EndPlate_R', 'Z_EndPlate_L', 'Z_EndPlate_R',
    'X_Carriage_Lower', 'X_Carriage_Upper',
    'Z_Carriage_Lower', 'Z_Carriage_Upper',
]

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


def main():
    doc = App.newDocument('LM6Base8')
    objs = []
    for n in TARGETS:
        s = Part.Shape()
        s.read(os.path.join(BRP, n + '.Shape.brp'))
        solids = list(s.Solids)
        good = [x for x in solids if x.isClosed() and x.isValid()]
        if not good:
            good = solids
        clean = good[0] if len(good) == 1 else Part.makeCompound(good)
        try:
            clean = clean.removeSplitter()
        except Exception as e:
            P('  removeSplitter skipped', n, repr(e))
        o = doc.addObject('Part::Feature', n)
        o.Label = n
        o.Shape = clean
        objs.append(o)
        b = clean.BoundBox
        P('LOAD %-20s V=%12.3f solids=%d faces=%d closed=%s bbox=[%.2f %.2f %.2f %.2f %.2f %.2f]' %
          (n, clean.Volume, len(clean.Solids), len(clean.Faces),
           clean.isClosed(), b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax))
    doc.recompute()
    Import.export(objs, OUT)
    P('WROTE', OUT, os.path.getsize(OUT), 'bytes')
    P('LM6 BASE8 STEP DONE')


main()
_f.close()
