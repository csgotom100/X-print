# -*- coding: utf-8 -*-
"""v12 磁路精算：用「磁化体元数值积分」替代点偶极子近似。

[p125_calc.py 的错误]
  把「磁环外表面到霍尔感测面的气隙 2.0 mm」当成了偶极子公式里的径向距离 r。
  偶极子公式里的 r 是「磁体轴线 -> 观测点」的距离，
  本模型探针轴 X78，霍尔感测面 X83.40（管芯再往里约 0.5），
  所以 v12 的 r = 5.90 mm，而不是 2.0 / 2.4 mm 的表面气隙。
  Br 斜率 ~ 1/r^4，(5/2)^4 ≈ 39 倍，直接导致「±5651 G 严重饱和」的误判。

[本脚本]
  轴向/厚度充磁磁环不是点偶极子（外径 Ø6，观测点距表面仅 2.4 mm），
  按均匀磁化 M 离散成圆环体元，逐元叠加偶极场，直接积分求 Bx。
  给出 Bx-行程曲线、单调区、A1324 输出电压、饱和判定。

  磁环：Ø6 / 内孔 Ø2.10 × 厚 2.00，N35，Br = 1.17 T，轴向（+Z）充磁
  霍尔：A1324LUA-T，5.0 mV/G，Vcc 5 V，零场 2.5 V，保守线性区 ±400 G
  v12 设计点：霍尔中心 Z79.00，管芯 r = 5.90 mm，有效行程 3.00 mm
"""
import io
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

MU0_4PI = 1.0e-7
BR_REM = 1.17                      # T, N35 剩磁
M = BR_REM / (4 * np.pi * 1e-7)    # A/m 磁化强度

RO, RI, H = 3.0e-3, 1.05e-3, 2.0e-3     # m（内孔 Ø2.10）
NR, NPHI, NZ = 20, 120, 10

# ---- 等面积圆环体元（每个体元体积相同）----
r = np.sqrt(RI**2 + (np.arange(NR) + 0.5) / NR * (RO**2 - RI**2))
phi = (np.arange(NPHI) + 0.5) / NPHI * 2 * np.pi
z = (np.arange(NZ) + 0.5) / NZ * H - H / 2
DV = np.pi * (RO**2 - RI**2) / NR / NPHI * (H / NZ)

RR, PP, ZZ = np.meshgrid(r, phi, z, indexing='ij')
VX = (RR * np.cos(PP)).ravel()
VY = (RR * np.sin(PP)).ravel()
VZ = ZZ.ravel()
MDV = M * DV                       # 每个体元的磁矩 A*m^2

print('=' * 78)
print('磁环离散：%d 体元，单体元磁矩 %.4e A*m^2，总磁矩 %.4f A*m^2'
      % (VX.size, MDV, MDV * VX.size))
print('=' * 78)


def bx_at(sensor_r, sensor_z_rel):
    """观测点 (r=sensor_r, y=0, z=sensor_z_rel) 相对磁环中心的 Bx，单位 Gauss。"""
    dx = sensor_r - VX
    dy = -VY
    dz = sensor_z_rel - VZ
    R5 = (dx * dx + dy * dy + dz * dz) ** 2.5
    return float(np.sum(3.0 * MU0_4PI * MDV * dx * dz / R5) * 1.0e4)


SENS = {'A1324': 5.000, 'A1325': 3.125, 'A1326': 2.500, 'SS49E': 1.400}  # mV/G
HALL_Z = 79.00                     # v12：霍尔中心 Z79.00
MAG_Z0 = 77.50                     # 自由位磁环中心
STROKE = 3.00

for hall_r in (5.0, 5.5, 5.9, 6.0):
    tag = '  <-- v12 设计点' if abs(hall_r - 5.9) < 1e-9 else ''
    print()
    print('=' * 78)
    print('霍尔感测管芯距探针轴 r = %.1f mm（磁环外缘气隙 %.1f mm）%s'
          % (hall_r, hall_r - 3.0, tag))
    print('=' * 78)
    print('  %-9s %-9s %-12s %-12s %-12s' %
          ('行程(mm)', 'z_rel(mm)', 'Bx(G)', 'A1324(V)', 'SS49E(V)'))
    rows = []
    for i in range(0, 13):
        s = i * 0.25                       # 0 ~ 3.00 mm
        mag_z = MAG_Z0 + s
        zrel = HALL_Z - mag_z              # 霍尔相对磁环中心
        b = bx_at(hall_r * 1e-3, zrel * 1e-3)
        v = 2.5 + b * SENS['A1324'] / 1000.0
        vs = 2.5 + b * SENS['SS49E'] / 1000.0
        rows.append((s, zrel, b, v))
        if i % 2 == 0:
            print('  %-9.2f %-9.2f %-12.1f %-12.3f %-12.3f' %
                  (s, zrel, b, v, vs))
    bs = np.array([x[2] for x in rows])
    ss = np.array([x[0] for x in rows])
    vv = np.array([x[3] for x in rows])
    # 零交叉附近斜率
    i0 = int(np.argmin(np.abs(bs)))
    if 0 < i0 < len(bs) - 1:
        slope = (bs[i0 + 1] - bs[i0 - 1]) / (ss[i0 + 1] - ss[i0 - 1])
    else:
        slope = (bs[1] - bs[0]) / (ss[1] - ss[0])
    d = np.diff(bs)
    mono = bool(np.all(d < 0) or np.all(d > 0))
    print('  ---')
    print('  峰值 |Bx|        = %.1f G' % np.max(np.abs(bs)))
    print('  零点附近斜率     = %.1f G/mm  -> A1324 %.3f V/mm'
          % (abs(slope), abs(slope) * SENS['A1324'] / 1000.0))
    print('  A1324 输出范围   = %.3f .. %.3f V' % (vv.min(), vv.max()))
    print('  ±400G 线性区     = %s' % ('OK' if np.max(np.abs(bs)) < 400 else '超出'))
    print('  全程单调         = %s' % ('是' if mono else '否（有极值，需限定量程）'))
    print('  12bit ADC 分辨率 = %.4f mm/LSB'
          % (5.0 / 4096 / (abs(slope) * SENS['A1324'] / 1000.0)))

print()
print('=' * 78)
print('结论提示：点偶极子近似只适用于观测距离 >> 磁体尺寸；')
print('          本例 r/RO ≈ 1.7~2.0，必须以体元积分或实物标定为准。')
print('          r=5.9 / Z79.00 为 v12 设计点；磁环必须轴向/厚度充磁。')
print('=' * 78)
