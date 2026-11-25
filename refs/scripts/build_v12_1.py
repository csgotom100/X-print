# -*- coding: utf-8 -*-
"""v12.1：完善 FreeCAD 探针总成结构（磁环腔高 2.00 保持不变）。

用户指令「不改了，你先完善freecad里的结构」——即不把磁环腔高从 2.00 改到 2.40
去迁就商家 ±0.2 公差，而是在现有腔体上补齐缺失的结构件。

[行程核验结论 test_v12_1.py]
  磁环腔 Z76.50..78.50 高 2.00，磁环厚 2.00，零位正好坐在下台阶上。
  dz = 0 .. +3.0 mm（探针被蛋面顶起）全程无干涉：磁环上移进入 Ø6.2 弹簧腔，
  dz < 0 会被 Ø2.46 针套孔台阶卡死。故本结构天然是「单向行程 + 机械零位」，
  磁环中心 Z77.50 -> 80.50，对应 z_rel = +1.5 -> -1.5，与磁路标定一致。

[本脚本做的事]
  1. 新增 HP45_DustSeal    防尘唇（毛毡/硅胶，粘在探针座底面）
  2. 新增 HP45_HallCover   霍尔盖板（压紧霍尔+PCB，Ø3.2 出线孔）
  3. 新增 HP45_CableClamp  出线护线套（Ø2.4 线孔，应变消除）
  4. 新增 HP45_SpringSpacer 弹簧预压垫圈（Z87.50..88.50，厚 1.00）
  5. HP45_PogoSpring 形状改为装配态 Z78.50..87.50（自由高 10.0 压到 9.0，预压 1.0 -> F0=0.045 N）
  6. HP45_PogoMagnet Label 口径修正为 Ø2.10 / 轴向（厚度）充磁
  7. 给新增件写 SpecNote / Material 自定义属性，模型自解释

所有新增件已由 test_v12_1.py 验证：与现有 147 对象零干涉、彼此零干涉、
全行程零干涉。运行前自动备份到 refs/CrossSlide_before_v12_1.FCStd。
"""
import io
import os
import shutil
import sys

import FreeCAD as App
import Part

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_v12_1.FCStd'
AX, AY = 78.00, -112.50
UP = App.Vector(0, 0, 1)

if not os.path.exists(BAK):
    shutil.copyfile(DOC, BAK)
    print('[backup] %s' % BAK)

d = App.openDocument(DOC)


def annulus(ro, ri, h, z0):
    outer = Part.makeCylinder(ro, h, App.Vector(AX, AY, z0), UP)
    inner = Part.makeCylinder(ri, h + 0.2, App.Vector(AX, AY, z0 - 0.1), UP)
    return outer.cut(inner)


def hole_x(plate, x0, dx, r, yc=AY, zc=79.00):
    return plate.cut(Part.makeCylinder(r, dx + 0.4,
                                       App.Vector(x0 - 0.2, yc, zc),
                                       App.Vector(1, 0, 0)))


def put(name, shape, label, note, material):
    o = d.getObject(name)
    if not o:
        o = d.addObject('Part::Feature', name)
    o.Shape = shape
    o.Label = label
    for prop in ('SpecNote', 'MaterialNote'):
        if prop not in o.PropertiesList:
            o.addProperty('App::PropertyString', prop, 'Design', 'v12.1 design note')
    o.SpecNote = note
    o.MaterialNote = material
    d.recompute()
    bb = o.Shape.BoundBox
    print('  %-22s V=%8.3f sol=%d valid=%s  X%.2f..%.2f Y%.2f..%.2f Z%.2f..%.2f'
          % (name, o.Shape.Volume, len(o.Shape.Solids), o.Shape.isValid(),
             bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    return o


print('=' * 96)
print('v12.1 结构完善（磁环腔 Z76.50..78.50 高 2.00 未改动）')
print('=' * 96)

# ---- 1) 先改弹簧为装配态，腾出 Z87.50..88.50 给垫圈 ----
sp = annulus(3.00, 2.30, 9.00, 78.50)
put('HP45_PogoSpring', sp,
    '轻弹簧 Ø6/Ø4.6/0.3x12圈 自由高10.0 装配高9.0 预压1.0 F0=0.045N',
    '装配态 Z78.50..87.50；自由高 10.00 mm，压到 9.00 mm 产生 1.00 mm 预压。'
    'k=0.045 N/mm -> F0=0.045 N，行程 +3.0 mm 时 F=0.180 N。'
    '并紧高度 3.60 mm，最大可用行程 5.40 mm > 3.00 mm。'
    '内部 P125 弹簧已环氧锁死，接触力全部由本外部弹簧提供。',
    '不锈钢琴钢丝 Ø0.3，12 圈，两端并紧磨平')

# ---- 2) 磁环 Label 口径修正（几何不动）----
mag = d.getObject('HP45_PogoMagnet')
mag.Label = '磁环 Ø6/内孔Ø2.10×厚2.00 轴向（厚度）充磁 N35 镀镍'
for prop in ('SpecNote', 'MaterialNote'):
    if prop not in mag.PropertiesList:
        mag.addProperty('App::PropertyString', prop, 'Design', 'v12.1 design note')
mag.SpecNote = ('内孔 2.10 套 P125 管身 Ø2.02，单边胶缝 0.04。'
                '商家 6*2*2轴向 公差 ±0.2：筛内孔 >=2.08、外径 <=6.20、'
                '不改模则厚度 <=2.00。轴向/厚度充磁，霍尔测 Bx 才单调。')
mag.MaterialNote = 'N35 钕铁硼，镀镍'
d.recompute()
print('  %-22s Label -> %s' % ('HP45_PogoMagnet', mag.Label))

# ---- 3) 四个新结构件 ----
dust = annulus(3.00, 1.05, 0.80, 57.20)
put('HP45_DustSeal', dust,
    '防尘唇 Ø6/内孔Ø2.10×0.80 毛毡/硅胶（粘于座底面 Z58.00）',
    '封住 R125 针套下端出口，阻挡蛋壳粉与墨雾进入 Ø2.10 导向孔。'
    'CAD 内孔按 Ø2.10 建模以免与 Ø2.02 针干涉；实物唇口取 Ø1.90 过盈贴针。'
    '全行程 +3.0 mm 时针尖升到 Z60.00，唇口短暂敞开，靠材料弹性自闭合。',
    '羊毛毡或邵氏 A30 硅胶，环氧/瞬干胶粘于探针座底面')

cover = hole_x(Part.makeBox(0.30, 5.00, 6.00,
                            App.Vector(85.50, -115.00, 76.50)),
               85.50, 0.30, 1.60)
put('HP45_HallCover', cover,
    '霍尔盖板 0.30×5.00×6.00 带 Ø3.2 出线孔（贴 X85.50 外壁）',
    '压紧 A1324 与转接 PCB，封闭霍尔窗 X81.00..85.50 / Z76.50..82.00。'
    '中央 Ø3.2 出线孔中心 (Y-112.50, Z79.00)。四周环氧封边，孔内灌胶密封。'
    '霍尔窗在 X81.00..83.40 尚余 2.40 mm，可塞 0.2/0.5 垫片把霍尔向 -X 移以微调 r'
    '（选配，不建模；r 变化须重新标定）。',
    'FR-4 薄片或 0.3 mm 铝片，环氧粘接')

clamp = hole_x(Part.makeBox(1.50, 4.00, 3.00,
                            App.Vector(85.80, -114.50, 77.50)),
               85.80, 1.50, 1.20)
put('HP45_CableClamp', clamp,
    '出线护线套 1.50×4.00×3.00 带 Ø2.4 线孔（应变消除）',
    '与盖板出线孔同轴 (Y-112.50, Z79.00)，把 A1324 的 Vcc/GND/Vout 三根引线'
    '约束成束并做应变消除，防止打印头往复运动时焊点疲劳断裂。'
    '贴盖板外侧 X85.80，环氧粘接或硅胶一体成型。',
    '硅胶或 TPU，邵氏 A50')

spacer = annulus(3.00, 1.20, 1.00, 87.50)
put('HP45_SpringSpacer', spacer,
    '弹簧预压垫圈 Ø6/内孔Ø2.40×1.00（坐通气孔台阶 Z88.50）',
    '把弹簧装配高从 10.00 压到 9.00，建立 1.00 mm 预压 = 0.045 N 接触力。'
    '上端面顶在 Ø6.2 弹簧腔 -> Ø2.5 通气孔的环形台阶上，内孔 Ø2.40 让 Ø2.02 针尾穿过。'
    '外径 Ø6.00 配弹簧腔 Ø6.20，单边 0.10。',
    'POM / 黄铜 / 3D 打印树脂，1.00 mm 厚')

# ---- 4) 探针座 Label 补充零位说明（几何不动）----
hous = d.getObject('HP45_ProbeHousing')
for prop in ('SpecNote',):
    if prop not in hous.PropertiesList:
        hous.addProperty('App::PropertyString', prop, 'Design', 'v12.1 design note')
hous.SpecNote = ('磁环腔 Z76.50..78.50 高 2.00 = 磁环零位下台阶机械限位，'
                 '禁止向下超程；探针只能被蛋面顶起 +Z 0..3.0 mm。'
                 '商家 ±0.2 公差靠筛选解决，腔高保持不变。')
d.recompute()

d.save()
print()
print('对象总数 = %d' % len(d.Objects))
print('[saved] %s' % DOC)
