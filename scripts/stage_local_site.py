"""Stage a locally servable copy of the case site, using the PUBLISHED file names.

`site/docs/` holds short names (EX-257.pdf) while the artifact hosts, and
`libdata` points at, the long ones ("docs/EX-257 Entry granting Motion for
Leave to Withdraw as Counsel.pdf"). Serving `site/` directly therefore 404s on
every document. This copies the page plus each document under the name the page
actually asks for, so the file hand-off can be exercised over real HTTP.

    python3 scripts/stage_local_site.py /tmp/sitetest
    npx http-server -p 8199 -s /tmp/sitetest
    node scripts/test_handoff.js http://127.0.0.1:8199/index.html
"""
import json
import os
import shutil
import sys

SITE = 'site/index.html'
DOCS = 'site/docs'
EXTS = ('.pdf', '.PDF', '.html', '.docx')


def libdata():
    lines = open(SITE, encoding='utf-8').read().split('\n')
    hits = [l for l in lines if 'id="libdata"' in l]
    assert len(hits) == 1
    l = hits[0]
    return json.loads(l[l.index('['):l.rindex(']') + 1])


def local_source(doc_id):
    for ext in EXTS:
        p = os.path.join(DOCS, doc_id + ext)
        if os.path.exists(p):
            return p
    return None


def main(dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(os.path.join(dest, 'docs'))
    shutil.copyfile(SITE, os.path.join(dest, 'index.html'))

    staged, missing = 0, []
    for r in libdata():
        if not r.get('pub'):
            continue
        src = local_source(r['id'])
        if not src:
            missing.append(r['id'])
            continue
        shutil.copyfile(src, os.path.join(dest, r['pub']))
        staged += 1

    print('staged %d documents into %s' % (staged, dest))
    if missing:
        print('no local source for: %s' % ', '.join(missing))
    return 1 if missing else 0


if __name__ == '__main__':
    if not os.path.exists(SITE):
        sys.exit('run from the repo root')
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '/tmp/sitetest'))
