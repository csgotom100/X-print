# -*- coding: utf-8 -*-
"""全原生重建：把 8 件 BREP 自动分解成「加料盒 + 切除圆柱」的参数化特征配方。

所有面都是 Plane / Cylinder。为避免 isInside 点阵全扫超时（项目已知坑），
改用「薄片切片 + 2D 面内判定」：
1) 沿 X 按所有轴对齐平面坐标切成薄片，每片只做 1 次 common 布尔；
2) 取薄片上法向沿 X 的平面 Face，用 Face.isInside 判定 Y/Z 网格单元是否实心；
3) 2D 贪心合并成矩形（Y 条 -> Z 片），再沿相邻 X 层合并成最少 3D 盒；
4) 所有整圆柱孔另外用 solid.cylinder cut 精确切回，使孔径成为可编辑参数；
5) 输出 refs/tmp/native_features.json，供 build_lm6_native.py 翻译为 SolidCraft 命令。

不调用 App.openDocument；用 fsync 日志。
"""
import os, sys, io, json, math, collections, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Part

ROOT = 'C:/ink'
BRP = ROOT + '/refs/tmp/brp_native'
RECIPE = ROOT + '/refs/tmp/lm6_native_recipe.json'
OUT = ROOT + '/refs/tmp/native_features.json'
LOG = ROOT + '/refs/tmp/build_native_recipe.log'
_f = open(LOG, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    try: print(s)
    except Exception: pass
    _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

TARGETS = [
    'X_EndPlate_L', 'X_EndPlate_R', 'Z_EndPlate_L', 'Z_EndPlate_R',
    'X_Carriage_Lower', 'X_Carriage_Upper',
    'Z_Carriage_Lower', 'Z_Carriage_Upper',
]
TOL = 1e-5

def load(n):
    s = Part.Shape(); s.read(os.path.join(BRP, n + '.Shape.brp')); return s

def r3(x): return round(float(x), 3)

def grid_coords(rp):
    bb = rp['bbox']
    out = []
    for ax, lo, hi in (('X', bb[0], bb[3]), ('Y', bb[1], bb[4]), ('Z', bb[2], bb[5])):
        cs = set(rp['plane_coords'][ax]); cs.add(lo); cs.add(hi)
        cs = sorted(v for v in cs if lo - 1e-6 <= v <= hi + 1e-6)
        ded = [cs[0]]
        for v in cs[1:]:
            if v - ded[-1] > 0.02: ded.append(v)
        if ded[-1] < hi - 1e-6: ded.append(hi)
        out.append([r3(v) for v in ded])
    return out

def rects_from_mask(mask, ny, nz):
    """2D 二值网格 -> 最少矩形 (j0,j1,k0,k1)。"""
    bars = []
    for k in range(nz):
        j = 0
        while j < ny:
            if not mask[k][j]: j += 1; continue
            j0 = j
            while j + 1 < ny and mask[k][j + 1]: j += 1
            bars.append((j0, j, k)); j += 1
    rects = []
    by = collections.defaultdict(list)
    for j0, j1, k in bars: by[(j0, j1)].append(k)
    for (j0, j1), ks in by.items():
        ks.sort(); s = 0
        while s < len(ks):
            k0 = ks[s]; k1 = k0
            while s + 1 < len(ks) and ks[s + 1] == k1 + 1:
                s += 1; k1 = ks[s]
            rects.append((j0, j1, k0, k1)); s += 1
    return rects

def decompose(shape, grids):
    """返回 3D 盒列表 {corner, size}。"""
    xs, ys, zs = grids
    ny, nz = len(ys) - 1, len(zs) - 1
    y0, z0 = ys[0], zs[0]
    dy, dz = ys[-1] - y0, zs[-1] - z0
    layer_rects = []
    t0 = time.time()
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        slab = Part.makeBox(x1 - x0, dy, dz, App.Vector(x0, y0, z0))
        inter = shape.common(slab)
        mask = [[False] * ny for _ in range(nz)]
        if not inter.isNull() and inter.Volume > 1e-9:
            # 取法向沿 X 的平面面片（薄片的两个端面，可能有多块）
            faces = []
            for f in inter.Faces:
                try:
                    if type(f.Surface).__name__ == 'Plane' and \
                       abs(f.Surface.Axis.x) > 0.9:
                        faces.append(f)
                except Exception:
                    pass
            for k in range(nz):
                cz = (zs[k] + zs[k + 1]) / 2.0
                for j in range(ny):
                    cy = (ys[j] + ys[j + 1]) / 2.0
                    for f in faces:
                        fx = f.BoundBox.XMin
                        try:
                            if f.isInside(App.Vector(fx, cy, cz), TOL, True):
                                mask[k][j] = True; break
                        except Exception:
                            pass
        layer_rects.append(rects_from_mask(mask, ny, nz))
    P('    slice', len(xs) - 1, 'layers in', round(time.time() - t0, 1), 's')
    # 沿 X 合并：同一 (j0,j1,k0,k1) 在连续层出现则合并 X 范围
    spans = collections.defaultdict(list)
    for i, rects in enumerate(layer_rects):
        for rc in rects: spans[rc].append(i)
    boxes = []
    for rc, idxs in spans.items():
        j0, j1, k0, k1 = rc
        idxs.sort(); s = 0
        while s < len(idxs):
            i0 = idxs[s]; i1 = i0
            while s + 1 < len(idxs) and idxs[s + 1] == i1 + 1:
                s += 1; i1 = idxs[s]
            boxes.append({
                'corner': [xs[i0], ys[j0], zs[k0]],
                'size': [r3(xs[i1 + 1] - xs[i0]),
                         r3(ys[j1 + 1] - ys[j0]),
                         r3(zs[k1 + 1] - zs[k0])],
            }); s += 1
    boxes.sort(key=lambda b: (b['corner'][2], b['corner'][1], b['corner'][0]))
    return boxes

def union_volume(boxes):
    v = 0.0
    for b in boxes:
        c, s = b['corner'], b['size']
        v += s[0] * s[1] * s[2]
    return v

def main():
    recipe = json.load(open(RECIPE, encoding='utf-8'))['targets']
    out = {}
    for n in TARGETS:
        s = load(n)
        rp = recipe[n]
        grids = grid_coords(rp)
        P('PART', n, 'grid', [len(g) - 1 for g in grids])
        boxes = decompose(s, grids)
        bv = union_volume(boxes)
        P('    boxes =', len(boxes), 'box_V=', r3(bv),
          'orig_V=', rp['volume'], 'delta=', r3(bv - rp['volume']))
        out[n] = {
            'bbox': rp['bbox'], 'orig_volume': rp['volume'],
            'grid': grids, 'boxes': boxes, 'box_volume': r3(bv),
            'cylinders': rp['cylinders'],
        }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.flush(); os.fsync(f.fileno())
    P('WROTE', OUT, os.path.getsize(OUT), 'bytes')
    P('NATIVE RECIPE BUILD DONE')

main()
_f.close()
