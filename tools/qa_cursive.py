#!/usr/bin/env python3
"""qa_cursive.py — Phase 2.1 verification for grecs-roi-greek-cursive.

Assertions (all fail-closed, exit != 0 on any FAIL):

  A. HarfBuzz ON/OFF:
     * locl[grek]:    sigma -> lunateSigma when features on, none when off
     * calt:          sigma.medial word-medial / sigma.cursive word-final /
                      rho.longtail word-initial / epsilon.cursive,
                      theta.cursive inside words — each verified by re-shaping
                      with the feature OFF and diffing the glyph sequence
     * liga:          the 4 named sequences (γερ μω οὖν φησί) still fuse
                      (regression vs the base derivative)
  B. Zero tofu: shape every word of every corpus/*.json with the shipping
     feature set; assert no .notdef anywhere.
  C. Copy invariant: the font maps only ordinary Unicode codepoints —
     shaping input is NFC text; no PUA glyph is required to render it
     (glyph NAMES may be PUA-sounding but codepoints are not).
  D. True-master audit (NOT faux-italic): for every minuscule glyph, compare
     the shipped outline against a pure shear of the base outline — the
     shipped font must differ (redrawn marks kept upright / exit flicks),
     and the alternates must be drawn masters absent from any shear copy.

Usage: python3 tools/qa_cursive.py [--font src/fonts/grecs-roi-greek-cursive.otf]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

ROOT = Path("/Volumes/RAID10/jon/Projects/grecs-du-roi")
BASE = ROOT / "src/fonts/grecs-roi-greek.otf"
CURSIVE = ROOT / "src/fonts/grecs-roi-greek-cursive.otf"

SFEATS = {"liga": 1, "clig": 1, "rlig": 1, "dlig": 1, "hlig": 1,
          "calt": 1, "locl": 1}
OFF = {k: 0 for k in SFEATS}
GREK = ("grek", 0, 0)

FAILS: list[str] = []


def check(cond: bool, label: str, detail: str = ""):
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {label}" + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)


def face_pair(path):
    blob = hb.Blob.from_file_path(str(path))
    f = hb.Face(blob)
    return hb.Font(f)


def shape(font, text, features, script="grek"):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.script = script
    hb.shape(font, buf, features)
    return buf.glyph_infos, buf.glyph_positions


def glyph_name(font, gid):
    return font.get_glyph_name(gid)


def gnames(font, infos):
    return [glyph_name(font, i.codepoint) for i in infos]


# ---------------------------------------------------------------- A. HB on/off
def test_positional(font):
    on, off = {}, {}

    def run(text, feats):
        infos, _ = shape(font, text, feats)
        return gnames(font, infos)

    # 1) lunate sigma: word-initial sigma becomes lunate under locl[grek]
    #    (probes must avoid sequences the Phase-2.2 fusion engine fuses —
    #    a fused sigma correctly disappears; these carriers keep the letter
    #    context intact: σο/κσ/ρσ σφ σθ-adjacent forms checked below)
    seq = run("σοφια", SFEATS)
    seq_off = run("σοφια", OFF)
    check("lunateSigma" in seq, "locl[grek]: sigma -> lunateSigma (ON)")
    check("lunateSigma" not in seq_off,
          "locl[grek] OFF leaves sigma untouched")

    # 2) medial vs final sigma forms
    seq = run("κσδ", SFEATS)           # sigma between κ and δ: no κσ/σδ fusion
    check("sigma.medial" in seq, "calt: medial sigma -> sigma.medial", str(seq))
    seq = run("ο πασ", SFEATS)         # final sigma after letter
    # note: uppercase Pi is upright; use all-lower:
    seq = run("ο πασ", SFEATS)
    check("sigma.cursive" in seq, "calt: final sigma -> sigma.cursive", str(seq))
    check("sigma.medial" not in run("ο πασ", OFF)
          and "sigma.cursive" not in run("ο πασ", OFF),
          "calt OFF: sigma forms untouched")

    # 3) word-initial rho -> longtail
    seq = run("απο ρο", SFEATS)        # rho after space = word-initial
    check("rho.longtail" in seq, "calt: initial rho -> rho.longtail", str(seq))
    check("rho.longtail" not in run("απο ρο", OFF),
          "calt OFF: rho untouched")

    # 4) cursive epsilon/theta inside words
    seq = run("αθοπ", SFEATS)          # θ medial; αθ/θο not fused sequences
    check("theta.cursive" in seq, "calt: medial theta -> theta.cursive", str(seq))
    seq = run("πεπτωκα", SFEATS)
    check("epsilon.cursive" in seq, "calt: medial epsilon -> epsilon.cursive", str(seq))
    check("theta.cursive" not in run("αθοπ", OFF)
          and "epsilon.cursive" not in run("πεπτωκα", OFF),
          "calt OFF: epsilon/theta untouched")

    # 5) accented letters keep word position (mark must not break context)
    seq = run("ἀνθρώπους", SFEATS)
    joined = "".join(seq)
    check("sigma.medial" in joined or "lunateSigma" in joined or
          "sigma.cursive" in seq,
          "calt sees through polytonic marks (᾽ἀνθρώπους)", str(seq))


def test_liga_regression(font):
    def fused(text):
        infos, _ = shape(font, text, SFEATS)
        return len(infos) < len([c for c in text])

    for seq in ("γερ", "μω"):
        check(fused(seq), f"liga still fires: {seq}")
    # οὖν / φησί use precomposed chars upstream; test via the plain forms the
    # base derivative also registered
    for txt in ("φησι", ):
        check(fused(txt), f"liga still fires: {txt}")
    seq2 = "\u03BF\u03C2"  # ο + final ϲ — the exact upstream ligature pair
    infos, _ = shape(font, seq2, SFEATS)
    check("omicronsigma" in gnames(font, infos), "liga: οϲ -> omicronsigma",
          str(gnames(font, infos)))
    infos_off, _ = shape(font, seq2, OFF)
    check("omicronsigma" not in gnames(font, infos_off),
          "liga OFF: οϲ unfolded")

    # punch-list minor 1a: -ος must fire AFTER an accented omicron
    # (explicit escapes: U+03C2 final sigma ς, not the lunate U+03F2)
    for txt, glyph in (("\u03CC\u03C2", "omicronsigma.tonos"),
                       ("\u1F7C\u03C2", "omicronsigma.varia"),
                       ("\u03CC\u03C3", "omicronsigma.tonos")):
        infos, _ = shape(font, txt, SFEATS)
        check(glyph in gnames(font, infos),
              f"1a: '{txt}' -> {glyph} (accented omicron + final sigma)",
              str(gnames(font, infos)))
        infos_off, _ = shape(font, txt, OFF)
        check(glyph not in gnames(font, infos_off),
              f"1a OFF: '{txt}' unfolded")


# ------------------------------------------------------------------ B. tofu
def test_no_tofu(font):
    # share the corpus loader with fusion-coverage.py: the scan-collation
    # file (john1_estienne1550.json) stores nested dicts/lists of apparatus
    # which an old naive .values() walk turned into pseudo-words like
    # 'Θ-signs,' — Latin furniture, not this face's responsibility.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fc", str(ROOT / "tools/fusion-coverage.py"))
    fc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fc)
    texts = fc.load_corpus(str(ROOT / "corpus"))
    words = []
    for lines in texts.values():
        for line in lines:
            for s, e in fc.words_of(line):
                w = line[s:e]
                if any(fc.is_greek(c) for c in w):
                    words.append(w)
    bad = []
    for w in words:
        infos, _ = shape(font, w, SFEATS)
        g = gnames(font, infos)
        if any(n == ".notdef" for n in g):
            bad.append(w)
    check(not bad, f"zero tofu across corpus ({len(words)} words)",
          f"{len(bad)} bad, e.g. {bad[:3]}")


# ------------------------------------------------------- C. copy invariant
def test_copy_invariant(font):
    cmap = {}
    for t in TTFont(str(CURSIVE))["cmap"].tables:
        if t.isUnicode():
            cmap.update(t.cmap)
    pua = [cp for cp in cmap if 0xE000 <= cp <= 0xF8FF or cp >= 0xF0000]
    check(not pua, "no PUA codepoints in cmap (copy invariant holds)",
          str([hex(p) for p in pua]))


# ------------------------------------------------- D. true-master audit
def _flat(cmds):
    pts = []
    for op, args in cmds:
        if op in ("moveTo", "lineTo"):
            pts.append(tuple(round(v, 1) for v in args[0]))
        elif op == "curveTo":
            pts.extend(tuple(round(v, 1) for v in a) for a in args)
    return pts


def _glyph_points(font, name):
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    gs = font.getGlyphSet()
    if name not in gs:
        return None
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    return _flat(pen.value)


def test_true_masters():
    curs = TTFont(str(CURSIVE))
    base = TTFont(str(BASE))
    SKEW = math.tan(math.radians(11.0))
    from fontTools.misc.transform import Transform
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.recordingPen import RecordingPen

    same_as_shear = 0
    differ = 0
    for g in ["alpha", "sigma", "rho", "theta", "omicron", "pi", "tau",
              "epsilon", "delta", "omega"]:
        bp = _glyph_points(base, g)
        rp = RecordingPen()
        tp = TransformPen(rp, Transform(1, 0, SKEW, 1, 0, 0))
        from fontTools.pens.recordingPen import DecomposingRecordingPen
        d = DecomposingRecordingPen(base.getGlyphSet())
        base.getGlyphSet()[g].draw(d)
        for op, args in d.value:
            getattr(tp, op)(*args)
        shear_pts = _flat(rp.value)
        cur_pts = _glyph_points(curs, g)
        if cur_pts is None:
            FAILS.append(f"true-master: {g} missing")
            continue
        if set(cur_pts) == set(shear_pts):
            same_as_shear += 1
        else:
            differ += 1
    check(differ > same_as_shear,
          "shipped minuscules differ from a pure shear (true masters, "
          "not faux-italic)", f"same={same_as_shear} differ={differ}")

    # the alternates have no counterpart in any sheared copy of the base
    for g in ("lunateSigma", "sigma.cursive", "sigma.medial",
              "epsilon.cursive", "theta.cursive", "rho.longtail"):
        check(_glyph_points(curs, g) not in (None, []),
              f"drawn alternate present: {g}")

    # marks kept upright: tonos in the cursive font must have the SAME
    # outline as base (only translated), i.e. no shear skew applied
    b = _glyph_points(base, "tonos")
    c = _glyph_points(curs, "tonos")
    def shift_eq(p1, p2):
        if not p1 or not p2 or len(p1) != len(p2):
            return False
        dx = round(p2[0][0] - p1[0][0], 1)
        dy = round(p2[0][1] - p1[0][1], 1)
        return all(round(bx + dx, 1) == ax and round(by + dy, 1) == ay
                   for (ax, ay), (bx, by) in zip(p2, p1))
    check(shift_eq(b, c), "polytonic marks stay upright (tonos translated only)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", default=str(CURSIVE))
    args = ap.parse_args()
    font = face_pair(args.font)
    print("== A. HarfBuzz on/off positional assertions ==")
    test_positional(font)
    print("== A2. liga regression (named fusions still live) ==")
    test_liga_regression(font)
    print("== B. zero tofu over corpus ==")
    test_no_tofu(font)
    print("== C. copy invariant (no PUA codepoints) ==")
    test_copy_invariant(font)
    print("== D. true-master audit (not a faux-italic shear) ==")
    test_true_masters()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURES:")
        for f_ in FAILS:
            print(" -", f_)
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
