/** พื้นหลังฟ้าไล่สี (บนจอ : ขอบฟ้าด้านล่าง → ฟ้าด้านบน) ด้วยพื้นผิวแคนวาสเล็ก ๆ ที่ถูกยืดเต็มจอ */
import { CanvasTexture, SRGBColorSpace } from 'three';
import { SKY_TEXTURE_PX } from '../constants/app';

export function makeSkyTexture(topColor: string, horizonColor: string): CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = SKY_TEXTURE_PX.w;
  canvas.height = SKY_TEXTURE_PX.h;
  const ctx = canvas.getContext('2d')!;
  const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
  grad.addColorStop(0, topColor);
  grad.addColorStop(1, horizonColor);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const tex = new CanvasTexture(canvas);
  tex.colorSpace = SRGBColorSpace;
  return tex;
}
