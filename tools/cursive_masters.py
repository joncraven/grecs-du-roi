#!/usr/bin/env python3
"""cursive_masters.py — Phase 2.1: slanted cursive masters + positional alternates.

Builds src/fonts/grecs-roi-greek-cursive.otf/.woff2 as a NEW face beside the
upright derivative (grecs-roi-greek.otf stays byte-identical, so the shipped
page and its copy invariant stay green while 2.2/2.4 land).

True masters, not a faux-italic shear — the shear is only the interpolation
starting point (decision D1=C, plan §Phase 2.1):

  1. body contours slant right (11 deg, baseline pivot);
  2. drawn cursive corrections composited on top: exit flicks on 18 minuscules
     (open join points — the unfinished-ductus read, and the anchors Phase 2.2
     fuses into ligatures), deepened sweeping rho descender for the
     word-initial alternate;
  3. accent/breathing contours stay UPRIGHT (only nudged right to sit over the
     leaning body) — plan §7: polytonic stacks must not drift with the shear;
  4. hand-drawn cursive masters for the positional alternates: lunate sigma
     (U+03F2), drawn final + medial sigma, deep-tailed initial rho, cursive
     medial epsilon and theta.

Positional alternates are GSUB-registered the same way the derivative already
re-registers liga under DFLT/grek/latn:

  * cmap U+03F2 -> lunateSigma master
  * locl[grek]:  sigma -> lunateSigma   (Estienne composes with lunate σ;
    HarfBuzz fires locl[grek] whenever it shapes Greek)
  * calt (DFLT/grek/latn), longest context first:
      @L sigma' @L   -> sigma.medial
      @L sigma'      -> sigma.cursive     (word-final)
      @X rho'        -> rho.longtail      (word-initial)
      @L epsilon' @L -> epsilon.cursive
      @L theta'  @L  -> theta.cursive
    @L = every letter glyph the cmap covers (incl. precomposed accented
    Greek), @X = space/punctuation, so marks never break word positions.

GSUB is rebuilt through fontTools.feaLib, so lookup indices compile
consistently; the 43 upstream liga rules are regenerated verbatim from the
base table into the same feature file (feature order: locl, calt, liga —
HarfBuzz applies lookups in definition order, so locl feeds calt).

Run:  python3 tools/cursive_masters.py
      [--base src/fonts/grecs-roi-greek.otf]
      [--out  src/fonts/grecs-roi-greek-cursive.woff2]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from pathlib import Path

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

ROOT = Path("/Volumes/RAID10/jon/Projects/grecs-du-roi")

ANGLE = 11.0
SKEW = math.tan(math.radians(ANGLE))
MARK_DX_Y = 210.0        # marks nudge right as if slanted only to this height
MARK_Y_MIN = 460         # contour with min-y >= this = accent/breathing layer

# ---- drawn cursive corrections ---------------------------------------------
# (anchor_x_fraction, anchor_y) in pre-shear space; the flick is a short
# upsloping open stroke continuing the pen's exit from the letter.
EXIT_ANCHORS = {
    "alpha": (0.90, 40), "delta": (0.92, 70), "epsilon": (0.90, 130),
    "eta":   (0.92, 30), "iota":  (0.88, 50),  "kappa": (0.92, 60),
    "lambda":(0.92, 20), "nu":    (0.92, 50),  "omicron": (0.88, 90),
    "pi":    (0.92, 50), "tau":   (0.90, 60),  "upsilon": (0.92, 70),
    "omega": (0.93, 40), "chi":   (0.92, 80),  "theta": (0.90, 130),
    "phi":   (0.90, 110), "rho":  (0.88, 120), "mu":    (0.92, 50),
    "uni03BC": (0.92, 50),
}
EXIT_FLICK = ((10, 40), (20, 74), (30, 96))
EXIT_WIDEN = 30

ALT_RHO_SCALE = 1.55     # sub-baseline tail stretch for the longtail master


def _slant_pt(x: float, y: float):
    return (x + SKEW * y, y)


def _rec(glyphset, name):
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(pen)
    return pen.value


def _contours(cmds):
    """recording-pen cmds -> list of contours; each contour is an op list
    [('moveTo',(x,y)), ('curveTo',((x1,y1),(x2,y2),(x3,y3))) | ('lineTo',(x,y)) ...]
    """
    out, cur = [], []
    for op, args in cmds:
        if op == "closePath":
            if cur:
                out.append(cur)
            cur = []
        elif op == "moveTo":
            cur = [("moveTo", args[0])]
        elif op == "lineTo":
            cur.append(("lineTo", args[0]))
        elif op == "curveTo":
            cur.append(("curveTo", tuple(args)))
    if cur:
        out.append(cur)
    return out


def _contour_pts(cont):
    for op, args in cont:
        if op in ("moveTo", "lineTo"):
            yield args
        elif op == "curveTo":
            yield from args


def _slant_ops(ops):
    out = []
    for op, args in ops:
        if op == "closePath":
            out.append((op, ()))
        elif op in ("moveTo", "lineTo"):
            out.append((op, _slant_pt(*args)))
        elif op == "curveTo":
            out.append((op, tuple(_slant_pt(*p) for p in args)))
    return out


def _nudge_ops(ops, dx):
    out = []
    for op, args in ops:
        if op == "closePath":
            out.append((op, ()))
        elif op in ("moveTo", "lineTo"):
            out.append((op, (args[0] + dx, args[1])))
        elif op == "curveTo":
            out.append((op, tuple((x + dx, y) for (x, y) in args)))
    return out


def build_master(cmds, width, name, upright=False):
    """Return (ops, new_width): slanted body + upright marks + exit flick.
    uppercase=False glyphs only: Estienne sets majuscules upright, so
    `upright=True` copies the contour through untouched."""
    if upright:
        ops = []
        for cont in _contours(cmds):
            ops.extend(cont)
            ops.append(("closePath", ()))
        return ops, width
    contours = _contours(cmds)
    body_ops, mark_ops = [], []
    body_right = 0.0
    has_body = False
    for cont in contours:
        ys = [p[1] for p in _contour_pts(cont)]
        if ys and min(ys) >= MARK_Y_MIN:
            mark_ops.append(cont)
        else:
            body_ops.append(cont)
            has_body = True
            xs = [p[0] for p in _contour_pts(cont)]
            body_right = max(body_right, max(xs) + SKEW * max(ys))

    ops = []
    for cont in body_ops:
        ops.extend(_slant_ops(cont))
        ops.append(("closePath", ()))
    mark_dx = SKEW * MARK_DX_Y if has_body else 0.0
    for cont in mark_ops:
        ops.extend(_nudge_ops(cont, mark_dx))
        ops.append(("closePath", ()))

    w = width
    if name in EXIT_ANCHORS:
        fx, ay = EXIT_ANCHORS[name]
        ax, ayy = _slant_pt(fx * width, ay)
        flick = [("moveTo", (ax, ayy))]
        flick.append(("curveTo", tuple(_slant_pt(fx * width + dx, ay + dy)
                                       for dx, dy in EXIT_FLICK)))
        flick.append(("closePath", ()))
        ops.extend(flick)
        body_right += EXIT_WIDEN
        w = int(width + EXIT_WIDEN)
    # advance follows the slanted extent, near-zero right side bearing
    # (cursive runs crowd together; Phase 2.2 ligatures carry the joins)
    w = max(w, int(math.ceil(body_right)) + 8)
    return ops, w


# ---- hand-drawn cursive alternate masters -----------------------------------
def alt_lunate_sigma():
    """ϲ: open-right lunate, matched outer/inner arcs, Gazis-ish ~46u stroke,
    ductus lean baked into the curve handles."""
    w = 355
    ops = [
        ("moveTo", (312, 398)),
        ("curveTo", ((272, 442), (182, 458), (122, 432))),
        ("curveTo", ((48, 400), (10, 322), (14, 240))),
        ("curveTo", ((18, 156), (66, 84), (142, 60))),
        ("curveTo", ((202, 40), (276, 50), (318, 88))),
        ("curveTo", ((300, 106), (286, 118), (276, 126))),
        ("curveTo", ((240, 92), (196, 84), (156, 96))),
        ("curveTo", ((102, 114), (64, 168), (62, 242))),
        ("curveTo", ((60, 318), (98, 380), (160, 404))),
        ("curveTo", ((212, 424), (268, 412), (300, 380))),
        ("curveTo", ((306, 386), (310, 392), (312, 398))),
        ("closePath", ()),
    ]
    return ops, w


def alt_sigma_cursive():
    """Drawn final sigma (σ.1): high cursive entry, open lower-right tail
    hooking left below the baseline — distinct from lunate and ligature forms."""
    w = 415
    ops = [
        ("moveTo", (348, 450)),
        ("curveTo", ((312, 474), (258, 468), (218, 440))),
        ("curveTo", ((162, 406), (130, 340), (130, 262))),
        ("curveTo", ((130, 178), (168, 106), (236, 74))),
        ("curveTo", ((282, 52), (338, 44), (382, 58))),
        ("curveTo", ((372, 36), (344, 18), (310, 8))),
        ("curveTo", ((316, -28), (306, -70), (274, -104))),
        ("curveTo", ((258, -74), (258, -32), (268, 2))),
        ("curveTo", ((216, 18), (164, 52), (130, 102))),
        ("curveTo", ((88, 164), (76, 240), (94, 312))),
        ("curveTo", ((110, 376), (152, 434), (214, 466))),
        ("curveTo", ((256, 488), (318, 484), (352, 462))),
        ("curveTo", ((350, 458), (349, 454), (348, 450))),
        ("closePath", ()),
    ]
    return ops, w


def alt_sigma_medial():
    """σ.2 medial: lunate body with entry from the left and an exit flick to
    the right — connects both ways (join anchors for Phase 2.2)."""
    w = 440
    ops = [
        ("moveTo", (28, 138)),
        ("curveTo", ((52, 96), (96, 62), (150, 48))),
        ("curveTo", ((196, 38), (236, 40), (268, 54))),
        ("curveTo", ((250, 74), (238, 86), (232, 96))),
        ("curveTo", ((204, 80), (174, 76), (146, 84))),
        ("curveTo", ((100, 98), (68, 148), (66, 222))),
        ("curveTo", ((64, 300), (102, 366), (164, 392))),
        ("curveTo", ((220, 414), (282, 402), (318, 366))),
        ("curveTo", ((318, 380), (320, 392), (324, 402))),
        ("curveTo", ((288, 442), (206, 456), (146, 432))),
        ("curveTo", ((72, 402), (32, 322), (34, 238))),
        ("curveTo", ((34, 204), (30, 168), (28, 138))),
        ("closePath", ()),
        # exit flick (separate contour, joins the next letter)
        ("moveTo", (320, 372)),
        ("curveTo", ((350, 388), (392, 412), (428, 440))),
        ("curveTo", ((398, 428), (362, 410), (330, 394))),
        ("curveTo", ((326, 386), (322, 378), (320, 372))),
        ("closePath", ()),
    ]
    return ops, w


def alt_epsilon_cursive():
    """ε cursive medial variant: fully rounded loop with entry+exit strokes."""
    w = 430
    ops = [
        ("moveTo", (26, 128)),
        ("curveTo", ((50, 84), (96, 50), (150, 38))),
        ("curveTo", ((216, 22), (282, 34), (322, 72))),
        ("curveTo", ((304, 92), (292, 104), (286, 114))),
        ("curveTo", ((252, 80), (210, 72), (168, 82))),
        ("curveTo", ((112, 98), (74, 152), (72, 226))),
        ("curveTo", ((70, 304), (108, 368), (170, 392))),
        ("curveTo", ((226, 414), (288, 402), (324, 366))),
        ("curveTo", ((350, 390), (382, 414), (414, 436))),
        ("curveTo", ((386, 424), (354, 408), (326, 392))),
        ("curveTo", ((282, 432), (210, 444), (152, 422))),
        ("curveTo", ((78, 394), (38, 316), (40, 232))),
        ("curveTo", ((40, 200), (28, 158), (26, 128))),
        ("closePath", ()),
    ]
    return ops, w


def alt_theta_cursive():
    """θ medial variant: pointed oval + slanted bar (Estienne forms); the bar
    splits the counters into two inner contours."""
    w = 540
    ops = [
        ("moveTo", (282, 452)),
        ("curveTo", ((178, 442), (84, 352), (68, 238))),
        ("curveTo", ((54, 136), (128, 30), (240, 8))),
        ("curveTo", ((354, -14), (462, 60), (488, 172))),
        ("curveTo", ((508, 268), (458, 376), (362, 424))),
        ("curveTo", ((334, 436), (308, 446), (282, 452))),
        ("closePath", ()),
        ("moveTo", (272, 400)),
        ("curveTo", ((190, 388), (124, 320), (112, 244))),
        ("curveTo", ((110, 232), (110, 222), (112, 212))),
        ("curveTo", ((180, 236), (300, 262), (424, 266))),
        ("curveTo", ((408, 340), (348, 388), (272, 400))),
        ("closePath", ()),
        ("moveTo", (252, 62)),
        ("curveTo", ((180, 78), (128, 128), (116, 172))),
        ("curveTo", ((186, 190), (300, 208), (428, 212))),
        ("curveTo", ((412, 142), (344, 70), (252, 62))),
        ("closePath", ()),
    ]
    return ops, w


ALTERNATES = {
    "lunateSigma": alt_lunate_sigma,
    "sigma.cursive": alt_sigma_cursive,
    "sigma.medial": alt_sigma_medial,
    "epsilon.cursive": alt_epsilon_cursive,
    "theta.cursive": alt_theta_cursive,
}


def master_rho_longtail(cmds, width):
    """Deep-tailed initial rho.  Input is the ALREADY-slanted rho outline:
    stretch its sub-baseline half (affine on y<0 = longer sweep, unchanged
    stroke weight) and kick the deepest part left into a cursive foot."""
    ops = []
    for cont in _contours(cmds):
        out = []
        for op, args in cont:
            if op in ("moveTo", "lineTo"):
                x, y = args
                ny = y * ALT_RHO_SCALE if y < 0 else y
                kick = -SKEW * 70 * min(1.0, max(0.0, -ny / 320))
                out.append((op, (x + kick, ny)))
            else:
                pts = []
                for (x, y) in args:
                    ny = y * ALT_RHO_SCALE if y < 0 else y
                    kick = -SKEW * 70 * min(1.0, max(0.0, -ny / 320))
                    pts.append((x + kick, ny))
                out.append((op, tuple(pts)))
        out.append(("closePath", ()))
        ops.extend(out)
    return ops, width


# ---- GSUB -------------------------------------------------------------------
def is_letter_cp(cp):
    ch = chr(cp)
    if 0x370 <= cp <= 0x3FF or 0x1F00 <= cp <= 0x1FFF:
        return unicodedata.category(ch).startswith("L")
    return False


def is_punct_cp(cp):
    ch = chr(cp)
    return unicodedata.category(ch)[0] in ("P", "Z")


def dump_existing_liga(font):
    """Serialize the base GSUB liga lookup (43 rules) to fea lines, so the
    feaLib rebuild preserves it verbatim."""
    lines = []
    gsub = font["GSUB"].table
    for lu in gsub.LookupList.Lookup:
        for st in lu.SubTable:
            ligs = getattr(st, "ligatures", None)
            if not ligs:
                continue
            for first, lst in ligs.items():
                for lig in lst:
                    comp = " ".join([first] + list(lig.Component))
                    lines.append(f"sub {comp} by {lig.LigGlyph};")
    return lines


def make_fea(font):
    cmap = font.getBestCmap()
    letters, puncts = set(), set()
    for cp, gn in cmap.items():
        if is_letter_cp(cp):
            letters.add(gn)
        elif is_punct_cp(cp):
            puncts.add(gn)
    letters |= {"sigma.cursive", "sigma.medial", "rho.longtail",
                "epsilon.cursive", "theta.cursive"}
    letters = sorted(letters)
    lat = " ".join(letters)
    liga_rules = dump_existing_liga(font)
    liga_body = "\n    ".join(liga_rules)

    # Named lookups; registered explicitly under DFLT/grek/latn (feaLib binds
    # rules to the CURRENT script/language system only — a bare run of
    # `script` statements silently registers just the last one, which is the
    # bug that hid these features from Greek shaping the first time).
    # Feature/lookup DEFINITION order = LookupList order = HarfBuzz
    # application order: LIGA first (so ligatures consume their components
    # before any alternate eats them), then LOCL (lunate), then CALT.
    return f"""
@L = [{lat}];

lookup LIGA {{
    {liga_body}
}} LIGA;

# locl: Estienne composes Greek with the lunate sigma; modern ς input maps
# to the drawn cursive final. (locl fires for grek; Latin has no sigma.)
lookup LOCL_LUNATE {{
    sub sigma' by lunateSigma;
    sub uni03C2' by sigma.cursive;
}} LOCL_LUNATE;

lookup CALT_SIGMA {{
    # medial first (longest context), then word-final fallback
    sub @L lunateSigma' @L by sigma.medial;
    sub @L lunateSigma' by sigma.cursive;
    sub @L sigma' @L by sigma.medial;
    sub @L sigma' by sigma.cursive;
}} CALT_SIGMA;

lookup CALT_RHO_SWAP {{
    sub rho' by rho.longtail;
}} CALT_RHO_SWAP;

lookup CALT_RHO_UNDO {{
    # revert any rho preceded by a letter (no buffer-start anchor in fea,
    # so swap-then-undo expresses "word-initial only")
    sub @L rho.longtail' by rho;
}} CALT_RHO_UNDO;

lookup CALT_EPSILON_THETA {{
    sub @L epsilon' @L by epsilon.cursive;
    sub @L theta' @L by theta.cursive;
}} CALT_EPSILON_THETA;
""" + "\n".join(
        f"feature {tag} {{\n"
        + "\n".join(f"    script {s}; language dflt;\n"
                    "    lookup LIGA;" for s in ("DFLT", "grek", "latn"))
        + f"}} {tag};"
        for tag in ("liga", "clig", "rlig", "dlig", "hlig")
    ) + """

feature locl {
    script grek; language dflt;
    lookup LOCL_LUNATE;
} locl;

feature calt {
    script DFLT; language dflt;
    lookup CALT_SIGMA; lookup CALT_RHO_SWAP; lookup CALT_RHO_UNDO;
    lookup CALT_EPSILON_THETA;
    script grek; language dflt;
    lookup CALT_SIGMA; lookup CALT_RHO_SWAP; lookup CALT_RHO_UNDO;
    lookup CALT_EPSILON_THETA;
    script latn; language dflt;
    lookup CALT_SIGMA; lookup CALT_RHO_SWAP; lookup CALT_RHO_UNDO;
    lookup CALT_EPSILON_THETA;
} calt;
"""


def charstring_from_ops(top, cff, ops, width):
    pen = T2CharStringPen(width, None)
    for op, args in ops:
        if op == "closePath":
            pen.closePath()
        elif op == "moveTo":
            pen.moveTo(args)
        elif op == "lineTo":
            pen.lineTo(args)
        elif op == "curveTo":
            pen.curveTo(*args)
    return pen.getCharString(private=top.Private,
                             globalSubrs=cff.cff.GlobalSubrs)


def set_charstring(top, cff, name, cs):
    """Assign a charstring, appending for brand-new glyph names (the
    CharStrings index dict has no plain __setitem__ for new entries)."""
    cs_obj = top.CharStrings
    if getattr(cs_obj, "charStringsAreIndexed", False):
        if name in cs_obj.charStrings:
            cs_obj[name] = cs
        else:
            idx = len(cs_obj.charStringsIndex)
            cs_obj.charStrings[name] = idx
            cs_obj.charStringsIndex.append(cs)
    else:
        cs_obj.charStrings[name] = cs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(ROOT / "src/fonts/grecs-roi-greek.otf"))
    ap.add_argument("--out", default=str(ROOT / "src/fonts/grecs-roi-greek-cursive.woff2"))
    args = ap.parse_args(argv)

    font = TTFont(args.base)
    cff = font["CFF "]
    top = cff.cff.topDictIndex[0]
    charstrings = top.CharStrings
    glyphset = font.getGlyphSet()
    hmtx = dict(font["hmtx"].metrics)
    order = list(font.getGlyphOrder())

    report = {"slanted": 0, "exit_flick_glyphs": [], "alternates": [],
              "cmap_added": {}, "cursive_masters": True}

    # 1. every glyph becomes a slanted+corrected master (majuscules stay
    #    upright — Estienne's caps are the upright round, only the
    #    minuscule set is the cursive revival; see plan §Phase 2.1
    #    "Greek minuscule set")
    cmap0 = font.getBestCmap()
    glyph_cps: dict[str, list[int]] = {}
    for cp, gn in cmap0.items():
        glyph_cps.setdefault(gn, []).append(cp)

    def is_upper(gn):
        cps = glyph_cps.get(gn) or []
        return bool(cps) and all(
            unicodedata.category(chr(cp)) in ("Lu", "Lt") for cp in cps)

    # snapshot the ORIGINAL outlines before touching anything: composites
    # (liga_ger, omicronsigma, precomposed accents) decompose through the
    # glyphset, so capturing them first guarantees parts are captured upright
    original = {}
    for g in order:
        if g == ".notdef":
            continue
        try:
            original[g] = _rec(glyphset, g)
        except Exception as exc:
            print(f"  skip {g}: {exc}")

    for g, cmds in original.items():
        w = hmtx.get(g, (500, 0))[0]
        ops, nw = build_master(cmds, w, g, upright=is_upper(g))
        charstrings[g] = charstring_from_ops(top, cff, ops, nw)
        hmtx[g] = (nw, 0)
        report["slanted"] += 1
        if g in EXIT_ANCHORS:
            report["exit_flick_glyphs"].append(g)

    # 2. hand-drawn alternate masters
    for name, drawer in ALTERNATES.items():
        ops, w = drawer()
        if name not in order:
            order.append(name)
        set_charstring(top, cff, name, charstring_from_ops(top, cff, ops, w))
        hmtx[name] = (w, 0)
        report["alternates"].append(name)

    # 3. rho.longtail (from the freshly slanted rho outline)
    rho_cmds = _rec(font.getGlyphSet(), "rho")
    rho_w = hmtx["rho"][0]
    ops, w = master_rho_longtail(rho_cmds, rho_w)
    if "rho.longtail" not in order:
        order.append("rho.longtail")
    set_charstring(top, cff, "rho.longtail",
                   charstring_from_ops(top, cff, ops, w))
    hmtx["rho.longtail"] = (w, 0)
    report["alternates"].append("rho.longtail")

    font.setGlyphOrder(order)
    font["hmtx"].metrics = hmtx
    font["maxp"].numGlyphs = len(order)
    try:
        charset = list(top.charset)
        for g in order:
            if g not in charset:
                charset.append(g)
        top.charset = charset
        top.encoding = charset
    except Exception as exc:
        print("charset note:", exc)

    # 4. cmap: lunate sigma codepoint -> new master; close the keraia gap
    #    (corpus elisions use U+02BC; the base derivative only mapped U+2019,
    #    so these 19 corpus words rendered tofu upstream too)
    for t in font["cmap"].tables:
        if t.isUnicode():
            t.cmap[0x03F2] = "lunateSigma"
            t.cmap[0x02BC] = "quoteright"     # greek keraia = right quote
            t.cmap[0x02BF] = "quoteright"     # greek koronis-ish fallback
    report["cmap_added"]["U+03F2"] = "lunateSigma"
    report["cmap_added"]["U+02BC"] = "quoteright (keraia — closes base tofu)"

    # 5. GSUB: drop the inherited table and rebuild everything (liga + locl
    #    + calt) from one fea source -> lookup indices are deterministic and
    #    application order (liga -> locl -> calt) is explicit.
    liga_fea = make_fea(font)
    if "GSUB" in font:
        del font["GSUB"]
    addOpenTypeFeaturesFromString(font, liga_fea)

    # 6. naming + OFL attribution
    ps = "GrecsRoiGreekCursive-Regular"
    for rec in font["name"].names:
        if rec.nameID in (1, 16):
            rec.string = "GrecsRoi Greek Cursive"
        elif rec.nameID == 4:
            rec.string = "GrecsRoi Greek Cursive Regular"
        elif rec.nameID == 6:
            rec.string = ps
        elif rec.nameID == 3:
            rec.string = f"1.001;GDR;{ps}"
        elif rec.nameID == 0:
            rec.string = (
                "Derived from GFS Gazis (c) Greek Font Society, OFL 1.1. "
                "Grecs du Roi Phase 2.1 slanted cursive masters: slant "
                "transformation with drawn ductus corrections, upright "
                "polytonic marks, hand-drawn positional alternates "
                "(locl/calt). Reserved Font Name 'GFS Gazis' is not used."
            )
        elif rec.nameID == 8:
            rec.string = "Greek Font Society (derivative: Grecs du Roi project)"
        elif rec.nameID == 9:
            rec.string = "George D. Matthiopoulos; Grecs du Roi cursive masters"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(str(out))
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    font.flavor = None
    otf = out.with_suffix(".otf")
    font.save(str(otf))
    print(f"wrote {otf} ({otf.stat().st_size} bytes)")
    meta = out.with_suffix(".masters.json")
    meta.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"masters: slanted={report['slanted']} "
          f"exit-flicks={len(report['exit_flick_glyphs'])} "
          f"alternates={report['alternates']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
