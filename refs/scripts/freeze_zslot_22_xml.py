# -*- coding: utf-8 -*-
"""把「Z 轴限位槽 22.00 保持」写成 FreeCAD 模型内的设计冻结标注（XML 精确编辑版）。

背景：freecadcmd 在本机 13:28 之后 openDocument 一律卡死（副本也一样），
故绕开 FreeCAD 引擎，直接编辑 FCStd 压缩包内的 Document.xml：
  * 仅为 3 个对象新增 App::PropertyString 元数据 DesignFreeze；
  * Properties/@Count 同步 +1；
  * 所有 *.brp / *.Map.txt / GuiDocument.xml 等条目按原字节、原压缩方式原样复制。
**不修改任何几何。**

产物写到 refs/tmp/freeze_xmledit.FCStd，由调用方确认后再覆盖主文件。
回滚点：refs/CrossSlide_before_zfreeze.FCStd（改动前的完整副本）。

用户原话：「既然Z轴已经是22了，那就不用修改」「z轴保持22.00」「Z 轴保持 22.00」。
"""
import hashlib
import os
import re
import zipfile
from xml.sax.saxutils import escape

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_zfreeze.FCStd'
OUT = 'C:/ink/refs/tmp/freeze_xmledit.FCStd'

NOTE = ('设计冻结（用户 2026-11-09 明确要求）：Z 轴限位开关安装槽净宽 '
        '22.00 mm，位于 Z_EndPlate_L 的 X139.00..161.00；开关本体 19.80，'
        '两侧各留 1.10 mm。禁止修改本端板、槽宽及两个 Z 限位开关安装位。'
        'X 轴端板口袋 20.80 mm 亦为已定稿尺寸，勿回退。')
TARGETS = ['Z_EndPlate_L', 'Z_LimitSwitch_Bot', 'Z_LimitSwitch_Top']

PROP_TPL = (
    '<Property name="DesignFreeze" type="App::PropertyString" group="Design" '
    'doc="Design freeze note (user decision)" attr="0" ro="0" hide="0" '
    'status="2097152">\n'
    '                    <String value="%s"/>\n'
    '                </Property>\n'
    '            '
)

if not os.path.exists(BAK):
    raise SystemExit('回滚备份不存在：%s' % BAK)

with zipfile.ZipFile(DOC) as zin:
    entries = [(i, zin.read(i.filename)) for i in zin.infolist()]

src = dict((i.filename, data) for i, data in entries)
text = src['Document.xml'].decode('utf-8')
orig_text = text

for name in TARGETS:
    head = '<Object name="%s">' % name
    start = text.find(head)
    if start < 0:
        raise SystemExit('找不到对象块：%s' % name)
    end = text.find('</Object>', start)
    if end < 0:
        raise SystemExit('对象块未闭合：%s' % name)
    block = text[start:end]
    if 'DesignFreeze' in block:
        print('  %-22s 已有 DesignFreeze，跳过' % name)
        continue

    m = re.search(r'<Properties Count="(\d+)"', block)
    if not m:
        raise SystemExit('找不到 Properties/@Count：%s' % name)
    cnt = int(m.group(1))
    nprops = len(re.findall(r'<Property\s', block))
    print('  %-22s Count=%d  实际 <Property>=%d' % (name, cnt, nprops))

    block = block[:m.start()] + '<Properties Count="%d"' % (cnt + 1) + block[m.end():]
    pos = block.rfind('</Properties>')
    if pos < 0:
        raise SystemExit('找不到 </Properties>：%s' % name)
    block = block[:pos] + (PROP_TPL % escape(NOTE)) + block[pos:]
    text = text[:start] + block + text[end:]
    print('  %-22s -> 插入 DesignFreeze，Count %d -> %d' % (name, cnt, cnt + 1))

# ---- 结构自检（覆盖前）----
import xml.etree.ElementTree as ET
ET.fromstring(text)                                   # 必须仍是合法 XML
assert text.count('name="DesignFreeze"') == len(TARGETS), 'DesignFreeze 数量不对'
assert text.count('<Object name=') == orig_text.count('<Object name='), '对象数量变化'
print()
print('  XML 合法；DesignFreeze 节点 = %d；对象块数 = %d'
      % (text.count('name="DesignFreeze"'), text.count('<Object name=')))

# ---- 重新打包：除 Document.xml 外全部原字节、原压缩方式 ----
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w') as zout:
    for info, data in entries:
        if info.filename == 'Document.xml':
            data = text.encode('utf-8')
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zi.internal_attr = info.internal_attr
        zi.create_system = info.create_system
        zi.comment = info.comment
        zout.writestr(zi, data)

# ---- 几何与非 XML 条目逐字节比对 ----
with zipfile.ZipFile(OUT) as znew:
    names_new = znew.namelist()
    assert names_new == [i.filename for i, _ in entries], '条目顺序/数量变化'
    diff = [n for n in names_new
            if n != 'Document.xml' and
            hashlib.sha256(znew.read(n)).digest() != hashlib.sha256(src[n]).digest()]
    print('  条目数 = %d；非 Document.xml 内容变化 = %d  %s'
          % (len(names_new), len(diff), diff[:5]))

print('  [产物] %s  size=%d' % (OUT, os.path.getsize(OUT)))
print('  [回滚] %s  size=%d' % (BAK, os.path.getsize(BAK)))
