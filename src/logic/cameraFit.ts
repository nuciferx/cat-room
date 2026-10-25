/** ระยะกล้องที่ทำให้แมวทั้งตัวอยู่ในจอ : คำนวณจาก fov แนวตั้ง สัดส่วนจอ และส่วนล่างที่แถบปุ่มบัง (ไม่รู้จัก three.js) */
const DEG = Math.PI / 180;

export interface FitInput {
  vfovDeg: number;
  /** กว้าง / สูง ของจอ */
  aspect: number;
  /** สัดส่วนความสูงจอที่แถบปุ่มบังด้านล่าง (0–<1) */
  insetFrac: number;
  /** ขนาดบริเวณที่ต้องเห็นเต็มที่จุดมอง (เมตร) */
  widthM: number;
  heightM: number;
}

export function fitDistance(i: FitInput): number {
  const tanV = Math.tan((i.vfovDeg * DEG) / 2);
  const freeHeight = Math.max(1 - i.insetFrac, 0.1);
  const byHeight = i.heightM / 2 / (tanV * freeHeight);
  const byWidth = i.widthM / 2 / (tanV * Math.max(i.aspect, 0.1));
  return Math.max(byHeight, byWidth);
}
