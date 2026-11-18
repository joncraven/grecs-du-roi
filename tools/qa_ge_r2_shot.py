#!/usr/bin/env python3
"""Render γενέσθαι + control words at the estienne page's reading size and
2x with the LOCAL patched font, Chromium+Firefox, for round-2 evidence."""
import glob, os
from pathlib import Path
CACHE = os.path.expanduser("~/Library/Caches/ms-playwright")
ROOT = Path(__file__).resolve().parent.parent
EV = ROOT / "qa-evidence"

HTML = """<!doctype html><meta charset=utf-8>
<style>
@font-face { font-family: GR; src: url("__FONT__"); }
body { background: #f3ead8; margin: 0; }
.line { font-family: GR; font-feature-settings: "liga" 1,"clig" 1,"rlig" 1,"dlig" 1,"hlig" 1,"calt" 1,"locl" 1; }
.s24 { font-size: 24px; } .s48 { font-size: 48px; } .s96 { font-size: 96px; }
</style>
<div class="line s24">Ὅσοι δὲ ἔλαβον αὐτόν, ἔδωκεν αὐτοῖς ἐξουσίαν τέκνα γενέσθαι, τοῖς πιστεύουσιν εἰς τὸ ὄνομα αὐτοῦ:</div>
<div class="line s48">τέκνα γενέσθαι · ἄγγελμα · μονογενοῦς · ἐγεννήθησαν</div>
<div class="line s96">γενέσθαι ἀγγελμα</div>
"""

from playwright.sync_api import sync_playwright
chrom = sorted(glob.glob(CACHE + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))[-1]
ffs = sorted(glob.glob(CACHE + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))
font = str(ROOT / "src/fonts/grecs-roi-greek-cursive.otf")
page = Path("/tmp/ge-round2-page.html"); page.write_text(HTML.replace("__FONT__", font))

with sync_playwright() as p:
    combos = [("chromium", lambda p: p.chromium.launch(executable_path=chrom))]
    if ffs: combos.append(("firefox", lambda p: p.firefox.launch(executable_path=ffs[-1])))
    for name, launch in combos:
        b = launch(p)
        pg = b.new_page(viewport={"width": 1400, "height": 700}, device_scale_factor=2)
        pg.goto("file://" + str(page))
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(EV / f"t_a5e3138b-r2-{name}.png"))
        b.close()
        print(name, "shot")
print("done")
