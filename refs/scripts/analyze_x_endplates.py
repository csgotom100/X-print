# -*- coding: utf-8 -*-
"""导出原始 X_EndPlate_L/R BREP 的面向量与关键几何，供 SolidCraft 原生重建。"""
from __future__ import annotations

import collections
import json
import math
import os
import sys

import Part

ROOT = 'C:/ink'
OUT = ROOT + '/refs/tmp/x_endplate_original_geometry.json'
BREPS = {
    'X_EndPlate_L': ROOT + '/refs/orig_X_EndPlate_L.brep',
    'X_EndPlate_R': ROOT + '/refs/orig_X_EndPlate_R.brep',
}


def v3(v):
    return [round(float(v.x), 6), round(float(v.y), 6), round(float(v.z), 6)]


def bbox(b):
    return [round(b.XMin, 6), round(b.YMin, 6), round(b.ZMin, 6),
            round(b.XMax, 6), round(b.YMax, 6), round(b.ZMax, 6)]


def surface_info(f):
    s = f.Surface
    t = type(s).__name__
    d = {'type': t, 'area': round(f.Area, 6), 'bbox': bbox(f.BoundBox)}
    if t == 'Plane':
        n = f.normalAt(0, 0)
        d['normal'] = v3(n)
        d['position'] = v3(s.Position)
    elif t == 'Cylinder':
        d['axis'] = v3(s.Axis)
        d['center'] = v3(s.Center)
        d['radius'] = round(float(s.Radius), 6)
    elif t == 'Circle':
        d['axis'] = v3(s.Axis)
        d['center'] = v3(s.Center)
        d['radius'] = round(float(s.Radius), 6)
    return d


def edge_info(e):
    c = e.Curve
    t = type(c).__name__
    d = {'type': t, 'length': round(e.Length, 6),
         'from': v3(e.Vertexes[0].Point), 'to': v3(e.Vertexes[-1].Point)}
    if t == 'Circle':
        d['center'] = v3(c.Center)
        d['axis'] = v3(c.Axis)
        d['radius'] = round(float(c.Radius), 6)
        d['angle'] = round(float(e.ParameterRange[1] - e.ParameterRange[0]), 6)
    return d


out = {}
for name, path in BREPS.items():
    s = Part.Shape()
    s.read(path)
    faces = []
    for i, f in enumerate(s.Faces):
        rec = {'index': i, **surface_info(f)}
        rec['edges'] = [edge_info(e) for e in f.Edges]
        faces.append(rec)
    norms = collections.Counter()
    planes = collections.defaultdict(list)
    for f in faces:
        if f['type'] == 'Plane':
            n = tuple(f['normal'])
            norms[n] += 1
            planes[n].append(f['index'])
    out[name] = {
        'bbox': bbox(s.BoundBox),
        'volume_mm3': round(s.Volume, 6),
        'area_mm2': round(s.Area, 6),
        'solids': len(s.Solids),
        'shells': len(s.Shells),
        'closed': s.isClosed(),
        'face_count': len(s.Faces),
        'face_types': dict(collections.Counter(f['type'] for f in faces)),
        'plane_normal_counts': {str(k): v for k, v in norms.most_common()},
        'plane_groups': {str(k): v for k, v in planes.items()},
        'faces': faces,
    }

with open(OUT, 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, indent=1)
print('WROTE', OUT)
for name, rec in out.items():
    print(name, 'bbox', rec['bbox'], 'V', rec['volume_mm3'],
          'faces', rec['face_count'], rec['face_types'],
          'normals', rec['plane_normal_counts'])
