# รวมภาพที่ฉายไว้ทุกชิ้นเป็น texture แผ่นเดียว แล้วรวม mesh เป็นวัตถุเดียว วัสดุเดียว (ใช้ใน project_views.py · station_assemble.py)
# ต้องวัสดุเดียว : ตัววาดของประกอบในเกม (villageGeometry.mergeHouse) ใช้แค่วัสดุแรกของโมเดล · วัสดุสีล้วน (หลังคาแผ่นลอน) ถูกวาดเป็นช่องสีในภาพรวม
import math

import bmesh
import bpy
import numpy as np

ATLAS_PX = 2048
PAD_PX = 3  # ระยะกันสีจากช่องข้างเคียงไหลเข้ามา
ROUGHNESS = 0.65
SOLID_PX = 16  # ขนาดภาพของวัสดุสีล้วนก่อนวางลงภาพรวม


def view_images(objs):
    seen = []
    for o in objs:
        for m in o.data.materials:
            img = _image_of(m)
            if img and img not in seen:
                seen.append(img)
    return seen


def _image_of(mat):
    if not mat or not mat.use_nodes:
        return None
    return next((n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE'), None)


def _srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def solid_to_image(mat):
    """วัสดุที่ไม่มีภาพ → ภาพสีล้วน (สีพื้นของ Principled) ต่อเข้า node ให้ remap จับได้เหมือนวัสดุภาพ"""
    nodes = mat.node_tree.nodes
    rgb = nodes['Principled BSDF'].inputs['Base Color'].default_value
    img = bpy.data.images.new(mat.name + '_solid', SOLID_PX, SOLID_PX)
    img.pixels = [v for _ in range(SOLID_PX * SOLID_PX) for v in (_srgb(rgb[0]), _srgb(rgb[1]), _srgb(rgb[2]), 1.0)]
    img.pack()  # ภาพที่สร้างเอง ถ้าไม่แพ็ก copy() ตอนวางลงภาพรวมจะได้ภาพเปล่า (สีดำ)
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = img


def pack(images):
    """วางภาพลงตาราง cols × rows ช่องเท่ากัน · คืน (ภาพรวม, {ภาพ: (u0, v0, du, dv)})"""
    cols = math.ceil(math.sqrt(len(images)))
    rows = math.ceil(len(images) / cols)
    cw, ch = ATLAS_PX // cols, ATLAS_PX // rows
    buf = np.zeros((ATLAS_PX, ATLAS_PX, 4), np.float32)
    rects = {}
    for i, img in enumerate(images):
        c, r = i % cols, i // cols
        cell = img.copy()
        cell.scale(cw - 2 * PAD_PX, ch - 2 * PAD_PX)
        px = np.array(cell.pixels[:], np.float32).reshape(ch - 2 * PAD_PX, cw - 2 * PAD_PX, 4)
        x0, y0 = c * cw + PAD_PX, r * ch + PAD_PX
        buf[y0:y0 + px.shape[0], x0:x0 + px.shape[1]] = px
        buf[y0:y0 + px.shape[0], x0:x0 + px.shape[1], 3] = 1
        bpy.data.images.remove(cell)
        rects[img] = (x0 / ATLAS_PX, y0 / ATLAS_PX, px.shape[1] / ATLAS_PX, px.shape[0] / ATLAS_PX)
    atlas = bpy.data.images.new('atlas', ATLAS_PX, ATLAS_PX)
    atlas.pixels = buf.ravel()
    return atlas, rects


def atlas_material(atlas):
    mat = bpy.data.materials.new('atlas')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes['Principled BSDF'].inputs['Roughness'].default_value = ROUGHNESS
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = atlas
    mat.node_tree.links.new(tex.outputs['Color'], nodes['Principled BSDF'].inputs['Base Color'])
    return mat


def remap(obj, rects, mat):
    """UV เดิม (0..1 ต่อภาพ) → ช่องของภาพนั้นในภาพรวม · วัสดุที่ไม่ใช่ภาพฉาย (เช่น หลังคา) คงไว้"""
    me = obj.data
    old = list(me.materials)
    keep = [m for m in old if _image_of(m) not in rects]
    bm = bmesh.new()
    bm.from_mesh(me)  # อ่านก่อนล้างวัสดุ : materials.clear() รีเซ็ตเลขวัสดุของทุกหน้าเป็น 0
    me.materials.clear()
    for m in [mat, *keep]:
        me.materials.append(m)
    solid_uv = None if bm.loops.layers.uv.active else True  # ไม่มี UV (ชิ้นสร้างจากโค้ด) = ทุกจุดชี้กลางช่องสี
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        src = old[f.material_index] if f.material_index < len(old) else None
        rect = rects.get(_image_of(src))
        f.material_index = 0 if rect else 1 + keep.index(src)
        for loop in (f.loops if rect else ()):
            u, v = loop[uv].uv if solid_uv is None else (0.5, 0.5)
            loop[uv].uv = (rect[0] + min(max(u, 0), 1) * rect[2], rect[1] + min(max(v, 0), 1) * rect[3])
    bm.to_mesh(me)
    bm.free()


def merge(objs, name):
    """รวมหลายวัตถุเป็นวัตถุเดียว (ค่าตำแหน่ง/ขนาด/การหมุนถูกฝังลงจุดยอด) · วัสดุชื่อเดียวกันใช้ช่องเดียวกัน"""
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        local = [m for m in me.materials]
        for m in local:
            if m not in mats:
                mats.append(m)
        for p in me.polygons:
            p.material_index = mats.index(local[p.material_index])
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    out = bpy.data.meshes.new(name)
    bm.to_mesh(out)
    bm.free()
    for m in mats:
        out.materials.append(m)
    obj = bpy.data.objects.new(name, out)
    bpy.context.scene.collection.objects.link(obj)
    for o in objs:
        bpy.data.objects.remove(o)
    return obj


def build(objs, name):
    for o in objs:
        for m in o.data.materials:
            if m and m.use_nodes and _image_of(m) is None:
                solid_to_image(m)
    images = view_images(objs)
    atlas, rects = pack(images)
    mat = atlas_material(atlas)
    mat.use_backface_culling = all(m.use_backface_culling for o in objs for m in o.data.materials if m)
    for o in objs:
        remap(o, rects, mat)
    return merge(objs, name)
