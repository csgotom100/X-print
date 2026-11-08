# X-print

面向工控喷墨打码机的 **X / Z 十字滑台 + HP45 热发泡喷头** 机械设计工程。

FreeCAD 1.1 单一装配文件，包含十字滑台本体、HP45 墨盒夹持总成、保湿站，
并配有 TechDraw 出图脚本，可一键重出 A1 整机三视图与 A2 喷头总成图。

![整机三视图](refs/System_Assembly_A1.png)

---

## 1. 系统构成

| 模块 | 说明 |
|---|---|
| **Z 轴（升降）** | 2040 铝型材 150 mm + 两根 Ø10 导杆（165 mm），GT2 同步带，NEMA17 驱动 |
| **X 轴（横移）** | 2040 铝型材 200 mm + 两根 Ø10 导杆（215 mm），GT2 同步带，NEMA17 驱动 |
| **XZ 连接板** | 10 mm 厚，连接两轴，构成十字滑台 |
| **HP45 喷头总成** | HP45 墨盒 + 卡扣（latch）+ 压紧弹片 + 墨盒座 |
| **探针** | 安装在喷头 X 方向前方，测量墨盒喷嘴面到工件的高度 |
| **保湿站** | 停机时密封喷嘴，防止墨水干涸 |
| **限位开关** | X / Z 各两个，机械式，M2.5 螺钉固定，按钮先触发 |

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
├── CrossSlide_P014013.FCStd          # 主装配文件（FreeCAD 1.1，141 个对象）
├── refs/
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

### 4.4 3D 打印注意

X / Z 端板为树脂 3D 打印件，设计时已考虑：

- 沉孔处局部加厚 2 mm，凸台 3 mm，螺钉头完全齐平
- 端板收敛为单一实体，无游离碎块
- 螺纹孔壁厚不低于 2 mm

---

## 5. 待办 / 后续优化方向

- [ ] 控制器 PCB 是否外置，以及安装位置
- [ ] 探针电气选型与接口（信号类型、接插件）
- [ ] 拖链与墨管夹的走线路径
- [ ] 惰轮张紧槽（当前张紧靠端板长孔）
- [ ] 保湿站废墨刮片

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
