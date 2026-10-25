"""โครงกระดูกสี่ขาชุดเดียว (ใช้ร่วมทุกตัว ต่างแค่ตำแหน่งข้อต่อใน json) + FK/IK ขา (numpy ล้วน ไม่พึ่ง Blender)
พิกัด = แบบ glTF : x = ซ้ายของตัว · y = ขึ้น · z = หน้า · เมตร · จุดกำเนิดที่พื้นใต้กลางลำตัว
ขาแต่ละขา = 4 ท่อน (ต้นขา · ปลายขา · ฝ่าเท้า/ข้อกีบ · กีบ/อุ้งเท้า) : ข้อกลางสองท่อนบนแก้ด้วย IK สองท่อน
ท่อนที่สาม (ฝ่าเท้า) หมุนตามมุม low ที่ท่ากำหนด · ท่อนปลาย (กีบ) หมุนตามมุม toe ในกรอบพื้น (หรือกรอบตัวเมื่อ attach)
ท่าของกระดูก b = การแปลง x ↦ D_b (x - หัวกระดูกตอนพัก) + p_b (D = การหมุนสะสมในกรอบโลก · แบบเดียวกับนก)"""
import numpy as np

from birds_parts import mirror_bones
from birds_pose import knee, partial, rot_between, rx

EYE = np.eye(3)
# (ชื่อ, แม่) เรียงแม่ก่อนลูก · ชื่อลงท้าย _L สร้างคู่ _R เอง · ทุกตัวต้องมีครบชุดนี้
SKELETON = (
    ('root', None), ('spine', 'root'), ('pelvis', 'spine'), ('chest', 'spine'), ('hackles', 'spine'),
    ('neck1', 'chest'), ('neck2', 'neck1'), ('head', 'neck2'), ('jaw', 'head'), ('ear_L', 'head'),
    ('tail1', 'pelvis'), ('tail2', 'tail1'), ('tail3', 'tail2'),
    ('upperarm_L', 'chest'), ('forearm_L', 'upperarm_L'), ('frontfoot_L', 'forearm_L'), ('fronttoe_L', 'frontfoot_L'),
    ('thigh_L', 'pelvis'), ('shin_L', 'thigh_L'), ('hindfoot_L', 'shin_L'), ('hindtoe_L', 'hindfoot_L'),
)
CHAIN = {'F': ('upperarm', 'forearm', 'frontfoot', 'fronttoe'), 'H': ('thigh', 'shin', 'hindfoot', 'hindtoe')}
LEGS = ('FL', 'FR', 'HL', 'HR')
SIGN = {'L': 1.0, 'R': -1.0}
SCALED_BONES = ('hackles',)  # กระดูกที่ใส่คีย์ขนาดได้ (ขนหลังตั้ง)


def leg_bones(leg):
    return [b + '_' + leg[1] for b in CHAIN[leg[0]]]


def _pairs(points):
    return [(points[i], points[i + 1]) for i in range(len(points) - 1)]


def rig_bones(r):
    """ค่า rig ใน json → [(ชื่อ, แม่, หัว, หาง)] ตามลำดับ SKELETON + คู่ขวา + กระดูกเสริม (extra)"""
    seg = {'root': ([0, 0, 0], [0, 0, 0.1])}
    for k in ('spine', 'pelvis', 'chest', 'hackles', 'jaw'):
        seg[k] = tuple(r[k])
    seg['ear_L'] = tuple(r['ear'])
    for name, s in zip(('neck1', 'neck2', 'head'), _pairs(r['neck'])):
        seg[name] = s
    for name, s in zip(('tail1', 'tail2', 'tail3'), _pairs(r['tail'])):
        seg[name] = s
    for key, part in (('front', 'F'), ('hind', 'H')):
        for name, s in zip(CHAIN[part], _pairs(r[key])):
            seg[name + '_L'] = s
    missing = [n for n, _ in SKELETON if n not in seg]
    if missing:
        raise ValueError('rig ขาดกระดูก %s' % missing)
    bones = [(n, p, list(seg[n][0]), list(seg[n][1])) for n, p in SKELETON]
    return mirror_bones(bones) + [tuple(e) for e in r.get('extra', [])]


class Rig:
    """โครงตอนพัก : order = แม่ก่อนลูก · legs = ข้อต่อพักของแต่ละขา (J0..J3 + ปลายกีบ) และทิศพับข้อกลาง"""

    def __init__(self, bones):
        self.order = [b[0] for b in bones]
        self.parent = {b[0]: b[1] for b in bones}
        self.head = {b[0]: np.asarray(b[2], dtype=float) for b in bones}
        self.tail = {b[0]: np.asarray(b[3], dtype=float) for b in bones}
        self.len = {n: float(np.linalg.norm(self.tail[n] - self.head[n])) for n in self.order}
        self.dir = {n: (self.tail[n] - self.head[n]) / self.len[n] for n in self.order}
        self.legs = {leg: self._leg(leg) for leg in LEGS}
        self.leg_of = {n: leg for leg in LEGS for n in self.legs[leg]['bones']}

    def _leg(self, leg):
        names = leg_bones(leg)
        j = [self.head[n] for n in names] + [self.tail[names[-1]]]
        u = (j[2] - j[0]) / np.linalg.norm(j[2] - j[0])
        bend = (j[1] - j[0]) - np.dot(j[1] - j[0], u) * u
        return {'bones': names, 'J': j, 'l0': self.len[names[0]], 'l1': self.len[names[1]],
                'bend': bend / max(np.linalg.norm(bend), 1e-9), 'height': float(j[0][1] - j[3][1])}


class Pose:
    """floor = y ต่ำสุดของเป้าข้อกีบ · off = เลื่อน root · local = หมุนเทียบแม่ · scale = ขนาดกระดูก (เวกเตอร์ 3) · legs = {ขา: LegPose} · err = ระยะที่ IK เอื้อมไม่ถึง (ม.)"""

    def __init__(self):
        self.off = np.zeros(3)
        self.local, self.scale, self.legs, self.err = {}, {}, {}, {}
        self.floor = 0.0  # ข้อกีบต่ำสุดได้แค่ระดับนี้ (กันขาจมพื้นตอนล้ม) · ว่ายน้ำตั้งต่ำมากเพื่อปิด


def leg_pose(off=(0.0, 0.0, 0.0), low=0.0, toe=0.0, attach=0.0):
    """off = เลื่อนข้อกีบจากที่พัก (ม. · กรอบพื้น หรือกรอบตัวเมื่อ attach = 1) · low/toe = องศา (+ = ปลายท่อนไปหลัง) · attach 0..1"""
    return {'off': np.asarray(off, dtype=float), 'low': low, 'toe': toe, 'attach': attach}


def _leg_target(leg_rest, lp, p0, d_par):
    j, att = leg_rest['J'], lp['attach']
    world_t = j[3] + lp['off']
    body_t = p0 + d_par @ (j[3] - j[0] + lp['off'])
    return world_t + (body_t - world_t) * att


def solve_leg(rig, pose, leg, p0, d_par):
    """IK หนึ่งขา : คืน {กระดูก: D} · เก็บระยะเอื้อมไม่ถึงไว้ใน pose.err"""
    lr = rig.legs[leg]
    lp = pose.legs.get(leg) or leg_pose()
    frame = partial(d_par, lp['attach']) if lp['attach'] > 0 else EYE
    j, names = lr['J'], lr['bones']
    target = _leg_target(lr, lp, p0, d_par)
    target[1] = max(target[1], pose.floor)
    j2 = target - frame @ rx(lp['low']) @ (j[3] - j[2])
    j1 = knee(p0, j2, lr['l0'], lr['l1'], d_par @ lr['bend'])
    d0 = rot_between(d_par @ rig.dir[names[0]], j1 - p0) @ d_par
    j1r = p0 + d0 @ (j[1] - j[0])
    d1 = rot_between(d0 @ rig.dir[names[1]], j2 - j1r) @ d0
    j2r = j1r + d1 @ (j[2] - j[1])
    d2 = rot_between(d1 @ rig.dir[names[2]], target - j2r) @ d1
    pose.err[leg] = float(np.linalg.norm(j2r + d2 @ (j[3] - j[2]) - target))
    return {names[0]: d0, names[1]: d1, names[2]: d2, names[3]: frame @ rx(lp['toe'])}


def _local(pose, name, d_par):
    d = d_par @ pose.local.get(name, EYE)
    s = pose.scale.get(name)
    return d @ np.diag(s) if s is not None else d


def fk(rig, pose):
    """คืน {กระดูก: (D, p)} : ขาแก้ IK ทั้งขาตอนเจอกระดูกบนสุดของขา"""
    out, legs = {}, {}
    for name in rig.order:
        par = rig.parent[name]
        if par is None:
            out[name] = (pose.local.get(name, EYE), rig.head[name] + pose.off)
            continue
        d_par, p_par = out[par]
        p = p_par + d_par @ (rig.head[name] - rig.head[par])
        leg = rig.leg_of.get(name)
        if leg is None:
            out[name] = (_local(pose, name, d_par), p)
            continue
        if leg not in legs:
            legs[leg] = solve_leg(rig, pose, leg, p, d_par)
        out[name] = (legs[leg][name], p)
    return out


def point(rig, posed, bone, x):
    d, p = posed[bone]
    return d @ (np.asarray(x, dtype=float) - rig.head[bone]) + p
