/** โหลดภาพผิวสำรอง (หลับตา · หน้าอารมณ์) · โหลดไม่ได้ → null (แมวแค่ใช้ภาพนั้นไม่ได้ ไม่โชว์ banner) */
import { TextureLoader, type Texture } from 'three';
import { defaultFace, type FaceName, type FaceSet } from '../constants/faces';
import type { FaceSkins } from '../render/catBlink';

export async function loadOptionalTexture(url: string): Promise<Texture | null> {
  try {
    return await new TextureLoader().loadAsync(url);
  } catch (err) {
    console.warn(`โหลดภาพผิวไม่ได้ (${url})`, err);
    return null;
  }
}

/** ภาพผิวของทุกหน้าที่ไม่ใช่หน้าเริ่มต้น · หน้าที่โหลดไม่ได้จะไม่อยู่ในผลลัพธ์ */
async function loadFaceTextures(set: FaceSet): Promise<Partial<Record<FaceName, Texture>>> {
  const entries = Object.entries(set.textures) as [FaceName, string][];
  const loaded = await Promise.all(entries.map(async ([name, url]) => [name, await loadOptionalTexture(url)] as const));
  const out: Partial<Record<FaceName, Texture>> = {};
  for (const [name, tex] of loaded) if (tex) out[name] = tex;
  return out;
}

/** ภาพหลับตา + ภาพหน้าอื่นของแมวหนึ่งตัว (โหลดพร้อมกัน) */
export async function loadFaceSkins(set: FaceSet): Promise<FaceSkins> {
  const [blink, faces] = await Promise.all([loadOptionalTexture(set.blinkUrl), loadFaceTextures(set)]);
  return { blink, faces, defaultFace: defaultFace(set) };
}
