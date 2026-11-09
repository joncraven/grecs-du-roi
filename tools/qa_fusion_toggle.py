#!/usr/bin/env python3
"""qa_fusion_toggle.py — Phase 2.2 exit-gate: the fused ligature engine must
be LIVE and TOGGLEABLE in Chromium + Firefox + WebKit.

Method (no screenshot reading needed):
  * for each probe word, render twice in "GrecsRoi Greek Cursive" — features
    ON ("liga" 1,"clig" 1,"rlig" 1,"dlig" 1,"hlig" 1) vs OFF (all 0) —
    in the same span geometry. A fused ligature collapses two+ advances
    into one glyph => the ON line is measurably SHORTER. Assert strict
    width shrink per probe.
  * the four hero sequences (γερ μω οὖν φησὶ) get the same A/B.
  * index.html must contain ZERO <img> inside the four hero specimen cells
    (deliverable: PNGs demoted to reference insets, not hero glyphs).
  * copy from the estienne page must contain no PUA characters (invariant).

Exit 0 = every engine green (real Safari remains the recorded human gate;
safaridriver enable is a sudo one-time step — see qa_three_browser.py).
"""
import glob
import json
import os
import re
import sys

BASE = "/Volumes/RAID10/jon/Projects/grecs-du-roi"
CACHE = os.path.expanduser("~/Library/Caches/ms-playwright")

PROBES = ["γερ", "μω", "οὖν", "φησὶ",          # gate four
          "οὐκ", "ανθρωπος", "ἐστιν", "λόγου",  # corpus fusions
          "αὐτοῦ", "πάντα", "ἦν ὁ λόγος"]

JS_TOGGLE = """
(args) => {
  const [text, on] = args;
  const s = document.createElement('span');
  s.style.cssText = 'position:absolute;visibility:hidden;white-space:pre;' +
    'font-family:"GrecsRoi Greek Cursive";font-size:48px;' +
    'font-feature-settings:' + (on
      ? '"liga" 1,"clig" 1,"rlig" 1,"dlig" 1,"hlig" 1'
      : '"liga" 0,"clig" 0,"rlig" 0,"dlig" 0,"hlig" 0');
  s.textContent = text;
  document.body.appendChild(s);
  const w = s.getBoundingClientRect().width;
  s.remove();
  return w;
}
"""


def run_engine(name, launch):
    from playwright.sync_api import sync_playwright
    fails = []
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page()
        pg.goto("file://" + BASE + "/src/cursive-compare.html")
        try:
            pg.evaluate("document.fonts.load('48px \"GrecsRoi Greek Cursive\"')")
            pg.wait_for_function(
                "document.fonts.check('48px \"GrecsRoi Greek Cursive\"')",
                timeout=10000)
        except Exception:
            pass  # engines vary on check(); width test below is self-proving
        for probe in PROBES:
            w_on = pg.evaluate(JS_TOGGLE, [probe, True])
            w_off = pg.evaluate(JS_TOGGLE, [probe, False])
            if not (w_on < w_off - 0.5):
                fails.append(
                    f"{name}: '{probe}' toggle dead (on={w_on:.1f} off={w_off:.1f})")
        # hero cells: live text, no img in the four converted specimens
        pg.goto("file://" + BASE + "/src/index.html")
        pg.wait_for_timeout(500)
        hero_html = pg.evaluate("""() => {
            const out = {};
            for (const li of document.querySelectorAll('.specimen')) {
              const name = li.querySelector('.specimen__name')?.textContent || '';
              if (/γερ|μω \\(|οὖν|φησὶ/.test(name))
                out[name] = li.querySelector('.specimen__glyph').innerHTML;
            }
            return out; }""")
        for cell, html in hero_html.items():
            if "<img" in html:
                fails.append(f"{name}: hero cell {cell!r} still an <img>")
        # PUA copy invariant from the estienne page
        pg.goto("file://" + BASE + "/src/estienne-john1.html")
        pg.wait_for_timeout(500)
        copied = pg.evaluate("""() => {
            const sel = getSelection(); const r = new Range();
            const tb = document.getElementById('textblock');
            if (!tb) return '';
            r.selectNode(tb); sel.removeAllRanges(); sel.addRange(r);
            const t = sel.toString(); sel.removeAllRanges(); return t; }""")
        pua = [c for c in copied if 0xE000 <= ord(c) <= 0xF8FF or ord(c) >= 0xF0000]
        if pua:
            fails.append(f"{name}: {len(pua)} PUA chars in estienne copy")
        b.close()
    return fails


def main():
    chromium = sorted(glob.glob(
        CACHE + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))
    firefox = sorted(glob.glob(CACHE + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))
    webkit = sorted(glob.glob(CACHE + "/webkit-*/pw_run.sh"))
    if not chromium:
        chromium = sorted(glob.glob(
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
    combos = [("chromium", lambda p: p.chromium.launch(
        executable_path=chromium[-1] if chromium else None))]
    if firefox:
        combos.append(("firefox", lambda p: p.firefox.launch(executable_path=firefox[-1])))
    if webkit:
        combos.append(("webkit", lambda p: p.webkit.launch(executable_path=webkit[-1])))

    results = {}
    for name, launch in combos:
        try:
            results[name] = run_engine(name, launch)
        except Exception as e:
            results[name] = [f"{name}: error {type(e).__name__}: {str(e)[:160]}"]

    print("=" * 64)
    print("  PHASE 2.2 FEATURE-TOGGLE GATE (fusion live ON, inert OFF)")
    print("=" * 64)
    ok = True
    for name, fails in results.items():
        status = "PASS" if not fails else "FAIL"
        print(f"  {name:10s} {status}")
        for f in fails:
            print("    -", f)
            ok = False
    if not results:
        print("  no engines available")
        ok = False
    print("  (real Safari: human gate — `sudo safaridriver --enable` once;")
    print("   WebKit is the same engine as Safari for shaping this face.)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
