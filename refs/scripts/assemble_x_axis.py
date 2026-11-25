# -*- coding: utf-8 -*-
"""装配完整 X 轴滑台：复刻端板（分层）+ 2040 型材 + Ø6 导杆 + LM6UU
+ 滑车 + GT2 同步带/轮 + 42 电机 + 限位开关。

基底 = refs/tmp/EP_bands_stage1.sc（64 个分层端板体，已验收 L +0.689% / R -2.444%）
在其上追加 20_x_axis_build.json 的参数段（1..131，含型材草图/拉伸）与端板之后的零件段（171..）。
旧的语义化端板命令（132..170）全部丢弃。
"""
from __future__ import annotations

import collections
import json

ROOT = 'C:/ink'
BASE_SC = ROOT + '/refs/tmp/EP_bands_stage1.sc'
SRC_JSON = ROOT + '/solidcraft/20_x_axis_build.json'
OUT_JSON = ROOT + '/solidcraft/40_x_axis_assembly.json'
OUT_SC = ROOT + '/solidcraft/X_Axis_Assembly.sc'

cmds = json.load(open(SRC_JSON, encoding='utf-8'))['commands']

# 1..131：参数 + X 型材草图/拉伸
head = cmds[:131]
# 171..：导杆、轴承、滑车、同步带、同步轮、惰轮轴、电机、限位开关
# 剔除旧的外观命令（它们引用已删除的 X_EndPlate_L/R），外观统一在末尾重新赋
tail = [c for c in cmds[170:]
        if c['command'] not in ('file.save', 'appearance.assign')]

# 端板外观：把分层体统一着色（PETG）
band_bodies = []
man = json.load(open(ROOT + '/refs/tmp/ep_dxf_manifest.json', encoding='utf-8'))
for tag in ('L', 'R'):
    for r in man[tag]:
        for k in range(len(r['dxf_outs'])):
            band_bodies.append('B%s%02d_%d' % (tag, r['index'], k))

assembly = []
# 修正电机机身起点：原件 Q 面在 Y=-57，机身从其后方（-57）开始，
# 只有 Ø22 定位凸台插入端板（Y-59..-57）。原先 -59 会让机身侵入端板 2 mm。
for c in head:
    if c['command'] == 'parameters.add' and c['params'].get('name') == 'MOTOR_Y0':
        c['params']['expression'] = '-57 mm'

assembly.extend(head)
assembly.extend(tail)

# 外观
assembly.append({'command': 'appearance.assign', 'params': {
    'name': 'PETG / 铝型材端面 3D 打印结构（复刻）',
    'bodies': band_bodies, 'color': '#e8923e',
    'pbr': {'metallic': 0.0, 'roughness': 0.45, 'dielectric_ior': 1.5}}})
assembly.append({'command': 'appearance.assign', 'params': {
    'name': '2040 铝型材 / 真实截面', 'bodies': ['X_Profile'],
    'color': '#b0b7bf',
    'pbr': {'metallic': 0.75, 'roughness': 0.35, 'dielectric_ior': 1.5}}})
assembly.append({'command': 'appearance.assign', 'params': {
    'name': 'Ø6 导杆 / 轴承钢',
    'bodies': ['X_GuideRod_LM6_1', 'X_GuideRod_LM6_2'], 'color': '#e1e4e8',
    'pbr': {'metallic': 0.85, 'roughness': 0.22, 'dielectric_ior': 1.5}}})
assembly.append({'command': 'appearance.assign', 'params': {
    'name': 'LM6UU / 轴承钢',
    'bodies': ['X_LM6UU_1', 'X_LM6UU_2'], 'color': '#5a606a',
    'pbr': {'metallic': 0.9, 'roughness': 0.28, 'dielectric_ior': 1.5}}})
assembly.append({'command': 'appearance.assign', 'params': {
    'name': 'GT2 同步带', 'bodies': ['X_Belt_GT2'], 'color': '#17191d',
    'pbr': {'metallic': 0.0, 'roughness': 0.75, 'dielectric_ior': 1.5}}})
assembly.append({'command': 'appearance.assign', 'params': {
    'name': 'GT2 同步轮 / 惰轮轴',
    'bodies': ['X_Pulley_Drive', 'X_Pulley_Idler', 'X_Screw_Idler'],
    'color': '#8a909a',
    'pbr': {'metallic': 0.8, 'roughness': 0.3, 'dielectric_ior': 1.5}}})
assembly.append({'command': 'appearance.assign', 'params': {
    'name': '42 步进电机', 'bodies': ['X_Motor_NEMA17'], 'color': '#2f343c',
    'pbr': {'metallic': 0.65, 'roughness': 0.4, 'dielectric_ior': 1.5}}})
assembly.append({'command': 'appearance.assign', 'params': {
    'name': 'KW11-3Z-A-1 限位开关',
    'bodies': ['X_LimitSwitch_L', 'X_LimitSwitch_R'], 'color': '#20252d',
    'pbr': {'metallic': 0.1, 'roughness': 0.6, 'dielectric_ior': 1.5}}})
assembly.append({'command': 'appearance.assign', 'params': {
    'name': '限位开关安装螺钉',
    'bodies': ['X_LimitScrew_L_1', 'X_LimitScrew_L_2',
               'X_LimitScrew_R_1', 'X_LimitScrew_R_2'], 'color': '#9aa0a8',
    'pbr': {'metallic': 0.85, 'roughness': 0.3, 'dielectric_ior': 1.5}}})

assembly.append({'command': 'file.save', 'params': {
    'path': OUT_SC, 'format': 'container', 'overwrite': True}})

json.dump({'commands': assembly}, open(OUT_JSON, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('base  ', BASE_SC)
print('out   ', OUT_SC)
print('commands', len(assembly), dict(collections.Counter(c['command'] for c in assembly)))
print('endplate band bodies', len(band_bodies))
