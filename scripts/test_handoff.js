/**
 * What happens when someone taps a document, under the three browsers that matter.
 *
 * The case site runs inside a sandboxed frame that will not paginate a PDF and
 * will not let the page download one, so a tap must hand the file to the device
 * instead of opening it here. This drives that hand-off with navigator.share
 * stubbed three ways — shares files, refuses files, refuses everything — and
 * asserts the page never navigates itself to the PDF.
 *
 *   python3 scripts/stage_local_site.py /tmp/sitetest
 *   npx http-server -p 8199 -s /tmp/sitetest
 *   node scripts/test_handoff.js [http://127.0.0.1:8199/index.html]
 */
let chromium;
try { ({ chromium } = require('playwright')); }
catch (e) { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }
const URL = process.argv[2] || 'http://127.0.0.1:8199/index.html';

async function newPage(browser, init) {
  const ctx = await browser.newContext();
  if (init) await ctx.addInitScript(init);
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  page.on('console', m => { if (m.type() === 'error' && !/CERT_AUTHORITY|favicon/.test(m.text())) errs.push(m.text()); });
  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForTimeout(400);
  await page.evaluate(() => { const s = document.getElementById('attachments'); if (s && s.__toggle) s.__toggle(true); });
  return { page, errs };
}
const firstShare = '#atRows li.arow:first-child button.sharebtn';

(async () => {
  const b = await chromium.launch();
  let fail = 0;
  const check = (name, ok, extra) => { console.log((ok ? 'PASS  ' : 'FAIL  ') + name + (extra ? '  ' + extra : '')); if (!ok) fail++; };

  // 1. iPad that can share files: expect navigator.share called with a real File, no navigation
  {
    const { page, errs } = await newPage(b, () => {
      window.__shared = [];
      navigator.canShare = d => !!(d && d.files && d.files.length);
      navigator.share = async d => {
        window.__shared.push({
          hasFiles: !!(d.files && d.files.length),
          name: d.files && d.files[0] && d.files[0].name,
          type: d.files && d.files[0] && d.files[0].type,
          size: d.files && d.files[0] && d.files[0].size,
        });
      };
      window.open = () => { window.__openCalled = true; return null; };
    });
    const before = page.url();
    await page.click(firstShare);
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => ({ shared: window.__shared, opened: !!window.__openCalled, url: location.href }));
    check('file share: navigator.share got the PDF as a File', r.shared.length === 1 && r.shared[0].hasFiles && r.shared[0].type === 'application/pdf' && r.shared[0].size > 1000, JSON.stringify(r.shared[0] || null));
    check('file share: page did not navigate', r.url === before);
    check('file share: no new-tab fallback fired', !r.opened);
    check('file share: no JS errors', errs.length === 0, errs.join('|'));
    await page.context().close();
  }

  // 2. share exists but refuses files: expect URL share, still no navigation
  {
    const { page } = await newPage(b, () => {
      window.__shared = [];
      navigator.canShare = () => false;
      navigator.share = async d => { window.__shared.push({ url: d.url, title: d.title }); };
      window.open = () => { window.__openCalled = true; return null; };
    });
    const before = page.url();
    await page.click(firstShare);
    await page.waitForTimeout(900);
    const r = await page.evaluate(() => ({ shared: window.__shared, opened: !!window.__openCalled, url: location.href }));
    check('link share: navigator.share got the file URL', r.shared.length === 1 && /\.pdf$/i.test(decodeURIComponent(r.shared[0].url || '')), JSON.stringify(r.shared[0] || null));
    check('link share: page did not navigate', r.url === before);
    await page.context().close();
  }

  // 3. everything blocked, as the artifact sandbox does: expect the address revealed, no navigation
  {
    const { page } = await newPage(b, () => {
      navigator.canShare = () => { throw new DOMException('blocked', 'NotAllowedError'); };
      navigator.share = async () => { throw new DOMException('blocked', 'NotAllowedError'); };
      window.open = () => null;
    });
    const before = page.url();
    await page.click(firstShare);
    await page.waitForTimeout(900);
    const r = await page.evaluate(() => {
      const row = document.querySelector('#atRows li.arow');
      const note = row.querySelector('.ublocked');
      const box = row.querySelector('.docurl');
      return {
        revealed: row.classList.contains('showurl'),
        note: note && note.textContent,
        urlVisible: box ? getComputedStyle(box).display !== 'none' : false,
        urlText: box && box.querySelector('.url').textContent,
        url: location.href,
      };
    });
    check('all blocked: address row revealed', r.revealed && r.urlVisible, r.urlText || '');
    check('all blocked: explains what to do', !!r.note && /Copy the address/.test(r.note + ''), (r.note || '').slice(0, 70) + '…');
    check('all blocked: page did not navigate', r.url === before);
    await page.context().close();
  }

  // 4. tapping the file NAME behaves the same as the button (no in-page navigation)
  {
    const { page } = await newPage(b, () => {
      window.__shared = [];
      navigator.canShare = d => !!(d && d.files && d.files.length);
      navigator.share = async d => { window.__shared.push(d.files[0].name); };
      window.open = () => null;
    });
    const before = page.url();
    await page.click('#atRows li.arow:first-child a.afile');
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => ({ shared: window.__shared, url: location.href }));
    check('file name tap: shared instead of navigating', r.shared.length === 1 && r.url === before, JSON.stringify(r.shared));
    await page.context().close();
  }

  // 5. same for a Document Library row and a timeline related-document link
  {
    const { page } = await newPage(b, () => {
      window.__shared = [];
      navigator.canShare = d => !!(d && d.files && d.files.length);
      navigator.share = async d => { window.__shared.push(d.files[0].name); };
      window.open = () => null;
    });
    await page.evaluate(() => { ['library','timeline'].forEach(id => { const s = document.getElementById(id); if (s && s.__toggle) s.__toggle(true); }); });
    const before = page.url();
    await page.click('#libRows a.doclink');
    await page.waitForTimeout(1200);
    await page.click('#tlList a.doclink');
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => ({ shared: window.__shared, url: location.href }));
    check('library + timeline links hand off too', r.shared.length === 2 && r.url === before, JSON.stringify(r.shared));
    await page.context().close();
  }

  await b.close();
  console.log(fail ? '\n' + fail + ' CHECK(S) FAILED' : '\nALL CHECKS PASSED');
  process.exit(fail ? 1 : 0);
})();
