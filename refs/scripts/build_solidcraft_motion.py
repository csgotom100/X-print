# -*- coding: utf-8 -*-
"""
Build the SolidCraft command scripts for:
  stage 1  21 v14 materials + kinematic tree (Z / X / probe sliders)
  stage 2  GT2 drive train (6 revolutes + 6 motion links)
  stage 3  the "coding cycle" motion study (100 steps, 3 keyed joints)

Inputs (all from this repository, no live SolidCraft state needed):
  refs/materials/material_summary.json       21 v14 materials (density, colour, note)
  refs/materials/material_assignments.csv    139 FreeCAD part -> material key
  refs/tmp/sc_body_names.json                144 body names as imported into SolidCraft
  refs/tmp/sc_occ_map.json                   occurrence id -> component name
  refs/tmp/diag joint.list dump              rigid joint ids (284 + (occ-4)/2)

Outputs:
  solidcraft/01_materials_kinematics.json   materials + Z/X/probe kinematic tree
  solidcraft/02_drive_train.json            GT2 pulley/shaft revolutes + motion links
  solidcraft/03_coding_motion.json          the "coding cycle" motion study
  solidcraft/MATERIAL_ASSIGNMENTS_SC.csv    human-readable assignment report
  solidcraft/build_manifest.json            counts / joint ids / material histogram

Run order (solidcraft-cli run <script> --in <base.sc> --save <out.sc>):
  01 -> stage1.sc    (base = solidcraft/CrossSlide_P014013.sc)
  02 -> stage2.sc    (in  = stage1.sc)
  03 -> motion.sc    (in  = stage2.sc)
After playback, reset the study to step 0 and re-save before delivery.
"""
from __future__ import annotations

import csv
import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "solidcraft"
OUT.mkdir(exist_ok=True)

summary = json.loads((ROOT / "refs/materials/material_summary.json").read_text(encoding="utf-8"))
mats = summary["materials"]
assign_rows = list(csv.DictReader((ROOT / "refs/materials/material_assignments.csv").open(encoding="utf-8-sig")))
key_of_part = {r["对象名"]: r["材质键"] for r in assign_rows}
body_names = json.loads((ROOT / "refs/tmp/sc_body_names.json").read_text(encoding="utf-8"))
occ_map = {int(k): v for k, v in json.loads((ROOT / "refs/tmp/sc_occ_map.json").read_text(encoding="utf-8")).items()}

# ---------------------------------------------------------------- materials
# SolidCraft's pbr requires metallic, roughness AND dielectric_ior; AUX stays
# semi-transparent so it must use scalar shading instead.
PBR = {
    "PETG":          (0.00, 0.55, 1.57),
    "AL6061":        (0.80, 0.35, 1.45),
    "AL6063":        (0.80, 0.35, 1.45),
    "AL_PULLEY":     (0.85, 0.30, 1.45),
    "STEEL_FASTENER": (0.85, 0.35, 1.45),
    "STEEL_ROD":     (0.90, 0.22, 1.45),
    "BEARING":       (0.90, 0.25, 1.45),
    "BRASS":         (0.85, 0.30, 1.45),
    "SPRING_STEEL":  (0.90, 0.25, 1.45),
    "PU_BELT":       (0.00, 0.80, 1.50),
    "MOTOR":         (0.50, 0.50, 1.50),
    "SWITCH":        (0.00, 0.60, 1.50),
    "ABS_CARTRIDGE": (0.00, 0.50, 1.52),
    "POM":           (0.00, 0.45, 1.48),
    "PA66GF30":      (0.00, 0.55, 1.53),
    "NDFEB":         (0.90, 0.28, 1.45),
    "FR4":           (0.00, 0.65, 1.55),
    "EPOXY_IC":      (0.00, 0.50, 1.55),
    "SILICONE":      (0.00, 0.80, 1.43),
    "SPONGE":        (0.00, 0.90, 1.40),
    "AUX":           None,
}


def rgb255(key: str) -> list[int]:
    return [int(round(float(c) * 255)) for c in mats[key]["color"]]


def base_name(n: str) -> str:
    """Cap_Spring (2) ... (5) are the 5 solids of the one FreeCAD spring part."""
    return re.sub(r" \(\d+\)$", "", n)


bodies_by_key: dict[str, list[str]] = OrderedDict((k, []) for k in mats)
for n in body_names:
    key = "AUX" if n == "Part__Feature" else key_of_part.get(base_name(n))
    if key is None:
        raise SystemExit(f"unmapped SolidCraft body: {n}")
    bodies_by_key[key].append(n)

material_commands = []
for key, m in mats.items():
    params = {
        "name": m["name"],
        "density_g_cm3": float(m["density_kg_m3"]) / 1000.0,
        "color": rgb255(key),
    }
    if PBR.get(key):
        metallic, roughness, ior = PBR[key]
        params["pbr"] = {"metallic": metallic, "roughness": roughness,
                         "dielectric_ior": ior}
    if key == "AUX":
        params["opacity"] = 0.35
    material_commands.append({"command": "material.create", "params": params})
for key, bodies in bodies_by_key.items():
    if not bodies:
        continue
    material_commands.append({
        "command": "material.assign",
        "params": {"bodies": bodies, "material": mats[key]["name"]},
    })

# ---------------------------------------------------------------- kinematics
# The STEP import rigidly locked all 140 occurrences to the root (occurrence 2)
# with joints 284..423, joint id = 284 + (occurrence_id - 4) / 2.
occ_of_name = {v: k for k, v in occ_map.items()}


def joint_id(part_name: str) -> int:
    occ = occ_of_name[part_name]
    jid = 284 + (occ - 4) // 2
    assert 284 <= jid <= 423, (part_name, occ, jid)
    return jid


FRAME_Z = {"origin": [0, 0, 0], "z": [0, 0, 1], "x": [1, 0, 0]}
FRAME_X = {"origin": [0, 0, 0], "z": [1, 0, 0], "x": [0, 1, 0]}

ROOT_OCC = 2
Z_LEADER = "Z_Carriage_Lower"
X_LEADER = "X_Carriage_Lower"
P_LEADER = "HP45_PogoPin"
X_FRAME = "X_Profile"
P_FRAME = "HP45_ProbeHousing"

Z_JOINT = "Z 升降 / Z approach"
X_JOINT = "X 扫描 / X scan"
P_JOINT = "探针压缩 / probe stroke"

# Ground: Z base, Z column, Z belts/motor/limit switches, capping station.
GROUND = set()
for p in ["Z_BaseBlock"] + [f"Bench_Screw_{i}" for i in range(4)]:
    GROUND.add(p)
for p in ["Z_Profile", "Z_EndPlate_L", "Z_EndPlate_R", "Z_Screw_Core_0", "Z_Screw_Core_1",
          "Z_GuideRod_1", "Z_GuideRod_2", "Z_Pulley_Drive", "Z_Pulley_Idler", "Z_Screw_Idler",
          "Z_Washer_Idler", "Z_Washer_Nut_Idler", "Z_Nut_Idler", "Z_Belt_GT2",
          "Z_Motor_NEMA17", "Z_Motor_Shaft", "Z_BaseScrew_0", "Z_BaseScrew_1",
          "Z_BaseScrew_2", "Z_BaseScrew_3", "Z_LimitSwitch_Bot", "Z_LimitSwitch_Top"]:
    GROUND.add(p)
for i in range(4):
    GROUND.add(f"Z_Screw_Motor_{i}")
for i in range(1, 5):
    GROUND.add(f"LimitScrew_{i}")
for p in ["Z_rod_1_tap", "Z_rod_2_tap", "Z_rod_fix_screw_1", "Z_rod_fix_screw_2"]:
    GROUND.add(p)
# capping station sits on the base
for p in ["Cap_Tray", "Cap_Seal", "Cap_Sponge", "Cap_BaseScrew_1", "Cap_BaseScrew_2"]:
    GROUND.add(p)
for n in body_names:
    if base_name(n) == "Cap_Spring":
        GROUND.add(n)

# Pogo group: needle + magnet + R125 sleeve travel together (+Z, 0..3 mm).
POGO = {"HP45_PogoMagnet", "HP45_SocketR125"}

# X group: X carriage and everything bolted to it (HP45 head + probe housing).
XGROUP = {
    "X_Carriage_Upper", "X_Insert_Car_0", "X_Screw_Car_0", "X_Insert_Car_1", "X_Screw_Car_1",
    "X_Clamp_Key_A", "X_Clamp_Key_B", "X_LM5UU_1", "X_LM5UU_2",
    "HP45_CarriageAdapter", "HP45_AdptScrew_0", "HP45_AdptScrew_1", "HP45_AdptScrew_2",
    "HP45_AdptScrew_3", "HP45_Real", "HP45CAR_P01", "HP45CAR_P03", "HP45CAR_P04",
    "HP45CAR_P02_R", "HP45CAR_P02_L", "HP45_P01Screw_0", "HP45_P01Screw_1",
    "HP45_P01Screw_2", "HP45_P01Screw_3", "HP45_ProbeArm", "HP45_ProbeScrew_0",
    "HP45_ProbeScrew_1", "HP45_ProbeHousing", "HP45_HousingScrew_0", "HP45_HousingScrew_1",
    "HP45_HallSensor", "HP45_HallPCB", "HP45_HallCover", "HP45_CableClamp",
    "HP45_SpringSpacer", "HP45_PogoSpring", "HP45_DustSeal",
}

# Everything else that is not ground / X / pogo / a leader moves with the Z carriage.
SPECIAL = GROUND | XGROUP | POGO | {Z_LEADER, X_LEADER, P_LEADER}
all_parts = {base_name(n) for n in body_names}
ZGROUP = all_parts - SPECIAL

# sanity: every occurrence must land in exactly one bucket
for name in sorted(all_parts):
    n = sum(name in s for s in (GROUND, XGROUP, POGO, ZGROUP))
    if name in (Z_LEADER, X_LEADER, P_LEADER):
        continue
    if n != 1:
        raise SystemExit(f"ambiguous bucket for {name}: {n}")
assert X_FRAME in ZGROUP, "X_Profile must be in the Z group (it is the X slider's frame)"
assert P_FRAME in XGROUP, "HP45_ProbeHousing must be in the X group"

joint_commands = []


def edit_parent(part: str, parent_occ, frame=FRAME_Z):
    """Re-anchor an imported rigid joint to another occurrence, keeping the part where it is."""
    joint_commands.append({
        "command": "joint.edit",
        "params": {
            "joint": joint_id(part),
            "a": {"occurrence": parent_occ, "frame": frame},
            "b": {"occurrence": f"{part}:1", "frame": frame},
            "flip": True,
            "quiet": True,
        },
    })


def edit_slider(part: str, parent_occ, frame, name, limits):
    joint_commands.append({
        "command": "joint.edit",
        "params": {
            "joint": joint_id(part),
            "type": "slider",
            "a": {"occurrence": parent_occ, "frame": frame},
            "b": {"occurrence": f"{part}:1", "frame": frame},
            "flip": True,
            "name": name,
            "quiet": True,
        },
    })
    joint_commands.append({
        "command": "joint.limits",
        "params": {"joint": name, "min": limits[0], "max": limits[1]},
    })


# 1) leaders first, so their parents are settled before children are re-anchored
edit_slider(Z_LEADER, ROOT_OCC, FRAME_Z, Z_JOINT, (-30.0, 30.0))
edit_slider(X_LEADER, f"{X_FRAME}:1", FRAME_X, X_JOINT, (-85.0, 85.0))
edit_slider(P_LEADER, f"{P_FRAME}:1", FRAME_Z, P_JOINT, (0.0, 3.0))

# 2) re-anchor the rest into the tree:  root -> Z -> X -> pogo
for part in sorted(ZGROUP):
    edit_parent(part, f"{Z_LEADER}:1")
for part in sorted(XGROUP):
    edit_parent(part, f"{X_LEADER}:1")
for part in sorted(POGO):
    edit_parent(part, f"{P_LEADER}:1")

# 3) hide the duplicate stray plate (open body, exact copy of X_EndPlate_R)
joint_commands.append({
    "command": "browser.visibility",
    "params": {"items": ["Part__Feature"], "visible": False},
})
# 4) keep the joint glyphs out of the animation
joint_commands.append({
    "command": "browser.visibility",
    "params": {"folder": "joints", "visible": False},
})

stage1 = material_commands + joint_commands

# ---------------------------------------------------------------- drive train
# GT2 16T pulley: pitch circumference = 16 teeth x 2 mm = 32 mm,
# pitch radius r = 32 / (2 pi) = 5.09296 mm, so 1 mm of belt travel turns the
# pulley 180 / (pi * r) = 11.2532 degrees.  The belts themselves are rigid
# bodies in the imported STEP, so they stay put; only the pulleys/shafts turn.
DEG_PER_MM = 180.0 / (3.141592653589793 * (32.0 / (2 * 3.141592653589793)))


def frame_y(origin):
    return {"origin": origin, "z": [0, 1, 0], "x": [1, 0, 0]}


def edit_revolute(part, parent_occ, origin, name):
    drive_commands.append({
        "command": "joint.edit",
        "params": {
            "joint": joint_id(part),
            "type": "revolute",
            "a": {"occurrence": parent_occ, "frame": frame_y(origin)},
            "b": {"occurrence": f"{part}:1", "frame": frame_y(origin)},
            "flip": True,
            "name": name,
            "quiet": True,
        },
    })


Z_DRIVE = "Z 主动轮 / Z drive pulley"
Z_IDLER = "Z 惰轮 / Z idler"
Z_SHAFT = "Z 电机轴 / Z motor shaft"
X_DRIVE = "X 主动轮 / X drive pulley"
X_IDLER = "X 惰轮 / X idler"
X_SHAFT = "X 电机轴 / X motor shaft"

drive_commands = []
edit_revolute("Z_Pulley_Drive", 2, [150, -12, 33], Z_DRIVE)
edit_revolute("Z_Pulley_Idler", 2, [150, -12, 241], Z_IDLER)
edit_revolute("Z_Motor_Shaft", 2, [150, -12, 33], Z_SHAFT)
edit_revolute("X_Pulley_Drive", "X_EndPlate_L:1", [21, -68, 137], X_DRIVE)
edit_revolute("X_Pulley_Idler", "X_EndPlate_R:1", [279, -68, 137], X_IDLER)
edit_revolute("X_Motor_Shaft", "X_EndPlate_L:1", [21, -68, 137], X_SHAFT)

for a, b, ratio in [
    (Z_JOINT, Z_DRIVE, DEG_PER_MM),
    (Z_DRIVE, Z_IDLER, 1.0),
    (Z_DRIVE, Z_SHAFT, 1.0),
    (X_JOINT, X_DRIVE, DEG_PER_MM),
    (X_DRIVE, X_IDLER, 1.0),
    (X_DRIVE, X_SHAFT, 1.0),
]:
    drive_commands.append({
        "command": "joint.motion_link",
        "params": {"a": a, "b": b, "ratio": ratio},
    })

# ---------------------------------------------------------------- motion study
# A complete coding cycle: home -> approach -> surface detect -> X scan -> lift
#                          -> park over capping station -> cap.
study_commands = [{
    "command": "motion.study",
    "params": {
        "name": "打码工作循环 / Coding cycle",
        "steps": 100,
        "keys": [
            {"joint": X_JOINT, "points": [
                [0, 0], [20, -40], [25, -40], [65, 40], [75, 0], [88, 75], [100, 75]]},
            {"joint": Z_JOINT, "points": [
                [0, 0], [8, -3], [80, -3], [84, 0], [92, -3], [100, -3]]},
            {"joint": P_JOINT, "points": [
                [0, 0], [8, 0], [12, 3], [78, 3], [84, 0], [100, 0]]},
        ],
    },
}]
stage2 = drive_commands
stage3 = study_commands

(OUT / "01_materials_kinematics.json").write_text(
    json.dumps({"commands": stage1}, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "02_drive_train.json").write_text(
    json.dumps({"commands": stage2}, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "03_coding_motion.json").write_text(
    json.dumps({"commands": stage3}, ensure_ascii=False, indent=1), encoding="utf-8")
old = OUT / "02_coding_motion.json"
if old.exists():
    old.unlink()

with (OUT / "MATERIAL_ASSIGNMENTS_SC.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["SolidCraft body", "material key", "material name", "density g/cm3", "colour RGB 0-255"])
    for key, bodies in bodies_by_key.items():
        for b in bodies:
            w.writerow([b, key, mats[key]["name"],
                        float(mats[key]["density_kg_m3"]) / 1000.0,
                        " ".join(map(str, rgb255(key)))])

meta = {
    "bodies": len(body_names),
    "material_commands": len(material_commands),
    "joint_commands": len(joint_commands),
    "drive_commands": len(drive_commands),
    "study_commands": len(study_commands),
    "deg_per_mm": DEG_PER_MM,
    "ground": len(GROUND),
    "z_group": len(ZGROUP),
    "x_group": len(XGROUP),
    "pogo_group": len(POGO),
    "leaders": {Z_JOINT: joint_id(Z_LEADER), X_JOINT: joint_id(X_LEADER), P_JOINT: joint_id(P_LEADER)},
    "material_counts": {k: len(v) for k, v in bodies_by_key.items() if v},
}
(OUT / "build_manifest.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(meta, ensure_ascii=False, indent=1))
