# -*- coding: utf-8 -*-
"""把 SolidCraft CLI snapshot 的渐变底转成纯白，并把整机图按内容裁紧。

SolidCraft 没有 viewport 纯色背景命令；`--no-grid --no-axes` 后仍是
逐行线性渐变（顶部 [240,243,247] -> 底部 [203,210,221]）。本脚本按行取
左右边缘的中位数作为该行背景色，再按「与背景的最大通道差」做软白化：
  d<=3 全白；3<d<10 线性过渡；d>=10 保持原像素（实体/描边不被洗掉）。

只处理整机等轴测图。轴承座近景图**不做白化**：近景相机里存在一条
地平线（地面受光，颜色随 x 变化，逐行背景模型不成立），且 Ø6 导杆的
#e1e4e8 与背景色接近，软白化会在导杆上留下白色条纹。近景图直接保留
CLI snapshot 的原始渐变底即可，别再后处理。

输入（由 solidcraft-cli snapshot 生成）：
  refs/tmp/lm6_iso_hi.png          3200x2000 混合方案等轴测（历史中间方案）
  refs/tmp/lm6_native_iso_hi.png   3200x2000 全原生方案等轴测
输出：
  solidcraft/LM6UU_Redesign_iso.png  混合方案整机白底紧裁（历史）
  solidcraft/LM6UU_Native_iso.png    全原生方案整机白底紧裁（当前权威）
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'solidcraft'


def whiten(src: Path, dst: Path, crop: bool = False, margin: int = 110):
    im = Image.open(src).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    h, w, _ = a.shape
    edge = np.concatenate([a[:, 0:60, :], a[:, -60:, :]], axis=1)
    bg = np.median(edge, axis=1)                      # (h, 3) 逐行背景
    d = np.max(np.abs(a - bg[:, None, :]), axis=2)    # (h, w)
    wt = np.clip((10.0 - d) / 7.0, 0.0, 1.0)         # 3 -> 1, 10 -> 0
    white = (255.0 - bg)[:, None, :]
    out = np.clip(a + white * wt[..., None], 0, 255).astype(np.uint8)
    if crop:
        ys, xs = np.where(d > 18)
        x0, x1 = max(0, int(xs.min()) - margin), min(w, int(xs.max()) + margin)
        y0, y1 = max(0, int(ys.min()) - margin), min(h, int(ys.max()) + margin)
        out = out[y0:y1, x0:x1]
    Image.fromarray(out).save(dst)
    return dst, out.shape


def report(tag, p, shape):
    a = np.asarray(Image.open(p).convert('RGB'))
    print(tag, p.name, shape, 'bytes', p.stat().st_size,
          'exact-white %.2f%%' % (100.0 * np.all(a == 255, axis=2).mean()))


if __name__ == '__main__':
    jobs = [
        ('hybrid-iso', 'refs/tmp/lm6_iso_hi.png', 'LM6UU_Redesign_iso.png'),
        ('native-iso', 'refs/tmp/lm6_native_iso_hi.png', 'LM6UU_Native_iso.png'),
    ]
    for tag, src, dst in jobs:
        s = ROOT / src
        if not s.exists():
            print(tag, 'SKIP (missing', src + ')')
            continue
        p, shape = whiten(s, OUT / dst, crop=True)
        report(tag, p, shape)
