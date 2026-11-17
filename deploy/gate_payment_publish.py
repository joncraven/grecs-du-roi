#!/usr/bin/env python3
"""Human gate for payment checkout URLs in a ship set (t_1259dd7a).

Default: refuse to publish if the tree contains PayPal, Stripe, Polar
checkout links, or data-donate-link attributes.

To re-enable Polar only, a human must write PAYMENT_PUBLISH_APPROVED
next to this script's --allowfile (default: deploy/PAYMENT_PUBLISH_APPROVED)
with:

    approved_by=<human name>
    approved_at=<ISO date>
    provider=polar
    checkout_url=https://buy.polar.sh/polar_cl_...

Any other provider, or Polar URL that does not match checkout_url exactly
(optional ?amount= query allowed), still fails. PayPal and Stripe always fail.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALWAYS_FORBIDDEN = re.compile(
    r"paypal\.me|paypal\.com|buy\.stripe\.com|js\.stripe\.com",
    re.I,
)
POLAR = re.compile(r"buy\.polar\.sh|polar\.sh/|polar_cl_", re.I)
DONATE_ATTR = re.compile(r"data-donate-link", re.I)
SCAN_SUFFIXES = {".html", ".htm", ".js", ".css", ".json", ".xml", ".txt", ".md"}


def load_allowfile(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip().lower()] = v.strip()
    return out


def polar_url_ok(url_in_file: str, allowed: str) -> bool:
    if url_in_file == allowed:
        return True
    prefix = allowed + "?amount="
    return url_in_file.startswith(prefix) and url_in_file[len(prefix) :].isdigit()


def iter_text_files(root: Path):
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in SCAN_SUFFIXES and f.name != "PAYMENT_PUBLISH_APPROVED":
            continue
        if f.name == "PAYMENT_PUBLISH_APPROVED":
            continue
        yield f


def scan(root: Path, allow: dict[str, str] | None) -> list[str]:
    errors: list[str] = []
    allowed_url = ""
    polar_enabled = False
    if allow:
        missing = [k for k in ("approved_by", "approved_at", "provider", "checkout_url") if not allow.get(k)]
        if missing:
            return [f"allowfile missing fields: {', '.join(missing)}"]
        if allow["provider"].lower() != "polar":
            return [f"provider={allow['provider']!r} is forbidden; only polar is allowed"]
        allowed_url = allow["checkout_url"]
        if not allowed_url.startswith("https://buy.polar.sh/polar_cl_"):
            return [f"checkout_url is not a Polar Checkout Link: {allowed_url}"]
        polar_enabled = True

    url_re = re.compile(r"https?://[^\s\"'<>]+", re.I)
    for f in iter_text_files(root):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"{f}: {exc}")
            continue
        rel = f.relative_to(root)
        if ALWAYS_FORBIDDEN.search(text):
            errors.append(f"{rel}: forbidden non-Polar payment URL (PayPal/Stripe)")
        if DONATE_ATTR.search(text) and not polar_enabled:
            errors.append(f"{rel}: data-donate-link present without human Polar approval")
        if POLAR.search(text) and not polar_enabled:
            errors.append(f"{rel}: Polar checkout URL present without human approval")
        if polar_enabled:
            for m in url_re.findall(text):
                if POLAR.search(m) and not polar_url_ok(m, allowed_url):
                    errors.append(f"{rel}: Polar URL {m} does not match approved checkout_url")
            if DONATE_ATTR.search(text) and allowed_url not in text:
                errors.append(f"{rel}: data-donate-link without the approved Polar URL")
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path, help="ship-set directory to scan")
    p.add_argument(
        "--allowfile",
        type=Path,
        default=None,
        help="human approval file (default: <root>/../deploy/PAYMENT_PUBLISH_APPROVED or ./deploy/PAYMENT_PUBLISH_APPROVED)",
    )
    args = p.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"gate_payment_publish: not a directory: {root}", file=sys.stderr)
        return 2
    allowfile = args.allowfile
    if allowfile is None:
        for cand in (root.parent / "deploy" / "PAYMENT_PUBLISH_APPROVED", Path("deploy/PAYMENT_PUBLISH_APPROVED")):
            if cand.is_file():
                allowfile = cand
                break
        if allowfile is None:
            allowfile = root.parent / "deploy" / "PAYMENT_PUBLISH_APPROVED"
    allow = load_allowfile(allowfile)
    errors = scan(root, allow)
    if errors:
        print("PAYMENT PUBLISH GATE FAILED (t_1259dd7a)", file=sys.stderr)
        print("Payment checkout URLs cannot ship without a human Polar allowfile.", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("payment publish gate: ok (no unauthorized checkout URLs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
