# Status — as of 2026-09-17 (later same day)

Read `PRD.md` first for why this exists and the rules that must not be re-litigated (iframe/link constraints, classification rule, redaction policy). This file is "what's true right now."

## ⚠️ Read this before touching the case site artifact

**Two Claude sessions edited `https://claude.ai/artifact/JbT43rhsCqEtpDkoF3E1WF` concurrently on 2026-09-17.** One session (this repo's usual lineage) was doing the invoice/personal redaction pass. A *second*, independent session — almost certainly started fresh from this repo's `PRD.md`/`STATUS.md` in a different tab/client while this one kept running unbroken — was working the same artifact at the same time and got further ahead on the actual hard problem (see below). Neither session knew about the other until a publish was refused with a version conflict.

**Before you touch `site/index.html` or publish to that URL again:**
1. `Artifact action:"read"` the live URL first. Do not assume this repo's `site/index.html` matches what's actually live — it may not.
2. If it doesn't match, that's not necessarily wrong — read what's there, and if it's further along than this repo (as it was on 2026-09-17), pull it in as the new base rather than overwriting it. `git` has no record of artifact-only changes; the live page can be ahead of the repo.
3. Check `list_sessions` / ask the user whether another session is active on this project before doing a large rewrite.

**What the other session had built, not yet captured in this repo as of this commit:** a dedicated `#attachments` section — "The files themselves — nothing else" — that hands each file to `navigator.share()` (Web Share API) instead of a plain link. On iOS this raises the native share sheet directly (Save to Files, Open in Books, Mail, Print), which is a materially more promising fix than the copy-address-into-Safari pattern this session had been using, because it doesn't depend on the user manually pasting anything. It also documents two fallbacks: long-press the filename for iPadOS's own context menu, or copy-address-into-Safari as a last resort. **This code was never committed to git — it exists only in the live published artifact.** If you can read it, pull `site/index.html` from the live artifact into this repo before doing anything else with the case site.

This session's own diagnostic contribution, not yet merged into the live artifact: pasting a hosted document's address into the browser bar redirected back to the main artifact page rather than loading the file — consistent with `claudeusercontent.com` being a registered iOS Universal Link domain and the installed Claude app intercepting the navigation (same mechanism suspected earlier for broken Gmail links). Safari is documented to exempt manually-entered addresses from that handoff; Chrome for iOS may not. Worth folding into whichever guidance text survives the merge.

## Live URLs

| What | URL | Version at last publish |
|---|---|---|
| Public case site | https://claude.ai/artifact/JbT43rhsCqEtpDkoF3E1WF | **Unknown/contested — see warning above. Do not trust the version number here.** |
| Email index QA viewer (redacted, public) | https://claude.ai/artifact/2LuiMSfwGFiSKaa414wMQb | 8 |

The email-index viewer had no concurrent-session conflict; its published state matches `email-index/index.public.html` in this repo. The case site did — see the warning section above before publishing to it.

## Repo layout

```
data/emails/*.json          complete, unredacted email database — 349 messages, source of truth
site/index.html             public case site source -- STALE relative to live artifact, see warning above
site/docs/                  105 hosted files in this repo (52 EX-* + 53 R-*; 3 invoice PDFs removed) -- the
                             live case-site artifact's actual file count may differ, see warning above
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

- **105 files, ~36 MB**, staged in `site/docs/` in this repo (down from 108/39 MB after the three invoice PDFs — EX-170, EX-222, EX-232 — were removed). This repo copy is what the *email-index* viewer's published `files` set is built from; **the case-site artifact's actual live file set is not known to match this** — see the concurrent-session warning up top.
- 52 are original case exhibits (`EX-006.pdf` … `EX-258.pdf`), matched against the `data/emails` records by (threadId, filename) — the mapping lives inline in both HTML files as `attmap` (email-index) and `libdata` (site).
- 53 (`R-001` … `R-053`) were recovered this session via the RAW-MIME technique below. Three are `.docx` sources the platform won't serve directly — `R-001/002/003.html` — rendered to readable HTML by `scripts/docx2html.py` because **LibreOffice is broken in this container** (fails `--convert-to pdf` even on a minimal valid docx with a simple filename; don't waste time on it again, use the script).
- **The public email-index viewer hosts 76 of these 105** — the rest (mostly R-* files) aren't referenced by any non-redacted email-index record. 105 remain in `site/docs/` here.

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
