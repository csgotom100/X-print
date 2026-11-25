# -*- coding: utf-8 -*-
"""全原生重建：从 FCStd 裸 BREP 提取 8 件结构件的「参数化配方」。

与 extract_lm6_interfaces.py 不同，这里保留全部平面/圆柱分组（不截断），
并按法向 + 坐标聚类出台阶坐标，按圆柱轴向范围给出孔/座的长度，
供 SolidCraft 原生 sketch/box/cylinder/hole 重建时取尺寸。

不调用 App.openDocument（本机 freecadcmd 会卡死），只读 FCStd ZIP 内裸 BREP。
"""
import os, sys, io, json, zipfile, math, shutil, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Part

ROOT = 'C:/ink'
FCSTD = ROOT + '/CrossSlide_P014013.FCStd'
BRP = ROOT + '/refs/tmp/brp_native'
JSONP = ROOT + '/refs/tmp/lm6_native_recipe.json'
LOGP = ROOT + '/refs/tmp/extract_native_recipe.log'

_f = open(LOGP, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    try:
        print(s)
    except Exception:
        pass
    _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

TARGETS = [
    'X_EndPlate_L', 'X_EndPlate_R', 'Z_EndPlate_L', 'Z_EndPlate_R',
    'X_Carriage_Lower', 'X_Carriage_Upper',
    'Z_Carriage_Lower', 'Z_Carriage_Upper',
]

def extract():
    if os.path.isdir(BRP):
        shutil.rmtree(BRP, ignore_errors=True)
    os.makedirs(BRP, exist_ok=True)
    with zipfile.ZipFile(FCSTD) as z:
        n = 0
        for name in z.namelist():
            if name.endswith('.brp'):
                with open(os.path.join(BRP, os.path.basename(name)), 'wb') as f:
                    f.write(z.read(name))
                n += 1
    P('EXTRACT', n, 'BREP ->', BRP)

def load(name):
    s = Part.Shape()
    s.read(os.path.join(BRP, name + '.Shape.brp'))
    return s

def r3(x):
    return round(float(x), 3)

def axis_dir(ax):
    a = (abs(ax.x), abs(ax.y), abs(ax.z))
    if a[0] > 0.9: return 'X'
    if a[1] > 0.9: return 'Y'
    if a[2] > 0.9: return 'Z'
    return '?'

def analyse(name):
    s = load(name)
    bb = s.BoundBox
    out = {
        'bbox': [r3(bb.XMin), r3(bb.YMin), r3(bb.ZMin),
                 r3(bb.XMax), r3(bb.YMax), r3(bb.ZMax)],
        'volume': r3(s.Volume),
        'solids': len(s.Solids),
        'faces': len(s.Faces),
        'face_types': {},
        'cylinders': [],
        'cones': [],
        'planes_by_normal': {},
        'plane_coords': {'X': [], 'Y': [], 'Z': []},
    }
    cyl = {}
    planes = collections.defaultdict(list)
    for fi, f in enumerate(s.Faces):
        try:
            su = f.Surface
            tn = type(su).__name__
        except Exception:
            tn = '?'
        out['face_types'][tn] = out['face_types'].get(tn, 0) + 1
        fb = f.BoundBox
        fb6 = [r3(fb.XMin), r3(fb.YMin), r3(fb.ZMin),
               r3(fb.XMax), r3(fb.YMax), r3(fb.ZMax)]
        if tn == 'Cylinder':
            radius = su.Radius
            ad = axis_dir(su.Axis)
            c = su.Center
            if ad == 'X':   q = (r3(c.y), r3(c.z)), 'x'
            elif ad == 'Y': q = (r3(c.x), r3(c.z)), 'y'
            elif ad == 'Z': q = (r3(c.x), r3(c.y)), 'z'
            else:           q = (r3(c.x), r3(c.y), r3(c.z)), '?'
            pos, along = q
            try:
                u0, u1, v0, v1 = f.ParameterRange
                sweep = math.degrees(u1 - u0)
            except Exception:
                sweep = 0.0
            key = (r3(radius), ad, pos)
            g = cyl.setdefault(key, {
                'radius': r3(radius), 'axis': ad, 'axis_pos': list(pos),
                'along': along, 'faces': 0, 'sweep_sum': 0.0,
                'area_sum': 0.0,
                'bbox': [1e9, 1e9, 1e9, -1e9, -1e9, -1e9],
            })
            g['faces'] += 1
            g['sweep_sum'] += sweep
            g['area_sum'] += f.Area
            for i in range(3):
                g['bbox'][i] = min(g['bbox'][i], fb6[i])
                g['bbox'][i + 3] = max(g['bbox'][i + 3], fb6[i + 3])
        elif tn == 'Cone':
            out['cones'].append({
                'radius': r3(getattr(su, 'Radius', 0.0)),
                'semi_angle': r3(math.degrees(getattr(su, 'SemiAngle', 0.0))),
                'bbox': fb6, 'area': r3(f.Area),
            })
        elif tn == 'Plane':
            try:
                nv = su.Axis
            except Exception:
                continue
            # 主轴法向
            nn = [abs(nv.x), abs(nv.y), abs(nv.z)]
            if max(nn) < 0.9:
                continue                      # 斜面（倒角）单独不参与台阶聚类
            ad = 'XYZ'[nn.index(max(nn))]
            coord = {'X': (fb.XMin + fb.XMax) / 2.0,
                     'Y': (fb.YMin + fb.YMax) / 2.0,
                     'Z': (fb.ZMin + fb.ZMax) / 2.0}[ad]
            rec = {'at': r3(coord), 'area': r3(f.Area), 'bbox': fb6,
                   'normal': [r3(nv.x), r3(nv.y), r3(nv.z)]}
            planes[ad].append(rec)
            out['plane_coords'][ad].append(r3(coord))

    for key, g in cyl.items():
        g['sweep_sum'] = r3(g['sweep_sum'])
        g['area_sum'] = r3(g['area_sum'])
        g['bbox'] = [r3(v) for v in g['bbox']]
        # 沿轴向的实际长度
        i = 'xyz'.index(g['along']) if g['along'] in 'xyz' else 0
        g['length'] = r3(g['bbox'][i + 3] - g['bbox'][i])
        # 整圆孔判定：sweep 累计接近 360 的倍数
        g['full_turns'] = round(g['sweep_sum'] / 360.0, 2)
        out['cylinders'].append(g)
    out['cylinders'].sort(key=lambda g: (-g['radius'], g['axis'], g['axis_pos']))

    for ad in 'XYZ':
        # 同一坐标的平面聚合，给出每个台阶的总面积和覆盖 bbox
        agg = {}
        for rec in planes[ad]:
            k = rec['at']
            a = agg.setdefault(k, {'at': k, 'area': 0.0, 'faces': 0,
                                   'bbox': [1e9, 1e9, 1e9, -1e9, -1e9, -1e9]})
            a['area'] += rec['area']; a['faces'] += 1
            for i in range(3):
                a['bbox'][i] = min(a['bbox'][i], rec['bbox'][i])
                a['bbox'][i + 3] = max(a['bbox'][i + 3], rec['bbox'][i + 3])
        lst = []
        for k in sorted(agg):
            a = agg[k]
            a['area'] = r3(a['area'])
            a['bbox'] = [r3(v) for v in a['bbox']]
            lst.append(a)
        out['planes_by_normal'][ad] = lst
        out['plane_coords'][ad] = sorted(set(out['plane_coords'][ad]))
    return out

def main():
    extract()
    shapes = {}
    for n in TARGETS:
        shapes[n] = analyse(n)
        v = shapes[n]
        P('TARGET', n, 'bbox', v['bbox'], 'V=', v['volume'],
          'faces=', v['faces'], 'types=', v['face_types'],
          'cyl=', len(v['cylinders']), 'cones=', len(v['cones']))
        for ad in 'XYZ':
            P('   plane', ad, 'coords', v['plane_coords'][ad])
    with open(JSONP, 'w', encoding='utf-8') as f:
        json.dump({'source': FCSTD, 'targets': shapes}, f,
                  ensure_ascii=False, indent=1)
        f.flush(); os.fsync(f.fileno())
    P('WROTE', JSONP, os.path.getsize(JSONP), 'bytes')
    P('NATIVE RECIPE DONE')

main()
_f.close()
