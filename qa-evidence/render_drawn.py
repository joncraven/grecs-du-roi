#!/usr/bin/env python3
"""Render drawn_ligatures candidates (slant only for ligatures)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import numpy as np
from PIL import Image, ImageDraw
import cursive_masters as cm
import drawn_ligatures as dl


def polys_from_ops(ops):
    polys, cur = [], None
    for op, args in ops:
        if op == "moveTo":
            if cur and len(cur) > 2:
                polys.append(cur)
            cur = [args]
        elif op == "lineTo":
            if cur is not None:
                cur.append(args)
        elif op == "curveTo":
            c1, c2, end = args
            p0 = cur[-1] if cur else (0, 0)
            n = 20
            for i in range(1, n + 1):
                t = i / n
                mt = 1 - t
                x = mt**3*p0[0] + 3*mt**2*t*c1[0] + 3*mt*t**2*c2[0] + t**3*end[0]
                y = mt**3*p0[1] + 3*mt**2*t*c1[1] + 3*mt*t**2*c2[1] + t**3*end[1]
                if cur is not None:
                    cur.append((x, y))
            if cur is not None:
                cur[-1] = end
        elif op == "closePath":
            if cur and len(cur) > 2:
                cur.append(cur[0])
                polys.append(cur)
            cur = None
    if cur and len(cur) > 2:
        cur.append(cur[0])
        polys.append(cur)
    return polys


def render(ops, path, scale=1.5, pad=40, even_odd=False):
    polys = polys_from_ops(ops)
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W = int((x1 - x0) * scale + pad * 2)
    H = int((y1 - y0) * scale + pad * 2)

    def tp(x, y):
        return (pad + (x - x0) * scale, H - pad - (y - y0) * scale)

    if even_odd:
        mask = np.zeros((H, W), dtype=np.uint8)
        for poly in polys:
            tmp = Image.new("L", (W, H), 0)
            ImageDraw.Draw(tmp).polygon([tp(x, y) for x, y in poly], fill=1)
            mask = ((mask ^ np.array(tmp)) & 1).astype(np.uint8)
        img = Image.fromarray((1 - mask) * 255)
    else:
        img = Image.new("L", (W, H), 255)
        d = ImageDraw.Draw(img)
        for poly in polys:
            d.polygon([tp(x, y) for x, y in poly], fill=0)
    img.save(path)
    print("wrote", path, img.size)


def slant(ops):
    out = []
    for cont in cm._contours(ops):
        out.extend(cm._slant_ops(cont))
        out.append(("closePath", ()))
    return out


if __name__ == "__main__":
    outdir = ROOT / "qa-evidence"
    ops, _ = dl.master_pi_flat()
    ink = cm.build_override(dl.master_pi_flat, "pi")[0]
    render(ops, outdir / "drawn-pi-flat-raw.png")
    render(ink, outdir / "drawn-pi-flat-ink.png")

    ops, _ = dl.alt_pi_rho()
    render(ops, outdir / "drawn-pi-rho-raw.png", even_odd=True)
    render(slant(ops), outdir / "drawn-pi-rho-ink.png", even_odd=True)

    ops, _ = dl.alt_eta_nu()
    render(ops, outdir / "drawn-hvn-raw.png")
    render(slant(ops), outdir / "drawn-hvn-ink.png")
