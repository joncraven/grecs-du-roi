#!/usr/bin/env python3
"""qa_three_browser.py — Phase 2.0 CI gate: render src/estienne-john1.html in
Chromium + Firefox + WebKit (Playwright engines) AND real Safari (safaridriver
WebDriver), screenshot each, and run the same-Unicode copy invariant:

  * zero PUA characters in the rendered copy text
  * John 1:1 core phrase present after select-all semantics (innerText)
  * nomina-sacra letters survive copy (ΘΣ letters, not PUA glyphs)
  * NFC-diff of the copy against corpus/john1_wh.json must be empty
    (allowing only the page furniture: verse numbers, title, macrons U+0305)

Exit code 0 = every available browser passed; 1 = any failure.
Real-Safari is attempted first (the standing "Safari not instrumented"
caveat); if safaridriver is not enabled it is reported as SKIP with the exact
one-time enable command, and the gate still evaluates the three engines.

Playwright cache pitfall (1223-vs-1248): executables are located by globbing
~/Library/Caches/ms-playwright/<engine>-*/ and passing executable_path,
because the installed playwright version may expect a cache dir that a newer
download has replaced. WebKit's entrypoint is pw_run.sh inside its dir.
"""
import glob
import os
import subprocess
import sys
import time
import unicodedata
import json
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_page_text import check_copy  # shared collation invariant

BASE = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
URL = "file://" + BASE + "/src/estienne-john1.html"
EV = BASE + "/qa-evidence"
CACHE = os.path.expanduser("~/Library/Caches/ms-playwright")

COPY_JS = """
() => {
  // selection copy with nomina sacra DISPLAYED: the Θ̅Σ̅ letters must survive
  const sel = window.getSelection();
  const range = document.createRange();
  range.selectNode(document.getElementById('textblock'));
  sel.removeAllRanges(); sel.addRange(range);
  const txt = sel.toString();
  sel.removeAllRanges();
  return txt;
}
"""

from check_page_text import check_copy  # noqa: E402  (shared collation invariant)

VERSES_JS = """
() => {
  const t = document.getElementById('nomTgl');
  if (t && t.checked) { t.checked = false; t.dispatchEvent(new Event('change')); }
  const out = Array.from(document.querySelectorAll('#textblock .verse')).map(v =>
    [v.getAttribute('data-verse'), v.querySelector('.vtext').innerText]);
  if (t) { t.checked = true; t.dispatchEvent(new Event('change')); }
  return out;
}
"""

def run_playwright():
    from playwright.sync_api import sync_playwright
    results = {}
    chromium = sorted(glob.glob(CACHE + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))
    firefox = sorted(glob.glob(CACHE + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))
    webkit = sorted(glob.glob(CACHE + "/webkit-*/pw_run.sh"))
    if not chromium:
        chromium = sorted(glob.glob("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
    combos = [("chromium", lambda p: p.chromium.launch(
                  executable_path=chromium[-1] if chromium else None))]
    if firefox:
        combos.append(("firefox", lambda p: p.firefox.launch(executable_path=firefox[-1])))
    if webkit:
        combos.append(("webkit", lambda p: p.webkit.launch(executable_path=webkit[-1])))
    with sync_playwright() as p:
        for name, launch in combos:
            try:
                b = launch(p)
                pg = b.new_page(viewport={"width": 1000, "height": 900})
                pg.goto(URL)
                pg.wait_for_timeout(700)
                pg.screenshot(path=f"{EV}/estienne-{name}-full.png", full_page=True)
                copied = pg.evaluate(COPY_JS)
                verses = pg.evaluate(VERSES_JS)
                results[name] = check_copy(name, copied, verse_pairs=verses)
                b.close()
            except Exception as e:
                results[name] = [f"{name}: launch/render error: {type(e).__name__}: {str(e)[:160]}"]
    return results

def safari_driver_running():
    try:
        with urllib.request.urlopen("http://127.0.0.1:55555/status", timeout=2) as r:
            body = r.read(2000).decode("utf-8", "replace")
        # newer safaridriver returns JSON with sessionId; older returns XML sessionId
        return "sessionId" in body
    except Exception:
        return False

def run_safari():
    """Real Safari via safaridriver WebDriver on :55555 (no sudo needed once
    enabled). Returns (status, fails) — status in PASS/SKIP/FAIL."""
    if not safari_driver_running():
        return ("SKIP", ["safari: safaridriver not running on 127.0.0.1:55555."
                         "  One-time human step:  sudo /usr/bin/safaridriver --enable"
                         "  then launch in background:  /usr/bin/safaridriver -p 55555"])
    try:
        import selenium.webdriver  # noqa: F401
    except ImportError:
        return ("SKIP", ["safari: selenium not installed (pip install selenium)"])
    from selenium import webdriver
    opts = webdriver.safari.options.Options()
    opts.webdriver_port = 55555
    driver = None
    try:
        driver = webdriver.Remote("http://127.0.0.1:55555", options=opts)
        driver.set_window_size(1000, 900)
        driver.get(URL)
        time.sleep(1.2)
        driver.execute_script("window.scrollTo(0,0)")
        png = driver.get_screenshot_as_png()
        with open(f"{EV}/estienne-safari-full.png", "wb") as f:
            f.write(png)
        # copy invariant via getComputedText / selection API
        driver.execute_script("""
            const sel = window.getSelection();
            const range = document.createRange();
            range.selectNode(document.getElementById('textblock'));
            sel.removeAllRanges(); sel.addRange(range);
        """)
        copied = driver.execute_script(
            "return window.getSelection().toString();")
        verses = driver.execute_script("return (" + VERSES_JS + ")();")
        fails = check_copy("safari", copied, verse_pairs=verses)
        return ("FAIL" if fails else "PASS", fails)
    except Exception as e:
        return ("FAIL", [f"safari: {type(e).__name__}: {str(e)[:200]}"])
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def main():
    results = run_playwright()
    status, sf = run_safari()
    fails = list(sf) if status == "FAIL" else []
    for name, f in results.items():
        fails += f
    print("=" * 64)
    print("  THREE-BROWSER QA GATE — estienne-john1.html")
    print("=" * 64)
    for name, f in results.items():
        print(f"  {name:<10} {'PASS' if not f else 'FAIL'}")
        for line in f:
            print("    -", line)
    print(f"  {'safari':<10} {status}")
    for line in sf:
        print("    -", line)
    print("  shots: " + EV + "/estienne-{chromium,firefox,webkit,safari}-full.png")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
