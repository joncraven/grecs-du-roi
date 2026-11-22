#!/usr/bin/env python3
"""Scratch design renderer: draw the candidate fused πρ master with the same
pipeline as the real build (slant → handwritten_body), render to PNG so we can
compare against the Estienne scan before committing to the font."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "tools"))
from PIL import Image, ImageDraw

import cursive_masters as cm

def render_ops(ops, w, scale=2, pad=80, name="glyph"):
    """ops = list of (op, args) CFF-style recorded ops. Fill even-odd."""
    # collect polygons
    polys = []
    cur = None
    for op, args in ops:
        if op == "moveTo":
            if cur and len(cur) > 2: polys.append(cur)
            cur = [args]
        elif op == "lineTo":
            cur.append(args)
        elif op == "curveTo":
            # cubic: 3 points (c1, c2, end). Use bezier sampling.
            c1, c2, end = args
            # find the last point (last of cur or implicit)
            if cur is None: cur = []
            p0 = cur[-1] if cur else (0, 0)
            pts = [p0]
            n = 24
            for i in range(1, n+1):
                t = i/n
                mt = 1-t
                x = mt**3*p0[0] + 3*mt**2*t*c1[0] + 3*mt*t**2*c2[0] + t**3*end[0]
                y = mt**3*p0[1] + 3*mt**2*t*c1[1] + 3*mt*t**2*c2[1] + t**3*end[1]
                cur.append((x, y))
            cur[-1] = end
        elif op == "closePath":
            if cur and len(cur) > 2:
                cur.append(cur[0]); polys.append(cur)
            cur = None
    if cur and len(cur) > 2:
        cur.append(cur[0]); polys.append(cur)
    # bounds
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    W = int((x1-x0)*scale + pad*2)
    H = int((y1-y0)*scale + pad*2)
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    def tp(x, y):
        return (pad + (x-x0)*scale, H - pad - (y-y0)*scale)
    polys_p = [[tp(x, y) for (x, y) in poly] for poly in polys]
    # even-odd fill: draw all with even-odd
    d.polygon(polys_p, fill=0)
    img.save(Path(__file__).parent / f"design_{name}.png")
    print("saved", f"design_{name}.png", img.size)

def build(ops, w, name):
    """Apply slant + handwritten_body like build_override does."""
    out = []
    for cont in cm._contours(ops):
        out.extend(cm._slant_ops(cont))
        out.append(("closePath", ()))
    out = cm.handwritten_body(out, name)
    return out

if __name__ == "__main__":
    # --- candidate 1: fused pi-rho as ONE contour (pi body + rho fused) ---
    # Strategy: take master_pi_var's omega body (pi), then attach a rho bowl
    # + tail on the RIGHT that shares the pi's right lobe as its entry.
    # We draw: pi omega body (3 lobes) + a rho loop starting from the right
    # lobe's top-right, looping up-right and back down as a tail.
    # Simpler: pi body (from master_pi_var) + a separate rho contour that
    # overlaps the right lobe. handwritten_body will fuse the overlap.
    pi_ops, pi_w = cm.master_pi_var()
    # Draw a cursive rho: bowl + right tail
    rho_ops = [
        # bowl: start at left (shared with pi's right lobe), curve up-right,
        # around, back down
        ("moveTo", (700, 300)),
        ("curveTo", ((700, 120), (820, 20), (960, 30))),
        ("curveTo", ((1100, 40), (1180, 160), (1160, 300))),
        ("curveTo", ((1140, 420), (1020, 500), (880, 480))),
        ("curveTo", ((800, 466), (740, 420), (720, 360))),
        ("curveTo", ((710, 340), (705, 320), (700, 300))),
        ("closePath", ()),
        # inner bowl (counter)
        ("moveTo", (800, 300)),
        ("curveTo", ((800, 180), (870, 100), (960, 100))),
        ("curveTo", ((1050, 100), (1110, 180), (1100, 290))),
        ("curveTo", ((1090, 380), (1010, 440), (920, 430))),
        ("curveTo", ((850, 420), (810, 380), (800, 300))),
        ("closePath", ()),
        # tail: from bowl bottom-right sweeping down-left
        ("moveTo", (1050, 440)),
        ("curveTo", ((1080, 460), (1100, 480), (1100, 510))),
        ("curveTo", ((1080, 490), (1060, 470), (1050, 440))),
        ("closePath", ()),
    ]
    # Render pi alone, rho alone, and fused
    build_ops_pi = build(pi_ops, pi_w, "pi")
    build_ops_fused = build(pi_ops + rho_ops, pi_w + 450, "fused")
    render_ops(build_ops_pi, pi_w, name="pi_var_standalone")
    render_ops(build_ops_fused, pi_w + 450, name="fused_pi_rho")
