/** มุ่ยแบบ 2.5D : ภาพแบนหันหากล้องเสมอ (three.js Sprite) · เลือกแถวทิศจากมุมกล้อง เลือกคอลัมน์จากเวลา
 *  ไม่เช็กความลึก (วาดทับพื้น) : ครึ่งล่างของภาพแบนตั้งฉากกับกล้องจะจมใต้พื้นเมื่อกล้องก้ม */
import { Group, LinearFilter, Quaternion, SRGBColorSpace, Sprite, SpriteMaterial, Vector3, type Camera, type Texture } from 'three';
import type { ClipName } from '../constants/clips';
import type { CatConfig } from '../data/config';
import type { SpriteSet } from '../data/spriteLoader';
import { azimuthDeg, frameIndex, pickDir } from '../logic/spriteFrame';
import type { CatActor } from './catActor';

const RAD_TO_DEG = 180 / Math.PI;
const pos = new Vector3();
const fwd = new Vector3();
const quat = new Quaternion();

/** มุมกล้องเทียบทิศที่แมวหัน (แมวเดินแล้วหมุนตัว ภาพต้องเปลี่ยนทิศตาม) */
function viewAngle(root: Group, camera: Camera): number {
  root.getWorldPosition(pos);
  root.getWorldQuaternion(quat);
  fwd.set(0, 0, 1).applyQuaternion(quat);
  const heading = Math.atan2(fwd.x, fwd.z) * RAD_TO_DEG;
  return azimuthDeg(camera.position.x - pos.x, camera.position.z - pos.z) - heading;
}

/** วาดหลังพื้นและตาราง */
const SPRITE_RENDER_ORDER = 10;

function prepare(tex: Texture, cols: number, rows: number): void {
  tex.colorSpace = SRGBColorSpace;
  tex.magFilter = LinearFilter;
  tex.minFilter = LinearFilter;
  tex.generateMipmaps = false;
  tex.repeat.set(1 / cols, 1 / rows);
  tex.needsUpdate = true;
}

export function createSpriteActor(set: SpriteSet, camera: Camera, cfg: CatConfig): CatActor {
  const { meta, sheets } = set;
  const rows = meta.dirs.length;
  for (const [clip, tex] of Object.entries(sheets)) prepare(tex, meta.frames[clip], rows);
  const material = new SpriteMaterial({ transparent: true, depthTest: false, depthWrite: false });
  const sprite = new Sprite(material);
  sprite.renderOrder = SPRITE_RENDER_ORDER;
  const root = new Group();
  root.add(sprite);
  let clip: string | null = null;
  let timeS = 0;
  let paused = false;
  let speed = 1;

  const show = (): void => {
    const tex = clip ? sheets[clip] : undefined;
    if (!clip || !tex) return;
    const cols = meta.frames[clip];
    const dir = pickDir(viewAngle(root, camera), meta.dirDeg);
    const col = frameIndex(timeS, meta.fps, cols);
    tex.offset.set(col / cols, 1 - (dir + 1) / rows);
    if (material.map !== tex) {
      material.map = tex;
      material.needsUpdate = true;
    }
    const size = meta.worldSizeM * cfg.sprite.sizeMul.value;
    sprite.scale.set(size, size, 1);
    sprite.position.y = meta.centerYM * cfg.sprite.sizeMul.value;
  };

  return {
    root,
    play(name: ClipName) {
      if (!sheets[name]) return false;
      if (clip !== name) timeS = 0;
      clip = name;
      show();
      return true;
    },
    setPaused(p) {
      paused = p;
    },
    setSpeed(s) {
      speed = s;
    },
    setEyesClosed: () => {},
    setFace: () => false,
    update(dtS) {
      if (!paused) timeS += dtS * speed;
      show();
    },
  };
}
