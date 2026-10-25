# สายการปั้นแมว (ภาพ GPT → Meshy/Hunyuan → กระดูกสี่ขา + ท่า → cat.glb)

ยกวิธีจากโป่งไพร : `F:/game/pp3/docs/character_pipeline.md` (คน) + `F:/game/pp3/tools/blender/build_quad_meshy.py` (สัตว์สี่ขา) · **ยังไม่ได้ลองกับแมว** ทุกข้อในไฟล์นี้เป็นแผน จนกว่าจะจดผลใน `log.md`

## ภาพรวม

```
ภาพ GPT 4 มุม 1024 + face.png (docs/05_gpt_image_brief.md)
   │
   ├─ ทาง A : Meshy image-to-3D (เจ้าของงานทำบนเว็บ Meshy) ──────────────► source.glb (เมชเดียว มีสี)
   └─ ทาง B : views_cutout → hunyuan_shape --ver 2mv → project_views ──► source.glb (เมชเดียว ฉายสี)
   │
   ▼
build_quad_meshy.py -- cat  (ค่าใน tools/blender/quad_meshy_cat.json)
   ตั้งพิกัด → ลดโพลี + normal จากเมชละเอียด → UV ใหม่ + อบภาพ 1024 → กระดูกสี่ขา → น้ำหนัก → ท่า → ส่งออก
   │
   ▼
public/assets/models/cat/cat.glb  → ห้องโชว์ cat.html (ดู/เดิน/สลับท่า)
```

## 1. คัดลอกเครื่องมือจาก pp3 (ครั้งเดียว)

คัดลอก ไม่ลิงก์ (pp3 อ่านอย่างเดียว) · จดชื่อไฟล์ + commit ต้นทางใน `docs/ASSETS.md` หัวข้อ "สคริปต์ที่ยกมา"

| ไฟล์ pp3 | ปลายทาง bb |
|---|---|
| `tools/blender/build_quad_meshy.py` + `quad_meshy_*.py` (bake clips lod material rig source tone weights preview check) | `tools/blender/` |
| `tools/blender/beasts_rig.py` `beasts_clips.py` `beasts_stance.py` `beasts_skin.py` `beasts_blender.py` | `tools/blender/` |
| ที่ถูก import ต่อ : `birds_blender.py` `birds_parts.py` `birds_pose.py` `gardener_img.py` | `tools/blender/` (ไล่ import ให้ครบก่อนรัน) |
| `tools/ai3d/hunyuan_shape.py` `views_cutout.py` `project_views.py` | `tools/ai3d/` |
| `tools/blender/quad_meshy_dog.json` | ต้นแบบของ `quad_meshy_cat.json` |

## 2. ภาพ

- เก็บที่ `F:/ai3d/in/cat/` (ไม่เข้า git) · ภาพอ้างอิงแรก `ref_sheet_8dir.webp` ใช้ดูทรง/สีเท่านั้น (เหตุผลใน `docs/02_feasibility.md`)
- ชุดที่ใช้ปั้น : `front.png` `left.png` `back.png` `right.png` 1024 พื้นเรียบ + `face.png`
- ⚠️ ตรวจทิศ : ภาพที่แมว **หันซ้ายของรูป** = กล้องอยู่ทาง **ขวาของตัวแมว** · ใส่ให้ตรงชื่อใน `viewFiles` ก่อนปั้น

## 3. ปั้นทรง

**ทาง A (Meshy)** : เจ้าของงานอัปโหลดภาพเข้า Meshy เอง (ส่งออกนอกเครื่อง = ห้าม agent ทำ) → ดาวน์โหลด glb ใส่ `shots/tmp.temp/meshy_cat/source.glb`

**ทาง B (Hunyuan ในเครื่อง)**

```bash
export PYTHONUTF8=1 HF_HUB_OFFLINE=1 TMP=F:/ai3d/tmp TEMP=F:/ai3d/tmp
PY=F:/ai3d/venv/Scripts/python
BL="F:/game/a/.tools/blender-5.2.1-windows-x64/blender.exe -b --factory-startup --python-exit-code 1 -P"
$PY tools/ai3d/views_cutout.py F:/ai3d/in/cat/views.json F:/ai3d/in/cat/cut
$PY tools/ai3d/hunyuan_shape.py F:/ai3d/in/cat/cut/cat F:/ai3d/out/cat/shape.glb --ver 2mv --octree 384 --faces 40000
$BL tools/ai3d/project_views.py -- F:/ai3d/out/cat/shape.glb F:/ai3d/in/cat/cut/cat shots/tmp.temp/hy_cat/source.glb --height 0.30 --tris 40000
```

- รันทีละงาน · ห้ามเปิด Blender ซ้อนตอน Hunyuan ทำงาน (RAM 16 GB)
- ⚠️ ยังไม่รู้ว่า `quad_meshy_source.py` อ่านภาพสีจากผล `project_views.py` ได้ไหม → ลองก่อนเขียนค่าอื่น

## 4. ไฟล์ค่าแมว `tools/blender/quad_meshy_cat.json`

เริ่มจาก `quad_meshy_dog.json` แล้วแก้ :

| ค่า | หมา | แมว (เสนอ · ต้องวัดจากโมเดลจริง) |
|---|---|---|
| `normalize.withersM` สูงไหล่ | 0.50 | ~0.25 (เปอร์เซียตัวโต · รวมขน) → **ถามเจ้าของงานว่าแมวตัวเท่าไร** |
| `budget.tris` | 4,000 | 6,000–8,000 (ตัวเอกเห็นใกล้ · ฉากมีตัวเดียว) |
| `budget.texPx` | 1,024 | 1,024 ตัว + ช่องตาแยกใน atlas |
| `legSplitZ` `hoofBand` | ตั้งจากหมา | วัดใหม่ : ขาสั้นจมในขน |
| กระดูกหาง | 3 ท่อน | 4–5 ท่อน (ผ่าน `rig.extra` หรือขยาย `SKELETON` ในสำเนาของเรา) |
| `mouth_item` | มี (คาบของ) | ตัดออก หรือคงไว้ถ้าแมวคาบของเล่น (ถามเจ้าของงาน) |
| `stances` `clips` | 17 ท่าหมา | ดูข้อ 5 |

## 5. ท่า

- **ยกจากหมาได้เลย (ปรับจังหวะ)** : idle · walk · trot · run · sit · lie · sniff · jump_up
- **ต้องเขียนใหม่ (ท่าแมว)** : ขดนอน · เลียขน/ล้างหน้า · บิดขี้เกียจ · นวด · ตะปบ/หมอบซุ่ม · ส่ายหาง/ตวัดหาง · กิน (ก้มชาม) · ถูกลูบ (เอียงหัว หลับตา)
- รายการจริงขึ้นกับระบบเกมที่เจ้าของงานตกลง (`docs/01_game_concept.md`) · ห้ามเขียนท่าเผื่อ
- ตา : ภาพตาสลับได้ (เปิด · หรี่ · หลับ) ในช่อง atlas แยก แทนกระดูกเปลือกตา · ตรวจว่าท่า "ถูกลูบ" ใช้หลับตา

## 6. ตรวจรับ

- ตัวตรวจไฟล์ `quad_meshy_check.mjs` (ยกมา) : จำนวนกระดูก · คลิปครบ · น้ำหนักรวม = 1 · ขนาดไฟล์ไม่เกินงบ
- ภาพตรวจ `quad_meshy_preview.py` (Blender ortho หลายมุม) เทียบกับภาพอ้างอิงทีละทิศ S SW W NW N NE E SE
- เจ้าของงานดูในห้องโชว์เอง (agent ไม่เปิดเบราว์เซอร์)

## กับดักที่รู้แล้ว (จากโป่งไพร)

- glb แยกจุดยอดทุกสามเหลี่ยม → **รวมจุดซ้อน (`remove_doubles`) ก่อนลดโพลี/นับเกาะ** ไม่งั้นผิวแตกหรือถูกลบหมด
- ภาพที่มีเงาเหลี่ยมติดมา ฉายลงเมชอื่น = ลายสามเหลี่ยมมั่ว → สีเรียบ (`flat`)
- Meshy มักมีปื้นแสงเงาติดใน texture → ขั้น `tone` ของ quad_meshy ลบปื้นสี คงลายขน
- ลดสามเหลี่ยมยาว ๆ แล้วลบสามเหลี่ยมทิ้งทั้งชิ้น = เป็นรู → ดึงจุดกลับแทนการลบ
