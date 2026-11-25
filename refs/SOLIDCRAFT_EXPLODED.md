# SolidCraft 整机功能组爆炸图报告（V1）

生成时间：2026-11-12
用户指令：「再生成一张爆炸图」

> **升级版已交付（V2）**：用户后续追加「中文标注部件名称 + 装配顺序线」「背景改白」「再多炸开一些零件」。
> V2 把固定基准从 40 件缩到 12 件、移动件 100 → **127**，并输出白底 + 11 组中文标注 + 装配顺序线最终图。
> 见 **`refs/SOLIDCRAFT_EXPLODED_V2.md`** 与 `solidcraft/CrossSlide_exploded_v2_annotated.png`。
> 本报告保留 V1（6 组 / 100 moves / 深灰底）的完整技术记录，作为 V2 的基线与历史留档。

**主交付**

- `solidcraft/CrossSlide_exploded.png` —— 2544×1957 / RGB / 852182 B / sha256 `c62fe382…`
- `solidcraft/CrossSlide_P014013_exploded.sc` —— 可编辑设计，1814859 B / sha256 `eb430e40…`

**基线**：`solidcraft/CrossSlide_P014013_motion.sc`（v14 材质 + 运动链 + 打码 study，见
`refs/SOLIDCRAFT_MOTION.md`）；几何来源见 `refs/SOLIDCRAFT_MIGRATION.md`。

---

## 1. 结论速览

| 项目 | 结果 |
|---|---|
| 爆炸视图 | id **425**，`整机爆炸图 / Assembly exploded` |
| 位移 | **100 条显式 `moves`**，另 **40 个 occurrence 作基准不动**，合计 140 = 全部非 root occurrence |
| 分组 | 6 个功能组 + 1 个 Z 轴骨架基准组（`EXPLODED_GROUPS.csv` 140 行审计表） |
| 出图 | **2544×1957 / 11284 色**，模型占画面 **91.7%**，四边无裁切 |
| 派生设计 | 从 `motion.sc` 派生；21 材质 / study 424 / step 0 / 爆炸视图 425 全部读回完好，`errors=0` |
| 几何 | 与 `motion.sc` 完全一致 —— `explode.show` 只改显示，**不改 placement / B-rep** |

---

## 2. 为什么不用 SolidCraft 的自动径向爆炸

`explode.create {scale: ...}` 在本设计上直接报错：

```
invalid parameters for `explode.create`: an exploded view needs two or more occurrences
```

两个原因：

1. **组件树是扁平的**。命名装配 STEP 导入后，140 个 occurrence 全部用 `rigid` 关节挂在
   root occurrence `2` 下（见 `refs/SOLIDCRAFT_MOTION.md` 第 4.1 节），没有嵌套子装配层级，
   自动径向爆炸算法找不到可展开的层级。
2. **即使可用也不可读**。本设计有 70 个紧固件；逐 occurrence 径向散开会把螺钉、T 型螺母
   甩得到处都是，装配关系彻底丢失。

因此改为**显式 `moves`：每个 occurrence 一条 `{occurrence, translate}`，但一个功能组共享
同一个 translate**。组内紧固件随组整体平移，组内装配关系保持完整；组与组之间沿 −Y 依次
拉开，并在 X / Z 上交错，避免等轴测视图里相互遮挡。Z 轴骨架保持原位作为读图基准。

> 已先用两个测试 occurrence 验证显式 `moves` 路径可行，再生成全量 100 条。

---

## 3. 分组方案

| 功能组 | 件数 | `translate [dx, dy, dz]` mm | 说明 |
|---|---:|---|---|
| Z 轴骨架（基准，不动） | 40 | `[0, 0, 0]` | Z 型材 / 端板 / 导杆 / 同步轮 / 同步带 / 电机 / 限位开关及紧固件 |
| Z 滑车 + XZ 连接板 | 23 | `[0, -40, 50]` | 上抬 +50 并前移，露出 Z 滑座与十字连接板 |
| X 横梁总成 | 30 | `[0, -85, 0]` | 型材、两端板、导杆、轮、带、电机、限位开关整体前移 |
| X 滑车 | 10 | `[0, -150, 0]` | 上下滑座、轴承、嵌件、夹紧键 |
| HP45 喷头总成 | 18 | `[-25, -235, 0]` | 墨盒、夹具五件、转接板、探针臂 |
| 接触式探针总成 | 13 | `[-115, -235, 0]` | 侧向再拉 −115，让小零件不与喷头总成重叠 |
| 保湿站 | 6 | `[95, -55, 0]` | 向 +X 拉出，与主体分离 |
| **合计** | **140** | | **100 移动 + 40 基准** |

分组依据的是**工程装配语义**，不是 SolidCraft 里的子装配（导入后本就没有子装配层级）。
`HP45_ProbeHousing` 等探针件单独成组，是因为它们体积小、又与喷头总成贴邻，留在同组会被遮住。

---

## 4. 生成器与命令格式

`refs/scripts/build_exploded_view.py` 输入 `refs/tmp/sc_occ_map.json`（occurrence id → 零件名），
输出 `solidcraft/04_exploded_view.json`（单条命令）与 `solidcraft/EXPLODED_GROUPS.csv`（审计表）。

分组用集合定义，紧固件用 `seq()` / `rng()` 批量展开：

```python
def seq(stem, count):
    return {f"{stem}_{i}" for i in range(count)}

def rng(stem, lo, hi):
    return {f"{stem}_{i}" for i in range(lo, hi + 1)}

GROUPS = [
    ("Z 滑车 + XZ 连接板", Z_CAR,   [0.0, -40.0, 50.0]),
    ("X 横梁总成",         X_FRAME, [0.0, -85.0, 0.0]),
    ("X 滑车",             X_CAR,   [0.0, -150.0, 0.0]),
    ("HP45 喷头总成",      HEAD,    [-25.0, -235.0, 0.0]),
    ("接触式探针总成",     PROBE,   [-115.0, -235.0, 0.0]),
    ("保湿站",             CAP,     [95.0, -55.0, 0.0]),
]
```

生成器带三项硬校验，任一失败即 `SystemExit`，避免静默漏件：

```python
for label, members, _ in GROUPS:
    unknown = members - all_names           # 名字必须存在于 occ_map
    if unknown: raise SystemExit(...)
    for n in members:
        if n in seen: raise SystemExit(...) # 不能同时属于两组
        seen[n] = label
ground = sorted(all_names - set(seen))
assert len(seen) + len(ground) == len(all_names)   # 140 全覆盖
```

输出命令（与其它三阶段脚本同为 `{"commands": [...]}` 包装）：

```json
{"commands": [{
  "command": "explode.create",
  "params": {"name": "整机爆炸图 / Assembly exploded",
             "moves": [{"occurrence": 42, "translate": [0.0, -40.0, 50.0]}, ...]}
}]}
```

`moves` 按 occurrence id 排序后写入；`Part__Feature`（隐藏辅助几何）与 root `2` 被明确排除。

---

## 5. 可复现通道

```bash
# 1) 生成命令脚本 + 审计表（依赖 refs/tmp/sc_occ_map.json）
python refs/scripts/build_exploded_view.py

# 2) 从 motion 基线派生爆炸视图设计
"/d/Program Files/SolidCraft/solidcraft-cli.exe" run \
  "D:/ink/solidcraft/04_exploded_view.json" \
  --in  "D:/mydocuments/SolidCraft/CrossSlide_P014013_motion.sc" \
  --save "D:/mydocuments/SolidCraft/CrossSlide_P014013_exploded.sc" \
  --results --json-out "D:/ink/refs/tmp/sc_explode_results.json" \
  --param-check warn

# 3) 应用内显示 → 高分辨率截图 → 复位为装配态
#    explode.show {view: 425}
#    screenshot   {path: ".../CrossSlide_exploded_6k.png", width: 6144, height: 3840}
#    explode.show {view: none}

# 4) 把 .sc 与裁切后的 PNG 拷回 D:/ink/solidcraft/
```

注意事项：

- **路径沙箱**：与前三阶段相同，`open` / `screenshot` / `file.save` 只能写
  `D:\mydocuments\SolidCraft` 等允许目录，产物再拷回项目。
- `moves` 里的 occurrence id 来自本次 STEP 导入顺序。**若重跑迁移或改零件名 / 数量，
  必须重跑 `refs/tmp/sc_occ_map.json` 映射与 `build_exploded_view.py`**，否则位移会落到错误零件上。
- 交付的 `.sc` 保存时处于**装配态**（未 show 爆炸视图），这样打开即见正常整机；
  查看爆炸图请在 SolidCraft 里执行 `explode.show {view: 425}`。

---

## 6. 出图与构图优化

爆炸视图是显示层效果，`screenshot` 的默认取景留白很大。逐轮试探过程：

| 尝试 | 结果 |
|---|---|
| `screenshot {view:"iso"}` | 模型仅占画面 **14.7%**，四周大片空白 |
| `screenshot {view:"fit"}` | **14.8%**，几乎无改善 |
| `render.camera.fit {aspect:1.6}` | **36.3%**，改善但仍不可用 |
| 手动 `render.camera.set` 调 `distance` 试探 | 偏离 fit 值后占比反而更小，放弃调相机 |
| `screenshot {width:4096, height:2560}` | 有效像素够，但留白比例不变 |
| `screenshot {width:6144, height:3840}` | 实际被 **clamp 到 4096×3840**，模型有效像素 2334×1797 |

最终采用**「先拉满渲染分辨率，再按模型包围盒裁切」**，而不是继续拧相机：

```python
mx, my = int((x1-x0)*0.045), int((y1-y0)*0.045)
L, T = max(0, x0-mx),            max(0, y0-my)
R, B = min(im.width, x1+mx),     min(im.height, y1+my)
crop = im.crop((L, T, R, B))
crop.save(out, optimize=True)
```

裁切结果：`solidcraft/CrossSlide_exploded.png` = **2544×1957 / 852182 B / RGB 11284 色 / 模型占 91.7% / 四边无裁切**。

**装配态 ↔ 爆炸态对照验证**（`D:/mydocuments/SolidCraft/CrossSlide_assembled_iso.png` 对照）：

```
mean |delta|            = 3.51
pixels changed > 20     = 7.3%
assembled bbox          = (1271,482)-(1824,1246)
exploded  bbox          = (1042,473)-(1924,1152)
```

模型包围盒明显向外扩张、像素确有变化，证明 `explode.show` 已进入渲染，不是空白或没生效。

> 本会话 `ViewImage` 不可用（`the selected model cannot receive images`）；判断构图一律用
> PIL + numpy 统计背景色、非背景像素占比、bbox 覆盖率与颜色数。
> `screenshot` 返回 `[image omitted: model does not support image input]` 是正常现象，PNG 已按 `path` 落盘。

---

## 7. 读回验证

重新打开磁盘中的 `CrossSlide_P014013_exploded.sc`，清掉内存里的临时显示 / 相机状态后做权威读回：

| 检查 | 结果 |
|---|---|
| `open` | `errors: 0` |
| `explode.list` | view **425**，`整机爆炸图 / Assembly exploded`，**100 条 moves** 全在 |
| `.sc` ZIP `/assembly/exploded[0]` | `id: 425` + name + 100 组 `[occ, translate]`（本地复核） |
| `.sc` ZIP 条目 | 3 个：`blobs/*.step` / `document.json` / `container.json` |
| `motion.list` | study **424**，`打码工作循环 / Coding cycle`，100 steps，3 keys |
| `joint.inspect 411` | `value: 0.0` / `resolves=true` / `conflicts=[]`（初始姿态未被爆炸操作改动） |
| `material.list` | 21 个 `user:true` 材质全部存在，末项 `工艺辅助几何非零件` |
| `document.json` 关键字计数 | `PETG-FDM occurrences = 18` / `Coding cycle = 1` / `Assembly exploded = 1` |

> 曾试图直接遍历 `document.json` 里的 `user:true` / `type:"slider"` 字段来找滑块与材质，
> 字段结构和预想不一致、一无所获。上述结论全部改用 SolidCraft 权威读回命令 +
> 本地只校验已明确的 `/assembly/exploded[0]` 路径，不要凭猜测解析文档结构。

---

## 8. 文件清单

| 文件 | 说明 | sha256 |
|---|---|---|
| `solidcraft/CrossSlide_exploded.png` | **主图**：2544×1957 / 852182 B / 模型占 91.7% | `c62fe382…` |
| `solidcraft/CrossSlide_P014013_exploded.sc` | **可编辑设计**：view 425 + 材质 + study 424，装配态保存 | `eb430e40…` |
| `solidcraft/04_exploded_view.json` | 阶段 4 命令脚本，1 条 `explode.create` / 100 moves，11689 B | `75980e67…` |
| `solidcraft/EXPLODED_GROUPS.csv` | 140 行功能组 / 零件 / occurrence id / 位移审计表，7551 B | `a1cce248…` |
| `refs/scripts/build_exploded_view.py` | 分组爆炸脚本生成器（含三项覆盖校验） | — |
| `refs/SOLIDCRAFT_EXPLODED.md` | 本报告 | — |
| `refs/tmp/sc_explode_results.json` | CLI 执行结果回显 | — |

中间渲染（均在 `D:\mydocuments\SolidCraft\`，不入项目库）：
`CrossSlide_exploded.png`（2560×1600 iso 初版）/ `_fit.png` / `_fitcam.png` /
`_zoom.png` / `_zoom2.png` / `_4k.png` / `_6k.png`（实际 4096×3840）/
`CrossSlide_assembled_iso.png`（装配态对照）。

---

## 9. 口径与限制（务必记住）

- **爆炸位移是显示层，不是真拆件**。`explode.show` 不改 placement、不改任何 B-rep；
  交付 `.sc` 的几何总体积仍为 `856894.075 mm³`，与迁移基线一致。`explode.show {view:none}`
  随时可回装配态。
- **PNG 是渲染截图，不是工程图**。没有尺寸标注、件号引线或 BOM 表；正式装配图仍需
  TechDraw / AutoCAD 出图（参见 `refs/drawings/X_EndPlate_L_3view.dxf` 的做法）。
- **分组是人为的工程语义分组**，SolidCraft 里并不存在对应子装配；100 条 `moves` 绑定
  occurrence id，重跑迁移 / 实施 LM6UU 改造后必须重新生成。
- **主模型仍是 `LM5UU Ø10×15 + Ø5 导杆`**：用户确认的 LM6UU / 外径 12 / 长 19 / 导杆 Ø6
  改造尚未落盘，本爆炸图反映的是磁盘当前状态。
- **3 个开放端板**（`X_EndPlate_L` / `X_EndPlate_R` / `Part__Feature`）仍 `closed=false`，
  只作视觉参照；21 种材质是 SolidCraft 独立 user material，与 FreeCAD `.FCMat` UUID 不联动。
  详见 `refs/SOLIDCRAFT_MOTION.md` 第 10 节与 `refs/SOLIDCRAFT_MIGRATION.md` 第 5 节。
