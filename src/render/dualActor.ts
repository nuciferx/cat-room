/** แมวหลายแบบในฉากเดียว (มุ่ย 3D · มุ่ย 2.5D · เจ้าส้ม 2.5D/3D · เจ้าดำ 2.5D) : สั่งทุกแบบพร้อมกันให้ท่าตรงกัน · แสดงทีละแบบ */
import { Group } from 'three';
import { DEFAULT_VIEW, MODEL_VIEWS, VIEW_NAMES, faceViewOf, type ViewName } from '../constants/views';
import type { CatActor } from './catActor';

export interface DualActor extends CatActor {
  /** false ถ้าไม่มีแมวแบบนั้น (เช่น ยังไม่มีภาพ 2.5D) */
  setView(view: ViewName): boolean;
  hasView(view: ViewName): boolean;
}

export function createDualActor(actors: Record<ViewName, CatActor | null>): DualActor {
  let view: ViewName = DEFAULT_VIEW;
  const all = (): CatActor[] => VIEW_NAMES.map((v) => actors[v]).filter((a): a is CatActor => a !== null);
  const sync = (): void => {
    for (const v of VIEW_NAMES) {
      const a = actors[v];
      if (a) a.root.visible = v === view;
    }
  };
  sync();
  const root = new Group();
  for (const a of all()) root.add(a.root);
  return {
    root,
    /** ผลของแบบที่แสดงอยู่ (ท่าที่แบบนั้นไม่มี = แจ้งเตือน) */
    play(name, fadeS) {
      const ok = all().map((a) => [a, a.play(name, fadeS)] as const);
      return ok.find(([a]) => a === actors[view])?.[1] ?? false;
    },
    setPaused: (p) => all().forEach((a) => a.setPaused(p)),
    setSpeed: (s) => all().forEach((a) => a.setSpeed(s)),
    /** ทุกโมเดลกระพริบพร้อมกัน (เห็นแค่ตัวที่แสดง) */
    setEyesClosed: (c) => MODEL_VIEWS.forEach((m) => actors[m]?.setEyesClosed(c)),
    /** หน้าของโมเดลที่ผูกกับแบบที่แสดงอยู่ (constants/views faceViewOf) */
    setFace: (f) => actors[faceViewOf(view)]?.setFace(f) ?? false,
    update: (dtS) => all().forEach((a) => a.update(dtS)),
    setView(v) {
      if (!actors[v]) return false;
      view = v;
      sync();
      return true;
    },
    hasView: (v) => actors[v] !== null,
  };
}
