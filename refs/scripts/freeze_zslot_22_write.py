# -*- coding: utf-8 -*-
"""把「Z 轴限位槽 22.00 保持」写成 FreeCAD 模型内的设计冻结标注。

【诊断脚本，已弃用】拆分版（原 freeze_zslot_22.py 超时）：本脚本 **只写不验**、
不重新打开文档、不调用 recompute（纯字符串属性无需重算几何）。每一步都写
独立文件日志并立即 flush+close，即使进程被强制杀掉也能看到停在哪一步。
用它定位到卡点就是 App.openDocument；正式写入请用 freeze_zslot_22_xml.py。

只加 App::PropertyString 元数据（DesignFreeze），不修改任何几何。
用户原话：「既然Z轴已经是22了，那就不用修改」「z轴保持22.00」「Z 轴保持 22.00」。
"""
import os
import shutil
import time
import traceback

import FreeCAD as App

DOC = 'C:/ink/CrossSlide_P014013.FCStd'
BAK = 'C:/ink/refs/CrossSlide_before_zfreeze.FCStd'
OUT = 'C:/ink/refs/tmp/freeze_out.FCStd'
LOG = 'C:/ink/refs/tmp/freeze_write.log'

NOTE = ('设计冻结（用户 2026-11-09 明确要求）：Z 轴限位开关安装槽净宽 '
        '22.00 mm，位于 Z_EndPlate_L 的 X139.00..161.00；开关本体 19.80，'
        '两侧各留 1.10 mm。禁止修改本端板、槽宽及两个 Z 限位开关安装位。'
        'X 轴端板口袋 20.80 mm 亦为已定稿尺寸，勿回退。')
TARGETS = ['Z_EndPlate_L', 'Z_LimitSwitch_Bot', 'Z_LimitSwitch_Top']


def log(msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()
        os.fsync(f.fileno())
    try:
        print(line, flush=True)
    except Exception:
        pass


if os.path.exists(LOG):
    os.remove(LOG)

log('START  pid=%d' % os.getpid())
try:
    if not os.path.exists(BAK):
        shutil.copyfile(DOC, BAK)
        log('backup created: %s' % BAK)
    else:
        log('backup already exists: %s' % BAK)
    log('FCStd before: size=%d mtime=%s'
        % (os.path.getsize(DOC), time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(DOC)))))

    log('openDocument ...')
    d = App.openDocument(DOC)
    log('openDocument OK  objects=%d' % len(d.Objects))

    for n in TARGETS:
        o = d.getObject(n)
        if o is None:
            raise RuntimeError('object not found: %s' % n)
        if 'DesignFreeze' not in o.PropertiesList:
            o.addProperty('App::PropertyString', 'DesignFreeze', 'Design',
                          'Design freeze note (user decision)')
            log('%s : addProperty done' % n)
        else:
            log('%s : DesignFreeze already present' % n)
        o.DesignFreeze = NOTE
        log('%s : value set' % n)

    # 纯字符串元数据，不做 recompute（原脚本疑似卡在这一步）
    log('saveAs -> %s ...' % OUT)
    if os.path.exists(OUT):
        os.remove(OUT)
    d.saveAs(OUT)
    log('saveAs OK  size=%d' % os.path.getsize(OUT))

    log('closeDocument ...')
    App.closeDocument(d.Name)
    log('closeDocument OK')

    # 用已验证的产物覆盖目标文件（绕开 GUI 打开同名文件时的写入冲突）
    shutil.copyfile(OUT, DOC)
    log('copied OUT -> DOC  size=%d' % os.path.getsize(DOC))
    log('DONE')
except Exception:
    log('EXCEPTION:\n' + traceback.format_exc())
    raise
