"""ขั้น Krita ของภาพ 2.5D มุ่ย : ภาพเรนเดอร์จาก Blender (sprite_render.py) → ย่อ + เก็บผิว → ไฟล์แอนิเมชัน .kra + แผ่นรวม
รัน (จากโฟลเดอร์นี้) : <Krita>/bin/kritarunner.com -s mui_sprites [ท่า] [ทิศ]   (ใส่ท่า/ทิศ = ทดสอบเฉพาะชุดนั้น)
  ค่าอยู่ใน tools/blender/sprite_cat.json (หัวข้อ krita) · kritarunner ไม่ส่ง print ออกมา → บันทึกลง <kritaDir>/log.txt
ผล (<kritaDir>) :
  frames/<ท่า>_<ทิศ>/NNNN.png  ภาพต่อเฟรมขนาด sizePx
  (<ท่า>.kra ปิดไว้ : importAnimation ล่มใน kritarunner)
  <ท่า>_sheet.png               แผ่นรวม แถว = ทิศ ตามลำดับ dirs · คอลัมน์ = เฟรม
  sprites.json                  ขนาดเฟรม fps ลำดับทิศ จำนวนเฟรมต่อท่า (ให้ฝั่งเว็บอ่าน)"""
import glob
import json
import os
import time
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
CFG = os.path.join(ROOT, 'tools', 'blender', 'sprite_cat.json')


def load_cfg():
    with open(CFG, encoding='utf-8') as f:
        return json.load(f)


def apply_filter(k, doc, node, name, props):
    flt = k.filter(name)
    conf = flt.configuration()  # เก็บตัวแปรไว้ ไม่งั้นวัตถุ C++ ถูกลบก่อนใช้
    for key, val in props.items():
        conf.setProperty(key, val)
    flt.setConfiguration(conf)
    flt.apply(node, 0, 0, doc.width(), doc.height())


def _read_png(path):
    """PNG → ไบต์ BGRA (ลำดับเดียวกับ pixelData ของ Krita RGBA U8) ผ่าน QImage (เร็วกว่าเปิดเป็นเอกสารหลายเท่า)"""
    from PyQt5.QtGui import QImage
    img = QImage(path).convertToFormat(QImage.Format_ARGB32)
    ptr = img.constBits()
    ptr.setsize(img.sizeInBytes())
    return bytes(ptr), img.width(), img.height()


def _write_png(path, data, size):
    from PyQt5.QtGui import QImage
    QImage(data, size, size, size * 4, QImage.Format_ARGB32).save(path)


def _timed(log, name, fn):
    t = time.perf_counter()
    out = fn()
    log.write('  %s %.2f วิ\n' % (name, time.perf_counter() - t))
    return out


def _paste(node, srcs, w, h):
    for i, src in enumerate(srcs):
        data, _, _ = _read_png(src)
        node.setPixelData(data, i * w, 0, w, h)


def process_strip(k, srcs, dsts, cfg, log):
    """ทั้งทิศในเอกสารเดียว (เฟรมเรียงแนวนอน) : วาง → ย่อเป็น sizePx → ฟิลเตอร์ครั้งเดียว → แยกเฟรมกลับ
    คืนไบต์พิกเซลต่อเฟรม · บันทึกเวลาทีละขั้นลง log"""
    kc, size = cfg['krita'], cfg['sizePx']
    _, w, h = _read_png(srcs[0])
    doc = k.createDocument(w * len(srcs), h, 'strip', 'RGBA', 'U8', '', 72.0)
    doc.setBatchmode(True)
    node = doc.createNode('strip', 'paintlayer')
    doc.rootNode().addChildNode(node, None)
    _timed(log, 'วางภาพ', lambda: (_paste(node, srcs, w, h), doc.waitForDone()))
    _timed(log, 'ย่อ', lambda: (doc.scaleImage(size * len(srcs), size, int(doc.xRes()), int(doc.yRes()), kc['scaleFilter']), doc.waitForDone()))
    for name, props in kc['filters']:
        _timed(log, name, lambda: (apply_filter(k, doc, node, name, props), doc.waitForDone()))
    frames = _timed(log, 'อ่านเฟรม', lambda: [bytes(node.pixelData(i * size, 0, size, size)) for i in range(len(srcs))])
    doc.close()
    _timed(log, 'เขียน PNG', lambda: [_write_png(dst, data, size) for data, dst in zip(frames, dsts)])
    return frames


def build_kra(k, path, layers, cfg):
    """แอนิเมชันหนึ่งท่า : importAnimation ทีละทิศ (ได้ชั้นใหม่ต่อครั้ง) → ตั้งชื่อชั้นตามทิศ"""
    size, n = cfg['sizePx'], max(len(f) for _, f in layers)
    doc = k.createDocument(size, size, os.path.basename(path), 'RGBA', 'U8', '', 72.0)
    doc.setBatchmode(True)
    doc.setFramesPerSecond(cfg['fps'])
    doc.setFullClipRangeStartTime(0)
    doc.setFullClipRangeEndTime(n - 1)
    for name, files in layers:
        before = {nd.uniqueId() for nd in doc.rootNode().childNodes()}
        doc.importAnimation(files, 0, 1)
        for nd in doc.rootNode().childNodes():
            if nd.uniqueId() not in before:
                nd.setName(name)
                nd.setVisible(name == layers[0][0])
    doc.saveAs(path)
    doc.close()


def build_sheet(k, path, rows, cfg):
    """แผ่นรวม : rows = [(ทิศ, [ไบต์พิกเซลต่อเฟรม])]"""
    from krita import InfoObject
    size = cfg['sizePx']
    cols = max(len(f) for _, f in rows)
    doc = k.createDocument(size * cols, size * len(rows), 'sheet', 'RGBA', 'U8', '', 72.0)
    doc.setBatchmode(True)
    node = doc.createNode('sheet', 'paintlayer')
    doc.rootNode().addChildNode(node, None)
    for r, (_, frames) in enumerate(rows):
        for c, data in enumerate(frames):
            node.setPixelData(data, c * size, r * size, size, size)
    doc.waitForDone()
    for nd in doc.rootNode().childNodes():
        if nd.name() != 'sheet':
            nd.setVisible(False)
    doc.refreshProjection()
    info = InfoObject()
    doc.exportImage(path, info)
    doc.close()


def run_clip(k, clip, cfg, src_dir, out_dir, log, only_dir=None):
    layers, rows = [], []
    for d in [x for x in cfg['dirs'] if only_dir in (None, x)]:
        srcs = sorted(glob.glob(os.path.join(src_dir, '%s_%s' % (clip, d), '*.png')))
        if not srcs:
            log.write('ข้าม %s_%s (ไม่มีภาพเรนเดอร์)\n' % (clip, d))
            continue
        folder = os.path.join(out_dir, 'frames', '%s_%s' % (clip, d))
        os.makedirs(folder, exist_ok=True)
        dsts = [os.path.join(folder, os.path.basename(s)) for s in srcs]
        t0 = time.perf_counter()
        rows.append((d, process_strip(k, srcs, dsts, cfg, log)))
        log.write('%s_%s %d เฟรม %.1f วิ\n' % (clip, d, len(srcs), time.perf_counter() - t0))
        layers.append((d, dsts))
    if not rows:
        return 0
    _timed(log, 'แผ่นรวม', lambda: build_sheet(k, os.path.join(out_dir, clip + '_sheet.png'), rows, cfg))
    # build_kra ปิดไว้ : Document.importAnimation ทำ kritarunner ล่ม (segfault) ตอนไม่มีหน้าต่าง · เปิดเฟรมใน Krita เอง : File > Import Animation Frames
    log.write('เสร็จ %s : %d ทิศ × %d เฟรม\n' % (clip, len(rows), len(rows[0][1])))
    return len(rows[0][1])


def run(log, args):
    from krita import Krita
    k = Krita.instance()
    cfg = load_cfg()
    src_dir = os.path.join(ROOT, cfg['outDir'])
    out_dir = os.path.join(ROOT, cfg['krita']['outDir'])
    os.makedirs(out_dir, exist_ok=True)
    clips = args[:1] or cfg['clips']
    only_dir = args[1] if len(args) > 1 else None
    frames = {c: run_clip(k, c, cfg, src_dir, out_dir, log, only_dir) for c in clips}
    meta = {'frameSizePx': cfg['sizePx'], 'fps': cfg['fps'], 'dirs': list(cfg['dirs']), 'dirDeg': list(cfg['dirs'].values()),
            'frames': frames, 'worldSizeM': cfg['camera']['orthoM'], 'centerYM': cfg['camera']['targetY']}
    with open(os.path.join(out_dir, 'sprites.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    log.write('SPRITES_DONE %s\n' % json.dumps(frames))


def __main__(args):
    cfg = load_cfg()
    out_dir = os.path.join(ROOT, cfg['krita']['outDir'])
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'log.txt'), 'w', encoding='utf-8', buffering=1) as log:
        try:
            run(log, list(args or []))
        except Exception:
            log.write(traceback.format_exc())
