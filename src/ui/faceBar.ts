/** แถบหน้า : ปุ่มเลือกหน้าของแมวตัวที่แสดงอยู่ (ชุดหน้าต่อตัว : constants/faces FACE_SETS) · ปุ่มลัด F วนหน้าถัดไป */
import type { FaceName } from '../constants/faces';
import type { Translate } from '../data/locale';
import { createChoiceBar, type ChoiceBar } from './choiceBar';

export interface FaceBar extends ChoiceBar {
  /** แสดงชุดหน้าใหม่ (สลับแมว) */
  setFaces(names: readonly FaceName[]): void;
}

export function createFaceBar(host: HTMLElement, t: Translate, names: readonly FaceName[], onSelect: (index: number) => void): FaceBar {
  const label = (list: readonly FaceName[]): string[] => list.map((n) => t(`face.${n}`));
  const bar = createChoiceBar(host, t('ui.faceBar'), label(names), onSelect);
  return { ...bar, setFaces: (list) => bar.setLabels(label(list)) };
}
