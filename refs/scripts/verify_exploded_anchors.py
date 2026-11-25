# -*- coding: utf-8 -*-
"""
Verify that every leader dot in the V2 exploded view really sits on a pixel of
the part group it labels.

The isometric projection of a group's 3D centroid is only an estimate: it can
land in the empty gap between two separated parts, on a nearer part belonging
to another group, or on pure background.  To check this independently of the
annotation code, we render the *same* exploded geometry with a unique flat
colour per functional group and read back the colour under each dot.

How the verification render is produced (all reproducible):
  1. refs/scripts/build_exploded_view_v2.py  -> 05_exploded_view_v2.json
  2. solidcraft-cli run 05_exploded_view_v2.json --in <motion>.sc --save <v2>.sc
  3. refs/tmp/dotcheck_colorize.json assigns one flat colour per group
     (DOTCHK_01..11) via material.create / material.assign
  4. the 127 explode moves are baked into occurrence transforms (the transform
     is column-major: translation lives in row 3), so an offscreen CLI render
     shows the exploded state without needing explode.show
  5. solidcraft-cli snapshot --camera <the exact render camera> --no-grid
     --no-axes -> refs/tmp/exploded_v2_group_colours.png (4096x3150)

The result is cropped with OX/OY into the 2209x1323 source-image coordinate
system used by EXPLODED_ANNOTATIONS_V2.csv.  Classification uses chromaticity
(r,g,b)/sum, because shading multiplies a colour by a scalar and therefore
preserves chromaticity exactly.

Run:
  python refs/scripts/verify_exploded_anchors.py
Exit code is 0 only when all 11 dots resolve to their own group.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CHECK_IMG = ROOT / "refs/tmp/exploded_v2_group_colours.png"
AUDIT = ROOT / "solidcraft/EXPLODED_ANNOTATIONS_V2.csv"

OX, OY = 753, 1009          # crop offset: source (x,y) -> 4K (x+OX, y+OY)
W, H = 2209, 1323           # source image size
R = 11                      # sample half-window around each dot

ORDER = [
    "Z 轴机架（固定基准）", "Z 端板与导杆", "Z 同步带传动", "Z 步进电机",
    "Z 限位开关", "Z 滑车 + XZ 连接板", "X 横梁总成", "X 滑车",
    "HP45 喷头总成", "接触式探针总成", "保湿站",
]
# DOTCHK_01..11 flat colours (pure hues, 30 deg apart)
COL = np.array([
    (255, 0, 0), (255, 128, 0), (255, 255, 0), (128, 255, 0), (0, 255, 0),
    (0, 255, 128), (0, 255, 255), (0, 128, 255), (0, 0, 255),
    (128, 0, 255), (255, 0, 255),
], dtype=np.float32)
REF = COL / COL.sum(1, keepdims=True)


def classify(img, x, y):
    """Majority group colour in a (2R+1)^2 window; returns (group, purity, coverage)."""
    sub = img[max(0, y - R):min(H, y + R + 1),
              max(0, x - R):min(W, x + R + 1)].reshape(-1, 3)
    chroma = sub.max(1) - sub.min(1)
    keep = (chroma > 45) & (sub.sum(1) > 90)
    coverage = float(keep.mean())
    if keep.sum() == 0:
        return None, 0, coverage
    v = sub[keep]
    n = v / v.sum(1, keepdims=True)
    labels = ((n[:, None, :] - REF[None, :, :]) ** 2).sum(2).argmin(1)
    counts = np.bincount(labels, minlength=len(ORDER))
    best = int(counts.argmax())
    return ORDER[best], int(100 * counts.max() / counts.sum()), coverage


def main():
    if not CHECK_IMG.exists():
        raise SystemExit(f"missing verification render: {CHECK_IMG}")
    a = np.array(Image.open(CHECK_IMG).convert("RGB")).astype(np.float32)
    if a.shape[0] < OY + H or a.shape[1] < OX + W:
        raise SystemExit(f"render too small: {a.shape}")
    img = a[OY:OY + H, OX:OX + W]

    rows = list(csv.DictReader(AUDIT.open(encoding="utf-8-sig")))
    print("seq | group                         | dot (x,y)     | source         | detected                      | pure | verdict")
    print("-" * 122)
    bad = []
    for r in rows:
        x, y = int(r["锚点 x"]), int(r["锚点 y"])
        group, purity, coverage = classify(img, x, y)
        ok = group == r["功能组"] and coverage >= 0.30
        if not ok:
            bad.append((r["序号"], r["功能组"], group, coverage))
        print(f" {r['序号']:>2s} | {r['功能组']:<28s} | ({x:4d},{y:4d})  | "
              f"{r['锚点来源']:<14s} | {str(group):<28s} | {purity:3d}% | "
              f"{'OK' if ok else 'MISMATCH'}")
    print()
    if bad:
        print("FAILED dots:", bad)
        return 1
    print(f"PASS: all {len(rows)} leader dots sit on their own functional group "
          f"({sum(1 for r in rows if r['锚点来源'] == '分色像素核实')} pixel-verified overrides, "
          f"{sum(1 for r in rows if r['锚点来源'] == '等轴测投影')} automatic projections)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
