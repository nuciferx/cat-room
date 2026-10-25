/** ปลายทางของ input ทุกแบบ (คีย์บอร์ด เมาส์ สัมผัส จอย) · ฝั่งแอปเป็นคน implement */
import type { Action } from '../constants/actions';

export interface InputSink {
  /** ปุ่มสั่งงาน (ท่าก่อน/ถัดไป หยุด/เล่น ตาราง ฯลฯ) */
  action(action: Action): void;
  /** เลือกท่าตามลำดับ (ปุ่มเลข) */
  selectClip(index: number): void;
  /** ลากหมุนกล้อง หน่วยพิกเซล */
  dragPx(dx: number, dy: number): void;
  /** ซูมเป็นก้าว (ล้อเมาส์) : บวก = ถอยออก */
  zoomSteps(steps: number): void;
  /** ซูมสองนิ้ว : ratio = ระยะนิ้วใหม่ ÷ เก่า */
  pinch(ratio: number): void;
  /** ไม้ขวาของจอย (-1..1 หลังตัดโซนตาย) · เรียกทุกเฟรมที่มีจอย */
  padRotate(x: number, y: number): void;
  /** ทิศเดิน (x = ขวา · y = หน้า · -1..1) และวิ่งไหม · เรียกทุกเฟรม (รวมคีย์บอร์ดกับจอยแล้ว) */
  move(x: number, y: number, run: boolean): void;
  /** ไกจอย LT/RT (-1..1) : บวก = ซูมเข้า · เรียกทุกเฟรมที่มีจอย */
  padZoom(axis: number): void;
}
