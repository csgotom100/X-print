# -*- coding: utf-8 -*-
"""FreeCAD -> SolidCraft 迁移桥梁。

从当前磁盘 FCStd 直接读 BREP（不 openDocument，避开本机 1.1 的卡死问题），
统计每个 Part::Feature 的拓扑健康度，再用 Import.export 生成一个
「每个零件一个 PRODUCT、名字=FreeCAD 对象名」的装配 STEP，
供 SolidCraft 的 file.insert_step {names:"product"} 导入。
"""
import os, sys, io, json, zipfile, re, tempfile, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Part

FCSTD = 'C:/ink/CrossSlide_P014013.FCStd'
OUT   = 'D:/mydocuments/SolidCraft/CrossSlide_P014013_named.step'
STAT  = 'C:/ink/refs/tmp/fcstd_topology.json'
LOGP  = 'C:/ink/refs/tmp/export_named_step.log'
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
P('FCStd Part::Feature 对象数 =', len(objs))

tmp = tempfile.mkdtemp(prefix='fcstd2step_')
doc = App.newDocument('Migration')
shapes, rows = [], []
for n in objs:
    fn = n + '.Shape.brp'
    if fn not in allnames:
        rows.append(dict(name=n, status='MISSING_BREP'))
        P('  MISSING BREP', n)
        continue
    p = os.path.join(tmp, fn.replace('/', '_'))
    with open(p, 'wb') as fh:
        fh.write(z.read(fn))
    s = Part.Shape()
    s.read(p)
    o = doc.addObject('Part::Feature', n)
    o.Shape = s
    o.Label = n
    shapes.append(o)
    bb = s.BoundBox
    rows.append(dict(
        name=n, status='OK', volume=round(s.Volume, 6),
        solids=len(s.Solids), shells=len(s.Shells), faces=len(s.Faces),
        valid=bool(s.isValid()), closed=bool(s.isClosed()),
        bbox=[round(v, 4) for v in (bb.XMin, bb.YMin, bb.ZMin,
                                    bb.XMax, bb.YMax, bb.ZMax)]))
doc.recompute()
P('已建立临时文档对象数 =', len(shapes))

ok = [r for r in rows if r['status'] == 'OK']
solid = [r for r in ok if r['solids'] > 0 and r['closed']]
open_ = [r for r in ok if not (r['solids'] > 0 and r['closed'])]
P('实体件 (solids>0 且 closed) =', len(solid))
P('非实体/开放件 =', len(open_))
P('总实体体积 = %.3f mm3' % sum(r['volume'] for r in solid))
P('非实体明细:')
for r in open_:
    P('   %-28s solids=%d shells=%d faces=%3d valid=%s closed=%s V=%.3f'
      % (r['name'], r['solids'], r['shells'], r['faces'],
         r['valid'], r['closed'], r['volume']))

method = ''
try:
    import Import
    Import.export(shapes, OUT)
    method = 'Import.export'
except Exception as e:
    P('Import.export 失败:', repr(e))
    Part.export(shapes, OUT)
    method = 'Part.export (fallback)'
P('STEP 写出方式 =', method)
P('STEP 文件 =', OUT, 'bytes =', os.path.getsize(OUT))

with open(STAT, 'w', encoding='utf-8') as fh:
    json.dump(dict(source=FCSTD, step=OUT, method=method,
                   object_count=len(objs), solid_count=len(solid),
                   total_solid_volume=sum(r['volume'] for r in solid),
                   rows=rows), fh, ensure_ascii=False, indent=1)
shutil.rmtree(tmp, ignore_errors=True)
P('DONE')
_f.close()
