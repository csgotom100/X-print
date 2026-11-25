# -*- coding: utf-8 -*-
"""v13.2 接触式测高探针总成 — 零件图（8 视图 + 针尖放大详图）。

文件名保留 draw_parts_v12.py，内容已同步 v13.2 注塑结构：
  * ③ 探针座：Z76.50..81.50 改为 8×8 磁环全行程通道（含 +3.0 mm 满程位置）；
    Z81.50..87.50 为 6.20 弹簧导向段；Z87.50..90.00 为座体一体顶棚，中心只留 Ø2.50；
    左侧橙色件为 `HP45_SpringSpacer` 复用对象名后的 -X 侧盖板。
  * ⑤ 弹簧 Ø6 规格不变，靠 6.20 窄腔单边 0.10 紧导向防偏斜；预压仍由顶棚 Z87.50 建立。
  * ⑦ 装配剖视同步为「磁环/弹簧 +X 侧装 → 探针 -Z 顶落 → 原位点胶 → 盖板 +X 扣合」。
  * 磁环零位台阶 Z76.50+2.00 / Z 轴 22.00 / r 5.90 / 霍尔中心 Z79.00 均未改动。

v13 在 Z78.50 用 6.40/6.20 分段，视图上留下 4 处微错台（用户所指「不连续小平面」）；
v13.2 把分段面上移到 Z81.50，错台收敛为一处近似对称环形台阶。
v13.2 脱模阻挡 = 0、静态干涉 = 0、混合装配阻塞 = 0、行程干涉 = 0，见 verify_v13_2.py。

替换旧版「定制黄铜针管 / Ø1.6 柱塞杆 / Ø3×3 径向磁铁」图纸。
输出：C:/ink/refs/pogo_parts_drawing.png

排版要点：
  - ①~⑥ 为等比例细长件，说明文字用 fig.text 按「子图单元格」宽度排，
    避免等比例坐标系把文字挤成窄条；
  - ⑦ 装配剖视里针尖 0.30 / 0.90 mm 的尺寸链在 32 mm 全高下分辨不出来，
    单独做「详 A」放大详图，主图只留三条细基准线。
"""
import io
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'pogo_parts_drawing.png')

C_MET = '#d9a441'; C_MET_E = '#8a6520'
C_RES = '#c5ccd3'; C_RES_E = '#3d4b5a'
C_MAG = '#8e44ad'; C_MAG_E = '#5b2c6f'
C_SPR = '#3498db'
C_HALL = '#1a1a1a'
C_PCB = '#1e8449'
C_SEAL = '#e8c9a0'; C_SEAL_E = '#a67c52'   # 防尘唇（毛毡/硅胶）
C_COV = '#b0bec5'; C_COV_E = '#546e7a'     # 霍尔盖板 / 护线套
C_SPC = '#f0b27a'; C_SPC_E = '#a04000'     # v13 -X 侧盖板（复用 HP45_SpringSpacer 对象名）
DIM = '#c0392b'
TXT = '#2c3e50'

fig = plt.figure(figsize=(18.0, 15.6), dpi=150)
gs = fig.add_gridspec(3, 3, hspace=0.56, wspace=0.24,
                      left=0.035, right=0.985, top=0.925, bottom=0.085,
                      height_ratios=[1.0, 1.0, 1.18])
CAPTIONS = []


def caption(ax, lines):
    CAPTIONS.append((ax, lines))


def dh(ax, x1, x2, y, txt, off=0.34, fs=9.2):
    ax.annotate('', xy=(x1, y), xytext=(x2, y),
                arrowprops=dict(arrowstyle='<->', color=DIM, lw=1.0,
                                shrinkA=0, shrinkB=0))
    ax.text((x1 + x2) / 2, y + off, txt, fontsize=fs, color=DIM,
            ha='center', va='bottom', fontweight='bold')


def dv(ax, y1, y2, x, txt, off=0.30, fs=9.2):
    ax.annotate('', xy=(x, y1), xytext=(x, y2),
                arrowprops=dict(arrowstyle='<->', color=DIM, lw=1.0,
                                shrinkA=0, shrinkB=0))
    ax.text(x + off, (y1 + y2) / 2, txt, fontsize=fs, color=DIM,
            ha='left', va='center', rotation=90, fontweight='bold')


def lead(ax, xy, tx, ty, s, col=TXT, fs=8.8, ha='left'):
    ax.annotate(s, xy=xy, xytext=(tx, ty), fontsize=fs, color=col,
                ha=ha, va='center',
                arrowprops=dict(arrowstyle='-', color='#95a5a6', lw=0.8))


# ==================== ① 华荣 P125 探针 ====================
ax = fig.add_subplot(gs[0, 0])
ax.set_title('① 华荣 P125 测试探针  ×1（内弹簧锁死）', fontsize=11.8, fontweight='bold', pad=9)
ax.add_patch(Rectangle((-1.01, 2.0), 2.02, 31.35, fc=C_MET, ec=C_MET_E, lw=1.2))
ax.add_patch(Circle((0, 2.0), 1.01, fc=C_MET, ec=C_MET_E, lw=1.2))
ax.add_patch(Rectangle((-1.01, 2.0), 1.01, 31.35, fc='white', ec='none'))
ax.add_patch(Rectangle((-0.62, 4.0), 1.24, 12.0, fc='#ecf0f1', ec='#7f8c8d', lw=0.8))
zz = np.linspace(16.0, 29.0, 300)
ax.plot(-0.55 * np.sin(zz * 2 * np.pi * 0.55), zz, color='#7f8c8d', lw=1.1)
ax.text(-0.05, 22.5, '内部弹簧·胶锁死', fontsize=7.4, color='#c0392b',
        ha='center', va='center', fontweight='bold', rotation=90)
ax.plot([0, 0], [0.5, 34.5], color='#7f8c8d', lw=0.7, ls='-.')
dh(ax, -1.01, 1.01, 34.6, 'Ø2.02', off=0.35)
dv(ax, 2.0, 33.35, 1.8, '33.35', off=0.30)
lead(ax, (0.55, 1.05), 3.1, 7.0, '圆头 R1.01', fs=8.4)
lead(ax, (1.01, 29.0), 3.1, 27.5, '管身 = 刚性滑杆', fs=8.4)
caption(ax, ['全行程 6.35（锁死不用）｜弹力标准 180 g，65 g 可定制',
             '内弹簧必须锁死，否则针头空缩、磁铁不动 → 无信号',
             '锁死后整支在 R125 针套内上下平移，磁铁随管身走'])
ax.set_xlim(-5.0, 8.0); ax.set_ylim(-20.0, 37.6)
ax.set_aspect('equal'); ax.axis('off')

# ==================== ② R125 针套 ====================
ax = fig.add_subplot(gs[0, 1])
ax.set_title('② R125 针套  ×1（切短）', fontsize=11.8, fontweight='bold', pad=9)
ax.add_patch(Rectangle((-1.18, 0), 2.36, 18.5, fc=C_MET, ec=C_MET_E, lw=1.2))
ax.add_patch(Rectangle((-1.05, 0), 2.10, 18.5, fc='white', ec=C_MET_E, lw=0.8))
ax.plot([-1.18, -1.18], [18.5, 30.0], color='#95a5a6', lw=1.0, ls='--')
ax.plot([1.18, 1.18], [18.5, 30.0], color='#95a5a6', lw=1.0, ls='--')
ax.plot([-1.18, 1.18], [30.0, 30.0], color='#95a5a6', lw=1.0, ls='--')
ax.text(0, 31.2, '原长 30.0（切掉）', fontsize=8.2, color='#7f8c8d', ha='center')
ax.plot([-1.18, 1.18], [18.5, 18.5], color=DIM, lw=2.0)
dh(ax, -1.18, 1.18, 20.6, 'Ø2.36', off=0.35)
dh(ax, -1.05, 1.05, -2.2, 'Ø2.10', off=0.32)
# v12.2：总高尺寸移到零件左侧，避免引线穿过旋转文字（同侧引线全在 x≥-0.9）
dv(ax, 0, 18.5, -2.6, '18.50 ±0.10', off=-0.30, fs=8.8)
lead(ax, (1.18, 11.5), 4.2, 15.0, '压入座孔 Ø2.37', fs=8.4)
lead(ax, (1.05, 4.0), 4.2, 4.5, '内壁镀金，探针滑动', fs=8.4)
caption(ax, ['探针 Ø2.02 / 内孔 Ø2.10 → 单边间隙 0.04',
             '顶面 Z76.50 兼作下行止挡｜外径 Ø2.36 配座孔 Ø2.37',
             '切短后端面去毛刺，垂直度 0.05'])
ax.set_xlim(-6.0, 13.0); ax.set_ylim(-18.0, 34.0)
ax.set_aspect('equal'); ax.axis('off')

# ========== ③ 探针座剖视（v13.2：8×8 全行程通道 + 6.20 导向段 + 侧盖板） ==========
ax = fig.add_subplot(gs[0, 2])
ax.set_title('③ 探针座 + −X 侧盖板  ×1', fontsize=11.8, fontweight='bold', pad=9)
ax.add_patch(Rectangle((-7.5, 0), 15.0, 32.0, fc=C_RES, ec=C_RES_E, lw=1.2))
# v13：沿 X 等截面的敞开槽；先挖到 -X 面外，再由盖板补形凸台填回 X70.50..75.00
ax.add_patch(Rectangle((-1.185, 0), 2.370, 18.50, fc='white', ec=C_RES_E, lw=0.9))
ax.add_patch(Rectangle((-7.5, 18.5), 11.50, 5.00, fc='white', ec=C_RES_E, lw=0.9))  # 8x8 通道 Z76.50..81.50
ax.add_patch(Rectangle((-7.5, 23.5), 10.60, 6.00, fc='white', ec=C_RES_E, lw=0.9))   # 6.20 导向 Z81.50..87.50
ax.add_patch(Rectangle((-1.25, 29.5), 2.50, 2.50, fc='white', ec=C_RES_E, lw=0.9))    # 顶棚中心 Ø2.50
ax.add_patch(Rectangle((3.0, 18.5), 4.5, 5.5, fc='white', ec=C_RES_E, lw=0.9))        # 霍尔窗
ax.plot([-7.5, 7.5], [29.5, 29.5], color=C_RES_E, lw=1.0)                              # 一体顶棚下表面
# 侧盖板：主板 + 两处等截面补形凸台
ax.add_patch(Rectangle((-9.40, 18.5), 1.90, 11.00, fc=C_SPC, ec=C_SPC_E, lw=1.0))
ax.add_patch(Rectangle((-7.50, 18.5), 3.50, 5.00, fc=C_SPC, ec=C_SPC_E, lw=0.9))  # 通道补形到 X74.00
ax.add_patch(Rectangle((-7.50, 23.5), 4.50, 6.00, fc=C_SPC, ec=C_SPC_E, lw=0.9))   # 导向凸台 Z81.50 起
ax.text(-8.45, 24.5, '[11] 盖板', fontsize=7.6, color=C_SPC_E, ha='center', va='center',
        rotation=90, fontweight='bold', bbox=dict(fc='white', ec='none', alpha=0.78, pad=0.4))
for sx in (-4.0, 4.0):
    ax.add_patch(Rectangle((sx - 1.25, 23.0), 2.5, 9.0, fc='none',
                           ec=C_RES_E, lw=0.8, ls='--'))
dh(ax, -7.5, 7.5, 33.6, '15.0', off=0.35)
dv(ax, 0, 32.0, -10.4, '32.0', off=-0.30)
ax.annotate('', xy=(-11.2, 30.6), xytext=(-8.0, 30.6),
            arrowprops=dict(arrowstyle='->', color=DIM, lw=1.0))
ax.text(-11.2, 31.1, '型芯 −X 抽出', fontsize=7.4, color=DIM, ha='left', va='bottom')
lead(ax, (1.185, 9.0), 9.0, 7.5, 'Ø2.37 针套孔（后钻/铰）', fs=8.0)
lead(ax, (3.2, 21.0), 9.0, 14.5, '8×8 磁环通道 Z76.50..81.50', fs=8.0)
lead(ax, (3.1, 26.0), 9.0, 23.5, '6.20 导向段 Z81.50..87.50', fs=8.0)
lead(ax, (1.25, 31.2), 9.0, 30.5, '一体顶棚 Ø2.50（v13.2）', fs=8.0)
lead(ax, (5.2, 21.2), 9.0, 19.0, '霍尔窗 4.5×3.2', fs=8.4)
caption(ax, ['Z58..90｜8×8 磁环通道 Z76.50..81.50；6.20 弹簧导向段 Z81.50..87.50',
             '两段沿 X 等截面，型芯 −X 抽出；Ø6 弹簧单边 0.10 紧导向防偏斜',
             'POM / PA66+GF30：1.5° / R0.4 / 壁厚 2.0；橙色 = −X 侧盖板 + 两凸台'])
ax.set_xlim(-12.0, 17.0); ax.set_ylim(-18.0, 36.0)
ax.set_aspect('equal'); ax.axis('off')

# ==================== ④ 轴向/厚度充磁磁环 ====================
ax = fig.add_subplot(gs[1, 0])
ax.set_title('④ 磁环 Ø6 / 内孔Ø2.10 × 厚2.00 轴向充磁  ×1', fontsize=11.0, fontweight='bold', pad=9)
ax.add_patch(Rectangle((-3.0, 0), 6.0, 2.0, fc=C_MAG, ec=C_MAG_E, lw=1.2))
ax.add_patch(Rectangle((-1.05, 0), 2.10, 2.0, fc='white', ec=C_MAG_E, lw=0.9))
for xx in (-2.3, -1.7, 1.7, 2.3):
    ax.annotate('', xy=(xx, 3.0), xytext=(xx, 0.3),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.5))
ax.text(0, 3.6, 'N ↑  磁化方向沿轴线 (+Z)  S ↓', fontsize=8.8,
        color='#c0392b', ha='center', fontweight='bold')
dh(ax, -3.0, 3.0, -1.6, 'Ø6.00', off=-1.25, fs=8.8)
dh(ax, -1.05, 1.05, 5.0, 'Ø2.10（套 Ø2.02 管身，单边胶缝 0.04）', off=0.30, fs=7.8)
dv(ax, 0, 2.0, 3.9, '2.00', off=0.28)
caption(ax, ['N35 钕铁硼，Br ≥ 11.7 kG，镀镍；Z76.50..78.50 环氧粘管身',
             '必须轴向/厚度充磁：两端面分别为 N/S，圆周无 N-S 交替',
             '本 v12 测 Bx 位形下，径向环的 Bx(z) 为偶函数 → 标定不可逆'])
ax.set_xlim(-6.5, 9.0); ax.set_ylim(-8.8, 6.6)
ax.set_aspect('equal'); ax.axis('off')

# ==================== ⑤ 外部轻弹簧 ====================
ax = fig.add_subplot(gs[1, 1])
ax.set_title('⑤ 外部回位弹簧  ×1（接触力来源）', fontsize=11.8, fontweight='bold', pad=9)
zs = np.linspace(0, 10.0, 900)
ax.plot(2.7 * np.sin(zs * 2 * np.pi * 1.2), zs, color=C_SPR, lw=1.6)
ax.plot([-3.0, 3.0], [0, 0], color=C_SPR, lw=2.4)
ax.plot([-3.0, 3.0], [10.0, 10.0], color=C_SPR, lw=2.4)
ax.plot([0, 0], [-1.0, 11.0], color='#95a5a6', lw=0.7, ls='-.')
dh(ax, -3.0, 3.0, 11.4, 'Ø6.00 外径', off=0.35)
dv(ax, 0, 10.0, -4.2, '10.00 自由高', off=0.28, fs=8.6)
lead(ax, (2.7, 5.0), 5.2, 7.0, '线径 Ø0.30 / 12 圈', fs=8.4)
caption(ax, ['自由高 10.00 → 装配高 9.00（Z78.50..87.50）',
             '由座体一体顶棚 Z87.50 压出 1.00 mm 预压（独立顶塞已取消）',
             'k = G·d⁴/(8·D³·n) = 0.045 N/mm；Ø6 不缩小（缩小 OD 会抬高 F0）',
             'F0 = 0.045 N（≈4.6 gf），满程 0.180 N，目标 0.03~0.08 N'])
ax.set_xlim(-6.0, 10.5); ax.set_ylim(-8.6, 13.2)
ax.set_aspect('equal'); ax.axis('off')

# ==================== ⑥ 霍尔 + PCB ====================
ax = fig.add_subplot(gs[1, 2])
ax.set_title('⑥ A1324 + 转接 PCB + 调整垫片', fontsize=11.8, fontweight='bold', pad=9)
ax.add_patch(Rectangle((0, 0), 1.50, 4.19, fc=C_HALL, ec='#000', lw=1.2))
ax.add_patch(Rectangle((1.50, -0.10), 0.60, 4.40, fc=C_PCB, ec=C_PCB, lw=1.0))
ax.add_patch(Rectangle((-0.50, 0), 0.50, 4.19, fc='#f1c40f', ec='#b7950b', lw=0.9))
ax.annotate('', xy=(-1.4, 2.1), xytext=(-0.1, 2.1),
            arrowprops=dict(arrowstyle='->', color=DIM, lw=1.6))
ax.text(-0.75, 2.65, 'Bx', fontsize=9.2, color=DIM, ha='center', fontweight='bold')
for xx in (0.4, 0.75, 1.1):
    ax.plot([xx, xx], [0, -2.4], color='#999', lw=1.3)
dh(ax, 0, 1.50, 5.1, '1.50', off=0.32)
dv(ax, 0, 4.19, 2.5, '4.19', off=0.28)
lead(ax, (-0.25, 3.2), 3.5, 5.6, '0.2 / 0.5 垫片（调 r）', col='#b7950b', fs=8.4)
lead(ax, (0.75, 3.6), 3.5, 4.1, '有字面 = 感测面，朝 −X', fs=8.4)
lead(ax, (1.8, 1.0), 3.5, 1.2, 'PCB 0.6×2.6×4.4', fs=8.4)
caption(ax, ['5.0 mV/G｜Vcc 5 V｜零场 2.50 V｜输出 1.43~3.57 V 全程单调',
             '感测面 X83.40 → 管芯 X83.90 → 磁路半径 r = 5.90',
             '霍尔中心 Z79.00（磁环中心 Z77.50）；垫片可微调 ±0.5'])
ax.set_xlim(-3.8, 11.6); ax.set_ylim(-8.6, 7.2)
ax.set_aspect('equal'); ax.axis('off')

# ==================== ⑦ 装配剖视（v13 混合装配） ====================
ax = fig.add_subplot(gs[2, 0:2])
ax.set_title('⑦ 装配剖视与尺寸链 v13.2 注塑（X–Z 面，Y = −112.50）', fontsize=11.8, fontweight='bold', pad=9)
ax.add_patch(Rectangle((-7.5, 0), 15.0, 32.0, fc=C_RES, ec=C_RES_E, lw=1.2))
# 座体：敞开 U 型槽 + 一体顶棚中心孔
ax.add_patch(Rectangle((-1.185, 0), 2.370, 18.50, fc='white', ec=C_RES_E, lw=0.9))
ax.add_patch(Rectangle((-7.5, 18.5), 11.50, 5.00, fc='white', ec=C_RES_E, lw=0.9))  # 8x8 通道
ax.add_patch(Rectangle((-7.5, 23.5), 10.60, 6.00, fc='white', ec=C_RES_E, lw=0.9))   # 6.20 导向
ax.add_patch(Rectangle((-1.25, 29.5), 2.50, 2.50, fc='white', ec=C_RES_E, lw=0.9))
ax.add_patch(Rectangle((3.0, 18.5), 4.5, 5.5, fc='white', ec=C_RES_E, lw=0.9))
ax.plot([-7.5, 7.5], [29.5, 29.5], color=C_RES_E, lw=1.0)     # 顶棚下表面 = 弹簧止挡
# -X 侧盖板：主板 + 两处补形凸台
ax.add_patch(Rectangle((-9.40, 18.5), 1.90, 11.00, fc=C_SPC, ec=C_SPC_E, lw=1.0))
ax.add_patch(Rectangle((-7.50, 18.5), 3.50, 5.00, fc=C_SPC, ec=C_SPC_E, lw=0.9))  # 通道补形到 X74.00
ax.add_patch(Rectangle((-7.50, 23.5), 4.50, 6.00, fc=C_SPC, ec=C_SPC_E, lw=0.9))   # 导向凸台 Z81.50 起
ax.text(-8.45, 19.8, '[11] 盖板', fontsize=7.6, color=C_SPC_E, ha='center', va='center',
        rotation=90, fontweight='bold', bbox=dict(fc='white', ec='none', alpha=0.78, pad=0.4))
# 内部运动件
ax.add_patch(Rectangle((-1.18, 0), 0.13, 18.5, fc=C_MET, ec='none'))
ax.add_patch(Rectangle((1.05, 0), 0.13, 18.5, fc=C_MET, ec='none'))
ax.add_patch(Rectangle((-1.01, -1.0), 2.02, 32.35, fc=C_MET, ec=C_MET_E, lw=1.0))
ax.add_patch(Circle((0, 0.01), 1.01, fc=C_MET, ec=C_MET_E, lw=1.0))
ax.add_patch(Rectangle((-3.0, 18.5), 6.0, 2.0, fc=C_MAG, ec=C_MAG_E, lw=1.0))
ax.add_patch(Rectangle((-1.01, 18.5), 2.02, 2.0, fc=C_MET, ec='none'))
zs2 = np.linspace(20.5, 29.5, 500)   # 装配高 9.00：Z78.50..87.50
ax.plot(2.7 * np.sin(zs2 * 2 * np.pi * 0.6), zs2, color=C_SPR, lw=1.4)
ax.add_patch(Rectangle((5.4, 18.9), 1.50, 4.19, fc=C_HALL, ec='#000', lw=1.0))
ax.add_patch(Rectangle((6.9, 18.8), 0.60, 4.40, fc=C_PCB, ec=C_PCB, lw=0.8))
# 原位点胶提示：磁环内孔与针身之间的胶缝
ax.add_patch(Rectangle((-1.10, 18.5), 0.12, 2.00, fc='#c0392b', ec='none', alpha=0.9))

# --- 其余结构件（剖视，坐标 = Z−58.00 / X−78.00）---
# [9] 防尘唇 Ø6/内孔Ø2.10×0.80，Z57.20..58.00 -> z −0.80..0
for x0 in (-3.0, 1.05):
    ax.add_patch(Rectangle((x0, -0.80), 1.95, 0.80,
                           fc=C_SEAL, ec=C_SEAL_E, lw=0.9))
ax.text(-3.35, -0.40, '[9]', fontsize=8.4, color=C_SEAL_E,
        ha='right', va='center', fontweight='bold')
# [10] 霍尔盖板 X85.50..85.80 / Z76.50..82.50，中央 Ø3.2 出线孔
for z0, h in ((18.5, 0.90), (22.6, 1.90)):
    ax.add_patch(Rectangle((7.5, z0), 0.30, h,
                           fc=C_COV, ec=C_COV_E, lw=0.9))
# [12] 出线护线套 X85.80..87.30 / Z77.50..80.50，Ø2.4 线孔
for z0, h in ((19.5, 0.30), (22.2, 0.30)):
    ax.add_patch(Rectangle((7.8, z0), 1.50, h,
                           fc=C_COV, ec=C_COV_E, lw=0.9, hatch='///'))
ax.text(7.35, 24.0, '[10]', fontsize=8.4, color=C_COV_E,
        ha='right', va='center', fontweight='bold')
ax.text(9.45, 21.0, '[12]', fontsize=8.4, color=C_COV_E,
        ha='left', va='center', fontweight='bold')
# v13 混合装配箭头
ax.annotate('', xy=(-8.0, 25.2), xytext=(-11.5, 25.2),
            arrowprops=dict(arrowstyle='->', color=DIM, lw=1.0))
ax.text(-11.5, 25.8, '磁环 / 弹簧 +X', fontsize=7.4, color=DIM, ha='left')
ax.annotate('', xy=(-8.0, 28.0), xytext=(-11.5, 28.0),
            arrowprops=dict(arrowstyle='->', color=DIM, lw=1.0))
ax.text(-11.5, 28.6, '盖板 +X', fontsize=7.4, color=DIM, ha='left')
ax.annotate('', xy=(-2.0, 29.8), xytext=(-2.0, 33.5),
            arrowprops=dict(arrowstyle='->', color=DIM, lw=1.0))
ax.text(-2.4, 32.7, '针 −Z', fontsize=7.4, color=DIM, ha='right')
# 三条基准线（不标文字，靠左下详图 A 放大）
ax.plot([-10.0, 10.0], [-0.10, -0.10], color='#c0392b', lw=1.4, ls='--')
ax.plot([-10.0, 10.0], [-1.00, -1.00], color='#1e8449', lw=1.0, ls=':')
ax.plot([-10.0, 10.0], [-1.30, -1.30], color='#8B6F47', lw=2.0)
ax.text(-2.6, -3.0, 'A', fontsize=11, color='#c0392b', fontweight='bold',
        ha='center', bbox=dict(boxstyle='circle,pad=0.2', fc='white', ec='#c0392b'))
ax.annotate('', xy=(-1.0, -1.3), xytext=(-2.2, -2.6),
            arrowprops=dict(arrowstyle='-', color='#c0392b', lw=0.9))
ax.annotate('', xy=(-9.2, 18.5), xytext=(-9.2, 21.5),
            arrowprops=dict(arrowstyle='<->', color=DIM, lw=1.0,
                            shrinkA=0, shrinkB=0))
ax.text(-9.2, 23.2, '行程 3.00', fontsize=8.4, color=DIM,
        ha='center', fontweight='bold')
# r 标注放在壳体上方，避开弹簧
ax.annotate('', xy=(0.0, 34.0), xytext=(5.9, 34.0),
            arrowprops=dict(arrowstyle='<->', color=DIM, lw=1.1))
ax.plot([0, 0], [32.0, 34.3], color='#95a5a6', lw=0.7, ls=':')
ax.plot([5.9, 5.9], [23.0, 34.3], color='#95a5a6', lw=0.7, ls=':')
ax.text(2.95, 34.5, 'r = 5.90（探针轴 → 霍尔管芯）', fontsize=8.6, color=DIM,
        ha='center', fontweight='bold')
lead(ax, (-1.1, 8.0), 9.0, 5.0, 'R125 针套  Z58.00..76.50', fs=8.4)
lead(ax, (-2.6, 19.5), 9.0, 11.0, '磁环  Z76.50..78.50（零位，原位点胶）', fs=8.2)
lead(ax, (2.6, 26.0), 9.0, 17.0, '弹簧 Ø6 / 6.20 紧导向（装配高 9.0）', fs=8.4)
lead(ax, (5.9, 21.0), 10.0, 22.5, 'A1324 中心 Z79.00', fs=8.4)
lead(ax, (0.0, 31.0), 9.0, 28.5, '针尾 Z90.35 伸出顶棚', fs=8.4)
lead(ax, (1.25, 30.8), 9.0, 31.8, '一体顶棚 Ø2.50 / 止挡 Z87.50', fs=8.2)
# 4 件辅助件名称统一放在图纸底部图注（避免说明框压住剖视内的标注）
ax.set_xlim(-12.5, 17.5); ax.set_ylim(-6.0, 36.5)
ax.set_aspect('equal'); ax.axis('off')

# ---- 详 A：针尖尺寸链放大（图级独立小坐标系，落在 ⑦ 左侧留白）----
axd = fig.add_axes([0.045, 0.105, 0.165, 0.135])
axd.set_xlim(0, 10); axd.set_ylim(0, 11); axd.axis('off')
axd.set_title('详 A　针尖尺寸链（纵向放大 7×）', fontsize=8.8,
              fontweight='bold', color=TXT, pad=4)
axd.plot([0.6, 9.4], [1.0, 1.0], color='#8B6F47', lw=3.0)
axd.plot([0.6, 9.4], [3.1, 3.1], color='#1e8449', lw=1.0, ls=':')
axd.plot([0.6, 9.4], [9.4, 9.4], color='#c0392b', lw=1.5, ls='--')
axd.add_patch(Rectangle((3.2, 3.1), 2.0, 5.6, fc=C_MET, ec=C_MET_E, lw=1.0))
axd.add_patch(Circle((4.2, 3.9), 1.0, fc=C_MET, ec=C_MET_E, lw=1.0))
axd.text(0.5, 9.7, '喷嘴面 Z57.90', fontsize=7.8, color='#c0392b', ha='left', fontweight='bold')
axd.text(0.5, 3.4, '针尖 Z57.00', fontsize=7.8, color='#1e8449', ha='left', fontweight='bold')
axd.text(0.5, 0.15, '蛋面 Z56.70', fontsize=7.8, color='#8B6F47', ha='left', fontweight='bold')
for (ya, yb, txt) in ((3.1, 9.4, '0.90'), (1.0, 3.1, '0.30')):
    axd.annotate('', xy=(9.0, ya), xytext=(9.0, yb),
                 arrowprops=dict(arrowstyle='<->', color='#1e8449', lw=1.0))
    axd.text(8.7, (ya + yb) / 2, txt, fontsize=7.8, color='#1e8449',
             ha='right', va='center', fontweight='bold')

# ==================== ⑧ 标定曲线 ====================
ax = fig.add_subplot(gs[2, 2])
ax.set_title('⑧ 磁路标定曲线（r = 5.90 mm）', fontsize=11.8, fontweight='bold', pad=9)
MU, M = 1e-7, 1.17 / (4 * np.pi * 1e-7)
RO, RI, H = 3.0e-3, 1.05e-3, 2.0e-3     # 内孔 Ø2.10
NR, NP, NZ = 20, 120, 10
r_ = np.sqrt(RI**2 + (np.arange(NR) + 0.5) / NR * (RO**2 - RI**2))
ph_ = (np.arange(NP) + 0.5) / NP * 2 * np.pi
z_ = (np.arange(NZ) + 0.5) / NZ * H - H / 2
R_, P_, Z_ = np.meshgrid(r_, ph_, z_, indexing='ij')
VX = (R_ * np.cos(P_)).ravel(); VY = (R_ * np.sin(P_)).ravel(); VZ = Z_.ravel()
MDV = M * (np.pi * (RO**2 - RI**2) / NR / NP * (H / NZ))


def bx(rr, zr):
    dx, dy, dz = rr - VX, -VY, zr - VZ
    return float(np.sum(3 * MU * MDV * dx * dz /
                        (dx * dx + dy * dy + dz * dz) ** 2.5) * 1e4)


stroke = np.linspace(0, 3.0, 25)
b = np.array([bx(5.9e-3, (1.5 - s) * 1e-3) for s in stroke])
v = 2.5 + b * 5.0 / 1000.0
ax.fill_between(stroke, 0.2, 4.8, color='#e8f6ef', alpha=0.6)
ax.axhline(2.5, color='#95a5a6', lw=0.9, ls='--')
ax.plot(stroke, v, color='#c0392b', lw=2.4)
ax.set_xlim(0, 3.0); ax.set_ylim(0, 5.0)
ax.set_xlabel('探针行程 / mm', fontsize=9.2)
ax.set_ylabel('A1324 输出 / V', fontsize=9.2)
ax.grid(alpha=0.28, lw=0.7); ax.tick_params(labelsize=8.4)
ax2 = ax.twinx()
ax2.set_ylim(-250, 250); ax2.set_ylabel('Bx / Gauss', fontsize=9.2, color='#8e44ad')
ax2.tick_params(labelsize=8.4, colors='#8e44ad')
ax.text(0.05, 0.09,
        '峰值 213.8 G｜输出 1.43~3.57 V\n全程单调、不饱和\n零点斜率 0.911 V/mm\n12 bit ADC ≈ 0.0013 mm/LSB\n零位 z_rel=+1.5 → 满程 −1.5',
        transform=ax.transAxes, fontsize=8.2, color=TXT,
        bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='#bdc3c7', alpha=0.94))
ax.text(2.94, 4.84, '轨 4.8 V', fontsize=7.2, color='#7f8c8d', ha='right')
ax.text(2.94, 0.26, '轨 0.2 V', fontsize=7.2, color='#7f8c8d', ha='right', va='bottom')

# ---- 说明文字：按子图单元格宽度排版 ----
for a_, lines in CAPTIONS:
    pos = a_.get_position(original=True)
    fig.text((pos.x0 + pos.x1) / 2, pos.y0 + 0.004, '\n'.join(lines),
             ha='center', va='bottom', fontsize=8.0, color='#465666',
             linespacing=1.42,
             bbox=dict(boxstyle='round,pad=0.32', fc='white',
                       ec='#dfe4e8', lw=0.6, alpha=0.95))

fig.suptitle('接触式连续测高探针总成 — 零件图 v13.2 注塑（8×8 磁环通道 + 6.20 弹簧导向）',
             fontsize=15.5, fontweight='bold', y=0.975)
fig.text(0.5, 0.012,
         '针尖 Z57.00（比喷嘴低 0.90 / 高于蛋面 0.30）｜有效行程 0~+3.00 mm 单向｜'
         '接触力 0.045 N（预压 1.0）｜r 5.90 / 霍尔中心 Z79.00｜输出 1.43~3.57 V 全程单调\n'
         '【v13.2 注塑】POM / PA66+GF30｜1.5° / R0.4 / 壁厚 2.0｜8×8 磁环全行程通道 Z76.50..81.50 + 6.20 弹簧导向段 Z81.50..87.50 + 一体顶棚 Ø2.50\n'
         '混合装配：磁环 / 弹簧 +X 侧装 → 探针 −Z 顶落 → 原位点胶 → 盖板 +X 扣合｜'
         '[9] 防尘唇 / [10] 霍尔盖板 / [12] 护线套\n'
         '磁环零位台阶高 2.00 = 机械限位｜弹簧 Ø6 不变 / F0 0.045 N｜Z 轴限位槽 22.00 冻结｜FCStd 151 对象｜'
         '脱模阻挡 0 / 静态干涉 0 / 侧装阻塞 0 / 行程干涉 0 / 冻结项 OK / 回写 OK',
         ha='center', va='bottom', fontsize=8.2, color=TXT, linespacing=1.30)

fig.savefig(OUT, bbox_inches='tight', facecolor='white')
print('saved:', os.path.abspath(OUT))
