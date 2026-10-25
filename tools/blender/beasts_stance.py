"""ท่าแบบชุดค่า (stance) ของสัตว์สี่ขา (numpy ล้วน) : dict ชื่อค่า → ตัวเลข (ไม่ใส่ = 0 = ท่าพัก) ผสมกันได้แบบเชิงเส้น
ค่าตัว : offX offY offZ (ม.) · pitch roll yaw (องศา หมุนทั้งตัวรอบกระดูก spine) · pelvisPitch chestPitch
คอ/หัว : neck1Pitch neck2Pitch headPitch neckYaw neck2Yaw headYaw headRoll · jaw jawYaw · hackles (ขนหลังตั้ง 0 = ราบ)
หู : earBack earSpread (+L/+R ต่อท้ายเฉพาะข้าง) · หาง : tail1Pitch tail2Pitch tail3Pitch tailYaw
legFloor = y ต่ำสุดของเป้าข้อกีบ (ค่าเริ่ม 0 = พื้น) · ขา : '<ขา>.<ค่า>' ขา = F H (คู่หน้า/หลัง) FL FR HL HR หรือ all · ค่า = dx (ออกข้าง +) dy dz low toe attach (รวมกันทุกระดับ)
มุมก้ม + = หัวก้มลง / ของที่ชี้ไปหลังเงยขึ้น (หางยก) · earBack + = หูพับไปหลัง · earSpread + = หูกางออกข้าง"""
import numpy as np

from beasts_rig import LEGS, SIGN, Pose, leg_pose, point, fk
from birds_pose import rx, ry, rz

LEG_KEYS = ('dx', 'dy', 'dz', 'low', 'toe', 'attach')
TAIL_YAW_SHARE = (0.45, 0.3, 0.25)


def blend(a, b, w):
    """ผสมท่า a → b ด้วยสัดส่วน w (คีย์ที่ไม่มี = 0)"""
    return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * w for k in set(a) | set(b)}


def add(s, extra, k=1.0):
    for key, v in extra.items():
        s[key] = s.get(key, 0.0) + v * k
    return s


def leg_value(s, leg, key):
    return s.get('all.' + key, 0.0) + s.get(leg[0] + '.' + key, 0.0) + s.get(leg + '.' + key, 0.0)


def _side(s, key, side):
    return s.get(key, 0.0) + s.get(key + side, 0.0)


def _head(p, g):
    p.local['spine'] = ry(g('yaw')) @ rx(g('pitch')) @ rz(g('roll'))
    p.local['pelvis'] = rx(g('pelvisPitch'))
    p.local['chest'] = rx(g('chestPitch'))
    p.local['neck1'] = ry(g('neckYaw')) @ rx(g('neck1Pitch'))
    p.local['neck2'] = ry(g('neck2Yaw')) @ rx(g('neck2Pitch'))
    p.local['head'] = ry(g('headYaw')) @ rz(g('headRoll')) @ rx(g('headPitch'))
    p.local['jaw'] = ry(g('jawYaw')) @ rx(g('jaw'))


def _ears_tail(p, s, g):
    for side in ('L', 'R'):
        p.local['ear_' + side] = rz(-SIGN[side] * _side(s, 'earSpread', side)) @ rx(-_side(s, 'earBack', side))
    for i, share in enumerate(TAIL_YAW_SHARE):
        p.local['tail%d' % (i + 1)] = ry(g('tailYaw') * share) @ rx(g('tail%dPitch' % (i + 1)))
    p.scale['hackles'] = np.array([1.0, 1.0 + g('hackles'), 1.0])


def to_pose(s):
    """ชุดค่า → Pose"""
    def g(k):
        return s.get(k, 0.0)
    p = Pose()
    p.off = np.array([g('offX'), g('offY'), g('offZ')])
    p.floor = g('legFloor')
    _head(p, g)
    _ears_tail(p, s, g)
    for leg in LEGS:
        v = {k: leg_value(s, leg, k) for k in LEG_KEYS}
        off = (SIGN[leg[1]] * v['dx'], v['dy'], v['dz'])
        p.legs[leg] = leg_pose(off, v['low'], v['toe'], min(max(v['attach'], 0.0), 1.0))
    return p


# ---------- แก้ค่าให้ถึงเป้า (ปากแตะพื้น · ตัวแนบพื้น) ----------

def _probe(rig, skin, stance, reach):
    posed = fk(rig, to_pose(stance))
    if 'tip' in reach:
        return float(point(rig, posed, reach['bone'], reach['tip'])[1])
    return float(skin.min_y(posed, reach['group'], reach.get('minW', 0.5)))


def _bracket(f, lo, hi, steps):
    """ไล่จาก lo ไป hi หาช่วงแรกที่ค่าเปลี่ยนเครื่องหมาย (ฟังก์ชันอาจไม่ทางเดียว เช่น ปากก้มเลยพื้นแล้วย้อนขึ้น)"""
    xs = [lo + (hi - lo) * i / steps for i in range(steps + 1)]
    fs = [f(x) for x in xs]
    for i in range(steps):
        if fs[i] * fs[i + 1] <= 0:
            return xs[i], fs[i], xs[i + 1]
    best = min(range(len(xs)), key=lambda i: abs(fs[i]))
    return None, abs(fs[best]), xs[best]


def solve_reach(rig, skin, stance, reach):
    """หาค่า reach.param ใน [lo, hi] ที่ทำให้ปลาย (tip ของ bone) หรือจุดต่ำสุดของกลุ่มกระดูก (group) อยู่ที่ targetY (bisection)"""
    key, target = reach['param'], reach['targetY']

    def f(v):
        return _probe(rig, skin, dict(stance, **{key: v}), reach) - target
    lo, flo, hi = _bracket(f, reach['lo'], reach['hi'], reach.get('steps', 16))
    if lo is None:
        print('BEAST_WARN reach ไม่ถึงเป้า', reach.get('_stance'), key, round(flo, 4))
        return hi
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def resolve_stances(raw, rig, skin):
    """ท่าใน json → ท่าที่พร้อมใช้ : _from = เริ่มจากท่าอื่นแล้วทับค่า · _reach = แก้ค่าตามเป้าทีละข้อ"""
    out = {'stand': {}}
    pending = dict(raw)
    while pending:
        ready = [n for n, sp in pending.items() if not sp.get('_from') or sp['_from'] in out]
        if not ready:
            raise ValueError('ท่าอ้าง _from ที่ไม่มี : %s' % sorted(pending))
        for name in ready:
            spec = pending[name]
            base = spec.get('_from')
            s = dict(out[base]) if base else {}
            s.update({k: v for k, v in spec.items() if not k.startswith('_')})
            for reach in spec.get('_reach', []):
                reach = dict(reach, _stance=name)
                s[reach['param']] = solve_reach(rig, skin, s, reach)
            out[name] = s
            del pending[name]
    return out
