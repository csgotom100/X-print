# -*- coding: utf-8 -*-
"""v13：探针总成主件改成可注塑成型结构（敞开 U 型腔 + 盖板 + 取消独立顶塞）。

用户 2026-11-09 确认的三项方案
--------------------------------------------------------------------
  1. 范围   = 探针总成主件：HP45_ProbeHousing 座体 + HP45_ProbeArm 臂体
  2. 路线   = 沿 X 分型的「敞开 U 型腔 + 盖板封腔」
  3. 顶塞   = 取消独立顶塞，弹簧止挡并入座体/盖板一体成型

为什么必须改（v12.2 的致命问题）
--------------------------------------------------------------------
  v12.2 座体是「沿 Z 轴的封闭阶梯圆孔」：
      Z58.00..76.50  Ø2.37 针套孔
      Z76.50..78.50  Ø6.40 磁环腔（高 2.00，冻结）
      Z78.50..88.50  Ø6.20 弹簧腔
      Z88.50..90.00  Ø6.40 顶装通道
  从 +Z 抽芯：顶口 Ø6.40 -> 弹簧腔 Ø6.20 收窄 -> 磁环腔 Ø6.40 胀大，
  Ø6.40 磁环腔被 Ø6.20 卡在下面 = 倒扣；从 -Z 抽芯底孔只有 Ø2.37，
  磁环腔完全过不去。**沿 Z 双向都抽不出芯，模具做不出来。**
  v12.2 解决的是「零件能从顶口塞进去」，不是「模具能成型」。

v13 的解法：把抽芯方向从 Z 改成 X
--------------------------------------------------------------------
  把 Z76.50..87.50 的封闭阶梯圆孔改成「从 -X 面敞开的阶梯 U 型槽」：
    * 槽沿 X 等截面（直壁），型芯从 -X 抽出，Z 向的 Ø6.40/Ø6.20 台阶
      变成平行于抽芯方向的直壁 —— 不再是倒扣，无需侧滑块。
    * Z87.50..90.00 保留座体一体成型的顶棚，中心 Ø2.50 通孔让针尾通过；
      顶棚底面 Z87.50 直接作弹簧上止挡 —— 独立顶塞彻底取消。
    * 一片盖板从 -X 侧封住槽口，内侧补形凸台把腔体收窄到 X75.00..81.20，
      使磁环/弹簧 Ø6.00 的定位间隙仍为 0.20（磁路气隙不变）。
    * +X 侧霍尔窗、霍尔传感器座、2×M3 孔、外形包络全部不动，
      冻结项 r=5.90 / X83.40 / Z79.00 / 磁环腔高 2.00 天然保持。

  装配顺序变为「侧装」：磁环/弹簧/探针从 -X 侧沿 +X 放入敞开槽
  -> 盖板扣合（凸台正好顶住零件左缘，无干涉）-> 2 处卡扣 + M3 固定。
  比 v12.2 的顶部塞入更简单，装配路径全程可达。

  其它 DFM 项（模具设计参数，写入 SpecNote / 图纸标注）
--------------------------------------------------------------------
  脱模斜度 1.5°、内角 R0.4、名义壁厚 2.0 mm（臂体顶板掏空减重）、
  Ø2.37 针套孔与 2×M3 孔为注塑后钻/铰或铜嵌件（细长孔不做型芯）。

  【v13.1 修正】盖板弹簧腔凸台的螺钉让位
  ------------------------------------------------------------------
  verify_v13 首跑查出盖板与 HP45_HousingScrew_0 干涉 1.2982 mm3。
  实测螺钉为阶梯件：头部 Ø6.00 (Z100..102)、杆部 Ø2.44 (Z84..100)，
  杆心 (74.00,-116.50)，杆外缘最远到 Y=-115.28；
  而弹簧腔凸台原 -Y 边在 Y=-115.60，故杆部 Z84..87.50 段啃进凸台
  0.32 mm（干涉包围盒 X73.169..74.831 / Y-115.600..-115.275 / Z84..87.50）。

  修正不用「圆柱让位孔」：沿 Z 的孔/凹弧对「沿 X 抽芯」是倒扣，需侧滑块或后铣。
  改为把凸台 -Y 边沿全高从 -115.60 退到 -114.90（退让 0.70）：
    * 凸台仍为等截面直棱柱，型芯沿 X 直抽，无侧滑块、无后加工；
    * 与杆部留 0.38 mm 间隙，覆盖注塑 ±0.1 公差与 1.5° 脱模斜度；
    * 凸台 +X 端面仍为 X75.00，磁环/弹簧的定位面不变，磁路尺寸不变。
  注：螺钉中心 (82.00,-108.50) 的 Screw_1 与盖板本就零干涉，无需再切。

实现通道说明
--------------------------------------------------------------------
  本机 FreeCAD 1.1 的 App.openDocument 在 13:28 之后一律卡死（GUI 与
  freecadcmd 都一样）。故本脚本完全绕开 openDocument：
    * 用 Part.Shape.read() 直接读 FCStd 压缩包内逐个 *.Shape.brp
    * 布尔运算生成新形状后用 exportBrep 写到 refs/tmp/v13out/
    * 由 writeback_v13.py 精确替换 zip 内 3 个 .brp 并更新 Document.xml
  除这 3 个对象外，其余 148 个对象的几何与全部非几何条目原字节不动。

运行：freecadcmd refs/scripts/build_v13.py   （只产出 BREP，不改主文档）
"""
import os
import sys
import FreeCAD as App
import Part

# Windows 控制台 GBK 无法编码 Ø；print 抛异常会终止整个 freecadcmd 脚本。
# 权威输出是 UTF-8 的 .log，控制台打印做成 best-effort。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

V = App.Vector
B = 'C:/ink/refs/tmp/v13brp/'
OUT = 'C:/ink/refs/tmp/v13out/'
LOGP = 'C:/ink/refs/tmp/build_v13.log'
os.makedirs(OUT, exist_ok=True)
_fh = open(LOGP, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    _fh.write(s + '\n'); _fh.flush(); os.fsync(_fh.fileno())
    try:
        print(s)
    except Exception:
        pass

AX, AY = 78.00, -112.50

def load(n):
    s = Part.Shape(); s.read(B + n + '.Shape.brp'); return s

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def cyl(r, z0, z1, cx=AX, cy=AY):
    return Part.makeCylinder(r, z1 - z0, V(cx, cy, z0), V(0, 0, 1))

def export(shape, name):
    p = OUT + name + '.Shape.brp'
    try:
        shape.exportBrep(p)
    except Exception:
        Part.export([shape], p)
    # 回读校验
    t = Part.Shape(); t.read(p)
    assert t.isValid() and abs(t.Volume - shape.Volume) < 1e-4, 'BREP 回读不一致: ' + name
    P('  [export] %-24s V=%10.3f sol=%d valid=%s  -> %s'
      % (name, shape.Volume, len(shape.Solids), shape.isValid(), p))

P('=' * 96)
P('v13 可注塑结构构造   （BREP 直读，绕开 openDocument）')
P('=' * 96)

h0 = load('HP45_ProbeHousing')
a0 = load('HP45_ProbeArm')
s0 = load('HP45_SpringSpacer')
P('基线: 座体 V=%.3f  臂体 V=%.3f  顶塞 V=%.3f' % (h0.Volume, a0.Volume, s0.Volume))

# ---------------------------------------------------------------- 1) 座体
P('')
P('--- 1) 座体：敞开阶梯 U 型槽 + 一体顶棚（弹簧止挡） ---')
# 1a) 敞开槽：从 X70.30（-X 面外 0.20）切到各腔右缘，型芯沿 -X 抽出
T_mag = box(70.30, 81.20, -115.70, -109.30, 76.50, 78.50)   # 磁环腔 Ø6.40 等效
T_spr = box(70.30, 81.10, -115.60, -109.40, 78.50, 87.50)   # 弹簧腔 Ø6.20 等效
h1 = h0.cut(T_mag).cut(T_spr).removeSplitter()
P('  cut 敞开槽后 V=%.3f sol=%d valid=%s' % (h1.Volume, len(h1.Solids), h1.isValid()))

# 1b) 填回 Z87.50..90.00 的 Ø6.40/Ø6.20 空腔，形成一体顶棚
plug_top = cyl(3.20, 87.50, 90.00)
h2 = h1.fuse(plug_top).removeSplitter()
P('  fuse 顶棚塞后 V=%.3f sol=%d valid=%s' % (h2.Volume, len(h2.Solids), h2.isValid()))

# 1c) 顶棚中心 Ø2.50 通孔，让 Ø2.02 针尾通过并保持 0..+3.0 行程
ctr = cyl(1.25, 87.50, 90.10)
h3 = h2.cut(ctr).removeSplitter()
P('  cut 中心孔后 V=%.3f sol=%d valid=%s' % (h3.Volume, len(h3.Solids), h3.isValid()))
assert h3.isValid() and len(h3.Solids) == 1, '座体应为单一有效实体'

# ---------------------------------------------------------------- 2) 盖板
P('')
P('--- 2) 盖板（复用 HP45_SpringSpacer 对象名，零件数不变） ---')
# 主板：贴在座体 -X 面 X70.50，覆盖敞开槽高度 Z76.50..87.50
c_main = box(68.60, 70.50, -119.00, -106.00, 76.50, 87.50)
# 补形凸台：X70.50..75.00，把敞开槽 -X 侧填回，最终腔 X75.00..81.20
c_mag = box(70.50, 75.00, -115.70, -109.30, 76.50, 78.50)
# 弹簧腔凸台 -Y 边退让到 -114.90：避开 HousingScrew_0 的 Ø2.44 杆部
# （杆心 74.00,-116.50，外缘到 Y=-115.28，留 0.38 mm 间隙）。见文件头 DFM 说明。
c_spr = box(70.50, 75.00, -114.90, -109.40, 78.50, 87.50)
cover = c_main.fuse(c_mag).fuse(c_spr).removeSplitter()
assert cover.isValid() and len(cover.Solids) == 1, '盖板应为单一有效实体'
# 让位自检：盖板不得与两颗座体螺钉干涉
for sname in ('HP45_HousingScrew_0', 'HP45_HousingScrew_1'):
    vs = cover.common(load(sname)).Volume
    P('  盖板 x %-22s = %.6f mm3  %s' % (sname, vs, 'OK' if vs < 0.001 else '!! 干涉'))
    assert vs < 0.001, '盖板与螺钉干涉: ' + sname
P('  盖板 V=%.3f sol=%d valid=%s  X%.2f..%.2f Y%.2f..%.2f Z%.2f..%.2f'
  % (cover.Volume, len(cover.Solids), cover.isValid(),
     cover.BoundBox.XMin, cover.BoundBox.XMax,
     cover.BoundBox.YMin, cover.BoundBox.YMax,
     cover.BoundBox.ZMin, cover.BoundBox.ZMax))

# ---------------------------------------------------------------- 3) 臂体
P('')
P('--- 3) 臂体：顶板掏空减重（均匀壁厚），装配面不动 ---')
# Z90..102 的 12 mm 实心顶板对注塑过厚，改成 3 mm 面板 + 底板 + 加强筋。
# 只在远离探针座接口（X68..86）与 M3 孔区开减重腔，纯减料，不新增干涉。
a1 = a0
CAV = [(90.0, 100.0), (102.5, 112.5), (115.0, 125.0)]
for x0, x1 in CAV:
    a1 = a1.cut(box(x0, x1, -118.00, -99.00, 93.00, 99.00))
a1 = a1.removeSplitter()
assert a1.isValid() and len(a1.Solids) == 1, '臂体应为单一有效实体'
P('  臂体 V %.3f -> %.3f  去除 %.3f mm3（%.1f%%） sol=%d valid=%s'
  % (a0.Volume, a1.Volume, a0.Volume - a1.Volume,
     100.0 * (a0.Volume - a1.Volume) / a0.Volume, len(a1.Solids), a1.isValid()))

# ---------------------------------------------------------------- 导出
P('')
P('--- 4) 导出新 BREP ---')
export(h3, 'HP45_ProbeHousing')
export(cover, 'HP45_SpringSpacer')
export(a1, 'HP45_ProbeArm')

P('')
P('BUILD V13 DONE  产物目录 = %s' % OUT)
_fh.close()
