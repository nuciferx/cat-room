/** กล้อง perspective orbit รอบแมว : เก็บสถานะ yaw/pitch/ระยะ แล้วคำนวณตำแหน่งด้วย logic/orbit */
import { PerspectiveCamera } from 'three';
import type { CatConfig } from '../data/config';
import { fitDistance } from '../logic/cameraFit';
import { clamp, orbitPosition, type OrbitLimits, type OrbitState } from '../logic/orbit';

export interface CameraRig {
  camera: PerspectiveCamera;
  state: OrbitState;
  limits(): OrbitLimits;
  /** ตั้งสถานะใหม่แล้วจัดกล้อง */
  set(state: OrbitState): void;
  /** กลับค่าเริ่มต้นจาก config */
  reset(): void;
  /** อ่าน fov/near/far/จุดมองใหม่จาก config แล้วจัดกล้อง (เรียกเมื่อแผง F1 ขยับ) */
  refresh(): void;
  /** ขนาดจอ + สัดส่วนความสูงที่แถบปุ่มบังด้านล่าง : เลื่อนภาพให้แมวอยู่กลางพื้นที่ที่ไม่ถูกบัง
   *  และดึงกล้องออกให้แมวทั้งตัวพอดี (ทำใหม่เมื่อจอพลิกตั้ง/นอน · ไม่ทับซูมของผู้ใช้ตอนปรับขนาดเล็กน้อย) */
  setLayout(width: number, height: number, insetFrac: number): void;
  /** จุดมองตามแมว (พื้น x, z) */
  setTarget(x: number, z: number): void;
}

export function createCameraRig(cfg: CatConfig): CameraRig {
  const camera = new PerspectiveCamera();
  const startState = (): OrbitState => ({
    yawDeg: cfg.camera.yawStartDeg.value,
    pitchDeg: cfg.camera.pitchStartDeg.value,
    dist: startDist(),
  });

  const target = { x: 0, z: 0 };
  const layout = { aspect: 1, insetFrac: 0 };
  let fittedPortrait: boolean | null = null;
  /** ระยะเริ่มต้น : ตาม config แต่ไม่ใกล้กว่าที่แมวทั้งตัวจะพอดีจอ */
  const startDist = (): number => {
    const c = cfg.camera;
    const fit = fitDistance({
      vfovDeg: c.fovDeg.value, aspect: layout.aspect, insetFrac: layout.insetFrac,
      widthM: c.fitWidthM.value, heightM: c.fitHeightM.value,
    });
    return clamp(Math.max(c.distStartM.value, fit), c.zoomMinM.value, c.zoomMaxM.value);
  };
  const place = (): void => {
    const c = cfg.camera;
    const p = orbitPosition(rig.state, c.targetHeightM.value);
    camera.position.set(p.x + target.x, p.y, p.z + target.z);
    camera.lookAt(target.x, c.targetHeightM.value, target.z);
  };

  const rig: CameraRig = {
    camera,
    state: startState(),
    limits: () => ({
      pitchMinDeg: cfg.camera.pitchMinDeg.value,
      pitchMaxDeg: cfg.camera.pitchMaxDeg.value,
      distMin: cfg.camera.zoomMinM.value,
      distMax: cfg.camera.zoomMaxM.value,
    }),
    set(state) {
      rig.state = state;
      place();
    },
    reset() {
      rig.set(startState());
    },
    refresh() {
      camera.fov = cfg.camera.fovDeg.value;
      camera.near = cfg.camera.near.value;
      camera.far = cfg.camera.far.value;
      camera.updateProjectionMatrix();
      place();
    },
    setLayout(width, height, insetFrac) {
      layout.aspect = width / height;
      layout.insetFrac = insetFrac;
      camera.aspect = layout.aspect;
      if (insetFrac > 0) camera.setViewOffset(width, height, 0, Math.round((insetFrac * height) / 2), width, height);
      else camera.clearViewOffset();
      camera.updateProjectionMatrix();
      const portrait = layout.aspect < 1;
      if (portrait === fittedPortrait) return;
      fittedPortrait = portrait;
      rig.set({ ...rig.state, dist: startDist() });
    },
    setTarget(x, z) {
      target.x = x;
      target.z = z;
      place();
    },
  };
  rig.refresh();
  return rig;
}
