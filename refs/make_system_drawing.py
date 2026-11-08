# -*- coding: utf-8 -*-
"""Post-process the TechDraw A1 whole-system sheet into a full assembly drawing.

Page: A1 landscape 841 x 594 mm, origin = top-left corner, all overlay
coordinates are millimetres (the raw SVG has viewBox 0 0 8410 5940, i.e.
10 user units per mm -> the overlay group uses scale(10)).

Model -> page mapping, scale 1:1, first-angle projection, source bbox
X 0..300 / Y -171.252..45 / Z -4..262, centre (150, -63.126, 129):

    front / top horizontal : px(X)  = X + 50
    front / left vertical  : pz(Z)  = 307 - Z
    top vertical           : py(Y)  = 381.874 - Y
    left horizontal        : plx(Y) = 421.874 - Y

View centres on the sheet (svg mm): front (200,180), left (485,180),
top (200,445), iso (710,180).
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(_HERE, 'System_Assembly_raw.svg')
OUT = os.path.join(_HERE, 'System_Assembly_A1.svg')
PNG = os.path.join(_HERE, 'System_Assembly_A1.png')
PDF = os.path.join(_HERE, 'System_Assembly_A1.pdf')

svg = open(RAW, encoding='utf-8').read()

# Drop the A1 template's editable placeholder texts so they cannot bleed
# through the custom title block drawn further down.
svg = re.sub(r'<text[^>]*freecad:editable="[^"]*"[^>]*>.*?</text>',
             '', svg, flags=re.S)

# ---------------------------------------------------------------- iso view
# When the TechDraw page is shown in the GUI and recomputed immediately before
# exportPageAsSvg(), TechDraw honours the per-view Scale=0.8 and bakes it into
# the path coordinates.  Measured raw isometric ink is then 174.8 x 241.8 mm
# about (710,180), which already fits the frame, so NO compensation is needed.
#
# Older exports (page not re-shown) baked 0.5 into the paths instead and needed
# a 1.6x enlargement (0.5 x 1.6 = 0.8).  Keep that hook available: set
# ISO_F = 1.6 and ISO_NEW = 'matrix(1.6,0,0,1.6,7100,1800)' if an export ever
# comes out at the old 108.9 x 150.9 mm size again.
ISO_OLD = 'matrix(1,0,0,1,7100,1800)'
ISO_NEW = ISO_OLD
ISO_F = 1.0

if ISO_F != 1.0:
    def fix_iso(m):
        tag = m.group(0).replace(ISO_OLD, ISO_NEW)
        tag = re.sub(r'stroke-width="([\d.]+)"',
                     lambda q: 'stroke-width="%.3f"' % (float(q.group(1)) / ISO_F),
                     tag)
        tag = re.sub(r'font-size="([\d.]+)"',
                     lambda q: 'font-size="%.3f"' % (float(q.group(1)) / ISO_F),
                     tag)
        return tag

    svg = re.sub(r'<[A-Za-z]+[^>]*transform="' + re.escape(ISO_OLD) + r'"[^>]*>',
                 fix_iso, svg)

o = []


def w(t):
    o.append(t)


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def ln(x1, y1, x2, y2, lw=0.18, dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    w('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#000" '
      'stroke-width="%.2f"%s/>' % (x1, y1, x2, y2, lw, d))


def rect(x, y, ww, hh, lw=0.25, fill='none'):
    w('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" '
      'stroke="%s" stroke-width="%.2f"/>'
      % (x, y, ww, hh, fill, '#000' if lw else 'none', lw))


def txt(x, y, t, sz=3.0, anc='middle', bold=False):
    w('<text x="%.2f" y="%.2f" font-family="Microsoft YaHei,SimHei,sans-serif" '
      'font-size="%.2f" text-anchor="%s" fill="#000"%s>%s</text>'
      % (x, y, sz, anc, ' font-weight="bold"' if bold else '', esc(t)))


def tri_h(x, y, sg):
    bx = x - sg * 2.6
    w('<polygon points="%.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="#000"/>'
      % (x, y, bx, y - 0.75, bx, y + 0.75))


def tri_v(x, y, sg):
    by = y - sg * 2.6
    w('<polygon points="%.2f,%.2f %.2f,%.2f %.2f,%.2f" fill="#000"/>'
      % (x, y, x - 0.75, by, x + 0.75, by))


def dimh(x1, x2, y, label, y_ext=None):
    if y_ext is not None:
        d = -2 if y < y_ext else 2
        ln(x1, y_ext, x1, y + d, 0.13)
        ln(x2, y_ext, x2, y + d, 0.13)
    ln(x1, y, x2, y, 0.18)
    if x2 - x1 > 9:
        tri_h(x1, y, -1)
        tri_h(x2, y, 1)
    txt((x1 + x2) / 2, y - 1.3, label, 3.0)


def dimv(y1, y2, x, label, x_ext=None):
    if x_ext is not None:
        d = -2 if x < x_ext else 2
        ln(x_ext, y1, x + d, y1, 0.13)
        ln(x_ext, y2, x + d, y2, 0.13)
    ln(x, y1, x, y2, 0.18)
    if y2 - y1 > 9:
        tri_v(x, y1, -1)
        tri_v(x, y2, 1)
    w('<text transform="translate(%.2f,%.2f) rotate(-90)" '
      'font-family="Microsoft YaHei,SimHei,sans-serif" font-size="3" '
      'text-anchor="middle" fill="#000">%s</text>'
      % (x - 1.5, (y1 + y2) / 2, label))


def balloon(x, y, n, tx, ty):
    ln(x, y, tx, ty, 0.15)
    w('<circle cx="%.2f" cy="%.2f" r="3.6" fill="#fff" stroke="#000" '
      'stroke-width="0.25"/>' % (x, y))
    txt(x, y + 1.2, str(n), 3.2)


def px(X):
    return X + 50.0


def pz(Z):
    return 307.0 - Z


def py(Y):
    return 381.874 - Y


def plx(Y):
    return 421.874 - Y


w('<g transform="scale(10)" stroke-linecap="round">')

# ------------------------------------------------------------ centre lines
C = '3,1.2,0.5,1.2'
ln(px(150), 42, px(150), 318, 0.15, C)                 # X / Z axis centre
ln(px(225), 250, px(225), 318, 0.13, '1.5,1.2')       # capping park centre
ln(45, py(-112.55), 356, py(-112.55), 0.15, C)        # nozzle row centre
ln(px(150), 332, px(150), 558, 0.15, C)               # top-view centre
ln(plx(-63.126), 42, plx(-63.126), 318, 0.15, C)      # left-view centre

# ------------------------------------------------------- overall dimensions
dimh(px(0), px(300), 36, '300', 45)                    # front: overall width
dimv(pz(262), pz(-4), 36, '266', 50)                   # front: overall height
dimv(pz(262), pz(-4), 607, '266', 593.2)               # left: overall height
dimh(plx(45), plx(-171.252), 325, '216.3', 315)        # left: overall depth
dimv(py(45), py(-171.252), 36, '216.3', 50)            # top: overall depth
dimh(px(0), px(300), 562, '300', 553.1)                # top: overall width

# ---------------------------------------------------------- view captions
txt(200, 330, '主视图  (沿 −Y)', 3.6, bold=True)
txt(485, 332, '左视图  (沿 −X)', 3.6, bold=True)
txt(710, 310, '轴测图  0.8 : 1', 3.6, bold=True)
txt(200, 573, '俯视图  (沿 −Z)', 3.6, bold=True)

# ----------------------------------------------------------- item balloons
balls = [
    (332, 300, 1, 230, 291),      # Z base + capping bypass arm
    (272, 76, 2, 202, 108),       # Z 2040 column
    (312, 52, 3, 202, 68),        # Z end plates / pulleys / rods
    (270, 212, 4, 205, 180),      # Z carriage + LM5UU
    (240, 126, 5, 202, 156),      # XZ adapter plate
    (92, 108, 6, 150, 168),       # X 2040 beam
    (64, 202, 7, 96, 169),        # X rods / end plates / pulleys
    (332, 196, 8, 198, 166),      # X carriage + LM5UU (centre block)
    (62, 250, 9, 71, 178),        # NEMA17 motors
    (250, 235, 10, 203, 207),     # HP45 printhead assembly
    (80, 292, 11, 128, 240),      # egg height probe
    (330, 242, 12, 275, 262),     # capping / moisturising station
    (365, 396, 13, 305, 443),     # limit switches (top view)
]
for x, y, n, tx, ty in balls:
    balloon(x, y, n, tx, ty)

# -------------------------------------------------------- technical notes
txt(390, 345, '明细栏', 3.6, 'start', True)
bx, by, rh = 390, 352, 9.0
cols = [13, 84, 15, 57, 41]
hdr = ['序号', '名称', '数量', '材料 / 规格', '备注']
rows = [
    ('1', 'Z 基座 + 保湿站绕行臂', '1', '光敏树脂', '一体成型'),
    ('2', 'Z 轴 2040 立柱', '1', '铝型材 2040', 'L = 150'),
    ('3', 'Z 导杆 / 端板 / 同步轮', '1 套', '不锈钢 + 树脂', '导杆 L = 165'),
    ('4', 'Z 滑座 + LM5UU', '1 套', '树脂 + 轴承', 'Ø5 × 2'),
    ('5', 'XZ 转接板', '1', '光敏树脂', 't = 10'),
    ('6', 'X 轴 2040 横梁', '1', '铝型材 2040', 'L = 200'),
    ('7', 'X 导杆 / 端板 / 同步轮', '1 套', '不锈钢 + 树脂', '导杆 L = 215'),
    ('8', 'X 滑座 + LM5UU', '1 套', '树脂 + 轴承', 'Ø5 × 2'),
    ('9', 'NEMA17 步进电机', '2', '标准件', 'X / Z 各 1'),
    ('10', 'HP45 打印头总成', '1 套', '51645A + P01~P04', '官方件'),
    ('11', '鹅蛋测高探针', '1 套', 'Ø6 不锈钢 + 弹簧', '前置'),
    ('12', '保湿站 (帽 / 海绵 / 弹簧)', '1 套', '硅胶 + 树脂', '浮动式'),
    ('13', '限位开关', '4', 'KW11-3Z', 'X / Z 两端'),
]
tw = sum(cols)
rect(bx, by, tw, rh * (len(rows) + 1), 0.3)
x = bx
for c in cols[:-1]:
    x += c
    ln(x, by, x, by + rh * (len(rows) + 1), 0.18)
for r in range(1, len(rows) + 1):
    ln(bx, by + rh * r, bx + tw, by + rh * r, 0.18)
x = bx
for i, c in enumerate(cols):
    txt(x + c / 2, by + 6.2, hdr[i], 3.0, 'middle', True)
    x += c
for r, row in enumerate(rows, start=1):
    yy = by + rh * r + 6.2
    x = bx
    for i, c in enumerate(cols):
        txt(x + c / 2 if i != 1 else x + 1.6, yy, row[i], 2.8,
            'middle' if i != 1 else 'start')
        x += c

# ---------------------------------------------------------- notes / params
nx = 615
txt(nx, 345, '技术要求', 3.6, 'start', True)
ln(nx, 347.5, 815, 347.5, 0.2)
notes = [
    '1. 第一角投影，单位 mm；主/俯/左视图 1:1，轴测 0.8:1。',
    '2. 两轴均为 GT2 同步带 + 16T 同步轮 + Ø5 导杆 + LM5UU。',
    '3. 铝型材 Z 立柱 150、X 横梁 200；导杆 165 / 215，长度固定。',
    '4. 树脂打印件沉孔处局部加厚 3，未注公差 ±0.2。',
    '5. 导杆仅一端端面钻盲孔攻丝 4 深，另一端端板为自适应通孔。',
    '6. 螺钉统一；底板 6×M4×16 (Ø8.4 沉孔/Ø4.5 通孔)；开关 Ø2.6+M2.5，按钮先触发。',
    '7. HP45 竖插，官方 P01~P04 锁扣压紧；控制器 PCB 外置。',
    '8. 探针位于喷头 X 前方，与 12.7 喷幅中心 Y 对齐。',
    '9. 保湿站底板与 Z 基座一体，L 形绕行让出最大打印空间。',
    '10. 紧固件、线束、拖链、墨管夹未逐一绘出，详见部件图。',
]
for i, t in enumerate(notes):
    txt(nx, 355 + i * 8.6, t, 2.7, 'start')

txt(nx, 447, '关键位置参数', 3.4, 'start', True)
ln(nx, 449.5, 815, 449.5, 0.2)
params = [
    '喷嘴面            Z = 57.9',
    '探针尖端          Z = 46.7   (低于喷嘴 11.2)',
    '保湿帽唇顶        Z = 55      (Z 下压 ≈3 密封)',
    '停车位置          X = 225   (滑座中心 150 → +75)',
    '喷嘴列中心        Y = −112.55，喷幅 12.7',
    '打印净空          底板仅占 20 × 80 窄带',
]
for i, t in enumerate(params):
    txt(nx, 458 + i * 8.4, t, 2.7, 'start')

# ---------------------------------------------- clean custom title block
# A1 template title block is x 641..821 / y 518..574; cover it plus a small
# margin, then restore the two outer frame edges.
rect(637, 514, 190, 64, 0, '#fff')
rect(818, 506, 10, 12, 0, '#fff')          # erase any zone letter
ln(825, 514, 825, 578, 0.25)
ln(637, 578, 825, 578, 0.25)

tx0, ty0, tw0, th0 = 641, 518, 180, 56
rect(tx0, ty0, tw0, th0, 0.35)
ln(tx0, ty0 + 16, tx0 + tw0, ty0 + 16, 0.3)     # y = 534
ln(tx0, ty0 + 34, tx0 + tw0, ty0 + 34, 0.3)     # y = 552
c1, c2, c3 = tx0 + 100, tx0 + 134, tx0 + 152     # 741 / 775 / 793
for cx in (c1, c2, c3):
    ln(cx, ty0 + 16, cx, ty0 + th0, 0.25)
ln(c1, ty0 + 26, tx0 + tw0, ty0 + 26, 0.25)     # y = 544
ln(c1, ty0 + 44, tx0 + tw0, ty0 + 44, 0.25)     # y = 562
m1, m2, m3 = (c1 + c2) / 2, (c2 + c3) / 2, (c3 + tx0 + tw0) / 2

txt(tx0 + tw0 / 2, ty0 + 11, '工控喷墨打码机 · 十字滑台 总装图', 5.4,
    'middle', True)
txt(tx0 + 5, ty0 + 24, '图号  CS-SYS-A01', 3.0, 'start')
txt(tx0 + 5, ty0 + 31, '第一角投影   单位：mm', 2.8, 'start')
txt(tx0 + 5, ty0 + 41, '设计 / 审核   —', 2.8, 'start')
txt(tx0 + 5, ty0 + 50, '日期  2026-11-06', 2.8, 'start')
for cx, head, a, head2, b in [
        (m1, '比例', '1 : 1', '张次', '第 1 张'),
        (m2, '重量', '—', '版本', 'A'),
        (m3, '图幅', 'A1', '视图', '三视图+轴测')]:
    txt(cx, ty0 + 23, head, 2.6)
    txt(cx, ty0 + 31, a, 3.0, 'middle', True)
    txt(cx, ty0 + 41, head2, 2.6)
    txt(cx, ty0 + 50, b, 2.4)

w('</g>')

out = svg.replace('</svg>', '\n'.join(o) + '\n</svg>')
open(OUT, 'w', encoding='utf-8').write(out)
print('SVG written', OUT, os.path.getsize(OUT), 'bytes')

# ---------------------------------------------------------- render PNG/PDF
try:
    from PySide6 import QtCore, QtGui, QtSvg
except ImportError:
    try:
        from PySide import QtCore, QtGui, QtSvg
    except ImportError:
        print('Qt bindings unavailable: SVG only. Render PNG/PDF in FreeCAD GUI.')
        raise SystemExit(0)

r = QtSvg.QSvgRenderer(OUT)
print('svg valid', r.isValid())
img = QtGui.QImage(3364, 2376, QtGui.QImage.Format_ARGB32)
img.fill(QtGui.QColor('white'))
p = QtGui.QPainter(img)
r.render(p)
p.end()
img.save(PNG)
print('PNG written', os.path.getsize(PNG))

try:
    writer = QtGui.QPdfWriter(PDF)
    writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A1))
    writer.setPageOrientation(QtGui.QPageLayout.Landscape)
    writer.setResolution(150)
    writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
    p = QtGui.QPainter(writer)
    r.render(p)
    p.end()
    print('PDF written', os.path.getsize(PDF))
except Exception as e:
    print('PDF failed', e)
