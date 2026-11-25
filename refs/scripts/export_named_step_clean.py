# -*- coding: utf-8 -*-
"""迁移桥梁 v2：净化版。

直读 FCStd -> 只保留每个对象的真实 Solid（丢弃可能造成 STEP 导入器
丢面的开放壳/自由面/线框），用单一 Solid 或 Compound(Solids) 重建，
再 Import.export 成带零件名的装配 STEP。目的是消除 SolidCraft 里
X_EndPlate_L/R 等件被判为 open body 的问题。
"""
import os, sys, io, json, zipfile, re, tempfile, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Part

FCSTD = 'C:/ink/CrossSlide_P014013.FCStd'
OUT   = 'D:/mydocuments/SolidCraft/CrossSlide_P014013_clean.step'
REP   = 'C:/ink/refs/tmp/clean_export_report.json'
LOGP  = 'C:/ink/refs/tmp/export_named_step_clean.log'
_f = open(LOGP, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    try: print(s)
    except Exception: pass
    _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

z = zipfile.ZipFile(FCSTD)
xml = z.read('Document.xml').decode('utf-8', 'replace')
objs = re.findall(r'<Object type="Part::Feature" name="([^"]+)"', xml)
allnames = set(z.namelist())
tmp = tempfile.mkdtemp(prefix='fcstd2step_clean_')
doc = App.newDocument('MigrationClean')
shapes, rep = [], []
multi = []

for n in objs:
    fn = n + '.Shape.brp'
    p = os.path.join(tmp, fn.replace('/', '_'))
    with open(p, 'wb') as fh:
        fh.write(z.read(fn))
    s = Part.Shape()
    s.read(p)
    solids = list(s.Solids)
    before = dict(solids=len(solids), shells=len(s.Shells), faces=len(s.Faces),
                  edges=len(s.Edges), valid=bool(s.isValid()),
                  closed=bool(s.isClosed()), volume=round(s.Volume, 6))
    # 只保留闭合的实体；单实体直接用 Solid，多实体用 Compound
    good = [x for x in solids if x.isClosed() and x.isValid()]
    if not good:
        good = solids
    clean = good[0] if len(good) == 1 else Part.makeCompound(good)
    try:
        clean = clean.removeSplitter()
    except Exception as e:
        P('  removeSplitter 跳过', n, repr(e))
    if len(solids) > 1:
        multi.append((n, len(solids), len(good)))
    o = doc.addObject('Part::Feature', n)
    o.Shape = clean
    o.Label = n
    shapes.append(o)
    rep.append(dict(name=n, before=before,
                    after=dict(solids=len(clean.Solids), faces=len(clean.Faces),
                               valid=bool(clean.isValid()),
                               closed=bool(clean.isClosed()),
                               volume=round(clean.Volume, 6))))
doc.recompute()
P('对象数 =', len(shapes))
P('多实体对象 =', multi)
diff = [r for r in rep if abs(r['before']['volume'] - r['after']['volume']) > 0.01]
P('净化前后体积变化 > 0.01 mm3 的件数 =', len(diff))
for r in diff[:15]:
    P('   %-28s %.3f -> %.3f' % (r['name'], r['before']['volume'], r['after']['volume']))
P('净化后总实体体积 = %.3f mm3' % sum(r['after']['volume'] for r in rep))

try:
    import Import
    Import.export(shapes, OUT)
    method = 'Import.export'
except Exception as e:
    P('Import.export 失败:', repr(e))
    Part.export(shapes, OUT)
    method = 'Part.export'
P('写出方式 =', method, 'bytes =', os.path.getsize(OUT))
with open(REP, 'w', encoding='utf-8') as fh:
    json.dump(dict(objects=len(shapes), multi=multi, rows=rep), fh,
              ensure_ascii=False, indent=1)
shutil.rmtree(tmp, ignore_errors=True)
P('DONE')
_f.close()
