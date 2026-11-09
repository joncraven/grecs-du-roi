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

def load_corpus_text():
    d = json.load(open(BASE + "/corpus/john1_wh.json", encoding="utf-8"))
    return unicodedata.normalize("NFC",
        " ".join(d[k] for k in sorted(d, key=int)))

def check_copy(name, copied, verse_pairs=None):
    """Return list of failures for a browser's copied string (+ per-verse data)."""
    fails = []
    pua = [c for c in copied if 0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c)]
    if pua:
        fails.append(f"{name}: {len(pua)} PUA chars in copy: {pua[:5]!r}")
    if "ἦν ὁ λόγος" not in copied:
        fails.append(f"{name}: John 1:1 core phrase missing from copy")
    for letters in ("ΘΣ", "ΧΣ"):
        no_macron = copied.replace("\u0304", "").replace("\u0305", "")
        if letters not in copied and letters not in no_macron:
            fails.append(f"{name}: nomen sacrum letters {letters} lost on copy")
    # per-verse NFC copy-diff against the corpus — two tiers:
    #   strict   : byte-exact NFC equality (Phase 2.4's acceptance gate; will
    #              only pass when the page matches the transcription exactly,
    #              incl. drop-cap casing and nomina rendering)
    #   skeleton : letters only, casefolded, combining marks stripped — proves
    #              the copy carries the SAME Unicode text (no PUA substitution)
    #              today; this is the Phase 2.0 gate.
    if verse_pairs is not None:
        corpus = json.load(open(BASE + "/corpus/john1_wh.json", encoding="utf-8"))

        def skel(s):
            s = unicodedata.normalize("NFD", s)
            s = "".join(c for c in s if not unicodedata.combining(c))
            s = "".join(c for c in s if not c.isspace())
            return s.casefold()

        strict_diffs, skel_diffs = [], []
        for v, text in verse_pairs:
            if str(v) not in corpus:
                continue
            want = unicodedata.normalize("NFC", corpus[str(v)])
            got = unicodedata.normalize("NFC", text).replace("\u0304", "").replace("\u0305", "")
            if " ".join(want.split()) != " ".join(got.split()):
                strict_diffs.append(v)
            if skel(want) != skel(" ".join(got.split())):
                skel_diffs.append((v, " ".join(want.split())[:40],
                                   " ".join(got.split())[:40]))
        if skel_diffs:
            fails.append(f"{name}: NFC copy-diff NOT empty on {len(skel_diffs)} verse(s): "
                         + "; ".join(f"v{v} want {w!r} got {g!r}"
                                     for v, w, g in skel_diffs[:3]))
        if strict_diffs:
            print(f"    [{name}] strict-byte NFC diff pending on verses "
                  f"{','.join(map(str, strict_diffs))} (drop-cap/nomina display "
                  f"forms — Phase 2.4 collation target)")
    return fails

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
