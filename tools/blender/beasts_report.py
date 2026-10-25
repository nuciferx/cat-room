"""วัดผลโมเดลสัตว์สี่ขาหลังใส่ท่า : ค่า y ของกีบ/อุ้งเท้าต่อคลิป (จากเมชที่ Blender ผันตามกระดูกจริง)
· ระยะที่ IK เอื้อมไม่ถึง · เท้าไถลช่วงยืน (gait) · ขนาดตอนพัก · ค่า y ทั้งหมดเป็นพิกัด glTF (= z ของ Blender)"""
import bpy
import numpy as np

from beasts_clips import cycle, planted
from beasts_rig import LEGS, fk, point
from birds_report import _coords, group_members

TOE_BONES = ['fronttoe_L', 'fronttoe_R', 'hindtoe_L', 'hindtoe_R']


def rest_stats(mesh_obj, arm_obj, rig, skin):
    arm_obj.animation_data.action = None
    bpy.context.scene.frame_set(0)
    co = _coords(mesh_obj)
    chest = skin.members(['chest', 'spine', 'hackles'], 0.5)
    z = -co[:, 1]
    return {'heightM': round(float(co[:, 2].max()), 4), 'minY': round(float(co[:, 2].min()), 4),
            'withersM': round(float(co[chest, 2].max()), 4), 'lengthM': round(float(z.max() - z.min()), 4),
            'frontZ': round(float(z.max()), 4), 'backZ': round(float(z.min()), 4),
            'halfWidthM': round(float(np.abs(co[:, 0]).max()), 4),
            'headAxis': '+Z (glTF)' if rig.tail['head'][2] > rig.tail['pelvis'][2] else '-Z'}


def _slip(c, rig, poses, fps):
    """ช่วงยืนของแต่ละขา : ปลายกีบ + ความเร็วเดิน × เวลา ต้องคงที่ · คืนระยะคลาดสูงสุด (ม.)"""
    v = c['strideM'] / cycle(c)
    worst = 0.0
    for leg in LEGS:
        bone = rig.legs[leg]['bones'][3]
        run = []
        for f, pose in enumerate(poses):
            t = f / fps
            if not planted(c, leg, t):
                run = []
                continue
            p = point(rig, fk(rig, pose), bone, rig.tail[bone]) + np.array([0.0, 0.0, v * t])
            run.append(p)
            arr = np.array(run)
            worst = max(worst, float(np.ptp(arr[:, 1])), float(np.ptp(arr[:, 2])))
    return round(worst, 4)


def clip_stats(mesh_obj, arm_obj, act, frames, toes, poses):
    arm_obj.animation_data.action = act
    per_frame, body_min = [], 1e9
    for f in range(frames + 1):
        bpy.context.scene.frame_set(f)
        co = _coords(mesh_obj)
        per_frame.append(float(co[toes, 2].min()))
        body_min = min(body_min, float(co[:, 2].min()))
    err = max(max(p.err.values()) for p in poses)
    return {'frames': frames, 'footMinY': round(min(per_frame), 4), 'footMinYWorstFrame': round(max(per_frame), 4),
            'meshMinY': round(body_min, 4), 'ikErrMaxM': round(err, 4)}


def gait_stats(c, rig, poses, fps):
    return {'strideM': c['strideM'], 'mps': round(c['strideM'] / cycle(c), 3), 'duty': c['duty'],
            'slipM': _slip(c, rig, poses, fps)}


def toe_members(mesh_obj):
    return group_members(mesh_obj, TOE_BONES, 0.5)
