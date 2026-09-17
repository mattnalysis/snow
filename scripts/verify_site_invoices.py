"""Prove the invoice material is gone from the public case site, not merely hidden.

Same posture as scripts/verify_redaction.py: grep the file itself, then re-parse
the embedded datasets and report what they actually carry now.

Run from the repo root:  python3 scripts/verify_site_invoices.py
"""
import json
import os
import sys

SITE = 'site/index.html'

# Strings that only exist in the invoice material.
FORBIDDEN = [
    'EX-221', 'EX-222', 'EX-232',          # the removed record ids
    '4044933', '4058433',                   # Eastman & Smith invoice numbers
    'Invoice (June 2026)',                  # subject of the invoice email
    '595.29',                               # balance carried on the Sept. 2026 invoice
    'lawpaylink',                           # credit-card payment link
    'Client/Company number',                # billing account identifiers
    'Checks can be made out',               # payment instructions
    'data-lk="invoice"',                    # the Invoices filter chip
]
UNHOSTED = ['site/docs/EX-222.pdf', 'site/docs/EX-232.pdf']


def main():
    page = open(SITE, encoding='utf-8').read()
    lines = page.split('\n')

    print('=== string scan ===')
    bad = []
    for s in FORBIDDEN:
        n = page.lower().count(s.lower())
        if n:
            bad.append((s, n))
        print('%-24s %s' % (s, 'absent' if not n else 'STILL PRESENT x%d' % n))

    print('\n=== hosted files ===')
    for p in UNHOSTED:
        here = os.path.exists(p)
        if here:
            bad.append((p, 1))
        print('%-24s %s' % (os.path.basename(p), 'removed' if not here else 'STILL ON DISK'))

    def array(marker):
        hits = [l for l in lines if marker in l]
        assert len(hits) == 1, marker
        l = hits[0]
        return json.loads(l[l.index('['):l.rindex(']') + 1])

    ex = array('id="exdata"')
    lib = array('id="libdata"')
    dt = array('const DOCTEXT=')

    print('\n=== datasets now carry ===')
    print('exdata   %d records, kinds: %s' % (len(ex), sorted(set(r['k'] for r in ex))))
    print('libdata  %d documents, kinds: %s' % (len(lib), sorted(set(r['k'] for r in lib))))
    print('DOCTEXT  %d extracted documents' % len(dt))

    # every kind the library can show must still have a label and a filter chip
    labels = lines[[i for i, l in enumerate(lines) if 'const LIBK=' in l][0]]
    missing = [k for k in set(r['k'] for r in lib) if (k + ':"') not in labels]
    if missing:
        bad.append(('unlabelled kinds: %s' % missing, 1))
    print('unlabelled library kinds:', missing or 'none')

    # every timeline cross-reference must resolve to a document still present
    ids = set(r['id'] for r in lib)
    tl = [l for l in lines if '":["EX-' in l]
    dangling = []
    for l in tl:
        for ref in json.loads(l.strip().rstrip(',').split(':', 1)[1]):
            if ref not in ids:
                dangling.append(ref)
    if dangling:
        bad.append(('dangling timeline refs: %s' % dangling, 1))
    print('dangling timeline document refs:', dangling or 'none')

    print('\nSITE CLEAN:', not bad)
    return 1 if bad else 0


if __name__ == '__main__':
    if not os.path.exists(SITE):
        sys.exit('run from the repo root')
    sys.exit(main())
