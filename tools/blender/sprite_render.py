"""ภาพ 2.5D ของมุ่ยจากโมเดล 3D : ทุกท่า × 8 ทิศ ทีละเฟรม พื้นโปร่งใส (PNG RGBA)
รัน : blender -b --factory-startup --python-exit-code 1 -P tools/blender/sprite_render.py -- [ค่า tools/blender/sprite_cat.json] [ท่า ...]
ผล : <outDir>/<ท่า>_<ทิศ>/0000.png … ขนาด renderPx (Krita ย่อเป็น sizePx และรวมแอนิเมชันต่อ : tools/krita/mui_sprites.py)
ลุคภาพวาด (สีขั้น + เส้นขอบ) : sprite_toon.py ตามหัวข้อ toon
กล้อง orthographic ระยะคงที่ หมุนรอบตัวตามทิศ แสงหมุนตามกล้อง → ทุกภาพขนาดแมวและทิศแสงเท่ากัน"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sprite_toon  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))


def load_cfg(argv):
    path = argv[0] if argv and argv[0].endswith('.json') else os.path.join(HERE, 'sprite_cat.json')
    with open(path, encoding='utf-8') as f:
        cfg = json.load(f)
    clips = [a for a in argv if not a.endswith('.json')] or cfg['clips']
    return cfg, clips


def load_model(path, src_fps):
    """ตัวนำเข้า glTF แปลงวินาทีเป็นเฟรมด้วย fps ของฉากตอนนำเข้า → ตั้งก่อน"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = src_fps
    bpy.ops.import_scene.gltf(filepath=path)
    return next(o for o in bpy.data.objects if o.type == 'ARMATURE')


def setup_scene(cfg):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = cfg['renderPx']
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('sprite_world')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[1].default_value = cfg['light']['worldStrength']
    sc.world = world
    rig = bpy.data.objects.new('sprite_rig', None)  # กล้อง + แดดเป็นลูก หมุน rig = หมุนทิศ
    sc.collection.objects.link(rig)
    cam = bpy.data.objects.new('sprite_cam', bpy.data.cameras.new('sprite_cam'))
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = cfg['camera']['orthoM']
    sun = bpy.data.objects.new('sprite_sun', bpy.data.lights.new('sprite_sun', 'SUN'))
    sun.data.energy = cfg['light']['sunEnergy']
    for o in (cam, sun):
        sc.collection.objects.link(o)
        o.parent = rig
    sc.camera = cam
    place(cam, sun, cfg)
    return rig


def place(cam, sun, cfg):
    """กล้องอยู่หน้าแมว (Blender −Y) ก้ม elevDeg เล็งจุด targetY · แดดเฉียงตาม sunSideDeg"""
    cc, lc = cfg['camera'], cfg['light']
    e = math.radians(cc['elevDeg'])
    target = Vector((0.0, 0.0, cc['targetY']))
    cam.location = target + Vector((0.0, -math.cos(e), math.sin(e))) * cc['distM']
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sun.rotation_euler = (math.radians(90 - lc['sunElevDeg']), 0.0, math.radians(lc['sunSideDeg']))


def use_action(arm, name):
    act = bpy.data.actions.get(name)
    if act is None:
        return None
    arm.animation_data.action = act
    slots = getattr(arm.animation_data, 'action_suitable_slots', None)
    if slots:
        arm.animation_data.action_slot = slots[0]
    return act


def frame_times(act, src_fps, fps):
    """เฟรมต้นทาง (ทศนิยมได้) ที่ fps ปลายทาง · ท่าวน = ไม่เอาเฟรมสุดท้ายซ้ำกับเฟรมแรก"""
    f0, f1 = act.frame_range
    n = max(1, round((f1 - f0) / src_fps * fps))
    return [f0 + (f1 - f0) * k / n for k in range(n)]


def render_clip(arm, rig, clip, cfg, out_dir):
    act = use_action(arm, clip)
    if act is None:
        print('SPRITE skip (ไม่มีท่า)', clip)
        return 0
    sc = bpy.context.scene
    times = frame_times(act, sc.render.fps, cfg['fps'])
    for d, deg in cfg['dirs'].items():
        rig.rotation_euler = (0.0, 0.0, math.radians(deg))
        folder = os.path.join(out_dir, '%s_%s' % (clip, d))
        os.makedirs(folder, exist_ok=True)
        for k, t in enumerate(times):
            sc.frame_set(int(t), subframe=t - int(t))
            sc.render.filepath = os.path.join(folder, '%04d.png' % k)
            bpy.ops.render.render(write_still=True)
    return len(times)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    cfg, clips = load_cfg(argv)
    arm = load_model(os.path.join(ROOT, cfg['model']), cfg['srcFps'])
    rig = setup_scene(cfg)
    if cfg.get('toon'):
        sprite_toon.apply(cfg['toon'])
    out_dir = os.path.join(ROOT, cfg['outDir'])
    counts = {c: render_clip(arm, rig, c, cfg, out_dir) for c in clips}
    print('SPRITE_DONE', json.dumps({'out': cfg['outDir'], 'frames': counts}))


main()
