"""Prove the excluded records are absent from the published file, not merely hidden."""
import json, re

page = open('/tmp/email_index_viewer.html', encoding='utf-8').read()
full = json.load(open('/tmp/emails_merged.json', encoding='utf-8'))
money = json.load(open('/tmp/money_tags.json', encoding='utf-8'))

removed = []
for e in full:
    m = money.get(e['messageId'])
    if e['classification'] == 'personal' or (m and m['cat'] in ('invoice', 'receipt')):
        removed.append(e)
print('records that should be gone:', len(removed))

# 1. no removed messageId anywhere in the file
id_hits = [e['messageId'] for e in removed if e['messageId'] in page]
print('removed messageIds still in page source:', len(id_hits))

# 2. no distinctive body text from a removed record
body_hits = []
for e in removed:
    b = (e.get('bodyText') or '').strip()
    if len(b) < 80:
        continue
    probe = b[40:140]
    if probe and probe in page:
        body_hits.append(e['messageId'])
print('removed bodies still in page source:', len(body_hits))

# 3. no invoice attachment filenames
fn_hits = []
for e in removed:
    for a in (e.get('attachments') or []):
        fn = a['filename']
        if re.match(r'^\d{6,}\.pdf$', fn, re.I) and fn in page:
            fn_hits.append(fn)
print('invoice-numbered attachment filenames still in page:', len(set(fn_hits)))

# 4. orphaned doc paths must not be referenced
orphans = json.load(open('/tmp/orphan_docs.json'))
path_hits = [o for o in orphans if o in page]
print('orphaned doc paths still referenced in page:', len(path_hits), path_hits[:4])

# 5. what the page actually carries now
m = re.search(r'<script type="application/json" id="emaildata">(.*?)</script>', page, re.S)
data = json.loads(m.group(1))
print('\npage now carries %d records' % len(data))
print('classifications present:', sorted(set(r['classification'] for r in data)))
mm = re.search(r'<script type="application/json" id="moneytags">(.*?)</script>', page, re.S)
cats = sorted(set(v['cat'] for v in json.loads(mm.group(1)).values()))
print('money categories present:', cats)

ok = not (id_hits or body_hits or fn_hits or path_hits)
print('\nREDACTION CLEAN:' , ok)
