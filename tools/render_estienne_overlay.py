#!/usr/bin/env python3
"""Render src/estienne-john1.html to src/estienne-render.png (folio element
only, 2x) for the estienne-compare.html overlay harness."""
import glob, os
from playwright.sync_api import sync_playwright

base = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
cache = os.path.expanduser("~/Library/Caches/ms-playwright")
chromium = sorted(glob.glob(cache + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing")) \
    or sorted(glob.glob("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=chromium[-1])
    pg = b.new_page(viewport={"width": 900, "height": 1400}, device_scale_factor=2)
    pg.goto("file://" + base + "/src/estienne-john1.html")
    pg.wait_for_timeout(700)
    pg.eval_on_selector_all(".toolbar", "els => els.forEach(e => e.remove())")
    el = pg.query_selector("#folio")
    el.screenshot(path=base + "/src/estienne-render.png")
    b.close()
print("wrote src/estienne-render.png")
