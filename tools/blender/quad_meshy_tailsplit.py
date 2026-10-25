"""bb : แยกพุ่มหางเป็นชิ้นต่างหาก (เมชเดียวกัน คนละเกาะ) ให้หางหมุนได้มากโดยผิวรอยต่อไม่ยืด
เหตุ : พุ่มหางมุ่ยเป็นก้อนใหญ่ติดก้นกว้าง ~10 ซม. ผันผิวตามกระดูกหางเกิน ~30° ผิวรอยต่อยืดทุกค่า (log 2026-10-24)
ขั้น (หลังลดโพลี ก่อนแตก UV/อบ) :
  1) ป้ายกระดูกต่อจุด (quad_meshy_weights.label) → หน้าที่จุดเป็นหางอย่างน้อย minTailVerts จุด = หาง · เก็บเกาะใหญ่สุด
  2) ตัดขอบระหว่างหาง/ตัว (split_edges) → ตัวเป็นรู · หางเป็นปากเปิด
  3) ปิดรูของตัว (ผิวเรียบ ใต้โคนหาง)
  4) ต่อปากหางยื่นเข้าไปในตัว : ดึงจุดขอบเข้าหาโคนกระดูก tail1 สัดส่วน sinkFrac แล้วปิดปาก → หางหมุนแล้วโคนยังจมในตัว
  ผล : จุดของชิ้นหางมีค่า attribute PIECE = 1 (rig_stage อ่านไปบังคับน้ำหนัก : ชิ้นหาง = กระดูกหางล้วน · ตัว = ห้ามกระดูกหาง)"""
import bmesh
import numpy as np

import quad_meshy_lod as qlod
import quad_meshy_rig as qrig
import quad_meshy_weights as qw

PIECE = 'tail_piece'
# หน้าที่สร้างใหม่ (ปิดรูก้น โคนหางที่ยื่นเข้าตัว ปิดปากหาง) อยู่ในตัว อบภาพแล้วรังสีไม่โดนผิว (ดำ) → quad_meshy_bake ทาสีขนเฉลี่ย
FILL = 'tail_fill'


def _tail_faces(bm, is_tail, need):
    faces = [f for f in bm.faces if sum(is_tail[v.index] for v in f.verts) >= need]
    return _largest_island(set(faces)), len(faces)


def _largest_island(faces):
    """เกาะใหญ่สุด (ต่อกันทางขอบ) ในชุดหน้า"""
    left, best = set(faces), set()
    while left:
        seed = left.pop()
        island, todo = {seed}, [seed]
        while todo:
            f = todo.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g in left:
                        left.discard(g)
                        island.add(g)
                        todo.append(g)
        if len(island) > len(best):
            best = island
    return best


def _smooth_set(tail, rounds):
    """bb : เกลี่ยขอบชุดหน้าหาง (รอยตัดเป็นฟันเลื่อย → ผิวปิดรูเป็นแฉกหนาม) : หน้าตัวที่มีขอบติดหาง ≥ 2 ด้าน → เข้าหาง
    หน้าหางที่มีขอบติดตัว ≥ 2 ด้าน → ออก · ทำ rounds รอบ (0 = แบบเดิม)"""
    tail = set(tail)
    for _ in range(rounds):
        border = {g for f in tail for e in f.edges for g in e.link_faces if g not in tail}
        grow = {f for f in border if sum(any(g in tail for g in e.link_faces if g is not f) for e in f.edges) >= 2}
        tail |= grow
        shrink = {f for f in tail if sum(not any(g in tail for g in e.link_faces if g is not f) for e in f.edges) >= 2}
        tail -= shrink
    return _largest_island(tail)


def _seam(tail):
    """ขอบที่หน้าหนึ่งเป็นหาง อีกหน้าเป็นตัว"""
    edges = {e for f in tail for e in f.edges}
    return [e for e in edges if len(e.link_faces) == 2 and sum(g in tail for g in e.link_faces) == 1]


def _open_edges(faces):
    return [e for e in {e for f in faces for e in f.edges} if len(e.link_faces) == 1]


def _close(bm, edges, anchor, frac):
    """ปิดรูด้วยพัดจากจุดกลางใหม่ (ทนวงที่ไม่เรียบ/จุดซ้ำซึ่ง holes_fill ปิดไม่ได้) · จุดกลาง = ค่าเฉลี่ยขอบ ดึงเข้าหา anchor สัดส่วน frac
    ทิศหน้าใหม่กลับกับหน้าข้างเคียงที่ใช้ขอบเดียวกัน (normal ไปทางเดียวกัน)"""
    if not edges:
        return []
    verts = list({v for e in edges for v in e.verts})
    mid = sum((v.co for v in verts[1:]), verts[0].co.copy()) / len(verts)
    center = bm.verts.new(mid.lerp(anchor, frac))
    faces = []
    for e in edges:
        loop = e.link_loops[0]
        a, b = loop.vert, loop.link_loop_next.vert
        faces.append(bm.faces.new((b, a, center)))
    return faces


def _sink(bm, rim, anchor, frac):
    """ต่อปากหางยื่นเข้าหา anchor (พิกัด Blender) → (หน้าใหม่, จุดใหม่)"""
    ret = bmesh.ops.extrude_edge_only(bm, edges=rim)
    verts = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMVert)]
    for v in verts:
        v.co = v.co.lerp(anchor, frac)
    faces = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMFace)]
    return faces, verts


def split(obj, cfg):
    """แยกชิ้นหางใน obj (แก้ในที่) · คืนรายงาน"""
    tc = cfg['tailSplit']
    _, rig = qrig.build(cfg['rig'])
    pos = qlod.vertex_pos(obj)
    lab, _ = qw.label(pos, rig, cfg['weights'])
    is_tail = np.isin(lab, qw.tail_bones(rig))
    for box in tc.get('addBoxes', []):  # ลำหางด้านหลังที่ป้ายน้ำหนักนับเป็นตัว
        is_tail |= np.all((pos >= np.asarray(box['min'])) & (pos <= np.asarray(box['max'])), axis=1)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    layer = bm.verts.layers.int.new(PIECE)  # ใส่ชั้นข้อมูลก่อนแก้เมช (ใส่ทีหลังแล้วตัวอ้างอิงหน้าเดิมใช้ไม่ได้)
    fill = bm.faces.layers.int.new(FILL)
    tail, n_cand = _tail_faces(bm, is_tail, tc['minTailVerts'])
    tail = _smooth_set(tail, tc.get('smoothRounds', 0))
    seam = _seam(tail)
    bmesh.ops.split_edges(bm, edges=seam)
    body = [f for f in bm.faces if f not in tail]
    hole = _open_edges(body)
    anchor = qlod.to_bl([rig.head['tail1']])[0]
    caps = _close(bm, hole, anchor, tc['capFrac'])
    sunk, sunk_verts = _sink(bm, _open_edges(tail), anchor, tc['sinkFrac'])
    plug = _close(bm, _open_edges(list(tail) + sunk), anchor, 0.0)
    piece = {v for f in list(tail) + sunk + plug for v in f.verts}
    for v in piece:
        v[layer] = 1
    for f in caps + sunk + plug:
        f[fill] = 1
    rep = {'tailVerts': int(is_tail.sum()), 'candFaces': n_cand, 'tailFaces': len(tail), 'seamEdges': len(seam),
           'bodyCapTris': len(caps), 'sinkVerts': len(sunk_verts), 'plugTris': len(plug), 'pieceVerts': len(piece)}
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return rep


def _fill_vertex_normals(me, flag):
    """ค่าเฉลี่ย normal ของหน้าเติมรอบแต่ละจุด (เงาเรียบภายในแผ่นปิดรู)"""
    acc = {}
    for poly in me.polygons:
        if flag[poly.index]:
            for vi in poly.vertices:
                acc[vi] = acc.get(vi, np.zeros(3)) + np.array(poly.normal)
    return {vi: tuple(n / max(np.linalg.norm(n), 1e-9)) for vi, n in acc.items()}


def flat_fill_normals(obj, smooth=False):
    """bb : หน้าปิดรู/โคนหางที่สร้างใหม่ → normal เงา = normal ของหน้าเอง (smooth = เฉลี่ยรอบจุดในแผ่นเติม · cat2 แผ่นปิดก้นโค้งนูน)
    (โอน normal จากเมชละเอียดแล้วได้ทิศของผิวหางที่ทับอยู่ → แผ่นปิดรูมืดดำ) · คืนจำนวนหน้า"""
    me = obj.data
    attr = me.attributes.get(FILL)
    if attr is None:
        return 0
    flag = np.empty(len(me.polygons), dtype=np.int32)
    attr.data.foreach_get('value', flag)
    normals = [tuple(n.vector) for n in me.corner_normals]
    vn = _fill_vertex_normals(me, flag) if smooth else {}
    for poly in me.polygons:
        if flag[poly.index]:
            for li in poly.loop_indices:
                normals[li] = vn.get(me.loops[li].vertex_index, tuple(poly.normal))
    me.normals_split_custom_set(normals)
    return int(flag.sum())


def piece_mask(obj):
    """จุดของชิ้นหาง (bool ต่อจุด) แล้วลบ attribute ทิ้ง (ไม่ให้ติดไปใน glb) · ไม่มี attribute = None"""
    attr = obj.data.attributes.get(PIECE)
    if attr is None:
        return None
    v = np.empty(len(obj.data.vertices), dtype=np.int32)
    attr.data.foreach_get('value', v)
    obj.data.attributes.remove(attr)
    if obj.data.attributes.get(FILL) is not None:
        obj.data.attributes.remove(obj.data.attributes[FILL])
    return v.astype(bool)
