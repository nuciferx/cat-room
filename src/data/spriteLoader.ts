/** โหลดภาพ 2.5D หนึ่งแบบ (sprites.json + แผ่นรวมต่อท่า ในโฟลเดอร์ dir) · ไม่มีไฟล์ → null (ปุ่มแบบนั้นแจ้งเตือนแทน)
 *  แผ่นที่กว้าง/สูงเกินที่การ์ดจอรองรับ (maxTexturePx) จะไม่ถูกถอดรหัส · จดไว้ใน skipped ให้ผู้เรียกแจ้งเตือน */
import { TextureLoader, type Texture } from 'three';
import { SPRITE_META } from '../constants/app';
import { PNG_HEADER_BYTES, readPngSize, type PngSize } from '../logic/pngSize';
import type { SpriteMeta } from '../logic/spriteFrame';

export interface SkippedSheet extends PngSize {
  clip: string;
}

export interface SpriteSet {
  meta: SpriteMeta;
  /** แผ่นรวมต่อท่า (เฉพาะท่าที่โหลดได้) */
  sheets: Record<string, Texture>;
  /** แผ่นที่ข้ามเพราะใหญ่เกิน maxTexturePx */
  skipped: SkippedSheet[];
}

export function sheetUrl(dir: string, clip: string): string {
  return `${dir}${clip}_sheet.png`;
}

async function loadMeta(dir: string): Promise<SpriteMeta> {
  const res = await fetch(`${dir}${SPRITE_META}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as SpriteMeta;
}

/** ขนาดแผ่นจากหัวไฟล์ (ขอเฉพาะไม่กี่ไบต์แรก · เซิร์ฟเวอร์ไม่รองรับ Range ก็ยังอ่านได้) · อ่านไม่ได้ = null */
async function fetchSheetSize(url: string): Promise<PngSize | null> {
  try {
    const res = await fetch(url, { headers: { Range: `bytes=0-${PNG_HEADER_BYTES - 1}` } });
    if (!res.ok) return null;
    return readPngSize(new Uint8Array(await res.arrayBuffer()));
  } catch {
    return null;
  }
}

type SheetResult = { tex: Texture } | { skipped: SkippedSheet } | null;

async function loadSheet(dir: string, clip: string, maxPx: number): Promise<SheetResult> {
  const url = sheetUrl(dir, clip);
  const size = await fetchSheetSize(url);
  if (size && (size.width > maxPx || size.height > maxPx)) return { skipped: { clip, ...size } };
  const tex = await new TextureLoader().loadAsync(url).catch(() => null);
  return tex ? { tex } : null;
}

export async function loadSpriteSet(dir: string, maxTexturePx: number): Promise<SpriteSet | null> {
  try {
    const meta = await loadMeta(dir);
    const clips = Object.keys(meta.frames).filter((c) => meta.frames[c] > 0);
    const results = await Promise.all(clips.map((c) => loadSheet(dir, c, maxTexturePx)));
    const set: SpriteSet = { meta, sheets: {}, skipped: [] };
    clips.forEach((c, i) => {
      const r = results[i];
      if (r && 'tex' in r) set.sheets[c] = r.tex;
      else if (r) set.skipped.push(r.skipped);
    });
    return set;
  } catch (err) {
    console.warn(`โหลดภาพ 2.5D ไม่ได้ (${dir})`, err);
    return null;
  }
}
