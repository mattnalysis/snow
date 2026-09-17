import json

p = '/tmp/email_index_viewer.html'
s = open(p, encoding='utf-8').read()


def sub(old, new, label):
    assert s.count(old) == 1, 'anchor not unique/found: ' + label + ' (count=%d)' % s.count(old)
    return s.replace(old, new)


# ---- A. styles for the document button + modal -------------------------------
old = ".att .fn{flex:1; overflow-wrap:anywhere}"
new = """.att .fn{flex:1; overflow-wrap:anywhere}
.att .nodoc{color:var(--muted); font-style:italic}
button.docbtn{font:inherit; font-family:"IBM Plex Mono",monospace; font-size:.74rem; text-align:left;
  flex:1; background:none; border:0; padding:0; color:var(--accent-deep); cursor:pointer;
  text-decoration:underline; text-decoration-color:color-mix(in srgb,var(--accent) 45%,transparent);
  text-underline-offset:2px; overflow-wrap:anywhere}
button.docbtn:hover{text-decoration-color:var(--accent-deep)}
.docmodal{position:fixed; inset:0; z-index:40}
.docmodal-backdrop{position:absolute; inset:0; background:rgba(8,14,20,.62)}
.docmodal-panel{position:relative; margin:2vh auto; width:min(96vw,900px); height:96vh;
  background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden;
  display:flex; flex-direction:column; box-shadow:0 12px 44px rgba(0,0,0,.35)}
.docmodal-bar{display:flex; align-items:center; gap:.75rem; padding:.6rem .75rem;
  border-bottom:1px solid var(--line); background:var(--panel2)}
.docmodal-title{flex:1; font-size:.8rem; font-weight:600; overflow:hidden;
  text-overflow:ellipsis; white-space:nowrap}
.docmodal-close{font:inherit; font-size:.76rem; background:none; border:1px solid var(--line);
  border-radius:4px; padding:.3rem .6rem; cursor:pointer; color:var(--ink); white-space:nowrap}
.docmodal-close:hover{border-color:var(--accent); color:var(--accent-deep)}
.docmodal-frame{flex:1; width:100%; min-height:0; border:0; background:#fff;
  -webkit-overflow-scrolling:touch}
@media (max-width:640px){ .docmodal-panel{width:100vw; height:100%; margin:0; border-radius:0} }"""
s = sub(old, new, 'css')

# ---- B. filter chip ----------------------------------------------------------
old = '<button id="f-att" data-f="att" aria-pressed="false">With attachments</button>'
new = ('<button id="f-att" data-f="att" aria-pressed="false">With attachments</button>\n'
       '        <button id="f-doc" data-f="doc" aria-pressed="false">Document attached</button>')
s = sub(old, new, 'chip')

# ---- C. modal markup + attachment map data block ----------------------------
old = '<script type="application/json" id="emaildata">'
new = """<div id="docModal" class="docmodal" hidden>
  <div class="docmodal-backdrop"></div>
  <div class="docmodal-panel">
    <div class="docmodal-bar">
      <span class="docmodal-title" id="docModalTitle"></span>
      <button type="button" class="docmodal-close" id="docModalClose">Close</button>
    </div>
    <iframe id="docModalFrame" class="docmodal-frame" title="Document viewer"></iframe>
  </div>
</div>

<script type="application/json" id="attmap">__ATTMAP__</script>
<script type="application/json" id="emaildata">"""
s = sub(old, new, 'modal+attmap')

# ---- D. parse the map, tag each record --------------------------------------
old = 'const DATA = JSON.parse(document.getElementById("emaildata").textContent);'
new = """const DATA = JSON.parse(document.getElementById("emaildata").textContent);
const ATT = JSON.parse(document.getElementById("attmap").textContent);
const ATT_SEP = " ||| ";
function docFor(r, filename){ return ATT[r.threadId + ATT_SEP + filename] || null; }"""
s = sub(old, new, 'attmap parse')

old = '  r._atts = (r.attachments||[]).length;'
new = """  r._atts = (r.attachments||[]).length;
  r._docs = (r.attachments||[]).filter(function(a){ return docFor(r, a.filename); }).length;"""
s = sub(old, new, 'record docs count')

# ---- E. attachment rows become document buttons -----------------------------
old = """          return '<div class="att"><span class="fn">'+esc(a.filename||"(unnamed)")+'</span>'+
            '<span>'+esc(a.mimeType||"")+'</span><span>'+fmtSize(a.size)+'</span></div>';"""
new = """          const doc = docFor(r, a.filename);
          const name = doc
            ? '<button type="button" class="docbtn" data-doc="'+esc(doc.path)+'" data-doctitle="'+
                esc(a.filename||"document")+'">'+esc(a.filename||"(unnamed)")+'</button>'
            : '<span class="fn">'+esc(a.filename||"(unnamed)")+'</span>';
          const size = doc ? fmtSize(doc.bytes) : fmtSize(a.size);
          const tail = doc ? '<span>'+esc(doc.exid)+'</span>'
                           : '<span class="nodoc">file not retrieved</span>';
          return '<div class="att">'+name+'<span>'+esc(a.mimeType||"")+'</span>'+
            '<span>'+size+'</span>'+tail+'</div>';"""
s = sub(old, new, 'attachment row')

# ---- F. filter by "has a document" ------------------------------------------
old = '  else if(filter==="att") list = list.filter(r=>r._atts>0);'
new = ('  else if(filter==="att") list = list.filter(r=>r._atts>0);\n'
       '  else if(filter==="doc") list = list.filter(r=>r._docs>0);')
s = sub(old, new, 'filter')

old = 'if(filter!=="all") bits.push(filter==="att" ? "with attachments" : filter);'
new = ('if(filter!=="all") bits.push(filter==="att" ? "with attachments"\n'
       '    : filter==="doc" ? "with an attached document open here" : filter);')
s = sub(old, new, 'filter label')

# ---- G. totals: how many attachments are actually openable ------------------
old = '  ["Attachments", nAtt.toLocaleString()],'
new = ('  ["Attachments", nAtt.toLocaleString()],\n'
       '  ["Documents here", nDocs.toLocaleString()],')
s = sub(old, new, 'totals row')

old = 'const nAtt   = DATA.reduce((s,r)=>s+r._atts,0);'
new = ('const nAtt   = DATA.reduce((s,r)=>s+r._atts,0);\n'
       'const nDocs  = DATA.reduce((s,r)=>s+r._docs,0);')
s = sub(old, new, 'totals count')

# ---- H. row metric shows the openable count ---------------------------------
old = """        (r._atts?' · '+r._atts+' att':'')+'</span>'+"""
new = """        (r._atts?' · '+r._atts+' att'+(r._docs?' ('+r._docs+' here)':'')+'':'')+'</span>'+"""
s = sub(old, new, 'row metric')

# ---- I. modal behaviour ------------------------------------------------------
old = 'document.getElementById("q").addEventListener("input", function(e){ q = e.target.value; render(); });'
new = """document.getElementById("q").addEventListener("input", function(e){ q = e.target.value; render(); });

/* Documents open in an iframe on this page: opening a new tab or navigating the
   top frame is blocked outright in some mobile browsers inside a sandboxed iframe. */
const docModal = document.getElementById("docModal"),
      docModalFrame = document.getElementById("docModalFrame"),
      docModalTitle = document.getElementById("docModalTitle");
function openDoc(path, title){
  docModalFrame.src = encodeURI(path);
  docModalTitle.textContent = title || "";
  docModal.hidden = false;
  document.body.style.overflow = "hidden";
}
function closeDoc(){
  docModal.hidden = true;
  docModalFrame.src = "about:blank";
  document.body.style.overflow = "";
}
document.getElementById("docModalClose").addEventListener("click", closeDoc);
docModal.querySelector(".docmodal-backdrop").addEventListener("click", closeDoc);
document.addEventListener("keydown", function(ev){
  if(ev.key === "Escape" && !docModal.hidden) closeDoc();
});
rowsEl.addEventListener("click", function(ev){
  const b = ev.target.closest("button.docbtn"); if(!b) return;
  ev.stopPropagation();
  openDoc(b.dataset.doc, b.dataset.doctitle);
});"""
s = sub(old, new, 'modal js')

# ---- inject the map itself ---------------------------------------------------
attmap = open('/tmp/attmap.json', encoding='utf-8').read()
attmap = attmap.replace('<', '\\u003c').replace('\ufffd', '\\uFFFD')
assert s.count('__ATTMAP__') == 1
s = s.replace('__ATTMAP__', attmap)

open(p, 'w', encoding='utf-8').write(s)
print('patched ok, bytes:', len(s))
