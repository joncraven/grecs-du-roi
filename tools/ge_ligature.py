#!/usr/bin/env python3
"""ge_ligature.py — t_a5e3138b round 2: a TRUE initial γε ligature glyph.

Round 1 shipped lig2_gamma_epsilon as the plain fuse_outline composite
(epsilon slid left by a 5% overlap). Gamma's ink at the baseline band
sits deep left (its descender curls to x<250) while epsilon started at
x≈612 — a ~220u hole under gamma's rising arm: epsilon read as floating
and the pair read as two loose letters (live KO on
greek.craven.fr/estienne-john1.html, 2026-11-15 dashboard comment).

Round 2 owns the glyph design in ONE place (the engine calls into it via
build_ops(glyphset); run standalone to (re)patch the shipped font):

  * epsilon pulled to a 12% overlap (offset 559),
  * a hand-drawn tapered bridge fills the hole under gamma's arm, joining
    gamma's inner-right edge (~x 500 y 280) to epsilon's left flank
    (~x 640 y 280), oriented to match the letters' winding so the
    nonzero-rule union reads as ONE connected glyph.

Commands:
  python3 tools/ge_ligature.py patch [font]   rewrite the glyph in place
  python3 tools/ge_ligature.py ops            dump design stats (json)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import cursive_masters as cm  # noqa: E402

FONT = ROOT / "src/fonts/grecs-roi-greek-cursive.otf"
GE_GLYPH = "lig2_gamma_epsilon"

EPS_XOFF = 545      # int(round(635 * 0.858)) — ~14% overlap into gamma


def _rec(glyphset, name):
    pen = RecordingPen()
    glyphset[name].draw(pen)
    return pen.value


def _bridge_contour():
    """Tapered pen-tongue from gamma's rising arm down-left rim into
    epsilon's left flank: fills the triangular hole beneath gamma's arm
    (the reason round 1 read as two letters). Spine starts DEEP inside
    gamma's arm (buried ~60u), runs with the arm's slope, ends buried in
    epsilon's left bowl so nonzero fill unions cleanly at both joints."""
    # spine stations (x, y, half_width) — thin calligraphic tongue: starts
    # at gamma's arm weight, eases down to ~30u where it meets epsilon
    S = [
        (400, 185, 46),   # deep inside gamma's rising arm
        (470, 215, 44),
        (540, 246, 38),
        (595, 268, 31),
        (636, 282, 22),   # buried in epsilon's left bowl
    ]
    top = [(x, y + hw) for x, y, hw in S]
    bot = [(x, y - hw) for x, y, hw in S]
    ops = [("moveTo", tuple(top[0]))]
    for x, y in top[1:]:
        ops.append(("curveTo", ((x - 40, y - 1), (x - 20, y), (x, y))))
    # tip at epsilon: small round cap
    x1, y1 = bot[-1]
    ops.append(("curveTo", ((x1 + 26, y1 + 20), (x1 + 26, y1 - 20), (x1, y1))))
    for x, y in reversed(bot[:-1]):
        ops.append(("curveTo", ((x + 40, y + 1), (x + 20, y), (x, y))))
    # round cap back at gamma
    x0, y0 = top[0]
    ops.append(("curveTo", ((x0 - 26, y0 + 46), (x0 - 26, y0 + 54), (x0, y0))))
    ops.append(("closePath", ()))
    return ops


def _reversed_contour(cont):
    """Reverse pen winding for a recording-pen contour list."""
    return cm._contours([("moveTo", cont[-1][1] if isinstance(cont[-1], tuple) else cont[-1])]) and _flip(cont)


def _flip(cont):
    """Flip a closed contour's winding: ops list -> reversed segment order.

    Recording contours here are [moveTo p0, curveTo (a,b,p1), ..., closePath].
    Reversal = start at last on-curve point, walk segments backwards swapping
    cubic control pairs."""
    on_first = cont[0][1]
    segs = []
    prev = on_first
    for c, v in cont[1:]:
        if c == "closePath":
            break
        if c == "curveTo" and isinstance(v[0], tuple) and len(v) == 3:
            segs.append((v[0], v[1], v[2]))
            prev = v[2]
        elif c == "curveTo":
            segs.append((v, None, None))
            prev = v
        elif c == "lineTo":
            segs.append((v, None, None))
            prev = v
    out = []
    start = prev
    out.append(("moveTo", start))
    for i in range(len(segs) - 1, -1, -1):
        a, b, p = segs[i]
        if b is None:
            nxt = out[-1][1] if i == len(segs) - 1 else None
            # line segment: target is previous segment's endpoint
            target = segs[i - 1][2] if i > 0 else on_first
            if not isinstance(target, tuple):
                target = on_first
            out.append(("lineTo", target))
        else:
            target = segs[i - 1][2] if i > 0 else on_first
            out.append(("curveTo", (b, a, target)))
    out.append(("closePath", ()))
    return out


def build_ops(glyphset):
    """(ops, advance) for the true initial γε ligature. Winding-safe:
    the bridge is oriented to match the letters so nonzero fill unions."""
    ops = []
    gamma_c = cm._contours(_rec(glyphset, "gamma"))[0]
    eps_c = cm._contours(_rec(glyphset, "epsilon"))[0]
    area_g = cm._signed_area_pts(list(cm._contour_pts(gamma_c)))
    ops.extend(gamma_c)
    ops.append(("closePath", ()))
    shifted = cm._nudge_ops(eps_c, EPS_XOFF)
    # keep epsilon's own winding
    ops.extend(shifted)
    ops.append(("closePath", ()))
    bridge = _bridge_contour()
    area_b = cm._signed_area_pts([p for c, v in bridge for p in _pts_of(v)])
    if (area_b > 0) != (area_g > 0):
        bridge = _flip(bridge)
    ops.extend(bridge)
    ops.append(("closePath", ()))
    return ops, EPS_XOFF + 469


def _pts_of(v):
    if isinstance(v, tuple) and v and isinstance(v[0], tuple):
        return v
    if isinstance(v, tuple) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
        return [v]
    return []


def patch(font_path=FONT):
    font_path = Path(font_path)
    font = TTFont(str(font_path))
    assert GE_GLYPH in font.getGlyphOrder(), f"{GE_GLYPH} missing"
    ops, w = build_ops(font.getGlyphSet())
    cff = font["CFF "]
    top = cff.cff.topDictIndex[0]
    cs = cm.charstring_from_ops(top, cff, ops, w)
    cm.set_charstring(top, cff, GE_GLYPH, cs)
    font["hmtx"].metrics[GE_GLYPH] = (w, 0)
    font.flavor = None
    font.save(str(font_path))
    font.flavor = "woff2"
    font.save(str(font_path.with_suffix(".woff2")))
    return w


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ops"
    f = TTFont(str(FONT))
    if cmd == "ops":
        ops, w = build_ops(f.getGlyphSet())
        conts = cm._contours(ops)
        stat = {"advance": w, "contours": len(conts)}
        print(json.dumps(stat, indent=2))
    elif cmd == "patch":
        target = Path(sys.argv[2]) if len(sys.argv) > 2 else FONT
        print(f"patched {GE_GLYPH} in {target} -> advance {patch(target)}")
    else:
        raise SystemExit(f"unknown cmd {cmd}")
