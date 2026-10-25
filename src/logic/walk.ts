/** มุ่ยเดินบนพื้น : ทิศจากปุ่ม/คันโยกเทียบมุมกล้อง → หันตัวทีละนิด → เดินไปทางที่หัวหัน · ตรรกะล้วน ไม่รู้จัก three.js
 *  มุมแบบ logic/orbit : heading 0 = หันไป +Z · บวก = หันไป +X · กล้อง yaw 0 = อยู่ด้าน +Z มองไป −Z */

export interface WalkState { x: number; z: number; headingDeg: number; moving: boolean; running: boolean }
export interface WalkCfg { walkMps: number; runMps: number; turnDegPerS: number; areaRadiusM: number; minInput: number }
/** x = ขวาของจอ · y = ไปข้างหน้า (ห่างกล้อง) · -1..1 */
export interface MoveInput { x: number; y: number; run: boolean }

const DEG = Math.PI / 180;
const FULL_TURN_DEG = 360;
const HALF_TURN_DEG = 180;

export function createWalkState(): WalkState {
  return { x: 0, z: 0, headingDeg: 0, moving: false, running: false };
}

/** มุมต่างแบบสั้นสุด −180..180 */
function deltaDeg(from: number, to: number): number {
  return ((((to - from + HALF_TURN_DEG) % FULL_TURN_DEG) + FULL_TURN_DEG) % FULL_TURN_DEG) - HALF_TURN_DEG;
}

/** ทิศในโลกของปุ่มกด (เทียบกล้อง) → มุมหัน · null = ไม่ได้กด */
function wishHeading(m: MoveInput, camYawDeg: number, minInput: number): { deg: number; mag: number } | null {
  const mag = Math.min(1, Math.hypot(m.x, m.y));
  if (mag < minInput) return null;
  const cy = camYawDeg * DEG;
  const dx = Math.cos(cy) * m.x - Math.sin(cy) * m.y;
  const dz = -Math.sin(cy) * m.x - Math.cos(cy) * m.y;
  return { deg: Math.atan2(dx, dz) / DEG, mag };
}

export function stepWalk(s: WalkState, m: MoveInput, camYawDeg: number, dtS: number, c: WalkCfg): WalkState {
  const wish = wishHeading(m, camYawDeg, c.minInput);
  if (!wish) return { ...s, moving: false, running: false };
  const turn = deltaDeg(s.headingDeg, wish.deg);
  const maxTurn = c.turnDegPerS * dtS;
  const headingDeg = s.headingDeg + Math.max(-maxTurn, Math.min(maxTurn, turn));
  const speed = (m.run ? c.runMps : c.walkMps) * wish.mag;
  let x = s.x + Math.sin(headingDeg * DEG) * speed * dtS;
  let z = s.z + Math.cos(headingDeg * DEG) * speed * dtS;
  const r = Math.hypot(x, z);
  if (r > c.areaRadiusM) {
    x *= c.areaRadiusM / r;
    z *= c.areaRadiusM / r;
  }
  return { x, z, headingDeg, moving: true, running: m.run };
}
