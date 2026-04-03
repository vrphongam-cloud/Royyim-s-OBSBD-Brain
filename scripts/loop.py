import anthropic
import os
import datetime
import json

client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

PROCESSED_LOG = 'logs/processed_files.json'
CLAUDE_PROJECT_ID = os.environ.get('CLAUDE_PROJECT_ID', '')


def _call_claude(prompt, max_tokens=2000):
    import time
    for attempt in range(3):
        try:
            message = client.messages.create(
                model='claude-opus-4-5',
                max_tokens=max_tokens,
                messages=[{'role': 'user', 'content': prompt}],
            )
            return message.content[0].text
        except Exception as e:
            print(f'  [retry {attempt+1}/3] {e}')
            if attempt < 2:
                time.sleep(30)
    return 'Error: cannot connect to Claude API after 3 attempts'


def load_processed_log():
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def save_processed_log(processed):
    os.makedirs('logs', exist_ok=True)
    with open(PROCESSED_LOG, 'w', encoding='utf-8') as f:
        json.dump(sorted(list(processed)), f, ensure_ascii=False, indent=2)


def read_new_inbox_files():
    inbox_path = 'inbox'
    processed = load_processed_log()
    new_files = []
    for f in sorted(os.listdir(inbox_path)):
        if f.endswith('.txt') or f.endswith('.md'):
            if f in processed:
                print(f'  [skip] {f}')
                continue
            filepath = os.path.join(inbox_path, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                new_files.append({'name': f, 'content': file.read()})
            print(f'  [new]  {f}')
    return new_files, processed


def crystallize(files):
    parts = []
    for f in files:
        parts.append('=== ' + f['name'] + ' ===\n' + f['content'])
    combined = '\n\n'.join(parts)
    prompt = ('คุณคือ Knowledge Agent ของ FN Decor Design\n\n'
              'อ่านไฟล์เหล่านี้จาก inbox แล้วทำการตกผลึกความรู้:\n'
              '1. สกัดประเด็นสำคัญ\n'
              '2. เชื่อมโยงกับงาน Interior Design / Built-in ของ FN Decor\n'
              '3. สรุปเป็น bullet points กระชับ พร้อม one-liner หลักจำ\n\n'
              'ไฟล์จาก inbox:\n' + combined)
    return _call_claude(prompt, max_tokens=2000)


def enrich(crystallized_text, file_names):
    topics = ', '.join([f.replace('.md', '').replace('.txt', '') for f in file_names])
    prompt = ('คุณคือ Knowledge Agent ของ FN Decor Design\n\n'
              'จากที่ตกผลึกความรู้ต่อไปนี้:\n' + crystallized_text + '\n\n'
              'ทำการ Enrich ความรู้เพิ่มเติมในหัวข้อ: ' + topics + '\n'
              'โดย:\n'
              '1. เชื่อมโยงกับหลักการ/ทฤษฎีที่เกี่ยวข้อง\n'
              '2. ยกตัวอย่างสถานการณ์จริงที่อาจเกิดขึ้นใน FN Decor 2-3 สถานการณ์\n'
              '3. แนะนำ Best Practice หรือ Framework ที่นำไปปรับใช้ได้ทันที\n'
              '4. สรุป Action Items ที่ทีมควรทำ 3-5 ข้อ')
    return _call_claude(prompt, max_tokens=2500)


def sync_to_claude_project(content, title):
    if not CLAUDE_PROJECT_ID:
        print('  [skip] CLAUDE_PROJECT_ID not set')
        return False
    try:
        file_bytes = content.encode('utf-8')
        response = client.beta.files.upload(
            file=(title + '.md', file_bytes, 'text/plain'),
        )
        file_id = response.id
        client.beta.projects.documents.create(
            project_id=CLAUDE_PROJECT_ID,
            file_id=file_id,
        )
        print(f'  [sync] uploaded → file_id: {file_id}')
        return True
    except Exception as e:
        print(f'  [warn] sync failed: {e}')
        return False


def save_to_knowledge_base(result, enriched):
    today = datetime.date.today().strftime('%Y-%m-%d')
    os.makedirs('knowledge-base', exist_ok=True)
    path = 'knowledge-base/' + today + '_crystallized.md'
    full_content = '# ตกผลึก ' + today + '\n\n' + result + '\n\n---\n\n## Enriched Knowledge\n\n' + enriched
    with open(path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    print(f'  [save] {path}')
    return path, full_content


def save_log(result, enriched, new_files, synced):
    today = datetime.date.today().strftime('%Y-%m-%d')
    os.makedirs('logs', exist_ok=True)
    path = 'logs/' + today + '_loop.log'
    file_list = '\n'.join(['  - ' + f['name'] for f in new_files]) if new_files else '  (none)'
    with open(path, 'w', encoding='utf-8') as f:
        f.write('Loop ran: ' + str(datetime.datetime.now()) + '\n'
                + 'New files (' + str(len(new_files)) + '):\n' + file_list + '\n'
                + 'Sync: ' + ('ok' if synced else 'skipped') + '\n\n'
                + '=== Crystallized ===\n' + result + '\n\n'
                + '=== Enriched ===\n' + enriched)


if __name__ == '__main__':
    print('=' * 50)
    print('FN Decor Brain Loop —', datetime.date.today())
    print('=' * 50)

    print('\n[1] reading new inbox files...')
    new_files, processed = read_new_inbox_files()

    if not new_files:
        print('  no new files today — done')
        save_log('no new files', '', [], False)
        exit(0)

    print(f'  found: {len(new_files)} new file(s)')

    print('\n[2] crystallize...')
    crystallized = crystallize(new_files)

    print('\n[3] enrich...')
    file_names = [f['name'] for f in new_files]
    enriched = enrich(crystallized, file_names)

    print('\n[4] save to knowledge-base...')
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    kb_path, full_content = save_to_knowledge_base(crystallized, enriched)

    print('\n[5] sync to Claude Project...')
    synced = sync_to_claude_project(full_content, 'FN-Decor-Knowledge-' + today_str)

    print('\n[6] save log and mark processed...')
    save_log(crystallized, enriched, new_files, synced)
    processed.update([f['name'] for f in new_files])
    save_processed_log(processed)

    print('\ndone!')
    print('=' * 50)
