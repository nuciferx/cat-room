/** จุดเริ่มห้องโชว์แมว (cat.html) : ประกอบชั้นข้อมูล/ฉาก/UI/input เข้าด้วยกัน แล้วเดินลูปเรนเดอร์ */
import '../ui/catPage.css';
import { ACTION } from '../constants/actions';
import { DEFAULT_CLIP, CLIP_NAMES } from '../constants/clips';
import { DOM_ID } from '../constants/dom';
import { FACE_SETS } from '../constants/faces';
import { DEFAULT_VIEW, VIEW_NAMES, faceViewOf } from '../constants/views';
import { loadConfig, type CatConfig } from '../data/config';
import { createLocale, type Locale } from '../data/locale';
import { parseQuery, type PageQuery } from '../data/query';
import { createInputHub } from '../input/inputHub';
import { createState } from '../logic/showroomState';
import { createCameraRig, type CameraRig } from '../render/cameraRig';
import { createStage, type Stage } from '../render/stage';
import type { DualActor } from '../render/dualActor';
import { createBanner, type Banner } from '../ui/banner';
import { createClipBar } from '../ui/clipBar';
import { createFaceBar } from '../ui/faceBar';
import { createViewBar } from '../ui/viewBar';
import { createHelpPanel } from '../ui/helpPanel';
import { bindHelpToggle } from '../ui/helpToggle';
import { createLayoutMode, type LayoutMode } from '../ui/layoutMode';
import { createTunePanel } from '../ui/tunePanel';
import { loadActor } from './actorLoader';
import { createBlinkDriver } from './blinkDriver';
import { watchContextLoss } from './contextLoss';
import { createWalkDriver, type WalkDriver } from './walkDriver';
import type { ShowroomCtx } from './context';
import { createRouter, faceModel, setClip, setFace, setView } from './catRouter';

/** แถบหน้าตอนเปิดหน้า = ชุดหน้าของโมเดลที่แบบเริ่มต้นผูกอยู่ */
const DEFAULT_FACE_MODEL = faceViewOf(DEFAULT_VIEW);

function el<T extends HTMLElement>(id: string): T {
  return document.getElementById(id) as T;
}

function startLoop(ctx: ShowroomCtx, walk: WalkDriver, poll: (deadzone: number) => void): void {
  const blink = createBlinkDriver(ctx.cfg, ctx.actor);
  let last = performance.now();
  const tick = (now: number): void => {
    ctx.frame.dtS = Math.min((now - last) / 1000, ctx.cfg.camera.maxDtS.value);
    last = now;
    poll(ctx.cfg.camera.padDeadzone.value);
    walk.update(ctx.frame.dtS);
    ctx.actor.update(ctx.frame.dtS);
    blink.update(ctx.frame.dtS, ctx.state.paused);
    ctx.stage.render(ctx.rig.camera);
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

interface Scene3d {
  stage: Stage;
  rig: CameraRig;
  actor: DualActor;
  applyTune(): void;
}

/** สร้าง renderer + กล้อง + แมว แล้วผูกการปรับตามขนาดจอ/ค่าจูน · null ถ้าเปิด WebGL ไม่ได้ */
async function buildScene(query: PageQuery, cfg: CatConfig, locale: Locale, banner: Banner, layout: LayoutMode): Promise<Scene3d | null> {
  const canvas = el<HTMLCanvasElement>(DOM_ID.canvas);
  let stage: Stage;
  try {
    stage = createStage(canvas, query.low, query.grid);
  } catch (err) {
    console.error(err);
    banner.show(locale.t('error.noWebgl'));
    return null;
  }
  watchContextLoss(canvas, locale, banner);
  const rig = createCameraRig(cfg);
  const actor = await loadActor({ cfg, locale, banner, camera: rig.camera, maxTexturePx: stage.maxTextureSize });
  stage.scene.add(actor.root);
  const resize = (): void => {
    const { compact, barFrac } = layout.refresh();
    stage.resize(canvas.clientWidth, canvas.clientHeight, cfg, compact);
    rig.setLayout(canvas.clientWidth, canvas.clientHeight, barFrac);
  };
  const applyTune = (): void => {
    stage.apply(cfg, layout.refresh().compact);
    rig.refresh();
    actor.setSpeed(cfg.anim.speed.value);
    resize();
  };
  applyTune();
  window.addEventListener('resize', resize);
  return { stage, rig, actor, applyTune };
}

async function main(): Promise<void> {
  const query = parseQuery(location.search);
  const locale = createLocale(query.lang);
  document.documentElement.lang = query.lang;
  document.title = locale.t('app.title');
  const cfg = loadConfig();
  const banner = createBanner(el(DOM_ID.banner));
  const layout = createLayoutMode(cfg, el(DOM_ID.bar));
  const compact = layout.refresh().compact;
  const scene = await buildScene(query, cfg, locale, banner, layout);
  if (!scene) return;

  // จอสัมผัสไม่มีคีย์ H : ซ่อนป้ายช่วยเหลือไว้ก่อน มีปุ่มเล็กเปิด
  const state = createState(CLIP_NAMES.indexOf(query.clip ?? DEFAULT_CLIP), VIEW_NAMES.indexOf(DEFAULT_VIEW), query.grid, !compact);
  const ctx: ShowroomCtx = {
    cfg, state, locale, banner, rig: scene.rig, actor: scene.actor, stage: scene.stage, frame: { dtS: 0 },
    clipBar: createClipBar(el(DOM_ID.clipBar), el(DOM_ID.current), locale.t, (i) => setClip(ctx, i)),
    viewBar: createViewBar(el(DOM_ID.viewBar), locale.t, (i) => setView(ctx, i)),
    faceBar: createFaceBar(el(DOM_ID.faceBar), locale.t, FACE_SETS[DEFAULT_FACE_MODEL].names, (i) => setFace(ctx, i)),
    help: createHelpPanel(el(DOM_ID.help), locale),
    tune: createTunePanel(el(DOM_ID.tune), cfg, locale.t, {
      onChange: scene.applyTune,
      notify: (text) => banner.show(text, cfg.ui.toastS.value),
    }),
  };
  setClip(ctx, state.clipIndex);
  ctx.faceBar.setActive(state.faceIndex[DEFAULT_FACE_MODEL]);
  ctx.viewBar.setActive(state.viewIndex);
  ctx.help.setVisible(state.helpOn);
  if (query.view) await setView(ctx, VIEW_NAMES.indexOf(query.view));
  if (query.face) setFace(ctx, FACE_SETS[faceModel(ctx)].names.indexOf(query.face));
  const walk = createWalkDriver(ctx);
  const router = createRouter(ctx, walk.setMove);
  bindHelpToggle(el<HTMLButtonElement>(DOM_ID.helpToggle), locale.t, () => router.action(ACTION.toggleHelp));
  const hub = createInputHub(el<HTMLCanvasElement>(DOM_ID.canvas), router);
  startLoop(ctx, walk, hub.poll);
}

void main();
