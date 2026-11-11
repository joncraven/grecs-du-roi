#!/usr/bin/env python3
"""cursive_masters.py — Phase 2.1: slanted cursive masters + positional alternates.

Builds src/fonts/grecs-roi-greek-cursive.otf/.woff2 as a NEW face beside the
upright derivative (grecs-roi-greek.otf stays byte-identical, so the shipped
page and its copy invariant stay green while 2.2/2.4 land).

True masters, not a faux-italic shear — the shear is only the interpolation
starting point (decision D1=C, plan §Phase 2.1):

  1. body contours slant right (11 deg, baseline pivot);
  2. handwritten ductus on minuscules only (majuscules stay untouched):
     even the stroke by expanding hairlines and organic cubic handles
     so the body no longer reads as a sheared Didone next to the upright caps;
  3. accent/breathing contours stay UPRIGHT (only nudged right to sit over the
     leaning body) — plan §7: polytonic stacks must not drift with the shear;
  4. hand-drawn cursive masters for the positional alternates: lunate sigma
     (U+03F2), drawn final + medial sigma, deep-tailed initial rho, cursive
     medial epsilon and theta, then the same ductus pass so they share ink.

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

ROOT = Path(__file__).resolve().parent.parent

ANGLE = 11.0
SKEW = math.tan(math.radians(ANGLE))
MARK_DX_Y = 210.0        # marks nudge right as if slanted only to this height
MARK_Y_MIN = 460         # contour with min-y >= this = accent/breathing layer

# ---- handwritten minuscule ductus (t_cd94bc54) -----------------------------
# Modest on purpose: enough to kill Gazis Didone hairlines, not so heavy that
# the body outweighs the upright Gazis caps on the same page. No extra flick
# contours — a detached ribbon reads as a computer tick, not a pen join
# (joins live in Phase 2.2 ligatures).
EMBOLDEN = 8.5          # contour offset (u); stroke grows ~17u, thins more relatively
ORGANIC = 2.4           # cubic-handle wobble (u), deterministic per glyph

ALT_RHO_SCALE = 1.55     # sub-baseline tail stretch for the longtail master


def _slant_pt(x: float, y: float):
    return (x + SKEW * y, y)


def _rec(glyphset, name):
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(pen)
    return pen.value


def _as_pt(args):
    """RecordingPen wraps points as args[0]=(x,y); our builders store (x,y)."""
    if not args:
        return args
    a0 = args[0]
    if isinstance(a0, (int, float)):
        return args
    return a0


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
            cur = [("moveTo", _as_pt(args))]
        elif op == "lineTo":
            cur.append(("lineTo", _as_pt(args)))
        elif op == "curveTo":
            pts = tuple(args) if (args and isinstance(args[0], tuple) and len(args[0]) == 2) else tuple(args)
            # RecordingPen: args = ((x1,y1),(x2,y2),(x3,y3))
            cur.append(("curveTo", pts))
        elif op == "qCurveTo":
            cur.append(("curveTo", tuple(_as_pt((a,)) if not isinstance(a, tuple) else a for a in args)))
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


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _vadd(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _vmul(a, s):
    return (a[0] * s, a[1] * s)


def _vnorm(a):
    l = math.hypot(a[0], a[1])
    if l < 1e-9:
        return (0.0, 0.0)
    return (a[0] / l, a[1] / l)


def _signed_area_pts(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def _contour_bbox(cont):
    xs, ys = [], []
    for p in _contour_pts(cont):
        xs.append(p[0])
        ys.append(p[1])
    if not xs:
        return (0, 0, 0, 0)
    return (min(xs), min(ys), max(xs), max(ys))


def _offset_pts(pts, dist):
    """Polyline offset along averaged left normals, miter-capped."""
    n = len(pts)
    if n < 2:
        return list(pts)
    out = []
    for i in range(n):
        prev = pts[i - 1]
        cur = pts[i]
        nxt = pts[(i + 1) % n]
        t_in = _vnorm(_vsub(cur, prev))
        t_out = _vnorm(_vsub(nxt, cur))
        if t_in == (0.0, 0.0):
            t_in = t_out
        if t_out == (0.0, 0.0):
            t_out = t_in
        n_in = (-t_in[1], t_in[0])
        n_out = (-t_out[1], t_out[0])
        nx, ny = n_in[0] + n_out[0], n_in[1] + n_out[1]
        nl = math.hypot(nx, ny)
        if nl < 1e-6:
            nx, ny = n_out
            nl = math.hypot(nx, ny) or 1.0
        nx, ny = nx / nl, ny / nl
        # miter: 1 / cos(half) ~ 1 / dot(n_in, n_avg)
        d = n_in[0] * nx + n_in[1] * ny
        miter = 1.0 / d if abs(d) > 0.22 else (4.0 if d >= 0 else -4.0)
        miter = max(-3.5, min(3.5, miter))
        out.append((cur[0] + nx * dist * miter, cur[1] + ny * dist * miter))
    return out


def _point_in_contour(pt, cont):
    """Even-odd ray cast on the on-curve polygon (good enough for holes)."""
    pts = list(_contour_pts(cont))
    x, y = pt
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y):
            den = (yj - yi) or 1e-12
            if x < (xj - xi) * (y - yi) / den + xi:
                inside = not inside
        j = i
    return inside


def _span(pts):
    return ((max(p[0] for p in pts) - min(p[0] for p in pts))
            + (max(p[1] for p in pts) - min(p[1] for p in pts)))


def _rebuild_contour(cont, off):
    rebuilt, i = [], 0
    for op, args in cont:
        if op in ("moveTo", "lineTo"):
            rebuilt.append((op, off[i]))
            i += 1
        elif op == "curveTo":
            rebuilt.append((op, (off[i], off[i + 1], off[i + 2])))
            i += 3
        else:
            rebuilt.append((op, args))
    return rebuilt


def _thicken_contour(cont, dist, want_grow):
    """Offset so an outer grows and a hole shrinks. Tiny contours skipped."""
    pts = list(_contour_pts(cont))
    if len(pts) < 3:
        return list(cont)
    x0, y0, x1, y1 = _contour_bbox(cont)
    if (x1 - x0) < 28 and (y1 - y0) < 28:
        return list(cont)
    off_pos = _offset_pts(pts, dist)
    grew = _span(off_pos) >= _span(pts) - 0.5
    off = off_pos if (want_grow == grew) else _offset_pts(pts, -dist)
    return _rebuild_contour(cont, off)


def _organic_contour(cont, rng):
    """Nudge cubic handles perpendicular to their chord — a written, not
    plotted, curve. On-curve points stay put so joins don't tear."""
    out = []
    for op, args in cont:
        if op != "curveTo":
            out.append((op, args))
            continue
        p1, p2, p3 = args
        # previous on-curve is whatever we last emitted
        prev = None
        for o2, a2 in reversed(out):
            if o2 in ("moveTo", "lineTo"):
                prev = a2
                break
            if o2 == "curveTo":
                prev = a2[-1]
                break
        if prev is None:
            out.append((op, args))
            continue
        chord = _vsub(p3, prev)
        nrm = _vnorm((-chord[1], chord[0]))
        k1 = rng() * ORGANIC
        k2 = rng() * ORGANIC
        np1 = _vadd(p1, _vmul(nrm, k1))
        np2 = _vadd(p2, _vmul(nrm, k2))
        out.append(("curveTo", (np1, np2, p3)))
    return out


def _rng(name):
    h = 2166136261
    for c in name:
        h ^= ord(c)
        h = (h * 16777619) & 0xFFFFFFFF

    def nxt():
        nonlocal h
        h = (h * 1664525 + 1013904223) & 0xFFFFFFFF
        return (h / 4294967295.0) * 2.0 - 1.0

    return nxt


def handwritten_body(ops, name):
    """Didone → written: even the stroke, organic cubics. No flicks here."""
    rng = _rng(name)
    contours = _contours(ops)
    holes = [False] * len(contours)
    cents, areas = [], []
    for c in contours:
        pts = list(_contour_pts(c))
        if pts:
            cents.append((sum(p[0] for p in pts) / len(pts),
                          sum(p[1] for p in pts) / len(pts)))
            areas.append(abs(_signed_area_pts(pts)))
        else:
            cents.append((0.0, 0.0))
            areas.append(0.0)
    for i in range(len(contours)):
        for j, other in enumerate(contours):
            if i == j or areas[j] <= areas[i]:
                continue
            if _point_in_contour(cents[i], other):
                holes[i] = True
                break
    out = []
    for i, cont in enumerate(contours):
        thick = _thicken_contour(cont, EMBOLDEN, want_grow=not holes[i])
        thick = _organic_contour(thick, rng)
        out.extend(thick)
        out.append(("closePath", ()))
    return out


def build_master(cmds, width, name, upright=False):
    """Return (ops, new_width): slanted body + handwritten ductus + upright
    marks. Majuscules (`upright=True`) copy through."""
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
    if has_body:
        ops = handwritten_body(ops, name)
        # recompute right extent after thicken
        body_right = 0.0
        for cont in _contours(ops):
            for x, y in _contour_pts(cont):
                body_right = max(body_right, x)
    mark_dx = SKEW * MARK_DX_Y if has_body else 0.0
    for cont in mark_ops:
        ops.extend(_nudge_ops(cont, mark_dx))
        ops.append(("closePath", ()))

    w = width
    # advance follows the slanted+thickened extent, near-zero right side bearing
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

    report = {"slanted": 0, "alternates": [],
              "cmap_added": {}, "cursive_masters": True,
              "handwritten_minuscules": True,
              "embolden": EMBOLDEN, "organic": ORGANIC}

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

    # 2. hand-drawn alternate masters (same ductus so they share ink)
    for name, drawer in ALTERNATES.items():
        ops, w = drawer()
        ops = handwritten_body(ops, name)
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
            rec.string = f"1.003;GDR;{ps}"
        elif rec.nameID == 0:
            rec.string = (
                "Derived from GFS Gazis (c) Greek Font Society, OFL 1.1. "
                "Grecs du Roi Phase 2.1 slanted cursive masters: slant "
                "transformation with handwritten minuscule ductus "
                "(evened stroke, organic cubics), upright "
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
          f"alternates={report['alternates']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
