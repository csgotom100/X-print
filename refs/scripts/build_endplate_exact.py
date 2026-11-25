# -*- coding: utf-8 -*-
"""端板逐面复刻：每层每个外环独立成体 + 孔切除，最后按端板合并。

Stage 1  每个外环一个 body（insert_dxf -> extrude），孔单独 cut
Stage 2  按 L/R 分组，用 solid.combine join 合成两个 body
"""
from __future__ import annotations

import json

ROOT = 'C:/ink'
MANIFEST = ROOT + '/refs/tmp/ep_dxf_manifest.json'
GUI_DIR = 'D:/mydocuments/SolidCraft'
OUT_S1 = ROOT + '/solidcraft/31_endplate_bands.json'
OUT_S2 = ROOT + '/solidcraft/32_endplate_merge.json'

man = json.load(open(MANIFEST, encoding='utf-8'))


def dxf_name(p):
    return GUI_DIR + '/' + p.replace('\\', '/').split('/')[-1]


# ---------------- Stage 1 ----------------
cmds = []
groups = {'L': [], 'R': []}
for tag in ('L', 'R'):
    for r in man[tag]:
        i = r['index']
        plane = {'origin': [0.0, r['y0'], 0.0], 'x_dir': [1.0, 0.0, 0.0],
                 'y_dir': [0.0, 0.0, -1.0]}
        hole_files = r.get('dxf_holes') or []
        for k, fpath in enumerate(r['dxf_outs']):
            b = 'B%s%02d_%d' % (tag, i, k)
            groups[tag].append(b)
            cmds.append({'command': 'sketch.create',
                         'params': {'plane': plane, 'name': b + '_sk'}})
            cmds.append({'command': 'sketch.insert_dxf',
                         'params': {'path': dxf_name(fpath)}})
            cmds.append({'command': 'sketch.finish', 'params': {}})
            cmds.append({'command': 'solid.extrude', 'params': {
                'distance': '%.4f mm' % r['t'], 'name': b, 'body_name': b}})
            # 该外环自己的孔
            hf = hole_files[k] if k < len(hole_files) else None
            if hf:
                cmds.append({'command': 'sketch.create',
                             'params': {'plane': plane, 'name': b + '_hk'}})
                cmds.append({'command': 'sketch.insert_dxf',
                             'params': {'path': dxf_name(hf)}})
                cmds.append({'command': 'sketch.finish', 'params': {}})
                cmds.append({'command': 'solid.extrude', 'params': {
                    'distance': '%.4f mm' % (r['t'] + 0.02),
                    'name': b + '_hole', 'operation': 'cut', 'targets': [b]}})
cmds.append({'command': 'file.save', 'params': {
    'path': ROOT + '/refs/tmp/EP_bands_stage1.sc',
    'format': 'container', 'overwrite': True}})
json.dump({'commands': cmds}, open(OUT_S1, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---------------- Stage 2 ----------------
cmds2 = []
for tag in ('L', 'R'):
    names = groups[tag]
    cmds2.append({'command': 'solid.combine', 'params': {
        'target': names[0], 'tools': names[1:], 'operation': 'join',
        'keep_tools': False}})
json.dump({'commands': cmds2}, open(OUT_S2, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('stage1 commands', len(cmds), 'bodies', sum(len(v) for v in groups.values()))
print('  L', len(groups['L']), 'R', len(groups['R']))
print('stage2 commands', len(cmds2))
for tag in ('L', 'R'):
    rows = man[tag]
    print(tag, 'layers', len(rows),
          'est V', round(sum(r['area'] * r['t'] for r in rows), 1))
