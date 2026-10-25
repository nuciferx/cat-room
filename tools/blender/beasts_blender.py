"""ส่วนที่แตะ Blender ของสัตว์สี่ขา : วัสดุ (ขน texture + ตา) · ใส่คีย์ท่าทุกเฟรม (หมุน + ตำแหน่ง root + ขนาด hackles) · ส่งออก glb
เมช กระดูก skin และฉากใช้ของชุดนก (birds_blender) · พิกัดสัตว์ (glTF) → Blender : (x, y, z) ↦ (x, -z, y)"""
import os

import bpy
from mathutils import Matrix

import birds_blender as bb
from beasts_rig import SCALED_BONES, fk
from birds_pose import basis_matrices


def make_materials(name, mcfg, rgb, out_png):
    main = bpy.data.materials.new(name + '_hair')
    main.use_nodes = True
    nt = main.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bb._image(name + '_tex', rgb, out_png)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = mcfg['roughness']
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Specular IOR Level'].default_value = mcfg['specular']  # ขนด้าน : ลดแสงสะท้อน (ส่งออกเป็น KHR_materials_specular)
    eye = bpy.data.materials.new(name + '_eye')
    eye.use_nodes = True
    eb = eye.node_tree.nodes['Principled BSDF']
    eb.inputs['Base Color'].default_value = tuple(mcfg['eyeLinear']) + (1.0,)
    eb.inputs['Roughness'].default_value = mcfg['eyeRoughness']
    return [main, eye]


def _key_bone(pb, m, last, is_root, f):
    """คีย์กระดูกเดียว : quaternion ซีกเดียวกับเฟรมก่อน · root มีตำแหน่ง · กระดูกใน SCALED_BONES มีขนาด"""
    pb.rotation_mode = 'QUATERNION'
    loc, q, sca = Matrix(m.tolist()).decompose()
    if pb.name in last and last[pb.name].dot(q) < 0:
        q.negate()
    last[pb.name] = q.copy()
    pb.rotation_quaternion = q
    pb.keyframe_insert('rotation_quaternion', frame=f)
    if is_root:
        pb.location = loc
        pb.keyframe_insert('location', frame=f)
    if pb.name in SCALED_BONES:
        pb.scale = sca
        pb.keyframe_insert('scale', frame=f)


def bake_clip(arm_obj, rig, rest_bl, name, frames, pose_at, fps, only=None):
    """คีย์ทุกเฟรม 0..frames · only = ใส่คีย์เฉพาะกระดูกเหล่านี้ (คลิปซ้อน เช่น wag) · คืน (action, [Pose ทุกเฟรม])"""
    if arm_obj.animation_data is None:
        arm_obj.animation_data_create()
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm_obj.animation_data.action = act
    last, poses = {}, []
    for f in range(frames + 1):
        pose = pose_at(f / fps)
        basis = basis_matrices(rig, fk(rig, pose), rest_bl)
        poses.append(pose)
        for bname in (only or rig.order):
            _key_bone(arm_obj.pose.bones[bname], basis[bname], last, rig.parent[bname] is None, f)
    return act, poses


def clear_pose(arm_obj):
    bb.clear_pose(arm_obj)
    for pb in arm_obj.pose.bones:
        pb.scale = (1, 1, 1)


def export_glb(path, objs, quality, frame_step):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=False, export_normals=True, export_texcoords=True,
                              export_materials='EXPORT', export_image_format='JPEG', export_jpeg_quality=quality,
                              export_skins=True, export_animations=True, export_animation_mode='ACTIONS',
                              export_frame_range=False, export_frame_step=frame_step,
                              export_optimize_animation_size=True, export_optimize_animation_keep_anim_armature=False,
                              export_cameras=False, export_lights=False)
