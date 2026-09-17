import shutil

src = '/tmp/new_full_site_v13.html'
dst = '/tmp/new_full_site_v14.html'
shutil.copy2(src, dst)
s = open(dst, encoding='utf-8').read()


def sub(old, new, label):
    assert s.count(old) == 1, 'anchor %s count=%d' % (label, s.count(old))
    return s.replace(old, new)


# --- library rows: filename becomes a real link + copyable address ------------
old = """    const nameCell = r.pub
      ? '<button type="button" class="doclink" data-docurl="'+encodeURI(r.pub)+'" data-doctitle="'+esc(r.t)+'">'+esc(r.t)+'</button>'"""
new = """    const nameCell = r.pub
      ? '<a class="doclink" href="'+encodeURI(r.pub)+'">'+esc(r.t)+'</a>'+
        '<div class="docurl"><b>Full document:</b> <span class="url">'+
          esc(new URL(r.pub, location.href).href)+'</span>'+
          '<button type="button" class="copyurl" data-url="'+esc(new URL(r.pub, location.href).href)+
          '">Copy address</button></div>'"""
s = sub(old, new, 'library name cell')

# --- timeline related documents ----------------------------------------------
old = """        ? '<button type="button" class="doclink" data-docurl="'+encodeURI(d.pub)+'" data-doctitle="'+esc(label)+'">'+esc(label)+'</button>'"""
new = """        ? '<a class="doclink" href="'+encodeURI(d.pub)+'">'+esc(label)+'</a>'"""
s = sub(old, new, 'timeline doc link')

# --- modal markup ------------------------------------------------------------
start = s.index('<div id="docModal" class="docmodal" hidden>')
end = s.index('</div>', s.index('<div id="docModalText"')) + len('</div>')
end = s.index('</div>\n</div>', start) + len('</div>\n</div>')
block = s[start:end]
assert 'docModalFrame' in block and len(block) < 900, len(block)
s = s[:start] + s[end:]

# --- modal JS -> copy-address handler ----------------------------------------
start = s.index('// Documents we host ourselves open in an inline viewer')
end = s.index('});', s.index('const t = ev.target.closest("button.textlink");')) + 3
end = s.index('\n});', end) + 4
block = s[start:end]
assert 'openDocModal' in block and 'openTextModal' in block, block[:200]
s = s[:start] + """// No embedded PDF frame: iOS renders a framed PDF as one static page, and the
// sandbox blocks page-initiated downloads. Documents are plain links, with their
// address shown for copy/paste so the browser can open them at top level, where
// they paginate and offer Download / Open in app. Extracted text still opens
// in place, since text has no such limitation.
document.addEventListener("click", function(ev){
  const c = ev.target.closest("button.copyurl");
  if(c){
    const url = c.dataset.url;
    const done = function(ok){
      c.textContent = ok ? "Copied" : "Copy failed";
      setTimeout(function(){ c.textContent = "Copy address"; }, 1600);
    };
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(url).then(function(){ done(true); }, function(){ done(false); });
    } else { done(false); }
    return;
  }
  const t = ev.target.closest("button.textlink");
  if(t){
    const row = LIB.find(function(x){ return x.id===t.dataset.docid; });
    if(row) openTextPanel(row.txt, t.dataset.doctitle);
  }
});
""" + s[end:]

# --- text viewer: keep it, but as an in-page panel, not an overlay -----------
old = '<div id="docModalText" class="docmodal-text" hidden></div>'
s = s.replace(old, '')

old = """  .docmodal{position:fixed;inset:0;z-index:1000;padding:0 0 env(safe-area-inset-bottom,0px)}"""
start = s.index(old)
end = s.index('@media (max-width:640px){ .docmodal-panel{width:100vw;height:100vh;margin:0;border-radius:0} }')
end += len('@media (max-width:640px){ .docmodal-panel{width:100vw;height:100vh;margin:0;border-radius:0} }')
s = s[:start] + """  a.doclink{font-weight:600;font-size:.9rem;color:var(--accent-deep);word-break:break-word;
    flex:1 1 16rem}
  .docurl{flex:1 1 100%;display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;margin-top:.3rem;
    padding:.3rem .45rem;border:1px dashed var(--line);border-radius:4px;background:var(--panel2);
    font-size:.68rem}
  .docurl b{font-weight:600;color:var(--ink);-webkit-user-select:none;user-select:none}
  .docurl .url{font-family:"IBM Plex Mono",monospace;color:var(--muted);word-break:break-all;
    -webkit-user-select:all;user-select:all}
  button.copyurl{font:inherit;font-family:"IBM Plex Mono",monospace;font-size:.66rem;
    color:var(--accent);background:none;border:1px solid var(--line);border-radius:4px;
    padding:.12rem .4rem;cursor:pointer;white-space:nowrap}
  button.copyurl:hover{border-color:var(--accent);color:var(--accent-deep)}
  .textpanel{margin-top:.6rem;border:1px solid var(--line);border-radius:6px;background:var(--panel);
    max-height:30rem;overflow:auto;-webkit-overflow-scrolling:touch;padding:.9rem 1rem;
    white-space:pre-wrap;word-break:break-word;font-size:.86rem;line-height:1.65}
  .textpanel .close{float:right;font:inherit;font-size:.7rem;background:none;
    border:1px solid var(--line);border-radius:4px;padding:.15rem .45rem;cursor:pointer;
    color:var(--ink);margin-left:.6rem}""" + s[end:]

# --- text panel implementation ------------------------------------------------
old = 'function wireCopyLinks(root){'
new = """function openTextPanel(text, title){
  const host = document.getElementById("libRows");
  let panel = document.getElementById("textPanel");
  if(!panel){
    panel = document.createElement("div");
    panel.id = "textPanel";
    panel.className = "textpanel";
    host.parentNode.insertBefore(panel, host);
  }
  panel.textContent = text || "";
  const close = document.createElement("button");
  close.className = "close"; close.type = "button"; close.textContent = "Close text";
  close.addEventListener("click", function(){ panel.remove(); });
  panel.insertBefore(close, panel.firstChild);
  panel.scrollIntoView({behavior:"smooth", block:"start"});
}
function wireCopyLinks(root){"""
s = sub(old, new, 'text panel fn')

open(dst, 'w', encoding='utf-8').write(s)
print('wrote v14, bytes:', len(s))
print('docmodal refs left:', s.count('docmodal'), '| docModal refs:', s.count('docModal'))
