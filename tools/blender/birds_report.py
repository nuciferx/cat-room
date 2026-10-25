"""วัดผลโมเดลนกหลังใส่ท่า (Blender) : สามเหลี่ยม · ความสูงตอนพัก · ทิศหัว · ค่า y ต่ำสุดของเท้าต่อคลิป · ระดับผิวน้ำ (swim)
ค่า y ทั้งหมดเป็นพิกัด glTF (= z ของ Blender) หน่วยโมเดลก่อนย่อ"""
import bpy
import numpy as np


def _coords(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    ev.to_mesh_clear()
    return co.reshape(-1, 3)


def group_members(obj, names, min_w):
    idx = {obj.vertex_groups[n].index for n in names if n in obj.vertex_groups}
    out = []
    for v in obj.data.vertices:
        if any(g.group in idx and g.weight >= min_w for g in v.groups):
            out.append(v.index)
    return np.array(out, dtype=int)


def rest_stats(mesh_obj, arm_obj):
    arm_obj.animation_data.action = None
    bpy.context.scene.frame_set(0)
    co = _coords(mesh_obj)
    head = co[:, 1].argmin()
    return {'heightM': round(float(co[:, 2].max() - co[:, 2].min()), 4), 'minY': round(float(co[:, 2].min()), 4),
            'lengthM': round(float(co[:, 1].max() - co[:, 1].min()), 4),
            'frontmostGltfZ': round(float(-co[head, 1]), 4), 'headAxis': '+Z (glTF)' if -co[head, 1] > 0 else '-Z'}


def clip_stats(mesh_obj, arm_obj, act, frames, feet):
    """ค่า y ต่ำสุด/สูงสุดของจุดยอดเท้าในแต่ละเฟรม → (ต่ำสุดทั้งคลิป, สูงสุดของค่าต่ำสุดรายเฟรม) + y ต่ำสุดทั้งตัว"""
    arm_obj.animation_data.action = act
    per_frame, body_min = [], 1e9
    for f in range(frames + 1):
        bpy.context.scene.frame_set(f)
        co = _coords(mesh_obj)
        per_frame.append(float(co[feet, 2].min()))
        body_min = min(body_min, float(co[:, 2].min()))
    return {'frames': frames, 'footMinY': round(min(per_frame), 4), 'footMinYWorstFrame': round(max(per_frame), 4),
            'meshMinY': round(body_min, 4)}


def waterline(mesh_obj, arm_obj, act, torso, frac, height):
    """ระดับผิวน้ำตอนลอย : ส่วนลำตัว (กลุ่ม body) เฟรม 0 จมจากท้องขึ้นมา frac ของความหนาลำตัว"""
    arm_obj.animation_data.action = act
    bpy.context.scene.frame_set(0)
    co = _coords(mesh_obj)[torso]
    lo, hi = float(co[:, 2].min()), float(co[:, 2].max())
    y = lo + (hi - lo) * frac
    return {'waterY': round(y, 4), 'waterYOverHeight': round(y / height, 4), 'torsoBottomY': round(lo, 4), 'torsoTopY': round(hi, 4)}
