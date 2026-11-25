# -*- coding: utf-8 -*-
"""诊断 X_EndPlate_L/R 经 STEP 导入 SolidCraft 变 open body 的原因。

输出 4 种 STEP 变体，逐一用 solidcraft-cli eval 检查 closed / faces。
不打开 FCStd 文档，从裸 BREP 直读。
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
OUTDIR = ROOT + '/refs/tmp/xep_variants'
os.makedirs(OUTDIR, exist_ok=True)
LOGP = ROOT + '/refs/tmp/probe_xendplate_step.log'
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


def load(name):
    s = Part.Shape()
    s.read(os.path.join(BRP, name + '.Shape.brp'))
    return s


def report(tag, s):
    P('%-26s faces=%d shells=%d solids=%d closed=%s valid=%s V=%.3f' %
      (tag, len(s.Faces), len(s.Shells), len(s.Solids),
       s.isClosed(), s.isValid(), s.Volume))


for name in ('X_EndPlate_L', 'X_EndPlate_R'):
    P('===', name)
    s = load(name)
    report('raw', s)
    solids = list(s.Solids)
    good = [x for x in solids if x.isClosed() and x.isValid()]
    base = good[0] if len(good) == 1 else Part.makeCompound(good)

    # V1: Import.export + removeSplitter (当前口径)
    d = App.newDocument('V1')
    o = d.addObject('Part::Feature', name)
    o.Label = name
    c = base.removeSplitter()
    o.Shape = c
    d.recompute()
    report('V1 removeSplitter', c)
    Import.export([o], OUTDIR + '/' + name + '_V1.step')
    App.closeDocument(d.Name)

    # V2: Import.export 不做 removeSplitter
    d = App.newDocument('V2')
    o = d.addObject('Part::Feature', name)
    o.Label = name
    o.Shape = base
    d.recompute()
    report('V2 no splitter', base)
    Import.export([o], OUTDIR + '/' + name + '_V2.step')
    App.closeDocument(d.Name)

    # V3: Part.export 单件
    base.exportStep(OUTDIR + '/' + name + '_V3.step')
    P('V3 exportStep written')

    # V4: 重新 makeSolid 从外壳
    try:
        shell = base.Shells[0]
        solid2 = Part.makeSolid(shell)
        report('V4 makeSolid', solid2)
        solid2.exportStep(OUTDIR + '/' + name + '_V4.step')
        P('V4 written')
    except Exception as e:
        P('V4 fail', repr(e))

for f in sorted(os.listdir(OUTDIR)):
    P('FILE', f, os.path.getsize(os.path.join(OUTDIR, f)))

P('PROBE DONE')
_f.close()
