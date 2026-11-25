# -*- coding: utf-8 -*-
"""商家标称 Ø6/内2/厚2 轴向磁环、尺寸公差 ±0.2 mm 时的容差敏感性核算。

假定磁环底部贴在 R125 针套顶面 Z76.50，厚度 H 变化会让磁环中心偏移
delta = (H - 2.00)/2，霍尔中心固定 Z79.00，行程 3 mm。
"""
import io
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

MU0_4PI = 1e-7
M = 1.17 / (4 * np.pi * 1e-7)
NR, NPHI, NZ = 20, 120, 10
R_HALL = 5.90e-3


def voxels(ro, ri, h):
    r = np.sqrt(ri ** 2 + (np.arange(NR) + 0.5) / NR * (ro ** 2 - ri ** 2))
    p = (np.arange(NPHI) + 0.5) / NPHI * 2 * np.pi
    z = (np.arange(NZ) + 0.5) / NZ * h - h / 2
    R, P, Z = np.meshgrid(r, p, z, indexing='ij')
    vx = (R * np.cos(P)).ravel()
    vy = (R * np.sin(P)).ravel()
    vz = Z.ravel()
    dv = np.pi * (ro ** 2 - ri ** 2) / NR / NPHI * (h / NZ)
    return vx, vy, vz, M * dv


def bx_at(v, z_rel_m):
    vx, vy, vz, mdv = v
    dx = R_HALL - vx
    dy = -vy
    dz = z_rel_m - vz
    r2 = dx * dx + dy * dy + dz * dz
    return float(np.sum(3 * MU0_4PI * mdv * dx * dz / r2 ** 2.5) * 1e4)


def evaluate(od, id_, h, bottom_fixed=True):
    v = voxels(od / 2 * 1e-3, id_ / 2 * 1e-3, h * 1e-3)
    delta = (h - 2.0) / 2 if bottom_fixed else 0.0
    zs = np.linspace(1.5 - delta, -1.5 - delta, 25) * 1e-3
    b = np.array([bx_at(v, z) for z in zs])
    vv = 2.5 + b * 5 / 1000
    slope = abs(b[13] - b[11]) / (abs(zs[13] - zs[11]) * 1e3) * 5 / 1000
    return np.max(np.abs(b)), vv.min(), vv.max(), slope, bool(np.all(np.diff(b) < 0) or np.all(np.diff(b) > 0))


print('=' * 100)
print('一、内孔公差 / 衬套方案（外径 6.00，厚 2.00，轴向充磁，底部固定）')
print('=' * 100)
print('  %-24s %-10s %-16s %-12s %s' % ('规格 OD/ID/H', '峰值 G', 'A1324 输出', '斜率 V/mm', '装配判定'))
for id_ in (2.00, 2.02, 2.05, 2.10, 2.20, 2.50, 3.00, 3.50):
    p, vmin, vmax, s, mono = evaluate(6.0, id_, 2.0)
    fit = ('过盈 %.2f' % (2.02 - id_)) if id_ < 2.02 else \
          ('刚好/无胶缝' if id_ < 2.05 else ('可用' if id_ <= 2.20 else '需衬套'))
    print('  Ø6 / 内%-5.2f / 厚2.00   %-10.1f %-16s %-12.3f %s%s'
          % (id_, p, '%.2f..%.2f V' % (vmin, vmax), s, fit, '' if mono else ' [非单调]'))

print()
print('=' * 100)
print('二、厚度公差（外径 6.00 / 内孔 2.10，底部固定 Z76.50，磁环中心随厚度偏移）')
print('=' * 100)
print('  %-12s %-12s %-10s %-16s %-12s %s' % ('厚度 mm', '中心偏移', '峰值 G', 'A1324 输出', '斜率 V/mm', '判定'))
for h in (1.80, 1.90, 2.00, 2.10, 2.20, 2.30):
    p, vmin, vmax, s, mono = evaluate(6.0, 2.10, h)
    print('  %-12.2f %+8.2f mm  %-10.1f %-16s %-12.3f %s'
          % (h, (h - 2.0) / 2, p, '%.2f..%.2f V' % (vmin, vmax), s,
             '单调' if mono else '非单调'))

print()
print('=' * 100)
print('三、外径公差（内孔 2.10 / 厚 2.00，磁环腔 Ø6.40）')
print('=' * 100)
print('  %-12s %-12s %-10s %-16s %-12s %s' % ('外径 mm', '单边余量', '峰值 G', 'A1324 输出', '斜率 V/mm', '装配判定'))
for od in (5.80, 5.90, 6.00, 6.10, 6.20, 6.30):
    p, vmin, vmax, s, mono = evaluate(od, 2.10, 2.0)
    print('  %-12.2f %-12.2f %-10.1f %-16s %-12.3f %s'
          % (od, (6.40 - od) / 2, p, '%.2f..%.2f V' % (vmin, vmax), s,
             '可放入' if od <= 6.30 else '需扩腔'))

print()
print('=' * 100)
print('结论：内孔是唯一硬门槛；外径 ≤6.20、厚度 1.8~2.3 都可通过垫片/胶缝/标定吸收。')
print('      内孔 <2.05 时不要用 P125 Ø2.02 管身硬套；>2.20 时改衬套方案。')
print('=' * 100)
