# -*- coding: utf-8 -*-
"""测试右端开关安装孔的不同起刀/长度，找出不产生壳体分裂的方案。"""
import json
import subprocess
import os

ROOT = 'C:/ink'
BASE = ROOT + '/solidcraft/20_x_axis_build.json'
TMP = ROOT + '/refs/tmp'

cmds = json.load(open(BASE, encoding='utf-8'))['commands']
head = cmds[:158]  # 到 XR_SwitchPocket 之后

VARIANTS = [
    ('A_y752_len37', '-75.2 mm', '3.7 mm'),
    ('B_y752_len40', '-75.2 mm', '4.0 mm'),
    ('C_y7510_len36', '-75.10 mm', '3.6 mm'),
    ('D_y760_len30', '-76.0 mm', '3.0 mm'),
    ('E_y752_len50', '-75.2 mm', '5.0 mm'),
    ('F_y752_len70', '-75.2 mm', '7.0 mm'),
]

for tag, y0, ln in VARIANTS:
    c = list(head)
    for i, zp in enumerate(('SW_HOLE_Z1', 'SW_HOLE_Z2'), 1):
        c.append({'command': 'solid.cylinder', 'params': {
            'radius': 'SW_HOLE_R', 'height': ln, 'base': ['SW_XC_R', y0, zp],
            'axis': 'Y', 'name': 'XR_SwitchHole%d' % i,
            'operation': 'cut', 'targets': ['X_EndPlate_R']}})
    sc = '%s/hole_%s.sc' % (TMP, tag)
    c.append({'command': 'file.save', 'params': {
        'path': sc, 'format': 'container', 'overwrite': True}})
    jp = '%s/hole_%s.json' % (TMP, tag)
    json.dump({'commands': c}, open(jp, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    r = subprocess.run(['solidcraft-cli', 'run', jp, '--results',
                        '%s/hole_%s_res.json' % (TMP, tag),
                        '--json-out', '%s/hole_%s_cli.json' % (TMP, tag)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(tag, 'RUN FAIL', r.stderr.strip()[:160])
        continue
    r2 = subprocess.run(['solidcraft-cli', 'eval', sc, '--json-out',
                         '%s/hole_%s_eval.json' % (TMP, tag)],
                        capture_output=True, text=True)
    if r2.returncode != 0:
        print(tag, 'EVAL FAIL', r2.stderr.strip()[:160])
        continue
    d = json.load(open('%s/hole_%s_eval.json' % (TMP, tag), encoding='utf-8'))
    b = [x for x in d['bodies'] if x['name'] == 'X_EndPlate_R'][0]
    print(tag, 'shells', b['kernel']['shells'], 'faces', b['faces'],
          'V', round(b['volume_mm3'], 2), 'closed', b['closed'])
