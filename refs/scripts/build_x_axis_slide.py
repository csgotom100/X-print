# -*- coding: utf-8 -*-
"""
以 SolidCraft 已打开的 CrossSlide_P014013（FreeCAD 迁移结构）为基准，
在 SolidCraft 里原生重设计「单独 X 轴滑台」。

用户 2026-11-16 纠正：
  「不是十字滑台；先把 X 轴滑台建立起来，材料为 4020 铝型材，
   直接 6mm 导轨，LM6UU 直线轴承，搭配铝型材端面的 3D 打印结构和
   同步带、同步轮、42 步进电机。」
  「参考 solidcraft 里已经打开的 CrossSlide_P014013 的结构，
   它是在 FreeCAD 里设计的，现在改在 SolidCraft 里重新设计。」

本脚本严格沿用参考模型的 X 轴骨架：
  X_Profile          X50..250, Y-57..-37, Z117..157（真实 BREP 截面）
  X_EndPlate_L       X0..53,   Y-79..-37, Z117..157
  X_EndPlate_R       X249.8..300, Y-79..-37, Z117..157
  X_GuideRod_1/2     X42.5..257.5, 中心 Y=-68, Z=152 / 122
  X_Carriage_Lower   X133.5..166.5, Y-68..-57.5, Z112..162
  X_Carriage_Upper   X133.5..166.5, Y-78..-68,   Z112..162
  X_Pulley_Drive     中心 (X21, Y-68, Z137)，原 LM5UU 位改 LM6UU
  X_Pulley_Idler     中心 (X279, Y-68, Z137)
  X_Belt_GT2         X14.35..285.65, Y-71..-65, Z130.35..143.65
  X_Motor_NEMA17     X0..42, Y-59..-17, Z116..158，轴沿 +Y/-Y

升级点（相对 FreeCAD 参考）：
  LM5UU Ø10×15 + Ø5 导杆 → LM6UU Ø12×19 + Ø6 导杆；
  主座 R5.00×15.60 → R6.05×19.20，端板导杆孔 R2.75 → R3.05。

输出：
  solidcraft/20_x_axis_build.json
  solidcraft/X_Axis_Slide.sc
  solidcraft/X_AXIS_SLIDE_PARAMS.csv
  solidcraft/21_x_axis_verify.json
"""
import csv
import json
import os
from collections import Counter

ROOT = 'C:/ink'
BASE_JSON = ROOT + '/solidcraft/13_profile_exact.json'
OUT_JSON = ROOT + '/solidcraft/20_x_axis_build.json'
OUT_SC = ROOT + '/solidcraft/X_Axis_Slide.sc'
OUT_CSV = ROOT + '/solidcraft/X_AXIS_SLIDE_PARAMS.csv'
OUT_VERIFY = ROOT + '/solidcraft/21_x_axis_verify.json'

# 前 26 条 = 11 个型材参数 + X 型材精确草图/拉伸；不要 Z 型材。
base_all = json.load(open(BASE_JSON, encoding='utf-8'))['commands']
base = base_all[:26]
assert base_all[25]['command'] == 'solid.extrude'
assert base_all[25]['params']['body_name'] == 'X_Profile'
existing_params = {c['params']['name'] for c in base if c['command'] == 'parameters.add'}
cmds = list(base)


def add(command, **params):
    cmds.append({'command': command, 'params': params})


def box(name, L, W, H, corner, op='new', body=None, targets=None):
    p = {'length': L, 'width': W, 'height': H, 'corner': list(corner), 'name': name}
    if op == 'new':
        p['operation'] = 'new'
        p['body_name'] = body
    else:
        p['operation'] = op
        p['targets'] = list(targets)
    add('solid.box', **p)


def cyl(name, r, h, base_xyz, axis, op='new', body=None, targets=None):
    p = {'radius': r, 'height': h, 'base': list(base_xyz), 'axis': axis, 'name': name}
    if op == 'new':
        p['operation'] = 'new'
        p['body_name'] = body
    else:
        p['operation'] = op
        p['targets'] = list(targets)
    add('solid.cylinder', **p)


PARAMS = [
    # Ø6 导轨 / LM6UU
    ('ROD_D', '6 mm', '导轨轴承', 'Ø6 导轨直径', True),
    ('ROD_LEN', '215 mm', '导轨轴承', 'X 导轨长度', False),
    ('ROD_X0', '42.5 mm', '导轨轴承', 'X 导轨起点', False),
    ('ROD_Y', '-68 mm', '导轨轴承', '双导轨中心 Y（滑车分型面）', True),
    ('ROD_Z1', '122 mm', '导轨轴承', '下导轨中心 Z', True),
    ('ROD_Z2', '152 mm', '导轨轴承', '上导轨中心 Z', True),
    ('BRG_OD', '12 mm', '导轨轴承', 'LM6UU 外径', True),
    ('BRG_ID', '6 mm', '导轨轴承', 'LM6UU 内孔', True),
    ('BRG_L', '19 mm', '导轨轴承', 'LM6UU 长度', True),
    ('SEAT_R', 'BRG_OD / 2 + 0.05 mm', '导轨轴承', 'LM6UU 主座半径 R6.05', True),
    ('SEAT_L', 'BRG_L + 0.2 mm', '导轨轴承', 'LM6UU 主座长度 19.20', True),
    ('ROD_HOLE_R', 'ROD_D / 2 + 0.05 mm', '导轨轴承', '端板导杆孔 R3.05', True),
    ('PILOT_R', '4.7 mm', '导轨轴承', '轴承座导入段半径', False),
    ('EXIT_R', '5.1 mm', '导轨轴承', '轴承座出口段半径', False),
    ('X_SEAT_X0', '140.4 mm', '导轨轴承', 'X 滑车主座起点', False),

    # 铝型材端面 3D 打印结构（bbox 对齐 CrossSlide_P014013）
    ('EB_L_X0', '0 mm', '端结构', '左端打印结构 X 起点', False),
    ('EB_L_LEN', '53 mm', '端结构', '左端打印结构 X 长度', False),
    ('EB_R_X0', '249.8 mm', '端结构', '右端打印结构 X 起点', False),
    ('EB_R_LEN', '50.2 mm', '端结构', '右端打印结构 X 长度', False),
    ('EB_Y0', '-79 mm', '端结构', '端结构 Y 起点', False),
    ('EB_W', '42 mm', '端结构', '端结构 Y 宽度', False),
    ('EB_Z0', '117 mm', '端结构', '端结构 Z 起点', False),
    ('EB_H', '40 mm', '端结构', '端结构 Z 高度', False),
    ('EB_WALL', '2 mm', '端结构', '打印框架壁厚', False),
    ('X_POCKET_W', '20.8 mm', '冻结项', 'X 限位口袋宽（禁止改动）', True),
    ('X_POCKET_Y1', '-71.1 mm', '冻结项', 'X 限位口袋终点（与 Ø6.10 孔留 0.05）', False),
    ('X_POCKET_ZC', '131.25 mm', '冻结项', 'X 限位口袋中心 Z', False),

    # X 滑车
    ('CAR_X0', '133.5 mm', '滑车', '滑车 X 起点', False),
    ('CAR_L', '33 mm', '滑车', '滑车 X 长度', True),
    ('CAR_SPAN', '50 mm', '滑车', '滑车 Z 跨距', True),
    ('CAR_Z0', '112 mm', '滑车', '滑车 Z 起点', False),
    ('CAR_T_LOWER', '10.5 mm', '滑车', '下滑车厚度', False),
    ('CAR_T_UPPER', '10 mm', '滑车', '上滑车厚度', False),
    ('CAR_LOWER_Y0', '-68 mm', '滑车', '下滑车 Y 起点', False),
    ('CAR_UPPER_Y0', '-78 mm', '滑车', '上滑车 Y 起点', False),
    ('CAR_CORNER_R', '4 mm', '滑车', '滑车外角圆角', False),
    ('CAR_M3_R', '1.7 mm', '滑车', '滑车 M3 孔半径', False),
    ('CAR_M3_PITCH', '12 mm', '滑车', '滑车 M3 孔距', False),
    ('CUT_EXT', '1 mm', '辅助', '刀具外扩', False),

    # GT2 同步带 / 同步轮（与参考模型同位置）
    ('PULLEY_CX_L', '21 mm', '同步带', '主动轮中心 X', False),
    ('PULLEY_CX_R', '279 mm', '同步带', '惰轮中心 X', False),
    ('PULLEY_CZ', '137 mm', '同步带', '同步轮中心 Z', False),
    ('PULLEY_PITCH_R', '5.95 mm', '同步带', 'GT2 节圆半径', True),
    ('BELT_T', '1.4 mm', '同步带', '同步带厚度', False),
    ('BELT_W', '6 mm', '同步带', '同步带宽度（沿 Y）', True),
    ('BELT_Y0', '-65 mm', '同步带', '同步带上表面 Y（向 -Y 拉伸 6）', False),
    ('PULLEY_R', '5.2 mm', '同步带', '同步轮轮毂半径', False),
    ('PULLEY_FLANGE_R', '8 mm', '同步带', '同步轮挡边半径', False),
    ('PULLEY_FLANGE_T', '1 mm', '同步带', '同步轮挡边厚度', False),
    ('PULLEY_W', '12 mm', '同步带', '同步轮总宽（Y-74..-62）', False),
    ('SHAFT_R', '2.5 mm', '同步带', '同步轮/电机轴半径', False),

    # 42 步进电机（参考 X_Motor_NEMA17 bbox）
    ('MOTOR_SIZE', '42 mm', '电机', '42 步进电机截面', True),
    ('MOTOR_LEN', '42 mm', '电机', '42 步进电机机身长度', False),
    ('MOTOR_X0', '0 mm', '电机', '电机机身 X 起点', False),
    ('MOTOR_Y0', '-59 mm', '电机', '电机机身 Y 起点', False),
    ('MOTOR_HOLE_PITCH', '31 mm', '电机', '电机安装孔距', False),
    ('MOTOR_BOSS_R', '11 mm', '电机', '前端定位凸台半径', False),
    ('MOTOR_BOSS_L', '2 mm', '电机', '前端定位凸台长度', False),
    ('MOTOR_RECESS_Y0', 'MOTOR_Y0 - 1 mm', '电机', '左端板电机沉腔起点 Y', False),
    ('MOTOR_RECESS_Y1', 'EB_Y0 + EB_W + 1 mm', '电机', '左端板电机沉腔终点 Y', False),
    ('MOTOR_RECESS_Z0', 'PULLEY_CZ - MOTOR_SIZE / 2 - 1 mm', '电机', '左端板电机沉腔起点 Z', False),
    ('MOTOR_RECESS_Z1', 'PULLEY_CZ + MOTOR_SIZE / 2 + 1 mm', '电机', '左端板电机沉腔终点 Z', False),
    ('BOSS_RELIEF_R', 'MOTOR_BOSS_R + 0.05 mm', '电机', '电机定位凸台让位孔半径', False),
    ('BOSS_RELIEF_Y0', 'MOTOR_Y0 - 3 mm', '电机', '电机定位凸台让位孔起点 Y', False),
    ('BOSS_RELIEF_L', '3 mm + CUT_EXT', '电机', '电机定位凸台让位孔长度', False),

    # 同步带避让 / 惰轮轴
    ('BELT_CLEAR_Y0', '-72 mm', '同步带', '同步带避让槽起点 Y', False),
    ('BELT_CLEAR_Y1', '-64 mm', '同步带', '同步带避让槽终点 Y', False),
    ('BELT_CLEAR_ZPAD', '1 mm', '同步带', '同步带避让槽 Z 单侧余量', False),
    ('IDLER_SHAFT_R', '4.75 mm', '同步带', '惰轮轴半径（与参考模型一致）', True),

    # 原 FreeCAD 端板样式：电机板 + 回折法兰 + 导杆凸台 + 开关耳
    ('MP_Y0', '-71.4 mm', '端结构', '框架前沿 Y', False),
    ('MP_Y1', '-37 mm', '端结构', '框架后沿 Y', False),
    ('MP_T', 'MP_Y1 - MP_Y0', '端结构', '框架 Y 向深度', False),
    ('FL_Y0', '-82 mm', '端结构', '回折法兰前沿 Y', False),
    ('FL_Y1', '-37 mm', '端结构', '回折法兰后沿 Y', False),
    ('FL_L_X0', '49 mm', '端结构', '左回折法兰 X 起点', False),
    ('FL_L_W', '4 mm', '端结构', '左回折法兰厚度', False),
    ('FL_R_X0', '249 mm', '端结构', '右回折法兰 X 起点', False),
    ('FL_R_W', '8.5 mm', '端结构', '右回折法兰厚度', False),
    ('FL_PF_W', '7.4 mm', '端结构', '前框横梁 Y 宽度（-82..-74.6）', False),
    ('ROD_BOSS_R', '5 mm', '端结构', '导杆孔外凸台半径', False),
    ('MOTOR_HOLE_R', '2.75 mm', '端结构', '42 电机安装孔半径', False),
    ('MOTOR_BORE_R', '11.4 mm', '端结构', '电机定位大孔半径', False),
    ('IDLER_BOSS_R', '8.5 mm', '端结构', '惰轮定位凸台半径', False),
    ('ROUND_END_R', '20 mm', '端结构', '右端板圆弧外轮廓半径', False),
    ('TAB_Z0', '119 mm', '端结构', '限位开关耳 Z 起点', False),
    ('TAB_H', '27 mm', '端结构', '限位开关耳 Z 高度', False),

    # KW11-3Z-A-1 限位开关与安装螺钉
    ('SW_L_X0', '41.6 mm', '限位开关', '左开关本体 X 起点', False),
    ('SW_R_X0', '249 mm', '限位开关', '右开关本体 X 起点', False),
    ('SW_W', '12.2 mm', '限位开关', '开关本体 X 宽度（含钮）', False),
    ('SW_D', '6.5 mm', '限位开关', '开关本体 Y 深度', False),
    ('SW_Y0', '-81 mm', '限位开关', '开关本体 Y 起点', False),
    ('SW_Z0', '121.35 mm', '限位开关', '开关本体 Z 起点', False),
    ('SW_H', '19.8 mm', '限位开关', '开关本体 Z 高度', False),
    ('SW_XC_L', '46.9 mm', '限位开关', '左开关安装孔中心 X', False),
    ('SW_XC_R', '255.9 mm', '限位开关', '右开关安装孔中心 X', False),
    ('SW_HOLE_R', '2.4 mm', '限位开关', '开关安装孔半径', False),
    ('SW_HOLE_Z1', '126.5 mm', '限位开关', '下安装孔中心 Z', False),
    ('SW_HOLE_Z2', '136 mm', '限位开关', '上安装孔中心 Z', False),
    ('SW_SCREW_R', '2.35 mm', '限位开关', '安装螺钉半径', False),
    ('SW_SCREW_Y0', '-83.5 mm', '限位开关', '安装螺钉 Y 起点', False),
    ('SW_SCREW_L', '10.1 mm', '限位开关', '安装螺钉长度', False),
    ('SW_HOLE_Y0_L', '-74.8 mm', '限位开关', '左端板开关孔起刀 Y（口袋底内侧）', False),
    ('SW_HOLE_LEN_L', '3.2 mm', '限位开关', '左端板开关孔深度（盲孔）', False),
    ('SW_HOLE_Y0_R', '-75.2 mm', '限位开关', '右端板开关孔起刀 Y（口袋底内侧）', False),
    ('SW_HOLE_LEN_R', '3.6 mm', '限位开关', '右端板开关孔深度（盲孔）', False),
]

new_params = []
for name, expr, group, note, fav in PARAMS:
    if name in existing_params:
        continue
    p = {'name': name, 'expression': expr, 'comment': '[%s] %s' % (group, note)}
    if fav:
        p['favorite'] = True
    add('parameters.add', **p)
    new_params.append((name, expr, group, note, fav))

# ---------------------------------------------------------------------------
# 1. 原 FreeCAD 样式的 L 形端结构
#    主板（电机/惰轮） + 回折法兰 + 导杆凸台 + 筋 + 限位开关耳。
#    不是原来的整块矩形框；尺寸取自原始 BREP 切面与切片。
# ---------------------------------------------------------------------------
BELT_CUT_H = '2 * (PULLEY_PITCH_R + BELT_T / 2 + BELT_CLEAR_ZPAD)'
BELT_CUT_Z = 'PULLEY_CZ - PULLEY_PITCH_R - BELT_T / 2 - BELT_CLEAR_ZPAD'
BELT_CUT_W = 'BELT_CLEAR_Y1 - BELT_CLEAR_Y0'
POCKET_Z0 = 'X_POCKET_ZC - X_POCKET_W / 2'

# 左端：整片法兰 X42.5..53（贴型材端面）+ 减重窗 + 导杆座 + 开关耳
# 42 电机机身位于 X0..42、Y-59..-17，端板在其外侧，故法兰从 X42.5 起
# 原 BREP：V 19158.4，bbox 53×45×40，填充率 20.1%
nm = 'X_EndPlate_L'
box('XL_Flange', '53 mm - 42.5 mm', 'FL_Y1 - FL_Y0', 'EB_H',
    ['42.5 mm', 'FL_Y0', 'EB_Z0'], body=nm)
# 前框：X0..53 上下两根横梁 + X0 竖柱，把 42 电机围在框中
# 只占 Y-82..-74.6，避开同步轮（Y-74..-62）、同步带（Y-71..-65）与电机（Y-59..-17）
box('XL_RailBot', '53 mm', 'FL_PF_W', '5 mm',
    ['EB_L_X0', 'FL_Y0', 'EB_Z0'], op='join', targets=[nm])
box('XL_RailTop', '53 mm', 'FL_PF_W', '5 mm',
    ['EB_L_X0', 'FL_Y0', '152 mm'], op='join', targets=[nm])
box('XL_PostFront', '5 mm', 'FL_PF_W', '40 mm',
    ['EB_L_X0', 'FL_Y0', 'EB_Z0'], op='join', targets=[nm])
# 中部竖撑：把前框与法兰连成一体
box('XL_PostMid', '4 mm', 'FL_PF_W', '40 mm',
    ['40 mm', 'FL_Y0', 'EB_Z0'], op='join', targets=[nm])
# 电机侧不设背板：42 电机机身 Y-59..-17 与端板 Y-59..-57 天然重叠 2 mm，
# 按装配关系让电机直接贴法兰背面，端板只在 X42.5 以外成形。
# 开关耳：法兰向 -Y 伸出
box('XL_SwitchTab', '53 mm - 41.6 mm', 'MP_Y0 - FL_Y0', 'TAB_H',
    ['41.6 mm', 'FL_Y0', 'TAB_Z0'], op='join', targets=[nm])
# 法兰减重窗：避开限位口袋所在 Y 段（-82..-71.4），只在电机/型材侧镂空
box('XL_Win1', '6 mm', '25 mm', '12 mm',
    ['43.5 mm', '-70 mm', '120 mm'], op='cut', targets=[nm])
box('XL_Win2', '6 mm', '25 mm', '12 mm',
    ['43.5 mm', '-70 mm', '144 mm'], op='cut', targets=[nm])

# 电机定位大孔 + 4 安装孔（穿过法兰框与后背板）
for sx in ('-1', '1'):
    for sz in ('-1', '1'):
        mx = 'PULLEY_CX_L + %s * MOTOR_HOLE_PITCH / 2' % sx
        mz = 'PULLEY_CZ + %s * MOTOR_HOLE_PITCH / 2' % sz
        cyl('XL_MotorHole_%s_%s' % (sx, sz), 'MOTOR_HOLE_R', '13 mm',
            [mx, '-58 mm', mz], 'Y', op='cut', targets=[nm])
# 导杆贯穿孔：Ø6.10 从法兰贯通到导杆座（X0..53 全长，避免分段残料）
for i, zp in enumerate(('ROD_Z1', 'ROD_Z2'), 1):
    cyl('XL_RodThru%d' % i, 'ROD_HOLE_R', '54 mm',
        ['-0.5 mm', 'ROD_Y', zp], 'X', op='cut', targets=[nm])
# 电机轴/凸台让位：机身贴 Y-57 法兰背面，仅凸台 + 轴进入端板
cyl('XL_MotorBossHole', 'MOTOR_BOSS_R + 0.2 mm', '4 mm',
    ['PULLEY_CX_L', '-60 mm', 'PULLEY_CZ'], 'Y', op='cut', targets=[nm])
# 同步轮让位：主动轮外径 Ø16 穿过端板
cyl('XL_PulleyClear', 'PULLEY_FLANGE_R + 0.2 mm', '54 mm',
    ['-0.5 mm', '-68 mm', 'PULLEY_CZ'], 'X', op='cut', targets=[nm])
# 同步带穿过端板：把带区整段让空（Z 130.35..143.65，Y -71..-65）
box('XL_BeltSlot', '53 mm + 2 * CUT_EXT', '9.4 mm', '18 mm',
    ['EB_L_X0 - CUT_EXT', '-72 mm', '128 mm'], op='cut', targets=[nm])
# 冻结 X 限位口袋 20.80：刀具只在开关耳 Y 段内，Z 向严格 20.80
box('XL_SwitchPocket', 'SW_W + 0.4 mm', 'MP_Y0 - FL_Y0', 'X_POCKET_W',
    ['SW_L_X0 - 0.3 mm', 'FL_Y0', POCKET_Z0],
    op='cut', targets=[nm])
for i, zp in enumerate(('SW_HOLE_Z1', 'SW_HOLE_Z2'), 1):
    cyl('XL_SwitchHole%d' % i, 'SW_HOLE_R', 'SW_HOLE_LEN_L',
        ['SW_XC_L', 'SW_HOLE_Y0_L', zp], 'Y', op='cut', targets=[nm])
box('XL_ProfileClear', '53 mm - 50 mm + 2 * CUT_EXT', '20 mm', '40 mm',
    ['50 mm - CUT_EXT', '-57 mm', '117 mm'], op='cut', targets=[nm])

# 右端：整片法兰 X249..257.5 + 圆弧外缘（R20，圆心 X280）+ 惰轮座 + 减重窗 + 开关耳
# 原 BREP：V 20565.7，bbox 51×45×40，填充率 22.4%
nm = 'X_EndPlate_R'
# 主法兰：X249..257.5 贴型材端面
box('XR_Flange', '257.5 mm - 249 mm', 'FL_Y1 - FL_Y0', 'EB_H',
    ['249 mm', 'FL_Y0', 'EB_Z0'], body=nm)
# 惰轮侧板：X257.5..300，Y-65..-37，与法兰重叠 0.5 mm
box('XR_IdlerPlate', '300 mm - 257 mm', 'MP_Y1 - (-65 mm)', 'EB_H',
    ['257 mm', '-65 mm', 'EB_Z0'], op='join', targets=[nm])
# 圆弧外缘：R20 圆心 (280, Z137)，与惰轮侧板重叠
cyl('XR_RoundEnd', 'ROUND_END_R', 'MP_Y1 - (-65 mm)',
    ['280 mm', '-65 mm', 'PULLEY_CZ'], 'Y', op='join', targets=[nm])
# 开关耳
box('XR_SwitchTab', '261.2 mm - 249 mm', 'MP_Y0 - FL_Y0', 'TAB_H',
    ['249 mm', 'FL_Y0', 'TAB_Z0'], op='join', targets=[nm])

# 减重窗：法兰上下各开一窗，保留边框与中部横筋
box('XR_Win1', '6.5 mm', '40 mm', '14 mm',
    ['249.5 mm', '-77 mm', '119 mm'], op='cut', targets=[nm])
box('XR_Win2', '6.5 mm', '40 mm', '14 mm',
    ['249.5 mm', '-77 mm', '143 mm'], op='cut', targets=[nm])
# 惰轮侧板：贯穿 Y 全深度的窗口，做成真正的框架（不是只在内部掏空）
box('XR_Win3', '28 mm', '30 mm', '15 mm',
    ['261 mm', '-66 mm', '120 mm'], op='cut', targets=[nm])
box('XR_Win4', '28 mm', '30 mm', '15 mm',
    ['261 mm', '-66 mm', '142 mm'], op='cut', targets=[nm])

# 惰轮让位 + 轴孔
cyl('XR_IdlerPocket', 'PULLEY_FLANGE_R + 0.2 mm', '8 mm',
    ['PULLEY_CX_R', '-66 mm', 'PULLEY_CZ'], 'Y', op='cut', targets=[nm])
cyl('XR_IdlerBore', 'IDLER_SHAFT_R + 0.05 mm', '5 mm',
    ['PULLEY_CX_R', '-61 mm', 'PULLEY_CZ'], 'Y', op='cut', targets=[nm])
# 惰轮轴贯穿法兰与后背板（Ø9.6 通孔，Y-61..-46 覆盖轴尾）
cyl('XR_IdlerThru', 'IDLER_SHAFT_R + 0.05 mm', '15 mm',
    ['PULLEY_CX_R', '-61 mm', 'PULLEY_CZ'], 'Y', op='cut', targets=[nm])
box('XR_BeltSlot', '257.5 mm - 248 mm + CUT_EXT', '9.4 mm', '18 mm',
    ['248 mm', '-72 mm', '128 mm'], op='cut', targets=[nm])
box('XR_SwitchPocket', 'SW_W + 0.4 mm', 'MP_Y0 - FL_Y0 + CUT_EXT', 'X_POCKET_W',
    ['SW_R_X0 - 0.2 mm', 'FL_Y0 - CUT_EXT', POCKET_Z0],
    op='cut', targets=[nm])
for i, zp in enumerate(('SW_HOLE_Z1', 'SW_HOLE_Z2'), 1):
    cyl('XR_SwitchHole%d' % i, 'SW_HOLE_R', 'SW_HOLE_LEN_R',
        ['SW_XC_R', 'SW_HOLE_Y0_R', zp], 'Y', op='cut', targets=[nm])
# 导杆贯穿孔
for i, zp in enumerate(('ROD_Z1', 'ROD_Z2'), 1):
    cyl('XR_RodThru%d' % i, 'ROD_HOLE_R', '52.5 mm',
        ['248 mm', 'ROD_Y', zp], 'X', op='cut', targets=[nm])
box('XR_ProfileClear', '250 mm - 249 mm + 2 * CUT_EXT', '20 mm', '40 mm',
    ['249 mm - CUT_EXT', '-57 mm', '117 mm'], op='cut', targets=[nm])

# ---------------------------------------------------------------------------
# 2. Ø6 导轨 + LM6UU + 上下滑车
# ---------------------------------------------------------------------------
for i, zp in enumerate(('ROD_Z1', 'ROD_Z2'), 1):
    cyl('XR_Rod%d' % i, 'ROD_D / 2', 'ROD_LEN',
        ['ROD_X0', 'ROD_Y', zp], 'X', body='X_GuideRod_LM6_%d' % i)
for i, zp in enumerate(('ROD_Z1', 'ROD_Z2'), 1):
    nm = 'X_LM6UU_%d' % i
    b = ['X_SEAT_X0', 'ROD_Y', zp]
    cyl('X_Brg%d_Outer' % i, 'BRG_OD / 2', 'BRG_L', b, 'X', body=nm)
    cyl('X_Brg%d_Bore' % i, 'BRG_ID / 2', 'BRG_L', b, 'X', op='cut', targets=[nm])

for half, y0p, tp in (('Lower', 'CAR_LOWER_Y0', 'CAR_T_LOWER'),
                      ('Upper', 'CAR_UPPER_Y0', 'CAR_T_UPPER')):
    nm = 'X_Carriage_' + half
    box('XC_%s_Blank' % half, 'CAR_L', tp, 'CAR_SPAN',
        ['CAR_X0', y0p, 'CAR_Z0'], body=nm)
    add('solid.fillet', body=nm, radius='CAR_CORNER_R',
        edges=[{'body': nm, 'index': i} for i in (0, 2, 8, 11)])
    # 相邻孔段做 1 mm 重叠，避免共面触发布尔重试；最终几何仍由最大径段决定
    pilot_len = 'X_SEAT_X0 - CAR_X0 + CUT_EXT'
    exit_len = 'CAR_X0 + CAR_L - X_SEAT_X0 - SEAT_L + CUT_EXT'
    for i, zp in enumerate(('ROD_Z1', 'ROD_Z2'), 1):
        cyl('XC_%s_Pilot%d' % (half, i), 'PILOT_R', pilot_len,
            ['CAR_X0', 'ROD_Y', zp], 'X', op='cut', targets=[nm])
        cyl('XC_%s_Seat%d' % (half, i), 'SEAT_R', 'SEAT_L',
            ['X_SEAT_X0', 'ROD_Y', zp], 'X', op='cut', targets=[nm])
        cyl('XC_%s_Exit%d' % (half, i), 'EXIT_R', exit_len,
            ['X_SEAT_X0 + SEAT_L - CUT_EXT', 'ROD_Y', zp], 'X',
            op='cut', targets=[nm])
    m3_z = 'CAR_Z0 + CAR_SPAN / 2'
    m3_xs = ['CAR_X0 + CAR_L / 2 - CAR_M3_PITCH / 2',
             'CAR_X0 + CAR_L / 2 + CAR_M3_PITCH / 2']
    for i, mx in enumerate(m3_xs, 1):
        cyl('XC_%s_M3_%d' % (half, i), 'CAR_M3_R', '%s + 2 * CUT_EXT' % tp,
            [mx, '%s - CUT_EXT' % y0p, m3_z], 'Y', op='cut', targets=[nm])
    # 同步带通过槽：夹带区保留在槽两侧，滑车上下半仍连成一体
    box('XC_%s_BeltClear' % half, 'CAR_L + 2 * CUT_EXT',
        'BELT_CLEAR_Y1 - BELT_CLEAR_Y0',
        '2 * (PULLEY_PITCH_R + BELT_T / 2 + BELT_CLEAR_ZPAD)',
        ['CAR_X0 - CUT_EXT', 'BELT_CLEAR_Y0',
         'PULLEY_CZ - PULLEY_PITCH_R - BELT_T / 2 - BELT_CLEAR_ZPAD'],
        op='cut', targets=[nm])

# ---------------------------------------------------------------------------
# 3. GT2 同步带：两条直线带 + 两端环形带，全部原生 box/cylinder
#    截面与 CrossSlide_P014013 对齐：X14.35..285.65, Y-71..-65, Z130.35..143.65
# ---------------------------------------------------------------------------
belt_len = 'PULLEY_CX_R - PULLEY_CX_L'
box('X_Belt_Top', belt_len, 'BELT_W', 'BELT_T',
    ['PULLEY_CX_L', '-71 mm',
     'PULLEY_CZ + PULLEY_PITCH_R - BELT_T / 2'], body='X_Belt_GT2')
# 先接两端包绕段，最后接下边，避免中途出现“joined piece doesn't touch”警告
for tag, cxp in (('L', 'PULLEY_CX_L'), ('R', 'PULLEY_CX_R')):
    cyl('X_Belt_Wrap_%s' % tag, 'PULLEY_PITCH_R + BELT_T / 2', 'BELT_W',
        [cxp, '-71 mm', 'PULLEY_CZ'], 'Y',
        op='join', targets=['X_Belt_GT2'])
box('X_Belt_Bottom', belt_len, 'BELT_W', 'BELT_T',
    ['PULLEY_CX_L', '-71 mm',
     'PULLEY_CZ - PULLEY_PITCH_R - BELT_T / 2'],
    op='join', targets=['X_Belt_GT2'])
for tag, cxp in (('L', 'PULLEY_CX_L'), ('R', 'PULLEY_CX_R')):
    cyl('X_Belt_Inner_%s' % tag, 'PULLEY_PITCH_R - BELT_T / 2', 'BELT_W',
        [cxp, '-71 mm', 'PULLEY_CZ'], 'Y',
        op='cut', targets=['X_Belt_GT2'])

# 同步轮：轮毂 + 双挡边，Y -74..-62，与参考模型一致
for tag, cxp in (('Drive', 'PULLEY_CX_L'), ('Idler', 'PULLEY_CX_R')):
    nm = 'X_Pulley_' + tag
    cyl('XPUL_%s_Hub' % tag, 'PULLEY_R', 'PULLEY_W',
        [cxp, '-74 mm', 'PULLEY_CZ'], 'Y', body=nm)
    cyl('XPUL_%s_Flange0' % tag, 'PULLEY_FLANGE_R', 'PULLEY_FLANGE_T',
        [cxp, '-75 mm', 'PULLEY_CZ'], 'Y', op='join', targets=[nm])
    cyl('XPUL_%s_Flange1' % tag, 'PULLEY_FLANGE_R', 'PULLEY_FLANGE_T',
        [cxp, '-62 mm - PULLEY_FLANGE_T', 'PULLEY_CZ'], 'Y',
        op='join', targets=[nm])
    bore_r = 'SHAFT_R' if tag == 'Drive' else 'IDLER_SHAFT_R'
    cyl('XPUL_%s_Bore' % tag, bore_r, 'PULLEY_W + 2 * PULLEY_FLANGE_T',
        [cxp, '-75 mm', 'PULLEY_CZ'], 'Y', op='cut', targets=[nm])

# 惰轮轴（右）：参考模型为 Ø9.5，穿过惰轮内孔而非与轮毂交叠
cyl('X_Screw_Idler', 'IDLER_SHAFT_R', '31.5 mm',
    ['PULLEY_CX_R', '-79.5 mm', 'PULLEY_CZ'], 'Y', body='X_Screw_Idler')

# ---------------------------------------------------------------------------
# 4. 42 步进电机（与 CrossSlide_P014013 的 X_Motor_NEMA17 同位置）
# ---------------------------------------------------------------------------
box('X_Motor_Blank', 'MOTOR_SIZE', 'MOTOR_LEN', 'MOTOR_SIZE',
    ['MOTOR_X0', 'MOTOR_Y0', 'PULLEY_CZ - MOTOR_SIZE / 2'],
    body='X_Motor_NEMA17')
cyl('X_Motor_Boss', 'MOTOR_BOSS_R', 'MOTOR_BOSS_L',
    ['PULLEY_CX_L', 'MOTOR_Y0 - MOTOR_BOSS_L', 'PULLEY_CZ'], 'Y',
    op='join', targets=['X_Motor_NEMA17'])
cyl('X_Motor_Shaft', 'SHAFT_R', '18 mm',
    ['PULLEY_CX_L', '-73 mm', 'PULLEY_CZ'], 'Y',
    op='join', targets=['X_Motor_NEMA17'])

# ---------------------------------------------------------------------------
# 5. KW11-3Z-A-1 限位开关 + 两颗 M3 安装螺钉（与参考模型同位置）
# ---------------------------------------------------------------------------
for tag, x0p, xcp in (('L', 'SW_L_X0', 'SW_XC_L'),
                      ('R', 'SW_R_X0', 'SW_XC_R')):
    nm = 'X_LimitSwitch_' + tag
    box('XLS_%s_Body' % tag, 'SW_W', 'SW_D', 'SW_H',
        [x0p, 'SW_Y0', 'SW_Z0'], body=nm)
    for i, zp in enumerate(('SW_HOLE_Z1', 'SW_HOLE_Z2'), 1):
        cyl('XLS_%s_Hole%d' % (tag, i), 'SW_HOLE_R', 'SW_D + 2 * CUT_EXT',
            [xcp, 'SW_Y0 - CUT_EXT', zp], 'Y', op='cut', targets=[nm])
    for i, zp in enumerate(('SW_HOLE_Z1', 'SW_HOLE_Z2'), 1):
        cyl('X_LimitScrew_%s_%d' % (tag, i), 'SW_SCREW_R', 'SW_SCREW_L',
            [xcp, 'SW_SCREW_Y0', zp], 'Y', body='X_LimitScrew_%s_%d' % (tag, i))

# ---------------------------------------------------------------------------
# 6. 外观与保存
# ---------------------------------------------------------------------------
add('appearance.assign', name='4020 铝型材 / 真实截面',
    bodies=['X_Profile'], color='#b0b7bf',
    pbr={'metallic': 0.75, 'roughness': 0.35, 'dielectric_ior': 1.5})
add('appearance.assign', name='PETG / 铝型材端面 3D 打印结构',
    bodies=['X_EndPlate_L', 'X_EndPlate_R',
            'X_Carriage_Lower', 'X_Carriage_Upper'],
    color='#e8923e', pbr={'metallic': 0.0, 'roughness': 0.45, 'dielectric_ior': 1.5})
add('appearance.assign', name='Ø6 导轨 / 轴承钢',
    bodies=['X_GuideRod_LM6_1', 'X_GuideRod_LM6_2'], color='#e1e4e8',
    pbr={'metallic': 0.85, 'roughness': 0.22, 'dielectric_ior': 1.5})
add('appearance.assign', name='LM6UU / 轴承钢',
    bodies=['X_LM6UU_1', 'X_LM6UU_2'], color='#5a606a',
    pbr={'metallic': 0.9, 'roughness': 0.28, 'dielectric_ior': 1.5})
add('appearance.assign', name='GT2 同步带',
    bodies=['X_Belt_GT2'], color='#17191d',
    pbr={'metallic': 0.0, 'roughness': 0.75, 'dielectric_ior': 1.5})
add('appearance.assign', name='GT2 同步轮 / 惰轮轴',
    bodies=['X_Pulley_Drive', 'X_Pulley_Idler', 'X_Screw_Idler'], color='#8a909a',
    pbr={'metallic': 0.8, 'roughness': 0.3, 'dielectric_ior': 1.5})
add('appearance.assign', name='42 步进电机',
    bodies=['X_Motor_NEMA17'], color='#2f343c',
    pbr={'metallic': 0.65, 'roughness': 0.4, 'dielectric_ior': 1.5})
add('appearance.assign', name='KW11-3Z-A-1 限位开关',
    bodies=['X_LimitSwitch_L', 'X_LimitSwitch_R'], color='#20252d',
    pbr={'metallic': 0.1, 'roughness': 0.6, 'dielectric_ior': 1.5})
add('appearance.assign', name='限位开关安装螺钉',
    bodies=['X_LimitScrew_L_1', 'X_LimitScrew_L_2',
            'X_LimitScrew_R_1', 'X_LimitScrew_R_2'], color='#9aa0a8',
    pbr={'metallic': 0.85, 'roughness': 0.3, 'dielectric_ior': 1.5})
add('file.save', path=OUT_SC, format='container', overwrite=True)

os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
json.dump({'commands': cmds}, open(OUT_JSON, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['分组', '参数名', '表达式', '说明', '核心参数', '生成方式'])
    for p in base:
        if p['command'] == 'parameters.add':
            q = p['params']
            w.writerow(['型材', q['name'], q['expression'], q.get('comment', ''), '',
                        'SolidCraft 原生 parameters.add'])
    for name, expr, group, note, fav in new_params:
        w.writerow([group, name, expr, note, '是' if fav else '',
                    'SolidCraft 原生 parameters.add'])

BODIES = [
    'X_Profile', 'X_EndPlate_L', 'X_EndPlate_R',
    'X_GuideRod_LM6_1', 'X_GuideRod_LM6_2',
    'X_LM6UU_1', 'X_LM6UU_2',
    'X_Carriage_Lower', 'X_Carriage_Upper',
    'X_Belt_GT2', 'X_Pulley_Drive', 'X_Pulley_Idler',
    'X_Screw_Idler', 'X_Motor_NEMA17',
    'X_LimitSwitch_L', 'X_LimitSwitch_R',
    'X_LimitScrew_L_1', 'X_LimitScrew_L_2',
    'X_LimitScrew_R_1', 'X_LimitScrew_R_2',
]
verify = {'commands': [
    {'command': 'inspect.measure', 'params': {'items': [
        {'type': 'face', 'body': 'X_EndPlate_L', 'point': [46.0, -76.0, 120.85]},
        {'type': 'face', 'body': 'X_EndPlate_L', 'point': [46.0, -76.0, 141.65]}]}},
    {'command': 'inspect.interference', 'params': {'bodies': BODIES, 'budget_s': 900}},
    {'command': 'parameters.list', 'params': {'filter': 'user'}},
    {'command': 'appearance.list', 'params': {}},
]}
json.dump(verify, open(OUT_VERIFY, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('WROTE', OUT_JSON)
print('WROTE', OUT_SC)
print('WROTE', OUT_CSV)
print('WROTE', OUT_VERIFY)
print('commands', len(cmds), dict(Counter(c['command'] for c in cmds)))
print('new params', len(new_params), 'total params', len(existing_params) + len(new_params))
print('X AXIS SLIDE BUILD SCRIPT DONE')
