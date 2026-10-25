"""ท่าของนกตามเวลา (numpy ล้วน) : คืน Pose ของเวลา t วินาที · ทุกท่าอยู่กับที่ (in-place) ตัวเลขทั้งหมดจาก build_birds.json
idle เหลียวหัวกระตุก · peck ก้มจิก (หาสเกลให้ปลายปากแตะพื้นเอง) · walk/run ก้าวขาแบบเท้าแนบพื้นช่วงยืน · flap กระโดดกระพือ
fly บินกระพือเต็มที่ขาพับ · swim (เป็ด) ลอยตัวพายเท้า"""
import math

import numpy as np

from birds_pose import Pose, SIDES, apply_point, fk, partial, rx, ry, rz

TAU = 2 * math.pi
SIGN = {'L': 1.0, 'R': -1.0}
# ปีกกาง : ปลายปีก (-z) → ออกข้าง (+x) · ผิวนอก (+x) → ขึ้น · ขอบบนตอนพับ → ไปหลัง
OPEN_L = np.array([[0.0, 0.0, -1.0], [1.0, 0.0, 0.0], [0.0, -1.0, 0.0]])
MIRROR = np.diag([-1.0, 1.0, 1.0])
OPEN = {'L': OPEN_L, 'R': MIRROR @ OPEN_L @ MIRROR}


def keys_at(keys, t):
    """keys = [[t, ค่า]] ต่อแบบโค้ง cosine"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-9)
            return a + (b - a) * (0.5 - 0.5 * math.cos(math.pi * u))
    return keys[-1][1]


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def wings(pose, spread=0.0, swing=0.0, open_f=0.0, beat=0.0, tip=0.0):
    """ปีกสองข้าง : spread = ขอบล่างกางออก · swing = ปลายปีกเบนออก · open_f = กางเต็ม 0..1 · beat = ยกปีก (องศา)"""
    for s in SIDES:
        g = SIGN[s]
        base = rz(g * spread) @ ry(-g * swing)
        op = partial(OPEN[s], open_f)
        pose.local['wing_' + s] = rz(g * beat) @ op @ base
        # ปลายปีกยกตามแกนหน้า-หลังของตัว (หลังกางแล้ว) : แปลงแกนเข้ากรอบพักของปีก
        pose.local['wing_tip_' + s] = (op @ base).T @ rz(g * tip) @ (op @ base)


def head_level(pose, yaw=0.0, pitch=0.0, roll=0.0):
    pose.absolute['head'] = ry(yaw) @ rz(roll) @ rx(pitch)


def foot(pose, rig, side, dy=0.0, dz=0.0, curl=0.0, yaw=0.0):
    pose.feet[side] = (rig.ankle(side) + np.array([0.0, dy, dz]), ry(yaw) @ rx(curl))


# ---------- idle ----------

def idle(c, rig, t):
    p = Pose()
    br = math.sin(TAU * c['breathCycles'] * t / c['seconds'])
    p.off[1] = c['bobM'] * br
    p.local['body'] = rx(c['bodyPitchDeg'] * br)
    p.local['tail'] = rx(c['tailDeg'] * br)
    yaw, roll, pitch = _snap_keys(c['headKeys'], t, c['snapS'])
    p.local['neck2'] = ry(yaw * c['neckShare'])
    head_level(p, yaw, pitch, roll)
    return p


def _snap_keys(keys, t, snap):
    """ค้างท่าแล้วสะบัดไปท่าถัดไปเร็ว ๆ ในเวลา snap (แบบไก่เหลียวหัว) · คีย์สุดท้ายควรเท่าคีย์แรกเพื่อวนต่อเนื่อง"""
    i = max(j for j, k in enumerate(keys) if k[0] <= t) if t >= keys[0][0] else 0
    prev, cur = keys[max(i - 1, 0)], keys[i]
    w = smoothstep((t - cur[0]) / snap)
    return [prev[j] + (cur[j] - prev[j]) * w for j in (1, 2, 3)]


# ---------- peck ----------

def peck_pose(c, rig, e):
    p = Pose()
    p.off[1] = -c['hipDropM'] * e
    p.local['body'] = rx(c['bodyPitchDeg'] * e)
    p.local['neck1'] = rx(c['neck1Deg'] * e)
    p.local['neck2'] = rx(c['neck2Deg'] * e)
    p.local['tail'] = rx(c['tailDeg'] * e)
    head_level(p, pitch=c['headDeg'] * e)
    return p


def beak_y(c, rig, e, tip):
    return apply_point(rig, fk(rig, peck_pose(c, rig, e)), 'head', tip)[1]


def solve_peck_scale(c, rig, tip):
    """หาสเกล k ที่ทำให้ปลายปากลงถึง beakTargetY พอดี (bisection) · คืน (k, ปลายปากต่ำสุดที่ได้)"""
    lo, hi = 0.0, c['maxScale']
    if beak_y(c, rig, hi, tip) > c['beakTargetY']:
        return hi, beak_y(c, rig, hi, tip)
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if beak_y(c, rig, mid, tip) > c['beakTargetY']:
            lo = mid
        else:
            hi = mid
    return hi, beak_y(c, rig, hi, tip)


def peck(c, rig, t):
    return peck_pose(c, rig, c['_scale'] * keys_at(c['env'], t))


# ---------- walk / run ----------

def _gait_feet(c, rig, pose, phase, yaw):
    beta, span = c['duty'], c['duty'] * c['strideM']
    for side, ph in (('L', phase), ('R', (phase + 0.5) % 1.0)):
        if ph < beta:
            foot(pose, rig, side, 0.0, span * (0.5 - ph / beta), 0.0, yaw)
            continue
        u = (ph - beta) / (1 - beta)
        lift = math.sin(math.pi * u)
        foot(pose, rig, side, c['liftM'] * lift, span * (smoothstep(u) - 0.5), c['toeCurlDeg'] * lift * lift, yaw)


def _head_bob(c, phase):
    """หัวค้างกลางอากาศแล้วพุ่งไปหน้า (ต่อก้าว) : คืนระยะหัวเทียบตัว (ม.)"""
    hb = c['headBob']
    amp = c['strideM'] * hb['hold'] / 4 * hb['ampScale']
    tau = (2 * phase) % 1.0
    if tau < hb['hold']:
        return amp * (1 - 2 * tau / hb['hold'])
    return -amp + 2 * amp * smoothstep((tau - hb['hold']) / (1 - hb['hold']))


def gait(c, rig, t):
    phase = (t / c['seconds']) % 1.0
    lean = math.cos(TAU * (phase - c['duty'] / 2))
    p = Pose()
    p.off[:] = [c['swayM'] * lean, -c['bobM'] * math.cos(2 * TAU * phase), 0.0]
    yaw = c['bodyYawDeg'] * lean
    p.local['body'] = rx(c['bodyPitchDeg']) @ ry(yaw) @ rz(-c['bodyRollDeg'] * lean)
    bob = math.degrees(_head_bob(c, phase) / rig.len['neck1'])
    p.local['neck1'] = rx(c['neck1Deg'] + bob)
    p.local['neck2'] = rx(c['neck2Deg'] - 0.5 * bob)
    p.local['tail'] = rx(c['tailDeg'] + c['tailWagDeg'] * math.sin(2 * TAU * phase))
    head_level(p, yaw * c['headYawShare'], c['headDeg'])
    _gait_feet(c, rig, p, phase, yaw)
    flutter = c.get('flutterDeg', 0.0) * math.sin(TAU * c.get('flutterCycles', 0) * phase)
    wings(p, c.get('wingSpreadDeg', 0.0) + flutter, c.get('wingSwingDeg', 0.0))
    return p


# ---------- flap / fly ----------

def _beat(b, t):
    """มุมยกปีก : เริ่มที่ยกสูงสุด แกว่งระหว่าง downDeg..upDeg จำนวน count รอบในช่วง from..to"""
    u = (t - b['from']) / (b['to'] - b['from'])
    if u < 0 or u > 1:
        return b['upDeg']
    return b['downDeg'] + (b['upDeg'] - b['downDeg']) * (0.5 + 0.5 * math.cos(TAU * b['count'] * u))


def _air_body(c, p, k):
    p.local['body'] = rx(c['bodyPitchDeg'] * k)
    p.local['neck1'] = rx(c['neck1Deg'] * k)
    p.local['neck2'] = rx(c['neck2Deg'] * k)
    p.local['tail'] = rx(c['tailDeg'] * k)
    head_level(p, pitch=c['headDeg'] * k)


def _tuck(c, rig, p, k):
    for s in SIDES:
        foot(p, rig, s, c['tuckM'][0] * k, c['tuckM'][1] * k, c['toeCurlDeg'] * k)


def flap(c, rig, t):
    p = Pose()
    p.off[1] = -c['dropM'] * keys_at(c['crouch'], t)
    _air_body(c, p, keys_at(c['pitch'], t))
    _tuck(c, rig, p, keys_at(c['tuck'], t))
    b, op = c['beat'], keys_at(c['open'], t)
    wings(p, open_f=op, beat=_beat(b, t) * op, tip=_beat(b, t - b['tipLagS']) * op * b['tipShare'])
    return p


def fly(c, rig, t):
    p = Pose()
    b = dict(c['beat'], **{'from': 0.0, 'to': c['seconds']})
    up = _beat(b, t)
    p.off[1] = -c['bobM'] * (up - b['downDeg']) / (b['upDeg'] - b['downDeg'])
    _air_body(c, p, 1.0)
    _tuck(c, rig, p, 1.0)
    wings(p, open_f=1.0, beat=up, tip=_beat(b, (t - b['tipLagS']) % c['seconds']) * b['tipShare'])
    return p


# ---------- swim (เป็ด) ----------

def swim(c, rig, t):
    phase = (t / c['seconds']) % 1.0
    p = Pose()
    nod = math.sin(2 * TAU * phase)
    p.off[1] = c['bobM'] * nod
    p.local['body'] = rx(c['bodyPitchDeg'])
    p.local['neck1'] = rx(c['neck1Deg'] + c['nodDeg'] * nod)
    p.local['neck2'] = rx(c['neck2Deg'] - 0.5 * c['nodDeg'] * nod)
    p.local['tail'] = rx(c['tailDeg'])
    head_level(p, pitch=c['headDeg'])
    wings(p, c.get('wingSpreadDeg', 0.0))
    for side, ph in (('L', phase), ('R', (phase + 0.5) % 1.0)):
        a = TAU * ph
        # 0..π = ถีบไปหลัง (เท้าต่ำ พังผืดกาง) · π..2π = ดึงกลับ (เท้ายก นิ้วหุบ)
        foot(p, rig, side, c['footUpM'] - c['ampYM'] * math.sin(a), c['footBackM'] + c['ampZM'] * math.cos(a),
             c['toeCurlDeg'] * (0.5 - 0.5 * math.sin(a)))
    return p


CLIPS = {'idle': idle, 'peck': peck, 'walk': gait, 'run': gait, 'flap': flap, 'fly': fly, 'swim': swim}
