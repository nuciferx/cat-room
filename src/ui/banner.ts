/** แถบข้อความบนจอ : ข้อความ error ค้างถาวร (ไม่ส่ง seconds) หรือข้อความแจ้งสั้น ๆ หายเองเมื่อครบ seconds */
import { CSS } from '../constants/dom';

export interface Banner {
  show(text: string, seconds?: number): void;
  hide(): void;
}

export function createBanner(el: HTMLElement): Banner {
  let timer = 0;
  return {
    show(text, seconds) {
      window.clearTimeout(timer);
      el.textContent = text;
      el.classList.remove(CSS.hidden);
      if (seconds === undefined) return;
      timer = window.setTimeout(() => el.classList.add(CSS.hidden), seconds * 1000);
    },
    hide() {
      window.clearTimeout(timer);
      el.classList.add(CSS.hidden);
    },
  };
}
