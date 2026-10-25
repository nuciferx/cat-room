/** โหลดแมวจาก glb · ล้มเหลว → แคปซูลขนาดแมว + ข้อความบอกคำสั่งสร้างโมเดล */
import { BUILD_CAT_CMD, CAT_GLB_URL, SOM_GLB_URL } from '../constants/app';
import { FACE_SETS, type FaceSet } from '../constants/faces';
import { loadFaceSkins } from '../data/blinkLoader';
import { loadCatGltf } from '../data/catLoader';
import type { CatConfig } from '../data/config';
import type { Locale } from '../data/locale';
import type { Camera } from 'three';
import { SPRITE_DIRS } from '../constants/views';
import { loadSpriteSet } from '../data/spriteLoader';
import { createCapsuleActor, createGltfActor, type CatActor } from '../render/catActor';
import { createSpriteActor } from '../render/catSprite';
import { createDualActor, type DualActor } from '../render/dualActor';
import type { Banner } from '../ui/banner';

async function loadModel(cfg: CatConfig, locale: Locale, banner: Banner): Promise<CatActor> {
  try {
    const [gltf, skins] = await Promise.all([loadCatGltf(CAT_GLB_URL), loadFaceSkins(FACE_SETS['3d'])]);
    return createGltfActor(gltf, skins);
  } catch (err) {
    console.error(err);
    banner.show(locale.t('error.glbMissing', { cmd: BUILD_CAT_CMD }));
    return createCapsuleActor(cfg.fallback);
  }
}

/** โมเดลเสริม (หน้าสลับ/กระพริบตามชุดหน้าของตัวนั้น) · โหลดไม่ได้ = null */
async function loadExtraModel(url: string, faces: FaceSet): Promise<CatActor | null> {
  try {
    const [gltf, skins] = await Promise.all([loadCatGltf(url), loadFaceSkins(faces)]);
    return createGltfActor(gltf, skins);
  } catch (err) {
    console.warn(`โหลดโมเดลไม่ได้ (${url})`, err);
    return null;
  }
}

async function loadSprite(dir: string, camera: Camera, cfg: CatConfig): Promise<CatActor | null> {
  const set = await loadSpriteSet(dir);
  return set ? createSpriteActor(set, camera, cfg) : null;
}

/** ตัว 3D + ภาพ 2.5D ทุกแบบ (โหลดพร้อมกัน · แบบที่ไม่มีไฟล์ = ปุ่มนั้นแจ้งเตือน) */
export async function loadActor(cfg: CatConfig, locale: Locale, banner: Banner, camera: Camera): Promise<DualActor> {
  const [model, mui, som, som3d, dam] = await Promise.all([
    loadModel(cfg, locale, banner),
    loadSprite(SPRITE_DIRS['25d'], camera, cfg),
    loadSprite(SPRITE_DIRS.som, camera, cfg),
    loadExtraModel(SOM_GLB_URL, FACE_SETS.som3d),
    loadSprite(SPRITE_DIRS.dam, camera, cfg),
  ]);
  return createDualActor({ '3d': model, '25d': mui, som, som3d, dam });
}
