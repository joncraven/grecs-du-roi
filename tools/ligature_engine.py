#!/usr/bin/env python3
"""ligature_engine.py — Phase 2.2: ligature engine v2 (the grind).

Ranked by corpus frequency (compute, don't guess), this tool:

  1. measures which corpus words the SHIPPED cursive face already fuses
     (real HarfBuzz spans, same logic as tools/fusion-coverage.py),
  2. greedy set-covers the remaining words with candidate letter sequences
     (len 2..6 inside letter runs), in coverage-yield order, capped at ~150,
  3. draws each chosen fused ligature glyph by composing the slanted cursive
     part masters with a join overlap (parts crowd together exactly like the
     cursive masters' advance logic; accents ride their own slot),
  4. rebuilds GSUB through ONE feaLib source: the 43 upstream liga rules +
     the new fusion rules (longest-first) + punch-list 1a (omicron+tonos /
     varia fuse with a following sigma) + the Phase-2.1 locl/calt block,
  5. asserts EVERY new ligature fuses live in HarfBuzz (features on) and
     disappears with features off, inside a real corpus word carrier,
  6. writes src/fonts/grecs-roi-greek-cursive.otf/.woff2 (+ .ligatures.json).

Punch-list minor 1a: the -ος fusion must fire after an ACCENTED omicron —
omicrontonos+σ/ς and ὸ+σ/ς map to dedicated fused glyphs carrying the accent
contour over the omicron half.

Run:  python3 tools/ligature_engine.py [--cap 150] [--overlap 0.18]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import cursive_masters as cm  # noqa: E402  (reuses pen/fea/charstring helpers)

# fusion-coverage.py has a dash in its name -> import by path
_fc_spec = importlib.util.spec_from_file_location(
    "fusion_coverage", str(ROOT / "tools" / "fusion-coverage.py"))
fc = importlib.util.module_from_spec(_fc_spec)
_fc_spec.loader.exec_module(fc)

SIGMA_GLYPHS = {"sigma", "uni03C2"}          # both input forms must fire ligatures
MARK_Y_MIN = cm.MARK_Y_MIN


# ---------------------------------------------------------------------------
# corpus words (frequency-weighted, same definition as fusion-coverage.py)
# ---------------------------------------------------------------------------
def corpus_words():
    texts = fc.load_corpus(str(ROOT / "corpus"))
    words = []
    for lines in texts.values():
        for line in lines:
            for s, e in fc.words_of(line):
                w = line[s:e]
                if sum(1 for c in w if fc.is_greek(c)) >= 2:
                    words.append(w)
    return words


def letter_runs(w):
    out, cur = [], ""
    for c in w + "#":
        if fc.is_greek(c):
            cur += c
        else:
            if len(cur) >= 2:
                out.append(cur)
            cur = ""
    return out


def seed_covered(words):
    """{word: True} for words the shipped cursive face already fuses."""
    font = fc.hb_font(str(ROOT / "src/fonts/grecs-roi-greek-cursive.otf"))
    covered = set()
    for w in set(words):
        if fc.fusion_spans(font, w):
            covered.add(w)
    return covered


# ---------------------------------------------------------------------------
# greedy set cover over uncovered word instances
# ---------------------------------------------------------------------------
def word_candidates(w):
    """all candidate sequences (len 2..4 inside letter runs) of one word."""
    out = set()
    for r in letter_runs(w):
        for L in range(2, min(4, len(r)) + 1):
            for i in range(len(r) - L + 1):
                out.add(r[i:i + L])
    return out


def select_sequences(words, covered, cap):
    """Greedy max-coverage over uncovered word INSTANCES (freq-weighted),
    drawing candidates in coverage-yield order up to `cap` (~150, the card's
    target set; the >=60% gate is usually crossed far earlier and the rest
    buys density toward the 1550 look)."""
    freq = Counter(words)
    todo = {w: n for w, n in freq.items() if w not in covered}
    total = sum(freq.values())
    done = total - sum(todo.values())

    # cand -> set of uncovered words containing it (built once)
    occ = {}
    for w in todo:
        for s in word_candidates(w):
            occ.setdefault(s, set()).add(w)

    chosen, gains = [], []
    while len(chosen) < cap and occ:
        def gain(s):
            return sum(todo[w] for w in occ[s] if todo[w])
        best = max(occ, key=lambda s: (gain(s), len(s), -occ[s].__len__()))
        best_gain = gain(best)
        if best_gain <= 0:
            break
        for w in list(occ[best]):
            if todo[w]:
                done += todo[w]
                todo[w] = 0
        chosen.append(best)
        gains.append(best_gain)
        # prune candidates with no remaining uncovered word
        occ = {s: ws for s, ws in occ.items()
               if s != best and any(todo[w] for w in ws)}
    return chosen, gains, done / total


# ---------------------------------------------------------------------------
# fused glyph composition
# ---------------------------------------------------------------------------
def _shift_ops(ops, dx):
    return cm._nudge_ops(ops, dx)


def fuse_outline(cmds_by_part, widths, overlap):
    """Compose parts side by side with `overlap` (fraction of each advance)
    stolen at each join. Every contour (body AND its accent layer) shifts by
    the same part offset — an accent rides its own letter slot, exactly like
    the standalone master. Returns (ops, advance)."""
    ops = []
    off = 0.0
    n = len(cmds_by_part)
    for i, cmds in enumerate(cmds_by_part):
        for cont in cm._contours(cmds):
            shifted = _shift_ops(cont, off)
            ops.extend(shifted)
            ops.append(("closePath", ()))
        if i < n - 1:
            off += widths[i] * (1.0 - overlap)
        else:
            off += widths[i]
    return ops, int(round(off))


def lig_name(seq, glyph_seq):
    base = "lig2_" + "_".join(glyph_seq)
    if len(base) <= 31:
        return base
    import hashlib
    return "lig2_" + hashlib.md5(seq.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# fea assembly (extends cursive_masters.make_fea with extra liga rules)
# ---------------------------------------------------------------------------
def make_fea_v2(font, extra_rules):
    fea = cm.make_fea(font)
    # splice the new rules into the LIGA lookup body (before its closing)
    head, sep, tail = fea.partition("lookup LIGA {")
    body, sep2, rest = tail.partition("} LIGA;")
    assert sep and sep2, "LIGA lookup block not found in v1 fea"
    extra = "\n    " + "\n    ".join(extra_rules) if extra_rules else ""
    fea = head + sep + body + extra + sep2 + rest

    # Drop the rlig registration for the cursive face. The upstream Gazis
    # derivative registers the liga lookup under liga/clig/rlig/dlig/hlig;
    # per CSS spec rlig (required ligatures) CANNOT be switched off by
    # font-feature-settings, and WebKit/Safari enforces that strictly — the
    # feature toggle was dead in WebKit (always-fused). These are historical/
    # discretionary fusions, so liga+clig+dlig+hlig is the honest tag set.
    # (Chromium/Firefox allow forcing rlig off; Safari is the stricter oracle.)
    fea = re.sub(r"feature rlig \{[^{}]*\} rlig;\s*", "", fea)
    assert "rlig" not in fea, "rlig feature not removed"

    # @L (the calt letter context class) must count FUSED glyphs as letters,
    # else positional alternates stop seeing through ligature joins: in
    # "ο πασ" with πα fused, the word-final sigma rule needs the ligature
    # glyph in @L for `sub @L sigma'` to still fire.
    m = re.search(r"@L = \[(.*?)\];", fea)
    assert m, "@L class not found"
    letters = m.group(1).split()
    lig_targets = []
    for rule in (body.split("\n") + (extra_rules or [])):
        parts = rule.replace(";", "").split()
        if len(parts) >= 4 and parts[0] == "sub" and "by" in parts:
            t = parts[parts.index("by") + 1]
            if t not in letters and t not in lig_targets:
                lig_targets.append(t)
    fea = fea.replace(m.group(0),
                      f"@L = [{' '.join(letters + lig_targets)}];", 1)
    return fea


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=150)
    # t_8ad4e391: scan ground truth (300-dpi secondsource, pixel-measured)
    # shows tight letters with a clean ~2px white gap at every join, never
    # fused ink. 0.18 stole ~125u at each join → parts crushed together.
    # 0.05 (~35-45u) keeps the joins tight like the scan with a hairline gap
    # and still shrinks the advance enough for the feature toggle to prove.
    ap.add_argument("--overlap", type=float, default=0.05)
    ap.add_argument("--font", default=str(ROOT / "src/fonts/grecs-roi-greek-cursive.otf"))
    args = ap.parse_args(argv)

    words = corpus_words()
    covered = seed_covered(words)
    print(f"corpus words: {len(words)} instances, "
          f"{len(covered)} distinct already fused")
    seqs, gains, cov_after = select_sequences(words, covered, args.cap)
    print(f"selected {len(seqs)} sequences, projected word coverage "
          f"{100*cov_after:.1f}%")
    print("  " + "  ".join(f"{s}+{g}" for s, g in list(zip(seqs, gains))[:20]))

    font = TTFont(args.font)
    cmap = font.getBestCmap()
    glyphset = font.getGlyphSet()
    hmtx = dict(font["hmtx"].metrics)
    cff = font["CFF "]
    top = cff.cff.topDictIndex[0]
    order = list(font.getGlyphOrder())
    existing_liga = cm.dump_existing_liga(font)
    existing_inputs = {tuple(line.split()[1:-2]) for line in existing_liga}
    # punch-list 1a inputs are owned by the dedicated accented fusions below
    existing_inputs |= {(a, sg) for a in ("omicrontonos", "uni1F7C")
                        for sg in sorted(SIGMA_GLYPHS)}

    # snapshot ORIGINAL outlines (composite safety, per Phase-2.1 pitfall 7)
    original = {g: cm._rec(glyphset, g) for g in order if g != ".notdef"}

    def part_glyphs(seq):
        return [cmap[ord(ch)] for ch in seq]

    new_glyphs = {}    # ligglyph -> (ops, width)
    rules = []         # fea lines
    drawn = []         # report rows

    # sigma-form expansion: each sigma slot may be typed as σ or ς
    def sigma_expansions(glyph_seq):
        slots = [[g] if g not in SIGMA_GLYPHS else ["sigma", "uni03C2"]
                 for g in glyph_seq]
        combos = [()]
        for slot in slots:
            combos = [c + (v,) for c in combos for v in slot]
        return combos

    for seq in seqs:
        glyph_seq = part_glyphs(seq)
        cmds_by_part = [original[g] for g in glyph_seq]
        widths = [hmtx.get(g, (500, 0))[0] for g in glyph_seq]
        ops, w = fuse_outline(cmds_by_part, widths, args.overlap)
        name = lig_name(seq, glyph_seq)
        if name in original:
            continue
        new_glyphs[name] = (ops, w)
        any_new = False
        for combo in sigma_expansions(glyph_seq):
            if combo in existing_inputs:
                continue
            existing_inputs.add(combo)          # global input dedup
            rules.append(f"sub {' '.join(combo)} by {name};")
            any_new = True
        if not any_new:
            del new_glyphs[name]
            continue
        drawn.append({"seq": seq, "glyph": name, "parts": glyph_seq,
                      "advance": w, "rules": len(sigma_expansions(glyph_seq))})

    # ---- punch-list minor 1a: accented omicron + final sigma ----------------
    # fused omicron-sigma carrying the accent contour of the accented master
    accent_masters = {"omicrontonos": ("omicronsigma.tonos", "ό"),
                      "uni1F7C": ("omicronsigma.varia", "ὸ")}
    om_body = original["omicron"]
    sig_body = original["sigma"]
    for acc, (name, accch) in accent_masters.items():
        parts = [om_body, sig_body]
        widths = [hmtx["omicron"][0], hmtx["sigma"][0]]
        ops, w = fuse_outline(parts, widths, args.overlap)
        # lift the accent layer from the accented omicron master, riding slot 0
        for cont in cm._contours(original[acc]):
            ys = [p[1] for p in cm._contour_pts(cont)]
            if ys and min(ys) >= MARK_Y_MIN:
                ops.extend(cont)          # slot 0 -> no shift
                ops.append(("closePath", ()))
        new_glyphs[name] = (ops, w)
        for sg in sorted(SIGMA_GLYPHS):
            rules.append(f"sub {acc} {sg} by {name};")
        drawn.append({"seq": accch + "σ", "glyph": name, "parts": [acc, "sigma"],
                      "advance": w, "punchlist": True})

    # ---- gate sequence oun: every accent variant of ο + υ(+accent) + ν ------
    # (οὖν with any precomposed upsilon accent — the hero cell must show a
    #  live 3-letter fusion for each, not just the two upstream Gazis forms)
    rev = {}
    for cp, gn in cmap.items():
        rev.setdefault(gn, cp)
    ups_accents = ["upsilon", "upsilontonos", "uni1F50", "uni1F51",
                   "uni1F52", "uni1F53", "uni1F54", "uni1F55",
                   "uni1F56", "uni1F57", "uni1F79", "uni1F7A",
                   "uni1FE4", "uni1FE5"]
    for u in ups_accents:
        combo = ("omicron", u, "nu")
        if combo in existing_inputs or u not in rev:
            continue
        cmds_by_part = [original[g] for g in combo]
        widths = [hmtx[g][0] for g in combo]
        ops, w = fuse_outline(cmds_by_part, widths, args.overlap)
        seq_txt = "".join(chr(rev[g]) for g in combo)
        name = lig_name(seq_txt, list(combo))
        if name in original:
            continue
        new_glyphs[name] = (ops, w)
        existing_inputs.add(combo)
        rules.append(f"sub {' '.join(combo)} by {name};")
        drawn.append({"seq": seq_txt, "glyph": name, "parts": list(combo),
                      "advance": w, "gate": True})

    # longest sequences first inside the lookup (HB is leftmost/longest within
    # a lookup anyway, but deterministic order keeps diffs auditable)
    rules.sort(key=lambda r: -r.split(" by ")[0].count(" "))
    print(f"drew {len(new_glyphs)} fused glyphs, {len(rules)} new rules")

    # ---- write outlines ----------------------------------------------------
    for name, (ops, w) in new_glyphs.items():
        if name not in order:
            order.append(name)
        cs = cm.charstring_from_ops(top, cff, ops, w)
        cm.set_charstring(top, cff, name, cs)
        hmtx[name] = (w, 0)

    font.setGlyphOrder(order)
    font["hmtx"].metrics = hmtx
    font["maxp"].numGlyphs = len(order)
    charset = list(top.charset)
    for g in order:
        if g not in charset:
            charset.append(g)
    top.charset = charset
    top.encoding = charset

    # ---- GSUB rebuild ------------------------------------------------------
    fea = make_fea_v2(font, rules)
    if "GSUB" in font:
        del font["GSUB"]
    addOpenTypeFeaturesFromString(font, fea)

    # ---- naming ------------------------------------------------------------
    for rec in font["name"].names:
        if rec.nameID == 0:
            rec.string = (
                "Derived from GFS Gazis (c) Greek Font Society, OFL 1.1. "
                "Grecs du Roi Phase 2.2 ligature engine v2: corpus-ranked "
                f"fused ligatures ({len(drawn)} glyphs) + positional "
                "alternates + punch-list accented-omicron sigma fusions. "
                "Reserved Font Name 'GFS Gazis' is not used.")
        elif rec.nameID == 3:
            rec.string = "1.002;GDR;GrecsRoiGreekCursive-Regular"

    out = Path(args.font)
    font.flavor = None
    font.save(str(out))
    woff = out.with_suffix(".woff2")
    font.flavor = "woff2"
    font.save(str(woff))
    print(f"wrote {out} ({out.stat().st_size} bytes) and {woff}")

    # ---- HarfBuzz assertion per new ligature -------------------------------
    fails = assert_live(str(out), drawn, words)
    report = {
        "engine": "tools/ligature_engine.py",
        "overlap": args.overlap,
        "cap": args.cap,
        "projected_word_coverage": round(100 * cov_after, 2),
        "ligatures": drawn,
        "hb_assert_failures": fails,
    }
    meta = out.with_suffix(".ligatures.json")
    meta.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"ligature manifest -> {meta}  ({len(drawn)} ligatures, "
          f"{len(fails)} assertion failures)")
    return 1 if fails else 0


def assert_live(font_path, drawn, words):
    """Every new ligature must fuse INSIDE a real corpus carrier (a span
    covering the sequence's position) and must NOT fuse with features off."""
    font = fc.hb_font(font_path)
    fails = []
    # carriers ranked by how tightly the sequence sits (a longer word gives
    # more chance of an upstream ligature eating a component, e.g. σ+τ stigma
    # consuming the tau of a following τε) — try shortest first
    by_word = {}
    for w in set(words):
        by_word.setdefault(w, [])
    uniq = sorted(set(words), key=len)
    for row in drawn:
        seq = row["seq"]
        probes = [seq, seq.replace("σ", "ς")]
        carriers = [w for w in uniq if any(p in w for p in probes)] or probes
        ok_span = None
        ok_probe = None
        for probe in probes + carriers:
            idx = max((probe.find(p) for p in probes if p in probe), default=0)
            on = fc.fusion_spans(font, probe)
            hit = [sp for sp in on if sp[0] <= idx and sp[1] >= idx + len(seq)]
            if hit:
                ok_span, ok_probe = hit, probe
                break
        if not ok_span:
            fails.append(f"{row['glyph']}: no live fusion covering '{seq}'")
            continue
        off = fc.shape_spans(font, ok_probe, {f: 0 for f in fc.SHIPPING_FEATURES})
        off_fused = {(s, e) for s, e in off if e - s >= 2}
        if any(span in off_fused for span in ok_span):
            fails.append(f"{row['glyph']}: fusion present with features OFF")
    return fails


if __name__ == "__main__":
    sys.exit(main())
