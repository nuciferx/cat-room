/** อ่าน config/catShowroom.json · ส่งสำเนาให้แอปเป็นเจ้าของ (แผง F1 แก้ค่าในสำเนานี้ ไม่แตะไฟล์) */
import json from '../../config/catShowroom.json';

export type CatConfig = Omit<typeof json, '_note'>;
export type GroupName = keyof CatConfig;

/** ค่าตัวเลขที่จูนได้ */
export interface NumParam { value: number; min: number; max: number; step: number }
/** ค่าสี hex sRGB */
export interface ColorParam { value: string }

export function loadConfig(): CatConfig {
  const { _note: _ignored, ...cfg } = structuredClone(json);
  return cfg;
}

export function isNumParam(p: NumParam | ColorParam): p is NumParam {
  return typeof p.value === 'number';
}

/** แปลงสำเนา config เป็น JSON พร้อมวางทับไฟล์ (ใส่ _note กลับ) */
export function serializeConfig(cfg: CatConfig): string {
  return JSON.stringify({ _note: json._note, ...cfg }, null, 2);
}
