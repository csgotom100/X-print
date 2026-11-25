# -*- coding: utf-8 -*-
"""按用户给的 2040 铝型材横截面图，用真实 BREP 曲线精确重建 2 根型材。

用户 2026-11-13：「铝型材的横截面是这样的」「按我给的横截面图重新设计」。
上一版 4 槽语义化近似（填充率 47.4%、体积 +25.1%）被否定；旧版
build_profile_exact.py 又把两个 Ø5 圆孔误写成退化缝隙。本版直接从
refs/tmp/profile_contours.json 取有序 BREP 几何：

  wire0 外轮廓 : 286 条 Line + 4 条 R1.5 圆弧，面积 491.272842 mm²
  wire1 圆孔   : Ø5，面积 19.634954 mm²
  wire2 中心腔 : 52 条 Line，面积 149.195000 mm²
  wire3 圆孔   : Ø5，面积 19.634954 mm²
  净截面积     : 302.807934 mm²，填充率 37.851%

建模路线（全 SolidCraft 原生、零 STEP）：
  parameters.add
  → sketch.create
  → sketch.line（连续直线段分组）+ sketch.arc.three_point（4 个真实圆角）
  → sketch.line（中心腔闭合轮廓）+ sketch.circle.center ×2（真实圆孔）
  → sketch.finish → solid.extrude
  → appearance.assign → file.save

型材是项目冻结的标准件（用户明确「铝型材不变」），故截面曲线与孔位按
BREP 固定；长度和 Ø5 孔半径由命名参数驱动，草图本身仍可编辑。端板 /
滑车才是后续全参数化重建的对象。

目标体积：X 60561.587 / Z 45421.190 mm³（原始），误差 < 0.1%。
"""
import csv
import hashlib
import json
import math
import os
import sys

ROOT = 'C:/ink'
SRC = ROOT + '/refs/tmp/profile_contours.json'
OUT_JSON = ROOT + '/solidcraft/13_profile_exact.json'
OUT_CSV = ROOT + '/solidcraft/LM6UU_PROFILE_EXACT_PARAMS.csv'
OUT_SC = ROOT + '/solidcraft/LM6UU_Profile_Exact.sc'
USER_SC = 'D:/mydocuments/SolidCraft/LM6UU_Profile_Exact.sc'

data = json.load(open(SRC, encoding='utf-8'))
cmds = []


def add(cmd, **kw):
    cmds.append({'command': cmd, 'params': kw})


PARAMS = [
    ('PW',           '20 mm',   'X 型材截面宽（2040 的 20）'),
    ('PH',           '40 mm',   'X 型材截面高（2040 的 40）'),
    ('PWZ',          '40 mm',   'Z 型材截面宽（旋转 90°）'),
    ('PHZ',          '20 mm',   'Z 型材截面深（旋转 90°）'),
    ('PROF_HOLE_R',  '2.5 mm',  '2040 型材两个中心孔半径（Ø5）'),
    ('X_PROF_Y0',    '-57 mm',  'X 型材 Y 起点'),
    ('X_PROF_Z0',    '117 mm',  'X 型材 Z 起点'),
    ('X_PROF_LEN',   '200 mm',  'X 型材长度'),
    ('Z_PROF_X0',    '130 mm',  'Z 型材 X 起点'),
    ('Z_PROF_Y0',    '-1 mm',   'Z 型材 Y 起点'),
    ('Z_PROF_LEN',   '150 mm',  'Z 型材长度'),
]
for n, e, c in PARAMS:
    add('parameters.add', name=n, expression=e, comment=c)


def pt(p):
    return [round(float(p[0]), 6), round(float(p[1]), 6)]


def close2(a, b, tol=1e-6):
    return math.hypot(float(a[0]) - float(b[0]),
                      float(a[1]) - float(b[1])) < tol


def draw_chain(wire):
    """把有序 line/arc 基元画成一个闭合轮廓，保留圆弧为真实圆弧。

    连续 line 合并为一条 sketch.line，减少特征数；圆弧用
    sketch.arc.three_point 的 BREP 中点保证 1:1 复刻。端点由 sketch 的
    connect 默认行为自动重合，最后一个直线组显式走回轮廓起点。
    """
    prims = wire['primitives']
    start = pt(wire['start'])
    assert prims and close2(prims[0]['start'], start)
    assert close2(prims[-1]['end'], start), 'chain must be closed'

    line_pts = []
    has_arc = any(p['type'] == 'arc' for p in prims)

    def flush(final=False):
        nonlocal line_pts
        if not line_pts:
            return
        pts = [pt(x) for x in line_pts]
        if final and not close2(pts[-1], start):
            pts.append(start)
        if not has_arc and len(pts) > 2 and close2(pts[0], pts[-1]):
            # 纯直线闭合腔：用 closed=True 明确闭合，避免依赖点吸附。
            add('sketch.line', points=pts[:-1], closed=True,
                connect=True, infer=False)
        else:
            add('sketch.line', points=pts, closed=False,
                connect=True, infer=False)
        line_pts = []

    for i, p in enumerate(prims):
        if p['type'] == 'line':
            if not line_pts:
                line_pts.append(p['start'])
            line_pts.append(p['end'])
        elif p['type'] == 'arc':
            flush()
            add('sketch.arc.three_point',
                start=pt(p['start']),
                end=pt(p['end']),
                through=pt(p['through']),
                connect=True)
        else:
            raise RuntimeError('unknown primitive %s' % p['type'])
    flush(final=True)


def circle_expr(name, idx):
    """两个 Ø5 圆孔中心用命名参数表达，便于后续改 2040 规格时联动。"""
    if name == 'X_Profile':
        u = 'X_PROF_Y0 + PW / 2'
        v = 'X_PROF_Z0 + PH / 4' if idx == 0 else 'X_PROF_Z0 + 3 * PH / 4'
    else:
        u = 'Z_PROF_X0 + PWZ / 4' if idx == 0 else 'Z_PROF_X0 + 3 * PWZ / 4'
        v = 'Z_PROF_Y0 + PHZ / 2'
    return [u, v]


def build(name, plane, length):
    prof = data['profiles'][name]
    assert abs(prof['rebuilt_area'] - prof['face_area']) < 1e-4, name
    wires = prof['wires']
    assert len(wires) == 4, name
    assert wires[0]['kind'] == 'chain' and wires[0]['role'] == 'outer'
    assert wires[1]['kind'] == 'circle'
    assert wires[2]['kind'] == 'chain' and wires[2]['role'] == 'hole'
    assert wires[3]['kind'] == 'circle'
    assert abs(wires[0]['area_abs'] - 491.272842) < 1e-4
    assert abs(wires[2]['area_abs'] - 149.195000) < 1e-4
    assert all(abs(w['radius'] - 2.5) < 1e-6 for w in (wires[1], wires[3]))

    add('sketch.create', plane=plane)
    draw_chain(wires[0])       # 外轮廓：286 直线 + 4 圆弧
    draw_chain(wires[2])       # 中心异型腔
    add('sketch.circle.center', center=circle_expr(name, 0),
        radius='PROF_HOLE_R', connect=True)
    add('sketch.circle.center', center=circle_expr(name, 1),
        radius='PROF_HOLE_R', connect=True)
    add('sketch.finish')
    add('solid.extrude', distance=length, operation='new', body_name=name)


# X 型材：截面在 YZ（草图局部 u=Y, v=Z），沿 +X 拉伸
build('X_Profile',
      {'origin': [50, 0, 0], 'x_dir': [0, 1, 0], 'y_dir': [0, 0, 1]},
      'X_PROF_LEN')

# Z 型材：截面在 XY（草图局部 u=X, v=Y），沿 +Z 拉伸
build('Z_Profile',
      {'origin': [0, 0, 62], 'x_dir': [1, 0, 0], 'y_dir': [0, 1, 0]},
      'Z_PROF_LEN')

add('appearance.assign',
    bodies=['X_Profile', 'Z_Profile'],
    color='#b0b7bf', name='2040 铝型材 / 真实 BREP 截面',
    pbr={'metallic': 0.75, 'roughness': 0.35, 'dielectric_ior': 1.5})
add('file.save', path=OUT_SC)

os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
with open(OUT_JSON, 'w', encoding='utf-8') as f:
    json.dump({'commands': cmds}, f, ensure_ascii=False, indent=1)
with open(OUT_CSV, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['name', 'expression', 'comment'])
    w.writerows(PARAMS)
print('WROTE', OUT_JSON)
print('WROTE', OUT_CSV)
print('commands', len(cmds), 'params', len(PARAMS))
for name, prof in data['profiles'].items():
    print(name, 'BREP area', prof['face_area'],
          'rebuilt', prof['rebuilt_area'],
          'target volume', round(prof['face_area'] *
                                 (200 if name == 'X_Profile' else 150), 3))
print('design', OUT_SC)
print('user copy', USER_SC)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def verify():
    """几何保真度验证：不看命令是否成功，直接比对 BREP 目标值。"""
    run = json.load(open(ROOT + '/refs/tmp/13_profile_exact_results.json',
                         encoding='utf-8'))
    ev = json.load(open(ROOT + '/refs/tmp/profile_exact_eval.json',
                        encoding='utf-8'))
    bodies = {b['name']: b for b in ev['bodies']}
    checks = []

    def ck(name, ok, detail):
        checks.append({'name': name, 'ok': bool(ok), 'detail': detail})

    ck('commands', len(run) == len(cmds),
       '%d / %d' % (len(run), len(cmds)))
    ck('command_errors', not any(isinstance(x, dict) and x.get('error')
                                 for x in run), '0 errors')
    ck('command_warnings', not any(isinstance(x, dict) and x.get('warning')
                                   for x in run), '0 warnings')
    ck('body_count', ev['body_count'] == 2, ev['body_count'])
    ck('open_bodies', ev['total']['open_bodies_skipped'] == 0,
       ev['total']['open_bodies_skipped'])
    ck('sketches_solved',
       all(s['status'] == 'solved' and s['profiles'] == 4
           for s in ev['sketches']),
       [(s['name'], s['status'], s['profiles']) for s in ev['sketches']])
    ck('timeline_errors',
       not any(t.get('error') or t.get('warning') for t in ev['timeline']),
       len(ev['timeline']))
    ck('parameter_errors',
       not any(p.get('error') for p in ev['params']) and
       not ev.get('cycles'), '%d params' % len(ev['params']))

    targets = {
        'X_Profile': {
            'volume': 60561.58668365398, 'length': 200.0,
            'bbox': ([50.0, -57.0, 117.0], [250.0, -37.0, 157.0]),
        },
        'Z_Profile': {
            'volume': 45421.19001274048, 'length': 150.0,
            'bbox': ([130.0, -1.0, 62.0], [170.0, 19.0, 212.0]),
        },
    }
    target_area = 302.8079334182873
    for name, t in targets.items():
        b = bodies[name]
        err = 100.0 * (b['volume_mm3'] / t['volume'] - 1.0)
        area = b['volume_mm3'] / t['length']
        ck(name + '_closed', b['closed'] is True, b['closed'])
        ck(name + '_single_shell', b['kernel']['shells'] == 1,
           b['kernel']['shells'])
        ck(name + '_faces_346', b['faces'] == 346, b['faces'])
        ck(name + '_face_types',
           b['face_types'].get('plane') == 340 and
           b['face_types'].get('cylinder') == 6, b['face_types'])
        ck(name + '_volume_err_lt_0.01pct', abs(err) < 0.01,
           '%+.6f %%' % err)
        ck(name + '_section_area', abs(area - target_area) < 0.01,
           '%.6f mm2' % area)
        got_min = [b['bbox']['min'][i] for i in range(3)]
        got_max = [b['bbox']['max'][i] for i in range(3)]
        ok_bb = all(abs(got_min[i] - t['bbox'][0][i]) < 1e-3 and
                    abs(got_max[i] - t['bbox'][1][i]) < 1e-3
                    for i in range(3))
        ck(name + '_bbox', ok_bb, [got_min, got_max])

    ck('design_exists', os.path.isfile(OUT_SC), OUT_SC)
    ck('gui_copy_exists', os.path.isfile(USER_SC), USER_SC)
    ck('sha256_match',
       os.path.isfile(OUT_SC) and os.path.isfile(USER_SC) and
       sha256(OUT_SC) == sha256(USER_SC),
       sha256(OUT_SC) if os.path.isfile(OUT_SC) else 'missing')

    report = {
        'status': 'PASS' if all(c['ok'] for c in checks) else 'FAIL',
        'checks': checks,
        'design': OUT_SC,
        'gui_copy': USER_SC,
        'sha256': sha256(OUT_SC) if os.path.isfile(OUT_SC) else None,
        'bodies': {n: {'volume_mm3': b['volume_mm3'],
                       'faces': b['faces'],
                       'shells': b['kernel']['shells'],
                       'closed': b['closed']}
                   for n, b in bodies.items()},
    }
    out = ROOT + '/refs/tmp/profile_exact_verify.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print('VERIFY', report['status'], 'checks', len(checks),
          'failed', sum(not c['ok'] for c in checks), '->', out)
    for c in checks:
        if not c['ok']:
            print('  FAIL', c['name'], c['detail'])
    if report['status'] != 'PASS':
        sys.exit(1)


if '--verify' in sys.argv:
    verify()
