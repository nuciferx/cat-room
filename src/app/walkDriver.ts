/** เดินมุ่ยทุกเฟรม : รับทิศจาก router → logic/walk → ย้าย/หมุนตัวแมว + กล้องตาม · เริ่มเดินเล่นท่าเดิน/วิ่ง หยุดแล้วกลับท่าที่เลือกไว้
 *  หยุดเล่น (Space) = ไม่เดิน */
import type { ClipName } from '../constants/clips';
import type { CatConfig } from '../data/config';
import { createWalkState, stepWalk, type MoveInput, type WalkCfg, type WalkState } from '../logic/walk';
import type { ShowroomCtx } from './context';
import { setClip } from './catRouter';

const WALK_CLIP: ClipName = 'walk';
const RUN_CLIP: ClipName = 'run';
const DEG = Math.PI / 180;

export interface WalkDriver {
  setMove(m: MoveInput): void;
  update(dtS: number): void;
}

function readCfg(c: CatConfig['walk']): WalkCfg {
  return {
    walkMps: c.walkMps.value,
    runMps: c.runMps.value,
    turnDegPerS: c.turnDegPerS.value,
    areaRadiusM: c.areaRadiusM.value,
    minInput: c.minInput.value,
  };
}

function gaitClip(ctx: ShowroomCtx, s: WalkState): void {
  // ภาพ 2.5D ไม่มีท่าวิ่ง → ใช้ท่าเดิน
  if (s.running && ctx.actor.play(RUN_CLIP, ctx.cfg.anim.crossfadeS.value)) return;
  ctx.actor.play(WALK_CLIP, ctx.cfg.anim.crossfadeS.value);
}

export function createWalkDriver(ctx: ShowroomCtx): WalkDriver {
  let move: MoveInput = { x: 0, y: 0, run: false };
  let state = createWalkState();
  return {
    setMove(m) {
      move = m;
    },
    update(dtS) {
      if (ctx.state.paused) return;
      const prev = state;
      state = stepWalk(state, move, ctx.rig.state.yawDeg, dtS, readCfg(ctx.cfg.walk));
      if (state.moving && (!prev.moving || prev.running !== state.running)) gaitClip(ctx, state);
      if (!state.moving && prev.moving) setClip(ctx, ctx.state.clipIndex);
      ctx.actor.root.position.set(state.x, 0, state.z);
      ctx.actor.root.rotation.y = state.headingDeg * DEG;
      ctx.rig.setTarget(state.x, state.z);
    },
  };
}
