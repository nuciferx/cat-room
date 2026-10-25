/** สถานะห้องโชว์ที่ไม่เกี่ยวกับ three.js/DOM : ท่าที่เล่น หน้าที่ใช้ (แยกต่อโมเดล) หยุดอยู่ไหม ตาราง/แผง/ป้ายช่วยเหลือเปิดอยู่ไหม */
import type { ModelViewName } from '../constants/views';
import { stepIndex } from './clipCycle';

export interface ShowroomState {
  clipIndex: number;
  /** ลำดับหน้าในชุดหน้าของแต่ละโมเดล (แต่ละตัวจำหน้าของตัวเอง) */
  faceIndex: Record<ModelViewName, number>;
  viewIndex: number;
  paused: boolean;
  gridOn: boolean;
  panelOpen: boolean;
  helpOn: boolean;
  /** เลขคำขอสลับแบบล่าสุด (สลับแบบที่ต้องโหลดภาพ : คำขอเก่าที่เสร็จทีหลังถูกทิ้ง) */
  viewRequest: number;
}

export function createState(clipIndex: number, viewIndex: number, gridOn: boolean, helpOn: boolean): ShowroomState {
  return { clipIndex, faceIndex: { '3d': 0, mui3d2: 0, som3d: 0 }, viewIndex, paused: false, gridOn, panelOpen: false, helpOn, viewRequest: 0 };
}

export function stepClip(s: ShowroomState, dir: number, count: number): void {
  s.clipIndex = stepIndex(s.clipIndex, dir, count);
}

/** ลำดับหน้าถัดไปของโมเดล (วนกลับหน้าแรก) · ไม่เปลี่ยน state เอง : ผู้เรียกตั้งเมื่อสลับภาพได้จริง */
export function stepFace(s: ShowroomState, model: ModelViewName, count: number): number {
  return stepIndex(s.faceIndex[model], 1, count);
}

/** ลำดับแบบแมวถัดไป (วนกลับ) · ไม่เปลี่ยน state เอง : ผู้เรียกตั้งเมื่อสลับได้จริง */
export function stepView(s: ShowroomState, count: number): number {
  return stepIndex(s.viewIndex, 1, count);
}
