# ภาพตรวจโมเดล 8 ทิศ (S SW W NW N NE E SE ตามภาพอ้างอิง) เรียงเป็นตาราง 4×2 ภาพเดียว
#   blender -b --factory-startup --python-exit-code 1 -P tools/ai3d/render_views.py -- <in.glb> <out.png> [--mode TEXTURE|SINGLE] [--px 400] [--pitch 12]
# แกน (Blender หลังนำเข้า glTF) : หน้าวัตถุหัน −Y · S = กล้องอยู่หน้าวัตถุ · W = แมวหันซ้ายของรูป (กล้องอยู่ข้างขวาของตัว)
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

# ทิศ → มุมกล้องรอบแกน Z (องศา · 0 = กล้องอยู่ −Y มองหน้าวัตถุ · บวก = หมุนทวนเข็มมองจากบน)
DIRS = (('S', 0), ('SW', 45), ('W', 90), ('NW', 135), ('N', 180), ('NE', -135), ('E', -90), ('SE', -45))
COLS = 4
MARGIN = 1.15


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:]
    p = argparse.ArgumentParser()
    p.add_argument('src')
    p.add_argument('out')
    p.add_argument('--mode', default='TEXTURE', choices=('TEXTURE', 'SINGLE'))
    p.add_argument('--px', type=int, default=400)
    p.add_argument('--pitch', type=float, default=12.0)
    return p.parse_args(argv)


def load(src):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.import_scene.gltf(filepath=src)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return (lo + hi) / 2, (hi - lo).length


def setup(args, size):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = args.mode
    sc.render.resolution_x = sc.render.resolution_y = args.px
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new('w')
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = size * MARGIN
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def aim(cam, center, dist, yaw, pitch):
    y, p = math.radians(yaw), math.radians(pitch)
    off = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p)))
    cam.location = center + off * dist
    cam.rotation_euler = (-off).to_track_quat('-Z', 'Y').to_euler()


def render_all(args, cam, center, size, tmp):
    paths = []
    for name, yaw in DIRS:
        aim(cam, center, size * 3, yaw, args.pitch)
        bpy.context.scene.render.filepath = os.path.join(tmp, name + '.png')
        bpy.ops.render.render(write_still=True)
        paths.append(bpy.context.scene.render.filepath)
    return paths


def grid(paths, out, px):
    rows = (len(paths) + COLS - 1) // COLS
    sheet = bpy.data.images.new('sheet', COLS * px, rows * px)
    buf = [0.0] * (COLS * px * rows * px * 4)
    for i, p in enumerate(paths):
        img = bpy.data.images.load(p)
        src = list(img.pixels)
        cx, cy = (i % COLS) * px, (rows - 1 - i // COLS) * px
        for r in range(px):
            d = ((cy + r) * COLS * px + cx) * 4
            buf[d:d + px * 4] = src[r * px * 4:(r + 1) * px * 4]
    sheet.pixels = buf
    sheet.filepath_raw = out
    sheet.file_format = 'PNG'
    sheet.save()


def main():
    args = parse()
    args.out = os.path.abspath(args.out)  # path สัมพัทธ์ : image.save ของ Blender ไม่เขียนลงโฟลเดอร์ปัจจุบัน
    center, size = load(args.src)
    cam = setup(args, size)
    tmp = os.path.splitext(args.out)[0] + '_views'
    os.makedirs(tmp, exist_ok=True)
    grid(render_all(args, cam, center, size, tmp), args.out, args.px)
    print('RENDER_VIEWS', args.out)


main()
