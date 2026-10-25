/** เลือกภาพ 2.5D : ทิศจากมุมกล้องรอบแมว + เฟรมจากเวลา · ตรรกะล้วน ไม่รู้จัก three.js
 *  มุมใช้แบบเดียวกับ logic/orbit : 0 = กล้องอยู่หน้าแมว (+Z, ทิศ S) · บวก = ไปทาง +X (ทิศ W) */

/** sprites.json ที่ tools/krita/mui_sprites.py เขียน */
export interface SpriteMeta {
  frameSizePx: number;
  fps: number;
  /** ชื่อทิศ ตามลำดับแถวในแผ่นรวม */
  dirs: string[];
  /** มุมกล้องของแต่ละทิศ (องศา) ขนานกับ dirs */
  dirDeg: number[];
  /** จำนวนเฟรมต่อท่า (0 = ไม่มี) */
  frames: Record<string, number>;
  /** ความกว้าง/สูงของหนึ่งเฟรมในโลก (เมตร) = orthoM ตอนเรนเดอร์ */
  worldSizeM: number;
  /** ความสูงจุดกลางภาพ (เมตร) = จุดเล็งกล้องตอนเรนเดอร์ */
  centerYM: number;
}

const FULL_TURN_DEG = 360;
const RAD_TO_DEG = 180 / Math.PI;

/** มุมกล้องรอบแมวจากตำแหน่งกล้องเทียบแมว (dx, dz) → 0..360 */
export function azimuthDeg(dx: number, dz: number): number {
  const deg = Math.atan2(dx, dz) * RAD_TO_DEG;
  return (deg + FULL_TURN_DEG) % FULL_TURN_DEG;
}

/** ระยะเชิงมุมที่สั้นสุด 0..180 */
function angleGap(a: number, b: number): number {
  const d = Math.abs(a - b) % FULL_TURN_DEG;
  return Math.min(d, FULL_TURN_DEG - d);
}

/** ดัชนีทิศที่ใกล้มุมกล้องที่สุด */
export function pickDir(azDeg: number, dirDeg: readonly number[]): number {
  let best = 0;
  dirDeg.forEach((deg, i) => {
    if (angleGap(azDeg, deg) < angleGap(azDeg, dirDeg[best])) best = i;
  });
  return best;
}

/** เฟรมที่เวลา timeS (วนท่า) */
export function frameIndex(timeS: number, fps: number, count: number): number {
  if (count <= 0) return 0;
  const k = Math.floor(timeS * fps) % count;
  return k < 0 ? k + count : k;
}
