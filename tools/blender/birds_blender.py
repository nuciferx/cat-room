"""ส่วนที่แตะ Blender ของนก : Part → เมชเดียว (UV ต่อมุม · กลุ่มจุดยอดตามกระดูก · วัสดุ 2 ชิ้น) · โครงกระดูก · ภาพ texture
· ใส่คีย์ท่าทุกเฟรม (matrix_basis จาก birds_pose) · ส่งออก glb (ท่าแยกต่อ action · texture JPEG)
พิกัดนก (glTF) → Blender : (x, y, z) ↦ (x, -z, y)"""
import os

import bpy
import numpy as np
from mathutils import Matrix

from birds_pose import basis_matrices, fk


def to_bl(p):
    return (float(p[0]), float(-p[2]), float(p[1]))


def reset_scene(fps):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = fps
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)


def _image(name, rgb, out_png):
    h, w, _ = rgb.shape
    img = bpy.data.images.new(name, w, h, alpha=False)
    rgba = np.concatenate([rgb, np.ones((h, w, 1))], axis=2).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = out_png
    img.file_format = 'PNG'
    img.save()
    img.pack()
    return img


def make_materials(name, mcfg, rgb, out_png):
    main = bpy.data.materials.new(name + '_feather')
    main.use_nodes = True
    nt = main.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = _image(name + '_tex', rgb, out_png)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = mcfg['roughness']
    bsdf.inputs['Metallic'].default_value = 0.0
    eye = bpy.data.materials.new(name + '_eye')
    eye.use_nodes = True
    eb = eye.node_tree.nodes['Principled BSDF']
    eb.inputs['Base Color'].default_value = tuple(mcfg['eyeLinear']) + (1.0,)
    eb.inputs['Roughness'].default_value = mcfg['eyeRoughness']
    return [main, eye]


def _merge(parts):
    verts, faces, uvs, mats, weights = [], [], [], [], []
    for part in parts:
        base = len(verts)
        verts += [to_bl(v) for v in part.verts]
        weights += part.weights
        faces += [tuple(base + i for i in f) for f in part.faces]
        uvs += list(part.uvs)
        mats += [part.material] * len(part.faces)
    return verts, faces, uvs, mats, weights


def make_mesh(name, parts, materials):
    verts, faces, uvs, mats, weights = _merge(parts)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    flat = [c for uv in uvs for corner in uv for c in corner]
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', flat)
    for m in materials:
        me.materials.append(m)
    me.polygons.foreach_set('material_index', mats)
    me.polygons.foreach_set('use_smooth', [True] * len(faces))
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj, weights


def make_armature(name, bones):
    arm = bpy.data.armatures.new(name + '_arm')
    obj = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    for bname, parent, head, tail in bones:
        eb = arm.edit_bones.new(bname)
        eb.head, eb.tail, eb.roll = to_bl(head), to_bl(tail), 0.0
        if parent:
            eb.parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def skin(mesh_obj, arm_obj, weights):
    groups = {}
    for vi, w in enumerate(weights):
        for bone, val in w.items():
            if val <= 1e-4:
                continue
            if bone not in groups:
                groups[bone] = mesh_obj.vertex_groups.new(name=bone)
            groups[bone].add([vi], float(val), 'REPLACE')
    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = arm_obj


def rest_matrices(arm_obj):
    return {b.name: np.array(b.matrix_local) for b in arm_obj.data.bones}


def _key_bone(pb, m, last, is_root, f):
    """ใส่คีย์กระดูกเดียว · quaternion ซีกเดียวกับเฟรมก่อน (กันหมุนกลับด้านตอนต่อคีย์) · root มีตำแหน่งด้วย"""
    pb.rotation_mode = 'QUATERNION'
    mat = Matrix(m.tolist())
    q = mat.to_quaternion()
    if pb.name in last and last[pb.name].dot(q) < 0:
        q.negate()
    last[pb.name] = q.copy()
    pb.rotation_quaternion = q
    pb.keyframe_insert('rotation_quaternion', frame=f)
    if is_root:
        pb.location = mat.to_translation()
        pb.keyframe_insert('location', frame=f)


def bake_clip(arm_obj, rig, rest_bl, name, frames, pose_at, fps):
    """ใส่คีย์ทุกเฟรม 0..frames (เฟรมสุดท้ายของท่าวน = เฟรมแรก) · คืน action"""
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm_obj.animation_data.action = act
    last = {}
    for f in range(frames + 1):
        basis = basis_matrices(rig, fk(rig, pose_at(f / fps)), rest_bl)
        for bname, m in basis.items():
            _key_bone(arm_obj.pose.bones[bname], m, last, rig.parent[bname] is None, f)
    return act


def clear_pose(arm_obj):
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)


def export_glb(path, objs, quality):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=False, export_normals=True, export_texcoords=True,
                              export_materials='EXPORT', export_image_format='JPEG', export_jpeg_quality=quality,
                              export_skins=True, export_animations=True, export_animation_mode='ACTIONS',
                              export_frame_range=False, export_optimize_animation_size=True,
                              export_cameras=False, export_lights=False)
