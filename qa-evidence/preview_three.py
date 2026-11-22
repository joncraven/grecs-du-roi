#!/usr/bin/env python3
"""Patch pi / pi.rho / lig2_uni1F26_nu into the live OTF and hb-view."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import cursive_masters as cm
import drawn_ligatures as dl
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OTF = ROOT / "src/fonts/grecs-roi-greek-cursive.otf"
OUT = Path("/tmp/t_8ad4e391_preview")
OUT.mkdir(exist_ok=True)


def slant_ops(ops0):
    out = []
    for cont in cm._contours(ops0):
        out.extend(cm._slant_ops(cont))
        out.append(("closePath", ()))
    return out


def main():
    font = TTFont(str(OTF))
    cff = font["CFF "]
    top = cff.cff.topDictIndex[0]
    hmtx = font["hmtx"].metrics

    pi_ops, pi_w = cm.build_override(dl.master_pi_flat, "pi")
    cm.set_charstring(top, cff, "pi", cm.charstring_from_ops(top, cff, pi_ops, pi_w))
    hmtx["pi"] = (pi_w, 0)

    pr_ops, pr_w = dl.alt_pi_rho()
    pr_ops = slant_ops(pr_ops)
    right = 0.0
    for cont in cm._contours(pr_ops):
        for x, _y in cm._contour_pts(cont):
            right = max(right, x)
    pr_w = max(pr_w, int(right) + 8)
    cm.set_charstring(top, cff, "pi.rho", cm.charstring_from_ops(top, cff, pr_ops, pr_w))
    hmtx["pi.rho"] = (pr_w, 0)

    body, bw = dl.alt_eta_nu()
    body = slant_ops(body)
    right = 0.0
    for cont in cm._contours(body):
        for x, _y in cm._contour_pts(cont):
            right = max(right, x)
    bw = max(bw, int(right) + 8)
    cm.set_charstring(top, cff, "eta.nu", cm.charstring_from_ops(top, cff, body, bw))
    hmtx["eta.nu"] = (bw, 0)

    ops = []
    for cont in cm._contours(body):
        ops.extend(cont)
        ops.append(("closePath", ()))
    for cont in cm._contours(dl.alt_eta_nu_marks()):
        ops.extend(cm._slant_ops(cont))
        ops.append(("closePath", ()))
    name = "lig2_uni1F26_nu"
    cm.set_charstring(top, cff, name, cm.charstring_from_ops(top, cff, ops, bw))
    hmtx[name] = (bw, 0)

    font["hmtx"].metrics = hmtx
    dest = OUT / "preview.otf"
    font.save(str(dest))
    print("wrote", dest, "pi_w", pi_w, "pr_w", pr_w, "bw", bw)


if __name__ == "__main__":
    main()
