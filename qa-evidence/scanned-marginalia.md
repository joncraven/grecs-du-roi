# Scanned marginalia — Estienne 1550, John 1 (fol. 161) — REVISED 2026-11-09 (run 2)

> **Correction log.** The run-1 version of this file (t_c33604f9-era) was
> produced from the 812-px-wide task scan at too-low resolution and contained
> fabrications and misreads. Specifically:
> - Line 54 claimed the first body line begins **«Νῆν λιῦ ὁ λόγος καὶ ὁ λόγος λιῦ»**.
>   That string exists nowhere in the scan. **The actual first line** (verified
>   on both the task scan and a 300-dpi second source at 2.2–5×) is
>   **«Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν»** — the Ε is the decorated initial.
> - Run-1 marginalia lines 2–5, 16, 17, 18 misread several verse digits (Λ for Α)
>   and line 14's siglum (Κερκ — actually Κσφ). Reviewer corrections confirmed.
>
> Run 2 re-read every marginal line individually at 8–16×, and — decisively —
> against a **second source**: a 300-dpi page image of an actual Editio Regia
> 1550 volume (archive.org item `TextusReceptusEditioRegia1550`, the fol. 161
> spread; identical page impression). Crops committed under
> `qa-evidence/crops/secondsource/` (per-line F01–F19, capstack, endmark, body).
> Contested final capitals were additionally checked by pixel-band forensics
> (Α = crossbar present at mid-height; Λ = none).
>
> The machine-readable truth is now **`corpus/john1_estienne1550.json`**
> (per-verse `notes` column + marginalia with per-line confidence). This file
> is the human-readable digest; where they differ, the JSON wins.

## Reference lines, top → bottom (scan column = 19 lines; alignment = verse)

| # | Scan (verbatim glyphs) | = Reference | Aligns v | Confidence |
|---|------------------------|-------------|----------|------------|
| 1 | Κολοσ. α´. Γ´ | Col 1:3 (τὰ πάντα δι᾽ αὐτοῦ) | 1 | high |
| 2 | Ματθ. γ´. Α´ | Matt 3:1 (ἔρχεται Ἰωάννης) | 6 | high |
| 3 | [unclear siglum]. α´. [?]´ | — | 7 | low: siglum μδρ/ρδρ across passes; 300-dpi shows inkblot over the verse digit |
| 4 | Λκ. γ´. Α´ | Luke 3:1 | 7 | high |
| 5 | [unclear siglum]. θ´. Α´ | — | 8 | low: siglum Κ?φ unstable (Κεφ/Κσφ) |
| 6 | ζ´. ιβ´. Ε´. Η´ | **Ammonian section** 12, canon table E–H | 8 | medium |
| 7 | Ε´ἐρ. ιβ´. Λ´ | [unclear] | 10 | low (kept from run 1, reviewer-endorsed) |
| 8 | Ματθ. α´. Γ´ | Matt 1:3 | 12 | high |
| 9 | Λκ. β´. Δ´ | Luke 2:4 | 13 | high |
| 10 | Ματθ. ιζ´. Λ´ | Matt 17:2 (transfiguration) | 14 | medium: final digit Α/Λ contested |
| 11 | β´. πε. α´. Δ´ | 2 Pet 1:4? | 15 | medium: middle token πε/πβ/πζ |
| 12 | Κολοσ. α´. Γ´ | Col 1:3 | 16 | high |
| 13 | ζ´. β´. Β´ | **Ammonian section** 2, canon B | 16 | medium |
| 14 | Κσφ. ε´. Ε´ | Eph 5:5 | 17 | medium (run-1 «Κερκ [unclear]» resolved — reviewer read Κσφ clearly) |
| 15 | α´. ιω´. η´. Γ´ | 1 Cor 11:7? | 18 | medium: verse digit η/ν contested |
| 16 | α´. ιμ´. ε´. Δ´ | 1 Cor? | 18 | low: ιμ token unstable |
| 17 | Ματθ. γ´. Α´ | Matt 3:1 | 19 | high |
| 18 | [unclear siglum]. α´. Α´ | — | 19 | medium |
| 19 | Λκ. γ´. Δ´ | Luke 3:4 | 19 | high |

Ammonian markers (6, 13) are section numbers + Eusebian canon letters, not book
references — same as run 1 (reviewer-endorsed).

## Body-text and apparatus results (was «Scan vs corpus — comparison result»)

- **First line: corrected as above** — «Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν».
- **Verse order** 1→19 confirmed again; the page breaks mid-v19 after «ὅτε».
- **Title** exact match: ΤΟ ΚΑΤΑ ΙΩΑΝΝΗΝ ΑΓΙΟΝ ΕΥΑΓΓΕΛΙΟΝ.
- **Marginalia: no longer a gap** — all 19 lines are in
  `corpus/john1_estienne1550.json` and rendered by the builder with
  `data-conf` flags (italic+underline = low confidence).
- **Endmark: no longer a gap** — the mark below the last line is **«l. i.»**
  (two abbreviated tokens each with a dot), positioned RIGHT-of-centre beside
  marginal line 19 (not page-centre as run 1 stated). Attested unambiguous in
  `qa-evidence/crops/secondsource/endmark300.png`. Corpus field: `endmark.raw`.
- **No running foot** is printed on this folio (bottom band blank).
- **Nomina sacra**: at 300 dpi the overlined contractions are **ΘΥ / ΙΥ / ΧΥ**
  (upsilon-final), at v6/v13/v17 — NOT the ΘΣ/ΧΣ sigma-final forms the low-res
  scan suggested; the builder NOMINA now uses the Υ forms (toggle still swaps
  to full words). Μωσέως is spelled **in full** (a real TR-vs-WH diff: WH
  Μωυσέως). v1/v2 Θεόν/Θεὸς full with capital theta; whether an overline also
  sits on them is CONTESTED between passes — recorded in the JSON, not guessed.
- **Text variants** WH vs scan (φαίνει/ἔφαινε v5, κέκραγε + «Οὗτος ἦν ὃν εἶπον»
  v15, ὁ μονογενὴς υἱός v18, Μωσέως v17, capital-theta θεοῦ throughout):
  per-verse in the JSON `notes` column.

## Method note (why run 2 differs)

Fixed-band crops of the 812-px scan (run-1 method) produced conflicting
readings and were discarded. Run 2: per-line segmentation from ink profiles →
one crop per line at 12× from the 300-dpi second source → two independent
vision passes per line → geometric forensics for the Α/Λ/Γ capitals →
reviewer's direct readings arbitrate any residual split. Anything still split
stays [unclear]/low-confidence — no silent best-guesses.
