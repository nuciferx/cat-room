/** ป้ายช่วยเหลือปุ่มลัด : แถวข้อความมาจาก locales `help.rows` · ซ่อน/แสดงด้วย H */
import { CSS } from '../constants/dom';
import type { Locale } from '../data/locale';

interface HelpRow { keys: string; text: string }

export interface HelpPanel {
  setVisible(on: boolean): void;
}

export function createHelpPanel(host: HTMLElement, locale: Locale): HelpPanel {
  const title = document.createElement('strong');
  title.textContent = locale.t('help.title');
  host.appendChild(title);
  for (const row of locale.raw<HelpRow[]>('help.rows')) {
    const line = document.createElement('div');
    line.className = CSS.helpRow;
    const keys = document.createElement('kbd');
    keys.textContent = row.keys;
    const text = document.createElement('span');
    text.textContent = row.text;
    line.append(keys, text);
    host.appendChild(line);
  }
  return { setVisible: (on) => host.classList.toggle(CSS.hidden, !on) };
}
