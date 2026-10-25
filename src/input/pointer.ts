/** เมาส์ + สัมผัส บน canvas ด้วย Pointer Events ชุดเดียว :
 *  ลากซ้าย/นิ้วเดียว = หมุนกล้อง · ล้อ = ซูม · สองนิ้วถ่าง/หุบ = ซูม
 *  (แตะปุ่มท่าในแถบเป็นของ ui/clipBar เพราะเป็นปุ่ม DOM ปกติ) */
import { clamp } from '../logic/orbit';
import { POINTER_MAP } from './inputMap';
import type { InputSink } from './types';

interface Pos { x: number; y: number }

export function bindPointer(canvas: HTMLCanvasElement, sink: InputSink): () => void {
  const pointers = new Map<number, Pos>();
  let pinchDist = 0;

  const measure = (): number => {
    const [a, b] = [...pointers.values()];
    return Math.hypot(a.x - b.x, a.y - b.y);
  };

  const onDown = (e: PointerEvent): void => {
    if (e.pointerType === 'mouse' && e.button !== POINTER_MAP.dragButton) return;
    canvas.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    pinchDist = pointers.size === 2 ? measure() : 0;
  };

  const onMove = (e: PointerEvent): void => {
    const prev = pointers.get(e.pointerId);
    if (!prev) return;
    const next = { x: e.clientX, y: e.clientY };
    pointers.set(e.pointerId, next);
    if (pointers.size === 1) {
      sink.dragPx(next.x - prev.x, next.y - prev.y);
      return;
    }
    if (pointers.size !== 2) return;
    const dist = measure();
    if (pinchDist > 0 && dist > 0) sink.pinch(dist / pinchDist);
    pinchDist = dist;
  };

  const onUp = (e: PointerEvent): void => {
    pointers.delete(e.pointerId);
    pinchDist = pointers.size === 2 ? measure() : 0;
  };

  const onWheel = (e: WheelEvent): void => {
    e.preventDefault();
    sink.zoomSteps(clamp(e.deltaY / POINTER_MAP.wheelNotchPx, -POINTER_MAP.wheelMaxSteps, POINTER_MAP.wheelMaxSteps));
  };

  canvas.addEventListener('pointerdown', onDown);
  canvas.addEventListener('pointermove', onMove);
  canvas.addEventListener('pointerup', onUp);
  canvas.addEventListener('pointercancel', onUp);
  canvas.addEventListener('wheel', onWheel, { passive: false });
  return () => {
    canvas.removeEventListener('pointerdown', onDown);
    canvas.removeEventListener('pointermove', onMove);
    canvas.removeEventListener('pointerup', onUp);
    canvas.removeEventListener('pointercancel', onUp);
    canvas.removeEventListener('wheel', onWheel);
  };
}
