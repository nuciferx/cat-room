# ตัดรูปมุมมองจากชีต 8 มุม → รูปไร้พื้นหลังที่ครอปชิดตัววัตถุ ใช้ฉายสีลงโมเดล (tools/ai3d/project_views.py) และเป็นอินพุต 2mv
#   F:/ai3d/venv/Scripts/python tools/ai3d/views_cutout.py <views.json> <โฟลเดอร์ผล>
# views.json : {"<ชื่อ>": {"sheet": "<ไฟล์ชีต ข้างไฟล์ json>", "views": {"front": [x0,y0,x1,y1], "left": [...], "back": [...], "right": [...]}}}
# ผล : <โฟลเดอร์ผล>/<ชื่อ>/<มุม>.png (RGBA ชิดขอบวัตถุ · ขยาย 2 เท่า)
import json
import os
import sys

ROOT = os.environ.get('HY3D_ROOT', 'F:/ai3d')
os.environ.setdefault('U2NET_HOME', os.path.join(ROOT, 'cache/u2net'))
sys.path.insert(0, os.path.join(ROOT, 'Hunyuan3D-2'))
UPSCALE = 2
ALPHA_MIN = 128  # พิกเซลที่ทึบน้อยกว่านี้ไม่นับเป็นตัววัตถุตอนหาขอบ
EDGE_ALPHA = 250  # พิกเซลที่ทึบน้อยกว่านี้ถูกเติมสีใหม่จากเนื้อวัตถุข้างใน
EDGE_GROW_PX = 2  # กินเข้าไปในขอบอีกกี่พิกเซล (ขอบ rembg มักเป็นสีพื้นหลังปน)
INPAINT_RADIUS = 6


def cutout(sheet, box, remover):
    from PIL import Image
    crop = sheet.crop(tuple(box))
    crop = crop.resize((crop.width * UPSCALE, crop.height * UPSCALE), Image.LANCZOS)
    rgba = remover(crop.convert('RGB'))
    solid = rgba.getchannel('A').point(lambda a: 255 if a >= ALPHA_MIN else 0)
    return fill_edges(rgba.crop(solid.getbbox()))


def fill_edges(rgba):
    """เติมสีจากตัววัตถุลงพิกเซลโปร่ง/ขอบ : ตอนฉายลงโมเดล ผิวที่ชิดขอบเงาจะได้สีวัตถุ ไม่ใช่เส้นขาว"""
    import cv2
    import numpy as np
    from PIL import Image
    a = np.asarray(rgba)
    hole = (a[..., 3] < EDGE_ALPHA).astype(np.uint8) * 255
    hole = cv2.dilate(hole, np.ones((3, 3), np.uint8), iterations=EDGE_GROW_PX)
    rgb = cv2.inpaint(np.ascontiguousarray(a[..., :3]), hole, INPAINT_RADIUS, cv2.INPAINT_TELEA)
    return Image.fromarray(np.dstack([rgb, a[..., 3]]), 'RGBA')


def main():
    from PIL import Image
    from hy3dgen.rembg import BackgroundRemover
    spec_path, out_root = sys.argv[1:3]
    spec = json.load(open(spec_path, encoding='utf-8'))
    remover = BackgroundRemover()
    for name, item in spec.items():
        sheet = Image.open(os.path.join(os.path.dirname(spec_path), item['sheet'])).convert('RGB')
        out_dir = os.path.join(out_root, name)
        os.makedirs(out_dir, exist_ok=True)
        for view, box in item['views'].items():
            img = cutout(sheet, box, remover)
            img.save(os.path.join(out_dir, view + '.png'))
            print('VIEW', name, view, img.size)


if __name__ == '__main__':
    main()
