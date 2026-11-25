# -*- coding: utf-8 -*-
"""v13.2 回写：把 8x8 通道 + 6.20 导向段的两件新 BREP 写进 GUI 已打开文档。

运行方式（FreeCAD GUI 的 MCP execute_code / Python 控制台）：
    exec(compile(open('C:/ink/refs/scripts/writeback_v13_2.py', encoding='utf-8').read(),
                 'writeback_v13_2.py', 'exec'))

为什么走 GUI：本机 FreeCAD 1.1 的 App.openDocument 会卡死；而 GUI 的
App.ActiveDocument 已装载目标文档。直接赋 obj.Shape + d.save()，由 FreeCAD
自行序列化 *.Shape.brp / *.Shape.Map.txt / ElementMap / GuiDocument.xml。
绝不手工替换 ZIP 内 BREP。

只改 2 件几何（臂体字节未动，不赋值）：
  HP45_ProbeHousing  5245.833 -> 5138.609
  HP45_SpringSpacer   552.050 ->  560.200
v14 材质（ShapeMaterial / MaterialSpec / ShapeColor）与 151 对象数全部保留。
回滚：refs/CrossSlide_before_v13_2.FCStd
"""
import os
import sys
import hashlib
import zipfile
import tempfile
import FreeCAD as App
import Part

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_v13_2.FCStd'
NEW = 'C:/ink/refs/tmp/v13_2out/'
LOGP = 'C:/ink/refs/tmp/writeback_v13_2.log'
_fh = open(LOGP, 'w', encoding='utf-8')


def P(*a):
    s = ' '.join(str(x) for x in a)
    _fh.write(s + '\n'); _fh.flush(); os.fsync(_fh.fileno())
    try:
        print(s)
    except Exception:
        pass


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def read_brp(path):
    s = Part.Shape(); s.read(path); return s


P('=' * 96)
P('v13.2 回写（GUI 已打开文档通道）')
P('=' * 96)
assert os.path.exists(BAK), '回滚备份不存在：' + BAK
assert sha(BAK) == sha(DOC), '主文档与回滚备份不一致，请先确认状态再回写'
P('  回滚备份 OK  size=%d  sha256=%s' % (os.path.getsize(BAK), sha(BAK)[:16]))

d = App.ActiveDocument
assert d is not None, 'GUI 里没有活动文档'
assert d.Name == 'CrossSlide_P014013', '活动文档不是目标：' + d.Name
assert os.path.normcase(os.path.abspath(d.FileName)) == os.path.normcase(os.path.abspath(DOC)), \
    '活动文档路径不符：' + d.FileName
g = d.getObject
P('  活动文档 %s  对象数=%d  FileName=%s' % (d.Name, len(d.Objects), d.FileName))

BEFORE = {'HP45_ProbeHousing': 5245.833, 'HP45_SpringSpacer': 552.050}
EXPECT = {'HP45_ProbeHousing': 5138.609, 'HP45_SpringSpacer': 560.200}
for n, v0 in BEFORE.items():
    o = g(n)
    assert o is not None, '缺少对象 ' + n
    assert abs(o.Shape.Volume - v0) < 0.01, \
        '%s 改前体积 %.3f != 期望 %.3f（脚本可能已跑过或 GUI 内存与磁盘不同步）' \
        % (n, o.Shape.Volume, v0)
    P('  改前 %-22s V=%10.3f  OK' % (n, o.Shape.Volume))
assert abs(g('HP45_ProbeArm').Shape.Volume - 11633.557) < 0.01, '臂体体积异常'

# 材质前置：v14 的 139 个 MaterialSpec 必须还在
parts = [o for o in d.Objects if o.TypeId == 'Part::Feature']
mat_n = sum(1 for o in parts if 'MaterialSpec' in o.PropertiesList and o.MaterialSpec)
P('  Part::Feature = %d  带 MaterialSpec = %d' % (len(parts), mat_n))
assert len(parts) == 139 and mat_n == 139, 'v14 材质标记不完整，停止回写'

FREEZE = ['Z_EndPlate_L', 'Z_EndPlate_R', 'Z_LimitSwitch_Bot',
          'Z_LimitSwitch_Top', 'Z_Profile', 'X_EndPlate_L']
with zipfile.ZipFile(BAK) as zb:
    fr_before = dict((n + '.Shape.brp', hashlib.sha256(zb.read(n + '.Shape.brp')).hexdigest())
                     for n in FREEZE)

# ---------------------------------------------------------------- 1) 载入
P('')
P('--- 1) 载入 v13.2 新 BREP ---')
shapes = {}
for n, v in EXPECT.items():
    p = NEW + n + '.Shape.brp'
    assert os.path.exists(p), '缺少新 BREP：' + p
    s = read_brp(p)
    assert s.isValid() and len(s.Solids) == 1, '新 BREP 非单一有效实体：' + n
    assert abs(s.Volume - v) < 0.01, '新 BREP 体积不符 %s: %.3f' % (n, s.Volume)
    shapes[n] = s
    P('  %-22s V=%10.3f sol=1 valid=True' % (n, s.Volume))


# ---------------------------------------------------------------- 2) 文字口径
def note(o, **kw):
    for prop, val in kw.items():
        if prop not in o.PropertiesList:
            o.addProperty('App::PropertyString', prop, 'Design', 'v13.2 design note')
        setattr(o, prop, val)


HOUS_LABEL = '探针座（v13.2 注塑：8x8 磁环全行程通道 + 6.20 弹簧导向段 + 一体顶棚 Ø2.50）'
HOUS_SPEC = (
    'v13.2 可注塑结构：沿 X 分型的 -X 敞开 U 型腔分两段。'
    '磁环全行程通道 Z76.50..81.50 为对称 8.00×8.00（X74.00..82.00 / '
    'Y-116.50..-108.50，以针轴 78.00/-112.50 为中心），覆盖磁环 0..+3.0 mm 全行程，'
    '现货 Ø6±0.2 磁环单边余 0.90~1.00 mm 正公差空间；磁环由针杆/针套定心，不靠腔壁。'
    '弹簧导向段 Z81.50..87.50 保持 Y 净宽 6.20（X75.00..81.10 / Y-115.60..-109.40），'
    'Ø6 弹簧单边 0.10 紧导向防偏斜。Z87.50..90.00 为座体一体顶棚，底面 Z87.50 即弹簧上止挡，'
    '中心 Ø2.50 通孔让 Ø2.02 针尾通过。Z78.50 的 4 处碎错台（0.80/0.10/0.10/0.90）'
    '收敛为 Z81.50 一处近似对称环形台阶（每边约 0.90）。'
    '主分型沿 X：两型芯 -X 抽出、霍尔窗型芯 +X 抽出，均无需侧滑块。'
    '冻结项不变：磁环下台阶 Z76.50 / 厚 2.00、霍尔感测面 X83.40、r=5.90、中心 Z79.00、'
    '霍尔窗 3.20×5.50、Ø2.37 针套孔、2×M3、外形 X70.50..85.50 / Y-119..-106 / Z58..90。'
)
SPACER_LABEL = '−X 侧盖板（v13.2：8x8 通道补形到 X74.00 + 6.20 导向凸台 Z81.50 起）'
SPACER_SPEC = (
    'v13.2 -X 侧盖板（不是顶塞）：主板 X68.60..70.50 / Y-119..-106 / Z76.50..87.50；'
    '8x8 通道补形凸台 X70.50..74.00 / Y-116.50..-108.50 / Z76.50..81.50；'
    '弹簧导向段补形凸台 X70.50..75.00 / Y-114.90..-109.40 / Z81.50..87.50，'
    '-Y 边仍退到 -114.90 避开 HousingScrew_0 的 Ø2.44 杆部。'
    '扣合后磁环净空为 X74.00..82.00 / Y-116.50..-108.50 的 8.00×8.00。'
    '卡扣 + 2×M3 固定；装配顺序：磁环/弹簧 +X 侧装 → 探针 -Z 落 → 原位点胶 → 盖板 +X 扣合。'
)
MAG_APPENDIX = (
    'v13.2：磁环运动通道扩为 8.00×8.00 并覆盖 Z76.50..81.50 全行程，'
    '磁环 Ø6 单边净空 1.00 mm（现货上限 Ø6.20 仍余 0.90 mm），'
    '不再依赖腔壁定心；仍必须逐只或分组标定，仍需经 -X 敞口原位点胶固化。'
)
SPR_APPENDIX = (
    'v13.2：弹簧规格保持 Ø6 / Ø4.6 / 0.30×12 圈 / k=0.045 N/mm / F0=0.045 N 不变；'
    'Z81.50..87.50 保留 Y 净宽 6.20 的紧导向段（单边 0.10）防止压缩时侧弯偏斜，'
    '不采用「缩小弹簧外径」方案以免 k∝1/D³ 抬高接触力。'
)

P('')
P('--- 2) 写入 2 件新几何 + 更新文字口径 ---')
for n, s in shapes.items():
    g(n).Shape = s
    P('  [shape] %-22s -> V=%10.3f' % (n, g(n).Shape.Volume))

h = g('HP45_ProbeHousing')
h.Label = HOUS_LABEL
note(h, SpecNote=HOUS_SPEC, AssemblyNote='v13.2 混合装配：磁环/弹簧 +X 侧装 → 探针 -Z 落 → 原位点胶 → 盖板 +X 扣合')
c = g('HP45_SpringSpacer')
c.Label = SPACER_LABEL
note(c, SpecNote=SPACER_SPEC)
m = g('HP45_PogoMagnet')
note(m, SpecNote=m.SpecNote.rstrip() + ' ' + MAG_APPENDIX)
sp = g('HP45_PogoSpring')
note(sp, SpecNote=(sp.SpecNote.rstrip() + ' ' + SPR_APPENDIX)
     if sp.SpecNote else SPR_APPENDIX)
P('  [notes] 座体 / 盖板 / 磁环 / 弹簧已改 v13.2 口径')

d.recompute()
for n, v in EXPECT.items():
    assert abs(g(n).Shape.Volume - v) < 0.01, 'recompute 后体积异常：' + n
P('  recompute 后两件体积与预期一致 OK')

# ---------------------------------------------------------------- 3) 保存
P('')
P('--- 3) d.save() ---')
d.save()
P('  已保存 %s  size=%d  sha256=%s' % (DOC, os.path.getsize(DOC), sha(DOC)[:16]))

# ---------------------------------------------------------------- 4) 保存后核验
P('')
P('--- 4) 保存后核验（直读 FCStd 压缩包）---')
with zipfile.ZipFile(DOC) as z:
    names = z.namelist()
    P('  ZIP 条目 = %d  testzip = %s  GuiDocument.xml = %s'
      % (len(names), z.testzip(), 'GuiDocument.xml' in names))
    assert z.testzip() is None and 'GuiDocument.xml' in names
    xml = z.read('Document.xml').decode('utf-8')
    P('  对象块 = %d  MaterialSpec = %d  PropertyMaterial uuid = %d'
      % (xml.count('<Object name='), xml.count('<Property name="MaterialSpec"'),
         xml.count('<PropertyMaterial uuid=')))
    assert xml.count('<Object name=') == 151
    assert xml.count('<Property name="MaterialSpec"') == 139
    import re
    refs = re.findall(r'ElementMap2 file="([^"]+)"', xml)
    dang = [r for r in refs if r not in names]
    P('  ElementMap2 引用 = %d  悬空 = %d' % (len(refs), len(dang)))
    assert not dang
    td = tempfile.mkdtemp(prefix='v132wb_')
    for n, v in EXPECT.items():
        p = os.path.join(td, n + '.brp')
        open(p, 'wb').write(z.read(n + '.Shape.brp'))
        s = read_brp(p); os.remove(p)
        ok = s.isValid() and len(s.Solids) == 1 and abs(s.Volume - v) < 0.01
        P('  %-22s FCStd 内 V=%10.3f sol=%d  %s' % (n, s.Volume, len(s.Solids), 'OK' if ok else '!! 不符'))
        assert ok
    os.rmdir(td)
    fr_ok = True
    for n in FREEZE:
        fn = n + '.Shape.brp'
        same = hashlib.sha256(z.read(fn)).hexdigest() == fr_before[fn]
        fr_ok &= same
        P('  冻结 %-22s %s' % (n, '字节一致 OK' if same else '!! 字节变化（需几何等价复核）'))
P('  >> 冻结项几何：%s' % ('全部未触碰 OK' if fr_ok else '需以对称差复核'))

P('')
P('=' * 96)
P('v13.2 回写完成：2 件几何已更新，151 对象 / 139 材质标记保留，'
  'GUI 视图数据保留。下一步：reload_document 重载读回 + 重跑 verify_v13_2.py')
P('回滚：copy /y "%s" "%s"' % (BAK.replace('/', '\\'), DOC.replace('/', '\\')))
P('=' * 96)
_fh.close()
