/** แมวหลายแบบในฉากเดียว (มุ่ย 3D · มุ่ย 2.5D · เจ้าส้ม 2.5D/3D · เจ้าดำ 2.5D) : สั่งทุกแบบที่โหลดแล้วพร้อมกันให้ท่าตรงกัน · แสดงทีละแบบ
 *  แบบที่ยังไม่โหลดจะโหลดตอนสลับไปครั้งแรก (ensureView) เพื่อไม่ให้มือถือกินหน่วยความจำตั้งแต่เปิดหน้า */
import { Group } from 'three';
import { DEFAULT_VIEW, MODEL_VIEWS, VIEW_NAMES, faceViewOf, type ViewName } from '../constants/views';
import type { CatActor } from './catActor';

export interface DualActor extends CatActor {
  /** false ถ้าแบบนั้นยังไม่โหลด/โหลดไม่ได้ (ให้เรียก ensureView ก่อน) */
  setView(view: ViewName): boolean;
  /** โหลดแล้วหรือยัง */
  hasView(view: ViewName): boolean;
  /** โหลดแบบนั้นถ้ายังไม่โหลด · false ถ้าโหลดไม่ได้ (ผู้โหลดแจ้งเตือนเอง) */
  ensureView(view: ViewName): Promise<boolean>;
}

/** สร้างแมวของแบบที่ขอ · null = ไม่ได้ */
export type ViewLoader = (view: ViewName) => Promise<CatActor | null>;

/** โหลดแบบที่ยังไม่มีทีละครั้ง (เรียกซ้ำระหว่างโหลด = รอตัวเดิม) แล้วส่งให้ adopt */
function createLazyLoader(
  actors: Partial<Record<ViewName, CatActor>>,
  loadView: ViewLoader,
  adopt: (v: ViewName, a: CatActor) => void,
): (v: ViewName) => Promise<boolean> {
  const pending = new Map<ViewName, Promise<boolean>>();
  const load = async (v: ViewName): Promise<boolean> => {
    const a = await loadView(v);
    if (a) adopt(v, a);
    return a !== null;
  };
  return (v) => {
    if (actors[v]) return Promise.resolve(true);
    let job = pending.get(v);
    if (!job) {
      job = load(v).finally(() => pending.delete(v));
      pending.set(v, job);
    }
    return job;
  };
}

export function createDualActor(initial: Partial<Record<ViewName, CatActor>>, loadView: ViewLoader): DualActor {
  const actors: Partial<Record<ViewName, CatActor>> = { ...initial };
  let view: ViewName = DEFAULT_VIEW;
  let paused = false;
  let speed = 1;
  const root = new Group();
  const all = (): CatActor[] => VIEW_NAMES.flatMap((v) => actors[v] ?? []);
  const sync = (): void => VIEW_NAMES.forEach((v) => { const a = actors[v]; if (a) a.root.visible = v === view; });
  const adopt = (v: ViewName, a: CatActor): void => {
    actors[v] = a;
    a.setPaused(paused);
    a.setSpeed(speed);
    root.add(a.root);
    sync();
  };
  const ensureView = createLazyLoader(actors, loadView, adopt);
  for (const a of all()) root.add(a.root);
  sync();
  return {
    root,
    /** ผลของแบบที่แสดงอยู่ (ท่าที่แบบนั้นไม่มี = แจ้งเตือน) */
    play(name, fadeS) {
      const ok = all().map((a) => [a, a.play(name, fadeS)] as const);
      return ok.find(([a]) => a === actors[view])?.[1] ?? false;
    },
    setPaused(p) {
      paused = p;
      all().forEach((a) => a.setPaused(p));
    },
    setSpeed(s) {
      speed = s;
      all().forEach((a) => a.setSpeed(s));
    },
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
    hasView: (v) => actors[v] !== undefined,
    ensureView,
  };
}
