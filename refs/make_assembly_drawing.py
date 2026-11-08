# -*- coding: utf-8 -*-
"""Post-process the TechDraw A2 sheet into a complete assembly drawing.
   All coordinates below are page millimetres, origin = top-left corner.
   Model -> page mapping (scale 1:1, first-angle projection):
     front/top horizontal : x = X + 25.4
     front/left vertical  : y = 261.1 - Z
     top vertical / left horizontal : v = 205.6 - Y
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(_HERE, 'HP45_Assembly_raw.svg')
OUT = os.path.join(_HERE, 'HP45_Assembly_A2.svg')
PNG = os.path.join(_HERE, 'HP45_Assembly_A2.png')
PDF = os.path.join(_HERE, 'HP45_Assembly_A2.pdf')

svg = open(RAW, encoding='utf-8').read()
# Drop the A2 template's editable placeholder texts (e.g. leftover
# "工控喷墨打码机 十字滑台") so they cannot bleed through the title block.
svg = re.sub(r'<text[^>]*freecad:editable="[^"]*"[^>]*>.*?</text>',
             '', svg, flags=re.S)
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
      'text-anchor="middle" fill="#000">%s</text>' % (x - 1.5, (y1 + y2) / 2, label))


def balloon(x, y, n, tx, ty):
    ln(x, y, tx, ty, 0.15)
    w('<circle cx="%.2f" cy="%.2f" r="3.4" fill="#fff" stroke="#000" '
      'stroke-width="0.25"/>' % (x, y))
    txt(x, y + 1.1, str(n), 3.2)


def leader(x1, y1, x2, y2, label, sz=2.8):
    ln(x1, y1, x2, y2, 0.15)
    txt(x1, y1 - 1.2, label, sz, 'start')


def px(X):
    return X + 25.4


def pz(Z):
    return 261.1 - Z


def py(Y):
    return 205.6 - Y


# ---------------------------------------------------------------- overlay
w('<g transform="scale(10)" stroke-linecap="round">')

# --- centre lines -------------------------------------------------------
ln(px(150.15), 78, px(150.15), 218, 0.15, '2.5,1.2,0.5,1.2')       # nozzle / head centre
ln(px(78), 150, px(78), 220, 0.15, '2.5,1.2,0.5,1.2')               # probe axis
ln(88, py(-112.55), 212, py(-112.55), 0.15, '2.5,1.2,0.5,1.2')     # nozzle row centre (top view)
txt(px(150.15), 76, '中心线', 2.5)

# --- FRONT VIEW dimensions ---------------------------------------------
dimh(px(68), px(181.2), 68, '113.2', 82)                             # overall width
dimv(pz(179.5), pz(46.7), 84, '132.8', 93)                           # overall height
dimh(px(78), px(150.15), 222, '72 (探针前置量)', 214)                # probe lead distance
# nozzle-plane callout: keep the label clear of the 11.2 extension line
ln(212, pz(57.9), px(159.6), pz(57.9), 0.15)
txt(212, pz(57.9) - 1.8, '喷嘴面', 2.8, 'start')
# nozzle plane / probe tip height difference (small dimension, plain leaders)
ln(px(150.15), pz(57.9), 218, pz(57.9), 0.13)
ln(px(78), pz(46.7), 218, pz(46.7), 0.13)
dimv(pz(57.9), pz(46.7), 215, '11.2')

# --- TOP VIEW dimensions -----------------------------------------------
dimv(py(-57.5), py(-171.3), 84, '113.8', 93)                         # overall depth
dimh(px(136.5), px(163.5), 250, '27', 263)                           # adapter hole pitch
dimv(py(-106.2), py(-118.9), 215, '12.7 喷幅')
leader(219, py(-112.55), px(150.15), py(-112.55), '喷嘴列中心线 / 探针对齐', 2.6)

# --- LEFT VIEW dimensions ----------------------------------------------
dimv(pz(149.6), pz(57.9), 250, '91.7 墨盒高')                        # cartridge height

# --- view captions ------------------------------------------------------
txt(150, 234, '主视图  (沿 −Y)', 3.4, bold=True)
txt(150, 392, '俯视图  (沿 −Z)', 3.4, bold=True)
txt(320, 234, '左视图  (沿 −X)', 3.4, bold=True)
txt(468, 242, '轴测图', 3.4, bold=True)

# --- item balloons -----------------------------------------------------
balloon(196, 96, 1, px(150.15), pz(120))        # HP45 cartridge
balloon(222, 122, 2, px(168), pz(100))          # P01 body
balloon(392, 92, 4, 330, 100)                   # P03 latch arm
balloon(392, 116, 5, 340, 126)                  # P04 clamp
balloon(222, 158, 6, px(166), pz(120))          # adapter plate
balloon(100, 232, 7, px(90), pz(96))            # probe arm
balloon(100, 196, 8, px(78), pz(80))            # sleeve
balloon(88, 208, 9, px(78), pz(52))             # probe shaft
balloon(116, 186, 10, px(78), pz(84))           # spring
balloon(222, 288, 11, px(150), py(-67))         # X carriage
balloon(392, 150, 3, 356, 138)                  # hinges
balloon(238, 182, 12, px(166), pz(70))          # M3 fasteners on adapter flange

# --- technical notes ---------------------------------------------------
txt(26, 240, '技术要求', 3.6, 'start', True)
ln(26, 242, 86, 242, 0.2)
notes = [
    '1. 墨盒竖插，喷嘴面朝下；',
    '   靠摆臂锁扣 + 压块压紧。',
    '2. 喷嘴面与探针尖端高差 11.2。',
    '3. 探针中心与 12.7 喷幅中心',
    '   在 Y 方向对齐。',
    '4. 转接板以 4×M3 固定于 X 滑座。',
    '5. 未注公差 ±0.2（3D 打印件）。',
    '6. 控制器 PCB 外置，线束另配。',
]
for i, t in enumerate(notes):
    txt(26, 248 + i * 5.2, t, 2.7, 'start')

# --- bill of materials -------------------------------------------------
bx, by, rh = 382, 250, 6.8
cols = [12, 74, 14, 36, 40]
hdr = ['序号', '名称', '数量', '材料 / 规格', '备注']
rows = [
    ('1', 'HP45 墨盒', '1', 'HP 51645A', '参考件'),
    ('2', '主 carriage 体 P01', '1', '树脂 / PLA', '官方件'),
    ('3', '铰链 P02', '2', '树脂 / PLA', '官方件'),
    ('4', '锁扣摆臂 P03', '1', '树脂 / PLA', '官方件'),
    ('5', '压块 P04', '1', '树脂 / PLA', '官方件'),
    ('6', '滑座转接板', '1', '光敏树脂', '自制'),
    ('7', '探针支架', '1', '光敏树脂', '自制'),
    ('8', '探针套筒', '1', '树脂 / 铜', 'Ø12 / Ø10'),
    ('9', '测高探针轴', '1', '不锈钢', 'Ø6'),
    ('10', '复位弹簧', '1', '弹簧钢', 'R4 × 5 圈'),
    ('11', 'X 滑座', '1', '光敏树脂', '已有件'),
    ('12', 'M3 螺钉', '10', '标准件', '4+4+2'),
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
    txt(x + c / 2, by + 4.7, hdr[i], 2.9, 'middle', True)
    x += c
for r, row in enumerate(rows, start=1):
    yy = by + rh * r + 4.7
    x = bx
    for i, c in enumerate(cols):
        txt(x + c / 2 if i != 1 else x + 1.5, yy, row[i], 2.8, 'middle' if i != 1 else 'start')
        x += c
txt(bx, by - 2.5, '明细栏', 3.2, 'start', True)

# --- clean title block (cover the template one) ------------------------
# Template inner frame: x 6..588, y 6..414 mm.  Cover a slightly larger
# patch to erase the template rules, then restore the two frame edges.
tx0, ty0, tw0, th0 = 398, 346, 190, 68
rect(395, 340, 193, 74, 0, '#fff')
rect(582, 334, 8, 12, 0, '#fff')             # erase the clipped zone letter "G"
ln(588, 334, 588, 414, 0.25)                 # right frame edge
ln(395, 414, 588, 414, 0.25)                 # bottom frame edge
rect(tx0, ty0, tw0, th0, 0.35)
ln(tx0, ty0 + 20, tx0 + tw0, ty0 + 20, 0.3)
ln(tx0, ty0 + 40, tx0 + tw0, ty0 + 40, 0.3)
# right-hand columns: 516..550 / 550..568 / 568..588
c1, c2, c3 = tx0 + 118, tx0 + 152, tx0 + 170
for cx in (c1, c2, c3):
    ln(cx, ty0 + 20, cx, ty0 + th0, 0.25)
ln(c1, ty0 + 30, tx0 + tw0, ty0 + 30, 0.25)
ln(c1, ty0 + 50, tx0 + tw0, ty0 + 50, 0.25)
m1, m2, m3 = (c1 + c2) / 2, (c2 + c3) / 2, (c3 + tx0 + tw0) / 2  # 533 / 559 / 578
txt(tx0 + tw0 / 2, ty0 + 13, 'HP45 打印头总成装配图', 6.5, 'middle', True)
txt(tx0 + 6, ty0 + 28, '工控喷墨打码机 · 十字滑台', 3.2, 'start')
txt(tx0 + 6, ty0 + 36, '第一角投影   单位：mm', 3.0, 'start')
txt(tx0 + 6, ty0 + 49, '图号  CS-HP45-A01', 3.2, 'start')
txt(tx0 + 6, ty0 + 58, '设计 / 审核', 3.0, 'start')
txt(tx0 + 6, ty0 + 64, '日期  2026-11-06', 3.0, 'start')
txt(m1, ty0 + 27, '比例', 2.8)
txt(m1, ty0 + 37, '1 : 1', 3.6, 'middle', True)
txt(m1, ty0 + 47, '张次', 2.8)
txt(m1, ty0 + 57, '第 1 张 / 共 1 张', 2.6)
txt(m1, ty0 + 64, 'A2  594 × 420', 2.6)
txt(m2, ty0 + 27, '重量', 2.8)
txt(m2, ty0 + 37, '—', 3.0)
txt(m2, ty0 + 47, '版本', 2.8)
txt(m2, ty0 + 57, 'A', 3.2)
txt(m3, ty0 + 27, '投影', 2.8)
txt(m3, ty0 + 37, '第一角', 2.6)
txt(m3, ty0 + 47, '视图', 2.8)
txt(m3, ty0 + 57, '三视图 + 轴测', 2.5)

w('</g>')

out = svg.replace('</svg>', '\n'.join(o) + '\n</svg>')
open(OUT, 'w', encoding='utf-8').write(out)
print('SVG written', OUT, os.path.getsize(OUT), 'bytes')

# --- render PNG + PDF ---------------------------------------------------
try:
    from PySide6 import QtCore, QtGui, QtSvg
except ImportError:
    try:
        from PySide import QtCore, QtGui, QtSvg
    except ImportError:
        print('Qt bindings unavailable: SVG only. Render PNG/PDF inside FreeCAD GUI.')
        raise SystemExit(0)

rend = QtSvg.QSvgRenderer(OUT)
print('svg valid', rend.isValid())
img = QtGui.QImage(2376, 1680, QtGui.QImage.Format_ARGB32)
img.fill(QtGui.QColor('white'))
p = QtGui.QPainter(img)
rend.render(p)
p.end()
img.save(PNG)
print('PNG written', os.path.getsize(PNG))

try:
    writer = QtGui.QPdfWriter(PDF)
    writer.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A2))
    writer.setPageOrientation(QtGui.QPageLayout.Landscape)
    writer.setResolution(200)
    writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
    p = QtGui.QPainter(writer)
    rend.render(p)
    p.end()
    print('PDF written', os.path.getsize(PDF))
except Exception as e:
    print('PDF failed', e)
