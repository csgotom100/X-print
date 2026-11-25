# -*- coding: utf-8 -*-
"""校验 DXF 并渲染 PNG / SVG 预览（白底黑线，便于用户截图后手绘标记）"""
import os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

DXF = 'C:/ink/refs/drawings/X_EndPlate_L_3view.dxf'
PNG = 'C:/ink/refs/drawings/X_EndPlate_L_3view.png'
SVG = 'C:/ink/refs/drawings/X_EndPlate_L_3view.svg'
LOGP = 'C:/ink/refs/tmp/render_3view_preview.log'

_f = open(LOGP, 'w', encoding='utf-8')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); _f.write(s + '\n'); _f.flush(); os.fsync(_f.fileno())

# ------------------------------------------------------------------ 校验
doc = ezdxf.readfile(DXF)
aud = doc.audit()
P('AUDIT errors=%d fixes=%d' % (len(aud.errors), len(aud.fixes)))
for e in aud.errors[:10]:
    P('  ERR', e)
msp = doc.modelspace()
P('DXF version', doc.dxfversion, 'units', doc.header.get('$INSUNITS'),
  'clayer', doc.header.get('$CLAYER'))
P('LAYERS:')
for l in doc.layers:
    P('  %-9s color=%-3s lt=%-12s off=%s' %
      (l.dxf.name, l.dxf.color, l.dxf.linetype, l.is_off()))
by = {}
for e in msp:
    by[e.dxf.layer] = by.get(e.dxf.layer, 0) + 1
P('ENTITIES by layer:', by)
P('TOTAL', len(msp))

# ------------------------------------------------------------------ 预览用副本
# HIDDEN 层在正式 DXF 中默认关闭；渲染后端不一定尊重 layer off，显式删掉
pv = ezdxf.readfile(DXF)
pm = pv.modelspace()
rm = [e for e in pm if e.dxf.layer in ('HIDDEN',)]
for e in rm:
    pm.delete_entity(e)
P('preview: removed %d hidden entities' % len(rm))
# 7 号色（白/黑自适应）在白纸上会被渲成白色 → 预览副本里改为 250 近黑
# 只改预览副本，正式 DXF 保留 7 号，AutoCAD 深浅背景都能正常显示
for ln in ('0', 'Defpoints', 'FRAME', 'OUTLINE'):
    try:
        pv.layers.get(ln).dxf.color = 250
    except Exception:
        pass
P('preview: FRAME/OUTLINE color 7 -> 250 (near-black on white)')

for fam in ('Microsoft YaHei', 'SimHei', 'SimSun', 'DengXian'):
    try:
        matplotlib.font_manager.findfont(fam, fallback_to_default=False)
        plt.rcParams['font.sans-serif'] = [fam, 'DejaVu Sans']
        P('font family', fam)
        break
    except Exception:
        continue
plt.rcParams['axes.unicode_minus'] = False

try:
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy
    # 按图层真实颜色渲染；预览副本已把 7 号改成 250 近黑
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE,
                        color_policy=ColorPolicy.COLOR)
    P('render config: WHITE / COLOR')
except Exception as ex:
    cfg = None
    P('render config FAILED (%s)' % ex)

fig = plt.figure(figsize=(16.8, 11.88), dpi=160, facecolor='white')
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor('white')
ctx = RenderContext(pv)
backend = MatplotlibBackend(ax)
if cfg is not None:
    Frontend(ctx, backend, config=cfg).draw_layout(pm, finalize=True)
else:
    ctx.current_layout_properties.set_colors('#FFFFFF', '#000000')
    Frontend(ctx, backend).draw_layout(pm, finalize=True)
ax.set_xlim(-2, 422)
ax.set_ylim(-2, 299)
ax.set_aspect('equal')
ax.axis('off')
fig.savefig(PNG, dpi=160, facecolor='white', bbox_inches=None)
fig.savefig(SVG, facecolor='white', bbox_inches=None)
plt.close(fig)
P('WROTE', PNG, os.path.getsize(PNG), 'bytes')
P('WROTE', SVG, os.path.getsize(SVG), 'bytes')
P('RENDER DONE')
_f.close()
