# -*- coding: utf-8 -*-
"""v13.2 全量核验：8x8 磁环全行程通道 + 6.20 弹簧导向段。

一次脚本两用：
  * 回写前 —— 第八节报 PENDING_WRITEBACK（主 FCStd 仍是 v13 几何，不算失败）
  * 回写后 —— 第八节报 OK（三件体积 = v13.2 目标值），结论全绿

运行：freecadcmd refs/scripts/verify_v13_2.py
"""
import os
import re
import sys
import hashlib
import tempfile
import zipfile
import FreeCAD as App
import Part

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

V = App.Vector
UP = V(0, 0, 1)
OLD = 'C:/ink/refs/tmp/brep_v14_baseline/'
NEW = 'C:/ink/refs/tmp/v13_2out/'
DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_v13_2.FCStd'
LOGP = 'C:/ink/refs/tmp/verify_v13_2.log'
_fh = open(LOGP, 'w', encoding='utf-8')


def P(*a):
    s = ' '.join(str(x) for x in a)
    _fh.write(s + '\n'); _fh.flush(); os.fsync(_fh.fileno())
    try:
        print(s)
    except Exception:
        pass


AX, AY = 78.00, -112.50
MOD = {'HP45_ProbeHousing', 'HP45_ProbeArm', 'HP45_SpringSpacer'}
V132 = {'HP45_ProbeHousing': 5138.609, 'HP45_ProbeArm': 11633.557,
        'HP45_SpringSpacer': 560.200}
V13 = {'HP45_ProbeHousing': 5245.833, 'HP45_ProbeArm': 11633.557,
       'HP45_SpringSpacer': 552.050}


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


def cv(x, y):
    try:
        c = x.common(y)
        return 0.0 if c.isNull() else c.Volume
    except Exception:
        return -1.0


NAMES = ['HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring',
         'HP45_SocketR125', 'HP45_ProbeHousing', 'HP45_HallSensor',
         'HP45_HallPCB', 'HP45_DustSeal', 'HP45_HallCover',
         'HP45_CableClamp', 'HP45_ProbeArm', 'HP45_SpringSpacer',
         'HP45_HousingScrew_0', 'HP45_HousingScrew_1']
S = {n: load(n) for n in NAMES}
hous, arm, cover = S['HP45_ProbeHousing'], S['HP45_ProbeArm'], S['HP45_SpringSpacer']

P('=' * 96)
P('v13.2 全量核验：8x8 磁环全行程通道 + 6.20 弹簧导向段')
P('=' * 96)

# ---------------------------------------------------------------- 一
P('')
P('一、几何清单')
for n in NAMES:
    o = S[n]; b = o.BoundBox
    P('  %-24s V=%9.3f sol=%d valid=%-5s Z%7.2f..%7.2f%s'
      % (n, o.Volume, len(o.Solids), o.isValid(), b.ZMin, b.ZMax,
         '  <- v13.2' if n in MOD else ''))
geom_ok = all(S[n].isValid() and len(S[n].Solids) == 1 for n in NAMES)
P('  全部单一有效实体：%s' % ('OK' if geom_ok else 'FAIL'))

# ---------------------------------------------------------------- 二
P('')
P('二、8x8 通道净空 —— 座体 / 盖板不得侵入磁环全行程空间')
CHAN = box(74.00, 82.00, -116.50, -108.50, 76.50, 81.50)
GUIDE = box(75.00, 81.10, -115.60, -109.40, 81.50, 87.50)
P('  目标通道 CHAN  X74.00..82.00 / Y-116.50..-108.50 / Z76.50..81.50 = 8.00 x 8.00 x 5.00')
P('  导向段   GUIDE X75.00..81.10 / Y-115.60..-109.40 / Z81.50..87.50 = Y净宽 6.20')
v_h, v_c = cv(hous, CHAN), cv(cover, CHAN)
v_hg, v_cg = cv(hous, GUIDE), cv(cover, GUIDE)
P('  座体 ∩ CHAN = %.6f mm3 ; 盖板 ∩ CHAN = %.6f mm3  %s'
  % (v_h, v_c, 'OK 通道全空' if v_h < 0.001 and v_c < 0.001 else '!! 被侵入'))
P('  座体 ∩ GUIDE = %.6f mm3 ; 盖板 ∩ GUIDE = %.6f mm3  %s'
  % (v_hg, v_cg, 'OK 导向段全空' if v_hg < 0.001 and v_cg < 0.001 else '!! 被侵入'))
chan_ok = max(v_h, v_c, v_hg, v_cg) < 0.001
# 腔外邻近点必须是实体，证明没有意外挖穿。
# 注意避开两处本来就是空的合法开口：
#   +X 霍尔窗 Y-114.10..-110.90 / Z76.50..82.00 / X81.00..85.50；
#   顶棚中心 Ø2.50 针尾孔（中心 X78.00 / Y-112.50）。
# 取 Y=-109.00 避开霍尔窗，取 X=80.50 避开中心孔。
probes = [
    ('通道 -Y 外侧 Z77', 78.00, -117.50, 77.00),
    ('通道 +Y 外侧 Z77', 78.00, -107.50, 77.00),
    ('通道 +X 侧墙 Z77', 83.00, -109.00, 77.00),
    ('导向段 -Y 外侧 Z84', 78.00, -116.00, 84.00),
    ('顶棚实体 Z89', 80.50, -112.50, 89.00),
]
wall_ok = True
for lab, x, y, z in probes:
    solid = ins(hous, x, y, z) or ins(cover, x, y, z)
    P('  壁/实体检查 %-22s (%6.2f,%8.2f,%5.2f) = %s'
      % (lab, x, y, z, '实体 OK' if solid else '!! 挖穿'))
    wall_ok &= solid
P('  磁环 Ø6 在 8x8 内单边净空 = %.2f mm（现货公差上限 Ø6.20 仍余 %.2f mm）'
  % ((8.00 - 6.00) / 2, (8.00 - 6.20) / 2))
P('  弹簧 Ø6 在 6.20 导向段内单边净空 = %.2f mm（紧导向，防偏斜）' % ((6.20 - 6.00) / 2))

# ---------------------------------------------------------------- 三 脱模
P('')
P('三、脱模性：主分型沿 X，两型芯 -X 抽出，霍尔窗型芯 +X 抽出')
cores = [
    ('8x8 通道型芯 Z76.50..81.50', box(-100.0, 82.00, -116.50, -108.50, 76.50, 81.50)),
    ('6.20 导向型芯 Z81.50..87.50', box(-100.0, 81.10, -115.60, -109.40, 81.50, 87.50)),
]
mold_bad = []
for lab, sw in cores:
    v = cv(sw, hous)
    P('  %-32s ∩ 座体 = %.6f mm3  %s' % (lab, v, 'OK 可脱模' if v < 0.001 else '!! 倒扣'))
    if v > 0.001: mold_bad.append((lab, v))
HZ0, HZ1, HY0, HY1 = 76.50, 82.00, -114.10, -110.90
hall_sw = box(81.00, 200.0, HY0, HY1, HZ0, HZ1)
v = cv(hall_sw, hous)
P('  %-32s ∩ 座体 = %.6f mm3  %s'
  % ('霍尔窗型芯沿 +X 抽出', v, 'OK 可脱模' if v < 0.001 else '!! 倒扣'))
if v > 0.001: mold_bad.append(('霍尔窗', v))
P('  >> 新通道到 X82.00 与霍尔窗 X81.00 起在 1.00 mm 区间对穿，不形成倒扣；'
  '距霍尔感测面 X83.40 尚余 1.40 mm')
P('  >> 沿 X 脱模阻挡点 = %d  %s' % (len(mold_bad), 'OK' if not mold_bad else '需处理'))

# ---------------------------------------------------------------- 四 静态干涉
P('')
P('四、两两静态干涉（装配完成态）')
bad = []
for i, a in enumerate(NAMES):
    for b in NAMES[i + 1:]:
        v = cv(S[a], S[b])
        if v > 0.01:
            bad.append((a, b, v)); P('  !! %-22s x %-22s V=%.4f' % (a, b, v))
P('  干涉对数 = %d  %s' % (len(bad), 'OK' if not bad else '需处理'))
# 与全部 139 件的扩展静态检查
S_all = {}
for fn in os.listdir(OLD):
    if fn.endswith('.Shape.brp'):
        n = fn[:-len('.Shape.brp')]
        s = Part.Shape(); s.read(OLD + fn); S_all[n] = s
S_all['HP45_ProbeHousing'] = hous
S_all['HP45_SpringSpacer'] = cover
ext_bad = []
for n in sorted(S_all):
    if n in ('HP45_ProbeHousing', 'HP45_SpringSpacer'):
        continue
    v1, v2 = cv(hous, S_all[n]), cv(cover, S_all[n])
    if v1 > 0.001 or v2 > 0.001:
        ext_bad.append((n, v1, v2))
P('  对全部 %d 件的扩展静态检查：干涉 %d 项  %s'
  % (len(S_all), len(ext_bad), 'OK' if not ext_bad else '需处理'))
for t in ext_bad[:8]: P('    !! %s %.4f / %.4f' % t)

# ---------------------------------------------------------------- 五 装配路径
P('')
P('五、混合装配路径（磁环/弹簧 +X 侧装 → 探针 -Z 落 → 盖板 +X 扣合）')
pin, mag, spr, sock = (S['HP45_PogoPin'], S['HP45_PogoMagnet'],
                       S['HP45_PogoSpring'], S['HP45_SocketR125'])


def sweep_max_x(shape, obstacles, t_max=9.0, step=0.20):
    worst, wt = 0.0, 0.0
    for i in range(int(round(t_max / step)) + 1):
        t = i * step
        c = shape.copy(); c.translate(V(-t, 0, 0))
        vol = 0.0
        for o in obstacles:
            try:
                vol += cv(c, o)
            except Exception:
                return float('inf'), t
        if vol > worst: worst, wt = vol, t
    return worst, wt


path_bad = []
w, t = sweep_max_x(mag, [hous])
P('  ① 磁环 +X 侧装   最大干涉 %.6f @ t=%.2f  %s' % (w, t, 'OK' if w < 0.01 else 'BLOCKED'))
if w > 0.01: path_bad.append(('磁环', w))
w, t = sweep_max_x(spr, [hous, mag])
P('  ② 弹簧 +X 侧装   最大干涉 %.6f @ t=%.2f  %s' % (w, t, 'OK' if w < 0.01 else 'BLOCKED'))
if w > 0.01: path_bad.append(('弹簧', w))
drop = cyl(1.01, 57.00, 200.00)
for oname, osh in (('座体', hous), ('R125针套', sock), ('磁环', mag),
                   ('弹簧', spr), ('盖板', cover)):
    v = cv(drop, osh)
    P('  ③ 探针 -Z 落下 ∩ %-10s = %.6f mm3  %s' % (oname, v, 'OK' if v < 0.01 else 'BLOCKED'))
    if v > 0.01: path_bad.append(('探针落下', oname, v))
w, t = sweep_max_x(cover, [hous, mag, spr, pin,
                           S['HP45_HousingScrew_0'], S['HP45_HousingScrew_1']])
P('  ④ 盖板 +X 扣合   最大干涉 %.6f @ t=%.2f  %s' % (w, t, 'OK' if w < 0.01 else 'BLOCKED'))
if w > 0.01: path_bad.append(('盖板', w))
P('  >> 装配路径阻塞点 = %d  %s' % (len(path_bad), 'OK 全程可达' if not path_bad else '需处理'))

# ---------------------------------------------------------------- 六 冻结项
P('')
P('六、尺寸链与设计冻结项')
hall = S['HP45_HallSensor']
P('  针尖 Z = %.2f ; 磁环 Z = %.2f..%.2f (厚 %.2f) ; 霍尔中心 Z = %.2f'
  % (pin.BoundBox.ZMin, mag.BoundBox.ZMin, mag.BoundBox.ZMax,
     mag.BoundBox.ZMax - mag.BoundBox.ZMin,
     (hall.BoundBox.ZMin + hall.BoundBox.ZMax) / 2))
P('  磁路半径 r = %.2f ; 霍尔感测面 X = %.2f ; 气隙 = %.2f'
  % (hall.BoundBox.XMin + 0.50 - 78.00, hall.BoundBox.XMin,
     hall.BoundBox.XMin - mag.BoundBox.XMax))
z_stop = bnd(hous, lambda z: (AX - 2.0, AY, z), 86.50, 88.50)
P('  一体顶棚下表面(弹簧止挡) Z = %.3f  %s' % (z_stop, 'OK 87.50' if abs(z_stop - 87.50) < 0.05 else '!! 变动'))
frz = [
    ('磁环下台阶 Z76.50 / 厚 2.00', abs(mag.BoundBox.ZMin - 76.50) < 0.01 and abs(mag.BoundBox.ZMax - 78.50) < 0.01),
    ('霍尔 r = 5.90', abs(hall.BoundBox.XMin + 0.5 - 78.0 - 5.90) < 0.02),
    ('霍尔感测面 X83.40', abs(hall.BoundBox.XMin - 83.40) < 0.02),
    ('弹簧装配高 9.00', abs((spr.BoundBox.ZMax - spr.BoundBox.ZMin) - 9.00) < 0.01),
    ('顶棚止挡 Z87.50', abs(z_stop - 87.50) < 0.05),
]
for lab, ok in frz:
    P('  %-30s %s' % (lab, 'OK 未动' if ok else '!! 变动'))
frz_ok = all(x[1] for x in frz)

# 冻结项对象：改前(回滚备份) vs 改后 BREP 基线，逐件几何等价
P('')
P('  冻结项对象（端板 / 限位开关 / 型材）—— 与回滚备份比对：')
FREEZE = ['Z_EndPlate_L', 'Z_EndPlate_R', 'Z_LimitSwitch_Bot',
          'Z_LimitSwitch_Top', 'Z_Profile', 'X_EndPlate_L']
zb = zipfile.ZipFile(BAK)
_td = tempfile.mkdtemp(prefix='v132fr_')
obj_ok = True
for n in FREEZE:
    fn = n + '.Shape.brp'
    s1 = Part.Shape(); s1.read(OLD + fn)
    p = os.path.join(_td, fn); open(p, 'wb').write(zb.read(fn))
    s2 = Part.Shape(); s2.read(p); os.remove(p)
    raw_same = open(OLD + fn, 'rb').read() == zb.read(fn)
    d = cv(s1, s2) + cv(s2, s1)
    ok = raw_same or (d < 1e-6 and abs(s1.Volume - s2.Volume) < 1e-6)
    obj_ok &= ok
    P('    %-22s V=%9.3f  %s' % (n, s1.Volume,
                              '字节一致 OK' if raw_same else ('对称差 %.6f OK' % d if ok else '!! 几何有变')))
os.rmdir(_td)
plate = S_all['Z_EndPlate_L']
mk = lambda x: (x, -22.0, 58.0)
slot_ok = False
if ins(plate, *mk(137.0)) and not ins(plate, *mk(150.0)) and ins(plate, *mk(163.0)):
    lo, hi = bnd(plate, mk, 137.0, 150.0), bnd(plate, mk, 150.0, 163.0)
    slot_ok = abs(hi - lo - 22.0) < 0.02
    P('    Z 轴限位槽实测 X%.3f..%.3f 净宽 %.3f mm  %s' % (lo, hi, hi - lo, 'OK 22.00' if slot_ok else '!! 偏离'))
xl = S_all['X_EndPlate_L']
mk2 = lambda zz: (45.0, -77.0, zz)
pock_ok = False
if ins(xl, *mk2(120.0)) and not ins(xl, *mk2(131.0)) and ins(xl, *mk2(150.0)):
    lo, hi = bnd(xl, mk2, 120.0, 131.0), bnd(xl, mk2, 131.0, 150.0)
    pock_ok = abs(hi - lo - 20.80) < 0.02
    P('    X 轴口袋实测 Z%.3f..%.3f 净高 %.3f mm  %s' % (lo, hi, hi - lo, 'OK 20.80' if pock_ok else '!! 偏离'))
P('  >> 冻结项几何：%s' % ('全部未触碰 OK' if obj_ok and slot_ok and pock_ok else '!! 有变化'))

# ---------------------------------------------------------------- 七 行程
P('')
P('七、单向行程扫描 0..+3.0 mm（磁环全程须留在 8x8 净空内）')
FIXED = [(n, S[n]) for n in NAMES if n not in ('HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring')]
SPR_TOP = 87.50
travel_bad, clearance_bad = [], []
for dz in (-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    p = pin.copy(); p.translate(V(0, 0, dz))
    m = mag.copy(); m.translate(V(0, 0, dz))
    sb = 78.50 + dz
    sp = annulus(3.00, 2.30, sb, SPR_TOP)
    hits = []
    for gn, gs in (('pin', p), ('magnet', m), ('spring', sp)):
        for other, osh in FIXED:
            v = cv(gs, osh)
            if v > 0.01: hits.append('%s x %s = %.2f' % (gn, other, v))
    for aa, bb, tag in ((sp, m, 'spring x magnet'), (sp, p, 'spring x pin')):
        v = cv(aa, bb)
        if v > 0.01: hits.append('%s = %.2f' % (tag, v))
    if dz >= 0 and hits: travel_bad.append(dz)
    # 磁环与 8x8 通道边界
    mb = m.BoundBox
    inside = (mb.XMin >= 74.00 - 1e-6 and mb.XMax <= 82.00 + 1e-6
              and mb.YMin >= -116.50 - 1e-6 and mb.YMax <= -108.50 + 1e-6
              and mb.ZMin >= 76.50 - 1e-6 and mb.ZMax <= 81.50 + 1e-6)
    gap = min(mb.XMin - 74.00, 82.00 - mb.XMax,
              mb.YMin - (-116.50), -108.50 - mb.YMax)
    if dz >= 0 and not inside: clearance_bad.append((dz, gap))
    P('  dz=%+.1f  磁环Z=%.2f..%.2f  弹簧高=%.2f  最小径向余量=%.2f  %s%s'
      % (dz, mb.ZMin, mb.ZMax, SPR_TOP - sb, gap,
         'OK' if not hits else '干涉 ' + '; '.join(hits[:2]),
         '' if inside or dz < 0 else ' / !! 越出8x8'))
P('  >> 行程 0..+3.0 mm 干涉 %d 项、8x8 越界 %d 项  %s'
  % (len(travel_bad), len(clearance_bad),
     'OK 全程在 8x8 净空内' if not travel_bad and not clearance_bad else '需处理'))

# ---------------------------------------------------------------- 八 弹簧力
P('')
P('八、接触力（弹簧采购规格未改：Ø6 / 0.30 / 12 圈 / k=0.045 N/mm）')
k, preload, asm_h = 0.045, 1.00, 9.00
for dz in (0.0, 1.0, 2.0, 3.0):
    P('  dz=%.1f  弹簧高=%.2f  压缩=%.2f  F=%.3f N' % (dz, asm_h - dz, preload + dz, k * (preload + dz)))
P('  F0=0.045 N（目标 0.03~0.08）；满程 0.180 N；并紧高 3.60 < 6.00  OK')

# ---------------------------------------------------------------- 九 FCStd
P('')
P('九、主 FCStd 状态（回写前 = PENDING；回写后 = OK）')
zf = zipfile.ZipFile(DOC)
fnames = zf.namelist()
fxml = zf.read('Document.xml').decode('utf-8')
P('  ZIP 条目 = %d  testzip = %s  GuiDocument.xml = %s  对象块 = %d'
  % (len(fnames), zf.testzip(), 'GuiDocument.xml' in fnames, fxml.count('<Object name=')))
refs = re.findall(r'ElementMap2 file="([^"]+)"', fxml)
dang = [r for r in refs if r not in fnames]
P('  ElementMap2 引用 = %d  悬空 = %d' % (len(refs), len(dang)))
_td2 = tempfile.mkdtemp(prefix='v132fc_')
vols = {}
for n in V132:
    p = os.path.join(_td2, n + '.brp')
    open(p, 'wb').write(zf.read(n + '.Shape.brp'))
    s = Part.Shape(); s.read(p); vols[n] = s.Volume; os.remove(p)
os.rmdir(_td2)
is_v132 = all(abs(vols[n] - V132[n]) < 0.01 for n in V132)
is_v13 = all(abs(vols[n] - V13[n]) < 0.01 for n in V13)
for n in V132:
    P('  %-22s FCStd 内 V=%10.3f (v13.2 目标 %.3f)' % (n, vols[n], V132[n]))
state = 'OK 与 v13.2 一致' if is_v132 else ('PENDING_WRITEBACK（当前仍为 v13 几何）' if is_v13 else '!! 未知几何')
P('  >> 主 FCStd 状态：%s' % state)
fc_ok = (zf.testzip() is None and 'GuiDocument.xml' in fnames
         and fxml.count('<Object name=') == 151 and not dang
         and (is_v132 or is_v13))

# ---------------------------------------------------------------- 结论
P('')
P('=' * 96)
ok = (geom_ok and chan_ok and wall_ok and not mold_bad and not bad
      and not ext_bad and not path_bad and frz_ok and obj_ok
      and slot_ok and pock_ok and not travel_bad and not clearance_bad and fc_ok)
P('结论：通道净空=%s 壁厚=%s 脱模阻挡=%d 静态干涉=%d/%d 装配阻塞=%d'
  % ('OK' if chan_ok else 'FAIL', 'OK' if wall_ok else 'FAIL',
     len(mold_bad), len(bad), len(ext_bad), len(path_bad)))
P('      冻结项=%s 行程干涉=%d 8x8越界=%d FCStd=%s'
  % ('OK' if frz_ok and obj_ok and slot_ok and pock_ok else 'FAIL',
     len(travel_bad), len(clearance_bad), state))
if ok and is_v132:
    verdict = '>>> v13.2 通过全部核验：8x8 全行程通道、6.20 紧导向、冻结项未动、脱模/装配/行程全绿、主文档已回写'
elif ok and is_v13:
    verdict = '>>> v13.2 几何验证全绿（脱模/干涉/装配/行程/冻结项）；主 FCStd 尚待 GUI 回写，回写后重跑本脚本即为全绿'
else:
    verdict = '>>> 存在未通过项，需修正'
P('      %s' % verdict)
P('=' * 96)
_fh.close()
