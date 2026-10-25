# ลงสีโมเดลจาก AI ด้วยการฉายรูป 4 ด้าน (หน้า ซ้าย หลัง ขวา) + มุมบน (top.png ถ้ามี) ลงบนผิว : แต่ละหน้าใช้รูปของด้านที่หันเข้าหามากที่สุด · ไม่ต้องอบ texture
#   blender -b --factory-startup --python-exit-code 1 -P tools/ai3d/project_views.py -- <in.glb> <โฟลเดอร์รูป> <out.glb> [--height 0.95] [--tris 4000]
# โฟลเดอร์รูป = ผลของ tools/ai3d/views_cutout.py (front/left/back/right.png ครอปชิดตัววัตถุ)
# top.png = มองลงตรง ๆ ด้านหน้าวัตถุอยู่ล่างของรูป
# แกน (Blender) : หน้าวัตถุหัน −Y · ซ้าย = กล้องอยู่ −X (ด้านหน้าอยู่ขวามือในรูป) · ขวา = กล้องอยู่ +X
import argparse
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atlas_pack  # noqa: E402

# มุม → (ทิศที่ผิวหันออก, แกนแนวนอนของรูปจากซ้ายไปขวา)
VIEWS = {
    'front': (Vector((0, -1, 0)), Vector((1, 0, 0))),
    'back': (Vector((0, 1, 0)), Vector((-1, 0, 0))),
    'left': (Vector((-1, 0, 0)), Vector((0, -1, 0))),
    'right': (Vector((1, 0, 0)), Vector((0, 1, 0))),
}
ROUGHNESS = 0.65
TOP_VIEW_NZ = 0.35  # มี top.png : ผิวที่หันขึ้นเกินนี้ใช้รูปมุมบน
TOP_NZ = 0.8  # ผิวที่หันขึ้นเกินนี้ (ฝาบน) ไม่มีรูปมุมบน : ทั้งหน้าใช้สีจุดเดียว ไม่ยืดเป็นริ้ว
TOP_SAMPLE_DROP = 0.04  # จุดสีของผิวบน = รูปด้านข้างที่ความสูงต่ำกว่าผิวนั้น (สัดส่วนความสูงวัตถุ) พ้นขอบที่มักสว่างจ้า


def parse():
    p = argparse.ArgumentParser()
    p.add_argument('src')
    p.add_argument('views')
    p.add_argument('out')
    p.add_argument('--height', type=float, default=0, help='ความสูงจริง (ม.) · 0 = คงขนาดเดิม')
    p.add_argument('--tris', type=int, default=0, help='จำนวนสามเหลี่ยมเป้าหมาย · 0 = ไม่ลด')
    p.add_argument('--atlas', type=int, default=1, help='1 = รวมภาพ 4 ด้านเป็นแผ่นเดียว วัสดุเดียว (ใช้ในเกมได้ตรง) · 0 = แยกวัสดุต่อด้าน (ชิ้นที่จะไปประกอบต่อ)')
    return p.parse_args(sys.argv[sys.argv.index('--') + 1:])


def import_mesh(path):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bm = bmesh.new()
    for o in meshes:
        part = o.data.copy()
        part.transform(o.matrix_world)
        bm.from_mesh(part)
    me = bpy.data.meshes.new('ai_mesh')
    bm.to_mesh(me)
    bm.free()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    obj = bpy.data.objects.new('ai_model', me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def normalize(obj, height):
    """วางกลางแกน X/Y ฐานที่ z = 0 · ปรับให้สูงตามจริง"""
    me = obj.data
    lo = Vector([min(v.co[i] for v in me.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in me.vertices) for i in range(3)])
    s = height / (hi.z - lo.z) if height else 1.0
    shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in me.vertices:
        v.co = (v.co - shift) * s


def decimate(obj, tris):
    if not tris or len(obj.data.polygons) <= tris:
        return
    mod = obj.modifiers.new('dec', 'DECIMATE')
    mod.ratio = tris / len(obj.data.polygons)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.remove(mod)
    old = obj.data
    obj.data = me
    bpy.data.meshes.remove(old)


def make_material(name, image_path):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True  # ผิวปิดด้านเดียว (atlas_pack คงค่านี้ไว้ ถ้าไม่มีชิ้นสองด้านอย่างแผ่นหลังคาปนมา)
    nodes = mat.node_tree.nodes
    bsdf = nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = ROUGHNESS
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(image_path)
    tex.extension = 'EXTEND'
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    return mat


def best_view(normal):
    flat = Vector((normal.x, normal.y, 0))
    if flat.length < 1e-4:
        return 'front'
    return max(VIEWS, key=lambda k: VIEWS[k][0].dot(flat))


def top_uv(p, lo, hi):
    return ((p.x - lo.x) / (hi.x - lo.x), (p.y - lo.y) / (hi.y - lo.y))


def project(obj, views_dir):
    me = obj.data
    names = [k for k in [*VIEWS, 'top'] if os.path.exists(os.path.join(views_dir, k + '.png'))]
    for k in names:
        me.materials.append(make_material('view_' + k, os.path.join(views_dir, k + '.png')))
    lo = Vector([min(v.co[i] for v in me.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in me.vertices) for i in range(3)])
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        if 'top' in names and f.normal.z > TOP_VIEW_NZ:
            f.material_index = names.index('top')
            for loop in f.loops:
                loop[uv].uv = top_uv(loop.vert.co, lo, hi)
            continue
        k = best_view(f.normal)
        k = k if k in names else names[0]
        f.material_index = names.index(k)
        axis = VIEWS[k][1]
        span = abs(axis.dot(hi - lo))
        start = min(axis.dot(lo), axis.dot(hi))
        top = f.normal.z > TOP_NZ
        c = f.calc_center_median()
        for loop in f.loops:
            p = c - Vector((0, 0, TOP_SAMPLE_DROP * (hi.z - lo.z))) if top else loop.vert.co
            loop[uv].uv = ((axis.dot(p) - start) / span, max(0.0, (p.z - lo.z) / (hi.z - lo.z)))
    bm.to_mesh(me)
    bm.free()


def main():
    a = parse()
    obj = import_mesh(a.src)
    normalize(obj, a.height)
    decimate(obj, a.tris)
    project(obj, a.views)
    if a.atlas:
        obj = atlas_pack.build([obj], 'ai_model')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=a.out, use_selection=True, export_format='GLB', export_image_format='JPEG')
    dims = obj.dimensions
    print(f'PROJECTED out={a.out} tris={sum(len(p.vertices) - 2 for p in obj.data.polygons)} size={dims.x:.2f}x{dims.y:.2f}x{dims.z:.2f}')


if __name__ == '__main__':
    main()
