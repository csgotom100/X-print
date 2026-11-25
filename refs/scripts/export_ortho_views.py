# -*- coding: utf-8 -*-
"""
export_ortho_views.py — 从主模型 FCStd 导出单个零件的三向真实消隐正投影。

用途：为 AutoCAD 三视图（DXF）提供几何源，见 build_autocad_3view.py。

做法：
  1. 从 FCStd ZIP 直接取 <name>.Shape.brp，用 Part.Shape().read() 加载
     （本机 FreeCAD 1.1 的 App.openDocument() 会卡死，见项目约定）。
  2. TechDraw.project(shape, direction) 做 OCC HLR，返回
     [visibleG0, visibleG1, hiddenG0, hiddenG1]。
  3. 把投影结果从「视图局部 uv」统一变换到工程视图坐标：
        FRONT (沿 -Y): u=-Z, v= X  ->  (x,y)=( v, -u)=(X, Z)
        TOP   (沿 -Z): u=-X, v= Y  ->  (x,y)=(-u,  v)=(X, Y)
        LEFT  (沿 -X): u=-Z, v=-Y  ->  (x,y)=(-v, -u)=(Y, Z)
     这样 FRONT/TOP 长对正（同为 X），FRONT/LEFT 高平齐（同为 Z），
     TOP/LEFT 宽相等（同为 Y）。
  4. 直线 -> line；整圆 -> circle；其余曲线按弦高 0.02 mm 离散 -> polyline。

输出：refs/tmp/ortho_<name>.json + 日志
"""
import os, sys, io, json, zipfile, math, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Part
import TechDraw

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
NAME = 'X_EndPlate_L'
TD = 'C:/ink/refs/tmp/ortho_brp/'
OUT = 'C:/ink/refs/tmp/ortho_%s.json' % NAME
LOGP = 'C:/ink/refs/tmp/export_ortho_views.log'

_f = open(LOGP, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    try:
        print(s)
    except Exception:
        pass
    _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

# ---------------------------------------------------------------- 取 BREP
if os.path.isdir(TD):
    shutil.rmtree(TD, ignore_errors=True)
os.makedirs(TD, exist_ok=True)
with zipfile.ZipFile(DOC) as z:
    assert z.testzip() is None, 'FCStd ZIP 损坏'
    key = NAME + '.Shape.brp'
    hit = [n for n in z.namelist() if n == key or n.endswith('/' + key)]
    assert hit, 'FCStd 内找不到 ' + key
    open(TD + key, 'wb').write(z.read(hit[0]))
    P('BREP', hit[0], len(z.read(hit[0])), 'bytes')

s = Part.Shape()
s.read(TD + key)
b = s.BoundBox
P('SHAPE %s  V=%.3f  faces=%d edges=%d solids=%d'
  % (NAME, s.Volume, len(s.Faces), len(s.Edges), len(s.Solids)))
P('BBOX X%.3f..%.3f  Y%.3f..%.3f  Z%.3f..%.3f'
  % (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax))

# ---------------------------------------------------------------- 视图定义
VIEWS = [
    dict(name='FRONT', label='主视图 FRONT', dir=(0, -1, 0),
         xaxis='X', yaxis='Z', why='沿 -Y 观察，投影到 X-Z'),
    dict(name='TOP', label='俯视图 TOP', dir=(0, 0, -1),
         xaxis='X', yaxis='Y', why='沿 -Z 观察，投影到 X-Y'),
    dict(name='LEFT', label='左视图 LEFT', dir=(-1, 0, 0),
         xaxis='Y', yaxis='Z', why='沿 -X 观察，投影到 Y-Z'),
]

def xf(name, u, v):
    """投影 uv -> 工程视图坐标 (x, y)"""
    if name == 'FRONT':      # u=-Z, v= X
        return (v, -u)
    if name == 'TOP':        # u=-X, v= Y
        return (-u, v)
    if name == 'LEFT':       # u=-Z, v=-Y
        return (-v, -u)
    raise ValueError(name)

def edge_entities(e, vname, vis):
    """把一条投影边转换成 1~N 个 DXF 可用的图元描述"""
    out = []
    try:
        cur = e.Curve
        cname = type(cur).__name__
    except Exception:
        cname = '?'

    # 整圆 / 圆弧：用曲线信息判断，变换是刚体+镜像，圆仍是圆
    if cname == 'Circle':
        try:
            r = cur.Radius
            c = cur.Center
            full = (abs(e.Length - 2.0 * math.pi * r) < 1e-4) or e.isClosed()
            if full and r > 1e-6:
                cx, cy = xf(vname, c.x, c.y)
                out.append(dict(t='circle', c=[round(cx, 5), round(cy, 5)],
                                r=round(r, 5), vis=vis))
                return out
        except Exception:
            pass

    # 直线：直接两端点
    if cname == 'Line' and len(e.Vertexes) >= 2:
        p0, p1 = e.Vertexes[0].Point, e.Vertexes[-1].Point
        a = xf(vname, p0.x, p0.y)
        c = xf(vname, p1.x, p1.y)
        if math.hypot(a[0] - c[0], a[1] - c[1]) > 1e-5:
            out.append(dict(t='line',
                            p=[[round(a[0], 5), round(a[1], 5)],
                               [round(c[0], 5), round(c[1], 5)]], vis=vis))
            return out

    # 其余（圆弧、B 样条、椭圆…）按弦高离散
    try:
        pts = e.discretize(Deflection=0.02)
    except Exception:
        try:
            pts = e.discretize(Number=24)
        except Exception:
            return out
    if len(pts) > 400:
        step = int(math.ceil(len(pts) / 400.0))
        pts = pts[::step] + [pts[-1]]
    xy = [list(xf(vname, p.x, p.y)) for p in pts]
    # 去掉连续重合点
    clean = []
    for q in xy:
        if not clean or math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) > 1e-5:
            clean.append([round(q[0], 5), round(q[1], 5)])
    if len(clean) >= 2:
        if len(clean) == 2:
            out.append(dict(t='line', p=clean, vis=vis))
        else:
            out.append(dict(t='polyline', p=clean, vis=vis))
    return out

result = dict(
    source=NAME,
    fcstd=os.path.basename(DOC),
    bbox=dict(x=[b.XMin, b.XMax], y=[b.YMin, b.YMax], z=[b.ZMin, b.ZMax]),
    volume=round(s.Volume, 4),
    views=[],
)

for V in VIEWS:
    d = App.Vector(*V['dir'])
    P('')
    P('==== %s  dir=%s ====' % (V['name'], V['dir']))
    groups = TechDraw.project(s, d)
    ents = []
    nv = nh = 0
    for gi, sh in enumerate(groups):
        vis = 1 if gi < 2 else 0
        try:
            es = sh.Edges
        except Exception:
            es = []
        P('  group[%d] %-7s edges=%d' % (gi, 'VIS' if vis else 'HID', len(es)))
        for e in es:
            got = edge_entities(e, V['name'], vis)
            ents.extend(got)
            if vis:
                nv += len(got)
            else:
                nh += len(got)
    allpts = [q for en in ents for q in ([en['c']] if en['t'] == 'circle' else en['p'])]
    xs = [q[0] for q in allpts]
    ys = [q[1] for q in allpts]
    bb2 = (min(xs), max(xs), min(ys), max(ys)) if xs else (0, 0, 0, 0)
    P('  entities vis=%d hid=%d  bbox X%.2f..%.2f Y%.2f..%.2f'
      % (nv, nh, bb2[0], bb2[1], bb2[2], bb2[3]))
    vv = dict(V)
    vv.pop('dir')
    vv['direction'] = list(V['dir'])
    vv['entities'] = ents
    vv['bbox2'] = [round(q, 4) for q in bb2]
    vv['count_visible'] = nv
    vv['count_hidden'] = nh
    result['views'].append(vv)

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, separators=(',', ':'))
P('')
P('WROTE', OUT, os.path.getsize(OUT), 'bytes')
P('EXPORT ORTHO DONE')
_f.close()
