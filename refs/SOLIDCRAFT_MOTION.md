# SolidCraft 材质赋值与打码运动仿真报告

生成时间：2026-11-12
主交付：`solidcraft/CrossSlide_P014013_motion.sc`（sha256 `e93e75b0…`）
基线：`solidcraft/CrossSlide_P014013.sc`（见 `refs/SOLIDCRAFT_MIGRATION.md`）

---

## 1. 任务与执行顺序

| 顺序 | 用户指令 | 意图 |
|---|---|---|
| 1 | 「导入成功后，再帮我在 solidcraft 里模拟系统的打码工作机械运动」 | 在已迁移的设计上建立 X/Z 扫描、探针抬压、保湿盖合的机构运动 |
| 2 | 「在 solidcraft 里为各零件赋予合理材质，再模拟运动」 | **明确改序**：先赋材质，再做运动；材质沿用 v14 定稿口径 |
| 3 | 「请继续执行任务」/ 本轮续跑 | 收尾：复位初始姿态、正式保存、拷回项目、同步文档与 Git |

本轮收尾完成的动作：把停在 **step 45** 的关节值复位到 **step 0**、覆盖保存 `.sc`、重新打开读回验证、把设计 / 动画 / 两张渲染图拷回 `solidcraft/`、补文档与项目记忆。

---

## 2. 结论速览

| 项目 | 结果 |
|---|---|
| v14 材质 | **21 种 user material**，**144 / 144 bodies** 全覆盖，无重复、无遗漏 |
| 关节重构 | 140 joints = `rigid 131` + `revolute 6` + `slider 3`；`conflicts=[]` `errors=[]` `floating=[]` |
| 运动链接 | 6 条 `joint.motion_link`，GT2 16T 传动比 **11.25 deg/mm** |
| 运动 study | id `424`，`打码工作循环 / Coding cycle`，**100 steps**，3 条关键帧曲线 |
| 干涉检查 | 26 采样 / 160 对 / **collisions 0** / `clear=true` / 未截断 |
| 动画 | `CrossSlide_coding_cycle.gif`，**1920×1200**，29 帧，14.29 fps，1578182 bytes |
| 几何一致性 | 144 bodies，总闭合体体积 **856894.0750482227 mm³**，与迁移基线完全一致 |
| 交付初始姿态 | **step 0**：X = 0 / Z = 0 / P = 0（已持久化，重新打开读回确认） |

---

## 3. 材质赋值

### 3.1 输入与口径

- `refs/materials/material_summary.json`：v14 的 21 种材质（名称、密度、弹性、颜色）。
- `refs/materials/material_assignments.csv`：139 个 FreeCAD 对象 → 材质键映射。
- 用户定稿口径：**异型结构件采用 PETG 材质 3D 打印**（16 件）；v13.2 三主件保留量产口径：探针座 / 侧盖板 `POM`、探针臂 `PA66-GF30`。

### 3.2 139 件 → 144 bodies 的映射处理

SolidCraft 导入后是 144 个 body，比 v14 CSV 的 139 行多 5 个，两类差异：

| 差异 | 处理 |
|---|---|
| `Cap_Spring` 在源 FCStd 里本就是 **5 个分离实体**，被拆成 `Cap_Spring`、`Cap_Spring (2)..(5)` | 用 `base_name()` 去掉 ` (\d+)` 后缀，全部归一到 `SPRING_STEEL` |
| `Part__Feature`（源模型里端板 R 的近似副本，开放壳）不在 v14 CSV | 归入 `AUX` = `工艺辅助几何非零件`，`opacity 0.35`，并用 `browser.visibility` 隐藏 |

代码：

```python
def base_name(n: str) -> str:
    """Cap_Spring (2) ... (5) are the 5 solids of the one FreeCAD spring part."""
    return re.sub(r" \(\d+\)$", "", n)

key = "AUX" if n == "Part__Feature" else key_of_part.get(base_name(n))
if key is None:
    raise SystemExit(f"unmapped SolidCraft body: {n}")
```

### 3.3 命令模式与踩过的坑

`material.create` 的完整参数：

```python
params = {
    "name": m["name"],
    "density_g_cm3": float(m["density_kg_m3"]) / 1000.0,
    "color": [int(round(c * 255)) for c in m["color"]],   # RGB 0-255
    "pbr": {"metallic": 0.0, "roughness": 0.55,
            "dielectric_ior": 1.57},                       # 三字段必须齐全
}
```

- **坑 1**：`pbr` 少任何一个字段会报
  `invalid parameters for material.create: pbr requires exactly metallic, roughness and dielectric_ior`。
  第一次运行因此失败，补齐 `dielectric_ior` 后通过。
- **坑 2**：`AUX` 需要半透明，改用 scalar shading（不传 `pbr`）+ `opacity: 0.35`。
- 共 `21 × material.create` + `21 × material.assign` = **42 条命令**；`material.assign` 用
  `{"bodies": [...], "material": <材质名>}` 批量按材质分组赋值，避免逐 body 调用。

### 3.4 材质分布（`build_manifest.json`）

| 材质键 | bodies | 材质键 | bodies |
|---|---:|---|---:|
| `STEEL_FASTENER` | 70 | `PETG` | 16 |
| `STEEL_ROD` | 6 | `PU_BELT` | 6 |
| `SPRING_STEEL` | 6 | `BRASS` | 6 |
| `AUX` | 5 | `AL_PULLEY` | 4 |
| `BEARING` | 4 | `SWITCH` | 4 |
| `SILICONE` | 3 | `AL6063` | 2 |
| `FR4` | 2 | `MOTOR` | 2 |
| `POM` | 2 | `AL6061` / `PA66GF30` / `NDFEB` / `EPOXY_IC` / `ABS_CARTRIDGE` / `SPONGE` | 各 1 |

合计 144。

### 3.5 读回验证

- `material.list`：21 个 `user: true` 材质全部建立，PBR / 颜色 / 密度逐项吻合。
- 144 个 body 全部有材质，无重复、无遗漏。
- 关键件读回：

```
HP45_ProbeHousing | POM注塑探针座与侧盖板 | density 1.41 g/cm3 | V=5138.62724278665 mm3
```

---

## 4. 运动链重建

### 4.1 导入态是「死刚体」

STEP 导入把 140 个 occurrence 全部用 `rigid` 关节锁到 root occurrence `2`：

```
joints 140   types {'rigid': 140}   fixed [0, 2]   floating []
dof         142 个 occurrence 全是 0
joint_id = 284 + (occurrence_id - 4) / 2        # 范围 284..423
```

没有任何可动自由度，必须把刚性关节改造成运动树。

### 4.2 分组与父子关系

| 分组 | 数量 | 说明 |
|---|---:|---|
| `GROUND` | 49 | Z 底座 / 立柱 / 端板 / 导杆 / 电机 / 同步带 / 限位开关 / 保湿站 |
| `ZGROUP` | 53 | 随 Z 滑座移动的一切（含 `X_Profile`，它是 X 滑块的机架） |
| `XGROUP` | 37 | X 滑车 + HP45 喷头总成 + 探针座（含 `HP45_ProbeHousing`，它是探针滑块的机架） |
| `POGO` | 2 | 针杆带动的磁环 `HP45_PogoMagnet` + 针套 `HP45_SocketR125` |
| 3 个 leader | 3 | `Z_Carriage_Lower` / `X_Carriage_Lower` / `HP45_PogoPin` |
| **合计** | **144** | 与 body 数一致，每个 body 恰好落在一个桶 |

运动树：

```
root(2)
 └─ Z_Carriage_Lower   [slider 303, Z 升降, ±30]
     └─ (53 件 ZGROUP，含 X_Profile)
         └─ X_Carriage_Lower   [slider 338, X 扫描, ±85, 轴沿 X]
             └─ (37 件 XGROUP，含 HP45_ProbeHousing)
                 └─ HP45_PogoPin   [slider 411, 探针压缩, 0..3]
                     └─ HP45_PogoMagnet + HP45_SocketR125
```

### 4.3 三个 slider

| id | 名称 | 父 occurrence | 轴 / 限位 |
|---:|---|---|---|
| 303 | `Z 升降 / Z approach` | root `2` | Z，`[-30, 30] mm` |
| 338 | `X 扫描 / X scan` | `X_Profile:1` | X，`[-85, 85] mm` |
| 411 | `探针压缩 / probe stroke` | `HP45_ProbeHousing:1` | Z，`[0, 3] mm` |

`411` 的上限 `3.0` 与项目冻结项「探针有效行程 0..+3.0 mm」一致。

### 4.4 命令模式

`joint.edit` 把导入的 rigid 关节重新锚定到新的父 occurrence，保持零件原位：

```python
def edit_slider(part, parent_occ, frame, name, limits):
    joint.edit {joint: joint_id(part), type: "slider",
                a: {occurrence: parent_occ, frame: frame},
                b: {occurrence: f"{part}:1", frame: frame},
                flip: True, name: name, quiet: True}
    joint.limits {joint: name, min: limits[0], max: limits[1]}
```

要点：
- **先改 3 个 leader，再改其余 99 件的父级**，否则子件锚到尚未稳定的父上会报错。
- `flip: True`、`quiet: True` 保证方向正确且不刷日志。
- `FRAME_Z` 用 `z=[0,0,1]`；`FRAME_X` 用 `z=[1,0,0], x=[0,1,0]`。
- 最后 `browser.visibility` 隐藏 `Part__Feature` 与关节 glyph 文件夹，避免动画里出现辅助几何和关节图标。

阶段 1 共 100 条 `joint.*` / `browser.visibility` 命令；读回后 `joint.list`：

```
joints 140  types {'rigid': 131, 'revolute': 6, 'slider': 3}
conflicts []  errors []  floating []  fixed [0, 2]  links 6
dof Counter({1: 54, 0: 44, 2: 41, 3: 3})
```

---

## 5. GT2 传动链

### 5.1 换算

GT2 16T 同步轮，节距 2 mm：

```
节圆周长 = 16 × 2 = 32 mm
节圆半径 r = 32 / (2π) = 5.09296 mm
1 mm 带位移 → 角度 = 180 / (π · r) = 11.25 deg
```

```python
DEG_PER_MM = 180.0 / (math.pi * (32.0 / (2 * math.pi)))   # 11.25 deg/mm
```

### 5.2 6 个转动关节与 6 条链接

| id | 关节 | 类型 | 父 | 回转轴心 |
|---:|---|---|---|---|
| 296 | `Z 主动轮 / Z drive pulley` | revolute | `2` | `[150,-12,33]` |
| 297 | `Z 惰轮 / Z idler` | revolute | `2` | `[150,-12,241]` |
| 314 | `Z 电机轴 / Z motor shaft` | revolute | `2` | `[150,-12,33]` |
| 331 | `X 主动轮 / X drive pulley` | revolute | `X_EndPlate_L:1` | `[21,-68,137]` |
| 332 | `X 惰轮 / X idler` | revolute | `X_EndPlate_R:1` | `[279,-68,137]` |
| 349 | `X 电机轴 / X motor shaft` | revolute | `X_EndPlate_L:1` | `[21,-68,137]` |

| 驱动 a | 从动 b | ratio |
|---|---|---:|
| `Z_JOINT` (303) | `Z_DRIVE` (296) | **11.25** |
| 296 → 297 | 惰轮 | 1.0 |
| 296 → 314 | 电机轴 | 1.0 |
| `X_JOINT` (338) | `X_DRIVE` (331) | **11.25** |
| 331 → 332 | 惰轮 | 1.0 |
| 331 → 349 | 电机轴 | 1.0 |

`motion.plot` 验证：Z 主动轮 / 惰轮 / 电机轴角度曲线完全重合，X 三条同样重合，且角度 = 位移 × 11.25 deg/mm。

> **限制**：导入的 `X_Belt_GT2` / `Z_Belt_GT2` 是刚体，不会随轮卷绕或变形；动画里只有轮和轴转动，皮带保持原位。这是刚体机构仿真的近似，不是柔性带传动。

---

## 6. 打码工作循环 study

`motion.study`，id `424`，100 步，3 条关键帧曲线（`unit: mm`）：

| 关节 | 关键帧 `[step, value]` |
|---|---|
| X 扫描 (338) | `[0,0] [20,-40] [25,-40] [65,40] [75,0] [88,75] [100,75]` |
| Z 升降 (303) | `[0,0] [8,-3] [80,-3] [84,0] [92,-3] [100,-3]` |
| 探针压缩 (411) | `[0,0] [8,0] [12,3] [78,3] [84,0] [100,0]` |

阶段解读：

| step | 动作 |
|---:|---|
| 0 | Home：X=0 / Z=0 / 探针未压缩 |
| 8 | Z 下降 3 mm 接近工件，X 同时移向扫描起点 |
| 12 | 探针压缩到 3 mm（接触式测高到位，霍尔检测窗口） |
| 20–25 | X 到 −40 mm 扫描起点，保持 |
| 25–65 | **打码扫描**：X 从 −40 → +40 mm，Z 保持 −3，探针保持 3 mm |
| 75 | X 回 0，抬升前归位 |
| 78–84 | 探针回 0，Z 抬升回 0 |
| 88 | X 移到 +75 mm（保湿站上方） |
| 92–100 | Z 再降 −3 mm，压入保湿站完成盖合密封 |

`motion.trace`（occurrence `HP45_Real:1`，跟踪点 `[150,-136,58]`，11 采样）记录喷头喷嘴轨迹由 `(150,-136,58)` 走到 `(225,-136,55)`：X +75 mm、Z −3 mm，与关键帧一致；`stopped_at / stopped_by_contact / stopped_by_loop` 均为 `null`（全程未触发停止条件）。

---

## 7. 验证

### 7.1 运动学 / 动力学输出

| 命令 | 结果 |
|---|---|
| `motion.export {samples:6}` | Z 滑座 0 → −3；step 20 `X=-40,Z=-3`、step 40 `X=-10,Z=-3`、step 60 `X=30,Z=-3`、step 100 `X=75,Z=-3`；探针针杆 / 磁环相对探针座额外 0..3 mm |
| `motion.trace` | 11 采样，轨迹与关键帧一致，无停止 |
| `motion.interference` | `samples 26` / `pairs 160` / `budget_s 240` / **`collisions []`** / `clear=true` / `truncated=false` |
| `motion.plot` | `samples 11` / `duration 10 s`，9 个运动关节的 value / velocity / acceleration；GT2 角度曲线校验通过 |
| `motion.export_animation` | 高清重出：**1920×1200 / 29 帧 / 1.51 MB**，`renderer: gpu`，70 ms/帧 ≈ 14.29 fps，约 2.03 s；`stopped_*` 均 `null` |
| `motion.play {study:424, step:45}` | `moved: true` / `conflicts: 0` |

> **动画高清重出（用户反馈「GIF 分辨率不够高」后追加）**
> 初版为 `960×600 / 31 帧 / 459962 bytes`。改为 `width:1920, height:1200` 后渲染器报
> `samples must be 2…29 for 1920 × 1200 frames` —— `motion.export_animation` 有**像素预算**，
> 分辨率越高允许的帧数越少，高分辨率与高帧数不能兼得。主诉是分辨率，故取分辨率优先：
> `samples:29`（帧数 31→29 几乎无感），`fps:14` 使时长约 2.03 s，接近初版 2.17 s。
> 结果 `1920×1200 / 29 帧 / 1578182 bytes / 70 ms 每帧 ≈ 14.29 fps / 循环播放`，
> sha256 `a1b5b46b…`；PIL 复核首帧 / 中帧 / 末帧像素确有变化（mean |Δ| 2.50 / 4.50），画面非空白。
> GIF 始终受 256 色调色板限制；若要 4K、60 帧以上或无损全彩，应把 `path` 指向**文件夹**
> 导出 PNG 帧序列（`frame-0001.png` …），再自行合成 MP4 / WebM。

### 7.2 本轮收尾发现并修复的问题

重新打开磁盘 `motion.sc` 后 `joint.list` 发现 3 个 slider 的当前值停在 **step 45**，不是 home 位：

```
303 Z 升降   value = -3.0      (limits [-30, 30])
338 X 扫描   value =  0.0      (limits [-85, 85])
411 探针压缩 value =  3.0      (limits [  0,  3])
```

即用户打开文件会直接看到「打码中途」姿态。修复流程：

1. `motion.play {step: 0}` **失败**：`invalid parameters: study must be an id or a name` —— `study` 是必填参数，不能只传 `step`。
2. `motion.play {study: 424, step: 0}` → `moved: true`，`values` 中 X/Z/P 全部 `0.0`，`conflicts: 0`。
3. `execute {command:"file.save", params:{path:..., format:"container", overwrite:true}}` 覆盖保存（注意 `mcp__solidcraft__save` 工具不接受 `overwrite`，必须走 engine 命令）。
4. `open` 重新加载磁盘文件，逐个 `joint.inspect {303/338/411}` 读回：

```
303  slider  Z 升降 / Z approach     value 0.0   resolves=true  conflicts=[]  errors=[]
338  slider  X 扫描 / X scan         value 0.0   resolves=true  conflicts=[]  errors=[]
411  slider  探针压缩 / probe stroke  value 0.0   resolves=true  conflicts=[]  errors=[]
```

5. `motion.list` 读回 study 424 与 3 条关键帧曲线完好；`material.list` 21 个 user material 完好。

### 7.3 几何未被运动化改动

`measure {summary:true}` 读回：

```
body_count 144
total.volume_mm3 = 856894.0750482227      # 与迁移基线 856894.075 一致
closed=false 的 3 件：X_EndPlate_L / X_EndPlate_R / Part__Feature（volume=null）
```

材质、关节、study 都属于装配层元数据，不改动任何 B-rep。

---

## 8. 可复现通道

```bash
# 1) 生成三阶段命令脚本 + 材质对照表 + manifest
python refs/scripts/build_solidcraft_motion.py

# 2) 阶段 1：v14 材质 + Z/X/探针运动树
"/d/Program Files/SolidCraft/solidcraft-cli.exe" run \
  "D:/ink/solidcraft/01_materials_kinematics.json" \
  --in "D:/ink/solidcraft/CrossSlide_P014013.sc" \
  --save "D:/mydocuments/SolidCraft/CrossSlide_P014013_stage1.sc" \
  --results --json-out "D:/ink/refs/tmp/sc_stage1_results.json" --param-check warn

# 3) 阶段 2：GT2 传动链
".../solidcraft-cli.exe" run "D:/ink/solidcraft/02_drive_train.json" \
  --in "D:/mydocuments/SolidCraft/CrossSlide_P014013_stage1.sc" \
  --save "D:/mydocuments/SolidCraft/CrossSlide_P014013_stage2.sc" \
  --results --json-out "D:/ink/refs/tmp/sc_stage2_results.json" --param-check warn

# 4) 阶段 3：打码工作循环 study
".../solidcraft-cli.exe" run "D:/ink/solidcraft/03_coding_motion.json" \
  --in "D:/mydocuments/SolidCraft/CrossSlide_P014013_stage2.sc" \
  --save "D:/mydocuments/SolidCraft/CrossSlide_P014013_motion.sc" \
  --results --json-out "D:/ink/refs/tmp/sc_stage3_results.json" --param-check warn

# 5) 打开设计，复位后正式保存（重要，否则交付姿态会停在播放位置）
open  {path:"D:/mydocuments/SolidCraft/CrossSlide_P014013_motion.sc"}
execute {command:"motion.play", params:{study:424, step:0}}
execute {command:"file.save", params:{path:".../CrossSlide_P014013_motion.sc",
                                     format:"container", overwrite:true}}
```

注意事项：

- **路径沙箱**：SolidCraft MCP 只允许 `D:\mydocuments\SolidCraft`、recovery 与临时目录，`--in` 可以读 `D:/ink`，但 MCP 的 `open` / `screenshot` / `file.save` 写入必须落在允许目录，产物再拷回项目。
- `joint_id = 284 + (occ - 4)/2` 依赖导入顺序；若重新导出 STEP 改变产品名顺序，需重跑 `refs/tmp/sc_occ_map.json` 映射。
- `joint.list` 输出约 90 KB，会超工具上限自动落盘到 `tool-results/`，用脚本解析而不是直接读文本。
- `measure` 是独立 MCP 工具，不是 engine 命令；`execute {command:"measure"}` 会报 `unknown command`。

---

## 9. 文件清单

| 文件 | 说明 | sha256 |
|---|---|---|
| `solidcraft/CrossSlide_P014013_motion.sc` | **主交付**：v14 材质 + 完整运动链 + 打码 study，初始位 step 0 | `e93e75b0…` |
| `solidcraft/CrossSlide_coding_cycle.gif` | 打码循环动画，**1920×1200 / 29 帧 / 14.29 fps**，1.51 MB | `a1b5b46b…` |
| `solidcraft/CrossSlide_coding_step0.png` | Home 位等轴测渲染，1200×800 | `e9d317b1…` |
| `solidcraft/CrossSlide_coding_step45.png` | 扫描中途姿态渲染，1200×800 | `46c9bd61…` |
| `solidcraft/01_materials_kinematics.json` | 阶段 1 命令脚本（42 材质 + 100 关节命令） | — |
| `solidcraft/02_drive_train.json` | 阶段 2 命令脚本（6 revolute + 6 link） | — |
| `solidcraft/03_coding_motion.json` | 阶段 3 命令脚本（study 424） | — |
| `solidcraft/build_manifest.json` | 计数 / 关节 id / 材质分布 / 11.25 deg/mm | — |
| `solidcraft/MATERIAL_ASSIGNMENTS_SC.csv` | 144 行 body → 材质对照表 | — |
| `refs/scripts/build_solidcraft_motion.py` | 三阶段脚本生成器（可复现链唯一入口） | — |
| `refs/SOLIDCRAFT_MIGRATION.md` | 迁移报告（几何口径） | — |
| `solidcraft/CrossSlide_P014013_exploded.sc` | **爆炸视图设计**：在 motion 基线上派生 view 425，材质 / study / step 0 全保留 | `eb430e40…` |
| `solidcraft/CrossSlide_exploded.png` | 整机功能组爆炸图，2544×1957 / 852182 B | `c62fe382…` |
| `solidcraft/04_exploded_view.json` | 阶段 4 命令脚本（1 条 `explode.create` / 100 moves） | — |
| `solidcraft/EXPLODED_GROUPS.csv` | 140 行功能组 / 位移审计表 | — |
| `refs/scripts/build_exploded_view.py` | 功能组爆炸脚本生成器 V1 | — |
| `refs/SOLIDCRAFT_EXPLODED.md` | **爆炸图独立报告 V1**（分组、出图、踩坑、读回验证） | — |
| `solidcraft/CrossSlide_P014013_exploded_v2.sc` | **爆炸视图设计 V2**：view 425 `整机爆炸图 V2` / 127 moves（Z 电机 `[0,80,0]`），材质 / study / step 0 全保留，1815034 B | `87cf1163…` |
| `solidcraft/CrossSlide_exploded_v2_annotated.png` | **升级版最终图**：白底 + 11 组中文标注 + 装配顺序线 + 圆点分色核实，2209×1713 / 726769 B | `18ed3aba…` |
| `solidcraft/CrossSlide_exploded_v2_white.png` / `_v2.png` | V2 纯白底图 495295 B / 深灰底裁切源图 466129 B | `aa93bc1e…` / `83dd9035…` |
| `solidcraft/05_exploded_view_v2.json` | 阶段 5 命令脚本（1 条 `explode.create` / 127 moves），14845 B | `5e6eb6ff…` |
| `solidcraft/EXPLODED_GROUPS_V2.csv` / `EXPLODED_ANNOTATIONS_V2.csv` | V2 分组审计表 7382 B / 中文标注锚点审计表（含 `锚点来源`）2726 B | `9bd53abd…` / `4a8c774a…` |
| `refs/scripts/build_exploded_view_v2.py` / `annotate_exploded_view.py` | V2 更细分组生成器（Z 电机纯 +Y）/ 白底+中文+顺序线+锚点覆盖生成器 | `b710d35b…` / `574a3af8…` |
| `refs/scripts/verify_exploded_anchors.py` / `refs/tmp/exploded_v2_group_colours.png` | **圆点分色核实脚本 / 11 组纯色 ground-truth 渲染**（PASS 11/11） | `0f0eff40…` / `de9de474…` |
| `refs/SOLIDCRAFT_EXPLODED_V2.md` | **升级版爆炸图独立报告 V2**（含 4.7 电机轴向修正 / 4.8 圆点核实） | — |

---

## 10. 口径与限制（务必记住）

- **主模型仍是 `LM5UU Ø10×15 + Ø5 导杆`**：`X_LM5UU_*` / `Z_LM5UU_*` 对象名、BOM、材质名都还是 LM5UU。用户确认的「LM6UU / 内径 6 / 外径 12 / 长 19 / 导杆 Ø6」改造**尚未落盘**，本仿真搬的是磁盘当前状态；若实施改造，运动链需重新生成（零件名 / occurrence id 会变）。
- **3 个开放端板**未修复：`X_EndPlate_L`、`X_EndPlate_R`、`Part__Feature` 在 SolidCraft 里 `closed=false`、不能算体积 / 做布尔；它们在本仿真中只作视觉与机架参照。绕行方案见迁移报告第 5 节。
- **无 sketch 历史**：导入结果是 1 个 Import base feature + subcomponents + joints，几何精确但不能回滚建模步骤。
- **材质不联动 FreeCAD**：SolidCraft 的 21 个 user material 是按 v14 CSV 重建的独立对象，与 FreeCAD `ShapeMaterial` 的 UUID 无关联；改 FreeCAD 材质库后需重跑阶段 1。
- **仿真边界**：刚体机构仿真，不含喷墨时序、墨滴、接触力、柔性皮带 / 线缆、电机加减速曲线；`motion.interference` 是 26 个离散采样的检查，不是连续扫掠保证。
- **冻结项几何未动**：磁环下台阶 Z76.50、Hall 感测面 X83.40 / 中心 Z79.00、磁路 r=5.90、Z 限位槽 22.00、X 端板口袋 20.80、弹簧 k=0.045 N/mm、有效行程 0..+3.0 mm。

---

## 11. 遗留待办

1. **LM6UU / Ø6 导杆改造**：4 根导杆、4 块端板导杆孔、4 个轴承对象、轴承座 R6.05 与轴向挡肩、C 形弹性卡扣（195° 包角 / 开口 11.996 mm / 压入量 0.104 mm）、BOM / 材质 / 图纸，以及**重跑 SolidCraft 迁移与三阶段脚本**。
2. GitHub 推送仍等待重新授权（v13.2 几何 + v14 材质）。
3. `System_Assembly_A1.svg/.png/.pdf` 的 BOM 第 13 行已改为 `KW11-3Z-A-1`，图片尚未重出。
4. SolidCraft 侧 3 个开放端板（见迁移报告第 5 节）。
5. 可选增强：把保湿站盖合动作、喷墨触发信号、电机 S 曲线加减速补进 study；或把 `motion.trace` 的轨迹点改为喷嘴面中心而非 `HP45_Real:1` 上的固定点。

---

## 12. 功能组爆炸视图（2026-11-12 增补）

用户追加指令：「再生成一张爆炸图」。完整独立报告见 `refs/SOLIDCRAFT_EXPLODED.md`，本节只记要点。

**为何不用自动爆炸**：`explode.create {scale:...}` 在本 STEP 扁平组件树上报
`an exploded view needs two or more occurrences`；且逐 occurrence 径向散开会把 70 个紧固件甩散，
装配关系不可读。改为**显式 `moves`：一个功能组共享一个 translate**，组内紧固件随组整体移动。

| 功能组 | 件数 | `translate [dx,dy,dz]` mm |
|---|---:|---|
| Z 轴骨架（基准，不动） | 40 | `[0, 0, 0]` |
| Z 滑车 + XZ 连接板 | 23 | `[0, -40, 50]` |
| X 横梁总成 | 30 | `[0, -85, 0]` |
| X 滑车 | 10 | `[0, -150, 0]` |
| HP45 喷头总成 | 18 | `[-25, -235, 0]` |
| 接触式探针总成 | 13 | `[-115, -235, 0]` |
| 保湿站 | 6 | `[95, -55, 0]` |

合计 **100 条 moves + 40 个基准 occurrence = 140**，与 `refs/tmp/sc_occ_map.json` 逐一对应、
无重复、无遗漏（`EXPLODED_GROUPS.csv` 为审计表）。view id **425**，`整机爆炸图 / Assembly exploded`。

**可复现通道（阶段 4）**：`python refs/scripts/build_exploded_view.py` →
`solidcraft-cli run solidcraft/04_exploded_view.json --in <motion.sc> --save <exploded.sc> --param-check warn`
→ 应用内 `explode.show {view:425}` → `screenshot` → `explode.show {view:none}`。

**最重要的口径**：`explode.show` **只改显示，不改 placement / B-rep**。交付的
`CrossSlide_P014013_exploded.sc` 里几何、21 种材质、study 424、step 0 全部与 `motion.sc` 一致；
打开文件默认是装配态，需手动 show 爆炸视图。出图采用「高分辨率渲染 4096×3840 +
PIL 按模型 bbox 加 4.5% 边距裁切」，最终 `CrossSlide_exploded.png` 为
**2544×1957 / 852182 B / 模型占画面 91.7%**。

---

## 13. 升级版爆炸图 V2（2026-11-12 增补）

用户三条追加指令合并成一张图：「爆炸图上用中文标明部件的名称，用线条标明空间装配的顺序和逻辑」
/「爆炸图背景改为白色」/「爆炸图还能再多炸开一些零部件吗？」。
完整独立报告见 `refs/SOLIDCRAFT_EXPLODED_V2.md`，本节只记要点。

| 项目 | V1（第 12 节） | **V2** |
|---|---|---|
| 移动 occurrence | 100 | **127** |
| 固定基准 | 40（端板/导杆/带传动/电机/限位挤在一起） | **12**（真机架：`Z_BaseBlock`+`Z_Profile`+2 tap+8 螺钉） |
| 功能组 | 6 组 + 1 基准 | **10 组 + 1 基准 + 1 隐藏辅助** |
| 背景 | 深灰 `[46,52,64]` | **纯白** |
| 中文标注 / 顺序线 | 无 | **11 组中文名称 + 序号 + 引线 + 主链 1→10 + 并行支路 1→11** |

**更细爆炸**：`build_exploded_view_v2.py` 把 V1 的 40 件基准拆成 5 个 Z 轴子组
（端板与导杆 8 `[70,-25,30]` / 同步带传动 7 `[120,-75,65]` / **步进电机 6 `[0,80,0]`** /
限位开关 6 `[175,-170,25]` / Z 滑车 + XZ 板 23 `[0,-80,95]`），并加大原有 6 组位移
（喷头 `[-50,-350,0]` / 探针 `[-185,-350,0]` 等）。生成器增加约束：`ground` 除
`Part__Feature` 外必须为空，逼着把 40 件全部归类。view id 仍 **425**，name 改为
`整机爆炸图 V2 / Assembly exploded V2`。
> Z 电机是唯一不扇出的组：位移由初版 `[-90,-35,60]` 修正为**纯 +Y 抽出 `[0,80,0]`**，
> 依据 4 颗 `Z_Screw_Motor_*` 的 `5.49×13.00×5.48 mm` 包围盒（长轴 Y）与电机本体 / 轴伸
> 分别在 +Y / −Y 侧；详见 V2 报告 4.7 节。

**白底**：SolidCraft 只有 `render.stage.backdrop`（物理布景），没有 viewport 纯色背景命令；
CLI `snapshot` 是浅灰渐变 `[240,243,247]` + 地平线且底部裁切，弃用；改用 MCP `screenshot`
的纯深灰底，再由 `annotate_exploded_view.py::to_white()` 用 alpha 近似 + `MaxFilter(3/5)`
边缘权重把背景与抗锯齿边一并换白。取景用 `render.camera.fit {aspect:1.3}` +
4096×3150 截图 + bbox 裁切 → `CrossSlide_exploded_v2.png` 2209×1323。

**中文标注与装配顺序**：11 个锚点由 `geometry_snapshot_v14.json` 的逐件 3D bbox +
V2 位移经正交等轴测投影（yaw −45° / pitch 35.264°，`u=0.866·(X+Y)`、`v=0.5·(X−Y)−Z`）
自动定标，**最终 `scale=2.4371 px/mm`**（Z 电机改位后相机重 fit 由 2.5906 重算；初版值已作废），
非手工点选。标签用积分图避让（`cost=0.8|Δx|+1.5|Δy|+3·occ`，框 `290×76`），
11 框与模型重叠 ≈0（最大 0.01%）。细实线引线 / 粗虚线箭头主链 / 绿色并行支路
全部加**白色 halo**，保证压在深色零件上仍清晰。

**读回验证（与 V1 同等权威）**：`open errors=0`、`explode.list` 425/127 moves、
`motion.list` study 424/100 steps/3 keys、`joint.inspect 303/338/411` 三 slider `value 0.0`
且 11.25 deg/mm `motion_link` 完好、`material.list` 21 个 user material、
`explode.show {view:425}` 正常 —— 几何 / 材质 / study / step 0 与 `motion.sc` 完全一致。

**序号牌去碰撞（出图后修正）**：用户截图反馈「这个 3 跟它后面的啥重叠了」。序号 3「Z 同步带传动」
与序号 2「Z 端板与导杆」的投影锚点仅相距 13.5 px、徽标直径 42 px，后画的 3 把 2 盖住。
`annotate_exploded_view.py` 新增 `place_badges()` 把冲突徽标对称推开至 ≥52 px（各移 19.8 px →
53.2 px），装配顺序链改连徽标而非锚点，被推开的牌用组内同色短细线回指真实锚点。
只改标注层，不动 `.sc` / 3D / 口径；详见 `refs/SOLIDCRAFT_EXPLODED_V2.md` 4.6 节。

**引线圆点分色核实（收尾修正）**：用户要求「核实圆点与部件是否正确对应」并指出
「5 限位开关的标识没有指向限位开关上」。投影质心只是估算，会落在拆散零件的空隙、
被更近的组挡住或落在背景。做法是给 11 组各赋一个纯色（`DOTCHK_01..11`）、**把 127 条
moves 烘焙进 occurrence 变换**（`explode.show` 只改显示，离屏 CLI 快照会渲染成装配态；
变换平移在**第 3 行** `T[3][i] += t[i]`，写 `T[i][3]` 会 `invalid placement`）、
用同一相机渲染，再按**色度** `(r,g,b)/sum` 多数投票读回每个圆点下的组。
查出 4 个错点：序号 2/3 互换、序号 5 旧点 `(1696,786)` 落在红色「Z 轴机架」上、
序号 10 落在背景 → 用 `ANCHOR_OVERRIDES` 覆盖为 `(1867,255)` / `(1822,220)` /
`(1720,974)`（下方 KW11-3Z-A-1 本体）/ `(195,802)`。审计 CSV 新增 `锚点来源` 列，
新增 `refs/scripts/verify_exploded_anchors.py`，实跑
**`PASS: all 11 leader dots sit on their own functional group`（4 覆盖 + 7 投影）**。
锚点拉开后最小序号牌间距 57.0 px、`displaced_badges = {}`，`place_badges()` 保留为兜底。
详见 V2 报告 4.8 节。

**最终图**：`CrossSlide_exploded_v2_annotated.png` **2209×1713 / 726769 B / `18ed3aba…`**
（原图 1323 + 标题带 150 + 图例带 240），四边 100% 纯白、无裁切、`exact_white 83.53%`；
中文为真实抗锯齿 CJK 字形（148 级灰度）。白底版 495295 B / `aa93bc1e…`、
深灰源图 466129 B / `83dd9035…`、可编辑 `.sc` 1815034 B / `87cf1163…`。

> 口径限制同第 10 节：127 条 `moves` 绑定 occurrence id、标注锚点绑定等轴测相机；
> 重跑迁移 / 实施 LM6UU 改造 / 再改任一组位移后必须**依次**重生成 V2 脚本 → 重新 fit 相机 →
> 重出标注 → 重跑 `verify_exploded_anchors.py`，否则 4 个分色覆盖坐标会立刻失效；
> PNG 是带标注渲染图，不是工程图。
