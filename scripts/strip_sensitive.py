import json, collections

SEP = ' ||| '
emails = json.load(open('/tmp/emails_merged.json', encoding='utf-8'))
money = json.load(open('/tmp/money_tags.json', encoding='utf-8'))
attmap = json.load(open('/tmp/attmap.json', encoding='utf-8'))

DROP_MONEY = {'invoice', 'receipt'}


def dropped(e):
    if e.get('classification') == 'personal':
        return 'personal'
    m = money.get(e['messageId'])
    if m and m['cat'] in DROP_MONEY:
        return m['cat']
    return None


keep, removed = [], collections.Counter()
for e in emails:
    why = dropped(e)
    if why:
        removed[why] += 1
    else:
        keep.append(e)

print('removed: %s  (total %d)' % (dict(removed), sum(removed.values())))
print('remaining messages: %d of %d' % (len(keep), len(emails)))

# which hosted documents are referenced ONLY by removed messages?
refs = collections.defaultdict(set)
for e in emails:
    for a in (e.get('attachments') or []):
        hit = attmap.get(e['threadId'] + SEP + a['filename'])
        if hit:
            refs[hit['path']].add(e['messageId'])
kept_ids = set(e['messageId'] for e in keep)
orphans = sorted(p for p, ids in refs.items() if not (ids & kept_ids))
print('hosted docs now orphaned: %d of %d' % (len(orphans), len(refs)))

# rebuild the map with only keys reachable from kept messages
new_attmap = {}
for e in keep:
    for a in (e.get('attachments') or []):
        k = e['threadId'] + SEP + a['filename']
        if k in attmap:
            new_attmap[k] = attmap[k]
new_money = {e['messageId']: money[e['messageId']] for e in keep if e['messageId'] in money}
cats = collections.Counter(v['cat'] for v in new_money.values())
print('money tags remaining: %d %s' % (len(new_money), dict(cats)))

linked = sum(1 for e in keep for a in (e.get('attachments') or [])
             if (e['threadId'] + SEP + a['filename']) in new_attmap)
atts = sum(len(e.get('attachments') or []) for e in keep)
print('attachments on kept messages: %d | openable: %d' % (atts, linked))

json.dump(keep, open('/tmp/emails_public.json', 'w'), separators=(',', ':'), ensure_ascii=False)
json.dump(new_attmap, open('/tmp/attmap_public.json', 'w'), ensure_ascii=False)
json.dump(new_money, open('/tmp/money_public.json', 'w'), ensure_ascii=False)
json.dump(orphans, open('/tmp/orphan_docs.json', 'w'), indent=1)
print('\nsample orphaned files:', orphans[:6])
