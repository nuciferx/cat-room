/** อ่านขนาดภาพ PNG จากหัวไฟล์ (IHDR) โดยไม่ต้องถอดรหัสภาพ · ไม่ใช่ PNG → null */
const SIGNATURE = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
const WIDTH_OFFSET = 16;
const HEADER_BYTES = 24;

/** จำนวนไบต์หัวไฟล์ที่พอให้อ่านขนาด */
export const PNG_HEADER_BYTES = HEADER_BYTES;

export interface PngSize { width: number; height: number }

export function readPngSize(bytes: Uint8Array): PngSize | null {
  if (bytes.length < HEADER_BYTES) return null;
  if (!SIGNATURE.every((b, i) => bytes[i] === b)) return null;
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  return { width: view.getUint32(WIDTH_OFFSET), height: view.getUint32(WIDTH_OFFSET + 4) };
}
