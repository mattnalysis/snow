import json, re

emails = json.load(open('/tmp/emails_merged.json', encoding='utf-8'))

AMT = re.compile(r'\$\s?\d[\d,]*(?:\.\d{2})?')
NUMERIC_FILE = re.compile(r'^\d{6,}\.pdf$', re.I)
INV_FILE = re.compile(r'(^inv\.|invoice|statement)', re.I)

BILLING_SENDERS = ('kjmartin@eastmansmith.com', 'kjlong@eastmansmith.com')


def money_class(e):
    """Return (category, why) or (None, None). Categories are ordered by specificity."""
    subj = (e.get('subject') or '').lower()
    body = (e.get('bodyText') or '').lower()
    sender = (e.get('from') or '').lower()
    files = [a.get('filename') or '' for a in (e.get('attachments') or [])]
    fl = ' '.join(files).lower()

    # 1. payment receipts — LawPay notifications are unambiguous
    if 'lawpay' in sender or 'payment receipt' in subj:
        return 'receipt', 'payment confirmation'

    # 2. retainer replenishment demands
    if 'retainer' in subj:
        return 'retainer', 'retainer replenishment'

    # 3. receiver / court fee applications (before generic invoice rules:
    #    a fee application is a court filing, not a bill to the group)
    if ('fees and costs' in subj or 'fees and costs' in fl or 'fee application' in subj
            or 'application of fees' in subj or 'interim app of fees' in fl):
        return 'fees', 'receiver fee application'

    # 4. invoices from counsel
    if 'invoice' in subj or 'past due' in subj:
        return 'invoice', 'invoice from counsel'
    if sender in BILLING_SENDERS and ('invoice' in body or 'balance' in body):
        return 'invoice', 'invoice from counsel'
    if any(NUMERIC_FILE.match(f) or INV_FILE.search(f) for f in files):
        return 'invoice', 'invoice attached'

    # 5. assessments levied on lot owners
    if 'assessment' in subj:
        return 'assessment', 'owner assessment'

    # 6. body-level discussion — only when money is actually named
    has_amt = bool(AMT.search(e.get('bodyText') or ''))
    strong_body = ('retainer' in body or 'invoice' in body or 'lawpay' in body
                   or 'balance due' in body or 'assessment' in body)
    if has_amt and strong_body:
        return 'discussion', 'discusses money'
    return None, None


def amounts(e):
    found = AMT.findall(e.get('bodyText') or '')
    out = []
    for f in found:
        try:
            v = float(f.replace('$', '').replace(',', '').strip())
        except ValueError:
            continue
        if v > 0:
            out.append(v)
    return out


counts = {}
tagged = {}
for e in emails:
    cat, why = money_class(e)
    if cat:
        counts[cat] = counts.get(cat, 0) + 1
        tagged[e['messageId']] = {'cat': cat, 'why': why, 'amts': amounts(e)}

print('=== classified ===')
for k in sorted(counts, key=lambda k: -counts[k]):
    print('%5d  %s' % (counts[k], k))
print('total money-related: %d of %d' % (len(tagged), len(emails)))

print('\n=== sample per category ===')
for cat in sorted(counts, key=lambda k: -counts[k]):
    print('\n--- %s ---' % cat)
    n = 0
    for e in emails:
        t = tagged.get(e['messageId'])
        if t and t['cat'] == cat:
            amt = max(t['amts']) if t['amts'] else None
            print('  %s | %-58s | %s' % (
                (e.get('date') or '')[:10], (e.get('subject') or '')[:58],
                ('${:,.2f}'.format(amt)) if amt else '-'))
            n += 1
            if n >= 6:
                break

print('\n=== NOT classified but mentions money words (check for misses) ===')
shown = 0
for e in emails:
    if e['messageId'] in tagged:
        continue
    blob = ((e.get('subject') or '') + ' ' + (e.get('bodyText') or '')).lower()
    if any(w in blob for w in ('invoice', 'retainer', 'lawpay', 'payment', 'balance due')):
        print('  %s | %s' % ((e.get('date') or '')[:10], (e.get('subject') or '')[:70]))
        shown += 1
        if shown >= 15:
            break
print('(showing up to 15)')

json.dump(tagged, open('/tmp/money_tags.json', 'w'), ensure_ascii=False)
