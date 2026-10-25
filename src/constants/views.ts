/** แบบของแมวในห้องโชว์ : มุ่ย 3D (cat.glb) · มุ่ย 2.5D · เจ้าส้ม 2.5D · เจ้าส้ม 3D (som.glb) · เจ้าดำ 2.5D (ภาพวาด 8 ทิศ เดินได้)
 *  ลำดับ = ลำดับปุ่ม · ชื่อภาษาคนอยู่ที่ locales `view.<ชื่อ>` */
export const VIEW_NAMES = ['3d', '25d', 'som', 'som3d', 'dam'] as const;

export type ViewName = (typeof VIEW_NAMES)[number];
/** แบบที่เป็นโมเดล glb (ที่เหลือเป็นภาพ 2.5D) */
export const MODEL_VIEWS = ['3d', 'som3d'] as const;
export type ModelViewName = (typeof MODEL_VIEWS)[number];
export type SpriteViewName = Exclude<ViewName, ModelViewName>;

export const DEFAULT_VIEW: ViewName = '3d';

/** โฟลเดอร์ภาพ 2.5D ต่อแบบ (public/ เสิร์ฟที่ราก) · มี sprites.json + <ท่า>_sheet.png */
export const SPRITE_DIRS: Readonly<Record<SpriteViewName, string>> = {
  '25d': 'assets/sprites/cat/',
  som: 'assets/sprites/som/',
  dam: 'assets/sprites/dam/',
};

/** แบบที่ใช้ชุดหน้า/กระพริบของโมเดลไหน : โมเดล = ตัวเอง · ภาพ 2.5D ไม่มีหน้า → ใช้ของมุ่ย 3D (พฤติกรรมเดิม) */
export function faceViewOf(view: ViewName): ModelViewName {
  return (MODEL_VIEWS as readonly ViewName[]).includes(view) ? (view as ModelViewName) : '3d';
}

export function isViewName(v: string | null): v is ViewName {
  return v !== null && (VIEW_NAMES as readonly string[]).includes(v);
}
