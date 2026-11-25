# -*- coding: utf-8 -*-
"""v12 磁环选型定稿复核：到底该选轴向/厚度充磁，还是径向充磁。

背景：
  探针轴沿 Z，磁环套在 P125 管身上随探针上下移动；A1324 侧置在 +X，
  默认敏感方向朝 -X，测 Bx；霍尔管芯 r = 5.90 mm，霍尔中心 Z79.00，
  有效行程 3.00 mm，即磁环相对霍尔中心 z_rel 从 +1.5 扫到 -1.5 mm。

本脚本把「径向」拆成两种常见解释一起核算，避免术语混淆：
  'Z' : 轴向/厚度充磁，M 沿 Z，两端面分别为 N/S
  'X' : 直径两极（diametric，中文电商常叫径向），M 沿某一固定直径 ∥X
  'R' : 真辐射充磁（radiation），M 沿局部半径 e_r，内圆一极、外圆一极

结论不依赖商家：v12 测 Bx 的位形只能配 'Z' 轴向/厚度充磁。
"""
import io
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

MU0_4PI = 1e-7                       # mu0 / 4pi
BR = 1.17                            # N35, T
M = BR / (4 * np.pi * 1e-7)          # 磁化强度 A/m
NR, NPHI, NZ = 20, 120, 10
R_HALL = 5.90e-3                     # 探针轴 -> 霍尔管芯, m
ZS = np.linspace(1.5, -1.5, 13) * 1e-3   # 相对磁环中心, m


def voxels(ro, ri, h):
    """等体积圆环体元。返回 (vx, vy, vz, phi, mdv, m_total)，单位 m / A*m^2。"""
    r = np.sqrt(ri ** 2 + (np.arange(NR) + 0.5) / NR * (ro ** 2 - ri ** 2))
    p = (np.arange(NPHI) + 0.5) / NPHI * 2 * np.pi
    z = (np.arange(NZ) + 0.5) / NZ * h - h / 2
    R, P, Z = np.meshgrid(r, p, z, indexing='ij')
    vx = (R * np.cos(P)).ravel()
    vy = (R * np.sin(P)).ravel()
    vz = Z.ravel()
    phi = np.arctan2(vy, vx)
    dv = np.pi * (ro ** 2 - ri ** 2) / NR / NPHI * (h / NZ)
    mdv = M * dv
    m_total = M * np.pi * (ro ** 2 - ri ** 2) * h
    return vx, vy, vz, phi, mdv, m_total


def unit_moment(orient, phi):
    """每个体元磁矩的单位方向。"""
    if orient == 'Z':            # 轴向/厚度
        return np.zeros_like(phi), np.zeros_like(phi), np.ones_like(phi)
    if orient == 'X':            # 直径两极
        return np.ones_like(phi), np.zeros_like(phi), np.zeros_like(phi)
    if orient == 'R':            # 真辐射取向
        return np.cos(phi), np.sin(phi), np.zeros_like(phi)
    raise ValueError('unknown orientation: %s' % orient)


def field(v, orient, r, z):
    """观测点 (r, 0, z) 相对磁环中心的 (Bx, Bz)，单位 Gauss。"""
    vx, vy, vz, phi, mdv, _ = v
    ux, uy, uz = unit_moment(orient, phi)
    mx, my, mz = mdv * ux, mdv * uy, mdv * uz
    dx = r - vx
    dy = -vy
    dz = z - vz
    d2 = dx * dx + dy * dy + dz * dz
    d3 = d2 ** 1.5
    d5 = d2 ** 2.5
    mdot = mx * dx + my * dy + mz * dz
    bx = np.sum(MU0_4PI * (3 * mdot * dx / d5 - mx / d3)) * 1e4
    bz = np.sum(MU0_4PI * (3 * mdot * dz / d5 - mz / d3)) * 1e4
    return bx, bz


def curve(v, orient, comp):
    out = []
    for z in ZS:
        bx, bz = field(v, orient, R_HALL, z)
        out.append(bx if comp == 'Bx' else bz)
    return np.array(out)


def report(tag, a, note=''):
    d = np.diff(a)
    v = 2.5 + a * 5.0 / 1000.0       # A1324: 5 mV/G, 零场 2.5 V
    mono = np.all(d < 0) or np.all(d > 0)
    print('  %-44s 峰值 %7.1f G  输出 %5.2f..%5.2f V  零点 %7.1f G  %-5s %s'
          % (tag, np.max(np.abs(a)), v.min(), v.max(), a[6],
             '单调' if mono else '非单调', note))
    return dict(peak=float(np.max(np.abs(a))), vmin=float(v.min()),
                vmax=float(v.max()), zero=float(a[6]), mono=bool(mono), arr=a)


print('=' * 104)
print('一、充磁方向 × 霍尔敏感方向（同一尺寸 Ø6 / 内孔 Ø2.10 / 厚 2.00，r=5.90，行程 ±1.5 mm）')
print('=' * 104)
V = voxels(3.0e-3, 1.05e-3, 2.0e-3)
print('  N35 磁化强度 M = %.3e A/m，总磁矩 m = %.4f A*m^2，离散 %d 体元'
      % (M, V[5], NR * NPHI * NZ))
print()

CASES = [
    ('轴向/厚度 m∥Z · 测 Bx（v12 采用）', 'Z', 'Bx', '可用：奇函数，过零单调'),
    ('轴向/厚度 m∥Z · 测 Bz', 'Z', 'Bz', '不用：偶函数，零位有大直流'),
    ('直径两极 m∥X · 测 Bx（径向环照搬）', 'X', 'Bx', '不可用：偶函数 + 贴 5 V 轨'),
    ('直径两极 m∥X · 测 Bz（霍尔转 90°）', 'X', 'Bz', '理论可用，但要改霍尔窗/PCB'),
    ('辐射 m∥e_r · 测 Bx', 'R', 'Bx', '见下方说明'),
    ('辐射 m∥e_r · 测 Bz', 'R', 'Bz', '见下方说明'),
]
RES = {}
for tag, orient, comp, note in CASES:
    RES[(orient, comp)] = report(tag, curve(V, orient, comp), note)

print()
print('  轴向·测 Bx 逐点（z_rel mm : Bx G : A1324 V）：')
ax = RES[('Z', 'Bx')]['arr']
for i, z in enumerate(ZS):
    if i % 2 == 0:
        print('    %+5.2f : %8.1f G : %6.3f V'
              % (z * 1e3, ax[i], 2.5 + ax[i] * 5 / 1000))
print('  径向(直径两极)·测 Bx 逐点：')
rb = RES[('X', 'Bx')]['arr']
for i, z in enumerate(ZS):
    if i % 2 == 0:
        print('    %+5.2f : %8.1f G : %6.3f V'
              % (z * 1e3, rb[i], 2.5 + rb[i] * 5 / 1000))
print('  -> z=±1.5 mm 给同一电压，曲线不可逆；零位 %.0f G 使 A1324 计算输出 %.2f V，'
      '实际会贴 5 V 轨饱和。' % (rb[6], 2.5 + rb[6] * 5 / 1000))
print('  -> 真辐射充磁环的外场更弱且仍不满足「测 Bx 奇函数过零」这一条，也不改结论。')

print()
print('=' * 104)
print('二、我们该选的规格（全部按轴向/厚度充磁计算，P125 管身 Ø2.02，磁环腔 Ø6.40 × 高 2.00）')
print('=' * 104)
print('  %-26s %-22s %-9s %-14s %-10s %s'
      % ('规格 OD/ID/H (mm)', '内孔判定', '厚度判定', '峰值 / A1324', '零点斜率', '结论'))
CANDS = [
    (6.0, 2.10, 2.00, '推荐：内孔对 Ø2.02 单边留 0.04 胶缝'),
    (6.0, 2.00, 2.00, '不推荐：内孔比管身小 0.02，硬套会撑裂'),
    (6.0, 2.20, 2.00, '可代用：需点胶定心工装'),
    (6.0, 2.00, 2.50, '不可用：磁环腔只有 2.00 高'),
    (5.5, 2.65, 2.00, '不推荐：需 Ø2.65→Ø2.10 衬套，磁量更小'),
]
for od, id_, h, note in CANDS:
    vv = voxels(od / 2 * 1e-3, id_ / 2 * 1e-3, h * 1e-3)
    a = curve(vv, 'Z', 'Bx')
    slope = abs((a[7] - a[5]) / 0.5) * 5 / 1000
    vmin, vmax = 2.5 + a.min() * 5 / 1000, 2.5 + a.max() * 5 / 1000
    bore = ('合适' if id_ >= 2.02 and id_ <= 2.20 else
            ('过盈 %.2f' % (2.02 - id_) if id_ < 2.02 else '需衬套'))
    thick = '合适' if abs(h - 2.0) <= 0.1 else '装不下 +%.2f' % (h - 2.0)
    print('  Ø%-4.1f / 内%-5.2f / 厚%-5.2f   %-22s %-9s %5.1f G / %.2f..%.2f V  %-10.3f %s'
          % (od, id_, h, bore, thick, np.max(np.abs(a)), vmin, vmax, slope, note))

print()
print('=' * 104)
print('结论：v12 选【轴向/厚度充磁】圆环：Ø6 / 内孔 Ø2.10 / 厚 2.00 / N35 / 镀镍。')
print('      两端面分别为 N/S；A1324 保持现状测 Bx，霍尔窗、PCB、探针座、3D 模型都不用改。')
print('      不采用径向环；若误买径向环，必须把霍尔转 90° 改测 Bz 并重做霍尔窗/PCB，不推荐。')
print('=' * 104)
