import json, re, collections

emails = json.load(open('/tmp/emails_merged.json', encoding='utf-8'))

TERMS = ['invoice', 'retainer', 'payment', 'lawpay', 'receipt', 'fees and costs',
         'fee application', 'assessment', 'pay ', 'paid', 'balance due', 'remit',
         'wire', 'check', 'billing', 'billed', 'escrow', 'trust account']

hits = collections.Counter()
senders = collections.Counter()
subjects = collections.Counter()
for e in emails:
    blob = ((e.get('subject') or '') + ' ' + (e.get('bodyText') or '') + ' ' +
            ' '.join(a['filename'] for a in (e.get('attachments') or []))).lower()
    matched = [t for t in TERMS if t in blob]
    if matched:
        for t in matched:
            hits[t] += 1
        senders[e['from']] += 1
        subjects[(e.get('subject') or '')[:70]] += 1

print('=== term frequency ===')
for t, c in hits.most_common():
    print('%5d  %s' % (c, t))

print('\n=== top senders in money-ish mail ===')
for s, c in senders.most_common(12):
    print('%5d  %s' % (c, s))

print('\n=== most common subjects ===')
for s, c in subjects.most_common(25):
    print('%4d  %s' % (c, s))

# dollar amounts
amt = re.compile(r'\$\s?[\d,]+(?:\.\d{2})?')
with_amt = 0
samples = []
for e in emails:
    body = e.get('bodyText') or ''
    found = amt.findall(body)
    if found:
        with_amt += 1
        if len(samples) < 12:
            samples.append(((e.get('date') or '')[:10], (e.get('subject') or '')[:55], found[:6]))
print('\n=== messages containing a dollar amount: %d ===' % with_amt)
for s in samples:
    print(s)
