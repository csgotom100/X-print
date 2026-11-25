# -*- coding: utf-8 -*-
"""v13 全量核验：注塑脱模性 / 冻结项 / 静态干涉 / 侧装路径 / 行程 / 弹簧止挡。

与 verify_v12_2.py 的区别
--------------------------------------------------------------------
v12.2 检查「顶装扫掠体沿 -Z 可达」；v13 的抽芯与腔体装配方向改成 X：
  * 第一节：脱模性 —— 把敞开槽型芯沿 -X 无限抽出的扫掠体造出来，
    与座体求 common()，体积必须为 0（无倒扣 = 可注塑）；
    +X 霍尔窗型芯另按「实测窗口边界」沿 +X 抽出。
  * 第二节：混合装配路径 —— 磁环/弹簧沿 +X 侧装、探针沿 -Z 顶落、
    盖板沿 +X 扣合。侧装件用「刚体平移逐点采样」，不用整体 bbox 包络；
    探针用等截面圆柱扫掠（v12.2 同款口径），不用方盒。
  * 冻结项、静态干涉、行程、弹簧受力沿用 v12.2 口径。

【v13.1 修正记录】首跑因 freecadcmd 的 GBK 控制台无法 print Ø 而在第二节
中断（已改为 best-effort print + UTF-8 权威日志）。随后 5 个告警经
probe_v13_issues.py / probe_v13_fine.py 定性：4 个是检查口径过保守
（霍尔窗 Z 上界、探针装入轴、盖板 bbox 包络），1 个是真实几何缺陷
（盖板凸台啃进 HousingScrew_0 的 Ø2.44 杆部），已在 build_v13.py 中
把凸台 -Y 边退让 0.70 mm 修正。

数据通道：本机 FreeCAD 1.1 openDocument 卡死，全部用 Part.Shape.read()
直读 FCStd 压缩包内的 BREP。新几何在 refs/tmp/v13out/，其余在原 brp 目录。
"""
import os
import sys
import zipfile
import FreeCAD as App
import Part

# Windows 控制台默认 GBK/cp936，无法编码 Ø(U+00D8) 等字符。
# freecadcmd 里 print() 一旦抛 UnicodeEncodeError 会直接终止整个脚本
# （2026-11-09 verify_v13 首跑即因此停在第二节）。
# 令 stdout 尽量走 UTF-8；即便失败，P() 内的 print 也被保护，
# 权威输出始终是以 UTF-8 写入的 .log 文件。
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

V = App.Vector
OLD = 'C:/ink/refs/tmp/v13brp/'
NEW = 'C:/ink/refs/tmp/v13out/'
LOGP = 'C:/ink/refs/tmp/verify_v13.log'
_fh = open(LOGP, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    _fh.write(s + '\n'); _fh.flush(); os.fsync(_fh.fileno())
    try:
        print(s)
    except Exception:
        pass

AX, AY = 78.00, -112.50
UP = V(0, 0, 1)
MOD = {'HP45_ProbeHousing', 'HP45_ProbeArm', 'HP45_SpringSpacer'}

def load(n):
    p = (NEW if n in MOD else OLD) + n + '.Shape.brp'
    s = Part.Shape(); s.read(p); return s

def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))

def cyl(r, z0, z1, cx=AX, cy=AY):
    return Part.makeCylinder(r, z1 - z0, V(cx, cy, z0), UP)

def annulus(ro, ri, z0, z1):
    return cyl(ro, z0, z1).cut(cyl(ri, z0 - 0.1, z1 + 0.1))

def ins(sh, x, y, z):
    return sh.isInside(V(x, y, z), 1e-5, True)

def bnd(sh, mk, a, b, iters=20):
    sa = ins(sh, *mk(a))
    for _ in range(iters):
        m = (a + b) / 2.0
        if ins(sh, *mk(m)) == sa:
            a = m
        else:
            b = m
    return (a + b) / 2.0

NAMES = ['HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring',
         'HP45_SocketR125', 'HP45_ProbeHousing', 'HP45_HallSensor',
         'HP45_HallPCB', 'HP45_DustSeal', 'HP45_HallCover',
         'HP45_CableClamp', 'HP45_ProbeArm', 'HP45_SpringSpacer',
         'HP45_HousingScrew_0', 'HP45_HousingScrew_1']
S = {n: load(n) for n in NAMES}
hous = S['HP45_ProbeHousing']
arm = S['HP45_ProbeArm']
cover = S['HP45_SpringSpacer']

P('=' * 96)
P('v13 探针总成全量核验（注塑 DFM + 装配）')
P('=' * 96)

P('')
P('一、各零件几何（新几何 = 座体/臂体/盖板）')
for n in NAMES:
    o = S[n]; b = o.BoundBox
    tag = '  <- v13 新' if n in MOD else ''
    P('  %-24s V=%9.3f sol=%d valid=%-5s  X%7.2f..%7.2f Y%8.2f..%8.2f Z%7.2f..%7.2f%s'
      % (n, o.Volume, len(o.Solids), o.isValid(),
         b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax, tag))

# ---------------------------------------------------------------- 二、脱模性
P('')
P('二、脱模性（v13 核心）：敞开 U 型槽型芯沿 -X 抽出的扫掠体 vs 座体')
P('  规则：型芯 = 敞开槽对应的矩形凸模；沿 -X 平移到无穷远的扫掠体')
P('        与座体求 common()，体积必须为 0 —— 即沿 -X 无任何阻挡/倒扣。')
P('  对照：v12.2 封闭阶梯圆孔沿 ±Z 双向都抽不出（Ø6.40 磁环腔被 Ø6.20 卡住）。')
cores = [
    ('磁环腔型芯 Z76.50..78.50', box(-100.0, 81.20, -115.70, -109.30, 76.50, 78.50)),
    ('弹簧腔型芯 Z78.50..87.50', box(-100.0, 81.10, -115.60, -109.40, 78.50, 87.50)),
]
mold_bad = []
for lab, sw in cores:
    v = sw.common(hous).Volume
    P('  %-28s common = %.6f mm3  %s' % (lab, v, 'OK 可脱模' if v < 0.001 else '!! 有倒扣'))
    if v > 0.001:
        mold_bad.append((lab, v))
# +X 侧霍尔窗型芯沿 +X 抽出
# 【v13.1 修正】窗口真实边界由 probe_v13_fine.py 二分实测：
#   Z76.5000..82.0000、Y-114.1000..-110.9000（窗高 5.50 / 宽 3.20）。
#   首版口径 Z76.55..82.45 把窗上方 Z82.00..82.45 的实体墙算进了型芯，
#   误报 3.20 × 4.50 × 0.44 = 6.336 mm3 的「倒扣」；用实测边界后为 0。
HZ0, HZ1, HY0, HY1 = 76.50, 82.00, -114.10, -110.90
hall_sw = box(81.00, 200.0, HY0, HY1, HZ0, HZ1)
v = hall_sw.common(hous).Volume
P('  %-28s common = %.6f mm3  %s'
  % ('霍尔窗型芯沿 +X 抽出', v, 'OK 可脱模' if v < 0.001 else '!! 有倒扣'))
P('      窗口实测边界 Z%.2f..%.2f / Y%.2f..%.2f（窗高 %.2f，宽 %.2f）'
  % (HZ0, HZ1, HY0, HY1, HZ1 - HZ0, HY1 - HY0))
if v > 0.001:
    mold_bad.append(('霍尔窗', v))
P('  >> 主分型沿 X：U 型槽型芯 -X 抽出、霍尔窗型芯 +X 抽出，均无需侧滑块。')
P('  >> 沿 Z 的细长孔（Ø2.37 针套孔 / 2×M3 / 顶棚中心 Ø2.50）按 DFM 后钻或铜嵌件。')
P('  >> 沿 X 脱模阻挡点 = %d  %s' % (len(mold_bad), 'OK' if not mold_bad else '需处理'))

# ---------------------------------------------------------------- 三、静态干涉
P('')
P('三、两两静态干涉（装配完成态）')
bad = []
keys = list(NAMES)
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = keys[i], keys[j]
        try:
            v = S[a].common(S[b]).Volume
        except Exception as e:
            P('  %-22s x %-22s ERR %s' % (a, b, e)); continue
        if v > 0.01:
            bad.append((a, b, v))
            P('  !! %-22s x %-22s V=%.4f' % (a, b, v))
P('  干涉对数 = %d  %s' % (len(bad), 'OK' if not bad else '需处理'))

# ---------------------------------------------------------------- 四、装配路径
P('')
P('四、装配路径可达性（v13「混合装配」：磁环/弹簧侧装 + 探针顶落 + 盖板侧扣）')
P('  沿用 verify_v12_2.py 的「扫掠体 vs 障碍」口径，修正首版两处口径错误：')
P('    (1) 探针是等截面 Ø2.02 圆柱，装入轴是 -Z（从一体顶棚 Ø2.50 孔落下），')
P('        不是 +X；扫掠体必须用 makeCylinder，不能用 bbox 方盒 —— 方盒四角')
P('        会假性啃进 Ø2.37 圆孔与磁环 Ø2.10 内孔（首版误报 277 / 9.9 mm3）。')
P('    (2) 盖板是「薄主板 + 窄凸台」，整体 bbox 包络把主板 13 mm 宽度错误地')
P('        延伸到 X70.50..75.00 的凸台区，假报 303 mm3；改用刚体平移逐点采样。')
P('  装配顺序（探针子总成先在台面装好，再整体装入臂体，故本步不以臂体为障碍）：')
P('    ① 磁环侧装 → ② 弹簧侧装 → ③ 探针 -Z 落下 → ④ 盖板 +X 扣合 → ⑤ 装 2 颗螺钉')

pin = S['HP45_PogoPin']
mag = S['HP45_PogoMagnet']
spr = S['HP45_PogoSpring']
sock = S['HP45_SocketR125']

def sweep_max_x(shape, obstacles, t_max=9.0, step=0.20):
    """刚体从 -X 侧沿 +X 推到目标位，逐点求交；返回最大干涉体积与对应 t。"""
    n = int(round(t_max / step))
    worst, wt = 0.0, 0.0
    for i in range(n + 1):
        t = i * step
        c = shape.copy(); c.translate(V(-t, 0, 0))
        vol = 0.0
        for o in obstacles:
            try:
                vol += c.common(o).Volume
            except Exception:
                return float('inf'), t
        if vol > worst:
            worst, wt = vol, t
    return worst, wt

path_bad = []
# ① 磁环：从 -X 沿 +X 进入敞开槽（盖板此时尚未装，障碍只有座体）
w, t = sweep_max_x(mag, [hous])
P('  ① 磁环 +X 侧装  最大干涉 = %.6f mm3 @ t=%.2f  %s'
  % (w, t, 'OK' if w < 0.01 else 'BLOCKED'))
if w > 0.01: path_bad.append(('磁环', w))
# ② 弹簧：障碍 = 座体 + 已就位磁环
w, t = sweep_max_x(spr, [hous, mag])
P('  ② 弹簧 +X 侧装  最大干涉 = %.6f mm3 @ t=%.2f  %s'
  % (w, t, 'OK' if w < 0.01 else 'BLOCKED'))
if w > 0.01: path_bad.append(('弹簧', w))
# ③ 探针：沿 -Z 从顶棚 Ø2.50 孔落下；等截面圆柱扫掠（v12.2 同款口径）
P('')
P('  ③ 探针沿 -Z 落下（扫掠 = Ø2.02 圆柱，Z57.00..+∞）')
drop = cyl(1.01, 57.00, 200.00)
for oname, osh in (('座体', hous), ('R125针套', sock), ('磁环', mag),
                   ('弹簧', spr), ('盖板', cover)):
    v = drop.common(osh).Volume
    P('     ∩ %-10s = %.6f mm3  %s' % (oname, v, 'OK' if v < 0.01 else 'BLOCKED'))
    if v > 0.01: path_bad.append(('探针落下', oname, v))
P('     探针最终位 ∩ 座体 = %.6f mm3' % pin.common(hous).Volume)
P('     参考：落下扫掠 ∩ 臂体 = %.4f mm3（臂体在探针子总成之后装配，按 v12.2 口径不作障碍）'
  % drop.common(arm).Volume)
# ④ 盖板扣合：刚体平移采样，障碍 = 座体 + 内部三件 + 2 颗螺钉
P('')
P('  ④ 盖板 +X 扣合（刚体平移采样，障碍 = 座体/磁环/弹簧/探针/2 螺钉）')
cover_obs = [hous, mag, spr, pin, S['HP45_HousingScrew_0'], S['HP45_HousingScrew_1']]
w, t = sweep_max_x(cover, cover_obs, t_max=9.0, step=0.20)
P('     最大干涉 = %.6f mm3 @ t=%.2f  %s' % (w, t, 'OK' if w < 0.01 else 'BLOCKED'))
if w > 0.01: path_bad.append(('盖板', w))
P('     t=0（目标位）盖板 ∩ 座体 = %.6f mm3' % cover.common(hous).Volume)
P('  >> 装配路径阻塞点 = %d  %s' % (len(path_bad), 'OK 全程可达' if not path_bad else '需处理'))

# ---------------------------------------------------------------- 五、尺寸链 / 冻结项
P('')
P('五、尺寸链与设计冻结项')
mag, hall, pin2, spr = (S['HP45_PogoMagnet'], S['HP45_HallSensor'],
                        S['HP45_PogoPin'], S['HP45_PogoSpring'])
P('  针尖 Z                = %.2f' % pin2.BoundBox.ZMin)
P('  磁环 Z                = %.2f..%.2f (厚 %.2f)'
  % (mag.BoundBox.ZMin, mag.BoundBox.ZMax, mag.BoundBox.ZMax - mag.BoundBox.ZMin))
P('  磁环中心 Z(零位)      = %.2f' % ((mag.BoundBox.ZMin + mag.BoundBox.ZMax) / 2))
P('  霍尔中心 Z            = %.2f' % ((hall.BoundBox.ZMin + hall.BoundBox.ZMax) / 2))
P('  磁路半径 r            = %.2f mm  (冻结 5.90)'
  % (hall.BoundBox.XMin + 0.50 - 78.00))
P('  表面气隙              = %.2f mm' % (hall.BoundBox.XMin - mag.BoundBox.XMax))
P('  弹簧装配高            = %.2f mm (Z%.2f..%.2f)'
  % (spr.BoundBox.ZMax - spr.BoundBox.ZMin, spr.BoundBox.ZMin, spr.BoundBox.ZMax))

# 磁环腔下台阶 Z76.50 / 腔高 2.00：用「磁环实测 Z 边界」核验（见下方断言）
# 更稳：直接测顶棚下表面 Z87.50（弹簧止挡）
z_stop = bnd(hous, lambda z: (AX - 2.0, AY, z), 86.50, 88.50)
P('  一体顶棚下表面(弹簧止挡) Z = %.3f  (目标 87.50)' % z_stop)
P('  >> 顶棚止挡 Z87.50 与弹簧上端面 Z%.2f：%s'
  % (spr.BoundBox.ZMax, '贴合 OK' if abs(z_stop - spr.BoundBox.ZMax) < 0.05 else '!! 不贴合'))
P('  >> 磁环腔高 2.00 (Z76.50..78.50)：磁环实际占 Z%.2f..%.2f，%s'
  % (mag.BoundBox.ZMin, mag.BoundBox.ZMax,
     'OK' if abs(mag.BoundBox.ZMin - 76.50) < 0.01 and abs(mag.BoundBox.ZMax - 78.50) < 0.01 else '!! 变动'))
P('  >> 霍尔 r = 5.90：%s' % ('OK 未动' if abs(hall.BoundBox.XMin + 0.5 - 78.0 - 5.90) < 0.02 else '!! 变动'))
P('  >> 霍尔感测面 X83.40：%s' % ('OK 未动' if abs(hall.BoundBox.XMin - 83.40) < 0.02 else '!! 变动'))

# 冻结项对象：改前(备份 FCStd) vs 改后(主 FCStd) 逐件比对
# 注：writeback 走 GUI 的 d.save()，FreeCAD 会把少数无关 BREP 重新序列化
#     （Z_Profile / X_Profile / HP45CAR_P04 字节变化但几何完全等价，
#      已由 check_reserialize.py 的对称差体积判据证明），故不能只看 SHA。
P('')
P('  冻结项对象（Z 端板 / 限位开关 / X 端板）—— 改前/改后 FCStd 几何等价：')
BAK = 'C:/ink/refs/CrossSlide_before_v13.FCStd'
z = zipfile.ZipFile('C:/ink/CrossSlide_P014013.FCStd')
zb = zipfile.ZipFile(BAK)
import hashlib
import tempfile
FREEZE = ['Z_EndPlate_L', 'Z_EndPlate_R', 'Z_LimitSwitch_Bot',
          'Z_LimitSwitch_Top', 'Z_Profile', 'X_EndPlate_L']
fr_ok = True
_td = tempfile.mkdtemp(prefix='v13fr_')
for n in FREEZE:
    fn = n + '.Shape.brp'
    raw, base = z.read(fn), zb.read(fn)
    if raw == base:
        ok, note = True, '字节一致 OK'
    else:
        p2 = os.path.join(_td, fn)
        open(p2, 'wb').write(raw)
        s1 = load(n)                      # 改前基线 BREP
        s2 = Part.Shape(); s2.read(p2)    # 改后 FCStd 内 BREP
        d1, d2 = s1.cut(s2).Volume, s2.cut(s1).Volume
        ok = (abs(d1) < 1e-6 and abs(d2) < 1e-6
              and abs(s1.Volume - s2.Volume) < 1e-6)
        note = ('重序列化/对称差 %.6f OK' % d1) if ok else '!! 几何有变'
        os.remove(p2)
    fr_ok &= ok
    P('    %-22s %s (V=%.3f)' % (n, note, load(n).Volume))
os.rmdir(_td)
plate = load('Z_EndPlate_L')
mk = lambda x: (x, -22.0, 58.0)
if ins(plate, *mk(137.0)) and not ins(plate, *mk(150.0)) and ins(plate, *mk(163.0)):
    lo = bnd(plate, mk, 137.0, 150.0); hi = bnd(plate, mk, 150.0, 163.0)
    P('    Z 轴限位槽实测 X%.3f..%.3f 净宽 %.3f mm  %s'
      % (lo, hi, hi - lo, 'OK 22.00' if abs(hi - lo - 22.0) < 0.02 else '!! 偏离'))
xl = load('X_EndPlate_L')
mk2 = lambda zz: (45.0, -77.0, zz)
if ins(xl, *mk2(120.0)) and not ins(xl, *mk2(131.0)) and ins(xl, *mk2(150.0)):
    lo = bnd(xl, mk2, 120.0, 131.0); hi = bnd(xl, mk2, 131.0, 150.0)
    P('    X 轴口袋实测 Z%.3f..%.3f 净高 %.3f mm  %s'
      % (lo, hi, hi - lo, 'OK 20.80' if abs(hi - lo - 20.80) < 0.02 else '!! 偏离'))
P('  >> 冻结项对象几何：%s' % ('全部未触碰 OK' if fr_ok else '!! 有变化'))

# ---------------------------------------------------------------- 六、行程
P('')
P('六、单向行程扫描（零位 = 磁环坐 Z76.50 下台阶；dz>0 被蛋面顶起）')
FIXED = [(n, S[n]) for n in NAMES if n not in ('HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring')]
SPR_TOP = 87.50
travel_bad = []
for dz in (-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    p = pin2.copy(); p.translate(V(0, 0, dz))
    m = mag.copy(); m.translate(V(0, 0, dz))
    sb = 78.50 + dz
    sp = annulus(3.00, 2.30, sb, SPR_TOP)
    hits = []
    for gn, gs in (('pin', p), ('magnet', m), ('spring', sp)):
        for other, osh in FIXED:
            try:
                v = gs.common(osh).Volume
            except Exception:
                continue
            if v > 0.01:
                hits.append('%s x %s = %.2f' % (gn, other, v))
    for aa, bb, tag in ((sp, m, 'spring x magnet'), (sp, p, 'spring x pin')):
        v = aa.common(bb).Volume
        if v > 0.01: hits.append('%s = %.2f' % (tag, v))
    if dz >= 0 and hits: travel_bad.append(dz)
    P('  dz=%+.1f  针尖Z=%.2f  磁环Z=%.2f..%.2f  弹簧高=%.2f  %s'
      % (dz, 57.00 + dz, 76.50 + dz, 78.50 + dz, SPR_TOP - sb,
         'OK' if not hits else '干涉 ' + '; '.join(hits[:3])))
P('  >> 有效行程 0..+3.0 mm：%s' % ('全程无干涉 OK' if not travel_bad else '存在干涉 %s' % travel_bad))

# ---------------------------------------------------------------- 七、弹簧受力
P('')
P('七、弹簧受力（k=0.045 N/mm，自由高 10.00，装配高 9.00，预压 1.00）')
k, preload, asm_h = 0.045, 1.00, 9.00
for dz in (0.0, 1.0, 2.0, 3.0):
    P('  dz=%.1f  弹簧高=%.2f  压缩=%.2f  F=%.3f N' % (dz, asm_h - dz, preload + dz, k * (preload + dz)))
P('  并紧高度 ≈ %.2f mm，最大可用行程 = %.2f mm > 3.00 mm  OK' % (12 * 0.30, asm_h - 12 * 0.30))

# ---------------------------------------------------------------- 八、FCStd 回写核验
P('')
P('八、主 FCStd 回写核验（writeback_v13.py 的 GUI d.save() 产物）')
import re
zf = zipfile.ZipFile('C:/ink/CrossSlide_P014013.FCStd')
fnames = zf.namelist()
fxml = zf.read('Document.xml').decode('utf-8')
fc_ok = True
P('  ZIP 条目 = %d  testzip = %s  GuiDocument.xml = %s  对象块 = %d'
  % (len(fnames), zf.testzip(), 'GuiDocument.xml' in fnames,
     fxml.count('<Object name=')))
fc_ok &= (zf.testzip() is None and 'GuiDocument.xml' in fnames
          and fxml.count('<Object name=') == 151)
refs = re.findall(r'ElementMap2 file="([^"]+)"', fxml)
dang = [r for r in refs if r not in fnames]
P('  ElementMap2 引用 = %d  悬空 = %d  %s'
  % (len(refs), len(dang), 'OK' if not dang else '!! 有悬空'))
fc_ok &= not dang
td2 = tempfile.mkdtemp(prefix='v13fcv_')
for n, v in (('HP45_ProbeHousing', 5245.833),
             ('HP45_ProbeArm', 11633.557),
             ('HP45_SpringSpacer', 552.050)):
    p = os.path.join(td2, n + '.brp')
    open(p, 'wb').write(zf.read(n + '.Shape.brp'))
    s = Part.Shape(); s.read(p)
    okk = s.isValid() and len(s.Solids) == 1 and abs(s.Volume - v) < 0.01
    fc_ok &= okk
    P('  %-22s FCStd 内 V=%10.3f sol=%d  %s'
      % (n, s.Volume, len(s.Solids), 'OK' if okk else '!! 不符'))
    os.remove(p)
os.rmdir(td2)
P('  >> 主 FCStd 回写：%s' % ('OK 与 v13 几何一致' if fc_ok else '!! 有未通过项'))

# ---------------------------------------------------------------- 九、结论
P('')
P('=' * 96)
ok = ((not mold_bad) and (not bad) and (not path_bad)
      and (not travel_bad) and fr_ok and fc_ok)
P('结论：脱模阻挡=%d  静态干涉=%d  侧装阻塞=%d  行程干涉=%d  冻结项=%s  FCStd回写=%s'
  % (len(mold_bad), len(bad), len(path_bad), len(travel_bad),
     'OK' if fr_ok else 'FAIL', 'OK' if fc_ok else 'FAIL'))
P('      %s' % ('>>> v13 通过全部核验：可注塑成型、可混合装配、冻结项几何未动、主文档已回写'
               if ok else '>>> 存在未通过项，需修正'))
P('=' * 96)
_fh.close()
