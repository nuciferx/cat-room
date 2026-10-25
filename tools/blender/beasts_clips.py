"""ท่าของสัตว์สี่ขาตามเวลา (numpy ล้วน) : ทุกคลิปคืนชุดค่า (stance) ของเวลา t วินาที · ค่าทั้งหมดมาจาก json ของแต่ละตัว
ชนิดคลิป : still = ท่าเรียงตามเวลา (seq) + ค่าบวกตามคีย์ (tracks) + แกว่ง (osc)
gait = still + ก้าวขาสี่ขา (เท้าแนบพื้นช่วงยืน ไม่ไถล) · paddle = still + ตีขาเป็นวงรี (ว่ายน้ำ)
ชื่อค่าใน tracks/osc ต่อท้าย #อะไรก็ได้ เพื่อใส่ค่าเดียวกันซ้ำหลายชุด (เช่น jaw#2)
osc = [แอมพลิจูด, จำนวนรอบต่อคลิป, เฟส (สัดส่วนรอบ), ชนิด 0 = sin / 1 = ยกบวกอย่างเดียว (0.5 - 0.5cos)]"""
import math

from beasts_rig import LEGS
from beasts_stance import blend
from birds_clips import keys_at, smoothstep

TAU = 2 * math.pi


def cycle(c):
    """คาบของการแกว่ง/ก้าว : cycleS (คลิปไม่วนที่ยาวกว่ารอบก้าว เช่น charge) ไม่ใส่ = ความยาวคลิป"""
    return c.get('cycleS', c['seconds'])


def _param(key):
    return key.split('#')[0]


def seq_stance(c, stances, t):
    """ท่าพื้นของเวลา t : seq = [[เวลา, ชื่อท่า]] ต่อกันแบบโค้ง cosine · ไม่มี seq = ท่า stance (ค่าเริ่ม stand)"""
    seq = c.get('seq') or [[0.0, c.get('stance', 'stand')]]
    if t <= seq[0][0]:
        return dict(stances[seq[0][1]])
    for (t0, a), (t1, b) in zip(seq, seq[1:]):
        if t <= t1:
            u = (t - t0) / max(t1 - t0, 1e-9)
            return blend(stances[a], stances[b], 0.5 - 0.5 * math.cos(math.pi * u))
    return dict(stances[seq[-1][1]])


def _osc_value(spec, t, seconds):
    amp, cycles, phase = spec[0], spec[1], spec[2]
    a = TAU * (cycles * t / seconds + phase)
    return amp * (0.5 - 0.5 * math.cos(a)) if len(spec) > 3 and spec[3] == 1 else amp * math.sin(a)


def add_motion(s, c, t, k=1.0):
    """บวกค่าจาก tracks (คีย์ต่อแบบ cosine) และ osc · k = คูณแรงของ osc (ใช้กับ env ของ gait)"""
    for key, keys in c.get('tracks', {}).items():
        p = _param(key)
        s[p] = s.get(p, 0.0) + keys_at(keys, t)
    for key, spec in c.get('osc', {}).items():
        p = _param(key)
        s[p] = s.get(p, 0.0) + k * _osc_value(spec, t, cycle(c))
    return s


def still(c, ctx, t):
    return add_motion(seq_stance(c, ctx.stances, t), c, t)


# ---------- gait ----------

def leg_phase(c, leg, t):
    return (t / cycle(c) - c['phases'][leg]) % 1.0


def planted(c, leg, t):
    return leg_phase(c, leg, t) < c['duty']


def _step(c, leg, t):
    """ระยะก้าวของขาหนึ่ง : ช่วงยืนเท้าเลื่อนไปหลังด้วยความเร็วคงที่ (= strideM / seconds) · ช่วงยกเท้าแกว่งกลับไปหน้า"""
    lc, phi, duty = c['legs'][leg[0]], leg_phase(c, leg, t), c['duty']
    span = duty * c['strideM']
    if phi < duty:
        return 0.0, span * (0.5 - phi / duty), 0.0, 0.0
    u = (phi - duty) / (1.0 - duty)
    a = math.sin(math.pi * u)
    return lc['liftM'] * a, span * (smoothstep(u) - 0.5), lc['lowSwingDeg'] * a, lc['toeSwingDeg'] * a


def gait_legs(s, c, rig, t, k=1.0):
    follow = c.get('lowFollow', 1.0)
    for leg in LEGS:
        dy, dz, low, toe = _step(c, leg, t)
        dz += c['legs'][leg[0]].get('reachM', 0.0)
        low -= follow * math.degrees(math.atan2(dz, rig.legs[leg]['height']))
        for key, v in (('dy', dy), ('dz', dz), ('low', low), ('toe', toe)):
            s[leg + '.' + key] = s.get(leg + '.' + key, 0.0) + v * k


def gait(c, ctx, t):
    """env = [[เวลา, แรง 0..1]] (คลิปไม่วน เช่น charge) คูณทั้งก้าวขาและ osc"""
    k = keys_at(c['env'], t) if 'env' in c else 1.0
    s = seq_stance(c, ctx.stances, t)
    gait_legs(s, c, ctx.rig, t, k)
    return add_motion(s, c, t, k)


# ---------- paddle (ว่ายน้ำ) ----------

def paddle(c, ctx, t):
    """ขาตีเป็นวงรีรอบจุด center ของขาคู่นั้น : ช่วงลง-ไปหลัง = ถีบน้ำ (ฝ่าเท้าตั้ง) · ช่วงขึ้น-ไปหน้า = ดึงกลับ (พับข้อ)"""
    s = add_motion(seq_stance(c, ctx.stances, t), c, t)
    for leg in LEGS:
        lc = c['legs'][leg[0]]
        a = TAU * (t / cycle(c) - c['phases'][leg])
        vals = {'dy': lc['centerY'] + lc['ampYM'] * math.sin(a), 'dz': lc['centerZ'] + lc['ampZM'] * math.cos(a),
                'low': lc['lowDeg'] + lc['lowAmpDeg'] * math.sin(a), 'toe': lc['toeDeg'] + lc['toeAmpDeg'] * math.sin(a)}
        for key, v in vals.items():
            s[leg + '.' + key] = s.get(leg + '.' + key, 0.0) + v
    return s


CLIP_TYPES = {'still': still, 'gait': gait, 'paddle': paddle}
