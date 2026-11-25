# -*- coding: utf-8 -*-
"""v13 回写：把 refs/tmp/v13out/ 的 3 个新 BREP 写进 GUI 已打开的文档并保存。

运行方式（FreeCAD GUI 的 Python 控制台 / MCP execute_code）：
    exec(compile(open('C:/ink/refs/scripts/writeback_v13.py', encoding='utf-8').read(),
                 'writeback_v13.py', 'exec'))

为什么走 GUI 而不是手工改 ZIP
--------------------------------------------------------------------
本机 2026-11-09 13:28 之后 freecadcmd 与 GUI 的 App.openDocument 一律卡死，
但 GUI 里 App.ActiveDocument 已装载 CrossSlide_P014013（151 对象，probe 已确认）。
直接对 3 个对象赋值 obj.Shape + d.save()，FreeCAD 会自行序列化
*.Shape.brp / *.Shape.Map.txt / ElementMap / GuiDocument.xml，
规避手工替换 BREP 的两个坑：
  * exportBrep 产物带 "DBRep_DrawableShape" 头，而 FCStd 内是裸 BREP；
  * *.Shape.Map.txt 是拓扑命名表，换 BREP 后必须一并重建。
与 build_v12_2.py 的回写通道完全一致。

回滚点：refs/CrossSlide_before_v13.FCStd（v12.2 完整副本，改前已校验字节一致）。

改动清单
--------------------------------------------------------------------
几何（3 件）：
  HP45_ProbeHousing  5567.474 -> 5245.833   敞开 U 型腔 + 一体顶棚
  HP45_ProbeArm     13460.557 -> 11633.557  顶板掏空减重 13.6%
  HP45_SpringSpacer    64.618 ->  552.050   阶梯顶塞 -> -X 侧盖板
文字（4 件）：座体 / 臂体 / 盖板 / 磁环 的 Label 与 Design 组注释改成 v13 口径
其余 148 个对象几何一字不动；冻结项用「改前 vs 改后 FCStd 内 BREP」的
SHA-256 逐字节比对证明未触碰。
"""
import hashlib
import os
import shutil
import zipfile
import FreeCAD as App
import Part

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_v13.FCStd'
NEW = 'C:/ink/refs/tmp/v13out/'
LOGP = 'C:/ink/refs/tmp/writeback_v13.log'
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
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def read_brp(path):
    s = Part.Shape(); s.read(path); return s

# ---------------------------------------------------------------- 0) 前置校验
P('=' * 96)
P('v13 回写（GUI 已打开文档通道）')
P('=' * 96)
assert os.path.exists(BAK), '回滚备份不存在：' + BAK
assert sha(BAK) == sha(DOC), '主文档与 v12.2 备份不一致，请先确认状态再回写'
P('  回滚备份 %s  size=%d  sha256=%s' % (BAK, os.path.getsize(BAK), sha(BAK)[:16]))

d = App.ActiveDocument
assert d is not None, 'GUI 里没有活动文档'
assert d.Name == 'CrossSlide_P014013', '活动文档不是目标：' + d.Name
assert os.path.normcase(os.path.abspath(d.FileName)) == os.path.normcase(os.path.abspath(DOC)), \
    '活动文档路径不符：' + d.FileName
g = d.getObject
P('  活动文档 %s  对象数=%d  FileName=%s' % (d.Name, len(d.Objects), d.FileName))

BASE = {'HP45_ProbeHousing': 5567.474,
        'HP45_ProbeArm': 13460.557,
        'HP45_SpringSpacer': 64.618}
EXPECT = {'HP45_ProbeHousing': 5245.833,
          'HP45_ProbeArm': 11633.557,
          'HP45_SpringSpacer': 552.050}
for n, v0 in BASE.items():
    o = g(n)
    assert o is not None, '缺少对象 ' + n
    assert abs(o.Shape.Volume - v0) < 0.01, \
        '%s 改前体积 %.3f != 期望 %.3f（脚本可能已跑过）' % (n, o.Shape.Volume, v0)
    P('  改前 %-22s V=%10.3f  OK' % (n, o.Shape.Volume))

# 记录冻结项改前字节（改后再比一次）
FREEZE = ['Z_EndPlate_L', 'Z_EndPlate_R', 'Z_LimitSwitch_Bot',
          'Z_LimitSwitch_Top', 'Z_Profile', 'X_EndPlate_L']
with zipfile.ZipFile(BAK) as zb:
    fr_before = dict((n + '.Shape.brp', hashlib.sha256(zb.read(n + '.Shape.brp')).hexdigest())
                     for n in FREEZE)

# ---------------------------------------------------------------- 1) 载入新几何
P('')
P('--- 1) 载入 v13 新 BREP ---')
shapes = {}
for n, v in EXPECT.items():
    p = NEW + n + '.Shape.brp'
    assert os.path.exists(p), '缺少新 BREP：' + p
    s = read_brp(p)
    assert s.isValid(), '新 BREP 无效：' + n
    assert len(s.Solids) == 1, '新 BREP 非单实体：' + n
    assert abs(s.Volume - v) < 0.01, '新 BREP 体积不符 %s: %.3f' % (n, s.Volume)
    shapes[n] = s
    P('  %-22s V=%10.3f sol=1 valid=True' % (n, s.Volume))

# ---------------------------------------------------------------- 2) 文字口径
def note(o, **kw):
    for prop, val in kw.items():
        if prop not in o.PropertiesList:
            o.addProperty('App::PropertyString', prop, 'Design', 'v13 design note')
        setattr(o, prop, val)

HOUS_LABEL = '探针座（v13 注塑：沿 X 分型敞开 U 型腔 + 一体顶棚 Ø2.50）'
HOUS_SPEC = (
    'v13 可注塑结构：Z76.50..78.50 磁环腔与 Z78.50..87.50 弹簧腔由封闭阶梯圆孔'
    '改成「从 -X 面敞开的阶梯 U 型槽」，槽沿 X 等截面直壁；主分型沿 X —— '
    'U 型槽型芯沿 -X 抽出、+X 霍尔窗型芯沿 +X 抽出，均无需侧滑块。'
    'Z87.50..90.00 是座体一体成型的顶棚，底面 Z87.50 即弹簧上止挡，'
    '中心 Ø2.50 通孔让 Ø2.02 针尾通过并保持 0..+3.0 mm 行程；独立阶梯顶塞取消。'
    '冻结项不变：磁环腔高 2.00 (Z76.50..78.50)、霍尔感测面 X83.40、r=5.90、'
    '中心 Z79.00、霍尔窗 3.20×5.50 (Z76.50..82.00 / Y-114.10..-110.90)、'
    'Ø2.37 针套孔、2×M3 孔、外形包络 X70.50..85.50 / Y-119..-106 / Z58..90。'
    '脱模性实测：U 型槽两型芯沿 -X 扫掠 common=0；霍尔窗型芯沿 +X 扫掠 common=0。'
)
HOUS_MAT = (
    '注塑级 POM 或 PA66+GF30（亦可 PC/ABS）；脱模斜度 1.5°、内角 R0.4、'
    '名义壁厚 2.0 mm。Ø2.37 针套孔、2×M3 螺纹孔、顶棚中心 Ø2.50 孔为'
    '注塑后钻/铰或铜嵌件，不做细长型芯。'
)
HOUS_ASM = (
    'v13 混合装配（探针子总成先在台面装好，再整体装入臂体）：'
    '① 磁环沿 +X 从 -X 侧装入敞开槽 Z76.50..78.50；'
    '② 弹簧沿 +X 侧装到 Z78.50..87.50；'
    '③ 探针 Ø2.02 从 +Z 经顶棚 Ø2.50 孔落下，穿过弹簧/磁环内孔进 Ø2.37 针套；'
    '④ 经 -X 敞开口在磁环内孔与针身间点低粘度环氧并固化（磁环须随针同步运动，'
    'v12.2 的「座体外预粘」因顶棚仅 Ø2.50 无法沿用）；'
    '⑤ -X 侧盖板沿 +X 扣合，两处补形凸台把腔体收窄到 X75.00..81.20；'
    '⑥ 卡扣 + 2 颗螺钉锁紧。禁止再从顶部塞入磁环/弹簧/顶塞（v12.2 通道已取消）。'
)

ARM_LABEL = '探针臂（v13 注塑：顶板掏空减重 13.6%，装配面不动）'
ARM_SPEC = (
    'v13 为均匀壁厚把 Z90..102 实心顶板局部掏空：在远离探针座接口 (X68..86) '
    '与 M3 孔区的 X90.0..100.0 / 102.5..112.5 / 115.0..125.0 三段开减重腔 '
    '(Y-118..-99 / Z93..99)，去除 1827.000 mm3 (13.6%)，'
    '成为 3 mm 面板 + 底板 + 加强筋。纯减料，不新增干涉；'
    '装配面、探针座口袋、M3 孔区、外形包络 X68..128 / Y-121.5..-96 / Z74..102 全部不动。'
)
ARM_MAT = (
    '注塑级 PA66+GF30 或 PC/ABS；名义壁厚 2.0 mm，脱模斜度 1.5°、内角 R0.4，'
    '避免 12 mm 厚实顶板产生缩痕。'
)
ARM_ASM = (
    '探针子总成（座体 + 内部零件 + 盖板）台面装配完成后，再整体装入臂体口袋'
    '并锁紧 2 颗 M3；臂体不作为台面装配阶段的障碍（沿用 verify_v12_2.py 口径）。'
)

SPACER_LABEL = '-X 侧盖板（v13：敞开腔封盖 + 两处补形凸台，含螺钉让位）'
SPACER_SPEC = (
    'v13 由「阶梯顶塞」改为「-X 侧盖板」，复用原对象名以保持 14 件清单与脚本引用不变。'
    '主板 X68.60..70.50 / Y-119..-106 / Z76.50..87.50，贴在座体 -X 面封住敞开槽；'
    '两处补形凸台 X70.50..75.00：磁环腔凸台 Y-115.70..-109.30 / Z76.50..78.50，'
    '弹簧腔凸台 Y-114.90..-109.40 / Z78.50..87.50。'
    '凸台 +X 端面 X75.00 把腔体收窄到 X75.00..81.20，磁环/弹簧 Ø6.00 定位间隙 0.20 不变。'
    '弹簧上止挡改由座体一体顶棚 Z87.50 承担，盖板不承受弹簧轴向力。'
)
SPACER_MAT = (
    '注塑级 POM 或 PA66；主板与两凸台均为等截面直棱柱，沿 X 直抽成型，无需侧滑块。'
    '弹簧腔凸台 -Y 边退到 Y-114.90（较槽壁让位 0.70），为 HP45_HousingScrew_0 的 '
    'Ø2.44 杆部（杆心 74.00,-116.50）留 0.38 mm 间隙，覆盖注塑 ±0.1 公差与 1.5° 斜度；'
    '该修正消除了首版 1.2982 mm3 的盖板/螺钉干涉。'
)
SPACER_ASM = (
    '第 5 步：磁环/弹簧/探针就位、磁环与针身点胶固化后，盖板从 -X 沿 +X 扣到座体 -X 面；'
    '刚体平移逐点采样验证全程无干涉（最大 0.000000 mm3）。2 处卡扣 + 2 颗 M3 固定。'
    'v12.2 的独立阶梯顶塞、Z88.50 肩部定位、凡士林临时固定、臂体顶棚压住顶塞'
    '等工序全部取消。'
)

MAG_APPENDIX = (
    'v13：敞开 U 型槽使磁环可从 -X 侧沿 +X 直接侧装进 Z76.50..78.50，'
    '不再需要穿过顶部细颈；外径仍按 <=6.10 筛选（沿用 v12.2 加严口径，留 0.10 余量），'
    '厚度 <=2.00 保证磁环腔高 2.00 不变。装配顺序改为先放磁环与弹簧，'
    '再从 +Z 落下探针穿过磁环内孔，随后在 -X 敞开口处点胶把磁环固定到针身。'
)
MAG_ASM = (
    'v13：磁环单独从 -X 侧沿 +X 侧装进敞开槽 Z76.50..78.50，由槽底 Z76.50 与'
    '盖板凸台定位；弹簧随后侧装、探针从 +Z 落下穿过内孔 Ø2.10。'
    '因顶棚中心仅 Ø2.50，Ø6 磁环无法随针从顶部装入，故「座体外 V 形夹具预粘」'
    '改为「装配到位后经 -X 敞开口在单边 0.04 胶缝点低粘度环氧并固化」；'
    '固化前用简易定位保证针身与磁环同轴度 <=0.1。磁环必须随针同步运动，'
    '否则霍尔输出不随行程变化。'
)

# ---------------------------------------------------------------- 3) 赋值
P('')
P('--- 2) 写入 3 个新几何 + 更新 4 个对象的文字口径 ---')
for n, s in shapes.items():
    g(n).Shape = s
    P('  [shape] %-22s -> V=%10.3f' % (n, g(n).Shape.Volume))

h = g('HP45_ProbeHousing')
h.Label = HOUS_LABEL
note(h, SpecNote=HOUS_SPEC, MaterialNote=HOUS_MAT, AssemblyNote=HOUS_ASM)
a = g('HP45_ProbeArm')
a.Label = ARM_LABEL
note(a, SpecNote=ARM_SPEC, MaterialNote=ARM_MAT, AssemblyNote=ARM_ASM)
c = g('HP45_SpringSpacer')
c.Label = SPACER_LABEL
note(c, SpecNote=SPACER_SPEC, MaterialNote=SPACER_MAT, AssemblyNote=SPACER_ASM)
m = g('HP45_PogoMagnet')
sp = m.SpecNote
idx = sp.find('v12.2：')
assert idx >= 0, '磁环 SpecNote 里找不到 v12.2 附录，需人工核对'
m.SpecNote = sp[:idx].rstrip() + ' ' + MAG_APPENDIX
note(m, AssemblyNote=MAG_ASM)
P('  [notes] 座体/臂体/盖板 Label+3 注释，磁环 SpecNote 附录与 AssemblyNote 已改 v13')

d.recompute()
for n, v in EXPECT.items():
    assert abs(g(n).Shape.Volume - v) < 0.01, 'recompute 后体积异常：' + n
P('  recompute 后 3 件体积与预期一致 OK')

# ---------------------------------------------------------------- 4) 保存
P('')
P('--- 3) d.save() ---')
d.save()
P('  已保存 %s  size=%d' % (DOC, os.path.getsize(DOC)))

# ---------------------------------------------------------------- 5) 保存后核验
P('')
P('--- 4) 保存后核验（直接读 FCStd 压缩包内的 BREP）---')
with zipfile.ZipFile(DOC) as z:
    names = z.namelist()
    bad = z.testzip()
    P('  ZIP entries=%d  testzip=%s  GuiDocument.xml=%s'
      % (len(names), bad, 'GuiDocument.xml' in names))
    assert bad is None, 'ZIP 损坏'
    assert 'GuiDocument.xml' in names, 'GuiDocument.xml 丢失'
    xml = z.read('Document.xml').decode('utf-8')
    P('  Document.xml 对象块数 = %d  %s'
      % (xml.count('<Object name='), 'OK 151' if xml.count('<Object name=') == 151 else '!! 变化'))
    assert xml.count('<Object name=') == 151, '对象数变化'
    # 3 个新几何：从 FCStd 内 BREP 回读体积
    import tempfile
    td = tempfile.mkdtemp(prefix='v13fc_')
    for n, v in EXPECT.items():
        fn = n + '.Shape.brp'
        p = os.path.join(td, fn)
        open(p, 'wb').write(z.read(fn))
        s = read_brp(p)
        P('  %-22s FCStd 内 V=%10.3f sol=%d valid=%s  %s'
          % (n, s.Volume, len(s.Solids), s.isValid(),
             'OK' if abs(s.Volume - v) < 0.01 and s.isValid() else '!! 不符'))
        assert abs(s.Volume - v) < 0.01 and s.isValid() and len(s.Solids) == 1, \
            'FCStd 内几何回读不符：' + n
        os.remove(p)
    os.rmdir(td)
    # 冻结项：改前 vs 改后 BREP 字节
    fr_ok = True
    for n in FREEZE:
        fn = n + '.Shape.brp'
        same = hashlib.sha256(z.read(fn)).hexdigest() == fr_before[fn]
        fr_ok &= same
        P('  冻结 %-22s %s' % (n, '字节一致 OK' if same else '!! 字节变化'))
    # 文字口径抽查
    for n, lab in (('HP45_ProbeHousing', HOUS_LABEL),
                   ('HP45_ProbeArm', ARM_LABEL),
                   ('HP45_SpringSpacer', SPACER_LABEL)):
        s = xml.find('<Object name="%s">' % n)
        e = xml.find('</Object>', s)
        ok = lab in xml[s:e]
        P('  Label %-22s %s' % (n, 'OK v13' if ok else '!! 未更新'))
        assert ok, 'Label 未写回：' + n
P('  >> 冻结项几何：%s' % ('全部未触碰 OK' if fr_ok else '!! 有字节变化（需人工核对）'))

P('')
P('=' * 96)
P('回写完成：3 件几何 = v13，151 对象数不变，冻结项%s，GUI 视图数据保留'
  % ('未触碰' if fr_ok else '需核对'))
P('回滚：copy /y "%s" "%s"' % (BAK.replace('/', '\\'), DOC.replace('/', '\\')))
P('=' * 96)
_fh.close()
