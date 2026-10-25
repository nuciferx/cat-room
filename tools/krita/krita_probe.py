"""วัดเวลาแต่ละขั้นของ Krita กับภาพเดียว (kritarunner -s krita_probe) · ผลเขียนลงไฟล์ (kritarunner ไม่ส่ง print ออกมา)"""
import time
import traceback

OUT = 'F:/game/bb/shots/tmp.temp/krita_probe.txt'
SRC = 'F:/game/bb/shots/tmp.temp/cat_sprites/walk_SW/0000.png'
DST = 'F:/game/bb/shots/tmp.temp/krita_probe_out.png'


def step(log, name, fn):
    t = time.perf_counter()
    out = fn()
    log.write('%s %.3f s\n' % (name, time.perf_counter() - t))
    return out


def run_filter(k, doc, node, name):
    f = k.filter(name)
    conf = f.configuration()
    f.setConfiguration(conf)
    f.apply(node, 0, 0, doc.width(), doc.height())


def run(log):
    from krita import Krita, InfoObject
    k = Krita.instance()
    doc = step(log, 'open', lambda: k.openDocument(SRC))
    doc.setBatchmode(True)
    step(log, 'scale', lambda: doc.scaleImage(256, 256, int(doc.xRes()), int(doc.yRes()), 'Bicubic'))
    node = doc.rootNode().childNodes()[0]
    step(log, 'noise', lambda: run_filter(k, doc, node, 'gaussiannoisereducer'))
    step(log, 'unsharp', lambda: run_filter(k, doc, node, 'unsharp'))
    step(log, 'refresh', doc.refreshProjection)
    info = InfoObject()
    step(log, 'export', lambda: doc.exportImage(DST, info))
    step(log, 'pixel', lambda: node.pixelData(0, 0, 256, 256))
    step(log, 'close', doc.close)


def __main__(args):
    with open(OUT, 'w', encoding='utf-8', buffering=1) as log:
        try:
            run(log)
        except Exception:
            log.write(traceback.format_exc())
