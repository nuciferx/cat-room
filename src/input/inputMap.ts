/** input map กลางที่เดียว : action → ปุ่ม ของคีย์บอร์ด/เมาส์/จอย/สัมผัส
 *  จะเปลี่ยนปุ่มให้แก้ที่ไฟล์นี้ไฟล์เดียว (ป้ายช่วยเหลือบนจออยู่ใน locales `help.rows` ต้องแก้ตาม) */
import { ACTION, type Action } from '../constants/actions';

/** คีย์บอร์ด : KeyboardEvent.code → action */
export const KEY_ACTIONS: Readonly<Record<string, Action>> = {
  BracketLeft: ACTION.prevClip,
  ArrowLeft: ACTION.prevClip,
  BracketRight: ACTION.nextClip,
  ArrowRight: ACTION.nextClip,
  Space: ACTION.togglePlay,
  KeyG: ACTION.toggleGrid,
  F1: ACTION.togglePanel,
  KeyH: ACTION.toggleHelp,
  KeyR: ACTION.resetCamera,
  KeyF: ACTION.nextFace,
  KeyV: ACTION.nextView,
};

/** ปุ่มเดิน (กดค้าง) : KeyboardEvent.code → [ขวา, หน้า] · รวมกันได้ (เดินเฉียง) */
export const MOVE_KEYS: Readonly<Record<string, readonly [number, number]>> = {
  KeyW: [0, 1],
  KeyS: [0, -1],
  KeyA: [-1, 0],
  KeyD: [1, 0],
};

/** กดค้างพร้อมปุ่มเดิน = วิ่ง */
export const RUN_KEYS: ReadonlySet<string> = new Set(['ShiftLeft', 'ShiftRight']);

/** ปุ่มที่เบราว์เซอร์มีพฤติกรรมของตัวเอง ต้อง preventDefault (เลื่อนหน้า, ช่วยเหลือของเบราว์เซอร์) */
export const KEYS_PREVENT_DEFAULT: ReadonlySet<string> = new Set(['Space', 'F1', 'ArrowLeft', 'ArrowRight']);

/** ปุ่มเลข 1–9,0 : KeyboardEvent.code → เลขบนปุ่ม (ลำดับท่าคำนวณใน logic/clipCycle) */
export const DIGIT_KEYS: Readonly<Record<string, number>> = Object.fromEntries(
  Array.from({ length: 10 }, (_, d) => [`Digit${d}`, d]),
);

/** เมาส์ : ปุ่มที่ใช้ลากหมุนกล้อง (0 = ซ้าย) และขนาดล้อ 1 คลิก (พิกเซล deltaY) */
export const POINTER_MAP = { dragButton: 0, wheelNotchPx: 100, wheelMaxSteps: 3 } as const;

/** จอย (Gamepad API ผัง standard) */
export const PAD_MAP = {
  buttons: { 4: ACTION.prevClip, 5: ACTION.nextClip, 0: ACTION.togglePlay, 3: ACTION.nextFace, 2: ACTION.nextView } as Readonly<Record<number, Action>>,
  zoomOutButton: 6,
  zoomInButton: 7,
  stickX: 2,
  stickY: 3,
  /** คันโยกซ้าย = เดิน (แกน y ของจอยชี้ลงเป็นบวก) · กดค้างปุ่ม 1 (B) = วิ่ง */
  moveX: 0,
  moveY: 1,
  runButton: 1,
} as const;
