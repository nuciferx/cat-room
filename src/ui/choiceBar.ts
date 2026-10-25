/** แถบปุ่มเลือกหนึ่งอย่าง (หน้า · แบบ 3D/2.5D) : ป้ายมาจากผู้เรียก (แปลแล้ว) */
import { CSS } from '../constants/dom';

export interface ChoiceBar {
  setActive(index: number): void;
  /** เปลี่ยนชุดปุ่มทั้งแถบ (เช่น หน้าของแมวตัวที่แสดงอยู่) */
  setLabels(labels: string[]): void;
}

function makeButtons(host: HTMLElement, labels: string[], onSelect: (index: number) => void): HTMLButtonElement[] {
  host.replaceChildren();
  return labels.map((label, index) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = CSS.clipButton;
    btn.textContent = label;
    btn.tabIndex = -1;
    btn.addEventListener('click', () => {
      onSelect(index);
      btn.blur(); // กัน Space ไปกดปุ่มที่ค้างโฟกัสซ้ำกับปุ่มลัดหยุด/เล่น
    });
    host.appendChild(btn);
    return btn;
  });
}

export function createChoiceBar(host: HTMLElement, ariaLabel: string, labels: string[], onSelect: (index: number) => void): ChoiceBar {
  host.setAttribute('aria-label', ariaLabel);
  let buttons = makeButtons(host, labels, onSelect);
  return {
    setActive(active) {
      buttons.forEach((b, i) => b.classList.toggle(CSS.active, i === active));
    },
    setLabels(next) {
      buttons = makeButtons(host, next, onSelect);
    },
  };
}
