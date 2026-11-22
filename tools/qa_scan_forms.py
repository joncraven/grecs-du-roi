#!/usr/bin/env python3
"""qa_scan_forms.py — visual-class gates for t_8ad4e391 (π / πρὸς / ἦν).

These are silhouette tests against hb-view rasters, not qa_cursive shaping.
They exist because six review rounds passed glyph names while πρὸς still
read as ω/œ and ἦν as a bare w.

  π     two-stem gateway (not varpi)
  πρ    italic æ: left a-curl sticks out past the left bowl; two holes
  ἦν    double-u with a two-hump wave sitting on the right bowl

Usage: python3 tools/qa_scan_forms.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "src/fonts/grecs-roi-greek-cursive.otf"
FAILS: list[str] = []


def check(cond: bool, label: str, detail: str = ""):
    tag = "PASS" if cond else "FAIL"
    extra = f"  {detail}" if detail else ""
    print(f"[{tag}] {label}{extra if not cond else extra}")
    if not cond:
        FAILS.append(label)


def hb_png(text: str, size: int = 180) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        out = Path(tmp.name)
    subprocess.check_call(
        ["hb-view", "--font-size", str(size), "-O", "png", "-o", str(out),
         str(FONT), text],
        stdout=subprocess.DEVNULL,
    )
    im = Image.open(out).convert("L")
    out.unlink(missing_ok=True)
    return im


def ink_mask(im: Image.Image, thresh: int = 240) -> np.ndarray:
    a = np.asarray(im)
    return a < thresh


def ink_bbox(mask: np.ndarray):
    ys, xs = np.where(mask)
    if xs.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def holes(mask: np.ndarray):
    """White components fully enclosed (not touching the image border)."""
    from scipy import ndimage
    inv = ~mask
    labeled, n = ndimage.label(inv)
    h, w = mask.shape
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(labeled == i)
        if xs.size == 0:
            continue
        if xs.min() == 0 or ys.min() == 0 or xs.max() == w - 1 or ys.max() == h - 1:
            continue
        out.append((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()),
                    int(xs.size)))
    out.sort(key=lambda t: t[0])
    return out


def shape_names(text: str) -> list[str]:
    import uharfbuzz as hb
    blob = hb.Blob.from_file_path(str(FONT))
    font = hb.Font(hb.Face(blob))
    feats = {"liga": 1, "clig": 1, "rlig": 1, "dlig": 1, "hlig": 1,
             "calt": 1, "locl": 1}
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.script = "grek"
    hb.shape(font, buf, feats)
    return [font.get_glyph_name(i.codepoint) for i in buf.glyph_infos]


def main() -> int:
    check(FONT.is_file(), "font exists", str(FONT))

    # --- shaping (regression, not visual evidence) --------------------------
    check(shape_names("π") == ["pi"], "shape π = [pi]", str(shape_names("π")))
    check(shape_names("πρὸς")[0] == "pi.rho",
          "shape πρὸς starts with pi.rho", str(shape_names("πρὸς")))
    check(shape_names("ἦν") == ["lig2_uni1F26_nu"],
          "shape ἦν = lig2_uni1F26_nu", str(shape_names("ἦν")))
    check(shape_names("ἤν") == ["lig2_uni1F24_nu"],
          "shape ἤν = lig2_uni1F24_nu", str(shape_names("ἤν")))
    check(shape_names("παρὰ")[0] == "lig2_pi_alpha",
          "shape παρὰ starts with lig2_pi_alpha (two-stem π, not pi.rho)",
          str(shape_names("παρὰ")))

    # --- π: two vertical stems, not an omega body ---------------------------
    pi = ink_mask(hb_png("π", 180))
    bb = ink_bbox(pi)
    check(bb is not None, "π has ink")
    if bb:
        x0, y0, x1, y1 = bb
        w, h = x1 - x0 + 1, y1 - y0 + 1
        # Mid-height slice: two ink runs (stems) with a paper gap.
        ymid = y0 + int(h * 0.55)
        row = pi[ymid, x0:x1 + 1]
        # compress to runs
        runs = []
        on = False
        for i, v in enumerate(row):
            if v and not on:
                s = i
                on = True
            elif not v and on:
                runs.append((s, i))
                on = False
        if on:
            runs.append((s, len(row)))
        ink_runs = [r for r in runs if (r[1] - r[0]) >= 2]
        check(len(ink_runs) >= 2, "π mid-slice has two stems",
              f"runs={ink_runs} w={w}")
        if len(ink_runs) >= 2:
            gap = ink_runs[1][0] - ink_runs[0][1]
            check(gap >= w * 0.12, "π stems have a paper counter",
                  f"gap={gap} w={w}")
        # Roof, not n-shoulder: near the top, one wide lid spanning both posts.
        ytop = y0 + max(1, int(h * 0.10))
        rowt = pi[ytop, x0:x1 + 1]
        runs_t, on, s = [], False, 0
        for i, v in enumerate(rowt):
            if v and not on:
                s, on = i, True
            elif not v and on:
                runs_t.append((s, i)); on = False
        if on:
            runs_t.append((s, len(rowt)))
        ink_t = [r for r in runs_t if (r[1] - r[0]) >= 3]
        check(len(ink_t) == 1, "π top is a single lid (not an n-shoulder)",
              f"runs={ink_t} w={w}")
        if ink_t:
            span = ink_t[0][1] - ink_t[0][0]
            check(span >= w * 0.55, "π lid spans both stems",
                  f"span={span} w={w}")

    # --- πρ: æ, not œ/ω -----------------------------------------------------
    # Render πρ alone so ὸς does not pollute hole counts.
    # ω/œ is widest at the left-bowl equator. Italic æ is widest (left) at
    # the high a-curl, with the bowl wall inset from that curl.
    pr = ink_mask(hb_png("πρ", 180))
    bb = ink_bbox(pr)
    check(bb is not None, "πρ has ink")
    if bb:
        x0, y0, x1, y1 = bb
        w, h = x1 - x0 + 1, y1 - y0 + 1
        hs = [t for t in holes(pr) if t[4] >= 40]
        check(len(hs) >= 1, "πρ has a paper a-counter",
              f"n_holes={len(hs)} sizes={[t[4] for t in hs]}")
        if hs:
            overhang = hs[0][0] - x0
            check(overhang >= max(12, int(0.30 * w)),
                  "πρ left a-curl sticks left of the a-bowl (æ, not ω/œ)",
                  f"overhang={overhang}px w={w} hole0={hs[0][0]} x0={x0}")
        if len(hs) >= 2:
            check(hs[1][4] <= hs[0][4] * 0.95,
                  "πρ right e-counter is smaller than the left a-bowl",
                  f"left={hs[0][4]} right={hs[1][4]}")

    # --- ἦν: two-hump wave sitting on the right bowl ------------------------
    # Open double-u has no enclosed holes. Measure how far the right-half
    # top sticks above the bowl ridge. A tiny ear lifts ~0–2px; scan 18's
    # ~ sits a clear stroke above the bowl across most of the right half.
    hn = ink_mask(hb_png("ἦν", 180))
    bb = ink_bbox(hn)
    check(bb is not None, "ἦν has ink")
    if bb:
        x0, y0, x1, y1 = bb
        w, h = x1 - x0 + 1, y1 - y0 + 1
        xmid = x0 + int(0.48 * w)
        # Left-bowl mass vs right-half highest ink. A fused ear lifts ~0–5px
        # above the right ridge; scan 18's ~ is as high as the left stem's
        # shoulder and well above both bowls.
        def col_tops(xa, xb):
            out = []
            for x in range(xa, xb + 1):
                ys = np.where(hn[y0:y1 + 1, x])[0]
                if ys.size:
                    out.append(int(ys[0]))
            return out
        left_bowl = col_tops(x0 + int(0.22 * w), x0 + int(0.48 * w))
        right = col_tops(xmid, x1)
        check(len(left_bowl) >= 8 and len(right) >= 10,
              "ἦν has left-bowl and right-half ink",
              f"nL={len(left_bowl)} nR={len(right)}")
        if len(left_bowl) >= 8 and len(right) >= 10:
            bowl = float(np.percentile(left_bowl, 50))
            right_high = float(min(right))
            lift = bowl - right_high
            check(lift >= 20,
                  "ἦν mark sits above the bowls, not a fused ear",
                  f"lift={lift:.0f}px bowl={bowl:.0f} right_high={right_high:.0f}")
            ycut = y0 + int(0.32 * h)
            wave = hn[y0:ycut + 1, xmid:x1 + 1]
            n_wave = int(wave.sum())
            check(n_wave >= 80,
                  "ἦν wave spans the right bowl (not a terminal spur)",
                  f"n_wave={n_wave}")
            prof = wave.sum(axis=0).astype(float)
            if prof.size >= 10:
                sm = np.convolve(prof, np.ones(5) / 5, mode="same")
                peaks = []
                cap = sm.max() * 0.45 if sm.max() > 0 else 0
                for i in range(2, len(sm) - 2):
                    if sm[i] >= sm[i - 1] and sm[i] >= sm[i + 1] and sm[i] >= cap and cap >= 4:
                        if not peaks or i - peaks[-1] >= 6:
                            peaks.append(i)
                check(len(peaks) >= 2,
                      "ἦν wave is two-hump (breathing+circumflex)",
                      f"peaks={len(peaks)} cap={cap:.1f}")

    print()
    if FAILS:
        print(f"{len(FAILS)} FAIL")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
