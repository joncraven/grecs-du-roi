#!/usr/bin/env python3
"""Render src/estienne-john1.html in Chromium+Firefox, screenshot it, and
run the same-Unicode copy invariant check (Phase 2.4 QA)."""
import sys
from playwright.sync_api import sync_playwright

base = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
url = "file://" + base + "/src/estienne-john1.html"
ev = base + "/qa-evidence"

with sync_playwright() as p:
    import glob, os
    cache = os.path.expanduser("~/Library/Caches/ms-playwright")
    chromium = sorted(glob.glob(cache + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))
    firefox = sorted(glob.glob(cache + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))
    if not chromium:
        chromium = sorted(glob.glob("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
    combos = [("chromium", lambda: p.chromium.launch(executable_path=chromium[-1] if chromium else None))]
    if firefox:
        combos.append(("firefox", lambda: p.firefox.launch(executable_path=firefox[-1])))
    for name, launch in combos:
        b = launch()
        pg = b.new_page(viewport={"width": 1000, "height": 900})
        pg.goto(url)
        pg.wait_for_timeout(700)
        pg.screenshot(path=f"{ev}/estienne-{name}-full.png", full_page=True)
        txt = pg.eval_on_selector("#textblock", "el => el.innerText")
        import unicodedata
        # NFD first: Υ+U+0304 precomposes to U+1FE9 under NFC; decomposing
        # returns the bare capital letters the copy invariant is about.
        nfd = unicodedata.normalize("NFD", txt)
        stripped = "".join(c for c in nfd if not unicodedata.combining(c))
        pua = [c for c in txt if 0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c)]
        # t_8e2d4b30: the folio's attested nomina are Υ-final (ΘΥ/ΧΥ/ΙΥ);
        # accept either contraction family as "letters survive paste".
        print(name, "| PUA chars:", len(pua),
              "| John1:1 present:", "ἦν ὁ λόγος" in txt,
              "| nomina letters in copy:", any(f in stripped for f in ("ΘΥ", "ΘΣ", "ΧΥ")))
        b.close()
print("shots done")
