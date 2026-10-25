# เก็บงานแมวหลังฉายสี (project_views.py) : ขยายหาง + ฉายภาพหน้าใกล้ (face.png) ลงผิวหัวที่หันหน้า
#   blender -b --factory-startup --python-exit-code 1 -P tools/ai3d/cat_touchup.py -- <in.glb> <out.glb> [--cfg tools/ai3d/cat_touchup.json] [--closed | --face <ภาพ>] [--atlas]
# ใช้กับแมวตัวอื่น : --cfg tools/ai3d/som_touchup.json (ไม่มีหัวข้อ tail/ears = ข้ามขั้นนั้น)
# --closed = ใช้ภาพหลับตาแทน · --face = ภาพหน้าอารมณ์อื่น (กรอบภาพเท่ากัน) · แกน Blender : หน้าแมวหัน −Y · ขึ้น +Z
# หน้าใช้ภาพแยกเพราะ project_views ให้ผิวที่หันเฉียงเกิน 45° ใช้ภาพข้าง → ตาจากมุมข้างหายไป
import argparse
import json
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import atlas_pack  # noqa: E402

FRONT = Vector((0, -1, 0))


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:]
    p = argparse.ArgumentParser()
    p.add_argument('src')
    p.add_argument('out')
    p.add_argument('--cfg', default=os.path.join(HERE, 'cat_touchup.json'))
    p.add_argument('--closed', action='store_true')
    p.add_argument('--face', help='ภาพหน้าแทน face.image (ภาพอารมณ์ กรอบเดียวกับต้นฉบับ)')
    p.add_argument('--atlas', action='store_true', help='รวมทุกวัสดุเป็นภาพเดียว วัสดุเดียว (สายสี่ขา build_quad_meshy อ่านได้แค่แบบนี้)')
    return p.parse_args(argv)


def load(src):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.import_scene.gltf(filepath=src)
    return next(o for o in bpy.data.objects if o.type == 'MESH')


def bounds(me):
    co = np.array([v.co[:] for v in me.vertices])
    return Vector(co.min(0)), Vector(co.max(0))


def frac(v, lo, hi, i):
    return (v[i] - lo[i]) / (hi[i] - lo[i])


def inflate_tail(me, t):
    lo, hi = bounds(me)
    picked = [v for v in me.vertices if frac(v.co, lo, hi, 1) > t['yFrac'] and frac(v.co, lo, hi, 2) > t['zFrac']]
    zs, cxs, cys = tail_axis(picked, t['slices'])
    for v in picked:
        cx, cy = np.interp(v.co.z, zs, cxs), np.interp(v.co.z, zs, cys)  # แกนไล่ต่อเนื่อง ไม่เป็นขั้นตามชั้น
        zf, yf = frac(v.co, lo, hi, 2), frac(v.co, lo, hi, 1)
        # น้ำหนักเริ่ม 0 ที่ขอบส่วนที่เลือกทุกด้าน : ตัดแข็งที่ yFrac เคยทำผิวขาดเป็นวงที่ยอดหาง
        w = min(1.0, (zf - t['zFrac']) / (t['zFull'] - t['zFrac']), (1.0 - zf) / (1.0 - t['zTop']),
                (yf - t['yFrac']) / t['yRamp'])
        k = 1.0 + (t['scale'] - 1.0) * w
        v.co.x = cx + (v.co.x - cx) * k
        v.co.y = cy + (v.co.y - cy) * k
    return len(picked)


def tail_axis(picked, slices):
    """แกนกลางหาง : จุดกลาง (x, y) ของแต่ละชั้นความสูง ที่ความสูงกลางชั้น (ชั้นว่างข้าม)"""
    co = np.array([v.co[:] for v in picked])
    edges = np.linspace(co[:, 2].min(), co[:, 2].max(), slices + 1)
    rows = []
    for z0, z1 in zip(edges[:-1], edges[1:]):
        m = (co[:, 2] >= z0) & (co[:, 2] <= z1)
        if m.any():
            rows.append(((z0 + z1) / 2, co[m, 0].mean(), co[m, 1].mean()))
    return [np.array(c) for c in zip(*rows)]


def fit_axes(pairs):
    """จุดคู่ (probe px → face px) → (s, t) ต่อแกน : face = probe · s + t (least squares แยกแกน x/y)"""
    a = np.array([p[0] for p in pairs], float)
    b = np.array([p[1] for p in pairs], float)
    ca, cb = a.mean(0), b.mean(0)
    s = ((a - ca) * (b - cb)).sum(0) / ((a - ca) ** 2).sum(0)
    return s, cb - s * ca


def face_material(path):
    mat = bpy.data.materials.new('view_face')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.65
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path)
    tex.extension = 'EXTEND'
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    return mat, tex.image.size


def project_face(obj, f, image):
    """maskImage (ถ้ามี) = ภาพที่ใช้ตัดพื้นหลัง แทนภาพที่ฉาย : ภาพหน้าอารมณ์ที่วาดแยกช่อง เงาหัวต่างกันเล็กน้อย
    ถ้าใช้มาสก์ของแต่ละภาพ ชุดหน้าที่ได้ภาพหน้าจะต่างกัน → UV ไม่ตรงกับภาพหลัก (bake.alts ใช้ไม่ได้)"""
    me = obj.data
    lo, hi = bounds(me)
    mat, (iw, ih) = face_material(image)
    me.materials.append(mat)
    s, t = fit_axes(f['pairs'])
    pr = f['probe']
    mask_src = bpy.data.images.load(f['maskImage']) if f.get('maskImage') else mat.node_tree.nodes['Image Texture'].image
    on_cat = cat_mask(mask_src, f['bgDiff'])
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active
    count = 0
    for face in bm.faces:
        if not face_wanted(face, lo, hi, f):
            continue
        uvs = [face_uv(loop.vert.co, pr, s, t, iw, ih) for loop in face.loops]
        if all(inside(on_cat, u) for u in uvs):
            face.material_index = len(me.materials) - 1
            for loop, u in zip(face.loops, uvs):
                loop[uv].uv = u
            count += 1
    bm.to_mesh(me)
    bm.free()
    return count


def cat_mask(img, bg_diff):
    """True = พิกเซลเป็นตัวแมว (ต่างจากสีพื้นหลังที่มุมซ้ายล่างเกิน bg_diff · 0–255) · แถว 0 = ล่างของภาพ (แบบ Blender)"""
    w, h = img.size
    px = np.array(img.pixels[:], np.float32).reshape(h, w, 4)[..., :3] * 255
    return np.abs(px - px[2, 2]).sum(-1) > bg_diff


def inside(mask, u):
    h, w = mask.shape
    x, y = int(u[0] * (w - 1)), int(u[1] * (h - 1))
    return 0 <= x < w and 0 <= y < h and mask[y, x]


def probe_px(p, pr):
    """พิกัดโมเดล → px ภาพหน้าตรงของ head_probe.py (สูตรเดียวกับที่สคริปต์นั้นพิมพ์)"""
    return np.array([((p.x - pr['cx']) / pr['scale'] + 0.5) * pr['px'],
                     ((pr['cz'] - p.z) / pr['scale'] + 0.5) * pr['px']])


def min_facing(f, x, y):
    """ผนังแอ่งตาที่ปั้นตั้งชัน/ใต้เปลือกตา ต้องฉายภาพหน้าด้วย ไม่งั้นค้างสีตาลืมจากภาพข้าง (เส้นขาว จุดชมพูหัวตา ตอนหลับตา)
    ต้องใช้กับทุกภาพหน้า (รวมหน้าหลัก) : ขั้นอบใช้ UV ของต้นทางหลัก ภาพสำรองต่างกันได้แค่ในแผงภาพหน้า"""
    w = f.get('eyeWall')
    if w and any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in w['boxes']):
        return w['minFacing']
    return f['minFacing']


def face_wanted(face, lo, hi, f):
    c = face.calc_center_median()
    x, y = probe_px(c, f['probe'])
    if face.normal.dot(FRONT) < min_facing(f, x, y) or frac(c, lo, hi, 1) > f['frontDepthFrac']:
        return False
    if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in f['exclude']):
        return False
    return f['bandY'][0] <= y <= f['bandY'][1]


def face_uv(p, pr, s, t, iw, ih):
    q = probe_px(p, pr) * s + t
    return (q[0] / iw, 1 - q[1] / ih)


def solid_material(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = [(c / 255) ** 2.2 for c in rgb] + [1.0]
    bsdf.inputs['Roughness'].default_value = 0.65
    return mat


def in_poly(x, y, poly):
    """จุดอยู่ในรูปหลายเหลี่ยม (ยิงเส้นแนวนอน นับจุดตัด)"""
    hit = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def paint_ears(obj, e, pr):
    me = obj.data
    lo, hi = bounds(me)
    me.materials.append(solid_material('ear_pink', e['pink']))
    me.materials.append(solid_material('ear_cream', e['cream']))
    pink, cream = len(me.materials) - 2, len(me.materials) - 1
    zone = [p for p in me.polygons if in_ear_zone(p.center, lo, hi, e, pr)]
    nearest = front_depth(zone, pr, e['cellPx'])
    counts = [0, 0]
    for poly in zone:
        x, y = probe_px(poly.center, pr)
        seen = poly.center.y - nearest[cell(x, y, e['cellPx'])] < e['depthTolM']  # ผิวหลังหู (ถูกหูบัง) ไม่นับ
        inner = seen and poly.normal.dot(FRONT) > e['minFacing'] and any(in_poly(x, y, p) for p in e['inner'])
        poly.material_index = pink if inner else cream
        counts[0 if inner else 1] += 1
    return counts


def in_ear_zone(c, lo, hi, e, pr):
    x, y = probe_px(c, pr)
    return frac(c, lo, hi, 1) <= e['depthFrac'] and any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in e['zones'])


def cell(x, y, size):
    return int(x // size), int(y // size)


def front_depth(polys, pr, size):
    """ระยะ y ที่ใกล้กล้องหน้าที่สุดต่อช่องภาพ (z-buffer หยาบ)"""
    near = {}
    for p in polys:
        k = cell(*probe_px(p.center, pr), size)
        near[k] = min(near.get(k, p.center.y), p.center.y)
    return near


def main():
    a = parse()
    with open(a.cfg, encoding='utf-8') as fp:
        cfg = json.load(fp)
    obj = load(a.src)
    n_tail = inflate_tail(obj.data, cfg['tail']) if 'tail' in cfg else 0  # ไม่มีหัวข้อ = ข้าม (เจ้าส้ม : หางพอแล้ว)
    image = a.face or cfg['face']['imageClosed' if a.closed else 'image']
    n_face = project_face(obj, cfg['face'], image)
    n_ear = paint_ears(obj, cfg['ears'], cfg['face']['probe']) if 'ears' in cfg else (0, 0)
    if a.atlas:
        obj = atlas_pack.build([obj], 'cat')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=a.out, use_selection=True, export_format='GLB', export_image_format='JPEG')
    print(f'CAT_TOUCHUP out={a.out} tailVerts={n_tail} faceTris={n_face} earPink={n_ear[0]} earCream={n_ear[1]}')


main()
