import sys, json, re, subprocess
sys.path.insert(0,'/tmp')
from extract import process, b64url
T='/root/.claude/projects/-home-user-snow/576c26f0-5c20-5bab-9cf3-f6b3e9fd0dac.jsonl'
mid=sys.argv[1]
found=None
for line in open(T, errors='replace'):
    if '"'+mid+'"' not in line or '"raw"' not in line: continue
    m=re.search(r'\{"historyId":"[^"]*","id":"'+re.escape(mid)+r'".*?"threadId":"[0-9a-f]+"\}', line)
    if m:
        try:
            obj=json.loads(m.group(0).replace('\\n','\n').replace('\\"','"').replace('\\\\','\\'))
            found=obj.get('raw')
        except Exception:
            # fallback: pull raw value directly
            m2=re.search(r'"raw":"([A-Za-z0-9_\-=]+)"', m.group(0))
            if m2: found=m2.group(1)
if not found:
    print('NOT_FOUND_IN_TRANSCRIPT'); sys.exit(1)
rb=b64url(found)
print('rawbytes', len(rb))
for fn,st,n in process(mid, rb):
    print(f'  {st:10s} {n:9d} {fn}')
