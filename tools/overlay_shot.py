"""Produce qa-evidence/estienne-overlay-check.png: estienne-compare.html in
overlay mode, 50% opacity, render scaled to scan width and aligned to the
scan image box (offsetParent-relative offsets of the scan <img> itself)."""
import glob, os
from playwright.sync_api import sync_playwright

base = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
cache = os.path.expanduser("~/Library/Caches/ms-playwright")
chromium = sorted(glob.glob(cache + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing")) \
    or sorted(glob.glob("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))

POS = """() => {
    const s = document.getElementById('scan'), r = document.getElementById('render');
    r.style.width = s.clientWidth + 'px';          // width-matched overlay
    r.style.left = s.offsetLeft + 'px';            // scan img box origin
    r.style.top  = s.offsetTop  + 'px';            //  (same offsetParent: .pane)
}"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=chromium[-1])
    pg = b.new_page(viewport={"width": 900, "height": 1400})
    pg.goto("file://" + base + "/src/estienne-compare.html")
    pg.wait_for_timeout(900)
    pg.eval_on_selector("#mode", "el => { el.checked = true; el.dispatchEvent(new Event('change')); }")
    pg.eval_on_selector("#op", "el => { el.value = 50; el.dispatchEvent(new Event('input')); }")
    pg.wait_for_timeout(300)
    pg.evaluate(POS)
    pg.wait_for_timeout(250)
    pg.evaluate(POS)
    pg.wait_for_timeout(250)
    pg.screenshot(path=base + "/qa-evidence/estienne-overlay-check.png")
    b.close()
print("wrote qa-evidence/estienne-overlay-check.png")
