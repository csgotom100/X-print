# FreeCAD → SolidCraft 迁移报告

生成时间：2026-11-12
源模型：`D:\ink\CrossSlide_P014013.FCStd`（sha256 `173b2315…`，152 对象 / 140 个 `Part::Feature`）
几何主交付：`solidcraft/CrossSlide_P014013.sc`
**含 v14 材质 + 打码运动仿真的完整交付**：`solidcraft/CrossSlide_P014013_motion.sc`，见 `refs/SOLIDCRAFT_MOTION.md`
**功能组爆炸图交付**：V1 `solidcraft/CrossSlide_P014013_exploded.sc` / `solidcraft/CrossSlide_exploded.png`，见 `refs/SOLIDCRAFT_EXPLODED.md`；**V2 升级版（更细爆炸 + 白底 + 中文标注 + 装配顺序线）** `solidcraft/CrossSlide_P014013_exploded_v2.sc` / `solidcraft/CrossSlide_exploded_v2_annotated.png`，见 `refs/SOLIDCRAFT_EXPLODED_V2.md`

---

## 1. 结论

| 项目 | 结果 |
|---|---|
| FreeCAD 零件名保留 | **140 / 140（100%）**，零缺失、零多出 |
| SolidCraft bodies | 144（`Cap_Spring` 在源模型里本就是 5 个实体，被拆成 5 个 body） |
| 几何完全一致 | **137 件**（135 件严格 OK + 2 件仅有微小数值误差） |
| 开放壳（不可算体积 / 不可布尔） | **3 件**：`X_EndPlate_L`、`X_EndPlate_R`、`Part__Feature` |
| 单位 / 坐标轴 | mm，Z-up，`up:"z"`，包围盒逐件吻合，**无坐标翻转** |
| FreeCAD 总实体体积 | 917731.653 mm³ |
| SolidCraft 总体积 | 856894.075 mm³（只计闭合体） |
| 差额 | 60837.578 mm³，**100% 来自上述 3 个开放件**，其余零件零损失 |

---

## 2. 为什么不能直接读 `.FCStd`

SolidCraft 的 `file.insert_step` 名义上支持 FreeCAD `.FCStd`，但本机实测直读会严重损坏拓扑：

| 路线 | bodies | 零件名 | errors | 开放壳 | 警告 |
|---|---|---|---|---|---|
| 直读 FCStd（`system: cadmpeg`） | 144 | 全部退化为 `CrossSlide_P014013 (N)` | 0 | **129** | **3184**（其中 2446 条 `unsupported curve CURVE_REPLICA`，另有成批 `loop-no-continuous-ordering` / `face-omitted-unclassified-loop`），甚至出现负体积 |
| 命名装配 STEP（`system: FreeCAD`） | 144 | **140 个原名全保留** | 0 | **3** | **4** |

根因：直读路径走 `cadmpeg` 内核，对 FreeCAD BREP 里的 `CURVE_REPLICA` 曲线和部分环拓扑支持不全，大量丢面。
因此正式通道固定为 **FreeCAD 导出命名装配 STEP → SolidCraft 按 `names:"product"` 导入**。

补充验证：在 FreeCAD 侧逐件直读 BREP，140 个对象**全部** `solids>0`、`isClosed()=True`、`isValid()=True`，总实体体积 917731.653 mm³ —— 源模型本身没有任何开放壳，直读损坏完全是导入器造成的。

---

## 3. 可复现通道

```bash
# 1) 从磁盘 FCStd 直读 BREP（不用 App.openDocument，避开本机 FreeCAD 1.1 的卡死）
"/d/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" refs/scripts/export_named_step.py
"/d/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" refs/scripts/export_named_step_clean.py   # 最终采用

# 2) SolidCraft（MCP）
open {path:"D:/mydocuments/SolidCraft/CrossSlide_P014013_clean.step",
      names:"product", up:"z"}
execute {command:"file.save", params:{path:"D:/mydocuments/SolidCraft/CrossSlide_P014013.sc",
                                     format:"container", overwrite:true}}

# 3) 逐件核验
"/d/Program Files/FreeCAD 1.1/bin/python.exe" refs/scripts/verify_solidcraft_migration.py
```

- `import Import; Import.export(objects, path)` 会为**每个** `Part::Feature` 写一个 STEP `PRODUCT`，名字取自对象 `Label`（= 对象名），这是名字能 100% 保留的关键。
- `export_named_step_clean.py` 额外做了净化：只保留每个对象的真实 `Solid`，单实体直接用 `Solid`、多实体用 `Part.makeCompound(solids)`，再 `removeSplitter()`。净化前后逐件体积变化 **0 件 > 0.01 mm³**，确认没有改几何。
- **SolidCraft 路径沙箱**：服务端只允许 `D:\mydocuments\SolidCraft`、`%LOCALAPPDATA%\SolidCraft\recovery`、临时目录等，不能直接读 `D:\ink`。所以脚本把 STEP/.sc 写到允许目录，产物再拷回项目 `solidcraft/`。若要直读 `D:\ink`，需在 MCP 客户端配置里加 `--allow-path D:\ink`。

---

## 4. 逐件核验明细

权威基准：`refs/tmp/fcstd_topology.json`（140 件体积 + bbox + 拓扑）
SolidCraft 实测：`mcp__solidcraft__measure {}` 全量输出
机器可读结果：`refs/tmp/solidcraft_verify.json`

判据：`|ΔV| / V < 0.001` 且 bbox 每坐标差 `< 0.05 mm` 且 `closed=True`。

| 状态 | 件数 | 说明 |
|---|---|---|
| `OK` | 135 | 严格通过 |
| `MISMATCH`（实为可忽略误差） | 2 | 见下 |
| `OPEN_BODY` | 3 | 见第 5 节 |

两件 `MISMATCH` 的实测数据：

```
Cap_Spring     fc=   284.245  sc=   284.1841  rel=2.13e-04  bbox_err=0.4367 mm  bodies=5
HP45CAR_P01    fc= 67917.314  sc= 67917.4002  rel=1.28e-06  bbox_err=1.3000 mm  bodies=1
```

- `Cap_Spring`：源模型是 5 个分离的弹簧圈实体，聚合比对；体积差 0.02%，bbox 差异来自离散曲面极值点。
- `HP45CAR_P01`：体积差 1.3 ppm（完全一致），bbox 差 1.3 mm 是某个极值点采样差，**不是几何损失**。

三件 `OPEN_BODY`：

```
X_EndPlate_L   fc V=19096.771 mm3   SolidCraft 169 faces  closed=false
X_EndPlate_R   fc V=20869.194 mm3   SolidCraft 171 faces  closed=false
Part__Feature  fc V=20869.189 mm3   SolidCraft 171 faces  closed=false
```

> 注：`Part__Feature` 是源 FCStd 里本来就存在的一个对象（早期建模遗留），其体积 / bbox 与 `X_EndPlate_R` 几乎相同，是端板 R 的近似副本。不是 STEP 导入产生的多余件。

关键件几何已确认带入：

```
HP45_ProbeHousing  V=5138.627   (v13.2 探针座)
HP45_SpringSpacer  V= 560.200   (v13.2 侧盖板)
HP45_ProbeArm      V=11633.624
X_LM5UU_1/2        V= 883.487   Ø10×15 / Ø5 导杆口径
X_GuideRod_1/2     V=4170.774   Ø5
```

---

## 5. 3 个开放壳：原因与绕行方案

**已排除的可能**：
- 不是源模型问题：FreeCAD 侧这 3 件都是 `solids=1, shells=1, closed=True`，面类型只有 `Plane`(155/157) + `Cylinder`(63)，没有 B-spline / 环形面。
- 不是装配 STEP 写法问题：把 `X_EndPlate_L` 用 `shape.exportStep()` **单独**导出成 `X_EndPlate_L_single.step`，SolidCraft 打开仍报 `imported as an open body`。
- 直接读 FCStd 时的相关告警也指向这三块板：`loop-no-continuous-ordering`、`face-omitted-unclassified-loop` 明确带 `X_EndPlate_L.Shape.brp:743`。

**结论**：SolidCraft 的 STEP/BREP 导入内核对这两块端板（218/220 面、63 个圆柱面、大量小倒角与孔环）会丢失约 49 个面，导致壳不闭合。这是导入器限制，换导出路径无法规避。

**随交付的备用件**（都在 `solidcraft/`）：

| 文件 | 用途 |
|---|---|
| `X_EndPlate_L_single.step` / `X_EndPlate_R_single.step` / `Part__Feature_single.step` | 单件 STEP，供 SolidCraft 后续版本重试导入 |
| `X_EndPlate_L_mesh.stl` / `X_EndPlate_R_mesh.stl` / `Part__Feature_mesh.stl` | 0.05 mm 弦差三角网格（16626 / 14680 面），可用 `file.insert_mesh` 补入，形状完整可见，但**不能做 B-rep 布尔 / 打孔** |

**如果要改端板导杆孔（Ø5→Ø6 / LM6UU）**，三个选项：
1. 在 SolidCraft 里用 `sketch` + `solid.box` + `solid.cylinder` 参数化重建端板（板状件，重建成本不高，且以后可编辑）；
2. 继续在 FreeCAD 改端板，改完重跑 `export_named_step_clean.py` 再迁移；
3. 暂时把网格体当视觉参考，几何改动只在 FreeCAD 侧做。

---

## 6. 口径提醒（很重要）

- **当前主模型仍是 `LM5UU Ø10×15 + Ø5 导杆`**：`X_LM5UU_1/2`、`Z_LM5UU_1/2` 四个对象名和 BOM/README 口径都还在。上一轮「确认是 LM6UU / 导杆 Ø6」的改造**尚未落盘**，本迁移搬的是磁盘上的当前状态。
- **v14 材质不会随 STEP 自动迁移**：FCStd 的 `ShapeMaterial` 只存 UUID，STEP 不携带 FreeCAD 材质库信息，所以本报告的几何基线 `.sc` 中所有 body 为 `Default`。**后续已补做**：按 `refs/materials/material_assignments.csv` 在 `CrossSlide_P014013_motion.sc` 中重建 21 种 SolidCraft user material 并覆盖全部 144 个 body（PETG-FDM 异型结构件 16 件、POM / PA66-GF30 三主件等），详见 `refs/SOLIDCRAFT_MOTION.md` 第 3 节。这套材质是 SolidCraft 独立对象，与 FreeCAD `.FCMat` 的 UUID 无联动。
- **参数化历史没有迁移**：导入结果是 1 个 `Import` base feature + 140 个 subcomponent / rigid joint，几何精确但无 sketch 历史。所有零件可在其上继续加特征，但不能回滚到建模步骤。
- **冻结项几何未动**：磁环下台阶 Z76.50、Hall 感测面 X83.40 / 中心 Z79.00、磁路 r=5.90、Z 轴限位槽 22.00、X 轴端板口袋 20.80、弹簧 k=0.045 N/mm、行程 0..+3.0。
- 图纸 / BOM / README / 系统装配图仍以 FreeCAD 侧为权威，本次未改动。

---

## 7. 文件清单

| 文件 | 说明 |
|---|---|
| `solidcraft/CrossSlide_P014013.sc` | **主交付**，SolidCraft 设计（1.8 MB） |
| `solidcraft/CrossSlide_P014013_clean.step` | 迁移桥梁：净化版命名装配 STEP（8.0 MB） |
| `solidcraft/CrossSlide_P014013_iso.png` | SolidCraft 等轴测渲染（1100×760） |
| `solidcraft/*_single.step` / `*_mesh.stl` | 3 个开放端板的备用件 |
| `refs/scripts/export_named_step.py` | BREP 直读 + 拓扑统计 + 命名 STEP 导出 |
| `refs/scripts/export_named_step_clean.py` | 净化版（最终采用） |
| `refs/scripts/export_endplate_probe.py` | 端板单件 STEP / 网格备份 + 面类型统计 |
| `refs/scripts/verify_solidcraft_migration.py` | 逐件体积 / bbox 核验 |
| `refs/tmp/fcstd_topology.json` | FreeCAD 权威基准（140 件） |
| `refs/tmp/solidcraft_verify.json` | 核验机器可读结果 |

脚本目录 `refs/scripts/` 是正式可复现链；`refs/tmp/` 是中间数据（被 `.gitignore` 忽略）。

---

## 8. 遗留待办

1. **LM6UU / Ø6 导杆改造**（上一轮任务被中断，尚未落盘）：需改 4 根导杆、4 块端板导杆孔、4 个轴承对象、轴承座 R6.05 与轴向挡肩、BOM / 材质说明 / 图纸。
2. GitHub 推送仍等待重新授权（v13.2 几何 + v14 材质）。
3. `System_Assembly_A1.svg/.png/.pdf` 的 BOM 第 13 行已改为 `KW11-3Z-A-1`，但图片尚未重出。
4. SolidCraft 侧 3 个开放端板（见第 5 节）。
5. 迁移后补做的材质与运动仿真见 `refs/SOLIDCRAFT_MOTION.md`；若实施第 1 项 LM6UU 改造，零件名 / occurrence id 会变，需**重跑迁移核验 + 三阶段运动脚本**。
