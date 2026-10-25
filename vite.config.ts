import { defineConfig } from 'vitest/config';

/** หน้าที่ build : ตอนนี้มีห้องโชว์แมวหน้าเดียว · เพิ่มหน้าใหม่ (เช่น index.html เกม) ที่นี่ที่เดียว */
const PAGES = { cat: 'cat.html' };

export default defineConfig({
  // ไฟล์ asset อ้างแบบสัมพัทธ์ → เปิดได้ทั้ง dev (/) และ GitHub Pages (/cat-room/)
  base: './',
  // ไม่เฝ้า shots/ (ภาพถ่ายจำนวนมาก ทำ dev server กินซีพียู/หน่วยความจำ)
  server: { port: 5173, strictPort: true, watch: { ignored: ['**/shots/**'] } },
  build: { rollupOptions: { input: PAGES } },
  test: { include: ['tests/**/*.test.ts'] },
});
