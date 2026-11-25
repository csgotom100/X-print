# -*- coding: utf-8 -*-
"""为 3 个在 SolidCraft 里变成开放壳的端板件导出单件 STEP / 网格备份，
并统计它们的曲面类型，定位导入器丢面原因。"""
import os, sys, io, zipfile, re, tempfile, shutil, collections, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace', write_through=True)
import FreeCAD as App
import Part

FCSTD = 'C:/ink/CrossSlide_P014013.FCStd'
DEST  = 'D:/mydocuments/SolidCraft'
TARGETS = ['X_EndPlate_L', 'X_EndPlate_R', 'Part__Feature']
LOG = 'C:/ink/refs/tmp/endplate_probe.log'
_f = open(LOG, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    try: print(s)
    except Exception: pass
    _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

z = zipfile.ZipFile(FCSTD)
tmp = tempfile.mkdtemp(prefix='endplate_')
for n in TARGETS:
    fn = n + '.Shape.brp'
    if fn not in z.namelist():
        P('MISSING', fn); continue
    p = os.path.join(tmp, fn)
    with open(p, 'wb') as fh:
        fh.write(z.read(fn))
    s = Part.Shape(); s.read(p)
    types = collections.Counter(type(f.Surface).__name__ for f in s.Faces)
    P('%s: V=%.3f solids=%d shells=%d faces=%d closed=%s'
      % (n, s.Volume, len(s.Solids), len(s.Shells), len(s.Faces), s.isClosed()))
    P('   面类型:', dict(types))
    # 单件 STEP（用 shape.exportStep，走另一条 STEP 写出路径）
    sp = os.path.join(DEST, n + '_single.step')
    s.exportStep(sp)
    P('   单件 STEP:', sp, os.path.getsize(sp), 'bytes')
    # 网格备份（3MF 由 FreeCAD 写 STL 后交给 SolidCraft 的 insert_mesh 更稳）
    stl = os.path.join(DEST, n + '_mesh.stl')
    import Mesh
    Mesh.export([__import__('Mesh').Mesh(s.tessellate(0.05))], stl) if False else None
    m = Mesh.Mesh(s.tessellate(0.05))
    m.write(stl)
    P('   网格 STL:', stl, os.path.getsize(stl), 'bytes  triangles=', m.CountFacets)
shutil.rmtree(tmp, ignore_errors=True)
P('DONE')
_f.close()
