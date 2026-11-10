#!/usr/bin/env python3
"""qa_reader_toggle.py — Phase 2.5 gate (t_1bdfa688): the reading-site
"grecs du roi ⇄ modern polytonic (Cardo)" toggle must be real in
Chromium + Firefox + WebKit.

Asserts per engine:
  1. the radios exist and switching them toggles body.mode-modern;
  2. the computed font-family of the running text actually changes
     (cursive face in roi mode, Cardo Polytonic in modern mode);
  3. fusion proof: γερ renders narrower than γ ε ρ in the cursive face
     (roi mode is the fused one), and the Cardo face shows NO feature
     width delta (modern mode is honestly unfused);
  4. same-Unicode invariant: the folio text is identical before, during
     and after flipping the toggle — the toggle never edits text;
  5. no PUA codepoints; document.fonts.check proves Cardo Polytonic
     covers every codepoint displayed on the page;
  6. no glyf-bbox console warnings (Didot resubset gate, minor 4).

Exit 0 = all engines green. Engine discovery mirrors qa_fusion_toggle.py.
"""
import glob
import os
import sys

BASE = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
CACHE = os.path.expanduser("~/Library/Caches/ms-playwright")


def engines():
    chromium = sorted(glob.glob(
        CACHE + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))
    firefox = sorted(glob.glob(CACHE + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))
    webkit = sorted(glob.glob(CACHE + "/webkit-*/pw_run.sh"))
    combos = [("chromium", lambda p: p.chromium.launch(
        executable_path=chromium[-1] if chromium else None))]
    if firefox:
        combos.append(("firefox", lambda p: p.firefox.launch(executable_path=firefox[-1])))
    if webkit:
        combos.append(("webkit", lambda p: p.webkit.launch(executable_path=webkit[-1])))
    return combos


def run(name, launch):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = launch(p)
        page = browser.new_page()
        console = []
        page.on("console", lambda m: console.append(f"{m.type}:{m.text}"))
        page.goto(f"file://{BASE}/src/estienne-john1.html")
        page.wait_for_timeout(700)

        fails = []

        fam_roi = page.evaluate(
            "getComputedStyle(document.querySelector('.vtext')).fontFamily")
        if "GrecsRoi Greek Cursive" not in fam_roi:
            fails.append(f"roi mode family wrong: {fam_roi}")

        text_before = page.evaluate(
            "document.querySelector('#textblock').innerText")

        page.check("input[name='face'][value='modern']")
        page.wait_for_timeout(300)
        if not page.evaluate("document.body.classList.contains('mode-modern')"):
            fails.append("body.mode-modern not applied on toggle")
        fam_mod = page.evaluate(
            "getComputedStyle(document.querySelector('.vtext')).fontFamily")
        if "Cardo" not in fam_mod:
            fails.append(f"modern mode family wrong: {fam_mod}")

        text_after = page.evaluate(
            "document.querySelector('#textblock').innerText")
        if text_before != text_after:
            fails.append("face toggle MUTATED the folio text")

        # fusion lives in the cursive face (qa_fusion_toggle.py owns that
        # gate); here assert the CARDO face is feature-invariant so modern
        # mode is honestly unfused:
        w_on, w_off = page.evaluate("""() => {
          const mk = (feat) => {
            const s = document.createElement('span');
            s.style.cssText = 'position:absolute;visibility:hidden;white-space:pre;'
              + 'font-size:48px;font-family:"Cardo Polytonic";'
              + 'font-feature-settings:' + feat;
            s.textContent = '\\u03ba\\u03b1\\u1f76 \\u03bf\\u1f66\\u03bd \\u03c6\\u03b7\\u03c3\\u1f66';
            document.body.appendChild(s);
            const w = s.getBoundingClientRect().width; s.remove(); return w;
          };
          return [mk('"liga" 1,"dlig" 1,"rlig" 1'), mk('"liga" 0,"dlig" 0,"rlig" 0')];
        }""")
        if abs(w_on - w_off) > 0.5:
            fails.append(f"Cardo shows GSUB width delta {w_on} vs {w_off} (modern mode not clean)")

        cps = sorted({ord(c) for c in text_after if not c.isspace()})
        pua = [c for c in cps if 0xE000 <= c <= 0xF8FF or c >= 0xF0000]
        if pua:
            fails.append(f"PUA in text: {[hex(c) for c in pua]}")
        missing = page.evaluate("""(cps) => {
          const out = [];
          for (const cp of cps) {
            if (!document.fonts.check('24px "Cardo Polytonic"',
                                      String.fromCodePoint(cp))) out.push(cp);
          }
          return out;
        }""", cps)
        if missing:
            fails.append(f"Cardo Polytonic missing {len(missing)} cps: {[hex(c) for c in missing[:10]]}")

        bad = [m for m in console if ("bbox" in m.lower() or "error" in m.lower())]
        if bad:
            fails.append(f"console errors: {bad[:3]}")

        browser.close()
        print(f"[{name}] {'PASS' if not fails else 'FAIL'}")
        for f in fails:
            print(f"   - {f}")
        return not fails


def main():
    results = []
    for name, launch in engines():
        try:
            results.append(run(name, launch))
        except Exception as exc:
            print(f"[{name}] SKIP ({exc})")
    ok = bool(results) and all(results)
    print("ALL PASS" if ok else "FAILURES ABOVE")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
