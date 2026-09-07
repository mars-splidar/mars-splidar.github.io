#!/usr/bin/env python3
"""Claim-hygiene and canonical-number audit for the MaRS project site.

Mechanises the non-negotiables in `WEBSITE_BUILD_STATUS.md` section 4 (items
1-5 and 11) as a grep-and-assert pass over every `.html` file in the repo. Its
job is to be boringly mechanical: it replaces "someone re-reads the whole page
carefully" with a command. Stage 06 runs it as a launch gate.

Standard library only, no dependencies.

    python tools/audit_claims.py            # audit the whole repo
    python tools/audit_claims.py --quiet    # failures only, no coverage report

Exit codes:
    0  every check passed
    1  at least one check failed (each failure printed as file:line)

EXPECTED STATE AFTER STAGE 01: exit 1, with the ONLY failures being the
`mars-todo` placeholders in the six stubbed content sections. Any other failure
at that point is a real bug.

--------------------------------------------------------------------------
Escape hatches a later stage may legitimately need to widen
--------------------------------------------------------------------------
* SANCTIONED_ROUNDINGS — rounded forms of canonical numbers that approved copy
  genuinely uses (e.g. the demo lab's "MaRS 1.01 s vs. gold standard 40.8 s").
  Add to it only for copy that has actually been approved, and say why.
* TITLE_CONTEXTS — strings containing the word "Simulator" that must not count
  as the "simulat" half of the 85 ns / simulation-grid conflation check. The
  paper's own title ends in "Simulator", so without this the check would fire
  on the page title every time.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ==========================================================================
# Pass 1 — forbidden patterns
# ==========================================================================

# (label, regex, non-negotiable reference, scope, regex flags)
#
#   scope "raw"  — matched against the file as written, comments included, so a
#                  forbidden phrase parked in an HTML comment is still caught.
#   scope "text" — matched against VISIBLE TEXT only (comments, <script>,
#                  <style> and all tags stripped). Anything that would
#                  otherwise fire on class names, ids or asset paths — the
#                  `mars-` prefix above all — must use this scope.
#
# The MaRS-casing rule is the reason `flags` exists: it is the one check that
# must be CASE-SENSITIVE. Run case-insensitively it matches every `mars-*`
# class name on the page.
FORBIDDEN: list[tuple[str, str, str, str, int]] = [
    # #1 — the LUT is tied to (t_r, n_b, sigma_t, t_d) and a bounded (S,B)
    # grid. Correct phrasing: "one table per sensor configuration, reused for
    # every pixel and depth."
    ("over-claimed LUT generality",
     r"any\s+scene\s*,?\s*any\s+depth", "#1", "text", re.I),
    ("over-claimed LUT generality",
     r"(one|a|single)\s+(lookup\s+)?table[^.]{0,40}any\s+(scene|depth)",
     "#1", "text", re.I),

    # #3 — MaRS MATCHES the gold standard. The accuracy claim is against
    # Poisson / Renewal / Zhang.
    ("claims MaRS beats the gold standard",
     r"(beats?|better\s+than|more\s+accurate\s+than|outperforms?|"
     r"surpass(es)?)\s+(the\s+)?gold[\s-]standard", "#3", "text", re.I),

    # #2 — the gold standard is CORRECT, merely unusable at scale. The whole
    # argument depends on respecting it.
    ("implies the gold standard is wrong",
     r"gold[\s-]standard\s+(simulator\s+)?is\s+(wrong|incorrect|inaccurate|"
     r"flawed)", "#2", "text", re.I),
    ("implies the gold standard is wrong",
     r"(wrong|incorrect|inaccurate|flawed)\s+gold[\s-]standard",
     "#2", "text", re.I),

    # #8 — delay invariance holds conditioned on fixed (S,B), not on scene
    # geometry.
    ("states delay invariance as scene geometry",
     r"moving\s+(an?\s+)?(object|target|surface)[^.]{0,40}"
     r"(only\s+)?shifts?\s+the\s+histogram", "#8", "text", re.I),

    # dead-link rule (PROJECT_BRIEF 7.7 made mechanical)
    ("dead link", r"href\s*=\s*[\"']#[\"']", "never link to nothing",
     "raw", re.I),

    # unfinished sections — expected to fail until stage 02
    ("unfinished section placeholder", r"mars-todo",
     "stage 02 removes these", "raw", re.I),

    # leftovers from the replaced placeholder page
    ("placeholder text survived", r"under\s+construction", "stage 01",
     "raw", re.I),
    ("placeholder title survived", r"High[\s-]Flux", "stage 01", "raw", re.I),
    ("placeholder author survived", r"Author\s+[23]\b", "stage 01",
     "raw", re.I),

    # #6 / conventions — MaRS is capital M, lowercase a, capital R, capital S.
    # CASE-SENSITIVE, visible text only.
    ("wrong MaRS casing", r"\b(MARS|Mars|MaRs)\b", "conventions", "text", 0),
]

# #4 — never conflate 85 ns (real hardware) with the 75 ns simulation grid.
# Implemented as: `85 ns` within CONFLATION_WINDOW characters of a word
# starting "simulat", excluding occurrences of "Simulator" that belong to the
# paper's own title (see TITLE_CONTEXTS).
CONFLATION_WINDOW = 200
TITLE_CONTEXTS = [
    "Single-Photon LiDAR Simulator",
    "Markov-Renewal Single-Photon LiDAR",
    "LiDAR Simulator",
]

# #5 — exactly one display equation on the whole public site. `.mars-eq` is the
# sanctioned display-equation container; stage 01 creates zero of them.
EQUATION_CONTAINER = "mars-eq"
EQUATION_MAX = 1

# ==========================================================================
# Pass 2 — canonical numbers (PROJECT_BRIEF.md section 3.4 / 3.5)
# ==========================================================================

CANONICAL = [
    # runtime
    "1.013", "0.071", "40.831", "8.045", "40×",
    "0.020", "0.144", "0.849",
    # LUT
    "108 GB", "105 MB", "1000×", "100.4 MB",
    # count-distribution accuracy
    "24.208", "18.821", "0.409", "0.013", "30×",
    "7966.130", "207.565", "2.337", "0.309",
    # covariance
    "125.91", "10.00", "12×",
    # dead time — both, and they must stay distinct (#4)
    "85 ns", "75 ns",
    # real-hardware validation
    "0.0651", "0.0601", "7.5 MHz",
    # downstream transfer
    "+17 dB", "1.654", "0.074", "36.49", "7.02", "24.03", "24.25",
]

# Rounded forms that APPROVED copy genuinely uses. Each needs a reason.
SANCTIONED_ROUNDINGS = {
    # MARS_WEBSITE_BUILD_GUIDE.md 5.4 / stage_01_foundation.md 3.6 specify this
    # exact wording for the demo lab's race panel.
    "1.01": "guide 5.4 — the race panel: 'MaRS 1.01 s vs. gold standard 40.8 s'",
    "40.8": "guide 5.4 — the race panel, same line",
    # PROJECT_BRIEF 3.4 gives the TV distances to four places; the guide's
    # Theory Results tab copy rounds them to three.
    "0.065": "guide 4.7 — Theory Results 'Real validation' tab copy",
    "0.060": "guide 4.7 — Theory Results 'Real validation' tab copy",
    # PROJECT_BRIEF 3.5's own headline sentence rounds the depth RMSE pair.
    "1.65": "PROJECT_BRIEF 3.5 headline: 'depth RMSE 1.65 -> 0.07 m'",
    "0.07": "PROJECT_BRIEF 3.5 headline, same sentence",
    # The four-gains numeral is spelled "+17dB" (guide 4.3); prose uses "+17 dB".
    "17": "guide 4.3 — the four-gains numeral '+17dB'",
    # Teaser single-cube timings, PROJECT_BRIEF 3.4.
    "0.2": "PROJECT_BRIEF 3.4 — teaser timings (Poisson 0.2 s)",
    "16.1": "PROJECT_BRIEF 3.4 — teaser timings (gold standard 16.1 s)",
    "0.3": "PROJECT_BRIEF 3.4 — teaser timings (MaRS 0.3 s)",
}

# A literal counts as a NEAR MISS of a canonical value — probably a typo, or a
# silent re-rounding of a number that survived review — when any of these hold:
#
#   (a) it lands within NEAR_MISS_TOL relative distance of the canonical value
#       while being written differently ("40.9" for 40.831);
#   (b) it has the same length and differs in exactly ONE character
#       ("0.014" for 0.013 — a last-digit slip, which for small values is far
#       outside the relative tolerance, hence this rule);
#   (c) it is a truncation of the canonical value ("24.20" for 24.208).
#
# Rules (b) and (c) apply only to canonical values carrying at least
# MIN_FRACTIONAL_DIGITS digits after the decimal point. Applying them to bare
# multipliers (12x, 30x, 40x, 1000x) or to one-decimal values would flag
# ordinary numbers like "20" as one-character slips of "30".
NEAR_MISS_TOL = 0.02
MIN_FRACTIONAL_DIGITS = 2

# Numbers that are structural rather than claim-bearing, and must never be
# treated as near-misses of a canonical value.
STRUCTURAL_NUMBERS = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "16", "9", "1024", "1280", "720", "128", "256", "1200", "630",
    "2026", "2133032", "2030570", "1.5", "1.0", "2.0", "100",
}

# The four gain numerals, in their settled order (#11).
GAIN_ORDER = ["30×", "1000×", "40×", "+17dB"]
GAIN_ALIASES = {"+17dB": ["+17dB", "+17 dB"]}


# ==========================================================================
# Helpers
# ==========================================================================

TAG_RE = re.compile(r"<[^>]*>")
SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1\s*>", re.S | re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
NUM_RE = re.compile(r"[+-]?\d+(?:\.\d+)?")


def html_files() -> list[Path]:
    return sorted(
        p for p in REPO.rglob("*.html")
        if ".git" not in p.parts and "node_modules" not in p.parts
    )


def visible_text(source: str) -> str:
    """Strip comments, <script>/<style> bodies and tags.

    Comments go first so that a commented-out claim is not audited — but note
    that pass 1 runs over the RAW source, deliberately, so a forbidden phrase
    parked in a comment is still caught.
    """
    s = COMMENT_RE.sub(" ", source)
    s = SCRIPT_STYLE_RE.sub(" ", s)
    s = TAG_RE.sub(" ", s)
    return html.unescape(re.sub(r"\s+", " ", s))


def line_of(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


class Report:
    def __init__(self) -> None:
        self.failures: list[tuple[str, str, str]] = []   # (where, label, detail)
        self.info: list[str] = []

    def fail(self, where: str, label: str, detail: str) -> None:
        self.failures.append((where, label, detail))


# ==========================================================================
# Checks
# ==========================================================================

def check_forbidden(source: str, text: str, rel: str, rep: Report) -> None:
    for label, pattern, ref, scope, flags in FORBIDDEN:
        haystack = source if scope == "raw" else text
        for m in re.finditer(pattern, haystack, flags):
            snippet = re.sub(r"\s+", " ", m.group(0))[:80]
            if scope == "raw":
                where = f"{rel}:{line_of(source, m.start())}"
            else:
                # visible text has no line numbers; recover one by locating
                # the matched snippet back in the raw source.
                at = source.find(m.group(0))
                where = f"{rel}:{line_of(source, at)}" if at != -1 else rel
            rep.fail(where, f"{label} [{ref}]", snippet)


def check_conflation(text: str, rel: str, rep: Report) -> None:
    """#4 — 85 ns (hardware) must never sit next to simulation-grid language."""

    # blank out the title occurrences of "Simulator" so they cannot pair up
    scrubbed = text
    for ctx in TITLE_CONTEXTS:
        scrubbed = scrubbed.replace(ctx, " " * len(ctx))

    for m in re.finditer(r"85\s*ns", scrubbed, re.I):
        lo = max(0, m.start() - CONFLATION_WINDOW)
        hi = min(len(scrubbed), m.end() + CONFLATION_WINDOW)
        window = scrubbed[lo:hi]
        sim = re.search(r"simulat\w*", window, re.I)
        if sim:
            flat = re.sub(r"\s+", " ", window)[:160]
            rep.fail(rel, "85 ns near simulation language [#4]",
                     f"...{flat}...")


def check_equation_count(files: list[Path], rep: Report) -> None:
    """#5 — exactly one display equation across the whole site."""
    hits: list[str] = []
    for path in files:
        source = path.read_text(encoding="utf-8", errors="replace")
        body = COMMENT_RE.sub(" ", source)
        rel = str(path.relative_to(REPO))
        for m in re.finditer(
                r'class\s*=\s*["\'][^"\']*\b' + EQUATION_CONTAINER + r'\b',
                body):
            hits.append(f"{rel}:{line_of(body, m.start())}")
    if len(hits) > EQUATION_MAX:
        rep.fail(", ".join(hits),
                 f"more than one .{EQUATION_CONTAINER} container [#5]",
                 f"found {len(hits)}, allowed {EQUATION_MAX}")
    rep.info.append(
        f"display equations (.{EQUATION_CONTAINER}): {len(hits)} "
        f"(allowed {EQUATION_MAX})"
        + (" -> " + ", ".join(hits) if hits else ""))


def _one_char_apart(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    diffs = sum(1 for x, y in zip(a, b) if x != y)
    return diffs == 1


def _is_truncation(lit: str, canon_num: str) -> bool:
    return (lit != canon_num
            and canon_num.startswith(lit)
            and "." in lit
            and len(lit) >= 4)


def near_miss_of(lit: str, canon_num: str) -> str | None:
    """Return the rule letter if `lit` is a near miss of `canon_num`."""
    if lit == canon_num:
        return None
    try:
        val, cval = float(lit), float(canon_num)
    except ValueError:
        return None
    if cval == 0 or val == 0:
        return None

    if abs(val - cval) / abs(cval) < NEAR_MISS_TOL:
        return "a"

    frac = canon_num.split(".", 1)[1] if "." in canon_num else ""
    precise = len(frac) >= MIN_FRACTIONAL_DIGITS
    if not precise:
        return None
    if _one_char_apart(lit, canon_num):
        return "b"
    if _is_truncation(lit, canon_num):
        return "c"
    return None


def check_numbers(text: str, rel: str, rep: Report,
                  found: dict[str, list[str]]) -> None:
    for canon in CANONICAL:
        if canon in text:
            found.setdefault(canon, []).append(rel)

    # numeric core of each canonical string -> the canonical string itself
    canon_nums: dict[str, str] = {}
    for canon in CANONICAL:
        m = NUM_RE.search(canon)
        if m:
            canon_nums[m.group(0)] = canon

    for m in NUM_RE.finditer(text):
        lit = m.group(0)
        if lit in STRUCTURAL_NUMBERS or lit in canon_nums \
                or lit in SANCTIONED_ROUNDINGS:
            continue
        for cnum, canon in canon_nums.items():
            rule = near_miss_of(lit, cnum)
            if not rule:
                continue
            ctx = re.sub(r"\s+", " ",
                         text[max(0, m.start() - 45):m.end() + 45])
            rep.fail(rel,
                     f"number {lit} is a near-miss of canonical "
                     f"{canon} [PROJECT_BRIEF 3.4, rule {rule}]",
                     f"...{ctx}... "
                     f"(if this rounding is approved copy, add it to "
                     f"SANCTIONED_ROUNDINGS with a reason)")
            break


def check_gain_order(rep: Report) -> None:
    """#11 — accuracy -> table size -> speed -> downstream, in that order."""
    index = REPO / "index.html"
    if not index.exists():
        rep.fail("index.html", "missing [#11]", "cannot check gain order")
        return
    text = visible_text(index.read_text(encoding="utf-8", errors="replace"))

    positions = []
    for gain in GAIN_ORDER:
        best = None
        for alias in GAIN_ALIASES.get(gain, [gain]):
            at = text.find(alias)
            if at != -1 and (best is None or at < best):
                best = at
        if best is None:
            rep.fail("index.html", f"gain numeral {gain} missing [#11]",
                     "the four gains are a settled decision, not a layout choice")
            return
        positions.append((gain, best))

    order = [g for g, _ in sorted(positions, key=lambda t: t[1])]
    if order != GAIN_ORDER:
        rep.fail("index.html", "four gains out of order [#11]",
                 f"found {' -> '.join(order)}, "
                 f"required {' -> '.join(GAIN_ORDER)}")
    else:
        rep.info.append(
            "four gains in the settled order: " + " -> ".join(GAIN_ORDER))


# ==========================================================================
# Main
# ==========================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true",
                    help="print failures only, skip the coverage report")
    args = ap.parse_args()

    files = html_files()
    if not files:
        print("ERROR: no .html files found under " + str(REPO), file=sys.stderr)
        return 1

    rep = Report()
    found: dict[str, list[str]] = {}

    print(f"MaRS claim audit — {len(files)} HTML file(s) under {REPO}\n")
    for path in files:
        rel = str(path.relative_to(REPO))
        source = path.read_text(encoding="utf-8", errors="replace")
        text = visible_text(source)
        check_forbidden(source, text, rel, rep)
        check_conflation(text, rel, rep)
        check_numbers(text, rel, rep, found)

    check_equation_count(files, rep)
    check_gain_order(rep)

    # ---- pass 2 coverage report -----------------------------------------
    if not args.quiet:
        print("PASS 2 — canonical-number coverage "
              "(informational; absence is not a failure)")
        for canon in CANONICAL:
            where = found.get(canon)
            mark = "found" if where else "  -  "
            loc = ", ".join(sorted(set(where))) if where else ""
            print(f"  [{mark}] {canon:<12} {loc}")
        print()
        for line in rep.info:
            print("  " + line)
        print()

    # ---- verdict ---------------------------------------------------------
    if not rep.failures:
        print("PASS — no claim-hygiene or canonical-number failures.")
        return 0

    print(f"FAIL — {len(rep.failures)} finding(s):\n")
    by_label: dict[str, int] = {}
    for where, label, detail in rep.failures:
        by_label[label] = by_label.get(label, 0) + 1
        print(f"  {where}")
        print(f"      {label}")
        print(f"      {detail}")
    print("\nfailure classes:")
    for label, n in sorted(by_label.items(), key=lambda t: -t[1]):
        print(f"  {n:>3}  {label}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
