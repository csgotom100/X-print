# -*- coding: utf-8 -*-
"""
V2 grouped exploded view: pull apart *more* parts than v1.

v1 kept 40 Z-axis parts fused together as a single "ground" reference, so
the base, end plates, guide rods, GT2 drive, motor and limit switches were
never separated.  V2 splits those 40 into 5 functional sub-groups, keeps only
the 12-part base frame as the true fixed reference, and increases the
separation distances.  Result: 127 of 140 occurrences move (v1: 100).

The Z stepper motor is the one group that does NOT fan out: it translates
purely along +Y, i.e. along the axis of its four mounting screws, straight
out of its mounting seat.  (The screws' 13 mm long axis is Y; the motor body
is on the +Y side of the end plate, the shaft/pulley on the -Y side.)

Input : refs/tmp/sc_occ_map.json
Output: solidcraft/05_exploded_view_v2.json
        solidcraft/EXPLODED_GROUPS_V2.csv

Run with:
  python refs/scripts/build_exploded_view_v2.py
  solidcraft-cli run solidcraft/05_exploded_view_v2.json \
      --in <CrossSlide_P014013_motion.sc> --save <..._exploded_v2.sc> \
      --results --param-check warn
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "solidcraft"

occ_map = {int(k): v for k, v in json.loads(
    (ROOT / "refs/tmp/sc_occ_map.json").read_text(encoding="utf-8")).items()}
ROOT_OCC = 2
VIEW_NAME = "整机爆炸图 V2 / Assembly exploded V2"


def seq(stem, count):
    return {f"{stem}_{i}" for i in range(count)}


def rng(stem, lo, hi):
    return {f"{stem}_{i}" for i in range(lo, hi + 1)}


# --------------------------------------------------------------- fixed frame
# The only parts that stay put: the base block, the 2040 Z column and the
# screws that tie them to the bench. Everything else is exploded.
FRAME = {
    "Z_BaseBlock", "Z_Profile", "Z_rod_1_tap", "Z_rod_2_tap",
} | seq("Z_BaseScrew", 4) | seq("Bench_Screw", 4)

# --------------------------------------------------------------- Z sub-groups
Z_PLATES = {
    "Z_EndPlate_L", "Z_EndPlate_R",
    "Z_GuideRod_1", "Z_GuideRod_2",
    "Z_rod_fix_screw_1", "Z_rod_fix_screw_2",
    "Z_Screw_Core_0", "Z_Screw_Core_1",
}
Z_DRIVE = {
    "Z_Belt_GT2", "Z_Pulley_Drive", "Z_Pulley_Idler",
    "Z_Screw_Idler", "Z_Washer_Idler", "Z_Nut_Idler",
    "Z_Washer_Nut_Idler",
}
Z_MOTOR = {
    "Z_Motor_NEMA17", "Z_Motor_Shaft",
} | seq("Z_Screw_Motor", 4)
Z_LIMITS = {
    "Z_LimitSwitch_Bot", "Z_LimitSwitch_Top",
} | rng("LimitScrew", 1, 4)

# --------------------------------------------------------------- v1's 6 groups
Z_CAR = {
    "Z_Carriage_Lower", "Z_Carriage_Upper",
    "Z_Insert_Car_0", "Z_Insert_Car_1",
    "Z_Screw_Car_0", "Z_Screw_Car_1",
    "Z_Clamp_Key_A", "Z_Clamp_Key_B",
    "Z_LM5UU_1", "Z_LM5UU_2",
    "XZ_Plate",
} | seq("Plate_M3", 4) | seq("Plate_M5", 4) | seq("TNut_M5", 4)

X_FRAME = {
    "X_Profile", "X_EndPlate_L", "X_EndPlate_R",
    "X_Screw_Core_0", "X_Screw_Core_1",
    "X_GuideRod_1", "X_GuideRod_2",
    "X_Pulley_Drive", "X_Pulley_Idler",
    "X_Screw_Idler", "X_Washer_Idler", "X_Washer_Nut_Idler", "X_Nut_Idler",
    "X_Belt_GT2", "X_Motor_NEMA17", "X_Motor_Shaft",
    "X_rod_1_tap", "X_rod_2_tap",
    "X_rod_fix_screw_1", "X_rod_fix_screw_2",
    "X_LimitSwitch_L", "X_LimitSwitch_R",
} | seq("X_Screw_Motor", 4) | rng("LimitScrew", 5, 8)

X_CAR = {
    "X_Carriage_Lower", "X_Carriage_Upper",
    "X_Insert_Car_0", "X_Insert_Car_1",
    "X_Screw_Car_0", "X_Screw_Car_1",
    "X_Clamp_Key_A", "X_Clamp_Key_B",
    "X_LM5UU_1", "X_LM5UU_2",
}
HEAD = {
    "HP45_Real", "HP45CAR_P01", "HP45CAR_P03", "HP45CAR_P04",
    "HP45CAR_P02_R", "HP45CAR_P02_L",
    "HP45_CarriageAdapter", "HP45_ProbeArm",
    "HP45_ProbeScrew_0", "HP45_ProbeScrew_1",
} | seq("HP45_AdptScrew", 4) | seq("HP45_P01Screw", 4)
PROBE = {
    "HP45_ProbeHousing", "HP45_PogoPin", "HP45_PogoMagnet", "HP45_PogoSpring",
    "HP45_HallSensor", "HP45_HallPCB",
    "HP45_HousingScrew_0", "HP45_HousingScrew_1",
    "HP45_SocketR125", "HP45_DustSeal",
    "HP45_HallCover", "HP45_CableClamp", "HP45_SpringSpacer",
}
CAP = {
    "Cap_Spring", "Cap_Tray", "Cap_Seal", "Cap_Sponge",
    "Cap_BaseScrew_1", "Cap_BaseScrew_2",
}

# name -> (label, [dx, dy, dz] mm)
# Main build chain runs along -Y; Z-axis accessories fan out to +/-X and +Z
# so they no longer sit inside the frame silhouette.
#
# EXCEPTION - Z stepper motor: it must NOT fly off diagonally.  The four
# Z_Screw_Motor_* fasteners have bbox 5.49 x 13.00 x 5.48 mm, i.e. their long
# (mounting-screw) axis is Y.  The motor body sits at Y=-3..39, the shaft and
# drive pulley at Y=-18..-6 on the -Y (front) side of the end plate, so the
# motor withdraws from its mounting seat along that same axis toward +Y.
# Hence dx=dz=0, dy>0: a pure translation along the screw axis, straight out
# of the mounting position (shaft retracting from the end plate).
GROUPS = [
    ("Z 端板与导杆",       Z_PLATES, [  70.0,  -25.0,  30.0]),
    ("Z 同步带传动",       Z_DRIVE,  [ 120.0,  -75.0,  65.0]),
    ("Z 步进电机",         Z_MOTOR,  [   0.0,   80.0,   0.0]),
    ("Z 限位开关",         Z_LIMITS, [ 175.0, -170.0,  25.0]),
    ("Z 滑车 + XZ 连接板", Z_CAR,    [   0.0,  -80.0,  95.0]),
    ("X 横梁总成",         X_FRAME,  [   0.0, -150.0,   0.0]),
    ("X 滑车",             X_CAR,    [   0.0, -230.0,   0.0]),
    ("HP45 喷头总成",      HEAD,     [ -50.0, -350.0,   0.0]),
    ("接触式探针总成",     PROBE,    [-185.0, -350.0,   0.0]),
    ("保湿站",             CAP,      [ 155.0,  -75.0,   0.0]),
]

# ------------------------------------------------------------------- validate
all_names = {v for k, v in occ_map.items() if k != ROOT_OCC}
seen: dict[str, str] = {}
for label, members, _ in GROUPS:
    unknown = members - all_names
    if unknown:
        raise SystemExit(f"{label}: names not in occ_map: {sorted(unknown)}")
    for n in members:
        if n in seen:
            raise SystemExit(f"{n} assigned to both {seen[n]} and {label}")
        seen[n] = label

unknown_frame = FRAME - all_names
if unknown_frame:
    raise SystemExit(f"FRAME: names not in occ_map: {sorted(unknown_frame)}")

ground = sorted(all_names - set(seen) - FRAME)
# ground must contain nothing except the hidden auxiliary body
unexpected = [n for n in ground if n != "Part__Feature"]
if unexpected:
    raise SystemExit(f"unassigned parts (not frame, not grouped, not auxiliary): {unexpected}")
assert len(seen) + len(FRAME) + len(ground) == len(all_names)

# ------------------------------------------------------------------------ emit
name_to_occ = {v: k for k, v in occ_map.items()}
moves, rows = [], []
for label, members, t in GROUPS:
    for n in sorted(members):
        moves.append({"occurrence": name_to_occ[n], "translate": t})
        rows.append([label, n, name_to_occ[n], *t])
for n in sorted(FRAME):
    rows.append(["Z 轴机架（固定基准）", n, name_to_occ[n], 0, 0, 0])
for n in ground:
    rows.append(["隐藏辅助几何（不显示）", n, name_to_occ[n], 0, 0, 0])
moves.sort(key=lambda m: m["occurrence"])

script = {"commands": [{
    "command": "explode.create",
    "params": {"name": VIEW_NAME, "moves": moves},
}]}
(OUT / "05_exploded_view_v2.json").write_text(
    json.dumps(script, ensure_ascii=False, indent=1), encoding="utf-8")

with (OUT / "EXPLODED_GROUPS_V2.csv").open("w", encoding="utf-8-sig",
                                          newline="") as f:
    w = csv.writer(f)
    w.writerow(["功能组", "零件名", "occurrence id", "dx mm", "dy mm", "dz mm"])
    w.writerows(rows)

meta = {
    "view_name": VIEW_NAME,
    "moved_occurrences": len(moves),
    "fixed_frame_occurrences": len(FRAME),
    "hidden_auxiliary": ground,
    "groups": {label: {"parts": len(members), "translate": t}
               for label, members, t in GROUPS},
}
print(json.dumps(meta, ensure_ascii=False, indent=1))
