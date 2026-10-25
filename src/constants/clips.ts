/** ชื่อคลิปใน cat.glb (ลำดับ = ลำดับปุ่มบนแถบ และปุ่มเลข 1–9,0) · ชื่อภาษาคนอยู่ที่ locales `clip.<ชื่อ>` */
export const CLIP_NAMES = ['idle', 'sit', 'lie', 'lie_down', 'walk', 'trot', 'run', 'sniff', 'wag', 'alarm', 'jump_up'] as const;

export type ClipName = (typeof CLIP_NAMES)[number];

/** ท่าเริ่มต้นเมื่อไม่มี ?clip= */
export const DEFAULT_CLIP: ClipName = 'idle';

export function isClipName(v: string | null): v is ClipName {
  return v !== null && (CLIP_NAMES as readonly string[]).includes(v);
}
