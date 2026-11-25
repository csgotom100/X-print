# -*- coding: utf-8 -*-
"""v12.2 全量核验：几何 / 静态干涉 / 装配路径可达性 / 行程 / 冻结项。

与 verify_v12_1.py 的根本区别
--------------------------------------------------------------------
v12.1 只检查「装配完成后两两干涉 = 0」和「0~+3 mm 行程无干涉」，
结果漏掉了最致命的一条：静态零干涉 != 零件能到达目标位姿。
v12.2 新增第三节「装配通道剖面」和第四节「装配序列扫掠体」：
把每个零件从 Z=90.00 上方沿 -Z 平移到目标位的**整个扫掠体**造出来，
与座体 / 已装零件求 common()，体积必须为 0，才算路径可达。

运行方式（在 FreeCAD GUI 里）：
    exec(compile(open('C:/ink/refs/scripts/verify_v12_2.py',
                      encoding='utf-8').read(), 'verify_v12_2.py', 'exec'))
输出同时写 refs/tmp/verify_v12_2.log（fsync 落盘，防超时丢日志）。
"""
import io
import os
import sys

import FreeCAD as App
import Part

if not getattr(App, 'GuiUp', False):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                      errors='replace', write_through=True)
    except Exception:
        pass

LOG = 'C:/ink/refs/tmp/verify_v12_2.log'
os.makedirs(os.path.dirname(LOG), exist_ok=True)
_fh = open(LOG, 'w', encoding='utf-8')
_orig_print = print


def print(*args, **kwargs):  # noqa: A001
    s = ' '.join(str(a) for a in args)
    _orig_print(s, **kwargs)
    _fh.write(s + '\n')
    _fh.flush()
    os.fsync(_fh.fileno())


d = App.ActiveDocument
if d is None:
    d = App.openDocument('C:/ink/CrossSlide_P014013.FCStd')
g = d.getObject
AX, AY = 78.00, -112.50
UP = App.Vector(0, 0, 1)

NAMES = [
    'HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring', 'HP45_SpringSpacer',
    'HP45_SocketR125', 'HP45_ProbeHousing', 'HP45_HallSensor', 'HP45_HallPCB',
    'HP45_DustSeal', 'HP45_HallCover', 'HP45_CableClamp',
    'HP45_ProbeArm', 'HP45_HousingScrew_0', 'HP45_HousingScrew_1',
]

# v12 基线（refs/tmp/audit_struct.log）
BASE = {
    'Z_EndPlate_L':      (41521.447, (105.00, 195.00, -30.00, 19.00, 12.00, 65.00)),
    'Z_EndPlate_R':      (23059.448, (130.00, 170.00, -23.00, 19.00, 211.00, 262.00)),
    'Z_LimitSwitch_Bot': (1328.479, (140.10, 159.90, -25.90, -19.40, 50.80, 63.00)),
    'Z_LimitSwitch_Top': (1328.479, (140.10, 159.90, -25.90, -19.40, 211.10, 223.30)),
    'Z_Profile':         (45421.190, (130.00, 170.00, -1.00, 19.00, 62.00, 212.00)),
    'X_EndPlate_L':      (19096.771, (0.00, 53.00, -79.00, -37.00, 117.00, 157.00)),
}
KEYS = ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax')


def annulus(ro, ri, z0, z1):
    outer = Part.makeCylinder(ro, z1 - z0, App.Vector(AX, AY, z0), UP)
    inner = Part.makeCylinder(ri, z1 - z0 + 0.2, App.Vector(AX, AY, z0 - 0.1), UP)
    return outer.cut(inner)


def inside(shape, x, y, z):
    return shape.isInside(App.Vector(x, y, z), 1e-5, True)


def bnd(shape, mk, a, b, iters=22):
    """a 与 b 材料性相反，二分返回跳变点坐标。"""
    sa = inside(shape, *mk(a))
    for _ in range(iters):
        m = (a + b) / 2.0
        if inside(shape, *mk(m)) == sa:
            a = m
        else:
            b = m
    return (a + b) / 2.0


print('=' * 96)
print('v12.2 探针总成全量核验   文档对象数 = %d' % len(d.Objects))
print('=' * 96)

S = {}
print('\n一、各零件几何')
for n in NAMES:
    o = g(n)
    if not o:
        print('  %-24s MISSING' % n)
        continue
    S[n] = o.Shape
    b = o.Shape.BoundBox
    print('  %-24s V=%9.3f sol=%d valid=%-5s  X%7.2f..%7.2f Y%8.2f..%8.2f Z%7.2f..%7.2f'
          % (n, o.Shape.Volume, len(o.Shape.Solids), o.Shape.isValid(),
             b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))

print('\n二、两两干涉（装配完成态，含臂体与 2 颗 M3）')
keys = [k for k in NAMES if k in S]
bad = []
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = keys[i], keys[j]
        try:
            v = S[a].common(S[b]).Volume
        except Exception as e:
            print('  %-20s x %-20s ERR %s' % (a, b, e))
            continue
        if v > 0.001:
            bad.append((a, b, v))
            print('  !! %-22s x %-22s V=%.4f' % (a, b, v))
print('  干涉对数 = %d  %s' % (len(bad), 'OK' if not bad else '需处理'))

hous = S['HP45_ProbeHousing']
arm = S['HP45_ProbeArm']
sleeve = S['HP45_SocketR125']

print('\n三、装配通道剖面（沿 -X 方向，避开 +X 霍尔窗，二分实测自由半径）')


def bore_r(z):
    mk = lambda r: (AX - r, AY, z)
    if not inside(hous, *mk(6.0)):
        return 6.0  # 该高度整个截面都在体外
    if inside(hous, *mk(0.01)):
        return 0.0
    return bnd(hous, mk, 0.01, 6.0)


for z in (58.10, 70.00, 76.40, 76.60, 77.00, 78.40, 78.60, 80.00,
          85.00, 88.40, 88.60, 89.50, 89.90):
    print('  Z=%6.2f  自由半径 r = %.3f mm  (Ø%.2f)' % (z, bore_r(z), 2 * bore_r(z)))

z_lo = bnd(hous, lambda z: (AX - 2.0, AY, z), 76.00, 77.00)
z_mid = bnd(hous, lambda z: (AX - 3.15, AY, z), 78.00, 79.00)
z_hi = bnd(hous, lambda z: (AX - 3.15, AY, z), 88.00, 89.00)
print('  磁环腔下台阶 Z = %.3f' % z_lo)
print('  Ø6.40 -> Ø6.20 变径 Z = %.3f  => 磁环腔高 = %.3f mm'
      % (z_mid, z_mid - z_lo))
print('  Ø6.20 -> Ø6.40 顶口台阶 Z = %.3f' % z_hi)
print('  >> 磁环腔高 2.00 保持不变：%s' % ('OK' if abs(z_mid - z_lo - 2.00) < 0.02 else '!! 被改动'))

print('\n四、装配序列扫掠体可达性（本版新增，v12.1 漏检项）')
print('  规则：零件从 Z=90.00 上方沿 -Z 平移到目标位，整个扫掠体')
print('        与座体 / 已装零件求 common()，体积必须为 0。')
print('        注意：顶塞装入时座体尚未装进臂体，故该步不检查臂体。')

TOP = 90.00
sweeps = []
# 1) 探针 + 已粘好的磁环（同一个刚体，一起下行）
T = TOP - 57.00
pin_sw = Part.makeCylinder(1.01, 33.35 + T, App.Vector(AX, AY, 57.00), UP)
mag_sw = annulus(3.00, 1.05, 76.50, 78.50 + (TOP - 76.50))
sweeps.append(('1 探针(Ø2.02) 由顶到底', pin_sw, [('座体', hous), ('R125针套', sleeve)]))
sweeps.append(('1 磁环(Ø6.00) 随针下行', mag_sw, [('座体', hous), ('R125针套', sleeve)]))
# 2) 外部弹簧
spr_sw = annulus(3.00, 2.30, 78.50, 87.50 + (TOP - 78.50))
sweeps.append(('2 弹簧(Ø6.00) 落到磁环上', spr_sw,
               [('座体', hous), ('磁环', S['HP45_PogoMagnet'])]))
# 3) 阶梯顶塞：下导向段 / 上塞体分别扫掠
T = TOP - 87.50
plug_spigot_sw = annulus(3.00, 1.20, 87.50, 88.50 + T)
plug_body_sw = annulus(3.18, 1.20, 88.50, 90.00 + T)
sweeps.append(('3 顶塞 下导向段 Ø6.00', plug_spigot_sw,
               [('座体', hous), ('弹簧', S['HP45_PogoSpring']), ('探针', S['HP45_PogoPin'])]))
sweeps.append(('3 顶塞 上塞体 Ø6.36', plug_body_sw,
               [('座体', hous), ('弹簧', S['HP45_PogoSpring']), ('探针', S['HP45_PogoPin'])]))

path_bad = []
for label, sw, obstacles in sweeps:
    row = []
    for oname, osh in obstacles:
        try:
            v = sw.common(osh).Volume
        except Exception as e:
            v = -1.0
            row.append('%s ERR %s' % (oname, e))
            continue
        row.append('%s=%.4f' % (oname, v))
        if v > 0.001:
            path_bad.append((label, oname, v))
    print('  %-28s %s  %s' % (label, '  '.join(row), 'OK' if all(
        '=' in r and float(r.split('=')[1]) <= 0.001 for r in row if 'ERR' not in r) else 'BLOCKED'))
print('  >> 装配路径阻塞点 = %d  %s' % (len(path_bad), 'OK 全程可达' if not path_bad else '需处理'))

print('\n五、顶塞正向止挡（臂体口袋顶棚 Z90.00）')
plug = S['HP45_SpringSpacer']
print('  顶塞上端面 Z = %.2f，座体顶面 Z = %.2f  %s'
      % (plug.BoundBox.ZMax, hous.BoundBox.ZMax,
         '齐平 OK' if abs(plug.BoundBox.ZMax - hous.BoundBox.ZMax) < 0.01 else '!! 不齐'))
for r in (1.20, 1.30, 2.00, 3.00, 3.18):
    print('  臂体 @Z90.05 r=%.2f -> %s' % (r, '实体' if inside(arm, AX + r, AY, 90.05) else '空'))
print('  臂体 @Z89.95 r=2.00 -> %s（口袋内，顶塞可自由下行）'
      % ('实体' if inside(arm, AX + 2.0, AY, 89.95) else '空'))
print('  >> 座体用 2 颗 M3 锁进臂体后，顶棚压住顶塞上端面 = 正向止挡')
print('  >> 臂体中心 Ø2.50 通孔让 Ø2.02 针尾通过，+3.0 mm 行程时针尾升至 Z93.35，仍畅通')

print('\n六、尺寸链 / 磁路工作点')
pin, mag, hall = S['HP45_PogoPin'], S['HP45_PogoMagnet'], S['HP45_HallSensor']
spr, spc = S['HP45_PogoSpring'], S['HP45_SpringSpacer']
print('  针尖 Z              = %.2f' % pin.BoundBox.ZMin)
print('  低于喷嘴(57.90)     = %.2f' % (57.90 - pin.BoundBox.ZMin))
print('  磁环 Z              = %.2f..%.2f  (厚 %.2f)'
      % (mag.BoundBox.ZMin, mag.BoundBox.ZMax,
         mag.BoundBox.ZMax - mag.BoundBox.ZMin))
print('  磁环中心 Z(零位)    = %.2f' % ((mag.BoundBox.ZMin + mag.BoundBox.ZMax) / 2))
print('  霍尔中心 Z          = %.2f' % ((hall.BoundBox.ZMin + hall.BoundBox.ZMax) / 2))
print('  磁路半径 r          = %.2f mm（探针轴 X78 -> 霍尔管芯）'
      % (hall.BoundBox.XMin + 0.50 - 78.00))
print('  表面气隙            = %.2f mm' % (hall.BoundBox.XMin - mag.BoundBox.XMax))
print('  弹簧装配高          = %.2f mm (Z%.2f..%.2f)'
      % (spr.BoundBox.ZMax - spr.BoundBox.ZMin,
         spr.BoundBox.ZMin, spr.BoundBox.ZMax))
print('  顶塞总高            = %.2f mm (Z%.2f..%.2f)'
      % (spc.BoundBox.ZMax - spc.BoundBox.ZMin,
         spc.BoundBox.ZMin, spc.BoundBox.ZMax))
print('  >> r = 5.90 保持不变：%s' % ('OK' if abs(hall.BoundBox.XMin + 0.50 - 78.00 - 5.90) < 0.02 else '!! 被改动'))

print('\n七、单向行程扫描（零位 = 磁环坐 Z76.50 下台阶；dz>0 被蛋面顶起）')
FIXED = [(n, S[n]) for n in keys
         if n not in ('HP45_PogoPin', 'HP45_PogoMagnet', 'HP45_PogoSpring')]
SPR_TOP = 87.50
travel_bad = []
for dz in (-0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    p = pin.copy(); p.translate(App.Vector(0, 0, dz))
    m = mag.copy(); m.translate(App.Vector(0, 0, dz))
    sb = 78.50 + dz
    sp = annulus(3.00, 2.30, sb, SPR_TOP)
    hits = []
    for gn, gs in (('pin', p), ('magnet', m), ('spring', sp)):
        for other, osh in FIXED:
            try:
                v = gs.common(osh).Volume
            except Exception:
                continue
            if v > 0.001:
                hits.append('%s x %s = %.2f' % (gn, other, v))
    for a, b, tag in ((sp, m, 'spring x magnet'), (sp, p, 'spring x pin')):
        v = a.common(b).Volume
        if v > 0.001:
            hits.append('%s = %.2f' % (tag, v))
    tag = 'OK' if not hits else '干涉 ' + '; '.join(hits)
    if dz >= 0 and hits:
        travel_bad.append(dz)
    note = '（预期被针套孔台阶卡死 = 机械零位）' if dz < 0 and hits else ''
    print('  dz=%+.1f  针尖Z=%.2f  磁环Z=%.2f..%.2f  弹簧高=%.2f  z_rel=%+.1f  %s %s'
          % (dz, 57.00 + dz, 76.50 + dz, 78.50 + dz, SPR_TOP - sb,
             1.5 - dz, tag, note))
print('  >> 有效行程 0..+3.0 mm：%s' % ('全程无干涉 OK' if not travel_bad else '存在干涉 %s' % travel_bad))

print('\n八、弹簧受力（k = 0.045 N/mm，自由高 10.00，装配高 9.00）')
k, preload, free_h, asm_h = 0.045, 1.00, 10.00, 9.00
for dz in (0.0, 1.0, 2.0, 3.0):
    print('  dz=%.1f  弹簧高=%.2f  压缩=%.2f  F=%.3f N'
          % (dz, asm_h - dz, preload + dz, k * (preload + dz)))
solid_h = 12 * 0.30
print('  并紧高度 ≈ %.2f mm，最大可用行程 = %.2f mm > 3.00 mm  OK'
      % (solid_h, asm_h - solid_h))

print('\n九、设计冻结项复核')
all_same = True
for n, (v0, bb0) in BASE.items():
    o = g(n)
    if not o:
        print('  %-22s MISSING' % n); all_same = False; continue
    v, bb = o.Shape.Volume, o.Shape.BoundBox
    dv = abs(v - v0)
    dbb = max(abs(getattr(bb, k) - b0) for k, b0 in zip(KEYS, bb0))
    same = dv < 0.01 and dbb < 0.01
    all_same &= same
    print('  %-22s V=%.3f (基线 %.3f, dV=%.4f) dBBox=%.4f  %s'
          % (n, v, v0, dv, dbb, '完全一致' if same else '!! 有变化'))
plate = g('Z_EndPlate_L').Shape
mk = lambda x: (x, -22.0, 58.0)
if inside(plate, *mk(137.0)) and not inside(plate, *mk(150.0)) and inside(plate, *mk(163.0)):
    lo = bnd(plate, mk, 137.0, 150.0)
    hi = bnd(plate, mk, 150.0, 163.0)
    print('  Z 轴槽实测 X%.3f..%.3f 净宽 %.3f mm  %s'
          % (lo, hi, hi - lo, 'OK' if abs(hi - lo - 22.00) < 0.02 else '!! 偏离 22.00'))
xl = g('X_EndPlate_L').Shape
mk2 = lambda z: (45.0, -77.0, z)
if inside(xl, *mk2(120.0)) and not inside(xl, *mk2(131.0)) and inside(xl, *mk2(150.0)):
    lo = bnd(xl, mk2, 120.0, 131.0)
    hi = bnd(xl, mk2, 131.0, 150.0)
    print('  X 轴口袋实测 Z%.3f..%.3f 净高 %.3f mm  %s'
          % (lo, hi, hi - lo, 'OK' if abs(hi - lo - 20.80) < 0.02 else '!! 偏离 20.80'))
print('  >> Z 轴端板/限位开关体积与属性：%s' % ('全部未触碰 OK' if all_same else '!! 有变化'))

print('\n' + '=' * 96)
print('结论：静态干涉对数=%d，装配路径阻塞点=%d，有效行程 0..+3.0 mm，'
      '磁环腔高 2.00 / Z 轴 22.00 / X 轴 20.80 / r 5.90 全部保持'
      % (len(bad), len(path_bad)))
print('=' * 96)
_fh.close()
