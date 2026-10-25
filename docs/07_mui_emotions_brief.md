# อารมณ์ของมุ่ย — คำสั่งภาพหน้า GPT

มุ่ย = ชื่อแมว (เจ้าของงานตั้ง 2026-10-24) · ชุดอารมณ์จริงที่ใช้ในเกม **รอเจ้าของงานเลือก** (รายการข้างล่างเป็นข้อเสนอ)

## อารมณ์ทำได้ 2 ชั้น

| ชั้น | ทำอะไร | ทำด้วย |
|---|---|---|
| หน้า (ตา คิ้ว ปาก) | สลับภาพหน้า | ภาพ GPT กรอบเดียวกับ `face.webp` เป๊ะ → `cat_touchup.py` ฉายลงหัวด้วยจุดผูกเดิม (ตา/จมูกที่ปั้น) |
| ท่าตัว (หู หาง หัว) | หูพับ หางฟู/สะบัด หัวเอียง | กระดูกที่มีแล้ว (ear_L/R tail1–3 head) · ใส่เป็นคลิปด้วยสคริปต์ |

ข้อจำกัด : ปากที่ปั้นเป็นปากปิด · ภาพปากอ้า (ร้อง/ขู่) จะดูแบนบนหน้าปิด → ใช้ได้กับปากอ้าเล็ก ๆ · ขู่อ้ากว้างต้องปั้นขากรรไกรเพิ่ม (กระดูก jaw มีแล้วแต่เนื้อในปากไม่มี)

## วิธีสั่ง (สำคัญที่สุด : กรอบภาพต้องเท่าเดิมเป๊ะ)

- ใช้ **แก้ภาพ (edit)** ไม่ใช่สร้างใหม่ : แนบ `F:/ai3d/in/cat/new/face.webp` ทุกครั้ง
- สั่งทีละอารมณ์ในบทสนทนาเดียว · ไฟล์ละอารมณ์ ชื่อ `face_<อารมณ์>.png` 1254×1254 (หรือขนาดเดียวกับต้นฉบับ)
- เก็บ `F:/ai3d/in/cat/new/emotions/` (ไม่เข้า git)

### ข้อความแรก

```
Edit the attached image. This is the face of my cat character "Mui", used as a texture on a 3D model.
Keep EVERYTHING pixel-identical: same framing, same size, same position of the head, ears, nose and fur,
same background, same lighting, same colors, same clay-like 3D style.
ONLY change the eyes, eyelids, eyebrows (fur above the eyes) and the small mouth line to show the emotion I ask.
Eyes must stay in exactly the same place and the same size as in the original. Do not add any objects, text or effects.
```

### ข้อความต่ออารมณ์ (เสนอ · เลือกเอง)

| ไฟล์ | อารมณ์ | ข้อความ |
|---|---|---|
| `face_grumpy.png` | บึ้ง (ค่าเริ่มต้น) | ใช้ `face.webp` เดิม ไม่ต้องสั่ง |
| `face_closed.png` | หลับตา | ใช้ `face_eyes_closed.webp` เดิม |
| `face_content.png` | พอใจ/ถูกลูบ | `Emotion: content and relaxed. Eyes gently closed in happy upward curves, relaxed brows, tiny soft smile.` |
| `face_happy.png` | ดีใจ | `Emotion: happy. Eyes open and bright with big shiny pupils, brows raised, small cheerful smile.` |
| `face_sleepy.png` | ง่วง | `Emotion: sleepy. Eyelids drooping almost closed, heavy relaxed brows, mouth line relaxed.` |
| `face_surprised.png` | ตกใจ | `Emotion: surprised. Eyes wide open and round, small pupils, brows raised high, mouth a tiny "o".` |
| `face_angry.png` | โกรธ | `Emotion: angry. Narrow eyes with thin slit pupils, brows pulled down hard into a deep V, mouth line tense and turned down.` |
| `face_sad.png` | เศร้า | `Emotion: sad. Big watery eyes looking slightly down, inner brows raised, mouth turned down.` |
| `face_curious.png` | สงสัย | `Emotion: curious. Eyes wide with large round pupils looking up and to the side, one brow slightly raised.` |
| `face_hungry.png` | หิว | `Emotion: hungry. Eyes big and pleading looking up, tiny pink tongue tip licking the upper lip.` |
| `face_blink.png` | กะพริบครึ่งตา | `Emotion: mid-blink. Same grumpy look but eyelids half closed.` |

### ได้ภาพแล้วตรวจ

- วางทับต้นฉบับแล้วกะพริบสลับดู : หู จมูก ขน ขอบหัว ต้องไม่ขยับ (session หลักตรวจให้ได้ด้วยการเทียบพิกเซลนอกบริเวณตา/ปาก)
- ตาอยู่ตำแหน่งเดิม ขนาดเดิม · ถ้าเลื่อน สั่ง `redo, keep the eyes exactly where they are in the original`

## ท่าตัวคู่อารมณ์ (เสนอ · ทำด้วยสคริปต์ ไม่ต้องสั่งภาพ)

| อารมณ์ | หู | หาง | หัว/ตัว |
|---|---|---|---|
| บึ้ง | ตั้งปกติ | ตั้ง ปลายกระดิก | นิ่ง |
| พอใจ | ตั้ง เอนหน้า | ตั้งตรง ปลายงอ | เอียงหัวพิง |
| ตกใจ | หันหน้า ตั้งชัน | ฟูขึ้น | ตัวเกร็ง ย่อ |
| โกรธ | พับแบนไปหลัง | สะบัดแรง | ย่อตัว |
| เศร้า | ลู่ข้าง | ห้อยต่ำ | ก้มหัว |
| ง่วง | ลู่เล็กน้อย | วางลง | หัวตก |
