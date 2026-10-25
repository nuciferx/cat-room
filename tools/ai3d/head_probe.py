# ภาพหน้าตรงของหัว (ทรงเปล่า + cavity) พร้อมสูตรแปลง px ↔ พิกัดโมเดล ไว้หาจุดตา/จมูก/หูที่ปั้นไว้จริง
#   blender -b --factory-startup --python-exit-code 1 -P tools/ai3d/head_probe.py -- <in.glb> <out.png> [--px 1024] [--zc 0.78] [--span 0.55] [--mode SINGLE|TEXTURE]
# zc = ความสูงกลางภาพ (สัดส่วนความสูงโมเดล) · span = ความกว้างภาพ (สัดส่วนความสูงโมเดล)
# พิมพ์ HEAD_PROBE cx cz scale px : x = cx + (px_x / px − 0.5) · scale · z = cz − (px_y / px − 0.5) · scale (หน้าแมวหัน −Y)
import argparse
import sys

import bpy
import numpy as np
from mathutils import Vector


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:]
    p = argparse.ArgumentParser()
    p.add_argument('src')
    p.add_argument('out')
    p.add_argument('--px', type=int, default=1024)
    p.add_argument('--zc', type=float, default=0.78)
    p.add_argument('--span', type=float, default=0.55)
    p.add_argument('--mode', default='SINGLE', choices=('SINGLE', 'TEXTURE'))
    return p.parse_args(argv)


def main():
    a = parse()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.import_scene.gltf(filepath=a.src)
    obj = next(o for o in bpy.data.objects if o.type == 'MESH')
    co = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
    lo, hi = co.min(0), co.max(0)
    h = hi[2] - lo[2]
    cx, cz, scale = (lo[0] + hi[0]) / 2, lo[2] + a.zc * h, a.span * h
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = a.mode
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = sc.render.resolution_y = a.px
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = scale
    cam.location = Vector((cx, lo[1] - 1.0, cz))
    cam.rotation_euler = (1.5707963, 0, 0)
    sc.collection.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = a.out
    bpy.ops.render.render(write_still=True)
    print(f'HEAD_PROBE cx={cx:.5f} cz={cz:.5f} scale={scale:.5f} px={a.px} lo={lo.tolist()} hi={hi.tolist()}')


main()
