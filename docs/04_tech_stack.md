# stack — ยกจากโป่งไพร (pp3)

รุ่นตรงกับ `F:/game/pp3/package.json` ณ 2026-10-24 · ใช้รุ่นเดียวกันเพื่อยกโค้ด/ความรู้ข้ามได้ตรง ๆ

| ส่วน | ของ | รุ่น | ใช้ทำ |
|---|---|---|---|
| ภาษา | TypeScript | ^7.0.2 | ทั้งเกม · `tsc --noEmit` คือด่านตรวจของ agent |
| build/dev | Vite | ^8.3.2 | หลายหน้า (`index.html` เกม · `cat.html` ห้องโชว์แมว) |
| ภาพ 3D | three | ^0.186.1 (+ `@types/three` ^0.186.0) | ฉาก โหลด glb · `AnimationMixer` เล่นคลิปของ cat.glb |
| post-processing | postprocessing ^6.39.5 · n8ao ^2.0.1 | | ภาพนุ่มแบบดินปั้น (AO) · ปิดได้ใน `q=low` |
| แผงจูน | lil-gui ^0.21.0 | | แผง F1 สร้าง slider จาก min/max/step ใน config |
| เทสต์ | Vitest ^5.0.3 | | เทสต์ชั้นตรรกะ (ค่าแมว เวลา เซฟ) ที่ไม่รู้จัก three.js |
| ฟิสิกส์ | `@dimforge/rapier3d-compat` ^0.21.0 | | **ยังไม่ใส่** · ห้องเดียวใช้ชนแบบง่ายพอ · ใส่เมื่อมีของกลิ้ง/โยน |
| ปั้นโมเดล | Blender 5.2.1 (สคริปต์ล้วน) · Hunyuan3D 2.0/2mv (`F:/ai3d`) · Meshy (เว็บ ของเจ้าของงาน) | | `docs/03_cat_pipeline.md` |

## โครงโฟลเดอร์ (ตามโป่งไพร · สร้างเมื่อเริ่มเขียนโค้ด)

```
config/        ค่าทุกตัว (*.json มี min/max/step)
locales/       th.json en.json
public/assets/models/cat/   cat.glb (ผลที่เข้า git ได้ตามสิทธิ์)
src/data/      โหลด glb/config · เซฟ (localStorage)        ← ไม่รู้จัก UI
src/logic/     ค่าแมว เวลา การกระทำ พฤติกรรม                ← ไม่รู้จัก three.js และ DOM
src/render/    ฉาก กล้อง แมว แอนิเมชัน                       ← ไม่เรียก logic ตรงจาก event
src/ui/        HUD ปุ่ม แผงจูน
src/input/     input map กลาง (คีย์ เมาส์ จอย สัมผัส)
src/constants/ ชื่อคลิป ชื่อวัสดุ คีย์เซฟ
tests/         เทสต์ชั้น logic
tools/ai3d/ tools/blender/   สคริปต์ปั้นที่ยกจาก pp3
shots/tmp.temp/              ไฟล์ทำงาน (ไม่เข้า git)
```

## ยกโค้ดจาก pp3 ที่คุ้ม (คัดลอก ไม่แก้ต้นทาง)

- ห้องโชว์ภู (`src/showroom/phu/`) : กล้อง เดิน WASD/จอย จอยสัมผัส (`phuTouch.ts`) สลับสีตามชื่อวัสดุ
- input map กลาง · ระบบ `q=low|mid` · แผง F1 จาก config
- ไล่หาไฟล์จริงก่อนคัดลอก (ส่ง haiku ค้น) · จดที่มาในหัวไฟล์
