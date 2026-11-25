# -*- coding: utf-8 -*-
"""
build_autocad_3view.py — 由 export_ortho_views.py 的 HLR 投影 JSON 生成 AutoCAD 三视图 DXF。

目标零件：X_EndPlate_L（X 轴电机侧端板，PETG 异型结构件）
投影法  ：第一角（GB/T 14692）—— 主视图左上、俯视图正下、左视图正右
比例    ：1:1，模型空间真实 mm 坐标（AutoCAD 里可直接量尺寸）

图层约定：
  OUTLINE  7 白/黑  CONTINUOUS  0.35  可见轮廓
  HIDDEN   8 灰     DASHED      0.18  隐藏线（默认关闭，需时打开）
  CENTER   4 青     CENTER      0.18  孔中心线
  DIM      2 黄     CONTINUOUS  0.18  尺寸线与尺寸文字
  FOCUS    6 洋红   DASHED      0.25  上次讨论的「敞开让位长槽」定位框（可关）
  GRID     9 浅灰   DOT         0.09  A~C / 1~3 区域网格
  NOTE     3 绿     CONTINUOUS  0.18  说明文字
  FRAME    7 白/黑  CONTINUOUS  0.25  图框 / 标题栏
  MARKUP   1 红     CONTINUOUS  0.50  【当前层】留空，供用户画圈 / 箭头 / 编号

输出：
  refs/drawings/X_EndPlate_L_3view.dxf
  refs/drawings/X_EndPlate_L_3view.svg
  refs/drawings/X_EndPlate_L_3view.png
"""
import os, sys, json, math
import ezdxf
from ezdxf import units

ROOT = 'C:/ink'
SRC = ROOT + '/refs/tmp/ortho_X_EndPlate_L.json'
OUTDIR = ROOT + '/refs/drawings'
DXF = OUTDIR + '/X_EndPlate_L_3view.dxf'
SVG = OUTDIR + '/X_EndPlate_L_3view.svg'
PNG = OUTDIR + '/X_EndPlate_L_3view.png'
LOGP = ROOT + '/refs/tmp/build_autocad_3view.log'

os.makedirs(OUTDIR, exist_ok=True)
_f = open(LOGP, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

data = json.load(open(SRC, encoding='utf-8'))
P('SOURCE', data['source'], 'bbox', data['bbox'], 'V=%.3f' % data['volume'])

# ------------------------------------------------------------------ 图幅/布局
W, H = 420.0, 297.0                     # A3 横向
M = 10.0                                # 内框边距
# 第一角布局：三视图共享 X（长对正）或 Z（高平齐）
LAYOUT = {
    'FRONT': dict(ox=100.0, oy=43.0),   # x=X+100 (100..153), y=Z+43  (160..200)
    'TOP':   dict(ox=100.0, oy=165.0),  # x=X+100 (100..153), y=Y+165 ( 86..128)
    'LEFT':  dict(ox=264.0, oy=43.0),   # x=Y+264 (185..227), y=Z+43  (160..200)
}
VB = {'FRONT': (100, 160, 153, 200),
      'TOP':   (100,  86, 153, 128),
      'LEFT':  (185, 160, 227, 200)}
GX0, GY0, GX1, GY1 = 100.0, 86.0, 227.0, 200.0   # 视图组外接矩形

# ------------------------------------------------------------------ 文档与图层
doc = ezdxf.new('R2010', setup=True)
doc.header['$INSUNITS'] = units.MM
doc.header['$MEASUREMENT'] = 1
doc.header['$LUNITS'] = 2
doc.header['$LUPREC'] = 2
doc.header['$DIMTXT'] = 2.2
doc.header['$EXTMIN'] = (0, 0, 0)
doc.header['$EXTMAX'] = (W, H, 0)

LAYERS = [
    # name,     color, linetype,     lineweight, off,  desc
    ('FRAME',    7, 'CONTINUOUS', 25, False, '图框 / 标题栏'),
    ('GRID',     9, 'DOT',         9, False, 'A~C / 1~3 区域网格'),
    ('OUTLINE',  7, 'CONTINUOUS', 35, False, '可见轮廓（HLR 真实消隐）'),
    ('HIDDEN',   8, 'DASHED',     18, True,  '隐藏线（默认关闭）'),
    ('CENTER',   4, 'CENTER',     18, False, '孔中心线'),
    ('FOCUS',    6, 'DASHED',     25, False, '上次讨论的敞开让位长槽定位框'),
    ('DIM',      2, 'CONTINUOUS', 18, False, '尺寸'),
    ('NOTE',     3, 'CONTINUOUS', 18, False, '说明文字'),
    ('MARKUP',   1, 'CONTINUOUS', 50, False, '【当前层】用户画圈 / 箭头 / 编号'),
]
for name, color, lt, lw, off, desc in LAYERS:
    lyr = doc.layers.new(name, dxfattribs={'color': color, 'linetype': lt,
                                           'lineweight': lw})
    if off:
        lyr.off()
    lyr.description = desc

try:
    doc.styles.new('HZ', dxfattribs={'font': 'simhei.ttf'})
except Exception:
    pass
doc.header['$CLAYER'] = 'MARKUP'
msp = doc.modelspace()

# ------------------------------------------------------------------ 绘图工具
def L(p0, p1, layer):
    msp.add_line(tuple(p0), tuple(p1), dxfattribs={'layer': layer})

def PL(pts, layer):
    if len(pts) == 2:
        L(pts[0], pts[1], layer)
    elif len(pts) > 2:
        msp.add_lwpolyline([tuple(q) for q in pts], dxfattribs={'layer': layer})

def C(c, r, layer):
    msp.add_circle(tuple(c), r, dxfattribs={'layer': layer})

def T(txt, x, y, h=2.2, layer='NOTE', style='Standard', rot=0):
    msp.add_text(str(txt), dxfattribs={
        'insert': (x, y), 'height': h, 'layer': layer,
        'style': style, 'rotation': rot})

def RECT(x0, y0, x1, y1, layer):
    PL([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], layer)

def cross(cx, cy, r, layer='CENTER'):
    d = r + 2.5
    L((cx - d, cy), (cx + d, cy), layer)
    L((cx, cy - d), (cx, cy + d), layer)

def tick(x, y, layer='DIM', size=1.6):
    L((x - size, y - size), (x + size, y + size), layer)

def dim_h(x0, x1, yref, ydim, label, layer='DIM'):
    """水平尺寸：x0/x1 为被注尺寸两端，yref 为图形上的引出基准，ydim 尺寸线高度"""
    L((x0, yref - 1.0), (x0, ydim + 2.5), layer)
    L((x1, yref - 1.0), (x1, ydim + 2.5), layer)
    L((x0, ydim), (x1, ydim), layer)
    tick(x0, ydim, layer); tick(x1, ydim, layer)
    T(label, (x0 + x1) / 2 - len(label) * 0.62, ydim + 1.4, 2.2, layer)

def dim_v(y0, y1, xref, xdim, label, layer='DIM'):
    """竖直尺寸；尺寸线在图形左侧时文字也放左侧，避免压住图形"""
    right = xdim >= xref
    xa, xb = (xref - 1.0, xdim + 2.5) if right else (xref + 1.0, xdim - 2.5)
    L((xa, y0), (xb, y0), layer)
    L((xa, y1), (xb, y1), layer)
    L((xdim, y0), (xdim, y1), layer)
    tick(xdim, y0, layer); tick(xdim, y1, layer)
    tx = xdim + 2.0 if right else xdim - 11.0
    T(label, tx, (y0 + y1) / 2 - 1.0, 2.2, layer)

def leader(p_from, p_to, txt, layer='DIM', h=2.1):
    L(p_from, p_to, layer)
    L(p_to, (p_to[0] + 4.0, p_to[1]), layer)
    T(txt, p_to[0] + 4.8, p_to[1] + 0.4, h, layer)

# ------------------------------------------------------------------ 图框 / 标题栏
RECT(0, 0, W, H, 'FRAME')
RECT(M, M, W - M, H - M, 'FRAME')
TB_X0, TB_Y0, TB_X1, TB_Y1 = 240.0, M, W - M, 54.0
RECT(TB_X0, TB_Y0, TB_X1, TB_Y1, 'FRAME')
for yy in (24.0, 38.0):
    L((TB_X0, yy), (TB_X1, yy), 'FRAME')
for xx in (TB_X0 + 58, TB_X0 + 112):
    L((xx, TB_Y0), (xx, TB_Y1), 'FRAME')
T('PART  零件', TB_X0 + 3, 44.0, 1.9, 'FRAME', 'HZ')
T('X_EndPlate_L', TB_X0 + 3, 39.6, 2.5, 'FRAME')
T('X轴电机侧端板', TB_X0 + 3, 31.5, 1.9, 'FRAME', 'HZ')
T('X motor-side end plate', TB_X0 + 3, 26.5, 1.7, 'FRAME')
T('MATERIAL  PETG-FDM 异型结构件', TB_X0 + 3, 18.5, 1.9, 'FRAME', 'HZ')
T('DATE 2026-11-10   REV v13.2 / v14', TB_X0 + 3, 12.5, 1.8, 'FRAME')
T('SCALE 1:1   UNIT mm', TB_X0 + 61, 44.0, 1.9, 'FRAME')
T('第一角 First-angle', TB_X0 + 61, 31.5, 1.9, 'FRAME', 'HZ')
T('PROJECTION', TB_X0 + 61, 26.5, 1.7, 'FRAME')
T('FreeCAD 1.1 / HLR', TB_X0 + 61, 18.5, 1.8, 'FRAME')
T('DRAWING X_EndPlate_L_3view', TB_X0 + 115, 44.0, 1.8, 'FRAME')
T('CrossSlide_P014013', TB_X0 + 115, 31.5, 1.8, 'FRAME')
T('FCStd', TB_X0 + 115, 26.5, 1.7, 'FRAME')
T('HLR: TechDraw.project() | 1:1', TB_X0 + 115, 12.5, 1.7, 'FRAME')

T('X_EndPlate_L  三视图 / THREE ORTHOGRAPHIC VIEWS', 100, 262, 4.4, 'NOTE', 'HZ')
T('用于图形化沟通：请在 MARKUP 层（红）画圈 / 箭头 / 编号后截图回传', 100, 255, 2.3, 'NOTE', 'HZ')
T('MARK UP ON LAYER "MARKUP" (red), then send a screenshot back', 100, 250.5, 2.0, 'NOTE')

# ------------------------------------------------------------------ 区域网格 A~C / 1~3
for i in range(1, 3):
    x = GX0 + (GX1 - GX0) * i / 3.0
    L((x, GY0), (x, GY1), 'GRID')
for j in range(1, 3):
    y = GY0 + (GY1 - GY0) * j / 3.0
    L((GX0, y), (GX1, y), 'GRID')
for i, lab in enumerate(('1', '2', '3')):
    x = GX0 + (GX1 - GX0) * (i + 0.5) / 3.0
    T(lab, x - 0.7, GY1 + 4.0, 3.0, 'NOTE')
for j, lab in enumerate(('C', 'B', 'A')):
    y = GY0 + (GY1 - GY0) * (j + 0.5) / 3.0
    T(lab, GX0 - 6.0, y - 1.0, 3.0, 'NOTE')

# ------------------------------------------------------------------ 三视图几何
counts = {}
for V in data['views']:
    name = V['name']
    ox, oy = LAYOUT[name]['ox'], LAYOUT[name]['oy']
    nv = nh = 0
    for en in V['entities']:
        layer = 'OUTLINE' if en['vis'] else 'HIDDEN'
        if en['t'] == 'circle':
            C((en['c'][0] + ox, en['c'][1] + oy), en['r'], layer)
        elif en['t'] == 'line':
            p = [(q[0] + ox, q[1] + oy) for q in en['p']]
            PL(p, layer)
        else:
            p = [(q[0] + ox, q[1] + oy) for q in en['p']]
            PL(p, layer)
        if en['vis']:
            nv += 1
        else:
            nh += 1
    counts[name] = (nv, nh)
    P('VIEW %-6s visible=%3d hidden=%3d  offset=(%.1f, %.1f)' % (name, nv, nh, ox, oy))
    # 视图标签
    x0, y0, x1, y1 = VB[name]
    T('%s  %s' % (V['label'], V['why']), x0, y1 + 13.0, 2.6, 'NOTE', 'HZ')
    T('(%s horizontal, %s vertical)' % (V['xaxis'], V['yaxis']), x0, y1 + 9.2, 1.9, 'NOTE')
    L((x0, y1 + 7.5), (x1, y1 + 7.5), 'FRAME')

# ------------------------------------------------------------------ 中心线
# HLR 实测：Ø22.8 电机孔中心 X21.00 / Z137.00，孔轴沿 Y → 在 FRONT 视图成圆
# 水平中心线贯穿主视图，竖直中心线只给大圆
L((96.0, 137.0 + 43.0), (156.0, 137.0 + 43.0), 'CENTER')
L((121.0, 166.0), (121.0, 194.0), 'CENTER')
# 俯视图上 GT2 皮带中心线 Y=-68.00（X_Belt_GT2 Y-71..-65）
L((96.0, -68.0 + 165.0), (156.0, -68.0 + 165.0), 'CENTER')

# ------------------------------------------------------------------ 尺寸
# FRONT：总长 53.00 / 总高 40.00
dim_h(100, 153, 160, 146, '53.00')
dim_v(160, 200, 100, 88, '40.00')
# TOP：总宽 42.00
dim_v(86, 128, 153, 162, '42.00')
# LEFT：限位开关槽 20.80（冻结项 Z120.85..141.65）
dim_v(120.85 + 43, 141.65 + 43, 227, 238, '20.80')
T('LIMIT POCKET (FROZEN)', 231, 138.0, 1.8, 'DIM')
T('Z120.85..141.65', 231, 134.8, 1.8, 'DIM')
# LEFT：总高 40.00
dim_v(160, 200, 227, 249, '40.00')
# 电机孔引注（起点 = 主视图大圆右上缘），皮带孔引注（起点 = 左视图皮带孔中心）
leader((129.0, 188.0), (160.0, 152.0), 'MOTOR BORE D22.80 (axis Y)')
leader((264.0 - 68.0, 137.0 + 43.0), (232.0, 154.0), 'GT2 SLOT 6.20x13.40')
# 俯视图：长条让位槽引注
leader((145.0, 100.0), (160.0, 78.0), 'OPEN RELIEF SLOT  X38..53')
# 限位开关 2xM2.5 孔距
dim_v(126.50 + 43, 136.00 + 43, 185, 176, '9.50')

# ------------------------------------------------------------------ FOCUS：上次讨论的开口
# 俯视图里 X38..53 / Y-79..-57 这块「敞开让位长槽」
RECT(38 + 100, -79 + 165, 53 + 100, -57 + 165, 'FOCUS')
L((153, 97), (157, 100), 'FOCUS')
T('TARGET?', 158, 99.5, 2.0, 'FOCUS')
# 左视图不再重复画框：Y-79..-57 全宽全高会盖住半个视图，反而干扰标注

# ------------------------------------------------------------------ 右侧说明区
NX, NY = 276.0, 262.0
def NOTE(txt, dy, h=2.1, style='Standard'):
    global NY
    T(txt, NX, NY - dy, h, 'NOTE', style)

NOTE('NOTES / 说明', 0, 3.0, 'HZ')
NY -= 4
NOTES = [
    ('1  第一角投影 First-angle projection', 'HZ'),
    ('   FRONT 主视图  沿 -Y 观察  →  X-Z 平面', 'HZ'),
    ('   TOP   俯视图  沿 -Z 观察  →  X-Y 平面', 'HZ'),
    ('   LEFT  左视图  沿 -X 观察  →  Y-Z 平面', 'HZ'),
    ('   长对正 FRONT/TOP (X) · 高平齐 FRONT/LEFT (Z)', 'HZ'),
    ('   宽相等 TOP/LEFT (Y)', 'HZ'),
    ('', 'Standard'),
    ('2  单位 mm，比例 1:1，模型空间为真实坐标', 'HZ'),
    ('   Units mm, scale 1:1, true model coordinates', 'Standard'),
    ('', 'Standard'),
    ('3  当前层 = MARKUP（红色），请在此层画圈 / 箭头 / 编号', 'HZ'),
    ('   Draw circles / arrows / numbers on layer MARKUP', 'Standard'),
    ('   可用 A~C + 1~3 区域编号指认位置，如 "B2 的槽"', 'HZ'),
    ('', 'Standard'),
    ('4  隐藏线在 HIDDEN 层，默认关闭；需要时打开', 'HZ'),
    ('   Hidden edges: layer HIDDEN, switched OFF by default', 'Standard'),
    ('   FOCUS 层（洋红虚线）= 上次讨论的敞开让位长槽', 'HZ'),
    ('   GRID 层 = 区域网格，可关闭', 'HZ'),
    ('', 'Standard'),
    ('KEY FEATURES / 关键特征', 'HZ'),
    ('  A  BBox X0..53 / Y-79..-37 / Z117..157', 'Standard'),
    ('  B  Limit pocket Z120.85..141.65 = 20.80 (FROZEN)', 'Standard'),
    ('  C  Open relief slot  X38..53 / Y-79..-57', 'Standard'),
    ('  D  Motor bore D22.80  X21.00 Z137.00, axis Y', 'Standard'),
    ('  E  GT2 belt slot 6.20 x 13.40  at X50.00', 'Standard'),
    ('  F  2 x D2.60 limit-switch holes, pitch 9.50', 'Standard'),
    ('  G  Material PETG-FDM; Z-axis 22.00 slot untouched', 'Standard'),
]
for i, (txt, style) in enumerate(NOTES):
    T(txt, NX, NY - i * 5.0, 2.0, 'NOTE', style)

# ------------------------------------------------------------------ 保存
doc.saveas(DXF)
P('')
P('WROTE', DXF, os.path.getsize(DXF), 'bytes')
P('LAYERS', ', '.join('%s%s' % (n, '(off)' if o else '') for n, _, _, _, o, _ in LAYERS))
P('ENTITIES', len(msp))
P('BUILD DXF DONE')
_f.close()
