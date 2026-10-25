/** กล้อง perspective orbit รอบแมว : เก็บสถานะ yaw/pitch/ระยะ แล้วคำนวณตำแหน่งด้วย logic/orbit */
import { PerspectiveCamera } from 'three';
import type { CatConfig } from '../data/config';
import { orbitPosition, type OrbitLimits, type OrbitState } from '../logic/orbit';

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
  setAspect(aspect: number): void;
  /** จุดมองตามแมว (พื้น x, z) */
  setTarget(x: number, z: number): void;
}

export function createCameraRig(cfg: CatConfig): CameraRig {
  const camera = new PerspectiveCamera();
  const startState = (): OrbitState => ({
    yawDeg: cfg.camera.yawStartDeg.value,
    pitchDeg: cfg.camera.pitchStartDeg.value,
    dist: cfg.camera.distStartM.value,
  });

  const target = { x: 0, z: 0 };
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
    setAspect(aspect) {
      camera.aspect = aspect;
      camera.updateProjectionMatrix();
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
