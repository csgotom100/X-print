# -*- coding: utf-8 -*-
"""验证端板逐面复刻结果：体积 / 包围盒 / 面数 / 闭合性 vs 原始 BREP。"""
from __future__ import annotations

import json

ROOT = 'C:/ink'
EVAL = ROOT + '/refs/tmp/x_endplate_exact_eval.json'
ORIG = ROOT + '/refs/tmp/x_endplate_original_geometry.json'

TARGET = {
    'X_EndPlate_L': {'volume': 19158.4432, 'bbox': [0.0, -82.0, 117.0, 53.0, -37.0, 157.0],
                     'faces': 192},
    'X_EndPlate_R': {'volume': 20565.7088, 'bbox': [249.0, -82.0, 117.0, 300.0, -37.0, 157.0],
                     'faces': 191},
}

d = json.load(open(EVAL, encoding='utf-8'))
bodies = {b['name']: b for b in d['bodies']}

print('timeline errors', sum(1 for v in d['timeline'] if v.get('error')),
      'warnings', sum(1 for v in d['timeline'] if v.get('warning')),
      'features', len(d['timeline']))
print()
ok = True
for name, t in TARGET.items():
    b = bodies.get(name)
    if not b:
        print('MISSING', name)
        ok = False
        continue
    v = b['volume_mm3']
    err = (v - t['volume']) / t['volume'] * 100.0
    bb = b['bbox']
    got = [round(bb['min'][0], 3), round(bb['min'][1], 3), round(bb['min'][2], 3),
           round(bb['max'][0], 3), round(bb['max'][1], 3), round(bb['max'][2], 3)]
    dbb = max(abs(a - c) for a, c in zip(got, t['bbox']))
    print('%-14s V %10.2f  target %10.2f  err %+6.3f%%' % (name, v, t['volume'], err))
    print('%-14s faces %4d (orig %d)  shells %d  closed %s'
          % ('', b['faces'], t['faces'], b['kernel']['shells'], b['closed']))
    print('%-14s bbox %s  max dev %.3f mm' % ('', got, dbb))
    if abs(err) > 1.0:
        print('   !! volume error over 1%')
        ok = False
    if dbb > 0.05:
        print('   !! bbox deviation over 0.05 mm')
        ok = False
    if not b['closed'] or b['kernel']['shells'] != 1:
        print('   !! not a single closed shell')
        ok = False
    print()

print('RESULT', 'PASS' if ok else 'FAIL')
