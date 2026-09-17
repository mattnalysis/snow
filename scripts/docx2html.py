"""Render a .docx into a readable standalone HTML page.

LibreOffice is unusable in this container, so we read WordprocessingML directly:
paragraphs, heading styles, list items and tables carry the structure that
matters for meeting minutes; runs contribute bold/italic.
"""
import sys, zipfile, html, re
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def runs_to_html(p):
    out = []
    for r in p.iter(W + 'r'):
        text = ''.join(t.text or '' for t in r.iter(W + 't'))
        if not text:
            if r.find(W + 'br') is not None:
                out.append('<br>')
            continue
        rpr = r.find(W + 'rPr')
        esc = html.escape(text)
        if rpr is not None:
            if rpr.find(W + 'b') is not None:
                esc = '<strong>' + esc + '</strong>'
            if rpr.find(W + 'i') is not None:
                esc = '<em>' + esc + '</em>'
            if rpr.find(W + 'u') is not None:
                esc = '<u>' + esc + '</u>'
        out.append(esc)
    return ''.join(out)


def para_style(p):
    ppr = p.find(W + 'pPr')
    if ppr is None:
        return None, False
    st = ppr.find(W + 'pStyle')
    name = st.get(W + 'val') if st is not None else None
    is_list = ppr.find(W + 'numPr') is not None
    return name, is_list


def convert(src, title):
    z = zipfile.ZipFile(src)
    root = ET.fromstring(z.read('word/document.xml'))
    body = root.find(W + 'body')
    parts, open_list = [], False

    def close_list():
        nonlocal open_list
        if open_list:
            parts.append('</ul>')
            open_list = False

    for el in body:
        tag = el.tag
        if tag == W + 'p':
            style, is_list = para_style(el)
            inner = runs_to_html(el).strip()
            if not inner:
                continue
            if is_list:
                if not open_list:
                    parts.append('<ul>')
                    open_list = True
                parts.append('<li>' + inner + '</li>')
                continue
            close_list()
            m = re.match(r'Heading(\d)', style or '', re.I)
            if m:
                lvl = min(int(m.group(1)) + 1, 5)
                parts.append('<h%d>%s</h%d>' % (lvl, inner, lvl))
            elif style and 'title' in style.lower():
                parts.append('<h1>' + inner + '</h1>')
            else:
                parts.append('<p>' + inner + '</p>')
        elif tag == W + 'tbl':
            close_list()
            rows = []
            for tr in el.findall(W + 'tr'):
                cells = []
                for tc in tr.findall(W + 'tc'):
                    txt = ' '.join(runs_to_html(p) for p in tc.findall(W + 'p')).strip()
                    cells.append('<td>' + txt + '</td>')
                rows.append('<tr>' + ''.join(cells) + '</tr>')
            if rows:
                parts.append('<div class="tw"><table>' + ''.join(rows) + '</table></div>')
    close_list()

    return """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title><style>
:root{color-scheme:light dark;--ink:#1B2420;--muted:#57635D;--paper:#FAFBFA;--line:#C6CFCA}
@media (prefers-color-scheme:dark){:root{--ink:#E5EBE7;--muted:#98A59F;--paper:#141B18;--line:#33403A}}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.65 Georgia,"Times New Roman",serif;padding:2rem 1rem 4rem}
main{max-width:46rem;margin:0 auto}
h1{font-size:1.5rem;line-height:1.25} h2{font-size:1.2rem} h3{font-size:1.05rem}
p{margin:.85rem 0} ul{margin:.6rem 0 .6rem 1.2rem} li{margin:.3rem 0}
.tw{overflow-x:auto;margin:1rem 0}
table{border-collapse:collapse;min-width:100%%}
td{border:1px solid var(--line);padding:.4rem .6rem;vertical-align:top;font-size:.95rem}
.src{color:var(--muted);font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
  border-bottom:1px solid var(--line);padding-bottom:.6rem;margin-bottom:1.4rem}
</style></head><body><main>
<p class="src">Text extracted from %s — original Word formatting and embedded images are not reproduced.</p>
%s
</main></body></html>""" % (html.escape(title), html.escape(title), '\n'.join(parts))


if __name__ == '__main__':
    src, dest, title = sys.argv[1], sys.argv[2], sys.argv[3]
    out = convert(src, title)
    open(dest, 'w', encoding='utf-8').write(out)
    print('%s -> %s (%d bytes)' % (title, dest, len(out)))
