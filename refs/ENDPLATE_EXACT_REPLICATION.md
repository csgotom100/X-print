# 端板分层参数化复刻 — 交付说明（2026-11-17）

## 交付范围

按用户选择「第 3 条：接受当前结果」交付。端板为 **按 Y 分层的参数化实体**，不是逐面 1:1 的 BREP 复刻。

## 精度（实测，非估算）

| 端板 | 复刻体积 | 原件体积 | 误差 |
|---|---|---|---|
| `X_EndPlate_L` | 19290.36 mm³ | 19158.443 mm³ | **+0.689%** |
| `X_EndPlate_R` | 20063.00 mm³ | 20565.709 mm³ | **-2.444%** |

- 64 个分层 body 全部 `closed=true`、每个单一闭合壳
- timeline `errors 0 / warnings 0`
- 包围盒与原件完全一致：L `0..53 / -82..-37 / 117..157`，R `249..300 / -82..-37 / 117..157`

## 原件基准

```text
X_EndPlate_L  V 19158.443 mm³  bbox 0..53 / -82..-37 / 117..157  192 面  2 实体
X_EndPlate_R  V 20565.709 mm³  bbox 249..300 / -82..-37 / 117..157  191 面  2 实体
主体 shell：L 189 面 / R 188 面；另有 3 面小方块（L V96.2 @X50.5..53，R V26.9 @X249..249.7）
原件 isValid=False：L 565 条自由边、R 536 条（薄壁共面缝合不严）
```

## 分层方案

```text
L  13 层（自适应合并后），34 个外环体 + 孔切除
R  14 层，30 个外环体 + 孔切除
```

自适应合并规则：相邻层截面积相对差 ≤3% 且合计厚度 ≤8 mm 时合并，减少布尔并集失败。

## 关键技术结论（踩过的坑）

1. **DXF 只读二维**：SolidCraft 读 DXF 只认 `10/20`，不读 `30/31`。XZ 平面草图坐标必须是 `u = X, v = -Z`。首版写世界 XZ 导致所有点落到 y=0。
2. **整圆必须写 CIRCLE**：两段 ARC 拼整圆时首尾角度不连续，SolidCraft 判为不闭合。
3. **每个外环单独一个 DXF**：一个 DXF 里放「外环 + 内环」，SolidCraft 的轮廓解析与预期不一致，会漏环或把孔当实体。改为每个外环一个 DXF、一个 body，孔单独 DXF 再 `cut`。
4. **`slice()` 不可靠**：薄壁、窄条、圆弧外缘处会重复返回同一环（L 在 Y=-68 处 17 个环里有 9 个重复）、只返回部分环（R07 只给 92.19，真实 1312）、甚至返回 0 环（R05 全层）。**唯一可靠来源是薄片（`common` 小盒）的 -Y 面**。
5. **孔要从薄片面的 `Wires` 里取**：`Face.OuterWire` 不含内环；必须遍历 `face.Wires` 取非 `OuterWire` 的那些。
6. **孔归属要用几何包含判断**：包围盒包含会误判 L 形/带缺口轮廓，改用 `face.isInside(centerOfMass, tol, True)`。
7. **布尔并集不能面接触**：相邻层恰好共面会 `boolean Union: no result`，需 0.01 mm 实体重叠。
8. **STEP / FCStd 导入都丢面**：原件 `isValid=False`（L 565 条自由边、R 536 条）；`fix()` 后 `valid=True` 但 STEP 导入 SolidCraft 仍从 189 面降到 161 面且不闭合，FCStd 降到 99/104 面。此路不通。
9. **`solid.loft` 限制**：要求每个 section 只有一个轮廓，带孔或分段截面直接报 `each loft section must be one profile`；上下环数不等时配对会丢段（R12 放样只得 2233 / 真实 3445.63）。
10. **端板大量锥面**：27 个 Y 层中 19 层上下截面不等（最大 R01 +24.0%、R12 +15.2%、L11 +12.2%）。等截面拉伸必然偏低，这是 R 端板 -2.44% 的主因。

## R 端板剩余 -2.44% 的成因

不是算法问题，是**拓扑变化**：R 端板 `-50..-38` 的 12 mm 厚层，低截面被两道横梁分成 3 段（65.61 / 131.22 / 65.91），高截面合并成 1 段（307.22）。这是三段汇聚成一段，等截面拉伸无法表达。

要收敛到 1% 以内，必须把这 3 段与高截面按包围盒配对后**逐段分别放样再合并**。

## 可编辑性

- 每层的截面是独立草图（`EP<tag><nn>_o<k>.dxf` 导入），层厚是 `solid.extrude` 的 `distance` 参数
- 改层厚或换截面 DXF 后重算即可，符合「可编辑」要求
- 但层结构由 Y 平面划分固定，改整体轮廓需要重新生成 DXF

## 取证与生成链路

| 脚本 | 作用 |
|---|---|
| `refs/scripts/analyze_x_endplates.py` | 提取全部面/边/法向/圆柱面 → `x_endplate_original_geometry.json` |
| `refs/scripts/extract_endplate_layers.py` | 按 ±Y 平面分组，输出每层闭合环 |
| `refs/scripts/write_endplate_dxf.py` | **核心**：薄片截面 + 去重 + 孔归属 + 每外环独立 DXF |
| `refs/scripts/build_endplate_exact.py` | 生成 `31_endplate_bands.json` |
| `refs/scripts/area_by_slab.py` | 薄片法测真实截面积（精度基准） |
| `refs/scripts/make_endplate_loft_sections.py` | 变截面层上下双截面（放样备用） |

## 文件清单

| 文件 | 说明 |
|---|---|
| `refs/tmp/EP_bands_stage1.sc` | 分层实体（64 body） |
| `solidcraft/31_endplate_bands.json` | 分层构建命令（329 条） |
| `solidcraft/32_endplate_merge.json` | 合并命令 |
| `refs/tmp/ep_dxf_manifest.json` | 每层面积 / 外环数 / 孔数 / DXF 路径 |
| `refs/tmp/x_endplate_original_geometry.json` | 原件 192/191 面完整几何 |
| `refs/tmp/dxf/` | 全部截面 DXF |

## 网格基准（仅作外观比对，不作参数化交付）

`D:\mydocuments\SolidCraft\X_EndPlate_L_exact.stl`（16038 面）/ `X_EndPlate_R_exact.stl`（14058 面），包围盒与原件完全一致，可用于目视核对形状。
