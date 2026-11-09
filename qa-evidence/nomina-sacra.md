# Nomina sacra inventory — Estienne 1550, fol. 161 recto (John 1:1–19)

Extracted from `qa-evidence/estienne-scan.jpg` (812×1276 px scan of the
Wikimedia Stephanus 1550 folio) with 6–12× line and word crops under
`qa-evidence/crops/ns/` (montages `montage_A.png`/`montage_B.png`, word crops
`w_L03_*.png`, `w_L24_27.png`). Read with the `estienne-compare.html`
side-by-side harness open. All readings below state their evidence crop.

## Scan-attested on THIS folio (the only verified set)

| Form | Expansion (WH ref) | Evidence | Confidence |
|------|--------------------|----------|------------|
| **ΘΣ** overlined | θεός / θεόν / θεοῦ (God) — John 1:1 (×2), 1:2, 1:18 | `w_L24_27.png` (v.18 monogenes … εἰς ‹Θ overlined› κόλπον: two independent vision passes agree the mark is a single theta carrying a straight overline bar, not a full word), `w_L03_w03.png` (v.1b–1c: two-letter theta+sigma form with an abbreviation stroke above — the model described it as wavy at 12×, ambiguous vs. straight) | **high for v.18, medium for v.1–2** |
| *lowercase* | the overline sits on minuscule-height letters (not full capitals) in Estienne's italic | `body_3.png` pass: reads "θς"/"θῦ" in minuscule with a line over both letters | form = minuscule theta + lunate/final sigma + bar |

Everything else on this folio is printed **in full**:

- Theological names in vv. 1–19 other than the God-abbreviation —
  ἄνθρωπος (vv. 6, 9), φῶς, κόσμος, τέκνα θεοῦ (v. 12 — vision pass on the
  vv.12–13 band reports the genitive *not* overlined there), υἱός (v. 18),
  μονογενής (v. 18), πάτερ/πατρός (v. 18), Μωυσῆς/Μωυσέως (v. 17),
  Ἰησοῦ Χριστοῦ (v. 17) — all confirmed full minuscule, no overline, in the
  band/line passes (`body_1..3.png`, `montage_B.png`, `w_L24_27.png`).
- No ΠΝΑ, ΠΗΡ, ΑΝΩ, ΜΗ, ΔΑ, ΣΩ mark appears anywhere in the visible page
  text (consistent: none of those lemmas occur in John 1:1–19 at all).

**Note on ΚΣ/ΙΣ:** the WH-based corpus of this page (corpus/john1_wh.json
vv. 1–19) contains no κύριος and no standalone Ἰησοῦς; the Erasmus text
under the scan likewise shows Ἰησοῦ Χριστοῦ in full at v. 17. So **this
folio attests the God-form only**. Any ΚΣ/ΙΣ design target must come from
another folio of the 1550 (the Wikipedia ligature table and the commission
brief carry the wider list), not from this page.

## Full Stephanus-era system (design reference, NOT attested on fol. 161)

For the font's nomina-sacra mechanism (encode as letters + U+0305/U+0304,
fire via GSUB `liga`, copy-invariant), the Stephanus/Byzantine standard set
the type system should eventually carry:

    ΘΣ  θεός        ΘΥ  θεοῦ         ΚΣ  κύριος      ΙΣ  Ἰησοῦς
    ΧΣ  χριστός     ΠΝΑ πνεῦμα       ΠΗΡ πατήρ (ΠHR)  ΜΗΡ μήτηρ
    ΑΝΟ / ΑΝΩ / ΑΝΟΣ ἄνθρωπος        ΣΩ  σωτηρία     ΣΗΡ σωτήρ
    ΔΑ  Δαυίδ       ΗΣ / ΙΣ  εἶναι-forms ambiguous — keep ΙΣ = Ἰησοῦς

Each is displayed with a horizontal overline spanning exactly the abbreviated
letters; the underlying text stays the ordinary letters (+ combining macron),
so select-copy stays NFC-readable (already the build_estienne_page.py
mechanism: `Θ` + U+0304 + `Σ` + U+0304).

## Corpus frequency on the WH page text (for ligature payoff ranking)

From corpus/john1_wh.json vv. 1–19 (display words that WOULD abbreviate):
θεόν ×2, θεός/θεὸς ×2, θεοῦ ×2 (vv. 1,2,6,12,13,18), Ἰησοῦ + Χριστοῦ ×1 (v.17).
→ The God-nomen alone already covers the scan-attested requirement; fusing
its letter pair is the cheapest nomina-sacra win for Phase 2.2.

## Builder guidance (feeds t_8e2d4b30, not owned by t_c33604f9)

`tools/build_estienne_page.py` NOMINA currently = {θεόν, θεὸς, Θεοῦ, Χριστοῦ}.
Scan says: keep the God-words; **drop Χριστοῦ** (printed full on this folio,
v. 17) or keep it flagged as design-system-only; add θεοῦ (vv. 6,12,13).
Overline should span both letters; letters minuscule-height italic.

## Method caveats (honest uncertainty)

- Two vision passes over John 1:1 (w_L03_w03/w05) disagreed on whether the
  v.1/2 God-words are ΘΣ-abbreviated or full Θεόν — the 12× crops are at the
  limit of the source scan's resolution. The v.18 mark was read identically
  ("overlined theta, one letter, abbreviation bar") in two independent
  passes, so the folio attestation rests on v.18.
- The scanned page is the 1550 folio-image at 812 px width; the plan's
  "450–1600 dpi crops" would resolve the v.1 disagreement. A higher-res
  capture of fol. 161 (Wikimedia has a larger file) should be pulled before
  Phase 2.4's overlay gate; until then treat v.1–2 God-forms as *probable*
  nomina, v.18 as *confirmed*.
- Fusion coverage of these forms in the current GrecsRoi font: the letters
  Θ Σ exist in cmap (310 Greek codepoints); no overline-composite glyph yet;
  `fusion-coverage.py` reports nomina-letter availability per font.
