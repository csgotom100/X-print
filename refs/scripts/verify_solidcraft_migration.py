# -*- coding: utf-8 -*-
"""FreeCAD -> SolidCraft 迁移核验。

以 FreeCAD 侧 BREP 直读结果 (fcstd_topology.json) 为权威，
逐件比对 SolidCraft 导入后 measure 全量输出中的体积与包围盒。
多实体件（Cap_Spring 拆成 5 个 body）按名字聚合后比较。
"""
import os, sys, io, json, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)

FC  = 'C:/ink/refs/tmp/fcstd_topology.json'
SC  = r'C:\Users\jack\.workbuddy-ai\projects\d-ink\380a1bbb-f5bd-458d-ba01-f7c4138b709d\tool-results\mcp-solidcraft-measure-1794464093024-ffc720.txt'
OUT = 'C:/ink/refs/tmp/solidcraft_verify.json'
LOG = 'C:/ink/refs/tmp/solidcraft_verify.log'
_f = open(LOG, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    try: print(s)
    except Exception: pass
    _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

fc = json.load(open(FC, encoding='utf-8'))
sc = json.load(open(SC, encoding='utf-8'))
fcmap = {r['name']: r for r in fc['rows'] if r.get('status') == 'OK'}
bodies = sc['bodies']
P('FreeCAD 对象 =', len(fcmap), ' SolidCraft bodies =', len(bodies))

def base(n):
    return re.sub(r' \(\d+\)$', '', n)

agg = collections.defaultdict(lambda: dict(n=0, volume=0.0, closed=True,
                                           bbox=None, names=[]))
for b in bodies:
    k = base(b['name'])
    a = agg[k]
    a['n'] += 1
    a['names'].append(b['name'])
    v = b.get('volume_mm3')
    if v is None:
        a['closed'] = False
    else:
        a['volume'] += v
    bb = b.get('bbox')
    if bb:
        lo, hi = bb['min'], bb['max']
        if a['bbox'] is None:
            a['bbox'] = [list(lo), list(hi)]
        else:
            for i in range(3):
                a['bbox'][0][i] = min(a['bbox'][0][i], lo[i])
                a['bbox'][1][i] = max(a['bbox'][1][i], hi[i])

P('SolidCraft 聚合后名字数 =', len(agg))
missing = sorted(set(fcmap) - set(agg))
extra   = sorted(set(agg) - set(fcmap))
P('FreeCAD 有 / SolidCraft 无 =', len(missing), missing)
P('SolidCraft 多出 =', len(extra), extra)

rows = []
for n in sorted(fcmap):
    f = fcmap[n]
    a = agg.get(n)
    if not a:
        rows.append(dict(name=n, status='MISSING')); continue
    fv = f['volume']
    sv = a['volume'] if a['closed'] else None
    rel = None if sv is None else abs(sv - fv) / max(fv, 1e-9)
    fb = f['bbox']            # [xmin,ymin,zmin,xmax,ymax,zmax]
    sb = a['bbox']
    bbox_err = None
    if sb:
        sflat = sb[0] + sb[1]
        bbox_err = max(abs(sflat[i] - fb[i]) for i in range(6))
    status = 'OPEN_BODY' if not a['closed'] else (
             'OK' if (rel is not None and rel < 0.001 and
                      bbox_err is not None and bbox_err < 0.05) else 'MISMATCH')
    rows.append(dict(name=n, status=status, fc_volume=round(fv, 4),
                     sc_volume=None if sv is None else round(sv, 4),
                     rel_err=None if rel is None else round(rel, 8),
                     bbox_err=None if bbox_err is None else round(bbox_err, 5),
                     sc_bodies=a['n'], closed=a['closed']))

cnt = collections.Counter(r['status'] for r in rows)
P('')
P('=== 核验结论 ===')
for k, v in cnt.most_common():
    P('  %-12s %3d 件' % (k, v))
bad = [r for r in rows if r['status'] not in ('OK',)]
P('')
P('非 OK 明细:')
for r in bad:
    P('  %-28s %-10s fc=%12.3f sc=%s rel=%s bbox_err=%s bodies=%d'
      % (r['name'], r['status'], r['fc_volume'], r.get('sc_volume'),
         r.get('rel_err'), r.get('bbox_err'), r.get('sc_bodies', 0)))

fc_total = sum(r['volume'] for r in fcmap.values())
sc_total = sc['total']['volume_mm3']
P('')
P('FreeCAD 总实体体积   = %.3f mm3' % fc_total)
P('SolidCraft 总体积    = %.3f mm3 (只计闭合体)' % sc_total)
P('差额                 = %.3f mm3' % (fc_total - sc_total))
P('SolidCraft body 数   = %d / 闭合 %d / 开放 %d'
  % (len(bodies), sum(1 for b in bodies if b.get('closed')),
     sum(1 for b in bodies if not b.get('closed'))))
P('开放 body 名单 =', [b['name'] for b in bodies if not b.get('closed')])

with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(dict(fc_objects=len(fcmap), sc_bodies=len(bodies),
                   counts=dict(cnt), missing=missing, extra=extra,
                   fc_total_volume=fc_total, sc_total_volume=sc_total,
                   rows=rows), fh, ensure_ascii=False, indent=1)
P('DONE')
_f.close()
