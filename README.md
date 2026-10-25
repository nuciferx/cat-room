# bb — เกมเลี้ยงแมว 3D (three.js)

เกมเลี้ยงแมวเปอร์เซียขนฟูหน้าบึ้ง บนเว็บ · ใช้ stack กฎ และวิธีปั้น 3D ของโป่งไพร (`F:/game/pp3`)

**สถานะ : ตั้งโครงการ ยังไม่มีโค้ด ยังไม่มีโมเดล** · รายละเอียด `CURRENT_STATUS.md`

## เอกสาร

| ไฟล์ | เรื่อง |
|---|---|
| `CLAUDE.md` | กฎการทำงานทั้งหมด (อ่านก่อนเริ่มทุกครั้ง) |
| `CONTEXT.md` | ศัพท์ที่ตกลงแล้ว |
| `CURRENT_STATUS.md` | ตอนนี้ทำถึงไหน |
| `NEXT_ACTION.md` | งานถัดไป เรียงลำดับ |
| `log.md` | บันทึกงานรายวัน |
| `docs/01_game_concept.md` | แนวเกม + คำถามที่รอเจ้าของงานตอบ |
| `docs/02_feasibility.md` | ประเมินความเป็นไปได้ของการปั้นแมวตามภาพ |
| `docs/03_cat_pipeline.md` | สายการปั้นแมว ภาพ → โมเดล → กระดูก → ท่า |
| `docs/04_tech_stack.md` | stack รุ่น และโครงโฟลเดอร์ |
| `docs/05_gpt_image_brief.md` | คำสั่งภาพ GPT ชุดปั้น |
| `docs/06_seedance_prompts.md` | คำสั่ง Seedance คลิปท่าแมว (แบบอ้างอิงตั้งท่า) |
| `docs/07_mui_emotions_brief.md` | อารมณ์ของมุ่ย : คำสั่งภาพหน้า GPT + ท่าตัวคู่อารมณ์ |
| `docs/ASSETS.md` | ทะเบียนที่มาและสิทธิ์ asset |
| `docs/adr/` | การตัดสินใจสำคัญ |
| `docs/agents/domain.md` | วิธีที่ skill อ่านเอกสารโดเมน |

## เริ่มใช้

```
npm install
npm run dev      # http://localhost:5173/cat.html (ห้องโชว์แมว)
npm run test     # vitest ชั้นตรรกะ
npm run build    # tsc --noEmit แล้ว vite build
```

## สิทธิ์ asset

ภาพอ้างอิง ภาพ GPT และไฟล์ต้นทาง Meshy/Hunyuan อยู่นอก repo (`F:/ai3d/in/cat/` · `shots/tmp.temp/`) · ดู `docs/ASSETS.md`
