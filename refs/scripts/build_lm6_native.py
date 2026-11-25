# -*- coding: utf-8 -*-
"""
生成「全部 SolidCraft 原生参数化」的 LM6UU 局部重设计命令脚本。

用户口径（2026-11-13）：
  「我要求你全部在 solidcraft 重新参数化设计，目的是为了修改设计时都能编辑」
  界面选择：语义化参数化 / 铝型材也改成原生参数化。

设计边界：
  * 零 STEP 导入、零哑实体；18 个 body 全部由 parameters.add + solid.* 生成。
  * 8 件结构件按设计意图语义化重建（法兰板 / 周边框架 / 电机安装台 /
    导杆孔 / 限位口袋 / 阶梯轴承座 / M3 合拢孔 / 皮带让位 / 角圆角）。
  * 2 根 2040 铝型材按截面 + 4 条 T 槽语义化重建，接口尺寸不变。
  * 4 导杆 + 4 LM6UU 为纯参数化原语。
  * 冻结项 Z 槽 22.00 / X 口袋 20.80 直接驱动切除特征，可实测。
  * 端板与型材改为「端面贴合」而非体积重叠，保证 0 干涉；
    装饰性镂空与原件允许差异（体积差在报告中量化）。

输出：
  solidcraft/07_lm6_native.json          主命令脚本
  solidcraft/LM6UU_NATIVE_PARAMS.csv     参数表
  solidcraft/08_lm6_native_verify.json   只读验证（冻结项/干涉/参数清单）
  solidcraft/09_lm6_native_paramtest.json 参数联动测试 A（改 SEAT_R 后量体积）
  solidcraft/10_lm6_native_paramtest_frozen.json 参数联动测试 B（坐标 + 冻结槽宽）
  solidcraft/LM6UU_Native.sc             由 CLI run 07 脚本生成
"""
import csv
import json
import os

ROOT = 'C:/ink'
OUT_JSON = ROOT + '/solidcraft/07_lm6_native.json'
OUT_CSV = ROOT + '/solidcraft/LM6UU_NATIVE_PARAMS.csv'
OUT_VERIFY = ROOT + '/solidcraft/08_lm6_native_verify.json'
OUT_PARAMTEST = ROOT + '/solidcraft/09_lm6_native_paramtest.json'
OUT_PARAMTEST2 = ROOT + '/solidcraft/10_lm6_native_paramtest_frozen.json'
OUT_APPEAR = ROOT + '/solidcraft/11_lm6_native_appearance.json'
DESIGN = ROOT + '/solidcraft/LM6UU_Native.sc'

# ---------------------------------------------------------------------------
# 参数表：name / expression / 分组 / 说明 / 是否核心
# 依赖顺序：被引用者必须在前。
# ---------------------------------------------------------------------------
PARAMS = [
    # A 轴承与导杆（LM6UU 核心）
    ('BRG_OD',      '12 mm',                       'A 轴承导杆', 'LM6UU 外径', True),
    ('BRG_ID',      '6 mm',                        'A 轴承导杆', 'LM6UU 内孔（= 导杆直径）', True),
    ('BRG_L',       '19 mm',                       'A 轴承导杆', 'LM6UU 长度', True),
    ('ROD_D',       '6 mm',                        'A 轴承导杆', '导杆直径', True),
    ('SEAT_R',      'BRG_OD / 2 + 0.05 mm',        'A 轴承导杆', '滑车主座半径（轴承外径 + 0.10 间隙）', True),
    ('SEAT_L',      'BRG_L + 0.2 mm',              'A 轴承导杆', '滑车主座长度', True),
    ('ROD_HOLE_R',  'ROD_D / 2 + 0.05 mm',         'A 轴承导杆', '端板导杆孔半径', True),
    ('PILOT_R',     '4.7 mm',                      'A 轴承导杆', '导入段半径（形成 -端轴向挡肩）', True),
    ('EXIT_R',      '5.1 mm',                      'A 轴承导杆', '出口段半径（形成 +端轴向挡肩）', True),
    ('ROD_X_LEN',   '215 mm',                      'A 轴承导杆', 'X 轴导杆长度', False),
    ('ROD_Z_LEN',   '165 mm',                      'A 轴承导杆', 'Z 轴导杆长度', False),
    ('X_ROD_X0',    '42.5 mm',                     'A 轴承导杆', 'X 导杆起点 X', False),
    ('X_ROD_Y',     '-68 mm',                      'A 轴承导杆', 'X 导杆中心 Y（滑车分型面）', False),
    ('X_ROD_Z1',    '122 mm',                      'A 轴承导杆', 'X 导杆 1 中心 Z', False),
    ('X_ROD_Z2',    '152 mm',                      'A 轴承导杆', 'X 导杆 2 中心 Z', False),
    ('Z_ROD_Z0',    '54.5 mm',                     'A 轴承导杆', 'Z 导杆起点 Z', False),
    ('Z_ROD_X1',    '135 mm',                      'A 轴承导杆', 'Z 导杆 1 中心 X', False),
    ('Z_ROD_X2',    '165 mm',                      'A 轴承导杆', 'Z 导杆 2 中心 X', False),
    ('Z_ROD_Y',     '-12 mm',                      'A 轴承导杆', 'Z 导杆中心 Y（滑车分型面）', False),
    ('X_SEAT_X0',   '140.4 mm',                    'A 轴承导杆', 'X 滑车主座起点 X', False),
    ('Z_SEAT_Z0',   '127.4 mm',                    'A 轴承导杆', 'Z 滑车主座起点 Z', False),

    # B 设计冻结项（直接驱动几何）
    ('Z_SLOT_W',    '22 mm',                       'B 冻结项', 'Z 轴限位开关槽宽（禁止改动）', True),
    ('X_POCKET_W',  '20.8 mm',                     'B 冻结项', 'X 轴限位开关口袋宽（禁止改动）', True),

    # C 端板公共语义尺寸
    ('FLANGE_T',    '7.5 mm',                      'C 端板', '端板法兰板厚度（贴型材端面）', False),
    ('FRAME_WALL',  '1.5 mm',                      'C 端板', '端板周边框架壁厚', False),
    ('MOTOR_PAD_L', '10 mm',                       'C 端板', '电机安装台伸出长度', False),
    ('MOTOR_PAD_W', '18 mm',                       'C 端板', '电机安装台宽度', False),
    ('MOTOR_PAD_H', '24 mm',                       'C 端板', '电机安装台高度', False),
    ('MOTOR_BORE_L_R', '8.5 mm',                   'C 端板', 'L 端板电机让位孔半径', False),
    ('MOTOR_BORE_R_R', '10 mm',                    'C 端板', 'R 端板电机让位孔半径', False),
    ('MOTOR_Y',     '-62 mm',                      'C 端板', 'X 端板电机孔中心 Y', False),
    ('MOTOR_Z',     '137 mm',                      'C 端板', 'X 端板电机孔中心 Z', False),
    ('Z_MOTOR_Y',   '9 mm',                        'C 端板', 'Z 端板电机孔中心 Y', False),
    ('MOUNT_R',     '1.7 mm',                      'C 端板', '端板安装孔半径（M3 过孔）', False),
    ('X_MOUNT_Y',   '-60 mm',                      'C 端板', 'X 端板安装孔中心 Y', False),
    ('Z_MOUNT_Y',   '-5 mm',                       'C 端板', 'Z 端板安装孔中心 Y', False),
    ('BELT_SLOT_H', '7 mm',                        'C 端板', '端板顶部皮带让位槽高度', False),

    # D X 轴端板
    ('X_EP_L_X0',   '0 mm',                        'D X 端板', 'X 端板 L 起点 X', False),
    ('X_EP_L_LEN',  '50 mm',                       'D X 端板', 'X 端板 L 长度（贴合型材 X50 端面）', False),
    ('X_EP_R_X0',   '250 mm',                      'D X 端板', 'X 端板 R 起点 X', False),
    ('X_EP_R_LEN',  '50 mm',                       'D X 端板', 'X 端板 R 长度', False),
    ('X_EP_Y0',     '-79 mm',                      'D X 端板', 'X 端板 Y 起点', False),
    ('X_EP_W',      '42 mm',                       'D X 端板', 'X 端板 Y 宽度', False),
    ('X_EP_Z0',     '117 mm',                      'D X 端板', 'X 端板 Z 起点', False),
    ('X_EP_H',      '40 mm',                       'D X 端板', 'X 端板 Z 高度', False),
    ('X_POCKET_X0', '41.5 mm',                     'D X 端板', '限位口袋起点 X', False),
    ('X_POCKET_Y0', '-79 mm',                      'D X 端板', '限位口袋起点 Y', False),
    ('X_POCKET_Y1', '-71.1 mm',                    'D X 端板', '限位口袋终点 Y（与 Ø6.10 孔留 0.05 间隙）', False),
    ('X_POCKET_ZC', '131.25 mm',                   'D X 端板', '限位口袋中心 Z', False),

    # E Z 轴端板
    ('Z_EP_L_X0',   '105 mm',                      'E Z 端板', 'Z 端板 L 起点 X', False),
    ('Z_EP_L_W',    '90 mm',                       'E Z 端板', 'Z 端板 L X 宽度', False),
    ('Z_EP_L_Y0',   '-30 mm',                      'E Z 端板', 'Z 端板 L Y 起点', False),
    ('Z_EP_L_D',    '49 mm',                       'E Z 端板', 'Z 端板 L Y 深度', False),
    ('Z_EP_L_Z0',   '12 mm',                       'E Z 端板', 'Z 端板 L Z 起点', False),
    ('Z_EP_L_H',    '50 mm',                       'E Z 端板', 'Z 端板 L Z 高度（贴合型材 Z62 端面）', False),
    ('Z_EP_R_X0',   '130 mm',                      'E Z 端板', 'Z 端板 R 起点 X', False),
    ('Z_EP_R_W',    '40 mm',                       'E Z 端板', 'Z 端板 R X 宽度', False),
    ('Z_EP_R_Y0',   '-23 mm',                      'E Z 端板', 'Z 端板 R Y 起点', False),
    ('Z_EP_R_D',    '42 mm',                       'E Z 端板', 'Z 端板 R Y 深度', False),
    ('Z_EP_R_Z0',   '212 mm',                      'E Z 端板', 'Z 端板 R Z 起点（贴合型材 Z212 端面）', False),
    ('Z_EP_R_H',    '50 mm',                       'E Z 端板', 'Z 端板 R Z 高度', False),
    ('Z_SLOT_XC',   '150 mm',                      'E Z 端板', 'Z 限位槽中心 X', False),
    ('Z_SLOT_Y0',   '-30 mm',                      'E Z 端板', 'Z 限位槽起点 Y', False),
    ('Z_SLOT_Y1',   '-10 mm',                      'E Z 端板', 'Z 限位槽终点 Y（局部槽，不切断端板）', False),
    ('Z_SLOT_Z0',   '52 mm',                       'E Z 端板', 'Z 限位槽起点 Z', False),

    # F 滑车（X/Z 同构，仅坐标映射不同）
    ('CAR_L',       '33 mm',                       'F 滑车', '滑车沿运动轴长度', True),
    ('CAR_SPAN',    '50 mm',                       'F 滑车', '滑车横向跨距（两导杆外侧）', True),
    ('CAR_T_LOWER', '10.5 mm',                     'F 滑车', '下滑车半体厚度', True),
    ('CAR_T_UPPER', '10 mm',                       'F 滑车', 'X 上滑车半体厚度', True),
    ('CAR_T_UPPER_Z','15 mm',                      'F 滑车', 'Z 上滑车半体厚度（真实 bbox Y-27..-12，与下半体在 Y=-12 合拢）', True),
    ('CAR_CORNER_R','4 mm',                        'F 滑车', '滑车四角圆角半径', False),
    ('CAR_M3_R',    '1.7 mm',                      'F 滑车', 'M3 合拢通孔半径', True),
    ('CAR_CB_R_UPPER','3.2 mm',                    'F 滑车', '上半体沉孔半径', False),
    ('CAR_CB_R_LOWER','2.3 mm',                    'F 滑车', '下半体沉孔半径', False),
    ('CAR_CB_DEPTH_UPPER','3 mm',                  'F 滑车', '上半体沉孔深度', False),
    ('CAR_CB_DEPTH_LOWER','8 mm',                  'F 滑车', '下半体沉孔深度', False),
    ('CAR_M3_PITCH','12 mm',                       'F 滑车', '两 M3 孔间距', False),
    ('CAR_BELT_W',  '5 mm',                        'F 滑车', '中央皮带让位腔边长（须 < M3 孔距 − 2×沉孔半径，避免与沉孔刀具重叠导致布尔空结果）', False),
    ('CAR_BELT_D',  '2 mm',                        'F 滑车', '中央皮带让位腔深度', False),
    ('X_CAR_X0',    '133.5 mm',                    'F 滑车', 'X 滑车起点 X', False),
    ('X_CAR_Z0',    '112 mm',                      'F 滑车', 'X 滑车起点 Z', False),
    ('Z_CAR_X0',    '125 mm',                      'F 滑车', 'Z 滑车起点 X', False),
    ('Z_CAR_Z0',    '120.5 mm',                    'F 滑车', 'Z 滑车起点 Z', False),
    ('X_CAR_LOWER_Y0','-68 mm',                    'F 滑车', 'X 下半体 Y 起点（= 分型面）', False),
    ('X_CAR_UPPER_Y0','-78 mm',                    'F 滑车', 'X 上半体 Y 起点', False),
    ('Z_CAR_LOWER_Y0','-12 mm',                    'F 滑车', 'Z 下半体 Y 起点（= 分型面）', False),
    ('Z_CAR_UPPER_Y0','-27 mm',                    'F 滑车', 'Z 上半体 Y 起点', False),

    # G 2040 铝型材
    ('X_PROF_X0',   '50 mm',                       'G 型材', 'X 型材起点 X', False),
    ('X_PROF_LEN',  '200 mm',                      'G 型材', 'X 型材长度', False),
    ('X_PROF_Y0',   '-57 mm',                      'G 型材', 'X 型材 Y 起点', False),
    ('X_PROF_W',    '20 mm',                       'G 型材', 'X 型材截面宽（2040 的 20）', False),
    ('X_PROF_Z0',   '117 mm',                      'G 型材', 'X 型材 Z 起点', False),
    ('X_PROF_H',    '40 mm',                       'G 型材', 'X 型材截面高（2040 的 40）', False),
    ('Z_PROF_X0',   '130 mm',                      'G 型材', 'Z 型材起点 X', False),
    ('Z_PROF_W',    '40 mm',                       'G 型材', 'Z 型材截面宽', False),
    ('Z_PROF_Y0',   '-1 mm',                       'G 型材', 'Z 型材 Y 起点', False),
    ('Z_PROF_D',    '20 mm',                       'G 型材', 'Z 型材截面深', False),
    ('Z_PROF_Z0',   '62 mm',                       'G 型材', 'Z 型材起点 Z', False),
    ('Z_PROF_LEN',  '150 mm',                      'G 型材', 'Z 型材长度', False),
    ('PROF_SLOT_W', '6 mm',                        'G 型材', 'T 槽口宽', False),
    ('PROF_SLOT_D', '6 mm',                        'G 型材', 'T 槽深', False),
    ('PROF_CORE_D', '6 mm',                        'G 型材', '中心通孔直径（语义化挤压截面，非真实薄壁型腔）', False),

    # H 建模辅助
    ('OVL',         '0.2 mm',                      'H 辅助', '加料特征与主体的重叠量（保证布尔可靠）', False),
    ('CUT_EXT',     '1 mm',                        'H 辅助', '去料刀具外延长度（保证贯通）', False),
]

cmds = []


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


def cyl(name, r, h, base, axis, op='new', body=None, targets=None):
    p = {'radius': r, 'height': h, 'base': list(base), 'axis': axis, 'name': name}
    if op == 'new':
        p['operation'] = 'new'
        p['body_name'] = body
    else:
        p['operation'] = op
        p['targets'] = list(targets)
    add('solid.cylinder', **p)


def corner_fillet(body, radius='CAR_CORNER_R'):
    # 4 条沿 Y（厚度方向）的边 = X-Z 外廓的四角 R4。
    # 已用 refs/tmp/fillet_cmp.json 实测：
    #   (0,2,8,11) -> dV=137.435 mm3 = 4*(16-4pi)*10  -> 沿 Y 的四角，正确
    #   (4,6,7,9)  -> dV=687.176 mm3 = 4*(16-4pi)*50  -> 沿 Z 的四角，错误
    # 索引与尺寸无关，参数改动后仍有效。
    add('solid.fillet', body=body, radius=radius,
        edges=[{'body': body, 'index': i} for i in (0, 2, 8, 11)])


# ===========================================================================
# 1. 参数
# ===========================================================================
for name, expr, group, note, fav in PARAMS:
    p = {'name': name, 'expression': expr, 'comment': '[%s] %s' % (group, note)}
    if fav:
        p['favorite'] = True
    add('parameters.add', **p)

# ===========================================================================
# 2. X 轴端板 L / R（法兰板 + 周边框架 + 电机安装台 + 导杆孔 + 限位口袋）
# ===========================================================================
for tag, x0p, lenp, side in (('L', 'X_EP_L_X0', 'X_EP_L_LEN', 'left'),
                             ('R', 'X_EP_R_X0', 'X_EP_R_LEN', 'right')):
    nm = 'X_EndPlate_' + tag
    f_l = '%s - FLANGE_T' % lenp
    # 毛坯：外廓
    box('XP_%s_Blank' % tag, lenp, 'X_EP_W', 'X_EP_H',
        [x0p, 'X_EP_Y0', 'X_EP_Z0'], body=nm)
    # 框架腔：留下周边壁 + 靠型材侧法兰板
    if side == 'left':
        cav_x0, cav_len = x0p, f_l
        pad_x0 = 'X_EP_L_X0 + X_EP_L_LEN - FLANGE_T - MOTOR_PAD_L'
    else:
        cav_x0, cav_len = '%s + FLANGE_T' % x0p, f_l
        pad_x0 = 'X_EP_R_X0 + FLANGE_T - OVL'
    box('XP_%s_FrameCavity' % tag, cav_len,
        'X_EP_W - 2 * FRAME_WALL', 'X_EP_H - 2 * FRAME_WALL',
        [cav_x0, 'X_EP_Y0 + FRAME_WALL', 'X_EP_Z0 + FRAME_WALL'],
        op='cut', targets=[nm])
    # 电机安装台（与法兰板重叠 OVL 保证连接）
    box('XP_%s_MotorPad' % tag, 'MOTOR_PAD_L + OVL', 'MOTOR_PAD_W', 'MOTOR_PAD_H',
        [pad_x0, 'MOTOR_Y - MOTOR_PAD_W / 2', 'MOTOR_Z - MOTOR_PAD_H / 2'],
        op='join', targets=[nm])
    # 电机让位孔
    mrb = 'MOTOR_BORE_L_R' if tag == 'L' else 'MOTOR_BORE_R_R'
    cyl('XP_%s_MotorBore' % tag, mrb,
        '%s + 2 * CUT_EXT' % lenp,
        ['%s - CUT_EXT' % x0p, 'MOTOR_Y', 'MOTOR_Z'], 'X', op='cut', targets=[nm])
    # 2 × Ø6.10 导杆孔（LM6UU 改造关键尺寸）
    for i, zp in enumerate(('X_ROD_Z1', 'X_ROD_Z2'), 1):
        cyl('XP_%s_RodBore%d' % (tag, i), 'ROD_HOLE_R', '%s + 2 * CUT_EXT' % lenp,
            ['%s - CUT_EXT' % x0p, 'X_ROD_Y', zp], 'X', op='cut', targets=[nm])
    # 2 × M3 安装孔
    for i, zp in enumerate(('X_ROD_Z1', 'X_ROD_Z2'), 1):
        cyl('XP_%s_MountHole%d' % (tag, i), 'MOUNT_R', '%s + 2 * CUT_EXT' % lenp,
            ['%s - CUT_EXT' % x0p, 'X_MOUNT_Y', zp], 'X', op='cut', targets=[nm])
    # 顶部皮带让位槽（型材侧、顶部敞开）
    box('XP_%s_BeltSlot' % tag, '%s + 2 * CUT_EXT' % lenp,
        'X_EP_Y0 + X_EP_W - X_PROF_Y0', 'BELT_SLOT_H + CUT_EXT',
        ['%s - CUT_EXT' % x0p, 'X_PROF_Y0',
         'X_EP_Z0 + X_EP_H - BELT_SLOT_H'], op='cut', targets=[nm])
    # L 端板专有：限位开关口袋（冻结 20.80）
    if tag == 'L':
        box('XP_L_LimitPocket', 'X_EP_L_LEN - X_POCKET_X0 + CUT_EXT',
            'X_POCKET_Y1 - X_POCKET_Y0', 'X_POCKET_W',
            ['X_POCKET_X0', 'X_POCKET_Y0', 'X_POCKET_ZC - X_POCKET_W / 2'],
            op='cut', targets=[nm])

# ===========================================================================
# 3. Z 轴端板 L / R
# ===========================================================================
for tag, x0p, wp, y0p, dp, z0p, hp, mot_r, flank in (
        ('L', 'Z_EP_L_X0', 'Z_EP_L_W', 'Z_EP_L_Y0', 'Z_EP_L_D',
         'Z_EP_L_Z0', 'Z_EP_L_H', 'MOTOR_BORE_L_R', 'low'),
        ('R', 'Z_EP_R_X0', 'Z_EP_R_W', 'Z_EP_R_Y0', 'Z_EP_R_D',
         'Z_EP_R_Z0', 'Z_EP_R_H', 'MOTOR_BORE_R_R', 'high')):
    nm = 'Z_EndPlate_' + tag
    box('ZP_%s_Blank' % tag, wp, dp, hp, [x0p, y0p, z0p], body=nm)
    # L：法兰板在高端（贴型材 Z62）；R：法兰板在低端（贴型材 Z212）
    if flank == 'low':
        cav_z0, cav_h = z0p, '%s - FLANGE_T' % hp
        pad_z0 = '%s + %s - FLANGE_T - MOTOR_PAD_L' % (z0p, hp)
        belt_z0 = '%s + %s - BELT_SLOT_H' % (z0p, hp)
    else:
        cav_z0, cav_h = '%s + FLANGE_T' % z0p, '%s - FLANGE_T' % hp
        pad_z0 = '%s + FLANGE_T - OVL' % z0p
        belt_z0 = '%s - CUT_EXT' % z0p
    box('ZP_%s_FrameCavity' % tag, '%s - 2 * FRAME_WALL' % wp,
        '%s - 2 * FRAME_WALL' % dp, cav_h,
        ['%s + FRAME_WALL' % x0p, '%s + FRAME_WALL' % y0p, cav_z0],
        op='cut', targets=[nm])
    box('ZP_%s_MotorPad' % tag, 'MOTOR_PAD_W', 'MOTOR_PAD_H', 'MOTOR_PAD_L + OVL',
        ['Z_SLOT_XC - MOTOR_PAD_W / 2', 'Z_MOTOR_Y - MOTOR_PAD_H / 2', pad_z0],
        op='join', targets=[nm])
    cyl('ZP_%s_MotorBore' % tag, mot_r, '%s + 2 * CUT_EXT' % hp,
        ['Z_SLOT_XC', 'Z_MOTOR_Y', '%s - CUT_EXT' % z0p], 'Z', op='cut', targets=[nm])
    for i, xp in enumerate(('Z_ROD_X1', 'Z_ROD_X2'), 1):
        cyl('ZP_%s_RodBore%d' % (tag, i), 'ROD_HOLE_R', '%s + 2 * CUT_EXT' % hp,
            [xp, 'Z_ROD_Y', '%s - CUT_EXT' % z0p], 'Z', op='cut', targets=[nm])
    for i, xp in enumerate(('Z_ROD_X1', 'Z_ROD_X2'), 1):
        cyl('ZP_%s_MountHole%d' % (tag, i), 'MOUNT_R', '%s + 2 * CUT_EXT' % hp,
            [xp, 'Z_MOUNT_Y', '%s - CUT_EXT' % z0p], 'Z', op='cut', targets=[nm])
    box('ZP_%s_BeltSlot' % tag, '%s + 2 * CUT_EXT' % wp,
        '%s + %s - Z_PROF_Y0' % (y0p, dp), 'BELT_SLOT_H + CUT_EXT',
        ['%s - CUT_EXT' % x0p, 'Z_PROF_Y0', belt_z0], op='cut', targets=[nm])
    # L 端板专有：限位开关槽（冻结 22.00）
    if tag == 'L':
        box('ZP_L_LimitSlot', 'Z_SLOT_W', 'Z_SLOT_Y1 - Z_SLOT_Y0',
            '%s + %s - Z_SLOT_Z0 + CUT_EXT' % (z0p, hp),
            ['Z_SLOT_XC - Z_SLOT_W / 2', 'Z_SLOT_Y0', 'Z_SLOT_Z0'],
            op='cut', targets=[nm])

# ===========================================================================
# 4. 4 件滑车半体（X/Z 同构，参数共享）
# ===========================================================================
for axis_tag, car_a0, car_b0, lower_y0, upper_y0, rod_a1, rod_a2, rod_b, seat0, seat_len in (
        ('X', 'X_CAR_X0', 'X_CAR_Z0', 'X_CAR_LOWER_Y0', 'X_CAR_UPPER_Y0',
         'X_ROD_Z1', 'X_ROD_Z2', 'X_ROD_Y', 'X_SEAT_X0', 'SEAT_L'),
        ('Z', 'Z_CAR_X0', 'Z_CAR_Z0', 'Z_CAR_LOWER_Y0', 'Z_CAR_UPPER_Y0',
         'Z_ROD_X1', 'Z_ROD_X2', 'Z_ROD_Y', 'Z_SEAT_Z0', 'SEAT_L')):
    along_x = (axis_tag == 'X')
    upper_tp = 'CAR_T_UPPER' if along_x else 'CAR_T_UPPER_Z'
    for half, y0p, tp, cb_r, cb_d in (
            ('Lower', lower_y0, 'CAR_T_LOWER', 'CAR_CB_R_LOWER', 'CAR_CB_DEPTH_LOWER'),
            ('Upper', upper_y0, upper_tp, 'CAR_CB_R_UPPER', 'CAR_CB_DEPTH_UPPER')):
        nm = '%s_Carriage_%s' % (axis_tag, half)
        # 毛坯：沿运动轴 CAR_L，横向 CAR_SPAN，厚度 tp
        if along_x:
            box('CA_%s_%s_Blank' % (axis_tag, half), 'CAR_L', tp, 'CAR_SPAN',
                [car_a0, y0p, car_b0], body=nm)
        else:
            box('CA_%s_%s_Blank' % (axis_tag, half), 'CAR_SPAN', tp, 'CAR_L',
                [car_a0, y0p, car_b0], body=nm)
        corner_fillet(nm)

        # 阶梯轴承座：导入段 R4.70 / 主座 R6.05×19.20 / 出口段 R5.10
        pilot_len = '%s - %s' % (seat0, car_a0 if along_x else car_b0)
        exit_len = '%s + CAR_L - %s - %s' % (
            car_a0 if along_x else car_b0, seat0, seat_len)
        for i, rp in enumerate((rod_a1, rod_a2), 1):
            if along_x:
                base_p = [car_a0, rod_b, rp]
                base_s = [seat0, rod_b, rp]
                base_e = ['%s + %s' % (seat0, seat_len), rod_b, rp]
                ax = 'X'
            else:
                base_p = [rp, rod_b, car_b0]
                base_s = [rp, rod_b, seat0]
                base_e = [rp, rod_b, '%s + %s' % (seat0, seat_len)]
                ax = 'Z'
            cyl('CA_%s_%s_Pilot%d' % (axis_tag, half, i), 'PILOT_R', pilot_len,
                base_p, ax, op='cut', targets=[nm])
            cyl('CA_%s_%s_Seat%d' % (axis_tag, half, i), 'SEAT_R', seat_len,
                base_s, ax, op='cut', targets=[nm])
            cyl('CA_%s_%s_Exit%d' % (axis_tag, half, i), 'EXIT_R', exit_len,
                base_e, ax, op='cut', targets=[nm])

        # 2 × M3 合拢孔（沿 Y 贯穿）+ 沉孔
        # X 滑车：孔沿运动轴 X 变化(144/156)，横向 Z 固定 137
        # Z 滑车：孔沿运动轴 Z 变化(131/143)，横向 X 固定 150
        if along_x:
            m3_xs = ['%s + CAR_L / 2 - CAR_M3_PITCH / 2' % car_a0,
                     '%s + CAR_L / 2 + CAR_M3_PITCH / 2' % car_a0]
            m3_z = '%s + CAR_SPAN / 2' % car_b0
            m3_xz = [(x, m3_z) for x in m3_xs]
            belt_a = '%s + CAR_L / 2 - CAR_BELT_W / 2' % car_a0
            belt_b = '%s + CAR_SPAN / 2 - CAR_BELT_W / 2' % car_b0
        else:
            m3_x = '%s + CAR_SPAN / 2' % car_a0
            m3_zs = ['%s + CAR_L / 2 - CAR_M3_PITCH / 2' % car_b0,
                     '%s + CAR_L / 2 + CAR_M3_PITCH / 2' % car_b0]
            m3_xz = [(m3_x, z) for z in m3_zs]
            belt_a = '%s + CAR_SPAN / 2 - CAR_BELT_W / 2' % car_a0
            belt_b = '%s + CAR_L / 2 - CAR_BELT_W / 2' % car_b0
        # 先两通孔、再两沉孔：符合加工逻辑，也避免沉孔空腔先出现后
        # 再去料触发 OCC "cavity ownership is ambiguous"。
        for i, (mx, mz) in enumerate(m3_xz, 1):
            cyl('CA_%s_%s_M3Through%d' % (axis_tag, half, i), 'CAR_M3_R',
                '%s + 2 * CUT_EXT' % tp,
                [mx, '%s - CUT_EXT' % y0p, mz], 'Y', op='cut', targets=[nm])
        # 沉孔刀具必须越过本体外表面起刀（base = y0 - CUT_EXT），
        # 否则刀具底面与本体外表面共面，OCC 会生成第 2 个内部壳；
        # 高度同步 +CUT_EXT，保证沉孔底面 y0 + cb_d 不变。
        for i, (mx, mz) in enumerate(m3_xz, 1):
            cyl('CA_%s_%s_M3Cbore%d' % (axis_tag, half, i), cb_r,
                '%s + CUT_EXT' % cb_d,
                [mx, '%s - CUT_EXT' % y0p, mz], 'Y', op='cut', targets=[nm])
        # 中央皮带让位腔（浅，避开 M3 孔）
        if along_x:
            bl, bw, bh = 'CAR_BELT_W', 'CAR_BELT_D + CUT_EXT', 'CAR_BELT_W'
            if half == 'Lower':
                bc = [belt_a, '%s + %s - CAR_BELT_D' % (lower_y0, 'CAR_T_LOWER'), belt_b]
            else:
                bc = [belt_a, '%s - CUT_EXT' % upper_y0, belt_b]
        else:
            bl, bw, bh = 'CAR_BELT_W', 'CAR_BELT_D + CUT_EXT', 'CAR_BELT_W'
            if half == 'Lower':
                bc = [belt_a, '%s + %s - CAR_BELT_D' % (lower_y0, 'CAR_T_LOWER'), belt_b]
            else:
                bc = [belt_a, '%s - CUT_EXT' % upper_y0, belt_b]
        box('CA_%s_%s_BeltRelief' % (axis_tag, half), bl, bw, bh, bc,
            op='cut', targets=[nm])

# ===========================================================================
# 5. 2 根 2040 铝型材（外廓 + 4 条 T 槽）
# ===========================================================================
box('PF_X_Blank', 'X_PROF_LEN', 'X_PROF_W', 'X_PROF_H',
    ['X_PROF_X0', 'X_PROF_Y0', 'X_PROF_Z0'], body='X_Profile')
x_slot_y = 'X_PROF_Y0 + X_PROF_W / 2 - PROF_SLOT_W / 2'
x_slot_z = 'X_PROF_Z0 + X_PROF_H / 2 - PROF_SLOT_W / 2'
box('PF_X_TSlotTop', 'X_PROF_LEN + 2 * CUT_EXT', 'PROF_SLOT_W', 'PROF_SLOT_D + CUT_EXT',
    ['X_PROF_X0 - CUT_EXT', x_slot_y, 'X_PROF_Z0 + X_PROF_H - PROF_SLOT_D'],
    op='cut', targets=['X_Profile'])
box('PF_X_TSlotBot', 'X_PROF_LEN + 2 * CUT_EXT', 'PROF_SLOT_W', 'PROF_SLOT_D + CUT_EXT',
    ['X_PROF_X0 - CUT_EXT', x_slot_y, 'X_PROF_Z0 - CUT_EXT'],
    op='cut', targets=['X_Profile'])
box('PF_X_TSlotLeft', 'X_PROF_LEN + 2 * CUT_EXT', 'PROF_SLOT_D + CUT_EXT', 'PROF_SLOT_W',
    ['X_PROF_X0 - CUT_EXT', 'X_PROF_Y0 - CUT_EXT', x_slot_z],
    op='cut', targets=['X_Profile'])
box('PF_X_TSlotRight', 'X_PROF_LEN + 2 * CUT_EXT', 'PROF_SLOT_D + CUT_EXT', 'PROF_SLOT_W',
    ['X_PROF_X0 - CUT_EXT', 'X_PROF_Y0 + X_PROF_W - PROF_SLOT_D', x_slot_z],
    op='cut', targets=['X_Profile'])
cyl('PF_X_Core', 'PROF_CORE_D / 2', 'X_PROF_LEN + 2 * CUT_EXT',
    ['X_PROF_X0 - CUT_EXT', 'X_PROF_Y0 + X_PROF_W / 2', 'X_PROF_Z0 + X_PROF_H / 2'],
    'X', op='cut', targets=['X_Profile'])

box('PF_Z_Blank', 'Z_PROF_W', 'Z_PROF_D', 'Z_PROF_LEN',
    ['Z_PROF_X0', 'Z_PROF_Y0', 'Z_PROF_Z0'], body='Z_Profile')
z_slot_x = 'Z_PROF_X0 + Z_PROF_W / 2 - PROF_SLOT_W / 2'
z_slot_y = 'Z_PROF_Y0 + Z_PROF_D / 2 - PROF_SLOT_W / 2'
zh = 'Z_PROF_LEN + 2 * CUT_EXT'
box('PF_Z_TSlotXHi', 'PROF_SLOT_D + CUT_EXT', 'PROF_SLOT_W', zh,
    ['Z_PROF_X0 + Z_PROF_W - PROF_SLOT_D', z_slot_y, 'Z_PROF_Z0 - CUT_EXT'],
    op='cut', targets=['Z_Profile'])
box('PF_Z_TSlotXLo', 'PROF_SLOT_D + CUT_EXT', 'PROF_SLOT_W', zh,
    ['Z_PROF_X0 - CUT_EXT', z_slot_y, 'Z_PROF_Z0 - CUT_EXT'],
    op='cut', targets=['Z_Profile'])
box('PF_Z_TSlotYHi', 'PROF_SLOT_W', 'PROF_SLOT_D + CUT_EXT', zh,
    [z_slot_x, 'Z_PROF_Y0 + Z_PROF_D - PROF_SLOT_D', 'Z_PROF_Z0 - CUT_EXT'],
    op='cut', targets=['Z_Profile'])
box('PF_Z_TSlotYLo', 'PROF_SLOT_W', 'PROF_SLOT_D + CUT_EXT', zh,
    [z_slot_x, 'Z_PROF_Y0 - CUT_EXT', 'Z_PROF_Z0 - CUT_EXT'],
    op='cut', targets=['Z_Profile'])
cyl('PF_Z_Core', 'PROF_CORE_D / 2', 'Z_PROF_LEN + 2 * CUT_EXT',
    ['Z_PROF_X0 + Z_PROF_W / 2', 'Z_PROF_Y0 + Z_PROF_D / 2', 'Z_PROF_Z0 - CUT_EXT'],
    'Z', op='cut', targets=['Z_Profile'])

# ===========================================================================
# 6. 4 根 Ø6 导杆 + 4 个 LM6UU 轴承
# ===========================================================================
for i, zp in enumerate(('X_ROD_Z1', 'X_ROD_Z2'), 1):
    cyl('X_Rod%d' % i, 'ROD_D / 2', 'ROD_X_LEN',
        ['X_ROD_X0', 'X_ROD_Y', zp], 'X', body='X_GuideRod_%d' % i)
for i, xp in enumerate(('Z_ROD_X1', 'Z_ROD_X2'), 1):
    cyl('Z_Rod%d' % i, 'ROD_D / 2', 'ROD_Z_LEN',
        [xp, 'Z_ROD_Y', 'Z_ROD_Z0'], 'Z', body='Z_GuideRod_%d' % i)

for i, zp in enumerate(('X_ROD_Z1', 'X_ROD_Z2'), 1):
    nm = 'X_LM6UU_%d' % i
    base = ['X_SEAT_X0', 'X_ROD_Y', zp]
    cyl('X_Brg%d_Outer' % i, 'BRG_OD / 2', 'BRG_L', base, 'X', body=nm)
    cyl('X_Brg%d_Bore' % i, 'BRG_ID / 2', 'BRG_L', base, 'X', op='cut', targets=[nm])
for i, xp in enumerate(('Z_ROD_X1', 'Z_ROD_X2'), 1):
    nm = 'Z_LM6UU_%d' % i
    base = [xp, 'Z_ROD_Y', 'Z_SEAT_Z0']
    cyl('Z_Brg%d_Outer' % i, 'BRG_OD / 2', 'BRG_L', base, 'Z', body=nm)
    cyl('Z_Brg%d_Bore' % i, 'BRG_ID / 2', 'BRG_L', base, 'Z', op='cut', targets=[nm])

# ===========================================================================
# 7. 外观 + 保存
# ===========================================================================
add('appearance.assign', name='PETG 异型结构件 / 端板',
    bodies=['X_EndPlate_L', 'X_EndPlate_R', 'Z_EndPlate_L', 'Z_EndPlate_R'],
    color=[232, 146, 62], pbr={'metallic': 0.0, 'roughness': 0.45, 'dielectric_ior': 1.5})
add('appearance.assign', name='PETG 异型结构件 / 滑车',
    bodies=['X_Carriage_Lower', 'X_Carriage_Upper',
            'Z_Carriage_Lower', 'Z_Carriage_Upper'],
    color=[238, 168, 88], pbr={'metallic': 0.0, 'roughness': 0.45, 'dielectric_ior': 1.5})
add('appearance.assign', name='2040 铝型材',
    bodies=['X_Profile', 'Z_Profile'],
    color=[176, 183, 191], pbr={'metallic': 0.75, 'roughness': 0.35, 'dielectric_ior': 1.5})
add('appearance.assign', name='Ø6 导杆 轴承钢',
    bodies=['X_GuideRod_1', 'X_GuideRod_2', 'Z_GuideRod_1', 'Z_GuideRod_2'],
    color=[225, 228, 232], pbr={'metallic': 0.85, 'roughness': 0.22, 'dielectric_ior': 1.5})
add('appearance.assign', name='LM6UU 轴承钢',
    bodies=['X_LM6UU_1', 'X_LM6UU_2', 'Z_LM6UU_1', 'Z_LM6UU_2'],
    color=[90, 96, 106], pbr={'metallic': 0.9, 'roughness': 0.28, 'dielectric_ior': 1.5})
add('file.save', path=DESIGN, format='container', overwrite=True)

# ===========================================================================
# 8. 输出
# ===========================================================================
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump({'commands': cmds}, f, ensure_ascii=False, indent=1)

with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['分组', '参数名', '表达式', '说明', '核心参数', '生成方式'])
    for name, expr, group, note, fav in PARAMS:
        w.writerow([group, name, expr, note, '是' if fav else '',
                    'SolidCraft 原生 parameters.add'])

ALL_BODIES = [
    'X_EndPlate_L', 'X_EndPlate_R', 'Z_EndPlate_L', 'Z_EndPlate_R',
    'X_Carriage_Lower', 'X_Carriage_Upper', 'Z_Carriage_Lower', 'Z_Carriage_Upper',
    'X_Profile', 'Z_Profile',
    'X_GuideRod_1', 'X_GuideRod_2', 'Z_GuideRod_1', 'Z_GuideRod_2',
    'X_LM6UU_1', 'X_LM6UU_2', 'Z_LM6UU_1', 'Z_LM6UU_2',
]
verify = {'commands': [
    {'command': 'inspect.measure', 'params': {'items': [
        {'type': 'face', 'body': 'Z_EndPlate_L', 'point': [139.0, -21.2, 58.25]},
        {'type': 'face', 'body': 'Z_EndPlate_L', 'point': [161.0, -21.2, 58.25]}]}},
    {'command': 'inspect.measure', 'params': {'items': [
        {'type': 'face', 'body': 'X_EndPlate_L', 'point': [46.7, -76.275, 120.85]},
        {'type': 'face', 'body': 'X_EndPlate_L', 'point': [46.7, -76.275, 141.65]}]}},
    {'command': 'inspect.interference', 'params': {'bodies': ALL_BODIES, 'budget_s': 420}},
    {'command': 'parameters.list', 'params': {'filter': 'user'}},
]}
with open(OUT_VERIFY, 'w', encoding='utf-8') as f:
    json.dump(verify, f, ensure_ascii=False, indent=1)

# 注意：每次 parameters.change 都会重算整条时间线（约 70~90 个特征），
# 单脚本内堆 3 次改动会超过 300 s。拆成两个可在数分钟内跑完的只读脚本；
# 两者都用 --in 打开设计，不保存，所以不会改动交付的 LM6UU_Native.sc。
MEASURE_4 = {'command': 'inspect.measure', 'params': {'bodies': [
    'X_Carriage_Lower', 'X_GuideRod_1', 'X_EndPlate_L', 'X_LM6UU_1']}}
paramtest = {'commands': [
    MEASURE_4,
    {'command': 'parameters.change', 'params': {
        'name': 'SEAT_R', 'expression': 'BRG_OD / 2 + 0.35 mm'}},
    MEASURE_4,
]}
with open(OUT_PARAMTEST, 'w', encoding='utf-8') as f:
    json.dump(paramtest, f, ensure_ascii=False, indent=1)

paramtest2 = {'commands': [
    {'command': 'inspect.measure', 'params': {'bodies': [
        'X_Carriage_Lower', 'Z_EndPlate_L']}},
    {'command': 'parameters.change', 'params': {
        'name': 'X_CAR_Z0', 'expression': '114 mm'}},
    {'command': 'parameters.change', 'params': {
        'name': 'Z_SLOT_W', 'expression': '24 mm'}},
    {'command': 'inspect.measure', 'params': {'bodies': [
        'X_Carriage_Lower', 'Z_EndPlate_L']}},
    {'command': 'inspect.measure', 'params': {'items': [
        {'type': 'face', 'body': 'Z_EndPlate_L', 'point': [138.0, -21.2, 58.25]},
        {'type': 'face', 'body': 'Z_EndPlate_L', 'point': [162.0, -21.2, 58.25]}]}},
]}
with open(OUT_PARAMTEST2, 'w', encoding='utf-8') as f:
    json.dump(paramtest2, f, ensure_ascii=False, indent=1)

# 外观读回（只读）；与 refs/tmp/native_appear.json 内容一致，固化为交付脚本
with open(OUT_APPEAR, 'w', encoding='utf-8') as f:
    json.dump({'commands': [{'command': 'appearance.list', 'params': {}}]},
              f, ensure_ascii=False, indent=1)

from collections import Counter
c = Counter(x['command'] for x in cmds)
print('WROTE', OUT_JSON)
print('WROTE', OUT_CSV)
print('WROTE', OUT_VERIFY)
print('WROTE', OUT_PARAMTEST)
print('WROTE', OUT_PARAMTEST2)
print('WROTE', OUT_APPEAR)
print('commands', len(cmds), dict(c))
print('parameters', len(PARAMS))
print('NATIVE BUILD SCRIPT DONE')
