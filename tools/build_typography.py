#!/usr/bin/env python3
"""Build the grecs-du-roi webfont stack and Commons glyph assets.

Derives GrecsRoi Greek from GFS Gazis (OFL) so ligature GSUB is registered
under grek/DFLT (upstream only tags latn) and extra catalog sequences get
discretionary ligatures. Subsets companion OFL faces for codepoints Gazis
does not carry. Downloads Wikipedia/Commons specimen images for the 16
alphabetic charts and the seven named historical forms.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

from fontTools.misc.transform import Transform
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otTables import (
    DefaultLangSys,
    Feature,
    FeatureRecord,
    LangSys,
    Script,
    ScriptRecord,
)

ROOT = Path("/Volumes/RAID10/Projects/grecs-du-roi")
SRC = ROOT / "src"
FONTS_DIR = SRC / "fonts"
GLYPHS_DIR = SRC / "glyphs"
CACHE = Path("/tmp/grecs-fonts")
USER_AGENT = "GrecsDuRoiTypography/1.0 (kanban t_95f74713; local specimen build)"

COMMONS = [
    "Greek_ligature_epsilon-iota-circumflex.png",
    "Greek_ligature_gamma-epsilon-rho.png",
    "Greek_ligature_kai.png",
    "Greek_ligature_mu-omega.png",
    "Greek_ligature_omikron-sigma.png",
    "Greek_ligature_oun.png",
    "Greek_ligature_phesi.png",
    "Greek_minuscule_Alpha_with_ligatures.svg",
    "Greek_minuscule_Kappa_with_ligatures.svg",
    "Greek_minuscule_Rho_with_ligatures.svg",
    "Greek_minuscule_Gamma_with_ligatures.svg",
    "Greek_minuscule_Lambda_with_ligatures.svg",
    "Greek_minuscule_Sigma_with_ligatures.svg",
    "Greek_minuscule_Delta_with_ligatures.svg",
    "Greek_minuscule_Mu_with_ligatures.svg",
    "Greek_minuscule_Tau_with_ligatures.svg",
    "Greek_minuscule_Epsilon_with_ligatures.svg",
    "Greek_minuscule_Nu_with_ligatures.svg",
    "Greek_minuscule_Upsilon_with_ligatures.svg",
    "Greek_minuscule_Eta_with_ligatures.svg",
    "Greek_minuscule_Omikron_with_ligatures.svg",
    "Greek_minuscule_Phi_with_ligatures.svg",
    "Greek_minuscule_Theta_with_ligatures.svg",
    "Greek_minuscule_Pi_with_ligatures.svg",
    "Greek_minuscule_Omega_with_ligatures.svg",
]


def fetch(url: str, dest: Path, retries: int = 5) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 100:
        print(f"have {dest.name} ({dest.stat().st_size} bytes)")
        return
    last_err = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                dest.write_bytes(resp.read())
            print(f"fetched {dest.name} ({dest.stat().st_size} bytes)")
            return
        except Exception as exc:
            last_err = exc
            wait = 2 ** attempt
            print(f"retry {dest.name} in {wait}s ({exc})")
            time.sleep(wait)
    raise RuntimeError(f"failed {url}: {last_err}")


def commons_upload_url(filename: str) -> str:
    digest = hashlib.md5(filename.encode("utf-8")).hexdigest()
    return (
        "https://upload.wikimedia.org/wikipedia/commons/"
        f"{digest[0]}/{digest[0:2]}/{filename}"
    )


def download_commons() -> None:
    GLYPHS_DIR.mkdir(parents=True, exist_ok=True)
    for name in COMMONS:
        fetch(commons_upload_url(name), GLYPHS_DIR / name)
        time.sleep(0.25)


def save_woff2(font: TTFont, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(str(path))
    print(f"wrote {path} ({path.stat().st_size} bytes)")


def subset_to_woff2(src: Path, dest: Path, unicodes: list[int], family: str | None = None) -> None:
    font = TTFont(str(src))
    opts = Options()
    opts.layout_features = ["*"]
    opts.glyph_names = True
    opts.notdef_outline = True
    opts.recommended_glyphs = True
    opts.drop_tables = ["DSIG"]
    sub = Subsetter(options=opts)
    sub.populate(unicodes=unicodes)
    sub.subset(font)
    if family:
        rename_family(font, family)
    save_woff2(font, dest)
    font.close()


def rename_family(font: TTFont, family: str) -> None:
    ps = family.replace(" ", "") + "-Regular"
    name = font["name"]
    for rec in name.names:
        if rec.nameID in (1, 16):
            rec.string = family
        elif rec.nameID == 4:
            rec.string = family + " Regular"
        elif rec.nameID == 6:
            rec.string = ps
        elif rec.nameID == 3:
            rec.string = f"1.001;GDR;{ps}"


def _langsys(feature_indices: list[int]) -> DefaultLangSys:
    ls = DefaultLangSys()
    ls.LookupOrder = None
    ls.ReqFeatureIndex = 65535
    ls.FeatureCount = len(feature_indices)
    ls.FeatureIndex = list(feature_indices)
    return ls


def _script_record(tag: str, feature_indices: list[int]) -> ScriptRecord:
    rec = ScriptRecord()
    rec.ScriptTag = tag
    script = Script()
    script.DefaultLangSys = _langsys(feature_indices)
    script.LangSysCount = 0
    script.LangSysRecord = []
    rec.Script = script
    return rec


def _feature_record(tag: str, lookups: list[int]) -> FeatureRecord:
    rec = FeatureRecord()
    rec.FeatureTag = tag
    feat = Feature()
    feat.FeatureParams = None
    feat.LookupCount = len(lookups)
    feat.LookupListIndex = list(lookups)
    rec.Feature = feat
    return rec


def add_composite_cff(font: TTFont, dest_name: str, parts: list[str], overlap: int = 90) -> bool:
    """Append a side-by-side CFF composite. Returns False if a part is missing."""
    gs = font.getGlyphSet()
    for p in parts:
        if p not in gs:
            print(f"  skip composite {dest_name}: missing {p}")
            return False
    widths = [gs[p].width for p in parts]
    total = int(sum(widths) - overlap * (len(parts) - 1))
    if total < 1:
        total = sum(widths)
    top = font["CFF "].cff.topDictIndex[0]
    pen = T2CharStringPen(total, None)
    x = 0.0
    for i, p in enumerate(parts):
        g = gs[p]
        tp = TransformPen(pen, Transform(1, 0, 0, 1, x, 0))
        g.draw(tp)
        if i < len(parts) - 1:
            x += widths[i] - overlap
    cs = pen.getCharString(private=getattr(top, "Private", None), globalSubrs=font["CFF "].cff.GlobalSubrs)
    charstrings = top.CharStrings
    order = list(font.getGlyphOrder())
    if dest_name not in order:
        order.append(dest_name)
        font.setGlyphOrder(order)
    if hasattr(charstrings, "charStringsAreIndexed") and charstrings.charStringsAreIndexed:
        if dest_name in charstrings.charStrings:
            charstrings[dest_name] = cs
        else:
            idx = len(charstrings.charStringsIndex)
            charstrings.charStrings[dest_name] = idx
            charstrings.charStringsIndex.append(cs)
    else:
        charstrings.charStrings[dest_name] = cs
    font["hmtx"].metrics[dest_name] = (total, 0)
    font["maxp"].numGlyphs = len(order)
    try:
        charset = list(top.charset)
        if dest_name not in charset:
            charset.append(dest_name)
            top.charset = charset
    except Exception as exc:
        print(f"  charset note for {dest_name}: {exc}")
    print(f"  composite {dest_name} <- {'+'.join(parts)} width={total}")
    return True


def add_ligature(subtable, first: str, rest: list[str], dest: str) -> None:
    from fontTools.ttLib.tables.otTables import Ligature

    lig = Ligature()
    lig.Component = list(rest)
    lig.LigGlyph = dest
    lig.CompCount = len(rest) + 1
    bucket = subtable.ligatures.setdefault(first, [])
    # longer matches first
    bucket.insert(0, lig)


def patch_gazis(src: Path, dest: Path) -> dict:
    font = TTFont(str(src))
    report = {"composites": [], "extra_ligatures": [], "scripts": [], "features": []}

    extras = [
        ("liga_ger", ["gamma", "epsilon", "rho"], "γερ"),
        ("liga_mo", ["uni03BC", "omega"], "μω"),
        ("liga_oun", ["omicron", "uni1F56", "nu"], "οὖν"),
        ("liga_phesi", ["phi", "eta", "sigma", "uni1F76"], "φησὶ"),
        ("liga_phesi_plain", ["phi", "eta", "sigma", "iota"], "φησι"),
    ]
    for name, parts, label in extras:
        if add_composite_cff(font, name, parts):
            report["composites"].append({"glyph": name, "parts": parts, "label": label})

    gsub = font["GSUB"].table
    liga_sub = gsub.LookupList.Lookup[0].SubTable[0]

    # Catalog sequences missing from upstream Gazis liga.
    extra_rules = [
        ("kappa", ["alpha", "uni1F76"], "kai"),  # καὶ
        ("omicron", ["uni03C2"], "omicronsigma"),  # ος with final sigma
        ("sigma", ["tau"], "uni03DA"),  # στ → stigma
    ]
    if "liga_ger" in font.getGlyphOrder():
        extra_rules.append(("gamma", ["epsilon", "rho"], "liga_ger"))
    if "liga_mo" in font.getGlyphOrder():
        extra_rules.append(("uni03BC", ["omega"], "liga_mo"))
    if "liga_oun" in font.getGlyphOrder():
        extra_rules.append(("omicron", ["uni1F56", "nu"], "liga_oun"))
        extra_rules.append(("ou.psilper", ["nu"], "liga_oun"))
    if "liga_phesi" in font.getGlyphOrder():
        extra_rules.append(("phi", ["eta", "sigma", "uni1F76"], "liga_phesi"))
    if "liga_phesi_plain" in font.getGlyphOrder():
        extra_rules.append(("phi", ["eta", "sigma", "iota"], "liga_phesi_plain"))

    for first, rest, dest_g in extra_rules:
        try:
            add_ligature(liga_sub, first, rest, dest_g)
            report["extra_ligatures"].append({"from": [first] + rest, "to": dest_g})
        except Exception as exc:
            print(f"  liga fail {first}+{rest}: {exc}")

    # Register liga/clig/rlig/dlig/hlig on DFLT, grek, and latn.
    tags = ["liga", "clig", "rlig", "dlig", "hlig"]
    gsub.FeatureList.FeatureRecord = [_feature_record(tag, [0]) for tag in tags]
    gsub.FeatureList.FeatureCount = len(tags)
    indices = list(range(len(tags)))
    gsub.ScriptList.ScriptRecord = [
        _script_record("DFLT", indices),
        _script_record("grek", indices),
        _script_record("latn", indices),
    ]
    gsub.ScriptList.ScriptCount = 3
    report["scripts"] = ["DFLT", "grek", "latn"]
    report["features"] = tags

    rename_family(font, "GrecsRoi Greek")
    # Keep OFL attribution in unique / manufacturer fields.
    for rec in font["name"].names:
        if rec.nameID == 8:
            rec.string = "Greek Font Society (derivative: Grecs du Roi project)"
        elif rec.nameID == 9:
            rec.string = "George D. Matthiopoulos; Grecs du Roi ligature engine"
        elif rec.nameID == 0:
            rec.string = (
                "Derived from GFS Gazis (c) Greek Font Society, OFL 1.1. "
                "Reserved Font Name 'GFS Gazis' is not used for this derivative. "
                "Ligature GSUB extended for polytonic Greek script tags."
            )

    save_woff2(font, dest)
    # Also keep an otf for inspection.
    font.flavor = None
    otf_path = dest.with_suffix(".otf")
    font.save(str(otf_path))
    print(f"wrote {otf_path}")
    font.close()
    return report


def verify_font(path: Path) -> dict:
    font = TTFont(str(path))
    cps = set()
    for t in font["cmap"].tables:
        cps.update(t.cmap.keys())
    gsub = font["GSUB"].table
    scripts = [r.ScriptTag for r in gsub.ScriptList.ScriptRecord]
    feats = [r.FeatureTag for r in gsub.FeatureList.FeatureRecord]
    ligs = []
    st = gsub.LookupList.Lookup[0].SubTable[0]
    for first, lst in st.ligatures.items():
        for lig in lst:
            ligs.append("+".join([first] + list(lig.Component)) + "->" + lig.LigGlyph)
    font.close()
    return {"scripts": scripts, "features": feats, "ligature_count": len(ligs), "ligatures": ligs}


def main() -> int:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    try:
        download_commons()
    except Exception as exc:
        print("commons download incomplete:", exc)
        print("continuing with fonts; remaining glyphs can be filled later")

    noto_src = CACHE / "NotoSerif-var.ttf"
    fetch(
        "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notoserif/NotoSerif[wdth,wght].ttf",
        noto_src,
    )

    gazis_src = CACHE / "gazis/GFS_GAZIS/GFSGazis.otf"
    didot_src = CACHE / "GFSDidot-Regular.ttf"
    cardo_src = CACHE / "Cardo-Regular.ttf"
    gentium_src = CACHE / "GentiumPlus-Regular.ttf"
    for p in (gazis_src, didot_src, cardo_src, gentium_src):
        if not p.exists():
            raise SystemExit(f"missing cached font {p}")

    report = {}
    report["gazis"] = patch_gazis(gazis_src, FONTS_DIR / "grecs-roi-greek.woff2")
    report["verify"] = verify_font(FONTS_DIR / "grecs-roi-greek.woff2")

    # GFS Didot: Latin + polytonic Greek fallback (stigma small U+03DB, etc.)
    didot = TTFont(str(didot_src))
    rename_family(didot, "GFS Didot")
    save_woff2(didot, FONTS_DIR / "gfs-didot.woff2")
    didot.close()

    subset_to_woff2(
        cardo_src,
        FONTS_DIR / "cardo-ou.woff2",
        unicodes=[0x0222, 0x0223, 0x0020],
        family="Cardo",
    )
    subset_to_woff2(
        gentium_src,
        FONTS_DIR / "gentium-kai-cap.woff2",
        unicodes=[0x03CF, 0x0020],
        family="Gentium Plus",
    )
    subset_to_woff2(
        noto_src,
        FONTS_DIR / "noto-serif-uk.woff2",
        unicodes=[0xA64A, 0xA64B, 0x0020],
        family="Noto Serif",
    )

    # Licences
    for src, name in [
        (CACHE / "GFSDidot-OFL.txt", "OFL-GFSDidot.txt"),
        (CACHE / "Cardo-OFL.txt", "OFL-Cardo.txt"),
        (CACHE / "gazis/GFS_GAZIS/OFL.txt", "OFL-GFSGazis.txt"),
    ]:
        if src.exists():
            shutil.copy(src, FONTS_DIR / name)

    (FONTS_DIR / "coverage.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["verify"], indent=2, ensure_ascii=False))
    print("glyph files", len(list(GLYPHS_DIR.iterdir())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
