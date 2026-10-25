"""ภาพตรวจสัตว์สี่ขา Meshy จาก glb ที่ส่งออกแล้ว (Blender Workbench สีตาม texture)
แถว = คลิป × เฟรม (preview.fractions) · คอลัมน์ = มุมกล้อง (preview.views : หน้า / ข้าง / มุมเกม yaw -30° เฉียงลง)
รัน : blender.exe -b --python tools/blender/quad_meshy_preview.py -- <ตัว> [idle walk]   (ตัว = quad_meshy_<ตัว>.json · ไม่ระบุคลิป = ทุกคลิปใน clips.order)
ผล : <preview.dir>/<ตัว>_preview.png + ภาพย่อยต่อคลิป <preview.dir>/<ตัว>_<คลิป>.png (เขียนทับทุกครั้ง)
ภาพย่อยต่อช่องอยู่ใน <preview.dir>/parts/ (เขียนทับ ไม่ลบ)"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CAM_DIST = 12.0


def _floor(pv):
    h = pv['floorSizeM'] / 2
    me = bpy.data.meshes.new('floor')
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    mat = bpy.data.materials.new('floor')
    mat.diffuse_color = pv['floorRGBA']
    me.materials.append(mat)
    bpy.context.scene.collection.objects.link(bpy.data.objects.new('floor', me))


def _scene(pv):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = pv['cell']
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'TEXTURE'
    sc.display.shading.show_cavity = True
    sc.display.render_aa = '8'
    sc.world = bpy.data.worlds.new('w')
    sc.world.color = pv['skyRGB']
    cam = bpy.data.cameras.new('cam')
    cam.type, cam.ortho_scale, cam.clip_end = 'ORTHO', pv['scale'], 50
    co = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(co)
    sc.camera = co
    _floor(pv)
    return sc, co


def _load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    arm = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    if arm.animation_data is None:
        arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(tr)
    return arm


def _use_clip(arm, name):
    act = next((a for a in bpy.data.actions if a.name == name or a.name.startswith(name + '_')), None)
    if act is None:
        return None
    for pb in arm.pose.bones:  # ช่องที่คลิปไม่มี (ค่าคงที่ถูกตัดตอนส่งออก) = ท่าพัก เหมือน three.js
        pb.matrix_basis.identity()
    arm.animation_data.action = act
    if getattr(act, 'slots', None) and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    return act


def _shot(sc, co, center, view, path):
    """center = จุดเล็งแบบ glTF (x, y ขึ้น, z หน้า) → Blender (x, -z, y)"""
    rx, rz = math.radians(view['tiltDeg']), math.radians(view['turnDeg'])
    c = (center[0], -center[2], center[1])
    d = (math.sin(rz) * math.sin(rx), -math.cos(rz) * math.sin(rx), math.cos(rx))
    co.location = [c[i] + d[i] * CAM_DIST for i in range(3)]
    co.rotation_euler = (rx, 0.0, rz)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _grid(paths, cols, out):
    imgs = [bpy.data.images.load(p, check_existing=False) for p in paths]
    w, h = imgs[0].size
    px = [np.array(i.pixels[:], dtype=np.float32).reshape(h, w, 4) for i in imgs]
    rows = [np.concatenate(px[r:r + cols], axis=1) for r in range(0, len(px), cols)]
    big = bpy.data.images.new('grid', w * cols, h * len(rows), alpha=True)
    big.pixels.foreach_set(np.concatenate(rows[::-1], axis=0).ravel())
    big.filepath_raw, big.file_format = out, 'PNG'
    big.save()
    for i in imgs:
        bpy.data.images.remove(i)
    bpy.data.images.remove(big)


def _shoot_clip(sc, co, pv, act, key, clip, out_dir):
    f0, f1 = act.frame_range
    paths = []
    for frac in pv['fractions']:
        sc.frame_set(int(round(f0 + (f1 - f0) * frac)))
        for vi, view in enumerate(pv['views']):
            path = os.path.join(out_dir, 'parts', '%s_%s_%03d_%d.png' % (key, clip, int(frac * 100), vi))
            _shot(sc, co, pv['center'], view, path)
            paths.append(path)
    _grid(paths, len(pv['views']), os.path.join(out_dir, '%s_%s.png' % (key, clip)))
    return paths


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    key = argv[0] if argv else 'boar'
    with open(os.path.join(HERE, 'quad_meshy_%s.json' % key), encoding='utf-8') as f:
        cfg = json.load(f)
    pv = cfg['preview']
    out_dir = os.path.join(ROOT, pv['dir'])
    os.makedirs(os.path.join(out_dir, 'parts'), exist_ok=True)
    sc, co = _scene(pv)
    arm = _load(os.path.join(ROOT, cfg['out']))
    paths = []
    for clip in argv[1:] or cfg['clips']['order']:
        act = _use_clip(arm, clip)
        if act is None:
            print('QUAD_PREVIEW ไม่พบคลิป', key, clip)
            continue
        paths += _shoot_clip(sc, co, pv, act, key, clip, out_dir)
    out = os.path.join(out_dir, '%s_preview.png' % key)
    _grid(paths, len(pv['views']), out)
    print('QUAD_PREVIEW', out)


main()
