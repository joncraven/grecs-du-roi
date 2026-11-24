# Scan-vs-text word-by-word correction cycle (t_717701c6)

The page `src/estienne-john1.html` can now be read **beside the source
scan** (toolbar: *show scan beside text*) and **marked word-by-word**
against the scan/WH comparison (toolbar: *review marks*). Both toggles
are display-only — they change no text node, so the same-Unicode copy
invariant is untouched.

## Data model

| file | role |
|---|---|
| `corpus/john1_estienne1550.json` | scan-collated readings (ground truth of the leaf) |
| `corpus/john1_wh.json` | Westcott-Hort comparison base |
| `corpus/john1_word_matrix.json` | **derived** word-by-word alignment, one entry per token (status + contested flags) — rebuild anytime |
| `corpus/john1_word_ledger.json` | **append-only decision store** — the audit trail; survives every rebuild |

Word statuses: `match · casing · elision · variant · scan_only · wh_only`.
A word named in a corpus collation note (or in the nomina-sacra
contestation) is flagged **contested** — the cycle starts from exactly
the questions the Phase-2.4 collation already logged.

## The cycle

```
python3 tools/word_matrix.py            # rebuild the matrix (corpus + ledger)
python3 tools/collation_cycle.py stats  # open vs decided counts, rounds
python3 tools/collation_cycle.py next   # next batch: contested/variant first
python3 tools/collation_cycle.py record --key K --verdict confirmed \
        --note "<evidence>" --round N    # append decision + rebuild
```

Verdicts: `confirmed` (scan reading stands, evidence cited),
`corrected` (corpus was wrong — edit the corpus file, the rebuild moves
the entry to `match`), `glyph-fix` (text stands, the font form needs
work), `superseded`. `apply-corrections` lists `corrected` decisions not
yet reflected in the matrix.

Progress is measured by `stats`: open items go down, ledger decisions go
up, and every open item is reachable by key from the page's review marks
(hover shows the WH reading / contested note / decision).

## Evidence protocol

Word questions are settled against the 300-dpi second source committed
under `qa-evidence/crops/secondsource/` — crop the region, zoom 3–5×,
and read the specific letter(s) in question, never from context
expectation. Record what the zoom showed in the decision note.

## Round 1 (t_717701c6)

20 open variant/scan_only/wh_only items adjudicated → **confirmed** with
zoom evidence (Ἰωάννης double-nu; ἦλθε no movable nu; κέκραγε; ὃν
εἶπον clause present; v16 begins Καὶ; Μωσέως without upsilon; ὁ
μονογενὴς υἱός; Ἰωάννου full nu; the ὃ γέγονεν items are TR verse
divisions, not omissions). 1 item deliberately left open:
`v13w2:ἐκ` — the round-1 zoom reads `οἳ οὐκ ἐξ αἱμα- / τος`, which
contradicts two earlier 300-dpi passes (no οὐκ) and the singular/plural
αἵματος/αἱμάτων question is still unsettled. It stays contested for a
human eye; the page keeps the current attested reading.

## Round 2 (t_717701c6)

22 mechanical items closed with evidence: 17 casing (capital theta and
sentence-initial capitals — confirmed against the committed 300-dpi
second-source reads; the WH lowercase difference is editorial, the
leaf's form stands) and 5 elision-class (U+1FBD koronis vs U+02BC
apostrophe — glyph convention of the leaf's font, letters identical).

**State after two rounds** (`collation_cycle.py stats`, 2026-11-24):
268 tokens tracked · 42 ledger decisions (rounds 1–2) · **open items 26
→ 4**, all four being the one genuine unresolved v13 question
(ἐκ/οὐκ/αἵματος vs WH οὐκ ἐξ αἱμάτων). The `next` call returns
exactly those 4; `record`ing them (or a corpus `corrected` edit +
rebuild) closes the page.

Evidence shots: `qa-evidence/t7-scan-default.png` (default view
unchanged), `t7-scan-side-by-side.png`, `t7-review-marks.png`,
`t7-review-textblock.png`, `t7-live-scan-side-by-side.png` (live site,
gate-authenticated, deploy e06b292).
