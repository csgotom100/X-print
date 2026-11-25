# -*- coding: utf-8 -*-
"""LM6UU 改造：从当前 FCStd 直接提取 8 件改动件的接口几何清单。

不调用 App.openDocument（本机 freecadcmd 会卡死），只从 FCStd ZIP 提取裸 BREP，
用 Part.Shape().read() 逐件加载。输出 refs/tmp/lm6_interfaces.json + fsync 日志。
"""
import os, sys, io, json, zipfile, math, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Part

ROOT = 'C:/ink'
FCSTD = ROOT + '/CrossSlide_P014013.FCStd'
BRP = ROOT + '/refs/tmp/brp_lm6'
JSONP = ROOT + '/refs/tmp/lm6_interfaces.json'
LOGP = ROOT + '/refs/tmp/extract_lm6_interfaces.log'

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
REFS = [
    'X_Profile', 'Z_Profile',
    'X_GuideRod_1', 'X_GuideRod_2', 'Z_GuideRod_1', 'Z_GuideRod_2',
    'X_LM5UU_1', 'X_LM5UU_2', 'Z_LM5UU_1', 'Z_LM5UU_2',
    'X_rod_1_tap', 'X_rod_2_tap', 'Z_rod_1_tap', 'Z_rod_2_tap',
    'X_rod_fix_screw_1', 'X_rod_fix_screw_2',
    'Z_rod_fix_screw_1', 'Z_rod_fix_screw_2',
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

def cyl_key(r, ax, center):
    """把同一孔的多张圆柱面片聚成一类：半径 + 轴向 + 轴线上一点的投影。"""
    a = (abs(ax.x), abs(ax.y), abs(ax.z))
    d = 'X' if a[0] > 0.9 else ('Y' if a[1] > 0.9 else ('Z' if a[2] > 0.9 else '?'))
    if d == 'X':
        q = (round(center.y, 2), round(center.z, 2))
    elif d == 'Y':
        q = (round(center.x, 2), round(center.z, 2))
    elif d == 'Z':
        q = (round(center.x, 2), round(center.y, 2))
    else:
        q = (round(center.x, 2), round(center.y, 2), round(center.z, 2))
    return (round(r, 3), d, q)

def analyse(name):
    s = load(name)
    bb = s.BoundBox
    out = {
        'bbox': [r3(bb.XMin), r3(bb.YMin), r3(bb.ZMin),
                 r3(bb.XMax), r3(bb.YMax), r3(bb.ZMax)],
        'volume': r3(s.Volume),
        'solids': len(s.Solids),
        'faces': len(s.Faces),
        'closed': bool(s.isClosed()) if hasattr(s, 'isClosed') else None,
        'face_types': {},
        'cylinders': [],
        'planes': [],
    }
    groups = {}
    for fi, f in enumerate(s.Faces):
        try:
            su = f.Surface
            tn = type(su).__name__
        except Exception:
            tn = '?'
        out['face_types'][tn] = out['face_types'].get(tn, 0) + 1
        fb = f.BoundBox
        if tn == 'Cylinder':
            r = su.Radius
            ax = su.Axis
            c = su.Center
            try:
                u0, u1, v0, v1 = f.ParameterRange
                sweep = math.degrees(u1 - u0)
            except Exception:
                sweep = 0.0
            k = cyl_key(r, ax, c)
            g = groups.setdefault(k, {
                'radius': round(r, 3), 'axis': k[1], 'axis_pos': list(k[2]),
                'faces': 0, 'sweep_sum': 0.0,
                'x': [1e9, -1e9], 'y': [1e9, -1e9], 'z': [1e9, -1e9],
            })
            g['faces'] += 1
            g['sweep_sum'] += sweep
            for key, lo, hi in (('x', fb.XMin, fb.XMax),
                                ('y', fb.YMin, fb.YMax),
                                ('z', fb.ZMin, fb.ZMax)):
                g[key][0] = min(g[key][0], lo)
                g[key][1] = max(g[key][1], hi)
        elif tn == 'Plane' and f.Area > 40.0:
            try:
                nv = su.Axis
            except Exception:
                continue
            out['planes'].append({
                'area': r3(f.Area),
                'normal': [r3(nv.x), r3(nv.y), r3(nv.z)],
                'at': [r3(fb.XMin), r3(fb.YMin), r3(fb.ZMin)],
                'bbox': [r3(fb.XMin), r3(fb.YMin), r3(fb.ZMin),
                         r3(fb.XMax), r3(fb.YMax), r3(fb.ZMax)],
            })
    for k, g in groups.items():
        g['sweep_sum'] = round(g['sweep_sum'], 1)
        for key in ('x', 'y', 'z'):
            g[key] = [r3(g[key][0]), r3(g[key][1])]
        out['cylinders'].append(g)
    out['cylinders'].sort(key=lambda g: (-g['radius'], g['axis'], g['axis_pos']))
    out['planes'].sort(key=lambda p: -p['area'])
    out['planes'] = out['planes'][:24]
    return out

def main():
    extract()
    shapes = {}
    for n in TARGETS:
        shapes[n] = analyse(n)
        P('TARGET', n, 'bbox', shapes[n]['bbox'], 'V=', shapes[n]['volume'],
          'faces=', shapes[n]['faces'], 'cyl_groups=', len(shapes[n]['cylinders']))
    refs = {}
    for n in REFS:
        try:
            s = load(n)
        except Exception as e:
            P('REF MISS', n, e)
            continue
        b = s.BoundBox
        refs[n] = {'bbox': [r3(b.XMin), r3(b.YMin), r3(b.ZMin),
                            r3(b.XMax), r3(b.YMax), r3(b.ZMax)],
                   'volume': r3(s.Volume)}
    with open(JSONP, 'w', encoding='utf-8') as f:
        json.dump({'source': FCSTD, 'targets': shapes, 'refs': refs},
                  f, ensure_ascii=False, indent=1)
        f.flush(); os.fsync(f.fileno())
    P('WROTE', JSONP, os.path.getsize(JSONP), 'bytes')
    P('LM6 INTERFACES DONE')

main()
_f.close()
