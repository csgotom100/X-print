# -*- coding: utf-8 -*-
"""导出 LM6UU 改造设计中「保持不变」的铝型材真几何，作为 SolidCraft 参照组件。

只导出 X_Profile / Z_Profile 两件；不打开 FCStd 文档（本机 freecadcmd 会卡死），
从 refs/tmp/brp_lm6/ 的裸 BREP 直读。
"""
import os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Part
import Import

ROOT = 'C:/ink'
BRP = ROOT + '/refs/tmp/brp_lm6'
OUT = ROOT + '/solidcraft/LM6UU_reference_profiles.step'
LOGP = ROOT + '/refs/tmp/export_lm6_reference_step.log'

_f = open(LOGP, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    try:
        print(s)
    except Exception:
        pass
    _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

def main():
    d = App.newDocument('LM6Reference')
    objs = []
    for n in ('X_Profile', 'Z_Profile'):
        s = Part.Shape()
        s.read(os.path.join(BRP, n + '.Shape.brp'))
        o = d.addObject('Part::Feature', n)
        o.Label = n
        o.Shape = s
        objs.append(o)
        b = s.BoundBox
        P('LOAD', n, 'V=%.3f' % s.Volume, 'solids', len(s.Solids),
          'bbox [%.2f %.2f %.2f %.2f %.2f %.2f]' %
          (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax))
    d.recompute()
    Import.export(objs, OUT)
    P('WROTE', OUT, os.path.getsize(OUT), 'bytes')
    P('LM6 REFERENCE STEP DONE')

main()
_f.close()
