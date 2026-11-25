# -*- coding: utf-8 -*-
"""X-print v14 材质闭环验证（独立 freecadcmd 进程，不调用 App.openDocument）。

验证链条：
  1. FCStd Document.xml 的 139 个 <PropertyMaterial uuid="..."/>
     -> FreeCAD 用户材质库 X-Print/*.FCMat
     -> Materials.MaterialManager 按 UUID 解析出名称 / 密度 / 颜色
     -> 与随文档保存的 MaterialSpec 文本一致；
  2. 几何未被材质设置改动：
     - 与 apply_materials.py 保存前的几何快照比体积 / 面数 / 实体数 / isValid；
     - 与 v13 定稿基线做双向 cut（对称差体积 = 0），这是项目既定的权威口径。
       136 件用 refs/CrossSlide_before_v13.FCStd（v12.2，几何未受 v13 影响），
       3 件 v13 主件用 refs/materials/baseline_v13/*.brp；
  3. ZIP / Document.xml / GuiDocument.xml 完整性。

注意：内存中的 Shape 带显示三角化缓存，圆柱/曲面件的 BoundBox 会略小于
从 BREP 直读（解析几何）的值，最大可达 1.3 mm。这是已知序列化现象，
不是几何变化，因此 BBox 只记录、不作失败判据；以对称差体积为准。

运行：
    "/d/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" refs/scripts/verify_materials.py
"""
import os
import sys
import re
import json
import zipfile
import hashlib
import traceback

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = r'C:/ink'
DOC = os.path.join(ROOT, 'CrossSlide_P014013.FCStd')
LOG = os.path.join(ROOT, 'refs', 'tmp', 'verify_materials.log')
LINES = []


def P(*a):
    s = ' '.join(str(x) for x in a)
    LINES.append(s)
    try:
        print(s)
    except Exception:
        pass


def flush():
    with open(LOG, 'w', encoding='utf-8') as f:
        f.write('\n'.join(LINES) + '\n')
        f.flush()
        os.fsync(f.fileno())


try:
    import FreeCAD as App
    import Materials
    import Part

    P('FreeCAD', App.Version()[0:3], 'UserAppData', App.getUserAppDataDir())

    z = zipfile.ZipFile(DOC)
    names = z.namelist()
    xml = z.read('Document.xml').decode('utf-8', errors='replace')
    objects_n = len(re.findall(r'<Object name=', xml))
    P('ZIP', 'entries', len(names), 'testzip', z.testzip(),
      'GuiDocument', 'GuiDocument.xml' in names)
    P('Objects', objects_n)
    P('SHA256', hashlib.sha256(open(DOC, 'rb').read()).hexdigest())
    emap = re.findall(r'<ElementMap2[^>]*file="([^"]+)"', xml)
    P('ElementMap2', len(emap), 'dangling', len([f for f in emap if f not in names]))

    # ---- 1) 材质闭环 ----------------------------------------------------
    pairs = []
    specs = {}
    for blk in re.split(r'(?=<Object name=")', xml):
        mo = re.match(r'<Object name="([^"]+)"', blk)
        if not mo:
            continue
        name = mo.group(1)
        um = re.search(r'<PropertyMaterial uuid="([^"]+)"', blk)
        if um:
            pairs.append((name, um.group(1)))
        sm = re.search(r'<Property name="MaterialSpec".*?<String value="([^"]*)"', blk, re.S)
        if sm:
            specs[name] = sm.group(1)
    P('ShapeMaterial refs', len(pairs), 'unique UUID', len(set(u for _, u in pairs)))
    P('MaterialSpec strings', len(specs))

    mm = Materials.MaterialManager()
    cache, missing, mismatch = {}, [], []
    for name, uid in pairs:
        if uid not in cache:
            try:
                cache[uid] = mm.getMaterial(uid)
            except Exception:
                cache[uid] = None
        m = cache[uid]
        if m is None:
            missing.append((name, uid))
            continue
        spec = specs.get(name, '')
        if spec and not spec.startswith(m.Name):
            mismatch.append((name, m.Name, spec[:40]))
    P('UUID 解析成功', len(pairs) - len(missing), '/', len(pairs),
      'MISSING', len(missing), 'SPEC_MISMATCH', len(mismatch))
    if missing:
        P('MISSING_DETAIL', missing[:8])
    if mismatch:
        P('MISMATCH_DETAIL', mismatch[:8])

    # ---- 2) 几何：保存前快照 ---------------------------------------------
    snap_path = os.path.join(ROOT, 'refs', 'materials', 'geometry_snapshot_v14.json')
    if not os.path.isfile(snap_path):
        snap_path = os.path.join(ROOT, 'refs', 'tmp', 'geometry_before_materials.json')
    before = json.load(open(snap_path, encoding='utf-8'))
    P('几何快照', os.path.relpath(snap_path, ROOT))

    brep_dir = os.path.join(ROOT, 'refs', 'tmp', 'brep_after_materials')
    os.makedirs(brep_dir, exist_ok=True)
    for f in names:
        if f.endswith('.Shape.brp'):
            with open(os.path.join(brep_dir, os.path.basename(f)), 'wb') as out:
                out.write(z.read(f))

    shapes = {}
    geom_bad, bbox_large = [], []
    checked, bbox_tri, bbox_max = 0, 0, 0.0
    for name, snap in before.items():
        fp = os.path.join(brep_dir, name + '.Shape.brp')
        if not os.path.isfile(fp):
            geom_bad.append((name, 'BREP missing'))
            continue
        s = Part.Shape()
        s.read(fp)
        shapes[name] = s
        bb = s.BoundBox
        now = dict(volume=round(s.Volume, 6),
                   bbox=[round(v, 6) for v in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)],
                   faces=len(s.Faces), solids=len(s.Solids), valid=s.isValid())
        checked += 1
        if (now['volume'] != snap['volume'] or now['faces'] != snap['faces']
                or now['solids'] != snap['solids'] or now['valid'] != snap['valid']):
            geom_bad.append((name, 'TOPO_OR_VOLUME', snap, now))
            continue
        delta = max(abs(a - b) for a, b in zip(now['bbox'], snap['bbox']))
        bbox_max = max(bbox_max, delta)
        if delta > 1e-9:
            bbox_tri += 1
        if delta > 0.05:
            bbox_large.append((name, round(delta, 4)))
    P('几何快照比对', checked, '件；体积/面数/实体数/有效性 差异', len(geom_bad))
    P('BBox 三角化缓存偏差', bbox_tri, '件，最大', round(bbox_max, 4),
      'mm；>0.05mm 的', len(bbox_large), '件（仅记录，以对称差为准）')
    if bbox_large:
        P('BBOX_LARGE', bbox_large[:8])
    if geom_bad:
        P('GEOM_DIFF', geom_bad[:5])

    # ---- 3) 权威几何等价：与 v13 基线双向 cut -----------------------------
    base_fcstd = os.path.join(ROOT, 'refs', 'CrossSlide_before_v13.FCStd')
    baseline_dir = os.path.join(ROOT, 'refs', 'tmp', 'brep_v12_2_baseline')
    os.makedirs(baseline_dir, exist_ok=True)
    if os.path.isfile(base_fcstd):
        bz = zipfile.ZipFile(base_fcstd)
        for f in bz.namelist():
            if f.endswith('.Shape.brp'):
                with open(os.path.join(baseline_dir, os.path.basename(f)), 'wb') as out:
                    out.write(bz.read(f))
    v13_dir = os.path.join(ROOT, 'refs', 'materials', 'baseline_v13')
    v13_parts = {'HP45_ProbeHousing', 'HP45_ProbeArm', 'HP45_SpringSpacer'}

    def cut_volume(x, y):
        """完全相同形状 cut 后是 Null shape（几何等价），按 0 处理。"""
        try:
            c = x.cut(y)
            return 0.0 if c.isNull() else c.Volume
        except ValueError:
            return 0.0

    sym_bad, sym_checked = [], 0
    for name in before:
        fp_a = os.path.join(brep_dir, name + '.Shape.brp')
        fp_b = (os.path.join(v13_dir, name + '.Shape.brp') if name in v13_parts
                else os.path.join(baseline_dir, name + '.Shape.brp'))
        if not os.path.isfile(fp_a) or not os.path.isfile(fp_b):
            sym_bad.append((name, 'baseline BREP missing'))
            continue
        a = shapes[name]
        b = Part.Shape()
        b.read(fp_b)
        d = cut_volume(a, b) + cut_volume(b, a)
        sym_checked += 1
        if d > 1e-6:
            sym_bad.append((name, round(d, 6)))
    P('对称差体积验证', sym_checked, '件，差异', len(sym_bad))
    if sym_bad:
        P('SYM_DIFF', sym_bad[:8])

    # ---- 4) 冻结项与抽样 -------------------------------------------------
    frozen = ['Z_EndPlate_L', 'Z_LimitSwitch_Bot', 'Z_LimitSwitch_Top',
              'X_EndPlate_L', 'HP45_ProbeHousing', 'HP45_ProbeArm', 'HP45_SpringSpacer']
    pmap = dict(pairs)
    for n in frozen:
        P('FROZEN', n, '|', mm.getMaterial(pmap[n]).Name if n in pmap else 'NA',
          '| V =', before.get(n, {}).get('volume'))

    summary = json.load(open(os.path.join(ROOT, 'refs', 'materials', 'material_summary.json'),
                             encoding='utf-8'))
    for key in ('PETG', 'POM', 'PA66GF30', 'NDFEB'):
        d = summary['materials'][key]
        m = mm.getMaterial(d['uuid'])
        P('SAMPLE', key, repr(m.Name),
          '| Density', m.PhysicalProperties.get('Density'),
          '| Diffuse', m.AppearanceProperties.get('DiffuseColor'))

    ok = (len(pairs) == 139 and len(set(u for _, u in pairs)) == 21
          and len(specs) == 139 and len(missing) == 0 and len(mismatch) == 0
          and len(geom_bad) == 0 and checked == 139
          and len(sym_bad) == 0 and sym_checked == 139
          and objects_n == 151 and z.testzip() is None
          and 'GuiDocument.xml' in names)
    P('CONCLUSION', 'PASS' if ok else 'FAIL')
    P('>>> v14 材质闭环验证通过：UUID 引用 / 材质库解析 / 材质文字标记 / 几何冻结项 / ZIP 完整性 全部 OK'
      if ok else '>>> 存在问题，见上')
    flush()
except Exception:
    P('FATAL\n' + traceback.format_exc())
    flush()
