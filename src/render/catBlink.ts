/** สลับ material.map ของเมชแมว : หน้า (บึ้ง/คลายเครียด ฯลฯ) × ตา (ลืม/หลับ) · ใช้วัสดุตัวเดิม ไม่สร้างใหม่
 *  กระพริบได้เฉพาะหน้าเริ่มต้นของตัวนั้น (ภาพหลับตามีแค่คู่กับหน้านี้) · หน้าอื่นสั่งหลับตาแล้วไม่เปลี่ยน */
import type { Material, Mesh, MeshStandardMaterial, Object3D, Texture } from 'three';
import type { FaceName } from '../constants/faces';

export interface FaceSkins {
  /** ภาพหลับตาของหน้าเริ่มต้น · null = ไม่กระพริบ */
  blink: Texture | null;
  /** ภาพของหน้าอื่น (หน้าเริ่มต้นใช้ map เดิมใน glb) */
  faces: Partial<Record<FaceName, Texture>>;
  /** หน้าที่ใช้ map เดิมใน glb (หน้าเริ่มต้นของตัวนี้) */
  defaultFace: FaceName;
}

export interface FaceSwapper {
  setClosed(closed: boolean): void;
  /** false ถ้าไม่มีภาพของหน้านี้ */
  setFace(face: FaceName): boolean;
}

function findMaterial(root: Object3D): MeshStandardMaterial | null {
  let found: MeshStandardMaterial | null = null;
  root.traverse((o) => {
    if (found || !(o as Mesh).isMesh) return;
    const m = (o as Mesh).material as Material | Material[];
    const mat = Array.isArray(m) ? m[0] : m;
    if (mat && (mat as MeshStandardMaterial).map) found = mat as MeshStandardMaterial;
  });
  return found;
}

/** ตั้งภาพสำรองให้ตรงกับ map เดิม (ภาพใน glTF ไม่พลิก) */
function matchTexture(tex: Texture, base: Texture): void {
  tex.flipY = false;
  tex.colorSpace = base.colorSpace;
  tex.channel = base.channel;
  tex.wrapS = base.wrapS;
  tex.wrapT = base.wrapT;
  tex.anisotropy = base.anisotropy;
  tex.needsUpdate = true;
}

/** null ถ้าหาวัสดุที่มี map ไม่เจอ (สลับผิวไม่ได้) */
export function createFaceSwapper(root: Object3D, skins: FaceSkins): FaceSwapper | null {
  const mat = findMaterial(root);
  const base = mat?.map;
  if (!mat || !base) return null;
  const faces: Partial<Record<FaceName, Texture>> = { ...skins.faces, [skins.defaultFace]: base };
  for (const tex of [skins.blink, ...Object.values(skins.faces)]) if (tex) matchTexture(tex, base);
  let face: FaceName = skins.defaultFace;
  let closed = false;
  const sync = (): void => {
    const blink = closed && face === skins.defaultFace ? skins.blink : null;
    const next = blink ?? faces[face] ?? base;
    if (mat.map !== next) mat.map = next;
  };
  return {
    setClosed(c) {
      closed = c;
      sync();
    },
    setFace(f) {
      if (!faces[f]) return false;
      face = f;
      sync();
      return true;
    },
  };
}
