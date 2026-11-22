#!/usr/bin/env python3
from PIL import Image, ImageDraw
from pathlib import Path

root = Path("/Volumes/RAID10/Projects/grecs-du-roi/.worktrees/t_8ad4e391")
att = Path("/Users/hermes/.hermes/kanban/boards/latin/attachments/t_8ad4e391")
pairs = [
    ("pi 10.56.49", att / "Screenshot 2026-11-19 at 10.56.49.png", root / "qa-evidence/hb-pi.png"),
    ("pros 10.56.22", att / "Screenshot 2026-11-19 at 10.56.22.png", root / "qa-evidence/hb-pros.png"),
    ("hn 10.55.18", att / "Screenshot 2026-11-19 at 10.55.18.png", root / "qa-evidence/hb-hn.png"),
]
W, H = 420, 280
cols = []
for title, scan, built in pairs:
    s = Image.open(scan).convert("RGB")
    b = Image.open(built).convert("RGB")

    def fit(im, w, h):
        im = im.copy()
        im.thumbnail((w, h - 28))
        canvas = Image.new("RGB", (w, h - 28), (255, 255, 255))
        canvas.paste(im, ((w - im.size[0]) // 2, (h - 28 - im.size[1]) // 2))
        return canvas

    top = fit(s, W, H)
    bot = fit(b, W, H)
    col = Image.new("RGB", (W, H * 2 + 40), (255, 255, 255))
    d = ImageDraw.Draw(col)
    d.text((8, 4), title + "  scan / hb-view", fill=(0, 0, 0))
    col.paste(top, (0, 24))
    col.paste(bot, (0, 24 + H))
    cols.append(col)
out = Image.new("RGB", (W * 3 + 16, cols[0].size[1] + 8), (255, 255, 255))
for i, c in enumerate(cols):
    out.paste(c, (8 + i * W, 4))
dest = root / "qa-evidence/scan-vs-hb-three.png"
out.save(dest)
print("wrote", dest, out.size)
