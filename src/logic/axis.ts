/** แกนอนาล็อก (ไม้จอย/ไกปืน) : ตัดโซนตายแล้วขยายค่าที่เหลือให้ยังเต็ม -1..1 · ตรรกะล้วน */
export function applyDeadzone(v: number, deadzone: number): number {
  const mag = Math.abs(v);
  if (mag <= deadzone) return 0;
  return Math.sign(v) * Math.min(1, (mag - deadzone) / (1 - deadzone));
}
