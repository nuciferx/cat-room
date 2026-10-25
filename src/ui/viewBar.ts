/** แถบแบบแมว : 3D · 2.5D · ปุ่มลัด V สลับ */
import { VIEW_NAMES } from '../constants/views';
import type { Translate } from '../data/locale';
import { createChoiceBar, type ChoiceBar } from './choiceBar';

export type ViewBar = ChoiceBar;

export function createViewBar(host: HTMLElement, t: Translate, onSelect: (index: number) => void): ViewBar {
  return createChoiceBar(host, t('ui.viewBar'), VIEW_NAMES.map((n) => t(`view.${n}`)), onSelect);
}
