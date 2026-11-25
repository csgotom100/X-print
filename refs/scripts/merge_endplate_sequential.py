# -*- coding: utf-8 -*-
"""顺序逐个合并分层体，失败即跳过并记录，最后输出可用的合并结果。

一次性 combine 30+ body 会触发内核退化（coincident faces / curved fallback）。
逐个合并让每一步只有一对实体参与，成功率显著提高。
"""
from __future__ import annotations

import json
import subprocess

ROOT = 'C:/ink'
SRC = ROOT + '/refs/tmp/EP_bands_stage1.sc'
GUI = 'D:/mydocuments/SolidCraft'
CLI = 'solidcraft-cli'

man = json.load(open(ROOT + '/refs/tmp/ep_dxf_manifest.json', encoding='utf-8'))


def bodies_of(tag):
    names = []
    for r in man[tag]:
        for k in range(len(r['dxf_outs'])):
            names.append('B%s%02d_%d' % (tag, r['index'], k))
    return names


def run(cmds, in_sc, out_sc):
    jp = ROOT + '/refs/tmp/_merge_step.json'
    json.dump({'commands': cmds}, open(jp, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    r = subprocess.run([CLI, 'run', jp, '--in', in_sc,
                        '--results', ROOT + '/refs/tmp/_merge_step_res.json',
                        '--json-out', ROOT + '/refs/tmp/_merge_step_cli.json'],
                       capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


for tag in ('L', 'R'):
    names = bodies_of(tag)
    target = 'X_EndPlate_' + tag
    cur = SRC
    merged = [names[0]]
    skipped = []
    # 第一轮：把第一个体改名成目标名（用 combine 自合并实现改名不便，直接用原文件）
    for n in names[1:]:
        cmds = [{'command': 'solid.combine',
                 'params': {'target': merged[0], 'tools': [n],
                            'operation': 'join', 'keep_tools': False}},
                {'command': 'file.save',
                 'params': {'path': ROOT + '/refs/tmp/_merge_acc_%s.sc' % tag,
                            'format': 'container', 'overwrite': True}}]
        ok, err = run(cmds, cur, None)
        if ok:
            cur = ROOT + '/refs/tmp/_merge_acc_%s.sc' % tag
        else:
            skipped.append((n, err[:80]))
    print(tag, 'merged', len(names) - len(skipped), 'of', len(names),
          'skipped', len(skipped))
    for n, e in skipped[:6]:
        print('   skip', n, e)
