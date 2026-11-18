#!/usr/bin/env python3
"""Render lig2_gamma_epsilon (current font state) big, for eyeball QA.
Flattens cubics properly so what we see is what the rasteriser fills."""
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

def contours_of(font, g):
    pen = RecordingPen(); font.getGlyphSet()[g].draw(pen)
    conts, cur = [], None
    for c, v in pen.value:
        if c == 'moveTo':
            cur = [('M', v[0])]; conts.append(cur)
        elif c == 'curveTo' and cur is not None:
            cur.append(('C', v))
        elif c == 'lineTo' and cur is not None:
            cur.append(('L', v[0]))
    return conts

def flatten(cont, n=20):
    pts = []
    prev = cont[0][1]; pts.append(prev)
    for kind, v in cont[1:]:
        if kind == 'L':
            pts.append(v); prev = v
        else:
            cps = [p for p in v if isinstance(p, tuple)]
            if len(cps) == 3:
                p1, p2, p3 = cps
            else:
                p1, p3 = cps; p2 = p3
            seg = []
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                x = mt**3*prev[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0]
                y = mt**3*prev[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]
                seg.append((x, y))
            pts.extend(seg); prev = seg[-1]
    return pts

def render(font_path, glyph, out, scale=2.2, pad=100):
    f = TTFont(str(font_path))
    w = f.getGlyphSet()[glyph].width
    img = Image.new("L", (int(w*scale) + 2*pad, int(800*scale)), 255)
    d = ImageDraw.Draw(img)
    base = int(600*scale) + pad
    for cont in contours_of(f, glyph):
        pl = [(pad + x*scale, base - y*scale) for x, y in flatten(cont)]
        d.polygon(pl, fill=0)
    d.line([(0, base), (img.width, base)], fill=190, width=2)
    img.convert("RGB").save(out)
    print(out)

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3])
