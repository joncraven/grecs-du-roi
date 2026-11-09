#!/usr/bin/env python3
"""Build src/estienne-john1.html — the Estienne 1550 folio-161 recreation (Phase 2.4, v1).

Text base: Westcott-Hort John 1 (Perseus canonical-greekLit tlg0031.tlg004, PD),
extracted to corpus/john1_wh.json. Collation against the scan (and TR variants)
is tracked as a follow-up card; this v1 uses WH verbatim, NFC.

Same-Unicode invariant: the DOM contains ordinary NFC polytonic Greek. Nomina
sacra are visual spans holding the real capital letters + U+0304 combining
macron (ΘΣ), never PUA; select-all → paste yields readable polytonic text.
Rebuild: python3 tools/build_estienne_page.py
"""
import json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSES = json.loads((ROOT / "corpus" / "john1_wh.json").read_text(encoding="utf-8"))
OUT = ROOT / "src" / "estienne-john1.html"

# Nomina sacra (scan-attested on this folio): full WH word -> displayed Greek
# capitals (each followed by combining macron U+0304 at render time).
NOMINA = {
    "θεόν":  ("ΘΣ", "theou-abbr"),
    "θεὸς":  ("ΘΣ", "theou-abbr"),
    "Θεοῦ":  ("ΘΣ", "theou-abbr"),
    "Χριστοῦ": ("ΧΣ", "christou-abbr"),
}

# Marginal parallel references (illustrative apparatus, abbreviations in the
# Estienne style; exact scan marginalia are a Phase-2.0 collation item).
MARGINALIA = {
    1: "Ματθ. α· Γ´", 3: "Κολ. α· Γ´", 4: "Ζαχ. ιδ· Β´", 5: "Ἠσ. νϛ· ι´",
    6: "Ματθ. γ· Α´", 9: "Ἰσ. μα´· Ιϛ´", 11: "Ἔξο. ιϛ·", 12: "Δευ. στ· ΚΗ´",
    14: "Ἔξο. λγ· ΙΑ´", 15: "Πρξ. ιγ· ΛΗ´", 17: "Ἔξο. κδ· ΙΒ´",
}

def greek_numeral(n: int) -> str:
    d = "ϛκγδεθιηεααβγδ".replace("α", "α")  # placeholder, replaced below
    units = ["", "α", "β", "γ", "δ", "ε", "ϛ", "ζ", "η", "θ"]
    tens = ["", "ι", "κ", "λ", "μ", "ν", "ξ", "ο", "π", "ϙ"]
    s = tens[n // 10] + units[n % 10]
    return s + "´"

def nom_render(word: str, caps: str) -> str:
    # ΘΣ -> Θ + U+0304 + Σ + U+0304 ; paste yields the letters (+ macrons)
    disp = "".join(ch + "\u0304" for ch in caps)
    return (f'<span class="nom" data-full="{word}">{disp}</span>')

def render_verse(n: int, text: str) -> str:
    esc = text
    for word, (caps, cls) in NOMINA.items():
        esc = re.sub(rf'(?<![\u0370-\u1FFF])' + re.escape(word) + r'(?![\u0370-\u1FFF])',
                     nom_render(word, caps), esc)
    vn = greek_numeral(n)
    first = n == 1
    body = esc
    if first:
        # drop-cap Ε lives inside the text flow: copy yields "Ἐν ἀρχῇ…" whole
        assert body.startswith("ΕΝ ΑΡΧΗ")
        body = ('<span class="initial" aria-hidden="false">Ε</span>'
                '<span class="initial-rest">ν ἀρχῇ</span>' + body[len("ΕΝ ΑΡΧΗ"):])
    marg = MARGINALIA.get(n)
    marg_html = f'<aside class="marginal">{marg}</aside>' if marg else ""
    return (f'<div class="verse" data-verse="{n}">'
            f'<span class="vnum" aria-hidden="true">{vn}</span>'
            f'{marg_html}<span class="vtext">{body}</span></div>')

verses_html = "\n".join(render_verse(int(k), v) for k, v in sorted(VERSES.items(), key=lambda kv: int(kv[0])))

# Headpiece: stylised Renaissance scrollwork band (drawn SVG, PD)
HEADPIECE = """
<svg class="headpiece" viewBox="0 0 820 74" role="img" aria-label="woodcut headpiece">
 <g fill="none" stroke="#2a2115" stroke-width="2.4" stroke-linecap="round">
  <path d="M12 37 H808"/>
  <path d="M410 37 c-18-26-52-30-70-8 -14 17 2 38 22 32 14-4 15-22 2-25"/>
  <path d="M410 37 c18-26 52-30 70-8 14 17-2 38-22 32-14-4-15-22-2-25"/>
  <path d="M300 37 c-26-22-58-16-62 4 -4 18 20 28 33 15 9-9 2-22-10-19"/>
  <path d="M520 37 c26-22 58-16 62 4 4 18-20 28-33 15-9-9-2-22 10-19"/>
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
     (Public domain). Phase 2.4 v1 — Grecs du Roi project, t_b16a2c44.
     Text: Westcott-Hort John 1 (PD). All text is live, selectable NFC
     polytonic Unicode; copy → normal polytonic Greek. Rebuilt by
     tools/build_estienne_page.py — do not hand-edit. -->
<style>
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
:root {{
  --parchment: #efe5c8; --parchment-deep: #e3d3ac;
  --ink: #2a2115; --ink-soft: #453a27; --rubric: #7c2d1c; --rule: #b99f6c;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: #d3bd8c;
  font-family: "GrecsRoi Greek", "GFS Didot", "Cardo", Georgia, "Times New Roman", serif;
  color: var(--ink);
  font-feature-settings: "liga" 1, "clig" 1, "rlig" 1, "dlig" 1, "hlig" 1;
  font-variant-ligatures: contextual discretionary;
}}
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
  text-align: center; font-weight: 700; letter-spacing: .06em;
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
.initial {{
  float: left; font-size: 4.1em; line-height: .82; padding: .04em .09em 0 0;
  color: var(--rubric); font-weight: 700;
}}
.nom {{ text-transform: uppercase; letter-spacing: .02em; }}
.endmark {{ text-align: center; font-size: .8em; margin-top: 1.1rem; color: var(--ink-soft); }}
.toolbar {{
  max-width: 820px; margin: 0 auto; padding: .4rem 2.2rem;
  font-family: Georgia, serif; font-size: .8rem; color: #453a27;
  display: flex; gap: 1rem; align-items: center;
}}
.toolbar a {{ color: #5c1f12; }}
@media print {{ .toolbar {{ display: none; }} .folio {{ box-shadow: none; margin: 0; }} }}
</style>
</head>
<body>
<div class="toolbar">
  <label><input type="checkbox" id="nomTgl" checked> nomina sacra (ΘΣ̅)</label>
  <span>text: Westcott-Hort (PD) · <a href="index.html">ligature specimen</a> ·
        <a href="../qa-evidence/estienne-scan.jpg">source scan (PD)</a></span>
</div>
<main class="folio" id="folio">
  <div class="folio-no" aria-hidden="true">161</div>
  {HEADPIECE}
  <h1 class="title" lang="grc">ΤΟ ΚΑΤΑ ΙΩΑΝΝΗΝ ΑΓΙΟΝ<br>ΕΥ ΑΓΓΕΛΙΟΝ.</h1>
  <section class="textblock" id="textblock" spellcheck="false">
{verses_html}
  </section>
  <div class="endmark" aria-hidden="true">ι´.</div>
</main>
<script>
/* Nomina-sacra toggle: swaps Θ̅Σ̅ ⇄ full WH word. Both forms are real Unicode. */
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
</script>
</body>
</html>
"""
OUT.write_text(unicodedata.normalize("NFC", HTML), encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
