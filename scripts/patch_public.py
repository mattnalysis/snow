import json

p = '/tmp/email_index_viewer.html'
s = open(p, encoding='utf-8').read()


def sub(old, new, label):
    assert s.count(old) == 1, 'anchor %s count=%d' % (label, s.count(old))
    return s.replace(old, new)


def swap_block(src, block_id):
    global s
    tag = '<script type="application/json" id="%s">' % block_id
    start = s.index(tag) + len(tag)
    end = s.index('</script>', start)
    data = open(src, encoding='utf-8').read().replace('<', '\\u003c').replace('\ufffd', '\\uFFFD')
    s = s[:start] + data + s[end:]


swap_block('/tmp/emails_public.json', 'emaildata')
swap_block('/tmp/attmap_public.json', 'attmap')
swap_block('/tmp/money_public.json', 'moneytags')

# --- no personal records remain: drop the chip -------------------------------
old = '        <button id="f-personal" data-f="personal" aria-pressed="false">Personal</button>\n'
s = sub(old, '', 'personal chip')
old = '        <button id="f-group" data-f="group" aria-pressed="false">Group</button>\n'
s = sub(old, '', 'group chip')

# --- money sub-select: invoices and receipts are gone ------------------------
old = """        <option value="invoice">Invoices from counsel</option>
        <option value="retainer">Retainer replenishment demands</option>
        <option value="receipt">Payment receipts</option>
        <option value="fees">Receiver fee applications</option>"""
new = """        <option value="retainer">Retainer replenishment demands</option>
        <option value="fees">Receiver fee applications</option>"""
s = sub(old, new, 'money options')

# --- totals: personal count is meaningless now -------------------------------
old = """  ["Group (full text)", nGroup.toLocaleString()],
  ["Personal (stub)", nPers.toLocaleString()],"""
new = ''
s = sub(old, new, 'totals personal')

# --- integrity checks: verify the redaction actually happened ----------------
old = """  [leaked===0, leaked===0 ? "No withheld message leaks content" : leaked+" personal records carry content"],"""
new = """  [nPers===0 && nRedacted===0, (nPers===0 && nRedacted===0)
    ? "No personal or invoice records present in this page"
    : (nPers+nRedacted)+" excluded records are still embedded"],"""
s = sub(old, new, 'integrity check')

old = 'const missing = DATA.filter(function(r){ return FIELDS.some(function(f){ return !(f in r); }); }).length;'
new = """const missing = DATA.filter(function(r){ return FIELDS.some(function(f){ return !(f in r); }); }).length;
const nRedacted = DATA.filter(function(r){
  const m = MONEY[r.messageId];
  return m && (m.cat === "invoice" || m.cat === "receipt");
}).length;"""
s = sub(old, new, 'redaction check')

# --- copy: say plainly what this page does and does not contain --------------
old = """  <p class="sub">Every case-related email pulled from Gmail into <span class="mono">mattnalysis/snow \u2192 data/emails/</span>, shown field by field so the extraction can be checked against the source. Group messages store full body text and attachment metadata; one-to-one messages are logged but their contents are deliberately withheld.</p>"""
new = """  <p class="sub">Case correspondence pulled from Gmail into <span class="mono">mattnalysis/snow \u2192 data/emails/</span>, shown field by field so the extraction can be checked against the source.</p>
  <p class="sub"><strong>This is a filtered copy.</strong> Personal one-to-one messages and everything billing-related \u2014 invoices from counsel and payment receipts \u2014 have been removed from this page entirely, along with the invoice PDFs they carried. They are not hidden: they are absent from the page and its source. The complete, unfiltered record remains in the git repository.</p>"""
s = sub(old, new, 'intro copy')

open(p, 'w', encoding='utf-8').write(s)
print('patched, bytes:', len(s))
print('sanity - personal chip gone:', 'f-personal' not in s)
