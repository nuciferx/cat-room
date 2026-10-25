/** โหลดภาพ 2.5D หนึ่งแบบ (sprites.json + แผ่นรวมต่อท่า ในโฟลเดอร์ dir) · ไม่มีไฟล์ → null (ปุ่มแบบนั้นแจ้งเตือนแทน) */
import { TextureLoader, type Texture } from 'three';
import { SPRITE_META } from '../constants/app';
import type { SpriteMeta } from '../logic/spriteFrame';

export interface SpriteSet {
  meta: SpriteMeta;
  /** แผ่นรวมต่อท่า (เฉพาะท่าที่โหลดได้) */
  sheets: Record<string, Texture>;
}

export function sheetUrl(dir: string, clip: string): string {
  return `${dir}${clip}_sheet.png`;
}

async function loadMeta(dir: string): Promise<SpriteMeta> {
  const res = await fetch(`${dir}${SPRITE_META}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as SpriteMeta;
}

export async function loadSpriteSet(dir: string): Promise<SpriteSet | null> {
  try {
    const meta = await loadMeta(dir);
    const clips = Object.keys(meta.frames).filter((c) => meta.frames[c] > 0);
    const loader = new TextureLoader();
    const texs = await Promise.all(clips.map((c) => loader.loadAsync(sheetUrl(dir, c)).catch(() => null)));
    const sheets: Record<string, Texture> = {};
    clips.forEach((c, i) => {
      const tex = texs[i];
      if (tex) sheets[c] = tex;
    });
    return { meta, sheets };
  } catch (err) {
    console.warn(`โหลดภาพ 2.5D ไม่ได้ (${dir})`, err);
    return null;
  }
}
