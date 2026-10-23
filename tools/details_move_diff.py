#!/usr/bin/env python3
"""Prove that /details/ carries v1's seven bands VERBATIM (stage 07, T1.6).

Stage 07 moved the Motivation, Approach, Contributions, Theory, Simulator,
Utility and Limitations bands off the main page and onto details/index.html.
The rule was "move, do not rewrite": markup, copy, alt text, captions, tables,
media slots, switch bars and markup comments all travel unchanged. This script
is the evidence.

For each band it extracts, from BOTH `git show <ref>:index.html` and the
working-tree details/index.html, the block that runs from the band's banner
comment (`<!-- ====...`) through its closing `</section>` — so the comments are
proven to have moved too, not just the markup. It then undoes the ONE
mechanical change the move allows (asset paths gained a `../`) and prints a
unified diff per band.

    python tools/details_move_diff.py                 # against v1.0-launch
    python tools/details_move_diff.py --ref main      # against another ref

Exit codes:
    0  every band is identical except for the ALLOWED edits listed below
    1  something else differs, or a band is missing / duplicated

ALLOWED, and nothing else (stage_07_v2_restructure.md T1.2): asset and script
paths; links that pointed at /demos/; the nav; the page head. Only the first
two can occur inside a band, and only one band contains a /demos/ link — the
Simulator card's `Try the demo lab →`, which becomes `See the simulator ↓` to
`#simulator`, together with the markup comment directly above it that
explained the old href. ALLOWED_EDITS pins that hunk exactly, so any other
difference — including a different rewording of that same link — fails.

Standard library only.
"""

from __future__ import annotations

import argparse
import difflib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BANDS = ["motivation", "approach", "contributions", "theory", "simulator",
         "utility", "limitations"]

# Lines that may appear ONLY on the v1 side (removed) and ONLY on the details
# side (added), per band. Compared after whitespace-stripping each line.
ALLOWED_EDITS = {
    "contributions": {
        "removed": [
            "<!-- href is the same relative path the nav pill and the closing band",
            "use; data-mars-config-href lets js/mars-nav.js keep it in step",
            "with MARS_CONFIG.demoLabUrl without ever leaving it empty. -->",
            '<a class="mars-card__link" href="demos/"',
            'data-mars-config-href="demoLabUrl">Try the demo lab &rarr;</a>',
        ],
        "added": [
            "<!-- STAGE 07 (v2, guide 0.2/0.4): /demos/ is unlinked from every",
            "public page until the playground ships, so this card no longer",
            'says "Try the demo lab" and no longer carries',
            'data-mars-config-href="demoLabUrl" — js/mars-nav.js would',
            "otherwise rewrite the href back to the demo lab at runtime. It",
            "points at the Simulator band on this page instead. -->",
            '<a class="mars-card__link" href="#simulator">See the simulator &darr;</a>',
        ],
    },
}

# The one mechanical rewrite: an attribute value that started `assets/` on `/`
# starts `../assets/` one directory down. Undone before diffing.
PATH_PREFIX = re.compile(
    r'((?:src|srcset|data-src|data-poster|href)=")\.\./(assets|js|css)/')


def band_blocks(source: str, label: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for bid in BANDS:
        hits = [m.start() for m in re.finditer(
            r'<section class="mars-band[^"]*" id="%s"' % bid, source)]
        if len(hits) != 1:
            raise SystemExit(f"{label}: expected exactly one <section "
                             f"id=\"{bid}\">, found {len(hits)}")
        start = hits[0]
        banner = source.rfind("<!-- =====", 0, start)
        gap = source[source.find("-->", banner) + 3:start]
        if banner == -1 or gap.strip():
            raise SystemExit(f"{label}: #{bid} has no banner comment directly "
                             f"above it")
        end = source.find("</section>", start) + len("</section>")
        out[bid] = source[banner:end]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ref", default="v1.0-launch",
                    help="git ref holding the v1 main page (default %(default)s)")
    args = ap.parse_args()

    v1 = subprocess.run(["git", "-C", str(REPO), "show",
                         f"{args.ref}:index.html"],
                        capture_output=True, text=True, check=True).stdout
    det_path = REPO / "details" / "index.html"
    det = det_path.read_text(encoding="utf-8")

    old = band_blocks(v1, f"{args.ref}:index.html")
    new = band_blocks(det, "details/index.html")

    rewritten = sum(len(PATH_PREFIX.findall(b)) for b in new.values())
    print(f"MaRS /details/ move check — {args.ref}:index.html vs "
          f"details/index.html")
    print(f"normalised {rewritten} path attribute(s) of the form "
          f"'../assets/' -> 'assets/'\n")

    bad = 0
    for bid in BANDS:
        a = old[bid].splitlines()
        b = PATH_PREFIX.sub(r"\1\2/", new[bid]).splitlines()
        diff = list(difflib.unified_diff(
            a, b, f"{args.ref}:index.html #{bid}",
            f"details/index.html #{bid} (paths normalised)", n=1, lineterm=""))
        removed = [l[1:].strip() for l in diff
                   if l.startswith("-") and not l.startswith("---")]
        added = [l[1:].strip() for l in diff
                 if l.startswith("+") and not l.startswith("+++")]
        allowed = ALLOWED_EDITS.get(bid, {"removed": [], "added": []})
        ok = removed == allowed["removed"] and added == allowed["added"]

        lines = len(a)
        if not diff:
            print(f"  [identical] #{bid:<14} {lines} lines")
            continue
        verdict = "ALLOWED T1.2 edit" if ok else "** UNEXPECTED **"
        print(f"  [{verdict}] #{bid:<14} {lines} lines, "
              f"{len(removed)} removed / {len(added)} added:")
        for l in diff:
            print("      " + l)
        if not ok:
            bad += 1

    print()
    if bad:
        print(f"FAIL — {bad} band(s) differ beyond the allowed T1.2 edits")
        return 1
    print("PASS — all seven bands are verbatim; the only difference is the "
          "Simulator card's demo-lab link (T1.2)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
