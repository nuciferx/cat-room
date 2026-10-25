"""ส่วน Blender ของสัตว์สี่ขา Meshy : เมชต้นทาง → ลดโพลี LOD เดียว → normal เนียนจากเมชละเอียด (ภาพอบใน quad_meshy_bake)
ใช้ din_new_mesh ซ้ำ (build_object / clean / decimate_to) · พิกัด glTF (x, y, z) → Blender (x, -z, y)
normal : เมชละเอียด shade smooth แล้วโอน corner normal ไปเมชที่ลดแล้ว (Data Transfer · custom normal)
จึงไม่เป็นเหลี่ยมตามสามเหลี่ยมใหญ่"""
import bpy
import numpy as np

import din_new_mesh as dmesh
from prep_din_mesh import set_active, tri_count

TONE = 'TONE'


def to_bl(p):
    p = np.asarray(p, dtype=float)
    return np.column_stack([p[:, 0], -p[:, 2], p[:, 1]])


def from_bl(p):
    p = np.asarray(p, dtype=float)
    return np.column_stack([p[:, 0], p[:, 2], -p[:, 1]])


def _shade_smooth(obj):
    me = obj.data
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.update()


def _tone_attr(obj, tri_keep):
    """ค่า keep ต่อสามเหลี่ยม (quad_meshy_tone) → สีมุม (CORNER) ชื่อ TONE · ใส่ก่อน clean (bmesh เก็บค่าต่อมุมไว้ตอนรวมจุด)"""
    me = obj.data
    attr = me.color_attributes.new(TONE, 'FLOAT_COLOR', 'CORNER')
    rgba = np.ones((len(me.loops), 4), dtype=np.float32)
    loop_face = np.repeat(np.arange(len(me.polygons)), 3)  # from_pydata : สามเหลี่ยมล้วน มุมเรียงตามหน้า
    rgba[:, :3] = tri_keep[loop_face, None]
    attr.data.foreach_set('color', rgba.ravel())


def build_source(src, mc, name, tri_keep):
    """เมชละเอียด (หลังตั้งพิกัด) → object · สีมุม TONE · merge จุดซ้ำ · ทิ้งชิ้นจิ๋ว · shade smooth"""
    uv = src.uv.copy()
    uv[:, 1] = 1.0 - uv[:, 1]  # glTF v ลง ↔ Blender v ขึ้น (ภาพต้นทางจะอ่านถูกตอนอบ)
    obj = dmesh.build_object(name + '_source', to_bl(src.pos), src.tri, uv, np.zeros((len(src.pos), 0)), [])
    _tone_attr(obj, tri_keep)
    rep = dmesh.clean(obj, mc)
    _shade_smooth(obj)
    return obj, rep


def tag_detail(obj, zones, strength):
    """vertex group 'detail' (ที่ decimate อ่าน) : จุดในกล่อง zones (พิกัด glTF) ลดโพลีน้อยลง · กล่องแรกที่เข้าชนะ"""
    vg = obj.vertex_groups.new(name=dmesh.DETAIL)
    co = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    p = from_bl(co.reshape(-1, 3))
    w = np.ones(len(p))
    done = np.zeros(len(p), dtype=bool)
    rep = {}
    for z in zones:
        q = p.copy()
        if z.get('mirrorX'):
            q[:, 0] = np.abs(q[:, 0])
        inside = np.all((q >= np.asarray(z['min'])) & (q <= np.asarray(z['max'])), axis=1) & ~done
        w[inside] = 1.0 - z.get('strength', strength)
        done |= inside
        rep[z.get('_n', str(len(rep)))] = int(inside.sum())
    for value in np.unique(w):
        vg.add(np.nonzero(w == value)[0].tolist(), float(value), 'REPLACE')
    return rep


def transfer_normals(low, high):
    """corner normal ของ high → custom normal ของ low (apply modifier)"""
    _shade_smooth(low)
    mod = low.modifiers.new('nrm', 'DATA_TRANSFER')
    mod.object = high
    mod.use_loop_data = True
    mod.data_types_loops = {'CUSTOM_NORMAL'}
    mod.loop_mapping = 'POLYINTERP_NEAREST'
    set_active(low)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def make_lod(src, mc, name, tri_keep):
    """คืน (object เมชที่ลดแล้ว, object เมชละเอียด (ใช้อบภาพ แล้วลบทิ้ง), รายงาน)"""
    high, rep_clean = build_source(src, mc, name, tri_keep)
    rep_zones = tag_detail(high, mc['detailZones'], mc['detailStrength'])
    low, delimit = dmesh.decimate_to(high, mc['targetTris'], name + '_mesh', mc)
    transfer_normals(low, high)
    low.vertex_groups.clear()
    while low.data.color_attributes:
        low.data.color_attributes.remove(low.data.color_attributes[0])
    rep = {'clean': rep_clean, 'detailZones': rep_zones, 'delimit': delimit, 'tris': tri_count(low),
           'verts': len(low.data.vertices), 'sourceTris': tri_count(high)}
    return low, high, rep


def vertex_pos(obj):
    """ตำแหน่งจุดยอด (พิกัด glTF) ขนานกับ obj.data.vertices"""
    co = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    return from_bl(co.reshape(-1, 3))


def edges(obj):
    e = np.empty(len(obj.data.edges) * 2, dtype=np.int64)
    obj.data.edges.foreach_get('vertices', e)
    return e.reshape(-1, 2)
