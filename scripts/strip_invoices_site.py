"""Strip invoice emails, invoice PDFs and billing detail out of the public case site.

Mirrors the redaction already applied to email-index/index.public.html: the
invoice/receipt category goes, the receiver's fee application (a court filing)
and the retainer narrative stay. Rewrites site/index.html in place.

Run from the repo root:  python3 scripts/strip_invoices_site.py
"""
import json
import os
import re
import sys

SITE = 'site/index.html'

# Invoice records to remove outright: the covering email and the two invoice PDFs.
DROP_EX = {'EX-221', 'EX-222', 'EX-232'}
DROP_DOCS = {'site/docs/EX-222.pdf', 'site/docs/EX-232.pdf'}
# Extracted text of those same PDFs, keyed by the filename DOCTEXT carries.
DROP_DOCTEXT = {'4044933.pdf', 'Inv. 4058433.pdf'}
# The receiver's fee application is a court filing, not a bill to the owners —
# reclassify rather than remove, so it survives the invoice kind going away.
RECLASS = {'EX-170': ('invoice', 'filing')}

# bodies are hard-wrapped at varying widths, so every gap has to tolerate a newline
BALANCE = re.compile(
    r"This\s+month[’']s\s+invoice\s+for\s+professional\s+services\s+rendered\s+has\s+"
    r"depleted\s+the\s+entire\s+retainer\s+and\s+left\s+balance\s+due\s+of\s+\$[\d,]+\.\d{2}\.")
BALANCE_KEEP = ("This month’s invoice for professional services rendered "
                "has depleted the entire retainer.")
# Check-mailing address through the billing clerk's direct line: account
# numbers, the LawPay payment link and payment mechanics all live in here.
PAYBLOCK = re.compile(r"Checks\s+can\s+be\s+made\s+out.*?614-564-1474\.", re.S)
PAYBLOCK_KEEP = "[Payment instructions and billing account details removed from the public archive.]"
ATTACH_MARKER = re.compile(r"\n?<(?:Inv\. )?40\d{5}\.pdf>\n?")


def scrub(text):
    if not text:
        return text
    out = BALANCE.sub(BALANCE_KEEP, text)
    out = PAYBLOCK.sub(PAYBLOCK_KEEP, out)
    out = ATTACH_MARKER.sub('\n', out)
    return out


def json_line(lines, marker):
    """Index of the single line carrying an embedded JSON array."""
    hits = [i for i, l in enumerate(lines) if marker in l]
    assert len(hits) == 1, (marker, len(hits))
    return hits[0]


def load_array(line):
    return json.loads(line[line.index('['):line.rindex(']') + 1])


def store_array(line, data):
    # the embedded datasets are pure ASCII with \u escapes — keep them that way
    return line[:line.index('[')] + json.dumps(data, separators=(',', ':')) + line[line.rindex(']') + 1:]


def replace_once(lines, needle, repl):
    hits = [i for i, l in enumerate(lines) if needle in l]
    assert len(hits) == 1, ('expected one line containing %r, found %d' % (needle, len(hits)))
    i = hits[0]
    lines[i] = lines[i].replace(needle, repl)
    return i


def drop_line(lines, needle):
    hits = [i for i, l in enumerate(lines) if needle in l]
    assert len(hits) == 1, ('expected one line containing %r, found %d' % (needle, len(hits)))
    lines.pop(hits[0])


def main():
    src = open(SITE, encoding='utf-8').read()
    lines = src.split('\n')

    # ---- exhibit/email dataset -------------------------------------------
    i = json_line(lines, 'id="exdata"')
    ex = load_array(lines[i])
    before = len(ex)
    ex = [r for r in ex if r['id'] not in DROP_EX]
    for r in ex:
        old_new = RECLASS.get(r['id'])
        if old_new and r['k'] == old_new[0]:
            r['k'] = old_new[1]
        r['x'] = scrub(r.get('x'))
    lines[i] = store_array(lines[i], ex)
    print('exdata: %d -> %d records' % (before, len(ex)))

    # ---- document library ------------------------------------------------
    i = json_line(lines, 'id="libdata"')
    lib = load_array(lines[i])
    before = len(lib)
    lib = [r for r in lib if r['id'] not in DROP_EX]
    for r in lib:
        old_new = RECLASS.get(r['id'])
        if old_new and r['k'] == old_new[0]:
            r['k'] = old_new[1]
    lines[i] = store_array(lines[i], lib)
    print('libdata: %d -> %d records' % (before, len(lib)))

    # ---- extracted document text ----------------------------------------
    i = json_line(lines, 'const DOCTEXT=')
    dt = load_array(lines[i])
    before = len(dt)
    dt = [r for r in dt if r['name'] not in DROP_DOCTEXT]
    lines[i] = store_array(lines[i], dt)
    print('DOCTEXT: %d -> %d documents' % (before, len(dt)))

    # ---- the aggregated billing record and its now-unused type ----------
    drop_line(lines, '{d:"2024-01-23",t:"billing"')
    replace_once(lines, ',billing:"Billing"', '')
    drop_line(lines, '.rec .chip.billing{')
    print('record: billing series entry and billing type removed')

    # ---- invoice affordances in the UI ----------------------------------
    drop_line(lines, '<button data-lk="invoice"')
    drop_line(lines, '  .exkind.invoice{')
    replace_once(lines, 'invoice:"Invoice",', '')
    replace_once(lines, '"retainer","invoice",', '"retainer",')
    print('UI: invoice filter, kind label and topic keyword removed')

    # ---- timeline "related documents" pointing at an invoice ------------
    drop_line(lines, '"Construction ahead of schedule":["EX-222"],')
    print('timeline: invoice cross-reference removed')

    open(SITE, 'w', encoding='utf-8').write('\n'.join(lines))

    for p in sorted(DROP_DOCS):
        if os.path.exists(p):
            os.remove(p)
            print('unhosted %s' % p)


if __name__ == '__main__':
    if not os.path.exists(SITE):
        sys.exit('run from the repo root')
    main()
