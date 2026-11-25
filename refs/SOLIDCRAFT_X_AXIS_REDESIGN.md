# SolidCraft 单独 X 轴滑台原生重设计（2026-11-16）

## 22.1 需求边界

用户明确纠正：

- 不是 X-Z 十字滑台；先把 **单独 X 轴滑台** 建立起来。
- 材料为真实截面的 2040/4020 铝型材，**直接 Ø6 mm 导杆**、**LM6UU 直线轴承**。
- 铝型材端面为 3D 打印结构，配 GT2 同步带 / 同步轮、42 步进电机。
- 参考 SolidCraft 已打开的 `CrossSlide_P014013`：它在 FreeCAD 中设计，本次是在 SolidCraft 里原生重新设计，而不是导入 STEP 哑实体。

因此，§21 的 `CrossSlide_XZ.sc` / `CrossSlide_XZ_mech.sc` 保留为历史阶段成果，**不再是当前目标**。当前权威为：

```text
solidcraft/X_Axis_Slide.sc
refs/scripts/build_x_axis_slide.py
solidcraft/20_x_axis_build.json
solidcraft/21_x_axis_verify.json
solidcraft/X_AXIS_SLIDE_PARAMS.csv
```

## 22.2 参考骨架与升级点

按 `CrossSlide_P014013` 的 X 轴 body bbox / 装配位置重建：

| 参考 body | 作用 | 本次处理 |
|---|---|---|
| `X_Profile` | X50..250，截面 346 面 | 直接沿用 §20 的真实 BREP 1:1 截面，不重画 4 槽近似 |
| `X_EndPlate_L/R` | 左端电机位、右端惰轮位 | 原生 box/cylinder 重建，增加电机沉腔、皮带让位槽、型材端面清根 |
| `X_GuideRod_1/2` | 双 Ø5 导杆 | 升级为 **两根 Ø6 导杆**，X42.5..257.5，中心 Y=-68，Z=122/152 |
| `X_LM5UU_1/2` | 旧轴承 | 升级为 **LM6UU Ø12/Ø6×19**，主座 `R6.05 × 19.20`，端板导杆孔 `Ø6.10` |
| `X_Carriage_Lower/Upper` | 上下半滑车 | 原生重建，三档轴承座孔（导入 R4.70 / 主座 R6.05 / 出口 R5.10）+ 同步带通过槽 |
| `X_Pulley_Drive/Idler` | GT2 同步轮 | 原生轮毂 + 双挡边；主动轮 Ø5 轴孔、惰轮 Ø9.5 轴孔 |
| `X_Belt_GT2` | 同步带 | 原生两直边 + 两端包绕 + 内孔切除，单一闭合体 |
| `X_Motor_NEMA17` | 42 步进电机 | 42×42×42 机身 + 定位凸台 + Ø5 轴，位置对齐参考模型 |
| `X_Screw_Idler` | 惰轮轴 | Ø9.5，与参考模型同尺寸 |

冻结项保持不变：

```text
X_POCKET_W = 20.80 mm
X_POCKET_ZC = 131.25 mm
```

## 22.3 构建结果

`refs/scripts/build_x_axis_slide.py` 从 `13_profile_exact.json` 只取 X 型材的 11 个参数 + 精确草图/拉伸，其余全部原生生成，零 STEP。

```text
170 条命令 / 80 个用户参数 / 14 body / 零 STEP
parameters.add 80
sketch.create 1 + line 6 + arc 4 + circle 2 + finish 1 + extrude 1
solid.box 17 + solid.cylinder 48 + solid.fillet 2
appearance.assign 7 + file.save 1
--param-check strict：全部成功
```

14 个 body：

```text
X_Profile                 V 60563.054  faces 346  shells 1
X_EndPlate_L              V 14485.078  faces 36   shells 1
X_EndPlate_R              V 23550.978  faces 23   shells 1
X_GuideRod_LM6_1/2        V  6077.702  faces 3    shells 1
X_LM6UU_1/2               V  1611.484  faces 4    shells 1
X_Carriage_Lower          V 11792.850  faces 28   shells 1
X_Carriage_Upper          V 10983.754  faces 28   shells 1
X_Belt_GT2                V  4868.884  faces 14   shells 1
X_Pulley_Drive            V  1081.219  faces 8    shells 1
X_Pulley_Idler            V   415.050  faces 8    shells 1
X_Screw_Idler             V  2232.418  faces 3    shells 1
X_Motor_NEMA17            V 75083.817  faces 10   shells 1
```

全部 `closed=true`。

## 22.4 干涉修复记录

首轮构建有 9 个干涉，已逐项定位并按实体几何修正，不是靠隐藏零件：

| 原干涉 | 原因 | 修正 |
|---|---|---|
| 型材 ↔ 左端板 908.434 mm³ | 端板法兰与型材端面 X50..53 实体重叠 | 增加 `XP_L_ProfileClear`，沿型材外接包络清根 |
| 型材 ↔ 右端板 60.562 mm³ | 右端 X249.8..250 重叠 | 增加 `XP_R_ProfileClear` |
| 左端板 ↔ 同步带 176.4 mm³ | 同步带穿过端板侧壁 | 增加 `XP_L_BeltClear`，Z 向让出 GT2 外轮廓 +1 mm |
| 右端板 ↔ 同步带 129.36 mm³ | 同上 | 增加 `XP_R_BeltClear` |
| 下滑车 ↔ 同步带 277.2 mm³ | 皮带穿过滑车 | 增加 `XC_Lower_BeltClear` |
| 上滑车 ↔ 同步带 277.2 mm³ | 同上 | 增加 `XC_Upper_BeltClear` |
| 左端板 ↔ 42 电机 9379.311 mm³ | 电机机身嵌入端板原空腔壁 | 增加电机沉腔、定位凸台让位孔，取消端板上不必要的实心凸台 |
| 右端板 ↔ 惰轮轴 100.904 mm³ | 轴孔仍按 Ø5 设计 | `XP_R_IdlerBore` 改为 `IDLER_SHAFT_R + 0.05` = Ø9.60 |
| 惰轮 ↔ 惰轮轴 666.152 mm³ | 惰轮孔按 Ø5，轴为 Ø9.5 | 惰轮孔改 `IDLER_SHAFT_R`，与参考模型一致 |

复查结果：

```text
interference count 0 / checked 20 / pairs_not_checked 0
budget_exceeded false / unchecked 0
X 限位口袋实测 20.80000000000001 mm
timeline errors 0 / warnings 0
parameters.list count 118 / cycles 未报异常
appearance.list bodies 20
```

同步带建模顺序也调整为「上边 → 两端包绕 → 下边 → 内孔」，消除了首轮的 `joined piece doesn't touch` 警告；轴承座三段孔做 1 mm 相邻重叠，消除了 4 条 `Boolean retry` 警告。

## 22.4b 端板样式回归原件（2026-11-17 修正）

首版端板用实心方框凑外框，被指出「样式跟原来差异太大」。按原始 BREP 与三视图重新提取后确认原件是**薄壁框架件**，不是实心块：

```text
X_EndPlate_L  原件 V 19158.4  bbox 53×45×40  fill 20.1%  faces 192
X_EndPlate_R  原件 V 20565.7  bbox 51×45×40  fill 22.4%  faces 191
```

重建方式改为「整片法兰 + 局部框筋 + 贯穿减重窗 + 开关耳」：

- 左端：X42.5..53 法兰 + X0..53 上下横梁与前后竖柱组成前框 + 两道减重窗 + 限位开关耳；
- 右端：X249..257.5 法兰 + X257..300 惰轮侧板 + R20 圆弧外缘（圆心 X280/Z137）+ 贯穿窗口 + 开关耳；
- 42 电机、Ø6 导杆、Ø16 同步轮、Ø9.6 惰轮轴全部按装配关系做贯穿/让位，不再与端板实体相交。

结果：

```text
X_EndPlate_L  V 12462.89  faces 55  shells 1  fill 13.1%
X_EndPlate_R  V 27666.93  faces 66  shells 1  fill 30.1%
两件 bbox 均与原件一致：L 0..53 / R 249..300，Y -82..-37，Z 117..157
```

## 22.4c 限位开关（KW11-3Z-A-1）

按参考模型 `X_LimitSwitch_L/R` 的位置新增左右限位开关与安装螺钉，共 6 个 body：

```text
X_LimitSwitch_L/R   12.2 × 6.5 × 19.8，V 1334.94 mm³，各 8 面
X_LimitScrew_L/R_1/2 Ø4.7 × 10.1，V 175.21 mm³，各 3 面
```

开关装在端板开关耳上，安装孔 Z 126.5 / 136、孔距 9.5，与 `refs/LIMIT_SWITCH.md` 的 KW11-3Z-A-1 规格一致；端板上开对应盲孔与 Ø4.8 安装孔。触发方向朝滑车，X 限位口袋 20.80 冻结项不变。

## 22.5 GUI 与预览

已同步到 SolidCraft GUI 用户目录：

```text
D:\mydocuments\SolidCraft\X_Axis_Slide.sc
D:\mydocuments\SolidCraft\X_AXIS_SLIDE_PARAMS.csv
D:\mydocuments\SolidCraft\X_Axis_Slide_iso_white.png
D:\mydocuments\SolidCraft\X_Axis_Slide_top_white.png
D:\mydocuments\SolidCraft\X_Axis_Slide_GUI_fit.png
```

源与 GUI 副本 sha256 一致：

```text
638624deecb11f5942885b7be4d15c47cb384bc520e56e269dda29fe116e7a60
```

已在 SolidCraft GUI 中直接打开并 `view.fit`：`errors 0 / features 116`，窗口内可见完整模型。此前 MCP 报 `os error 10060` 是因为 `current.port` 指向 27878、而工具默认连 49187；改用当前端口后打开正常。

## 22.6 文件清单

| 文件 | 说明 |
|---|---|
| `solidcraft/X_Axis_Slide.sc` | 当前 X 轴滑台权威设计（20 body / 118 参数） |
| `solidcraft/20_x_axis_build.json` | 原生构建命令（含端板与限位开关） |
| `solidcraft/21_x_axis_verify.json` | 冻结尺寸 / 干涉 / 参数 / 外观只读验证 |
| `solidcraft/X_AXIS_SLIDE_PARAMS.csv` | 118 项用户参数表 |
| `refs/scripts/build_x_axis_slide.py` | 可重复生成脚本 |
| `refs/tmp/20_x_axis_build_cli.json` | 构建 CLI 证据 |
| `refs/tmp/x_axis_slide_eval.json` | 逐 body bbox / 面数 / 体积 / timeline 证据 |
| `refs/tmp/21_x_axis_verify_cli.json` | 0 干涉 + 20.8 限位口袋验证证据 |
| `refs/drawings/X_Axis_Slide_iso_white.png` | 白底等轴测图 |
| `refs/drawings/X_Axis_Slide_top_white.png` | 白底俯视图 |

## 22.7 边界说明

- 型材为真实 BREP 截面 1:1；端板、滑车、同步带、同步轮、电机仍是 **语义化原生参数化重建**，不是逐面 1:1 复刻。
- 本版是单独 X 轴静态滑台，没有加 X 行程 slider / motion study；如需运动，应在确认结构后再加组件与 joint。
- 参考模型中的 washer / nut / 限位开关 / rod tap / fix screw / clamp key 尚未纳入本版；当前 14 body 覆盖用户明确点名的型材、端结构、Ø6 导杆、LM6UU、同步带、同步轮和 42 电机。
