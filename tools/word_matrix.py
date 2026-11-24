#!/usr/bin/env python3
"""word_matrix.py — the structured word-by-word comparison behind the
scan-vs-text correction cycle (t_717701c6).

Each word of the folio (corpus/john1_estienne1550.json, scan-collated
readings) is aligned against the corresponding Westcott-Hort word run
(corpus/john1_wh.json) and classified:

  match      bare letters identical (notation freedom only)
  casing     letters agree; scan differs only in capitalisation (Θεόν etc.)
  elision    letters identical; the elision apostrophe glyph differs (᾽ vs ʼ)
  variant    a genuine orthographic/wording difference (κέκραγε, Μωσέως …)
  scan_only  the scan word could not be paired to any WH word
  wh_only    a WH word has no counterpart on the folio (candidate omission
             or a wording gap the next review round must adjudicate)

Contested flags are seeded from the per-verse `notes` column of the corpus
file plus the corpus-level nomina_sacra contestation: a word named in a
note (or a word inside a contested nomen-sacra verse) becomes contested,
so the cycle starts from exactly the questions the collation already
logged instead of a cold re-review.

Every entry gets a stable key  v<verse>w<index>:<word>  (WH-only entries:
v<verse>Wh<j>:<word>).  Decisions are recorded against that key in
corpus/john1_word_ledger.json (append-only, via tools/collation_cycle.py
record) and SURVIVE regeneration: the matrix is rebuilt from corpus +
ledger each time, so progress = decisions applied, never a rewritten
baseline.

Rebuild: python3 tools/word_matrix.py
"""
import difflib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = ROOT / "corpus/john1_estienne1550.json"
WH = ROOT / "corpus/john1_wh.json"
MATRIX_OUT = ROOT / "corpus/john1_word_matrix.json"
LEDGER = ROOT / "corpus/john1_word_ledger.json"

PUNCT = ".,·;:()\"'\u02bc\u2019\u2018\u2013-\u2014\u1fbd\u1fbf\u1ffe"
GREEP = r"[\u0370-\u1FFF']"


def strip_word(word: str) -> str:
    """A word stripped of leading/trailing editorial punctuation
    (WH wraps some verses in parentheses) for alignment."""
    return word.strip(PUNCT)


def skeleton(word: str) -> str:
    """Letters only: NFD, strip combining marks and punctuation, casefold,
    unify the elision apostrophe so δι᾽ and δι' compare equal."""
    s = unicodedata.normalize("NFD", word)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\u2019", "'").replace("\u02bc", "'").replace("\u1fbd", "'")
    s = "".join(c for c in s if c not in PUNCT)
    return s.casefold()


def letters(word: str) -> str:
    """Case-preserving bare letters (punctuation and marks removed)."""
    s = unicodedata.normalize("NFD", word)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s if c not in PUNCT)


def core(word: str) -> str:
    """Skeleton with elision apostrophes removed too (δι' -> δι)."""
    return skeleton(word).replace("'", "")


def tokenize(text: str) -> list:
    """Split a verse line into words on whitespace, keeping punctuation
    attached to its preceding word (scan convention)."""
    return text.split()


def classify(scan_w: str, wh_w: str) -> str:
    """match | casing | elision | variant for a paired word."""
    la, lb = letters(scan_w), letters(wh_w)
    if la == lb:
        apo_a = ("\u02bc" in scan_w) != ("\u02bc" in wh_w) or \
                ("\u2019" in scan_w) != ("\u2019" in wh_w)
        return "elision" if apo_a else "match"
    if la.casefold() == lb.casefold():
        return "casing"
    return "variant"


def char_sim(a: str, b: str) -> float:
    """Similarity on accent-stripped, casefolded letters — Greek pairs
    on bare letters, diacritics would only punish legitimate matches."""
    return difflib.SequenceMatcher(None, skeleton(a), skeleton(b),
                                   autojunk=False).ratio()


def pair_block(sw, ww, i0, i1, j0, j1, min_sim=0.6):
    """Pair scan words sw[i0:i1] with WH words ww[j0:j1] greedily by
    character similarity, order-preserving."""
    cands = []
    for i in range(i0, i1):
        for j in range(j0, j1):
            cands.append((char_sim(strip_word(sw[i]), strip_word(ww[j])), i, j))
    cands.sort(reverse=True)
    used_i, used_j, out = set(), set(), {}
    for sim, i, j in cands:
        if sim < min_sim:
            break
        if i in used_i or j in used_j:
            continue
        used_i.add(i)
        used_j.add(j)
        out[i] = j
    return out


def note_contested_words(note: str) -> set:
    """Bare-letter forms of every Greek word mentioned in a collation note."""
    found = set()
    for m in re.finditer(GREEP + r"{2,}", note):
        sk = core(m.group(0))
        if sk:
            found.add(sk)
    return found


def page_contestation(scan: dict) -> set:
    """Contested word forms implied corpus-wide: the nomina-sacra
    overline/spelling contestation covers the Θε- words of the verses it
    cites (corpus nomina_sacra.attestation names 1:1/1:17 among others)."""
    extra = set()
    ns = scan.get("nomina_sacra", {})
    text = json.dumps(ns, ensure_ascii=False)
    if "contested" in text or "Overline status contested" in text:
        for m in re.finditer(GREEP + r"{2,}", text):
            sk = core(m.group(0))
            if sk.startswith(("θ", "ι", "χ")):   # nomen-sacra families
                extra.add(sk)
    return extra


def build(decisions: dict) -> dict:
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    wh = json.loads(WH.read_text(encoding="utf-8"))
    global_contest = page_contestation(scan)
    words = []
    for vn in sorted(scan["verses"], key=int):
        rec = scan["verses"][vn]
        scan_words = tokenize(rec["scan"])
        # WH line for the same verse; v19 WH continues past the folio break —
        # align only up to the attested extent (the split point 'ὅτε').
        wh_line = wh[vn]
        if vn == "19":
            idx = wh_line.find("ὅτε")
            if idx >= 0:
                wh_line = wh_line[: idx + len("ὅτε")]
        wh_words = tokenize(wh_line)
        hints = note_contested_words(rec.get("notes", "")) | global_contest

        # pairing: greedy char-similarity over the whole verse (order-
        # preserving), seeded by the difflib backbone so long equal runs
        # cost nothing. Char-similarity (not accent-stripped skeleton)
        # keeps ἐκ/ἐξ and ὁ/ὃν DISTINCT — an elided scan preposition must
        # surface as scan_only against its WH form, not silently pair.
        seed = {}
        seed_j = set()
        sm = difflib.SequenceMatcher(
            a=[skeleton(w) for w in scan_words],
            b=[skeleton(w) for w in wh_words], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    seed[i1 + k] = j1 + k
                    seed_j.add(j1 + k)
        free_i = [i for i in range(len(scan_words)) if i not in seed]
        free_j = [j for j in range(len(wh_words)) if j not in seed_j]
        pairs = dict(seed)
        used_j = set(seed_j)
        cands = sorted(
            ((char_sim(strip_word(scan_words[i]), strip_word(wh_words[j])), i, j)
             for i in free_i for j in free_j), reverse=True)
        used_i = set()
        for sim, i, j in cands:
            if sim < 0.75:
                break
            if i in used_i or j in used_j:
                continue
            used_i.add(i)
            used_j.add(j)
            pairs[i] = j

        for i, w in enumerate(scan_words):
            j = pairs.get(i)
            whw = wh_words[j] if j is not None else None
            key = f"v{vn}w{i+1}:{unicodedata.normalize('NFC', w)}"
            if whw is None:
                status = "scan_only"
            else:
                status = classify(w, whw)
            sk_scan = core(strip_word(w))
            sk_wh = core(strip_word(whw)) if whw else ""
            contested = sk_scan in hints or sk_wh in hints
            entry = {
                "key": key, "verse": int(vn), "index": i + 1,
                "scan": unicodedata.normalize("NFC", w),
                "wh": unicodedata.normalize("NFC", whw) if whw else None,
                "status": status,
                "contested_note": rec.get("notes", "") if contested else "",
            }
            dec = decisions.get(key)
            if dec:
                entry["decision"] = dec
            words.append(entry)
        # WH words no scan word paired to = candidate omissions in the scan
        for j, w in enumerate(wh_words):
            if j not in used_j:
                if not letters(w):   # bare "—" / "(" editorial tokens: noise
                    continue
                key = f"v{vn}Wh{j+1}:{unicodedata.normalize('NFC', w)}"
                entry = {
                    "key": key, "verse": int(vn), "index": -(j + 1),
                    "scan": None,
                    "wh": unicodedata.normalize("NFC", w),
                    "status": "wh_only",
                    "contested_note": (rec.get("notes", "")
                                       if core(strip_word(w)) in hints else ""),
                }
                dec = decisions.get(key)
                if dec:
                    entry["decision"] = dec
                words.append(entry)
    return {"_meta": {
        "generated_from": [SCAN.name, WH.name],
        "decisions_from": LEDGER.name,
        "note": "derived file — rebuild with tools/word_matrix.py; decisions "
                "live in corpus/john1_word_ledger.json and survive rebuilds",
    }, "words": words}


def load_ledger() -> dict:
    if LEDGER.exists():
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
        return {d["key"]: d for d in data.get("decisions", [])
                if "superseded_by" not in d}
    return {}


if __name__ == "__main__":
    m = build(load_ledger())
    MATRIX_OUT.write_text(json.dumps(m, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    from collections import Counter
    c = Counter(w["status"] for w in m["words"])
    dec = sum(1 for w in m["words"] if "decision" in w)
    print(f"wrote {MATRIX_OUT} — {len(m['words'])} words")
    for k in ("match", "casing", "elision", "variant", "scan_only", "wh_only"):
        print(f"  {k:10s} {c.get(k, 0)}")
    print(f"  contested-flagged {sum(1 for w in m['words'] if w['contested_note'])}")
    print(f"  with decision   {dec}")
