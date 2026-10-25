/** แถบท่า : ปุ่มกดเลือกท่า (ป้ายเลขปุ่มลัด + ชื่อท่า) และข้อความท่าปัจจุบัน/หยุดอยู่ */
import { CSS } from '../constants/dom';
import { CLIP_NAMES } from '../constants/clips';
import type { Translate } from '../data/locale';

export interface ClipBar {
  setActive(index: number): void;
  setPaused(paused: boolean): void;
}

export function createClipBar(host: HTMLElement, currentEl: HTMLElement, t: Translate, onSelect: (index: number) => void): ClipBar {
  const buttons = CLIP_NAMES.map((name, index) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = CSS.clipButton;
    // ป้ายเลข = ปุ่มลัด (ท่าที่ 10 ใช้ปุ่ม 0 · เกิน 10 ท่าไม่มีปุ่มลัด ใช้ลูกศร)
    const key = index < 10 ? `${(index + 1) % 10} ` : '';
    btn.textContent = `${key}${t(`clip.${name}`)}`;
    btn.tabIndex = -1;
    btn.addEventListener('click', () => {
      onSelect(index);
      btn.blur(); // กัน Space ไปกดปุ่มที่ค้างโฟกัสซ้ำกับปุ่มลัดหยุด/เล่น
    });
    host.appendChild(btn);
    return btn;
  });
  let active = 0;
  let paused = false;

  const refresh = (): void => {
    buttons.forEach((b, i) => b.classList.toggle(CSS.active, i === active));
    const pausedText = paused ? ` · ${t('ui.paused')}` : '';
    currentEl.textContent = `${t('ui.current')} : ${t(`clip.${CLIP_NAMES[active]}`)}${pausedText}`;
    currentEl.classList.toggle(CSS.paused, paused);
  };

  return {
    setActive(i) {
      active = i;
      refresh();
    },
    setPaused(p) {
      paused = p;
      refresh();
    },
  };
}
