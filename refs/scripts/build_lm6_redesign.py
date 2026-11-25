# -*- coding: utf-8 -*-
"""生成 SolidCraft 参数化命令脚本：LM6UU / Ø6 导杆改造（X+Z 两轴，独立新设计）。

用户口径：「不是重新设计整个项目，是因为直线轴承的更改，滑台两端的结构件
要重新设计，铝型材不变，滑车也要重新修改参数」；方案选择：
  保留上下两半 + M3 合拢 / 新建独立参数化设计 / X+Z 两轴全改。

设计保真策略（重要）
--------------------
* 8 件改动件的**真实几何**来自当前 FCStd（v13.2）的裸 BREP，接口 / 减重腔 /
  冻结槽位 100% 保真，不用方盒臆造。由 `build_lm6_geometry.py` 导出：
    - LM6UU_base6.step        6 件（2 个 Z 端板已预切 + 4 滑车未改）
    - LM6UU_xplates_lm6.step  2 件 X 端板（已预切 Ø6.10 导杆孔）
* SolidCraft 的 STEP 导入体布尔不稳：X_EndPlate_L/R 被丢掉 49 个面判为
  open body，开放体上布尔无限挂起（>165 s）；Z_EndPlate_R（93 面）上做细环形
  扩孔布尔 180 s 未返回，整段脚本第 41 步报
  `boolean Cut: the operation failed: no result`。FreeCAD 中 X 端板 cut 后调用
  removeSplitter() 也会退化成 invalid。故 **4 个端板的 8 处导杆孔全部在
  FreeCAD 侧预切**（X_EndPlate_L 的 Z122 孔另做 20.80 冻结口袋刀具遮罩），
  SolidCraft 中只对 4 个滑车半体做 **8 处实时参数化切除**（实测约 1.8 s/步，
  由 SEAT_R / SEAT_L 驱动），避免任何端板布尔。
* 4 根 Ø6 导杆、4 个 LM6UU 轴承是 SolidCraft 原生参数化实体（BRG_OD / BRG_ID /
  BRG_L / ROD_D），不是导入件。
* X_Profile / Z_Profile 铝型材以真几何 STEP 原样插入，明确不变。

输出：
  solidcraft/06_lm6_redesign.json   SolidCraft CLI 命令脚本
  solidcraft/LM6UU_PARAMS.csv       参数表（旧值 / 新值 / 依据）
  refs/tmp/lm6_build_manifest.json 生成清单
  solidcraft/LM6UU_Redesign.sc      由 06 脚本执行 file.save 生成

运行：
  solidcraft-cli run solidcraft/06_lm6_redesign.json \
      --results --json-out refs/tmp/lm6_stage1_results.json --param-check warn
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'solidcraft'

cmds: list[dict] = []
_seq = [0]


def add(command: str, **params):
    """命令参数一律用关键字传入；不要再给 add 一个位置 name 形参，
    否则 parameters.add / file.insert_step / appearance.assign 自带的
    name 字段会和它冲突（实测 TypeError: got multiple values for 'name'）。"""
    _seq[0] += 1
    cmds.append({'command': command, 'params': params})


def feature(prefix: str) -> str:
    _seq[0] += 1
    return f'{prefix}_{_seq[0]:03d}'


# ---------------------------------------------------------------- 参数表
# 表达式引用其它参数，改一个值 8 件改动件 + 4 根导杆 + 4 个轴承联动。
PARAMS = [
    ('BRG_OD',      '12 mm',                   'LM6UU 外径 Ø12'),
    ('BRG_ID',      '6 mm',                    'LM6UU 内孔 Ø6'),
    ('BRG_L',       '19 mm',                   'LM6UU 长度 19'),
    ('ROD_D',       '6 mm',                    '导杆 Ø6（原 Ø5）'),
    ('SEAT_R',      'BRG_OD / 2 + 0.05 mm',    '轴承座孔 R6.05（原 R5.00）'),
    ('SEAT_L',      'BRG_L + 0.2 mm',          '主座长 19.20（原 15.60）'),
    ('ROD_HOLE_R',  'ROD_D / 2 + 0.05 mm',     '端板导杆孔 R3.05（原 R2.75）'),
    ('PILOT_R',     '4.7 mm',                  '导入段 R4.70（不变，形成轴向挡肩）'),
    ('EXIT_R',      '5.1 mm',                  '出口段 R5.10（不变，形成轴向挡肩）'),
    ('M3_R',        '1.7 mm',                  'M3 合拢过孔 R1.70（不变）'),
    ('X_SEAT_X0',   '140.4 mm',                'X 轴主座起点'),
    ('Z_SEAT_Z0',   '127.4 mm',                'Z 轴主座起点'),
    ('ROD_X_LEN',   '215 mm',                  'X 导杆长度'),
    ('ROD_Z_LEN',   '165 mm',                  'Z 导杆长度'),
    ('Z_SLOT_W',    '22 mm',                   '【冻结】Z 轴限位槽宽'),
    ('X_POCKET_W',  '20.8 mm',                 '【冻结】X 轴限位口袋宽'),
]
for pname, expr, _ in PARAMS:
    add('parameters.add', name=pname, expression=expr)

PARAM_ROWS = [
    ('轴承外径',      'BRG_OD',     'Ø10.00', 'Ø12.00', 'LM6UU 外购件规格'),
    ('轴承内孔',      'BRG_ID',     'Ø5.00',  'Ø6.00',  'LM6UU 外购件规格'),
    ('轴承长度',      'BRG_L',      '15.00',  '19.00',  'LM6UU 外购件规格'),
    ('导杆直径',      'ROD_D',      'Ø5.00',  'Ø6.00',  '与 LM6UU 内孔配'),
    ('滑车主座半径',  'SEAT_R',     'R5.000', 'R6.050', '单边 0.05 装配间隙'),
    ('滑车主座长度',  'SEAT_L',     '15.60',  '19.20',  '轴承两端各留 0.10'),
    ('端板导杆孔',    'ROD_HOLE_R', 'R2.750', 'R3.050', '单边 0.05 装配间隙'),
    ('导入段半径',    'PILOT_R',    'R4.700', 'R4.700', '不变；< R6.05 形成前挡肩'),
    ('出口段半径',    'EXIT_R',     'R5.100', 'R5.100', '不变；< R6.05 形成后挡肩'),
    ('M3 合拢孔',     'M3_R',       'R1.700', 'R1.700', '不变；上下两半 + M3 合拢'),
    ('Z 限位槽宽',    'Z_SLOT_W',   '22.00',  '22.00',  '【冻结】用户明令不得改动'),
    ('X 限位口袋',    'X_POCKET_W', '20.80',  '20.80',  '【冻结】用户明令不得改动'),
    ('两轴承位中心距', '—',          '30.00',  '30.00',  '不变；X 为 Z122/152，Z 为 X135/165'),
    ('X 导杆长度',    'ROD_X_LEN',  '215.00', '215.00', '不变；X42.5..257.5'),
    ('Z 导杆长度',    'ROD_Z_LEN',  '165.00', '165.00', '不变；Z54.5..219.5'),
    ('铝型材',        '—',          '2040 ×2', '2040 ×2', '不变；真几何 STEP 原样插入'),
]

# ---------------------------------------------------------------- helpers
def cyl_cut(body: str, r, h, base, axis, tag: str):
    add('solid.cylinder', name=feature(tag), radius=r, height=h, base=list(base),
        axis=axis, operation='cut', targets=[body])


def cyl_new(body: str, r, h, base, axis, tag: str):
    add('solid.cylinder', name=feature(tag), radius=r, height=h, base=list(base),
        axis=axis, operation='new', body_name=body)


# ---------------------------------------------------------------- 原生参数化：4 根 Ø6 导杆
# 先建原生体，再 insert_step，避免新体被挂到某个导入组件下。
RODS = []
for i, zc in enumerate((122.0, 152.0), 1):
    n = f'X_GuideRod_{i}'
    RODS.append(n)
    cyl_new(n, 'ROD_D / 2', 'ROD_X_LEN', [42.5, -68.0, zc], 'X', f'X_Rod{i}')
for i, xc in enumerate((135.0, 165.0), 1):
    n = f'Z_GuideRod_{i}'
    RODS.append(n)
    cyl_new(n, 'ROD_D / 2', 'ROD_Z_LEN', [xc, -12.0, 54.5], 'Z', f'Z_Rod{i}')

# ---------------------------------------------------------------- 原生参数化：4 个 LM6UU
BEARINGS = []
BRG_SPEC = [
    ('X_LM6UU_1', [140.5, -68.0, 122.0], 'X'),
    ('X_LM6UU_2', [140.5, -68.0, 152.0], 'X'),
    ('Z_LM6UU_1', [135.0, -12.0, 127.5], 'Z'),
    ('Z_LM6UU_2', [165.0, -12.0, 127.5], 'Z'),
]
for name, base, ax in BRG_SPEC:
    BEARINGS.append(name)
    cyl_new(name, 'BRG_OD / 2', 'BRG_L', base, ax, f'{name}_Outer')
    cyl_cut(name, 'BRG_ID / 2', 'BRG_L', base, ax, f'{name}_Bore')

# ---------------------------------------------------------------- 插入真实几何
add('file.insert_step', name='LM6_Base6_Structural',
    path=str(OUT / 'LM6UU_base6.step').replace('\\', '/'), names='product')
add('file.insert_step', name='LM6_XEndPlates_Prebored',
    path=str(OUT / 'LM6UU_xplates_lm6.step').replace('\\', '/'), names='product')
add('file.insert_step', name='Aluminium_Profiles_UNCHANGED',
    path=str(OUT / 'LM6UU_reference_profiles.step').replace('\\', '/'),
    names='product')

STRUCTURAL = [
    'X_EndPlate_L', 'X_EndPlate_R', 'Z_EndPlate_L', 'Z_EndPlate_R',
    'X_Carriage_Lower', 'X_Carriage_Upper',
    'Z_Carriage_Lower', 'Z_Carriage_Upper',
]
PROFILES = ['X_Profile', 'Z_Profile']

# ---------------------------------------------------------------- 8 处滑车主座（实时参数化切除）
# 分型面 Y=-68（X 轴）/ Y=-12（Z 轴）上切整圆，上下两半各得一个半圆座。
for zc in (122.0, 152.0):
    for body in ('X_Carriage_Lower', 'X_Carriage_Upper'):
        cyl_cut(body, 'SEAT_R', 'SEAT_L',
                ['X_SEAT_X0', -68.0, zc], 'X',
                f'X_Seat_Z{int(zc)}_{"L" if body.endswith("Lower") else "U"}')
for xc in (135.0, 165.0):
    for body in ('Z_Carriage_Lower', 'Z_Carriage_Upper'):
        cyl_cut(body, 'SEAT_R', 'SEAT_L',
                [xc, -12.0, 'Z_SEAT_Z0'], 'Z',
                f'Z_Seat_X{int(xc)}_{"L" if body.endswith("Lower") else "U"}')

# ---------------------------------------------------------------- 端板导杆孔（全部 FreeCAD 预切）
# 8 处 Ø6.10 导杆孔（R2.75 -> R3.05）在 build_lm6_geometry.py 中用同一组参数
# 完成并写入 STEP。ROD_HOLE_R 仍保留在参数表 / CSV 中作为设计口径，
# 但不在这里重复布尔，避免 SolidCraft 导入体上的环形薄壁切除失败。
# X: LM6UU_xplates_lm6.step（X_EndPlate_L 的 Z122 孔带冻结口袋遮罩）
# Z: LM6UU_base6.step 内的 Z_EndPlate_L / Z_EndPlate_R

# ---------------------------------------------------------------- 外观
APPEAR = [
    ('PETG 异型结构件', [51, 140, 204], STRUCTURAL, 0.0, 0.48),
    ('铝型材 2040（不变）', [176, 183, 191], PROFILES, 0.75, 0.35),
    ('LM6UU 轴承钢', [90, 96, 106], BEARINGS, 0.90, 0.28),
    ('Ø6 导杆 轴承钢', [225, 228, 232], RODS, 0.85, 0.22),
]
for label, color, bodies, metallic, roughness in APPEAR:
    add('appearance.assign', name=label, bodies=bodies, color=color,
        pbr={'metallic': metallic, 'roughness': roughness,
             'dielectric_ior': 1.5})

# ---------------------------------------------------------------- save
add('file.save', path=str(OUT / 'LM6UU_Redesign.sc').replace('\\', '/'),
    format='container', overwrite=True)

# ---------------------------------------------------------------- outputs
script = {'commands': cmds}
(OUT / '06_lm6_redesign.json').write_text(
    json.dumps(script, ensure_ascii=False, indent=1), encoding='utf-8')

with (OUT / 'LM6UU_PARAMS.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['项目', '参数名', 'LM5UU 原值', 'LM6UU 新值', '依据 / 说明'])
    w.writerows(PARAM_ROWS)

manifest = {
    'design': 'solidcraft/LM6UU_Redesign.sc',
    'command_count': len(cmds),
    'parameters': len(PARAMS),
    'native_parametric_bodies': RODS + BEARINGS,
    'imported_true_geometry': STRUCTURAL + PROFILES,
    'live_parametric_cuts': {
        'carriage_half_seats': 8,
        'endplate_rod_bores_prebored_in_freecad': 8,
        'endplate_rod_bores_live_in_solidcraft': 0,
        'note': 'STEP 导入端板上的环形薄壁扩孔布尔会挂起/失败，故全部在 FreeCAD 侧预切',
    },
    'frozen': {'Z_SLOT_W': 22.0, 'X_POCKET_W': 20.8},
    'aluminium_profiles': 'unchanged; inserted as true geometry from LM6UU_reference_profiles.step',
    'geometry_report': 'refs/tmp/lm6_geometry_report.json (CONCLUSION PASS)',
}
(ROOT / 'refs/tmp/lm6_build_manifest.json').write_text(
    json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')

print('commands', len(cmds))
print('parameters', len(PARAMS))
print('bodies', len(STRUCTURAL + PROFILES + RODS + BEARINGS))
print('wrote', OUT / '06_lm6_redesign.json')
