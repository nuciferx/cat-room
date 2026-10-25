"""สัตว์สี่ขาจากโมเดล Meshy (เมชเดียว ไม่มีกระดูก ไม่มีท่า) → glb พร้อมกระดูกและคลิป (ทับไฟล์ปลายทาง)
รัน : F:/game/a/.tools/blender-5.2.1-windows-x64/blender.exe -b --python tools/blender/build_quad_meshy.py -- boar dog
      (ชื่อตัว = ไฟล์ค่า tools/blender/quad_meshy_<ตัว>.json · ไม่ระบุ = boar)
รายงาน <workDir>/report.json (+ บรรทัด QUAD_REPORT) · ภาพตรวจ quad_meshy_preview.py · ตรวจไฟล์ quad_meshy_check.mjs
ขั้น : ตั้งพิกัด (สเกล หันหน้า +z จุดกำเนิดที่พื้น) → ลบปื้นสีของ texture (คงลายขน) → ลดโพลี + normal จากเมชละเอียด → แตก UV ใหม่ + อบภาพสี/normal 1024 → วัสดุด้าน
     → กระดูกชุดสัตว์สี่ขา (beasts_rig.SKELETON + extra) ข้อต่อตามรูปร่างของตัว → น้ำหนัก (ป้ายตามเขต + เกลี่ย)
     → แก้ท่า (beasts_stance) → ใส่คีย์ทุกคลิป (beasts_clips) → วัดผล → ส่งออก glb"""
import json
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import beasts_blender as xb  # noqa: E402
import birds_blender as bb  # noqa: E402
import gardener_img as gimg  # noqa: E402
import quad_meshy_bake as qbake  # noqa: E402
import quad_meshy_clips as qclips  # noqa: E402
import quad_meshy_lod as qlod  # noqa: E402
import quad_meshy_material as qmat  # noqa: E402
import quad_meshy_rig as qrig  # noqa: E402
import quad_meshy_source as qsrc  # noqa: E402
import quad_meshy_tailsplit as qtail  # noqa: E402
import quad_meshy_tone as qtone  # noqa: E402
import quad_meshy_weights as qw  # noqa: E402
from beasts_skin import Skin  # noqa: E402
from beasts_stance import resolve_stances  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))


def log(*a):
    print('[quad_meshy]', *a, flush=True)


def full(path):
    return os.path.join(ROOT, path)


def cfg_path(key):
    """ชื่อตัว → tools/blender/quad_meshy_<ตัว>.json · ลงท้าย .json = path ไฟล์ค่าตรง ๆ (ใช้สร้างลงที่ทดลองโดยไม่แตะไฟล์ค่าจริง)"""
    return key if key.endswith('.json') else os.path.join(HERE, 'quad_meshy_%s.json' % key)


def cfg_key(key):
    return os.path.basename(key)[len('quad_meshy_'):-len('.json')] if key.endswith('.json') else key


def load_cfg(key):
    with open(cfg_path(key), encoding='utf-8') as f:
        return json.load(f)


def tone_stage(cfg, key, src, report):
    """ลบปื้นสี (ไม่มีหัวข้อ tone = ใช้ภาพต้นทางตรง ๆ) → (keep ต่อสามเหลี่ยม, path ภาพปรับ หรือ None)"""
    if not cfg.get('tone'):
        return np.ones(len(src.tri), dtype=np.float32), None
    data, mime = src.image('base')
    px = gimg.decode(data, mime, full(cfg['workDir']), key + '_tone_probe')
    flat, report['tone'] = qtone.flatten(px, cfg['tone'])
    gimg.encode_jpeg(flat, full(cfg['workDir']), key + '_src_flat', 95)
    tri_keep, report['toneKeep'] = qtone.keep(src, cfg['tone'])
    return tri_keep, os.path.join(full(cfg['workDir']), key + '_src_flat.jpg')


def alt_sources(cfg, flat_path):
    """bb : bake.alts = {ชื่อ: {source: glb ที่ UV ตรงกับต้นทางหลัก, out: ภาพปลายทาง, region: เขตที่ยอมให้ต่าง (ไม่ใส่ = ทั้งภาพ)}} → รายการให้ qbake.bake_alts"""
    if flat_path is not None:
        raise ValueError('bake.alts ใช้กับต้นทางที่มี tone ไม่ได้ (ภาพปรับปื้นมีแค่ชุดหลัก)')
    out = []
    for name, a in cfg['bake']['alts'].items():
        data, mime = qsrc.Source(a['source']).image('base')
        out.append((name, data, mime, full(a['out']), a.get('region')))
    return out


def mesh_stage(cfg, key, report):
    src = qsrc.Source(full(cfg['source']))
    qsrc.normalize(src, cfg['normalize'])
    report['source'] = src.report
    tri_keep, flat_path = tone_stage(cfg, key, src, report)
    mesh, high, report['lod'] = qlod.make_lod(src, cfg['mesh'], key, tri_keep)
    mesh.name = mesh.data.name = key + '_mesh'
    if cfg.get('tailSplit'):  # bb : แยกพุ่มหางเป็นชิ้นต่างหาก แล้วโอน normal ใหม่ (หน้าปิดรู/โคนหางที่เพิ่ม)
        report['tailSplit'] = qtail.split(mesh, cfg)
        qlod.transfer_normals(mesh, high)
        if cfg['tailSplit'].get('flatFillNormals'):
            report['tailSplit']['flatFillFaces'] = qtail.flat_fill_normals(mesh, cfg['tailSplit'].get('smoothFillNormals', False))
        log(key, 'แยกชิ้นหาง', report['tailSplit'])
    log(key, 'ลดโพลีเหลือ', report['lod']['tris'], 'สามเหลี่ยม · อบภาพ')
    images, report['bake'], base_raw = qbake.bake(mesh, high, src, cfg['bake'], full(cfg['workDir']), key, flat_path)
    if cfg['bake'].get('alts'):
        report['bake']['alts'] = qbake.bake_alts(mesh, high, alt_sources(cfg, flat_path), cfg['bake'],
                                                   full(cfg['workDir']), key, base_raw)
    bpy.data.objects.remove(high)
    mesh.data.materials.clear()
    mat, report['material'] = qmat.make(images, cfg['material'], key)
    mesh.data.materials.append(mat)
    return mesh


def rig_stage(cfg, key, mesh, report):
    bones, rig = qrig.build(cfg['rig'])
    pos = qlod.vertex_pos(mesh)
    w, report['weights'] = qw.compute(pos, qlod.edges(mesh), rig, cfg['weights'], qtail.piece_mask(mesh))
    weights = qw.as_dicts(w, rig.order)
    skin = Skin(rig, pos, weights)
    arm = bb.make_armature(key, bones)
    bb.skin(mesh, arm, weights)
    ctx = SimpleNamespace(rig=rig, skin=skin, stances=resolve_stances(cfg.get('stances', {}), rig, skin))
    report['bones'] = len(bones)
    report['stances'] = {k: {p: round(v, 3) for p, v in s.items()} for k, s in ctx.stances.items()}
    return arm, ctx


def export_glb(path, objs, frame_step):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_apply=False, export_normals=True, export_texcoords=True, export_tangents=False,
                              export_materials='EXPORT', export_image_format='AUTO',
                              export_skins=True, export_animations=True, export_animation_mode='ACTIONS',
                              export_frame_range=False, export_frame_step=frame_step,
                              export_optimize_animation_size=True, export_optimize_animation_keep_anim_armature=False,
                              export_cameras=False, export_lights=False)


def build(arg):
    cfg, key = load_cfg(arg), cfg_key(arg)
    os.makedirs(full(cfg['workDir']), exist_ok=True)
    bb.reset_scene(cfg['fps'])
    report = {'animal': key, 'config': arg if arg.endswith('.json') else 'tools/blender/quad_meshy_%s.json' % key}
    mesh = mesh_stage(cfg, key, report)
    arm, ctx = rig_stage(cfg, key, mesh, report)
    clips = qclips.bake_all(cfg, arm, ctx, bb.rest_matrices(arm), cfg['fps'])
    report.update(qclips.measure(mesh, arm, ctx, clips, cfg['fps']))
    path = full(cfg['out'])
    export_glb(path, [arm, mesh], cfg['frameStep'])
    report['file'] = {'path': cfg['out'], 'KB': round(os.path.getsize(path) / 1024, 1)}
    report['budget'] = dict(cfg['budget'], trisOk=report['lod']['tris'] <= cfg['budget']['tris'],
                            fileOk=report['file']['KB'] <= cfg['budget']['fileKB'])
    with open(os.path.join(full(cfg['workDir']), 'report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print('QUAD_REPORT', json.dumps({k: report[k] for k in ('animal', 'lod', 'file', 'budget', 'rest')}, ensure_ascii=False))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for key in argv or ['boar']:
        build(key)


main()
