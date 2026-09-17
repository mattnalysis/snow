# Status — as of 2026-09-17

> **Invoice material was stripped from the public case site and the live artifact republished** (Version 24) — see "Redaction — public case site" below.

Read `PRD.md` first for why this exists and the rules that must not be re-litigated (iframe/link constraints, classification rule, redaction policy). This file is "what's true right now."

## Live URLs

| What | URL | Version at last publish |
|---|---|---|
| Public case site | https://claude.ai/artifact/JbT43rhsCqEtpDkoF3E1WF | 24 |
| Email index QA viewer (redacted, public) | https://claude.ai/artifact/2LuiMSfwGFiSKaa414wMQb | 7 |

Both are published from files now committed in this repo (`site/index.html`, `email-index/index.public.html`), so they can be re-published in one `Artifact` publish call with `url:` set to the link above — no need to rebuild from scratch.

**Live had drifted from the repo before Version 24.** Version 22 was *not* this repo's `site/index.html`: it was an earlier build that had already dropped `EX-170` and the two invoice attachment records from its data (while still hosting the invoice PDFs), and that never got the "Retainer replenishment demanded" record. Publishing the redacted repo copy as Version 24 made live match the repo again, which also put `EX-170` (the receiver's fee application, whose PDF was hosted all along) and that retainer record on the public site. Worth re-checking `list_files` and a `read` before assuming live matches the repo — it did not this time.

## Repo layout

```
data/emails/*.json          complete, unredacted email database — 349 messages, source of truth
site/index.html             public case site source (published as Version 22 above)
site/docs/                  106 hosted files shared by both artifacts (53 EX-* originals + 53 R-* recovered)
email-index/index.public.html   redacted viewer, currently published (254 messages, 76 files)
email-index/index.full.html     complete viewer, NEVER published — local reference / audit copy only
email-index/recovered-manifest.json   provenance for the 61 recovered attachments (messageId → saved file)
scripts/                    the working pipeline: classification, docx→html conversion, redaction, verification
```

## Email database — complete

349 messages across 166 threads, all five year-buckets present and pushed:

| Bucket | Messages | Group | Personal |
|---|---|---|---|
| pre-2023 | 25 | 23 | 2 |
| 2023 | 99 | 84 | 15 |
| 2024 | 113 | 87 | 26 |
| 2025 | 73 | 65 | 8 |
| 2026 | 39 | 34 | 5 |
| **Total** | **349** | **293** | **56** |

Integrity verified: all 10 schema fields present on every record, no personal record carries body/attachment content, no duplicate message IDs within or across files. 152 attachments catalogued (metadata); 586,233 characters of body text.

**Caveat on completeness:** discovery was a keyword sweep (`"Knox Cattle" OR "The Landings" OR Mullins OR "20IN06" OR Chappelear OR "Eastman & Smith" OR receiver OR ARPA OR Wetzel OR Kimbler OR ...`, see `scripts/build_worklist.py` for the exact query). ~250 of the ~440 candidate threads it surfaced were newsletter/e-commerce false positives, filtered by sender/content inspection. A genuine case email from an unusual sender using none of this vocabulary could in principle be missed. Re-running discovery periodically (new mail keeps arriving — Eastman & Smith's withdrawal was Sept. 2026) is worth doing rather than treating this as permanently closed.

## Document hosting

- **106 files**, staged in `site/docs/` and hosted by both artifacts (was 108 — the two invoice PDFs were deleted in the case-site redaction below).
- **Names differ between here and the artifacts.** `site/docs/` uses short ids (`EX-257.pdf`); the artifacts host, and both pages' data point at, the long descriptive names (`docs/EX-257 Entry granting Motion for Leave to Withdraw as Counsel.pdf`). Republishing the whole `docs/` directory from this repo would rename every hosted file and break every document link — publish `index.html` alone unless you deliberately rebuild the file map. `scripts/stage_local_site.py` reconstructs the published names for local testing.
- 53 are the original case exhibits (`EX-006.pdf` … `EX-258.pdf`), matched against the `data/emails` records by (threadId, filename) — the mapping lives inline in both HTML files as `attmap` (email-index) and `libdata` (site).
- 53 (`R-001` … `R-053`) were recovered this session via the RAW-MIME technique below. Three are `.docx` sources the platform won't serve directly — `R-001/002/003.html` — rendered to readable HTML by `scripts/docx2html.py` because **LibreOffice is broken in this container** (fails `--convert-to pdf` even on a minimal valid docx with a simple filename; don't waste time on it again, use the script).
- **The public email-index viewer hosts only 76 of these** — 33 invoice PDFs were deliberately unpublished as part of its redaction (see below). The case site hosts 53.

### Attachment recovery — how, and where it stopped
No Gmail tool exposes attachment bytes directly. Working method: `mcp__Gmail__get_message` with `messageFormat: "RAW"` returns full MIME; attachments are inline base64. Decode (`base64.urlsafe_b64decode`, padded) and parse with `email.message_from_bytes(...)`. Scripted in `scripts/extract.py`.

- **Confirmed hard ceiling: ~7 MB.** Every message at or above that size drops the Gmail MCP connection ("session expired"), consistently, across repeated attempts with 90s/180s backoff. This is a transport limit, not rate limiting — retrying the same way won't help.
- 61 attachments recovered this way (manifest in `email-index/recovered-manifest.json`).
- **Confirmed unrecoverable by any method (exceed the ~15 MB Artifact hosting cap regardless):**
  - Mullins Documents, 2 PDFs — message ~40.5 MB
  - Steve Mullins 10-10-23 transcript (zip) — message ~20.4 MB
  - Steve Mullins Vol II 11-29-23 (PDF) — message ~20.3 MB
  - These need the user's own manual download from Gmail, and would need to live in Google Drive with a link from the archive (not hosted on the Artifact) since they're over the size cap even once downloaded.
- **Unresolved, worth another look:** 5 messages, 7–15.8 MB, holding ~13 legal PDFs/DOCXs that are individually probably under the hosting cap but sit above the RAW-MIME transport ceiling — currently unreachable by any method tried. Not attempted: the `download_exhibits.py` script sitting in the user's Google Drive folder "Mullins Exhibit Downloader" (created by the user, not this session) — never inspected or run. Worth asking the user about before the next attempt.

## Attachments section and the file hand-off (case site)

Reported: "I can only open the first page of the pdf." Cause is the platform constraint in `PRD.md` — a document link navigated the page itself, and a PDF inside the artifact's sandboxed frame renders as one static, unscrollable page. Fixed by never navigating to the file:

- New **Attachments** section (`#attachments`, linked from the nav): the 53 hosted files as a plain list — filename, kind, date, size, a name filter, and nothing else.
- A tap on any document anywhere on the page (Attachments, Document Library, the timeline's "Related documents") runs one hand-off: fetch the file → `navigator.share({files})` → system share sheet. Falls through to sharing the URL, then `window.open`, then revealing the file's full address with an explanation, if the sandbox refuses a step. The links stay real `<a href>`s so long-press still gives iPadOS's own Download / Share menu.
- `scripts/test_handoff.js` drives all of that with `navigator.share` stubbed three ways and asserts the page never navigates to the PDF. Run it against a local copy staged by `scripts/stage_local_site.py` (needed because `site/docs/` uses short names while the page asks for the published long ones — see Document hosting below).
- Corrected stale copy while in there: the library said "55 of 76 files" (now 53 of 74) and "15 of those by OCR" (10, computed from the page's own data), and two paragraphs still described an in-page viewer that no longer exists.

## Redaction — public case site (`site/index.html`)

User asked to remove the invoice email and invoice details from the case site. Done by `scripts/strip_invoices_site.py`, verified by `scripts/verify_site_invoices.py`:

- 3 records removed from `exdata` (258 → 255): `EX-221` (the June 2026 "Invoice" covering email), `EX-222` and `EX-232` (the two Eastman & Smith invoice PDFs, each carrying a named client's address plus invoice/client/matter numbers).
- 2 documents removed from the library (76 → 74) and their extracted text removed from `DOCTEXT` (56 → 54). `site/docs/` is down to 106 files; the site hosts 53 of them.
- `EX-170` (the receiver's First Interim Application of Fees and Costs) was **reclassified** `invoice` → `filing` rather than removed — it is a court filing, not a bill to the owners, and the money classifier has always treated it that way.
- The aggregated "Eastman & Smith invoices & retainer demands — the full billing series" record is gone, along with the now-unused `billing` record type.
- Billing detail quoted inside messages that stay was scrubbed in place: the `$595.29` invoice balance, the check-mailing/credit-card payment block, the LawPay link and the client/matter numbers, replaced with a visible "[Payment instructions and billing account details removed from the public archive.]" marker. The retainer facts the case narrative depends on (the $800 demand, its Sept. 25 deadline, that the invoice depleted the retainer) are kept.
- UI: the "Invoices" filter chip, the `invoice` kind label, the `invoice` topic keyword and the timeline's cross-reference to `EX-222` are all gone, so nothing renders empty.
- Checked by rendering the page headless (Playwright/Chromium): no JS errors, 83 records, "74 of 74 documents", no empty "Related documents" blocks.
- **Published as Version 24**, and the two invoice PDFs (`docs/EX-222 4044933.pdf`, `docs/EX-232 Inv. 4058433.pdf`) were removed from the artifact's hosted files — they had stayed reachable by direct URL even after an earlier build stopped linking them. The artifact hosts 54 files now. Re-downloaded the published `index.html` afterwards and grepped it: none of the invoice ids, invoice numbers, the balance, the payment link or the account numbers survive in it.

**Still outstanding on the other public artifact:** `email-index/index.public.html` keeps the Sept. 2026 retainer thread (correctly — `retainer` was never the redaction target), and that thread's body text still contains the `$595.29` balance, the LawPay payment link and client #3472 / matter #222027. If those should go too, it is the same scrub applied to that file's `emaildata`, plus the `595.29` entry in `moneytags`.

## Redaction (public email-index viewer only)

User asked to strip personal and invoice/receipt messages from the *public* copy. Done in `email-index/index.public.html`:
- 95 messages removed (56 personal + 39 invoice/receipt — all 9 LawPay receipts were already inside the personal set).
- 33 now-orphaned invoice PDFs unpublished from that artifact (not just unlinked — actually removed from the hosted file set).
- Verified by `scripts/verify_redaction.py` against the published source: zero removed message IDs, zero removed body-text fragments, zero invoice filenames, zero orphaned doc paths anywhere in the file.
- **`data/emails/*.json` and `email-index/index.full.html` are intentionally NOT redacted** — they are the complete private record. Never publish `index.full.html`.

## Money/invoice classification

`scripts/classify_money.py` — a scored classifier (LawPay sender → receipt; "retainer" in subject → retainer; "invoice"/"past due" in subject or numerically-named PDF attachment → invoice; "fees and costs" → fee application; else a dollar amount + strong body keyword → "discussion"). Deliberately not keyword-matching on words like "paid"/"check" — those appear throughout ordinary status-conference chatter and would swamp the filter. This classifier's output (`money_tags`) is embedded in both email-index viewers; it's gone from the public one except `retainer`/`fees`/`discussion` categories (invoices and receipts were the redaction target).

**Known gap:** invoice *amounts* are not in the email body text — Eastman & Smith's covering emails say "see balance on page two" of the attached PDF. The filter gets you to the right message/document; it does not currently extract the dollar figure itself.

## Known open items / next steps

1. **2023 was lost once already** to a session rate limit mid-run and had to be redone — if this database is regenerated from scratch in a future session, budget for that and write output incrementally (the retry did this; the original attempt did not).
2. **The 5 stuck 7–15.8 MB messages** (~13 documents) — try a different retrieval path, or ask the user whether their own `download_exhibits.py` (Google Drive, "Mullins Exhibit Downloader" folder) is meant to solve this.
3. **The three genuinely-too-large Mullins items** need the user to download manually and decide on Drive-linking rather than hosting.
4. Both artifacts' `site/docs` / hosted-file sets can drift from `site/docs/` in this repo if either is republished with a different `files` map elsewhere — this repo copy is the durable reference; reconcile with `list_files` on the live artifact before assuming they match.
5. Re-run the Gmail discovery sweep periodically — new case mail keeps arriving (counsel's withdrawal was Sept. 2026; a new-counsel search is actively underway per the case site's own timeline).
