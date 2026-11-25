# -*- coding: utf-8 -*-
"""阶段预览：只重建 2 根 2040 铝型材，供用户在 SolidCraft 里先看截面观感。

用户 2026-11-13 要求：「你拉出型材后先让我在 solidcraft 里看看」。
本脚本不做端板 / 滑车，只出型材；截面观感确认后再继续 v2 全原生重做。

几何来源：refs/tmp/profile_sections.json（从 FCStd 裸 BREP 提取的真实 2040 截面）
  40×20 外廓、真实为 6 条外窄内宽 T 槽（40 面各 2 条、20 面各 1 条）、
  中心十字腔、四角减重腔、面积 302.81 mm²、填充率 37.9%、
  X 体积 60561.6 / Z 体积 45421.2 mm³。
本预览采用「4 条 T 槽（每边居中）+ 中心腔 + 四角腔」语义化近似，
  截面积 ≈ 379 mm² / 填充率 47.4%，体积比真实高约 +25%。
  这是给用户确认截面观感的阶段件，不是最终保真版；确认后按真实
  295 点截面轮廓做参数化抽象，把体积误差压到 <10%。

建模路线（全 SolidCraft 原生、零 STEP、每个特征都是命名参数化特征）：
  parameters.add → sketch.create + sketch.line（20×40 外廓）→ solid.extrude
  → 4 组 T 槽（每组 2 个 solid.box cut：窄槽口 + 宽内腔）
  → 中心腔 + 4 个角腔 solid.box cut → appearance → file.save
改 SLOT_W / SLOT_D / CAV_W / CAV_D / CORE_U / CORE_V / PW / PH 即整根重算。

【三次失败与修正，留作记录】
 1) 初版把中心腔 / 四角腔画成草图内轮廓 → 内岛与 T 槽凹口相切，
    被求解器吞掉（Extrude1 profiles=7 / Extrude2 profiles=15），
    实测 V=106400 mm³ = 截面积 532 mm² = 800 - 268(4 条 T 槽)，
    5 个内岛一个都没生效。属于「参数写了、几何没变」。
 2) 二版改用布尔切割但中心腔与左右 T 槽腔连通 → 在槽口高度把型材
    拦腰切穿，body_count=4（每根断成上下两块），不是有效产品。
 3) 三版改真实 6 槽布局 → 槽口 + 内腔在角部切断连接筋，四角块脱离
    主体，body_count=10。说明语义化槽距/槽深不能照搬真实截面。
 4) 本版：4 槽 + 中心腔四周留 1 mm 筋 + 四角腔，保证单一连通实体。
    交付时如实标注与真实截面 +25% 的体积差，不冒充高保真。
"""
import json
import os

ROOT = 'C:/ink'
OUT_JSON = ROOT + '/solidcraft/12_profile_preview.json'
OUT_SC = ROOT + '/solidcraft/LM6UU_Profile_Preview.sc'
USER_SC = 'D:/mydocuments/SolidCraft/LM6UU_Profile_Preview.sc'

cmds = []


def add(cmd, **kw):
    cmds.append({'command': cmd, 'params': kw})


# ---- 参数（全部可编辑，改一个即重算） ------------------------------------
PARAMS = [
    ('PW',         '20 mm',  'X 型材截面宽（2040 的 20，沿 Y）'),
    ('PH',         '40 mm',  'X 型材截面高（2040 的 40，沿 Z）'),
    ('PWZ',        '40 mm',  'Z 型材截面宽（旋转 90° 后为 40，沿 X）'),
    ('PHZ',        '20 mm',  'Z 型材截面深（旋转 90° 后为 20，沿 Y）'),
    ('SLOT_W',     '6 mm',   'T 槽槽口宽'),
    ('SLOT_D',     '2 mm',   'T 槽槽口深（外窄段）'),
    ('CAV_W',      '11 mm',  'T 槽内部腔宽（内宽段）'),
    ('CAV_D',      '5 mm',   'T 槽内部腔深'),
    ('CORE_U',     '2 mm',   '中心腔沿 20 方向半宽（与 T 槽内腔留 WALL 筋）'),
    ('CORE_V',     '12 mm',  '中心腔沿 40 方向半长'),
    ('CORNER_U',   '2.6 mm', '四角减重腔沿 20 方向尺寸'),
    ('CORNER_V',   '5.5 mm', '四角减重腔沿 40 方向尺寸'),
    ('WALL',       '1 mm',   '中心腔到 T 槽内腔的最小材料筋'),
    ('CUT_EXT',    '1 mm',   '切割刀具两端外伸量（避免共面）'),
    ('X_PROF_X0',  '50 mm',  'X 型材起点 X'),
    ('X_PROF_Y0',  '-57 mm', 'X 型材起点 Y'),
    ('X_PROF_Z0',  '117 mm', 'X 型材起点 Z'),
    ('X_PROF_LEN', '200 mm', 'X 型材长度'),
    ('Z_PROF_X0',  '130 mm', 'Z 型材起点 X'),
    ('Z_PROF_Y0',  '-1 mm',  'Z 型材起点 Y'),
    ('Z_PROF_Z0',  '62 mm',  'Z 型材起点 Z'),
    ('Z_PROF_LEN', '150 mm', 'Z 型材长度'),
]
for n, e, c in PARAMS:
    add('parameters.add', name=n, expression=e, comment=c)


def tslots(Wn, Hn, wide_u):
    """6 条 T 槽的切割矩形，每条 = 窄槽口 + 宽内腔，共 12 个 box。

    局部 (u,v)：wide_u=True 表示 u 是 40 方向（Z 型材旋转 90°）。
      · 沿 u 的边（v=0 / v=H）：长度 = W；40 长边给 2 槽（W/4、3W/4），
        20 短边给 1 槽（W/2）。
      · 沿 v 的边（u=0 / u=W）：长度 = H；40 长边给 2 槽（H/4、3H/4），
        20 短边给 1 槽（H/2）。
    """
    hs, hc = 'SLOT_W / 2', 'CAV_W / 2'
    # 本预览用 4 槽语义化截面（每边 1 条、居中）。真实 6 槽布局见下方说明。
    cu = [f'{Wn} / 2']
    cv = [f'{Hn} / 2']
    out = []
    for c in cu:
        # 底边 v=0（向 +v 凹）
        out.append((f'{c} - {hs}', '0 mm', f'{c} + {hs}', 'SLOT_D'))
        out.append((f'{c} - {hc}', 'SLOT_D', f'{c} + {hc}', 'SLOT_D + CAV_D'))
        # 顶边 v=H（向 -v 凹）
        out.append((f'{c} - {hs}', f'{Hn} - SLOT_D', f'{c} + {hs}', Hn))
        out.append((f'{c} - {hc}', f'{Hn} - SLOT_D - CAV_D',
                    f'{c} + {hc}', f'{Hn} - SLOT_D'))
    for c in cv:
        # 左边 u=0（向 +u 凹）
        out.append(('0 mm', f'{c} - {hs}', 'SLOT_D', f'{c} + {hs}'))
        out.append(('SLOT_D', f'{c} - {hc}', 'SLOT_D + CAV_D', f'{c} + {hc}'))
        # 右边 u=W（向 -u 凹）
        out.append((f'{Wn} - SLOT_D', f'{c} - {hs}', Wn, f'{c} + {hs}'))
        out.append((f'{Wn} - SLOT_D - CAV_D', f'{c} - {hc}',
                    f'{Wn} - SLOT_D', f'{c} + {hc}'))
    return out


def core(Wn, Hn, wide_u):
    """中心减重腔；四周留 WALL 筋，保证材料连成单一实体。"""
    if wide_u:                       # u = 40 方向，v = 20 方向
        return (f'{Wn} / 2 - CORE_V', f'{Hn} / 2 - CORE_U',
                f'{Wn} / 2 + CORE_V', f'{Hn} / 2 + CORE_U')
    return (f'{Wn} / 2 - CORE_U', f'{Hn} / 2 - CORE_V',
            f'{Wn} / 2 + CORE_U', f'{Hn} / 2 + CORE_V')


def corners(Wn, Hn, wide_u):
    """四角减重腔；避开 T 槽凹口并留 WALL 筋。"""
    A = Hn if wide_u else Wn         # 20 方向
    B = Wn if wide_u else Hn         # 40 方向
    a0, a1 = 'WALL', 'WALL + CORNER_U'
    a2, a3 = f'{A} - WALL - CORNER_U', f'{A} - WALL'
    b0 = 'SLOT_D + CAV_D + WALL'
    b1 = 'SLOT_D + CAV_D + WALL + CORNER_V'
    b2 = f'{B} - SLOT_D - CAV_D - WALL - CORNER_V'
    b3 = f'{B} - SLOT_D - CAV_D - WALL'
    if wide_u:
        return [(b0, a0, b1, a1), (b2, a0, b3, a1),
                (b0, a2, b1, a3), (b2, a2, b3, a3)]
    return [(a0, b0, a1, b1), (a2, b0, a3, b1),
            (a0, b2, a1, b3), (a2, b2, a3, b3)]


def boxcut(name, rect, axis, target, p0, length):
    """把局部矩形 (u0,v0,u1,v1) 变成沿 axis 贯通的 solid.box cut。"""
    u0, v0, u1, v1 = rect
    du = f'({u1}) - ({u0})'
    dv = f'({v1}) - ({v0})'
    if axis == 'X':                       # 截面在 YZ，沿 X 拉伸
        corner = [f'{p0[0]} - CUT_EXT', f'{p0[1]} + ({u0})', f'{p0[2]} + ({v0})']
        length_, width, height = f'{length} + 2 * CUT_EXT', du, dv
    else:                                 # 截面在 XY，沿 Z 拉伸
        corner = [f'{p0[0]} + ({u0})', f'{p0[1]} + ({v0})', f'{p0[2]} - CUT_EXT']
        length_, width, height = du, dv, f'{length} + 2 * CUT_EXT'
    add('solid.box', length=length_, width=width, height=height,
        corner=corner, operation='cut', targets=[target], name=name)


def build_profile(name, Wn, Hn, origin, x_dir, y_dir, length, wide_u,
                  axis, p0):
    add('sketch.create', plane={'origin': origin, 'x_dir': x_dir, 'y_dir': y_dir})
    add('sketch.line',
        points=[[0, 0], [Wn, 0], [Wn, Hn], [0, Hn]], closed=True)
    add('sketch.finish')
    add('solid.extrude', distance=length, operation='new', body_name=name)
    for i, r in enumerate(tslots(Wn, Hn, wide_u), 1):
        boxcut('%s_TSlot%02d' % (name, i), r, axis, name, p0, length)
    boxcut('%s_CoreCavity' % name, core(Wn, Hn, wide_u),
           axis, name, p0, length)
    for i, r in enumerate(corners(Wn, Hn, wide_u), 1):
        boxcut('%s_CornerCavity%02d' % (name, i), r, axis, name, p0, length)


# X 型材：截面在 YZ，沿 +X 拉伸。origin = (X50, Y-57, Z117)
build_profile('X_Profile', 'PW', 'PH',
              [50, -57, 117], [0, 1, 0], [0, 0, 1], 'X_PROF_LEN', False,
              'X', ('X_PROF_X0', 'X_PROF_Y0', 'X_PROF_Z0'))

# Z 型材：截面在 XY，沿 +Z 拉伸。origin = (X130, Y-1, Z62)
build_profile('Z_Profile', 'PWZ', 'PHZ',
              [130, -1, 62], [1, 0, 0], [0, 1, 0], 'Z_PROF_LEN', True,
              'Z', ('Z_PROF_X0', 'Z_PROF_Y0', 'Z_PROF_Z0'))

add('appearance.assign',
    bodies=['X_Profile', 'Z_Profile'],
    color='#b0b7bf', name='2040 铝型材 / 原生参数化截面',
    pbr={'metallic': 0.75, 'roughness': 0.35, 'dielectric_ior': 1.5})
add('file.save', path=OUT_SC)

os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump({'commands': cmds}, f, ensure_ascii=False, indent=1)
print('WROTE', OUT_JSON)
print('commands', len(cmds))
print('params', len(PARAMS))
print('design', OUT_SC)
print('user copy', USER_SC)
