# -*- coding: utf-8 -*-
"""X-print 材质方案 v14 —— 在 FreeCAD 1.1 中为全部零件确定并设置材质。

用户口径（2026-11-10）：**异型结构件采用 PETG 材质 3D 打印**。

FreeCAD 1.1 使用新的材质系统：
  * Part::Feature.ShapeMaterial 的类型是 Materials::PropertyMaterial；
  * FCStd 的 Document.xml 只保存 <PropertyMaterial uuid="..."/>，
    材质实体必须存在于 System / User 材质库，否则重开文档会回落到 Default；
  * 视图颜色由材质的 AppearanceModels/BasicRendering/DiffuseColor 驱动，
    赋值时会自动同步 ViewObject.ShapeColor。

因此本脚本做三件事：
  1. 生成 21 种项目材质的 .FCMat（YAML），同时写入
     - refs/materials/                 （随项目版本控制，可复现）
     - <UserAppData>/Material/X-Print/ （FreeCAD 用户材质库，供 UUID 解析）
     UUID 由 uuid5 固定，重复运行结果稳定；
  2. 为 139 个 Part::Feature 逐一赋 ShapeMaterial、显式设视图颜色，
     并新增 MaterialSpec 字符串属性把材质名/工艺写进 FCStd 本体；
  3. d.recompute() + d.save()，导出几何快照与材质对照表供验证。

不改任何几何、不增删文档对象、不覆盖已有 MaterialNote / SpecNote / DesignFreeze。

运行方式（必须在已打开 CrossSlide_P014013 的 FreeCAD GUI 会话里）：
    exec(compile(open(r'C:/ink/refs/scripts/apply_materials.py', encoding='utf-8').read(),
                 r'C:/ink/refs/scripts/apply_materials.py', 'exec'), {'__name__': '__main__'})
"""

import os
import sys
import csv
import json
import uuid
import traceback

import FreeCAD as App
import Materials

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# --------------------------------------------------------------------------
# FreeCAD 1.1 内置模型 UUID
# --------------------------------------------------------------------------
MODEL_DENSITY = '454661e5-265b-4320-8e6f-fcf6223ac3af'   # Density
MODEL_ELASTIC = '7b561d1d-fb9b-44f6-9da9-56a4f74d7536'   # Linear Elastic
MODEL_RENDER = 'f006c7e4-35b7-43d5-bbf9-c5d572309e6e'    # Basic Rendering
UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/csgotom100/X-print/materials')

LOG_LINES = []


def P(*args):
    s = ' '.join(str(x) for x in args)
    LOG_LINES.append(s)
    try:
        print(s)
    except Exception:
        pass


# --------------------------------------------------------------------------
# 材质表：name = FCMat 文件名/FreeCAD 显示名；density = kg/m^3
# youngs = MPa；poisson = 泊松比；color = DiffuseColor
# 弹性体 / 皮带 / 外购总成不虚构力学参数，只给密度与外观。
# --------------------------------------------------------------------------
MATERIALS = {
    'PETG': dict(
        name='PETG-FDM 异型结构件', density=1270, youngs=2100, poisson=0.38,
        color=(0.20, 0.55, 0.80), shininess=0.30,
        note='FDM 3D 打印：0.4 喷嘴 / 层高 0.20 / 4 周壁 / 40% 网格填充 / 240C 喷嘴 / 80C 热床；'
             '承力方向避免层间受拉；端板沉孔局部加厚 2 mm、凸台 3 mm、螺纹孔壁厚 >=2 mm'),
    'AL6061': dict(
        name='6061-T6 铝合金板', density=2700, youngs=69000, poisson=0.33,
        color=(0.68, 0.71, 0.74), shininess=0.60,
        note='XZ 连接板：15 mm 铝板 CNC 铣削 / 阳极氧化'),
    'AL6063': dict(
        name='6063-T5 铝型材2040', density=2700, youngs=69000, poisson=0.33,
        color=(0.78, 0.80, 0.82), shininess=0.60,
        note='2040 工业铝型材，挤压型材锯切，端面攻 M6 芯孔'),
    'AL_PULLEY': dict(
        name='铝合金GT2同步轮', density=2700, youngs=69000, poisson=0.33,
        color=(0.72, 0.74, 0.77), shininess=0.65,
        note='GT2 16T 同步轮，铝合金阳极氧化外购件'),
    'STEEL_FASTENER': dict(
        name='8.8级碳钢紧固件', density=7850, youngs=210000, poisson=0.30,
        color=(0.32, 0.34, 0.38), shininess=0.55,
        note='SHCS 内六角螺钉 / 螺母 / 垫圈 / T 型锤头螺母 / 限位螺钉，8.8 级碳钢镀锌外购'),
    'STEEL_ROD': dict(
        name='GCr15淬硬导杆与轴', density=7830, youngs=210000, poisson=0.30,
        color=(0.60, 0.63, 0.66), shininess=0.70,
        note='D5 直线导杆与电机轴，GCr15/45# 钢淬硬磨光，表面镀硬铬'),
    'BEARING': dict(
        name='GCr15直线轴承LM5UU', density=7830, youngs=210000, poisson=0.30,
        color=(0.48, 0.51, 0.55), shininess=0.70,
        note='LM5UU D10x15 直线轴承总成，轴承钢外购件'),
    'BRASS': dict(
        name='黄铜热熔螺母与针套', density=8500, youngs=100000, poisson=0.34,
        color=(0.82, 0.64, 0.26), shininess=0.65,
        note='M3 热熔铜嵌件 / R125 针套 / P125 探针管身，黄铜车削镀镍或镀金'),
    'SPRING_STEEL': dict(
        name='琴钢丝与不锈钢弹片', density=7900, youngs=210000, poisson=0.30,
        color=(0.70, 0.72, 0.75), shininess=0.70,
        note='探针回位弹簧 D0.3 琴钢丝 12 圈 / 保湿站压紧弹片，两端并紧磨平'),
    'PU_BELT': dict(
        name='PU玻纤GT2同步带', density=1200,
        color=(0.12, 0.12, 0.14), shininess=0.15,
        note='GT2-6 开口同步带及夹持键（同材质皮带裁段），聚氨酯 + 玻纤芯'),
    'MOTOR': dict(
        name='NEMA17步进电机总成', density=4500,
        color=(0.24, 0.27, 0.34), shininess=0.50,
        note='42x42x40 双极步进电机，钢/铜/磁体复合外购总成，密度为等效估值'),
    'SWITCH': dict(
        name='机械式限位开关', density=1400,
        color=(0.15, 0.16, 0.18), shininess=0.25,
        note='19.80 本体机械微动开关，PA66 壳 + 铜触点外购件'),
    'ABS_CARTRIDGE': dict(
        name='HP45墨盒ABS-PP壳体', density=1050, youngs=2200, poisson=0.35,
        color=(0.18, 0.20, 0.23), shininess=0.30,
        note='HP45 原装墨盒（第三方 STEP 参考体），ABS/PP 壳体 + 喷嘴硅片'),
    'POM': dict(
        name='POM注塑探针座与侧盖板', density=1410, youngs=2800, poisson=0.35,
        color=(0.91, 0.88, 0.79), shininess=0.35,
        note='v13 注塑件：探针座 + -X 侧盖板；1.5 deg 拔模 / R0.4 / 名义壁厚 2.0；'
             '原型试制可用 PETG FDM 或 CNC POM，量产口径为 POM / PA66'),
    'PA66GF30': dict(
        name='PA66-GF30注塑探针臂', density=1360, youngs=6000, poisson=0.35,
        color=(0.34, 0.42, 0.51), shininess=0.30,
        note='v13 注塑件：顶板三处减重腔（体积 -13.6%）；PA66+GF30 或 PC/ABS；'
             '原型试制可用 PETG FDM，量产口径为注塑'),
    'NDFEB': dict(
        name='N35钕铁硼镀镍磁环', density=7500, youngs=160000, poisson=0.24,
        color=(0.80, 0.82, 0.85), shininess=0.75,
        note='D6 / 内孔 D2.10 x 2.00 N35 镀镍，轴向（厚度）充磁；'
             '逐只筛选内孔 >=2.08 / 外径 <=6.10 / 厚度 <=2.00'),
    'FR4': dict(
        name='FR-4霍尔PCB与盖板', density=1850, youngs=22000, poisson=0.15,
        color=(0.16, 0.48, 0.28), shininess=0.35,
        note='0.6 mm 霍尔转接 PCB / 0.3 mm 霍尔盖板（FR-4 或铝片），环氧封边'),
    'EPOXY_IC': dict(
        name='A1324霍尔环氧封装', density=1500,
        color=(0.10, 0.10, 0.12), shininess=0.30,
        note='A1324 线性霍尔（5 mV/G），环氧封装 TO-92 类外购件'),
    'SILICONE': dict(
        name='硅胶TPU密封与护线', density=1150,
        color=(0.92, 0.55, 0.24), shininess=0.20,
        note='防尘唇（毛毡或邵氏 A30 硅胶）/ 护线套（硅胶或 TPU A50）/ 保湿站密封圈'),
    'SPONGE': dict(
        name='保湿海绵', density=100,
        color=(0.93, 0.86, 0.62), shininess=0.10,
        note='保湿站吸墨海绵，开孔聚氨酯泡棉'),
    'AUX': dict(
        name='工艺辅助几何非零件', density=1000,
        color=(0.85, 0.85, 0.85), shininess=0.10, transparency=65,
        note='M3 攻丝孔建模辅助体，仅表示工艺孔位，不是实体零件；半透明显示'),
}

# --------------------------------------------------------------------------
# 对象 -> 材质：显式清单优先，再按命名规则归类
# --------------------------------------------------------------------------
EXACT = {
    # 3D 打印异型结构件（用户 2026-11-10 口径：PETG）
    'Z_BaseBlock': 'PETG',
    'HP45_CarriageAdapter': 'PETG',
    'Cap_Tray': 'PETG',
    # 机加工铝板 / 型材
    'XZ_Plate': 'AL6061',
    # HP45 参考墨盒
    'HP45_Real': 'ABS_CARTRIDGE',
    # v13 注塑三主件（量产材质不变，原型可 PETG 打印）
    'HP45_ProbeHousing': 'POM',
    'HP45_SpringSpacer': 'POM',
    'HP45_ProbeArm': 'PA66GF30',
    # 探针内部功能件
    'HP45_PogoPin': 'BRASS',
    'HP45_SocketR125': 'BRASS',
    'HP45_PogoMagnet': 'NDFEB',
    'HP45_PogoSpring': 'SPRING_STEEL',
    'HP45_HallSensor': 'EPOXY_IC',
    'HP45_HallPCB': 'FR4',
    'HP45_HallCover': 'FR4',
    'HP45_DustSeal': 'SILICONE',
    'HP45_CableClamp': 'SILICONE',
    'Cap_Spring': 'SPRING_STEEL',
    'Cap_Seal': 'SILICONE',
    'Cap_Sponge': 'SPONGE',
}

RULES = [
    (lambda n: n.endswith('_tap'), 'AUX'),
    (lambda n: 'LimitSwitch' in n, 'SWITCH'),
    (lambda n: 'Insert_Car' in n, 'BRASS'),
    (lambda n: n.startswith('HP45CAR_'), 'PETG'),
    (lambda n: 'Carriage_' in n or 'EndPlate' in n, 'PETG'),
    (lambda n: n.endswith('Profile'), 'AL6063'),
    (lambda n: 'Pulley' in n, 'AL_PULLEY'),
    (lambda n: 'GuideRod' in n or 'Motor_Shaft' in n, 'STEEL_ROD'),
    (lambda n: 'LM5UU' in n, 'BEARING'),
    (lambda n: 'Motor_NEMA' in n, 'MOTOR'),
    (lambda n: 'Belt' in n or 'Clamp_Key' in n, 'PU_BELT'),
    (lambda n: ('Screw' in n or 'Washer' in n or 'TNut' in n or
                'Nut_Idler' in n or n.startswith('Plate_M') or
                'fix_screw' in n), 'STEEL_FASTENER'),
]


def classify(name):
    if name in EXACT:
        return EXACT[name]
    for pred, key in RULES:
        if pred(name):
            return key
    raise KeyError('未归类的零件: ' + name)


# --------------------------------------------------------------------------
# FCMat 生成
# --------------------------------------------------------------------------
def material_uuid(key):
    return str(uuid.uuid5(UUID_NAMESPACE, key))


def fcmat_text(key, d):
    uid = material_uuid(key)
    r, g, b = d['color']
    amb = tuple(round(v * 0.50, 4) for v in (r, g, b))
    spec = d.get('specular', (0.35, 0.35, 0.35))
    sh = d.get('shininess', 0.30)
    tr = d.get('transparency', 0)
    L = [
        '---',
        'General:',
        '  UUID: "%s"' % uid,
        '  Name: "%s"' % d['name'],
        '  Author: "X-print"',
        '  License: "CC0-1.0"',
        '  Description: "%s"' % d['note'].replace('"', "'"),
        'Models:',
        '  Density:',
        "    UUID: '%s'" % MODEL_DENSITY,
        '    Density: "%d kg/m^3"' % d['density'],
    ]
    if 'youngs' in d or 'poisson' in d:
        L += ['  LinearElastic:', "    UUID: '%s'" % MODEL_ELASTIC]
        if 'youngs' in d:
            L += ['    YoungsModulus: "%d MPa"' % d['youngs']]
        if 'poisson' in d:
            L += ['    PoissonRatio: "%s"' % d['poisson']]
    L += [
        'AppearanceModels:',
        '  BasicRendering:',
        "    UUID: '%s'" % MODEL_RENDER,
        '    AmbientColor: "(%s, 1)"' % ', '.join('%.4f' % v for v in amb),
        '    DiffuseColor: "(%.2f, %.2f, %.2f, 1)"' % (r, g, b),
        '    EmissiveColor: "(0, 0, 0, 1)"',
        '    SpecularColor: "(%s, 1)"' % ', '.join('%.2f' % v for v in spec),
        '    Shininess: "%.2f"' % sh,
        '    Transparency: "%d"' % tr,
        '',
    ]
    return uid, '\n'.join(L)


def ensure_libraries(root):
    proj = os.path.join(root, 'refs', 'materials')
    user = os.path.join(App.getUserAppDataDir(), 'Material', 'X-Print')
    os.makedirs(proj, exist_ok=True)
    os.makedirs(user, exist_ok=True)
    for key, d in MATERIALS.items():
        uid, text = fcmat_text(key, d)
        fn = d['name'] + '.FCMat'
        for base in (proj, user):
            with open(os.path.join(base, fn), 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
    P('材质库文件: 项目 %s / 用户 %s，共 %d 种' % (proj, user, len(MATERIALS)))
    mm = Materials.MaterialManager()
    mm.refresh()
    for key in MATERIALS:
        m = mm.getMaterial(material_uuid(key))
        if m is None:
            raise RuntimeError('材质未注册: ' + key)
    P('MaterialManager.refresh() OK，全部 UUID 可解析')
    return mm, proj, user


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
def geometry_snapshot(doc):
    snap = {}
    for o in doc.Objects:
        if o.TypeId != 'Part::Feature':
            continue
        s = o.Shape
        bb = s.BoundBox
        snap[o.Name] = dict(
            volume=round(s.Volume, 6),
            bbox=[round(v, 6) for v in (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)],
            faces=len(s.Faces), solids=len(s.Solids), valid=s.isValid())
    return snap


def main():
    doc = App.ActiveDocument
    if doc is None or not doc.FileName:
        raise RuntimeError('请先在 FreeCAD GUI 中打开 CrossSlide_P014013.FCStd')
    root = os.path.dirname(doc.FileName)
    tmp = os.path.join(root, 'refs', 'tmp')
    os.makedirs(tmp, exist_ok=True)
    P('文档:', doc.Name, doc.FileName)
    P('FreeCAD:', App.Version()[0:3])

    parts = [o for o in doc.Objects if o.TypeId == 'Part::Feature']
    P('Part::Feature 数量:', len(parts), '文档对象总数:', len(doc.Objects))

    # 1) 归类自检：必须 100% 覆盖且无重复
    mapping = {}
    for o in parts:
        mapping[o.Name] = classify(o.Name)
    unknown = [n for n, k in mapping.items() if k not in MATERIALS]
    if unknown:
        raise RuntimeError('材质键不存在: ' + str(unknown))
    P('归类完成，未归类零件 = 0')

    # 2) 几何快照（验证材质设置未改动几何）
    before = geometry_snapshot(doc)
    for fp in (os.path.join(tmp, 'geometry_before_materials.json'),
               os.path.join(root, 'refs', 'materials', 'geometry_snapshot_v14.json')):
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(before, f, ensure_ascii=False, indent=1)

    # 3) 生成并注册材质库
    mm, proj, user = ensure_libraries(root)

    # 4) 逐件赋材质
    counts = {}
    rows = []
    for o in parts:
        key = mapping[o.Name]
        d = MATERIALS[key]
        m = mm.getMaterial(material_uuid(key))
        o.ShapeMaterial = m
        o.ViewObject.ShapeColor = tuple(d['color'])
        if key == 'AUX':
            o.ViewObject.Transparency = d.get('transparency', 0)
        if 'MaterialSpec' not in o.PropertiesList:
            o.addProperty('App::PropertyString', 'MaterialSpec', 'X-Print Material',
                          'v14 材质方案标记（材质名 | 工艺说明）')
        o.MaterialSpec = d['name'] + ' | ' + d['note']
        counts[key] = counts.get(key, 0) + 1
        rows.append([o.Name, o.Label, key, d['name'], d['density'], d['note']])

    # 5) 校验读回
    bad = []
    for o in parts:
        k = mapping[o.Name]
        sm = o.ShapeMaterial
        if sm is None or sm.Name != MATERIALS[k]['name']:
            bad.append((o.Name, repr(sm.Name) if sm else 'None'))
        if getattr(o, 'MaterialSpec', '') == '':
            bad.append((o.Name, 'MaterialSpec empty'))
    if bad:
        raise RuntimeError('材质读回不一致: ' + str(bad[:10]))
    P('逐件读回校验 OK：139 件 ShapeMaterial.Name / MaterialSpec 全部一致')

    after = geometry_snapshot(doc)
    if before != after:
        diff = [n for n in before if before[n] != after.get(n)]
        raise RuntimeError('几何在赋材质过程中发生变化: ' + str(diff[:10]))
    P('几何快照比对 OK：体积 / BBox / 面数 / 实体数 / isValid 全部未变')

    # 6) 报告
    csv_path = os.path.join(proj, 'material_assignments.csv')
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['对象名', 'Label', '材质键', '材质名', '密度 kg/m^3', '工艺说明'])
        w.writerows(rows)
    P('材质对照表:', csv_path)

    summary = os.path.join(proj, 'material_summary.json')
    with open(summary, 'w', encoding='utf-8') as f:
        json.dump(dict(
            version='v14', model='CrossSlide_P014013.FCStd',
            material_count=len(MATERIALS), part_count=len(parts),
            counts=counts,
            materials={k: dict(name=v['name'], density_kg_m3=v['density'],
                               youngs_MPa=v.get('youngs'), poisson=v.get('poisson'),
                               color=list(v['color']), note=v['note'],
                               uuid=material_uuid(k))
                       for k, v in MATERIALS.items()}), f, ensure_ascii=False, indent=2)

    doc.recompute()
    doc.save()
    P('d.save() 完成:', doc.FileName, os.path.getsize(doc.FileName), 'bytes')
    P('各材质件数:', json.dumps(counts, ensure_ascii=False, sort_keys=True))
    P('>>> v14 材质设置完成')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        P('FATAL\n' + traceback.format_exc())
        raise
    finally:
        try:
            root = os.path.dirname(App.ActiveDocument.FileName)
            path = os.path.join(root, 'refs', 'tmp', 'apply_materials.log')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(LOG_LINES) + '\n')
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass
