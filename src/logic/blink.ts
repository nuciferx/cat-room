/** จังหวะกระพริบตา (ชั้นตรรกะ : ไม่รู้จัก three.js/DOM) · rand ส่งเข้ามาเพื่อทดสอบได้ */

export interface BlinkCfg {
  intervalMinS: number;
  intervalMaxS: number;
  closedS: number;
  doubleChance: number;
  /** ระยะลืมตาระหว่างกระพริบสองครั้งติด (เท่าของ closedS) */
  doubleGapRatio: number;
}

export interface BlinkState {
  /** วินาทีที่เหลือก่อนกระพริบครั้งถัดไป (ตอนลืมตา) */
  waitS: number;
  /** วินาทีที่เหลือของการหลับตา (0 = ลืมตาอยู่) */
  closedLeftS: number;
  /** การหลับตารอบนี้ต้องตามด้วยกระพริบซ้ำติดกันไหม */
  repeatPending: boolean;
  /** รอบนี้คือครั้งที่สองของการกระพริบสองครั้ง (ห้ามซ้ำอีก) */
  isSecond: boolean;
}

export interface BlinkStep {
  state: BlinkState;
  closed: boolean;
}

function randomWaitS(cfg: BlinkCfg, rand: () => number): number {
  const lo = Math.min(cfg.intervalMinS, cfg.intervalMaxS);
  const hi = Math.max(cfg.intervalMinS, cfg.intervalMaxS);
  return lo + (hi - lo) * rand();
}

export function createBlinkState(cfg: BlinkCfg, rand: () => number): BlinkState {
  return { waitS: randomWaitS(cfg, rand), closedLeftS: 0, repeatPending: false, isSecond: false };
}

/** เดินเวลา dtS วินาที · คืน state ใหม่ (ไม่แก้ของเดิม) กับสถานะหลับตา ณ ตอนนี้ */
export function stepBlink(state: BlinkState, dtS: number, cfg: BlinkCfg, rand: () => number): BlinkStep {
  if (state.closedLeftS > 0) {
    const left = state.closedLeftS - dtS;
    if (left > 0) return { state: { ...state, closedLeftS: left }, closed: true };
    const again = state.repeatPending;
    const wait = again ? cfg.closedS * cfg.doubleGapRatio : randomWaitS(cfg, rand);
    return { state: { waitS: wait, closedLeftS: 0, repeatPending: false, isSecond: again }, closed: false };
  }
  const wait = state.waitS - dtS;
  if (wait > 0) return { state: { ...state, waitS: wait }, closed: false };
  const repeat = !state.isSecond && rand() < cfg.doubleChance;
  return { state: { waitS: 0, closedLeftS: cfg.closedS, repeatPending: repeat, isSecond: state.isSecond }, closed: true };
}
