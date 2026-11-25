# -*- coding: utf-8 -*-
"""总装收口：只挖实测干涉对应的必要让位，逐条试切，失败自动跳过。

实测干涉（总装 40 号）：
  42 电机 ↔ 左端板  BL08_0 863.15 + BL09_0 1600.81 mm³
  惰轮轴 ↔ 右端板  BR09_0 175.92 + BR10_0 71.47 mm³
  限位开关 ↔ 端板耳  BL00_0 30.78 / BL01_0 74.32 / BR00_0 30.78 / BR01_0 74.32 mm³
  导杆 ↔ 端板  BL04_3 3.01 / BL04_5 0.08 / BR05_3 0.08 mm³（擦边，可忽略）
"""
from __future__ import annotations

import json
import subprocess

ROOT = 'C:/ink'
SRC = ROOT + '/solidcraft/40_x_axis_assembly.json'
OUT = ROOT + '/solidcraft/42_x_axis_assembly_clearance.json'
CLI = 'solidcraft-cli'

cmds = json.load(open(SRC, encoding='utf-8'))['commands']
tail_save = [c for c in cmds if c['command'] == 'file.save']
body = [c for c in cmds if c['command'] not in ('file.save', 'appearance.assign')]
appear = [c for c in cmds if c['command'] == 'appearance.assign']

tasks = []


def add(kind, params, target, tag):
    p = dict(params)
    p['operation'] = 'cut'
    p['targets'] = [target]
    p['name'] = 'CLR_%s_%s' % (tag, target)
    tasks.append({'command': kind, 'params': p})


# 1) 端板电机固定孔：原件实测 4×r1.7（Ø3.4 M3 通孔）
#    位置 X5.5/36.5、Z121.5/152.5（孔距 31），Y-62.0..-57.0 → 跨 BL08 尾与 BL09
for b in ('BL08_0', 'BL09_0'):
    for sx in ('-1', '1'):
        for sz in ('-1', '1'):
            add('solid.cylinder', {
                'radius': 'MOTOR_HOLE_R - 0.75 mm', 'height': '7 mm',
                'base': ['PULLEY_CX_L + %s * MOTOR_HOLE_PITCH / 2' % sx,
                         '-61.5 mm',
                         'PULLEY_CZ + %s * MOTOR_HOLE_PITCH / 2' % sz],
                'axis': 'Y'}, b, 'MotorHole%s%s' % (sx, sz))

# 2) 惰轮轴孔（右端板）
for b in ('BR09_0', 'BR10_0'):
    add('solid.cylinder', {
        'radius': 'IDLER_SHAFT_R + 0.2 mm', 'height': '20 mm',
        'base': ['PULLEY_CX_R', '-62 mm', 'PULLEY_CZ'], 'axis': 'Y'}, b, 'IdlerBore')

# 3) 限位开关口袋（开关耳）
for tag, b in (('L', 'BL00_0'), ('L', 'BL01_0'),
               ('R', 'BR00_0'), ('R', 'BR01_0')):
    x0 = 'SW_L_X0' if tag == 'L' else 'SW_R_X0'
    add('solid.box', {
        'length': 'SW_W + 0.6 mm', 'width': 'MP_Y0 - FL_Y0',
        'height': 'X_POCKET_W + 0.6 mm',
        'corner': ['%s - 0.3 mm' % x0, 'FL_Y0',
                   'X_POCKET_ZC - X_POCKET_W / 2 - 0.3 mm']}, b, 'SwitchPocket')

# 逐条试切：失败跳过
kept, skipped = [], []
cur = ROOT + '/refs/tmp/EP_bands_stage1.sc'
acc = ROOT + '/refs/tmp/_clr_acc.sc'
for t in tasks:
    trial = body + kept + [t, {'command': 'file.save', 'params': {
        'path': acc, 'format': 'container', 'overwrite': True}}]
    jp = ROOT + '/refs/tmp/_clr_try.json'
    json.dump({'commands': trial}, open(jp, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    r = subprocess.run([CLI, 'run', jp, '--in', cur,
                        '--results', ROOT + '/refs/tmp/_clr_try_res.json',
                        '--json-out', ROOT + '/refs/tmp/_clr_try_cli.json'],
                       capture_output=True, text=True)
    if r.returncode == 0:
        kept.append(t)
    else:
        skipped.append((t['params']['name'], r.stderr.strip()[:70]))

print('kept %d / %d  skipped %d' % (len(kept), len(tasks), len(skipped)))
for n, e in skipped:
    print('  skip', n, '|', e)

out = body + kept + appear + tail_save
json.dump({'commands': out}, open(OUT, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('WROTE', OUT, 'commands', len(out))
