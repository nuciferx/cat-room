"""อ่าน/เขียน GLB แบบดิบ (ไม่พึ่ง Blender) : เปลี่ยนเฉพาะ animation ที่ระบุ ที่เหลือคงไบต์เดิม
- add_animation : ต่อ accessor/bufferView ของท่าใหม่ท้ายไบนารี
- compact       : ทิ้ง accessor/bufferView ที่ไม่มีใครอ้างถึง (ท่าเก่าที่ถูกแทน) แล้วจัดไบนารีใหม่
"""
import json
import struct

MAGIC = 0x46546C67
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942
F32 = 5126
TARGET_NONE = None
TYPE_COMPONENTS = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}


class Glb:
    def __init__(self, gltf, binary):
        self.gltf = gltf
        self.bin = bytearray(binary)


def read_glb(path):
    with open(path, 'rb') as f:
        data = f.read()
    magic, _version, _length = struct.unpack_from('<III', data, 0)
    if magic != MAGIC:
        raise ValueError('ไม่ใช่ไฟล์ GLB: ' + path)
    gltf, binary, off = None, b'', 12
    while off < len(data):
        size, kind = struct.unpack_from('<II', data, off)
        body = data[off + 8: off + 8 + size]
        if kind == CHUNK_JSON:
            gltf = json.loads(body.decode('utf-8'))
        elif kind == CHUNK_BIN:
            binary = body
        off += 8 + size
    return Glb(gltf, binary)


def _pad(data, fill):
    return data + fill * ((-len(data)) % 4)


def write_glb(glb, path):
    glb.gltf['buffers'] = [{'byteLength': len(glb.bin)}]
    js = _pad(json.dumps(glb.gltf, separators=(',', ':')).encode('utf-8'), b' ')
    bn = _pad(bytes(glb.bin), b'\0')
    total = 12 + 8 + len(js) + 8 + len(bn)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', MAGIC, 2, total))
        f.write(struct.pack('<II', len(js), CHUNK_JSON) + js)
        f.write(struct.pack('<II', len(bn), CHUNK_BIN) + bn)


def _append_accessor(glb, values, comps, acc_type, with_minmax):
    """เพิ่ม accessor float32 ท้ายไบนารี คืนดัชนี accessor"""
    g = glb.gltf
    while len(glb.bin) % 4:
        glb.bin.append(0)
    offset = len(glb.bin)
    glb.bin += struct.pack('<%df' % len(values), *values)
    g.setdefault('bufferViews', []).append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(values) * 4})
    acc = {'bufferView': len(g['bufferViews']) - 1, 'componentType': F32, 'count': len(values) // comps, 'type': acc_type}
    if with_minmax:
        acc['min'], acc['max'] = [min(values)], [max(values)]
    g.setdefault('accessors', []).append(acc)
    return len(g['accessors']) - 1


def add_animation(glb, name, tracks):
    """tracks = [(ชื่อโหนด, 'rotation'|'translation', [เวลา], [ค่าแบนราบ])] · interpolation LINEAR
    ท่าชื่อซ้ำของเดิมถูกถอดก่อน (ตำแหน่งในรายการเดิมคงไว้)"""
    g = glb.gltf
    index = {n.get('name'): i for i, n in enumerate(g['nodes'])}
    time_cache, samplers, channels = {}, [], []
    for node, path, times, values in tracks:
        key = tuple(times)
        if key not in time_cache:
            time_cache[key] = _append_accessor(glb, list(times), 1, 'SCALAR', True)
        comps = 4 if path == 'rotation' else 3
        out = _append_accessor(glb, list(values), comps, 'VEC4' if comps == 4 else 'VEC3', False)
        samplers.append({'input': time_cache[key], 'output': out, 'interpolation': 'LINEAR'})
        channels.append({'sampler': len(samplers) - 1, 'target': {'node': index[node], 'path': path}})
    anim = {'name': name, 'samplers': samplers, 'channels': channels}
    anims = g.setdefault('animations', [])
    slot = next((i for i, a in enumerate(anims) if a.get('name') == name), None)
    if slot is None:
        anims.append(anim)
    else:
        anims[slot] = anim


def _accessor_refs(g):
    """รายการ (dict, key) ที่ชี้ accessor ทั้งหมดใน glTF"""
    refs = []
    for mesh in g.get('meshes', []):
        for prim in mesh.get('primitives', []):
            refs += [(prim['attributes'], k) for k in prim['attributes']]
            if 'indices' in prim:
                refs.append((prim, 'indices'))
            for target in prim.get('targets', []):
                refs += [(target, k) for k in target]
    refs += [(s, 'inverseBindMatrices') for s in g.get('skins', []) if 'inverseBindMatrices' in s]
    for anim in g.get('animations', []):
        for s in anim['samplers']:
            refs += [(s, 'input'), (s, 'output')]
    return refs


def _view_refs(g):
    refs = [(a, 'bufferView') for a in g.get('accessors', []) if 'bufferView' in a]
    for a in g.get('accessors', []):
        sparse = a.get('sparse')
        if sparse:
            refs += [(sparse['indices'], 'bufferView'), (sparse['values'], 'bufferView')]
    refs += [(im, 'bufferView') for im in g.get('images', []) if 'bufferView' in im]
    return refs


def _renumber(refs, keep):
    """ลบรายการที่ไม่อยู่ใน keep แล้วเขียนดัชนีใหม่ให้ทุกการอ้างอิง · คืน {เก่า: ใหม่}"""
    mapping = {old: new for new, old in enumerate(sorted(keep))}
    for holder, key in refs:
        holder[key] = mapping[holder[key]]
    return mapping


def compact(glb):
    """ทิ้ง accessor/bufferView ที่ไม่ถูกอ้าง แล้วจัดไบนารีใหม่ (เรียงตามเดิม จัด 4 ไบต์)"""
    g = glb.gltf
    used_acc = {h[k] for h, k in _accessor_refs(g)}
    refs = _accessor_refs(g)
    old_acc = g.get('accessors', [])
    g['accessors'] = [a for i, a in enumerate(old_acc) if i in used_acc]
    _renumber(refs, used_acc)
    view_refs = _view_refs(g)
    used_views = {h[k] for h, k in view_refs}
    old_views = g.get('bufferViews', [])
    new_bin, new_views = bytearray(), []
    for i, v in enumerate(old_views):
        if i not in used_views:
            continue
        while len(new_bin) % 4:
            new_bin.append(0)
        start = v.get('byteOffset', 0)
        nv = dict(v)
        nv['byteOffset'] = len(new_bin)
        new_bin += glb.bin[start: start + v['byteLength']]
        new_views.append(nv)
    g['bufferViews'] = new_views
    _renumber(view_refs, used_views)
    glb.bin = new_bin
