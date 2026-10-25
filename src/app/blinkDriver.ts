/** เดินจังหวะกระพริบทุกเฟรมแล้วสั่ง actor · หยุดเล่น = ลืมตาค้าง ไม่เดินเวลา */
import type { CatConfig } from '../data/config';
import { createBlinkState, stepBlink, type BlinkCfg, type BlinkState } from '../logic/blink';
import type { CatActor } from '../render/catActor';

export interface BlinkDriver {
  update(dtS: number, paused: boolean): void;
}

function readCfg(cfg: CatConfig['blink']): BlinkCfg {
  return {
    intervalMinS: cfg.intervalMinS.value,
    intervalMaxS: cfg.intervalMaxS.value,
    closedS: cfg.closedS.value,
    doubleChance: cfg.doubleChance.value,
    doubleGapRatio: cfg.doubleGapRatio.value,
  };
}

export function createBlinkDriver(cfg: CatConfig, actor: CatActor, rand: () => number = Math.random): BlinkDriver {
  let state: BlinkState = createBlinkState(readCfg(cfg.blink), rand);
  return {
    update(dtS, paused) {
      if (paused) {
        actor.setEyesClosed(false);
        return;
      }
      const step = stepBlink(state, dtS, readCfg(cfg.blink), rand);
      state = step.state;
      actor.setEyesClosed(step.closed);
    },
  };
}
