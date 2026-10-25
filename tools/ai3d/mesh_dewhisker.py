# ตัดเส้นหนวดที่ Hunyuan ปั้นเป็นเส้นแข็งยื่นออกจากหน้า (ก่อน project_views · ลายหนวดในภาพผิวพอ)
#   blender -b --factory-startup --python-exit-code 1 -P tools/ai3d/mesh_dewhisker.py -- <in.glb> <out.glb> [--cfg tools/ai3d/som_dewhisker.json]
# เหตุ : ลดโพลีแล้วเส้นหนวดกลายเป็นแผ่นแหลม + กินจุดยอดของงบลดโพลี
# วิธี : ความหนาเฉพาะที่ (ยิงรังสีจากจุดยอดเข้าในตัวตาม −normal) บางกว่า thinFrac × สูง = จุดบาง
#        → กลุ่มจุดบางที่ต่อกัน (≥ minVerts) และอยู่ด้านหน้า (สัดส่วนแกนหน้า-หลัง ≤ frontMaxFrac : แยกจากใบหูที่บางเหมือนกัน)
#        → ขยาย growRings วง → ลบหน้าที่แตะ → ทิ้งเศษลอย → ปิดรู
# แกน Blender : หน้าหัน −Y · ขึ้น +Z
import argparse
import json
import os
import sys

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:]
    p = argparse.ArgumentParser()
    p.add_argument('src')
    p.add_argument('out')
    p.add_argument('--cfg', default=os.path.join(HERE, 'som_dewhisker.json'))
    return p.parse_args(argv)


def load_bm(path):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    bpy.ops.import_scene.gltf(filepath=path)
    bm = bmesh.new()
    for ob in [o for o in bpy.data.objects if o.type == 'MESH']:
        part = ob.data.copy()
        part.transform(ob.matrix_world)
        bm.from_mesh(part)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update()
    return bm


def thickness(bm, height, reach):
    """ระยะเข้าเนื้อตาม −normal (สัดส่วนความสูง) · ไม่โดนภายใน reach = 9"""
    tree = BVHTree.FromBMesh(bm)
    out = {}
    for v in bm.verts:
        n = v.normal
        loc, _, _, d = tree.ray_cast(v.co - n * height * 1e-4, -n, height * reach)
        out[v] = d / height if loc is not None else 9.0
    return out


def thin_groups(bm, thin):
    """กลุ่มจุดบางที่ต่อกันทางขอบ"""
    left, groups = set(thin), []
    while left:
        seed = left.pop()
        group, todo = {seed}, [seed]
        while todo:
            v = todo.pop()
            for e in v.link_edges:
                w = e.other_vert(v)
                if w in left:
                    left.discard(w)
                    group.add(w)
                    todo.append(w)
        groups.append(group)
    return groups


def pick(bm, c):
    zs = [v.co.z for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    height, y0, ydepth = max(zs) - min(zs), min(ys), max(ys) - min(ys)
    th = thickness(bm, height, c['reach'])
    thin = [v for v in bm.verts if th[v] < c['thinFrac']]
    picked = set()
    for g in thin_groups(bm, thin):
        front = max((v.co.y - y0) / ydepth for v in g)
        if len(g) >= c['minVerts'] and front <= c['frontMaxFrac']:
            picked |= g
    for _ in range(c['growRings']):
        picked |= {e.other_vert(v) for v in picked for e in v.link_edges}
    return picked, len(thin)


def drop_loose(bm, min_faces):
    """ทิ้งเกาะที่เล็กกว่า min_faces (ปลายหนวดที่ขาดลอย)"""
    left, dead = set(bm.faces), []
    while left:
        seed = left.pop()
        isl, todo = [seed], [seed]
        while todo:
            f = todo.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g in left:
                        left.discard(g)
                        isl.append(g)
                        todo.append(g)
        if len(isl) < min_faces:
            dead += isl
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    return len(dead)


def cut(bm, picked, c):
    faces = list({f for v in picked for f in v.link_faces})
    bmesh.ops.delete(bm, geom=faces, context='FACES')
    loose = drop_loose(bm, c['minIslandFaces'])
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    rim = [e for e in bm.edges if e.is_boundary]
    filled = bmesh.ops.holes_fill(bm, edges=rim, sides=0)['faces']
    bmesh.ops.triangulate(bm, faces=filled)
    for _ in range(c['fillSmooth']):  # รอยปิดรูเรียบเข้ากับผิวข้างเคียง
        verts = list({v for f in filled if f.is_valid for v in f.verts})
        bmesh.ops.smooth_vert(bm, verts=verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    left = sum(1 for e in bm.edges if e.is_boundary)
    return {'deletedFaces': len(faces), 'looseFaces': loose, 'filledFaces': len(filled), 'openEdgesLeft': left}


def main():
    a = parse()
    with open(a.cfg, encoding='utf-8') as fp:
        c = json.load(fp)
    bm = load_bm(a.src)
    picked, n_thin = pick(bm, c)
    rep = cut(bm, picked, c)
    me = bpy.data.meshes.new('dewhisker')
    bm.to_mesh(me)
    bm.free()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    obj = bpy.data.objects.new('dewhisker', me)
    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=a.out, use_selection=True, export_format='GLB')
    print('DEWHISKER', json.dumps(dict(rep, thinVerts=n_thin, pickedVerts=len(picked), out=a.out)))


main()
