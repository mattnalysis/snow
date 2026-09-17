import re

p = '/tmp/email_index_viewer.html'
s = open(p, encoding='utf-8').read()


def sub(old, new, label):
    assert s.count(old) == 1, 'anchor %s count=%d' % (label, s.count(old))
    return s.replace(old, new)


# ---- 1. drop the modal markup ------------------------------------------------
old = """<div id="docModal" class="docmodal" hidden>
  <div class="docmodal-backdrop"></div>
  <div class="docmodal-panel">
    <div class="docmodal-bar">
      <span class="docmodal-title" id="docModalTitle"></span>
      <button type="button" class="docmodal-close" id="docModalClose">Close</button>
    </div>
    <iframe id="docModalFrame" class="docmodal-frame" title="Document viewer"></iframe>
  </div>
</div>

"""
s = sub(old, '', 'modal markup')

# ---- 2. drop the modal JS ----------------------------------------------------
start = s.index('/* Documents open in an iframe on this page')
end = s.index('});', s.index('rowsEl.addEventListener("click", function(ev){\n  const b = ev.target.closest("button.docbtn")')) + 3
modal_js = s[start:end]
assert 'docModalFrame' in modal_js and len(modal_js) < 1600, len(modal_js)
s = s[:start] + """/* No embedded PDF frame: iOS renders a framed PDF as a single static page, and
   the sandbox blocks page-initiated downloads. A direct link plus a copyable
   address lets the browser open the file at top level, where it paginates and
   offers its own share / download / open-in-app options. */
rowsEl.addEventListener("click", function(ev){
  const b = ev.target.closest("button.copyurl"); if(!b) return;
  ev.stopPropagation();
  const url = b.dataset.url;
  const done = function(ok){
    b.textContent = ok ? "Copied" : "Copy failed";
    setTimeout(function(){ b.textContent = "Copy address"; }, 1600);
  };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(url).then(function(){ done(true); }, function(){ done(false); });
  } else { done(false); }
});
rowsEl.addEventListener("click", function(ev){
  if(ev.target.closest("a.docfile") || ev.target.closest(".docurl")) ev.stopPropagation();
});""" + s[end:]

# ---- 3. attachment row: link + address, no modal button ---------------------
old = """          const doc = docFor(r, a.filename);
          const name = doc
            ? '<button type="button" class="docbtn" data-doc="'+esc(doc.path)+'" data-doctitle="'+
                esc(a.filename||"document")+'">'+esc(a.filename||"(unnamed)")+'</button>'
            : '<span class="fn">'+esc(a.filename||"(unnamed)")+'</span>';
          const size = doc ? fmtSize(doc.bytes) : fmtSize(a.size);
          const tail = doc ? '<span>'+esc(doc.exid)+'</span>'
                           : '<span class="nodoc">file not retrieved</span>';
          return '<div class="att">'+name+'<span>'+esc(a.mimeType||"")+'</span>'+
            '<span>'+size+'</span>'+tail+'</div>';"""
new = """          const doc = docFor(r, a.filename);
          const size = doc ? fmtSize(doc.bytes) : fmtSize(a.size);
          if(!doc){
            return '<div class="att"><span class="fn">'+esc(a.filename||"(unnamed)")+'</span>'+
              '<span>'+esc(a.mimeType||"")+'</span><span>'+size+'</span>'+
              '<span class="nodoc">file not retrieved</span></div>';
          }
          const href = encodeURI(doc.path);
          const abs = new URL(doc.path, location.href).href;
          return '<div class="att">'+
            '<a class="docfile" href="'+href+'">'+esc(a.filename||"(unnamed)")+'</a>'+
            '<span>'+esc(a.mimeType||"")+'</span><span>'+size+'</span>'+
            '<span>'+esc(doc.exid)+'</span>'+
            '<div class="docurl"><b>Full document:</b> <span class="url">'+esc(abs)+'</span>'+
              '<button type="button" class="copyurl" data-url="'+esc(abs)+'">Copy address</button>'+
            '</div>'+
          '</div>';"""
s = sub(old, new, 'attachment row')

# ---- 4. styles: link + address block; drop modal styles ---------------------
start = s.index('.docmodal{position:fixed')
end = s.index('@media (max-width:640px){ .docmodal-panel{width:100vw; height:100%; margin:0; border-radius:0} }')
end += len('@media (max-width:640px){ .docmodal-panel{width:100vw; height:100%; margin:0; border-radius:0} }')
s = s[:start] + """a.docfile{flex:1 1 14rem; font-family:"IBM Plex Mono",monospace; font-size:.74rem;
  color:var(--accent-deep); overflow-wrap:anywhere; text-underline-offset:2px}
.att{flex-wrap:wrap}
.docurl{flex:1 1 100%; display:flex; flex-wrap:wrap; align-items:center; gap:.4rem;
  margin-top:.3rem; padding:.3rem .45rem; border:1px dashed var(--line);
  border-radius:4px; background:var(--panel2); font-size:.68rem}
.docurl b{font-weight:600; color:var(--ink); -webkit-user-select:none; user-select:none}
.docurl .url{font-family:"IBM Plex Mono",monospace; color:var(--muted); overflow-wrap:anywhere;
  -webkit-user-select:all; user-select:all}
button.copyurl{font:inherit; font-family:"IBM Plex Mono",monospace; font-size:.66rem;
  color:var(--accent); background:none; border:1px solid var(--line); border-radius:4px;
  padding:.12rem .4rem; cursor:pointer; white-space:nowrap}
button.copyurl:hover{border-color:var(--accent); color:var(--accent-deep)}""" + s[end:]

# ---- 5. explain it once, up top ---------------------------------------------
old = """    <p class="stat" id="stat"></p>
    <div class="moneybar" id="moneyBar" hidden></div>"""
new = """    <p class="stat" id="stat"></p>
    <p class="stat" style="color:var(--muted)">Attached documents open by link. If your browser shows
      only the first page, copy the address under the file and paste it into a new tab — at top level
      the PDF paginates and your browser's own share menu offers Download and Open in&nbsp;app.</p>
    <div class="moneybar" id="moneyBar" hidden></div>"""
s = sub(old, new, 'explainer')

open(p, 'w', encoding='utf-8').write(s)
print('patched, bytes:', len(s))
print('docmodal refs left:', s.count('docmodal'), '| docbtn refs left:', s.count('docbtn'))
