"""อบภาพใหม่ลงเมชที่ลดโพลีแล้ว (Blender Cycles · selected to active) : สีพื้น (DIFFUSE COLOR) + normal (tangent)
เหตุที่ไม่ใช้ UV เดิมของ Meshy : UV เดิมเป็นเกาะเล็กจำนวนมาก ลดโพลีเหลือ ~4k สามเหลี่ยมแล้วภาพเพี้ยนเป็นปื้น
ขั้น : เมชละเอียดใส่วัสดุจากภาพต้นทาง (base ที่ปรับปื้นแล้ว + normal map) → เมชหยาบแตก UV ใหม่ (smart project) → อบ → ภาพ JPEG ขนาด bake.size"""
import os

import bpy
import numpy as np

from prep_din_mesh import set_active
from quad_meshy_altmask import composite, region_mask, tri_mask
from quad_meshy_lod import TONE

SRC_BASE_NODE = 'src_base'
FILL = 'tail_fill'  # bb : ค่าเดียวกับ quad_meshy_tailsplit.FILL (หน้าในตัวที่รังสีอบไม่โดนผิว)


def _src_image(src, key, work_dir, name, non_color):
    data, mime = src.image(key)
    path = os.path.join(work_dir, '%s_src_%s.%s' % (name, key, 'png' if mime.endswith('png') else 'jpg'))
    with open(path, 'wb') as f:
        f.write(data)
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    return img


def _base_color(nt, tex, flat_path):
    """ช่องสีพื้น : ไม่มีภาพปรับ = ภาพต้นทาง · มี = ผสม ภาพปรับ ↔ ภาพต้นทาง ตามสีมุม TONE (1 = ภาพต้นทาง)"""
    if flat_path is None:
        return tex.outputs['Color']
    flat = nt.nodes.new('ShaderNodeTexImage')
    flat.image = bpy.data.images.load(flat_path, check_existing=False)
    tone = nt.nodes.new('ShaderNodeVertexColor')
    tone.layer_name = TONE
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    nt.links.new(tone.outputs['Color'], mix.inputs['Factor'])
    nt.links.new(flat.outputs['Color'], mix.inputs['A'])
    nt.links.new(tex.outputs['Color'], mix.inputs['B'])
    return mix.outputs['Result']


def source_material(high, src, work_dir, name, flat_path):
    """วัสดุของเมชละเอียด (ใช้เป็นต้นทางของการอบเท่านั้น) : สีพื้นตาม _base_color + normal map ของต้นทาง"""
    mat = bpy.data.materials.new(name + '_src')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.name = SRC_BASE_NODE
    tex.image = _src_image(src, 'base', work_dir, name, False)
    nt.links.new(_base_color(nt, tex, flat_path), bsdf.inputs['Base Color'])
    if src.image('normal') is None:  # bb : ต้นทาง Hunyuan ไม่มี normal map (รายละเอียดผิวมาจากเมชละเอียดอย่างเดียว)
        high.data.materials.clear()
        high.data.materials.append(mat)
        return
    ntex = nt.nodes.new('ShaderNodeTexImage')
    ntex.image = _src_image(src, 'normal', work_dir, name, True)
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(ntex.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    high.data.materials.clear()
    high.data.materials.append(mat)


def unwrap(low, bc):
    """UV ใหม่ทั้งเมช (ลบ UV เดิม)"""
    me = low.data
    while me.uv_layers:
        me.uv_layers.remove(me.uv_layers[0])
    me.uv_layers.new(name='UVMap')
    set_active(low)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=bc['uvAngleRad'], island_margin=bc['uvMargin'])
    bpy.ops.object.mode_set(mode='OBJECT')


def _target(low, name, size, non_color):
    img = bpy.data.images.new(name, size, size, alpha=False)
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    mat = low.data.materials[0] if low.data.materials else bpy.data.materials.new(low.name + '_bake')
    if not low.data.materials:
        mat.use_nodes = True
        low.data.materials.append(mat)
    node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = img
    mat.node_tree.nodes.active = node
    return img, node, mat


def _bake_cage(low, high, bc, kind, img_name, non_color, cage):
    img, node, mat = _target(low, img_name, bc['size'], non_color)
    bpy.ops.object.select_all(action='DESELECT')
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    kw = {'pass_filter': {'COLOR'}} if kind == 'DIFFUSE' else {'normal_space': 'TANGENT'}
    bpy.ops.object.bake(type=kind, use_selected_to_active=True, cage_extrusion=cage['cageM'],
                        max_ray_distance=cage['rayM'], margin=bc['marginPx'], use_clear=True, **kw)
    mat.node_tree.nodes.remove(node)
    return img


def _bake_one(low, high, bc, kind, img_name, non_color):
    """bb : bake.nearCage = อบซ้ำด้วยระยะรังสีสั้นแล้วใช้เฉพาะในเขต region (หน้า : ร่องตาลึก ระยะ 3 ซม. ยิงไปโดนจมูก/สันจมูก
    → หัวตาเป็นแผ่นขาว/จุดชมพู · ระยะสั้นทั้งตัวไม่ได้ หาง/หลังที่ลดโพลีแล้วผิวห่างกว่ารังสี → จุดดำ)"""
    img = _bake_cage(low, high, bc, kind, img_name, non_color, bc)
    near = bc.get('nearCage')
    if near:
        close = _bake_cage(low, high, bc, kind, img_name + '_near', non_color, near)
        _merge_region(low, img, np.array(img.pixels[:]), np.array(close.pixels[:]), near['region'])
        bpy.data.images.remove(close)
    return img


def _save(img, path, quality):
    img.filepath_raw = path
    img.file_format = 'JPEG'
    img.save(quality=quality)
    out = bpy.data.images.load(path, check_existing=False)
    out.colorspace_settings.name = img.colorspace_settings.name
    out.pack()
    bpy.data.images.remove(img)
    return out


def bake(low, high, src, bc, work_dir, name, flat_path):
    """คืน ({'base': ภาพ, 'normal': ภาพ}, รายงาน, พิกเซลดิบของภาพสีพื้นก่อนเข้ารหัส JPEG (bb : ให้ bake_alts))"""
    source_material(high, src, work_dir, name, flat_path)
    unwrap(low, bc)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = bc['samples']
    sc.render.bake.margin_type = 'EXTEND'
    sc.view_settings.view_transform = 'Standard'
    out = {}
    for key, kind, non_color in (('base', 'DIFFUSE', False), ('normal', 'NORMAL', True)):
        img = _bake_one(low, high, bc, kind, '%s_%s' % (name, key), non_color)
        _fill_hidden(low, img, key, bc['marginPx'])
        if key == 'base':
            raw = np.array(img.pixels[:])
        path = os.path.join(work_dir, '%s_%s_%d.jpg' % (name, key, bc['size']))
        out[key] = _save(img, path, bc['jpegQuality'])
    rep = {'size': bc['size'], 'bytes': {k: os.path.getsize(v.filepath_raw) for k, v in out.items()}}
    return out, rep, raw


def _uv_tris(low):
    """(จุดยอด glTF n×3, ดัชนีสามเหลี่ยม m×3, UV มุม m×3×2) ของเมชหยาบ"""
    me = low.data
    me.calc_loop_triangles()
    mw = low.matrix_world
    co = np.array([(mw @ v.co)[:] for v in me.vertices])
    pos = np.column_stack([co[:, 0], co[:, 2], -co[:, 1]])
    uv = me.uv_layers.active.data
    tris = np.array([t.vertices[:] for t in me.loop_triangles])
    tri_uv = np.array([[uv[li].uv[:] for li in t.loops] for t in me.loop_triangles])
    return pos, tris, tri_uv


def _merge_region(low, img, base_px, alt_px, region):
    """img = base_px นอกเขต region · alt_px ในเขต (ดู quad_meshy_altmask) · คืนสัดส่วนพื้นที่เขต"""
    size = img.size[0]
    pos, tris, tri_uv = _uv_tris(low)
    mask = region_mask(pos, tris, tri_uv, size, region)
    img.pixels = composite(base_px.reshape(size, size, 4), alt_px.reshape(size, size, 4), mask).ravel()
    return float(mask.mean())


def _fill_hidden(low, img, key, grow_px):
    """bb : หน้าที่ติด FILL (ปิดรูก้น/โคนหางในตัว) → สีพื้น = ค่ากลางของสีที่อบได้ทั้งตัว · normal = แบน · ไม่มี = ไม่ทำ"""
    attr = low.data.attributes.get(FILL)
    if attr is None:
        return
    flag = np.empty(len(low.data.polygons), dtype=np.int32)
    attr.data.foreach_get('value', flag)
    _, _, tri_uv = _uv_tris(low)
    poly = np.array([t.polygon_index for t in low.data.loop_triangles])
    size = img.size[0]
    hidden = tri_mask(tri_uv, size, np.nonzero(flag[poly] == 1)[0], grow_px)
    px = np.array(img.pixels[:]).reshape(size, size, 4)
    if key == 'base':
        seen = tri_mask(tri_uv, size, np.nonzero(flag[poly] == 0)[0], 0) & ~hidden
        px[hidden, :3] = np.median(px[seen, :3], axis=0)
    else:
        px[hidden, :3] = (0.5, 0.5, 1.0)
    img.pixels = px.ravel()


def _limit_to_region(low, img, base_raw, region):
    """bb : ภาพชุดอื่นต่างจากภาพหลักได้เฉพาะในเขต region · แก้พิกเซลของ img ในที่"""
    return _merge_region(low, img, base_raw, np.array(img.pixels[:]), region)


def bake_alts(low, high, alts, bc, work_dir, name, base_raw=None):
    """bb : ภาพสีพื้นชุดอื่นบน UV เดียวกัน (เช่น หลับตา) · alts = [(ชื่อ, ไบต์ภาพต้นทาง, mime, path ปลายทาง .jpg, region หรือ None)]
    ต้นทางต้องเป็นภาพที่ UV ตรงกับภาพหลักทุกพิกเซล (cat_touchup --atlas ชุดเดียวกัน) · ใช้กับต้นทางที่ไม่มีภาพปรับปื้น (tone) เท่านั้น
    region + base_raw = นอกเขต region ใช้พิกเซลดิบของภาพหลัก → เข้ารหัส JPEG แล้วได้บล็อกเดียวกับภาพหลัก (กันจุดต่างที่เกิดจากการอบ)"""
    node = high.data.materials[0].node_tree.nodes[SRC_BASE_NODE]
    rep = {}
    for key, data, mime, out_path, region in alts:
        path = os.path.join(work_dir, '%s_src_%s.%s' % (name, key, 'png' if mime.endswith('png') else 'jpg'))
        with open(path, 'wb') as f:
            f.write(data)
        node.image = bpy.data.images.load(path, check_existing=False)
        img = _bake_one(low, high, bc, 'DIFFUSE', '%s_%s' % (name, key), False)
        rep[key] = {}
        if region and base_raw is not None:
            rep[key]['maskFraction'] = round(_limit_to_region(low, img, base_raw, region), 5)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        img.filepath_raw = out_path
        img.file_format = 'JPEG'
        img.save(quality=bc['jpegQuality'])
        bpy.data.images.remove(img)
        rep[key]['bytes'] = os.path.getsize(out_path)
    return rep
