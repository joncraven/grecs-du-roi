#!/usr/bin/env python3
"""Build src/estienne-john1.html — the Estienne 1550 folio-161 recreation (Phase 2.4, v2).

Text base: corpus/john1_estienne1550.json — the scan-collated wording of the
folio (t_8e2d4b30 run 2; each verse carries a notes column citing WH diffs).
The page prints exactly the attested extent of the folio (1:1–1:19 up to
'ὅτε'); the tail of v19 past the page break comes from corpus/john1_wh.json
and is marked as such in the DOM title attribute.

Marginalia, nomina sacra and the l.i. endmark are the scan's own apparatus,
transcribed line-by-line at 8–16x against the 300-dpi second source
(qa-evidence/crops/secondsource/); contested readings carry the corpus
confidence flags as data-* attributes instead of silent guesses.

Same-Unicode invariant: the DOM contains ordinary NFC polytonic Greek. Nomina
sacra are visual spans holding the real capital letters + U+0304 combining
macron (ΘΥ), never PUA; select-all → paste yields readable polytonic text.
Rebuild: python3 tools/build_estienne_page.py
"""
import json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WH = json.loads((ROOT / "corpus" / "john1_wh.json").read_text(encoding="utf-8"))
SCAN = json.loads((ROOT / "corpus" / "john1_estienne1550.json").read_text(encoding="utf-8"))
OUT = ROOT / "src" / "estienne-john1.html"
MATRIX_PATH = ROOT / "corpus" / "john1_word_matrix.json"

# t_717701c6: word-by-word correction cycle. Every rendered word token
# carries the matrix entry for its (verse, index) as data attributes, so a
# "review marks" mode can show open scan-vs-WH diffs in place. If the
# matrix is absent the page still builds (plain, unmarked).
MATRIX = {}
if MATRIX_PATH.exists():
    MATRIX = {(w["verse"], w["index"]): w
              for w in json.loads(MATRIX_PATH.read_text(encoding="utf-8"))["words"]
              if w["index"] > 0}

# Nomina sacra verified on this folio (corpus.nomina_sacra.attested_forms):
# Υ-final overlined contractions at 1:6/1:13/1:17. Keys are the scan-form
# words they replace; display keeps the letters + U+0304 (paste-safe).
NOMINA = {
    "Θεοῦ":     ("Θ\u03A5", "theo-abbr"),
    "Χριστοῦ":  ("Χ\u03A5", "christou-abbr"),
    "Ἰησοῦ":    ("\u0399\u03A5", "iesou-abbr"),
}

# Right-margin parallel references, transcribed from the scan (corpus
# .marginalia). key = verse whose first line the reference sits beside
# (y-alignment measured against the 300-dpi body-line segmentation).
MARGINALIA = {m["align_verse"]: m for m in SCAN["marginalia"]}
# lines sharing a verse anchor stack under that verse in scan order
MARG_BY_VERSE = {}
for m in SCAN["marginalia"]:
    MARG_BY_VERSE.setdefault(m["align_verse"], []).append(m)

def greek_numeral(n: int) -> str:
    units = ["", "α", "β", "γ", "δ", "ε", "ϛ", "ζ", "η", "θ"]
    tens = ["", "ι", "κ", "λ", "μ", "ν", "ξ", "ο", "π", "ϙ"]
    s = tens[n // 10] + units[n % 10]
    return s + "´"

def nom_render(word: str, caps: str) -> str:
    # Each cap letter gets a U+0304 combining macron.  The caps are already
    # base letters (no diacritics), so the result is naturally decomposed:
    # e.g. "ΘΥ" → Θ+U+0304+Υ+U+0304.  We must NOT NFC-normalize the output
    # (see write step) or the browser will render the precomposed
    # upsilon-with-macron (U+1FE9) as an iota.
    disp = "".join(ch + "\u0304" for ch in caps)
    return (f'<span class="nom" data-full="{word}">{disp}</span>')

def render_token(n: int, idx: int, word: str, inner: str = "") -> str:
    """One whitespace token → inline <span class="w"> carrying its word-
    matrix entry (key/status/WH reading) for the review-marks mode.
    Text content is unchanged — same-Unicode copy invariant is untouched.
    `inner` overrides the visible markup (drop-cap Ε) but keeps the word's
    plain letters first in the text stream (Ε + ν = Ἐν on copy)."""
    if not inner:
        inner = word
        stem = word.rstrip(".,·;:()\"'\u02bc\u2019")
        trail = word[len(stem):]
        if stem in NOMINA:
            caps, cls = NOMINA[stem]
            inner = nom_render(stem, caps) + trail
    entry = MATRIX.get((n, idx))
    attrs = ""
    if entry:
        title = ""
        if entry["wh"] and entry["status"] != "match":
            title = entry["wh"]
        if entry.get("decision"):
            title = (title + " — " if title else "") + \
                f"decided: {entry['decision']['verdict']} (round {entry['decision'].get('round')})"
        if entry["contested_note"]:
            title = (title + " — " if title else "") + entry["contested_note"]
        attrs = (f' data-wkey="{entry["key"]}" data-wstat="{entry["status"]}"'
                 + (' data-wcontest="1"' if entry["contested_note"] else "")
                 + (' data-wdecided="1"' if entry.get("decision") else "")
                 + (f' data-wwh="{title}"' if title else ""))
    return f'<span class="w"{attrs}>{inner}</span>'


def render_words(n: int, text: str) -> str:
    return " ".join(render_token(n, i + 1, w)
                    for i, w in enumerate(text.split()))


def render_verse(n: int, text: str) -> str:
    vn = greek_numeral(n)
    first = n == 1
    if first:
        # drop-cap Ε lives inside the text flow: copy yields "Ἐν ἀρχῇ…" whole
        assert text.startswith("Ἐν ἀρχῇ"), text[:12]
        words = text.split()
        assert words[0] == "Ἐν" and words[1] == "ἀρχῇ", words[:2]
        cap = render_token(
            n, 1, "Ἐν",
            inner='<span class="initial" aria-hidden="false">Ε</span>'
                  '<span class="initial-rest">ν</span>')
        body = cap + " " + render_token(n, 2, words[1]) + " " + " ".join(
            render_token(n, i + 1, w) for i, w in enumerate(words[2:], start=2))
    else:
        body = render_words(n, text)
    marg_html = ""
    for m in MARG_BY_VERSE.get(n, []):
        conf = m["confidence"]
        marg_html += (f'<aside class="marginal" data-conf="{conf}"'
                      f' title="{m["raw"]} — confidence {conf}">{m["raw"]}</aside>')
    tail = ""
    if n == 19:  # page break: folio 161 stops at 'ὅτε'
        attested, rest = text.split(" ὅτε", 1)
        body = (f'<span title="attested to here on fol. 161">'
                + render_words(n, attested + " ὅτε") + '</span>'
                '<span class="pagebreak-tail" title="continues on fol. 162; supplied from WH">'
                + (" " + render_words(n + 100, rest) if rest else "") + "</span>")
    return (f'<div class="verse" data-verse="{n}">'
            f'<span class="vnum" aria-hidden="true">{vn}</span>'
            f'{marg_html}<span class="vtext">{body}</span></div>')

def verse_text(n: int) -> str:
    v = SCAN["verses"].get(str(n))
    if v:
        return v["scan"]
    return WH[str(n)]  # only ever reached for verses past the page extent (none here)

verses_html = "\n".join(
    render_verse(n, verse_text(n))
    for n in sorted(int(k) for k in WH) if n <= 19)

# Headpiece: stylised Renaissance scrollwork band (drawn SVG, PD)
HEADPIECE = """
<svg class="headpiece" viewBox="0 0 820 74" role="img" aria-label="woodcut headpiece">
 <g fill="none" stroke="#2a2115" stroke-width="2.4" stroke-linecap="round">
  <path d="M12 37 H808"/>
  <path d="M410 37 c-18-26-52-30-70-8 -14 17 2 38 22 32 14-4 15-22 2-25"/>
  <path d="M410 37 c18-26 52-30 70-8 14 17-2 38-22 32-14-4-15-22-2-25"/>
  <path d="M300 37 c-26-22-58-16-62 4 -4 18 20 28 33 15 9-9 2-22-10-19"/>
  <path d="M520 37 c26-22 58-16 62 4 4 18-20 28-33 15-9-9-2-22-10-19"/>
  <path d="M190 37 c-22 0-38-14-52-10 -14 4-10 24 6 24 12 0 16-14 4-16"/>
  <path d="M630 37 c22 0 38-14 52-10 14 4 10 24-6 24-12 0-16-14-4-16"/>
  <path d="M96 37 c-16 0-26-8-36-6 M724 37 c16 0 26-8 36-6"/>
  <circle cx="410" cy="30" r="4" fill="#2a2115"/>
  <path d="M410 12 c-6 8 6 12 0 20 M404 18 c4 2 8 2 12 0"/>
 </g>
</svg>"""

HTML = f"""<!DOCTYPE html>
<html lang="grc">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ΤΟ ΚΑΤΑ ΙΩΑΝΝΗΝ ΑΓΙΟΝ ΕΥΑΓΓΕΛΙΟΝ — Estienne 1550, fol. 161</title>
<!-- Recreation of https://upload.wikimedia.org/wikipedia/commons/5/58/Gospel_Estienne_1550.jpg
     (Public domain). Phase 2.4 v2 — Grecs du Roi project, t_8e2d4b30.
     Text: scan-collated Estienne 1550 wording (corpus/john1_estienne1550.json,
     PD); tail of 1:19 from Westcott-Hort. Marginalia + l.i. endmark are the
     scan's own apparatus. All text is live, selectable NFC polytonic
     Unicode; copy → normal polytonic Greek. Rebuilt by
     tools/build_estienne_page.py — do not hand-edit. -->
<style>
@font-face {{
  font-family: "GrecsRoi Greek Cursive";
  src: url("fonts/grecs-roi-greek-cursive.woff2") format("woff2");
  unicode-range: U+0370-03FF, U+1F00-1FFF, U+03F2, U+02BC;
  font-display: block;
}}
@font-face {{
  font-family: "GrecsRoi Greek";
  src: url("fonts/grecs-roi-greek.woff2") format("woff2");
  unicode-range: U+0370-03FF, U+1F00-1FFF;
  font-display: block;
}}
@font-face {{
  font-family: "GFS Didot";
  src: url("fonts/gfs-didot.woff2") format("woff2");
  font-display: block;
}}
@font-face {{
  font-family: "Cardo Polytonic";
  src: url("fonts/cardo-polytonic.woff2") format("woff2");
  unicode-range: U+0020-03FF, U+1F00-1FFF, U+2000-2206, U+2126;
  font-display: block;
}}
:root {{
  --parchment: #efe5c8; --parchment-deep: #e3d3ac;
  --ink: #2a2115; --ink-soft: #453a27; --rubric: #7c2d1c; --rule: #b99f6c;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: #d3bd8c;
  font-family: "GrecsRoi Greek Cursive", "GrecsRoi Greek", "GFS Didot", "Cardo", Georgia, "Times New Roman", serif;
  color: var(--ink);
  font-feature-settings: "liga" 1, "clig" 1, "rlig" 1, "dlig" 1, "hlig" 1,
                         "calt" 1, "locl" 1;
  font-variant-ligatures: contextual discretionary;
}}
/* Phase 2.5 reading-site toggle: "modern polytonic (Cardo)" swaps ONLY the
   font-family on the identical NFC text nodes — no text substitution. */
body.mode-modern .folio {{
  font-family: "Cardo Polytonic", "GFS Didot", Cardo, Georgia, "Times New Roman", serif;
  font-feature-settings: "liga" 0, "clig" 0, "rlig" 0, "dlig" 0, "hlig" 0,
                         "calt" 0, "locl" 0;
  font-variant-ligatures: none;
}}
body.mode-modern {{ background: #cbb684; }}
.folio {{
  max-width: 820px; margin: 2rem auto; padding: 2.6rem 2.2rem 3rem;
  background:
    radial-gradient(ellipse at 50% 8%, rgba(255,255,255,.28), transparent 60%),
    radial-gradient(ellipse at 50% 100%, rgba(122,94,46,.18), transparent 55%),
    var(--parchment);
  box-shadow: 0 4px 24px rgba(42,33,21,.35);
  position: relative;
}}
.folio-no {{ position: absolute; top: 1rem; right: 1.4rem; font-size: .95rem; color: var(--ink-soft); }}
.headpiece {{ width: 100%; height: auto; display: block; margin-bottom: .9rem; }}
.title {{
  /* weight 400: the shipped GrecsRoi faces are single-weight (OS/2 400) —
     700 here made Chromium SYNTHESISE a fake bold, giving the capitals a
     generic fallback look instead of the real GrecsRoi letterforms
     (t_76ac62df; scan's title capitals stay honest at regular weight). */
  text-align: center; font-weight: 400; letter-spacing: .06em;
  line-height: 1.45; font-size: 1.5rem; margin: 0 0 1.1rem; color: var(--ink);
}}
.textblock {{
  display: grid; grid-template-columns: 1.6rem 1fr 5.4rem;
  column-gap: .55rem; font-size: 1.32rem; line-height: 1.72;
}}
.verse {{ display: contents; }}
.vnum {{
  grid-column: 1; text-align: right; font-size: .62em; color: var(--rubric);
  line-height: inherit; padding-top: .35em; user-select: none;
}}
.vtext {{ grid-column: 2; text-align: justify; hyphens: none; }}
.marginal {{
  grid-column: 3; font-size: .58em; line-height: 1.5; color: var(--ink-soft);
  padding-top: .28em; user-select: none;
}}
.marginal[data-conf="low"] {{ font-style: italic; text-decoration: underline dotted; }}
.pagebreak-tail {{ color: var(--ink-soft); }}
.initial {{
  float: left; font-size: 4.1em; line-height: .82; padding: .04em .09em 0 0;
  color: var(--rubric); font-weight: 700;
}}
.nom {{ text-transform: uppercase; letter-spacing: .02em; }}
.endmark {{ text-align: right; font-size: .8em; margin-top: 1.1rem; color: var(--ink-soft);
            padding-right: 6.4rem; }}
.toolbar {{
  max-width: 820px; margin: 0 auto; padding: .4rem 2.2rem;
  font-family: Georgia, serif; font-size: .8rem; color: #453a27;
  display: flex; gap: 1rem; align-items: center;
}}
.toolbar a {{ color: #5c1f12; }}
/* t_717701c6 — scan beside the text + word-by-word review marks.
   .folio-wrap is a plain block by default (single-column page unchanged);
   body.show-scan turns it into a two-column flex with the source scan
   sticky next to the text. Review marks colour the word spans the builder
   tagged with data-wstat/data-wkey; text nodes are untouched either way. */
.folio-wrap {{ display: block; }}
.scan-pane {{ display: none; }}
body.show-scan .folio-wrap {{
  display: flex; gap: 1.4rem; align-items: flex-start;
  max-width: 1500px; margin: 0 auto; padding: 0 1.2rem;
}}
body.show-scan .folio {{ margin: 2rem 0; flex: 1 1 60%; min-width: 0; }}
body.show-scan .scan-pane {{
  display: block; flex: 0 1 40%; position: sticky; top: .8rem;
  margin-top: 2rem; background: #efe9dc; padding: .5rem;
  box-shadow: 0 2px 12px rgba(42,33,21,.35);
}}
.scan-pane img {{ display: block; width: 100%; height: auto; }}
.scan-pane figcaption {{
  font-family: Georgia, serif; font-size: .68rem; color: #453a27;
  padding: .35rem .2rem .1rem;
}}
/* review marks: open diffs are visible; decided/match words are not */
body.review-marks .w {{ position: relative; }}
body.review-marks .w[data-wcontest="1"] {{ background: #f6dfb9; }}
body.review-marks .w[data-wstat="variant"]:not([data-wcontest]) {{ background: #f3c9b4; }}
body.review-marks .w[data-wstat="scan_only"] {{ background: #e7d3f0; }}
body.review-marks .w[data-wstat="wh_only"] {{ background: #cfe3f3; }}
body.review-marks .w[data-wdecided="1"] {{ background: #dcecd2; }}
.review-legend {{
  display: none; gap: 1rem; flex-wrap: wrap; font-family: Georgia, serif;
  font-size: .72rem; color: #453a27; max-width: 820px; margin: 0 auto;
  padding: 0 2.2rem;
}}
body.review-marks .review-legend {{ display: flex; }}
.review-legend i {{ font-style: normal; padding: 0 .35rem; border-radius: 2px; }}
@media print {{ .toolbar {{ display: none; }} .folio {{ box-shadow: none; margin: 0; }} }}
</style>
</head>
<body>
<div class="toolbar">
  <span class="face-toggle" role="radiogroup" aria-label="Typeface">
    <label><input type="radio" name="face" value="roi" checked> grecs du roi</label>
    <label><input type="radio" name="face" value="modern"> modern polytonic (Cardo)</label>
  </span>
  <label><input type="checkbox" id="nomTgl" checked> nomina sacra (ΘΥ̅)</label>
  <label><input type="checkbox" id="scanTgl"> show scan beside text</label>
  <label><input type="checkbox" id="revTgl"> review marks</label>
  <span>text: Estienne 1550 scan-collated (PD) · <a href="index.html">ligature specimen</a> ·
        <a href="../qa-evidence/estienne-scan.jpg">source scan (PD)</a></span>
</div>
<div class="review-legend" aria-label="Review mark legend">
  <span>open word-diffs (t_717701c6 cycle):</span>
  <i style="background:#f6dfb9">contested reading</i>
  <i style="background:#f3c9b4">variant vs WH</i>
  <i style="background:#e7d3f0">scan-only word</i>
  <i style="background:#dcecd2">decided</i>
  <span>· hover a word for its WH reading / note / decision</span>
</div>
<div class="folio-wrap">
<main class="folio" id="folio">
  <div class="folio-no" aria-hidden="true">161</div>
  {HEADPIECE}
  <h1 class="title" lang="grc">ΤΟ ΚΑΤΑ ΙΩΑΝΝΗΝ ΑΓΙΟΝ<br>ΕΥΑΓΓΕΛΙΟΝ.</h1>
  <section class="textblock" id="textblock" spellcheck="false">
{verses_html}
  </section>
  <div class="endmark" aria-hidden="true" title="end-of-page mark attested below the last line (right side)">l. i.</div>
</main>
<figure class="scan-pane" id="scanPane">
  <img src="estienne-scan.jpg" alt="source scan: Estienne 1550 fol. 161 verso, the same page rendered at left" loading="lazy">
  <figcaption>source scan — Estienne 1550 (Editio Regia), fol. 161 verso
    (PD, Wikimedia Commons). The text at left is this page, recreated.</figcaption>
</figure>
</div><!-- /folio-wrap -->
<script>
/* t_717701c6: scan-beside-text and review-marks toggles. Persisted like
   the face toggle; neither changes any text node (same-Unicode invariant). */
const scanTgl = document.getElementById('scanTgl');
function applyScan() {{
  document.body.classList.toggle('show-scan', scanTgl.checked);
  try {{ localStorage.setItem('gdr-scan', scanTgl.checked ? '1' : '0'); }} catch (e) {{}}
}}
scanTgl.addEventListener('change', applyScan);
const revTgl = document.getElementById('revTgl');
function applyRev() {{
  document.body.classList.toggle('review-marks', revTgl.checked);
  document.querySelectorAll('.w[data-wwh]').forEach(s => {{
    if (revTgl.checked) s.setAttribute('title', s.dataset.wwh);
    else s.removeAttribute('title');
  }});
  try {{ localStorage.setItem('gdr-rev', revTgl.checked ? '1' : '0'); }} catch (e) {{}}
}}
revTgl.addEventListener('change', applyRev);
try {{
  if (localStorage.getItem('gdr-scan') === '1') {{ scanTgl.checked = true; applyScan(); }}
  if (localStorage.getItem('gdr-rev') === '1') {{ revTgl.checked = true; applyRev(); }}
}} catch (e) {{}}
</script>
<script>
/* Nomina-sacra toggle: swaps ΘΥ̅ ⇄ full scan word. Both forms are real Unicode. */
const tgl = document.getElementById('nomTgl');
function applyNom() {{
  document.querySelectorAll('.nom').forEach(s => {{
    const full = s.dataset.full;
    if (tgl.checked) {{
      if (s.textContent !== s._abbr) {{ s._abbr = s._abbr || s.textContent; }}
      s.textContent = s._abbr;
    }} else {{
      s.textContent = full;
    }}
  }});
}}
tgl.addEventListener('change', applyNom);
document.querySelectorAll('.nom').forEach(s => s._abbr = s.textContent);

/* Phase 2.5 face toggle: grecs du roi ⇄ modern polytonic (Cardo).
   Same Unicode text in both modes — only the CSS font stack changes. */
const faceRadios = document.querySelectorAll('input[name="face"]');
function applyFace() {{
  const v = document.querySelector('input[name="face"]:checked').value;
  document.body.classList.toggle('mode-modern', v === 'modern');
  try {{ localStorage.setItem('gdr-face', v); }} catch (e) {{}}
}}
faceRadios.forEach(r => r.addEventListener('change', applyFace));
try {{
  const saved = localStorage.getItem('gdr-face');
  if (saved === 'modern') {{
    document.querySelector('input[name="face"][value="modern"]').checked = true;
    applyFace();
  }}
}} catch (e) {{}}
</script>
</body>
</html>
"""
# NOTE: No NFC normalization here.  The nomina-sacra spans use decomposed
# forms (base letter + U+0304 combining macron) because some fonts render the
# precomposed Greek capital-with-macron codepoints (U+1FE0–U+1FEF) as the
# wrong letter shape.  NFC would collapse e.g. Υ+U+0304 → U+1FE9 (Ῡ), which
# many fonts display as an iota.  The HTML is generated by us; we write the
# exact code points we intend.
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
