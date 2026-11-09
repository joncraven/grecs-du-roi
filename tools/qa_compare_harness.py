#!/usr/bin/env python3
"""Screenshot the estienne-compare.html harness and report failed requests."""
import glob, os
from playwright.sync_api import sync_playwright

cache = os.path.expanduser("~/Library/Caches/ms-playwright")
cr = sorted(glob.glob(cache + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))[-1]
base = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=cr)
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    errs = []
    pg.on("requestfailed", lambda r: errs.append(r.url))
    pg.goto("file://" + base + "/src/estienne-compare.html")
    pg.wait_for_timeout(800)
    pg.screenshot(path=base + "/qa-evidence/estienne-compare-harness.png")
    print("failed requests:", errs)
    b.close()
