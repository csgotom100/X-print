# SolidCraft LM6UU / Ø6 导杆局部重设计（X + Z 两轴）

> 日期：2026-11-13 · 本文覆盖**两代方案**：
> **§1–§10 = 混合式 `LM6UU_Redesign.sc`（历史中间方案，已被用户推翻，仅作对照）**；
> **§11 起 = 全原生 `LM6UU_Native.sc`（当前权威交付）**。
>
> 用户最终口径：「**我要求你全部在solidcraft重新参数化设计，目的是为了修改设计时都能编辑**」，
> 界面选择「语义化参数化」+「也改成原生参数化」。因此当前权威设计是
> `solidcraft/LM6UU_Native.sc`（878047 B，零 STEP 导入、104 参数全部可编辑），
> **不要再把 §1–§10 的混合方案当作最终交付**。
> 本项目其它设计（`CrossSlide_P014013_motion.sc`、`..._exploded_v2.sc`、动画、爆炸图、主 FCStd）**均未改动**。

---

## 1. 需求与范围

用户口径：

> 「不是重新设计整个项目，是因为直线轴承的更改，滑台两端的结构件要重新设计，铝型材不变，滑车也要重新修改参数」

界面确认的三项选择：

| 项 | 选择 |
|---|---|
| 轴承夹持方式 | **保留上下两半 + M3 合拢** |
| 设计文件 | **新建独立参数化设计**（不动现有 `motion.sc`） |
| 改造范围 | **X + Z 两轴全改** |

外购件实测规格（用户确认）：**LM6UU，内径 Ø6 / 外径 Ø12 / 长度 19**；导杆 **Ø6**。
磁盘上原模型为 **LM5UU Ø10×15 + Ø5 导杆**，故 8 件必须改：

```
X_EndPlate_L / X_EndPlate_R / Z_EndPlate_L / Z_EndPlate_R
X_Carriage_Lower / X_Carriage_Upper / Z_Carriage_Lower / Z_Carriage_Upper
```

**明确不变**：`X_Profile`、`Z_Profile` 两根 2040 铝型材；全部冻结项；探针总成 / 磁路 / v13.2 / v14 材质。

---

## 2. 设计结论

| 检查项 | 结果 |
|---|---|
| 几何改造去料处数 | **16**（滑车主座 8 + 端板导杆孔 8） |
| 逐件 `closed / valid / bbox 不变` | **8/8 PASS** |
| 冻结项 Z 槽 22.00 / X 口袋 20.80 | **零改动 PASS** |
| 新件与改后件 / 型材干涉 | **0 对** |
| LM6UU 双向轴向挡肩 | **4/4 PASS**（±2 mm 平移均与滑车实体重叠） |
| 铝型材 | 真几何原样插入，体积 / bbox 一字未改 |
| SolidCraft 参数 | 16 个，表达式互相引用，可联动 |
| SolidCraft 实时参数化切除 | **8 处滑车主座**（另 8 处端板导杆孔在 FreeCAD 侧预切，见 §5.4） |
| 最终 `.sc` | 18 body / 23 时间线特征 / **error 0** / 44 命令全部成功 |
| SolidCraft 内实测冻结尺寸 | Z 槽 **22.000 mm**、X 口袋 **20.800 mm**（`inspect.measure` 面对面） |
| SolidCraft 内干涉 | **0 对**，全配对检查完成、`pairs_not_checked = 0` |

核心洞察：**LM6UU 改造全部是「去料」**。原滑车本来就是

```
导入段 R4.70 → 主座 R5.00×15.60 → 过渡 R4.80 → 出口 R5.10（总长 33）
```

只需把主座放大为 **R6.05 × 19.20**，两端剩余的 R4.70 / R5.10 自动变成**双向轴向挡肩**，
把 Ø12 的 LM6UU 明显卡住 —— 这正是用户指出「现在的结构设计不能明显卡住直线轴承」要解决的问题。
因此无需重画零件，保留全部真实接口即可。

---

## 3. 参数表

完整表见 `solidcraft/LM6UU_PARAMS.csv`。摘要：

| 参数 | 原值 (LM5UU) | 新值 (LM6UU) | 依据 |
|---|---|---|---|
| `BRG_OD` | Ø10.00 | **Ø12.00** | LM6UU 规格 |
| `BRG_ID` / `ROD_D` | Ø5.00 | **Ø6.00** | LM6UU 内孔 / 导杆 |
| `BRG_L` | 15.00 | **19.00** | LM6UU 规格 |
| `SEAT_R` | R5.000 | **R6.050** | `BRG_OD/2 + 0.05 mm` 单边间隙 |
| `SEAT_L` | 15.60 | **19.20** | `BRG_L + 0.2 mm`，两端各留 0.10 |
| `ROD_HOLE_R` | R2.750 | **R3.050** | `ROD_D/2 + 0.05 mm` |
| `PILOT_R` / `EXIT_R` | R4.700 / R5.100 | **不变** | 形成前后轴向挡肩 |
| `M3_R` | R1.700 | **不变** | 上下两半 + M3 合拢 |
| `Z_SLOT_W` / `X_POCKET_W` | 22.00 / 20.80 | **不变** | 【冻结】用户明令 |

**主座轴向尺寸**：X 轴 `X140.40..159.60`（Z 位 122 / 152）；Z 轴 `Z127.40..146.60`（X 位 135 / 165）。
轴承位置相应为 X `X140.50..159.50`、Z `Z127.50..146.50`，两端各留 0.10。

**弹簧 / 力系不变**：本次改造与探针弹簧无关；`k=0.045 N/mm`、`F0=0.045 N`、满程 `0.180 N` 全部沿用。

---

## 4. 为什么用「真实几何 + 参数化特征」，而不是方盒重建

最初方案是用 `solid.box` 原语把 8 件全部重建。核查接口数据后否决：

* `X_EndPlate_L` 是 **218 面 / V=19096.771 mm³** 的高度镂空阶梯框架，
  `X_EndPlate_R` 220 面、体积填充率仅约 21%。用 3~4 个方盒无法复现，
  且会丢掉 45° 倒角、GT2 皮带让位槽与全部安装孔位。
* 原滑车已存在完整的 R4.70 / R5.00 / R4.80 / R5.10 阶梯半圆座和 M3 合拢孔
  （X 位 144/156 @ Z137；Z 位 Z131/143 @ X150），重建等于把已验证的设计推倒。

最终采用：

```
FCStd 裸 BREP 直读 → 参数驱动的 16 处去料（FreeCAD 全量验证）
   → named STEP（8 处端板导杆孔已预切，4 滑车半体保留原几何）
   → SolidCraft file.insert_step（真几何，接口 100% 保真）
   → 8 处 solid.cylinder 实时参数化主座切除 + 8 个原生参数化实体
   → LM6UU_Redesign.sc
```

---

## 5. 两个必须绕开的坑（实测）

### 5.1 SolidCraft STEP 导入器丢弃 X 端板的 49 个面

`X_EndPlate_L / R` 经 STEP 导入 SolidCraft 后 `closed=false`，
`faces` 从 218/220 降到 169/171（`kernel.faces` 仍是 218/220）。
所有面都是 `Plane` / `Cylinder`，不是曲面类型问题；实测以下手段**全部无效**：

* `Import.export` / `exportStep` / `makeSolid(shell)` 四种导出变体
* `fixTolerance(1e-3 / 1e-2 / 5e-2)` + `sewShape()` + `fix()`
* `removeSplitter()` 开 / 关

在开放体上做 `solid.cylinder cut` 会**无限挂起**（实测 >165 s 未完成，已终止）。
因此这两件的 4 处导杆孔由 `build_lm6_geometry.py` 在 FreeCAD 侧预切。

### 5.2 FreeCAD 中 X 端板 cut 之后不能 `removeSplitter()`

实测 `X_EndPlate_L/R` 原始 BREP `valid=True`，但 `cut()` 之后调用
`removeSplitter()` 会退化成 `valid=False`（体积与对称差全部失真）。
`build_lm6_geometry.py` 全程**不做 refine**，切完直接用，8 件 `valid=True`。

### 5.3 20.80 冻结口袋的 0.05 mm 交界

`X_EndPlate_L` 的 Z=122 导杆孔（中心 Y=-68，R3.05 → Y 到 -71.05）与
冻结口袋保护区（Y-79..-71）只差 0.05 mm，整圆刀具会削掉口袋壁 **0.2736 mm³**。
处理：刀具先 `cut` 掉冻结保护区再切，`frozenLost = 0.00000000`，
且刀具 / 结果 BREP 均 `valid=True`。

### 5.4 第 41 步 `boolean Cut: no result` —— 端板扩孔布尔整体下放到 FreeCAD

初版 `06_lm6_redesign.json` 有 48 条命令，试图让 4 个 Z 端板导杆孔也在
SolidCraft 里做实时参数化切除。首次执行耗时 5 min 8 s 后失败：

```
error: step 41 (solid.cylinder): boolean Cut: the operation failed: no result
```

第 41 步是 `ZR_RodBore_X135`（`Z_EndPlate_R`，R3.05×7.9，base `[135,-12,211.9]`）。
排查链：

1. `solidcraft-cli eval LM6UU_base6.step`：6 件**全部** `closed=true`，
   `Z_EndPlate_R` 93 面 / V=23059.432 mm³，与 FreeCAD 一致 → 不是开壳问题。
2. 圆柱轴向探针：base z=100 / h=5 / `axis:"Z"` → bbox `100..105`，
   确认是**沿 +Z 拉伸**，坐标没写反。
3. 加长刀具（209..223）单独对 `Z_EndPlate_R` 切除，`timeout 180 s` 被 SIGTERM；
   而「只插入 STEP + 保存」只要 0.7 s → 布尔本身挂起。
4. 结论：STEP 导入的复杂端板上做**同心细环形扩孔**（R2.75 → R3.05，单边
   仅 0.30 mm）会让 OCC 布尔长时间不收敛；`Z_EndPlate_L` 那一步虽成功也极慢。

修复：把 4 个 Z 端板孔也并入 `build_lm6_geometry.py` 的预切流程，
`LM6UU_base6.step` 改为「2 个 Z 端板已预切 + 4 滑车未改」，`06` 脚本删掉
这 4 条切除命令（48 → **44 条**）。只对简单的滑车半体保留 8 处实时特征
（实测约 1.8 s/步）。`ROD_HOLE_R` 参数与 CSV 口径保留，端板几何由
FreeCAD 侧同一参数值生成，不重复布尔。

修订后 `solidcraft-cli run` **44/44 成功、0 error**，用时从 5 min+ 降到秒级。

---

## 6. 几何验证（`refs/tmp/lm6_geometry_report.json`，CONCLUSION PASS）

```
PART X_EndPlate_L      19096.771 -> 19015.595  Δ=  -81.175  added=0 closed/valid OK bbox OK
PART X_EndPlate_R      20869.194 -> 20787.198  Δ=  -81.996  added=0 closed/valid OK bbox OK
PART Z_EndPlate_L      41521.447 -> 41439.994  Δ=  -81.453  added=0 closed/valid OK bbox OK
PART Z_EndPlate_R      23059.448 -> 22977.452  Δ=  -81.996  added=0 closed/valid OK bbox OK
PART X_Carriage_Lower  13295.278 -> 12577.223  Δ= -718.055  added=0 closed/valid OK bbox OK
PART X_Carriage_Upper  12457.113 -> 11739.058  Δ= -718.055  added=0 closed/valid OK bbox OK
PART Z_Carriage_Lower  13295.278 -> 12577.223  Δ= -718.055  added=0 closed/valid OK bbox OK
PART Z_Carriage_Upper  20503.537 -> 19785.482  Δ= -718.055  added=0 closed/valid OK bbox OK
FROZEN Z_SLOT_W_22.00     OK {}
FROZEN X_POCKET_W_20.80   OK {}
INTERFERENCE pairs_over_1e-3 = 0
RETENTION 4/4 OK (+2mm 59.631 mm3 / -2mm 83.029 mm3)
```

* `added=0` 说明是**纯去料**，没有偷偷加料。
* `bbox 不变` 说明外形与安装面完全保真。
* 干涉检查覆盖：4 个 LM6UU + 4 根 Ø6 导杆 × 8 件改后件 × 2 根铝型材。
* 挡肩检查：把 LM6UU 沿轴向平移 ±2 mm，与滑车实体重叠 59.631 / 83.029 mm³
  → 两端确实有台阶，轴承无法轴向脱出。

其它冻结项（磁环腔 2.00、霍尔 X83.40 / Z79.00 / r5.90）位于探针总成，
本次 8 件改动件完全不涉及，天然未动。

---

## 7. SolidCraft 设计结构

`solidcraft/06_lm6_redesign.json`，**44 条命令，全部执行成功**：

| 段 | 命令数 | 内容 |
|---|---|---|
| 参数 | 16 | `parameters.add`，含 `SEAT_R = BRG_OD / 2 + 0.05 mm` 等联动表达式 |
| 原生参数化实体 | 12 | 4 根 Ø6 导杆 + 4 个 LM6UU 外圆 + 4 个内孔 |
| 真几何插入 | 3 | `LM6UU_base6.step` / `LM6UU_xplates_lm6.step` / `LM6UU_reference_profiles.step` |
| 实时参数化切除 | **8** | 4 滑车半体 × 2 主座，`SEAT_R × SEAT_L` |
| 外观 | 4 | PETG 蓝 / 铝型材银 / 轴承钢深灰 / 导杆亮钢 |
| 保存 | 1 | `solidcraft/LM6UU_Redesign.sc` |

形成的 3 个导入组件 + 1 个根组件：

```
LM6_Base6_Structural        Z_EndPlate_L/R（已预切 Ø6.10 导杆孔）+ 4 滑车半体（靠实时特征改）
LM6_XEndPlates_Prebored     X_EndPlate_L/R（已预切 Ø6.10 导杆孔）
Aluminium_Profiles_UNCHANGED  X_Profile / Z_Profile（原样，不变）
(root)                      4 × X/Z_GuideRod + 4 × X/Z_LM6UU（原生参数化）
```

共 **18 个 body**：8 结构件 + 2 铝型材 + 4 导杆 + 4 轴承。
`eval` 读回：23 个时间线特征、**error 0**；2 条 warning 是 X 端板导入为
open body（§5.1 已知且可接受，不做布尔、不参与体积/质量统计）。
`appearance.list` 读回 18 个 body 均有颜色；`material` 字段是物理密度
（默认 Default），与外观颜色是两套独立属性。

**参数化边界（重要，勿把本设计理解为「全参数化重建」）**

本设计是**混合式**：真实 BREP 保真 + SolidCraft 原生参数化特征叠加。
SolidCraft 时间线上的 23 个特征里，只有下列内容是真正可用参数驱动的：

| 类别 | 数量 | 是否 SolidCraft 原生 / 参数联动 |
|---|---|---|
| Ø6 导杆 | 4 body | ✅ 原生 `solid.cylinder`，`ROD_D` / `ROD_X_LEN` / `ROD_Z_LEN` 驱动 |
| LM6UU 轴承 | 4 body（各 2 特征） | ✅ 原生 new + cut，`BRG_OD` / `BRG_ID` / `BRG_L` 驱动 |
| 滑车主座切除 | 8 特征 | ✅ 实时参数化 `cut`，`SEAT_R` / `SEAT_L` / 座起点驱动 |
| 滑车 / 端板**主体几何** | 8 body | ❌ STEP 导入哑实体，无草图、无特征树、不可参数化编辑 |
| 端板导杆孔（Ø6.10） | 8 处 | ❌ FreeCAD 侧预切，SolidCraft 内**无对应特征、不随参数变化** |
| 铝型材 | 2 body | ❌ 原样导入（按用户口径本就不改） |

16 个参数中，**10 个驱动几何**：`BRG_OD`、`BRG_ID`、`BRG_L`、`ROD_D`、
`SEAT_R`、`SEAT_L`、`X_SEAT_X0`、`Z_SEAT_Z0`、`ROD_X_LEN`、`ROD_Z_LEN`；
**6 个为设计口径 / 冻结项记录，不联动任何 SolidCraft 几何**：
`ROD_HOLE_R`、`PILOT_R`、`EXIT_R`、`M3_R`、`Z_SLOT_W`、`X_POCKET_W`
（前 4 个的实际值写在 `build_lm6_geometry.py` 的 `P_` 字典里，后 2 个是冻结项校验目标）。

因此「改 `ROD_HOLE_R` 就能让端板孔跟着变」**当前不成立**；要达成需让
`build_lm6_geometry.py` 与 `build_lm6_redesign.py` 共用同一份参数真源并重新导出
STEP（几何不变，但两个 STEP 与 `.sc` 的字节 / hash 会变，需重跑 §9 复现链）。
完全用 SolidCraft 原生原语重建 8 件结构件已被 §4 否决：X 端板是 218 面、
约 21% 填充率的镂空框架，重建会丢失冻结槽、45° 倒角、GT2 皮带让位槽与 M3 孔位。

### 7.1 SolidCraft 内独立复核（不是只靠 FreeCAD 报告）

* **冻结项实测**：`inspect.measure` 选两面 →
  `Z_EndPlate_L` X139.00 / X161.00 两面 `min = 22.000 mm`；
  `X_EndPlate_L` Z120.85 / Z141.65 两面 `min = 20.800 mm`。
* **干涉**：`inspect.interference` 分两次覆盖全部 18 个 body。
  第一次 120 s 预算内有 16 对未查完（铝型材 × 端板最慢，48.5 s/对），
  第二次把这 16 对所在的 14 个 body 单独跑 420 s 预算 →
  `checked 14 / count 0 / pairs_not_checked 0 / budget_exceeded false`。
  两次合计 **0 处实体重叠**（Ø6 导杆与 Ø6 轴承内孔、Ø12 轴承与 Ø12.10 座
  均为零间隙设计，未产生体积干涉）。
* **关键尺寸**：LM6UU `V=1611.484 mm³`（理论 π(6²−3²)·19 = 1611.6）；
  X 导杆 `6077.702` / Z 导杆 `4664.490 mm³`；
  `X_Profile 60564.140` / `Z_Profile 45423.068 mm³` 且 bbox 与原始一致。
* **装配保真**：4 个滑车半体切后体积 `12577.418 / 11739.255 / 12577.456 /
  19785.740 mm³`，与 FreeCAD 报告的 `12577.223 / 11739.058 / 12577.223 /
  19785.482` 相差 < 0.26 mm³（STEP 精度），说明 8 处实时切除落地正确。

---

## 8. 与原设计链的关系（重要）

本次是**独立新设计**，不修改任何现有 `.sc` / STEP / 图纸：

* `CrossSlide_P014013_motion.sc`（材质 / 运动树 / study 424）、`CrossSlide_coding_cycle.gif`、
  `CrossSlide_P014013_exploded_v2.sc`、V2 中文标注爆炸图 —— **全部保持原状**。
* 主 FreeCAD 模型 `CrossSlide_P014013.FCStd` —— **未写入**，仍是 v13.2 几何 + v14 材质。
  本次改造只从它读取 BREP 作输入。

若将来要把 LM6UU 改造合并回主设计，零件名 / occurrence id 会变化，必须按顺序重跑：

```
STEP 迁移核验 → 三阶段运动脚本 → V2 爆炸脚本 → 相机 fit → 中文标注
→ verify_exploded_anchors.py 分色圆点核实
```

顺序不可颠倒（见 `refs/SOLIDCRAFT_EXPLODED_V2.md` 第 4.7/4.8 节）。

---

## 9. 复现

```bash
# 1) 从 FCStd ZIP 提取 140 个裸 BREP（只跑一次）
"/d/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" refs/scripts/extract_lm6_interfaces.py
"/d/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" refs/scripts/export_lm6_reference_step.py

# 2) 参数驱动的 16 处去料 + 全量验证 + 3 个 named STEP
"/d/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" refs/scripts/build_lm6_geometry.py
#    -> refs/tmp/lm6_geometry_report.json 必须 CONCLUSION PASS

# 3) 生成 SolidCraft 命令脚本
python refs/scripts/build_lm6_redesign.py

# 4) 执行并保存 .sc（44 条命令，exit 0）
"/d/Program Files/SolidCraft/solidcraft-cli.exe" run solidcraft/06_lm6_redesign.json \
    --results --json-out refs/tmp/lm6_stage1_results.json --param-check warn

# 5) 独立复核：body / 参数 / 时间线，冻结尺寸，全配对干涉
SC="/d/Program Files/SolidCraft/solidcraft-cli.exe"
"$SC" eval solidcraft/LM6UU_Redesign.sc --json-out refs/tmp/lm6_design_eval.json
"$SC" run refs/tmp/lm6_verify.json  --in solidcraft/LM6UU_Redesign.sc --results \
    --json-out refs/tmp/lm6_verify_results.json
"$SC" run refs/tmp/lm6_verify2.json --in solidcraft/LM6UU_Redesign.sc --results \
    --json-out refs/tmp/lm6_verify2_results.json

# 6) 出图（整机 3200x2000 -> 白底紧裁；近景 1800x1200 保留原始渐变底）
"$SC" snapshot solidcraft/LM6UU_Redesign.sc --out refs/tmp/lm6_iso_hi.png \
    --width 3200 --height 2000 --view iso --no-grid --no-axes
"$SC" snapshot solidcraft/LM6UU_Redesign.sc \
    --out solidcraft/LM6UU_Redesign_seat_detail.png \
    --width 1800 --height 1200 --no-grid --no-axes \
    --camera '{"target":[150,-68,137],"yaw":0.785,"pitch":0.5,"distance":180,"fov":0.55}' \
    --body X_Carriage_Lower:opacity=0.28 --body X_Carriage_Upper:opacity=0.28 \
    --body X_LM6UU_1:color=#e8623a --body X_LM6UU_2:color=#e8623a
python refs/scripts/render_lm6_views.py
```

---

## 10. 文件清单

| 文件 | 说明 |
|---|---|
| `solidcraft/LM6UU_Redesign.sc` | **最终交付**：独立参数化设计，564301 B |
| `solidcraft/LM6UU_Redesign_iso.png` | 整机白底等轴测图（1162×1241） |
| `solidcraft/LM6UU_Redesign_seat_detail.png` | 轴承座近景：滑车半透明 + LM6UU 橙色高亮（1800×1200） |
| `solidcraft/06_lm6_redesign.json` | 44 条 SolidCraft 命令 |
| `solidcraft/LM6UU_PARAMS.csv` | 参数表（旧值 / 新值 / 依据） |
| `solidcraft/LM6UU_base6.step` | 6 件（2 Z 端板已预切 + 4 滑车未改） |
| `solidcraft/LM6UU_xplates_lm6.step` | 2 件已预切 X 端板 |
| `solidcraft/LM6UU_reference_profiles.step` | 2 根铝型材真几何（不变） |
| `solidcraft/LM6UU_interfaces.json` | 8 件接口几何清单（bbox / 体积 / 孔位） |
| `refs/tmp/lm6_geometry_report.json` | FreeCAD：几何 / 冻结 / 干涉 / 挡肩报告（PASS） |
| `refs/tmp/lm6_design_eval.json` | SolidCraft：18 body / 16 参数 / timeline error 0 |
| `refs/tmp/lm6_verify_results.json` | SolidCraft：22.000 / 20.800 mm 实测 + 第一轮干涉 |
| `refs/tmp/lm6_verify2_results.json` | SolidCraft：补齐干涉，`checked 14 / count 0 / unchecked 0` |
| `refs/scripts/build_lm6_geometry.py` | 几何生成 + 全量验证 + 3 个 STEP |
| `refs/scripts/build_lm6_redesign.py` | SolidCraft 命令脚本生成器 |
| `refs/scripts/render_lm6_views.py` | 整机图渐变底转白 + 紧裁 |
| `refs/scripts/extract_lm6_interfaces.py` | FCStd BREP 提取与接口分析 |
| `refs/scripts/export_lm6_reference_step.py` | 铝型材 STEP 导出 |

---
---

# 第二部分：全原生语义化参数化设计（§11 起为当前权威）

## 11. 需求变更与最终范围

用户质疑混合方案后明确推翻：

> 「在solidcraft参数化设计的吗？」
> 「**我要求你全部在solidcraft重新参数化设计，目的是为了修改设计时都能编辑**」

界面确认两项：

| 项 | 选择 |
|---|---|
| 端板重建方式 | **语义化参数化**（按设计意图重建，不追求几何 1:1 复刻） |
| 2 根 2040 铝型材 | **也改成原生参数化** |

最终口径（覆盖 §1 的「铝型材不变、只做局部去料」）：

```
8 件结构件 + 2 根铝型材 = 全部 SolidCraft 原生特征重建
零 STEP 导入（file.insert_step = 0）
所有关键尺寸 / 坐标 / 冻结项都是命名参数，改参数即可重算
端板按设计意图语义化重建：保留外形 bbox、安装孔位、冻结槽、
  主座 R6.05×19.20、Ø6.10 导杆孔、M3 合拢孔位；
  装饰性镂空允许差异，体积允许几个百分点差别
```

被否决的路线：`refs/scripts/build_native_recipe.py` 自动盒分解复刻端点几何 —— `X_EndPlate_L` 需 95 个碎盒且 `box_V 23488.014` vs `orig 19096.771`（+23%），`X_EndPlate_R` 110 盒、`Z_EndPlate_L` 44 盒，特征树不可读、不利编辑。

## 12. 为什么必须放弃混合方案

§7「参数化边界」已经说明混合方案的 8 件结构件主体是 STEP 哑实体、端板 8 处孔在 FreeCAD 侧预切、**改参数不会联动**。此外 §5.1 记录 SolidCraft STEP 导入器会丢 `X_EndPlate_L/R` 各 49 个面并判为 open body，在开放体上做布尔会无限挂起。这两点是「改设计时都能编辑」无法绕过的硬障碍，因此不是打补丁，而是整条建模路线重做。

前置分析产物：

| 产物 | 结论 |
|---|---|
| `refs/scripts/extract_native_recipe.py` → `refs/tmp/lm6_native_recipe.json` | 8 件结构件全部只有 `Plane` / `Cylinder` 面，**`Cone = 0`**，可用 box + cylinder + fillet 语义化表达 |
| `refs/tmp/shape_diag.log` | 完整圆柱特征清单 + 4 件端板代表性截面 ASCII |
| `refs/tmp/void_diag.json` | 端板空隙是单一复杂连通块 → 自动复刻必然碎片化 |

## 13. 全原生设计结构

生成器 `refs/scripts/build_lm6_native.py` → `solidcraft/07_lm6_native.json`，**224 条命令全部执行成功（exit 0）**：

```
104  parameters.add      ← 全部为用户参数，表达式可互相引用
 36  solid.box           ← 法兰板 / 纵梁 / 立柱 / 皮带槽 / 型材本体
 74  solid.cylinder      ← 导杆、LM6UU、阶梯轴承座、导杆孔、M3 孔 / 沉孔、型材中心通孔
  4  solid.fillet        ← 4 件滑车半体四角 R4
  5  appearance.assign   ← PETG 端板 / PETG 滑车 / 铝型材 / 轴承钢 / 导杆钢
  1  file.save           → solidcraft/LM6UU_Native.sc (878047 B)
  0  file.insert_step    ← 零 STEP 导入
```

参数表 `solidcraft/LM6UU_NATIVE_PARAMS.csv`（104 行 + 表头）按 A–G 分组：轴承导杆、端板、滑车、冻结项、型材、加工余量等；`parameters.list` 读回 `count 104 / cycles [] / errors []`，**无未引用参数**。

形成的 **18 个 body**（名称与混合方案一致，便于对照）：

```
8 结构件  X/Z_EndPlate_L/R、X/Z_Carriage_Lower/Upper
2 型材    X_Profile、Z_Profile（原生 box + 参数化中心通孔，非真薄壁型腔）
4 导杆    X/Z_GuideRod_1/2（Ø6）
4 轴承    X/Z_LM6UU_1/2（Ø12 × Ø6 × 19）
```

`eval` 读回：**18 body / 104 params / 114 timeline 特征 / `open_bodies_skipped 0` / `timeline errors 0` / 总体积 397775.42 mm³**。

## 14. 关键建模决策与冻结项保真

| 决策 | 口径 |
|---|---|
| 轴承主座 | `SEAT_R = BRG_OD / 2 + 0.05 mm` = **R6.05**，`SEAT_L = BRG_L + 0.2 mm` = **19.20**；两端 `R4.70 / R5.10` 保留为双向轴向挡肩 |
| 端板导杆孔 | `ROD_HOLE_R = ROD_D / 2 + 0.05 mm` = **R3.05（Ø6.10）**；本次是 SolidCraft 内**原生 cut 特征**，随参数联动 |
| M3 合拢 | 上下两半 + 2×M3 通孔 + 2×沉孔，孔位由命名参数驱动（X 位 144/156 @ Z137；Z 位 Z131/143 @ X150） |
| 冻结 Z 槽 | `Z_SLOT_W = 22 mm` 直接驱动 `Z_EndPlate_L` 槽宽，实测 **22.000 mm** |
| 冻结 X 口袋 | `X_POCKET_W = 20.8 mm` 驱动 `X_EndPlate_L` 口袋，实测 **20.800 mm** |
| 铝型材 | 2040 接口尺寸不变，`solid.box` 原生表达 + `PROF_CORE_D = 6 mm` 参数化中心通孔（语义化挤压截面，非真实薄壁型腔） |
| 语义化差异 | 端板内部装饰性镂空按设计意图重新组织，体积与原 BREP 允许几个百分点差别；外形 bbox 与全部安装 / 冻结接口保持 |

## 15. 三个 OCC 布尔坑与修复（实测）

### 15.1 step 164 `cavity ownership is ambiguous`

```
error: step 164 (solid.cylinder):
lumps: shell boundaries intersect or touch; cavity ownership is ambiguous
```

按检查点逐个保存 `.sc` 并 `eval` 定位：`X_Carriage_Upper` 在 `M3Cbore1` 之后 `kernel.shells` 从 `1` 变 `2`（`ck_b_seats` 1 壳 → `ck_c_through1` 1 壳 → `ck_d_cbore1` 2 壳）。根因是**沉孔刀具底面与本体外表面共面**，OCC 生成了第 2 个内部壳；后续再切通孔就报空腔归属歧义。

修复（`refs/scripts/build_lm6_native.py`）：

```python
# 先两通孔、再两沉孔：符合加工逻辑，也避免沉孔空腔先出现后再去料
for i, (mx, mz) in enumerate(m3_xz, 1):
    cyl('CA_%s_%s_M3Through%d' % (axis_tag, half, i), 'CAR_M3_R',
        '%s + 2 * CUT_EXT' % tp,
        [mx, '%s - CUT_EXT' % y0p, mz], 'Y', op='cut', targets=[nm])

# 沉孔刀具必须越过本体外表面起刀（base = y0 - CUT_EXT），
# 高度同步 +CUT_EXT，保证沉孔底面 y0 + cb_d 不变
for i, (mx, mz) in enumerate(m3_xz, 1):
    cyl('CA_%s_%s_M3Cbore%d' % (axis_tag, half, i), cb_r,
        '%s + CUT_EXT' % cb_d,
        [mx, '%s - CUT_EXT' % y0p, mz], 'Y', op='cut', targets=[nm])
```

变体 A/B/C 验证：V1（外延+原顺序）`exit=0`、V2（先通孔+外延沉孔）`exit=0`、V3（只重排不外扩）仍报同样错误 → **沉孔外延是必要修复**。修复后 `shells=1 / closed=True / V=12680.899 / faces=35 / timeline errors=[]`。

### 15.2 step 193 `boolean Cut: no result`

`CA_Z_Upper_BeltRelief` 中央皮带让位腔（`CAR_BELT_W = 8 mm`）与两个 `CAR_CB_R_UPPER = 3.2 mm` 的 M3 沉孔在 X/Z 上重叠，刀具与已有空腔相切导致布尔空结果。变体实测：5×5 成功 / 8×8 失败 / 8×5 成功 → 把 **`CAR_BELT_W` 从 `8 mm` 改为 `5 mm`**。

### 15.3 三处独立核对修正

* `corner_fillet()` 边索引：`refs/tmp/fillet_cmp.json` 实测 `(0,2,8,11)` 的 `dV=137.435 mm³ = 4×(16−4π)×10` 才是**沿 Y 厚度方向的四角 R4**；`(4,6,7,9)` 的 `dV=687.176 mm³` 圆的是沿 Z 的长边，不符合设计意图。**保留 `(0,2,8,11)`**。
* Z 上滑车厚度：真实 bbox `[125,-27,120.5 … 175,-12,153.5]` 要求 **15 mm**，新增 `CAR_T_UPPER_Z = 15 mm`（X 上滑车仍是 `CAR_T_UPPER = 10 mm`），保证在 `Y=-12` 与下半体合拢。
* 参数联动测试拆分：一次 `parameters.change` 会重算整条时间线（70~90 特征），单脚本堆 3 次改动会超 300 s（实测 `exit=124`）。拆成 `09`（只测 `SEAT_R`）与 `10`（测 `X_CAR_Z0` + `Z_SLOT_W`），两者 `--in` 只读、不保存，均 `exit=0`。

## 16. 全量验证结果（当前权威）

| 检查 | 结果 | 证据 |
|---|---|---|
| `07` 脚本执行 | **224/224 成功，exit 0** | `refs/tmp/lm6_native_run_results.json` |
| 零 STEP | `file.insert_step = 0` | 命令构成统计 |
| `eval` | **18 body / 104 params / 114 timeline / error 0 / open skipped 0** | `refs/tmp/native_eval.json` |
| 冻结 Z 槽 | **22.000 mm** | `08_lm6_native_verify.json` → `inspect.measure` |
| 冻结 X 口袋 | **20.800 mm** | 同上（`20.80000000081833`） |
| 全量干涉 | **count 0 / checked 18 / pairs_not_checked 0 / budget_exceeded false / truncated false** | 同上，`budget_s=420` |
| 参数清单 | **104 / cycles 0 / errors 0** | 同上 `parameters.list` |
| 外观读回 | **18/18 body** 有颜色 + PBR | `refs/tmp/native_appear_results.json` |
| 参数联动 A | `SEAT_R 6.05 → 6.35`：`X_Carriage_Lower V 13569.202 → 13344.825`，`recomputed 73 / errors []`；端板 / 导杆 / 轴承体积不变 | `09_lm6_native_paramtest.json` |
| 参数联动 B | `X_CAR_Z0 112 → 114`：滑车 bbox minZ `112 → 114`；`Z_SLOT_W 22 → 24`：`Z_EndPlate_L V 35532.048 → 35225.097`、实测槽宽 **24.0 mm**；`recomputed 76 / 86 / errors []` | `10_lm6_native_paramtest_frozen.json` |

**结论**：关键尺寸、坐标、冻结项都是**可编辑且联动**的，达成了用户「修改设计时都能编辑」的目标。混合方案里「改 `ROD_HOLE_R` 端板孔不变」的缺陷已消除。

## 17. 复现（全原生）

```bash
SC="/d/Program Files/SolidCraft/solidcraft-cli.exe"

# 1) 生成 224 条命令 + 104 行参数表 + 3 个只读验证脚本
python refs/scripts/build_lm6_native.py

# 2) 执行并保存 .sc（224/224，exit 0）
"$SC" run solidcraft/07_lm6_native.json --results \
    --json-out refs/tmp/lm6_native_run_results.json --param-check warn

# 3) 结构 / 冻结项 / 干涉 / 参数清单
"$SC" eval solidcraft/LM6UU_Native.sc --json-out refs/tmp/native_eval.json
"$SC" run solidcraft/08_lm6_native_verify.json --in solidcraft/LM6UU_Native.sc \
    --results --json-out refs/tmp/native_verify_results.json
"$SC" run solidcraft/11_lm6_native_appearance.json --in solidcraft/LM6UU_Native.sc \
    --results --json-out refs/tmp/native_appear_results.json

# 4) 参数联动（只读，不保存）
"$SC" run solidcraft/09_lm6_native_paramtest.json --in solidcraft/LM6UU_Native.sc \
    --results --json-out refs/tmp/09_lm6_native_paramtest_results.json
"$SC" run solidcraft/10_lm6_native_paramtest_frozen.json --in solidcraft/LM6UU_Native.sc \
    --results --json-out refs/tmp/10_lm6_native_paramtest_frozen_results.json

# 5) 出图（整机 3200×2000 → 白底紧裁；近景 1800×1200 保留原始渐变底）
"$SC" snapshot solidcraft/LM6UU_Native.sc --out refs/tmp/lm6_native_iso_hi.png \
    --width 3200 --height 2000 --view iso --no-grid --no-axes
"$SC" snapshot solidcraft/LM6UU_Native.sc \
    --out solidcraft/LM6UU_Native_seat_detail.png \
    --width 1800 --height 1200 --no-grid --no-axes \
    --camera '{"target":[150,-68,137],"yaw":0.785,"pitch":0.5,"distance":180,"fov":0.55}' \
    --body X_Carriage_Lower:opacity=0.28 --body X_Carriage_Upper:opacity=0.28 \
    --body X_LM6UU_1:color=#e8623a --body X_LM6UU_2:color=#e8623a
python refs/scripts/render_lm6_views.py
```

## 18. 全原生文件清单

| 文件 | 说明 |
|---|---|
| `solidcraft/LM6UU_Native.sc` | **当前权威交付**：878047 B / 18 body / 104 参数 / 114 特征 / 零 STEP |
| `solidcraft/LM6UU_Native_iso.png` | 整机白底等轴测图（1264×1302） |
| `solidcraft/LM6UU_Native_seat_detail.png` | 轴承座近景：滑车半透明 + LM6UU 橙色高亮（1800×1200） |
| `solidcraft/07_lm6_native.json` | 224 条主命令（生成器输出） |
| `solidcraft/LM6UU_NATIVE_PARAMS.csv` | 104 行参数表（分组 / 表达式 / 说明 / 核心标记） |
| `solidcraft/08_lm6_native_verify.json` | 只读复核：两冻结项实测 + 全配对干涉 + 参数清单 |
| `solidcraft/09_lm6_native_paramtest.json` | 只读联动测试 A：`SEAT_R` |
| `solidcraft/10_lm6_native_paramtest_frozen.json` | 只读联动测试 B：`X_CAR_Z0` / `Z_SLOT_W` |
| `solidcraft/11_lm6_native_appearance.json` | 只读外观读回：`appearance.list`（18/18 body） |
| `refs/scripts/build_lm6_native.py` | **可复现生成器**（参数表 + 特征树 + 全部输出脚本） |
| `refs/scripts/render_lm6_views.py` | 渐变底转白 + 紧裁（同时处理混合 / 全原生两张等轴测图） |
| `refs/scripts/extract_native_recipe.py` | 8 件 BREP 配方提取（Plane/Cylinder 分析） |
| `refs/scripts/build_native_recipe.py` | 自动盒分解方案（**已否决**，保留作决策记录） |

## 19. 口径边界与未决

* **语义化 ≠ 几何 1:1**：端板装饰性镂空按设计意图重建，体积与原 BREP 差别在几个百分点内；外形 bbox 与全部安装 / 冻结接口保持一致。若需要严格 1:1 制造几何，仍以主 `CrossSlide_P014013.FCStd` 的 v13.2 BREP 为准。
* **未合并回主设计**：`CrossSlide_P014013.FCStd`（v13.2 几何 + v14 材质）、`motion.sc`（仍是 LM5UU）、V2 爆炸图、动画、图纸、21 种材质**全部未改动**。若将来合并，occurrence id 会变，必须按 §8 的顺序重跑整条链。
* **不是模具图**：本设计验证的是「参数可编辑 + 接口保真 + 无干涉」，量产前仍需模具详细设计、原位点胶工装 / 固化标定、试模件实测、模具费评估。
* **GitHub 推送**仍需用户重新授权，不得重试或绕过 token / 代理限制。

## 20. v1 外观被否定后的 v2 重做：真实 2040 截面阶段（2026-11-13，当前型材权威）

### 20.1 为什么 §11–§19 的「全绿」不能继续当权威

用户原话：

> 「solidcraft设计效果很差，完全不像正常的产品设计，比freecad差多了，你看看哪里出了大问题。」

复核后确认此前是**验证口径错误（假绿）**：`08_lm6_native_verify.json` 只查了冻结尺寸、零干涉、参数联动、外观读回，没有查逐件几何 / 外观保真度。量化结果：

| 项 | 原始 BREP | 全原生 v1 | 偏差 |
|---|---:|---:|---:|
| 8 件结构件总面数 | 931 | 256 | **约 27% 保真度** |
| `X_Profile` 体积 | 60561.587 mm³ | 125546.2 mm³ | **+107%** |
| `Z_Profile` 体积 | 45421.190 mm³ | 94159.6 mm³ | **+107%** |
| 2040 截面填充率 | 37.9% | 约 78% | 实心方棒 + 4 直槽 |
| 整机 body / 色组 | 140 / 21 材质 | 18 / 5 色组 | 完整机器未重建 |

用户选择「**重做原生几何（推荐）**」，并要求「你拉出型材后先让我在 solidcraft 里看看」。阶段预览 `LM6UU_Profile_Preview.sc`（4 槽薄壁、V +25.1%）在用户给出真实横截面图后被否定，故本节只交付**精确型材**，端板 / 滑车 v2 尚未开始。

### 20.2 精确截面来源与旧提取 bug

用户图是带尺寸标注的白底线稿，当前模型无法直接接收图像；线稿 flood-fill 也不闭合，故改用项目原始 FCStd 裸 BREP 端面曲线作为权威几何，**不再猜截面**。

旧 `refs/scripts/extract_profile_contours.py` 把两个 Ø5 圆孔误写成 3 点零面积缝隙，少算 `2×19.634954 = 39.269908 mm²`；外轮廓 4 个 R1.5 圆弧也被折线化。修正后用 `Wire.OrderedEdges / OrderedVertexes` 输出真实曲线：

```text
wire0 外轮廓 : 286 Line + 4 个 R1.5 圆弧   491.272842 mm²
wire1 圆孔   : Circle Ø5                   19.634954 mm²
wire2 中心腔 : 52 Line                     149.195000 mm²
wire3 圆孔   : Circle Ø5                   19.634954 mm²
净截面积     :                             302.807934 mm²
BREP 端面    :                             302.807933 mm²  delta 1e-6
```

圆弧面积必须取 `Part.Face(wire).Area`；若用「起点—弧中点—终点」折线算面积，4 个圆角合计少 `0.704628 mm²`。

### 20.3 全原生精确重建

`refs/scripts/build_profile_exact.py` → `solidcraft/13_profile_exact.json`：

```text
43 commands / 11 user parameters / 0 file.insert_step
sketch.create ×2
sketch.line（外轮廓连续直线分组 + 中心腔闭合轮廓）
sketch.arc.three_point ×8（两根型材各 4 个 R1.5 真实圆角）
sketch.circle.center ×4（两根型材各 2 个 Ø5 孔）
sketch.finish ×2 / solid.extrude ×2 / appearance.assign / file.save
```

`--param-check strict` 43/43 成功、0 error / 0 warning。型材是冻结标准件，截面曲线与孔位按 BREP 固定；`X_PROF_LEN`、`Z_PROF_LEN`、`PROF_HOLE_R` 为命名参数并驱动特征，草图本身仍可编辑。

### 20.4 几何保真度（不是「命令成功」）

`solidcraft-cli eval` 与 `build_profile_exact.py --verify` 结果：

| 检查 | `X_Profile` | `Z_Profile` | 目标 / 判据 |
|---|---:|---:|---|
| closed / shells | `true / 1` | `true / 1` | 单一闭合实体 |
| faces | **346** | **346** | 原始 BREP 346 面 |
| face_types | plane 340 + cylinder 6 | plane 340 + cylinder 6 | 原始同为 346 面 |
| volume | 60563.053507 mm³ | 45421.783053 mm³ | 60561.586684 / 45421.190013 |
| volume error | **+0.0024%** | **+0.0013%** | `< 0.01%` |
| section area | 302.815268 mm² | 302.811887 mm² | 302.807933 mm² |
| bbox | `[50,-57,117]..[250,-37,157]` | `[130,-1,62]..[170,19,212]` | 与原始一致 |

`refs/tmp/profile_exact_verify.json`：**25 项检查 PASS / failed 0**，含命令结果、草图求解状态、timeline、参数错误、bbox、闭合壳、面数 / 面类型、体积误差、截面积、源与 GUI 副本 sha256 一致性。源 / 用户目录 `.sc` sha256 均 `b9cd20789a99c3e9ac93aa7d4f61932c27f14084dec6e2bea2619db7600cc6a9`。

### 20.5 GUI 与出图

```text
mcp__solidcraft__open  D:/mydocuments/SolidCraft/LM6UU_Profile_Exact.sc
  → errors 0 / features 4 / name LM6UU_Profile_Exact
mcp__solidcraft__execute view.fit + expect
  → bodies 2 / volume 105984.836560 / bbox [50,-57,62]..[250,19,212] / ok=true
mcp__solidcraft__execute parameters.list
  → 17 项（11 用户参数 + 6 派生），cycles []、error null
mcp__solidcraft__screenshot source:"model", view:"fit", grid:false, axes:false
  → LM6UU_Profile_Exact_GUI_fit.png（1600×1000）
```

`source:"window"` 因窗口被最小化 / 未呈现帧返回 `no frame was presented`；PowerShell COM / `Add-Type` / `Reflection.Assembly` 自动置前均被安全策略拒绝，不再重试。已改用 model 渲染并提示用户手动点开任务栏 SolidCraft 窗口。

出图：`LM6UU_Profile_Exact_iso_white.png`（白底等轴测）、`LM6UU_Profile_Exact_GUI_fit_white.png`（GUI model 渲染白底）、`LM6UU_Profile_Exact_section.png`（BREP 原始 vs SolidCraft 精确复刻对比）。

### 20.6 文件清单与下一步

| 文件 | 说明 |
|---|---|
| `solidcraft/LM6UU_Profile_Exact.sc` | **当前型材阶段权威**；2 body / 346 面每件 |
| `solidcraft/13_profile_exact.json` | 43 条全原生命令 |
| `solidcraft/LM6UU_PROFILE_EXACT_PARAMS.csv` | 11 行用户参数表 |
| `refs/scripts/extract_profile_contours.py` | 修正后的 BREP 有序曲线提取器 |
| `refs/scripts/build_profile_exact.py` | 生成器 + `--verify` 25 项保真度验证 |
| `refs/tmp/profile_contours.json` / `profile_exact_eval.json` / `profile_exact_verify.json` | 轮廓 / eval / 验证证据 |
| `solidcraft/LM6UU_Profile_Exact_*.png` | 等轴测、GUI fit、剖面对比图 |

## 21. 用官方 skill 建立 X-Z 十字滑台（2026-11-16）

用户确认型材后要求：「利用这些 skill，在 SolidCraft 把鹅蛋喷码机的十字滑台先建立起来，4020 铝型材已经在项目里建立了。」

### 21.1 skill 使用边界

按安装的官方 skill 分工：

| skill | 本次用途 |
|---|---|
| `solidcraft-modeling` | 先算参数和世界坐标，再按 stage 分批 `parameters.add` / `solid.box` / `solid.cylinder` / `solid.fillet`；每阶段用 `measure` 对计算值 |
| `solidcraft-editing` | 在已建立的 `LM6UU_Profile_Exact.sc` 命令基线上扩展，不重复导入 STEP，不改型材冻结截面 |
| `solidcraft-checking` | 逐件 bbox / closed / faces / volume，冻结尺寸，干涉，参数范围与联动，timeline health |
| `solidcraft-mechanisms` | 建立 `X_Base` / `X_Stage` / `Z_Stage` 三个 component，`X_Travel` / `Z_Travel` slider，`CrossSlide_Cycle` study |
| `solidcraft-sheetmetal` | 本次没有钣金件，未调用 |

### 21.2 设计内容

静态主体 `solidcraft/CrossSlide_XZ.sc` 与机构版 `solidcraft/CrossSlide_XZ_mech.sc` 都是 **18 body / 100 用户参数 / 零 STEP**：

```text
已建立型材  X_Profile / Z_Profile（沿用 §20 真实 BREP 1:1 截面，346 面/件）
结构件      X/Z 端板 4 件 + X/Z 上下滑车 4 件
传动件      4 × Ø6 导杆 + 4 × LM6UU Ø12/Ø6×19
轴承接口    主座 R6.05 × SEAT_L 19.20；端板导杆孔 R3.05（Ø6.10）
冻结项      Z 槽 22.00；X 口袋 20.80
机构        X slider [-80,+80]；Z slider [-55,+55]；study 10 步
```

`14_cross_slide_xz.json` 共 238 条命令：`parameters.add` 100、精确型材草图/拉伸、`solid.box` 26、`solid.cylinder` 72、`solid.fillet` 4、外观 5、保存 1。`--param-check strict` 238/238 成功，无 error；10 条 `Boolean retry: tool displacement ...` 警告的位移仅 `1.22~1.24e-4 mm`、转角 `2e-6 rad`，逐件体积与解析值一致，按 checking skill 属可接受的 kernel 微调。

### 21.3 验证

`refs/scripts/verify_cross_slide_xz.py` 汇总 `refs/tmp/*cross_slide*` 证据：

```text
CONCLUSION PASS / failed 0
body_count 18 / all closed / timeline errors 0
Z 槽 22.000 mm / X 口袋 20.800 mm
interference count 0 / checked 18 / pairs_not_checked 0 / budget_exceeded false
parameters cycles [] / errors [] / 用户参数 100
SEAT_R 6.05→6.35 → X_Carriage_Lower V 13569.202→13344.825 mm³
Z_SLOT_W 22→24 → 实测 24.0；Z_EndPlate_L V 35532.048→35225.097 mm³
joint conflicts [] / floating []
joint.drive X=20 → X_Stage +20X；Z=15 → Z_Stage 再 +15Z
```

型材保真度沿用 §20：体积误差 `+0.0024% / +0.0013%`，面数 346 与原始 BREP 一致。**端板 / 滑车本阶段仍是语义化重建**：8 件结构件合计 256 面（原始 931 面），端板体积偏差约 `-3% ~ -26%`，滑车约 `+1.6% ~ +2.3%`。报告中的 `structural_volume_deviation_informational` 明确保留这些数值，后续若要求 1:1 外观，必须逐件按 BREP 曲线补薄法兰、中央筋、镂空与阶梯台。

### 21.4 GUI / 出图

文件已同步到 `D:\mydocuments\SolidCraft\`：两个 `.sc`、参数表、白底等轴测 / 俯视图、headless fit 图。源与 GUI 目录的 `CrossSlide_XZ_mech.sc` sha256 一致：

```text
105eebc1d190f59d7f7f1ec412a43d4671c65fe312a083c05c15849e40dc0357
```

Headless MCP 打开成功：`errors 0 / features 124`；joint.list 两个 slider 均 `resolves true / conflicts [] / errors []`。本次 GUI MCP `open` 仍报 `the agent chat has no message in progress`，不再自动重试；用户手动点开 SolidCraft 窗口后 File→Open `CrossSlide_XZ_mech.sc`、View→Fit 即可查看。也可直接看 `CrossSlide_XZ_iso_white.png`、`CrossSlide_XZ_top_white.png`、`CrossSlide_XZ_headless_fit.png`。

### 21.5 文件清单

| 文件 | 说明 |
|---|---|
| `solidcraft/CrossSlide_XZ.sc` | 静态主体，18 body / 100 参数 |
| `solidcraft/CrossSlide_XZ_mech.sc` | 机构版，3 component / 2 slider / 1 study |
| `solidcraft/14_cross_slide_xz.json` | 238 条建模命令 |
| `solidcraft/15_cross_slide_xz_verify.json` | 冻结项 / 干涉 / 参数 / 外观只读复核 |
| `solidcraft/16_cross_slide_mechanism.json` | 组件 / slider / study |
| `solidcraft/17_cross_slide_motion_check.json` | 两轴驱动与质心平移验证 |
| `solidcraft/18_cross_slide_param_seat.json` | `SEAT_R` 参数联动 |
| `solidcraft/19_cross_slide_param_frozen.json` | `Z_SLOT_W` 冻结项联动 |
| `solidcraft/CROSS_SLIDE_XZ_PARAMS.csv` | 100 行参数表 |
| `refs/scripts/build_cross_slide_xz.py` / `verify_cross_slide_xz.py` | 生成器 / 汇总验证器 |
| `refs/tmp/cross_slide_xz_verify_summary.json` | 15 项检查 PASS / failed 0 |

**下一步**：若用户要求提高外观保真度，按 #76–#80 逐件重建端板薄法兰 + 中央筋、滑车 LM6UU 座 / 皮带让位 / 阶梯台的真实 BREP 曲线；不得把当前语义化结构件误称为 1:1 复刻。

## 22. 单独 X 轴滑台原生重设计（当前目标）

§21 的 X-Z 十字滑台是阶段历史：用户随后明确纠正为「先把 X 轴滑台建立起来」，并要求参考已打开的 `CrossSlide_P014013`，在 SolidCraft 中原生重新设计单独 X 轴。当前权威报告见 `refs/SOLIDCRAFT_X_AXIS_REDESIGN.md`。

```text
权威设计        solidcraft/X_Axis_Slide.sc
生成脚本        refs/scripts/build_x_axis_slide.py
构建规模        170 命令 / 80 用户参数 / 14 body / 零 STEP
模型健康        全部 closed；timeline errors 0 / warnings 0
干涉            count 0 / checked 14 / pairs_not_checked 0 / unchecked 0
冻结项          X 限位口袋 20.80000000000001 mm
型材            X_Profile 346 面 / V 60563.054 mm³，真实 BREP 1:1 截面
```

LM6UU 接口继续沿用本文件冻结值：`SEAT_R=6.05`、`SEAT_L=19.20`、端板导杆孔 `Ø6.10`；参考模型中的 Ø9.5 惰轮轴也按原尺寸恢复。首轮 9 个干涉已逐项修正：型材/端板端面清根、同步带避让槽、电机沉腔与凸台让位、惰轮轴孔与惰轮内孔对齐。同步带改为「上边→两端包绕→下边→内孔」顺序，轴承座三段孔做 1 mm 相邻重叠，所有时间线警告清零。

GUI 目录已同步 `.sc`、参数 CSV、白底等轴测/俯视图；headless MCP 打开 `errors 0 / features 69`。GUI MCP 因控制端口被既有进程占用而超时，未强杀用户窗口，改为提示手动 File→Open + View→Fit。端板/滑车等仍为语义化原生重建，不是逐面 1:1；本版不含 slider / motion study，也未纳入 washer、nut、限位开关、rod tap、fix screw、clamp key。
