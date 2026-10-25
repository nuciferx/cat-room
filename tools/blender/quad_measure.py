"""วัดสัตว์สี่ขาหลังตั้งพิกัดแบบเดียวกับ build_quad_meshy (ไม่พึ่ง Blender) : ภาพเงา ข้าง/หน้า/บน มีเส้นตาราง 2 ซม. + ตัวเลขหลัก
ไว้วางข้อต่อใน quad_meshy_<ตัว>.json หัวข้อ rig / weights
รัน : python tools/blender/quad_measure.py <ตัว> <โฟลเดอร์ภาพ>   (อ่าน source + normalize จาก quad_meshy_<ตัว>.json)
ภาพ : side.png (แกนนอน z หน้าไปขวา · แกนตั้ง y) · front.png (แกนนอน x ซ้ายของตัวไปขวาของภาพ · แกนตั้ง y) · top.png (x นอน · z ตั้ง หน้าขึ้น)
สีเทาเข้ม = ใกล้กล้อง (ความลึก) · เส้นแดง = ทุก 10 ซม. · เส้นฟ้า = ทุก 2 ซม."""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import quad_meshy_source as qsrc  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PX_PER_M = 2000
GRID_M = 0.02


def views(p):
    """(ชื่อ, แกนนอน, แกนตั้ง, แกนลึก, กลับแกนนอน, กลับลึก) · ลึกน้อย = ใกล้กล้อง"""
    return (('side', 2, 1, 0, False, True), ('front', 0, 1, 2, True, True), ('top', 0, 2, 1, True, True))


def draw(p, h_ax, v_ax, d_ax, flip_h, near_high, out):
    h = -p[:, h_ax] if flip_h else p[:, h_ax]
    v, d = p[:, v_ax], p[:, d_ax]
    lo_h, hi_h, lo_v, hi_v = h.min() - 0.02, h.max() + 0.02, v.min() - 0.02, v.max() + 0.02
    w, ht = int((hi_h - lo_h) * PX_PER_M), int((hi_v - lo_v) * PX_PER_M)
    img = np.full((ht, w), 255, np.float32)
    order = np.argsort(d if near_high else -d)  # วาดไกลก่อน ใกล้ทับ
    dn = (d - d.min()) / max(d.max() - d.min(), 1e-6)
    shade = 60 + 150 * (1 - dn if near_high else dn)
    xs = ((h - lo_h) * PX_PER_M).astype(int).clip(0, w - 1)
    ys = ((hi_v - v) * PX_PER_M).astype(int).clip(0, ht - 1)
    for i in order:
        img[ys[i] - 1:ys[i] + 2, xs[i] - 1:xs[i] + 2] = shade[i]
    im = Image.fromarray(img.astype(np.uint8)).convert('RGB')
    grid(ImageDraw.Draw(im), lo_h, hi_h, lo_v, hi_v, flip_h)
    im.save(out)


def grid(dr, lo_h, hi_h, lo_v, hi_v, flip_h):
    for k in range(int(np.floor(lo_h / GRID_M)), int(np.ceil(hi_h / GRID_M)) + 1):
        x = int((k * GRID_M - lo_h) * PX_PER_M)
        major = k % 5 == 0
        dr.line([(x, 0), (x, 10000)], fill=(220, 0, 0) if major else (120, 180, 255), width=1)
        if major:
            dr.text((x + 2, 2), '%.2f' % (-k * GRID_M if flip_h else k * GRID_M), fill=(220, 0, 0))
    for k in range(int(np.floor(lo_v / GRID_M)), int(np.ceil(hi_v / GRID_M)) + 1):
        y = int((hi_v - k * GRID_M) * PX_PER_M)
        major = k % 5 == 0
        dr.line([(0, y), (10000, y)], fill=(220, 0, 0) if major else (120, 180, 255), width=1)
        if major:
            dr.text((2, y + 2), '%.2f' % (k * GRID_M), fill=(220, 0, 0))


def main():
    key, out = sys.argv[1], sys.argv[2]
    with open(os.path.join(HERE, 'quad_meshy_%s.json' % key), encoding='utf-8') as f:
        cfg = json.load(f)
    src = qsrc.Source(os.path.join(ROOT, cfg['source']))
    rep = qsrc.normalize(src, cfg['normalize'])
    os.makedirs(out, exist_ok=True)
    for name, h, v, d, flip, near in views(src.pos):
        draw(src.pos, h, v, d, flip, near, os.path.join(out, name + '.png'))
    print('QUAD_MEASURE', json.dumps(rep, ensure_ascii=False))


main()
