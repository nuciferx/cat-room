"""คลิปของสัตว์สี่ขา Meshy (Blender) : ใส่คีย์ทุกเฟรมด้วยตัวสร้างท่าของสัตว์สี่ขาชุดเดิม (beasts_clips / beasts_stance / beasts_blender)
แล้ววัดผลจากเมชที่ Blender ผันตามกระดูกจริง (beasts_report) · ค่าคลิป/ท่าทั้งหมดอยู่ใน quad_meshy_<ตัว>.json หัวข้อ clips / stances
ค่าเพิ่มต่อคลิป : ความเร็ว (ระยะก้าว / รอบก้าว) · จุด mouth_item ตอนจบ · ระดับผิวน้ำ (waterline) · ระยะเลื่อนตอนจบ (reportEnd)"""
import beasts_blender as xb
import beasts_report as rep
from beasts_clips import CLIP_TYPES, cycle
from beasts_rig import fk, point
from beasts_stance import to_pose


def bake_all(animal, arm, ctx, rest_bl, fps):
    out = {}
    for name in animal['clips']['order']:
        frames = int(round(animal['clips'][name]['seconds'] * fps))
        c = dict(animal['clips'][name], seconds=frames / fps)  # ความยาวจริง = จำนวนเฟรมเต็ม (ท่าวนต่อกันสนิท)
        fn = CLIP_TYPES[c.get('type', 'still')]
        act, poses = xb.bake_clip(arm, ctx.rig, rest_bl, name, frames,
                                  lambda t, c=c, fn=fn: to_pose(fn(c, ctx, t), ctx.rig), fps, c.get('only'))
        out[name] = (act, frames, c, poses)
    return out


def _speed(c):
    if c.get('type') != 'gait':
        return {'mps': c['mps']} if 'mps' in c else {}
    s = {'strideM': c['strideM'], 'cycleS': round(cycle(c), 4), 'mps': round(c['strideM'] / cycle(c), 3), 'duty': c['duty']}
    if 'env' in c:
        s['note'] = 'mps = ความเร็วช่วงก้าวเต็มแรง (env = 1)'
    return s


def _r(v):
    return [round(float(x), 3) for x in v]


def _extras(ctx, c, poses):
    out = {}
    if 'mouth_item' in ctx.rig.head:
        out['mouthItemEnd'] = _r(point(ctx.rig, fk(ctx.rig, poses[-1]), 'mouth_item', ctx.rig.head['mouth_item']))
    if c.get('waterline'):
        co = ctx.skin.posed(fk(ctx.rig, poses[0]))
        head = ctx.skin.members(['head', 'jaw'], 0.5)
        out['waterline'] = {'waterY': 0.0, 'headTopY': round(float(co[head, 1].max()), 3),
                            'snoutMinY': round(float(co[head, 1].min()), 3), 'meshTopY': round(float(co[:, 1].max()), 3)}
    if c.get('reportEnd'):
        out['endOffset'] = _r(poses[-1].off)
    return out


def measure(mesh, arm, ctx, clips, fps):
    toes = rep.toe_members(mesh)
    arm.animation_data.action = None
    xb.clear_pose(arm)
    info = {'rest': rep.rest_stats(mesh, arm, ctx.rig, ctx.skin), 'toeVerts': int(len(toes)), 'clips': {}}
    for name, (act, frames, c, poses) in clips.items():
        s = rep.clip_stats(mesh, arm, act, frames, toes, poses)
        s.update(seconds=round(frames / fps, 4), loop=c.get('loop', True))
        s.update(_speed(c))
        if c.get('type') == 'gait' and 'env' not in c:
            s['slipM'] = rep.gait_stats(c, ctx.rig, poses, fps)['slipM']
        s.update(_extras(ctx, c, poses))
        info['clips'][name] = s
    arm.animation_data.action = None
    xb.clear_pose(arm)
    return info
