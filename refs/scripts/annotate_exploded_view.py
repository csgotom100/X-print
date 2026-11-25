# -*- coding: utf-8 -*-
"""
Annotate the V2 SolidCraft exploded view:

  * white background (replaces the dark viewport colour [46,52,64])
  * 11 Chinese part-group labels with leader lines
  * a dashed, arrowed assembly-order chain (1->10 plus a parallel branch)
  * numbered badges auto-nudged apart when two 3D centroids project to nearly
    the same pixel (seq 2 / seq 3 were 13.5 px apart, badges are 42 px wide);
    a short tether in the group colour links each nudged badge to its anchor
  * the Z stepper motor is exploded along its mounting-screw axis (pure +Y),
    not diagonally; its action text and the footnote call this out
  * leader dots are pixel-verified: four groups whose projected 3D centroid
    landed on a neighbouring group / a gap / background use ANCHOR_OVERRIDES,
    checked against a per-group flat-colour render by
    refs/scripts/verify_exploded_anchors.py

Pixel anchors are computed, not eye-balled:
  per-part 3D bounding boxes + each group's explode translate give the group
  centroid in 3D; the camera is an orthographic Z-up isometric view
  (yaw -45 deg, pitch 35.264 deg), whose screen projection is
        u = 0.8660254*(X + Y)        (screen right)
        v = 0.5*(X - Y) - Z          (screen down)
  The (u,v) extent of *all* part corners is mapped linearly onto the measured
  model bounding box of the render, so the calibration stays valid if the
  render is regenerated. Cross-checked against connected components of the
  image: X carriage 19 px, capping station 14 px, HP45 head 60 px error.

Inputs:
  solidcraft/CrossSlide_exploded_v2.png
  refs/materials/geometry_snapshot_v14.json
  solidcraft/EXPLODED_GROUPS_V2.csv
Outputs:
  solidcraft/CrossSlide_exploded_v2_white.png       (white, no annotation)
  solidcraft/CrossSlide_exploded_v2_annotated.png   (final: white + labels + chain)
  solidcraft/EXPLODED_ANNOTATIONS_V2.csv           (anchor / label / order audit)
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SC = ROOT / "solidcraft"
SRC = SC / "CrossSlide_exploded_v2.png"
WHITE = SC / "CrossSlide_exploded_v2_white.png"
ANNOT = SC / "CrossSlide_exploded_v2_annotated.png"
AUDIT = SC / "EXPLODED_ANNOTATIONS_V2.csv"
GROUPS_CSV = SC / "EXPLODED_GROUPS_V2.csv"
GEO = ROOT / "refs/materials/geometry_snapshot_v14.json"

FONT_REG = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
BG = np.array([46, 52, 64], dtype=np.float32)

TOP, BOTTOM = 150, 240
LABEL_W, LABEL_H = 290, 76
BADGE_R = 21                 # numbered badge outer radius
MIN_BADGE_SEP = 52           # keep >= 10 px clear gap between two badges

# ---------------------------------------------------------------- anchors
# A group's 3D centroid, projected isometrically, does not always land ON one
# of that group's parts: it can fall into a gap between two separated parts,
# behind a nearer part of another group, or on empty background.  A per-group
# flat-colour render (refs/tmp/exploded_v2_group_colours.png, re-checkable with
# refs/scripts/verify_exploded_anchors.py) exposed exactly four such cases:
#   seq 2 / 3 - the Z plates and Z belt-drive groups overlap in projection;
#               each centroid landed on the *other* group's pixels
#   seq 5     - the two KW11 switches sit far apart (y~564 and y~974), so the
#               centroid (1696,786) fell into the empty gap and showed the red
#               base frame behind it
#   seq 10    - the probe-group centroid landed on pure background
# These overrides snap the leader dot onto a pixel that really belongs to the
# group (>=85% local colour purity).  The other 7 groups were verified correct
# and keep their automatic projection anchors.
ANCHOR_OVERRIDES = {
    "Z 端板与导杆":    (1867, 255),
    "Z 同步带传动":    (1822, 220),
    "Z 限位开关":      (1720, 974),   # lower KW11-3Z-A-1 body
    "接触式探针总成":  (195, 802),
}

# (group name as in EXPLODED_GROUPS_V2.csv, seq, colour, short action, note)
ORDER = [
    ("Z 轴机架（固定基准）", 1, "#4B5563", "装配基准 · 底座与 2040 立柱",
     "Z_BaseBlock + Z_Profile + 底板/型材螺钉，全图唯一不动的基准"),
    ("Z 端板与导杆", 2, "#2563EB", "端板与两根 Ø10 导杆装入立柱",
     "Z 上下端板 + 两根导杆 + 固定螺钉"),
    ("Z 同步带传动", 3, "#0891B2", "GT2 轮 / 带 / 张紧件装到端板",
     "主动轮 / 惰轮 / 同步带 / 张紧垫片与螺母"),
    ("Z 步进电机", 4, "#7C3AED", "沿螺钉轴线 +Y 抽出 80 mm",
     "4 颗 Z_Screw_Motor_* 长轴 = Y（5.49×13.00×5.48）；电机本体在端板 +Y 侧、轴与主动轮在 −Y 侧，"
     "故从安装位沿安装螺钉轴线纯 +Y 平移抽出（dx=dz=0），不再 −X/−Y/+Z 斜向飞出"),
    ("Z 限位开关", 5, "#DB2777", "上下各一 KW11-3Z-A-1",
     "直压按钮式微动开关 + 4 颗 M2.5 限位螺钉；上下两开关分离较远，"
     "圆点经分色像素核实指向下方 KW11-3Z-A-1 本体，不再落在两开关之间的机架上"),
    ("Z 滑车 + XZ 连接板", 6, "#0D9488", "滑座套 Z 导杆挂带，XZ 板 M5 锁定",
     "上下滑座 + LM5UU + 嵌件 + 夹紧键 + XZ 连接板"),
    ("X 横梁总成", 7, "#EA580C", "经 XZ 板固定到 Z 滑车",
     "X 型材 / 端板 / 导杆 / 轮带 / 电机 / 限位整体装附"),
    ("X 滑车", 8, "#6366F1", "上下滑座扣合、夹紧 GT2 带",
     "扣合上下半滑座，套入 X 导杆并夹紧同步带"),
    ("HP45 喷头总成", 9, "#D97706", "夹具与转接板装到 X 滑车",
     "墨盒夹具五件 + 转接板 + 探针臂"),
    ("接触式探针总成", 10, "#DC2626", "侧装于喷头臂（+X 侧装）",
     "探针座侧装；磁环 / 弹簧 +X 侧装 → 探针 −Z 顶落 → 侧盖板扣合"),
    ("保湿站", 11, "#059669", "并行：独立装于底座 +X 侧",
     "与主链无先后依赖，作为机架附件独立装附"),
]
PARTS = {
    "Z 轴机架（固定基准）": 12, "Z 端板与导杆": 8, "Z 同步带传动": 7,
    "Z 步进电机": 6, "Z 限位开关": 6, "Z 滑车 + XZ 连接板": 23,
    "X 横梁总成": 30, "X 滑车": 10, "HP45 喷头总成": 18,
    "接触式探针总成": 13, "保湿站": 6,
}
MAIN_CHAIN = list(range(1, 11))   # 1 -> 2 -> ... -> 10
BRANCH = (1, 11)                 # parallel capping-station branch


def base_name(n):
    return re.sub(r" \(\d+\)$", "", n)


def font(path, size):
    return ImageFont.truetype(path, size)


# ------------------------------------------------------------------ white bg
def to_white(src):
    c = np.array(src.convert("RGB")).astype(np.float32)
    near = np.max(np.abs(c - BG), axis=2) <= 3
    ni = Image.fromarray((near * 255).astype(np.uint8))
    d1 = np.array(ni.filter(ImageFilter.MaxFilter(3))) > 0
    d2 = np.array(ni.filter(ImageFilter.MaxFilter(5))) > 0
    # an antialiased pixel c = a*fg + (1-a)*bg becomes
    # c + (white-bg)*(1-a) when composited onto white
    w = np.where(near, 1.0, np.where(d1, 0.62, np.where(d2, 0.24, 0.0)))
    out = np.clip(c + (255.0 - BG)[None, None, :] * w[..., None], 0, 255)
    white = Image.fromarray(out.astype(np.uint8))
    # model bbox measured on the *original* dark render
    dark = np.array(src.convert("RGB")).astype(np.int16)
    m = np.max(np.abs(dark - BG.astype(np.int16)), axis=2) > 14
    ys, xs = np.where(m)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return white, m, bbox


# ------------------------------------------------------------------ anchors
def projection_anchors(bbox):
    geo = json.loads(GEO.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(GROUPS_CSV.open(encoding="utf-8-sig")))
    corners, gc = [], defaultdict(list)
    for r in rows:
        n = base_name(r["零件名"])
        if n not in geo:                    # hidden auxiliary body
            continue
        b = geo[n]["bbox"]
        t = [float(r["dx mm"]), float(r["dy mm"]), float(r["dz mm"])]
        for x in (b[0], b[3]):
            for y in (b[1], b[4]):
                for z in (b[2], b[5]):
                    corners.append((x + t[0], y + t[1], z + t[2]))
        gc[r["功能组"]].append([
            (b[0] + b[3]) / 2 + t[0],
            (b[1] + b[4]) / 2 + t[1],
            (b[2] + b[5]) / 2 + t[2],
        ])
    P = np.array(corners)
    u = 0.8660254 * (P[:, 0] + P[:, 1])
    v = 0.5 * (P[:, 0] - P[:, 1]) - P[:, 2]
    umin, umax, vmin, vmax = u.min(), u.max(), v.min(), v.max()
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    s = min(bw / (umax - umin), bh / (vmax - vmin))
    ox = x0 + (bw - s * (umax - umin)) / 2 - s * umin
    oy = y0 + (bh - s * (vmax - vmin)) / 2 - s * vmin
    anchors, xyz = {}, {}
    for g, arr in gc.items():
        c = np.array(arr).mean(axis=0)
        uu, vv = 0.8660254 * (c[0] + c[1]), 0.5 * (c[0] - c[1]) - c[2]
        anchors[g] = (int(round(ox + s * uu)), int(round(oy + s * vv)))
        xyz[g] = [round(float(t), 2) for t in c]
    return anchors, xyz, round(float(s), 4)


# ------------------------------------------------------------------ layout
def place_labels(anchors, model_mask, W, H):
    m = np.array(Image.fromarray((model_mask * 255).astype(np.uint8))
                 .filter(ImageFilter.MaxFilter(13))) > 0
    integ = np.pad(m.astype(np.int64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def occ(x, y, w, h):
        return (integ[y+h, x+w] - integ[y, x+w]
                - integ[y+h, x] + integ[y, x])

    placed = {}
    for g, seq, *_ in ORDER:
        ax, ay = anchors[g]
        # Hug the anchor: the occupancy penalty pushes the box into the
        # nearest patch of empty background, which keeps leader lines short.
        tx, ty = ax, ay
        best, best_cost = None, 1e18
        for y in range(20, H - LABEL_H - 20, 14):
            for x in range(20, W - LABEL_W - 20, 14):
                if any(not (x + LABEL_W + 12 < px or px + LABEL_W + 12 < x or
                            y + LABEL_H + 12 < py or py + LABEL_H + 12 < y)
                       for px, py in placed.values()):
                    continue
                cx, cy = x + LABEL_W / 2, y + LABEL_H / 2
                # keeping the box on the anchor's horizontal band matters
                # more than a short horizontal offset: it stops leaders from
                # crossing each other.
                cost = (0.8 * abs(cx - tx) + 1.5 * abs(cy - ty)
                        + occ(x, y, LABEL_W, LABEL_H) * 3.0)
                if cost < best_cost:
                    best, best_cost = (x, y), cost
        placed[g] = best
    return placed


# ------------------------------------------------------------------ badges
def place_badges(anchors_canvas, W, H_canvas):
    """Push overlapping numbered badges apart.

    Two groups whose 3D centroids project to nearly the same pixel (e.g. seq 2
    'Z 端板与导杆' and seq 3 'Z 同步带传动', 13.5 px apart) would otherwise have
    their 42 px badges stacked: the later one hides the earlier one entirely.
    We iteratively separate any pair closer than MIN_BADGE_SEP along their
    connecting line, keeping the true anchor as the leader/chain endpoint and
    drawing a short tether from the anchor to the displaced badge.
    """
    pos = {g: [float(p[0]), float(p[1])] for g, p in anchors_canvas.items()}
    keys = list(pos)
    for _ in range(80):
        worst = 0.0
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
                d = math.hypot(dx, dy)
                if d < 1e-6:
                    dx, dy, d = 1.0, 0.0, 1.0
                if d < MIN_BADGE_SEP:
                    push = (MIN_BADGE_SEP - d) / 2.0 + 0.5
                    ux, uy = dx / d, dy / d
                    pos[a][0] += ux * push; pos[a][1] += uy * push
                    pos[b][0] -= ux * push; pos[b][1] -= uy * push
                    worst = max(worst, MIN_BADGE_SEP - d)
        if worst < 0.5:
            break
    # clamp inside canvas so no badge is cut at an edge
    for g in keys:
        pos[g][0] = min(max(pos[g][0], BADGE_R + 3), W - BADGE_R - 3)
        pos[g][1] = min(max(pos[g][1], TOP + BADGE_R + 3), H_canvas - BADGE_R - 3)
    return {g: (int(round(p[0])), int(round(p[1]))) for g, p in pos.items()}


# ------------------------------------------------------------------ drawing
def _dashed_raw(draw, p0, p1, fill, width, dash, gap):
    x0, y0 = p0; x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    s = 0.0
    while s < L:
        e = min(s + dash, L)
        draw.line([(x0 + ux*s, y0 + uy*s), (x0 + ux*e, y0 + uy*e)],
                  fill=fill, width=width)
        s += dash + gap


def dashed(draw, p0, p1, fill, width=3, dash=18, gap=11, halo=3):
    """White halo keeps the dashed chain readable over dark parts."""
    if halo:
        _dashed_raw(draw, p0, p1, "#FFFFFF", width + halo, dash, gap)
    _dashed_raw(draw, p0, p1, fill, width, dash, gap)


def arrow_head(draw, p0, p1, fill, size=13):
    x0, y0 = p0; x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0) or 1
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    px, py = -uy, ux
    draw.polygon([
        (x1, y1),
        (x1 - ux*size + px*size*0.48, y1 - uy*size + py*size*0.48),
        (x1 - ux*size - px*size*0.48, y1 - uy*size - py*size*0.48),
    ], fill=fill, outline="#FFFFFF", width=2)


def chain_segment(draw, p0, p1, fill, width=3, trim=26):
    x0, y0 = p0; x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0) or 1
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    trim = min(trim, L * 0.30)          # never eat a short segment entirely
    s = (x0 + ux*trim, y0 + uy*trim)
    e = (x1 - ux*trim, y1 - uy*trim)
    dashed(draw, s, e, fill, width)
    mx = s[0] + (e[0]-s[0])*0.60
    my = s[1] + (e[1]-s[1])*0.60
    arrow_head(draw, (mx-ux*17, my-uy*17), (mx, my), fill)


def txt_center(draw, xy, s, f, fill):
    x, y = xy
    bb = draw.textbbox((0, 0), s, font=f)
    draw.text((x - (bb[2]-bb[0])/2, y - (bb[3]-bb[1])/2 - bb[1]),
              s, font=f, fill=fill)


def main():
    src = Image.open(SRC).convert("RGB")
    W, H = src.size
    white, model_mask, bbox = to_white(src)
    white.save(WHITE, optimize=True)

    anchors, xyz, scale = projection_anchors(bbox)
    anchor_source = {g: "等轴测投影" for g in anchors}
    for g, p in ANCHOR_OVERRIDES.items():
        anchors[g] = p
        anchor_source[g] = "分色像素核实"
    boxes = place_labels(anchors, model_mask, W, H)
    H_canvas = H + TOP + BOTTOM
    anchors_c = {g: (x, y + TOP) for g, (x, y) in anchors.items()}
    badges = place_badges(anchors_c, W, H_canvas)

    canvas = Image.new("RGB", (W, H_canvas), "white")
    canvas.paste(white, (0, TOP))
    d = ImageDraw.Draw(canvas)

    f_title = font(FONT_BOLD, 44)
    f_sub = font(FONT_REG, 20)
    f_name = font(FONT_BOLD, 23)
    f_meta = font(FONT_REG, 15)
    f_leg = font(FONT_REG, 19)
    f_num = font(FONT_BOLD, 18)
    f_small = font(FONT_BOLD, 15)

    def P(g):
        x, y = anchors[g]
        return (x, y + TOP)

    # assembly-order chain, underneath everything else.
    # It connects the *numbered badges* (which may be nudged apart), so arrows
    # always land on a visible number rather than on a hidden stacked anchor.
    chain_fill = "#3E5266"
    by_seq = {s: g for g, s, *_ in ORDER}
    def B(g):
        return badges[g]
    for a, b in zip(MAIN_CHAIN, MAIN_CHAIN[1:]):
        chain_segment(d, B(by_seq[a]), B(by_seq[b]), chain_fill, 3)
    chain_segment(d, B(by_seq[BRANCH[0]]), B(by_seq[BRANCH[1]]),
                  "#059669", 3, trim=30)

    # leader lines + label boxes
    for g, seq, colour, action, note in ORDER:
        ax, ay = P(g)
        bx, by = boxes[g]
        by += TOP
        sx = bx + LABEL_W if ax > bx + LABEL_W/2 else bx
        sy = by + LABEL_H/2
        elbow = (sx + (24 if sx == bx + LABEL_W else -24), sy)
        pts = [(sx, sy), elbow, (ax, ay)]
        d.line(pts, fill="#FFFFFF", width=6)          # halo over dark parts
        d.line(pts, fill="#93A1B0", width=2)
        d.ellipse([ax-5, ay-5, ax+5, ay+5], fill="#93A1B0")
        d.rounded_rectangle([bx, by, bx+LABEL_W, by+LABEL_H], radius=9,
                            fill="#FFFFFF", outline="#D3DBE4", width=2)
        d.rounded_rectangle([bx, by, bx+6, by+LABEL_H], radius=3, fill=colour)
        d.ellipse([bx+15, by+16, bx+51, by+52], fill=colour)
        txt_center(d, (bx+33, by+34), str(seq), f_num, "white")
        d.text((bx+62, by+8), g, font=f_name, fill="#1F2933")
        d.text((bx+62, by+43),
               f"{PARTS[g]} 件 · {action[:11]}", font=f_meta, fill="#5B6775")

    # numbered badges (nudged apart where anchors collide).  A short tether in
    # the group's own colour links a displaced badge back to its real anchor,
    # so the reader can still tell which part the number refers to.
    for g, seq, colour, *_ in ORDER:
        ax, ay = P(g)                 # true part anchor
        cx, cy = B(g)                 # badge centre (may be displaced)
        shift = math.hypot(cx-ax, cy-ay)
        if shift > 2:
            d.line([(ax, ay), (cx, cy)], fill="#FFFFFF", width=7)   # halo
            d.line([(ax, ay), (cx, cy)], fill=colour, width=2)
            d.ellipse([ax-4, ay-4, ax+4, ay+4], fill=colour)
        d.ellipse([cx-21, cy-21, cx+21, cy+21], fill="white",
                  outline=colour, width=4)
        d.ellipse([cx-17, cy-17, cx+17, cy+17], fill=colour)
        txt_center(d, (cx, cy), str(seq), f_small, "white")

    # title band
    d.text((36, 24), "X-print 十字滑台总成 · 装配爆炸图 V2",
           font=f_title, fill="#16222E")
    d.text((38, 86),
           "SolidCraft 功能组爆炸视图 view 425 ｜ 10 组 127 件分离 + 12 件固定机架基准 ｜ 单位 mm ｜ 白底",
           font=f_sub, fill="#5B6775")
    d.line([(36, 128), (W-36, 128)], fill="#D3DBE4", width=2)

    # legend band
    ly = H + TOP + 20
    d.line([(36, ly-10), (W-36, ly-10)], fill="#D3DBE4", width=2)
    lx = 40
    d.line([(lx, ly+16), (lx+54, ly+16)], fill="#93A1B0", width=2)
    d.ellipse([lx+50, ly+12, lx+58, ly+20], fill="#93A1B0")
    d.text((lx+70, ly+2), "细实线 + 圆点：部件中文名称引线", font=f_leg,
           fill="#33414F")
    lx += 380
    dashed(d, (lx, ly+16), (lx+54, ly+16), chain_fill, 3, 12, 8)
    arrow_head(d, (lx+38, ly+16), (lx+54, ly+16), chain_fill, 11)
    d.text((lx+70, ly+2), "粗虚线箭头：装配顺序主链 1→10", font=f_leg,
           fill="#33414F")
    lx += 400
    dashed(d, (lx, ly+16), (lx+54, ly+16), "#059669", 3, 12, 8)
    d.text((lx+70, ly+2), "绿色虚线：并行支路 1→11（保湿站）",
           font=f_leg, fill="#33414F")

    d.text((40, ly+44),
           "装配逻辑：1 Z 机架 → 2 端板导杆 → 3 同步带传动 → 4 步进电机 → 5 限位开关 → "
           "6 Z 滑车与 XZ 板 → 7 X 横梁 → 8 X 滑车 → 9 HP45 喷头 → 10 接触式探针；11 保湿站并行安装。",
           font=f_sub, fill="#33414F")
    d.text((40, ly+80),
           "V2 较 V1 把原先挤在基准里的 40 件再拆成 5 个 Z 轴子组，分离件数 100 → 127，并加大各向位移；"
           "爆炸位移只改显示，不改 placement / B-rep。",
           font=f_meta, fill="#5B6775")
    d.text((40, ly+108),
           "口径：主模型仍为 LM5UU Ø10×15 + Ø5 导杆；3 个开放端板仅作视觉参照；"
           "标注锚点由等轴测投影定标，非手工点选；序号牌过近时微调错位并用同色细线回指部件。",
           font=f_meta, fill="#7A8794")
    d.text((40, ly+136),
           "本版修正：Z 步进电机不再 −X/−Y/+Z 斜向飞出，改为从安装位沿 4 颗安装螺钉轴线（Y 轴）"
           "纯 +Y 平移 80 mm 抽出，电机轴随之从端板孔退出；其余 9 组位移不变。",
           font=f_meta, fill="#7A8794")
    d.text((40, ly+164),
           "圆点核实：用分功能组纯色渲染逐点回验，序号 2/3/5/10 的原投影质心分别落在邻组、空档或背景上，"
           "现已吸附到本组零件像素（序号 5 指向下方 KW11-3Z-A-1 本体）；其余 7 组原锚点即正确。",
           font=f_meta, fill="#7A8794")

    canvas.save(ANNOT, optimize=True)

    with AUDIT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["序号", "功能组", "件数", "锚点 x", "锚点 y", "锚点来源",
                    "标签 x", "标签 y", "序号牌 x", "序号牌 y", "序号牌偏移 px",
                    "装配链", "装配动作", "口径说明",
                    "3D 质心 X", "3D 质心 Y", "3D 质心 Z"])
        for g, seq, colour, action, note in ORDER:
            x, y = anchors[g]
            cx, cy = badges[g]
            shift = round(math.hypot(cx - x, cy - (y + TOP)), 1)
            chain = "1→2→…→10" if seq <= 10 else "1→11 并行支路"
            w.writerow([seq, g, PARTS[g], x, y, anchor_source[g],
                        boxes[g][0], boxes[g][1], cx, cy, shift,
                        chain, action, note, *xyz[g]])

    displaced = {g: {"badge": badges[g], "anchor_canvas": anchors_c[g],
                     "shift_px": round(math.hypot(
                         badges[g][0]-anchors_c[g][0],
                         badges[g][1]-anchors_c[g][1]), 1)}
                 for g in anchors if math.hypot(
                     badges[g][0]-anchors_c[g][0],
                     badges[g][1]-anchors_c[g][1]) > 2}
    print(json.dumps({
        "source": str(SRC), "white": str(WHITE), "annotated": str(ANNOT),
        "canvas": list(canvas.size), "model_bbox": list(bbox),
        "projection_scale_px_per_mm": scale,
        "anchors": anchors, "labels": boxes, "badges": badges,
        "displaced_badges": displaced,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
