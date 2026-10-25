# ล้างสีชมพู (ในหู/จมูก) ออกจากภาพมุมที่ไม่ใช่ภาพหน้า ก่อนฉายสี : หูในแต่ละภาพไม่ตรงหูที่ปั้น ฉายแล้วเป็นจุดชมพูบนหัว
# หูด้านในทาชมพูทีหลังด้วย cat_touchup.py (ears) แทน
#   python tools/ai3d/views_depink.py <โฟลเดอร์รูปเดิม> <โฟลเดอร์ผล> [--keep front] [--cream 238,214,184]
import argparse
import os
import shutil

import numpy as np
from PIL import Image, ImageFilter

PINK_RG = 60  # แดงมากกว่าเขียวเกินนี้ = ชมพู (ตัวครีม r−g ≈ 25–30)
PINK_R = 150
GROW_PX = 5  # ขยายหน้ากากกินขอบไล่สี


def parse():
    p = argparse.ArgumentParser()
    p.add_argument('src')
    p.add_argument('out')
    p.add_argument('--keep', default='front', help='มุมที่ไม่ล้าง คั่นด้วย ,')
    p.add_argument('--cream', default='238,214,184')
    return p.parse_args()


def depink(path, out, cream):
    img = Image.open(path).convert('RGBA')
    a = np.asarray(img).copy()
    r, g = a[..., 0].astype(int), a[..., 1].astype(int)
    mask = Image.fromarray(((r - g > PINK_RG) & (r > PINK_R)).astype(np.uint8) * 255)
    mask = np.asarray(mask.filter(ImageFilter.MaxFilter(GROW_PX * 2 + 1))) > 0
    a[mask, :3] = cream
    Image.fromarray(a, 'RGBA').save(out)
    return int(mask.sum())


def main():
    a = parse()
    keep = set(a.keep.split(','))
    cream = [int(c) for c in a.cream.split(',')]
    os.makedirs(a.out, exist_ok=True)
    for name in sorted(os.listdir(a.src)):
        src, dst = os.path.join(a.src, name), os.path.join(a.out, name)
        if os.path.splitext(name)[0] in keep or not name.endswith('.png'):
            shutil.copyfile(src, dst)
            continue
        print('DEPINK', name, depink(src, dst, cream), 'px')


main()
