# ทะเบียน asset — ที่มาและสิทธิ์

กฎ : ลงทะเบียนก่อนใช้ทุกชิ้น · ภาพ GPT ภาพอ้างอิงเว็บ ไฟล์ต้นทาง Meshy/Hunyuan **ไม่เข้า git**

## ภาพอ้างอิง (ไม่เข้า git)

| ไฟล์ | ที่มา | สิทธิ์ | วันที่ |
|---|---|---|---|
| `F:/ai3d/in/cat/ref_sheet_8dir.webp` (1672×941 · แมว 8 ทิศ S SW W NW N NE E SE) | เจ้าของงานส่งในบทสนทนา (ภาพสร้างด้วย AI · ยังไม่ได้ถามว่าเครื่องมือไหน) | ใช้ดูทรงและสีเท่านั้น | 2026-10-24 |
| `F:/ai3d/in/cat/new/*.webp` (หน้า หลัง ข้าง×2 บน หน้าใกล้ลืม/หลับตา · 1254 px) | เจ้าของงานสั่ง GPT ตาม `docs/05_gpt_image_brief.md` | ใช้ปั้นทรงและฉายสี · ไม่เข้า git | 2026-10-24 |
| `F:/ai3d/in/cat/new/emotions/face_relaxed.webp` (หน้าคลายเครียด ตาหลับยิ้ม · 1254 px) | เจ้าของงานส่งภาพ GPT ในแชต (แก้จาก `face.webp`) | ภาพหน้าอารมณ์ · ไม่เข้า git · กรอบตรงต้นฉบับ (ต่างเฉพาะตา คิ้ว ปาก) · อบเป็น `public/assets/models/cat/cat_relaxed.jpg` | 2026-10-24 |
| `F:/ai3d/in/cat/motion/clip_01.mp4` (1920×1080 · 23.976 fps · 34.7 วิ · แมวลายสลิดจริงเดินบนสนามหญ้า กล้องแพนตาม) | เจ้าของงานส่งในบทสนทนา · **ยังไม่รู้ที่มา/สิทธิ์** | ใช้ดูจังหวะเดินเท่านั้น · ไม่เข้า git | 2026-10-24 |
| `F:/ai3d/in/cat/motion/clip_02.mp4` (1280×720 · 30 fps · 7.5 วิ · แมวเบงกอลเดินอยู่กับที่บนฉากเขียว มุมข้างเฉียงหน้า) | เจ้าของงานส่งในบทสนทนา (ชื่อไฟล์เดิม `318833_tiny.mp4` · **ยังไม่รู้ที่มา/สิทธิ์**) | ใช้ดูจังหวะเดินเท่านั้น · ไม่เข้า git | 2026-10-24 |
| `F:/ai3d/in/cat/motion/clip_03.mp4` (2560×1440 · 30 fps · 14.7 วิ · เสือโคร่ง (น่าจะ CG) เดินเข้า ยืนมอง แล้วหมอบลงนอน ฉากเขียว) | เจ้าของงานส่งในบทสนทนา (ชื่อไฟล์เดิม `318694_medium.mp4` · **ยังไม่รู้ที่มา/สิทธิ์**) | ใช้ดูท่านอนลงเท่านั้น · ไม่เข้า git | 2026-10-24 |
| `F:/ai3d/in/cat/sprite_sheet_8x8.webp` (1254×1254 · 8 ทิศ × 8 เฟรมเดิน) | เจ้าของงานส่งในบทสนทนา (ภาพ AI) | ใช้อ้างอิงท่าเดินเท่านั้น | 2026-10-24 |

## โมเดล

| ไฟล์ | ที่มา | สิทธิ์ | วันที่ |
|---|---|---|---|
| `public/assets/models/som/som.glb` + `som_blink.jpg` `som_{smile,happy,sad,wink,sleepy}.jpg` (เจ้าส้ม 9.8k สามเหลี่ยม · 11 คลิป · ภาพหน้า 6 แบบ) | `F:/ai3d/in/cat/som/ref3d_sheet.png` (ยืน 4 ทิศ + ช่องหน้า 6 แบบ ตัดด้วย `sheet_crop.py` → `F:/ai3d/in/cat/som/faces/` ไม่เข้า git) → Hunyuan3D 2mv → `mesh_dewhisker` `project_views` `cat_touchup --cfg som_touchup.json` → `build_quad_meshy.py -- som` | เหมือน cat.glb (Hunyuan 2.0 Community) · ภาพต้นทาง AI ของเจ้าของงาน | 2026-10-25 |
| `public/assets/models/cat/cat.glb` (10k สามเหลี่ยม · 10 คลิป) | ภาพ GPT ของเจ้าของงาน → Hunyuan3D 2mv ในเครื่อง → `views_depink` `project_views` `cat_touchup --atlas` → `build_quad_meshy.py -- cat` · ท่าสร้างด้วยสคริปต์ | Meshy แผนเสียเงิน : ผู้ใช้เป็นเจ้าของ · Hunyuan 2.0 Community : ห้าม EU/UK/เกาหลีใต้ ผู้ใช้ >1 ล้าน/เดือนต้องขอ Tencent · **รอเจ้าของงานตอบว่าขายหรือไม่** | — |
| `public/assets/models/cat2/cat2.glb` + `cat2_blink.jpg` `cat2_relaxed.jpg` (มุ่ยกระดูกใหม่ 40 ชิ้น · 11 คลิป · ท่านั่งใหม่) | ต้นทางเดียวกับ cat.glb → `build_quad_meshy.py -- cat2` (`quad_meshy_cat2.json`) · ท่านั่งดูมุมข้อต่อจาก `F:/ai3d/in/cat/poses/som/sit.png` (ภาพอ้างอิงท่า ไม่เข้า git · ไม่ได้ใช้ภาพในโมเดล) | ตามสิทธิ์ของ cat.glb | 2026-10-25 |

## สคริปต์ที่ยกมาจากโปรเจกต์อื่นของเจ้าของงาน

| ไฟล์ใน bb | ต้นทาง | commit ต้นทาง | วันที่ |
|---|---|---|---|
| `tools/ai3d/hunyuan_shape.py` `views_cutout.py` `project_views.py` `atlas_pack.py` (คัดลอกตรง ไม่แก้) | `F:/game/pp3/tools/ai3d/` | 7bd56e6 | 2026-10-24 |
| `tools/blender/` 27 ไฟล์สายสี่ขา (`build_quad_meshy.py` `quad_meshy_*` `beasts_*` `birds_*` `din_new_*` `glb_io` `gardener_img` `prep_din_mesh(.json)`) + `quad_meshy_check.mjs` · แก้ `quad_meshy_weights._tail` (aboveY) `quad_meshy_weights._torso` (upperarmMaxY/Z) `_ear_mask` (fromBones/maxDzM/minY) `compute(piece)` · `quad_meshy_bake.source_material` (ไม่มี normal) `nearCage` `_fill_hidden` `bake_alts` · ไฟล์ใหม่ของ bb : `quad_meshy_altmask.py` `quad_meshy_tailsplit.py` | `F:/game/pp3/tools/blender/` | 7bd56e6 | 2026-10-24 |
| `public/assets/sprites/cat/` (ภาพ 2.5D มุ่ย ยืนพัก/เดิน 8 ทิศ) | เรนเดอร์จาก `cat.glb` (`sprite_render.py`) → Krita (`tools/krita/mui_sprites.py`) | ตามสิทธิ์ของ cat.glb | 2026-10-25 |
| Krita 5.3.4.1 portable (`F:/tools/krita/` ไม่เข้า git) | https://krita.org/en/download/ | GPL · เครื่องมือ | 2026-10-25 |
| `F:/ai3d/in/cat/som/ref_8dir.webp` (เจ้าส้ม 8 ทิศ 1448×1086 ไม่เข้า git) → `public/assets/sprites/som/` | เจ้าของงานส่งในแชต (ภาพสร้างด้วย AI · ยังไม่ได้ถามเครื่องมือ) | ภาพตัวละครในห้องโชว์ | 2026-10-25 |
| `F:/ai3d/in/cat/som/walk_8x4.webp` (เจ้าส้มเดิน 8 ทิศ × 4 เฟรม 1774×887 ไม่เข้า git) → `public/assets/sprites/som/` | เจ้าของงานส่งในแชต (ภาพสร้างด้วย AI) | ภาพตัวละครในห้องโชว์ (แทนชุด ref_8dir) | 2026-10-25 |
| `F:/ai3d/in/cat/dam/walk_8x16.webp` (เจ้าดำเดิน 8 ทิศ × 16 เฟรม 1774×887 ไม่เข้า git) → `public/assets/sprites/dam/` | เจ้าของงานส่งในแชต (ภาพสร้างด้วย AI) | ภาพตัวละครในห้องโชว์ | 2026-10-25 |
| `F:/ai3d/in/cat/som/ref3d_sheet.png` (แผ่นอ้างอิงเจ้าส้มลายเรนเดอร์ 3D : ยืน 8 ทิศ + หน้า 6 อารมณ์ 1536×1024 ไม่เข้า git) → Hunyuan3D 2mv → `public/assets/models/som/som.glb` | เจ้าของงานส่ง (ภาพสร้างด้วย AI · ไฟล์ Downloads `แผ่นอ้างอิงแมวส้มแสนน่ารัก.png`) | โมเดลตัวละครในห้องโชว์ | 2026-10-25 |
| `F:/ai3d/in/cat/som/walk3d_8x4.webp` · `stand2d_8dir.png` (ภาพเดินลายเรนเดอร์ 3D / ภาพยืน 8 ทิศลายวาด ไม่เข้า git) | เจ้าของงานส่งในแชต (ภาพสร้างด้วย AI) | ทดลอง 2.5D `public/assets/sprites/som3d/` (ยังไม่ใช้) / สำรอง | 2026-10-25 |
