import json, os, hashlib, collections

d = '/tmp/recovered_docs'
manifest = json.load(open(os.path.join(d, 'manifest.json')))

MAGIC = {b'%PDF': 'pdf', b'PK\x03\x04': 'zip/office', b'\xff\xd8\xff': 'jpeg',
         b'\x89PNG': 'png', b'{\\rt': 'rtf'}


def sniff(path):
    with open(path, 'rb') as f:
        head = f.read(8)
    for magic, kind in MAGIC.items():
        if head.startswith(magic):
            return kind
    return 'unknown:' + repr(head[:6])


kinds = collections.Counter()
bad = []
byhash = collections.defaultdict(list)
for e in manifest:
    p = os.path.join(d, e['savedAs'])
    if not os.path.exists(p):
        bad.append((e['savedAs'], 'MISSING'))
        continue
    k = sniff(p)
    kinds[k] += 1
    if k.startswith('unknown'):
        bad.append((e['savedAs'], k))
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    byhash[h].append(e)

print('file kinds:', dict(kinds))
print('problem files:', bad)
print('manifest entries: %d | distinct contents: %d' % (len(manifest), len(byhash)))

dupes = {h: v for h, v in byhash.items() if len(v) > 1}
print('\nduplicate content groups: %d' % len(dupes))
for h, v in list(dupes.items())[:6]:
    print('  %-52s x%d' % (v[0]['originalFilename'][:52], len(v)))

ext = collections.Counter(os.path.splitext(e['originalFilename'])[1].lower() for e in manifest)
print('\nextensions:', dict(ext))
total = sum(os.path.getsize(os.path.join(d, e['savedAs'])) for e in manifest if os.path.exists(os.path.join(d, e['savedAs'])))
uniq = sum(os.path.getsize(os.path.join(d, v[0]['savedAs'])) for v in byhash.values())
print('total MB: %.1f | deduplicated MB: %.1f' % (total / 1048576, uniq / 1048576))
