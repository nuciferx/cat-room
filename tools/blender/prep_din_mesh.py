"""เตรียมโมเดล "ดิน" ตัวใหม่ (Meshy, ยังไม่มีกระดูก) ให้พร้อมใส่กระดูก
ลดโพลี (lod0 ~10k, lod1 ~3k) · ปรับขนาด/ทิศ/origin ให้ตรงดินเดิม · ย่อ texture · ส่งออก FBX (Mixamo) + GLB
รัน :  F:/game/a/.tools/blender-5.2.1-windows-x64/blender.exe -b --python tools/blender/prep_din_mesh.py
ค่าตัวเลขทั้งหมดอยู่ใน prep_din_mesh.json (คู่กัน) · ผลลัพธ์ลง out_dir (ไม่เข้า git)
ต่อด้วย  python tools/blender/compose_din_compare.py  เพื่อวางภาพเรนเดอร์เป็น compare.png
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'prep_din_mesh.json'), encoding='utf-8'))
OUT = CFG['out_dir']
TEX = os.path.join(OUT, 'tex')
CELLS = os.path.join(OUT, 'cells')
GROUP = 'detail'


def log(*a):
    print('[prep]', *a, flush=True)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def tri_count(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def world_bbox(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return [[min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]]


def r3(v):
    return [round(float(x), 5) for x in v]


def bbox_report(obj):
    lo, hi = world_bbox(obj)
    return {'min': r3(lo), 'max': r3(hi), 'size': r3([hi[i] - lo[i] for i in range(3)])}


def feet_center(obj):
    """จุดกึ่งกลาง XY ของกล่องรอบเท้า (จุดยอดที่ต่ำกว่า z_min + feet_z_max)"""
    mw = obj.matrix_world
    zs = [(mw @ v.co) for v in obj.data.vertices]
    zmin = min(p.z for p in zs)
    feet = [p for p in zs if p.z < zmin + CFG['feet_z_max']]
    xs, ys = [p.x for p in feet], [p.y for p in feet]
    return {'x': (min(xs) + max(xs)) / 2, 'y': (min(ys) + max(ys)) / 2, 'zmin': zmin,
            'x_range': [min(xs), max(xs)], 'y_range': [min(ys), max(ys)]}


def measure_din():
    """อ่านความสูง/เท้า/ทิศหน้าของดินเดิม (อ่านอย่างเดียว)"""
    reset_scene()
    bpy.ops.import_scene.gltf(filepath=CFG['din_glb'])
    obj = bpy.data.objects[CFG['din_mesh_name']]
    lo, hi = world_bbox(obj)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    bone = arm.data.bones['LeftFoot']
    toe_dir_y = (arm.matrix_world @ bone.tail_local).y - (arm.matrix_world @ bone.head_local).y
    info = {'zmin': lo[2], 'zmax': hi[2], 'height': hi[2] - lo[2], 'bbox': bbox_report(obj),
            'feet': feet_center(obj), 'front_axis': '-Y' if toe_dir_y < 0 else '+Y',
            'tris': tri_count(obj)}
    log('din', info['height'], info['front_axis'], info['feet'])
    return info


def import_source():
    reset_scene()
    bpy.ops.import_scene.gltf(filepath=CFG['source_glb'])
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    assert len(meshes) == 1, 'ต้นฉบับควรมี mesh เดียว'
    return meshes[0]


def bake_transform(obj, matrix):
    obj.data.transform(matrix @ obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    obj.parent = None
    obj.data.update()


def place_like_din(obj, din):
    """หมุนตามค่า config · ย่อ/ขยายให้สูงเท่าดิน · เท้าแตะ z=0 · กึ่งกลางเท้าตรงดินเดิม"""
    before = bbox_report(obj)
    rot = Matrix.Rotation(math.radians(CFG['rotate_z_deg']), 4, 'Z')
    bake_transform(obj, rot)
    lo, hi = world_bbox(obj)
    scale = din['height'] / (hi[2] - lo[2])
    bake_transform(obj, Matrix.Scale(scale, 4))
    feet = feet_center(obj)
    shift = Vector((-feet['x'], din['feet']['y'] - feet['y'], -feet['zmin']))
    bake_transform(obj, Matrix.Translation(shift))
    return {'bbox_before': before, 'rotate_z_deg': CFG['rotate_z_deg'], 'scale': scale,
            'shift': r3(shift), 'bbox_after': bbox_report(obj), 'feet_after': feet_center(obj)}


def islands(bm):
    """แยกชิ้นที่ไม่ติดกัน คืนรายการ (รายการหน้า) เรียงใหญ่ไปเล็ก"""
    seen, comps = set(), []
    for f in bm.faces:
        if f in seen:
            continue
        comp, stack = [], [f]
        seen.add(f)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for e in cur.edges:
                stack.extend(x for x in e.link_faces if x not in seen and not seen.add(x))
        comps.append(comp)
    return sorted(comps, key=len, reverse=True)


def drop_small_islands(bm, min_tris):
    doomed = [f for comp in islands(bm) if len(comp) < min_tris for f in comp]
    bmesh.ops.delete(bm, geom=doomed, context='FACES')
    return len(doomed)


def clean_mesh(obj):
    """merge by distance (ระยะเล็กมาก — UV เก็บรายมุมอยู่แล้วจึงไม่ขาด) · ทิ้งชิ้นจิ๋วลอย · ล้าง normal เดิม"""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    verts_before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=CFG['merge_distance'])
    islands_before = [len(c) for c in islands(bm)]
    removed = drop_small_islands(bm, CFG['min_island_tris'])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.triangulate(bm, faces=bm.faces)
    islands_after = [len(c) for c in islands(bm)]
    bm.to_mesh(me)
    bm.free()
    set_active(obj)
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    return {'verts_before': verts_before, 'verts_after': len(me.vertices), 'tris': tri_count(obj),
            'islands_before_top': islands_before[:12], 'islands_before_count': len(islands_before),
            'removed_small_island_tris': removed, 'islands_after': islands_after}


def set_active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def in_region(p, name):
    r = CFG['detail_regions'][name]
    if name == 'head':
        return p.z >= r['z_min']
    return abs(p.x) >= r['abs_x_min'] and r['z_min'] <= p.z <= r['z_max']


def tag_detail_group(obj):
    """น้ำหนัก vertex group ของ Decimate = ระดับที่ "ยอมให้ลด" (1 = ลดเต็มที่, 0 = ห้ามแตะ)
    ตัว/ขากางเกง = body_weight · หัว/มือ = detail_weight (ต่ำกว่า จึงเก็บรายละเอียดไว้มากกว่า)"""
    vg = obj.vertex_groups.get(GROUP) or obj.vertex_groups.new(name=GROUP)
    heads, hands, body = [], [], []
    for v in obj.data.vertices:
        if in_region(v.co, 'head'):
            heads.append(v.index)
        elif in_region(v.co, 'hand'):
            hands.append(v.index)
        else:
            body.append(v.index)
    vg.add(body, CFG['body_weight'], 'REPLACE')
    vg.add(heads + hands, CFG['detail_weight'], 'REPLACE')
    return {'head_verts': len(heads), 'hand_verts': len(hands), 'body_verts': len(body)}


def region_tris(obj):
    """จำนวนสามเหลี่ยมที่จุดกลางอยู่ในหัว / มือซ้าย-ขวา — ไว้ดูว่ารายละเอียดถูกเก็บไว้ไหม"""
    me = obj.data
    me.calc_loop_triangles()
    out = {'head': 0, 'hand_left': 0, 'hand_right': 0}
    for t in me.loop_triangles:
        c = sum((me.vertices[i].co for i in t.vertices), Vector()) / 3
        if in_region(c, 'head'):
            out['head'] += 1
        elif in_region(c, 'hand'):
            out['hand_left' if c.x > 0 else 'hand_right'] += 1
    return out


def duplicate(obj, name):
    dup = obj.copy()
    dup.data = obj.data.copy()
    dup.name = name
    dup.data.name = name + '_mesh'
    bpy.context.scene.collection.objects.link(dup)
    return dup


def apply_decimate(obj, ratio, delimit):
    mod = obj.modifiers.new('dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    mod.delimit = set(delimit)
    mod.vertex_group = GROUP
    mod.vertex_group_factor = CFG['detail_factor']
    set_active(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)


def decimate_to(src, target, name, delimit):
    """ลองหลายรอบปรับ ratio จนจำนวนสามเหลี่ยมอยู่ในช่วง tolerance ของเป้า (ผลของ weight ทำให้ไม่เชิงเส้น)"""
    ratio, best, last = target / tri_count(src), None, None
    for attempt in range(10):
        dup = duplicate(src, name)
        apply_decimate(dup, min(ratio, 1.0), delimit)
        n = tri_count(dup)
        log(name, 'delimit', delimit, 'attempt', attempt, 'ratio', round(ratio, 4), '->', n)
        if best is None or abs(n - target) < abs(tri_count(best) - target):
            if best is not None:
                bpy.data.objects.remove(best)
            best = dup
        else:
            bpy.data.objects.remove(dup)
        if abs(n - target) <= target * CFG['tolerance'] or n == last:
            break
        last = n
        ratio *= target / n
    return best


def make_lod(src, target, name):
    for delimit in (CFG['decimate_delimit'], CFG['decimate_delimit_fallback']):
        obj = decimate_to(src, target, name, delimit)
        if abs(tri_count(obj) - target) <= target * CFG['tolerance'] * 2:
            return obj, delimit
        bpy.data.objects.remove(obj)
    raise RuntimeError('ลดโพลีไม่ถึงเป้า ' + name)


def smooth_shade(obj):
    set_active(obj)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(CFG['smooth_angle_deg']))


def find_source_images(obj):
    """คืน dict base / mr / normal จาก node ของวัสดุ Meshy"""
    nt = obj.data.materials[0].node_tree
    out = {}
    for link in nt.links:
        if link.from_node.type == 'TEX_IMAGE' and link.to_node.type == 'BSDF_PRINCIPLED':
            out['base'] = link.from_node.image
        if link.from_node.type == 'TEX_IMAGE' and link.to_node.type == 'NORMAL_MAP':
            out['normal'] = link.from_node.image
        if link.from_node.type == 'TEX_IMAGE' and link.to_node.type == 'SEPARATE_COLOR':
            out['mr'] = link.from_node.image
    return out


def save_small_textures(images):
    """ย่อเป็น texture_size แล้วเซฟเป็น JPEG ลง tex/ (ไม่ผ่าน view transform จึงไม่เพี้ยนสี)"""
    os.makedirs(TEX, exist_ok=True)
    size, paths, sizes = CFG['texture_size'], {}, {}
    for key, img in images.items():
        small = img.copy()
        small.scale(size, size)
        path = os.path.join(TEX, f'din_new_{key}_{size}.jpg')
        small.filepath_raw = path
        small.file_format = 'JPEG'
        small.save(quality=CFG['jpeg_quality'])
        paths[key] = path
        sizes[key] = {'src': list(img.size), 'out': [size, size], 'bytes': os.path.getsize(path)}
    return paths, sizes


def build_material(name, paths, with_pbr):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']

    def tex(key, srgb):
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(paths[key], check_existing=False)
        node.image.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
        return node

    nt.links.new(tex('base', True).outputs['Color'], bsdf.inputs['Base Color'])
    if with_pbr:
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(tex('mr', False).outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
        nmap = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(tex('normal', False).outputs['Color'], nmap.inputs['Color'])
        nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        bsdf.inputs['Roughness'].default_value = 0.8
    return mat


def assign_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def export_glb(obj, path):
    set_active(obj)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True,
                              export_image_format='JPEG', export_jpeg_quality=CFG['jpeg_quality'],
                              export_yup=True, export_apply=False, export_cameras=False,
                              export_lights=False)


def export_fbx(obj, path):
    set_active(obj)
    f = CFG['fbx']
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'},
                             axis_forward=f['axis_forward'], axis_up=f['axis_up'],
                             path_mode=f['path_mode'], embed_textures=f['embed_textures'],
                             mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
                             use_mesh_modifiers=False)


def setup_render():
    sc = bpy.context.scene
    r = CFG['render']
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = sc.render.resolution_y = r['cell']
    sc.render.image_settings.file_format = 'PNG'
    sc.display.shading.light = 'STUDIO'
    sc.display.shading.color_type = 'TEXTURE'
    sc.display.render_aa = '8'
    world = bpy.data.worlds.new('w')
    world.color = (0.82, 0.84, 0.86)
    sc.world = world
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    co = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(co)
    sc.camera = co
    return sc, co


def render_cells(label_objs):
    """เรนเดอร์ภาพ หน้า/ข้าง/ใบหน้า/มือ ของแต่ละ object (ทีละตัว) ลง cells/"""
    os.makedirs(CELLS, exist_ok=True)
    sc, co = setup_render()
    r = CFG['render']
    views = {
        'front': ((0, -6, r['body_scale'] / 2 - 0.15), (math.pi / 2, 0, 0), r['body_scale']),
        'side': ((6, 0, r['body_scale'] / 2 - 0.15), (math.pi / 2, 0, math.pi / 2), r['body_scale']),
        'face': ((r['face_center'][0], -6, r['face_center'][1]), (math.pi / 2, 0, 0), r['face_scale']),
        'hand': ((r['hand_center'][0], -6, r['hand_center'][1]), (math.pi / 2, 0, 0), r['hand_scale']),
    }
    for label, obj in label_objs.items():
        for o in label_objs.values():
            o.hide_render = o is not obj
        for vname, (loc, rot, scale) in views.items():
            co.location, co.rotation_euler, co.data.ortho_scale = loc, rot, scale
            sc.render.filepath = os.path.join(CELLS, f'{label}_{vname}.png')
            bpy.ops.render.render(write_still=True)


def reimport_stats(path):
    """เปิดไฟล์ที่ export แล้วกลับเข้า Blender วัดซ้ำ (จำนวนสามเหลี่ยม + bbox + ทิศหน้า)"""
    reset_scene()
    if path.endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    tris = sum(tri_count(o) for o in meshes)
    box = bbox_report(meshes[0])
    return {'meshes': len(meshes), 'tris': tris, 'bbox': box, 'images': [i.name for i in bpy.data.images]}


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {'config_file': 'tools/blender/prep_din_mesh.json'}
    din = measure_din()
    report['din'] = din
    obj = import_source()
    images = find_source_images(obj)
    report['source_tris_raw'] = tri_count(obj)
    report['placement'] = place_like_din(obj, din)
    report['clean'] = clean_mesh(obj)
    report['detail_group'] = tag_detail_group(obj)
    obj.name, obj.data.name = 'Din_source', 'Din_source_mesh'
    smooth_shade(obj)
    report['region_tris'] = {'source': region_tris(obj)}

    paths, report['textures'] = save_small_textures(images)
    lods = {}
    for label, target in (('Din_LOD0', CFG['lod0_tris']), ('Din_LOD1', CFG['lod1_tris'])):
        lod, delimit = make_lod(obj, target, label)
        smooth_shade(lod)
        lods[label] = lod
        report.setdefault('decimate', {})[label] = {'target': target, 'tris': tri_count(lod), 'delimit': delimit}
        report['region_tris'][label] = region_tris(lod)
    render_cells({'1_source': obj, '2_lod0': lods['Din_LOD0'], '3_lod1': lods['Din_LOD1']})

    full_mat, base_mat = build_material('Din_new_pbr', paths, True), build_material('Din_new_base', paths, False)
    files = {}
    assign_material(lods['Din_LOD0'], base_mat)
    export_fbx(lods['Din_LOD0'], os.path.join(OUT, 'din_new_lod0.fbx'))
    for label, name in (('Din_LOD0', 'din_new_lod0.glb'), ('Din_LOD1', 'din_new_lod1.glb')):
        assign_material(lods[label], full_mat if CFG['glb_keep_pbr'] else base_mat)
        export_glb(lods[label], os.path.join(OUT, name))
    report['fbx_export'] = CFG['fbx']
    for name in ('din_new_lod0.fbx', 'din_new_lod0.glb', 'din_new_lod1.glb'):
        files[name] = {'bytes': os.path.getsize(os.path.join(OUT, name))}
    for name in files:
        files[name]['reimport'] = reimport_stats(os.path.join(OUT, name))
    report['files'] = files
    json.dump(report, open(os.path.join(OUT, 'report.json'), 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    log('เสร็จ')


if __name__ == '__main__':
    main()
