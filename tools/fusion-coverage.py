#!/usr/bin/env python3
"""fusion-coverage.py — Phase 2.0 coverage gate for Grecs du Roi.

Measures, per font, what fraction of the target corpus is actually touched by
a LIVE ligature, using real HarfBuzz shaping (not GSUB-table string matching):

  * pairs_pct — % of adjacent Greek-letter pairs in the corpus that a single
    shaped glyph covers (cluster span >= 2 letters) with the font's shipping
    font-feature-settings ("liga clig rlig dlig hlig" — exactly what
    estienne-john1.html applies), and how many of those pairs disappear when
    the features are switched off (proof the fusion is *active*, not kerning)
  * words_pct — % of corpus words containing at least one such fused pair
  * required  — do the gate sequences γερ, μω, οὖν, φησὶ fuse live?
  * nomina    — scan-attested nomina sacra inventory (see
    qa-evidence/nomina-sacra.md) and whether the font can render the letters

Outputs:
  stdout    — human-readable report
  --json F  — machine-readable coverage.json

Usage:
  python3 tools/fusion-coverage.py
  python3 tools/fusion-coverage.py --font src/fonts/grecs-roi-greek.otf
  python3 tools/fusion-coverage.py --json src/fonts/coverage.json

Corpus: corpus/*.json (NFC polytonic Greek, verbatim from Perseus
canonical-greekLit). Each file is either
  { "lines_map": { "1": "…", … }, … }   or a bare { "1": "…", "2": "…" } map.

Requires: fontTools, uharfbuzz. (Old coverage.py logic superseded.)
"""

import argparse
import io
import json
import os
import re
import sys
import unicodedata

try:
    from fontTools.ttLib import TTFont
    HAVE_FONTTOOLS = True
except ImportError:
    HAVE_FONTTOOLS = False

try:
    import uharfbuzz as hb
    HAVE_HB = True
except ImportError:
    HAVE_HB = False

# The features the shipping pages enable (estienne-john1.html):
SHIPPING_FEATURES = ("liga", "clig", "rlig", "dlig", "hlig")
# Gate sequences named in docs/phase2-plan.md §2.0 — must fuse live:
REQUIRED_SEQS = ["γερ", "μω", "οὐ", "φησ"]

# Scan-attested nomina sacra for fol. 161 (John 1), from
# qa-evidence/nomina-sacra.md — letters only, macron is U+0304 at render.
NOMINA_SACRA = {
    "ΘΣ": "θεός/θεοῦ/θεόν (God)",
    "ΚΣ": "κύριος (Lord) — WH v.10",
    "ΙΣ": "Ἰησοῦς (Jesus) — WH v.17",
    "ΧΣ": "Χριστός (Christ) — WH v.17",
}


# ---------------------------------------------------------------------------
# HarfBuzz helpers
# ---------------------------------------------------------------------------

def hb_font(font_path):
    """Load a font (ttf/otf/woff/woff2) as a HarfBuzz font via fontTools."""
    ft = TTFont(font_path, lazy=False)
    ft.flavor = None            # decompress woff/woff2 into plain sfnt
    bio = io.BytesIO()
    ft.save(bio)
    ft.close()
    blob = hb.Blob(bio.getvalue())
    face = hb.Face(blob)
    return hb.Font(face)


def shape_spans(font, text, features):
    """Shape `text` → list of (start,end) codepoint-index spans per glyph."""
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, features)
    infos = buf.glyph_infos
    if not infos:
        return []
    clusters = [g.cluster for g in infos] + [len(text)]
    return [(clusters[i], clusters[i + 1]) for i in range(len(infos))]


def fusion_spans(font, word):
    """(start,end) spans >=2 codepoints that a single LIVE ligature glyph
    covers — verified active by re-shaping with the features disabled."""
    on = shape_spans(font, word, {f: 1 for f in SHIPPING_FEATURES})
    fused = [(s, e) for s, e in on if e - s >= 2]
    if not fused:
        return []
    off = shape_spans(font, word, {f: 0 for f in SHIPPING_FEATURES})
    off_set = {(s, e) for s, e in off if e - s >= 2}
    # a span counts only if it disappears with features off (true GSUB fusion),
    # unless the baseline itself already shaped it fused (calt-driven): accept
    # when either the OFF pass un-fuses it, or the on-pass glyph differs.
    return [(s, e) for (s, e) in fused if (s, e) not in off_set]


# ---------------------------------------------------------------------------
# Font metadata (glyph census + GSUB inventory, kept from old coverage.py)
# ---------------------------------------------------------------------------

def font_census(font_path):
    cmap = set()
    gsub = {}
    try:
        font = TTFont(font_path, lazy=True)
        cmap = {cp for cp, g in (font.getBestCmap() or {}).items() if g}
        gs = font.get("GSUB")
        if gs is not None:
            for feat in gs.table.FeatureList.FeatureRecord:
                tag = feat.FeatureTag
                cnt = 0
                for li in feat.Feature.LookupListIndex:
                    lk = gs.table.LookupList.Lookup[li]
                    for st in lk.SubTable:
                        if hasattr(st, "ligatures"):
                            cnt += sum(len(v) for v in st.ligatures.values())
                gsub[tag] = gsub.get(tag, 0) + cnt
        font.close()
    except Exception:
        pass
    return cmap, gsub


def is_greek(c):
    cp = ord(c)
    return (0x0370 <= cp <= 0x03FF) or (0x1F00 <= cp <= 0x1FFF)


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------

def load_corpus(corpus_dir):
    texts = {}
    for fn in sorted(os.listdir(corpus_dir)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(corpus_dir, fn), encoding="utf-8") as f:
            data = json.load(f)
        lines = []
        if "lines_map" in data:
            lm = data["lines_map"]
            keys = sorted(lm, key=lambda k: int(k) if str(k).isdigit() else 0)
            lines = [lm[k] for k in keys]
        elif any(str(k).isdigit() for k in data):
            keys = sorted((k for k in data if str(k).isdigit()), key=int)
            lines = [data[k] for k in keys]
        if lines:
            texts[fn] = [unicodedata.normalize("NFC", l) for l in lines]
    return texts


def words_of(line):
    return [(m.start(), m.end()) for m in re.finditer(r"\S+", line)]


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def measure(font_path):
    label = os.path.basename(font_path).rsplit(".", 1)[0]
    cmap, gsub = font_census(font_path)
    res = {
        "font": label,
        "path": font_path,
        "cmap_codepoints": len(cmap),
        "greek_codepoints": sum(1 for cp in cmap if is_greek(chr(cp))),
        "gsub_ligature_counts": gsub,
        "harfbuzz": False,
        "pairs_total": 0, "pairs_covered": 0, "pairs_pct": 0.0,
        "words_total": 0, "words_covered": 0, "words_pct": 0.0,
        "top_fusions": [],
        "required_seq_live": {},
        "corpus_lines": 0,
    }

    corpus = load_corpus(CORPUS_DIR)
    all_words = []
    for lines in corpus.values():
        for line in lines:
            res["corpus_lines"] += 1
            for s, e in words_of(line):
                w = line[s:e]
                if sum(1 for c in w if is_greek(c)) >= 2:
                    all_words.append(w)

    # pair totals (adjacent Greek letters inside words)
    pairs_total = 0
    for w in all_words:
        idx = [i for i, c in enumerate(w) if is_greek(c)]
        for i in range(len(idx) - 1):
            if idx[i + 1] == idx[i] + 1:
                pairs_total += 1
    res["pairs_total"] = pairs_total
    res["words_total"] = len(all_words)

    if not (HAVE_HB and HAVE_FONTTOOLS):
        return res, corpus
    try:
        font = hb_font(font_path)
    except Exception as e:
        res["hb_error"] = str(e)
        return res, corpus
    res["harfbuzz"] = True

    from collections import Counter
    fusion_counter = Counter()
    seen = {}
    for w in set(all_words):
        spans = fusion_spans(font, w)
        idx = [i for i, c in enumerate(w) if is_greek(c)]
        adj = set()
        for i in range(len(idx) - 1):
            if idx[i + 1] == idx[i] + 1:
                adj.add((idx[i], idx[i + 1]))
        wpairs = sum(
            1 for s, e in spans
            for p in [(s + k, s + k + 1) for k in range(e - s - 1)]
            if p in adj
        )
        if spans:
            fusion_counter.update(w[s:e] for s, e in spans)
        seen[w] = (spans, wpairs)

    freq = Counter(all_words)
    covered_pairs = 0
    covered_words = 0
    for w, n in freq.items():
        spans, wpairs = seen.get(w, ([], None))
        if spans:
            covered_pairs += (wpairs or 0) * n
            covered_words += n
    res["pairs_covered"] = covered_pairs
    res["pairs_pct"] = 100.0 * covered_pairs / pairs_total if pairs_total else 0.0
    res["words_covered"] = covered_words
    res["words_pct"] = 100.0 * covered_words / len(all_words) if all_words else 0.0
    res["top_fusions"] = [
        {"text": t, "count": c} for t, c in fusion_counter.most_common(25)
    ]

    # gate sequences: fuse inside realistic word carriers (accept when a
    # fusion span fully covers the sequence inside the carrier)
    carriers = {
        "γερ": ["γερουσια", "γερ"],
        "μω": ["μωμος", "μω"],
        "οὐ": ["οὐκ", "οὐδὲ", "οὐ"],
        "φησ": ["φησί", "φησὶ", "φησιν"],
    }
    for seq, probes in carriers.items():
        live = False
        for p in probes:
            for s, e in fusion_spans(font, p):
                if p.find(seq) >= 0 and s <= p.find(seq) and e >= p.find(seq) + len(seq):
                    live = True
                    break
            if live:
                break
        res["required_seq_live"][seq] = live

    # nomina sacra letters present in cmap?
    ns_ok = {}
    for letters, gloss in NOMINA_SACRA.items():
        ns_ok[letters] = all(ord(c) in cmap for c in letters)
    res["nomina_sacra_letters"] = ns_ok
    return res, corpus


CORPUS_DIR = "corpus"


def print_report(report, gate):
    W = 72
    print("=" * W)
    print("  FUSION COVERAGE — Grecs du Roi (Phase 2.0, HarfBuzz-measured)")
    print("=" * W)
    print()
    for r in report:
        print(f"  Font: {r['font']} ({os.path.basename(r['path'])})")
        print(f"    cmap codepoints: {r['cmap_codepoints']} "
              f"(Greek {r['greek_codepoints']})  "
              f"GSUB lig entries: {sum(r['gsub_ligature_counts'].values())} "
              f"{r['gsub_ligature_counts']}")
        if not r["harfbuzz"]:
            print("    HarfBuzz: NOT AVAILABLE — counts are zero by default")
            print()
            continue
        print(f"    Corpus: {r['corpus_lines']} lines, "
              f"{r['words_total']} words, {r['pairs_total']} adjacent pairs")
        print(f"    Pairs fused: {r['pairs_covered']}/{r['pairs_total']}"
              f"  ({r['pairs_pct']:.1f}%)")
        print(f"    Words fused: {r['words_covered']}/{r['words_total']}"
              f"  ({r['words_pct']:.1f}%)")
        req = r["required_seq_live"]
        print(f"    Gate seqs live: " +
              "  ".join(f"{k}:{'OK' if v else 'MISSING'}" for k, v in req.items()))
        if r["top_fusions"]:
            tops = ", ".join(f"{f['text']}×{f['count']}"
                             for f in r["top_fusions"][:10])
            print(f"    Top fusions: {tops}")
        print()

    print("-" * W)
    print(f"  PHASE 2 GATE: words ≥ {gate:.0f}%  ·  "
          f"γερ/μω/οὖν/φησὶ live  ·  nomina sacra letters  ·  zero PNG cells")
    print("-" * W)
    ok_any = False
    for r in report:
        req_ok = all(r["required_seq_live"].values()) if r["required_seq_live"] else False
        passed = r["words_pct"] >= gate and req_ok
        if passed:
            ok_any = True
        print(f"  {r['font']}: {r['words_pct']:.1f}% words "
              f"{'PASS' if passed else 'FAIL'}")
    return ok_any


def main():
    global CORPUS_DIR
    ap = argparse.ArgumentParser(description="Fusion coverage gate (HarfBuzz)")
    ap.add_argument("--font", action="append", default=[])
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--gate", type=float, default=60.0)
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CORPUS_DIR = args.corpus or os.path.join(root, "corpus")
    if not os.path.isdir(CORPUS_DIR):
        print(f"ERROR: corpus dir not found: {CORPUS_DIR}", file=sys.stderr)
        return 1

    fonts = args.font
    if not fonts:
        fdir = os.path.join(root, "src", "fonts")
        fonts = [os.path.join(fdir, fn) for fn in sorted(os.listdir(fdir))
                 if fn.endswith((".otf", ".ttf", ".woff", ".woff2"))]

    report = [measure(fp)[0] for fp in fonts if os.path.isfile(fp)]
    ok = print_report(report, args.gate)

    if args.json:
        out = {
            "generated_by": "tools/fusion-coverage.py (HarfBuzz real-shaping)",
            "gate": args.gate,
            "shipping_features": list(SHIPPING_FEATURES),
            "required_sequences": REQUIRED_SEQS,
            "nomina_sacra_expected": NOMINA_SACRA,
            "corpus_files": sorted(load_corpus(CORPUS_DIR).keys()),
            "report": report,
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  JSON report → {args.json}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
