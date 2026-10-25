/** โหมดจอเล็ก/จอสัมผัส (compact) : เปิดเมื่อตัวชี้หลักเป็นนิ้ว หรือจอกว้างไม่เกินค่าใน config `layout.compactMaxWidthPx`
 *  เป็นที่เดียวที่ตัดสินโหมดนี้ · CSS ใช้ class `is-compact` บน body · ค่า barFrac = สัดส่วนความสูงจอที่แถบปุ่มบัง (ให้กล้องเผื่อที่) */
import { COARSE_POINTER_QUERY } from '../constants/app';
import { CSS } from '../constants/dom';
import type { CatConfig } from '../data/config';

export interface LayoutState {
  compact: boolean;
  /** 0 เมื่อไม่ใช่ compact · ไม่เกิน config `layout.insetMaxFrac` */
  barFrac: number;
}

export interface LayoutMode {
  /** ตัดสินโหมดใหม่ + ตั้ง class + วัดแถบปุ่ม (เรียกตอนปรับขนาดจอ) */
  refresh(): LayoutState;
}

export function createLayoutMode(cfg: CatConfig, bar: HTMLElement): LayoutMode {
  const coarse = window.matchMedia?.(COARSE_POINTER_QUERY);
  return {
    refresh() {
      const compact = (coarse?.matches ?? false) || window.innerWidth <= cfg.layout.compactMaxWidthPx.value;
      document.body.classList.toggle(CSS.compact, compact);
      if (!compact) return { compact, barFrac: 0 };
      const frac = bar.getBoundingClientRect().height / Math.max(window.innerHeight, 1);
      return { compact, barFrac: Math.min(frac, cfg.layout.insetMaxFrac.value) };
    },
  };
}
