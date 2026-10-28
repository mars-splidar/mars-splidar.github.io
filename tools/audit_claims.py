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

EXPECTED STATE AFTER STAGE 1.5: exit 0. The `mars-todo` placeholders that made
stage 01 exit 1 are gone — the stub gate removed them from the markup rather
than hiding them — so this is the first stage at which the audit passes clean.
Any failure from here on is a real bug.

STAGE 07 (v2): the site is now TWO public pages, `/` and `/details/`. Every
pass already ran over every .html file; stage 07 adds PUBLIC_PAGES (both must
exist), zero links to /demos/ on either, the 85 ns / 75 ns rule made
section-aware on /details/, and scopes the gain-order check to the gains
strip. "Exactly one .mars-eq" stays site-wide, across both pages.

STAGE 10b: the webfonts are self-hosted, so check_third_party() now fails on
any resource that a page or the stylesheet would FETCH from another host:
<link rel=stylesheet|preload|preconnect|dns-prefetch|modulepreload|icon>,
<script src>, <img>/<source>/<video>/<audio>/<track>/<iframe> src, srcset,
poster, data-src*/data-poster, and CSS url()/@import. Links a reader clicks
(<a href>), the canonical URL, and the absolute og:/twitter: image URLs (they
are this site's own host, read by crawlers) are not fetches and are allowed.

Pass 3 (contrast) was added in stage 1.5 to stop the GOLD/AGED contrast fix
from silently regressing. It is the only pass that reads CSS rather than HTML.

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
* SURFACES / CONTRAST_EXEMPT — pass 3 (below) resolves every `color:` rule in
  css/mars.css against the surface it is painted on. A new surface, or a rule
  WCAG genuinely exempts, is declared there with a reason.
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
    # NARROWED IN STAGE 02. The placeholder page's title was "Markov-Renewal
    # Simulator for High-Flux Single-Photon LiDAR", and `High[\s-]Flux` alone
    # also matches the ordinary phrase "high flux" — which is standard
    # terminology in this field and appears three times in stage 02's Theory
    # copy ("at low and at high flux"). Requiring the rest of the placeholder
    # title keeps the check exact: it still matches the placeholder string in
    # every spelling the old pattern did, and no longer matches prose.
    # Self-tested against the original placeholder title; see stage 02's
    # handoff in WEBSITE_BUILD_STATUS.md section 5.
    ("placeholder title survived",
     r"High[\s-]Flux\s+Single[\s-]Photon", "stage 01", "raw", re.I),
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
    # COMPLETED IN STAGE 02 — these are EXACT values from PROJECT_BRIEF, not
    # roundings, and belong in CANONICAL rather than in SANCTIONED_ROUNDINGS.
    # The list previously carried only the Poisson and MaRS rows of the
    # section 3.5 transfer table plus its headline; stage 02 renders the whole
    # table, so the Renewal and Zhang et al. rows and both val columns are
    # needed too. Without them the auditor flags real canonical numbers as
    # near-misses of each other: 29.72 of "30x", 12.12 of "12x", 0.072 of
    # 0.071, 0.054 of 0.074 and 0.053 of 0.013.
    # section 3.5, the rest of the val->test table (SBR 0.6):
    "0.072", "29.72", "12.12", "0.054", "0.096", "22.74", "22.54",
    "0.053", "0.082",
    # section 3.4, count-distribution mean / variance difference:
    "0.269", "1.588", "0.282", "64.558",
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

# Numbers that are NOT claims and NOT roundings, but happen to sit within the
# near-miss tolerance of a canonical value. Each needs a reason. Kept apart
# from SANCTIONED_ROUNDINGS on purpose: these are not re-written canonical
# numbers, and listing them there would misdescribe them. (Stage 09.)
NON_CLAIM_NUMBERS = {
    "64": "the Efficiency schematic's grid size, '3 realizations × 64 pixels' "
          "(8 x 8 cells, stage v2.2-B). A count of drawn cells, not a "
          "measurement; within 2% of the Zhang et al. variance difference "
          "64.558 only by coincidence",
    "8.2": "Demo 2's operating point, S = B = 8.2 (grid index 8 of the stored "
           "count-distribution results; video/data.py::count_distributions). "
           "A coordinate, not a measurement; 1.9% from the gold standard's "
           "8.045 s runtime spread only by coincidence",
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
# Pass 3 — contrast (WEBSITE_BUILD_STATUS.md 3.6, added stage 1.5)
# ==========================================================================
#
# Stage 01 measured that the guide asked for two things that cannot both hold:
# "contrast >= 4.5:1" and "gold stat numerals". GOLD on MINT is 1.73:1, which
# fails even the 3:1 large-text bar. The author's resolution was to make GOLD
# fill-only and derive --aged-text for gold TEXT on mint. This pass is what
# stops that fix from quietly eroding as later stages add copy.
#
# It does two things:
#
#   3a. HARD RULE — --gold (or its literal #CFB991) must never appear as the
#       value of a `color:` declaration. Gold is a fill: background, pill, bar,
#       underline, border. No exceptions, no size threshold. Gold used as TEXT
#       on an ink surface is legitimate at 9.36:1, but it has its own token
#       (--ink-accent) precisely so that this rule can stay absolute.
#
#   3b. Every `color:` rule in css/mars.css is resolved to a real hex, paired
#       with the surface its selector is painted on, and checked at 4.5:1.
#
# 3b is the part that needs maintaining. There is no way to know from CSS text
# alone what background a selector will actually sit on, so SURFACES below maps
# selector patterns to surfaces, FIRST MATCH WINS, with PAPER as the default.
# If a later stage introduces a new painted surface, add it here — an unmapped
# selector is silently assumed to be on paper, which is the safe assumption for
# this site but not a guarantee.

CSS_FILE = "css/mars.css"
CONTRAST_MIN = 4.5

# HOW A RULE'S BACKGROUND IS DECIDED, in order:
#
#   1. If the rule declares its own `background` / `background-color` and that
#      resolves to a hex, that is the surface. This is exact, needs no table,
#      and covers most of the stylesheet — the skip link, the badge, the
#      buttons, the plates.
#   2. Otherwise the selector is matched against SURFACES below, first match
#      wins. These are the rules that inherit a background from an ancestor,
#      which CSS text alone cannot tell you about.
#   3. Otherwise PAPER, the page's default ground.
#
# Patterns are deliberately prefix-shaped rather than \b-anchored: BEM class
# names like `.mars-nav__brand` continue with an underscore, which is a word
# character, so \b after `.mars-nav` would never match.
SURFACES: list[tuple[str, str, str]] = [
    # --- ink surfaces: the nav strip, the closing band, the lab sidebar ---
    (r"\.mars-code",                 "#0d1113", "code block"),
    (r"\.mars-nav",                  "--ink",   "nav strip"),
    (r"\.mars-closing",              "--ink",   "closing band"),
    (r"\.mars-lab__(sidebar|nav|item|tag)", "--ink", "demo lab sidebar"),
    (r"\.mars-band\.is-ink",         "--ink",   "ink band"),
    # --- mint surfaces: see the MINT SURFACES block in css/mars.css ---
    (r"\.mars-media__(frame|placeholder)", "--mint", "media slot frame"),
    (r"#playground-root",            "--mint",  "playground placeholder"),
    (r"\.mars-lab__caveat",          "--mint",  "demo lab caveat"),
    (r"\.mars-card",                 "--mint",  "contribution card"),
    (r"\.mars-eq",                   "--mint",  "display equation"),
    (r"\.mars-table thead",          "--mint",  "table header"),
    (r"\.is-mint",                   "--mint",  "mint band"),
    # --- gold-wash hover states, which repaint the ground under the label ---
    (r"\.mars-(btn|switch__pill)[^,]*:hover", "--gold-soft", "gold-wash hover"),
    # --- v2.2-C: the Downstream chips sit on the IMAGES, as INK at 82 %
    # (rgba(20, 24, 26, .82)). The worst case is a white image pixel under
    # the chip, which composites to #3e4243; text is checked against that.
    (r"\.mars-compare__chip",        "#3e4243", "image chip (INK 82 % over white)"),
    # --- the skip link paints itself AGED but only in the :focus rule ---
    (r"\.mars-skip",                 "--aged",  "skip link"),
]
DEFAULT_SURFACE = ("--paper", "paper band (default)")

# Surfaces that count as MINT for the purpose of --aged-fg. A rule painted on
# one of these resolves --aged-fg to --aged-text rather than to --aged, exactly
# as the cascade does in the browser. The override VALUES are read out of the
# stylesheet rather than hard-coded here, so the two cannot drift apart.
MINT_SURFACE_HEXES = {"#ecf6ef", "#e2eee6"}

# Rules WCAG genuinely exempts, or that are not text. Each needs a reason.
# Keyed by the exact selector text as it appears in css/mars.css.
CONTRAST_EXEMPT = {
    ".mars-btn.is-soon":
        "WCAG 1.4.3 exempts inactive UI components. These are the `· soon` "
        "pills for URLs that do not exist yet — rendered as <span>, "
        "aria-disabled, not focusable, nothing to activate.",
    ".mars-btn.is-soon:hover": "same element as .mars-btn.is-soon",
    ".mars-btn__soon":
        "the `· soon` suffix inside an inactive UI component; same exemption",
    ".mars-lab__status.is-soon":
        "the `soon` badge on the unbuilt demo panels — all FOUR of them as of "
        "stage 06, since stage 03 is deferred and the dead-time playground "
        "ships unbuilt too; same exemption",
}


def _srgb_lin(channel: int) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_colour: str) -> float:
    h = hex_colour.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (0.2126 * _srgb_lin(r) + 0.7152 * _srgb_lin(g)
            + 0.0722 * _srgb_lin(b))


def contrast_ratio(fg: str, bg: str) -> float:
    a, b = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


ROOT_TOKEN_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")
COLOR_DECL_RE = re.compile(r"(?<![-\w])color\s*:\s*([^;{}]+);")
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
NAMED = {"white": "#ffffff", "black": "#000000", "transparent": None,
         "inherit": None, "currentcolor": None, "initial": None,
         "unset": None, "revert": None}


def read_tokens(css: str) -> dict[str, str]:
    """Resolve the :root custom properties down to concrete hex values.

    Resolution is iterative because tokens are allowed to reference each other
    — --aged-fg is literally `var(--aged)`, which is the whole point of it.
    """
    m = re.search(r":root\s*\{(.*?)\}", css, re.S)
    if not m:
        return {}
    raw = {k: v.strip() for k, v in ROOT_TOKEN_RE.findall(m.group(1))}
    resolved: dict[str, str] = {}
    for _ in range(8):
        changed = False
        for key, val in raw.items():
            if key in resolved:
                continue
            hexes = HEX_RE.findall(val)
            if hexes:
                resolved[key] = hexes[0]
                changed = True
                continue
            ref = re.search(r"var\(\s*(--[a-z0-9-]+)", val)
            if ref and ref.group(1) in resolved:
                resolved[key] = resolved[ref.group(1)]
                changed = True
        if not changed:
            break
    return resolved


def resolve_colour(value: str, tokens: dict[str, str]) -> str | None:
    """Turn a declaration value into a hex, or None if it is not a colour."""
    value = value.strip().lower()
    if value in NAMED:
        return NAMED[value]
    hexes = HEX_RE.findall(value)
    if hexes:
        return hexes[0]
    ref = re.search(r"var\(\s*(--[a-z0-9-]+)", value)
    if ref:
        return tokens.get(ref.group(1))
    return None


BACKGROUND_DECL_RE = re.compile(
    r"(?<![-\w])background(?:-color)?\s*:\s*([^;{}]+);")


def read_surface_overrides(css: str) -> dict[str, str]:
    """Custom properties re-declared OUTSIDE :root — i.e. per-surface.

    css/mars.css re-points --aged-fg to --aged-text on every mint surface, so
    that gold TEXT darkens automatically wherever the ground is mint. The
    browser resolves that through the cascade; this reads the same declaration
    so the audit sees the same colour the visitor does.
    """
    out: dict[str, str] = {}
    for selector, body, _ in iter_rules(css):
        if selector == ":root":
            continue
        for key, value in ROOT_TOKEN_RE.findall(body):
            out[key] = value.strip()
    return out


def surface_for(selector: str, body: str,
                tokens: dict[str, str]) -> tuple[str, str] | None:
    """The background this rule's text sits on, or None if it is not pinned.

    None is the important return value. A selector like `.mars-eyebrow` is
    used on PAPER bands and MINT bands alike, so there is no single answer —
    and assuming paper is exactly how a 4.23:1 gold-on-mint eyebrow would slip
    back in unnoticed. The caller checks unpinned rules against BOTH grounds.
    """
    for decl in BACKGROUND_DECL_RE.findall(body):
        own = resolve_colour(decl, tokens)
        if own:
            return own, "its own background"
    for pattern, surface, label in SURFACES:
        if re.search(pattern, selector):
            hexed = tokens.get(surface, surface)
            if hexed and hexed.startswith("#"):
                return hexed, label
    return None


def iter_rules(css: str):
    """Yield (selector, body, line) for every top-level-ish rule.

    Comments are stripped first — a `color: var(--gold)` written inside a
    comment is documentation, not a declaration, and pass 3a would otherwise
    fire on this file's own explanation of the rule.
    """
    stripped = CSS_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), css)
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", stripped):
        selector = re.sub(r"\s+", " ", m.group(1)).strip()
        if not selector or selector.startswith("@"):
            continue
        yield selector, m.group(2), stripped.count("\n", 0, m.start(2)) + 1


def check_contrast(rep: Report) -> None:
    path = REPO / CSS_FILE
    if not path.exists():
        rep.fail(CSS_FILE, "stylesheet missing [3.6]",
                 "the contrast pass has nothing to check")
        return
    css = path.read_text(encoding="utf-8", errors="replace")
    tokens = read_tokens(css)
    overrides = read_surface_overrides(css)

    if "--aged-text" not in tokens:
        rep.fail(CSS_FILE, "--aged-text token missing [3.6]",
                 "the derived gold-text-on-mint token is required")
    elif tokens["--aged-text"].lower() != "#806438":
        rep.fail(CSS_FILE, "--aged-text has the wrong value [3.6]",
                 f"found {tokens['--aged-text']}, required #806438")

    # The mint variant of the token table: same as `tokens`, except that any
    # custom property the stylesheet re-declares on a mint surface takes its
    # mint value. Today that is exactly --aged-fg -> --aged-text.
    mint_tokens = dict(tokens)
    for key, value in overrides.items():
        resolved = resolve_colour(value, tokens)
        if resolved:
            mint_tokens[key] = resolved

    checked = 0
    exempted = 0
    worst: tuple[float, str] | None = None

    for selector, body, line in iter_rules(css):
        if selector == ":root":
            continue
        for decl in COLOR_DECL_RE.findall(body):
            value = decl.strip()

            # ---- 3a: gold is never a text colour ----
            if re.search(r"--gold(?![\w-])", value) or "#cfb991" in value.lower():
                rep.fail(f"{CSS_FILE}:{line}",
                         "--gold used as a text colour [3.6, hard rule]",
                         f"{selector} {{ color: {value} }} — gold is FILL "
                         f"ONLY. Gold text on ink uses --ink-accent.")
                continue

            if any(selector == k or k in [t.strip()
                                          for t in selector.split(",")]
                   for k in CONTRAST_EXEMPT):
                exempted += 1
                continue

            pinned = surface_for(selector, body, tokens)
            if pinned is not None:
                grounds = [pinned]
            else:
                # Not pinned to one surface: this rule can land on either of
                # the two content grounds, so it has to clear BOTH.
                grounds = [
                    (tokens.get("--paper", "#FAFBFA"), "paper band"),
                    (tokens.get("--mint", "#ECF6EF"), "mint band"),
                ]

            for bg, surface_label in grounds:
                table = (mint_tokens if bg.lower() in MINT_SURFACE_HEXES
                         else tokens)
                fg = resolve_colour(value, table)
                if fg is None:
                    continue

                ratio = contrast_ratio(fg, bg)
                checked += 1
                if worst is None or ratio < worst[0]:
                    worst = (ratio, f"{selector} on {surface_label}")
                if ratio < CONTRAST_MIN:
                    rep.fail(
                        f"{CSS_FILE}:{line}",
                        f"contrast {ratio:.2f}:1 below {CONTRAST_MIN}:1 [3.6]",
                        f"{selector} — {fg} on {bg} ({surface_label}). "
                        f"Either darken the text, use var(--aged-fg) so the "
                        f"surface picks the right gold, pin the selector in "
                        f"SURFACES, or declare the exemption in "
                        f"CONTRAST_EXEMPT with a reason.")

    rep.info.append(
        f"contrast: {checked} in-use text/background pair(s) checked, all "
        f">= {CONTRAST_MIN}:1"
        + (f" (worst {worst[0]:.2f}:1 — {worst[1]})" if worst else "")
        + f"; {exempted} WCAG-exempt rule(s) skipped")


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
                or lit in SANCTIONED_ROUNDINGS or lit in NON_CLAIM_NUMBERS:
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


# ==========================================================================
# v2 checks — added stage 07, when the site became two public pages
# ==========================================================================

# The public pages every gate must cover. /demos/ is NOT public in v2: it stays
# at its URL but nothing links to it (guide 0.2), so it is audited for claims
# like any other file but is not held to the rules below.
PUBLIC_PAGES = ["index.html", "details/index.html"]

# guide 0.2 / decision P2: zero links to /demos/ from a public page until the
# playground ships. Checked on `href` ATTRIBUTE VALUES (comments stripped), so
# a markup comment explaining the rule does not trip it, plus the
# `data-mars-config-href="demoLabUrl"` hook, which js/mars-nav.js would turn
# into a demo-lab link at runtime whatever the hand-written href says.
DEMOS_HREF = re.compile(r'\bhref\s*=\s*["\']([^"\']*demos[^"\']*)["\']', re.I)
DEMOS_CONFIG = re.compile(r'data-mars-config-href\s*=\s*["\']demoLabUrl["\']')


def check_public_pages(rep: Report) -> None:
    for page in PUBLIC_PAGES:
        path = REPO / page
        if not path.exists():
            rep.fail(page, "public page missing [stage 07]",
                     "every gate must cover both / and /details/")
            continue
        body = COMMENT_RE.sub(" ", path.read_text(encoding="utf-8",
                                                  errors="replace"))
        hits = [m.group(1) for m in DEMOS_HREF.finditer(body)]
        hits += ["data-mars-config-href=demoLabUrl"
                 for _ in DEMOS_CONFIG.finditer(body)]
        for h in hits:
            rep.fail(page, "link to /demos/ on a public page [guide 0.2]", h)
        rep.info.append(f"links to /demos/ on {page}: {len(hits)}")


# stage 10b: zero third-party requests. The only allowed absolute host is the
# site's own (og:/twitter:/canonical/JSON-LD URLs are written absolute).
OWN_HOST = "mars-splidar.github.io"
FETCH_ATTR = re.compile(
    r'<(link)\b[^>]*\brel\s*=\s*["\']([^"\']*)["\'][^>]*\bhref\s*=\s*["\']([^"\']+)["\']'
    r'|<(link)\b[^>]*\bhref\s*=\s*["\']([^"\']+)["\'][^>]*\brel\s*=\s*["\']([^"\']*)["\']'
    r'|<(script|img|source|video|audio|track|iframe|embed)\b[^>]*?\b(src|srcset|poster|data-src[\w-]*|data-poster)\s*=\s*["\']([^"\']+)["\']',
    re.I)
FETCH_RELS = {"stylesheet", "preload", "preconnect", "dns-prefetch",
              "modulepreload", "icon", "prefetch"}
CSS_URL = re.compile(r'(?:url\(\s*["\']?|@import\s+["\'])(https?:)?//([^/"\')\s]+)', re.I)


def _foreign(url: str) -> str | None:
    m = re.match(r"\s*(?:https?:)?//([^/\s]+)", url)
    return m.group(1) if m and m.group(1).lower() != OWN_HOST else None


def check_third_party(files: list[Path], rep: Report) -> None:
    total = 0
    for path in files:
        rel = str(path.relative_to(REPO))
        body = COMMENT_RE.sub(" ", path.read_text(encoding="utf-8", errors="replace"))
        for m in FETCH_ATTR.finditer(body):
            if m.group(1) or m.group(4):
                rels = (m.group(2) if m.group(1) else m.group(6)).lower().split()
                url = m.group(3) if m.group(1) else m.group(5)
                if not FETCH_RELS & set(rels):
                    continue
                urls = [url]
            else:
                urls = [u.strip().split(" ")[0] for u in m.group(9).split(",")]
            for u in urls:
                host = _foreign(u)
                if host:
                    total += 1
                    rep.fail(rel, "third-party request [stage 10b]", f"{host}: {u[:90]}")
    css = (REPO / CSS_FILE).read_text(encoding="utf-8", errors="replace") if (REPO / CSS_FILE).exists() else ""
    for m in CSS_URL.finditer(CSS_COMMENT_RE.sub(" ", css)):
        if m.group(2).lower() != OWN_HOST:
            total += 1
            rep.fail(CSS_FILE, "third-party request in CSS [stage 10b]", m.group(2))
    rep.info.append(f"third-party fetches (HTML + CSS): {total}")


def check_dead_time_sections(rep: Report) -> None:
    """#4, made structural on /details/: 85 ns (hardware) and 75 ns
    (simulation grid) must not share a band. The proximity window in
    check_conflation() is the character-level half of the same rule."""
    page = "details/index.html"
    path = REPO / page
    if not path.exists():
        return
    source = COMMENT_RE.sub(" ", path.read_text(encoding="utf-8",
                                                errors="replace"))
    where: dict[str, list[str]] = {"85 ns": [], "75 ns": []}
    for sec in re.finditer(r'<section\b[^>]*\bid="([^"]+)"(.*?)</section>',
                           source, re.S):
        text = visible_text(sec.group(2))
        for k in where:
            if re.search(k.replace(" ", r"\s*"), text):
                where[k].append(sec.group(1))
    shared = set(where["85 ns"]) & set(where["75 ns"])
    if shared:
        rep.fail(page, "85 ns and 75 ns in the same band [#4]",
                 ", ".join(sorted(shared)))
    rep.info.append(f"/details/ dead-time placement: 85 ns in "
                    f"{where['85 ns'] or 'nowhere'}, 75 ns in "
                    f"{where['75 ns'] or 'nowhere'} (must never share a band)")


# v2.2-B — THE EFFICIENCY MODULE. Its note is the one place on `/` that states
# the table's size and the delay shift, so it must carry, in EVERY schematic
# (one SVG per breakpoint, only one shown), PROJECT_BRIEF 3.4's two LUT sizes,
# #1's sanctioned phrase and #8's conditioned statement. The note is the stage
# doc's verbatim copy, which splits #1's phrase around the sizes ("So one
# table per sensor configuration is 105 MB instead of 108 GB, reused for
# every pixel and depth."), so #1 is matched as both halves in one sentence.
EFFICIENCY_ID = "demo-efficiency"
EFFICIENCY_REQUIRED = [
    ("105 MB [PROJECT_BRIEF 3.4]", r"\b105\s*MB\b"),
    ("108 GB [PROJECT_BRIEF 3.4]", r"\b108\s*GB\b"),
    ("#1 sanctioned phrase", r"one\s+table\s+per\s+sensor\s+configuration[^.]{0,60}"
                             r"reused\s+for\s+every\s+pixel\s+and\s+depth"),
    ("#8 conditioned delay statement",
     r"At\s+fixed\s+S\s+and\s+B,\s+the\s+delay\s+only\s+shifts\s+π"),
]
# #8, the unconditioned form, anywhere on any page: "the delay / depth (change)
# only shifts ..." with no fixed (S, B) / signal and background in the 80
# characters before it. /details/ conditions it in the sentence before
# ("with those held, moving the delay ... only shifts"), which this pattern
# does not match.
DELAY_SHIFT = re.compile(r"\b(delay|depth|τ)(\s+change)?\s+only\s+shifts?\b", re.I)
DELAY_COND = re.compile(r"fixed\s+(S\s+and\s+B|\(\s*S\s*,\s*B\s*\)|signal\s+and\s+background)",
                        re.I)


def check_delay_condition(text: str, rel: str, rep: Report) -> None:
    for m in DELAY_SHIFT.finditer(text):
        before = text[max(0, m.start() - 80):m.start()]
        if not DELAY_COND.search(before):
            ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 60):m.end() + 30])
            rep.fail(rel, "delay invariance stated without fixed (S, B) [#8]",
                     f"...{ctx}...")


def check_efficiency(rep: Report) -> None:
    source = (REPO / "index.html").read_text(encoding="utf-8", errors="replace")
    source = COMMENT_RE.sub(" ", source)
    art = re.search(r'<article\b[^>]*\bid="%s"(.*?)</article>' % EFFICIENCY_ID,
                    source, re.S)
    if not art:
        rep.fail("index.html", "Efficiency module missing [v2.2-B]",
                 f"no article#{EFFICIENCY_ID}")
        return
    svgs = re.findall(r'<svg\b[^>]*\bmars-schematic\b[^>]*>.*?</svg>', art.group(1), re.S)
    if len(svgs) != 2:
        rep.fail("index.html", "Efficiency schematics [v2.2-B]",
                 f"expected 2 .mars-schematic SVGs (wide, phone), found {len(svgs)}")
    for k, svg in enumerate(svgs):
        text = visible_text(svg)
        for label, rx in EFFICIENCY_REQUIRED:
            if not re.search(rx, text):
                rep.fail("index.html", f"Efficiency schematic {k + 1}: {label} missing",
                         "the note must carry it in every layout [v2.2-B]")
    rep.info.append(f"Efficiency note: 105 MB, 108 GB, #1 and #8 phrasing present in "
                    f"{len(svgs)} schematic(s)")


# v2.2-C — THE DOWNSTREAM MODULE AND THE COUNT-MODEL ABLATION. Every number
# they show is PROJECT_BRIEF 3.5's (SBR 0.6), which rounds the paper's
# tab:reconstruction_results (paper/sec/6_experiments.tex l. 195-233; the four
# decimals are in the comments below). TRANSFER_35 is that table, by row:
# reflectivity PSNR val, test (dB), depth RMSE val, test (m). "val" is tested
# on the row's own simulator / count model, "test" on gold-standard data.
TRANSFER_35 = {
    "poisson": ("36.49", "7.02", "0.072", "1.654"),   # 36.4946 7.0237 0.0722 1.6537
    "renewal": ("29.72", "12.12", "0.054", "0.096"),  # 29.7230 12.1210 0.0543 0.0959
    "zhang":   ("22.74", "22.54", "0.053", "0.082"),  # 22.7444 22.5421 0.0526 0.0820
    "mars":    ("24.03", "24.25", "0.053", "0.074"),  # 24.0321 24.2488 0.0532 0.0739
}
TRANSFER_NAMES = {"poisson": "Poisson", "renewal": "Renewal",
                  "zhang": "Zhang et al.", "mars": "MaRS"}
BRIEF = REPO.parent.parent / "PROJECT_BRIEF.md"   # absent in a bare site clone
# The ablation's framing is the point (stage doc 0): the three rows share the
# prior-work temporal PDF and our pipeline; only the count model changes.
ABLATION_REQUIRED = [
    ("'no separate Renewal or Zhang et al. simulator'",
     r"There\s+is\s+no\s+separate\s+Renewal\s+or\s+Zhang\s+et\s+al\.\s+simulator\."),
    ("'They differ only in the count mean and variance'",
     r"They\s+differ\s+only\s+in\s+the\s+count\s+mean\s+and\s+variance\."),
    ("'same accurate temporal PDF from prior work'",
     r"same\s+accurate\s+temporal\s+PDF\s+from\s+prior\s+work"),
]


def _brief_35() -> dict[str, tuple[str, ...]] | None:
    """PROJECT_BRIEF 3.5's table, parsed, when the brief is beside the repo."""
    if not BRIEF.exists():
        return None
    md = BRIEF.read_text(encoding="utf-8")
    sec = md[md.index("### 3.5"):]
    sec = sec[:sec.index("### 3.6")]
    out = {}
    for name, key in (("Poisson", "poisson"), ("Renewal", "renewal"),
                      ("Zhang et al.", "zhang"), ("MaRS", "mars")):
        row = re.search(r"^\|\s*\**" + re.escape(name) + r"\**\s*\|(.*)$", sec, re.M)
        if row:
            out[key] = tuple(re.findall(r"\d+\.\d+", row.group(1)))
    return out


def _num(s: str) -> str:
    return re.sub(r"[^\d.]", "", html.unescape(s))


def check_downstream(rep: Report) -> None:
    source = COMMENT_RE.sub(" ", (REPO / "index.html").read_text(
        encoding="utf-8", errors="replace"))
    brief = _brief_35()
    if brief is None:
        rep.info.append("v2.2-C: PROJECT_BRIEF.md not beside the repo; "
                        "TRANSFER_35 used as written")
    elif brief != TRANSFER_35:
        rep.fail("tools/audit_claims.py", "TRANSFER_35 differs from PROJECT_BRIEF 3.5 [v2.2-C]",
                 f"brief {brief} vs {TRANSFER_35}")

    # Part 1: the two chips, Reflectivity as shipped and Depth in data-depth
    art = re.search(r'<article\b[^>]*\bid="demo-downstream"(.*?)</article>', source, re.S)
    if not art:
        rep.fail("index.html", "Downstream module missing [v2.2-C]", "no article#demo-downstream")
    else:
        for side, key in (("is-left", "poisson"), ("is-right", "mars")):
            m = re.search(r'<p class="mars-compare__chip %s"\s+data-depth="([^"]*)">(.*?)</p>'
                          % side, art.group(1), re.S)
            if not m:
                rep.fail("index.html", f"Downstream chip {side} missing [v2.2-C]", "")
                continue
            depth = re.search(r"<b>(.*?)</b>", html.unescape(m.group(1)))
            refl = re.search(r"<b>(.*?)</b>", m.group(2))
            got = (_num(refl.group(1)) if refl else None, _num(depth.group(1)) if depth else None)
            want = (TRANSFER_35[key][1], TRANSFER_35[key][3])
            if got != want:
                rep.fail("index.html", f"Downstream chip {key} != PROJECT_BRIEF 3.5 [v2.2-C]",
                         f"shows {got}, 3.5 test values {want}")

    # Part 2: the table is the one source; it must equal 3.5, and the
    # captions shipped in the HTML must equal the table.
    art = re.search(r'<article\b[^>]*\bid="demo-ablation"(.*?)</article>', source, re.S)
    if not art:
        rep.fail("index.html", "Ablation module missing [v2.2-C]", "no article#demo-ablation")
        return
    body = art.group(1)
    rows = dict(re.findall(r'<tr data-k="(\w+)">(.*?)</tr>', body, re.S))
    if sorted(rows) != ["mars", "renewal", "zhang"]:
        rep.fail("index.html", "Ablation table rows [v2.2-C]",
                 f"expected renewal, zhang, mars (no Poisson), found {sorted(rows)}")
    for key, row in rows.items():
        cells = tuple(c.strip() for c in re.findall(r"<td>(.*?)</td>", row))
        if key not in TRANSFER_35 or cells != TRANSFER_35[key]:
            rep.fail("index.html", f"Ablation table row {key} != PROJECT_BRIEF 3.5 [v2.2-C]",
                     f"{cells} vs {TRANSFER_35.get(key)}")
        name = re.search(r"<th[^>]*>(.*?)</th>", row).group(1)
        if name != TRANSFER_NAMES.get(key, "?") + " count":
            rep.fail("index.html", f"Ablation table row {key} named {name!r} [v2.2-C]", "")
    caps = re.findall(r'<b data-k="(\w+)">(.*?)</b>', body)
    if sorted(k for k, _ in caps) != ["mars", "renewal", "zhang"]:
        rep.fail("index.html", "Ablation tile captions [v2.2-C]", f"found {caps}")
    for key, val in caps:
        cells = re.findall(r"<td>(.*?)</td>", rows.get(key, ""))
        if len(cells) < 2 or _num(val) != cells[1].strip() or "dB" not in val:
            rep.fail("index.html", f"Ablation caption {key} != its table value [v2.2-C]",
                     f"caption {val!r}, table test PSNR {cells[1] if len(cells) > 1 else None}")
    text = visible_text(body)
    for label, rx in ABLATION_REQUIRED:
        if not re.search(rx, text):
            rep.fail("index.html", f"Ablation footnote: {label} missing [v2.2-C]",
                     "the framing must be unmistakable (stage doc 0)")
    rep.info.append("Downstream + ablation: chips, table and captions = PROJECT_BRIEF 3.5"
                    + (" (parsed from the brief)" if brief else "")
                    + "; the 'no separate simulator' footnote present")


def check_gain_order(rep: Report) -> None:
    """#11 — accuracy -> table size -> speed -> downstream, in that order.

    RETIRED FOR `/` IN STAGE v2.2-A, deliberately and not silently: the four
    gains strip is gone from the main page (MARS_WEBSITE_BUILD_GUIDE.md 0.7;
    WEBSITE_BUILD_STATUS.md 3.7, "v2.2 amendments": "Non-negotiable #11 no
    longer applies to `/`: the strip is gone. The auditor's check is retired
    for `/` with a comment saying why"). Each number now lives in its own
    module (30x Accuracy, 40x / 1000x Efficiency, +17 dB Downstream), and
    every one of them is still traced by pass 2 and by its own copy rule.
    The function stays so the rule comes back by itself if a `ul.mars-stats`
    strip ever returns to the page: then it must be in the settled order.
    """
    index = REPO / "index.html"
    if not index.exists():
        rep.fail("index.html", "missing [#11]", "cannot check gain order")
        return
    source = index.read_text(encoding="utf-8", errors="replace")
    # SCOPED TO THE GAINS STRIP since stage 07. v2's "In short" paragraph
    # says "about 40x faster" in prose ABOVE the strip, so the first "40x" in
    # the page's visible text is no longer a gain numeral, and a whole-page
    # search reported a false 40x -> 30x -> 1000x order. #11 is about the four
    # gain blocks, so read the order out of the one `ul.mars-stats` list.
    strips = re.findall(r'<ul class="mars-stats">(.*?)</ul>', source, re.S)
    if not strips:
        rep.info.append(
            "four gains order [#11]: retired for / (v2.2-A, guide 0.7 / status "
            "3.7 v2.2 amendment) — no ul.mars-stats strip on the page")
        return
    if len(strips) != 1:
        rep.fail("index.html", "gains strip [#11]",
                 f"expected exactly one <ul class=\"mars-stats\">, found "
                 f"{len(strips)}")
        return
    text = visible_text(strips[0])

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

    print(f"MaRS claim audit — {len(files)} HTML file(s) under {REPO}")
    print("  " + ", ".join(str(f.relative_to(REPO)) for f in files)
          + f"   (public: {', '.join(PUBLIC_PAGES)})\n")
    for path in files:
        rel = str(path.relative_to(REPO))
        source = path.read_text(encoding="utf-8", errors="replace")
        text = visible_text(source)
        check_forbidden(source, text, rel, rep)
        check_conflation(text, rel, rep)
        check_numbers(text, rel, rep, found)
        check_delay_condition(text, rel, rep)

    check_equation_count(files, rep)
    check_gain_order(rep)
    check_efficiency(rep)
    check_downstream(rep)
    check_public_pages(rep)
    check_third_party(files, rep)
    check_dead_time_sections(rep)
    check_contrast(rep)

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
