#!/usr/bin/env python3
"""Render π / πρὸς / ἦν from the built font next to each other."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import numpy as np
from PIL import Image, ImageDraw
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
import uharfbuzz as hb

FONT = str(ROOT / "src/fonts/grecs-roi-greek-cursive.otf")
tt = TTFont(FONT)
gs = tt.getGlyphSet()
SFEATS = {"liga": 1, "clig": 1, "dlig": 1, "hlig": 1, "calt": 1, "locl": 1}


def glyph_polys(gname, dx=0):
    pen = RecordingPen()
    gs[gname].draw(pen)
    polys, cur, last = [], [], None
    for op, args in pen.value:
        if op == "moveTo":
            if len(cur) > 2:
                polys.append(cur)
            cur = [(args[0][0] + dx, args[0][1])]
            last = args[0]
        elif op == "lineTo":
            cur.append((args[0][0] + dx, args[0][1]))
            last = args[0]
        elif op == "curveTo":
            c1, c2, end = args
            p0 = last
            n = 20
            for i in range(1, n + 1):
                t = i / n
                mt = 1 - t
                x = mt**3*p0[0] + 3*mt**2*t*c1[0] + 3*mt*t**2*c2[0] + t**3*end[0]
                y = mt**3*p0[1] + 3*mt**2*t*c1[1] + 3*mt*t**2*c2[1] + t**3*end[1]
                cur.append((x + dx, y))
            last = end
        elif op == "closePath":
            if len(cur) > 2:
                cur.append(cur[0])
                polys.append(cur)
            cur = []
    if len(cur) > 2:
        cur.append(cur[0])
        polys.append(cur)
    return polys


def render_even_odd(polys, outpath, scale=1.2, pad=40, xor=False):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    W = int((x1 - x0) * scale) + pad * 2
    H = int((y1 - y0) * scale) + pad * 2

    def tp(p):
        return (pad + (p[0] - x0) * scale, H - pad - (p[1] - y0) * scale)

    if xor:
        mask = np.zeros((H, W), dtype=np.uint8)
        for poly in polys:
            tmp = Image.new("L", (W, H), 0)
            ImageDraw.Draw(tmp).polygon([tp(p) for p in poly], fill=1)
            mask = ((mask ^ np.array(tmp)) & 1).astype(np.uint8)
        Image.fromarray(((1 - mask) * 255).astype(np.uint8)).save(outpath)
    else:
        img = Image.new("L", (W, H), 255)
        d = ImageDraw.Draw(img)
        signed = []
        for poly in polys:
            area = 0.0
            for i in range(len(poly) - 1):
                x1_, y1_ = poly[i]
                x2_, y2_ = poly[i + 1]
                area += x1_ * y2_ - x2_ * y1_
            signed.append((abs(area), area, poly))
        signed.sort(reverse=True)
        outer_sign = signed[0][1]
        for _ab, area, poly in signed:
            # opposite winding → hole (white); same winding → union (black)
            fill = 255 if (area != 0 and (area > 0) != (outer_sign > 0)) else 0
            d.polygon([tp(p) for p in poly], fill=fill)
        img.save(outpath)
    print("wrote", outpath, W, H)


def shape(text):
    blob = hb.Blob.from_file_path(FONT)
    font = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.script = "grek"
    hb.shape(font, buf, SFEATS)
    names, pos = [], []
    x = 0
    for info, p in zip(buf.glyph_infos, buf.glyph_positions):
        names.append(font.get_glyph_name(info.codepoint))
        pos.append(x + p.x_offset)
        x += p.x_advance
    return names, pos


if __name__ == "__main__":
    out = ROOT / "qa-evidence"
    for g, fn in [
        ("pi", "built-pi.png"),
        ("pi.rho", "built-pi-rho.png"),
        ("eta.nu", "built-eta-nu.png"),
        ("lig2_uni1F26_nu", "built-hvn.png"),
        ("lig2_uni1F23_nu", "built-hvn-grave.png"),
    ]:
        render_even_odd(glyph_polys(g), out / fn)

    for text, fn in [("πρὸς", "built-pros-word.png"), ("ἦν", "built-hn-word.png"),
                     ("π", "built-pi-word.png")]:
        names, pos = shape(text)
        print(text, names)
        polys = []
        for n, dx in zip(names, pos):
            polys.extend(glyph_polys(n, dx))
        render_even_odd(polys, out / fn, scale=1.6)
