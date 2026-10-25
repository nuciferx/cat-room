# ตัดช่องภาพจากแผ่นอ้างอิงตามกรอบใน json (ไม่ลบพื้นหลัง : cat_touchup ใช้สีพื้นหลังที่มุมภาพแยกตัวแมว)
#   python tools/ai3d/sheet_crop.py <cfg.json> [หัวข้อ = cells]
# cfg[หัวข้อ] = {"sheet": ภาพแผ่น, "outDir": โฟลเดอร์ผล, "boxes": {ชื่อ: [x0, y0, x1, y1]}} → <outDir>/<ชื่อ>.png
import json
import os
import sys

from PIL import Image


def main():
    cfg_path, key = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'cells')
    with open(cfg_path, encoding='utf-8') as fp:
        c = json.load(fp)[key]
    sheet = Image.open(c['sheet']).convert('RGB')
    os.makedirs(c['outDir'], exist_ok=True)
    for name, box in c['boxes'].items():
        if name.startswith('_'):
            continue
        out = os.path.join(c['outDir'], name + '.png')
        sheet.crop(tuple(box)).save(out)
        print('CROP', name, box, out)


main()
