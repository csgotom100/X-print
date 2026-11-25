# -*- coding: utf-8 -*-
"""
Build a *grouped* exploded view for the SolidCraft CrossSlide assembly.

Why not SolidCraft's automatic radial explode:
  * `explode.create {scale:...}` fails on this STEP import with
    "an exploded view needs two or more occurrences" (flat component tree),
  * and a per-occurrence radial scatter would send all 70 fasteners flying,
    which makes the assembly relationship unreadable.

So we give every occurrence an explicit translate, but **one translate per
functional group** -- the group's own fasteners travel with it, intact. The
Z-axis frame stays put as the reference; the other six groups step away along
-Y and are staggered in X/Z so no two groups overlap in the iso render.

Input : refs/tmp/sc_occ_map.json   (occurrence id -> component name)
Output: solidcraft/04_exploded_view.json      (single explode.create command)
        solidcraft/EXPLODED_GROUPS.csv        (group / part / translate audit)

Run with:
  solidcraft-cli run solidcraft/04_exploded_view.json \
      --in  <CrossSlide_P014013_motion.sc> \
      --save <CrossSlide_P014013_exploded.sc> --results --param-check warn
Then in the app: explode.show -> screenshot -> explode.show {view: none}.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "solidcraft"
OUT.mkdir(exist_ok=True)

occ_map = {
    int(k): v
    for k, v in json.loads(
        (ROOT / "refs/tmp/sc_occ_map.json").read_text(encoding="utf-8")
    ).items()
}
ROOT_OCC = 2
VIEW_NAME = "整机爆炸图 / Assembly exploded"


def seq(stem, count):
    return {f"{stem}_{i}" for i in range(count)}


def rng(stem, lo, hi):
    return {f"{stem}_{i}" for i in range(lo, hi + 1)}


# ---------------------------------------------------------------- groups
# 1) Z carriage + XZ adapter plate + their fasteners: up and forward.
Z_CAR = {
    "Z_Carriage_Lower", "Z_Carriage_Upper",
    "Z_Insert_Car_0", "Z_Insert_Car_1",
    "Z_Screw_Car_0", "Z_Screw_Car_1",
    "Z_Clamp_Key_A", "Z_Clamp_Key_B",
    "Z_LM5UU_1", "Z_LM5UU_2",
    "XZ_Plate",
} | seq("Plate_M3", 4) | seq("Plate_M5", 4) | seq("TNut_M5", 4)

# 2) X beam / end plates / guide rods / pulleys / belt / motor / limit switches.
X_FRAME = {
    "X_Profile", "X_EndPlate_L", "X_EndPlate_R",
    "X_Screw_Core_0", "X_Screw_Core_1",
    "X_GuideRod_1", "X_GuideRod_2",
    "X_Pulley_Drive", "X_Pulley_Idler",
    "X_Screw_Idler", "X_Washer_Idler", "X_Washer_Nut_Idler", "X_Nut_Idler",
    "X_Belt_GT2",
    "X_Motor_NEMA17", "X_Motor_Shaft",
    "X_rod_1_tap", "X_rod_2_tap",
    "X_rod_fix_screw_1", "X_rod_fix_screw_2",
    "X_LimitSwitch_L", "X_LimitSwitch_R",
} | seq("X_Screw_Motor", 4) | rng("LimitScrew", 5, 8)

# 3) X carriage halves, bearings, clamp keys, inserts.
X_CAR = {
    "X_Carriage_Lower", "X_Carriage_Upper",
    "X_Insert_Car_0", "X_Insert_Car_1",
    "X_Screw_Car_0", "X_Screw_Car_1",
    "X_Clamp_Key_A", "X_Clamp_Key_B",
    "X_LM5UU_1", "X_LM5UU_2",
}

# 4) HP45 head: cartridge, latch parts, carriage adapter, probe arm.
HEAD = {
    "HP45_Real",
    "HP45CAR_P01", "HP45CAR_P03", "HP45CAR_P04",
    "HP45CAR_P02_R", "HP45CAR_P02_L",
    "HP45_CarriageAdapter",
    "HP45_ProbeArm",
    "HP45_ProbeScrew_0", "HP45_ProbeScrew_1",
} | seq("HP45_AdptScrew", 4) | seq("HP45_P01Screw", 4)

# 5) Contact probe sub-assembly (small parts, pulled out sideways to be visible).
PROBE = {
    "HP45_ProbeHousing", "HP45_PogoPin", "HP45_PogoMagnet", "HP45_PogoSpring",
    "HP45_HallSensor", "HP45_HallPCB",
    "HP45_HousingScrew_0", "HP45_HousingScrew_1",
    "HP45_SocketR125", "HP45_DustSeal",
    "HP45_HallCover", "HP45_CableClamp", "HP45_SpringSpacer",
}

# 6) Capping station, pulled out to +X.
CAP = {
    "Cap_Spring", "Cap_Tray", "Cap_Seal", "Cap_Sponge",
    "Cap_BaseScrew_1", "Cap_BaseScrew_2",
}

# name -> (label, [dx, dy, dz])
GROUPS = [
    ("Z 滑车 + XZ 连接板", Z_CAR, [0.0, -40.0, 50.0]),
    ("X 横梁总成",         X_FRAME, [0.0, -85.0, 0.0]),
    ("X 滑车",             X_CAR, [0.0, -150.0, 0.0]),
    ("HP45 喷头总成",      HEAD, [-25.0, -235.0, 0.0]),
    ("接触式探针总成",     PROBE, [-115.0, -235.0, 0.0]),
    ("保湿站",             CAP, [95.0, -55.0, 0.0]),
]

# ---------------------------------------------------------------- validate
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

ground = sorted(all_names - set(seen))
assert len(seen) + len(ground) == len(all_names)

# ---------------------------------------------------------------- emit
name_to_occ = {v: k for k, v in occ_map.items()}
moves = []
rows = []
for label, members, t in GROUPS:
    for n in sorted(members):
        moves.append({"occurrence": name_to_occ[n], "translate": t})
        rows.append([label, n, name_to_occ[n], *t])
for n in ground:
    rows.append(["Z 轴骨架（基准，不动）", n, name_to_occ[n], 0, 0, 0])
moves.sort(key=lambda m: m["occurrence"])

script = {"commands": [{
    "command": "explode.create",
    "params": {"name": VIEW_NAME, "moves": moves},
}]}
(OUT / "04_exploded_view.json").write_text(
    json.dumps(script, ensure_ascii=False, indent=1), encoding="utf-8")

with (OUT / "EXPLODED_GROUPS.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["功能组", "零件名", "occurrence id", "dx mm", "dy mm", "dz mm"])
    w.writerows(rows)

meta = {
    "view_name": VIEW_NAME,
    "moved_occurrences": len(moves),
    "ground_occurrences": len(ground),
    "groups": {label: {"parts": len(members), "translate": t}
               for label, members, t in GROUPS},
    "excluded": ["Part__Feature (hidden auxiliary)", "root occurrence 2"],
}
print(json.dumps(meta, ensure_ascii=False, indent=1))
