/** ค่าคงที่ระดับแอป : query, ภาษา, path asset, คำสั่งสร้างโมเดล (ที่เดียวในโปรเจกต์) */

export const QUERY = { clip: 'clip', face: 'face', view: 'view', quality: 'q', grid: 'grid', lang: 'lang' } as const;

/** ค่าของ ?q= */
export const QUALITY_LOW = 'low';
/** ค่าของ ?grid= ที่แปลว่าปิด */
export const GRID_OFF = '0';

export const LANGS = ['th', 'en'] as const;
export type Lang = (typeof LANGS)[number];
export const DEFAULT_LANG: Lang = 'th';

/** public/ เสิร์ฟที่ราก */
export const CAT_GLB_URL = 'assets/models/cat/cat.glb';
/** เจ้าส้ม 3D (build_quad_meshy.py -- som) · ไม่มีไฟล์ = ปุ่มนั้นแจ้งเตือน */
export const SOM_GLB_URL = 'assets/models/som/som.glb';
/** ไฟล์ข้อมูลในโฟลเดอร์ภาพ 2.5D (โฟลเดอร์ต่อแบบ : constants/views SPRITE_DIRS) · แผ่นรวมชื่อ <ท่า>_sheet.png */
export const SPRITE_META = 'sprites.json';

/** คำสั่งสร้าง cat.glb (แสดงในข้อความ error ตอนโหลดไม่ได้) */
export const BUILD_CAT_CMD = 'blender -b --factory-startup --python-exit-code 1 --python tools/blender/build_quad_meshy.py -- cat';

/** ขนาดพื้นผิวไล่สีฟ้า (พิกเซล) : กว้าง × สูง */
export const SKY_TEXTURE_PX = { w: 2, h: 256 } as const;
