"""อ่าน accessor ของ GLB เป็น numpy และประกอบ GLB ใหม่จากอาร์เรย์ (ไม่พึ่ง Blender)
ใช้กับ build_din_new.py / check_din_new.py · อ่านไฟล์ด้วย glb_io.read_glb ตัวเดิม"""
import json

import numpy as np

import glb_io

DTYPE = {5126: np.float32, 5121: np.uint8, 5123: np.uint16, 5125: np.uint32}
CTYPE = {np.dtype(np.float32): 5126, np.dtype(np.uint8): 5121, np.dtype(np.uint16): 5123, np.dtype(np.uint32): 5125}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
TYPE_OF = {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4', 16: 'MAT4'}
ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER = 34962, 34963


def accessor(glb, index):
    """คืน accessor เป็นอาร์เรย์ (count, ncomp) ชนิดตามไฟล์ (รองรับ byteStride)"""
    g = glb.gltf
    a = g['accessors'][index]
    view = g['bufferViews'][a['bufferView']]
    n, dt = NCOMP[a['type']], np.dtype(DTYPE[a['componentType']])
    off = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = view.get('byteStride', 0) or n * dt.itemsize
    raw = np.frombuffer(glb.bin, dtype=np.uint8, count=stride * (a['count'] - 1) + n * dt.itemsize, offset=off)
    rows = np.lib.stride_tricks.as_strided(raw, shape=(a['count'], n * dt.itemsize), strides=(stride, 1))
    out = np.ascontiguousarray(rows).view(dt).reshape(a['count'], n)
    if a.get('normalized') and dt != np.float32:
        out = out.astype(np.float32) / np.iinfo(dt).max
    return out


def matrices(glb, index):
    """accessor MAT4 (column-major ตาม glTF) -> อาร์เรย์ (count, 4, 4) แบบแถว"""
    return accessor(glb, index).reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)


def image_bytes(glb, image_index):
    g = glb.gltf
    im = g['images'][image_index]
    view = g['bufferViews'][im['bufferView']]
    start = view.get('byteOffset', 0)
    return bytes(glb.bin[start: start + view['byteLength']]), im.get('mimeType', 'image/jpeg')


class GlbBuilder:
    """ประกอบ glTF + ไบนารี : เพิ่ม accessor/รูป แล้วเขียนไฟล์ด้วย glb_io.write_glb"""

    def __init__(self, gltf):
        self.gltf = gltf
        self.bin = bytearray()
        gltf['accessors'], gltf['bufferViews'] = [], []

    def _view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        view = {'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': len(data)}
        if target:
            view['target'] = target
        self.bin += data
        self.gltf['bufferViews'].append(view)
        return len(self.gltf['bufferViews']) - 1

    def add(self, array, target=None, minmax=False, normalized=False):
        arr = np.ascontiguousarray(array)
        arr2 = arr.reshape(arr.shape[0], -1)
        acc = {'bufferView': self._view(arr2.tobytes(), target), 'componentType': CTYPE[arr2.dtype],
               'count': int(arr2.shape[0]), 'type': TYPE_OF[arr2.shape[1]]}
        if normalized:
            acc['normalized'] = True
        if minmax:
            acc['min'] = [float(x) for x in arr2.min(0)]
            acc['max'] = [float(x) for x in arr2.max(0)]
        self.gltf['accessors'].append(acc)
        return len(self.gltf['accessors']) - 1

    def add_matrices(self, mats):
        """(count,4,4) แบบแถว -> MAT4 column-major float32"""
        cols = np.asarray(mats, dtype=np.float64).transpose(0, 2, 1).reshape(-1, 16).astype(np.float32)
        return self.add(cols)

    def add_image(self, data, mime, name):
        self.gltf.setdefault('images', []).append({'bufferView': self._view(data), 'mimeType': mime, 'name': name})
        return len(self.gltf['images']) - 1

    def write(self, path):
        glb = glb_io.Glb(self.gltf, bytes(self.bin))
        glb_io.write_glb(glb, path)


def dump_json(obj, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
