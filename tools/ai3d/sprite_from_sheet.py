"""ตัวละคร 2.5D จากภาพวาดตาราง (ทิศตามแกน dirAxis : "col" = คอลัมน์เป็นทิศ แถวเป็นเฟรม · "row" = กลับกัน) → แผ่นรวมแบบเดียวกับมุ่ย
รัน : F:/ai3d/venv/Scripts/python.exe tools/ai3d/sprite_from_sheet.py [tools/ai3d/som_sprites.json]
ผล (<outDir>) : <ท่า>_sheet.png (แถว = ทิศตามลำดับ dirs · คอลัมน์ = เฟรมของท่า) + sprites.json
ทุกเฟรมในทิศเดียวกันใช้การย่อ/เลื่อนเดียวกัน (กรอบรวมของทั้งคอลัมน์) → ขาขยับตามภาพ ตัวไม่กระตุก"""
import json
import os
import sys

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def cut(img, cfg, dir_i, frame_i):
    """ช่องของทิศ dir_i เฟรม frame_i ตามแกน dirAxis"""
    col, row = (dir_i, frame_i) if cfg['dirAxis'] == 'col' else (frame_i, dir_i)
    xs, ys, k = cfg['colsX'], cfg['rowsY'], cfg['inset']
    return img[ys[row] + k:ys[row + 1] - k, xs[col] + k:xs[col + 1] - k].copy()


def remove_bg(cell, tol, feather, light=None):
    """เทจากจุดบนขอบช่องที่ยังเป็นพื้น → alpha 0 · คืน BGRA"""
    h, w = cell.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    bg = np.median(np.concatenate([cell[0], cell[-1], cell[:, 0], cell[:, -1]]), axis=0)
    border = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    for x, y in border[::6]:
        if mask[y + 1, x + 1] == 0 and np.abs(cell[y, x].astype(int) - bg).max() <= tol:
            cv2.floodFill(cell, mask, (x, y), 0, (tol,) * 3, (tol,) * 3, flags)
    alpha = 255 - mask[1:-1, 1:-1]
    if light:  # ช่องปิดระหว่างขาที่เทจากขอบไม่ถึง : สีเทาสว่าง (ตัวละครไม่มีสีนี้ เช่น แมวดำ) = พื้น
        c = cell.astype(int)
        gray_light = (c.mean(2) >= light['minGray']) & (c.max(2) - c.min(2) <= light['maxSat'])
        alpha[gray_light] = 0
    if feather > 0:
        alpha = cv2.GaussianBlur(cv2.erode(alpha, np.ones((3, 3), np.uint8)), (0, 0), feather)
    return np.dstack([cell, alpha])


def union_box(frames):
    """กรอบรวมของทุกเฟรม (ช่องขนาดเท่ากันในคอลัมน์เดียว) · x0 x1 y0 y1"""
    a = np.max([f[..., 3] for f in frames], axis=0) > 32
    ys, xs = np.nonzero(a)
    return xs.min(), xs.max(), ys.min(), ys.max()


def place_column(frames, scale, cfg):
    """ย่อทุกเฟรมด้วย scale เดียว วางด้วยกรอบรวม (กลางแนวนอน · ขอบล่างห่าง footFrac)"""
    x0, x1, y0, y1 = union_box(frames)
    n = cfg['framePx']
    out = []
    for f in frames:
        crop = cv2.resize(f[y0:y1 + 1, x0:x1 + 1], None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h, w = crop.shape[:2]
        frame = np.zeros((n, n, 4), np.uint8)
        bottom = n - int(round(cfg['footFrac'] * n))
        left = (n - w) // 2
        frame[bottom - h:bottom, left:left + w] = crop
        out.append(frame)
    return out


def _even(frames):
    """ช่องขนาดไม่เท่ากัน → ตัดให้เท่าช่องเล็กสุด ยึดขอบล่าง (เท้า) และกลางแนวนอน"""
    h = min(f.shape[0] for f in frames)
    w = min(f.shape[1] for f in frames)
    out = []
    for f in frames:
        x = (f.shape[1] - w) // 2
        out.append(f[f.shape[0] - h:, x:x + w])
    return out


def load_columns(cfg):
    """ทิศ → [BGRA ต่อเฟรม] (กลับซ้ายขวาตาม dirCell)"""
    img = cv2.imread(cfg['source'])
    lines = cfg['rowsY'] if cfg['dirAxis'] == 'col' else cfg['colsX']
    cols = {}
    for d, (index, flip) in cfg['dirCell'].items():
        frames = _even([remove_bg(cut(img, cfg, index, f), cfg['tolerance'], cfg['featherPx'], cfg.get('lightBg')) for f in range(len(lines) - 1)])
        cols[d] = [cv2.flip(f, 1) for f in frames] if flip else frames
    return cols


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'som_sprites.json')
    with open(path, encoding='utf-8') as f:
        cfg = json.load(f)
    cols = load_columns(cfg)
    tallest = max(union_box(fr)[3] - union_box(fr)[2] + 1 for fr in cols.values())
    scale = cfg['heightFrac'] * cfg['framePx'] / tallest
    placed = {d: place_column(cols[d], scale, cfg) for d in cfg['dirs']}
    out = os.path.join(ROOT, cfg['outDir'])
    os.makedirs(out, exist_ok=True)
    for clip, rows in cfg['clips'].items():
        sheet = np.vstack([np.hstack([placed[d][r] for r in rows]) for d in cfg['dirs']])
        cv2.imwrite(os.path.join(out, clip + '_sheet.png'), sheet)
    world = cfg['catHeightM'] / cfg['heightFrac']
    meta = {'frameSizePx': cfg['framePx'], 'fps': cfg['fps'], 'dirs': list(cfg['dirs']), 'dirDeg': list(cfg['dirs'].values()),
            'frames': {c: len(r) for c, r in cfg['clips'].items()}, 'worldSizeM': round(world, 4),
            'centerYM': round(world * (0.5 - cfg['footFrac']), 4)}
    with open(os.path.join(out, 'sprites.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print('SOM_DONE', json.dumps(meta))


main()
