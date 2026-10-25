"""bb : มาสก์เขตที่ภาพสีพื้นชุดอื่น (เช่น หลับตา) ต่างจากภาพหลักได้ (numpy ล้วน ไม่รู้จัก Blender)
เหตุ : อบสองรอบจากต้นทาง JPEG สองไฟล์ → นอกเขตตาก็ต่างกันเป็นจุดเล็ก ๆ (สัญญาณรบกวนของการเข้ารหัส/การอบ) → ตอนสลับภาพเห็นจุดวูบ
วิธี : สามเหลี่ยมที่มีจุดยอดในกล่อง region (พิกัด glTF ม.) → ระบายลงพื้นที่ UV → ขยาย growPx → เกลี่ยขอบ featherPx
ผล = ภาพหลัก + มาสก์ × (ภาพชุดอื่น − ภาพหลัก) · นอกเขตจึงเท่าภาพหลัก"""
import numpy as np


def _box_blur(x, r):
    """ค่าเฉลี่ยในกรอบ (2r+1)² ด้วยผลรวมสะสม (ขอบเติมศูนย์)"""
    if r <= 0:
        return x
    k = 2 * r + 1
    c = np.cumsum(np.cumsum(np.pad(x, ((r + 1, r), (r + 1, r))), 0), 1)
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def _fill_tri(mask, t):
    """ระบายสามเหลี่ยมหนึ่งรูป (t = 3×2 พิกัดพิกเซล x, y) ลง mask"""
    h, w = mask.shape
    x0, y0 = np.floor(t.min(0)).astype(int)
    x1, y1 = np.ceil(t.max(0)).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w - 1), min(y1, h - 1)
    if x1 < x0 or y1 < y0:
        return
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    (ax, ay), (bx, by), (cx, cy) = t
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-12:
        return
    l1 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
    l2 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
    inside = (l1 >= -0.01) & (l2 >= -0.01) & (1 - l1 - l2 >= -0.01)
    mask[y0:y1 + 1, x0:x1 + 1] |= inside


def region_mask(pos, tris, tri_uv, size, region):
    """pos = จุดยอด (n×3 glTF) · tris = ดัชนีจุดยอด (m×3) · tri_uv = UV ของมุมสามเหลี่ยม (m×3×2)
    → มาสก์ 0..1 ขนาด size×size (แถว 0 = v ต่ำสุด แบบภาพของ Blender)"""
    lo, hi = np.asarray(region['min']), np.asarray(region['max'])
    inside = np.all((pos >= lo) & (pos <= hi), axis=1)
    mask = np.zeros((size, size), dtype=bool)
    for k in np.nonzero(inside[tris].any(axis=1))[0]:
        _fill_tri(mask, tri_uv[k] * size)
    grown = _box_blur(mask.astype(float), region['growPx']) > 0
    return np.clip(_box_blur(grown.astype(float), region['featherPx']), 0.0, 1.0)


def tri_mask(tri_uv, size, sel, grow_px):
    """มาสก์ bool ของสามเหลี่ยมที่เลือก (sel = ดัชนี) ในพื้นที่ UV · ขยาย grow_px"""
    mask = np.zeros((size, size), dtype=bool)
    for k in sel:
        _fill_tri(mask, tri_uv[k] * size)
    return _box_blur(mask.astype(float), grow_px) > 0 if grow_px > 0 else mask


def composite(base, alt, mask):
    """base/alt = พิกเซล (h×w×4) · คืนภาพหลักที่แทนด้วยภาพชุดอื่นเฉพาะในมาสก์"""
    m = mask[:, :, None]
    return base + m * (alt - base)
