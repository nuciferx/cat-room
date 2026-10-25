/** คีย์บอร์ด → InputSink ตามตารางใน inputMap · ไม่ทำงานตอนพิมพ์ในช่องกรอก (เช่น ช่องตัวเลขของแผง F1) */
import { digitToIndex } from '../logic/clipCycle';
import { CLIP_NAMES } from '../constants/clips';
import { DIGIT_KEYS, KEYS_PREVENT_DEFAULT, KEY_ACTIONS, MOVE_KEYS, RUN_KEYS } from './inputMap';
import type { InputSink } from './types';

function isTyping(target: EventTarget | null): boolean {
  return target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement;
}

export function bindKeyboard(sink: InputSink): () => void {
  const onKeyDown = (e: KeyboardEvent): void => {
    if (e.ctrlKey || e.altKey || e.metaKey || isTyping(e.target)) return;
    if (KEYS_PREVENT_DEFAULT.has(e.code)) e.preventDefault();
    if (e.repeat) return;
    const action = KEY_ACTIONS[e.code];
    if (action) {
      sink.action(action);
      return;
    }
    const digit = DIGIT_KEYS[e.code];
    if (digit === undefined) return;
    const index = digitToIndex(digit, CLIP_NAMES.length);
    if (index >= 0) sink.selectClip(index);
  };
  window.addEventListener('keydown', onKeyDown);
  return () => window.removeEventListener('keydown', onKeyDown);
}

export interface HeldKeys {
  /** [ขวา, หน้า, วิ่ง] จากปุ่มที่กดค้างอยู่ */
  axis(): [number, number, boolean];
  dispose(): void;
}

/** จำปุ่มเดิน/วิ่งที่กดค้าง (ปล่อยเมื่อหน้าต่างเสียโฟกัส กันเดินค้าง) */
export function bindHeldKeys(): HeldKeys {
  const held = new Set<string>();
  const down = (e: KeyboardEvent): void => {
    if (isTyping(e.target)) return;
    if (MOVE_KEYS[e.code] || RUN_KEYS.has(e.code)) held.add(e.code);
  };
  const up = (e: KeyboardEvent): void => {
    held.delete(e.code);
  };
  const clear = (): void => held.clear();
  window.addEventListener('keydown', down);
  window.addEventListener('keyup', up);
  window.addEventListener('blur', clear);
  return {
    axis() {
      let x = 0;
      let y = 0;
      for (const code of held) {
        const v = MOVE_KEYS[code];
        if (v) {
          x += v[0];
          y += v[1];
        }
      }
      return [x, y, [...held].some((c) => RUN_KEYS.has(c))];
    },
    dispose() {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('blur', clear);
    },
  };
}
