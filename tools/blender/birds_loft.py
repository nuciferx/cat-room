"""เรขาคณิตของนก (ไม่พึ่ง Blender) : ท่อ loft ตามสถานีแบบ Catmull-Rom → Part (จุดยอด หน้า UV ต่อมุม น้ำหนักกระดูก)
พิกัดนก = แบบ glTF : x = ซ้ายของตัว · y = ขึ้น · z = หน้า (หัว) · หน่วยเมตร · เท้าแตะ y = 0
สถานี = [x, y, z, w, hp, hn(, tilt องศา)] : w = ครึ่งกว้างตามแกนข้าง · hp/hn = ครึ่งสูงไปทาง +p / -p
p = cross(แนวท่อ, แกนข้าง) : ท่อที่วิ่งไปหน้า p = ขึ้น · ท่อที่วิ่งขึ้น p = หลัง · ท่อที่วิ่งไปหลัง p = ลง"""
import math

import numpy as np

EPS = 1e-6


class Part:
    """ชิ้นเมชหนึ่งชิ้น : faces = ทูเพิลดัชนีจุดยอด (เรียงตามเข็มนาฬิกากลับ = หน้าออกนอก) · uvs ขนานกับ faces"""

    def __init__(self, name, material=0):
        self.name, self.material = name, material
        self.verts, self.weights, self.faces, self.uvs = [], [], [], []

    def add_vert(self, p, w):
        self.verts.append(np.asarray(p, dtype=float))
        self.weights.append(dict(w))
        return len(self.verts) - 1

    def add_face(self, idx, uv):
        self.faces.append(tuple(idx))
        self.uvs.append(tuple(uv))

    def tri_count(self):
        return sum(len(f) - 2 for f in self.faces)


def catmull(stations, t):
    """ค่าบนเส้น Catmull-Rom ผ่านทุกสถานี · t ∈ [0, 1] เท่ากันทุกช่วง"""
    s = np.asarray(stations, dtype=float)
    n = len(s)
    x = min(max(t, 0.0), 1.0) * (n - 1)
    i = min(int(x), n - 2)
    u = x - i
    p0, p1, p2, p3 = s[max(i - 1, 0)], s[i], s[i + 1], s[min(i + 2, n - 1)]
    return 0.5 * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (3 * p1 - p0 - 3 * p2 + p3) * u ** 3)


def _norm(v):
    n = np.linalg.norm(v)
    return v / n if n > EPS else v


def sample_rings(stations, rings, smooth=True):
    """คืนรายการวง {c, w, hp, hn, tilt, t} : smooth = เส้นโค้งผ่านสถานี · ไม่ smooth = ใช้สถานีตรง ๆ (ขอบหยัก เช่น หงอน)"""
    st = [list(s) + [0.0] * (7 - len(s)) for s in stations]
    if not smooth or rings <= 0:
        rows = [(np.asarray(s, dtype=float), i / (len(st) - 1)) for i, s in enumerate(st)]
    else:
        rows = [(catmull(st, i / (rings - 1)), i / (rings - 1)) for i in range(rings)]
    return [{'c': r[:3], 'w': max(r[3], 0.0), 'hp': max(r[4], 0.0), 'hn': max(r[5], 0.0), 'tilt': r[6], 'param': t} for r, t in rows]


def ring_frames(rings, side):
    """ใส่แกน t (แนวท่อ) s (ข้าง) p ให้ทุกวง · แกนข้างตั้งฉากกับแนวท่อเสมอ แล้วหมุนตาม tilt"""
    side = np.asarray(side, dtype=float)
    n = len(rings)
    for i, r in enumerate(rings):
        a, b = rings[max(i - 1, 0)]['c'], rings[min(i + 1, n - 1)]['c']
        t = _norm(b - a)
        s = _norm(side - np.dot(side, t) * t)
        p = np.cross(t, s)
        k = math.radians(r['tilt'])
        r['t'], r['s'], r['p'] = t, -p * math.sin(k) + s * math.cos(k), p * math.cos(k) + s * math.sin(k)
    return rings


def _is_apex(r):
    return r['w'] < EPS and r['hp'] < EPS and r['hn'] < EPS


def ring_points(r, around):
    """จุดรอบวง เริ่มที่ด้าน -p (รอยต่อ UV อยู่ด้านท้อง/ด้านล่าง) · วงยอดแหลม = จุดเดียว"""
    if _is_apex(r):
        return [r['c']]
    out = []
    for k in range(around):
        a = math.pi + 2 * math.pi * k / around
        ca, sa = math.cos(a), math.sin(a)
        h = r['hp'] if ca > 0 else r['hn']
        out.append(r['c'] + r['p'] * (h * ca) + r['s'] * (r['w'] * sa))
    return out


def knot_weights(bones, t):
    """bones = ชื่อกระดูกเดียว หรือ [[t, ชื่อ], ...] ไล่น้ำหนักเชิงเส้นตาม t"""
    if isinstance(bones, str):
        return {bones: 1.0}
    if t <= bones[0][0]:
        return {bones[0][1]: 1.0}
    for (t0, b0), (t1, b1) in zip(bones, bones[1:]):
        if t <= t1:
            u = (t - t0) / max(t1 - t0, EPS)
            w = {b0: 1.0 - u}
            w[b1] = w.get(b1, 0.0) + u
            return w
    return {bones[-1][1]: 1.0}


def _uv(rect, k, around, t):
    u0, v0, u1, v1 = rect
    return (u0 + (u1 - u0) * k / around, v0 + (v1 - v0) * t)


def _bridge(part, ia, ib, ra, rb, around, rect):
    """ต่อหน้าระหว่างสองวง (วงละ around จุด หรือจุดเดียวถ้าเป็นยอดแหลม)"""
    for k in range(around):
        k1 = (k + 1) % around
        uva = [_uv(rect, k + (0.5 if len(ia) == 1 else 0), around, ra['param']), _uv(rect, k + 1, around, ra['param'])]
        uvb = [_uv(rect, k + (0.5 if len(ib) == 1 else 0), around, rb['param']), _uv(rect, k + 1, around, rb['param'])]
        if len(ia) == 1:
            part.add_face((ia[0], ib[k], ib[k1]), (uva[0], uvb[0], uvb[1]))
        elif len(ib) == 1:
            part.add_face((ia[k], ib[0], ia[k1]), (uva[0], uvb[0], uva[1]))
        else:
            part.add_face((ia[k], ib[k], ib[k1], ia[k1]), (uva[0], uvb[0], uvb[1], uva[1]))


def loft(name, spec, rect, material=0):
    """spec = {stations, rings, around, side, smooth, bones} → Part"""
    rings = sample_rings(spec['stations'], spec.get('rings', 0), spec.get('smooth', True))
    ring_frames(rings, spec.get('side', [1, 0, 0]))
    part, around = Part(name, material), spec['around']
    prev = None
    for r in rings:
        w = knot_weights(spec['bones'], r['param'])
        idx = [part.add_vert(p, w) for p in ring_points(r, around)]
        if prev is not None and not (len(prev[0]) == 1 and len(idx) == 1):
            _bridge(part, prev[0], idx, prev[1], r, around, rect)
        prev = (idx, r)
    return part, rings


def mirror(part, name):
    """สำเนาฝั่งขวา : x กลับด้าน · กระดูก _L → _R · กลับลำดับมุมของหน้าเพื่อให้หน้ายังหันออก"""
    out = Part(name, part.material)
    for p, w in zip(part.verts, part.weights):
        out.add_vert((-p[0], p[1], p[2]), {_swap_side(b): v for b, v in w.items()})
    for f, uv in zip(part.faces, part.uvs):
        out.add_face(tuple(reversed(f)), tuple(reversed(uv)))
    return out


def _swap_side(bone):
    return bone[:-2] + '_R' if bone.endswith('_L') else bone
