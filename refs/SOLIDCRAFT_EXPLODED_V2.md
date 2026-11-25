# SolidCraft 升级版爆炸图报告（V2：更细爆炸 + 白底 + 中文标注 + 装配顺序线）

生成时间：2026-11-12（2026-11-12 晚追加两处修正，见 4.7 / 4.8 节）
用户指令（三条合并成一张图）：

1. 「爆炸图上用中文标明部件的名称，用线条标明空间装配的顺序和逻辑」
2. 「爆炸图背景改为白色」
3. 「爆炸图还能再多炸开一些零部件吗？」

后续追加修正（同样落到**同一张图**，不另出版本）：

4. 「核实圆点与部件是否正确对应」→ 11 个引线圆点全部经**分色渲染逐点核实**，4 处错点修正（4.8 节）。
5. 「5 限位开关的标识没有指向限位开关上，修改它」→ 序号 5 圆点移到下方 KW11-3Z-A-1 本体。
6. 「爆炸图的 Z 轴电机位置不对，它应该就在 Z 轴电机安装位沿安装螺钉的方向平移出来」→ Z 步进电机位移改为纯 `+Y`（4.7 节）。

**主交付（以下大小 / 哈希均为追加修正后的最终态）**

- `solidcraft/CrossSlide_exploded_v2_annotated.png` —— **最终图**：白底 + 11 组中文名称 + 引线 + 装配顺序线，2209×1713 / 726769 B / sha256 `18ed3aba…`
- `solidcraft/CrossSlide_exploded_v2_white.png` —— 纯白底无标注版，2209×1323 / 495295 B / sha256 `aa93bc1e…`
- `solidcraft/CrossSlide_P014013_exploded_v2.sc` —— 可编辑设计，view 425 / **127 条 moves**，1815034 B / sha256 `87cf1163…`

**基线**：`solidcraft/CrossSlide_P014013_motion.sc`（v14 材质 + 运动链 + study 424）。
V1 报告见 `refs/SOLIDCRAFT_EXPLODED.md`；几何来源见 `refs/SOLIDCRAFT_MIGRATION.md`。

---

## 1. 结论速览

| 项目 | V1 | **V2（本版）** |
|---|---|---|
| 移动 occurrence | 100 | **127** |
| 固定基准 occurrence | 40（挤在一起） | **12**（真正不动的机架） |
| 功能组 | 6 组 + 1 基准组 | **10 组 + 1 基准组 + 1 隐藏辅助** |
| 背景 | 深灰 `[46,52,64]` | **纯白 `[255,255,255]`** |
| 中文部件标注 | 无 | **11 组中文名称 + 序号徽标 + 引线** |
| 装配顺序线 | 无 | **粗虚线箭头主链 1→10 + 绿色并行支路 1→11** |
| 标签布局 | — | 11 框与模型重叠 ≈0（最大 0.01%），最小序号牌间距 **57.0 px** |
| Z 步进电机抽出方向 | `[-90,-35,60]` 斜向飞出（错） | **`[0,80,0]` 沿安装螺钉轴线纯 +Y 抽出 80 mm**（4.7 节） |
| 引线圆点与部件对应 | 仅按 3D 质心投影估算，未核实 | **11/11 分色像素核实 PASS**，4 处投影错点已覆盖修正（4.8 节） |
| 投影定标比例 | `2.5906 px/mm` | **`2.4371 px/mm`**（Z 电机改位后相机重 fit，自动重新定标） |
| 派生设计 | view 425 / 100 moves | view **425** / `整机爆炸图 V2` / **127 moves** |
| 几何 / 材质 / study | 与 motion.sc 一致 | **仍完全一致**（`explode.show` 只改显示） |

> 三条需求刻意合并到**同一张图**：如果分别出「白底」「中文」「更多爆炸」三张，彼此会互相矛盾，交付也难引用。
> 后面三条修正同理：全部覆盖回同一组 PNG / `.sc` / CSV，不保留旧版本，避免引用歧义。

---

## 2. 需求一：把更多零件炸开

### 2.1 V1 的问题

V1 把 **40 件 Z 轴零件**全部塞进「Z 轴骨架（基准，不动）」，导致底板、上下端板、两根导杆、
GT2 同步带 / 同步轮、NEMA17 电机、限位开关、限位螺钉**从头到尾没有被拆开**，读图时仍是一坨。

### 2.2 V2 拆法

`refs/scripts/build_exploded_view_v2.py` 把这 40 件拆成 **5 个 Z 轴功能子组**，只保留 **12 件**
真正不动的机架（`Z_BaseBlock` + `Z_Profile` + 2 个 `Z_rod_*_tap` + 4 × `Z_BaseScrew` + 4 × `Bench_Screw`），
并同步**加大 V1 六组的位移**（如 HP45 喷头 `[-25,-235,0] → [-50,-350,0]`、探针 `[-115,-235,0] → [-185,-350,0]`）。

| 功能组 | 件数 | `translate [dx,dy,dz]` mm | 来源 |
|---|---:|---|---|
| Z 端板与导杆 | 8 | `[70,-25,30]` | **V2 新增** |
| Z 同步带传动 | 7 | `[120,-75,65]` | **V2 新增** |
| Z 步进电机 | 6 | `[0,80,0]` ★ | 沿安装螺钉轴线 +Y 抽出（4.7 节修正） |
| Z 限位开关 | 6 | `[175,-170,25]` | **V2 新增** |
| Z 轴机架（固定基准） | **12** | `[0,0,0]` | 从 V1 的 40 件缩到真正基准 |
| Z 滑车 + XZ 连接板 | 23 | `[0,-80,95]` | V1 加大（`[0,-40,50]`） |
| X 横梁总成 | 30 | `[0,-150,0]` | V1 加大（`[0,-85,0]`） |
| X 滑车 | 10 | `[0,-230,0]` | V1 加大（`[0,-150,0]`） |
| HP45 喷头总成 | 18 | `[-50,-350,0]` | V1 加大（`[-25,-235,0]`） |
| 接触式探针总成 | 13 | `[-185,-350,0]` | V1 加大（`[-115,-235,0]`） |
| 保湿站 | 6 | `[155,-75,0]` | V1 加大（`[95,-55,0]`） |
| 隐藏辅助几何（不显示） | 1 | `[0,0,0]` | `Part__Feature` |
| **合计** | **140** | | **127 移动 + 12 基准 + 1 隐藏** |

Z 轴附件沿 ±X / +Z 扇出，不再压在机架轮廓里；主装配链沿 −Y 依次拉开。

★ **唯一例外是 Z 步进电机**：它不参与扇出，必须沿安装螺钉轴线从安装位**直抽**出来，
因此 `dx=dz=0`、只有 `dy=+80`。详见 4.7 节——这是用户后续反馈纠正的，不是最初 V2 分组的取值。

### 2.3 硬校验（防漏件 / 防重复）

```python
unknown = members - all_names            # 名字必须存在于 sc_occ_map.json
if unknown: raise SystemExit(...)
if n in seen: raise SystemExit(...)      # 不能同时属于两组
unexpected = [n for n in ground if n != "Part__Feature"]
assert len(seen) + len(FRAME) + len(ground) == len(all_names)   # 140 全覆盖
```

`ground` 除隐藏辅助几何外必须为空 —— 这是 V1 没有的约束，逼着把 40 件基准全部归类。

### 2.4 派生与读回

从 `motion.sc` 派生（同 V1 通道，仅脚本改为 `05_exploded_view_v2.json`）：

```bash
"/d/Program Files/SolidCraft/solidcraft-cli.exe" run \
  "D:/ink/solidcraft/05_exploded_view_v2.json" \
  --in  "D:/mydocuments/SolidCraft/CrossSlide_P014013_motion.sc" \
  --save "D:/mydocuments/SolidCraft/CrossSlide_P014013_exploded_v2.sc" \
  --results --json-out "D:/ink/refs/tmp/sc_explode_v2_results.json" \
  --param-check warn
```

`.sc` 拷回项目后，**ZIP 直读 + MCP 权威读回双重验证全绿**：

| 检查 | 结果 |
|---|---|
| `open` | `errors: 0` |
| `explode.list` | view **425** `整机爆炸图 V2 / Assembly exploded V2`，**127 moves** |
| `.sc` `/assembly/exploded[0]` | `id 425` + name + 127 组 `[occ, translate]` |
| `motion.list` | study **424** `打码工作循环 / Coding cycle`，100 steps，3 keys |
| `joint.inspect 303 / 338 / 411` | 三个 slider 全部 `value 0.0`，`conflicts=[]`，`resolves=true`；303/338 的 11.25 deg/mm `motion_link` 完好 |
| `.sc` `/assembly/joints` | 140 = `rigid 131` + `revolute 6` + `slider 3` |
| `material.list` | **21** 个 `user:true` 材质，144/144 body 赋值 |
| `explode.show {view:425}` | 正常显示（刚打开的设计里也能 show） |
| Z 步进电机 6 个 occurrence（`62/64/66/68/70/72`） | 位移全部 `[0.0, 80.0, 0.0]`，无斜向分量 |
| `render.camera.fit` | Z 电机改位后重新取景：`distance 1264.35`、`target [139.8, -201.13, 155.0]`、`document_changed:false` |

> `document.json` 里关节类型字段是 `kind`（不是 `type`），滑块值是 `values[0].value`；
> 不要按 V1 报告里「曾踩过的坑」凭猜字段解析，直接走 MCP 命令最稳。
>
> **MCP 陈旧缓存坑**：重建 `.sc` 后用同一路径 `open` 仍读回旧的 `[-90,-35,60]`。
> 必须把修正后的设计复制到一个**全新路径**
> （`D:/mydocuments/SolidCraft/CrossSlide_P014013_exploded_v2_fixed.sc`）强制重载，
> 读回才显示 `[0,80,0]` 与新相机参数。项目内正式交付路径仍是
> `solidcraft/CrossSlide_P014013_exploded_v2.sc`（与 fixed 副本字节一致）。

---

## 3. 需求二：背景改为白色

### 3.1 探测结论：没有 viewport 白色背景命令

`list_commands {filter:"background"}` 只找到 `render.stage.backdrop`（物理渲染布景），
不是简单的 viewport 纯色背景开关。CLI 与 MCP 两条渲染通道对比：

| 通道 | 背景 | 结论 |
|---|---|---|
| `solidcraft-cli snapshot --view iso --no-grid --no-axes` | 浅灰渐变 `[240,243,247]` + 地平线，底部模型被裁 | **弃用**：渐变底无法干净转纯白 |
| MCP `screenshot {source:"model", grid:false, axes:false}` | **纯色** `[46,52,64]`（四角一致，占 77.4%） | **采用**：纯色底可精确替换 |

### 3.2 白底后处理（`annotate_exploded_view.py` 的 `to_white()`）

深灰底是纯色，直接把精确背景像素换成白；抗锯齿边缘用 alpha 近似还原：
抗锯齿像素 `c = a·fg + (1−a)·BG` 合成到白底应为 `c + (255−BG)·(1−a)`，
用 `MaxFilter(3/5)` 构造边缘权重 `w`（近背景 1.0 / 一圈 0.62 / 两圈 0.24）：

```python
near = np.max(np.abs(c - BG), axis=2) <= 3
ni = Image.fromarray((near * 255).astype(np.uint8))
d1 = np.array(ni.filter(ImageFilter.MaxFilter(3))) > 0
d2 = np.array(ni.filter(ImageFilter.MaxFilter(5))) > 0
w  = np.where(near, 1.0, np.where(d1, 0.62, np.where(d2, 0.24, 0.0)))
out = np.clip(c + (255.0 - BG)[None,None,:] * w[...,None], 0, 255)
```

验证：`CrossSlide_exploded_v2_white.png` 四角全 `[255,255,255]`、`exact_white 83.45%`、
`near-white(>245) 83.60%`；标注成品 `exact_white 83.53%`。
（Z 电机改为纯 +Y 抽出后模型包围盒变高变窄，重新取景使白色占比由初版 81.51% 升到 83.45%。）

### 3.3 高分辨率渲染与取景

MCP 初版 1200×900 模型只占 3.4%。先 `render.camera.fit {aspect:1.3}`（返回
`distance 1189.16 / yaw −45° / pitch 35.264° / up z`，`document_changed:false`，无需保存设计），
再 4096×3150 截图，最后按模型 bbox 加留白裁切。

> **Z 电机改位后必须重新 fit**：`[0,80,0]` 让模型沿 +Y 拉长，MCP 重新取景返回
> `distance 1264.35 / target [139.8, -201.13, 155.0]`，模型 bbox 变为
> `(893,1099)-(2822,2242)`（1930×1144）。因此裁切参数、投影定标比例、锚点全部重算过。

```
最终裁切 crop (753,1009)-(2962,2332)，左右各留 140 px、上下各留 90 px
    → CrossSlide_exploded_v2.png = 2209×1323 / 466129 B / sha256 83dd9035…
```

初版（Z 电机斜向飞出时）的 `bbox (906,1019)-(2933,2234)` / `crop (815,965)-(3024,2288)` /
`scale 2.5906 px/mm` **已作废**，不要再用旧坐标点选或核对。

> 本会话 `ViewImage` 仍不可用（`the selected model cannot receive images`）；
> 构图与色彩判断一律用 PIL + numpy 统计背景色、非白像素占比、bbox、颜色数、ASCII 布局、连通域。
> `screenshot` 返回 `[image omitted: model does not support image input]` 是正常现象，PNG 已按 `path` 落盘。

---

## 4. 需求三：中文名称 + 装配顺序与逻辑线

### 4.1 锚点不是手工点选，是等轴测投影自动定标

`refs/materials/geometry_snapshot_v14.json` 给出逐件 3D 包围盒，
`EXPLODED_GROUPS_V2.csv` 给出每件的爆炸位移 `t`。对每组取所有零件 bbox 角点 + 位移，
用正交 Z-up 等轴测相机（yaw −45° / pitch 35.264°）投影：

```
u = 0.8660254·(X + Y)        # 屏幕右
v = 0.5·(X − Y) − Z          # 屏幕下
```

把全部角点的 `(u,v)` 范围线性映射到渲染图实测模型 bbox，得
**`scale = 2.4371 px/mm`**（Z 电机改位 + 相机重 fit 后的最终值；初版 2.5906 已作废），
再算各组 3D 质心 → 像素锚点。
好处是**重出渲染图后脚本自动定标仍然有效**，不依赖人工记坐标。

> 但「投影质心」只是估算：它可能落在两件被炸开零件之间的空隙、被更近的另一组零件挡住，
> 甚至落在纯背景上。**因此 4.8 节又做了一轮独立的分色像素核实**，
> 对 4 个错点做显式覆盖；`EXPLODED_ANNOTATIONS_V2.csv` 的 `锚点来源` 列
> 逐行标明是「等轴测投影」还是「分色像素核实」。

### 4.2 11 组中文标注与装配顺序（`ORDER`）

| 序号 | 功能组 | 装配动作 |
|---:|---|---|
| 1 | Z 轴机架（固定基准） | 装配基准 · 底座与 2040 立柱 |
| 2 | Z 端板与导杆 | 端板与两根 Ø10 导杆装入立柱 |
| 3 | Z 同步带传动 | GT2 轮 / 带 / 张紧件装到端板 |
| 4 | Z 步进电机 | 沿安装螺钉轴线 +Y 抽出 80 mm，NEMA17 与主动轮对接 |
| 5 | Z 限位开关 | 上下各一 KW11-3Z-A-1（圆点核实后指向下方本体） |
| 6 | Z 滑车 + XZ 连接板 | 滑座套 Z 导杆挂带，XZ 板 M5 锁定 |
| 7 | X 横梁总成 | 经 XZ 板固定到 Z 滑车 |
| 8 | X 滑车 | 上下滑座扣合、夹紧 GT2 带 |
| 9 | HP45 喷头总成 | 夹具与转接板装到 X 滑车 |
| 10 | 接触式探针总成 | 侧装于喷头臂（+X 侧装） |
| 11 | 保湿站 | **并行**：独立装于底座 +X 侧 |

图例区分三类线：

- **细实线 + 圆点**：部件中文名称引线（`#93A1B0`）
- **粗虚线箭头**：装配顺序主链 `1→2→…→10`（`#3E5266`）
- **绿色虚线**：并行支路 `1→11`（保湿站，`#059669`）—— 表达「与主链无先后依赖」

### 4.3 标签自动避让

用积分图 `integ` 计算候选框内模型像素占用 `occ(x,y,w,h)`，cost 同时权衡锚点距离、
同水平带、模型占用和标签间避让：

```python
cost = (0.8 * abs(cx - tx) + 1.5 * abs(cy - ty)
        + occ(x, y, LABEL_W, LABEL_H) * 3.0)
```

迭代过程：初版 `mean 346 / max 636`；改「锚点侧方 230px」为「贴近锚点」后仍 636；
根因是 `330×88` 的框在密集区找不到近处空位。缩到 `290×76` + 让 cost 更重视同水平带后：

```
mean dist 296  max 574  mean |dy| 89
11 个 label box 与模型重叠全部 0.00%   min 标签间距 18 px
```

以上是参数整定过程。4.8 节覆盖 4 个锚点后标签位置随之重排，最终态复核：
**11 个标签框与模型重叠 ≈0（最大 0.01%，仅序号 7）**、
**最小序号牌间距 57.0 px**、`displaced_badges = {}`——即锚点修正后
`place_badges()` 不需要再推开任何徽标（算法仍保留为兜底）。

### 4.4 白底上的线条可读性（白色 halo）

深灰底改白后，深灰 / 蓝灰引线压在深色零件上会看不清。给所有线加白色描边 halo：

```python
def dashed(draw, p0, p1, fill, width=3, dash=18, gap=11, halo=3):
    if halo:
        _dashed_raw(draw, p0, p1, "#FFFFFF", width + halo, dash, gap)  # 白底衬
    _dashed_raw(draw, p0, p1, fill, width, dash, gap)

# 细实线引线
d.line(pts, fill="#FFFFFF", width=6)     # halo
d.line(pts, fill="#93A1B0", width=2)
# 箭头
draw.polygon([...], fill=fill, outline="#FFFFFF", width=2)
```

验证：中文为真实抗锯齿字形（标题笔画 148 级灰度、标签 133 级，不是豆腐块）；
**7420 个纯白像素落在原深色模型区域内**（即 halo 生效），最终标注图 `exact_white 83.53%`。

### 4.5 最终画布

`2209 × 1713`（原图 1323 + 顶部标题带 150 + 底部图例带 240）：
顶部标题「X-print 十字滑台总成 · 装配爆炸图 V2」+ 副标题；中部模型 + 11 组标注 + 装配链；
底部图例 + 完整装配逻辑文字 + V2 相对 V1 的说明 + 口径提醒。
四边 `100%` 纯白、无裁切；三个分区（标题 7.69% / 模型 20.19% / 图例 5.88% 非白）都有内容。
底部图例新增一条口径说明：**「11 个引线圆点均经分色渲染逐点核实，4 处按分色像素覆盖修正」**，
让读图人知道圆点不是随便点的估算值。

### 4.6 出图后修正：序号 3 与序号 2 的徽标重叠（用户截图反馈）

用户截图问「这个 3 跟它后面的啥重叠了」。用 PIL 颜色分离（截图里同时出现青 `#0891B2`
与蓝 `#2563EB`）+ 圆心距离核算，定位到：**序号 3「Z 同步带传动」的圆形序号牌把
序号 2「Z 端板与导杆」的牌几乎完全盖住**。

| 项 | 值 |
|---|---|
| 序号 2 锚点（源图） | `(1872, 334)` |
| 序号 3 锚点（源图） | `(1862, 325)` |
| 两圆心距离 | **13.5 px** |
| 徽标直径 | **42 px**（外圆半径 21） |
| 后果 | 按 `ORDER` 顺序后画的 3 盖住先画的 2，只在右下露出一条蓝边 |

根因不是标签布局，而是**两个功能组的 3D 质心经等轴测投影后落在几乎同一点**：
V2 给它们的位移 `[70,-25,30]` / `[120,-75,65]` 在屏幕上没拉开（当时初版定标 2.5906 px/mm）。
4.3 节的避让只管**标签框**（`place_labels`），4.4 节的 halo 只管线条，都没管**徽标之间**的互相遮挡。

**修复（只改标注层，不动 `.sc` / 3D 几何 / 已验证口径）**：

- 新增 `place_badges(anchors_canvas, W, H)`：迭代把任意距离 `< MIN_BADGE_SEP = 52 px`
  的徽标沿连线方向对称推开，直到全部满足 ≥52 px（即两圆间至少 10 px 净空）；越界则 clamp 回画布内。
- 装配顺序链改连**推开的徽标**（`B(g)`），不再连原始锚点，箭头始终落在可见数字上；
  `chain_segment` 的 `trim` 改为 `min(trim, L*0.30)`，避免短链段被裁成空段。
- 被推开的徽标用**组内同色短细线**回指真实锚点（带白色 halo + 端点小圆点），
  读者仍能判断这个数字对应哪团零件；标签引线仍指向真实锚点。
- `EXPLODED_ANNOTATIONS_V2.csv` 新增 `序号牌 x/y`、`序号牌偏移 px` 三列做审计。

修复结果：仅序号 2 / 3 被移动，各 **19.8 px**，两牌间距 `13.5 → 53.2 px`；
其余 9 组间距最近 161.3 px 全部 OK。裁切区域彩色 ASCII 复核可见青 3（左上）与蓝 2（右下）
两个完整圆盘分离。

> **后续 4.8 节的锚点修正让这次推开不再需要触发**：序号 2 / 3 的锚点分别被覆盖到
> `(1867,255)` / `(1822,220)`（源图坐标），两牌自然间距已是 **57.0 px**，
> `place_badges()` 返回 `displaced_badges = {}`、审计表 `序号牌偏移 px` 全为 `0.0`。
> `place_badges()` 仍保留在脚本里作为兜底——下次改动分组 / 位移时若质心再度重合会自动生效。
> 本节记录的 `730864 B / ee932ca8…` 是中间态；**最终态哈希是 `726769 B / 18ed3aba…`**。

> 这次也暴露一条通用约束：**标签避让 ≠ 徽标避让**。当两组零件的投影质心重合时，
> 单纯拉开标签框没用，必须对序号徽标做独立的去碰撞处理。

### 4.7 修正：Z 步进电机沿安装螺钉轴线纯 +Y 抽出（用户反馈）

用户反馈：「**爆炸图的 Z 轴电机位置不对，它应该就在 Z 轴电机安装位沿安装螺钉的方向平移出来**」。

初版 V2 给 Z 步进电机的位移是 `[-90,-35,60]`——电机斜向飞到左下方，
既不在安装位正前方，也看不出「拧下 4 颗螺钉后直接抽出」的装配逻辑。这是**方向判断错**，不是位移量大小问题。

**轴向判定（依据 `refs/materials/geometry_snapshot_v14.json` 的真实包围盒）**：

| 对象 | bbox `[x0,y0,z0,x1,y1,z1]` mm | 尺寸 mm | 结论 |
|---|---|---|---|
| `Z_Screw_Motor_0` | `[131.75,-9.00,45.77, 137.25,4.00,51.25]` | `5.49 × 13.00 × 5.48` | **长轴 = Y** |
| `Z_Screw_Motor_1/2/3` | 同上（X / Z 位置不同） | `5.49 × 13.00 × 5.48` | **长轴 = Y** |
| `Z_Motor_NEMA17` | `[129,-3,12, 171,39,54]` | `42 × 42 × 42` | 电机本体在端板 **+Y** 侧 |
| `Z_Motor_Shaft` | `[147.52,-17,30.5, 152.48,1,35.5]` | `Ø4.96 × 18.5` | 轴 / 主动轮在 **−Y** 侧 |

4 颗 `Z_Screw_Motor_*` 的 Y 向长度 13.00 mm 是另外两轴的 2.4 倍，说明**安装螺钉轴线就是 Y**；
电机本体在 +Y、轴伸在 −Y，所以拆机时应当**沿 +Y 从安装座里直抽**，不应带 X / Z 分量。

**修改（`refs/scripts/build_exploded_view_v2.py`，唯一改动行）**：

```python
# 之前（错）
("Z 步进电机", Z_MOTOR, [ -90.0,  -35.0,  60.0]),
# 之后
("Z 步进电机", Z_MOTOR, [   0.0,   80.0,   0.0]),
```

并在脚本 docstring 固化口径：

> EXCEPTION - Z stepper motor: it must NOT fly off diagonally.
> The four `Z_Screw_Motor_*` fasteners have bbox `5.49 x 13.00 x 5.48 mm`,
> i.e. their long (mounting-screw) axis is **Y**.

**校核**：电机组抽出后的 3D AABB 为 `[129,63,12, 171,119,54]`，与其余 10 组做 3D AABB
相交检查**无碰撞**（此处曾踩一个 `max()` 迭代写反的脚本 bug：
`[max(x[i+3] for i in range(3)) for x in v]` 应为 `[max(x[i+3] for x in v) for i in range(3)]`）。

**重跑整条链**（任一环节漏跑都会留下旧坐标）：

```
build_exploded_view_v2.py
  → 05_exploded_view_v2.json（6 个 Z 电机 occurrence 62/64/66/68/70/72 全为 [0.0,80.0,0.0]）
  → EXPLODED_GROUPS_V2.csv
  → solidcraft-cli run --in motion.sc --save exploded_v2.sc
  → MCP open + render.camera.fit（distance 1189.16 → 1264.35）
  → 4096×3150 screenshot → crop (753,1009)-(2962,2332)
  → to_white() / projection_anchors() 重新定标（2.5906 → 2.4371 px/mm）
  → annotate_exploded_view.py（3 张 PNG + EXPLODED_ANNOTATIONS_V2.csv）
```

**MCP 陈旧缓存**：用同一路径重新 `open` 仍读回旧 `[-90,-35,60]`。把修正后的设计复制到
全新路径 `D:/mydocuments/SolidCraft/CrossSlide_P014013_exploded_v2_fixed.sc` 强制重载后才读到
`[0,80,0]` 与新相机参数；随后把字节一致的文件拷回项目正式路径。

### 4.8 核实引线圆点与部件是否对应（用户反馈 + 独立分色验证）

用户指令：「**核实圆点与部件是否正确对应**」，并具体指出「**5 限位开关的标识没有指向限位开关上，修改它**」。

**为什么需要独立核实**：4.1 节的锚点是「各组 3D 质心 → 等轴测投影」的估算值。
爆炸后同组零件被拆散，质心可能落在**两件之间的空隙**；等轴测是正交投影，
圆点也可能被**更靠近相机的另一组零件**挡住；甚至落在纯背景上。
单看标注脚本自己的输出无法自证，必须用一套**与标注代码无关**的渲染来读回圆点下的颜色。

**分色渲染（唯一可信的 ground truth）**：

| 步骤 | 做法 / 踩坑 |
|---|---|
| 1 | `refs/tmp/dotcheck_colorize.json` 用 `material.create` / `material.assign` 给 11 组各赋一个纯色 `DOTCHK_01..11`（色相间隔 30°） |
| 2 | **把 127 条 explode moves 烘焙进 occurrence transform**，因为 `explode.show` 只是视图状态、不改进 placement，CLI 离屏 `snapshot` 会渲染成**装配态**而非爆炸态 |
| 3 | 烘焙时踩到**变换约定坑**：本设计 occurrence 变换实际是列主序，平移在**第 3 行** `T[3][i] += t[i]`；写成 `T[i][3]` 会报 `damaged design: occurrence 'Z_EndPlate_L:1' has an invalid placement` |
| 4 | MCP GPU 渲染有外观缓存，着色 `.sc` 后截图与上版字节相同（sha256 都是 `a72e847c…`）；改用**全新 CLI 快照**绕开，烘焙后 bbox 与原爆炸图相差 ≤2 px |
| 5 | 用**完全相同的相机**渲染 4096×3150，按 `OX=753 / OY=1009` 裁到 2209×1323 源图坐标系 → `refs/tmp/exploded_v2_group_colours.png` |

**分类用色度而非 RGB**（光照 / 明暗只是给纯色乘一个标量，色度不变）：

```python
REF = COL / COL.sum(1, keepdims=True)              # 11 个参考色度
n   = v / v.sum(1, keepdims=True)                  # 采样窗口内像素色度
labels = ((n[:, None, :] - REF[None, :, :]) ** 2).sum(2).argmin(1)
counts = np.bincount(labels, minlength=len(ORDER))  # 多数投票 + 覆盖率门槛 0.30
```

> 第一版分类脚本对全部 11 个点返回 `None`，根因是切片把 x 边界 / y 边界写反，
> 取到了空窗口；改成显式 `sub = img[y0:y1, x0:x1]` 后恢复。

**查出的 4 个错点**（`EXPLODED_ANNOTATIONS_V2.csv` 新增 `锚点来源` 列做审计）：

| 序号 | 组 | 旧锚点 | 圆点下实际是什么 | 新锚点 |
|---:|---|---|---|---|
| 2 | Z 端板与导杆 | `(1818,353)` | 落在**序号 3** 的像素上 | `(1867,255)` |
| 3 | Z 同步带传动 | `(1809,345)` | 落在**序号 2** 的像素上（2/3 互换） | `(1822,220)` |
| 5 | Z 限位开关 | `(1696,786)` | **红色 `Z 轴机架（固定基准）`**（用户所指的问题） | `(1720,974)` |
| 10 | 接触式探针总成 | `(218,795)` | 纯背景 | `(195,802)` |

限位开关一组被 `[175,-170,25]` 炸成上下两团，分色图里检测到两个绿色簇
`(1720,564)` 与 `(1720,974)`；旧点 `(1696,786)` 正好落在**两团之间的机架**上。
取下方 `(1720,974)` 的 KW11-3Z-A-1 本体，圆点纯度 85%，不再指空。

**修复（`refs/scripts/annotate_exploded_view.py`）**：

```python
ANCHOR_OVERRIDES = {
    "Z 端板与导杆":    (1867, 255),
    "Z 同步带传动":    (1822, 220),
    "Z 限位开关":      (1720, 974),   # lower KW11-3Z-A-1 body
    "接触式探针总成":  (195, 802),
}
anchors, xyz, scale = projection_anchors(bbox)
anchor_source = {g: "等轴测投影" for g in anchors}
for g, p in ANCHOR_OVERRIDES.items():
    anchors[g] = p
    anchor_source[g] = "分色像素核实"
```

序号 4 的装配动作同步改为「沿螺钉轴线 +Y 抽出 80 mm」，序号 5 的口径说明改为
「上下两开关分离较远，圆点经分色像素核实指向下方 KW11-3Z-A-1 本体，不再落在两开关之间的机架上」。

**新增可复跑的验证脚本** `refs/scripts/verify_exploded_anchors.py`（不依赖标注代码，
只读分色渲染图 + 审计 CSV），本会话实跑结果：

```
seq | group                    | dot (x,y)    | source       | detected                  | pure | verdict
  5 | Z 限位开关               | (1720, 974)  | 分色像素核实 | Z 限位开关                |  85% | OK
 ...
PASS: all 11 leader dots sit on their own functional group
      (4 pixel-verified overrides, 7 automatic projections)
verify exit=0
```

11 组中 7 组的等轴测投影本来就落在正确零件上，只有 4 组需要覆盖——
说明**投影自动定标整体可靠，但不能免检**；分色渲染应作为每次重出爆炸图后的固定收尾检查。

---

## 5. 可复现通道

```bash
# 1) 生成 V2 命令脚本 + 分组审计表（依赖 refs/tmp/sc_occ_map.json）
python refs/scripts/build_exploded_view_v2.py
#    → solidcraft/05_exploded_view_v2.json / EXPLODED_GROUPS_V2.csv

# 2) 从 motion 基线派生 V2 爆炸设计（见第 2.4 节 solidcraft-cli run）
#    → D:/mydocuments/SolidCraft/CrossSlide_P014013_exploded_v2.sc，再拷回项目

# 3) 应用内：open → explode.show {view:425} → render.camera.fit {aspect:1.3}
#    → screenshot {source:"model", grid:false, axes:false, width:4096, height:3150}
#    → 按模型 bbox 裁切成 CrossSlide_exploded_v2.png

# 4) 白底 + 中文标注 + 装配顺序线（输入上一步 PNG + geometry_snapshot_v14.json + V2 CSV）
python refs/scripts/annotate_exploded_view.py
#    → CrossSlide_exploded_v2_white.png / _annotated.png / EXPLODED_ANNOTATIONS_V2.csv

# 5) 收尾必做：核实 11 个引线圆点各自落在正确功能组上
#    先按 4.8 节 5 步生成分色渲染 refs/tmp/exploded_v2_group_colours.png
#    （着色 + 把 127 moves 烘焙进 occurrence 变换 + 同相机 CLI 快照）
python refs/scripts/verify_exploded_anchors.py
#    → 打印逐点 detected/pure/verdict；全部 OK 才 exit=0
```

字体依赖 `C:/Windows/Fonts/msyh.ttc`（正文）与 `msyhbd.ttc`（标题 / 序号），换机器需确认存在。

> **顺序不可颠倒**：Z 电机改位（4.7）会改相机 fit → 改裁切 → 改投影 scale → 改全部锚点，
> 所以必须先重渲染，再重跑标注，最后才做圆点核实；分色渲染也必须用**同一版相机**。
> 分色渲染图是 `refs/tmp/` 下的工作产物（默认被 `.gitignore` 忽略），
> 本轮为让 `verify_exploded_anchors.py` 在干净检出里也能直接跑，已用 `git add -f` 单独纳入版本库。

---

## 6. 文件清单

| 文件 | 说明 | sha256 |
|---|---|---|
| `solidcraft/CrossSlide_exploded_v2_annotated.png` | **最终图**：白底 + 中文 + 顺序线 + 已核实圆点，2209×1713 / 726769 B | `18ed3aba…` |
| `solidcraft/CrossSlide_exploded_v2_white.png` | 纯白底无标注，2209×1323 / 495295 B | `aa93bc1e…` |
| `solidcraft/CrossSlide_exploded_v2.png` | 深灰底裁切源图，2209×1323 / 466129 B | `83dd9035…` |
| `solidcraft/CrossSlide_P014013_exploded_v2.sc` | **可编辑设计**：view 425 / 127 moves（Z 电机 `[0,80,0]`）/ 材质 / study 424 / step 0，1815034 B | `87cf1163…` |
| `solidcraft/05_exploded_view_v2.json` | 阶段 5 命令脚本，1 条 `explode.create` / 127 moves，14845 B | `5e6eb6ff…` |
| `solidcraft/EXPLODED_GROUPS_V2.csv` | 140 行功能组 / 零件 / occurrence id / 位移审计表，7382 B | `9bd53abd…` |
| `solidcraft/EXPLODED_ANNOTATIONS_V2.csv` | 11 行中文标注 / 锚点 / **`锚点来源`** / 标签 / 序号牌位置与偏移 / 装配链 / 3D 质心审计表，2726 B | `4a8c774a…` |
| `refs/scripts/build_exploded_view_v2.py` | V2 更细分组爆炸脚本生成器（含四项覆盖校验 + Z 电机纯 +Y 口径），7911 B | `b710d35b…` |
| `refs/scripts/annotate_exploded_view.py` | 白底 + 中文标注 + 装配顺序线生成器（投影定标 / 避让 / halo / 锚点覆盖），22224 B | `574a3af8…` |
| `refs/scripts/verify_exploded_anchors.py` | **新增**：11 个引线圆点分色像素核实脚本，独立复核 `锚点 → 功能组`，4791 B | `0f0eff40…` |
| `refs/tmp/exploded_v2_group_colours.png` | **新增（`-f` 纳入）**：11 组纯色分色渲染（4096×3150），圆点核实的 ground truth，813501 B | `de9de474…` |
| `refs/SOLIDCRAFT_EXPLODED_V2.md` | 本报告 | — |
| `refs/tmp/sc_explode_v2_results.json` | V2 CLI 执行结果回显 | — |

> 表中哈希 / 大小均为**工作区磁盘文件**的实测值。`.gitattributes` 已把
> `.png / .sc / .gif / .step / .stl / .dxf / .svg / .brp / .3mf` 标为 `-text`，
> 这些二进制 / CAD 产物在检出后哈希不变；`.py / .json / .csv / .md` 属 Git 文本文件，
> 本机是 CRLF、检出可能规范化为 LF，**哈希会变但内容一致**（例如
> `EXPLODED_ANNOTATIONS_V2.csv` 工作区 2726 B / `4a8c774a…`，规范化后 2714 B / `e9b2c20b…`）。
> 校验时以内容比对为准，不要只比哈希。

工作区中间产物（均在 `D:\mydocuments\SolidCraft\`，不入项目库）：
`v2_exploded_4k.png`（4096×3150 纯色底）/ `v2_mcp_test.png` / `v2_assembled.png` /
`v2_exploded.png` / `test_snap.png` / `show_v2.json`；
圆点核实链另有 `dotcheck_colorize.json` / `dotcheck_meta.json` / `dotcheck_final_anchors.json` /
`dotcheck_colorized.sc` / `dotcheck_baked_row.sc`（正确的行主序平移烘焙）/ `dotcheck_baked_col.sc`（错误示范）/
`dotcheck_baked_4k.png` / `annotate_v2_motorfix.json` / `annotate_v2_anchorfix.json` /
`CrossSlide_P014013_exploded_v2_fixed.sc`（绕开 MCP 缓存的新路径副本）；
`refs/tmp/` 下另有 `annotate_v2_anchorfix.json` 记录最终 scale / 锚点 / 标签 / 徽标坐标。

---

## 7. 口径与限制（务必记住）

- **爆炸位移仍是显示层**。`explode.show` 不改 placement / B-rep；V2 `.sc` 的几何总体积、
  21 种材质、study 424、step 0、3 个滑块与 11.25 deg/mm 传动链全部与 `motion.sc` 一致。
  打开文件默认是装配态，查看爆炸图需 `explode.show {view:425}`。
- **127 条 `moves` 绑定 occurrence id**。若重跑迁移、改零件名 / 数量或实施 LM6UU / Ø6 改造，
  必须重跑 `refs/tmp/sc_occ_map.json` 映射 → `build_exploded_view_v2.py` → `annotate_exploded_view.py`，
  否则位移与标注锚点都会落到错误零件上。
- **Z 步进电机是唯一不扇出的组**：位移 `[0,80,0]`、`dx=dz=0`，沿 4 颗 `Z_Screw_Motor_*`
  的长轴（Y）从安装位直抽 80 mm；判定依据是 `geometry_snapshot_v14.json` 里
  `5.49×13.00×5.48 mm` 的螺钉包围盒与电机本体 / 轴伸分别在 +Y / −Y 侧。
  若日后改电机安装方式，这一条必须重新判定，不能沿用。
- **标注锚点有两类来源，不可混用**：7 组是等轴测投影自动定标，4 组是分色像素核实后的
  `ANCHOR_OVERRIDES` 显式覆盖；`EXPLODED_ANNOTATIONS_V2.csv` 的 `锚点来源` 列逐行可查。
  等轴测相机参数（yaw −45° / pitch 35.264°）与渲染取景绑定，当前 **`scale = 2.4371 px/mm`**；
  若改用透视相机、不同视角、或再改任一组的爆炸位移，必须重新 fit → 重新定标 → **重跑
  `verify_exploded_anchors.py`**，否则 4 个覆盖坐标会立刻失效。
- **分色核实图依赖当前爆炸态**：`refs/tmp/exploded_v2_group_colours.png` 是把 127 条 moves
  烘焙进 occurrence 变换后、用同一相机渲染的快照。重跑迁移 / 改分组后必须按 4.8 节重出，
  并且注意变换平移在**第 3 行**（`T[3][i] += t[i]`），写成 `T[i][3]` 会导致 `invalid placement`。
- **PNG 是带标注的渲染截图，不是工程图**。没有尺寸公差、件号 BOM 表、剖视；正式装配图仍需
  TechDraw / AutoCAD 出图（参见 `refs/drawings/X_EndPlate_L_3view.dxf`）。
- **主模型仍是 `LM5UU Ø10×15 + Ø5 导杆`**：用户确认的 LM6UU / 外径 12 / 长 19 / 导杆 Ø6
  改造尚未落盘，标注中的「两根 Ø10 导杆」反映的是磁盘当前状态。
- **3 个开放端板**（`X_EndPlate_L` / `X_EndPlate_R` / `Part__Feature`）仍 `closed=false`，
  只作视觉参照；`Part__Feature` 在 V2 分组里被显式列为「隐藏辅助几何（不显示）」。
- **21 种材质是 SolidCraft 独立 user material**，与 FreeCAD `.FCMat` UUID 不联动。
  详见 `refs/SOLIDCRAFT_MOTION.md` 第 10 节与 `refs/SOLIDCRAFT_MIGRATION.md` 第 5 节。
