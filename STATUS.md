# Status — as of 2026-09-23 (end of session)

Read `PRD.md` first for why this project exists and the platform rules that must not be re-litigated (iframe/link constraints, classification rule, redaction policy). This file is "what's true right now" — rewritten this session to replace a stale 2026-09-17 version. If you're starting a fresh session after a context clear, read this file, then `research/litigation-status-2026-09-21.md` (case facts), in that order, before touching anything.

## Live URLs

| What | URL | Version at last publish |
|---|---|---|
| Public case site | https://claude.ai/artifact/JbT43rhsCqEtpDkoF3E1WF | **36** (2026-09-23) |
| Email index QA viewer (redacted, public) | https://claude.ai/artifact/2LuiMSfwGFiSKaa414wMQb | 8 (untouched this session) |

`site/index.html` in this repo is kept byte-identical to the live artifact after every publish this session — safe to treat the repo copy as current, but **always re-`Artifact action:"read"` the live URL before your first edit of a new session anyway**, in case something changed outside this repo's lineage (this exact thing happened once earlier in the project's history — see git log `bbdd21b`).

## What the site now contains (11 sections, in nav order)

1. **Brief** — case summary narrative (5 subsections)
2. **Decided & Open** — scorecard of resolved/unresolved issues
3. **Timeline** — litigation dispute chronology (`TL` array, 33 entries after tonight)
4. **People** — 18 bios (`PEOPLE` array), each linking into filtered Record search
5. **Questions** — "Outstanding Questions": 18 Q&A cards, case questions + Matt's own, each tagged answered/disputed/still-open with a source line
6. **Neighborhoods** — HOA formation timeline + the "who pays what" SVG diagram + the ownership-vs-cost-sharing explanation callout
7. **Costs** — new this session: a 29-row table (`<table class="costtable">`) of every dollar figure found in the case, by category, with payer and status
8. **Geography** — real street addresses + Google Maps links + an 18-term legal/real-estate glossary, both with click-to-expand "More detail"
9. **The Record** — searchable email/filing database (`R`/`GROUP`/`PERS`), with content-type/filer/response/person/topic filters
10. **Documents** (`#library`) — full document library (`LIB` array), Drive-linked where possible
11. **Press**

## Technical architecture — read this before editing `site/index.html` again

The page has **three `<script>` tags**, executed in this order, sharing one global scope (classic scripts, not modules — `let`/`const`/`function` declared in one are visible to the others):

- **script_0** (~1.18 MB): defines `R` (the Record array, ~83 entries), `GROUP`/`PERS`, `TOPICS`, `ALIAS`, and — **a dead, superseded `render()` function plus chip/scope UI wiring that has no matching HTML anymore.** It runs harmlessly (its `querySelectorAll` calls just return empty NodeLists) but if you go looking for "the render function," don't stop at the first one you find in source order — it's not the one that runs. Also contains orphaned CSS-adjacent dead code: the `.tcard`/`.tgrid`/"information web" topic-cards feature was fully styled but never built into HTML; harmless, never cleaned up, still there.
- **script_1** (~6 KB): the **real, active** `render()` for the Record section, plus `FILEMETA` (filer/response tags for the 28 filing-type records, added this session), the `R.forEach` enrichment loop (`_docs`, `_email`, `_hay`, `_tp`, `_filingSub`, `_filer`, `_resp`).
- **script_2** (~21 KB): `LIB`/`PEOPLE` arrays, `renderLib()`, `renderTimeline()`, `EX_TO_DRIVE`/`driveLinkHtml()` (Drive-link fix for the iOS interception bug — 53 mapped EX/R ids), the dropdown-filter event wiring, `setupCollapsible()` (every `main > section` collapses on load; a link into `#record` etc. auto-expands its target via each section's own `.__toggle(true)` method it attaches to itself).

**Consequence for Playwright verification:** every section is collapsed by default. Before asserting on content inside a section, call `document.getElementById(id).__toggle(true)` in `page.evaluate`, or nothing you're checking exists in the DOM yet as far as visible/interactive state goes (it's in the DOM, just hidden — `hidden` attribute on `.sec-body`).

## The safe-edit workflow (validated repeatedly this session — follow it exactly)

1. `Artifact action:"read"` the live URL. Note the saved file path in the tool result — that's your base, not any local file you remember from earlier in the conversation.
2. Copy that file into the scratchpad (`cp <saved-path> .../scratchpad/site_vNN.html`) and edit it there with **Python scripts using exact string `.replace()` with an `assert count==1` guard** — the file is ~3.2 MB on a handful of enormous single lines; the `Edit` tool's line-based matching is not practical here, and blind multi-match replaces are how you silently corrupt three things at once.
3. Verify, in order, before ever publishing:
   - `grep -c '<section id=' file | ` vs `grep -c '</section>'` — must match.
   - Extract every non-JSON `<script>` body and run `node --check` on each. **Two real bugs this session were caught exactly here**: (a) injecting `<a href="...">` into an already-double-quoted JS string without escaping the inner quotes as `\"` (broke `script_0.js` parsing); (b) an apostrophe inside a single-quoted Python string while *writing* the edit script itself (Python-level, caught before it ever touched the HTML).
   - Playwright: load the file, expand any sections you're testing, assert on real DOM state (element counts, computed `href`s, filter behavior), capture `pageerror`/`console` listeners, and — for anything visual (SVG diagrams, tables, new layout) — take a screenshot and actually look at it. A wide `<table>` or `<svg>` should sit inside `.figwrap` (`overflow-x:auto`); confirm with `body.scrollWidth === body.clientWidth` that the *page* never overflows, only the inner wrapper (checked explicitly this session for the Costs table).
4. Publish: `Artifact action:"publish"` with the **same `url`**, `file_path` pointing at your verified scratchpad file, a `label` under 60 characters.
5. Immediately `cp` that same file over `site/index.html` in the repo, `git add`/`commit`/`push` to `claude/dam-lawsuit-research-brief-uxry1u`. Never let the repo and the live artifact drift — this session kept them byte-identical after every single publish (v30 through v36).

## Reusable patterns established this session

- **Drive-link fix for "opens the Claude artifact, not the file"**: `EX_TO_DRIVE` id→URL map + `driveLinkHtml(id, label)` in script_2, called first by any code that would otherwise render a `doclink`/`sharebtn`. Extend this map (don't build a second mechanism) if more documents get Drive copies.
- **Google Maps links, no API key needed**: single pin — `https://www.google.com/maps/search/?api=1&query=<urlencoded address>`; multiple pins in one view — `https://www.google.com/maps/dir/<addr1>/<addr2>/.../` (kept to ~9 waypoints; untested above that).
- **Click-to-expand, zero JS**: native `<details class="gmore"><summary>More detail</summary><div class="gmorebody">…</div></details>`, styled only via `.gmore summary::marker{color:...}`. Used for the Geography glossary (18 terms) and neighborhood rows (7). Prefer this over hand-rolled toggle JS for any future "show more" request.
- **Cost/data tables**: real `<table>` inside a `.figwrap` div for horizontal-scroll-on-mobile, category-header rows as `<tr class="cat-row"><th colspan="4">…</th></tr>`, status as a small pill (`<span class="cost-status paid|ongoing|pending|rejected|trial|historical">`).

## Known open items

1. **The Sept. 23, 2024 ownership ruling itself ("download (3).pdf") is still not in the archive.** It's a real attachment (Gmail thread `19224bab1069880d`, message `19224bab1069880d`, sender Mark Long) but at ~22 MB it's more than 3× the ~7 MB Gmail RAW-MIME transport ceiling (confirmed dropped again this session) and isn't sitting in Matt's Drive folder under any name searched so far. **Ask Matt to upload it to the shared Drive folder** (any filename) — then wire it in via the same `EX_TO_DRIVE` pattern rather than attempting Gmail recovery again.
2. **Two competing draft maintenance-fee models exist** (flat $12.23/mo vs. tiered $12.08 condo/$17.25 single-family) and it's not established in the record which one the receiver will actually file. Logged as an open question on the site; worth a fresh Gmail/Drive search if a definitive later document surfaces.
3. **Mullins Bros.' $20,000 court-costs deposit** (ordered Oct. 2024) has no confirmation of payment anywhere recovered — worth checking for a compliance filing if it ever matters.
4. The dead code in script_0 (old `render()`, chips/scope UI, `.tcard`/`.tgrid` information-web CSS) still hasn't been cleaned up. Low priority — it's inert — but flagging again since it was flagged once before (this file's prior version, 2026-09-17) and still hasn't been touched. If a future session has spare scope, removing it would shrink the file and reduce confusion for the next editor.
5. Standing instruction, still in effect: **do not attempt to send anything to emoyo@porterwright.com** (Elizabeth Moyo, Porter Wright) unless Matt explicitly asks again — he told a prior session to stop.

## Case-knowledge pointer

Every substantive case finding from this session (and prior ones) is in `research/litigation-status-2026-09-21.md`, appended chronologically with dated section headers and full sourcing (document names, thread IDs, exact quotes). It now runs ~290+ lines; a short index of section headers would help a fresh reader — worth adding if this file keeps growing. The single highest-value thing learned this session, if you only remember one: **ownership of the dam (narrow, court-ordered, ~68 Phase VII/VIII owners) and the ongoing maintenance assessment (broad, 245 properties, a never-litigated stormwater-basin utility-fee theory) rest on two different legal foundations that a July 2022 court order once tried to reconcile and then never did** — that single fact explains most of what looks contradictory about "who owes what" in this case.

## Repo layout (unchanged from PRD.md, repeated for convenience)

```
site/index.html             public case site — kept identical to the live artifact
site/docs/                  hosted exhibit/recovered files
research/litigation-status-2026-09-21.md   the case-research log — read this for facts
data/emails/*.json          complete, unredacted email database (349 messages)
email-index/                the separate email-index viewer product (see PRD.md)
PRD.md                      why this project exists, hard platform constraints
STATUS.md                   this file
```
