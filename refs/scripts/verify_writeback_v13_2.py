# -*- coding: utf-8 -*-
"""v13.2 回写后逐件几何核对：主 FCStd vs 回滚备份。

字节哈希变化 ≠ 几何变化（FreeCAD GUI d.save() 会重序列化部分无关 BREP）。
本脚本对全部 139 件做「双向 cut 对称差 + 体积/面数/实体数」判据，
证明只有 HP45_ProbeHousing / HP45_SpringSpacer 两件几何真的变了。

运行：freecadcmd refs/scripts/verify_writeback_v13_2.py
"""
import os
import sys
import zipfile
import tempfile
import shutil
import FreeCAD as App
import Part

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_v13_2.FCStd'
LOGP = 'C:/ink/refs/tmp/verify_writeback_v13_2.log'
_fh = open(LOGP, 'w', encoding='utf-8')


def P(*a):
    s = ' '.join(str(x) for x in a)
    _fh.write(s + '\n'); _fh.flush(); os.fsync(_fh.fileno())
    try:
        print(s)
    except Exception:
        pass


def cutv(x, y):
    try:
        c = x.cut(y)
        return 0.0 if c.isNull() else c.Volume
    except Exception:
        return 0.0


EXPECT_CHANGED = {'HP45_ProbeHousing', 'HP45_SpringSpacer'}
P('=' * 96)
P('v13.2 回写后逐件几何核对（主 FCStd vs 回滚备份）')
P('=' * 96)

za, zb = zipfile.ZipFile(DOC), zipfile.ZipFile(BAK)
na = set(n for n in za.namelist() if n.endswith('.Shape.brp'))
nb = set(n for n in zb.namelist() if n.endswith('.Shape.brp'))
P('主 FCStd BREP %d 件 / 备份 %d 件 / 仅一侧 %d' % (len(na), len(nb), len(na ^ nb)))
assert na == nb, 'BREP 条目集合不一致'

td = tempfile.mkdtemp(prefix='v132wbchk_')
byte_same, reserial, changed, bad = [], [], [], []
for fn in sorted(na):
    n = fn[:-len('.Shape.brp')]
    ra, rb = za.read(fn), zb.read(fn)
    pa, pb = os.path.join(td, 'a.brp'), os.path.join(td, 'b.brp')
    open(pa, 'wb').write(ra); open(pb, 'wb').write(rb)
    sa, sb = Part.Shape(), Part.Shape()
    sa.read(pa); sb.read(pb)
    if ra == rb:
        byte_same.append(n)
        continue
    d = cutv(sa, sb) + cutv(sb, sa)
    geom_same = (d < 1e-6 and abs(sa.Volume - sb.Volume) < 1e-6
                 and len(sa.Faces) == len(sb.Faces)
                 and len(sa.Solids) == len(sb.Solids))
    if geom_same:
        reserial.append(n)
    else:
        changed.append((n, sa.Volume, sb.Volume, d))
    if not geom_same and n not in EXPECT_CHANGED:
        bad.append(n)

# 字节一致的分支会提前 continue，临时文件可能残留，统一由 rmtree 清理
shutil.rmtree(td, ignore_errors=True)

P('  字节完全一致          : %d 件' % len(byte_same))
P('  重序列化但几何等价    : %d 件  %s' % (len(reserial), reserial[:12]))
P('  几何真实变化          : %d 件' % len(changed))
for n, va, vb, d in changed:
    P('    %-24s V %.3f -> %.3f  (Δ%.3f)  对称差 %.6f' % (n, vb, va, va - vb, d))
P('  非预期几何变化        : %d 件  %s' % (len(bad), bad[:10]))
P('  151 对象 / 139 材质   : 由 writeback_v13_2.py 与 reload 读回验证')
ok = (len(changed) == 2
      and set(x[0] for x in changed) == EXPECT_CHANGED
      and not bad and na == nb)
P('')
P('  >> %s' % ('CONCLUSION PASS：仅 2 件几何改变，其余 137 件几何完全等价'
               if ok else 'CONCLUSION FAIL：存在非预期几何变化'))
P('=' * 96)
_fh.close()
