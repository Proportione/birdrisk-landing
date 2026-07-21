#!/usr/bin/env python3
"""BirdRisk copy doctrine check: the site INFORMS, it never ADVISES.

BirdRisk shows the pilot what the risk is. It never tells them whether, when or
where to fly — that is the pilot-in-command's call. This is not a style
preference: it is the line between an information product and an advisory one,
with the legal and positioning consequences that follow.

This check exists because a previous verification pass reported "clean" while
two advisory phrases were live in production. The grep it used tested a word
list that did not contain the words actually at fault ("wait", "re-time",
"calmer window"). A guard that does not test what it claims to test is worse
than no guard, so this one reports what it scanned.

Only *visible text* is scanned: <style> and <script> are stripped first, so
that CSS (`width: 50%`) and JS (`window.gtag`) cannot trigger or mask a hit.

Usage:  python3 tools/check-doctrine.py [file.html ...]     (default: *.html)
Exit 0 = clean, 1 = violations found.
"""

import re
import sys
from pathlib import Path

# (pattern, why it violates the doctrine)
FORBIDDEN = [
    (r"\bavoid\b",                  "tells the pilot what not to do"),
    (r"\bre-?route\b",              "prescribes an action"),
    (r"\bre-?time\b",               "prescribes an action (delay by another name)"),
    # Only the advisory sense. "the data may be delayed" is a correct factual
    # statement about the feed, not advice, and must not trip the guard.
    (r"\bdelay(ing)?\s+(your|the)\s+\w+", "prescribes an action"),
    (r"\bwait\b",                   "prescribes an action"),
    (r"\bdo\s?n[o']t\s+fly\b",      "a go/no-go instruction"),
    (r"\bshould\s+(you|fly|wait)",  "advisory mood"),
    (r"\byou\s+should\b",           "advisory mood"),
    (r"\bwe\s+recommend\b",         "advisory mood"),
    (r"\brecommend(s|ed|ation)?\b", "advisory mood"),
    (r"\bconsider\b",               "advisory mood"),
    (r"\bbest\s+time\s+to\s+fly\b", "guides the decision"),
    (r"\b(calm|calmer|safer|better|quieter)\s+(window|time|hour|slot)\b",
                                    "guides the pilot toward re-timing"),
    (r"\bfind\s+the\s+\w+\s+window\b", "guides the pilot toward re-timing"),
]

TAG = re.compile(r"<[^>]+>")
DROP = re.compile(r"<(style|script)\b.*?</\1>", re.S | re.I)


def visible_text(html: str) -> str:
    """Everything the reader actually sees — no CSS, no JS, no tags."""
    return TAG.sub(" ", DROP.sub(" ", html))


def check(path: Path):
    text = visible_text(path.read_text(encoding="utf-8"))
    hits = []
    for pattern, why in FORBIDDEN:
        for m in re.finditer(pattern, text, re.I):
            start, end = max(0, m.start() - 70), m.end() + 70
            context = " ".join(text[start:end].split())
            hits.append((m.group(0), why, context))
    return hits


def main(argv):
    targets = [Path(a) for a in argv[1:]] or sorted(Path(".").glob("*.html"))
    targets = [p for p in targets if p.is_file()]
    if not targets:
        print("doctrine: no HTML files to scan", file=sys.stderr)
        return 1

    total = 0
    for path in targets:
        hits = check(path)
        total += len(hits)
        status = f"{len(hits)} violation(s)" if hits else "clean"
        print(f"  {path}: {status}")
        for phrase, why, context in hits:
            print(f"    ✗ {phrase!r} — {why}")
            print(f"      …{context}…")

    print(f"\ndoctrine: scanned {len(targets)} file(s), "
          f"{len(FORBIDDEN)} patterns, {total} violation(s)")
    if total:
        print("\nThe site informs; it does not advise. Describe what the app "
              "SHOWS, not what the pilot should DO.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
