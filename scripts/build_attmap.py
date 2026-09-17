import re, json, os, shutil

SEP = ' ||| '

site = open('/tmp/new_full_site_v13.html', encoding='utf-8').read()
m = re.search(r'<script type="application/json" id="libdata">(.*?)</script>', site, re.S)
LIB = json.loads(m.group(1))
emails = json.load(open('/tmp/emails_merged.json', encoding='utf-8'))

srcdir = '/tmp/site_preview5/docs'
by_exid = {}
for f in os.listdir(srcdir):
    by_exid[f.split(' ', 1)[0]] = f

os.makedirs('/tmp/viewer_docs', exist_ok=True)
mapping = {}
copied = 0
for r in LIB:
    if not r.get('pub'):
        continue
    src = by_exid.get(r['id'])
    if not src:
        print('NO DISK FILE for', r['id'])
        continue
    ext = os.path.splitext(src)[1].lower()
    dest_name = r['id'] + ext
    shutil.copy2(os.path.join(srcdir, src), os.path.join('/tmp/viewer_docs', dest_name))
    copied += 1
    if r.get('tid') and r.get('t'):
        mapping[r['tid'] + SEP + r['t']] = {
            'path': 'docs/' + dest_name,
            'exid': r['id'],
            'bytes': os.path.getsize(os.path.join(srcdir, src)),
        }

print('copied files:', copied)
json.dump(mapping, open('/tmp/attmap.json', 'w'), ensure_ascii=False)

linked = total = 0
unlinked = []
for e in emails:
    for a in (e.get('attachments') or []):
        total += 1
        if (e['threadId'] + SEP + a['filename']) in mapping:
            linked += 1
        else:
            unlinked.append(a['filename'])
print('attachments: %d | linkable to a hosted doc: %d' % (total, linked))
mb = sum(os.path.getsize('/tmp/viewer_docs/' + f) for f in os.listdir('/tmp/viewer_docs')) / 1048576
print('staged docs total MB:', round(mb, 1))
json.dump(sorted(set(unlinked)), open('/tmp/unlinked_attachments.json', 'w'), ensure_ascii=False, indent=1)
print('distinct unlinked filenames:', len(set(unlinked)))
