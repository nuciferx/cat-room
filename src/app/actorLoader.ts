/** โหลดแมวจาก glb · ล้มเหลว → แคปซูลขนาดแมว + ข้อความบอกคำสั่งสร้างโมเดล
 *  ตอนเปิดหน้าโหลดแค่มุ่ย 3D · แบบอื่น (ภาพ 2.5D · เจ้าส้ม 3D) โหลดเมื่อสลับไปครั้งแรก (DualActor.ensureView)
 *  แบบที่โหลดไม่ได้ : ที่นี่แจ้งเตือนเอง (ผู้เรียกไม่ต้องแจ้งซ้ำ) */
import { BUILD_CAT_CMD, CAT_GLB_URL, MUI2_GLB_URL, SOM_GLB_URL } from '../constants/app';
import { FACE_SETS, type FaceSet } from '../constants/faces';
import { SPRITE_DIRS, type ViewName } from '../constants/views';
import { loadFaceSkins } from '../data/blinkLoader';
import { loadCatGltf } from '../data/catLoader';
import type { CatConfig } from '../data/config';
import type { Locale } from '../data/locale';
import { loadSpriteSet, type SkippedSheet } from '../data/spriteLoader';
import { createCapsuleActor, createGltfActor, type CatActor } from '../render/catActor';
import { createSpriteActor } from '../render/catSprite';
import { createDualActor, type DualActor } from '../render/dualActor';
import type { Camera } from 'three';
import type { Banner } from '../ui/banner';

export interface LoaderEnv {
  cfg: CatConfig;
  locale: Locale;
  banner: Banner;
  camera: Camera;
  /** ขนาดภาพสูงสุดที่การ์ดจอรองรับ (พิกเซล) */
  maxTexturePx: number;
}

async function loadModel(env: LoaderEnv): Promise<CatActor> {
  try {
    const [gltf, skins] = await Promise.all([loadCatGltf(CAT_GLB_URL), loadFaceSkins(FACE_SETS['3d'])]);
    return createGltfActor(gltf, skins);
  } catch (err) {
    console.error(err);
    env.banner.show(env.locale.t('error.glbMissing', { cmd: BUILD_CAT_CMD }));
    return createCapsuleActor(env.cfg.fallback);
  }
}

function warnMissing(env: LoaderEnv): void {
  env.banner.show(env.locale.t('error.viewMissing'), env.cfg.ui.warnS.value);
}

/** โมเดลเสริม (หน้าสลับ/กระพริบตามชุดหน้าของตัวนั้น) · โหลดไม่ได้ = null + แจ้งเตือน */
async function loadExtraModel(env: LoaderEnv, url: string, faces: FaceSet): Promise<CatActor | null> {
  try {
    const [gltf, skins] = await Promise.all([loadCatGltf(url), loadFaceSkins(faces)]);
    return createGltfActor(gltf, skins);
  } catch (err) {
    console.warn(`โหลดโมเดลไม่ได้ (${url})`, err);
    warnMissing(env);
    return null;
  }
}

function warnSkipped(env: LoaderEnv, view: ViewName, skipped: SkippedSheet[]): void {
  const sheets = skipped.map((s) => `${s.clip} ${s.width}×${s.height}`).join(', ');
  const text = env.locale.t('error.textureTooBig', { view: env.locale.t(`view.${view}`), sheets, max: String(env.maxTexturePx) });
  env.banner.show(text, env.cfg.ui.warnS.value);
}

/** ภาพ 2.5D : แผ่นใหญ่เกินการ์ดจอข้าม + แจ้งเตือน · ไม่เหลือแผ่นใช้ได้ = null */
async function loadSprite(env: LoaderEnv, view: ViewName, dir: string): Promise<CatActor | null> {
  const set = await loadSpriteSet(dir, env.maxTexturePx);
  if (!set) {
    warnMissing(env);
    return null;
  }
  if (set.skipped.length > 0) warnSkipped(env, view, set.skipped);
  if (Object.keys(set.sheets).length > 0) return createSpriteActor(set, env.camera, env.cfg);
  if (set.skipped.length === 0) warnMissing(env);
  return null;
}

function loadView(env: LoaderEnv, view: ViewName): Promise<CatActor | null> {
  if (view === '3d') return Promise.resolve(null);
  if (view === 'mui3d2') return loadExtraModel(env, MUI2_GLB_URL, FACE_SETS.mui3d2);
  if (view === 'som3d') return loadExtraModel(env, SOM_GLB_URL, FACE_SETS.som3d);
  return loadSprite(env, view, SPRITE_DIRS[view]);
}

/** ตัว 3D ของมุ่ย (แบบเริ่มต้น) · แบบอื่นโหลดทีหลังตอนผู้ใช้สลับ */
export async function loadActor(env: LoaderEnv): Promise<DualActor> {
  const model = await loadModel(env);
  return createDualActor({ '3d': model }, (view) => loadView(env, view));
}
