/** กล้อง orbit รอบจุดมอง : yaw/pitch/ระยะ → ตำแหน่ง · clamp ซูม/ก้มเงย · ตรรกะล้วน ไม่รู้จัก three.js
 *  yaw 0 = กล้องอยู่ด้านหน้าแมว (+Z) · yaw บวก = ไปทาง +X · pitch บวก = กล้องสูงขึ้น */

export interface OrbitState { yawDeg: number; pitchDeg: number; dist: number }
export interface OrbitLimits { pitchMinDeg: number; pitchMaxDeg: number; distMin: number; distMax: number }
export interface Vec3 { x: number; y: number; z: number }

const DEG = Math.PI / 180;
const FULL_TURN_DEG = 360;
const HALF_TURN_DEG = 180;

export function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}

/** ห่อมุม yaw ให้อยู่ใน -180..180 */
function wrapDeg(deg: number): number {
  return ((((deg + HALF_TURN_DEG) % FULL_TURN_DEG) + FULL_TURN_DEG) % FULL_TURN_DEG) - HALF_TURN_DEG;
}

export function clampOrbit(s: OrbitState, lim: OrbitLimits): OrbitState {
  return {
    yawDeg: wrapDeg(s.yawDeg),
    pitchDeg: clamp(s.pitchDeg, lim.pitchMinDeg, lim.pitchMaxDeg),
    dist: clamp(s.dist, lim.distMin, lim.distMax),
  };
}

/** ลากเมาส์/นิ้ว (หน่วยองศา) : ลากขวา → กล้องวนซ้าย · ลากลง → กล้องสูงขึ้น */
export function dragOrbit(s: OrbitState, dxDeg: number, dyDeg: number, lim: OrbitLimits): OrbitState {
  return clampOrbit({ ...s, yawDeg: s.yawDeg - dxDeg, pitchDeg: s.pitchDeg + dyDeg }, lim);
}

/** ซูมเป็นก้าว : steps บวก = ถอยออก (ระยะ × step^steps) */
export function zoomBySteps(s: OrbitState, steps: number, stepFactor: number, lim: OrbitLimits): OrbitState {
  return clampOrbit({ ...s, dist: s.dist * Math.pow(stepFactor, steps) }, lim);
}

/** ซูมแบบถ่างนิ้ว : ratio = ระยะนิ้วใหม่ ÷ เก่า (ถ่างออก ratio>1 → ระยะกล้องลด) */
export function zoomByRatio(s: OrbitState, ratio: number, lim: OrbitLimits): OrbitState {
  return clampOrbit({ ...s, dist: s.dist / ratio }, lim);
}

/** ตำแหน่งกล้องรอบจุดมอง (0, targetY, 0) */
export function orbitPosition(s: OrbitState, targetY: number): Vec3 {
  const yaw = s.yawDeg * DEG;
  const pitch = s.pitchDeg * DEG;
  const flat = Math.cos(pitch) * s.dist;
  return { x: Math.sin(yaw) * flat, y: targetY + Math.sin(pitch) * s.dist, z: Math.cos(yaw) * flat };
}

/** ทิศแสงอาทิตย์จาก azimuth/elevation (องศา) · ใช้สูตรเดียวกับกล้อง */
export function sunDirection(azimuthDeg: number, elevationDeg: number): Vec3 {
  return orbitPosition({ yawDeg: azimuthDeg, pitchDeg: elevationDeg, dist: 1 }, 0);
}
