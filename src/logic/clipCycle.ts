/** เลือกคลิปถัดไป/ก่อนหน้าแบบวนรอบ และแปลงเลขปุ่มเป็นลำดับคลิป · ตรรกะล้วน */

/** ขยับ index ไป dir (+1/-1) วนรอบในช่วง 0..count-1 */
export function stepIndex(index: number, dir: number, count: number): number {
  return (((index + dir) % count) + count) % count;
}

/** ปุ่มเลข 1–9 → 0–8, ปุ่ม 0 → 9 · คืน -1 ถ้าเกินจำนวนคลิป */
export function digitToIndex(digit: number, count: number): number {
  const index = digit === 0 ? 9 : digit - 1;
  return index < count ? index : -1;
}
