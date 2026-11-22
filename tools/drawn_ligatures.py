#!/usr/bin/env python3
"""Hand-drawn Estienne ligatures for t_8ad4e391.

π (scan 49): compact two-stem minuscule, arched bar, one closed outline.
Not varpi.

πρ (scan 22): italic æ = ɑ + e. The left silhouette is an a-curl that is
LEFTMOST at curl-height, with the ɑ-bowl wall inset from that curl. Two
open paper counters. Not œ (two equal o's, widest at the equator) and
not ω.

ἦν / ἤν (scan 18): double-u; two-hump wave sits ON the right-bowl ink
with a trailing flick — a naive reader must see the marks.
"""
from __future__ import annotations

import math


def _cubic(p0, p1, p2, p3, n=18):
    pts = []
    for i in range(n):
        t = i / n
        u = 1.0 - t
        pts.append((
            u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
            u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1],
        ))
    return pts


def _chain(segments, n=18):
    pts = []
    for seg in segments:
        pts.extend(_cubic(*seg, n=n))
    pts.append(segments[-1][3])
    return pts


def _offset(pts, radius, closed=False):
    n = len(pts)
    ns = []
    for i, p in enumerate(pts):
        if closed:
            a, b = pts[i - 1], pts[(i + 1) % n]
        else:
            a = pts[max(0, i - 1)]
            b = pts[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        ns.append((-ty / L, tx / L))
    sm = []
    for i, nrm in enumerate(ns):
        if closed:
            a, b = ns[i - 1], ns[(i + 1) % n]
        else:
            a = ns[max(0, i - 1)]
            b = ns[min(n - 1, i + 1)]
        x, y = a[0] + nrm[0] + b[0], a[1] + nrm[1] + b[1]
        L = math.hypot(x, y) or 1.0
        sm.append((x / L, y / L))
    left = [(p[0] + n[0] * radius, p[1] + n[1] * radius) for p, n in zip(pts, sm)]
    right = [(p[0] - n[0] * radius, p[1] - n[1] * radius) for p, n in zip(pts, sm)]
    if closed:
        outline = left + list(reversed(right))
    else:
        def _tan(a, b):
            tx, ty = b[0] - a[0], b[1] - a[1]
            L = math.hypot(tx, ty) or 1.0
            return (tx / L, ty / L)

        def round_cap(center, n_from, t_out, steps=8):
            out = []
            for i in range(1, steps):
                a = math.pi * (i / steps)
                nx = n_from[0] * math.cos(a) + t_out[0] * math.sin(a)
                ny = n_from[1] * math.cos(a) + t_out[1] * math.sin(a)
                L = math.hypot(nx, ny) or 1.0
                out.append((center[0] + nx / L * radius,
                            center[1] + ny / L * radius))
            return out

        te = _tan(pts[-2], pts[-1])
        ts = _tan(pts[0], pts[1])
        outline = (
            left
            + round_cap(pts[-1], sm[-1], te)
            + list(reversed(right))
            + round_cap(pts[0], (-sm[0][0], -sm[0][1]), (-ts[0], -ts[1]))
        )
    ops = [("moveTo", outline[0])]
    for q in outline[1:]:
        ops.append(("lineTo", q))
    ops.append(("closePath", ()))
    return ops


def ribbon(segments, radius=24.0, closed=False, n=20):
    return _offset(_chain(segments, n=n), radius, closed=closed)


def _ops_from_cubics(segs):
    ops = [("moveTo", segs[0][0])]
    for s in segs:
        ops.append(("curveTo", (s[1], s[2], s[3])))
    ops.append(("closePath", ()))
    return ops


def master_pi_flat():
    """Scan 49: compact two-stem minuscule π, not Latin n.

    Two parallel posts under a slightly arched roof. The roof is a lid
    across both stems (π), not an n-shoulder that springs from the left
    post into a thick right leg. Small right foot. Ribbons only so the
    paper counter between stems stays open (CFF non-zero fill).
    """
    w = 400
    ops = []
    # Left post
    ops += ribbon([
        ((72, 18), (70, 140), (72, 280), (74, 410)),
    ], radius=26.0, n=16)
    # Right post (near-parallel, slight thick)
    ops += ribbon([
        ((292, 18), (294, 140), (296, 280), (298, 410)),
    ], radius=30.0, n=16)
    # Roof / lid: sits ON the posts, slight arch, small overhang both sides
    ops += ribbon([
        ((28, 418), (90, 455), (190, 468), (300, 452)),
        ((300, 452), (330, 444), (348, 428), (352, 408)),
    ], radius=22.0, n=18)
    # Short right foot (scan 49 kicks out at the baseline)
    ops += ribbon([
        ((292, 18), (318, 6), (348, 10), (372, 28)),
    ], radius=16.0, n=12)
    return ops, w


def alt_pi_rho():
    """Scan 22: italic æ (a+e), not œ (o+o) and not ω.

    Left = ɑ with a far-left curl (leftmost at curl-height) and a D-bowl
    whose wall sits right of that curl. Right = italic e (small eye +
    crossbar + open lower), not a second o. Thin lid. Ribbons only.
    """
    w = 8
    ops = []
    # Hook: leftmost ~x=0 at y≈270. Separate from the bowl wall.
    ops += ribbon([
        ((75, 180), (25, 205), (0, 255), (6, 310)),
        ((6, 310), (18, 355), (70, 395), (130, 405)),
        ((130, 405), (175, 408), (215, 385), (238, 350)),
    ], radius=12.5, n=22)
    # ɑ-bowl: closed D against the stem. Left wall ~x=155 at y=210.
    ops += ribbon([
        ((248, 350), (190, 372), (148, 305), (142, 215)),
        ((142, 215), (140, 135), (168, 42), (218, 16)),
        ((218, 16), (248, 8), (262, 55), (258, 140)),
        ((258, 140), (255, 230), (252, 310), (248, 350)),
    ], radius=16.5, n=22)
    # Stem.
    ops += ribbon([
        ((250, 405), (258, 245), (260, 75), (252, 4)),
    ], radius=17.0, n=10)
    # Italic e: small upper eye, crossbar, open lower (NOT a closed o).
    ops += ribbon([
        ((300, 255), (345, 305), (395, 295), (408, 250)),
        ((408, 250), (400, 220), (355, 215), (315, 235)),
        ((315, 235), (300, 250), (302, 255), (300, 255)),
    ], radius=13.0, n=18)
    ops += ribbon([
        ((268, 238), (320, 250), (380, 248), (425, 232)),
    ], radius=10.0, n=12)
    ops += ribbon([
        ((305, 230), (325, 140), (355, 45), (415, 18)),
        ((415, 18), (455, 8), (470, 55), (448, 95)),
    ], radius=14.0, n=16)
    ops += ribbon([
        ((120, 402), (210, 422), (310, 400), (400, 320)),
    ], radius=8.0, n=14)
    return ops, w


def alt_eta_nu():
    """Scan 18: double-u. Tall left stem with a left serif; two U-bowls."""
    w = 620
    r = 31.0
    ops = []
    ops += ribbon([
        ((8, 510), (-16, 518), (-20, 478), (6, 455)),
        ((6, 455), (18, 280), (36, 55), (118, 12)),
        ((118, 12), (180, -8), (240, 28), (252, 160)),
        ((252, 160), (258, 250), (250, 320), (238, 350)),
    ], radius=r, n=22)
    ops += ribbon([
        ((238, 345), (246, 180), (290, 12), (380, 12)),
        ((380, 12), (460, 12), (510, 80), (500, 210)),
        ((500, 210), (492, 290), (470, 330), (448, 342)),
    ], radius=r, n=22)
    return ops, w


def alt_eta_nu_marks():
    """Scan 18: two-hump wave ON the right-bowl ink, trailing flick.

    Right bowl of alt_eta_nu tops near y=342 / x=448, ribbon radius 31 so
    ink reaches ~y=373. Wave troughs sit on that ink; peaks clear it by
    ~90 units so 180pt hb-view shows a ~ not an ear.
    """
    return ribbon([
        ((355, 372), (395, 455), (448, 442), (492, 375)),
        ((492, 375), (540, 460), (592, 440), (638, 348)),
    ], radius=14.0, n=20)
