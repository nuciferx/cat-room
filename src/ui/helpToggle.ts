/** ปุ่มเล็กเปิด/ปิดป้ายช่วยเหลือบนจอสัมผัส (ไม่มีคีย์ H) · ผูก event ที่นี่ ไม่ใช้ onclick ใน HTML */
import type { Translate } from '../data/locale';

export function bindHelpToggle(btn: HTMLButtonElement, t: Translate, onToggle: () => void): void {
  btn.textContent = t('ui.helpToggle');
  btn.setAttribute('aria-label', t('ui.helpToggleAria'));
  btn.addEventListener('click', () => {
    onToggle();
    btn.blur();
  });
}
