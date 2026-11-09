# Grecs du Roi — QA punch-list

**Task:** t_75006155  
**Page:** `http://127.0.0.1:8877/` (served from `/Volumes/RAID10/jon/Projects/grecs-du-roi/src`)  
**Date:** 2026-11-06  
**Browsers:** Chromium (Google Chrome channel) + Firefox (Playwright Nightly 1538)  
**Viewports:** 1440×900 desktop, 390×844 mobile  

Verdict: **no blockers**. The specimen page covers every ligature item on the Wikipedia *Greek ligatures* list, OpenType features are actually substituting, the stack is serif-only, and the page reads as parchment / revival print rather than a modern UI kit.

Evidence: `qa-evidence/` (grid, passages, hero, feature-toggle, mobile full).

---

## Method (what was actually checked)

1. Live page in Chromium and Firefox at desktop and mobile widths; full-page + clipped screenshots of hero, specimen grid, and sample passages.
2. 34 `.specimen` cards vs Wikipedia revision used by `ligature-catalog.md` plus a fresh fetch of `https://en.wikipedia.org/wiki/Greek_ligatures` image filenames.
3. Computed `font-feature-settings` on `body` / `.passage__quote` / `.specimen__glyph` = `"liga", "clig", "rlig", "dlig", "hlig"`. Toggle probe: same strings with features forced off; HarfBuzz on `grecs-roi-greek.otf` as an independent shaper.
4. Computed `font-family` chains; `document.fonts` (all 5 `@font-face` faces `loaded`); regex leak check for Inter / Roboto / system-ui / Helvetica / Arial / Neohellenic.
5. Visual tone from screenshots (not CSS comments).
6. Network: 22/22 specimen images 200; 5/5 woff2 200. First Chrome session logged a favicon 404; no other failed requests.

---

## Wikipedia list × specimen grid

Wikipedia named examples (7), Unicode ligatures (3), derived letters (4), minuscule charts (18 files), sidebar companions (digamma + koppa/sampi) = **34 items**. Grid has **34 cards**. None missing.

| Wikipedia item | Card | Large cell |
|---|---|---|
| εῖ | εῖ (-ei-) | live GSUB `ei.per` |
| γερ | γερ (-ger-) | Commons PNG; GSUB `liga_ger` in example/running text |
| καὶ | καὶ (kai) | live GSUB `kai` |
| μω | μω (-mō-) | Commons PNG; GSUB `liga_mo` in example line |
| ος | ος (-os) | live GSUB `omicronsigma` |
| οὖν | οὖν (oûn) | Commons PNG; GSUB `liga_oun` |
| φησὶ | φησὶ (phēsi) | Commons PNG; GSUB `liga_phesi` |
| ϛ / Ϛ | stigma | live cps (Didot paints small ϛ) |
| ϗ | kai symbol | live U+03D7 |
| Ϗ | kai capital | Gentium Plus unicode-range |
| Ȣ / ȣ | Latin OU | Cardo subset |
| Ꙋ / ꙋ | Cyrillic UK | Noto Serif subset |
| 18 minuscule charts | 18 Alphabet cards | Commons PNG thumbs (Pi has its own file; catalog row for Pi had a Phi typo, HTML is correct) |
| Ϝ, ϟ/Ϡ | digamma · koppa/sampi | live cps |

Not in the grid (article *illustrations*, not ligature cells): 1566 Aristotle print, Caslon type sample. Flagged as nit.

---

## Feature toggle (proof they fire)

HarfBuzz, `grecs-roi-greek.otf`, features on vs off:

| Input | ON | OFF |
|---|---|---|
| εῖ | `ei.per` | `epsilon,uni1FD6` |
| καὶ | `kai` | `kappa,alpha,uni1F76` |
| ος | `omicronsigma` | `omicron,uni03C2` |
| γερ | `liga_ger` | `gamma,epsilon,rho` |
| μω | `liga_mo` | `uni03BC,omega` |
| οὖν | `liga_oun` | `omicron,uni1F56,nu` |
| φησὶ | `liga_phesi` | `phi,eta,sigma,uni1F76` |
| ου | `ou` | `omicron,upsilon` |
| μέθοδος | `…,omicronsigma` | `…,omicron,uni03C2` |
| εἶναι | `ei.psilper,…` | `epsilon,uni1F36,…` |
| στ | `uni03DA` | `sigma,tau` |
| λλ | `lambdalambda` | `lambda,lambda` |

Chrome width probe (72px): ος / γερ / μω / οὖν / φησὶ / ου shrink when features are on (connected cuts). εῖ / καὶ *grow* on — the historical glyphs are wider than the separate letters, not a miss. Screenshots `chromium-toggle-on-off.png` and `firefox-toggle-on-off.png` show ON connected, OFF split in both browsers.

Greek passage clipboard text is ordinary polytonic NFC (`μῆνιν…`, `καὶ`, `φησὶ`, `οὖν`, `μέθοδός`); no PUA. Note: the passage spells **μέθοδός** (oxia on omicron, U+03CC) so the -ος ligature does **not** fire there — see minor 1a.

---

## Font stack / modern leak

Computed body / quote / glyph family:

` "GrecsRoi Greek", "GFS Didot", Cardo, "Gentium Plus", "Noto Serif", Georgia, "Times New Roman", serif `

Hero title uses Didot first (Latin display). `sansLeak` false in both browsers. GFS Neohellenic is commented out and not loaded. No Inter / Roboto / system-ui / Helvetica / Arial in any `font-family`.

---

## Tone

Parchment ground, iron-gall ink, rubric labels, gilt rules. Running Greek is a Gazis-derived cursive revival with live ligatures (kai, -os, ou, ei), not Times/Gentium textbook polytonic and not a sans UI. It is **not** a facsimile of Estienne 1550 / Garamond Grecs du Roi metal; it is an honest 21st-century OFL revival on aged paper. That is a gap versus the parent epic, not a fail of this page’s ligature spec.

---

## Issues

### Blocker

None.

### Minor

1a. **Showcase -ος sequence is accented, so it never ligates.** Card example `θεός` and passage `μέθοδός` shape as `omicrontonos + uni03C2` with features on *or* off. Unaccented `μέθοδος` / `ος` correctly become `omicronsigma`. Wikipedia’s 1566 sample is specifically μέθοδος. **Fix:** use `μέθοδος` (and `θεος` or a word whose ο is unaccented) in the example line and the decree sentence, or add GSUB for `omicrontonos+sigma/ς`.

1. **Four named ligatures are raster in the large cell** (`γερ`, `μω`, `οὖν`, `φησὶ`). Wikipedia historical *form* is shown via Commons PNG; DevTools feature-off does not break those hero glyphs. Typed example lines and the Homer/decree passage *do* ligate via composite GSUB (`liga_ger` etc.), which are side-by-side CFF joins, not the Wikipedia cuts. Documented in README. **Fix:** keep PNG as a “historical form” inset; make the large cell the live GSUB string so toggle-off is visible on the card itself.

2. **Face mix inside the grid.** Live Gazis-derived cuts (εῖ, καὶ, ος) sit next to scanned minuscule charts and Gentium/Cardo/Noto fallbacks (Ϗ, Ȣ/ȣ, Ꙋ/ꙋ, Latin-looking Ϝ). No tofu, but the royal texture is not one face. **Fix:** subset a single display face for the Unicode fallbacks, or label fallback cards more loudly than the current note line.

3. **Running text ≠ 1541 Grecs du Roi.** Iliad 1.1–2 ligates, but the ductus is GFS Gazis, not Garamond’s royal Greek. Parent goal (selectable Estienne gospel page) is still open. **Fix:** out of scope for this specimen; track on t_b16a2c44.

4. **Firefox `gfs-didot.woff2` glyf bbox warnings** (many glyphs). Chrome is quiet. Subset artifacts; glyphs still paint. **Fix:** re-subset Didot with correct `glyf` bboxes (`fontTools` `ttLib` / `recalcBounds`).

5. **Copy claims a hover reveal that does not exist.** Intro: “Hover or tap a card to reveal the feature name and Unicode range.” Names/codes are always visible; hover only lifts the card and ORs `calt` which is still `"calt" 0`. **Fix:** drop the sentence, or implement a real reveal / set `--calt` to 1 if the face has alternates.

### Nit

6. **Wikipedia print samples omitted.** 1566 Aristotle and Caslon plates are on the article and on disk (`src/glyphs/Greek_print_1566_Aristotle.png`, `250px-Caslon_Greek_type_sample.jpeg`) but unused. Optional comparison strip.

7. **Latin citation.** “Verba volant, scripta manent” is a proverb, not Seneca *Ep.* 9.13.

8. **Favicon 404** in Chromium (no `favicon.ico`). Harmless.

9. **Chart `<img alt="">` inside `aria-hidden` glyphs.** Decorative for AT; the card title still names the set. Fine unless charts are treated as content.

10. **Safari not instrumented.** Task asked Chromium + Firefox; both match. No WebKit screenshots this pass.

11. **Catalog vs grid count.** `ligature-catalog.md` acceptance table says 16 alphabetic SVGs; Wikipedia and the page have 18. Catalog Pi row points at the Phi SVG. HTML is the source of truth.

---

## Suggested follow-ups (do not block)

- Re-subset Didot to silence Firefox bbox warnings.
- Live GSUB in the four PNG hero cells.
- Optional Estienne/Caslon comparison strip for the parent epic.

---

## Evidence files

- `/Volumes/RAID10/jon/Projects/grecs-du-roi/qa-evidence/chromium-desktop-grid.png`
- `/Volumes/RAID10/jon/Projects/grecs-du-roi/qa-evidence/chromium-desktop-passages.png`
- `/Volumes/RAID10/jon/Projects/grecs-du-roi/qa-evidence/chromium-toggle-on-off.png`
- `/Volumes/RAID10/jon/Projects/grecs-du-roi/qa-evidence/chromium-desktop-hero.png`
- `/Volumes/RAID10/jon/Projects/grecs-du-roi/qa-evidence/chromium-mobile-full.png`
- `/Volumes/RAID10/jon/Projects/grecs-du-roi/qa-evidence/firefox-desktop-grid.png`
- `/Volumes/RAID10/jon/Projects/grecs-du-roi/qa-evidence/firefox-desktop-passages.png`
- `/Volumes/RAID10/jon/Projects/grecs-du-roi/qa-evidence/firefox-toggle-on-off.png`

---

## t_8e2d4b30 — Scanned marginalia & verse-order verification (2026-11-09)

**Scope:** Compare the scanned Estienne 1550 page (`qa-evidence/estienne-scan.jpg`)
against the corpus `corpus/john1_wh.json` — verse order, title, marginalia, endmark.

**Method:**
- Measured page geometry (main text 11–68% width; margin refs 74–80%; page edge >92%).
- Cropped the right-margin column at 5× scale (`qa-evidence/crops/margin_full.png`)
  and transcribed all 19 parallel-reference lines.
- Cropped the running title, decorated initial, and l.i. endmark for verification.
- Confirmed single-column layout (no two-column reading-order ambiguity).

**Findings:**
1. **Verse order: OK.** Scan reads 1→19 top-to-bottom (left-margin numerals α…σ).
   Corpus has 19 verses in the same order. No missing verses, no reordering.
2. **Title: exact match.** Scan "ΤΟ ΚΑΤΑ ΙΩΑΝΝΗΝ ΑΓΙΟΝ ΕΥΑΓΓΕΛΙΟΝ" = corpus title.
3. **Marginalia: gap.** Scan carries 19 parallel references (Col 1:16, Matt 3:16,
   Rev 2:4, Luke 3:16, Eph 1:11, 2 Ammonian markers, Matt 1:17, Luke 2:4,
   Matt 17:16, 2 Pet 1:4, 1 Cor 11:7, 1 Cor 5:4, etc.). Corpus marginalia array
   is empty. Two lines flagged [unclear] (siglums "E'ερ", "Κερκ") — do not
   commit to corpus until confirmed against a second source.
4. **Endmark: gap.** Scan has l.i. ligature at bottom center; corpus schema has
   no endmark field.

**Evidence:**
- `qa-evidence/scanned-marginalia.md` — full transcription + comparison
- `qa-evidence/crops/margin_full.png` — clean 5× crop of the right margin
- `qa-evidence/crops/title.png`, `initial.png`, `endmark.png` — page furniture
- `qa-evidence/crops/mr1..4.png` — band-by-band marginalia strips

**Open items for follow-up (not blocking this task):**
- Decide whether to add the 19 marginalia to the corpus schema (would require
  a schema change — new field `marginalia: [{book, chapter, verse, raw}]`).
- Confirm the two [unclear] siglums against a digital Estienne 1550 or a
  second physical copy.
- Add an `endmark` field to the corpus to capture the l.i. ligature.

---

## t_c33604f9 — Phase 2.0 target corpus + fusion-coverage rig (2026-11-09)

**Corpus (verbatim Perseus canonical-greekLit, NFC):**
- `corpus/iliad_a1_117.json` — Il. A 1–117 (Murray 1924), 117 lines
- `corpus/hymn_delos_callimachus.json` — Callimachus Hymn 4 (Delos), 326 lines
- `corpus/dem_18_psephisma.json` — Demosthenes 18 §§29/118/164/165: genuine
  Athenian decree texts quoted verbatim with full ψήφισμα protocol
  (ἐπὶ ἄρχοντος… φυλῆς πρυτανευούσης… δεδόχθαι τῇ βουλῇ καὶ τῷ δήμῳ)
- `corpus/john1_wh.json` — unchanged (WH John 1)

**Rig:** `tools/fusion-coverage.py` rewritten on real HarfBuzz shaping
(uharfbuzz + fontTools; the old GSUB-string matcher under-counted). Measures
adjacent-pair % and word-% touched by a LIVE ligature (features on vs. off),
gate sequences γερ/μω/οὐ/φησὶ, and nomina letters, per font →
`src/fonts/coverage.json`. **Measured baseline: grecs-roi-greek 9.0% pairs /
32.6% words** (old string-match numbers were 4.6%/22% — both below the
≥60% gate; the gap is Phase 2.2's worklist, and `top_fusions` in
coverage.json ranks what to draw first: ος, ει, ου, στ, εί, λλ, οῦ…).

**Nomina sacra:** `qa-evidence/nomina-sacra.md` — fol. 161 attests the
overlined ΘΣ-form of θεός only (v.18 confirmed twice; v.1–2 probable),
everything else on the page printed in full; full Stephanus set listed as
design reference for Phase 2.3.

**Browsers:** `tools/qa_three_browser.py` — Chromium+Firefox+WebKit(Playwright
engine) PASS incl. same-Unicode copy invariant + two-tier NFC copy-diff
(skeleton empty now; strict-byte pending on vv.1,2,17,18 = drop-cap + nomina
display forms, Phase 2.4 target). **Real Safari: needs the one-time human
step** `sudo /usr/bin/safaridriver --enable` (password prompt cannot be
answered headless), then `/usr/bin/safaridriver -p 55555` in background;
the harness auto-detects and runs it (selenium already installed).

