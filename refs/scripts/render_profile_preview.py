# -*- coding: utf-8 -*-
"""型材阶段预览与精确截面出图：白化等轴测图 + 截面差异 / 1:1 复刻对比图。

用户 2026-11-13：「你拉出型材后先让我在 solidcraft 里看看」
→ 「铝型材的横截面是这样的」「按我给的横截面图重新设计」。
.sc 文件才是主交付；这些图只是让截面差异和精确复刻结果一眼可见。
"""
import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('C:/ink')
USER = Path('D:/mydocuments/SolidCraft')
FONT_REG = 'C:/Windows/Fonts/msyh.ttc'
FONT_BOLD = 'C:/Windows/Fonts/msyhbd.ttc'

ISO_SRC = USER / 'LM6UU_Profile_Preview_iso.png'
ISO_OUT = ROOT / 'solidcraft/LM6UU_Profile_Preview_iso_white.png'
CMP_OUT = ROOT / 'solidcraft/LM6UU_Profile_Preview_section.png'


def font(path, size):
    return ImageFont.truetype(path, size)


# ---- 1) 等轴测图：逐行背景白化 + 紧裁 -----------------------------------
im = Image.open(ISO_SRC).convert('RGB')
a = np.asarray(im).astype(np.float32)
h, w, _ = a.shape
edge = np.concatenate([a[:, :60, :], a[:, -60:, :]], axis=1)
bg = np.median(edge, axis=1)                       # (h,3) 每行背景
d = np.max(np.abs(a - bg[:, None, :]), axis=2)
wt = np.clip((10.0 - d) / 7.0, 0.0, 1.0)
white = (255.0 - bg)[:, None, :]
out = np.clip(a + white * wt[..., None], 0, 255).astype(np.uint8)

mask = np.max(255 - out.astype(np.int16), axis=2) > 14
ys, xs = np.where(mask)
margin = 70
x0, x1 = max(0, xs.min() - margin), min(w, xs.max() + margin)
y0, y1 = max(0, ys.min() - margin), min(h, ys.max() + margin)
crop = Image.fromarray(out[y0:y1, x0:x1])
crop.save(ISO_OUT)
print('ISO', ISO_OUT, crop.size)


# ---- 2) 预览截面：按 12_profile_preview.json 的参数做 2D 布尔 -----------
W, H = 20.0, 40.0
S = 12                                              # px / mm
gw, gh = int(W * S), int(H * S)
u = (np.arange(gw) + 0.5) / S
v = H - (np.arange(gh) + 0.5) / S                  # 图像顶部 = v 最大
U, V = np.meshgrid(u, v)
inside = np.ones((gh, gw), dtype=bool)


def cut(x0, x1, y0, y1):
    global inside
    inside &= ~((U >= x0) & (U <= x1) & (V >= y0) & (V <= y1))


SLOT_W, SLOT_D, CAV_W, CAV_D = 6.0, 2.0, 11.0, 5.0
CORE_U, CORE_V, WALL = 2.0, 12.0, 1.0
CORNER_U, CORNER_V = 2.6, 5.5
hs, hc = SLOT_W / 2, CAV_W / 2

# 4 条 T 槽（每边居中）：窄槽口 + 宽内腔
cut(W / 2 - hs, W / 2 + hs, 0, SLOT_D)
cut(W / 2 - hc, W / 2 + hc, SLOT_D, SLOT_D + CAV_D)
cut(W / 2 - hs, W / 2 + hs, H - SLOT_D, H)
cut(W / 2 - hc, W / 2 + hc, H - SLOT_D - CAV_D, H - SLOT_D)
cut(0, SLOT_D, H / 2 - hs, H / 2 + hs)
cut(SLOT_D, SLOT_D + CAV_D, H / 2 - hc, H / 2 + hc)
cut(W - SLOT_D, W, H / 2 - hs, H / 2 + hs)
cut(W - SLOT_D - CAV_D, W - SLOT_D, H / 2 - hc, H / 2 + hc)

# 中心腔
cut(W / 2 - CORE_U, W / 2 + CORE_U, H / 2 - CORE_V, H / 2 + CORE_V)

# 四角减重腔
a0, a1 = WALL, WALL + CORNER_U
a2, a3 = W - WALL - CORNER_U, W - WALL
b0 = SLOT_D + CAV_D + WALL
b1 = b0 + CORNER_V
b2 = H - SLOT_D - CAV_D - WALL - CORNER_V
b3 = H - SLOT_D - CAV_D - WALL
for r in [(a0, a1, b0, b1), (a2, a3, b0, b1),
          (a0, a1, b2, b3), (a2, a3, b2, b3)]:
    cut(*r)

area_prev = float(inside.mean()) * W * H
print('preview section area %.2f mm2  fill %.1f%%' % (area_prev, 100 * area_prev / (W * H)))

preview_img = Image.fromarray(np.where(inside, 70, 255).astype(np.uint8), 'L').convert('RGB')


# ---- 3) 真实截面：FCStd BREP 提取的 44×44 点阵 -------------------------
d = json.load(open(ROOT / 'refs/tmp/profile_sections.json', encoding='utf-8'))
ascii_rows = d['profiles']['X_Profile']['ascii']
if isinstance(ascii_rows, str):
    ascii_rows = ascii_rows.splitlines()
nr, nc = len(ascii_rows), len(ascii_rows[0])
real = Image.new('RGB', (gw, gh), 'white')
dr = ImageDraw.Draw(real)
for r, line in enumerate(ascii_rows):
    for c, ch in enumerate(line):
        if ch == '#':
            dr.rectangle([c * gw / nc, r * gh / nr,
                          (c + 1) * gw / nc, (r + 1) * gh / nr],
                         fill=(70, 70, 70))
area_real = d['profiles']['X_Profile']['section_area_approx']


# ---- 4) 拼对比图 ---------------------------------------------------------
CW, CH = 1500, 940
canvas = Image.new('RGB', (CW, CH), 'white')
D = ImageDraw.Draw(canvas)
f_title = font(FONT_BOLD, 40)
f_sub = font(FONT_REG, 21)
f_name = font(FONT_BOLD, 27)
f_meta = font(FONT_REG, 19)
f_small = font(FONT_REG, 17)

D.text((60, 36), '2040 铝型材截面 · SolidCraft 原生预览 vs FreeCAD 原始',
       font=f_title, fill=(25, 30, 40))
D.text((60, 92), '阶段预览：仅型材，未做端板 / 滑车。零 STEP，22 个命名参数，30 个可编辑特征。',
       font=f_sub, fill=(95, 105, 120))
D.line([(60, 132), (CW - 60, 132)], fill=(220, 225, 232), width=2)

SCALE = 1.62
tw, th = int(gw * SCALE), int(gh * SCALE)
left_x, right_x, top_y = 150, 880, 205


def panel(x, img, title, lines, accent):
    D.text((x, 158), title, font=f_name, fill=accent)
    big = img.resize((tw, th), Image.NEAREST)
    canvas.paste(big, (x, top_y))
    D.rectangle([x - 2, top_y - 2, x + tw + 2, top_y + th + 2],
                outline=(205, 212, 222), width=2)
    yy = top_y + th + 26
    for t in lines:
        D.text((x, yy), t, font=f_meta, fill=(60, 68, 80))
        yy += 30


panel(left_x, real, '① FreeCAD 原始 BREP 截面', [
    '面积 302.81 mm²  ·  填充率 37.9%',
    '6 条 T 槽（40 面各 2 / 20 面各 1）',
    '中心十字筋 + 四角减重腔',
], (35, 95, 165))

panel(right_x, preview_img, '② SolidCraft 原生预览', [
    '面积 %.2f mm²  ·  填充率 %.1f%%' % (area_prev, 100 * area_prev / (W * H)),
    '4 条 T 槽（每边居中）+ 中心腔 + 四角腔',
    '体积比真实高 +25.1%（阶段件，待精调）',
], (190, 105, 35))

D.text((60, CH - 62),
       '结论：截面形态已是薄壁挤压件（v1 全原生是实心方棒，填充率 78%）；但槽数与腔体仍与原始有差距。',
       font=f_small, fill=(120, 128, 140))
D.text((60, CH - 34),
       '请在 SolidCraft GUI 打开 LM6UU_Profile_Preview.sc 并 View → Fit 确认观感，再决定是否继续做高保真截面。',
       font=f_small, fill=(120, 128, 140))

canvas.save(CMP_OUT)
print('CMP', CMP_OUT, canvas.size)

# ---- 5) 同步到 GUI 用户目录 ---------------------------------------------
for p in (ISO_OUT, CMP_OUT):
    dst = USER / p.name
    dst.write_bytes(p.read_bytes())
    print('COPIED', dst)


# ---- 6) 精确截面版：等轴测白图 + 「BREP 原始 vs SolidCraft 1:1」对比 ----
EXACT_ISO_SRC = ROOT / 'solidcraft/LM6UU_Profile_Exact_iso.png'
EXACT_ISO_OUT = ROOT / 'solidcraft/LM6UU_Profile_Exact_iso_white.png'
EXACT_CMP_OUT = ROOT / 'solidcraft/LM6UU_Profile_Exact_section.png'

im = Image.open(EXACT_ISO_SRC).convert('RGB')
a = np.asarray(im).astype(np.float32)
h, w, _ = a.shape
edge = np.concatenate([a[:, :60, :], a[:, -60:, :]], axis=1)
bg = np.median(edge, axis=1)
diff = np.max(np.abs(a - bg[:, None, :]), axis=2)
wt = np.clip((10.0 - diff) / 7.0, 0.0, 1.0)
white = (255.0 - bg)[:, None, :]
out = np.clip(a + white * wt[..., None], 0, 255).astype(np.uint8)
mask = np.max(255 - out.astype(np.int16), axis=2) > 14
ys, xs = np.where(mask)
margin = 70
x0, x1 = max(0, xs.min() - margin), min(w, xs.max() + margin)
y0, y1 = max(0, ys.min() - margin), min(h, ys.max() + margin)
crop = Image.fromarray(out[y0:y1, x0:x1])
crop.save(EXACT_ISO_OUT)
print('EXACT ISO', EXACT_ISO_OUT, crop.size)

exact = json.load(open(ROOT / 'refs/tmp/profile_contours.json', encoding='utf-8'))
prof = exact['profiles']['X_Profile']
face_area = float(prof['face_area'])
rebuilt_area = float(prof['rebuilt_area'])
eval_exact = json.load(open(ROOT / 'refs/tmp/profile_exact_eval.json', encoding='utf-8'))
vol = {b['name']: b for b in eval_exact['bodies']}
target_x, target_z = 60561.58668365398, 45421.19001274048
err_x = 100.0 * (vol['X_Profile']['volume_mm3'] / target_x - 1.0)
err_z = 100.0 * (vol['Z_Profile']['volume_mm3'] / target_z - 1.0)

W, H = 20.0, 40.0
S = 12
AA = 4
umin, umax = float(prof['u_range'][0]), float(prof['u_range'][1])
vmin, vmax = float(prof['v_range'][0]), float(prof['v_range'][1])
gw0, gh0 = int(W * S), int(H * S)
gw, gh = gw0 * AA, gh0 * AA


def tx(p):
    return ((float(p[0]) - umin) * S * AA,
            (vmax - float(p[1])) * S * AA)


def circle_from3(p0, p1, p2):
    ax, ay = map(float, p0)
    bx, by = map(float, p1)
    cx, cy = map(float, p2)
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) +
          (bx * bx + by * by) * (cy - ay) +
          (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) +
          (bx * bx + by * by) * (ax - cx) +
          (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy), math.hypot(ux - ax, uy - ay)


def arc_points(p, n=14):
    a, m, b = p['start'], p['through'], p['end']
    (cx, cy), r = circle_from3(a, m, b)
    a0 = math.atan2(float(a[1]) - cy, float(a[0]) - cx)
    a1 = math.atan2(float(b[1]) - cy, float(b[0]) - cx)
    am = math.atan2(float(m[1]) - cy, float(m[0]) - cx)
    tau = 2.0 * math.pi
    ccw = (a1 - a0) % tau
    if (am - a0) % tau <= ccw + 1e-9:
        sweep = ccw
    else:
        sweep = -((a0 - a1) % tau)
    pts = [a]
    for k in range(1, n + 1):
        t = a0 + sweep * k / float(n)
        pts.append([cx + r * math.cos(t), cy + r * math.sin(t)])
    pts[-1] = b
    return pts


def wire_points(wire):
    pts = [wire['start']]
    for p in wire['primitives']:
        if p['type'] == 'line':
            pts.append(p['end'])
        else:
            pts.extend(arc_points(p)[1:])
    return pts


def poly(img, pts, fill, outline=None, width=1):
    dr = ImageDraw.Draw(img)
    q = [tx(p) for p in pts]
    dr.polygon(q, fill=fill)
    if outline:
        dr.line(q + [q[0]], fill=outline, width=width, joint='curve')


exact_img = Image.new('RGB', (gw, gh), 'white')
outer = prof['wires'][0]
center = prof['wires'][2]
poly(exact_img, wire_points(outer), (70, 76, 84), (25, 30, 38), 2 * AA)
poly(exact_img, wire_points(center), 'white', (25, 30, 38), 2 * AA)
dr = ImageDraw.Draw(exact_img)
for hole in (prof['wires'][1], prof['wires'][3]):
    cx, cy = tx(hole['center'])
    rr = hole['radius'] * S * AA
    dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
              fill='white', outline=(25, 30, 38), width=2 * AA)
exact_img = exact_img.resize((gw0, gh0), Image.LANCZOS)

sections = json.load(open(ROOT / 'refs/tmp/profile_sections.json', encoding='utf-8'))
ascii_rows = sections['profiles']['X_Profile']['ascii']
if isinstance(ascii_rows, str):
    ascii_rows = ascii_rows.splitlines()
nr, nc = len(ascii_rows), len(ascii_rows[0])
real_exact = Image.new('RGB', (gw0, gh0), 'white')
dr = ImageDraw.Draw(real_exact)
for r, line in enumerate(ascii_rows):
    for c, ch in enumerate(line):
        if ch == '#':
            dr.rectangle([c * gw0 / nc, r * gh0 / nr,
                          (c + 1) * gw0 / nc, (r + 1) * gh0 / nr],
                         fill=(70, 76, 84))

CW, CH = 1500, 940
canvas = Image.new('RGB', (CW, CH), 'white')
D = ImageDraw.Draw(canvas)
f_title = font(FONT_BOLD, 40)
f_sub = font(FONT_REG, 21)
f_name = font(FONT_BOLD, 27)
f_meta = font(FONT_REG, 19)
f_small = font(FONT_REG, 17)
D.text((60, 36), '2040 铝型材截面 · BREP 原始 vs SolidCraft 精确复刻',
       font=f_title, fill=(25, 30, 40))
D.text((60, 92), '按用户给的横截面图重建：零 STEP，全原生草图，外轮廓 / 圆角 / 中心腔 / 两个 Ø5 孔 1:1 复刻。',
       font=f_sub, fill=(95, 105, 120))
D.line([(60, 132), (CW - 60, 132)], fill=(220, 225, 232), width=2)

SCALE = 1.62
tw, th = int(gw0 * SCALE), int(gh0 * SCALE)
left_x, right_x, top_y = 150, 880, 205


def panel(x, img, title, lines, accent, nearest=False):
    D.text((x, 158), title, font=f_name, fill=accent)
    big = img.resize((tw, th), Image.NEAREST if nearest else Image.LANCZOS)
    canvas.paste(big, (x, top_y))
    D.rectangle([x - 2, top_y - 2, x + tw + 2, top_y + th + 2],
                outline=(205, 212, 222), width=2)
    yy = top_y + th + 26
    for t in lines:
        D.text((x, yy), t, font=f_meta, fill=(60, 68, 80))
        yy += 30


panel(left_x, real_exact, '① FreeCAD / 用户图原始截面', [
    '净截面积 %.3f mm²  ·  填充率 %.2f%%' % (face_area, 100 * face_area / (W * H)),
    '6 条 T 槽 + 4 个 R1.5 圆角',
    '中心异型腔 + 2 个 Ø5 孔 + 346 面',
], (35, 95, 165), nearest=True)

panel(right_x, exact_img, '② SolidCraft 精确复刻截面', [
    '净截面积 %.3f mm²  ·  填充率 %.2f%%' % (rebuilt_area, 100 * rebuilt_area / (W * H)),
    '原生草图：286 直线 + 4 圆弧 + 52 边腔 + 2 圆',
    'X 体积误差 %+.4f%%  ·  Z 体积误差 %+.4f%%' % (err_x, err_z),
], (25, 135, 90))

D.text((60, CH - 62),
       '结论：截面曲线、孔位、面数（346 面/件）与原始 BREP 对齐；两根型材均为单一闭合壳，体积误差 < 0.003%。',
       font=f_small, fill=(120, 128, 140))
D.text((60, CH - 34),
       'GUI 文件：D:\\mydocuments\\SolidCraft\\LM6UU_Profile_Exact.sc  ·  打开后 View → Fit。端板 / 滑车继续后续重建。',
       font=f_small, fill=(120, 128, 140))
canvas.save(EXACT_CMP_OUT)
print('EXACT CMP', EXACT_CMP_OUT, canvas.size)

for p in (EXACT_ISO_OUT, EXACT_CMP_OUT):
    dst = USER / p.name
    dst.write_bytes(p.read_bytes())
    print('COPIED', dst)
