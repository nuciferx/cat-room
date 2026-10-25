"""สัตว์สี่ขา Meshy : อ่านเมชต้นทาง (เมชเดียว ไม่มีกระดูก) แล้วตั้งพิกัดเกม (numpy ไม่รู้จัก Blender)
พิกัด glTF : x = ซ้ายของตัว · y = ขึ้น · z = หน้า (ต้นทางหันหัวไป +z อยู่แล้ว ตรวจด้วย headSign ใน json)
- สเกลเท่ากันทุกแกน = ค่าเฉลี่ยของ (ยาวเป้า / ยาวต้นทาง) กับ (สูงไหล่เป้า / สูงไหล่ต้นทาง) · lengthM null = ใช้สูงไหล่อย่างเดียว
  ยาวต้นทาง = ปลายจมูก/เขี้ยว ถึงก้น (ไม่นับหาง : จุดที่ |x| เกิน tailHalfWidth) · สูงไหล่ = ยอดช่วง z กีบหน้า + withersOffsetZ ± withersWindow (รวมแผงขน) ถึงพื้น
- จุดกำเนิด : y = 0 ที่กีบต่ำสุด · x = กลางกล่อง · z = กลางระหว่างกีบหน้ากับกีบหลัง"""
import numpy as np

import din_new_glb as gio
import glb_io


class Source:
    """pos (N, 3) normal uv tri · material · ภาพ (ไบต์) ของ texture"""

    def __init__(self, path):
        self.glb = glb_io.read_glb(path)
        g = self.glb.gltf
        assert len(g['meshes']) == 1 and len(g['meshes'][0]['primitives']) == 1, 'เมช Meshy ควรมีเมชเดียว primitive เดียว'
        prim = g['meshes'][0]['primitives'][0]
        a = prim['attributes']
        self.pos = gio.accessor(self.glb, a['POSITION']).astype(float)
        self.normal = gio.accessor(self.glb, a['NORMAL']).astype(float)
        self.uv = gio.accessor(self.glb, a['TEXCOORD_0']).astype(float)
        self.tri = gio.accessor(self.glb, prim['indices']).reshape(-1, 3).astype(np.int64)
        self.material = g['materials'][prim['material']]
        self.report = {'tris': int(len(self.tri)), 'verts': int(len(self.pos)),
                       'bboxMin': np.round(self.pos.min(0), 4).tolist(), 'bboxMax': np.round(self.pos.max(0), 4).tolist()}

    def image(self, key):
        """ไบต์ภาพของ 'base' | 'mr' | 'normal' → (ไบต์, mime) หรือ None"""
        pbr = self.material['pbrMetallicRoughness']
        ref = {'base': pbr.get('baseColorTexture'), 'mr': pbr.get('metallicRoughnessTexture'),
               'normal': self.material.get('normalTexture')}[key]
        if ref is None:
            return None
        tex = self.glb.gltf['textures'][ref['index']]
        return gio.image_bytes(self.glb, tex['source'])


def _hoof_z(p, floor_y, band, z_split):
    """z กลางของกีบหน้า และกีบหลัง (จุดยอดสูงจากพื้นไม่เกิน band)"""
    low = p[p[:, 1] < floor_y + band]
    front, hind = low[low[:, 2] > z_split], low[low[:, 2] <= z_split]
    return float(np.median(front[:, 2])), float(np.median(hind[:, 2]))


def measure(p, c):
    """ขนาดต้นทาง (หน่วยไฟล์) : ยาวหัว-ก้น · สูงไหล่ · z กีบหน้า/หลัง"""
    floor_y = float(p[:, 1].min())
    fz, hz = _hoof_z(p, floor_y, c['hoofBand'], c['legSplitZ'])
    body = p[np.abs(p[:, 0]) > c['tailHalfWidth']]
    length = float(p[:, 2].max() - body[:, 2].min())
    near = p[np.abs(p[:, 2] - fz - c.get('withersOffsetZ', 0.0)) < c['withersWindow']]
    withers = float(near[:, 1].max() - floor_y)
    return {'floorY': floor_y, 'frontHoofZ': fz, 'hindHoofZ': hz, 'length': length, 'withers': withers}


def normalize(src, c):
    """ตั้งพิกัดเกมในที่ (src.pos / src.normal) · คืนรายงาน"""
    p = src.pos.copy()
    if c['headSign'] < 0:  # หัวอยู่ -z : หมุน 180° รอบแกน y
        p[:, 0], p[:, 2] = -p[:, 0], -p[:, 2]
        src.normal[:, 0], src.normal[:, 2] = -src.normal[:, 0], -src.normal[:, 2]
    m = measure(p, c)
    s_len, s_wit = (c['lengthM'] or 0.0) / m['length'], c['withersM'] / m['withers']
    s = 0.5 * (s_len + s_wit) if c['lengthM'] else s_wit
    mid_z = 0.5 * (m['frontHoofZ'] + m['hindHoofZ'])
    mid_x = 0.5 * (p[:, 0].min() + p[:, 0].max())
    p = (p - np.array([mid_x, m['floorY'], mid_z])) * s
    src.pos = p
    rep = {'scale': round(s, 5), 'scaleForLength': round(s_len, 5), 'scaleForWithers': round(s_wit, 5),
           'lengthM': round(m['length'] * s, 4), 'withersM': round(m['withers'] * s, 4),
           'frontHoofZ': round((m['frontHoofZ'] - mid_z) * s, 4), 'hindHoofZ': round((m['hindHoofZ'] - mid_z) * s, 4),
           'bboxMin': np.round(p.min(0), 4).tolist(), 'bboxMax': np.round(p.max(0), 4).tolist()}
    src.report['normalize'] = rep
    return rep
