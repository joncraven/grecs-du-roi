#!/usr/bin/env python3
"""Recompute glyf bounding boxes in a shipped TrueType-flavour webfont.

Punch-list minor 4 (t_1bdfa688): the shipped gfs-didot.woff2 carries 106
glyphs whose stored glyf bbox under-flows the real outline (an artifact of
GFS Didot's FFTM hinting surviving subsetting). Firefox logs a console
warning per rendered glyph. This script loads the woff2, recomputes every
bbox with a BoundsPen and stores integer bounds rounded outward, and saves
back — glyph outlines and metrics are untouched, only the four bbox ints
grow where they were too small.

  python3 tools/fix_font_bboxes.py src/fonts/gfs-didot.woff2

build_typography.py applies the same pass (fix_glyf_bboxes) when it builds
Didot from scratch; this is the in-place repair for an already-shipped file.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont


def fix_glyf_bboxes(font: TTFont) -> int:
    glyf = font["glyf"]
    gs = font.getGlyphSet()
    fixed = 0
    for gname in glyf.keys():
        g = glyf[gname]
        if g.numberOfContours <= 0 and not getattr(g, "components", None):
            continue
        pen = BoundsPen(gs)
        try:
            g.draw(pen, gs)
        except Exception:
            continue
        b = pen.bounds
        if b is None:
            continue
        new = (math.floor(b[0]), math.floor(b[1]), math.ceil(b[2]), math.ceil(b[3]))
        if new != (g.xMin, g.yMin, g.xMax, g.yMax):
            g.xMin, g.yMin, g.xMax, g.yMax = new
            fixed += 1
    return fixed


def main(path: str) -> int:
    p = Path(path)
    font = TTFont(str(p))
    fixed = fix_glyf_bboxes(font)
    font.save(str(p))
    print(f"{p.name}: recomputed bbox on {fixed} glyphs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "src/fonts/gfs-didot.woff2"))
