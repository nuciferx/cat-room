"""โครงกระดูกสัตว์สี่ขา Meshy (numpy ล้วน) : ชื่อ/ลำดับ/แม่ = beasts_rig.SKELETON ทุกท่อน (ใช้ rig_bones ของ beasts_rig ตรง ๆ)
ต่างแค่ตำแหน่งข้อต่อ (ค่าในไฟล์ quad_meshy_<ตัว>.json หัวข้อ rig · extra = กระดูกเสริมเช่น mouth_item) · legOverrides = ขาที่ไม่สมมาตรกับข้างซ้าย
(ต้นทางยืนขาหน้าซ้ายก้าวนำ) : ให้ข้อต่อ 5 จุดของขานั้นเอง (หัวท่อน 1-4 + ปลายกีบ) แทนค่าที่ส่องจากข้างซ้าย
bb (แมว cat2) : กระดูกเพิ่มเปิดผ่านค่าเท่านั้น (ไม่มีค่า = โครงเดิมทุกอย่าง) :
  tail มีจุดเกิน 4 จุด → tail4, tail5 ... ต่อกันเป็นสาย · more = [[ชื่อ, แม่, หัว, หาง]] ชื่อลงท้าย _L สร้างคู่ _R เอง
  reparent = {กระดูก: แม่ใหม่} (ลงท้าย _L ใช้กับคู่ _R ด้วย) แล้วเรียงแม่ก่อนลูกใหม่
  slideBones = กระดูกที่เลื่อนตำแหน่งได้ (ใส่คีย์ location) · poseSpread = แบ่งการหมุนของกระดูกเดิมให้กระดูกที่เพิ่ม (beasts_stance)"""
from beasts_rig import Rig, leg_bones, rig_bones
from birds_parts import mirror_bones


def _sided(d):
    """{ชื่อ_L: ค่า} → เพิ่ม {ชื่อ_R: ค่า (ชื่อ _L ในค่าเปลี่ยนเป็น _R)}"""
    out = dict(d)
    for k, v in d.items():
        if k.endswith('_L'):
            out[k[:-2] + '_R'] = _flip(v)
    return out


def _flip(v):
    if isinstance(v, str):
        return v[:-2] + '_R' if v.endswith('_L') else v
    return [[_flip(t), s] for t, s in v]


def _tail_more(r):
    pts = r['tail']
    return [('tail%d' % (i + 1), 'tail%d' % i, list(pts[i]), list(pts[i + 1])) for i in range(3, len(pts) - 1)]


def _topo(bones):
    """เรียงแม่ก่อนลูก (คงลำดับเดิมให้มากที่สุด)"""
    placed, out, left = set(), [], list(bones)
    while left:
        ready = [b for b in left if b[1] is None or b[1] in placed]
        if not ready:
            raise ValueError('rig : แม่ของกระดูกวนกัน %s' % [b[0] for b in left])
        out.append(ready[0])
        placed.add(ready[0][0])
        left.remove(ready[0])
    return out


def _plus(r, bones):
    """กระดูกเพิ่มของ bb (ไม่มีค่า = คืน bones เดิมทุกตัวตามลำดับเดิม)"""
    more = _tail_more(r) + [tuple(b) for b in mirror_bones([tuple(b) for b in r.get('more', [])])]
    reparent = _sided(r.get('reparent', {}))
    if not more and not reparent:
        return bones
    bones = [(n, reparent.get(n, p), h, t) for n, p, h, t in bones + more]
    return _topo(bones)


def bones_of(r):
    """[(ชื่อ, แม่, หัว, หาง)] ตามลำดับ SKELETON + คู่ขวา (+ กระดูกเพิ่มของ bb)"""
    bones = rig_bones(r)
    index = {b[0]: i for i, b in enumerate(bones)}
    for leg, pts in r.get('legOverrides', {}).items():
        if leg.startswith('_'):
            continue
        for k, name in enumerate(leg_bones(leg)):
            _, parent, _, _ = bones[index[name]]
            bones[index[name]] = (name, parent, list(pts[k]), list(pts[k + 1]))
    return _plus(r, bones)


def build(r):
    bones = bones_of(r)
    rig = Rig(bones)
    rig.slide = set(_sided({b: b for b in r.get('slideBones', [])}))
    rig.spread = {k: v for k, v in _sided(r.get('poseSpread', {})).items() if not k.startswith('_')}
    return bones, rig
