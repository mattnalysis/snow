# Knox Cattle Dam Case Archive — Product Requirements

## Background

Matt Snow (matthew.m.snow@gmail.com) is a defendant homeowner in *State of Ohio ex rel. Yost v. The Landings Property Association, Inc., et al. / Mullins Bros., Ltd. v. Didinger*, Knox County (Ohio) Court of Common Pleas, Case No. 20IN06-0149 — the "Knox Cattle Company Dam" litigation. He is one of roughly 70 Phase VII/VIII lot owners jointly defending, represented (until Sept. 2026) by Eastman & Smith. This repo is the working archive for that defense: a public case-tracking site for the owner group, and a private, structured index of the underlying email record.

## Goals

1. **A public, no-login case-tracking website** the ~70-owner litigation group can use to understand the case: timeline, current legal posture, every non-personal email and document, searchable.
2. **A private, durable, structured database of case correspondence** — not just a curated summary — that can be queried, audited, and built on independent of any single polished front end.
3. Both deliverables must **never expose personal 1:1 correspondence** or other owners' private data (e.g., HOA roster with names/addresses) to the public.

## Product 1: Public case site

**Live at:** https://claude.ai/artifact/JbT43rhsCqEtpDkoF3E1WF (Claude Artifact, single HTML file + hosted PDF/HTML exhibits)
**Source of truth in this repo:** `site/index.html` + `site/docs/`

### Requirements established over the course of this project
- Merge what were originally separate "Record," "Exhibits," "Document Index," and "Document Library" sections into one coherent, collapsible, searchable page — repeated user feedback converged on: **one Documents section**, full-text search across names/descriptions/extracted text, and a card layout (not a spreadsheet grid).
- Real hosted files, not just links to Gmail threads. Every exhibit gets a stable `EX-###` id.
- Every document/email needs a plain-English summary — a reader shouldn't have to open a filing to know what it says.
- No personal correspondence, ever, in the public site. A message is "personal" if it wasn't broadcast to the litigation group (see Classification rule, below).
- Timeline includes forward-looking deadlines/gates (status conferences, the Dec 31, 2026 ARPA spend-down deadline, open trial issues), not just past events, visually distinguished (amber "Upcoming/Deadline" markers).
- People Involved section with bios and a live link into filtered search.
- Filtering: dropdowns for content type (Email/Filing subtype/Report/News), Person, Topic — not pill buttons.

### Hard platform constraints discovered (do not re-litigate these)
- **Artifacts render inside a sandboxed iframe.** On the user's actual device (iPad, Chrome), `target="_blank"` and `target="_top"` links both silently do nothing — confirmed by direct testing, not theory. Any link to an external, non-hosted origin (Gmail threads, court portal, news articles) **cannot be made to reliably open** from inside the page. The only reliable mitigation is showing the raw URL as visible, selectable text with instructions to copy it into the browser's own address bar.
- **A PDF embedded in an `<iframe>` renders as a single static page on iOS Safari/WebKit** — it does not paginate, and the sandbox blocks any page-initiated download (`<a download>`, blob/data URLs, script-driven saves are all inert). The fix that works: **plain links to the hosted file, plus its full URL shown for copy/paste**, so the browser opens the PDF at top level (where it paginates and the OS's own share sheet offers Download / Open in App). Do not reintroduce an iframe PDF viewer.
- Hosted document filenames get silently truncated by the Artifact platform at some byte length; the truncation can land mid-extension (e.g. `.pd` instead of `.pdf`). **Any time a "document won't open" bug is reported, first diff the dataset's referenced filenames against `list_files` output** — this exact bug recurred and cost real time each time it wasn't checked first.

## Product 2: Email/document database

**Public QA viewer (redacted):** https://claude.ai/artifact/2LuiMSfwGFiSKaa414wMQb
**Source of truth in this repo:** `data/emails/*.json` (complete, unredacted — five files by year, ~349 messages), `email-index/index.full.html` (complete viewer, not published), `email-index/index.public.html` (redacted viewer, currently live).

### Requirements
- Index **every case-related email**, not just the ~76 previously hand-curated for the public site — a fresh, broad Gmail sweep, not a re-derivation of the known set.
- Per message: threadId, messageId, date, from, to[], cc[], subject, full body text, attachment metadata (filename/mimeType/size).
- **Classification rule (approved, applies everywhere in this project):** a message broadcast to 3+ total recipients (to+cc, excluding sender) is `"group"` and indexed in full; a message with fewer than 3 is `"personal"` and stored as a stub only — threadId/messageId/date/from/to/cc/subject, with `bodyText: null` and `attachments: []`. Personal content is never stored beyond the stub, in any dataset derived from this one.
- Data lives durably in this git repo (not only inside an Artifact's embedded JSON) specifically so it can be inspected, diffed, and rebuilt independent of any one published page.
- A minimal test/QA view is a legitimate deliverable in its own right, not just a means to an end — it must let a human independently verify the pipeline actually captured real data (field-by-field row inspection, integrity checks, coverage-by-year visualization that makes *gaps* visible).
- Where a redacted public copy is needed (see below), the redaction must be real: records removed from the published file's embedded data, not merely filtered out of the UI. Verify by grepping the published source for excluded message IDs/body text/filenames — don't trust the UI.

### Redaction policy (as of the current live public viewer)
The user asked to remove **personal messages and invoice/receipt-related messages** from the public copy. Both are gone from `email-index/index.public.html`'s embedded data and from its hosted `files` (33 now-orphaned invoice PDFs were unpublished, not just unlinked). The **complete, unredacted dataset remains in `data/emails/*.json`** and in `email-index/index.full.html` (local reference copy, never published). Any future redaction pass should follow the same pattern: strip from the embedded JSON, unpublish orphaned hosted files, verify with `scripts/verify_redaction.py`.

### Known limitation: attachment bytes
No Gmail MCP tool exposes attachment content directly. The workaround — `get_message` with `messageFormat: "RAW"`, which returns full MIME with attachments inline as base64 — works but has a **hard transport ceiling around 7 MB**; larger messages drop the connection outright ("Gmail session expired"), regardless of backoff/retry. See STATUS.md for exactly what is and isn't recovered as of the last session.

## Non-goals / explicitly deferred
- Attachment content for messages whose RAW MIME exceeds the ~7 MB transport ceiling — needs a different retrieval method (see STATUS.md "Mullins Exhibit Downloader" note) or manual download by the user.
- Any file over ~15 MB cannot be hosted on the Artifact platform regardless of how it's retrieved (both Mullins deposition volumes and the Mullins bank records fall in this category).
- Full-text search over invoice *amounts* — the invoice emails themselves don't contain dollar figures in the body (Eastman & Smith's covering notes say "see page two of the attachment"); only the hosted PDF carries the real numbers, and PDF text isn't currently OCR'd into the email database.
