# X-print

面向工控喷墨打码机的 **X / Z 十字滑台 + HP45 热发泡喷头** 机械设计工程。

FreeCAD 1.1 单一装配文件，包含十字滑台本体、HP45 墨盒夹持总成、保湿站，
并配有 TechDraw 出图脚本，可一键重出 A1 整机三视图与 A2 喷头总成图。

> **当前版本（2026-11-10）**：主模型 `CrossSlide_P014013.FCStd` 几何为 **v13.2，151 对象**；
> 材质方案为 **v14** —— `139` 个 `Part::Feature` 全部赋值，共 `21` 种材质。
> HP45 旁置接触式连续测高探针的座体 / 臂体 / 侧盖板为**沿 X 分型的可注塑结构**：
> `-X` 敞开腔 + 侧盖板 + 座体一体顶棚，取消独立阶梯顶塞。
> **v13.2（本版几何）**：`Z76.50..81.50` 改为 **8×8 磁环全行程通道**（覆盖 0~+3.0 mm），
> `Z81.50..87.50` 保留 **6.20 窄腔**给 Ø6 弹簧做单边 0.10 紧导向；弹簧采购规格 / k / F0 不变。
> `verify_v13_2.py` 全绿：通道净空 OK / 脱模阻挡 0 / 静态干涉 0 / 装配阻塞 0 /
> 行程干涉 0 / 8×8 越界 0 / 冻结项 OK / FCStd 回写 OK；
> `verify_writeback_v13_2.py` 证明回写后**仅 2 件几何改变、其余 137 件几何等价**；
> `verify_materials.py` 结论为「UUID 139/139 可解析 / ZIP 完整 / CONCLUSION PASS」。
> 用户口径：**异型结构件采用 PETG 材质 3D 打印**（16 件，见 4.6 节）。
> 采购、装配和图纸口径见 `refs/POGO_BOM.md` 第七节与**第十七节**；材质口径见第十六节。

> **状态更新（2026-11-22）**：因 SolidCraft 侧发现几何/布尔类问题，项目已**回退到迁移前的 FreeCAD 主模型**：
> `CrossSlide_P014013.FCStd`（v13.2 几何 + v14 材质）重新成为唯一权威设计文件；第 8 节及 `solidcraft/`
> 下的迁移、运动、爆炸图、LM6UU、X 轴总装、端板分层复刻等成果均保留为**历史参考，不作当前交付基线**。
> 当前主模型已恢复到回退前校验状态：152 对象 / 140 个 `Part::Feature`（均带 `ShapeMaterial`）/ 21 种项目材质；
> v13.2 探针座、盖板几何与冻结项复核通过。SolidCraft 相关文件未删除。
> **2026-11-22 设计变更**：X / Z 滑车轴承座由“0.3 台阶 + 0.2 挡唇 + Ø10.2 让位”改为**两侧对称 1.5 mm 台阶**，
> 并把座段总长从 33 缩到 **29**（两端孔段 8.7 → **6.7**，座孔 15.6 / 轴承 15 / 两端 0.3 浮动不变）；
> 缩短后端面四角原 R4 圆角被截断，已用几何布尔重建为**完整 R2 圆角**（每半体 4 处，精确 Y 边界，无新增干涉）；
> 并在 X 滑车上半补 4 个 M3 螺钉让位孔。当前剖面：`Ø7 × 6.7 → Ø10 座孔 × 15.6 → Ø7 × 6.7`。
> **2026-11-22 减重窗变更**：X 滑车（上下半）中间减重窗两端连同 0.7 mm 台阶**整体填实以增强结构强度**，
> 窗底由带台阶变为**单一平面**，窗宽由 **23 改为 18**（窗底平台 X=141..159、Z=132.45）；
> 沉孔、轴承座、导杆配合不变，无效干涉。备份 `refs/tmp/fcstd_states/before_window_18_20261122.FCStd`。
> **2026-11-22 Z 滑车裁短**：`Z_Carriage_Lower/Upper` 沿 Z 由 29 裁到 **24**（Z=125..149，两端各 2.5），
> 按用户红框范围直接裁切，沉孔被切平成缺口；轴承座孔 Z=129.2..144.8 完整保留，与导杆/轴承/端板等我方零件干涉 0。
> 备份 `refs/tmp/fcstd_states/before_ztrim_20261122.FCStd`。
> **2026-11-23 全天修改已回退**：用户要求“退回到今天最开始的状态”。当前唯一权威主模型已恢复为
> `refs/tmp/fcstd_states/before_window15_20261123.FCStd`（SHA256 `92e248f2…`），即当天第一次修改前的状态：
> X 滑车减重窗 **18**（X=141..159），台阶 **1.2 mm**（窗底 Z=131.25），同步带避让尚未做，
> 因此上下滑车与同步带各恢复约 **5.074 mm³** 的历史干涉（当日后续修复已撤销）。
> 回退前的 11-23 版本（窗宽 16 + 同步带避让，SHA256 `bc7270e1…`）保存在
> `refs/tmp/fcstd_states/before_revert_to_daystart_20261123.FCStd`，需要时可再恢复。
> 当日曾做的 15→16、错误补料及回退、同步带避让、四角贯穿螺杆方案验证均只作为历史记录，**不是当前基线**。
> **2026-11-25 设计变更（X 滑车让位孔豁口修复）**：11-22 把座段 33→29 时切掉了 X<135.5 / X>164.5，
> 而 4 个 M3 让位孔（Ø3.2，孔心 X=136.5/163.5、Z=118/148）外缘到 X=134.9/165.1，被削掉 0.6 mm 成豁口。
> 本次把 X 滑车上下半的 X 向总长恢复并加大到 **34.2**（X=132.90..167.10，每端比 29 版补 2.6 mm），
> 端部几何取自 33 mm 备份 `before_shorten_29_20261122.FCStd` 以保留完整圆孔，再向外延伸到 34.2；
> 同步带区域按带实体求交避让，轴承孔段 R3.5 同步延伸。
> 结果：4 孔全部 **360° 完整圆**，孔心到端面壁厚 **2.0 mm**（满足 PETG 件孔壁厚 ≥2 mm 规范）；
> 两件均有效单实体；导杆/LM5UU/端板/XZ 板/HP45 适配板/同步带/带轮/丝杆螺母干涉**全部零增量**
> （带干涉维持原 10.1472 mm³），上下半互穿 0。主模型 SHA256 `c1348087…`；
> 修复前备份 `refs/tmp/fcstd_states/before_notchfix_20261125.FCStd`（SHA256 `92e248f2…`）。
> **2026-11-25 续（端面四角 R2 圆角重建）**：加大到 34.2 后端面外扩 2.6 mm，11-22 的 R2 圆角未跟随，
> 四角变成「薄片尖角 + 凹口 + 旧 R2 残面」拼接的毛刺。`makeFillet` 在残面交线上仍报 `StdFail_NotDone`；
> 改用 11-22 验证过的 **fill + cut** 布尔法（`fill 盒 Y 范围精确等于半体边界`，再切「2×2 盒 − R2 圆柱」）：
> 每半体四角重建为 **4 个完整 90° R2 圆角**，尖角直线边 0；上下半有效单实体、bbox 不变；
> 4 个 M3 让位孔仍 360°、带通道空腔正常、13 件相邻干涉零增量（带维持 10.1472）、互穿 0。
> 主模型 SHA256 `ccebe351…`；重建前备份 `refs/tmp/fcstd_states/before_r2_corners_20261125.FCStd`（SHA256 `c1348087…`）。
> **2026-11-25 续（Z 滑车 24 → 30）**：`Z_Carriage_Upper/Lower` 的 4 个 Ø3.6 安装孔（X=135/165、Z=127/147）距 Z 边缘仅 0.2 mm，
> 按「单边加大 3 mm」把 Z 向总高 24 → **30**（Z=122..152，两端各 +3），孔壁变为 3.2 mm。
> 端部几何取自裁短前备份 `before_ztrim_20261122.FCStd`（原 29 mm 版本），超出的 0.5 mm 用纯 box 补；
> 补料按 **Z 导杆 + Z 同步带实体求交避让**（否则导杆各新增 9.82、带新增 7.60 mm³），四角重建 R2 圆角。
> 结果：4 孔仍 360°、两件有效单实体、尖角 0、每半体 4 个 R2；17 个相邻件干涉零增量、互穿 0。
> 主模型 SHA256 `01a2e2d4…`；变更前备份 `refs/tmp/fcstd_states/before_zextend_20261125.FCStd`（SHA256 `ccebe351…`）。
> **2026-11-25 续（X 滑车 4 让位孔对称化）**：X 滑车 4 个 M3 让位孔原在 Z118/148（孔群中心 Z133，偏离板中心 Z137 下 4 mm）。
> 直接上移 4 mm 到 Z122/152 会撞两根 X 导杆（各新增 2.70 mm³）并切进轴承座 r3.5 段（3.92→27.39 mm³）——**不可行**。
> 改用关于板中心 Z137 对称的 **Z128/146**（下孔 +10、上孔 −2，孔距 30→18），导杆/轴承/同步带/带轮/端板等 15 件干涉零增量、间隙 ≥1.9 mm。
> `HP45_CarriageAdapter` 的 4 个对位孔与 `HP45_AdptScrew_0..3` 同步移到 Z128/146（d=128 两颗 +10、d=146 两颗 −2），4 孔与 4 对位孔均 360°。
> 主模型 SHA256 `d1c9bf54…`；变更前备份 `refs/tmp/fcstd_states/before_xhole_shift_20261125.FCStd`（SHA256 `01a2e2d4…`）。
> **2026-11-25 续（带槽壁厚修正，最终）**：Z128/146 虽躲开导杆，但孔缘到同步带槽壁只剩 0.75 mm（切穿槽壁，PETG 规范 ≥2 mm）。
> 改为关于 Z137 严格对称的 **Z125.9 / 148.1**（下孔 +7.9、上孔 +0.1，孔距 22.2 mm）：导杆/LM5UU 干涉 0，
> 孔缘到带槽壁厚 bottom 5.50 / top **2.10** mm；对位孔与 4 螺丝同步移到 Z125.9/148.1。
> 15 件相邻件与原始基线对比零增量（带维持 5.0736），4 孔与 4 对位孔均 360°。
> 主模型 SHA256 `c8357969…`；变更前备份 `before_xhole_shift_20261125.FCStd`（SHA256 `01a2e2d4…`）。
>
> **2026-11-25 续（四孔移到板角，当前基线）**：Z125.9/148.1 的孔缘仍越过导杆表面 0.20 mm（几何重叠 0.245 mm³/孔），
> 按用户示意把 4 个 M3 让位孔移到板件四角。精确核算后取 X=137/163、Z=115.6/158.4（关于 X150、Z137 严格对称，孔距 26×42 mm）：
> 导杆净距 **2.30 mm**、板边壁厚 X 2.5 / Z 2.0 mm（PETG ≥2 达标）、4 孔与 4 对位孔均 360°、同步带零干涉。
> 连带把 `HP45_CarriageAdapter` 顶端从 Z156 加长到 Z162（与全机零干涉），4 个 Ø3.4 对位孔与 4 颗螺丝同步移到新位。
> 19 件相邻件与基线对比零增量（带维持 5.0736）。主模型 SHA256 `7f893605…`；变更前备份 `before_cornerholes_20261125.FCStd`（SHA256 `c8357969…`）。

![整机三视图](refs/System_Assembly_A1.png)

---

## 1. 系统构成

| 模块 | 说明 |
|---|---|
| **Z 轴（升降）** | 2040 铝型材 150 mm + 两根 **Ø5** 导杆（165 mm），配 2× LM5UU（Ø10×15），GT2 同步带，NEMA17 驱动 |
| **X 轴（横移）** | 2040 铝型材 200 mm + 两根 **Ø5** 导杆（215 mm），配 2× LM5UU（Ø10×15），GT2 同步带，NEMA17 驱动 |
| **XZ 连接板** | 10 mm 厚，连接两轴，构成十字滑台 |
| **HP45 喷头总成** | HP45 墨盒 + 卡扣（latch）+ 压紧弹片 + 墨盒座 |
| **探针** | 安装在喷头 X 方向前方，测量墨盒喷嘴面到工件的高度 |
| **保湿站** | 停机时密封喷嘴，防止墨水干涸 |
| **限位开关** | X / Z 各两个，**KW11-3Z-A-1**（无摆杆直压按钮式微动开关），M2.5 螺钉固定，按钮先触发；资料见 `refs/LIMIT_SWITCH.md` |

### 关键尺寸

```
整机包络     X 0..300   Y -171.252..45   Z -4..262  (mm)
Z 轴导杆     165 mm       X 轴导杆  215 mm
Z 轴型材     150 mm       X 轴型材  200 mm
底板螺钉     6 × M4×16   (Ø8.4 沉孔 / Ø4.5 通孔)
限位开关     2.6 孔 × M2.5
```

---

## 2. 文件结构

```
X-print/
├── CrossSlide_P014013.FCStd          # 主装配文件（FreeCAD 1.1，v13.2 几何 + v14 材质，151 对象）
├── solidcraft/                       # SolidCraft 迁移 + 材质 + 运动仿真 + 爆炸图（见第 8 节）
│   ├── CrossSlide_P014013.sc         #   几何迁移基线（140 个零件名 100% 保留）
│   ├── CrossSlide_P014013_motion.sc  #   完整交付：v14 材质 + 运动链 + 打码 study
│   ├── CrossSlide_P014013_exploded.sc #  爆炸视图设计 V1（view 425 / 100 moves）
│   ├── CrossSlide_exploded.png       #   整机功能组爆炸图 V1（2544×1957，深灰底）
│   ├── CrossSlide_P014013_exploded_v2.sc # 爆炸视图设计 V2（view 425 / 127 moves，Z 电机 [0,80,0]）
│   ├── CrossSlide_exploded_v2.png    #   V2 深灰底裁切源图（2209×1323）
│   ├── CrossSlide_exploded_v2_white.png     # V2 纯白底无标注图
│   ├── CrossSlide_exploded_v2_annotated.png # V2 最终图：白底 + 中文标注 + 装配顺序线 + 已核实圆点
│   ├── CrossSlide_coding_cycle.gif   #   打码循环动画（1920×1200 / 29 帧）
│   ├── LM6UU_Native.sc               #   【历史 v1，已否定】全原生语义化参数化设计（见 8.3）
│   ├── LM6UU_Profile_Exact.sc        #   【当前型材阶段权威】真实 BREP 2040 截面 1:1（见 8.4）
│   ├── 13_profile_exact.json         #   43 条精确截面命令 / 11 用户参数 / 零 STEP
│   ├── LM6UU_PROFILE_EXACT_PARAMS.csv#   11 行精确截面参数表
│   ├── LM6UU_Profile_Exact_section.png / _iso_white.png / _GUI_fit_white.png # 截面 1:1 对比 / 白底等轴测 / GUI fit
│   ├── CrossSlide_XZ.sc              # 【当前十字滑台静态主体】18 body / 100 用户参数 / 零 STEP（见 8.5）
│   ├── CrossSlide_XZ_mech.sc         # 【当前十字滑台机构】X/Z 两个 slider + CrossSlide_Cycle study
│   ├── 14_cross_slide_xz.json        # 238 条十字滑台原生命令（精确型材 + 8 结构件 + 导杆/轴承）
│   ├── CROSS_SLIDE_XZ_PARAMS.csv     # 100 行十字滑台参数表
│   ├── 15_cross_slide_xz_verify.json # 冻结项 / 干涉 / 参数 / 外观只读复核脚本
│   ├── 16_cross_slide_mechanism.json # 组件分组 + X/Z slider + motion study
│   ├── CrossSlide_XZ_iso_white.png / _top_white.png # 白底等轴测 / 俯视
│   ├── CrossSlide_XZ_headless_fit.png # Headless model fit 渲染
│   ├── LM6UU_Native_iso.png          #   v1 整机白底等轴测图
│   ├── LM6UU_Native_seat_detail.png  #   全原生 LM6UU 轴承座半透明近景图
│   ├── 07_lm6_native.json            #   224 条全原生建模命令（104 参数 / 36 box / 74 cylinder / 4 fillet）
│   ├── 08_lm6_native_verify.json     #   只读复核：冻结项实测 + 全配对干涉 + 参数清单
│   ├── 09_lm6_native_paramtest.json  #   只读参数联动 A：SEAT_R
│   ├── 10_lm6_native_paramtest_frozen.json # 只读参数联动 B：X_CAR_Z0 / Z_SLOT_W
│   ├── 11_lm6_native_appearance.json #   只读外观读回（18/18 body）
│   ├── LM6UU_NATIVE_PARAMS.csv       #   104 行全原生参数表（分组 / 表达式 / 说明）
│   ├── LM6UU_Redesign.sc             #   【历史中间方案】混合式参数化（已被全原生取代）
│   ├── LM6UU_Redesign_iso.png        #   混合方案整机白底等轴测图
│   ├── LM6UU_Redesign_seat_detail.png#   混合方案 LM6UU 轴承座近景图
│   ├── 06_lm6_redesign.json          #   混合方案 44 条命令
│   ├── LM6UU_PARAMS.csv              #   混合方案 LM5UU → LM6UU 参数对照表
│   ├── LM6UU_base6.step / LM6UU_xplates_lm6.step / LM6UU_reference_profiles.step # 混合方案真几何输入
│   ├── LM6UU_interfaces.json         #   8 件接口几何清单
│   ├── 01_*.json ~ 13_*.json        #   可复现命令脚本（04 V1 / 05 V2 爆炸 / 06 混合 / 07~11 v1 / 12 预览 / 13 精确截面）
│   ├── MATERIAL_ASSIGNMENTS_SC.csv   #   144 body → 材质对照表
│   ├── EXPLODED_GROUPS.csv           #   V1 140 行功能组 / 位移审计表
│   ├── EXPLODED_GROUPS_V2.csv        #   V2 140 行功能组 / 位移审计表
│   ├── EXPLODED_ANNOTATIONS_V2.csv   #   V2 11 行中文标注 / 锚点 / 锚点来源 / 装配链审计表
│   └── build_manifest.json           #   计数 / 关节 id / 材质分布
├── refs/
│   ├── POGO_BOM.md                   # 探针采购 / 加工 / 装配清单（v13.2 几何 + v14 材质）
│   ├── SOLIDCRAFT_MIGRATION.md       # FreeCAD → SolidCraft 迁移与逐件几何核验报告
│   ├── SOLIDCRAFT_MOTION.md          # SolidCraft 材质赋值 + 打码运动仿真报告
│   ├── SOLIDCRAFT_EXPLODED.md        # SolidCraft 功能组爆炸图报告 V1
│   ├── SOLIDCRAFT_EXPLODED_V2.md     # 升级版爆炸图报告 V2（更细爆炸+白底+中文+顺序线）
│   ├── SOLIDCRAFT_LM6UU_REDESIGN.md  # LM6UU / Ø6 导杆重设计报告（§1–19 历史 / §20 精确截面阶段）
│   ├── materials/                    # v14 项目材质库（21 个 .FCMat + 映射表 + 几何基线）
│   │   ├── *.FCMat                   #   材质定义（须同步安装到 FreeCAD 用户材质库）
│   │   ├── material_assignments.csv #   139 件对象 → 材质对照表
│   │   ├── material_summary.json    #   21 种材质总表（UUID / 密度 / 弹性 / 颜色）
│   │   ├── geometry_snapshot_v14.json #  材质设置前几何快照
│   │   └── baseline_v13/*.brp       #   3 件 v13 主件 BREP 几何基线
│   ├── pogo_parts_drawing.png        # v13.2 探针零件图
│   ├── hall_probe_assembly_3view.png # v13.2 探针三视图装配图（另有 .pdf）
│   ├── LIMIT_SWITCH.md               # 限位开关 KW11-3Z-A-1 选型与规格卡
│   ├── scripts/
│   │   ├── build_v13_2.py            # v13.2 几何构造（8×8 通道 + 6.20 导向段）
│   │   ├── verify_v13_2.py           # v13.2 全量核验（含全行程 8×8 越界检查）
│   │   ├── writeback_v13_2.py        # v13.2 FCStd 安全回写
│   │   ├── verify_writeback_v13_2.py # 回写后逐件几何等价核对
│   │   ├── build_v13.py              # v13 主件几何构造（历史）
│   │   ├── verify_v13.py             # v13 注塑 DFM + 装配全量核验（历史）
│   │   ├── writeback_v13.py          # v13 FCStd 安全回写（历史）
│   │   ├── apply_materials.py        # v14 材质库生成 + FCStd 材质赋值（可复现）
│   │   ├── verify_materials.py       # v14 材质读回 / 几何冻结 / ZIP 完整性核验
│   │   ├── build_solidcraft_motion.py #  SolidCraft 材质 / 运动三阶段命令生成器
│   │   ├── build_exploded_view.py    #  功能组爆炸视图 V1 命令生成器
│   │   ├── build_exploded_view_v2.py #  功能组爆炸视图 V2 命令生成器（更细分组 + Z 电机纯 +Y）
│   │   ├── annotate_exploded_view.py #  白底 / 中文标注 / 装配顺序线 / 锚点覆盖生成器（投影定标）
│   │   ├── verify_exploded_anchors.py #  11 个引线圆点分色像素核实（PASS 11/11）
│   │   ├── extract_lm6_interfaces.py #  FCStd BREP 直读 + 8 件接口几何提取
│   │   ├── build_lm6_geometry.py     #  16 处去料 + 冻结/干涉/挡肩全量验证 + named STEP
│   │   ├── build_lm6_redesign.py     #  混合方案 44 条命令生成器（历史）
│   │   ├── build_lm6_native.py       #  v1 历史：全原生 224 条命令生成器（已被用户否定）
│   │   ├── extract_native_recipe.py  #  8 件 BREP 配方提取（Plane/Cylinder 分析）
│   │   ├── build_native_recipe.py    #  自动盒分解复刻（已否决，保留决策记录）
│   │   ├── render_lm6_views.py       #  整机图渐变底转白 + 紧裁（混合 / 全原生两版）
│   │   ├── extract_profile_contours.py # 2040 BREP 有序曲线提取（修正 Ø5 孔 / R1.5 圆弧）
│   │   ├── build_profile_exact.py    #  当前型材阶段：43 条精确截面命令 + --verify 25 项保真度
│   │   ├── render_profile_preview.py #  阶段预览 / 精确截面白图与 1:1 对比图
│   │   ├── build_cross_slide_xz.py   #  十字滑台原生参数化构建（精确型材 + 8 结构件 + 导杆/轴承）
│   │   ├── verify_cross_slide_xz.py  #  几何/冻结/干涉/参数/运动汇总验证（PASS）
│   │   ├── export_lm6_reference_step.py # 铝型材真几何 STEP 导出
│   │   ├── export_lm6_base8_step.py  #  8 件真几何基座 STEP（诊断用）
│   │   ├── draw_parts_v12.py         # 文件名保留，内容已同步 v13.2 零件图
│   │   └── draw_assembly_3view.py    # 内容已同步 v13.2 三视图装配图
│   ├── make_system_drawing.py        # A1 整机三视图后处理脚本
│   ├── make_assembly_drawing.py      # A2 喷头总成图后处理脚本
│   ├── System_Assembly_raw.svg       # TechDraw 原始导出（脚本输入）
│   ├── System_Assembly_A1.svg/.png/.pdf   # A1 整机三视图成品
│   ├── HP45_Assembly_A2.svg/.pdf     # A2 喷头总成图
│   ├── HP45_Mechanical/              # HP45 卡扣原始 STEP / 图纸（第三方）
│   └── HP45_Electronics/             # HP45 控制器固件 / KiCad（第三方）
└── .gitignore
```

### 主装配文件的对象分组

| 前缀 | 内容 |
|---|---|
| `Z_*` | Z 轴：型材、端板、导杆、同步轮、同步带、滑座、直线轴承、电机、限位开关 |
| `X_*` | X 轴：同上 |
| `XZ_*` | 十字连接板 |
| `HP45*` | 墨盒、卡扣、压紧弹片、座、探针 |
| `Cap_*` | 保湿站 |
| `LimitScrew_1..8` | 限位开关螺钉（X 4 颗 / Z 4 颗） |
| `SYS_*` / `V_*` | TechDraw 视图（A1 整机 / A2 喷头） |

---

## 3. 重新出图

出图分两步：先在 FreeCAD 里导出 TechDraw 原始 SVG，再跑 Python 脚本叠加
标题栏、尺寸标注和技术要求。

### 3.1 导出 TechDraw 原始 SVG

在 FreeCAD Python 控制台执行：

```python
import FreeCAD as App, FreeCADGui as Gui, TechDrawGui

d = App.ActiveDocument
Gui.activateWorkbench('TechDrawWorkbench')
page = d.getObject('System_Assembly_Drawing')
page.ViewObject.show()
for vn in ('SYS_Front', 'SYS_Top', 'SYS_Left', 'SYS_Iso'):
    d.getObject(vn).ViewObject.show()
d.recompute()

TechDrawGui.exportPageAsSvg(page, r'refs/System_Assembly_raw.svg')
```

> **注意**：`page.show()` 不存在，必须用 `page.ViewObject.show()`。
> 若导出后 SVG 明显偏小（约 2.3 MB 而非 2.9 MB），说明视图尚未计算完，
> 再 `recompute()` 一次并等 2 秒重新导出。

### 3.2 生成成品图

```bash
python refs/make_system_drawing.py
```

脚本会输出 `System_Assembly_A1.svg`。PNG / PDF 需要 Qt 绑定，
在 FreeCAD GUI 里 `import make_system_drawing` 即可一并生成。

---

## 4. 设计要点与约束

### 4.1 限位开关安装位

选型为 **KW11-3Z-A-1**（`19.80 × 6.50 × 12.20` 含按钮，2×Ø2.60 孔距 9.50，SPDT COM/NO/NC，
AC250V 0.5A）。同系列带 16.50 mm 滚轮弹片的 `KW11-3Z-B-2` 已评估否决（多占 6 mm/轴行程）。
完整规格、接线与采购注意见 `refs/LIMIT_SWITCH.md`，原始规格图在 `refs/datasheets/`。

两轴的安装槽尺寸**刻意不同**，各自独立：

| | 安装槽 | 开关 | 单边间隙 |
|---|---|---|---|
| **X 轴** | Z **20.80**（120.85..141.65） | 19.80 | **0.50 / 0.50** |
| **Z 轴** | X **22.00**（139.00..161.00） | 19.80 | **1.10 / 1.10** |

Z 轴槽宽 22.00 本来就比 20.80 大，间隙更宽松，**不要再收紧到 20.80** ——
那样反而要往槽里加料 1.20 mm，把间隙压到 0.50。

X 轴口袋入口处有 **0.65 × 0.65 的 45° 导入倒角**（4 处：左右端板 × 上下），
便于开关装入。倒角由多刀切割边界差 0.10 mm 留下的直角台阶改来。

### 4.2 螺钉咬合量

| | 螺纹咬合 | 说明 |
|---|---|---|
| X 轴限位螺钉 | 1.10 mm（1.5896 mm³） | 受口袋底面位置限制 |
| Z 轴限位螺钉 | 2.80 mm（4.0464 mm³） | 受端板壁厚 4.40 mm 限制，M2.5 约 1.12D |

### 4.3 同步带间隙

- X 轴开关安装台距同步带前表面 **3.50 mm**
- Z 轴限位螺钉杆端距同步带 **1.60 mm**

两轴限位螺钉与同步带的干涉均已归零。

### 4.4 3D 打印注意（异型结构件，v14 PETG 口径）

异型结构件统一为 **PETG FDM 3D 打印**（v14 口径，**不再是树脂 / SLA 件**）。
主模型里共 16 件已标记 `PETG-FDM 异型结构件`：X / Z 端板与上下滑座、`Z_BaseBlock`、
`HP45_CarriageAdapter`、`Cap_Tray`、`HP45CAR_*` 夹具五件（完整清单见 4.6 节）。

打印参数：`0.4 mm` 喷嘴 / 层高 `0.20` / 4 周壁 / 40% 网格填充 / 240 °C 喷嘴 / 80 °C 热床。
PETG 层间结合弱于 PLA，**承力方向必须避免层间受拉**，必要时调整打印摆位或改局部加厚。
端板设计已考虑：

- 沉孔处局部加厚 2 mm，凸台 3 mm，螺钉头完全齐平
- 端板收敛为单一实体，无游离碎块
- 螺纹孔壁厚不低于 2 mm；M3 建议用热熔铜嵌件而非直接攻丝

### 4.5 探针总成主件 v13.2 注塑注意（8×8 磁环全行程通道）

探针座 `HP45_ProbeHousing`、探针臂 `HP45_ProbeArm` 与 `-X` 侧盖板 `HP45_SpringSpacer` 已按可注塑结构改造：

- 主分型沿 X：8×8 通道型芯 / 6.20 导向型芯向 `-X` 抽出，霍尔窗型芯向 `+X` 抽出，无需侧滑块；
- **8×8 磁环全行程通道** `Z76.50..81.50`：座体 `X70.30..82.00 / Y−116.50..−108.50`，盖板补形到 `X74.00`；扣盖后净空 8.00 × 8.00，磁环 Ø6 单边净空 1.00 mm，覆盖 `dz=0..+3.0` 全部位置；
- **6.20 弹簧导向段** `Z81.50..87.50`：座体 `X70.30..81.10 / Y−115.60..−109.40`，盖板补形到 `X75.00`（`−Y` 边 `Y−114.90` 给 M3 杆留 0.38 mm）；Ø6 弹簧单边 0.10 mm 紧导向防压缩偏斜；
- **弹簧 Ø6 / Ø4.6 / 0.30×12 圈不变**：`k ∝ 1/D³`，缩小外径会把 F0 从 0.045 N 抬到 0.080 N（Ø5）甚至 0.105 N（Ø4.6），超出 0.03~0.08 N 目标；防偏斜靠窄腔导向而非缩簧；
- 座体 `Z87.50..90.00` 为**一体顶棚**，底面 `Z87.50` 作弹簧上止挡，中心只留 Ø2.50 针尾孔；独立阶梯顶塞已取消；
- 名义壁厚 2.0 mm、脱模斜度 1.5°、内角 R0.4；Ø2.37 / 2×M3 / Ø2.50 细长孔后钻/铰或铜嵌件；
- 装配改为「磁环 / 弹簧 `+X` 侧装 → 探针 `−Z` 顶落 → 原位点胶 → 盖板 `+X` 扣合」；顶棚只有 Ø2.50，磁环不能再预粘在针身上从顶部塞入；
- 磁环由针杆 / R125 针套定心，不靠腔壁；放大通道不会引入磁路偏心。`Z76.50` 下台阶与 2.00 零位高度、霍尔 r=5.90 / X83.40 / Z79.00、Z 轴 22.00、X 轴 20.80 等冻结项均未改动；
- 当前 FCStd 是名义直壁验证几何，正式模具 CAD 需加入斜度 / 圆角 / 卡扣细部并复验间隙。

完整口径与验收记录见 `refs/POGO_BOM.md` **第十七节**、`refs/scripts/verify_v13_2.py` 与 `refs/tmp/verify_v13_2.log`。

### 4.6 v14 材质方案（已写入 FCStd）

用户口径：**异型结构件采用 PETG 材质 3D 打印**。主模型 `139` 个 `Part::Feature`
已全部设置 FreeCAD 1.1 的 `ShapeMaterial`（`Materials::PropertyMaterial`）、
视图 `ShapeColor` 与文字标记 `MaterialSpec`，共 `21` 种材质，**无遗漏、几何未动**。

| 材质（FCMat 名） | 件数 | 密度 kg/m³ | 归属 |
|---|---:|---:|---|
| `PETG-FDM 异型结构件` | **16** | 1270 | **异型结构件，FDM 打印** |
| `POM注塑探针座与侧盖板` | 2 | 1410 | v13.2 量产注塑主件 |
| `PA66-GF30注塑探针臂` | 1 | 1360 | v13.2 量产注塑主件 |
| `8.8级碳钢紧固件` | 70 | 7850 | 外购标准件 |
| `GCr15淬硬导杆与轴` | 6 | 7830 | 外购 |
| `GCr15直线轴承LM5UU` | 4 | 7830 | 外购 |
| `黄铜热熔螺母与针套` | 6 | 8500 | 外购 / 车削 |
| `PU玻纤GT2同步带` | 6 | 1200 | 外购 |
| `6063-T5 铝型材2040` | 2 | 2700 | 外购型材锯切 |
| `6061-T6 铝合金板` | 1 | 2700 | XZ 连接板 CNC |
| `铝合金GT2同步轮` | 4 | 2700 | 外购 |
| `NEMA17步进电机总成` | 2 | 4500* | 外购总成（等效密度） |
| `机械式限位开关` | 4 | 1400* | 外购，**KW11-3Z-A-1** |
| `HP45墨盒ABS-PP壳体` | 1 | 1050 | 原装墨盒 / 参考体 |
| `N35钕铁硼镀镍磁环` | 1 | 7500 | 轴向充磁，逐只筛选 |
| `FR-4霍尔PCB与盖板` | 2 | 1850 | 转接 PCB / 盖板 |
| `A1324霍尔环氧封装` | 1 | 1500* | 外购 IC |
| `琴钢丝与不锈钢弹片` | 2 | 7900 | 弹簧 / 压紧弹片 |
| `硅胶TPU密封与护线` | 3 | 1150* | 防尘唇 / 护线 / 密封圈 |
| `保湿海绵` | 1 | 100* | 开孔 PU 泡棉 |
| `工艺辅助几何非零件` | 4 | 1000* | 攻丝孔辅助体，半透明，不计 BOM |

`*` 为等效估值，仅用于质量估算，不参与强度计算。完整 UUID、弹性模量、泊松比、
颜色与工艺说明见 `refs/materials/material_summary.json`；逐件对照见
`refs/materials/material_assignments.csv`。

**16 件 PETG 异型结构件**：
`Z_BaseBlock`、`Z_EndPlate_L/R`、`Z_Carriage_Lower/Upper`、`X_EndPlate_L/R`、
`X_Carriage_Lower/Upper`、`HP45_CarriageAdapter`、`HP45CAR_P01`、`HP45CAR_P02_L`、
`HP45CAR_P02_R`、`HP45CAR_P03`、`HP45CAR_P04`、`Cap_Tray`。

> **重要：FCStd 只保存材质 UUID**。FreeCAD 1.1 的 `Document.xml` 里材质只剩
> `<PropertyMaterial uuid="..."/>`，不含名称 / 密度 / 颜色。换机器打开前，必须把
> `refs/materials/*.FCMat` 安装到用户材质库
> `%APPDATA%/FreeCAD/v1-1/Material/X-Print/`，或在 FreeCAD 里运行
> `refs/scripts/apply_materials.py`（自动双写项目库与用户库）。缺库时材质会回落到
> `Default`，但零件上的 `MaterialSpec` 文字标记仍可查。

可复现流程：

```python
# 1. 在 FreeCAD GUI 的 Python 控制台执行（需已打开主文档）
exec(open(r'C/ink/refs/scripts/apply_materials.py', encoding='utf-8').read())
```

```bash
# 2. 独立进程闭环验证（不依赖 GUI；GUI 卡死时也能验证）
"/d/Program Files/FreeCAD 1.1/bin/freecadcmd.exe" refs/scripts/verify_materials.py
```

验证结果（`refs/tmp/verify_materials.log`）：`139/139` UUID 可解析、`21` 个唯一材质、
`139` 个 `MaterialSpec` 一致、与 v13 基线双向 `cut` 对称差体积 **0**（冻结项几何未动）、
FCStd `601` ZIP 条目 `testzip=None`、`151` 对象、`CONCLUSION PASS`；
GUI `reload_document` 重载后同样读回 `139/139` 材质与颜色。

> **几何与材质解耦**：v14 只赋材质，不改几何。Z 轴 22.00 / X 轴 20.80 /
> 磁环零位台阶 2.00 / 霍尔感测面 X83.40、中心 Z79.00 等冻结项全部保持 v13 原值。
> 之后的 **v13.2 只改了座体 / 盖板两件的腔体分段**（8×8 全行程通道 + 6.20 导向段），
> 材质赋值、磁路参数与上述冻结项均未改动；见 4.5 节及 `refs/POGO_BOM.md` 第十七节。

---

## 5. 待办 / 后续优化方向

- [ ] 控制器 PCB 是否外置，以及安装位置
- [ ] 探针电气选型与接口（信号类型、接插件）
- [ ] 拖链与墨管夹的走线路径
- [ ] 惰轮张紧槽（当前张紧靠端板长孔）
- [ ] 保湿站废墨刮片
- [ ] v13.2 注塑模具详细设计：斜度 / 圆角 / 浇口 / 顶针 / 2 处卡扣 / 缩水率与试模（两段腔型芯）
- [ ] 磁环原位点胶工装、实物筛选与逐只标定
- [ ] PETG 试打件实测：端板沉孔 / 热熔铜嵌件 / 螺纹孔壁厚 / 层间受拉方向
- [ ] 换机器或重装 FreeCAD 后，把 `refs/materials/*.FCMat` 装进用户材质库
- [ ] 待用户重新授权后推送 v13.2 几何 + v14 材质到 GitHub（`refs/tmp/push_api.py`）

---

## 6. 第三方来源

`refs/HP45_Mechanical` 与 `refs/HP45_Electronics` 来自开源项目：

- **HP45 Standalone Controller V4.02** — <https://github.com/yvodehaas/HP45-standalone-controller-V4.02>
- **HP45 Standalone V4 固件** — <https://github.com/yvodehaas/HP45-standalone-V4>
- **Inkjet Commander** — 上位机软件

这些目录保留了原始 LICENSE，版权归原作者所有，仅作为设计参考随附。
本项目自身的机械设计部分可自由参考使用。

---

## 7. 环境

| | 版本 |
|---|---|
| FreeCAD | 1.1.4 |
| Python | 3.13 |
| 出图脚本依赖 | 标准库；PNG/PDF 需 PySide（FreeCAD 自带） |
| SolidCraft | 本机 `solidcraft-cli` + MCP（允许路径见 `refs/SOLIDCRAFT_MIGRATION.md` 第 3 节） |

---

## 8. SolidCraft 迁移与打码运动仿真（2026-11-12）

> 完整报告：`refs/SOLIDCRAFT_MIGRATION.md`（几何核验）、
> `refs/SOLIDCRAFT_MOTION.md`（材质赋值 + 运动仿真）。

| 交付 | 内容 |
|---|---|
| `solidcraft/CrossSlide_P014013.sc` | 几何迁移基线：**140 个零件名 100% 保留**，137 件几何等价，3 件端板为开放壳 |
| `solidcraft/CrossSlide_P014013_motion.sc` | **完整交付**：在基线上赋 v14 的 21 种材质（144/144 bodies）、重建 Z/X/探针三级运动链、GT2 传动链、100 步打码工作循环 study；初始姿态已复位到 step 0 |
| `solidcraft/CrossSlide_P014013_exploded.sc` / `CrossSlide_exploded.png` | **爆炸图 V1**：view 425 功能组爆炸（6 组 / 100 条 moves）与 2544×1957 主图，详见 `refs/SOLIDCRAFT_EXPLODED.md` |
| `solidcraft/CrossSlide_P014013_exploded_v2.sc` / `CrossSlide_exploded_v2_annotated.png` | **爆炸图 V2（最新）**：更细爆炸 127 件 + 白底 + 11 组中文标注 + 装配顺序线 + 引线圆点已分色核实，详见 `refs/SOLIDCRAFT_EXPLODED_V2.md` |

**不能直接读 `.FCStd`**：SolidCraft 的 `cadmpeg` 直读路径会产生 129 个开放壳、3184 条警告、零件名全部退化。正式通道是
`FreeCAD 导出命名装配 STEP → SolidCraft open {names:"product", up:"z"} → file.save`，详见迁移报告第 2/3 节。

**运动链**：140 关节 = `rigid 131` / `revolute 6` / `slider 3`，`conflicts=[]` `errors=[]`：

- 三个移动关节：`Z 升降 / Z approach`（±30 mm）、`X 扫描 / X scan`（±85 mm）、`探针压缩 / probe stroke`（0~3 mm，与冻结项「有效行程 0..+3.0」一致）。
- GT2 16T 传动比 **11.25 deg/mm**，6 条 `motion_link` 驱动 4 个同步轮 + 2 根电机轴。
- study `打码工作循环 / Coding cycle`（100 步）：Home → Z 下降 3 mm → 探针压缩 3 mm 测高 → X 从 −40 扫到 +40 mm → 抬升 → X 到 +75 mm 保湿站上方 → 盖合密封。

**验证**：26 采样 / 160 对干涉检查 `collisions 0`；`motion.plot` 校验传动比与速度 / 加速度曲线；`motion.trace` 记录喷嘴轨迹 X +75 / Z −3；动画 `CrossSlide_coding_cycle.gif` **1920×1200 / 29 帧 / 14.29 fps**；几何总体积 `856894.075 mm³` 与迁移基线完全一致。

**口径提醒**：SolidCraft 侧**主模型 `motion.sc` 仍是 `LM5UU Ø10×15 + Ø5 导杆`**；LM6UU / Ø6 改造已作为**独立全原生新设计**落盘在 `solidcraft/LM6UU_Native.sc`（见 8.3），并未合并回主模型（`LM6UU_Redesign.sc` 是被推翻的混合式历史中间方案）；3 个开放端板仍不能做布尔；21 种材质是 SolidCraft 独立 user material，与 FreeCAD `.FCMat` UUID 不联动。若将来要把 LM6UU 改造合并回主设计，零件名与 occurrence id 会变，需**重跑迁移核验 + `refs/scripts/build_solidcraft_motion.py` 三阶段脚本**，再按 8.2 末尾顺序重跑爆炸/标注/圆点核实。

### 8.1 功能组爆炸图

用户指令：「再生成一张爆炸图」。完整报告 `refs/SOLIDCRAFT_EXPLODED.md`。

SolidCraft 的自动径向爆炸 `explode.create {scale:...}` 在本 STEP 扁平组件树上失败
（`an exploded view needs two or more occurrences`，140 个 occurrence 全挂 root `2`），
且逐件径向散开会把 70 个紧固件甩散、装配关系不可读。因此改为**显式 `moves` + 功能组共享位移**：
Z 轴骨架 40 件作基准不动，其余 6 组共 100 件沿 −Y 依次拉开并在 X / Z 交错：
Z 滑车 + XZ 连接板 23 `[0,-40,50]`、X 横梁总成 30 `[0,-85,0]`、X 滑车 10 `[0,-150,0]`、
HP45 喷头总成 18 `[-25,-235,0]`、接触式探针总成 13 `[-115,-235,0]`、保湿站 6 `[95,-55,0]`（单位 mm）。
分组与逐件位移见 `solidcraft/EXPLODED_GROUPS.csv`（140 行），命令脚本 `solidcraft/04_exploded_view.json`，
生成器 `refs/scripts/build_exploded_view.py`。

view id **425** `整机爆炸图 / Assembly exploded`。**`explode.show` 只改显示、不改 placement / B-rep**：
交付 `.sc` 的几何（总体积 `856894.075 mm³`）、21 种材质、study 424、step 0 与 `motion.sc` 完全一致；
打开文件默认是装配态，需手动 `explode.show {view:425}` 查看爆炸图。
主图 `solidcraft/CrossSlide_exploded.png` 为 **2544×1957 / 852182 B**，由 4096×3840 渲染
按模型 bbox 加 4.5% 边距裁切而来，模型占画面 91.7%。

### 8.2 升级版爆炸图 V2（更细爆炸 + 白底 + 中文标注 + 装配顺序线）

用户三条追加指令合并成**一张图**：「用中文标明部件名称，用线条标明空间装配的顺序和逻辑」、
「背景改为白色」、「还能再多炸开一些零部件吗」。完整报告 `refs/SOLIDCRAFT_EXPLODED_V2.md`。

| 项目 | V1 | **V2** |
|---|---|---|
| 移动件 | 100 | **127** |
| 固定基准 | 40（挤在一起，含端板 / 导杆 / 电机 / 限位） | **12**（真机架） |
| 分组 | 6 组 + 1 基准 | **10 组 + 1 基准 + 1 隐藏辅助** |
| 背景 | 深灰 `[46,52,64]` | **纯白** |
| 标注 | 无 | **11 组中文名称 + 序号 + 引线** |
| 顺序线 | 无 | 粗虚线主链 `1→10` + 绿色并行支路 `1→11` |

- **更细爆炸**：`refs/scripts/build_exploded_view_v2.py` 把 V1 挤在基准里的 40 件 Z 轴零件拆成
  5 个子组（Z 端板与导杆 / Z 同步带传动 / Z 步进电机 / Z 限位开关 / Z 滑车 + XZ 板），
  并加大原有 6 组位移；`solidcraft/05_exploded_view_v2.json`（127 moves）→
  `solidcraft/CrossSlide_P014013_exploded_v2.sc`（view 425 `整机爆炸图 V2`）。
- **白底**：SolidCraft 无 viewport 纯色背景命令，CLI `snapshot` 是渐变底 + 地平线；
  采用 MCP `screenshot {source:"model",grid:false,axes:false}` 的纯深灰底，再由
  `refs/scripts/annotate_exploded_view.py` 的 `to_white()` 用 alpha 近似 + `MaxFilter` 边缘权重换白。
- **中文 + 顺序线**：11 个锚点由 3D bbox + 爆炸位移经**等轴测投影自动定标**
  （最终 `scale 2.4371 px/mm`，非手工点选）；标签用积分图避让，11 框与模型重叠 ≈0%；
  线加白色 halo 保证压在深色零件上仍清晰。装配逻辑：
  `1 Z 机架 → 2 端板导杆 → 3 同步带 → 4 电机 → 5 限位 → 6 Z 滑车 → 7 X 横梁 → 8 X 滑车 → 9 HP45 喷头 → 10 探针`，保湿站 `11` 并行。
- **序号牌去碰撞**：出图后按用户截图反馈修正了「序号 3 压住序号 2」——两组 Z 轴部件投影质心
  相距仅 13.5 px、徽标却有 42 px。`annotate_exploded_view.py` 新增 `place_badges()` 自动推开到
  ≥52 px，装配链改连徽标，被推开的牌用同色短细线回指真实锚点（详见 V2 报告 4.6 节）。
- **Z 步进电机改为沿安装螺钉轴线直抽**：用户指出「Z 轴电机位置不对，应沿安装螺钉方向平移出来」。
  依 `refs/materials/geometry_snapshot_v14.json`，4 颗 `Z_Screw_Motor_*` 包围盒 `5.49×13.00×5.48 mm`
  → 长轴为 **Y**，电机本体在 +Y、轴伸在 −Y；故位移由 `[-90,-35,60]` 改为 **`[0,80,0]`**（`dx=dz=0`）。
  改位后相机重新 fit（`distance 1189.16 → 1264.35`）、裁切 `(753,1009)-(2962,2332)`、投影定标
  `2.5906 → 2.4371 px/mm`，并整链重跑 `.sc` / 4K 渲染 / 白底 / 标注 / 审计表（V2 报告 4.7 节）。
  注意 MCP 对同路径有缓存，需复制到新路径强制重载才能读到新位移。
- **11 个引线圆点已分色核实**：用户要求「核实圆点与部件是否正确对应」并指出「5 限位开关的标识没有指向限位开关上」。
  做法是把 127 条 moves 烘焙进 occurrence 变换（平移在**第 3 行**）、给 11 组各赋纯色、用同一相机渲染，
  再按色度分类读回每个圆点下的颜色。查出 4 个错点（序号 2/3 互换、序号 5 落在红色机架上、
  序号 10 落在背景），用 `ANCHOR_OVERRIDES` 覆盖；序号 5 改指下方 KW11-3Z-A-1 本体 `(1720,974)`。
  审计表新增 `锚点来源` 列；`python refs/scripts/verify_exploded_anchors.py` 实跑
  **PASS: 11/11（4 处分色覆盖 + 7 处投影）**，最小序号牌间距 57.0 px、无需再推开徽标（V2 报告 4.8 节）。
- **读回验证**：`open errors=0`、`explode.list` 425/127 moves、Z 电机 6 个 occurrence 全 `[0,80,0]`、
  `motion.list` study 424/100 steps、三 slider `value 0.0` + 11.25 deg/mm link、21 材质 ——
  几何 / 材质 / study 与 `motion.sc` 完全一致（`explode.show` 只改显示）。

主交付 `solidcraft/CrossSlide_exploded_v2_annotated.png`（**2209×1713 / 726769 B / `18ed3aba…`**），
另有纯白无标注版 `CrossSlide_exploded_v2_white.png`（495295 B）、深灰底源图 `CrossSlide_exploded_v2.png`（466129 B）、
11 组标注审计表 `EXPLODED_ANNOTATIONS_V2.csv`（含 `锚点来源`）、
复核脚本 `refs/scripts/verify_exploded_anchors.py` 与分色渲染 `refs/tmp/exploded_v2_group_colours.png`。
口径限制同 8.1：127 条 `moves` 绑定 occurrence id、锚点绑定等轴测相机；
**重跑迁移 / LM6UU 改造 / 再改任一组位移后，必须重生成 V2 脚本与标注，并重跑圆点核实**，
否则 4 个分色覆盖坐标会立刻失效。

### 8.3 LM6UU / Ø6 导杆局部重设计（2026-11-13）

> **状态提示（2026-11-13 晚）**：本节记录的 `LM6UU_Native.sc` 是**被用户否定的 v1 历史版本**，仅保留作参数化方法记录；当前正在按用户给出的 2040 横截面图重做，型材阶段权威见 **§8.4**。

用户最初口径：「不是重新设计整个项目，是因为直线轴承的更改，滑台两端的结构件要重新设计，
铝型材不变，滑车也要重新修改参数」。用户先确认选型 **LM6UU（Ø6/Ø12/长19）+ Ø6 导杆**，
原磁盘主模型是 LM5UU Ø10×15 + Ø5。随后明确加码要求：

> 「**我要求你全部在solidcraft重新参数化设计，目的是为了修改设计时都能编辑**」

界面选择「**语义化参数化**」+「**也改成原生参数化**」→ **v1 历史口径**：

```
8 件结构件 + 2 根 2040 铝型材 = 全部 SolidCraft 原生特征重建
零 STEP 导入；所有关键尺寸 / 坐标 / 冻结项都是命名参数，改参数即重算
端板按设计意图语义化重建，保留外形 bbox 与全部安装 / 冻结接口；
装饰性镂空允许差异，体积允许几个百分点差别
```

完整报告 `refs/SOLIDCRAFT_LM6UU_REDESIGN.md`（§1–§10 混合方案为历史，§11 起为当前权威）。

| 交付（当前权威） | 内容 |
|---|---|
| `solidcraft/LM6UU_Native.sc` | **878047 B**；18 body / **104 参数** / 114 时间线特征 / `error 0` / `open_bodies_skipped 0` / **零 `file.insert_step`** |
| `solidcraft/07_lm6_native.json` | **224 条命令，全部成功**：104 `parameters.add` + 36 `solid.box` + 74 `solid.cylinder` + 4 `solid.fillet` + 5 `appearance.assign` + 1 `file.save` |
| `solidcraft/LM6UU_NATIVE_PARAMS.csv` | 104 行参数表（分组 / 表达式 / 说明 / 核心标记），生成方式全为 `SolidCraft 原生 parameters.add` |
| `solidcraft/08_lm6_native_verify.json` | 只读复核：两冻结项实测 + 全配对干涉 + 参数清单 |
| `solidcraft/09/10/11_lm6_native_*.json` | 只读参数联动测试 A / B 与外观读回 |
| `solidcraft/LM6UU_Native_iso.png` / `_seat_detail.png` | 整机白底等轴测图（1264×1302）/ 滑车半透明 + LM6UU 橙色高亮近景图（1800×1200） |
| `refs/scripts/build_lm6_native.py` | 可复现生成器：参数表 + 特征树 + 全部输出脚本 |

> **在 SolidCraft GUI 里查看本设计**：CLI 是离屏生成的，`.sc` 只落在 `C\ink\solidcraft\`，
> 而 SolidCraft 的用户设计目录是 `D:\mydocuments\SolidCraft`（MCP 路径白名单也只允许这里）。
> 因此交付时已同步一份到 `D:\mydocuments\SolidCraft\LM6UU_Native.sc`（sha256 一致）。
> 在 GUI 里 **File → Open** 选该文件，再执行 **View → Fit** —— 本设计 bbox
> `[0,-79,12]..[300,21,262]` 远离原点，不 fit 会看不到模型。

**验证结论（全绿）**：`eval` 18 body / 104 params / 114 timeline / error 0；
`inspect.measure` 冻结 **Z 槽 22.000 mm**、**X 口袋 20.800 mm**；
`inspect.interference` **count 0 / checked 18 / pairs_not_checked 0 / budget_exceeded false**；
`parameters.list` **104 / cycles 0 / errors 0**；`appearance.list` **18/18 body** 有颜色 + PBR。

**参数可编辑性实测**（这是本次重做的目的，混合方案做不到）：

| 改动 | 实测结果 |
|---|---|
| `SEAT_R 6.05 → 6.35` | `X_Carriage_Lower V 13569.202 → 13344.825 mm³`，`recomputed 73 / errors []`；端板 / 导杆 / 轴承不变 |
| `X_CAR_Z0 112 → 114 mm` | 滑车 bbox minZ `112 → 114`，`recomputed 76 / errors []` |
| `Z_SLOT_W 22 → 24 mm` | `Z_EndPlate_L V 35532.048 → 35225.097`，实测槽宽 **24.0 mm**，`recomputed 86 / errors []` |

- **接口保真**：主座 `R6.05 × 19.20`（`BRG_OD/2+0.05` / `BRG_L+0.2`），两端 `R4.70 / R5.10`
  仍为**双向轴向挡肩**；导杆孔 `ROD_HOLE_R = ROD_D/2+0.05 = R3.05`（Ø6.10）现在是
  SolidCraft 内的**原生 cut 特征**、随参数联动；M3 上下两半合拢孔位不变；
  铝型材 2040 接口尺寸不变，改为原生 box + `PROF_CORE_D = 6 mm` 参数化中心通孔。
- **三个 OCC 坑及修复**：① step 164 `cavity ownership is ambiguous` —— M3 沉孔刀具底面与
  本体外表面共面产生第 2 个内部壳；改为「先两通孔、再两外延沉孔（起刀越过外表面 `CUT_EXT`）」；
  ② step 193 `boolean Cut: no result` —— 皮带让位腔与 M3 沉孔重叠，`CAR_BELT_W 8 → 5 mm`；
  ③ 复核 `solid.fillet` 边索引，`(0,2,8,11)` 才是沿厚度 Y 的四角 R4（`(4,6,7,9)` 会圆到长边）。
  另修正 Z 上滑车厚度 `15 mm`、把参数联动测试拆成两个只读脚本避免重算超时。
- **历史中间方案（仅作对照，勿当最终交付）**：`solidcraft/LM6UU_Redesign.sc`（564301 B）是
  **混合式**：8 件结构件主体为 STEP 导入哑实体、16 个参数中仅 10 个驱动几何、端板 8 处孔在
  FreeCAD 侧预切且不联动。相关文件 `06_lm6_redesign.json`、`LM6UU_PARAMS.csv`、
  `LM6UU_Redesign_iso.png` / `_seat_detail.png` 与报告 §1–§10 一并保留。
  自动盒分解 1:1 复刻路线也已否决（端板需 95~110 个碎盒、体积误差 +11%~+23%）。
- **不动的东西**：主 `CrossSlide_P014013.FCStd`（仍是 v13.2 几何 + v14 材质，LM5UU）、
  `motion.sc`、V2 爆炸图、动画、图纸、21 种材质。本设计只从 FCStd 读取接口数据。
  **语义化 ≠ 几何 1:1**：严格制造几何仍以主 FCStd 为准。
  若将来要合并回主设计，零件名 / occurrence id 会变，必须按 8.2 末尾的顺序重跑整条链。

### 8.4 按用户横截面图重做：真实 2040 型材精确截面（2026-11-13，当前型材阶段权威）

用户否定 v1 外观：

> 「solidcraft设计效果很差，完全不像正常的产品设计，比freecad差多了，你看看哪里出了大问题。」

复核确认 v1 的「全绿」是**假绿**：只验了冻结尺寸、零干涉、参数联动，未验逐件几何保真度。8 件结构件 256 面 vs 原始 931 面（约 27%）；两根型材体积 **+107%**、填充率 78% vs 真实 37.9%，实际是实心方棒 + 4 直槽；整机也只有 18 body / 5 色组。用户选择「重做原生几何」，并要求「你拉出型材后先让我在 solidcraft 里看看」。4 槽阶段预览 `LM6UU_Profile_Preview.sc`（V +25.1%）被用户给的 2040 横截面图否定，本节是**精确型材阶段**；端板 / 滑车 v2 尚未开始。

#### 轮廓修正

当前模型不能直接接收图像，线稿 flood-fill 也不闭合，故以主 FCStd 裸 BREP 端面为权威。旧轮廓提取把两个 **Ø5 圆孔**误写成零面积缝隙，少算 `39.2699 mm²`；重写 `refs/scripts/extract_profile_contours.py` 用 `Wire.OrderedEdges/OrderedVertexes` 输出：

```text
外轮廓  286 Line + 4 个 R1.5 圆弧   491.272842 mm²
圆孔    Circle Ø5 ×2                39.269908 mm²
中心腔  52 Line                     149.195000 mm²
净截面积                           302.807934 mm²（BREP 302.807933，delta 1e-6）
```

#### 交付与验证

| 文件 | 内容 |
|---|---|
| `solidcraft/LM6UU_Profile_Exact.sc` | **当前型材阶段权威**：2 body / 346 面每件 / 单一闭合壳 / 零 STEP |
| `solidcraft/13_profile_exact.json` | 43 条全原生命令；`--param-check strict` 43/43 成功 |
| `solidcraft/LM6UU_PROFILE_EXACT_PARAMS.csv` | 11 行用户参数；长度与 Ø5 孔半径驱动特征 |
| `refs/scripts/build_profile_exact.py` | 生成器 + `--verify` 25 项几何保真度检查 |
| `solidcraft/LM6UU_Profile_Exact_section.png` | BREP 原始 vs SolidCraft 1:1 复刻截面对比 |
| `solidcraft/LM6UU_Profile_Exact_iso_white.png` / `_GUI_fit_white.png` | 白底等轴测 / GUI model 渲染白底 |

```text
X_Profile V 60563.053507 mm³  目标 60561.586684  +0.0024%
Z_Profile V 45421.783053 mm³  目标 45421.190013  +0.0013%
两件 faces 346 / plane 340 + cylinder 6 / shells 1 / closed true
sketch 2 × (curves 344 / profiles 4 / solved)
timeline 4 features / errors 0 / warnings 0
verify 25 checks PASS / failed 0
```

面数与原始 BREP **完全一致**；`refs/tmp/profile_exact_verify.json` 明确检查了命令错误、草图求解、bbox、闭合壳、面数 / 面类型、体积误差、截面积、源与 GUI 副本 sha256，避免再次出现「假绿」。

#### 在 SolidCraft GUI 里查看

已复制到 `D:\mydocuments\SolidCraft\LM6UU_Profile_Exact.sc`（源/目标 sha256 `b9cd2078…a9`），并通过 GUI MCP 执行：

```text
mcp__solidcraft__open            → errors 0 / features 4
mcp__solidcraft__execute view.fit → expect ok=true，bodies 2 / volume 105984.836560
mcp__solidcraft__execute parameters.list → 17 项，cycles [] / error null
mcp__solidcraft__screenshot source:"model", view:"fit" → GUI fit 渲染
```

`source:"window"` 截图若报 `window hidden / no frame was presented`，说明 SolidCraft 窗口被最小化；自动置前被 PowerShell 安全策略拦截，不再重试。请手动点任务栏 SolidCraft 窗口，然后 **View → Fit**；也可直接看交付的白底 model 渲染。

### 8.5 用 SolidCraft 官方 skill 建立 X-Z 十字滑台（2026-11-16，当前阶段成果）

用户要求：「利用这些 skill，在 SolidCraft 把鹅蛋喷码机的十字滑台先建立起来，4020 铝型材已经在项目里建立了。」

本次按官方 skill 的分工执行：

- `solidcraft-modeling`：工作前读 `skill_reference`，先写参数/坐标/预期体积，再分批建模、逐步 `measure`；
- `solidcraft-editing`：基于已建立的真实截面型材设计扩展，不重复导入 STEP；
- `solidcraft-checking`：每次参数走查 / 干涉 / timeline health / 逐件几何核对；
- `solidcraft-mechanisms`：把静态 body 分入 `X_Base` / `X_Stage` / `Z_Stage`，加两个 slider 与 motion study；
- `solidcraft-sheetmetal` 本次不涉及钣金，未使用。

#### 建模结果

`solidcraft/CrossSlide_XZ.sc` 是静态主体，`solidcraft/CrossSlide_XZ_mech.sc` 是在其上加机构的可运动版本。两版均 **18 body / 100 用户参数 / 零 STEP**：

| 分组 | 内容 |
|---|---|
| 已建立型材 | `X_Profile` / `Z_Profile` 直接沿用 §8.4 的真实 BREP 1:1 截面，各 346 面、单一闭合壳 |
| 结构件 | `X_EndPlate_L/R`、`Z_EndPlate_L/R`、4 件上下滑车；全部 SolidCraft 原生 box / cylinder / fillet |
| 传动件 | 4 × Ø6 导杆、4 × LM6UU（Ø12/Ø6×19）轴承，主座 `R6.05×19.20`、端板导杆孔 `Ø6.10` |
| 冻结项 | Z 限位槽 `22.00`、X 限位口袋 `20.80` 均由命名参数驱动 |
| 机构 | `X_Travel` slider `[-80,+80] mm`、`Z_Travel` slider `[-55,+55] mm`、`CrossSlide_Cycle` 10 步 study |

主构建脚本 `14_cross_slide_xz.json` 共 **238 条命令**（100 `parameters.add` + 精确型材草图/拉伸 + 26 `solid.box` + 72 `solid.cylinder` + 4 `solid.fillet` + 5 外观 + 1 保存），`--param-check strict` 全部成功。机构脚本 `16_cross_slide_mechanism.json` 12 条命令，component / joint / study 均无 conflicts、无 errors、无 floating。

#### 验证结果（`refs/tmp/cross_slide_xz_verify_summary.json`）

```text
CONCLUSION PASS / failed 0
body_count 18                         所有 body closed=true
timeline 106 features / errors 0      10 条 Boolean retry 警告，位移 1.22~1.24e-4 mm、转角 2e-6 rad，体积与解析值一致
Z 限位槽 22.000 mm                    X 限位口袋 20.800 mm
干涉 count 0 / checked 18 / pairs_not_checked 0 / budget_exceeded false
参数 cycles [] / errors []            用户参数 100
SEAT_R 6.05→6.35                      X_Carriage_Lower V 13569.202→13344.825 mm³
Z_SLOT_W 22→24                        实测槽宽 24.0；Z_EndPlate_L V 35532.048→35225.097 mm³
joint conflicts [] / floating []      X=+20 驱动使 X_Stage +20X；Z=+15 使 Z_Stage 再 +15Z
```

需要明确：型材是 1:1 保真；**端板 / 滑车本阶段是语义化参数化重建，不是逐面复刻**。原始 8 件结构件合计 931 面，本版仍只有 256 面；端板体积相对原始偏差约 `-3% ~ -26%`，滑车偏差约 `+1.6% ~ +2.3%`。这些偏差已写入验证报告的 `structural_volume_deviation_informational`，下一阶段若要继续提高外观保真度，应逐件按原始 BREP 曲线重建端板筋 / 镂空 / 阶梯台，而不是把当前版本误称为 1:1 复刻。

#### 打开与出图

已同步到 GUI 用户目录：

```text
D:\mydocuments\SolidCraft\CrossSlide_XZ.sc
D:\mydocuments\SolidCraft\CrossSlide_XZ_mech.sc
D:\mydocuments\SolidCraft\CROSS_SLIDE_XZ_PARAMS.csv
D:\mydocuments\SolidCraft\CrossSlide_XZ_iso_white.png
D:\mydocuments\SolidCraft\CrossSlide_XZ_top_white.png
D:\mydocuments\SolidCraft\CrossSlide_XZ_headless_fit.png
```

Git Bash / PowerShell 均可解析 `solidcraft-cli 0.30.1`；`commands` 返回 570。Headless MCP 已成功打开 `CrossSlide_XZ_mech.sc`：`errors 0 / features 124`，joint.list 回读两个 slider 均 `resolves true / conflicts [] / errors []`。本次 GUI MCP `open` 又返回 `the agent chat has no message in progress`，因此不再反复重试；请在任务栏点开 SolidCraft 窗口后 **File → Open** 选 `CrossSlide_XZ_mech.sc`，再 **View → Fit**。也可直接查看交付的白底等轴测 / 俯视图与 headless fit 渲染。

> 注意：§8.5 保留为阶段历史。用户随后明确纠正「不是十字滑台，先做单独 X 轴滑台」，当前目标见 §8.6。

### 8.6 单独 X 轴滑台原生重设计（当前目标，2026-11-16）

用户明确要求先做 **单独 X 轴滑台**，而不是十字滑台：2040/4020 真实截面铝型材、直接 Ø6 导杆、LM6UU、型材端面 3D 打印结构、GT2 同步带/同步轮、42 步进电机，并参考已打开的 `CrossSlide_P014013` 在 SolidCraft 中原生重设计。

当前权威文件是 `solidcraft/X_Axis_Slide.sc`，详见 `refs/SOLIDCRAFT_X_AXIS_REDESIGN.md`。构建脚本 `refs/scripts/build_x_axis_slide.py` 从真实截面型材配方只取 X 型材部分，其余全部 SolidCraft 原生命令生成：

```text
20 body / 118 用户参数 / 零 STEP
全部 body closed=true / 每个 body 单一闭合壳
timeline errors 0 / warnings 0
interference count 0 / checked 20 / pairs_not_checked 0 / budget_exceeded false / unchecked 0
X 限位口袋 20.80000000000001 mm
X_Profile faces 346 / V 60563.054 mm³（真实 BREP 1:1 截面）
X_EndPlate_L V 12462.89 faces 55 fill 13.1%（原件 V 19158.4 / 192 面 / 20.1%）
X_EndPlate_R V 27666.93 faces 66 fill 30.1%（原件 V 20565.7 / 191 面 / 22.4%）
X_LimitSwitch_L/R V 1334.94，X_LimitScrew_* V 175.21
```

相比 FreeCAD 参考，导杆升级为 Ø6，轴承升级为 LM6UU Ø12/Ø6×19；主座 `R6.05×19.20`，端板导杆孔 Ø6.10，惰轮轴/孔按参考模型 Ø9.5/Ø9.6。

端板样式已按原件回归：不再用实心方框，而是「整片法兰 + 上下横梁/前后竖柱前框 + 贯穿减重窗 + 开关耳」；右端为「法兰 + 惰轮侧板 + R20 圆弧外缘 + 贯穿窗口」。42 电机、Ø6 导杆、Ø16 同步轮、Ø9.6 惰轮轴均按装配关系做贯穿/让位。

左右限位开关按参考位置新增：`X_LimitSwitch_L/R` 为 KW11-3Z-A-1（12.2×6.5×19.8），配 4 颗 `X_LimitScrew_*`，装于端板开关耳，孔距 9.5、Z 126.5/136。

已同步到 GUI 用户目录：

```text
D:\mydocuments\SolidCraft\X_Axis_Slide.sc
D:\mydocuments\SolidCraft\X_AXIS_SLIDE_PARAMS.csv
D:\mydocuments\SolidCraft\X_Axis_Slide_iso_white.png
D:\mydocuments\SolidCraft\X_Axis_Slide_top_white.png
```

源与 GUI 副本 sha256 `638624deecb11f5942885b7be4d15c47cb384bc520e56e269dda29fe116e7a60` 一致。**已在 SolidCraft 窗口中直接打开并 View Fit**（`errors 0 / features 116`）。此前 MCP 报 `os error 10060` 的原因是 `current.port` 指向 27878，而工具默认连 49187；改用当前端口后打开正常。

边界：型材 1:1；端板已按原件薄壁框架语言重建（填充率 13.1%/30.1%，原件 20.1%/22.4%），但仍不是逐面复刻。本版为单独 X 轴静态滑台，尚未加 slider / motion study；washer、nut、rod tap、fix screw、clamp key 尚未纳入 20 body。

### 8.7 端板分层参数化复刻（2026-11-17）

用户要求把 X 轴两端 3D 打印端板逐面复刻，并选择「分层参数化（可编辑）」路线，按「接受当前结果」交付。详见 `refs/ENDPLATE_EXACT_REPLICATION.md`。

精度（实测）：

```text
X_EndPlate_L  19290.36 mm³  vs 原件 19158.443  →  +0.689%
X_EndPlate_R  20063.00 mm³  vs 原件 20565.709  →  -2.444%
64 个分层 body 全部 closed / 单一闭合壳；timeline errors 0 / warnings 0
包围盒与原件完全一致
```

分层：L 13 层 / 34 外环体，R 14 层 / 30 外环体，自适应合并（相邻层面积差 ≤3% 且合计厚 ≤8 mm 合并）。

核心脚本 `refs/scripts/write_endplate_dxf.py`：用薄片 `common` 的 -Y 面取截面（`slice()` 在薄壁/圆弧外缘会重复、漏环甚至返回 0 环），`dedupe_loops` 去重，`pick_loops` 用 `isInside` 判孔归属，每个外环写独立 DXF。

R 端板剩余 -2.44% 的成因是拓扑变化：`-50..-38` 的 12 mm 厚层低截面被两道横梁分成 3 段（65.61 / 131.22 / 65.91），高截面合并成 1 段（307.22）。要收敛到 1% 需逐段放样再合并。

### 8.8 X 轴滑台完整总装（2026-11-17）

把 2040 型材、Ø6 导杆、LM6UU、滑车、GT2 同步带/轮、42 电机、左右限位开关与复刻端板装成一体：

```text
solidcraft/X_Axis_Assembly.sc   84 body / 236 features / 零 STEP
timeline errors 0 / warnings 0 / 全部 body closed
干涉 5 处共 12.4 mm³（导杆 3.09 + 型材 9.23，均为分层台阶残差，亚毫米级）
```

装配要点：

- 基座沿用真实截面 2040 型材（346 面，V 60563.05），端板为 §8.7 的分层复刻体（64 个外环体）
- 复刻端板按装配关系补挖：限位开关口袋 ×2、Ø9.6 惰轮轴孔 ×2、4 个电机 M3 固定孔 ×2 层
- **端板电机固定孔为 4 个**：原件实测 `X5.5/36.5 × Z121.5/152.5`、`r1.7`（Ø3.4）、孔距 31 mm、Y-62..-57；BL08 层切孔后圆柱面 3→7（+4），已定量确认
- 电机机身 Y 起点由 -59 修正为 -57：原件安装面在 Y=-57，仅 Ø22 定位凸台插入端板；原值会让机身侵入端板 2 mm，造成 2464 mm³ 干涉

干涉收敛过程：2464（电机）→ 2294 → 12.4 mm³。
