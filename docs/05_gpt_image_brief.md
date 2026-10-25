# คำสั่งภาพ GPT สำหรับปั้นแมว

เจ้าของงานเป็นคนสั่งภาพ (ส่งข้อความออกนอกเครื่อง) · ภาพทั้งหมดเก็บ `F:/ai3d/in/cat/new/` ไม่เข้า git · เหตุผลอยู่ใน `docs/02_feasibility.md` และผลปั้นรอบแรกใน `log.md` 2026-10-24

## ปั้นรอบแรกสอนอะไร (เหตุผลของข้อกำหนด)

- ท่าขาต่างกันทุกมุม → Hunyuan ยังปั้นได้ แต่ขาไม่แน่นอน → **ท่ายืนนิ่งเหมือนกันทุกภาพ**
- หูแต่ละภาพอยู่คนละที่ → สีชมพูหูเลอะหัวและหลัง → **หูตำแหน่งเดียวกัน ด้านในหูชมพูเห็นชัด ขอบหูครีม**
- ภาพข้างฉายตาลงแก้ม → **ต้องมีภาพหน้าตรงใกล้ ๆ แยก** ใช้ทำหน้าอย่างเดียว
- ภาพข้างเดิมกล้องสูงเฉียงเล็กน้อย → **กล้องระดับสายตาแมว ตรงข้าง 90°**
- หลังหัวและหลังตัวไม่มีภาพมองลง → **เพิ่มภาพมองจากบน** (`project_views.py` ใช้ `top.png` ได้)
- มีวงคล้ายปลอกที่โคนหาง → ระบุ **ไม่มีปลอกคอ ไม่มีโบว์ ไม่มีของตกแต่ง**

## ภาพที่ต้องได้

| ลำดับ | ไฟล์ | มุม | จำเป็น |
|---|---|---|---|
| 1 | `front.png` | ตรงหน้า | ✅ |
| 2 | `side_head_left.png` | ข้างตรง 90° หัวไปทางซ้ายของรูป | ✅ |
| 3 | `back.png` | ตรงหลัง | ✅ |
| 4 | `side_head_right.png` | ข้างตรง 90° หัวไปทางขวาของรูป | ✅ |
| 5 | `top.png` | มองลงตรง ๆ จากบน หัวอยู่ล่างของรูป | ✅ |
| 6 | `face.png` | หน้าตรงใกล้ เต็มกรอบ ตาครึ่งปิดหน้าบึ้ง | ✅ |
| 7 | `face_eyes_closed.png` | เหมือนข้อ 6 แต่หลับตา | ถ้ามีท่าหลับ/ถูกลูบ |
| 8 | `face_eyes_open.png` | เหมือนข้อ 6 แต่ตาเปิดกว้าง (ตกใจ/สนใจ) | ไม่จำเป็นตอนนี้ |

ชื่อไฟล์ข้าง (2, 4) ตั้งตามทิศหัว ไม่ใช้ left/right กันสับสน (session หลักแปลงเป็นชื่อของสคริปต์เอง)

## ข้อความตั้งต้น (ส่งครั้งแรก พร้อมแนบภาพอ้างอิง 8 ทิศ)

```
I will ask you for several images of the SAME cat for 3D modeling. Keep the cat identical in every image.
Cat: the fluffy cream Persian cat from the attached reference, soft clay-like 3D render style,
grumpy half-closed amber eyes, small pink nose, ears with clearly pink inner ear and cream fur rim,
huge plume tail curving up and slightly forward over the back.
Pose (every body image): neutral standing, all four paws planted flat, legs straight and clearly
separated with a visible gap under the belly, mouth closed, head level looking straight ahead,
tail in the same shape every time.
No collar, no bow, no accessories. Plain flat light-grey background, no floor, no cast shadow,
no text, no labels, no border. 1024x1024, one view per image, whole cat in frame with small margin,
same scale in every image, orthographic-like camera (no perspective distortion).
```

## ข้อความต่อภาพ (ส่งทีละข้อในบทสนทนาเดียวกัน)

1. `Image 1: exact FRONT view, camera at the cat's eye level.`
2. `Image 2: exact SIDE view at 90 degrees, head pointing to the LEFT of the image, camera at the cat's eye level.`
3. `Image 3: exact BACK view, camera at the cat's eye level.`
4. `Image 4: exact SIDE view at 90 degrees, head pointing to the RIGHT of the image, camera at the cat's eye level.`
5. `Image 5: exact TOP view looking straight down from above, head toward the BOTTOM of the image.`
6. `Image 6: close-up of the face only, exact front view, face fills the frame, same grumpy half-closed eyes.`
7. `Image 7: same as image 6, identical framing, but eyes fully closed (content, relaxed).`

## ได้ภาพแล้วตรวจก่อนส่ง

- ขาทั้ง 4 อยู่ตำแหน่งเดียวกันทุกภาพตัว · หางรูปเดียวกัน · หูตำแหน่งเดียวกัน
- ภาพ 2 หัวไปซ้าย · ภาพ 4 หัวไปขวา
- ไม่มีเงาบนพื้น ไม่มีตัวอักษร
- ภาพไหนผิด สั่งใหม่เฉพาะภาพนั้น ("redo image N, keep everything else the same")
