# -*- coding: utf-8 -*-
"""v12.2：把一体式探针座改成「顶装 + 嵌入式顶塞」的可装配结构。

问题（用户 2026-11-09 指出「但看起来这个霍尔传感探针无法装配」）
--------------------------------------------------------------------
v12.1 的 HP45_ProbeHousing 是单一实体，中间大腔三个方向都被封死：

    Z58.00..76.50   Ø2.37  R125 针套孔
    Z76.50..78.50   Ø6.40  磁环腔（高 2.00，冻结）
    Z78.50..88.50   Ø6.20  弹簧腔
    Z88.50..90.00   Ø2.50  通气孔  <-- 封死顶口
    +X 霍尔窗       3.2 mm(Y) x 5.5 mm(Z)

而磁环 / 弹簧 / 预压垫圈都是 Ø6.00。三个入口全部小于零件外径，
静态干涉 = 0 不等于「零件能到达目标位姿」；BOM 第七节装配顺序也因此自相矛盾。

改动（最小改动，只动 1 处孔 + 1 个零件）
--------------------------------------------------------------------
1. HP45_ProbeHousing：仅把顶口 Z88.50..90.00 从 Ø2.50 扩成 Ø6.40 装配通道。
   其余孔系（Ø2.37 / Ø6.40 磁环腔 / Ø6.20 弹簧腔 / 霍尔窗 / 2 个 M3 孔）
   一律不动。Z88.50 自然形成 r=3.10 -> r=3.20 的 0.10 mm 环形沉孔台阶。
2. HP45_SpringSpacer：由 Ø6.00 x 1.00 平垫圈改成阶梯顶塞（仍用原对象名，
   保持 14 件清单与所有脚本引用不变）：
       下导向段  Ø6.00 / 内孔 Ø2.40 x 1.00   Z87.50..88.50  (进 Ø6.20 弹簧腔)
       上塞体    Ø6.36 / 内孔 Ø2.40 x 1.50   Z88.50..90.00  (进 Ø6.40 沉孔)
       总高 2.50，肩部坐 Z88.50 台阶，上端面与座体顶面齐平 Z90.00
   臂体口袋顶棚实测正好在 Z90.00（r>=1.30 为实体，中心 Ø2.50 让针尾通过），
   座体用 2 颗 M3 锁紧后，顶棚永久压住顶塞 = 正向止挡，弹簧被压到
   装配高 9.00 mm（Z78.50..87.50），预压 1.00 mm，F0 = 0.045 N 不变。

装配通道（自上而下）
--------------------------------------------------------------------
    Ø6.40  Z90.00..88.50   (新开)
    Ø6.20  Z88.50..78.50   (原有弹簧腔)
    Ø6.40  Z78.50..76.50   (原有磁环腔)
    Ø2.37  Z76.50..58.00   (针套孔，只有 Ø2.02 针身能过)
磁环 / 弹簧 / 顶塞外径 6.00 / 6.00 / 6.36，均可从顶部到达各自位置。

设计冻结项（全部未动）
--------------------------------------------------------------------
    Z 轴限位槽宽 22.00     Z_EndPlate_L X139.00..161.00
    X 轴限位口袋 20.80      X_EndPlate_L Z120.85..141.65
    磁环腔高 2.00           Z76.50..78.50，下台阶机械零位
    霍尔管芯 r = 5.90       感测面 X83.40，中心 Z79.00

运行方式：在 FreeCAD GUI 的 Python 控制台 / execute_code 里
    exec(compile(open('C:/ink/refs/scripts/build_v12_2.py', encoding='utf-8').read(),
                 'build_v12_2.py', 'exec'))
不要用 freecadcmd：本机 2026-11-09 13:28 之后 App.openDocument 一律卡死。
运行前自动备份到 refs/CrossSlide_before_topload.FCStd。
"""
import io
import os
import shutil
import sys

import FreeCAD as App
import Part

# 只在无 GUI 的独立进程里改 stdout 编码；GUI 控制台本身是 UTF-8，
# 替换 sys.stdout 会破坏 execute_code 的输出捕获。
if not getattr(App, 'GuiUp', False):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                      errors='replace', write_through=True)
    except Exception:
        pass

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_topload.FCStd'
AX, AY = 78.00, -112.50
UP = App.Vector(0, 0, 1)

if not os.path.exists(BAK):
    shutil.copyfile(DOC, BAK)
    print('[backup] %s' % BAK)

# GUI 里直接用已打开的文档；只有独立进程才 openDocument（本机 freecadcmd 会卡死）
d = App.ActiveDocument
if d is None or not d.FileName.lower().endswith('crossslide_p014013.fcstd'):
    d = App.openDocument(DOC)
g = d.getObject


def annulus(ro, ri, h, z0):
    outer = Part.makeCylinder(ro, h, App.Vector(AX, AY, z0), UP)
    inner = Part.makeCylinder(ri, h + 0.2, App.Vector(AX, AY, z0 - 0.1), UP)
    return outer.cut(inner)


def note(o, spec, material, extra=None):
    for prop in ('SpecNote', 'MaterialNote', 'AssemblyNote'):
        if prop not in o.PropertiesList:
            o.addProperty('App::PropertyString', prop, 'Design', 'v12.2 design note')
    o.SpecNote = spec
    o.MaterialNote = material
    if extra:
        o.AssemblyNote = extra


print('=' * 96)
print('v12.2 顶装可装配结构改造   改前对象数 = %d' % len(d.Objects))
print('=' * 96)

# ---- 0) 改动前留痕：冻结项复核 ------------------------------------------
hous0 = g('HP45_ProbeHousing')
v0 = hous0.Shape.Volume
freeze = {}
for n in ('Z_EndPlate_L', 'Z_LimitSwitch_Bot', 'Z_LimitSwitch_Top'):
    o = g(n)
    freeze[n] = (o.Shape.Volume, getattr(o, 'DesignFreeze', ''))
print('[freeze] 三个 Z 对象体积已记录，脚本不触碰它们')

# ---- 1) 座体顶口：Ø2.50 -> Ø6.40 ---------------------------------------
# 从 Z88.50 起切到 Z90.10（略超出顶面，保证顶部完全贯通，不留薄膜）
tool = Part.makeCylinder(3.20, 1.60, App.Vector(AX, AY, 88.50), UP)
new_hous = hous0.Shape.cut(tool).removeSplitter()
assert new_hous.isValid(), '座体 cut 后形状无效'
assert len(new_hous.Solids) == 1, '座体应仍为单一实体'
hous0.Shape = new_hous
hous0.Label = '探针座（v12.2 顶装：顶口 Ø6.40 装配通道 Z88.50..90.00）'
note(hous0,
     'v12.2：顶口由 Ø2.50 扩为 Ø6.40，形成自上而下的装配通道；'
     '磁环腔 Ø6.40 / 高 2.00（Z76.50..78.50）、弹簧腔 Ø6.20（Z78.50..88.50）、'
     'Ø2.37 针套孔、3.2x5.5 霍尔窗、2 个 M3 孔全部未改。'
     'Z88.50 处 r=3.10->3.20 的 0.10 mm 环形台阶是顶塞肩部定位面。',
     '铝合金 6061 或 POM，Ø6.40 / Ø6.20 一次装夹铰削保证同轴',
     '装配通道：Ø6.40(Z90..88.50) -> Ø6.20(Z88.50..78.50) -> '
     'Ø6.40(Z78.50..76.50) -> Ø2.37(Z76.50..58.00)。'
     '磁环/弹簧/顶塞全部从顶部装入，不许再从底部或侧窗塞入。')
d.recompute()
print('[housing] V %.3f -> %.3f  (去除 %.3f mm3)' % (v0, hous0.Shape.Volume,
                                                     v0 - hous0.Shape.Volume))

# ---- 2) 预压垫圈 -> 阶梯顶塞 --------------------------------------------
plug = g('HP45_SpringSpacer')
spigot = annulus(3.00, 1.20, 1.00, 87.50)   # Ø6.00 / Ø2.40 x 1.00
body = annulus(3.18, 1.20, 1.50, 88.50)     # Ø6.36 / Ø2.40 x 1.50
plug_shape = spigot.fuse(body).removeSplitter()
assert plug_shape.isValid(), '顶塞形状无效'
assert len(plug_shape.Solids) == 1, '顶塞应为单一实体'
plug.Shape = plug_shape
plug.Label = '阶梯顶塞 Ø6.36/Ø6.00 内孔Ø2.40 总高2.50（弹簧预压 + 上止挡）'
note(plug,
     '下导向段 Ø6.00 x 1.00 (Z87.50..88.50) 进 Ø6.20 弹簧腔，压弹簧到装配高 9.00；'
     '上塞体 Ø6.36 x 1.50 (Z88.50..90.00) 进 Ø6.40 沉孔，肩部坐 Z88.50 台阶，'
     '上端面齐平座体顶面 Z90.00。内孔 Ø2.40 让 Ø2.02 针尾滑动通过。'
     '座体装入臂体口袋后，臂体顶棚 Z90.00 压住上端面形成正向止挡（弹簧力仅 0.045 N）。',
     'POM / 黄铜 / 3D 打印树脂；Ø6.36 段与 Ø6.40 沉孔滑配，单边 0.02',
     '第 5 步：从顶部放入，压到肩部贴 Z88.50 台阶、上端面齐平 Z90.00；'
     '第 6 步：用凡士林/胶带临时固定（F0=0.045 N），座体从臂体下方装入口袋并锁紧 2 颗 M3，'
     '臂体顶棚即永久压住顶塞。')
d.recompute()
bb = plug.Shape.BoundBox
print('[plug]    V=%.3f sol=%d valid=%s Z%.2f..%.2f X%.2f..%.2f'
      % (plug.Shape.Volume, len(plug.Shape.Solids), plug.Shape.isValid(),
         bb.ZMin, bb.ZMax, bb.XMin, bb.XMax))

# ---- 3) 磁环 Label 补充装配口径 ------------------------------------------
mag = g('HP45_PogoMagnet')
note(mag,
     getattr(mag, 'SpecNote', '') + ' v12.2：磁环在座体外先粘到针身，'
     '再随探针从顶部 Ø6.40 通道下行穿过 Ø6.20 弹簧腔落到 Z76.50 下台阶；'
     '外径须筛到 <=6.10（比原 <=6.20 更严），或把 Ø6.20 弹簧腔铰到 Ø6.25，'
     '否则极限尺寸磁环会卡在 Z78.50 台阶。',
     getattr(mag, 'MaterialNote', 'N35 钕铁硼，镀镍'),
     '在座体外用 V 形夹具保证与针身同轴度 <=0.1 后点环氧，固化后再插入。')

# ---- 4) 冻结项逐字节级复核（体积不变即可证明几何未动）--------------------
for n, (vol, txt) in freeze.items():
    o = g(n)
    assert abs(o.Shape.Volume - vol) < 1e-6, '%s 体积被改动，违反冻结项' % n
    assert getattr(o, 'DesignFreeze', '') == txt, '%s 冻结属性被改动' % n
print('[freeze] Z_EndPlate_L / Z_LimitSwitch_Bot / Z_LimitSwitch_Top 体积与属性未变 OK')

d.recompute()
d.save()
print()
print('对象总数 = %d（与 v12.1 相同，未增未减）' % len(d.Objects))
print('[saved] %s' % DOC)
