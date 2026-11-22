#!/usr/bin/env python3
"""Patch pi.rho / eta.nu / ἦν stamps into a copy of the cursive OTF and hb-view."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import cursive_masters as cm
import drawn_ligatures as dl
from fontTools.ttLib import TTFont

SRC = ROOT / "src/fonts/grecs-roi-greek-cursive.otf"
OUT = Path("/tmp/t_8ad4e391_preview.otf")
DIR = Path("/tmp/t_8ad4e391_r7")


def slant_ops(ops0):
    slanted = []
    for cont in cm._contours(ops0):
        slanted.extend(cm._slant_ops(cont))
        slanted.append(("closePath", ()))
    return slanted


def advance(ops, w):
    right = 0.0
    for cont in cm._contours(ops):
        for x, _y in cm._contour_pts(cont):
            right = max(right, x)
    return max(w, int(right) + 8)


def main():
    shutil.copy2(SRC, OUT)
    font = TTFont(str(OUT))
    cff = font["CFF "]
    top = cff.cff.topDictIndex[0]
    hmtx = font["hmtx"].metrics

    def put(name, ops, w):
        w = advance(ops, w)
        cs = cm.charstring_from_ops(top, cff, ops, w)
        cm.set_charstring(top, cff, name, cs)
        hmtx[name] = (w, 0)
        print(f"  {name} w={w}")

    pi_rho, w = dl.alt_pi_rho()
    put("pi.rho", slant_ops(pi_rho), w)

    body, bw = dl.alt_eta_nu()
    body_s = slant_ops(body)
    bw = advance(body_s, bw)
    put("eta.nu", body_s, bw)

    marks = slant_ops(dl.alt_eta_nu_marks())
    for lig, extra in (
        ("lig2_eta_nu", None),
        ("lig2_uni1F26_nu", marks),
        ("lig2_uni1F23_nu", None),
    ):
        ops = list(body_s)
        if extra:
            ops.extend(extra)
        put(lig, ops, bw)

    # ἤν keeps oxia from the live uni1F24 marks, scaled like ligature_engine.
    acc = "uni1F24"
    if acc in font.getGlyphOrder():
        gs = font.getGlyphSet()
        orig = {}
        # reuse recording via cm helpers already on the live font
        from fontTools.pens.recordingPen import DecomposingRecordingPen
        pen = DecomposingRecordingPen(gs)
        gs[acc].draw(pen)
        acc_ops = list(pen.value)
        mark_conts = []
        for cont in cm._contours(acc_ops):
            ys = [p[1] for p in cm._contour_pts(cont)]
            if ys and min(ys) >= cm.MARK_Y_MIN:
                mark_conts.append(cont)
        ops = list(body_s)
        if mark_conts:
            xs, ys = [], []
            for c in mark_conts:
                for x, y in cm._contour_pts(c):
                    xs.append(x); ys.append(y)
            bowl_top = 0.0
            for cont in cm._contours(body_s):
                for x, y in cm._contour_pts(cont):
                    if x >= bw * 0.45:
                        bowl_top = max(bowl_top, y)
            cx = sum(xs) / len(xs)
            mn = min(ys)
            s = 0.50
            dx = bw * 0.68 - cx
            dy = (bowl_top + 8) - mn

            def xf(x, y):
                return ((x - cx) * s + cx + dx, (y - mn) * s + mn + dy)

            for cont in mark_conts:
                for op, pts in cont:
                    if op == "closePath":
                        ops.append((op, ()))
                    elif op in ("moveTo", "lineTo"):
                        ops.append((op, xf(pts[0], pts[1])))
                    elif op == "curveTo":
                        ops.append((op, tuple(xf(x, y) for (x, y) in pts)))
                ops.append(("closePath", ()))
        put("lig2_uni1F24_nu", ops, bw)

    font["hmtx"].metrics = hmtx
    font.save(str(OUT))
    DIR.mkdir(exist_ok=True)
    for text, name in (("π", "pi"), ("πρ", "pr"), ("πρὸς", "pros"),
                       ("ἦν", "hn26"), ("ἤν", "hn24"), ("παρὰ", "para")):
        dest = DIR / f"{name}.png"
        subprocess.check_call([
            "hb-view", "--font-size", "180",
            "-O", "png", "-o", str(dest), str(OUT), text,
        ])
        print("wrote", dest)


if __name__ == "__main__":
    main()
