"""ประกอบชิ้นส่วนนกจาก build_birds.json (ไม่พึ่ง Blender) : ลำตัว-คอ-หัว ปีกแนบตัว หาง หงอน ปาก ตา ขา นิ้ว พังผืด
ทุกชิ้นเป็น loft (birds_loft) ยกเว้นพังผืดเท้าเป็ด · ปีกคำนวณระยะห่างจากผิวลำตัวเอง (hug) จึงไม่จมตัวและไม่ลอยห่าง"""
import math

import numpy as np

from birds_loft import EPS, Part, loft, mirror

MATERIAL_INDEX = {'main': 0, 'eye': 1}


def _torso(rings, until):
    rows = [r for r in rings if r['param'] <= until + EPS]
    return sorted(rows, key=lambda r: r['c'][2])


def body_x(torso, z, y):
    """ครึ่งกว้างของลำตัวที่ (z, y) : ตัดวงรีของวงที่ขนาบ z (ถือว่า p ของลำตัวชี้ขึ้น) · นอกช่วงลำตัว = 0"""
    if not torso or z < torso[0]['c'][2] or z > torso[-1]['c'][2]:
        return 0.0
    for a, b in zip(torso, torso[1:]):
        if a['c'][2] <= z <= b['c'][2]:
            u = (z - a['c'][2]) / max(b['c'][2] - a['c'][2], EPS)
            cy, w = a['c'][1] + (b['c'][1] - a['c'][1]) * u, a['w'] + (b['w'] - a['w']) * u
            dy = y - cy
            h = (a['hp'] + (b['hp'] - a['hp']) * u) if dy > 0 else (a['hn'] + (b['hn'] - a['hn']) * u)
            f = 1.0 - (dy / max(h, EPS)) ** 2
            return w * math.sqrt(f) if f > 0 else 0.0
    return 0.0


def hug_stations(stations, torso, gap, min_x):
    """สถานีปีก [z, y, หนา, ครึ่งสูงล่าง, ครึ่งสูงบน] → [x, y, z, w, hp, hn, tilt] ให้ขอบบน/ล่างแนบผิวลำตัว"""
    out = []
    for z, y, w, hp, hn in stations:
        x_top = max(body_x(torso, z, y + hn), min_x) + gap + w
        x_bot = max(body_x(torso, z, y - hp), min_x) + gap + w
        x = x_top + (x_bot - x_top) * hn / max(hp + hn, EPS)
        x = max(x, body_x(torso, z, y) + gap + w)  # กลางปีกต้องไม่จมท้องที่ป่องกว่าเส้นตรงระหว่างขอบ
        s = max(-1.0, min(1.0, (x_bot - x_top) / max(hp + hn, EPS)))
        out.append([x, y, z, w, hp, hn, math.degrees(math.asin(s))])
    return out


def _web(spec, lofts, name):
    """พังผืดระหว่างนิ้วที่อยู่ติดกัน : แผ่นบน (หน้าหันขึ้น) + แผ่นล่าง (หน้าหันลง) แยกจุดยอดกัน"""
    part = Part(name)
    lines = [[r['c'] for r in lofts[t][1]] for t in spec['toes']]
    n = spec['samples']
    for a, b in zip(lines, lines[1:]):
        pa = [_along(a, spec['frac'] * i / (n - 1)) for i in range(n)]
        pb = [_along(b, spec['frac'] * i / (n - 1)) for i in range(n)]
        for lift, up in ((spec['liftM'], True), (0.0, False)):
            _web_sheet(part, pa, pb, lift, up, spec)
    return part


def _along(line, t):
    x = t * (len(line) - 1)
    i = min(int(x), len(line) - 2)
    return line[i] + (line[i + 1] - line[i]) * (x - i)


def _web_sheet(part, pa, pb, lift, up, spec):
    off = np.array([0.0, lift, 0.0])
    ia = [part.add_vert(p + off, {spec['bones']: 1.0}) for p in pa]
    ib = [part.add_vert(p + off, {spec['bones']: 1.0}) for p in pb]
    u0, v0, u1, v1 = spec['rect']
    for i in range(len(ia) - 1):
        quad = [ia[i], ib[i], ib[i + 1], ia[i + 1]]
        uv = [(u0, v0 + (v1 - v0) * i / len(ia)), (u1, v0 + (v1 - v0) * i / len(ia)),
              (u1, v0 + (v1 - v0) * (i + 1) / len(ia)), (u0, v0 + (v1 - v0) * (i + 1) / len(ia))]
        q = [part.verts[k] for k in quad]
        ny = np.cross(q[1] - q[0], q[3] - q[0])[1]
        if (ny > 0) != up:
            quad, uv = quad[::-1], uv[::-1]
        part.add_face(quad, uv)


def inset_atlas(atlas, inset):
    """ขยับขอบ UV เข้าในช่องเล็กน้อย กันสีช่องข้างเคียงซึมตอน mipmap"""
    return {k: [r[0] + inset, r[1] + inset, r[2] - inset, r[3] - inset] for k, r in atlas.items()}


def _rect(atlas, region):
    return atlas[region]


def _build_one(spec, atlas, lofts, torso):
    kind = spec.get('kind', 'loft')
    mat = MATERIAL_INDEX[spec.get('material', 'main')]
    if kind == 'web':
        return _web(dict(spec, rect=_rect(atlas, spec['region'])), lofts, spec['name'])
    if kind == 'wing':
        h = spec['hug']
        spec = dict(spec, stations=hug_stations(spec['stations'], torso, h['gapM'], h['minX']))
    part, rings = loft(spec['name'], spec, _rect(atlas, spec['region']), mat)
    lofts[spec['name']] = (part, rings)
    return part


def build_parts(bird, inset):
    """คืนรายการ Part ทั้งหมด (ฝั่งซ้าย + สำเนาฝั่งขวาของชิ้นที่ mirror)"""
    atlas, lofts, parts, torso = inset_atlas(bird['atlas'], inset), {}, [], []
    for spec in bird['parts']:
        part = _build_one(spec, atlas, lofts, torso)
        if spec.get('torsoUntil') is not None:
            torso[:] = _torso(lofts[spec['name']][1], spec['torsoUntil'])
        parts.append(part)
        if spec.get('mirror'):
            parts.append(mirror(part, spec['name'].replace('_L', '_R')))
    return parts


def mirror_bones(bones):
    """[[ชื่อ, แม่, หัว, หาง]] : กระดูก _L สร้างคู่ _R (x กลับด้าน)"""
    out = []
    for name, parent, head, tail in bones:
        out.append((name, parent, head, tail))
        if name.endswith('_L'):
            par = parent[:-2] + '_R' if parent and parent.endswith('_L') else parent
            out.append((name[:-2] + '_R', par, [-head[0], head[1], head[2]], [-tail[0], tail[1], tail[2]]))
    return out
