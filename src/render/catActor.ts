/** แมวในฉาก : ตัวจริงจาก glb (AnimationMixer + crossfade) หรือแคปซูลสำรอง ใช้ interface เดียวกัน
 *  จุดที่ไม่ชัด : ระหว่างหยุดเล่น (timeScale 0) เฟดไม่เดิน จึงสลับท่าทันทีแล้ว update(0) ให้ท่าใหม่ขึ้นจอ */
import { AnimationMixer, CapsuleGeometry, Color, Mesh, MeshStandardMaterial, type AnimationAction, type Object3D } from 'three';
import type { GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import type { ClipName } from '../constants/clips';
import { FACE_SETS, type FaceName } from '../constants/faces';
import type { CatConfig } from '../data/config';
import { createFaceSwapper, type FaceSkins } from './catBlink';

export interface CatActor {
  root: Object3D;
  /** เล่นท่า (เฟดข้ามจากท่าเดิม fadeS วินาที) · คืน false ถ้าไม่มีท่านี้ในโมเดล */
  play(name: ClipName, fadeS: number): boolean;
  setPaused(paused: boolean): void;
  setSpeed(speed: number): void;
  /** หลับตา/ลืมตา (สลับภาพผิว) · ไม่มีภาพหลับตา = ไม่ทำอะไร */
  setEyesClosed(closed: boolean): void;
  /** สลับหน้า (ภาพผิว) · false ถ้าไม่มีภาพของหน้านี้ */
  setFace(face: FaceName): boolean;
  update(dtS: number): void;
}

/** SkinnedMesh : ปิด frustum culling กันแมวหายเมื่อท่าขยับออกนอกกล่องเดิม · ให้ทุกชิ้นรับ/ทอดเงา */
function prepareMeshes(root: Object3D): void {
  root.traverse((o) => {
    if (!(o as Mesh).isMesh) return;
    o.frustumCulled = false;
    o.castShadow = true;
    o.receiveShadow = true;
  });
}

const NO_SKINS: FaceSkins = { blink: null, faces: {}, defaultFace: FACE_SETS['3d'].names[0] };

export function createGltfActor(gltf: GLTF, skins: FaceSkins = NO_SKINS): CatActor {
  const root = gltf.scene;
  prepareMeshes(root);
  const mixer = new AnimationMixer(root);
  const actions = new Map<string, AnimationAction>(gltf.animations.map((c) => [c.name, mixer.clipAction(c)]));
  const skin = createFaceSwapper(root, skins);
  let current: AnimationAction | null = null;
  let paused = false;
  let speed = 1;

  const syncScale = (): void => {
    mixer.timeScale = paused ? 0 : speed;
  };

  return {
    root,
    play(name, fadeS) {
      const next = actions.get(name);
      if (!next) return false;
      if (next === current) return true;
      const instant = paused || fadeS <= 0 || current === null;
      next.reset().play();
      if (current) {
        if (instant) current.stop();
        else next.crossFadeFrom(current, fadeS, false);
      }
      current = next;
      if (paused) mixer.update(0);
      return true;
    },
    setPaused(p) {
      paused = p;
      syncScale();
    },
    setSpeed(s) {
      speed = s;
      syncScale();
    },
    setEyesClosed(closed) {
      skin?.setClosed(closed);
    },
    setFace(face) {
      return skin?.setFace(face) ?? false;
    },
    update(dtS) {
      mixer.update(dtS);
    },
  };
}

/** แคปซูลขนาดแมวยืนตรง (ใช้เมื่อโหลด glb ไม่ได้) · play() แค่รับทราบ ไม่มีแอนิเมชัน */
export function createCapsuleActor(cfg: CatConfig['fallback']): CatActor {
  const radius = cfg.radiusM.value;
  const body = new Mesh(
    new CapsuleGeometry(radius, Math.max(0, cfg.heightM.value - 2 * radius), 8, 16),
    new MeshStandardMaterial({ color: new Color(cfg.color.value) }),
  );
  body.position.y = cfg.heightM.value / 2;
  body.castShadow = true;
  body.receiveShadow = true;
  return { root: body, play: () => true, setPaused: () => {}, setSpeed: () => {}, setEyesClosed: () => {}, setFace: () => false, update: () => {} };
}
