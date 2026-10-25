"""ส่วนที่ต้องใช้ Blender ของดินตัวใหม่ : สร้างเมชจากอาร์เรย์ (พร้อม vertex group = น้ำหนักกระดูก)
· merge จุดซ้ำ · ทิ้งชิ้นจิ๋ว · decimate (รักษาหัว/มือด้วย vertex group) · ดึงอาร์เรย์กลับแบบ glTF · ย่อ texture"""
import math
import os

import bmesh
import bpy
import numpy as np

from prep_din_mesh import drop_small_islands, duplicate, set_active, tri_count

DETAIL = 'detail'


def build_object(name, verts, tris, uv, weights, group_names):
    """อาร์เรย์แบบ glTF (uv ต่อจุดยอด) -> object เมช + vertex group ต่อกระดูก"""
    me = bpy.data.meshes.new(name + '_mesh')
    me.from_pydata(verts.tolist(), [], tris.tolist())
    loop_v = np.empty(len(me.loops), dtype=np.int64)
    me.loops.foreach_get('vertex_index', loop_v)
    me.uv_layers.new(name='UVMap').data.foreach_set('uv', uv[loop_v].astype(np.float32).ravel())
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    for j, gname in enumerate(group_names):
        vg = obj.vertex_groups.new(name=gname)
        for r in np.nonzero(weights[:, j] > 0)[0]:
            vg.add([int(r)], float(weights[r, j]), 'REPLACE')
    return obj


def clean(obj, cfg):
    """merge จุดซ้ำระยะเล็กมาก (UV เก็บรายมุมจึงไม่ขาด) · ทิ้งชิ้นจิ๋วลอย · สามเหลี่ยมล้วน"""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=cfg['merge_distance'])
    removed = drop_small_islands(bm, cfg['min_island_tris'])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return {'verts_before': before, 'verts_after': len(me.vertices), 'tris': tri_count(obj), 'removed_island_tris': removed}


def tag_detail(obj, cfg, group_names):
    """น้ำหนัก vertex group 'detail' = ระดับที่ยอมให้ลด (1 ลดเต็มที่) : จุดที่ผูกกับหัว/มือ/นิ้วมาก ลดน้อยลง"""
    names = set(cfg['detail_bones'])
    if cfg['detail_include_fingers']:
        names |= {n for n in group_names if any(f in n for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Little'))}
    ids = {obj.vertex_groups[n].index for n in names}
    vg = obj.vertex_groups.new(name=DETAIL)
    for v in obj.data.vertices:
        share = sum(g.weight for g in v.groups if g.group in ids)
        vg.add([v.index], 1.0 - cfg['detail_strength'] * min(share, 1.0), 'REPLACE')


def smooth(obj, cfg):
    set_active(obj)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(cfg['smooth_angle_deg']))


def _decimate_once(obj, ratio, delimit, cfg):
    mod = obj.modifiers.new('dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = min(ratio, 1.0)
    mod.use_collapse_triangulate = True
    mod.delimit = set(delimit)
    mod.vertex_group = DETAIL
    mod.vertex_group_factor = cfg['detail_factor']
    set_active(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def decimate_to(src, target, name, cfg):
    """ลองหลายรอบปรับ ratio จนจำนวนสามเหลี่ยมใกล้เป้า (vertex group ทำให้ไม่เชิงเส้น) · ลอง delimit UV ก่อน"""
    best, used = None, None
    for delimit in (cfg['decimate_delimit'], cfg['decimate_delimit_fallback']):
        ratio, last = target / tri_count(src), None
        for _ in range(10):
            dup = duplicate(src, name + '_try')
            _decimate_once(dup, ratio, delimit, cfg)
            n = tri_count(dup)
            if best is None or abs(n - target) < abs(tri_count(best) - target):
                if best is not None:
                    bpy.data.objects.remove(best)
                best, used = dup, list(delimit)
            else:
                bpy.data.objects.remove(dup)
            if abs(n - target) <= target * cfg['tolerance'] or n == last:
                break
            last, ratio = n, ratio * target / n
        if abs(tri_count(best) - target) <= target * cfg['tolerance'] * 2:
            break
    best.name = name
    return best, used


def _dense_groups(obj, group_names):
    gid = {obj.vertex_groups[n].index: j for j, n in enumerate(group_names)}
    out = np.zeros((len(obj.data.vertices), len(group_names)))
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group in gid:
                out[v.index, gid[g.group]] = g.weight
    return out


def limit_weights(dense, count, min_weight):
    """เก็บน้ำหนักมากสุด count ตัวต่อจุด ตัดที่ต่ำกว่า min_weight แล้ว normalize -> (JOINTS uint8, WEIGHTS float32)"""
    idx = np.argsort(-dense, axis=1)[:, :count]
    w = np.take_along_axis(dense, idx, axis=1)
    w[w < min_weight] = 0.0
    w[w.sum(1) <= 0, 0] = 1.0
    w = w / w.sum(1, keepdims=True)
    idx[w == 0] = 0
    return idx.astype(np.uint8), w.astype(np.float32)


def extract(obj, group_names, cfg):
    """เมช Blender -> อาร์เรย์ glTF (แยกจุดยอดตาม UV/normal ต่อมุม) : pos normal uv joints weights indices dense"""
    me = obj.data
    me.calc_loop_triangles()
    nl, nv = len(me.loops), len(me.vertices)
    co = np.empty(nv * 3)
    me.vertices.foreach_get('co', co)
    tri_loops = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get('loops', tri_loops)
    loop_v = np.empty(nl, dtype=np.int64)
    me.loops.foreach_get('vertex_index', loop_v)
    nrm = np.empty(nl * 3)
    me.corner_normals.foreach_get('vector', nrm)
    uv = np.empty(nl * 2)
    me.uv_layers.active.data.foreach_get('uv', uv)
    key = np.hstack([loop_v[:, None].astype(float), uv.reshape(-1, 2), nrm.reshape(-1, 3)])[tri_loops]
    uniq, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    vids = uniq[:, 0].astype(np.int64)
    dense = _dense_groups(obj, group_names)[vids]
    joints, weights = limit_weights(dense, cfg['max_influences'], cfg['min_weight'])
    return {'pos': co.reshape(-1, 3)[vids], 'normal': uniq[:, 3:6], 'uv': uniq[:, 1:3], 'joints': joints,
            'weights': weights, 'indices': inverse.ravel().astype(np.int64), 'dense': dense}


def resize_image(data, mime, out_dir, name, tex_cfg, non_color):
    """ย่อภาพเป็น size (คงสัดส่วน) แล้วเซฟ JPEG -> ไบต์ (เซฟตรงไม่ผ่าน view transform)"""
    os.makedirs(out_dir, exist_ok=True)
    src = os.path.join(out_dir, name + ('_src.png' if mime.endswith('png') else '_src.jpg'))
    with open(src, 'wb') as f:
        f.write(data)
    img = bpy.data.images.load(src, check_existing=False)
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    w, h = img.size
    k = tex_cfg['size'] / max(w, h)
    if k < 1.0:
        img.scale(max(1, round(w * k)), max(1, round(h * k)))
    out = os.path.join(out_dir, '%s_%d.jpg' % (name, max(img.size)))
    img.filepath_raw = out
    img.file_format = 'JPEG'
    img.save(quality=tex_cfg['jpeg_quality'])
    os.remove(src)
    with open(out, 'rb') as f:
        return f.read(), {'src': [w, h], 'out': list(img.size), 'bytes': os.path.getsize(out)}
