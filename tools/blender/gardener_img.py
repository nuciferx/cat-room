"""อ่าน/เขียนภาพผ่าน Blender (ไม่มี PIL ใน python ของ Blender) : ไบต์ JPEG/PNG <-> อาร์เรย์ float (H, W, 3) ค่า sRGB 0..1
แถว 0 = บนสุดของภาพ (ตรงกับ v = 0 ของ glTF)"""
import os

import bpy
import numpy as np


def decode(data, mime, work_dir, name):
    os.makedirs(work_dir, exist_ok=True)
    path = os.path.join(work_dir, name + ('.png' if mime.endswith('png') else '.jpg'))
    with open(path, 'wb') as f:
        f.write(data)
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(img)
    return np.ascontiguousarray(np.flipud(px)[:, :, :3])


def encode_jpeg(rgb, work_dir, name, quality):
    """อาร์เรย์ (H, W, 3) -> ไบต์ JPEG (เซฟตรง ไม่ผ่าน view transform)"""
    os.makedirs(work_dir, exist_ok=True)
    h, w = rgb.shape[:2]
    rgba = np.concatenate([np.flipud(np.clip(rgb, 0.0, 1.0)), np.ones((h, w, 1), dtype=np.float32)], axis=2)
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    path = os.path.join(work_dir, name + '.jpg')
    img.filepath_raw = path
    img.file_format = 'JPEG'
    img.save(quality=quality)
    bpy.data.images.remove(img)
    with open(path, 'rb') as f:
        return f.read()
