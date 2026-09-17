import json

SEP = ' ||| '
mapping = json.load(open('/tmp/attmap.json', encoding='utf-8'))
emails = json.load(open('/tmp/emails_merged.json', encoding='utf-8'))

work = []
seen = set()
for e in emails:
    for a in (e.get('attachments') or []):
        key = e['threadId'] + SEP + a['filename']
        if key in mapping:
            continue
        dedupe = (e['messageId'], a['filename'])
        if dedupe in seen:
            continue
        seen.add(dedupe)
        work.append({
            'messageId': e['messageId'],
            'threadId': e['threadId'],
            'filename': a['filename'],
            'mimeType': a.get('mimeType'),
            'date': e['date'][:10],
            'subject': e['subject'][:80],
        })

work.sort(key=lambda w: w['date'])
json.dump(work, open('/tmp/attachment_worklist.json', 'w'), ensure_ascii=False, indent=1)
print('attachments needing recovery:', len(work))
print('distinct messages to fetch:', len(set(w['messageId'] for w in work)))
for w in work[:8]:
    print('  ', w['date'], w['filename'][:70])
