# ปั้นทรง 3D จากรูปเดียวด้วย Hunyuan3D บนเครื่อง (ทรงอย่างเดียว ไม่ลงสี : การ์ดจอ 8 GB ลงสีไม่ไหว)
# ใช้ venv ที่ F:/ai3d/venv (โค้ด Hunyuan ที่ F:/ai3d/Hunyuan3D-2 · โมเดล/แคชทั้งหมดอยู่บน F: กัน C: เต็ม)
# รุ่น 2.1 ลบออกแล้ว 2026-10-22 : บนการ์ดจอ 8 GB ช้ากว่า 2.0 ราว 20 เท่า (39 นาที vs 2 นาที) ผลดีขึ้นนิดเดียว
#   F:/ai3d/venv/Scripts/python tools/ai3d/hunyuan_shape.py <รูป.png> <ผล.glb> [--ver 2.0|2mv] [--steps 30] [--octree 256] [--faces 40000]
# รุ่น 2mv (หลายมุม) : <รูป> เป็นโฟลเดอร์ที่มี front.png left.png back.png right.png (มีไฟล์ไหนใช้ไฟล์นั้น · left = หมุนตามเข็ม 90° จากหน้า)
# รูปที่มีพื้นหลังจะถูกตัดพื้นหลังเอง (rembg) · ผลเป็น glb ทรงล้วน ไปใส่วัสดุต่อใน Blender (tools/blender/meshy_buddha.py)
import argparse
import importlib
import os
import sys
import time

ROOT = os.environ.get('HY3D_ROOT', 'F:/ai3d')
for key, sub in (('HF_HOME', 'cache/hf'), ('HY3DGEN_MODELS', 'cache/hy3dgen'), ('U2NET_HOME', 'cache/u2net')):
    os.environ.setdefault(key, os.path.join(ROOT, sub))

# รุ่น → (โฟลเดอร์โค้ดที่ใส่ sys.path, ชื่อแพ็กเกจ, repo บน HF, โฟลเดอร์โมเดลทรง)
VERSIONS = {
    '2.0': ('Hunyuan3D-2', 'hy3dgen.shapegen', 'tencent/Hunyuan3D-2', 'hunyuan3d-dit-v2-0'),
    '2mv': ('Hunyuan3D-2', 'hy3dgen.shapegen', 'tencent/Hunyuan3D-2mv', 'hunyuan3d-dit-v2-mv'),
}


def parse():
    p = argparse.ArgumentParser()
    p.add_argument('image')
    p.add_argument('out')
    p.add_argument('--ver', default='2.0', choices=sorted(VERSIONS))
    p.add_argument('--steps', type=int, default=30)
    p.add_argument('--octree', type=int, default=256)
    p.add_argument('--seed', type=int, default=1234)
    p.add_argument('--faces', type=int, default=0, help='0 = ไม่ลดโพลี')
    return p.parse_args()


def load_package(ver):
    code_dir, pkg, _, _ = VERSIONS[ver]
    sys.path.insert(0, os.path.join(ROOT, code_dir))
    return importlib.import_module(pkg), importlib.import_module(pkg.split('.')[0] + '.rembg')


VIEWS = ('front', 'left', 'back', 'right')


def load_one(path, remover):
    from PIL import Image
    img = Image.open(path).convert('RGBA')
    if img.getextrema()[3][0] == 255:  # ไม่มีส่วนโปร่งใส = มีพื้นหลัง
        img = remover(img.convert('RGB'))
    return img


def load_image(path, rembg):
    remover = rembg.BackgroundRemover()
    if not os.path.isdir(path):
        return load_one(path, remover)
    found = [v for v in VIEWS if os.path.exists(os.path.join(path, v + '.png'))]
    return {v: load_one(os.path.join(path, v + '.png'), remover) for v in found}


def load_pipe(shapegen, repo, sub):
    """โหลดแบบประหยัด RAM (เครื่อง 16 GB) : ไฟล์ ckpt เปิดแบบ mmap ไม่อ่านทั้งก้อน · สร้างโมเดลเป็น fp16 ตั้งแต่ต้น (รุ่น 2.1 3B พารามิเตอร์ fp32 = ~12 GB)"""
    import torch
    raw_load, raw_dtype = torch.load, torch.get_default_dtype()
    torch.load = lambda *a, **k: raw_load(*a, **{**k, 'mmap': True})
    torch.set_default_dtype(torch.float16)
    try:
        # ใช้ model.fp16.ckpt · ถ้าไม่มี HY3DGEN_MODELS/<repo>/<sub> โค้ดจะดึงจาก HF cache (HF_HUB_OFFLINE=1 กันโหลดซ้ำ)
        return shapegen.Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(repo, subfolder=sub, use_safetensors=False, variant='fp16')
    finally:
        torch.load = raw_load
        torch.set_default_dtype(raw_dtype)


def main():
    import torch
    a = parse()
    shapegen, rembg = load_package(a.ver)
    _, _, repo, sub = VERSIONS[a.ver]
    image = load_image(a.image, rembg)  # ตัดพื้นหลังก่อนโหลดโมเดลใหญ่ (ตัวตัดพื้นหลังกิน RAM · เครื่อง 16 GB)
    t0 = time.time()
    pipe = load_pipe(shapegen, repo, sub)
    t1 = time.time()
    gen = torch.Generator('cuda').manual_seed(a.seed)
    mesh = pipe(image=image, num_inference_steps=a.steps, octree_resolution=a.octree, generator=gen)[0]
    mesh = shapegen.DegenerateFaceRemover()(shapegen.FloaterRemover()(mesh))
    if a.faces:
        mesh = shapegen.FaceReducer()(mesh, max_facenum=a.faces)
    mesh.export(a.out)
    peak = torch.cuda.max_memory_allocated() / 2**30
    print(f'HY3D_SHAPE ver={a.ver} out={a.out} faces={len(mesh.faces)} load={t1 - t0:.0f}s gen={time.time() - t1:.0f}s vramPeakGB={peak:.1f}')


if __name__ == '__main__':
    main()
