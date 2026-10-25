"""ปรับสีพื้นของ texture Meshy ให้สม่ำเสมอ (numpy) ก่อนอบ
ภาพ basecolor ของ Meshy เป็นปื้นสว่าง/มืดสลับกันเป็นหย่อม ๆ (ในไฟล์ต้นทางถูกกลบด้วย metallicFactor 1 จึงดูเป็นสีเข้มเรียบ
แต่ในเกมใช้ metallic 0 ปื้นจะโผล่เป็นลายพราง) · ปื้นอยู่ภายในเกาะ UV ด้วย จึงแก้ทีละเกาะไม่ได้
วิธี : แยกความถี่ในภาพต้นทาง (ค่า linear) : ต่ำ = เบลอกล่องซ้อน blurPasses รอบ รัศมี blurPx · รายละเอียด = ภาพ / ต่ำ
ผล = สีเป้า × รายละเอียด ^ detail (ลายขนคงอยู่ ปื้นหาย) · ส่วนที่ต้องคงสีเดิม (เขี้ยว กีบ : เกาะ UV ที่จุดกลางอยู่ใน keepBoxes)
ส่งเป็นค่า keep ต่อสามเหลี่ยม แล้ววัสดุตอนอบผสม ภาพปรับ ↔ ภาพเดิม ตามค่านี้"""
import numpy as np


def _lin(c):
    c = np.asarray(c, dtype=np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def _box(a, r, axis):
    """เบลอกล่องกว้าง 2r+1 ตามแกนเดียว (ขอบภาพยืดค่าขอบ)"""
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode='edge'), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def blur(a, r, passes):
    for _ in range(passes):
        a = _box(_box(a, r, 0), r, 1)
    return a


def flatten(px, tc):
    """px = ภาพ base (H, W, 3) ค่า sRGB → ภาพปรับแล้ว (sRGB) + รายงาน"""
    lin = _lin(px)
    low = np.maximum(blur(lin, tc['blurPx'], tc['blurPasses']), 1e-4)
    detail = np.clip(lin / low, 0.0, tc['detailMax']) ** tc['detail']
    out = _lin(tc['targetSRGB'])[None, None, :] * detail
    lum = low @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    rep = {'lowLumP10P90Before': np.round(np.percentile(lum, [10, 90]), 4).tolist(),
           'meanSRGBAfter': np.round(_srgb(out).reshape(-1, 3).mean(0), 3).tolist()}
    return _srgb(out), rep


def islands(tri, n_verts, max_iter=500):
    """ป้ายเกาะต่อจุดยอด (จุดที่แยกตามรอยต่อ UV ของไฟล์ต้นทาง = คนละเกาะ) : กระจายค่าต่ำสุดผ่านสามเหลี่ยม"""
    lab = np.arange(n_verts)
    for _ in range(max_iter):
        m = lab[tri].min(1)
        new = lab.copy()
        for k in range(3):
            np.minimum.at(new, tri[:, k], m)
        new = new[new]  # กระโดดตามตัวชี้ (เร็วขึ้น)
        if np.array_equal(new, lab):
            break
        lab = new
    _, lab = np.unique(lab, return_inverse=True)
    return lab.ravel()


def _in_boxes(p, boxes):
    hit = np.zeros(len(p), dtype=bool)
    for b in boxes:
        q = p.copy()
        if b.get('mirrorX'):
            q[:, 0] = np.abs(q[:, 0])
        hit |= np.all((q >= np.asarray(b['min'])) & (q <= np.asarray(b['max'])), axis=1)
    return hit


def keep(src, tc):
    """ค่า keep ต่อสามเหลี่ยม (1 = ใช้สีเดิม) จากเกาะ UV ที่จุดกลางอยู่ใน keepBoxes + รายงาน"""
    lab = islands(src.tri, len(src.pos))
    n = lab.max() + 1
    cnt = np.bincount(lab, minlength=n).astype(float)
    cen = np.column_stack([np.bincount(lab, src.pos[:, k], n) for k in range(3)]) / cnt[:, None]
    kept = _in_boxes(cen, tc['keepBoxes'])
    k = kept[lab[src.tri[:, 0]]].astype(np.float32)
    return k, {'islands': int(n), 'keptIslands': int(kept.sum()), 'keptTris': int(k.sum())}
