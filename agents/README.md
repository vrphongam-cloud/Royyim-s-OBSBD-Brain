# Agents — FN Decor Design AI Team

โฟลเดอร์นี้เก็บ Role Profile ของ AI Agent ทั้ง 12 ตัวใน FN Decor Brain System
แต่ละไฟล์จะถูกใช้เป็น context โดย loop.py เพื่อให้ Claude รู้ว่ากำลังทำงานในฐานะ Agent คนไหน

## รายชื่อ Agents

| ไฟล์ | ชื่อ Agent | บทบาทหลัก |
|------|-----------|-----------|
| 00_secretary.md | AI เลขา | ประสานงาน สรุป จัดการข้อมูล |
| 01_data-agent.md | Data Agent | วิเคราะห์ข้อมูล ตัวเลข สถิติ |
| 02_writer-agent.md | Writer Agent | เขียนคอนเทนต์ รายงาน |
| 03_strategy-agent.md | Strategy Agent | วางแผนกลยุทธ์ธุรกิจ |
| 04_ops-agent.md | Ops Agent | จัดการ operations หน้างาน |
| 05_sales-agent.md | Sales Agent | เทคนิคขาย จิตวิทยาการขาย |
| 06_negotiation-agent.md | Negotiation Agent | การเจรจาต่อรอง |
| 07_knowledge-coach-agent.md | Knowledge Coach | สอน สรุป ถ่ายทอดความรู้ |
| 08_legal-agent.md | Legal Agent | กฎหมาย สัญญา ข้อกำหนด |
| 09_growth-motivation-agent.md | Growth & Motivation Agent | การเติบโต แรงจูงใจทีม |
| 10_critical-thinker-agent.md | Critical Thinker Agent | วิเคราะห์เชิงวิพากษ์ |
| 11_interior-expert-agent.md | Interior Expert Agent | ความเชี่ยวชาญ Interior Design / Built-in |

## วิธีการทำงาน

loop.py จะวนอ่าน agents/*.md แต่ละไฟล์ แล้วรัน crystallize + enrich
โดยส่ง role profile ของ Agent นั้นเป็น context เพื่อให้ความรู้ที่ได้
ตรงกับมุมมองและโดเมนของ Agent แต่ละคน
