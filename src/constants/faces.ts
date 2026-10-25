/** หน้าของแมวแต่ละตัว (ภาพผิวสำรองบน UV เดียวกับ glb ของตัวนั้น) · ชื่อภาษาคนอยู่ที่ locales `face.<ชื่อ>`
 *  มุ่ย : บึ้ง / คลายเครียด · เจ้าส้ม : ช่องหน้า 6 แบบในแผ่นอ้างอิง (bake.alts ใน quad_meshy_som.json) */
import type { ModelViewName } from './views';

export const FACE_NAMES = ['grumpy', 'relaxed', 'normal', 'smile', 'happy', 'sad', 'wink', 'sleepy'] as const;

export type FaceName = (typeof FACE_NAMES)[number];

export interface FaceSet {
  /** ลำดับ = ลำดับปุ่มบนแถบหน้า · ตัวแรก = หน้าเริ่มต้น (ภาพผิวใน glb เอง ไม่ต้องโหลดเพิ่ม · หน้าเดียวที่กระพริบตา) */
  names: readonly FaceName[];
  /** ภาพผิวของหน้าอื่น (public/ เสิร์ฟที่ราก) · ไม่มีไฟล์ = กดปุ่มหน้านั้นแล้วแจ้งเตือน */
  textures: Readonly<Partial<Record<FaceName, string>>>;
  /** ภาพหลับตาของหน้าเริ่มต้น · ไม่มีไฟล์ = ไม่กระพริบ */
  blinkUrl: string;
}

export const FACE_SETS: Readonly<Record<ModelViewName, FaceSet>> = {
  '3d': {
    names: ['grumpy', 'relaxed'],
    textures: { relaxed: 'assets/models/cat/cat_relaxed.jpg' },
    blinkUrl: 'assets/models/cat/cat_blink.jpg',
  },
  mui3d2: {
    names: ['grumpy', 'relaxed'],
    textures: { relaxed: 'assets/models/cat2/cat2_relaxed.jpg' },
    blinkUrl: 'assets/models/cat2/cat2_blink.jpg',
  },
  som3d: {
    names: ['normal', 'smile', 'happy', 'sad', 'wink', 'sleepy'],
    textures: {
      smile: 'assets/models/som/som_smile.jpg',
      happy: 'assets/models/som/som_happy.jpg',
      sad: 'assets/models/som/som_sad.jpg',
      wink: 'assets/models/som/som_wink.jpg',
      sleepy: 'assets/models/som/som_sleepy.jpg',
    },
    blinkUrl: 'assets/models/som/som_blink.jpg',
  },
};

export function defaultFace(set: FaceSet): FaceName {
  return set.names[0];
}

export function isFaceName(v: string | null): v is FaceName {
  return v !== null && (FACE_NAMES as readonly string[]).includes(v);
}
