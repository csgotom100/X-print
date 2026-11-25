# -*- coding: utf-8 -*-
"""汇总 X-Z 十字滑台的几何、冻结项、干涉、参数和运动检查。"""
import json
from pathlib import Path

ROOT = Path('C:/ink')
TMP = ROOT / 'refs/tmp'


def load(name):
    return json.loads((TMP / name).read_text(encoding='utf-8'))


eval_d = load('cross_slide_xz_eval.json')
verify = load('15_cross_slide_xz_verify_results.json')
seat = load('18_cross_slide_param_seat_results.json')
frozen = load('19_cross_slide_param_frozen_results.json')
motion = load('17_cross_slide_motion_check_results.json')
mech = load('16_cross_slide_mechanism_results.json')

bodies = {b['name']: b for b in eval_d['bodies']}
timeline = eval_d['timeline']
inter = verify[2]
params = verify[3]
joint_list = motion[6]

checks = []


def chk(name, ok, detail):
    checks.append({'name': name, 'pass': bool(ok), 'detail': detail})


chk('body_count=18', eval_d.get('body_count') == 18, eval_d.get('body_count'))
chk('all_bodies_closed', all(b.get('closed') for b in bodies.values()),
    [n for n, b in bodies.items() if not b.get('closed')])
chk('timeline_errors=0', sum(1 for t in timeline if t.get('error')) == 0,
    {'errors': sum(1 for t in timeline if t.get('error')),
     'warnings': sum(1 for t in timeline if t.get('warning'))})

targets = {
    'X_Profile': (60561.587, 346),
    'Z_Profile': (45421.190, 346),
}
profile_detail = {}
for n, (target_v, target_f) in targets.items():
    b = bodies[n]
    err = (b['volume_mm3'] - target_v) / target_v * 100.0
    profile_detail[n] = {
        'volume_mm3': round(b['volume_mm3'], 6),
        'target_mm3': target_v,
        'error_pct': round(err, 6),
        'faces': b['faces'],
        'target_faces': target_f,
        'shells': b.get('kernel', {}).get('shells'),
    }
chk('profile_volume_fidelity', all(abs(v['error_pct']) < 0.01 for v in profile_detail.values()),
    profile_detail)
chk('profile_face_count', all(v['faces'] == v['target_faces'] for v in profile_detail.values()),
    profile_detail)

chk('Z_slot_width_22', abs(verify[0]['distance_mm'] - 22.0) < 1e-6,
    verify[0]['distance_mm'])
chk('X_pocket_width_20_8', abs(verify[1]['distance_mm'] - 20.8) < 1e-4,
    verify[1]['distance_mm'])
chk('interference_zero',
    inter['count'] == 0 and inter['checked'] == 18 and
    inter['pairs_not_checked'] == 0 and not inter['budget_exceeded'],
    {k: inter[k] for k in ('count', 'checked', 'pairs_not_checked', 'budget_exceeded',
                           'pairs_candidate', 'pairs_intersected')})
chk('parameters_cycles_errors_zero',
    params.get('cycles') == [] and
    all(p.get('error') is None for p in params.get('parameters', [])),
    {'count': params.get('count'), 'cycles': params.get('cycles'),
     'errors': [p.get('error') for p in params.get('parameters', []) if p.get('error')]})

seat_before = {b['name']: b['volume_mm3'] for b in seat[0]['bodies']}
seat_after = {b['name']: b['volume_mm3'] for b in seat[2]['bodies']}
chk('param_SEAT_R_linkage',
    seat[1]['errors'] == [] and
    abs(seat_before['X_Carriage_Lower'] - 13569.202) < 0.01 and
    abs(seat_after['X_Carriage_Lower'] - 13344.825) < 0.01,
    {'6.05mm': round(seat_before['X_Carriage_Lower'], 3),
     '6.35mm': round(seat_after['X_Carriage_Lower'], 3),
     'recomputed': seat[1]['recomputed']})
chk('param_Z_SLOT_W_linkage',
    frozen[1]['errors'] == [] and abs(frozen[3]['distance_mm'] - 24.0) < 1e-6 and
    abs(frozen[0]['bodies'][0]['volume_mm3'] - 35532.048) < 0.01 and
    abs(frozen[2]['bodies'][0]['volume_mm3'] - 35225.097) < 0.01,
    {'22mm': round(frozen[0]['bodies'][0]['volume_mm3'], 3),
     '24mm': round(frozen[2]['bodies'][0]['volume_mm3'], 3),
     'measured_slot': frozen[3]['distance_mm']})

chk('joints_no_conflicts',
    joint_list['conflicts'] == [] and joint_list['errors'] == [] and
    joint_list['floating'] == [],
    {'joints': [j['name'] for j in joint_list['joints']],
     'fixed': joint_list['fixed'],
     'dof': joint_list['dof']})
chk('motion_X_plus20',
    motion[2]['moved'] and motion[2]['values'][0]['value'] == 20.0,
    {'requested': motion[2]['requested'], 'values': motion[2]['values']})
chk('motion_Z_plus15',
    motion[3]['moved'] and motion[3]['values'][0]['value'] == 15.0,
    {'requested': motion[3]['requested'], 'values': motion[3]['values']})

# Z 滑车在 X 驱动 +20 和 Z 驱动 +15 后，整体应平移 (+20, 0, +15)。
def com(body_list, name):
    return next(b['center_of_mass'] for b in body_list if b['name'] == name)

b0 = com(motion[1]['bodies'], 'Z_LM6UU_1')
b1 = com(motion[5]['bodies'], 'Z_LM6UU_1')
delta = [round(b1[i] - b0[i], 6) for i in range(3)]
chk('motion_com_translation', all(abs(delta[i] - expected) < 1e-4
                                  for i, expected in enumerate((20.0, 0.0, 15.0))),
    {'delta': delta, 'expected': [20.0, 0.0, 15.0]})

structural_ref = {
    'X_EndPlate_L': 19096.771, 'X_EndPlate_R': 20869.194,
    'Z_EndPlate_L': 41521.447, 'Z_EndPlate_R': 23059.448,
    'X_Carriage_Lower': 13295.278, 'X_Carriage_Upper': 12457.113,
    'Z_Carriage_Lower': 13295.278, 'Z_Carriage_Upper': 20503.537,
}
fidelity = {}
for n, ref in structural_ref.items():
    cur = bodies[n]['volume_mm3']
    fidelity[n] = {'current_mm3': round(cur, 3), 'original_mm3': ref,
                   'error_pct': round((cur - ref) / ref * 100.0, 3)}

out = {
    'project': 'X-Z 十字滑台',
    'designs': {
        'static': 'solidcraft/CrossSlide_XZ.sc',
        'mechanism': 'solidcraft/CrossSlide_XZ_mech.sc',
    },
    'build': {
        'commands': len(json.loads((ROOT / 'solidcraft/14_cross_slide_xz.json').read_text(encoding='utf-8'))['commands']),
        'user_parameters': params.get('count'),
        'timeline_features': len(timeline),
        'transform_scripts': len(json.loads((ROOT / 'solidcraft/16_cross_slide_mechanism.json').read_text(encoding='utf-8'))['commands']),
    },
    'bodies': {n: {'volume_mm3': round(b['volume_mm3'], 3), 'faces': b['faces'],
                   'closed': b['closed'], 'bbox': b['bbox']} for n, b in bodies.items()},
    'profile_fidelity': profile_detail,
    'structural_volume_deviation_informational': fidelity,
    'checks': checks,
    'failed': [c['name'] for c in checks if not c['pass']],
    'warnings': [{'feature': t['name'], 'message': t['warning']}
                 for t in timeline if t.get('warning')],
    'conclusion': 'PASS' if all(c['pass'] for c in checks) else 'FAIL',
}
out_path = TMP / 'cross_slide_xz_verify_summary.json'
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
print('SUMMARY', out_path)
print('CONCLUSION', out['conclusion'], 'failed', out['failed'])
for c in checks:
    print(('PASS ' if c['pass'] else 'FAIL '), c['name'])
