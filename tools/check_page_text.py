#!/usr/bin/env python3
"""check_page_text.py — the text-collation invariant shared by the QA gates.

src/estienne-john1.html is a scan-collated recreation: its text base is
corpus/john1_estienne1550.json (the Estienne 1550 fol. 161 wording, vv.1-19
up to the page break at 'ὅτε'; the v19 tail past the break comes from
corpus/john1_wh.json). The Phase 2.0 gate therefore has to compare the
rendered copy against the ATTESTED page text, not against Westcott-Hort:
the folio genuinely differs from WH (e.g. v1 ἦν ὁ λόγος ... Θεόν orderings,
v4 Ἐν αὐτῷ, v6 capital Θεοῦ, v18 ὁ μονογενὴς υἱός — see the `notes`
column in the corpus file), and comparing against WH would report the very
collation work of Phase 2.4 as a copy failure.

Tiers (unchanged from the Phase 2.0 gate):
  * zero PUA characters in the copied text
  * John 1:1 core phrase survives select-all copy
  * nomina-sacra letters survive copy as real Unicode (ΘΥ/ΙΥ/ΧΥ toggle on
    the page — the sigma-final ΘΣ/ΧΣ set from the inventory stays accepted
    for any build still rendering those forms), with the overline stripped
  * skeleton diff per verse (letters only, caseless, marks/overline stripped,
    whitespace collapsed) against the attested scan text must be EMPTY
  * strict byte-exact NFC diff (macrons stripped) is REPORTED, not failed:
    the nomina toggle replaces contractions with data-full expansions, so
    byte-exactness is a later gate (whitespace-only diffs here are the
    expected state)
"""
import json
import unicodedata

BASE = "/Volumes/RAID10/jon/Projects/grecs-du-roi"


def load_expected():
    """Per-verse expected text for the rendered extent (vv.1-19).

    Mirrors tools/build_estienne_page.py verse_text(): the scan-collated
    wording per verse; the folio breaks mid-v19 at 'ὅτε' and the builder's
    pagebreak-tail is currently empty there, so the attested string is the
    full expected text.
    """
    scan = json.load(open(BASE + "/corpus/john1_estienne1550.json",
                          encoding="utf-8"))
    return {str(v): rec["scan"] for v, rec in scan["verses"].items()}


def skel(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(c for c in s if not c.isspace())
    return s.casefold()


def norm_ws(s):
    return " ".join(s.split())


def strip_bars(s):
    return s.replace("\u0304", "").replace("\u0305", "")


def check_copy(name, copied, verse_pairs=None, expected=None):
    """Return list of failures for a browser's copied string (+ per-verse data)."""
    fails = []
    pua = [c for c in copied if 0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c)]
    if pua:
        fails.append(f"{name}: {len(pua)} PUA chars in copy: {pua[:5]!r}")
    if "ἦν ὁ λόγος" not in copied:
        fails.append(f"{name}: John 1:1 core phrase missing from copy")
    # Nomina-sacra letters must survive copy as real Unicode (not PUA).
    # The folio's verified contractions are the Υ-final set (ΘΥ/ΙΥ/ΧΥ,
    # corpus nomina_sacra.attested_forms — Phase 2.4 collation); the older
    # sigma-final set (ΘΣ/ΧΣ) from the Phase 2.0 inventory stays accepted.
    # Matched on the skeleton (NFD-decomposed, marks stripped, casefolded):
    # the rendered Υ carries a macron and NFC re-composes it to U+1FE9, so a
    # raw substring test on the copy can never see "ΘΥ".
    skel_copy = skel(copied)
    if not ("θυ" in skel_copy or "θσ" in skel_copy):
        fails.append(f"{name}: nomen sacrum Θ-form (ΘΥ/ΘΣ) lost on copy")
    if not ("χυ" in skel_copy or "χσ" in skel_copy):
        fails.append(f"{name}: nomen sacrum Χ-form (ΧΥ/ΧΣ) lost on copy")
    if verse_pairs is not None:
        if expected is None:
            expected = load_expected()
        strict_diffs, skel_diffs = [], []
        for v, text in verse_pairs:
            if str(v) not in expected:
                continue
            want = unicodedata.normalize("NFC", expected[str(v)])
            got = unicodedata.normalize("NFC", text)
            if norm_ws(strip_bars(want)) != norm_ws(strip_bars(got)):
                strict_diffs.append((v, norm_ws(want)[:40],
                                     norm_ws(got)[:40]))
            if skel(want) != skel(norm_ws(got)):
                skel_diffs.append((v, norm_ws(want)[:40],
                                   norm_ws(got)[:40]))
        if skel_diffs:
            fails.append(f"{name}: NFC copy-diff NOT empty on "
                         f"{len(skel_diffs)} verse(s): "
                         + "; ".join(f"v{v} want {w!r} got {g!r}"
                                     for v, w, g in skel_diffs[:3]))
        if strict_diffs:
            print(f"    [{name}] strict-byte NFC diff pending on verses "
                  f"{','.join(str(v) for v, _, _ in strict_diffs)} "
                  f"(drop-cap/nomina display forms — collation display tier)")
    return fails
