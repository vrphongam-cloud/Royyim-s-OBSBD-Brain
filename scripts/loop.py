import anthropic
import os
import datetime
import json
import re

# ============================================================
# FN Decor Brain — loop.py (v2)
# ใหม่:  1) คัดเฉพาะไฟล์ใหม่จาก inbox (ไม่ crystallize ซ้ำ)
#         2) Enrich ความรู้เพิ่มเติมจากหัวข้อที่ได้รับ
#         3) Sync ผลลัพธ์ขึ้น Claude Project Knowledge
# ============================================================

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROCESSED_LOG = "logs/processed_files.json"
CLAUDE_PROJECT_ID = os.environ.get("CLAUDE_PROJECT_ID", "")


# ----------------------------------------------------------
# 1. อ่านไฟล์ใหม่จาก inbox (ข้ามไฟล์ที่เคย process แล้ว)
# ----------------------------------------------------------
def load_processed_log():
        if os.path.exists(PROCESSED_LOG):
                    with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
                                    return set(json.load(f))
                            return set()


def save_processed_log(processed: set):
        os.makedirs("logs", exist_ok=True)
        with open(PROCESSED_LOG, "w", encoding="utf-8") as f:
                    json.dump(sorted(list(processed)), f, ensure_ascii=False, indent=2)


def read_new_inbox_files():
        inbox_path = "inbox"
        processed = load_processed_log()
        new_files = []
        for f in os.listdir(inbox_path):
                    if f.endswith(".txt") or f.endswith(".md"):
                                    if f in processed:
                                                        print(f"  [skip] {f} — เคย process แล้ว")
                                                        continue
                                                    with open(f"{inbox_path}/{f}", "r", encoding="utf-8") as file:
                                                                        new_files.append({"name": f, "content": file.read()})
                                                                    print(f"  [new]  {f}")
                            return new_files, processed


# ----------------------------------------------------------
# 2. Crystallize — สกัดและตกผลึกความรู้จาก inbox
# ----------------------------------------------------------
def crystallize(files):
        combined = "\n\n".join(
                    [f"=== {f['name']} ===\n{f['content']}" for f in files]
        )
        prompt = f"""คุณคือ Knowledge Agent ของ FN Decor Design

    อ่านไฟล์เหล่านี้จาก inbox แล้วทำการตกผลึกความรู้:
    1. สกัดประเด็นสำคัญ
    2. เชื่อมโยงกับงาน Interior Design / Built-in ของ FN Decor
    3. สรุปเป็น bullet points กระชับ พร้อม one-liner หลักจำ

    ไฟล์จาก inbox:
    {combined}"""
        return _call_claude(prompt, max_tokens=2000)


# ----------------------------------------------------------
# 3. Enrich — ให้ Claude ขยายความรู้จากหัวข้อที่ได้รับ
#    (เหมือนสมองที่ 2 ไปหาความรู้เพิ่มเองในหัวข้อนั้น)
# ----------------------------------------------------------
def enrich(crystallized_text: str, file_names: list):
        topics = ", ".join([f.replace(".md", "").replace(".txt", "") for f in file_names])
        prompt = f"""คุณคือ Knowledge Agent ของ FN Decor Design

    จากที่ตกผลึกความรู้ต่อไปนี้:
    {crystallized_text}

    ทำการ Enrich ความรู้เพิ่มเติมในหัวข้อ: {topics}
    โดย:
    1. เชื่อมโยงกับหลักการ/ทฤษฎีที่เกี่ยวข้อง (เช่น Sales Psychology, Customer Experience, Interior Design principle)
    2. ยกตัวอย่างสถานการณ์จริงที่อาจเกิดขึ้นใน FN Decor เพิ่มเติม 2-3 สถานการณ์
    3. แนะนำ Best Practice หรือ Framework ที่นำไปปรับใช้ได้ทันที
    4. สรุป Action Items ที่ทีมควรทำ (3-5 ข้อ)

    เขียนเป็นภาษาไทย กระชับ เข้าใจง่าย เหมาะกับทีม Interior Design / Sales"""
        return _call_claude(prompt, max_tokens=2500)


# ----------------------------------------------------------
# 4. Sync ขึ้น Claude Project Knowledge
# ----------------------------------------------------------
def sync_to_claude_project(content: str, title: str):
        if not CLAUDE_PROJECT_ID:
                    print("  [skip] CLAUDE_PROJECT_ID ไม่ได้ตั้งค่า — ข้าม sync")
                    return False
                try:
                            # อัปโหลด document เข้า Claude Project ผ่าน Files API
                            # แล้ว attach เป็น Project Knowledge
                            file_content = content.encode("utf-8")
                            response = client.beta.files.upload(
                                file=(f"{title}.md", file_content, "text/plain"),
                            )
                            file_id = response.id
                            # เพิ่มเข้า Project Knowledge
                            client.beta.projects.documents.create(
                                            project_id=CLAUDE_PROJECT_ID,
                                            file_id=file_id,
                            )
        print(f"  [sync] อัปโหลดสำเร็จ → Claude Project: {file_id}")
        return True
except Exception as e:
        print(f"  [warn] Sync to Claude Project ล้มเหลว: {e}")
        print("         (ตรวจสอบ CLAUDE_PROJECT_ID และ ANTHROPIC_API_KEY)")
        return False


# ----------------------------------------------------------
# 5. บันทึกไฟล์ต่างๆ
# ----------------------------------------------------------
def save_to_knowledge_base(result: str, enriched: str):
        today = datetime.date.today().strftime("%Y-%m-%d")
        os.makedirs("knowledge-base", exist_ok=True)
        path = f"knowledge-base/{today}_crystallized.md"
        full_content = f"# ตกผลึก {today}\n\n{result}\n\n---\n\n## 🔍 Enriched Knowledge\n\n{enriched}"
        with open(path, "w", encoding="utf-8") as f:
                    f.write(full_content)
                print(f"  [save] knowledge-base → {path}")
    return path, full_content


def save_log(result: str, enriched: str, new_files: list, synced: bool):
        today = datetime.date.today().strftime("%Y-%m-%d")
    os.makedirs("logs", exist_ok=True)
    path = f"logs/{today}_loop.log"
    file_list = "\n".join([f"  - {f['name']}" for f in new_files])
    with open(path, "w", encoding="utf-8") as f:
                f.write(
                                f"Loop รันเมื่อ: {datetime.datetime.now()}\n"
                                f"ไฟล์ใหม่ที่ประมวลผล ({len(new_files)} ไฟล์):\n{file_list}\n"
                                f"Sync to Claude Project: {'สำเร็จ' if synced else 'ข้าม/ล้มเหลว'}\n\n"
                                f"=== Crystallized ===\n{result}\n\n"
                                f"=== Enriched ===\n{enriched}"
                )


# ----------------------------------------------------------
# Helper: เรียก Claude API พร้อม retry
# ----------------------------------------------------------
def _call_claude(prompt: str, max_tokens: int = 2000) -> str:
        import time
    for attempt in range(3):
                try:
                                message = client.messages.create(
                                                    model="claude-opus-4-6",
                                                    max_tokens=max_tokens,
                                                    messages=[{"role": "user", "content": prompt}],
                                )
                                return message.content[0].text
except Exception as e:
            print(f"  [retry {attempt+1}/3] {e}")
            if attempt < 2:
                                time.sleep(30)
                    return "Error: ไม่สามารถเชื่อมต่อ Claude API ได้หลังจากลอง 3 ครั้ง"


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------
if __name__ == "__main__":
        print("=" * 50)
    print(f"FN Decor Brain Loop — {datetime.date.today()}")
    print("=" * 50)

    # Step 1: อ่านเฉพาะไฟล์ใหม่
    print("\n[1] อ่านไฟล์ใหม่จาก inbox...")
    new_files, processed = read_new_inbox_files()

    if not new_files:
                print("  ไม่มีไฟล์ใหม่วันนี้ — จบการทำงาน")
                save_log("ไม่มีไฟล์ใหม่", "", [], False)
                exit(0)

    print(f"  พบไฟล์ใหม่: {len(new_files)} ไฟล์")

    # Step 2: Crystallize
    print("\n[2] Crystallize ความรู้...")
    crystallized = crystallize(new_files)

    # Step 3: Enrich
    print("\n[3] Enrich ความรู้เพิ่มเติม...")
    file_names = [f["name"] for f in new_files]
    enriched = enrich(crystallized, file_names)

    # Step 4: บันทึกลง knowledge-base
    print("\n[4] บันทึกลง knowledge-base...")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    kb_path, full_content = save_to_knowledge_base(crystallized, enriched)

    # Step 5: Sync ขึ้น Claude Project
    print("\n[5] Sync ขึ้น Claude Project...")
    synced = sync_to_claude_project(full_content, f"FN-Decor-Knowledge-{today_str}")

    # Step 6: บันทึก log และ mark files as processed
    print("\n[6] บันทึก log และ mark processed...")
    save_log(crystallized, enriched, new_files, synced)
    processed.update([f["name"] for f in new_files])
    save_processed_log(processed)

    print("\nเสร็จแล้วค่ะ ✅")
    print("=" * 50)
