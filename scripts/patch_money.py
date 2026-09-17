import json

p = '/tmp/email_index_viewer.html'
s = open(p, encoding='utf-8').read()


def sub(old, new, label):
    assert s.count(old) == 1, 'anchor %s count=%d' % (label, s.count(old))
    return s.replace(old, new)


# ---- styles: money badges + sub-filter select --------------------------------
old = '.tag.group{color:var(--ok)} .tag.personal{color:var(--warn)}'
new = """.tag.group{color:var(--ok)} .tag.personal{color:var(--warn)}
.tag.invoice{color:var(--accent-deep)} .tag.retainer{color:var(--bad)}
.tag.receipt{color:var(--ok)} .tag.fees{color:var(--accent-deep)}
.tag.assessment{color:var(--warn)} .tag.discussion{color:var(--muted)}
.amt{font-family:"IBM Plex Mono",monospace; font-size:.72rem; font-variant-numeric:tabular-nums;
  color:var(--ink); white-space:nowrap}
.subfilter{display:flex; align-items:center; gap:.45rem; font-size:.78rem; color:var(--muted)}
.subfilter select{font:inherit; font-size:.8rem; padding:.35rem .5rem; color:var(--ink);
  background:var(--panel); border:1px solid var(--line); border-radius:6px}
.moneybar{margin:.5rem 0 0; padding:.55rem .75rem; background:var(--accent-soft);
  border-radius:6px; font-size:.8rem; color:var(--ink)}
.moneybar b{font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums}"""
s = sub(old, new, 'money css')

# ---- chip + sub-select -------------------------------------------------------
old = '        <button id="f-doc" data-f="doc" aria-pressed="false">Document attached</button>'
new = """        <button id="f-doc" data-f="doc" aria-pressed="false">Document attached</button>
        <button id="f-money" data-f="money" aria-pressed="false">Invoices &amp; payments</button>"""
s = sub(old, new, 'money chip')

old = '    <p class="stat" id="stat"></p>'
new = """    <label class="subfilter" id="moneySubWrap" hidden>Kind
      <select id="moneySub" aria-label="Filter by kind of money message">
        <option value="all">All money mail</option>
        <option value="invoice">Invoices from counsel</option>
        <option value="retainer">Retainer replenishment demands</option>
        <option value="receipt">Payment receipts</option>
        <option value="fees">Receiver fee applications</option>
        <option value="discussion">Mentions an amount</option>
      </select>
    </label>
    <p class="stat" id="stat"></p>
    <div class="moneybar" id="moneyBar" hidden></div>"""
s = sub(old, new, 'money subselect')

# ---- data block --------------------------------------------------------------
old = '<script type="application/json" id="attmap">'
new = '<script type="application/json" id="moneytags">__MONEY__</script>\n<script type="application/json" id="attmap">'
s = sub(old, new, 'money data block')

old = 'const ATT = JSON.parse(document.getElementById("attmap").textContent);'
new = """const ATT = JSON.parse(document.getElementById("attmap").textContent);
const MONEY = JSON.parse(document.getElementById("moneytags").textContent);
const MONEY_LABEL = {invoice:"invoice", retainer:"retainer due", receipt:"payment receipt",
  fees:"fee application", assessment:"assessment", discussion:"names an amount"};
function money(r){ return MONEY[r.messageId] || null; }
function fmtAmt(v){ return "$" + v.toLocaleString(undefined,{minimumFractionDigits:2, maximumFractionDigits:2}); }"""
s = sub(old, new, 'money parse')

# ---- per-record tagging ------------------------------------------------------
old = '  r._docs = (r.attachments||[]).filter(function(a){ return docFor(r, a.filename); }).length;'
new = """  r._docs = (r.attachments||[]).filter(function(a){ return docFor(r, a.filename); }).length;
  const mt = MONEY[r.messageId];
  r._money = mt ? mt.cat : null;
  r._amts = mt && mt.amts ? mt.amts.slice().sort(function(a,b){return b-a;}) : [];"""
s = sub(old, new, 'money record tag')

# ---- filtering ---------------------------------------------------------------
old = '  else if(filter==="doc") list = list.filter(r=>r._docs>0);'
new = """  else if(filter==="doc") list = list.filter(r=>r._docs>0);
  else if(filter==="money"){
    list = list.filter(r=>r._money);
    if(moneySub!=="all") list = list.filter(r=>r._money===moneySub);
  }"""
s = sub(old, new, 'money filter')

old = """if(filter!=="all") bits.push(filter==="att" ? "with attachments"
    : filter==="doc" ? "with an attached document open here" : filter);"""
new = """if(filter!=="all") bits.push(filter==="att" ? "with attachments"
    : filter==="doc" ? "with an attached document open here"
    : filter==="money" ? (moneySub==="all" ? "invoices and payments" : MONEY_LABEL[moneySub])
    : filter);"""
s = sub(old, new, 'money stat label')

# ---- money summary bar -------------------------------------------------------
old = '  if(!list.length){ rowsEl.innerHTML = \'<li class="empty">No messages match.</li>\'; return; }'
new = """  const bar = document.getElementById("moneyBar");
  if(filter==="money"){
    const byCat = {};
    list.forEach(function(r){ byCat[r._money] = (byCat[r._money]||0)+1; });
    const parts = Object.keys(byCat).sort(function(a,b){ return byCat[b]-byCat[a]; })
      .map(function(k){ return "<b>"+byCat[k]+"</b> "+MONEY_LABEL[k]+(byCat[k]===1?"":"s"); });
    const withAmt = list.filter(function(r){ return r._amts.length; }).length;
    bar.innerHTML = parts.join(" · ") +
      '<br><span style="color:var(--muted)">Amounts shown are figures named in the email body; ' +
      withAmt + ' of these messages name one. Invoice totals live inside the attached PDF, ' +
      'not the email text.</span>';
    bar.hidden = false;
  } else { bar.hidden = true; }
  if(!list.length){ rowsEl.innerHTML = '<li class="empty">No messages match.</li>'; return; }"""
s = sub(old, new, 'money bar')

# ---- row: money badge + largest amount --------------------------------------
old = """      '<span><span class="tag '+r.classification+'">'+r.classification+'</span></span>'+"""
new = """      '<span><span class="tag '+r.classification+'">'+r.classification+'</span>'+
        (r._money?' <span class="tag '+r._money+'">'+MONEY_LABEL[r._money]+'</span>':'')+
        (r._amts.length?' <span class="amt" title="Largest amount named in the email body">'+
          fmtAmt(r._amts[0])+'</span>':'')+'</span>'+"""
s = sub(old, new, 'row money badge')

# ---- detail: amounts field ---------------------------------------------------
old = """        '<dt>Class</dt><dd>'+esc(r.classification)+' · '+recipCount(r)+' recipients</dd>'+"""
new = """        '<dt>Class</dt><dd>'+esc(r.classification)+' · '+recipCount(r)+' recipients</dd>'+
        (r._money?'<dt>Money</dt><dd>'+esc(MONEY_LABEL[r._money])+
          (r._amts.length?' · amounts named in body: '+r._amts.map(fmtAmt).join(", "):
            ' · no amount in the email text')+'</dd>':'')+"""
s = sub(old, new, 'detail money field')

# ---- sub-select wiring -------------------------------------------------------
old = """document.querySelectorAll(".chips button").forEach(function(b){
  b.addEventListener("click", function(){
    filter = b.dataset.f;"""
new = """document.getElementById("moneySub").addEventListener("change", function(e){
  moneySub = e.target.value; render();
});
document.querySelectorAll(".chips button").forEach(function(b){
  b.addEventListener("click", function(){
    filter = b.dataset.f;
    document.getElementById("moneySubWrap").hidden = (filter !== "money");
    if(filter !== "money"){ moneySub = "all"; document.getElementById("moneySub").value = "all"; }"""
s = sub(old, new, 'subselect wiring')

old = 'let q = "", filter = "all", year = null;'
new = 'let q = "", filter = "all", year = null, moneySub = "all";'
s = sub(old, new, 'state var')

tags = open('/tmp/money_tags.json', encoding='utf-8').read()
tags = tags.replace('<', '\\u003c').replace('\ufffd', '\\uFFFD')
assert s.count('__MONEY__') == 1
s = s.replace('__MONEY__', tags)

open(p, 'w', encoding='utf-8').write(s)
print('patched, bytes:', len(s))
