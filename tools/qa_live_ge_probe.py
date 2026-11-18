#!/usr/bin/env python3
"""Probe the LIVE estienne page: is word-initial γε fused in each engine?

Uses Canvas TextMetrics.actualBoundingBox / getTextRunInfo where available
plus the width A/B (features on vs off) used by qa_fusion_toggle.py, and
also renders the exact verse-12 span live-measured width vs a manual
gamma+epsilon reconstruction.
"""
import glob, os, sys
CACHE = os.path.expanduser("~/Library/Caches/ms-playwright")
AUTH = {"username": "invitedguest", "password": os.environ["INVITEDGUEST_PASS"],
        "origin": "https://greek.craven.fr", "send": "always"}
URL = "https://greek.craven.fr/estienne-john1.html"

JS_PROBE = """
(args) => {
  const [text] = args;
  const mk = (on) => {
    const s = document.createElement('span');
    s.style.cssText = 'position:absolute;visibility:hidden;white-space:pre;' +
      'font-family:"GrecsRoi Greek Cursive";font-size:48px;' +
      'font-feature-settings:' + (on
        ? '"liga" 1,"clig" 1,"rlig" 1,"dlig" 1,"hlig" 1,"calt" 1,"locl" 1'
        : '"liga" 0,"clig" 0,"rlig" 0,"dlig" 0,"hlig" 0,"calt" 0,"locl" 0');
    s.textContent = text;
    document.body.appendChild(s);
    const w = s.getBoundingClientRect().width;
    s.remove();
    return w;
  };
  // also measure the real live element for verse 12
  const el = document.querySelector('[data-verse="12"] .vtext');
  return {on: mk(true), off: mk(false), liveText: el ? el.textContent.includes('γενέσθαι') : null};
}
"""

from playwright.sync_api import sync_playwright
chrom = sorted(glob.glob(CACHE + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))[-1]
ff = sorted(glob.glob(CACHE + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))
ff_hw = ff[-1] if ff else None

fails = []
with sync_playwright() as p:
    engines = []
    engines.append(("chromium", lambda: p.chromium.launch(executable_path=chrom)))
    if ff_hw:
        engines.append(("firefox", lambda: p.firefox.launch(executable_path=ff_hw)))
    engines.append(("webkit", lambda: p.webkit.launch()))
    for name, launch in engines:
        try:
            b = launch()
        except Exception as e:
            print(f"{name}: launch failed {e}"); continue
        ctx = b.new_context(http_credentials=AUTH)
        pg = ctx.new_page()
        pg.goto(URL, wait_until="load")
        pg.wait_for_timeout(1500)  # let fonts settle
        for probe in ["γενέσθαι", "ἄγγελμα", "μονογενοῦς"]:
            r = pg.evaluate(JS_PROBE, [probe])
            shrink = r["off"] - r["on"]
            status = "FUSED" if r["on"] < r["off"] - 1 else "NOT-FUSED" if probe == "γενέσθαι" else "ok"
            print(f"{name:8s} {probe!r}: on={r['on']:.1f} off={r['off']:.1f} shrink={shrink:+.1f} -> {status}")
        b.close()
print("done")
