"""Render CFF glyph outlines from the built font with even-odd fill."""
import sys; sys.path.insert(0, 'tools')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from PIL import Image, ImageDraw

font = TTFont('src/fonts/grecs-roi-greek-cursive.otf')
gs = font.getGlyphSet()

def glyph_polys(gname):
    pen = RecordingPen()
    gs[gname].draw(pen)
    polys = []
    cur = []
    last = None
    for op, args in pen.value:
        if op == 'moveTo':
            if len(cur) > 2: polys.append(cur)
            cur = [list(args[0])]
            last = list(args[0])
        elif op == 'lineTo':
            cur.append(list(args[0]))
            last = list(args[0])
        elif op == 'curveTo':
            c1, c2, end = args
            p0 = last
            n = 24
            for i in range(1, n+1):
                t = i/n; mt = 1-t
                x = mt**3*p0[0] + 3*mt**2*t*c1[0] + 3*mt*t**2*c2[0] + t**3*end[0]
                y = mt**3*p0[1] + 3*mt**2*t*c1[1] + 3*mt*t**2*c2[1] + t**3*end[1]
                cur.append([x, y])
            last = list(end)
        elif op == 'closePath':
            if len(cur) > 2:
                cur.append(list(cur[0]))
                polys.append(cur)
            cur = []
    if len(cur) > 2:
        cur.append(list(cur[0]))
        polys.append(cur)
    return polys

def render_even_odd(polys, outpath, scale=3, pad=30):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)

    W = int((x1-x0)*scale) + pad*2
    H = int((y1-y0)*scale) + pad*2

    mask_arr = np.zeros((H, W), dtype=np.uint8)
    for poly in polys:
        tmp = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(tmp)
        pts = [(pad + (p[0]-x0)*scale, H - pad - (p[1]-y0)*scale) for p in poly]
        d.polygon(pts, fill=1)
        tmp_arr = np.array(tmp)
        mask_arr = ((mask_arr ^ tmp_arr) & 1).astype(np.uint8)

    mask_img = Image.fromarray((mask_arr * 255).astype(np.uint8))
    black = Image.new('RGB', (W, H), (0, 0, 0))
    white = Image.new('RGB', (W, H), (255, 255, 255))
    img = Image.composite(black, white, mask_img)
    img.save(outpath)
    print(f"Rendered {len(polys)} contours -> {outpath} ({W}x{H})")

if __name__ == '__main__':
    for gname, out in [('pi.rho', 'qa-evidence/pi-rho-render.png'),
                       ('pi', 'qa-evidence/pi-standalone-render.png')]:
        polys = glyph_polys(gname)
        render_even_odd(polys, out)
