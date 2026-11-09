#!/usr/bin/env python3
"""Screenshot src/cursive-compare.html (Phase 2.1 side-by-side evidence)."""
import glob, os, sys
from playwright.sync_api import sync_playwright

cache = os.path.expanduser("~/Library/Caches/ms-playwright")
cr = sorted(glob.glob(cache + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))
ff = sorted(glob.glob(cache + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))
base = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
url = "file://" + base + "/src/cursive-compare.html"

with sync_playwright() as p:
    combos = [("chromium", lambda: p.chromium.launch(executable_path=cr[-1] if cr else None))]
    if ff:
        combos.append(("firefox", lambda: p.firefox.launch(executable_path=ff[-1])))
    for name, launch in combos:
        b = launch()
        pg = b.new_page(viewport={"width": 1500, "height": 1100})
        errs = []
        pg.on("requestfailed", lambda r: errs.append(r.url))
        pg.goto(url)
        pg.wait_for_timeout(900)
        pg.screenshot(path=f"{base}/qa-evidence/cursive-compare-{name}.png",
                      full_page=True)
        # copy invariant on the specimen text
        txt = pg.evaluate("""() => {
            const t = [...document.querySelectorAll('.cursive, .upright')]
                .map(e => e.innerText).join('\\n');
            return t; }""")
        pua = [c for c in txt if 0xE000 <= ord(c) <= 0xF8FF or ord(c) >= 0xF0000]
        print(name, "| failed requests:", errs, "| PUA chars:", len(pua))
        b.close()
print("shots done")
