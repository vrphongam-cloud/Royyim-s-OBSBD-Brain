import anthropic
import os
import datetime

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def read_inbox():
    inbox_path = "inbox"
    files = []
    for f in os.listdir(inbox_path):
        if f.endswith(".txt") or f.endswith(".md"):
            with open(f"{inbox_path}/{f}", "r", encoding="utf-8") as file:
                files.append({"name": f, "content": file.read()})
    return files

def crystallize(files):
    if not files:
        return "ไม่มีไฟล์ใน inbox วันนี้ค่ะ"
    
    combined = "\n\n".join([f"=== {f['name']} ===\n{f['content']}" for f in files])
    
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": f"""คุณคือ Knowledge Agent ของ FN Decor Design
                    
อ่านไฟล์เหล่านี้จาก inbox แล้วทำการตกผลึกความรู้:
1. สกัดประเด็นสำคัญ
2. เชื่อมโยงกับงาน Interior Design
3. สรุปเป็น bullet points กระชับ

ไฟล์จาก inbox:
{combined}"""
                }]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                import time
                time.sleep(30)
    return "Error: ไม่สามารถเชื่อมต่อ Claude API ได้หลังจากลอง 3 ครั้งค่ะ"

def save_to_knowledge_base(result):
    today = datetime.date.today().strftime("%Y-%m-%d")
    path = f"knowledge-base/{today}_crystallized.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# ตกผลึก {today}\n\n{result}")
    print(f"บันทึกแล้วที่: {path}")

def save_log(result):
    today = datetime.date.today().strftime("%Y-%m-%d")
    path = f"logs/{today}_loop.log"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Loop รันเมื่อ: {datetime.datetime.now()}\n\n{result}")

if __name__ == "__main__":
    print("เริ่ม Loop...")
    files = read_inbox()
    print(f"พบไฟล์ใน inbox: {len(files)} ไฟล์")
    result = crystallize(files)
    save_to_knowledge_base(result)
    save_log(result)
    print("เสร็จแล้วค่ะ")
