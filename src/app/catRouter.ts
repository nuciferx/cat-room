/** แปลง input เป็นการเปลี่ยนสถานะ + สั่งฝั่งแสดงผล (ตัวเดียวที่ implement InputSink) */
import { ACTION, type Action } from '../constants/actions';
import { CLIP_NAMES } from '../constants/clips';
import { FACE_SETS } from '../constants/faces';
import { VIEW_NAMES, faceViewOf, type ModelViewName } from '../constants/views';
import type { InputSink } from '../input/types';
import type { MoveInput } from '../logic/walk';
import { dragOrbit, zoomByRatio, zoomBySteps } from '../logic/orbit';
import { stepClip, stepFace, stepView } from '../logic/showroomState';
import type { ShowroomCtx } from './context';

export function setClip(ctx: ShowroomCtx, index: number): void {
  const name = CLIP_NAMES[index];
  ctx.state.clipIndex = index;
  ctx.clipBar.setActive(index);
  const ok = ctx.actor.play(name, ctx.cfg.anim.crossfadeS.value);
  if (!ok) ctx.banner.show(ctx.locale.t('error.clipMissing', { clip: name }), ctx.cfg.ui.toastS.value);
}

/** โมเดลที่แถบหน้าคุมอยู่ (ตามแบบที่แสดง) */
export function faceModel(ctx: ShowroomCtx): ModelViewName {
  return faceViewOf(VIEW_NAMES[ctx.state.viewIndex]);
}

/** สลับหน้า (ภาพผิว) ของแมวตัวที่แสดงอยู่ · ไม่มีภาพของหน้านั้น = แจ้งเตือน แถบยังชี้หน้าเดิม */
export function setFace(ctx: ShowroomCtx, index: number): void {
  const model = faceModel(ctx);
  const name = FACE_SETS[model].names[index];
  if (!name || !ctx.actor.setFace(name)) {
    ctx.banner.show(ctx.locale.t('error.faceMissing', { face: name ?? String(index) }), ctx.cfg.ui.toastS.value);
    return;
  }
  ctx.state.faceIndex[model] = index;
  ctx.faceBar.setActive(index);
}

/** แถบหน้าแสดงชุดหน้าของแมวตัวที่แสดงอยู่ + ชี้หน้าที่ตัวนั้นใช้อยู่ */
function syncFaceBar(ctx: ShowroomCtx): void {
  const model = faceModel(ctx);
  ctx.faceBar.setFaces(FACE_SETS[model].names);
  ctx.faceBar.setActive(ctx.state.faceIndex[model]);
}

/** สลับแบบแมว (3D · 2.5D) · ไม่มีแบบนั้น = แจ้งเตือน · สลับแล้วเล่นท่าเดิมซ้ำ (แจ้งถ้าแบบใหม่ไม่มีท่านี้) */
export function setView(ctx: ShowroomCtx, index: number): void {
  if (!ctx.actor.setView(VIEW_NAMES[index])) {
    ctx.banner.show(ctx.locale.t('error.viewMissing'), ctx.cfg.ui.toastS.value);
    return;
  }
  ctx.state.viewIndex = index;
  ctx.viewBar.setActive(index);
  syncFaceBar(ctx);
  setClip(ctx, ctx.state.clipIndex);
}

function togglePlay(ctx: ShowroomCtx): void {
  ctx.state.paused = !ctx.state.paused;
  ctx.actor.setPaused(ctx.state.paused);
  ctx.clipBar.setPaused(ctx.state.paused);
}

function runAction(ctx: ShowroomCtx, action: Action): void {
  const s = ctx.state;
  switch (action) {
    case ACTION.prevClip:
    case ACTION.nextClip:
      stepClip(s, action === ACTION.nextClip ? 1 : -1, CLIP_NAMES.length);
      setClip(ctx, s.clipIndex);
      break;
    case ACTION.nextView:
      setView(ctx, stepView(s, VIEW_NAMES.length));
      break;
    case ACTION.nextFace: {
      const model = faceModel(ctx);
      setFace(ctx, stepFace(s, model, FACE_SETS[model].names.length));
      break;
    }
    case ACTION.togglePlay:
      togglePlay(ctx);
      break;
    case ACTION.toggleGrid:
      s.gridOn = !s.gridOn;
      ctx.stage.floor.setGridVisible(s.gridOn);
      break;
    case ACTION.togglePanel:
      s.panelOpen = !s.panelOpen;
      ctx.tune.setOpen(s.panelOpen);
      break;
    case ACTION.toggleHelp:
      s.helpOn = !s.helpOn;
      ctx.help.setVisible(s.helpOn);
      break;
    case ACTION.resetCamera:
      ctx.rig.reset();
      break;
  }
}

export function createRouter(ctx: ShowroomCtx, onMove: (m: MoveInput) => void): InputSink {
  const { rig, cfg } = ctx;
  return {
    action: (a) => runAction(ctx, a),
    selectClip: (i) => setClip(ctx, i),
    move: (x, y, run) => onMove({ x, y, run }),
    dragPx(dx, dy) {
      const k = cfg.camera.dragDegPerPx.value;
      rig.set(dragOrbit(rig.state, dx * k, dy * k, rig.limits()));
    },
    zoomSteps: (n) => rig.set(zoomBySteps(rig.state, n, cfg.camera.zoomStep.value, rig.limits())),
    pinch: (ratio) => rig.set(zoomByRatio(rig.state, ratio, rig.limits())),
    padRotate(x, y) {
      if (x === 0 && y === 0) return;
      const k = cfg.camera.padRotateDegPerS.value * ctx.frame.dtS;
      rig.set(dragOrbit(rig.state, x * k, y * k, rig.limits()));
    },
    padZoom(axis) {
      if (axis === 0) return;
      const steps = -axis * cfg.camera.padZoomStepsPerS.value * ctx.frame.dtS;
      rig.set(zoomBySteps(rig.state, steps, cfg.camera.zoomStep.value, rig.limits()));
    },
  };
}
