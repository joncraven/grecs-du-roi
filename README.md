# Grecs du Roi — typography engine

Ligature CSS, webfonts, and specimen page for the catalog in `ligature-catalog.md`.
Open `src/index.html` in Chromium, Firefox, or Safari (desktop).

## Estienne 1550 page (Phase 2.4, v1)

- `src/estienne-john1.html` — recreation of the folio-161 John 1 page
  (`qa-evidence/estienne-scan.jpg`, Public domain). Folio number, drawn SVG
  headpiece, centered title, rubric drop-cap Ε, left-margin verse numbers,
  right-margin parallel references, nomina sacra (ΘΣ̅ / ΧΣ̅ as real letters +
  combining macron, toggleable). Text = Westcott-Hort John 1 (`corpus/john1_wh.json`,
  PD, extracted from Perseus canonical-greekLit). Fully live NFC polytonic
  Unicode: select → copy → normal polytonic Greek (QA: 0 PUA chars, verified
  Chromium + Firefox via `tools/qa_estienne_page.py`).
- `src/estienne-compare.html` — side-by-side + draggable/scalable opacity
  overlay of the render against the scan for the ±½-line line-break check.
- Rebuild: `python3 tools/build_estienne_page.py` then `python3 tools/render_estienne_overlay.py`.
- Line-by-line scan collation and the cursive font (Phase 2.1–2.2) are open;
  see `docs/phase2-plan.md`.

## Font stack (serif only)

| Face | Role | unicode-range |
|------|------|----------------|
| **GrecsRoi Greek** | Greek running text + OpenType ligatures | U+0370–03FF, U+1F00–1FFF |
| **GFS Didot** | Latin display; polytonic fallback; small stigma | Latin + Greek |
| **Cardo** | Latin OU Ȣ/ȣ (U+0222/U+0223) | those two cps |
| **Gentium Plus** | capital kai Ϗ (U+03CF) | U+03CF |
| **Noto Serif** | Cyrillic UK Ꙋ/ꙋ (U+A64A/U+A64B) | those two cps |
| Georgia → Times New Roman → `serif` | last-resort system serifs | — |

GFS Neohellenic is **not** loaded. It is a sans-serif cut; including it would violate the no-modern-sans rule.

`font-display: block` so a webfont miss does not flash a UI sans. `font-feature-settings` for `liga`, `clig`, `rlig`, `dlig`, and `hlig` are set on `body` (not left to browser defaults).

GrecsRoi Greek is an OFL **derivative** of GFS Gazis (reserved name not reused). Upstream Gazis registered `liga` only under script `latn`, so Greek letters would not ligate in a browser. The derivative registers the same lookup under `DFLT`, `grek`, and `latn`, and adds `clig`/`rlig`/`dlig`/`hlig` feature tags.

Rebuild fonts: `python3 tools/build_typography.py`

## Ligatures that render as true GSUB glyphs (GFS Gazis)

Typed as normal polytonic Greek; copy/paste yields the letters, not PUA.

- **εῖ** ε + ῖ → `ei.per`
- **ει** and the other ε+ι breathing/accent variants
- **καὶ / και / καί** κ+α+ι → `kai` (also precomposed U+03D7)
- **ος / ος-final** ο+σ and ο+ς → `omicronsigma`
- **ου** and accented ου (including οῦ, οὐ, …)
- **λλ**, **υι**
- **στ** → stigma Ϛ

## Gaps (no historical ligature glyph in the free fonts)

These six catalog items have **no Unicode codepoint**. Of them, only εῖ / καὶ / ος exist as real connected cuts in GFS Gazis.

| Ligature | Why it cannot use a historical font glyph | Workaround on the page |
|----------|-------------------------------------------|-------------------------|
| **γερ** | No GSUB ligature in GFS Didot, Cardo, Gentium, or Gazis | Wikimedia PNG in the cell; discretionary composite γ+ε+ρ in the derivative font |
| **μω** | Same | Wikimedia PNG; composite μ+ω |
| **οὖν** | Same; Latin ȣ / Cyrillic ꙋ are **not** Greek | Wikimedia PNG; composite ο+ὖ+ν |
| **φησὶ** | Same | Wikimedia PNG; composite φ+η+σ+ὶ |
| **16 alphabetic charts** | Each SVG is a *set* of pairs, not one ligature, and they are unlabelled in the article | 250px Wikimedia thumbs in the grid (SVG originals were rate-limited; PNG thumbs are the documented Commons rendition) |
| **GFS Didot / Cardo / Gentium “full historical GSUB”** | Inspected: Didot `liga` is only Latin fi/fl; Cardo/Gentium have no Greek letter ligatures | Gazis derivative used instead |

Small stigma **ϛ U+03DB** is absent from Gazis; GFS Didot paints it via unicode-range. Capital kai **Ϗ U+03CF** is absent from Gazis; Gentium Plus paints it.

## Copy behaviour

The Homer / decree passage is ordinary NFC polytonic Unicode (`μῆνιν ἄειδε…`, `καὶ`, `φησὶ`, `οὖν`, `μέθοδος`). Selecting it and pasting into a text editor must not produce Private Use Area codepoints.

## Licences

OFL copies sit in `src/fonts/`. Wikimedia charts are CC BY-SA (filename preserved under `src/glyphs/`).
