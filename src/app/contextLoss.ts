/** WebGL context หายกลางทาง (มือถือหน่วยความจำไม่พอ) : ขึ้นแถบเตือนแนะนำโหมดเบา · กลับมาได้เองก็ซ่อนแถบ */
import { LOW_QUALITY_HINT } from '../constants/app';
import type { Locale } from '../data/locale';
import type { Banner } from '../ui/banner';

export function watchContextLoss(canvas: HTMLCanvasElement, locale: Locale, banner: Banner): void {
  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault(); // ขอให้เบราว์เซอร์กู้ context ให้ถ้าทำได้
    banner.show(locale.t('error.contextLost', { hint: LOW_QUALITY_HINT }));
  });
  canvas.addEventListener('webglcontextrestored', () => banner.hide());
}
