# Grecs du Roi — Phase 2 Project Plan

**Task:** t_b16a2c44 · **Date:** 2026-11-06 · **Author:** spark
**Status:** APPROVED (D1=C now, B later if needed; D2=John 1 page — human sign-off recorded §3).
**Progress (2026-11-09):** Phase 2.4 v1 built early so the user can compare
against the scan now: `src/estienne-john1.html` + `src/estienne-compare.html`
(WH text, current Gazis-derivative font, scan-overlay harness). Collation and
the cursive font remain.

---

## 1. Where we are (and why it falls short)

Built so far (`/Volumes/RAID10/jon/Projects/grecs-du-roi/`):

- `ligature-catalog.md` — all 33–34 items from https://en.wikipedia.org/wiki/Greek_ligatures cataloged.
- `src/` specimen page — 34 cards, `GrecsRoi Greek` (OFL derivative of GFS Gazis) with 43 GSUB ligatures under DFLT/grek/latn, explicit `liga/clig/rlig/dlig/hlig`.
- QA (`review-punchlist.md`) — zero blockers *against the ligature-catalog spec*, and that is exactly the problem: the spec it passed was "show the Wikipedia ligatures", not "look like the grecs du roi".

Measured gap (t_a8519b7b experiment, not opinion):

| Dimension | Target (Estienne 1550 / fig-171) | Current build |
|---|---|---|
| Ductus | cursive minuscule, true slanted joins | upright Gazis Didone revival |
| Fusion density | most letter pairs fused | top-4 sequences = 4.6% of pairs / 22% of words (Il. A 1–21, `coverage.py`) |
| Contextual alternates | heavy (letter shape by position) | none |
| Abbreviations / nomina sacra (Θ̅ς, Κ̅ς, Π̅να) | everywhere | none |
| Four named ligatures (γερ μω οὖν φησὶ) | live type | Commons **PNGs** in the hero cells |
| Page recreation (John 1 page, headpiece, decorated initial, verse numbers, marginalia) | the goal | not attempted |

**Conclusion accepted by the user:** GSUB tricks over upright Didone outlines cannot reach the look. Phase 2 = a genuine cursive revival typeface + a real Estienne-page recreation.

## 2. Hard constraints (unchanged from Phase 1, all re-verified 2026-11-06)

1. **Same-Unicode invariant.** The DOM holds ordinary NFC polytonic Greek (U+1F00–1FFF). Selection/copy must yield normal polytonic text — no PUA codepoints, no images of text. Ligatures live in GSUB lookups only.
2. **License.** Everything shipped on a public site must be OFL-compatible or public domain. Re-verified this pass:
   - All four known digital revivals unusable as-is: Jalleau/Imprimerie nationale (proprietary), Anagrafi KS-GrequeX (commercial, web-embedding license required), Strockis "Grecs du roi WG" (ligature-less, download dead), Douros Anaktoria (PUA-only — **violates constraint 1 by construction**).
   - `https://upload.wikimedia.org/wikipedia/commons/5/58/Gospel_Estienne_1550.jpg` — **Public domain** (Commons API `LicenseShortName: Public domain`, verified today). The 1550 typeface itself is 475 years out of copyright; only *digital derivations* by others carry rights.
   - GitHub search `"grecs du roi"` repositories: **total_count = 0** (verified today). No existing free revival to fork.
   - Old Standard TT (OFL, has a true −15° italic): fontTools-verified — its only GSUB ligatures are `fi`/`fl` + diacritic builds; **zero Greek letter ligatures**. Confirms free fonts alone cannot get there.
3. **Rendering.** Chromium, Firefox, Safari desktop via `font-feature-settings`/`font-variant-ligatures`; HarfBuzz as oracle shaper. `safaridriver` exists on this machine (`/usr/bin/safaridriver`) — Safari instrumentation is possible for the first time (needs `safaridriver --enable` once).

## 3. Strategy decision

**D1 — how to obtain the cursive typeface (the crux):**

| Option | What | Cost | Fidelity | Risk |
|---|---|---|---|---|
| **A. Commission a revival** (type designer draws ~600–900 glyphs + ~150 ligatures from the scans) | true grecs-du-roi outlines | market rate ≈ €8k–25k, 3–6 months calendar; commissioning/rounds = the bottleneck, not agent-hours | highest | low; standard practice (GFS Gazis itself is such a commission) |
| **B. Agent-assisted tracing revival** — cut glyph exemplars from the PD 1550 scan at high dpi, auto-vectorize (potrace/vtracer) + manual clean-up passes in fontForge/Glyphs, assemble in FontTool | we build it ourselves | ~2–4 agent-weeks first pass; realistically 500–1500 hrs of skilled clean-up for publishable quality | medium-high; scan quality varies (ink spread, page curvature), auto-traced joins look "crunchy" | high effort-sink; needs strong human-art direction; outlines from print ≠ consistent ductus |
| **C. Stylized composite** — extend the existing Gazis derivative: true slant masters (not sheared composites — redraw slanted), ~150 hand-drawn fused ligatures covering **≥60% of word-pairs**, contextual alternates (`calt`) for σ/ρ/letter-position forms, nomina-sacra via `liga`+combining macron | "grecs-du-roi-flavoured cursive revival", honestly labeled | ~1–2 agent-weeks per feature-set; no cash | medium — closest we can *ship* now; will not fool a paleographer | the fused-ligature coverage is a grind; previous experiment showed 22% coverage is easy, 60% is the real work |

**Recommendation: C now, A as a parallel tracked option.** C is incremental on working infrastructure (the OFL derivation + feaLib build + toggle harness + coverage metric all transfer, per t_a8519b7b Q2), produces a shippable site within weeks, and the same acceptance harness then scores a future commissioned font with zero rework. B is not recommended as primary — auto-tracing a 1550 impression produces inconsistent ductus and burns months; it is only worth a spike (§6 Phase-2.0) if we decide fidelity-per-dollar must beat C.

==> Human-approved decision: C now, we can potentially work from C to B gradually later only to the extent required to reach the look/quality we want (if C is "good enough", we stop there).

**D2 — page scope:** recreate the John 1 page (`Gospel_Estienne_1550.jpg`, PD) as the flagship, then generalize the layout into the reading-site template (greek.craven.fr-style, sibling of latin.craven.fr).

==> Human-approved decision: Agreed

## 4. Work breakdown (Option C path; cards to create)

### Phase 2.0 — Target corpus & measurement rig (2–3 days)
- Digitize the target: transcribe the John 1:1–18 Estienne page (polytonic NFC; text base: Westcott-Hort/Scrivener PD, collated against the scan at 450–1600 dpi crops — the latin-audiobooks OCR-repair workflow applies).
- Corpus of representative runs (John 1, Il. A 1–117, a decree) → extend `coverage.py` into **`fusion-coverage.py`**: % of adjacent pairs and % of words touched by an active ligature, per font. Baselines: current GrecsRoi 22% words; **gate for Phase 2: ≥60% of words, γερ/μω/οὖν/φησὶ live (no PNG), nomina sacra firing.**
- Named-entity (nomina sacra) inventory extracted from the scan: ΘΣ ΚΣ ΙΣ ΠΝΑ ΠΗΡ ΑΝΘ ΩΝ ΟΥΝ ΟΣ ΔΑ ΜΗΤ ΙΗΛ … with their exact overline forms.
- Safari harness: enable `safaridriver`, extend existing Playwright matrix → Chromium+Firefox+Safari screenshots as CI gate (closes the standing "Safari not instrumented" caveat).

### Phase 2.1 — Slanted cursive masters (1–2 weeks)
- **STATUS (2026-11-09, t_480a0018): DONE.** Separate face
  `src/fonts/grecs-roi-greek-cursive.otf/.woff2` (upright derivative ships
  unchanged). Builder `tools/cursive_masters.py` (wired into
  `build_typography.py`), assertions `tools/qa_cursive.py` (26/26 PASS:
  HB on/off per alternate, liga regression, zero tofu over 4262 corpus
  words, 0-PUA cmap, true-master shear audit, upright-mark audit),
  side-by-side `src/cursive-compare.html` + `qa-evidence/cursive-compare-*.png`.
  feaLib pitfall recorded: rules bind to the CURRENT script block only —
  register named lookups explicitly per script (DFLT/grek/latn).
  Cursive face closes the U+02BC keraia + lunate-sigma cmap gaps upstream;
  Phase 2.2 draws its fused ligatures on these masters.
- Redraw the 431-symbol Gazis-derivative Greek set slanted as true masters (interpolation helper: slant existing outlines → redraw joins/opticals; no `faux-italic` shears in the shipped font).
- Positional alternates: final-medial-initial σ, lunate σ, ρ with descender variants, ε/θ cursive variants — registered as `calt`/`locl` under `grek`.
- Verification: HarfBuzz on/off + side-by-side against scan crops at 200% zoom; tofu = zero.

### Phase 2.2 — Ligature engine v2: ≥60% fusion (2–3 weeks, the grind)
- **STATUS (2026-11-10, t_a130c5fc): DONE.** Builder
  `tools/ligature_engine.py` (wired into `build_typography.py` after
  `cursive_masters.py`): corpus word frequency → greedy set-cover over
  uncovered word *instances* (candidates len 2–4 inside letter runs) →
  fused glyph = slanted part masters composed with an 18% join overlap,
  accents riding their own slot → ONE feaLib rebuild (upstream 43 liga
  rules + 165 corpus-ranked fusions + punch-list 1a + oun accent variants,
  longest-first inside LIGA; `@L` extended with ligature glyphs so calt
  position alternates see through joins). HarfBuzz asserts every ligature
  fuses inside a real corpus carrier and disappears with features off
  (0/165 failures). Measured: **words 97.3% / pairs 37.4%** (gate ≥60%,
  baseline 32.6%) — `src/fonts/coverage.json`. Manifest
  `src/fonts/grecs-roi-greek-cursive.ligatures.json`.
  - Four hero cells (γερ μω οὖν φησὶ) now LIVE fused text in
    `src/index.html`; the Commons PNGs are demoted to reference links.
    The oὖν cell needed new 3-letter rules for *every* precomposed
    upsilon accent (only two forms existed upstream).
  - Punch-list minor 1a FIXED: `omicronsigma.tonos` / `omicronsigma.varia`
    fuse ό+ς, ὸ+ς (σ and ς forms), accent contour lifted from the
    accented master; asserted in `qa_cursive.py`.
  - **WebKit/Safari toggle fix:** the upstream derivative registers liga
    under `rlig` too, and CSS `rlig` cannot be switched off — WebKit
    (strict, unlike Chromium/Firefox which allowed forcing) showed the
    fusions permanently. The cursive face ships **without the rlig
    registration** (liga+clig+dlig+hlig is the honest tag set for
    historical fusions). New gate `tools/qa_fusion_toggle.py`: per-probe
    A/B width shrink (fused ⇒ strictly shorter) in Chromium+Firefox+
    WebKit + hero-cell no-img check + PUA copy check — 3/3 PASS. Real
    Safari remains the standing human gate (`sudo safaridriver --enable`).
  - feaLib pitfall learned: `calt`/`locl` context class `@L` must include
    ligature TARGET glyphs, or positional alternates stop seeing through
    fused pairs (`sub @L sigma'` dies after a preceding fused pair).
- Rank candidate pairs/triplets by frequency in the corpus (top ~150 sequences cover the coverage gate — compute, don't guess).
- Draw fused ligatures in order of coverage yield; each one goes through: outline → GSUB injection (feaLib, `liga`+`dlig`) → HarfBuzz assertion → coverage-metric bump recorded in `coverage.json`.
- Real historical forms for γερ/μω/οὖν/φησὶ replace the PNG cells (PNGs stay as "historical reference" insets — punch-list minor 1).
- Fix punch-list minor 1a: `-ος` ligature must fire after accented ο (add `omicrontonos+ς` lookups or use unaccented examples correctly).
- Exit criterion = fusion-coverage gate (§Phase 2.0) + feature-toggle test green in all three browsers.

### Phase 2.3 — Abbreviations & apparatus (3–5 days)
- Nomina sacra: encode as normal letters + U+0304 combining macron, drawn as `liga`-triggered precomposed glyphs (Θ̅ς → one glyph); keeps the copy invariant (paste yields the letters).
- Estienne punctuation (· comma, ·, ··), section numbers, enlarged initial Ε as live glyph (decorated initial via SVG inset for the *ornament*, letter itself live text).

### Phase 2.4 — Estienne page recreation (1 week)
- HTML page mirroring the scan: woodcut headpiece (drawn SVG), running head + folio, two-tier layout — main column + right marginalia (parallel references), verse numbers in the margin, decorated initial.
- **Overlay QA:** page the scan at 50% opacity behind the HTML column; acceptance = line-breaks and letter positions within ±½ line across the page (proves the recreation, not just vibes).
- Same-Unicode check: select-all → paste → NFC-diff against the source transcription must be empty.

### Phase 2.5 — Site integration (1–2 weeks)
- Turn the template into the reading site (sibling of latin.craven.fr deploy path — `scripts/deploy.sh` from main, per project memory).
- Toggle: "grecs du roi" ⇄ "modern polytonic (Cardo)" on the *same* Unicode text.
- Specimen page updates: replace the four PNG hero cells with live GSUB (punch-list minors 1, 2, 5), re-subset Didot to silence Firefox bbox warnings (minor 4).

> **DONE (2026-11-10, t_1bdfa688).** Reading site = `src/estienne-john1.html` with a
> face radiogroup (grecs du roi ⇄ modern polytonic/Cardo); the toggle changes only the
> CSS font stack — `tools/qa_reader_toggle.py` proves text byte-identity, Cardo
> full-cmap coverage, no PUA, zero bbox warnings in chromium+firefox+webkit.
> Minor 4 closed (`tools/fix_font_bboxes.py`, 154 glyphs; Firefox console 0 warnings).
> Minor 5 closed (hover-reveal claim removed). Public repo: github.com/joncraven/grecs-du-roi
> (build pipeline + `tools/license_manifest.py --check` in CI, all OFL).
> Deployed to grecs.craven.fr via `deploy/deploy.sh` (main-only, static tree, marked
> Caddy block, web01 mount via `deploy/ensure-mount.sh`); verified live with
> `tools/qa_live_site.py` (toggle, fonts, copy, hero cells all pass against the server).
> **Outstanding human step:** add OVH A record `grecs.craven.fr → 91.99.62.203`, then
> `./deploy/enable-tls.sh` flips to HTTPS (`curl -sfL https://grecs.craven.fr/`).

### Phase 2.6 — Commission track (parallel, unblocks on D1=A later)
- Keep the commissioned-revival brief from `docs/grec-du-roi-answer.md` warm: RFQ text, candidate designers (Greek type community: e.g. type designers behind GFS/AIOLE releases), quote collection. When a real font arrives, it drops into the same build/verification harness with the same acceptance gate.

## 5. Definition of done (the whole epic)

1. Page renders the full Wikipedia ligature set **live** (zero PNG ligature cells) in Chromium+Firefox+Safari.
2. Fusion coverage ≥60% of words in the corpus, reported by `fusion-coverage.py` (target: match the density visible in the 1550 page).
3. John 1 page recreation passes the ±½-line scan-overlay test.
4. Select-copy-paste = ordinary NFC polytonic Greek (automated NFC-diff test in CI).
5. Every shipped glyph OFL/PD; license manifest regenerated by `tools/build_typography.py`.

==> Human addition: shipped glyphs and related development added to a github repository for others to use / contribute

## 6. Spiked / parked

- **Option-B spike (1 day):** vtracer-trace a 1200 dpi letter exemplar set from the scan; if joins/ductus survive at 200%, revisit B. Expected to fail; cheap to prove.
- Anagrafi KS-GrequeX web license quote (would be the fastest honest path to the true forms *if* paid licensing is acceptable — currently ruled out by the free-site constraint, revisit only if user relaxes it).

## 7. Risks

- **Coverage grind (highest):** drawing 150 good fused ligatures is iterative art, not scripting. Mitigate: frequency-ranked queue, per-ligature verification, stop at gate.
- Slanted redrawing degrading diacritic placement on polytonic (accents + breathings + iota subscript stacking). Mitigate: marks as separate GPOS anchor pass after masters settle.
- Safari GSUB quirks (Safari historically ignores `content-z`/complex shaping for some scripts). Mitigate: Safari is now in the CI matrix from day 1 (2.0).
- Scope creep into full-site typography before the font gate passes. Mitigate: 2.5 blocked until 2.2 gate is green.

## 8. Effort summary

| Phase | Agent-work | Wall-clock |
|---|---|---|
| 2.0 corpus + rig | 2–3 d | 2–3 d |
| 2.1 slant masters | 1–2 wk | 1–2 wk |
| 2.2 ligature engine v2 | 2–3 wk | 2–3 wk |
| 2.3 abbreviations | 3–5 d | 3–5 d |
| 2.4 page recreation | 1 wk | 1 wk |
| 2.5 site integration | 1–2 wk | 1–2 wk |
| **Total (Option C)** | **~6–10 weeks** | |
| Option A instead of 2.1–2.2 | + cash (€8k–25k) | 3–6 months |

Plan authored in-workspace at
`/Volumes/RAID10/jon/Projects/grecs-du-roi/docs/phase2-plan.md`.
