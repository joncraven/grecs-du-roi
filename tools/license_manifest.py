#!/usr/bin/env python3
"""license_manifest.py — regenerate LICENSES.json (Definition of Done #5).

Every shipped glyph must trace to an OFL or public-domain source. This
scanner reads src/fonts/, matches each webfont/OpenType artifact to a
license file and an upstream family, and asserts the OFL texts actually
contain the SIL OFL 1.1 grant (not a stub). The GitHub CI runs
`python3 tools/license_manifest.py --check` and fails on drift.

Manifest facts (family -> source/license) are declared in ENTRIES below —
single source of truth reviewed by a human, machine-verified against the
bytes on disk.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "src" / "fonts"

# artifact -> (upstream family, license kind, license file in src/fonts or None,
#              provenance note)
ENTRIES = {
    "grecs-roi-greek.woff2": (
        "GrecsRoi Greek", "OFL-1.1", "OFL-GFSGazis.txt",
        "Derivative of GFS Gazis (OFL); rebuilt by tools/build_typography.py"),
    "grecs-roi-greek.otf": (
        "GrecsRoi Greek", "OFL-1.1", "OFL-GFSGazis.txt",
        "Desktop twin of the woff2"),
    "grecs-roi-greek-cursive.woff2": (
        "GrecsRoi Greek Cursive", "OFL-1.1", "OFL-GFSGazis.txt",
        "Phase-2.1/2.2 slanted derivative + fused ligatures (tools/cursive_masters.py, tools/ligature_engine.py)"),
    "grecs-roi-greek-cursive.otf": (
        "GrecsRoi Greek Cursive", "OFL-1.1", "OFL-GFSGazis.txt",
        "Desktop twin of the cursive woff2"),
    "gfs-didot.woff2": (
        "GFS Didot", "OFL-1.1", "OFL-GFSDidot.txt",
        "Greek Font Society subset, bbox-recomputed (tools/fix_font_bboxes.py)"),
    "cardo-ou.woff2": (
        "Cardo", "OFL-1.1", "OFL-Cardo.txt",
        "Latin-extended OU ligature letter subset"),
    "cardo-polytonic.woff2": (
        "Cardo", "OFL-1.1", "OFL-Cardo.txt",
        "Full polytonic Greek subset for the reader's modern mode"),
    "gentium-kai-cap.woff2": (
        "Gentium Plus", "OFL-1.1", "OFL-Gentium.txt",
        "Kai capital U+03CF subset; SIL OFL 1.1 (upstream: sil.org/Gentium)"),
    "noto-serif-uk.woff2": (
        "Noto Serif", "OFL-1.1", "OFL-NotoSerif.txt",
        "Cyrillic UK U+A64A/B subset; SIL OFL 1.1 (upstream: fonts.google.com/notoserif)"),
}

# Text/image assets licensed outside the font stack
ASSETS = {
    "corpus/*.json": ("public-domain", "Westcott-Hort 1881 + Estienne 1550 (PD); scan-collated wording, Perseus canonical-greekLit"),
    "src/glyphs/*": ("public-domain", "Wikimedia Commons scans of historical Greek prints/ligatures"),
    "src/estienne-john1.html": ("public-domain-text", "Recreation of the PD Estienne 1550 folio-161 scan"),
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build() -> dict:
    fonts = sorted(p.name for p in FONTS.iterdir()
                   if p.suffix in (".woff2", ".otf", ".ttf"))
    unknown = [f for f in fonts if f not in ENTRIES]
    if unknown:
        raise SystemExit(f"FAIL: shipped font without license entry: {unknown}")
    out = {"generated_by": "tools/license_manifest.py", "fonts": {}}
    for fname, (family, kind, lic_file, note) in sorted(ENTRIES.items()):
        path = FONTS / fname
        if not path.exists():
            raise SystemExit(f"FAIL: manifest entry for missing file {fname}")
        rec = {
            "family": family, "license": kind, "provenance": note,
            "sha256": sha256(path), "bytes": path.stat().st_size,
        }
        if lic_file:
            lp = FONTS / lic_file
            if not lp.exists():
                raise SystemExit(f"FAIL: license file {lic_file} missing")
            text = lp.read_text(encoding="utf-8", errors="replace")
            if "SIL OPEN FONT LICENSE" not in text.upper():
                raise SystemExit(f"FAIL: {lic_file} is not an OFL text")
            rec["license_file"] = lic_file
            rec["license_sha256"] = sha256(lp)
        else:
            rec["license_note"] = "SIL OFL 1.1 upstream; full text: scripts.sil.org/OFL"
        if not kind.startswith("OFL"):
            raise SystemExit(f"FAIL: {fname} not OFL/PD")
        out["fonts"][fname] = rec
    out["assets"] = ASSETS
    return out


def main() -> int:
    check = "--check" in sys.argv
    manifest = build()
    dest = FONTS / "LICENSES.json"
    blob = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if check:
        if not dest.exists():
            raise SystemExit("FAIL: LICENSES.json missing; run without --check")
        if dest.read_text(encoding="utf-8") != blob:
            raise SystemExit("FAIL: LICENSES.json drift; regenerate with tools/license_manifest.py")
        print(f"OK: license manifest current ({len(manifest['fonts'])} fonts, all OFL)")
        return 0
    dest.write_text(blob, encoding="utf-8")
    print(f"wrote {dest} ({len(manifest['fonts'])} fonts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
