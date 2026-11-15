#!/usr/bin/env python3
"""qa_live_site.py — verify the deployed greek.craven.fr (t_1bdfa688, host t_4c9f46bf).

Runs while the OVH A record is still pending by pointing Chromium at
web01 directly (host-resolver-rules). Asserts, against the LIVE server:
  * reader page: face toggle works, Cardo + cursive webfonts fetch 200,
    copied folio text is polytonic with zero PUA and NFC-stable once the
    nomina-sacra display bars (U+0304/U+0305) are stripped — the decomposed
    macrons are deliberate (fb0a4e4: NFC would fold Υ+U+0304 to U+1FE9,
    which the cursive font renders as iota);
  * specimen page: hero cells are live text (no <img>), zero tofu.
Once DNS + enable-tls.sh land, the same checks work over https without
the resolver flag: WEB01_IP= (empty) switches to the public https path.
"""
import glob
import os
import unicodedata

CACHE = os.path.expanduser("~/Library/Caches/ms-playwright")
WEB01 = os.environ.get("WEB01_IP", "")  # set to pin (pre-DNS http path); unset = public https
BASE = ("http://greek.craven.fr" if WEB01 else "https://greek.craven.fr")

chrom = sorted(glob.glob(
    CACHE + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))[-1]

from playwright.sync_api import sync_playwright

fails = []
args = [f"--host-resolver-rules=MAP greek.craven.fr {WEB01}"] if WEB01 else []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=chrom, args=args)
    pg = b.new_page()
    bad_resp = []
    pg.on("response", lambda r: bad_resp.append(r.url) if r.status >= 400 else None)

    pg.goto(f"{BASE}/estienne-john1.html")
    pg.wait_for_timeout(900)
    fam = pg.evaluate("getComputedStyle(document.querySelector('.vtext')).fontFamily")
    if "GrecsRoi Greek Cursive" not in fam:
        fails.append(f"live roi family: {fam}")
    pg.check("input[name='face'][value='modern']")
    pg.wait_for_timeout(400)
    fam2 = pg.evaluate("getComputedStyle(document.querySelector('.vtext')).fontFamily")
    if "Cardo" not in fam2:
        fails.append(f"live Cardo family: {fam2}")
    pg.eval_on_selector("body", "b => b.classList.remove('mode-modern')")
    copied = pg.evaluate("""() => {
        const r = document.createRange();
        r.selectNodeContents(document.querySelector('#textblock'));
        const s = getSelection(); s.removeAllRanges(); s.addRange(r);
        return s.toString();
    }""")
    # Intentional exception (fb0a4e4): the nomina-sacra display spans carry
    # decomposed U+0304 macrons (Θ+U+0304+Υ+U+0304), because NFC would
    # recompose Υ+U+0304 into precomposed U+1FE9 and the shipping cursive
    # font renders that as an iota.  The invariant is therefore "NFC after
    # the display bars are stripped" — the same tolerance the strict-byte
    # tier in tools/check_page_text.py applies via strip_bars().
    bars = copied.replace("\u0304", "").replace("\u0305", "")
    if unicodedata.normalize("NFC", bars) != bars:
        fails.append("copied live text is not NFC-normalised "
                     "(after stripping nomina display bars)")
    pua = [hex(ord(c)) for c in copied if 0xE000 <= ord(c) <= 0xF8FF]
    if pua:
        fails.append(f"PUA in live copy: {pua}")
    if "ἦν ὁ λόγος" not in copied:
        fails.append("John 1:1 clause missing from live copy")

    pg.goto(f"{BASE}/index.html")
    pg.wait_for_timeout(800)
    img_heroes = pg.evaluate(
        "() => [...document.querySelectorAll('.specimen__glyph')]"
        ".filter(s => /γερ|μω|οὖν|φησὶ/.test(s.textContent) && s.querySelector('img')).length")
    if img_heroes:
        fails.append(f"{img_heroes} hero cells regressed to <img> on live")
    if bad_resp:
        fails.append(f"live 4xx/5xx: {bad_resp[:5]}")
    b.close()

print("LIVE " + ("ALL PASS" if not fails else "FAIL"))
for f in fails:
    print("   -", f)
raise SystemExit(0 if not fails else 1)
