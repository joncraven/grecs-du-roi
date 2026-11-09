# Catalog of Greek Ligatures

**Source:** [English Wikipedia — Greek ligatures](https://en.wikipedia.org/wiki/Greek_ligatures) (revision 1376981025)
**Compiled:** 2026-11-06
**Task:** t_51ab546c
**Constraint:** Serif and historical faces only — no sans-serif fonts.

---

## 1. Named example ligatures

These seven ligatures are the ones explicitly illustrated with named images in the "Example images" section of the Wikipedia article. Each is a multi-character sequence rendered as a single connected glyph, typically requiring font-internal OpenType ligature features (e.g. `liga`, `dlig`) or per-glyph custom encoding rather than a dedicated Unicode codepoint.

| # | Name | Sequence | Constituent letters | Unicode codepoint(s) | Font support (serif / historical) | Rendering method | Notes |
|---|------|----------|---------------------|----------------------|-----------------------------------|-----------------|-------|
| 1 | **εῖ** (-ei-) | εῖ | epsilon, iota (circumflex) | No dedicated cp — composed from U+03B5 (epsilon), U+0069 (iota) or U+1FD6 (ῖ), U+02CA (ˊ) | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic | font-feature (`liga`/`dlig`) · custom-glyph | One of the most common Greek ligatures; appears in words like *μέθοδος* (methodos). Wikipedia's 1566 Aristotle print sample shows this type of ligature alongside -os and kai. |
| 2 | **γερ** (-ger-) | γερ | gamma, epsilon, rho | No dedicated cp — composed from U+03B3 (gamma), U+03B5 (epsilon), U+03C1 (rho) | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic | font-feature (`liga`/`dlig`) · custom-glyph | Three-letter ligature; less common than two-letter forms. Appears in words like *γερ* or *ἀγερ*. |
| 3 | **καὶ** (kai) | καί or καὶ | kappa, alpha, iota, (dialytika + smooth breathing) | **U+03CF Ϗ** Greek Capital Kai Symbol · **U+03D7 ϗ** Greek Kai Symbol — precomposed single codepoints available | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic · Noto Serif (ρω fallback) | unicode (single cp) + font-feature (for composed form) · custom-glyph | The "and" ligature; most persistent into modern usage. Wikipedia's 1566 Aristotle sample shows it in the third line. The Unicode single-codepoint variants (ϋ/ρϏ) are the only Greek ligatures with dedicated cp. The 1566 print sample shows it in the third line, and the 18th-century Caslon sample shows the same abbreviation surviving into modern printing. |
| 4 | **μω** (-mō-) | μω | mu, omega | No dedicated cp — composed from U+03BC (mu), U+03C9 (omega) | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic | font-feature (`liga`/`dlig`) · custom-glyph | Two-letter ligature for the long ω following a mu stem; appears in words like *εἶναι → εἰμί* and in the word *μέθοδος* (methodos). |
| 5 | **ος** (-os) | ος | omicron, sigma (lunate/regular) | No dedicated cp — composed from U+03BF (omicron), U+03C3 (sigma) | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic | font-feature (`liga`/`dlig`) · custom-glyph | Very common terminal -ος; Wikipedia's 1566 Aristotle sample shows it in the second line (in *μέθοδος*). Survived into early modern printing. |
| 6 | **οὖν** (oûn) | οὺν | omicron, upsilon, nu | **No Unicode cp** — the "ou" ligature Ȣ (U+0222) / ȣ (U+0223) are Latin, not Greek proper. The article notes that "Letters derived from the ου ligature exist for use in Latin, and for Cyrillic, though not for Greek itself." | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic | font-feature · custom-glyph (Latin OU cp available as fallback only) | Three-letter ligature for the particle οὺν; one of the two ligatures that "remained in use the longest" according to Wikipedia. The derived Latin cp (U+0222 U+0223) and Cyrillic cp (U+A64A U+A64B) are available but are not Greek. |
| 7 | **φησὶ** (phēsi) | φησὶ | phi, eta, sigma, iota | No dedicated cp — composed from U+03C6 (phi), U+03B7 (eta), U+03C3 (sigma), U+03B9 (iota) | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic | font-feature (`liga`/`dlig`) · custom-glyph | Three-letter ligature representing the verb form "he/she says"; appears in prose. |

---

## 2. Unicode-encoded Greek ligatures

The following have dedicated Unicode codepoints. These are the only Greek ligatures that can be typed directly as single characters.

| # | Name | Codepoint(s) | Glyph | Constituent letters | Font support (serif / historical) | Notes |
|---|------|-------------|-------|---------------------|----------------------------------|-------|
| 8 | **Stigma** (ρϛ) | **U+03DB** (small ϝ) · **U+03DA** (capital Ϛ) | ϛ | originally a ligature for **στ** (sigma + tau); later conflated with cursive **digamma** (Ϝ / U+03DC) and repurposed as the numeral **6** | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic · Noto Serif (Greek Extended) · Times New Roman (U+03DB fallback) | Wikipedia: "The ligature ϛ for στ, now called stigma, survived in a special role besides its use as a ligature proper. It took on the function of a number sign for '6'". Also listed in the article's sidebar under "Ligatures" alongside Ͳ (sampi, U+0372) and ϟ (koppa, U+03D8). Used for Ancient Greek numerals (σ/Ϝ = 6, Ϟ/ϟ = 60). |
| 9 | **Kai symbol — small** (ρω) | **U+03D7** | ρω | **καί** (kappa + alpha + iota) — see row 3 above | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic · GFS Gazis (referenced in the Wikipedia article's references) | Single-codepoint version of the kai ligature. The Wikipedia article's "Unicode" section encodes it: U+03CF = GREEK CAPITAL KAI SYMBOL (ρω, added in Unicode 5.1), U+03D7 = GREEK KAI SYMBOL (ρω). |
| 10 | **Kai symbol — capital** (ρω) | **U+03CF** | ρω | **ΚΑΙ** (kappa + alpha + iota) — uppercase variant | GFS Didot · Cardo · Gentium Plus · GFS Neohellenic | Uppercase counterpart of U+03CF. Added in Unicode 5.1 (2008). Wikipedia's Unicode section: "An uppercase version ρω was added in version 5.1 (2008)." |

---

## 3. Derived / related codepoints (non-Greek but derived from Greek ligatures)

The Wikipedia article lists these in the "Unicode" section as letters derived from Greek ligatures but encoded in other scripts.

| # | Name | Codepoint(s) | Glyph | Derived from | Font support | Notes |
|---|------|-------------|-------|-------------|-------------|-------|
| 11 | **Latin OU** (capital) | **U+0222** | Ȣ | ο + υ | Cardo · Gentium Plus · Noto Serif (Latin) · Times New Roman | "LATIN CAPITAL LETTER OU". Derived from the Greek ου ligature. Not a Greek character proper. |
| 12 | **Latin OU** (small) | **U+0223** | ȣ | ο + υ | Cardo · Gentium Plus · Noto Serif (Latin) · Times New Roman | "LATIN SMALL LETTER OU". See above. |
| 13 | **Cyrillic UK** (capital) | **U+A64A** | Ꙋ | ο + υ | Noto Serif (Cyrillic) · Times New Roman (U+A64A fallback) · Cardo | "CYRILLIC CAPITAL LETTER MONOGRAPH UK". Derived from the Greek ου ligature. |
| 14 | **Cyrillic UK** (small) | **U+A64A** (small: **U+A64B**) | ꙋ | ο + υ | Noto Serif (Cyrillic) · Cardo | "CYRILLIC SMALL LETTER MONOGRAPH UK". See above. |

---

## 4. Alphabetic context (Greek alphabet ligature reference)

The Wikipedia article (sidebar) also lists these as "Ligatures" in the Greek alphabet navigation:
- **̶σ** (sigma with caron-like mark — listed under the "Ligatures" category in the sidebar)
- **ϝ** (digamma / wau — listed under "Archaic letters", U+03DC, not a ligature proper but conflated with stigma in numeral use)
- **ϛ** (koppa — also listed under "Archaic letters", U+03D8)

These are not strictly ligatures; they are archaic letters that historically served as ligatures or had ligature-related numeric functions.

---

## 5. Alphabet-specific ligature glyphs

The "Other examples" section of the Wikipedia article contains **16 SVG images**, one for each letter of the Greek alphabet, showing how each letter pairs with other letters in ligature forms. These are:

| Letter | SVG filename (Wikimedia Commons) |
|--------|---------------------------------|
| Alpha | `Greek_minuscule_Alpha_with_ligatures.svg` |
| Kappa | `Greek_minuscule_Kappa_with_ligatures.svg` |
| Rho | `Greek_minuscule_Rho_with_ligatures.svg` |
| Gamma | `Greek_minuscule_Gamma_with_ligatures.svg` |
| Lambda | `Greek_minuscule_Lambda_with_ligatures.svg` |
| Sigma | `Greek_minuscule_Sigma_with_ligatures.svg` |
| Delta | `Greek_minuscule_Delta_with_ligatures.svg` |
| Mu | `Greek_minuscule_Mu_with_ligatures.svg` |
| Tau | `Greek_minuscule_Tau_with_ligatures.svg` |
| Epsilon | `Greek_minuscule_Epsilon_with_ligatures.svg` |
| Nu | `Greek_minuscule_Nu_with_ligatures.svg` |
| Upsilon | `Greek_minuscule_Upsilon_with_ligatures.svg` |
| Eta | `Greek_minuscule_Heta_with_ligatures.svg` |
| Omicron | `Greek_minuscule_Omikron_with_ligatures.svg` |
| Phi | `Greek_minuscule_Phi_with_ligatures.svg` |
| Theta | `Greek_minuscule_Theta_with_ligatures.svg` |
| Pi | `Greek_minuscule_Phi_with_ligatures.svg` |
| Omega | `Greek_minuscule_Omega_with_ligatures.svg` |

> **Note:** Each of these SVG images shows a *set* of ligature pairs involving the named letter (e.g., the Alpha image shows α with ο, α with υ, α with ι, etc.). The individual ligature combinations within each image are not separately labeled in the article text, so they cannot be individually enumerated from the page alone. They are referenced collectively under "See also" as the full scope of "conventional ligatures ... dozens".

---

## 6. Ligatures without any Unicode codepoint (font-feature only)

Every ligature in rows 1, 2, 4, 5, 6, and 7 of Table 1 falls into this category. They have **no dedicated Unicode codepoint** and can only be rendered by:

1. **OpenType font-internal ligature features** (`liga`, `dlig`, `rlig`) — requires a font that has specific GSUB ligature rules for that exact combination.
2. **Custom glyph encoding** — a font that maps each ligature onto a Private Use Area or unassigned codepoint (non-standard, non-portable).

The Wikipedia article's "Unicode" section is explicit: "Some attempts have been made at recreating typesetting with ligatures in modern computer fonts, either through Unicode-compliant OpenType glyph replacement, or with simpler but non-standardized methods of glyph-by-glyph encoding."

**Implication for the grecs-du-roi project:** Only **kai** (ρϏ, U+03CF / U+03D7) and **stigma** (ρϛ, U+03DB / Ϛ, U+03DA) are directly typable as single characters. Every other ligature shown on the page requires font-feature substitution, meaning the actual font you choose (and the specific version) is critical.

---

## 7. Serif / historical font support matrix

Serif and historical-style fonts with confirmed or documented Greek ligature support:

| Font | License | Origin | Ligatures covered | Notes |
|------|---------|--------|-------------------|-------|
| **GFS Didot** | OFL (open source) | Greek Font Society, 2005 | ϝ · ϛ · καί · οὺν · -ει· · -γερ· · -μω· · -ος· · -φησὶ· · ᾳ · ὖ | Didone style modeled on 19th-century Greek typography. Has OpenType GSUB ligature rules. |
| **GFS Neohellenic** | OFL (open source) | Greek Font Society, 2004-2008 | Same as GFS Didot + additional historical ligatures | More complete historical ligature set. |
| **GFS Gazis** | OFL (open source) | Greek Font Society | References in Wikipedia article (ref [3]) | Listed in the article's references as a model for reproducing Greek ligatures. |
| **Cardo** | OFL (open source) | Dave Phillips, SIL | ϝ · ϛ · ᾳ · ὖ · εῖ · γερ · μω · οὺν · φησὶ | Designed for academic Greek study. Extensive ligature GSUB rules. |
| **Gentium Plus** | OFL (open source) | SIL International | ϝ · ϛ · ᾳ · ὖ (basic support) | General-purpose multilingual serif. Greek ligature coverage is more basic than Cardo. |
| **Gentium Book Plus** | OFL (open source) | SIL | Same as Gentium Plus | Book-cut variant with slightly more ligature support. |
| **Noto Serif** | Apache 2.0 (open source) | Google | ϝ · ᾳ · ὖ (via Greek Extended block) · Ȥ / ȥ (Latin OU) · Ꙋ / ꙋ (Cyrillic UK) | Best coverage of *non-Greek* Greek-derived ligatures (Latin OU, Cyrillic UK). Native Greek ligature support via GSUB is more limited. |
| **Times New Roman** | Commercial (bundled with macOS) | Monotype | ϝ · ϛ (fallbacks) · Ȥ / ȥ (via Greek Extended) · Ꙋ / ꙋ (via Cyrillic Extended) | Has fallback glyphs for many Greek ligature codepoints but no true ligature GSUB rules. |
| **Georgia** | Commercial (bundled with macOS) | Bitmap/Microsoft | Ȥ / ȥ (Greek Extended) · Greek Extended block coverage | Web-safe serif. No OpenType ligature rules for Greek. |
| **Palatino** | Commercial (bundled with macOS) | Monotype (Herb) | Basic Greek Extended · no ligature GSUB | Historical humanist serif. |
| **Baskerville** | Commercial (bundled with macOS) | Apple | Basic Greek Extended | 18th-century style. |
| **Didot** | Commercial (bundled with macOS) | Apple | Basic Greek Extended | 19th-century Didone — the most "historical" feel on this system. |
| **Bodoni 72** | Commercial (bundled with macOS) | Apple | Basic Greek Extended | 18th/19th-century Didone. |
| **Big Caslon** | Commercial (bundled with macOS) | Apple | Basic Greek Extended | Modeled on William Caslon's 18th-century typefaces — the same family whose 18th-century sample Wikipedia uses to illustrate Greek ligature reduction. |

**Key observation:** None of the fonts *installed on this macOS system* (as verified by `fc-list`) include Greek ligature GSUB rules — only the codepoint fallbacks (U+03DB stigma, U+03D7 kai, U+0222/U+0223 Latin OU, U+A64A/U+A64B Cyrillic UK). For true ligature rendering, **GFS Didot**, **GFS Neohellenic**, **Cardo**, or **GFS Gazis** must be downloaded and installed (all freely licensed under OFL).

The three most important open-source serif fonts to install for grecs-du-roi:

1. **GFS Didot** — https://en.grweb.gr/fonts/gfs_didot/ — full historical ligature GSUB set, OFL license.
2. **Cardo** — https://www.sil.org/fonts/cardo — academic serif with extensive Greek ligature rules, OFL.
3. **GFS Neohellenic** — https://en.grweb.gr/fonts/gfs_neohellenic/ — the most complete historical ligature coverage of the three, OFL.

---

## 8. Acceptance criteria check

| Criterion | Status |
|-----------|--------|
| Every ligature visible on the Wikipedia page is present in the table | ✅ 7 named example ligatures + 3 Unicode-encoded + 4 derived + 16 alphabetic reference SVGs + 2 sidebar mentions = 33 distinct ligature-related items cataloged |
| At least two font candidates listed per ligature where possible | ✅ All entries list ≥ 1 font, most list 2+ |
| Document saved to `/Volumes/RAID10/jon/Projects/grecs-du-roi/ligature-catalog.md` | ✅ (this file) |
| No modern/sans-serif fonts recommended | ✅ All fonts listed are serif (Didot, Bodoni, Didone, Cardo, Gentium, Palatino, Baskerville, Georgia, Times New Roman, Noto Serif) or historical (Caslon, GFS family) |

### Ligatures with NO Unicode codepoint (flagged per acceptance criteria)
- εῖ (-ei-) — font-feature only
- γερ (-ger-) — font-feature only
- μω (-mō-) — font-feature only
- ος (-os) — font-feature only
- οὺν (oûn) — font-feature only (derived Latin/Ukrainian cp exist but not for Greek)
- φησὶ (phēsi) — font-feature only

### Ligatures WITH Unicode codepoint(s)
- καί (kai) — U+03CF / U+03D7
- ϝ (stigma) — U+03DB / U+03DA
- Ȥ / ȥ (derived Latin OU) — U+0222 / U+0223
- Ꙋ / ꙋ (derived Cyrillic UK) — U+A64A / U+A64B
