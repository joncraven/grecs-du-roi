#!/usr/bin/env python3
"""Capture Phase 2.5 reader-toggle evidence + Firefox Didot bbox probe."""
import glob
import os

from playwright.sync_api import sync_playwright

CACHE = os.path.expanduser("~/Library/Caches/ms-playwright")
BASE = "/Volumes/RAID10/jon/Projects/grecs-du-roi"

chrom = sorted(glob.glob(
    CACHE + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))[-1]
ffp = sorted(glob.glob(CACHE + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))[-1]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=chrom)
    pg = b.new_page(viewport={"width": 1000, "height": 1400})
    pg.goto(f"file://{BASE}/src/estienne-john1.html")
    pg.wait_for_timeout(900)
    pg.screenshot(path=f"{BASE}/qa-evidence/reader-mode-roi.png")
    pg.check("input[name='face'][value='modern']")
    pg.wait_for_timeout(600)
    pg.screenshot(path=f"{BASE}/qa-evidence/reader-mode-modern.png")
    b.close()

    fb = p.firefox.launch(executable_path=ffp)
    fpg = fb.new_page()
    msgs = []
    fpg.on("console", lambda m: msgs.append(m.text))
    fpg.goto(f"file://{BASE}/src/index.html")
    fpg.wait_for_timeout(1500)
    bbox = [m for m in msgs if "bbox" in m.lower() or "glyph" in m.lower()]
    print("firefox bbox/glyph console warnings on specimen page:", len(bbox))
    for m in bbox[:5]:
        print("  ", m[:120])
    fb.close()
print("shots ok")
