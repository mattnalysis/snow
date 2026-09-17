import json, os, hashlib, shutil

SEP = ' ||| '
REC = '/tmp/recovered_docs'
OUT = '/tmp/viewer_docs'          # already holds the 55 EX-* library docs

manifest = json.load(open(os.path.join(REC, 'manifest.json')))
attmap = json.load(open('/tmp/attmap.json', encoding='utf-8'))
before = len(attmap)

# .docx cannot be served by the platform; we rendered each to .html alongside it
def served_file(entry):
    saved = entry['savedAs']
    if saved.lower().endswith('.docx'):
        alt = saved[:-5] + '.html'
        if os.path.exists(os.path.join(REC, alt)):
            return alt, 'text rendering'
    return saved, 'recovered'


# dedupe identical payloads (the Snow affidavits were re-sent on four threads)
byhash = {}
added = skipped = 0
for e in manifest:
    saved, label = served_file(e)
    src = os.path.join(REC, saved)
    if not os.path.exists(src):
        skipped += 1
        continue
    h = hashlib.sha256(open(src, 'rb').read()).hexdigest()
    if h not in byhash:
        n = len(byhash) + 1
        ext = os.path.splitext(saved)[1].lower()
        dest_name = 'R-%03d%s' % (n, ext)
        shutil.copy2(src, os.path.join(OUT, dest_name))
        byhash[h] = {'path': 'docs/' + dest_name, 'bytes': os.path.getsize(src), 'label': label}
    info = byhash[h]
    key = e['threadId'] + SEP + e['originalFilename']
    if key in attmap:
        skipped += 1
        continue
    attmap[key] = {'path': info['path'], 'exid': info['label'], 'bytes': info['bytes']}
    added += 1

json.dump(attmap, open('/tmp/attmap.json', 'w'), ensure_ascii=False)

files = sorted(os.listdir(OUT))
total = sum(os.path.getsize(os.path.join(OUT, f)) for f in files)
print('attachment map: %d -> %d entries (added %d, skipped %d)' % (before, len(attmap), added, skipped))
print('distinct files hosted: %d (%.1f MB)' % (len(files), total / 1048576))

emails = json.load(open('/tmp/emails_merged.json', encoding='utf-8'))
linked = tot = 0
for em in emails:
    for a in (em.get('attachments') or []):
        tot += 1
        if (em['threadId'] + SEP + a['filename']) in attmap:
            linked += 1
print('attachments: %d | now openable: %d (was 57)' % (tot, linked))

fmap = {('docs/' + f): f for f in files}
json.dump(fmap, open('/tmp/files_param.json', 'w'), indent=0)
print('wrote files map with %d entries' % len(fmap))
