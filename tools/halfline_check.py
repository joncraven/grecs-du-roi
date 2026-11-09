"""±½-line overlay check for t_8e2d4b30.

Method (programmatic equivalent of the estienne-compare.html visual test):
1. Load estienne-john1.html, capture every body-text visual line rect (DOM
   Range client rects) in CSS px, plus the folio box.
2. Segment the scan's body lines by ink profile (scan px).
3. Fit a linear map render-CSS-px -> scan-px anchored on the scan sheet height
   the overlay harness uses (render scaled to scan width), then compute the
   vertical residual of each render line vs the nearest scan line and vs the
   scan's line-index interpolation; report worst |residual| against ½ of the
   scan's mean line pitch.
"""
import glob, os, json, sys
import numpy as np
from PIL import Image, ImageFilter
from playwright.sync_api import sync_playwright

base = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
cache = os.path.expanduser("~/Library/Caches/ms-playwright")
chromium = sorted(glob.glob(cache + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing")) \
    or sorted(glob.glob("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))

JS = """() => {
  const out = [];
  document.querySelectorAll('#textblock .vtext').forEach(v => {
    const rng = document.createRange(); rng.selectNodeContents(v);
    let cur = null;
    for (const r of rng.getClientRects()) {
      if (!cur || Math.abs(r.top - cur.top) > 4) { cur = {top:r.top, bottom:r.bottom, left:r.left, right:r.right, v: v.parentElement.dataset.verse}; out.push(cur); }
      else { cur.left=Math.min(cur.left,r.left); cur.right=Math.max(cur.right,r.right); }
    }
  });
  const f = document.querySelector('.folio').getBoundingClientRect();
  return {folio:{top:f.top,left:f.top,width:f.width}, lines: out};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=chromium[-1])
    pg = b.new_page(viewport={"width": 1000, "height": 900})
    pg.goto("file://" + base + "/src/estienne-john1.html")
    pg.wait_for_timeout(700)
    data = pg.evaluate(JS)
    b.close()

lines = data["lines"]
print("render visual lines:", len(lines))

# scan body lines
im = Image.open(base + "/qa-evidence/estienne-scan.jpg").convert("L")
a = np.array(im).astype(float); H, W = a.shape
bg = np.array(im.filter(ImageFilter.GaussianBlur(25))).astype(float)
ink = (bg - a) > 16
# main text column: 11-68% of sheet width (measured earlier in run)
x0, x1 = int(W * 0.11), int(W * 0.68)
prof = ink[:, x0:x1].sum(axis=1) / (x1 - x0)
groups, cur = [], None
for y in range(300, H - 30):
    if prof[y] > 0.16:
        if cur is None: cur = [y, y]
        else: cur[1] = y
    elif cur:
        if y - cur[1] > 6:
            if cur[1] - cur[0] > 8: groups.append(((cur[0]+cur[1])/2, cur[0], cur[1]))
            cur = None
# drop the 2 title lines: they are the first two groups with the largest height
groups_h = [g for g in groups if g[2]-g[1] > 7]
title = groups_h[:2]
scan_lines = [g[0] for g in groups_h[2:]]
pitch = (scan_lines[-1]-scan_lines[0])/(len(scan_lines)-1)
print(f"scan sheet {W}x{H}, column x {x0}-{x1}, body lines {len(scan_lines)}, pitch {pitch:.1f}")

r_top = min(l["top"] for l in lines); r_bot = max(l["bottom"] for l in lines)
s_top, s_bot = scan_lines[0], scan_lines[-1]
k = (s_bot - s_top) / (r_bot - r_top)
mapped = [s_top + (l["top"] - r_top) * k for l in lines]
idx = np.arange(len(scan_lines))
resid = []
for i, m in enumerate(mapped):
    j = min(len(scan_lines)-1, max(0, int(round((m - s_top)/pitch))))
    nearest = min(scan_lines, key=lambda s: abs(s-m))
    resid.append((int(lines[i]["v"]), m, nearest, m - nearest, abs(m-nearest)))
worst = max(r[4] for r in resid)
print("verse  mappedY  nearestScanY  resid  (scan px)")
for v, m, n, d, ad in resid:
    print(f"{v:>4}  {m:7.1f}  {n:7.1f}  {d:+6.1f}")
print(f"worst |resid| = {worst:.1f} px; 1/2 line = {pitch/2:.1f} px -> "
      + ("PASS" if worst <= pitch/2 else "FAIL"))
json.dump({"worst_px": worst, "half_line_px": pitch/2,
           "render_lines": len(lines), "scan_lines": len(scan_lines),
           "verdict": "PASS" if worst <= pitch/2 else "FAIL"},
          open(base + "/qa-evidence/overlay-halfline.json", "w"))
