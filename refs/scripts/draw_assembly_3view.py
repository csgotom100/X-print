# -*- coding: utf-8 -*-
"""霍尔传感连续测高探针总成 — 独立三视图装配图（v13.2 可注塑结构）。

版式沿用项目既有 A2 装配图（refs/HP45_Assembly_A2.png）：
  黑白工程线稿 / 内外图框 + 分区 / 右下标题栏 / 明细表 / 技术要求 /
  圆圈序号气泡 / 第一角画法 / 视图名标「（沿 -Y / -Z / -X）」。

视图配置（第一角画法，GB/T 14692）：
  主视图 A-A  沿 -Y 观察，剖切平面 Y = -112.50（过探针轴线），全剖；
               实心件（探针、霍尔、PCB）纵向按不剖绘制；
               +3.00 满程磁环位置用双点划线表示（运动件极限位置）。
  俯视图      沿 -Z 观察，配置在主视图正下方，X 与主视图对齐。
  左视图      沿 -X 观察，配置在主视图正右方，Z 与主视图对齐。
  D 向局部    从 +X 看霍尔出线侧，放大 1.6 倍，属补充向视图，不计入三视图。

坐标换算（数据坐标，单位 mm）：
  主/俯视图  u = X - 78.00        探针轴线 u = 0
  主/左视图  w = Z - 57.00        针尖自由位 w = 0
  俯视图     w = -12 - (Y + 112.50)
  左视图     v = 24 + (Y + 112.50)

几何来源：CrossSlide_P014013.FCStd（v13.2，151 对象）14 件真实几何，
以及 2026-11-10 verify_v13_2.py 的脱模 / 干涉 / 混合装配路径 / 全行程核验。
所有尺寸均为模型真值，非示意。

v13.2 修订（用户指出 v13 在 Z78.50 的「不连续小平面」，要求给磁环留正公差空间）：
  件3 探针座：Z76.50..81.50 改为 8×8 磁环全行程通道（覆盖 0..+3.0 mm 全部位置）；
               Z81.50..87.50 保留 6.20 窄腔给 Ø6 弹簧做单边 0.10 紧导向；
               Z87.50..90.00 仍为座体一体顶棚，中心仅留 Ø2.50 针尾孔。
  件6 侧盖板两处补形凸台同步改为「通道补形到 X74.00 / 导向凸台 Z81.50 起」。
  弹簧 Ø6 / Ø4.6 / 0.30 x 12 圈、k=0.045 N/mm、F0=0.045 N 不变：
  缩小外径在 k ∝ 1/D³ 下会抬高接触力，防偏斜靠窄腔导向而非缩簧。
  磁环零位台阶 Z76.50+2.00 / 霍尔 r 5.90 / 中心 Z79.00 / Z 轴 22.00 均冻结。
  verify_v13_2.py 结论：通道净空 OK / 脱模阻挡 0 / 静态干涉 0 / 装配阻塞 0 /
  行程干涉 0 / 8x8 越界 0 / 冻结项 OK / FCStd 回写 OK。

输出：refs/hall_probe_assembly_3view.png / .pdf
"""
import io
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Arc
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PNG = os.path.join(HERE, '..', 'hall_probe_assembly_3view.png')
OUT_PDF = os.path.join(HERE, '..', 'hall_probe_assembly_3view.pdf')

FIGW, FIGH, DPI = 19.2, 13.6, 170          # A2 横放比例 594:420 = 1.414
INK = '#20272e'                             # 轮廓 / 文字
LINE = '#4b565f'                            # 细实线
FAINT = '#98a2ab'                           # 中心线 / 假想线
DIMC = '#2c3e50'                            # 尺寸线
H1 = '#e9edf0'                              # 座体 / 探针填充
H2 = '#c9d0d6'                              # 针套 / -X 侧盖板填充
H3 = '#8d969e'                              # 磁环 / 霍尔元件填充
H4 = '#f4f6f7'                              # 弹簧 / PCB / 护线套填充

fig = plt.figure(figsize=(FIGW, FIGH), dpi=DPI, facecolor='white')

# ==================================================================== 图框
FR = Rectangle((0.008, 0.008), 0.984, 0.984, transform=fig.transFigure,
               fill=False, ec=INK, lw=1.6)
fig.add_artist(FR)
IR = Rectangle((0.030, 0.028), 0.940, 0.944, transform=fig.transFigure,
               fill=False, ec=INK, lw=0.9)
fig.add_artist(IR)

# 上下分区 1..8 / 左右分区 A..D
for i in range(1, 9):
    x = 0.030 + i * 0.940 / 8
    for y, va in ((0.0175, 'center'), (0.9830, 'center')):
        fig.text(x - 0.940 / 16, y, str(i), ha='center', va=va,
                 fontsize=7.4, color=LINE)
    if i < 8:
        fig.add_artist(plt.Line2D([x, x], [0.008, 0.030], transform=fig.transFigure,
                                  color=INK, lw=0.7))
        fig.add_artist(plt.Line2D([x, x], [0.972, 0.992], transform=fig.transFigure,
                                  color=INK, lw=0.7))
for i, ch in enumerate('ABCD'):
    y = 0.028 + (i + 0.5) * 0.944 / 4
    for x in (0.019, 0.981):
        fig.text(x, y, ch, ha='center', va='center', fontsize=7.4, color=LINE)
    if i < 3:
        yy = 0.028 + (i + 1) * 0.944 / 4
        for a, b in ((0.008, 0.030), (0.970, 0.992)):
            fig.add_artist(plt.Line2D([a, b], [yy, yy], transform=fig.transFigure,
                                      color=INK, lw=0.7))
# 四边中部对中三角
for x in (0.5,):
    fig.add_artist(Polygon([[x - .006, .008], [x + .006, .008], [x, .021]],
                           closed=True, transform=fig.transFigure,
                           fc=INK, ec=INK, lw=.5))
    fig.add_artist(Polygon([[x - .006, .992], [x + .006, .992], [x, .979]],
                           closed=True, transform=fig.transFigure,
                           fc=INK, ec=INK, lw=.5))
for y in (0.5,):
    fig.add_artist(Polygon([[.008, y - .006], [.008, y + .006], [.021, y]],
                           closed=True, transform=fig.transFigure,
                           fc=INK, ec=INK, lw=.5))
    fig.add_artist(Polygon([[.992, y - .006], [.992, y + .006], [.979, y]],
                           closed=True, transform=fig.transFigure,
                           fc=INK, ec=INK, lw=.5))

# ==================================================================== 主图区
XMIN, XMAX = -13.5, 36.0
YMIN, YMAX = -23.0, 38.5
AXRECT = [0.038, 0.055, 0.545, 0.900]
ax = fig.add_axes(AXRECT)
ax.set_xlim(XMIN, XMAX)
ax.set_ylim(YMIN, YMAX)
ax.set_aspect('equal', adjustable='box')
ax.axis('off')

scale_in = min(FIGW * AXRECT[2] / (XMAX - XMIN), FIGH * AXRECT[3] / (YMAX - YMIN))
RATIO = scale_in * 25.4                      # 图面 mm / 实物 mm

# ---------------------------------------------------------------- 绘图工具
def rect(x, y, w_, h_, fc='white', ec=INK, lw=1.0, ls='-', hatch=None, z=3):
    ax.add_patch(Rectangle((x, y), w_, h_, fc=fc, ec=ec, lw=lw,
                           linestyle=ls, hatch=hatch, zorder=z))


def hole(x, y, w_, h_):
    """全剖视图中把孔挖成白底并保留孔壁线。"""
    rect(x, y, w_, h_, fc='white', ec=LINE, lw=0.85, z=4)


def circ(x, y, r, fc='white', ec=INK, lw=1.0, ls='-', z=5):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=lw, linestyle=ls, zorder=z))


def ln(x1, y1, x2, y2, color=LINE, lw=0.7, ls='-', z=6):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw, ls=ls, zorder=z,
            solid_capstyle='butt')


def dash_center(x1, y1, x2, y2, color=FAINT):
    ln(x1, y1, x2, y2, color=color, lw=0.55, ls=(0, (6, 2, 1, 2)), z=2)


def txt(x, y, s, fs=7.0, ha='left', va='center', rot=0, color=INK,
        weight='normal', z=9):
    ax.text(x, y, s, fontsize=fs, ha=ha, va=va, rotation=rot, color=color,
            fontweight=weight, zorder=z)


def dh(x1, x2, y, s, fs=6.8, off=0.55):
    """水平尺寸线（两端箭头 + 尺寸界线）。"""
    ln(x1, y, x2, y, color=DIMC, lw=0.65)
    for xx in (x1, x2):
        ln(xx, y - 0.45, xx, y + 0.45, color=DIMC, lw=0.65)
        ax.annotate('', xy=(xx, y), xytext=(xx + (0.7 if xx == x1 else -0.7), y),
                    arrowprops=dict(arrowstyle='-|>', color=DIMC, lw=0.7,
                                    mutation_scale=5), zorder=8)
    txt((x1 + x2) / 2, y + off, s, fs=fs, ha='center', va='bottom',
        color=DIMC, weight='bold')


def dv(y1, y2, x, s, fs=6.8, off=0.55):
    """竖直尺寸线。"""
    ln(x, y1, x, y2, color=DIMC, lw=0.65)
    for yy in (y1, y2):
        ln(x - 0.45, yy, x + 0.45, yy, color=DIMC, lw=0.65)
        ax.annotate('', xy=(x, yy), xytext=(x, yy + (0.7 if yy == y1 else -0.7)),
                    arrowprops=dict(arrowstyle='-|>', color=DIMC, lw=0.7,
                                    mutation_scale=5), zorder=8)
    txt(x + off, (y1 + y2) / 2, s, fs=fs, ha='left', va='center',
        rot=90, color=DIMC, weight='bold')


def balloon(px, py, num, bx, by, r=0.92, fs=7.2):
    """序号气泡：px,py 指向点；bx,by 气泡中心。"""
    ln(px, py, bx, by, color=LINE, lw=0.6, z=7)
    circ(bx, by, r, fc='white', ec=INK, lw=0.9, z=8)
    txt(bx, by, str(num), fs=fs, ha='center', va='center', z=9)


def leader(px, py, tx, ty, s, fs=6.6, ha='left'):
    ln(px, py, tx, ty, color=LINE, lw=0.55, z=7)
    txt(tx + (0.15 if ha == 'left' else -0.15), ty, s, fs=fs, ha=ha, z=9)


# ==================================================================== ① 主视图 A-A（全剖）
txt(0.0, 37.5, '主视图 A-A（全剖，沿 -Y，剖切平面 Y = -112.50）',
    fs=9.4, ha='center', weight='bold')

# --- 件 3 探针座：v13.2 8x8 通道 + 6.20 导向段 + 一体顶棚 ---
rect(-7.5, 1.0, 15.0, 32.0, fc=H1, ec=INK, lw=1.5, hatch='///', z=1)
for (a, b, c, d) in (
        (-1.185, 1.0, 2.370, 18.50),      # Ø2.37 针套孔 Z58.00..76.50
        (-7.500, 19.5, 11.50, 5.00),      # 8x8 磁环全行程通道 Z76.50..81.50
        (-7.500, 24.5, 10.60, 6.00),      # 6.20 弹簧导向段 Z81.50..87.50
        (-1.250, 30.5, 2.500, 2.50),      # 一体顶棚中心 Ø2.50 / Z87.50..90.00
        (3.000, 19.5, 4.500, 5.50)):      # 霍尔窗 X81.0..85.5 / Z76.5..82.0
    hole(a, b, c, d)
ln(-7.5, 30.5, 7.5, 30.5, color=INK, lw=1.0, z=4)   # 顶棚下表面 = 弹簧上止挡
# --- 件 6 -X 侧盖板：主板 + 两处等截面补形凸台，型芯沿 -X 抽出 ---
rect(-9.40, 19.5, 1.90, 11.00, fc=H2, ec=INK, lw=1.1, hatch='///', z=5)
rect(-7.50, 19.5, 3.50, 5.00, fc=H2, ec=INK, lw=0.9, hatch='///', z=5)
rect(-7.50, 24.5, 4.50, 6.00, fc=H2, ec=INK, lw=0.9, hatch='///', z=5)

# --- 件 7 防尘唇 Z57.20..58.00 ---
for x0, wd in ((-3.0, 1.95), (1.05, 1.95)):
    rect(x0, -0.80, wd, 0.80, fc=H2, ec=INK, lw=0.9, z=5)

# --- 件 2 R125 针套 Z58.00..76.50（纵向剖切，反向剖面线）---
for x0, wd in ((-1.18, 0.13), (1.05, 0.13)):
    rect(x0, 1.0, wd, 18.50, fc=H2, ec=INK, lw=0.9, hatch='\\\\\\', z=5)

# --- 件 1 P125 探针 Ø2.02, Z57.00..90.35（实心件纵向不剖）---
rect(-1.01, 1.01, 2.02, 32.34, fc=H1, ec=INK, lw=1.05, z=6)
ax.add_patch(Arc((0, 1.01), 2.02, 2.02, theta1=180, theta2=360,
                 fc=H1, ec=INK, lw=1.05, zorder=6))
ax.add_patch(Polygon([[-1.01, 1.01], [1.01, 1.01], [1.01, 0.0], [-1.01, 0.0]],
                     closed=True, facecolor=H1, edgecolor='none', zorder=6))
ax.add_patch(Arc((0, 1.01), 2.02, 2.02, theta1=180, theta2=360,
                 fill=False, ec=INK, lw=1.05, zorder=7))
ln(-1.01, 1.01, -1.01, 33.35, color=INK, lw=0.9, z=7)
ln(1.01, 1.01, 1.01, 33.35, color=INK, lw=0.9, z=7)
dash_center(0, -1.6, 0, 34.6)
txt(0.35, 11.0, 'P125 内弹簧已环氧锁死', fs=6.2, color='#5d6d7e', rot=90)

# --- 件 4 磁环 Ø6 / 内孔 Ø2.10 / 厚 2.00 ---
for x0, wd in ((-3.0, 1.99), (1.01, 1.99)):
    rect(x0, 19.5, wd, 2.0, fc=H3, ec=INK, lw=0.95, z=6)
# 满程 +3.00 极限位置（双点划线）
rect(-3.0, 22.5, 6.0, 2.0, fc='none', ec='#7f8c8d', lw=0.9,
     ls=(0, (5, 1.5, 1, 1.5)), z=6)
ln(3.0, 23.5, 4.2, 26.6, color=LINE, lw=0.55, z=7)
ax.text(4.35, 26.6, '满程 +3.00（双点划线）', fontsize=6.2, ha='left',
        va='center', color=INK, bbox=dict(fc='white', ec='none', pad=0.5),
        zorder=9)

# --- 件 5 外部弹簧：正弦线示意，装配高 9.00 ---
zz = np.linspace(21.5, 30.5, 700)
ax.plot(2.70 * np.sin((zz - 21.5) * 2 * np.pi * 12 / 9.0), zz,
        color='#5d6d7e', lw=1.0, zorder=6)
ln(-2.9, 21.5, 2.9, 21.5, color=INK, lw=1.2, z=6)
ln(-2.9, 30.5, 2.9, 30.5, color=INK, lw=1.2, z=6)

# --- 件 6 v13：独立阶梯顶塞已取消；弹簧直接顶在座体一体顶棚下表面 ---
ln(-7.5, 30.5, 7.5, 30.5, color=INK, lw=1.0, z=7)

# --- 件 8 A1324 / 件 9 PCB / 件 10 盖板 / 件 11 护线套 ---
rect(5.40, 19.90, 1.50, 4.19, fc=H3, ec=INK, lw=1.0, z=6)       # A1324 X83.40..84.90
rect(6.90, 19.80, 0.60, 4.40, fc=H4, ec=INK, lw=0.9, z=6)        # PCB X84.90..85.50
for y0, hh in ((19.5, 0.90), (23.6, 1.90)):                       # 盖板 Ø3.2 出线孔
    rect(7.50, y0, 0.30, hh, fc=H2, ec=INK, lw=0.9, z=6)
for y0, hh in ((20.5, 0.30), (23.2, 0.30)):                       # 护线套 Ø2.4 线孔
    rect(7.80, y0, 1.50, hh, fc=H2, ec=INK, lw=0.9, hatch='///', z=6)
for yy in (21.4, 22.0, 22.6):                                      # 三根引线（止于护线套出口）
    ln(7.5, yy, 9.30, yy, color='#7f8c8d', lw=0.6, z=6)
# 座体与侧盖板外轮廓重描，保证压住剖面线
rect(-7.5, 1.0, 15.0, 32.0, fc='none', ec=INK, lw=1.5, z=7)
rect(-9.40, 19.5, 1.90, 11.00, fc='none', ec=INK, lw=1.2, z=7)
rect(-7.50, 19.5, 3.50, 5.00, fc='none', ec=INK, lw=0.9, z=7)
rect(-7.50, 24.5, 4.50, 6.00, fc='none', ec=INK, lw=0.9, z=7)

# 安装基体（件 12 臂体）局部，双点划线，不属本总成外形
rect(-7.5, 33.0, 15.0, 2.6, fc='none', ec=FAINT, lw=0.9,
     ls=(0, (5, 1.5, 1, 1.5)), z=6)
txt(0, 34.3, '件12 臂体顶板 Z90.00（假想线；与件3 一体顶棚上表面贴装）',
    fs=6.2, ha='center', color='#7f8c8d')
leader(1.25, 31.8, 4.5, 31.8, '一体顶棚 Ø2.50 / 弹簧止挡 Z87.50', fs=6.1)

# --- 磁环充磁方向（箭头留在环体内部，避免压住弹簧）---
for xx in (-2.5, 2.5):
    ax.annotate('', xy=(xx, 21.35), xytext=(xx, 19.65),
                arrowprops=dict(arrowstyle='->', color=DIMC, lw=0.9), zorder=8)
ax.text(0, 20.5, 'N', fontsize=6.4, ha='center', va='center', color=DIMC,
        fontweight='bold', bbox=dict(fc='white', ec='none', pad=0.35), zorder=9)

# --- 尺寸：左侧分段链 ---
for (a, b, s) in ((0.0, 1.0, '1.00'), (1.0, 19.5, '18.50'),
                  (19.5, 24.5, '5.00'), (24.5, 30.5, '6.00'),
                  (30.5, 33.0, '2.50')):
    dv(a, b, -11.6, s, fs=6.2, off=0.42)
txt(-11.6, 35.0, 'Z 向尺寸链', fs=6.3, ha='center', color=DIMC, weight='bold')

# --- 尺寸：总高 / 磁路半径 r / 针尖 ---
dv(0.0, 33.35, -13.0, '33.35', fs=6.4, off=0.40)
dh(0.0, 5.90, 35.8, 'r = 5.90（探针轴 → 霍尔管芯）', fs=6.6)
ln(0, 33.6, 0, 35.95, color=FAINT, lw=0.5, ls=':')
ln(5.90, 24.3, 5.90, 35.95, color=FAINT, lw=0.5, ls=':')
txt(2.6, 0.35, 'Z57.00 针尖', fs=6.2, color=DIMC, weight='bold')

# --- 主视图气泡 ---
for (px, py, num, by) in (
        (-2.0, -0.40, 7, 1.5),      # 防尘唇
        (-1.15, 8.0, 2, 6.2),       # 针套
        (0.0, 12.0, 1, 11.0),       # 探针
        (-6.2, 16.5, 3, 16.0),      # 座体
        (-2.1, 20.5, 4, 20.8),      # 磁环
        (-2.6, 26.0, 5, 26.0),      # 弹簧
        (-8.45, 27.0, 6, 31.6)):    # v13.2 -X 侧盖板
    balloon(px, py, num, -9.4, by)
# 气泡按目标高度单调排布，避免引线互相交叉
for (px, py, num, by) in (
        (7.2, 20.4, 9, 18.0),       # PCB
        (6.1, 22.0, 8, 21.5),       # A1324
        (8.9, 23.2, 11, 25.0),      # 护线套
        (7.65, 25.0, 10, 28.5),     # 盖板
        (7.4, 33.3, 12, 33.0)):     # 臂体（短引线，不横穿视图）
    balloon(px, py, num, 11.6, by)

# ==================================================================== ② 俯视图（沿 -Z）
txt(0.0, -20.6, '俯视图（沿 -Z）   A—A 剖切位置见中心线',
    fs=9.4, ha='center', weight='bold')
# 件6 -X 侧盖板顶面投影（Z87.50，低于件3 顶棚但在 -X 外侧可见）
rect(-9.4, -18.5, 1.9, 13.0, fc=H2, ec=INK, lw=1.1, hatch='///', z=3)
rect(-7.5, -18.5, 15.0, 13.0, fc=H1, ec=INK, lw=1.4, z=3)
# 件3 一体顶棚中心 Ø2.50 通孔与件1 针尾 Ø2.02；独立顶塞已取消
circ(0, -12.0, 1.25, fc='white', ec=INK, lw=1.05, z=5)
circ(0, -12.0, 1.01, fc=H1, ec=INK, lw=0.9, z=6)
for (u_, yr, num) in ((-4.0, -4.0, 13), (4.0, 4.0, 14)):
    wt_ = -12.0 - yr
    circ(u_, wt_, 1.25, fc='white', ec=INK, lw=0.95, z=5)        # 2x M3 底孔 Ø2.5
    dash_center(u_ - 2.1, wt_, u_ + 2.1, wt_)
    dash_center(u_, wt_ - 2.1, u_, wt_ + 2.1)
    txt(u_ + 1.7, wt_ - 1.6, str(num), fs=6.6, color=DIMC, weight='bold')
# 霍尔盖板 / 护线套在 +X 侧的顶面投影
rect(7.5, -14.5, 0.30, 5.0, fc=H2, ec=INK, lw=0.9, z=5)
rect(7.8, -14.0, 1.50, 4.0, fc=H4, ec=INK, lw=0.9, hatch='///', z=5)
# A-A 剖切符号（沿 u 方向，Y = -112.50 -> w = -12）
ln(-10.8, -12.0, -9.8, -12.0, color=INK, lw=1.8, z=7)
ln(9.8, -12.0, 10.8, -12.0, color=INK, lw=1.8, z=7)
ax.annotate('', xy=(-9.4, -12.0), xytext=(-10.4, -12.0),
            arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0), zorder=8)
ax.annotate('', xy=(9.4, -12.0), xytext=(10.4, -12.0),
            arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0), zorder=8)
txt(-10.6, -10.9, 'A', fs=7.4, ha='center', weight='bold')
txt(10.7, -10.9, 'A', fs=7.4, ha='center', weight='bold')
dash_center(-10.6, -12.0, 10.6, -12.0)
# 尺寸
dh(-7.5, 7.5, -4.1, '15.00', fs=6.8)
dh(-9.4, 9.3, -3.0, '18.70（含 −X 侧盖板 / 护线套）', fs=6.4)
dv(-18.5, -5.5, -11.0, '13.00', fs=6.6, off=0.42)
leader(1.25, -12.0, 4.2, -12.0, '座体一体顶棚 / 中心 Ø2.50 针尾孔', fs=6.1)
leader(-8.45, -17.6, -6.9, -16.2, '件6 −X 侧盖板（俯视投影）', fs=6.1)
leader(-4.0, -8.0, -6.9, -6.6, '2x M3 底孔 Ø2.5，对角 8.00 x 8.00', fs=6.1)
# ==================================================================== ③ 左视图（沿 -X）
txt(24.0, -3.1, '左视图（沿 -X，+Y 向右）', fs=9.4, ha='center', weight='bold')
rect(17.5, 1.0, 13.0, 32.0, fc=H1, ec=INK, lw=1.4, z=3)
ln(17.5, 1.0, 30.5, 1.0, color=INK, lw=1.4, z=4)
ln(17.5, 33.0, 30.5, 33.0, color=INK, lw=1.4, z=4)
dash_center(24.0, -1.6, 24.0, 35.6)                              # 探针轴线
# 座体外、可直接看到的针尖与防尘唇
rect(21.0, -0.80, 6.0, 0.80, fc=H2, ec=INK, lw=1.0, z=5)         # 防尘唇 Ø6
rect(22.99, 0.0, 2.02, 1.00, fc=H1, ec=INK, lw=1.0, z=5)         # 针尖 Ø2.02
ax.add_patch(Arc((24.0, 1.01), 2.02, 2.02, theta1=180, theta2=360,
                 fill=False, ec=INK, lw=1.0, zorder=5))
# 件6 -X 侧盖板前面：Z76.50..87.50，覆盖完整 13.00 宽度
rect(17.5, 19.5, 13.0, 11.0, fc=H2, ec=INK, lw=1.2, hatch='///', z=5)
ax.text(24.0, 28.7, '件6 −X 侧盖板（前面）', fontsize=6.2, ha='center',
        va='center', color=INK,
        bbox=dict(fc='white', ec='none', alpha=0.78, pad=0.4), zorder=9)
# 虚线：套筒孔、U 槽补形凸台、顶棚中心孔
for vv in (22.815, 25.185):
    ln(vv, 1.0, vv, 19.5, color=FAINT, lw=0.6, ls=(0, (3, 1.5)), z=6)
for vv in (20.0, 28.0):        # 8x8 通道 Y−116.50..−108.50
    ln(vv, 19.5, vv, 24.5, color=FAINT, lw=0.6, ls=(0, (3, 1.5)), z=6)
for vv in (20.9, 27.1):        # 座体导向段 Y−115.60..−109.40（6.20）
    ln(vv, 24.5, vv, 30.5, color=FAINT, lw=0.6, ls=(0, (3, 1.5)), z=6)
for vv in (21.6, 27.1):        # 盖板导向凸台 Y−114.90..−109.40（避 M3）
    ln(vv, 24.5, vv, 30.5, color=FAINT, lw=0.6, ls=(0, (3, 1.5)), z=6)
for vv in (22.75, 25.25):
    ln(vv, 30.5, vv, 33.0, color=FAINT, lw=0.6, ls=(0, (3, 1.5)), z=6)
for ww, a_, b_ in ((19.5, 20.0, 28.0), (24.5, 20.0, 28.0),
                   (24.5, 20.9, 27.1), (30.5, 21.6, 27.1),
                   (30.5, 22.75, 25.25), (33.0, 22.75, 25.25)):
    ln(a_, ww, b_, ww, color=FAINT, lw=0.6, ls=(0, (3, 1.5)), z=6)
# 背侧霍尔组件（被座体遮挡，虚线）
rect(22.4, 19.5, 3.2, 5.5, fc='none', ec=FAINT, lw=0.8,
     ls=(0, (3, 1.5)), z=4)                       # 霍尔窗 3.2 x 5.5
rect(21.5, 19.5, 5.0, 6.0, fc='none', ec=FAINT, lw=0.8,
     ls=(0, (3, 1.5)), z=4)                       # 盖板 5.00 x 6.00
circ(24.0, 22.0, 1.6, fc='none', ec=FAINT, lw=0.8,
     ls=(0, (3, 1.5)), z=4)                       # Ø3.2 出线孔
txt(24.0, 25.0, '背侧霍尔组件（虚线）', fs=6.1, ha='center', color=LINE)
txt(24.0, 18.6, '霍尔盖板 5.00 x 6.00 / Ø3.2', fs=6.1, ha='center', color=LINE)
# 2x M3 螺钉中心 + 臂体顶板假想线
for vv in (20.0, 28.0):
    dash_center(vv, 27.0, vv, 35.6)
    rect(vv - 1.5, 33.0, 3.0, 2.0, fc='none', ec=FAINT, lw=0.7,
         ls=(0, (3, 1.5)), z=4)
rect(17.5, 33.0, 13.0, 2.6, fc='none', ec=FAINT, lw=0.9,
     ls=(0, (5, 1.5, 1, 1.5)), z=4)
txt(24.0, 34.3, '件12 臂体顶板（假想线）', fs=6.0, ha='center', color='#7f8c8d')
# 尺寸
dv(1.0, 33.0, 32.2, '32.00', fs=6.6, off=0.42)
dh(17.5, 30.5, -1.9, '13.00', fs=6.6)
txt(24.0, 8.7, '实线：件6 侧盖板前面；虚线：8×8 通道 / 6.20 导向 / 顶棚孔 / 背侧霍尔',
    fs=6.2, ha='center', color=LINE)
txt(24.0, 7.3, 'Z76.50 零位  Z79.00 霍尔  Z81.50 导向分段  Z87.50 止挡  Z90.00 座顶',
    fs=6.2, ha='center', color=LINE)

# ==================================================================== ④ D 向局部视图
K = 1.6
CX, CY = 25.5, -12.0
txt(CX, -20.6, 'D 向局部视图（霍尔出线侧，沿 -X，1.6x）',
    fs=8.6, ha='center', weight='bold')
rect(CX - 2.5 * K, CY - 3.0 * K, 5.0 * K, 6.0 * K,
     fc=H2, ec=INK, lw=1.2, z=3)                                  # 盖板 5 x 6
circ(CX, CY, 1.6 * K, fc='white', ec=INK, lw=1.2, z=4)             # Ø3.2 出线孔
rect(CX - 2.0 * K, CY - 1.5 * K, 4.0 * K, 3.0 * K,
     fc=H4, ec=INK, lw=1.0, hatch='///', z=5)                     # 护线套 4 x 3
circ(CX, CY, 1.2 * K, fc='white', ec=INK, lw=1.0, z=6)             # Ø2.4 线孔
for dy in (-0.55, 0, 0.55):
    ln(CX - 1.05 * K, CY + dy * K, CX + 1.05 * K, CY + dy * K,
       color='#7f8c8d', lw=0.7, z=7)
leader(CX - 1.6 * K, CY + 1.6 * K, CX - 4.1 * K, CY + 3.4,
       'Ø3.2 出线孔', fs=6.1, ha='right')
txt(CX, CY - 3.0 * K - 1.0, '件10 盖板 5.00 x 6.00 x 0.30，Ø3.2 出线孔',
    fs=6.1, ha='center', color=LINE)
txt(CX, CY - 3.0 * K - 2.0, '件11 护线套 4.00 x 3.00 x 1.50，Ø2.4 线孔',
    fs=6.1, ha='center', color=LINE)

# ==================================================================== 面板工具
def panel(rect_):
    a = fig.add_axes(rect_)
    a.set_xlim(0, 1); a.set_ylim(0, 1); a.axis('off')
    return a


def pline(a, x1, y1, x2, y2, lw=0.7, color=INK):
    a.plot([x1, x2], [y1, y2], color=color, lw=lw, clip_on=False)


def ptext(a, x, y, s, fs=7.2, ha='left', va='center', weight='normal', color=INK):
    a.text(x, y, s, fontsize=fs, ha=ha, va=va, fontweight=weight,
           color=color, transform=a.transAxes)


# ---------------------------------------------------------- 明细表
PB = [0.600, 0.435, 0.368, 0.505]
b = panel(PB)
ptext(b, 0.0, 0.975, '明  细  表', fs=10.0, weight='bold', va='center')
COLS = [0.000, 0.055, 0.395, 0.455, 0.760, 1.000]
HEAD = ['序号', '名  称 / 对象名', '数量', '材料 / 规格', '备注']
ROWS = [
    ('1', 'P125 测试探针  HP45_PogoPin', '1', '铍铜镀金 Ø2.02 x 33.35', '内弹簧环氧锁死'),
    ('2', 'R125 针套  HP45_SocketR125', '1', '黄铜 Ø2.36/Ø2.10 x 18.50', '切短、压入 Ø2.37'),
    ('3', '探针座  HP45_ProbeHousing', '1', 'POM / PA66+GF30  15x13x32', '−X 敞开 U 槽 / 一体顶棚'),
    ('4', '磁环  HP45_PogoMagnet', '1', 'N35 镀镍 Ø6-Ø2.10 x 2.00', '轴向（厚度）充磁'),
    ('5', '外部回位弹簧  HP45_PogoSpring', '1', '琴钢丝 Ø0.30 / 12 圈', '自由高 10.00'),
    ('6', '−X 侧盖板  HP45_SpringSpacer', '1', 'POM / PA66+GF30  1.9x13x11 + 2 凸台', '卡扣 + 2xM3 / 补形凸台'),
    ('7', '防尘唇  HP45_DustSeal', '1', '毛毡 / 硅胶 A30 Ø6-Ø2.10x0.8', '实物唇口 Ø1.90'),
    ('8', '线性霍尔 A1324  HP45_HallSensor', '1', 'TO-92  5.0 mV/G', '感测面 X83.40'),
    ('9', '霍尔转接 PCB  HP45_HallPCB', '1', 'FR-4  0.60x2.60x4.40', '可加垫片调 r'),
    ('10', '霍尔盖板  HP45_HallCover', '1', 'FR-4 / 铝  0.30x5x6', 'Ø3.2 出线孔'),
    ('11', '出线护线套  HP45_CableClamp', '1', '硅胶 / TPU A50  1.5x4x3', 'Ø2.4 线孔'),
    ('12', '探针臂  HP45_ProbeArm', '1', 'POM / PA66+GF30（借用件）', '3 处减重腔 / 安装基体'),
    ('13', 'M3 沉头螺钉  HP45_HousingScrew_0', '1', '不锈钢 M3', '顶板固定'),
    ('14', 'M3 沉头螺钉  HP45_HousingScrew_1', '1', '不锈钢 M3', '顶板固定'),
]
NROW = len(ROWS) + 1
YTOP, YBOT = 0.935, 0.012
RH = (YTOP - YBOT) / NROW
for i in range(NROW + 1):
    yy = YBOT + i * RH
    pline(b, 0, yy, 1, yy, lw=0.8 if i in (0, NROW) else 0.45,
          color=INK if i in (0, NROW) else LINE)
for xx in COLS:
    pline(b, xx, YBOT, xx, YTOP, lw=0.6)
for j, htxt in enumerate(HEAD):
    ptext(b, (COLS[j] + COLS[j + 1]) / 2, YTOP - RH / 2, htxt,
          fs=7.4, ha='center', weight='bold')
for i, row in enumerate(ROWS):
    yy = YTOP - (i + 1.5) * RH
    for j, cell in enumerate(row):
        ptext(b, (COLS[j] + COLS[j + 1]) / 2 if j in (0, 2) else COLS[j] + 0.008,
              yy, cell, fs=6.9,
              ha='center' if j in (0, 2) else 'left',
              color=INK if j < 3 else '#3d4b56')

# ---------------------------------------------------------- 关键尺寸条
KD = panel([0.600, 0.385, 0.368, 0.045])
KD.add_patch(Rectangle((0, 0), 1, 1, transform=KD.transAxes,
                       fc='#f4f6f7', ec=INK, lw=0.7))
ptext(KD, 0.012, 0.68, '关键 Z 标高 / 尺寸链（mm）', fs=7.6, weight='bold')
ptext(KD, 0.012, 0.28,
      '针尖 57.00  零位 76.50-78.50(2.00)  霍尔 79.00  8×8 通道 76.50-81.50  '
      '6.20 导向 81.50-87.50  弹簧 9.00  顶棚 87.50-90.00  Ø2.50  '
      '侧盖板 X68.60-75.00  针尾 90.35  r 5.90  行程 0~+3.00',
      fs=6.0, color='#3d4b56')

# ---------------------------------------------------------- 技术要求
TR = panel([0.600, 0.190, 0.368, 0.190])
TR.add_patch(Rectangle((0, 0), 1, 1, transform=TR.transAxes,
                       fill=False, ec=INK, lw=0.8))
ptext(TR, 0.018, 0.925, '技  术  要  求', fs=9.4, weight='bold')
NOTES = [
    '1. 未注线性尺寸公差 ±0.10 mm；单位 mm；第一角画法；比例见标题栏。',
    '2. 件1 内部弹簧/柱塞须环氧锁死，整支作刚性滑杆；接触力由件5 提供。',
    '3. 件4 轴向充磁，N 极朝 +Z；内孔 ≥2.08、厚度 ≤2.00、外径 ≤6.10；经 −X 敞口原位点胶。',
    '4. 磁环零位台阶 Z76.50 起 2.00 为机械下限位，禁止向下超程、禁止改模加高。',
    '5. 件8 感测面朝 −X，管芯 X83.90 → r = 5.90 ±0.10；霍尔中心 Z79.00 ±0.10。',
    '6. 件5 自由高 10.00 装到 9.00；件3 一体顶棚 Z87.50 直接止挡，预压 1.00 → F0 0.045 N。',
    '7. 探针轴线与件2 针套孔同轴度 ≤0.05；推压 0~+3.00 mm 全程无卡滞、无干涉。',
    '8. 装配后逐只标定 A1324 输出（理论 1.43~3.57 V 全程单调），不得共用理论曲线。',
    '9. Z 轴限位开关槽 22.00 为设计冻结项；安装本总成不得改动 Z 端板与开关位。',
    '10. 装配基准：针尖自由位 Z57.00，比喷嘴面 Z57.90 低 0.90；蛋面 Z56.70，接触余量 0.30。',
    '11. 【v13.2 注塑】件3/6 沿 X 分型：8×8 通道型芯 −X（Z76.50-81.50）、6.20 导向型芯 −X、霍尔窗 +X；1.5° / R0.4 / 壁厚 2.0。',
    '12. 【v13.2 装配】件4/5 +X 侧装 → 件1 −Z 顶落 → 原位点胶 → 件6 卡扣 + 2xM3 +X 扣合；Ø6 弹簧靠 6.20 窄腔导向，不得缩小外径。',
]
for i, s in enumerate(NOTES):
    ptext(TR, 0.018, 0.855 - i * 0.071, s, fs=6.1, color='#2c3e50')

# ---------------------------------------------------------- 标题栏
TB = panel([0.600, 0.032, 0.368, 0.150])
TB.add_patch(Rectangle((0, 0), 1, 1, transform=TB.transAxes,
                       fill=False, ec=INK, lw=1.3))
pline(TB, 0, 0.52, 1, 0.52, lw=0.9)
pline(TB, 0, 0.26, 1, 0.26, lw=0.7)
pline(TB, 0.62, 0.0, 0.62, 0.52, lw=0.7)
pline(TB, 0.62, 0.26, 1, 0.26, lw=0.5, color=LINE)
pline(TB, 0.81, 0.0, 0.81, 0.26, lw=0.5, color=LINE)
ptext(TB, 0.5, 0.79, '霍尔传感连续测高探针总成  装配图', fs=13.0,
      ha='center', weight='bold')
ptext(TB, 0.5, 0.62, '三视图 · 14 件 · v13.2 可注塑', fs=8.4, ha='center', color='#3d4b56')
ptext(TB, 0.016, 0.39, '图号  X-PRINT-HP45-PROBE-ASSY-01', fs=7.4)
ptext(TB, 0.016, 0.22, '第一角画法 / 单位 mm', fs=7.2)
ptext(TB, 0.016, 0.10, '日期  2026-11-10', fs=7.2)
ptext(TB, 0.635, 0.39, '比例  %.0f:1' % RATIO, fs=8.0, weight='bold')
ptext(TB, 0.635, 0.13, '幅面  A2', fs=7.4)
ptext(TB, 0.825, 0.39, '版本  v13.2', fs=7.4)
ptext(TB, 0.825, 0.13, '第 1 张 / 共 1 张', fs=7.0)

# ---------------------------------------------------------- 图顶说明
fig.text(0.5, 0.965,
         '鹅蛋种蛋曲面喷码机 X-print  |  HP45 喷头旁置接触式连续测高探针  |  '
         '模型 CrossSlide_P014013.FCStd（v13.2，151 对象；8×8 磁环全行程通道 / 6.20 弹簧导向段 / '
         '脱模阻挡 0 / 静态干涉 0 / 装配阻塞 0 / 行程干涉 0 / 冻结项 OK / 回写 OK）',
         ha='center', va='center', fontsize=9.4, color='#3d4b56')

fig.savefig(OUT_PNG, dpi=DPI, facecolor='white')
fig.savefig(OUT_PDF, facecolor='white')
print('比例 %.2f:1 (%.4f in/mm)' % (RATIO, scale_in))
print('saved:', os.path.abspath(OUT_PNG))
print('saved:', os.path.abspath(OUT_PDF))
