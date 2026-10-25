"""โครงกระดูกสัตว์สี่ขา Meshy (numpy ล้วน) : ชื่อ/ลำดับ/แม่ = beasts_rig.SKELETON ทุกท่อน (ใช้ rig_bones ของ beasts_rig ตรง ๆ)
ต่างแค่ตำแหน่งข้อต่อ (ค่าในไฟล์ quad_meshy_<ตัว>.json หัวข้อ rig · extra = กระดูกเสริมเช่น mouth_item) · legOverrides = ขาที่ไม่สมมาตรกับข้างซ้าย
(ต้นทางยืนขาหน้าซ้ายก้าวนำ) : ให้ข้อต่อ 5 จุดของขานั้นเอง (หัวท่อน 1-4 + ปลายกีบ) แทนค่าที่ส่องจากข้างซ้าย"""
from beasts_rig import Rig, leg_bones, rig_bones


def bones_of(r):
    """[(ชื่อ, แม่, หัว, หาง)] ตามลำดับ SKELETON + คู่ขวา"""
    bones = rig_bones(r)
    index = {b[0]: i for i, b in enumerate(bones)}
    for leg, pts in r.get('legOverrides', {}).items():
        if leg.startswith('_'):
            continue
        for k, name in enumerate(leg_bones(leg)):
            _, parent, _, _ = bones[index[name]]
            bones[index[name]] = (name, parent, list(pts[k]), list(pts[k + 1]))
    return bones


def build(r):
    bones = bones_of(r)
    return bones, Rig(bones)
