#!/usr/bin/env python3
"""Screenshot the verse-12 line (γενέσθαι) on the LIVE estienne page in
chromium/firefox and crop close so the γε can be eyeballed. Also measures
per-run geometry via Canvas where possible."""
import glob, os
CACHE = os.path.expanduser("~/Library/Caches/ms-playwright")
AUTH = {"username": "invitedguest", "password": os.environ["INVITEDGUEST_PASS"],
        "origin": "https://greek.craven.fr", "send": "always"}
URL = "https://greek.craven.fr/estienne-john1.html"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "qa-evidence")
OUT = os.path.abspath(OUT)

from playwright.sync_api import sync_playwright
chrom = sorted(glob.glob(CACHE + "/chromium-*/chrome-mac-arm64/*.app/Contents/MacOS/Google Chrome for Testing"))[-1]
ffs = sorted(glob.glob(CACHE + "/firefox-*/firefox/*.app/Contents/MacOS/firefox"))
wks = sorted(glob.glob(CACHE + "/webkit-*/pw_run.sh"))

combos = [("chromium", lambda p: p.chromium.launch(executable_path=chrom))]
if ffs: combos.append(("firefox", lambda p: p.firefox.launch(executable_path=ffs[-1])))
if wks: combos.append(("webkit", lambda p: p.webkit.launch(p)))

with sync_playwright() as p:
    for name, launch in combos:
        try:
            b = launch(p)
        except Exception as e:
            print(name, "launch fail:", str(e)[:120]); continue
        ctx = b.new_context(http_credentials=AUTH, viewport={"width": 1100, "height": 900},
                            device_scale_factor=3)
        pg = ctx.new_page()
        pg.goto(URL, wait_until="load")
        pg.wait_for_timeout(2000)
        # make sure cursive face active (default) and zoom the line
        box = pg.evaluate("""() => {
            const el = document.querySelector('[data-verse="12"] .vtext');
            const r = el.getBoundingClientRect();
            return {x: r.x, y: r.y, w: r.width, h: r.height, top: r.top + scrollY};
        }""")
        el = pg.query_selector('[data-verse="12"] .vtext')
        el.scroll_into_view_if_needed()
        pg.wait_for_timeout(300)
        path = os.path.join(OUT, f"t_a5e3138b-refix-{name}.png")
        bb = el.bounding_box()
        pg.screenshot(path=path, clip={"x": bb["x"], "y": bb["y"],
                                       "width": min(1100 - bb["x"], bb["width"]),
                                       "height": bb["height"] + 6})
        # also a big re-rendered probe span of the exact word at page face
        probe = pg.evaluate("""() => {
            const s = document.createElement('div');
            s.style.cssText = 'position:fixed;left:10px;top:10px;z-index:9999;background:#fff;' +
              'font-family:"GrecsRoi Greek Cursive";font-size:64px;' +
              'font-feature-settings:\\"liga\\" 1,\\"clig\\" 1,\\"rlig\\" 1,\\"dlig\\" 1,\\"hlig\\" 1,\\"calt\\" 1,\\"locl\\" 1;';
            s.textContent = 'Θ̄Ῡ ἐξουσίαν τέκνα γενέσθαι, ἄγγελμα μονογενοῦς';
            document.body.appendChild(s);
            const r = s.getBoundingClientRect();
            return {x: r.x, y: r.y, width: r.width, height: r.height};
        }""")
        pg.screenshot(path=os.path.join(OUT, f"t_a5e3138b-probe-{name}.png"),
                      clip={"x": max(0, probe["x"]), "y": max(0, probe["y"]),
                            "width": min(1100, probe["width"]), "height": min(900, probe["height"])})
        b.close()
        print(name, "->", path, "verse-box:", {k: round(v) for k, v in box.items()})
print("done")
