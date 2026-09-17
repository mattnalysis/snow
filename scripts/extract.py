import sys, json, os, re, base64, email, email.policy, glob

OUT='/tmp/recovered_docs'
MAN=os.path.join(OUT,'manifest.json')
LOG='/tmp/recovery_log.json'
os.makedirs(OUT, exist_ok=True)

keep=json.load(open('/tmp/keep.json'))

def load(p):
    manifest = json.load(open(p)) if os.path.exists(p) else []
    return manifest

def safe(mid, fn):
    fn = fn.replace('/','_').replace('\\','_').replace(' ','_')
    fn = re.sub(r'[^A-Za-z0-9._\-\[\]()]','_',fn)
    return f"{mid}_{fn}"

def find_raw(obj):
    """recursively find the raw base64 string in a json tool result"""
    best=None
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k in ('raw','rawMessage','raw_message') and isinstance(v,str) and len(v)>200:
                return v
            r=find_raw(v)
            if r and (best is None or len(r)>len(best)): best=r
    elif isinstance(obj, list):
        for v in obj:
            r=find_raw(v)
            if r and (best is None or len(r)>len(best)): best=r
    elif isinstance(obj, str):
        s=obj.strip()
        if len(s)>2000 and re.fullmatch(r'[A-Za-z0-9_\-+/=\s]+', s):
            return s
        # maybe nested json
        if s.startswith('{') or s.startswith('['):
            try: return find_raw(json.loads(s))
            except Exception: return None
    return best

def b64url(s):
    s=re.sub(r'\s','',s)
    pad='='*(-len(s)%4)
    try:
        return base64.urlsafe_b64decode(s+pad)
    except Exception:
        return base64.b64decode(s+pad)

def process(mid, rawbytes):
    manifest=load(MAN)
    log=load(LOG)
    wanted=[e for e in keep if e['messageId']==mid]
    msg=email.message_from_bytes(rawbytes, policy=email.policy.default)
    parts={}
    for part in msg.walk():
        fn=part.get_filename()
        if not fn: continue
        try: payload=part.get_payload(decode=True)
        except Exception: continue
        if payload is None: continue
        parts.setdefault(fn, payload)
        parts.setdefault(fn.strip(), payload)
    results=[]
    for e in wanted:
        fn=e['filename']
        payload=parts.get(fn)
        if payload is None:
            # fuzzy: match by basename-ish
            for k,v in parts.items():
                if k.replace(' ','')==fn.replace(' ',''):
                    payload=v; break
        if payload is None:
            log.append({**e,'status':'not_found_in_mime'}); results.append((fn,'not_found',0)); continue
        n=len(payload)
        if n > 14*1024*1024:
            log.append({**e,'status':'skipped_too_large','bytes':n}); results.append((fn,'too_large',n)); continue
        if fn.lower().startswith('image00') and n < 60*1024:
            log.append({**e,'status':'skipped_noise_signature_image','bytes':n}); results.append((fn,'noise',n)); continue
        sv=safe(mid,fn)
        open(os.path.join(OUT,sv),'wb').write(payload)
        manifest=[m for m in manifest if not (m['messageId']==mid and m['originalFilename']==fn)]
        manifest.append({'messageId':mid,'threadId':e['threadId'],'originalFilename':fn,
                         'savedAs':sv,'bytes':n,'mimeType':e['mimeType']})
        results.append((fn,'saved',n))
    json.dump(manifest, open(MAN,'w'), indent=1)
    json.dump(log, open(LOG,'w'), indent=1)
    return results

if __name__=='__main__':
    path=sys.argv[1]; mid=sys.argv[2]
    data=json.load(open(path))
    raw=find_raw(data)
    if not raw:
        print('NO_RAW_FOUND'); sys.exit(1)
    rb=b64url(raw)
    print('rawbytes', len(rb))
    for fn,st,n in process(mid, rb):
        print(f'  {st:10s} {n:9d} {fn}')
