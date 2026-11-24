#!/usr/bin/env python3
"""collation_cycle.py — the word-by-word correction cycle (t_717701c6).

The cycle state is the pair (corpus/john1_word_matrix.json, derived from
tools/word_matrix.py) + (corpus/john1_word_ledger.json, the append-only
decision store). Progress = open diffs going down, decisions going up.

Commands:
  stats                       open/decided counts per status, last round
  next [--round N]            the next batch of open items (contested and
                              variant first — the ones worth a human eye),
                              with the evidence pointers for each
  record --key KEY --verdict V [--note TEXT] [--round N]
                              append one decision to the ledger and rebuild
                              the matrix. Verdicts:
                                confirmed      scan reading stands (diff is
                                               real and correct on the page)
                                corrected      corpus was wrong; the entry
                                               was fixed in the corpus file
                                glyph-fix      text stands; the FONT form is
                                               what needed work (routes to a
                                               glyph punch-list note)
                                superseded     replaced by a later decision
  note --key KEY --note TEXT   attach/replace evidence on an open item
  apply-corrections            list decisions whose verdict implies a corpus
                              edit not yet reflected in the matrix

Every decision records round number, timestamp, and evidence text, so the
ledger is the audit trail the acceptance criteria ask for ("records or
tracks differences and shows progress").
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "corpus/john1_word_matrix.json"
LEDGER = ROOT / "corpus/john1_word_ledger.json"

OPEN_BY_STATUS = {  # what still needs adjudication, by priority
    "contested": 0,
    "variant": 1,
    "scan_only": 2,
    "wh_only": 3,
    "casing": 4,
    "elision": 5,
}
# statuses that count as a live difference until decided
DIFF_STATUSES = set(OPEN_BY_STATUS)


def load_matrix():
    if not MATRIX.exists():
        subprocess.run([sys.executable, str(ROOT / "tools/word_matrix.py")],
                       check=True, capture_output=True)
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def load_ledger():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"decisions": []}


def save_ledger(led):
    LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "tools/word_matrix.py")],
                   check=True, capture_output=True)


def open_items(m):
    out = []
    for w in m["words"]:
        if "decision" in w or w["status"] not in DIFF_STATUSES:
            continue
        cls = "contested" if w["contested_note"] else w["status"]
        out.append((OPEN_BY_STATUS[cls], w["verse"], cls, w))
    out.sort(key=lambda t: (t[0], t[1]))
    return [t[3] for t in out]


def cmd_stats(m, led):
    from collections import Counter
    status = Counter(w["status"] for w in m["words"])
    decided = Counter(d["verdict"] for d in led["decisions"])
    rounds = sorted({d.get("round", 0) for d in led["decisions"]})
    open_list = open_items(m)
    by_cls = Counter(("contested" if w["contested_note"] else w["status"])
                     for w in open_list)
    total = len(m["words"])
    print(f"words tracked:        {total}")
    for k in ("match", "casing", "elision", "variant", "scan_only", "wh_only"):
        print(f"  {k:10s} {status.get(k, 0)}")
    print(f"open items (no decision): {len(open_list)}")
    for k in ("contested", "variant", "scan_only", "wh_only", "casing",
              "elision"):
        if by_cls.get(k):
            print(f"  {k:10s} {by_cls[k]}")
    print(f"decisions in ledger:  {len(led['decisions'])}")
    for k, v in decided.items():
        print(f"  {k:12s} {v}")
    print(f"rounds recorded:      {rounds}")
    if led["decisions"]:
        last = max(led["decisions"], key=lambda d: (d.get("round", 0),
                                                    d.get("ts", "")))
        print(f"last decision:        round {last.get('round')} "
              f"{last['key']} -> {last['verdict']}")


def cmd_next(m, n):
    items = open_items(m)[:n]
    if not items:
        print("no open items — the cycle is done for this page")
        return
    for w in items:
        cls = "contested" if w["contested_note"] else w["status"]
        print(f"[{cls:9s}] {w['key']}")
        print(f"   scan: {w['scan']!r}   wh: {w['wh']!r}")
        if w["contested_note"]:
            print(f"   note: {w['contested_note']}")
        print(f"   evidence: qa-evidence/crops/secondsource/ (300-dpi) +"
              f" src/estienne-scan.jpg (task scan)")
    print(f"\nshowing {len(items)} of {len(open_items(m))} open items")


def cmd_record(m, led, key, verdict, note, rnd):
    known = {w["key"] for w in m["words"]}
    if key not in known:
        sys.exit(f"unknown key {key!r} (run: collation_cycle.py next)")
    if verdict not in ("confirmed", "corrected", "glyph-fix", "superseded"):
        sys.exit(f"bad verdict {verdict!r}")
    # replacing a prior decision on the same key keeps history: mark old one
    for d in led["decisions"]:
        if d["key"] == key and "superseded_by" not in d:
            d["superseded_by"] = f"round {rnd} {verdict}"
    entry = {"key": key, "verdict": verdict, "round": rnd,
             "ts": datetime.datetime.now(datetime.timezone.utc)
                   .strftime("%Y-%m-%dT%H:%MZ"),
             "note": note or ""}
    led["decisions"].append(entry)
    save_ledger(led)
    print(f"recorded round {rnd}: {key} -> {verdict}")
    m2 = load_matrix()
    cmd_stats(m2, load_ledger())


def cmd_apply(m):
    """Decisions that imply a corpus edit not yet reflected in the matrix."""
    pend = []
    for w in m["words"]:
        d = w.get("decision")
        if d and d["verdict"] == "corrected" and w["status"] != "match":
            pend.append((w["key"], d))
    if not pend:
        print("no pending corpus corrections")
    for key, d in pend:
        print(f"pending edit: {key} (round {d.get('round')}: {d['note'][:60]})")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    p = sub.add_parser("next")
    p.add_argument("--count", "-n", type=int, default=12)
    p = sub.add_parser("record")
    p.add_argument("--key", required=True)
    p.add_argument("--verdict", required=True)
    p.add_argument("--note", default="")
    p.add_argument("--round", "-r", type=int, default=1)
    p = sub.add_parser("note")
    p.add_argument("--key", required=True)
    p.add_argument("--note", required=True)
    sub.add_parser("apply-corrections")
    args = ap.parse_args()
    m, led = load_matrix(), load_ledger()
    if args.cmd == "stats":
        cmd_stats(m, led)
    elif args.cmd == "next":
        cmd_next(m, args.count)
    elif args.cmd == "record":
        cmd_record(m, led, args.key, args.verdict, args.note, args.round)
    elif args.cmd == "note":
        cmd_note(m, led, args.key, args.note)
    elif args.cmd == "apply-corrections":
        cmd_apply(m)


if __name__ == "__main__":
    main()
