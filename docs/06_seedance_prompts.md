# คำสั่ง Seedance — คลิปท่าแมว (ใช้เป็นแบบอ้างอิงตั้งท่าใน `quad_meshy_cat.json`)

เจ้าของงานเป็นคนสั่ง (ส่งออกนอกเครื่อง) · วิดีโอเก็บ `F:/ai3d/in/cat/motion/<ท่า>.mp4` ไม่เข้า git · ลงทะเบียนใน `docs/ASSETS.md`
ใช้ทำอะไร : ดูจังหวะขา หลัง หาง หัว แล้วตั้งค่าท่าด้วยสคริปต์ (ไม่ได้แปลงวิดีโอเป็นท่าโดยตรง)

## ตั้งค่า

- แบบ **ภาพ → วิดีโอ** · ภาพแรก = `F:/ai3d/in/cat/new/side_head_left.webp` (ข้างตรง หัวไปซ้าย) · ท่าที่ดูจากหน้าดีกว่า ใช้ `front.webp`
- ยาว 5 วินาที · กล้องนิ่ง · ถ้ามีตัวเลือก "กล้องคงที่" ให้เปิด
- ⚠️ ยังไม่ได้เปิดเอกสาร Seedance ยืนยันชื่อตัวเลือก/ความยาว/ขนาด — ใช้ตามที่หน้าเว็บมี

## ข้อความร่วม (วางหน้าทุกท่า)

```
The fluffy cream Persian cat from the image, same design, same soft clay-like 3D render style,
grumpy half-closed amber eyes. Plain flat light-grey studio background, no floor texture, no props.
Locked-off static camera, orthographic-like side view at the cat's height, whole body and tail always in frame,
no camera movement, no zoom, no cuts. Realistic cat body mechanics, smooth natural motion.
```

## ท่าที่มีอยู่แล้วในโมเดล (10 คลิป · แก้ให้เป็นท่าแมว)

| คลิป | ข้อความต่อท้าย | ภาพแรก |
|---|---|---|
| `idle` | `The cat stands still in place, breathing slowly, looks left and right with small head turns, ears twitch once, tail tip sways gently. Seamless loop.` | ข้าง |
| `walk` | `The cat walks slowly in place like on a treadmill, relaxed lazy walk, diagonal leg pairs, body stays level, head steady, tail held up. Seamless walk cycle loop.` | ข้าง |
| `trot` | `The cat trots in place like on a treadmill, quicker bouncy gait, tail up. Seamless loop.` | ข้าง |
| `run` | `The cat runs in place like on a treadmill, full gallop, back flexes and extends, tail streams behind but stays fluffy. Seamless loop.` | ข้าง |
| `sit` | `The cat sits down: hips lower to the floor, front legs stay straight, then it sits upright calmly with the tail wrapped around its front paws. Hold the sitting pose.` | ข้าง |
| `lie` | `The cat lies down: lowers its chest and belly to the floor, front paws tucked under (loaf pose), tail curled along its side. Hold the pose, slow breathing.` | ข้าง |
| `sniff` | `The cat lowers its head to sniff the floor in front of it, nose twitching, then lifts its head again. Body stays in place.` | ข้าง |
| `wag` | `The cat stands still, annoyed, and swishes its tail side to side slowly. Seamless loop.` | หน้า |
| `alarm` | `The cat startles: freezes, ears turn forward, body tenses and crouches slightly, tail puffs up, stares ahead.` | ข้าง |
| `jump_up` | `The cat crouches, wiggles its hips, then jumps straight up onto a low ledge just above its head height and lands on all four paws.` | ข้าง |

## ท่าแมวที่ยังไม่มี (สั่งเผื่อไว้ได้ · จะใส่เกมหรือไม่ รอตกลงระบบใน `docs/01_game_concept.md`)

| ท่า | ข้อความต่อท้าย | ภาพแรก |
|---|---|---|
| ขดนอน | `The cat lies down and curls into a tight ball, tail wrapped over its nose, eyes closed, sleeping, slow breathing.` | ข้าง |
| เลียขน | `The cat sits and licks its front paw, then wipes its face with the paw, grooming. Seamless loop.` | หน้า |
| บิดขี้เกียจ | `The cat does a long stretch: front legs reach forward low, rear raised, then stretches back legs one by one.` | ข้าง |
| นวด | `The cat lies in loaf pose and kneads with its front paws alternately, eyes half closed, content.` | หน้า |
| ตะปบ | `The cat crouches low, wiggles its hips, then pounces forward a short distance with both front paws.` | ข้าง |
| กิน | `The cat stands with head lowered, eating from the floor in front of it, small chewing head movements. Seamless loop.` | ข้าง |
| ถูกลูบ | `The cat stands still while being petted by an off-screen hand, closes its eyes, tilts its head, leans into the touch, tail raised.` | หน้า |
| หาว | `The cat sits and yawns widely, mouth open showing small teeth, then closes mouth and blinks slowly.` | หน้า |

## ได้วิดีโอแล้วตรวจก่อนส่ง

- ตัวแมวหน้าตาเหมือนภาพ (สี หน้าบึ้ง หางพุ่ม) ตลอดคลิป
- กล้องไม่ขยับ · ตัวไม่เดินออกนอกกรอบ (ท่าเดิน/วิ่งต้องอยู่กับที่)
- ขาไม่ซ้อน/งอกเกิน 4 ขา (วิดีโอ AI พลาดบ่อย)
