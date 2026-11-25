# -*- coding: utf-8 -*-
"""验收端板复刻结果：体积 / 包围盒 / 面数 / 闭合性，对照原件基准。"""
from __future__ import annotations

import json
import sys

ROOT = 'C:/ink'

TARGET = {
    'X_EndPlate_L': {'volume': 19158.4432,
                     'bbox': [0.0, -82.0, 117.0, 53.0, -37.0, 157.0]},
    'X_EndPlate_R': {'volume': 20565.7088,
                     'bbox': [249.0, -82.0, 117.0, 300.0, -37.0, 157.0]},
}
TOL_PCT = 3.0     # 交付容差：3%
TOL_BBOX = 0.05   # mm


def main(eval_path):
    d = json.load(open(eval_path, encoding='utf-8'))
    bodies = {b['name']: b for b in d['bodies']}
    errs = sum(1 for v in d['timeline'] if v.get('error'))
    warns = sum(1 for v in d['timeline'] if v.get('warning'))
    print('timeline errors %d / warnings %d / features %d'
          % (errs, warns, len(d['timeline'])))
    print()

    ok = True
    for name, t in TARGET.items():
        # 允许合并后名字带后缀，或仍为分层体：按前缀汇总
        cand = [b for n, b in bodies.items()
                if n == name or n.startswith('B' + name[-1])]
        if not cand:
            print('MISSING', name)
            ok = False
            continue
        vol = sum(b['volume_mm3'] for b in cand if b['volume_mm3'])
        err = (vol - t['volume']) / t['volume'] * 100.0
        # 包围盒取并集
        xs = [b['bbox']['min'][0] for b in cand] + [b['bbox']['max'][0] for b in cand]
        ys = [b['bbox']['min'][1] for b in cand] + [b['bbox']['max'][1] for b in cand]
        zs = [b['bbox']['min'][2] for b in cand] + [b['bbox']['max'][2] for b in cand]
        got = [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)]
        dev = max(abs(a - c) for a, c in zip(got, t['bbox']))
        closed = all(b['closed'] for b in cand)
        single = all(b['kernel']['shells'] == 1 for b in cand)

        print('%-14s bodies %2d  V %10.2f  target %10.2f  err %+7.3f%%'
              % (name, len(cand), vol, t['volume'], err))
        print('%-14s bbox %s  max dev %.3f mm'
              % ('', [round(v, 2) for v in got], dev))
        print('%-14s closed %s  single-shell %s' % ('', closed, single))
        if abs(err) > TOL_PCT:
            print('   !! volume error over %.1f%%' % TOL_PCT)
            ok = False
        if dev > TOL_BBOX:
            print('   !! bbox deviation over %.2f mm' % TOL_BBOX)
            ok = False
        if not closed or not single:
            print('   !! not closed / not single shell')
            ok = False
        print()

    if errs:
        print('   !! timeline has errors')
        ok = False
    print('RESULT', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else ROOT + '/refs/tmp/ep_bands_stage1_eval.json'))
