#!/usr/bin/env python3
"""Main-page budget gate — MARS_WEBSITE_BUILD_GUIDE.md 0.1, as revised by 0.6 item 6 and 0.7.

v1's main page measured about 2,440 visible words, 21 images, 5 animations and
12 switch-bar tabs. v2's rule is that `/` answers "what is this, why does it
matter, and is it real" in about 30 seconds. This script measures the built
index.html against the guide's budget table and exits non-zero on any breach,
so the page cannot quietly grow back.

    python tools/page_budget.py            # measure index.html, print, gate
    python tools/page_budget.py --words    # also print every counted word

Budgets (guide 0.1; since stage v2.1-A the limits of guide 0.6 item 6 —
420 words, at most 6 media items; since stage v2.2-A those of guide 0.7 —
520 words, at most 9 media items), and exactly how each is measured:

  1. VISIBLE WORDS <= 599 (v2.3-B's measured total; 604 at v2.3-A, 598 at v2.2-D), re-pinned by v2.2-P at 600 once Demo 2's 12 chart
     words became schematic text (612 at v2.2-C's pin; 350 until v2.1-A, 420 until
     v2.2-A, 520 until v2.2-C; 580 was the planned v2.2-C limit), excluding the nav, the BibTeX
     code block and the funding line. "Visible" means what a sighted reader sees on the built
     page, so these are also EXCLUDED: anything inside an element with the
     `hidden` attribute, `aria-hidden="true"` or class `mars-visually-hidden`;
     <script>, <style>, <template>, comments; attribute text (alt, title,
     aria-label). These are INCLUDED even though they are not in the HTML
     source: the hero button labels, a null URL's "<Label> coming soon" text
     (v2.2-A; it was "<Label> · soon"), and the "Full-resolution originals"
     line (in Go deeper since v2.2-A), which js/mars-nav.js renders from
     js/site.config.js — read here from those two files, so a new button is
     counted.
     ONE DELIBERATE EXCEPTION to the `hidden` rule: the teaser's HTML label
     row (`.mars-teaser__labels`) is counted even if it ships `hidden`.
     Stage 07 shipped it hidden behind an interim raster and un-hid it at
     runtime; since stage 09 it is visible from first paint, so the
     exception no longer changes the count, and stays only so the gate
     cannot be gamed by re-hiding it.
     JS-SWAPPED TEXT (stage 09): Demo 3's Reflectivity / Depth toggle swaps
     its side labels and note from data-depth attributes. The gate counts
     the Reflectivity state the HTML ships; the Depth state has the same
     word count (measured in the browser, stage 09 measurements.txt).
     v2.3-B: the note is gone; the swapped text is the four captions under
     the two sliders ("Poisson-trained 7.02 dB" <-> "... 1.654 m"), the same
     3 words in either mode. The "Ground truth" each caption shows while the
     phone hold button is held ships `hidden`, so it is not counted.
     INTERACTIVE UI SCOPE (stage v2.1-C, WEBSITE_BUILD_STATUS 3.7 v2.1
     amendment): text inside an element with class `mars-ui` — control
     labels, buttons, legends, axis text and the slicer's status line — is
     NOT prose. (The slicer's three image names are a label row, so they stay
     prose, like the teaser's.) It is counted and reported separately
     ("UI words") and is not held against the 420. Prose stays counted
     wherever it sits: headings, paragraphs, captions, label rows, readouts.
     SCHEMATIC SCOPE (stage v2.2-B, WEBSITE_BUILD_STATUS 2, "Budget scope
     extended (2026-10-28)"): text inside an element with class
     `mars-schematic` (the Efficiency diagram's SVG labels and captions)
     counts like `.mars-ui`: reported, not counted against the prose budget.
     It is reported per schematic, because the module ships one SVG per
     breakpoint and only one of them is ever shown. v2.2-P: Demo 2's chart
     joined it (two wrappers, desktop and phone, 12 words each).
     A WORD is a whitespace-separated token containing at least one letter or
     digit. So "—", "·", "→" and "↓" are not words; a hyphenated or
     ×-joined compound ("single-photon", "128×128×1024") is one word; "40×"
     and "+17dB" are one word each.
  2. MEDIA ITEMS above the BibTeX band <= 9 (v2.2-A, guide 0.7; 6 from
     v2.1-A, == 4 before) — guide 0.6 item 6 named six: the Fig. 1 top half,
     the teaser, the cube slicer, Demo 2, Demo 3 and the film; v2.2-B/C add
     Efficiency and the ablation. The Fig. 1 figure (in the In short band
     since v2.2-A) is ONE item although it holds two <picture>s (the desktop
     image, and the second phone crop).
     Counted as `[data-media-slot]` containers, not as <img> tags: a demo's
     one media item may legitimately hold several images (stage 07's interim
     Demo 3 is a two-up). As a guard, any <img>, <video>, <picture>,
     <iframe> or <canvas> above BibTeX that is NOT inside a slot is a breach.
  3. SWITCH BARS: `[data-switch]` == 0.
  4. DISPLAY EQUATIONS: `.mars-eq` == 0 on `/` (the one sanctioned equation
     lives on /details/; tools/audit_claims.py checks "exactly one" site-wide).
  5. PER DEMO (each `article.mars-demo`): an eyebrow; a title
     (`.mars-demo__title`) of at most 8 words; exactly ONE sentence
     (`.mars-demo__sentence`) of at most 35 words, ending in . ! or ? with no
     sentence break inside it; exactly one media slot.
     v2.2-A EXCEPTION, by id (SENTENCES_MAX below): #demo-accuracy may hold
     TWO sentences. Guide 0.7's style rule (no semicolons) and the stage doc's
     T5 turned its one sentence's semicolon into a full stop — the same
     words, now two sentences. The 35-word limit is unchanged.
     v2.2-B, by id: #demo-efficiency holds THREE sentences, the lead of
     guide 0.7 verbatim, which is 38 words. SENTENCE_WORDS_MAX pins its word
     limit at exactly that approved length (not a looser round number), so
     the lead cannot grow; every other demo keeps 35.
     v2.2-C, by id: #demo-downstream holds THREE sentences ("We trained ...
     gold-standard data. Trained on Poisson, it fails. Trained on MaRS, it
     works.", 25 words) and #demo-ablation TWO (26 words), the stage doc's
     verbatim leads (stage_v22C_downstream.md 1). Both are within 35.
     v2.2-C also moved Downstream's Reflectivity / Depth toggle into
     `.mars-ui` (it was counted as prose before) along with the new
     toggle, legend and hold button; the image chips and tile captions are
     a label row and captions, so they stay prose.
     AMBIGUITY, flagged rather than resolved: the guide writes "eyebrow +
     title <= 8 words". Read as a combined limit, the guide's own approved
     Demo 3 title ("Train on wrong physics, fail on real physics.", 8 words)
     fails with its eyebrow. So the gate applies 8 to the TITLE and prints the
     eyebrow + title total beside it for the record.
  Also gated, from guide 0.3 ②: the "In short" paragraph (`.mars-inshort`)
  is at most 70 words.
  6. THE CUBE SLICER (v2.1-C, guide 0.6 items 3 and 5), `section#slicer`:
     one eyebrow; a title (`#slicer-title`) of at most 8 words; the guiding
     text (`.mars-slicer__guide`) at most 35 words — it is the guide's
     approved sentences, verbatim (three since v2.2-A, guide 0.7), so the
     per-demo one-sentence rule is not applied (it is not an
     article.mars-demo); exactly one media slot.
     The readout and footnote are prose and counted above.

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# v2.2-C: PINNED at the measured total of the verbatim v2.2-C copy (612),
# the author's choice of 2026-10-28, like v2.2-B's 38-word pin: the planning
# raise to 580 assumed ~60 new words, and the approved Downstream + ablation
# copy is +110 net. Nothing on `/` can grow without a new decision.
# v2.2-P: RE-PINNED at 600. Demo 2's chart words (12: Renewal, Zhang et al.,
# MaRS, Gold standard, Poisson, Registered photon count, Probability) moved
# into .mars-schematic wrappers, by the 2026-10-28 rule (WEBSITE_BUILD_STATUS
# 2, "Budget pinned at 612"): moving words out re-pins the limit at the new
# measured total, so it never creates room for new copy.
# v2.2-D: RE-PINNED at 598, the measured total after the author's copy
# changes (approved copy re-pins the same way, guide 0.7): the slicer eyebrow
# "Cube slicer · Visualize dead-time effects" +3, the BibTeX "Provisional
# entry" note removed (the entry is final, author 2026-10-29) -5; the Accuracy
# title's full stop, the Efficiency note's word order and the dash and
# semicolon sweep change no word count. The 2 freed words are not room.
# v2.3-A: RE-PINNED at 604, the measured total after the approved v2.3 copy
# (guide 0.8): the teaser tagline "MaRS: an accurate and fast single-photon
# LiDAR simulator." removed -8 (a hyphenated compound is one word), the new
# three-sentence Fig. 1 caption +14 (49 words, was 35). The slicer's preset
# hints and note are .mars-ui (reported as UI words, 55 -> 82: hints +6, the
# bright note +21); their four aria-hidden sizer copies count nowhere.
# v2.3-B: RE-PINNED at 599, the measured total after guide 0.8's Downstream
# (two scenes): the note under the module removed -17; the v2.2-C image
# chips removed -8 (Poisson-trained 7.02 dB, MaRS-trained 24.25 dB, Ground
# truth); the two group headers "SBR 0.6" / "SBR 1.0" +4, the two "Ground
# truth" captions +4 and the four slider captions +12, counted as the chips
# were (captions are prose). The toggle's new "PSNR" / "RMSE" are .mars-ui
# (UI words 82 -> 84). The 5 freed words are not room.
# v2.3-C: RE-PINNED at 609, the measured total after guide 0.8's Ablation
# (SBR 0.6 and SBR 1.0, zoom rows): the lead's second sentence swapped, 15
# words for 15 (0); the footnote's "Test set, SBR 0.6, same network for every
# row." removed -9; the v2.2-C tile captions removed -23 (Ground truth
# reference, and "<model> count test set <value> dB" x 3); the two zoom-row
# headers "SBR 0.6" / "SBR 1.0" +4, the two "Ground truth drag the box"
# captions +10 and the six "<model> count <value> dB" captions +28 (captions
# are prose, both rows count although phones show one at a time). The phone
# SBR toggle is .mars-ui (UI words 84 -> 88); the chart's SVG text is .mars-ui
# as before; the two visually hidden row sentences count nowhere.
WORD_LIMIT = 609        # v2.3-C re-pin; 599 v2.3-B, 604 v2.3-A, 598 v2.2-D, 600 v2.2-P, 612 v2.2-C pin, 580 planned (status 2), 520 from v2.2-A, 420 from v2.1-A, 350 before
MEDIA_ITEMS = 9         # guide 0.7 (v2.2-A): at most 9; 6 from v2.1-A, exactly 4 before
SWITCH_MAX = 0
EQ_MAX = 0
DEMO_TITLE_MAX = 8
DEMO_SENTENCE_MAX = 35
# v2.2-A: sentences allowed in a demo's `.mars-demo__sentence`, by article id
# (default 1). See docstring item 5.
SENTENCES_MAX = {"demo-accuracy": 2, "demo-efficiency": 3,
                 "demo-downstream": 3, "demo-ablation": 2}
# v2.2-B: a demo's sentence word limit, by article id (default
# DEMO_SENTENCE_MAX). The Efficiency lead is guide 0.7's three sentences,
# verbatim: 38 words. See docstring item 5.
SENTENCE_WORDS_MAX = {"demo-efficiency": 38}
INSHORT_MAX = 70

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "template", "noscript"}
MEDIA_TAGS = {"img", "video", "picture", "iframe", "canvas"}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.children: list = []        # Node or str

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.walk()

    def ancestors(self):
        a = self.parent
        while a is not None:
            yield a
            a = a.parent


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def is_ui(n: Node) -> bool:
    """`.mars-ui` control text, or `.mars-schematic` diagram text (v2.2-B):
    neither is prose."""
    return any("mars-ui" in x.classes or "mars-schematic" in x.classes
               for x in [n, *n.ancestors()])


def is_schematic(n: Node) -> bool:
    return any("mars-schematic" in x.classes for x in [n, *n.ancestors()])


def excluded(n: Node, ui_too: bool = True) -> bool:
    """Not visible text, or outside the word budget by the guide's rule.
    With ui_too, `.mars-ui` text is excluded as well (it is not prose)."""
    if ui_too and is_ui(n):
        return True
    for x in [n, *n.ancestors()]:
        if x.tag in SKIP_TAGS or x.tag in ("nav", "pre"):
            return True
        if ("hidden" in x.attrs and "mars-teaser__labels" not in x.classes) \
                or x.attrs.get("aria-hidden") == "true":
            return True
        if "mars-visually-hidden" in x.classes:
            return True
        if "mars-closing__footer" in x.classes:      # the funding line
            return True
    return False


def text_of(n: Node, respect_exclusions=True, ui_only=False) -> str:
    """Visible prose under n; with ui_only, only the visible `.mars-ui`
    text instead."""
    out = []
    def rec(x):
        if respect_exclusions and excluded(x, ui_too=not ui_only):
            return
        if ui_only and not is_ui(x):
            for c in x.children:
                if isinstance(c, Node):
                    rec(c)
                    out.append(" ")
            return
        for c in x.children:
            if isinstance(c, str):
                out.append(c)
            else:
                rec(c)
                if ui_only:         # "<p>Poisson</p><p>Gold …" are two labels
                    out.append(" ")
    rec(n)
    return re.sub(r"\s+", " ", "".join(out)).strip()


WORD = re.compile(r"[0-9A-Za-zÀ-ÿ]")


def words(s: str) -> list[str]:
    return [t for t in s.split() if WORD.search(t)]


def js_rendered_words() -> tuple[list[str], str]:
    """The hero buttons and the full-resolution note, as mars-nav.js renders
    them from site.config.js. Read from the sources, not hard-coded."""
    nav = (REPO / "js" / "mars-nav.js").read_text(encoding="utf-8")
    cfg = (REPO / "js" / "site.config.js").read_text(encoding="utf-8")
    block = nav[nav.index("var BUTTONS = ["):]
    block = block[:block.index("];")]
    out = []
    for m in re.finditer(r'\{\s*label:\s*"([^"]+)"(.*?)\}', block, re.S):
        label, rest = m.group(1), m.group(2)
        out.append(label)
        km = re.search(r'key:\s*"(\w+)"', rest)
        if km and re.search(r"\b%s:\s*null\b" % km.group(1), cfg):
            out.append("coming soon")       # "Code coming soon" (v2.2-A)
    note = []
    for key, lab in (("paperPdfFull", "paperPdfFullLabel"),
                     ("posterPdfFull", "posterPdfFullLabel")):
        if re.search(r'\b%s:\s*"' % key, cfg):
            lm = re.search(r'\b%s:\s*"([^"]+)"' % lab, cfg)
            note.append(lm.group(1) if lm else key)
    if note:
        out.append("Full-resolution originals: " + " · ".join(note))
    text = " ".join(out)
    return words(text), text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--words", action="store_true",
                    help="print every counted word, grouped by region")
    ap.add_argument("--page", default="index.html")
    args = ap.parse_args()

    b = Builder()
    b.feed((REPO / args.page).read_text(encoding="utf-8"))
    nodes = list(b.root.walk())
    body = next(n for n in nodes if n.tag == "body")
    fails: list[str] = []

    def check(ok, label, value, limit):
        mark = "ok  " if ok else "FAIL"
        print(f"  [{mark}] {label:<52} {value}  (limit {limit})")
        if not ok:
            fails.append(label)

    print(f"MaRS main-page budget — {args.page}  (MARS_WEBSITE_BUILD_GUIDE.md 0.1 / 0.6 / 0.7)\n")

    # 1 — visible words
    static_words = words(text_of(body))
    js_words, js_text = js_rendered_words()
    total = len(static_words) + len(js_words)
    print("  visible words, by top-level region:")
    regions = [c for c in body.children if isinstance(c, Node)]
    for r in regions:
        for sec in ([c for c in r.children if isinstance(c, Node)]
                    if r.tag == "main" else [r]):
            w = words(text_of(sec))
            if not w:
                continue
            name = sec.attrs.get("id") or sec.attrs.get("aria-labelledby") \
                or sec.tag
            print(f"      {len(w):>4}  {sec.tag}#{name}")
            if args.words:
                print("            " + " ".join(w))
    print(f"      {len(js_words):>4}  rendered by js/mars-nav.js: {js_text}")
    sch_nodes = [n for n in nodes if "mars-schematic" in n.classes]
    sch_words = [w for n in sch_nodes for w in words(text_of(n, ui_only=True))]
    ui_words = words(text_of(body, ui_only=True))
    print(f"      UI words in .mars-ui (reported, not counted): "
          f"{len(ui_words) - len(sch_words)}")
    if args.words and ui_words:
        print("            " + " ".join(w for w in ui_words))
    for n in sch_nodes:
        w = words(text_of(n, ui_only=True))
        cls = (" ".join(c for c in n.classes if c.startswith("is-"))
               or next((c for c in n.classes if c != "mars-schematic"), n.tag))
        print(f"      schematic words in .mars-schematic {n.tag}.{cls} "
              f"(reported, not counted): {len(w)}")
    check(total <= WORD_LIMIT, "visible PROSE words (nav, BibTeX code, funding, .mars-ui, .mars-schematic excluded)",
          total, f"<= {WORD_LIMIT}")

    # 2 — media items above BibTeX
    order = nodes
    bib = next((i for i, n in enumerate(order) if n.attrs.get("id") == "bibtex"),
               len(order))
    above = order[:bib]
    slots = [n for n in above if "data-media-slot" in n.attrs]
    stray = [n for n in above if n.tag in MEDIA_TAGS
             and not any("data-media-slot" in a.attrs for a in n.ancestors())
             and "data-media-slot" not in n.attrs]
    print("\n  media slots above BibTeX: "
          + ", ".join(n.attrs["data-media-slot"] for n in slots))
    check(len(slots) <= MEDIA_ITEMS, "media items above the BibTeX band",
          len(slots), f"<= {MEDIA_ITEMS}")
    check(not stray, "media elements outside any [data-media-slot]",
          len(stray), "== 0")

    # 3, 4
    sw = [n for n in nodes if "data-switch" in n.attrs]
    eq = [n for n in nodes if "mars-eq" in n.classes]
    check(len(sw) <= SWITCH_MAX, "switch bars [data-switch]", len(sw),
          f"== {SWITCH_MAX}")
    check(len(eq) <= EQ_MAX, "display equations .mars-eq", len(eq),
          f"== {EQ_MAX}")

    # In short
    ins = [n for n in nodes if "mars-inshort" in n.classes]
    if len(ins) != 1:
        check(False, "exactly one .mars-inshort paragraph", len(ins), "== 1")
    else:
        check(len(words(text_of(ins[0]))) <= INSHORT_MAX,
              "'In short' paragraph words", len(words(text_of(ins[0]))),
              f"<= {INSHORT_MAX}")

    # 5 — per demo
    demos = [n for n in nodes if n.tag == "article" and "mars-demo" in n.classes]
    print(f"\n  demo cards: {len(demos)}")
    for d in demos:
        did = d.attrs.get("id", "?")
        sub = list(d.walk())
        eb = [n for n in sub if "mars-eyebrow" in n.classes]
        ti = [n for n in sub if "mars-demo__title" in n.classes]
        se = [n for n in sub if "mars-demo__sentence" in n.classes]
        ms = [n for n in sub if "data-media-slot" in n.attrs]
        ebw = len(words(text_of(eb[0]))) if eb else 0
        tiw = len(words(text_of(ti[0]))) if ti else 0
        print(f"    #{did}: eyebrow {ebw} word(s), title {tiw}, "
              f"eyebrow + title {ebw + tiw}")
        check(len(eb) == 1, f"#{did} has one eyebrow", len(eb), "== 1")
        check(len(ti) == 1 and tiw <= DEMO_TITLE_MAX, f"#{did} title words",
              tiw, f"<= {DEMO_TITLE_MAX}")
        if len(se) != 1:
            check(False, f"#{did} has exactly one sentence element", len(se), "== 1")
        else:
            s = text_of(se[0])
            sw_ = len(words(s))
            breaks = re.findall(r"[.!?]\s+[A-Z]", s)
            nmax = SENTENCES_MAX.get(did, 1)
            wmax = SENTENCE_WORDS_MAX.get(did, DEMO_SENTENCE_MAX)
            check(sw_ <= wmax, f"#{did} sentence words", sw_, f"<= {wmax}")
            check(len(breaks) <= nmax - 1 and s.rstrip()[-1:] in ".!?",
                  f"#{did} is {'ONE sentence' if nmax == 1 else f'<= {nmax} sentences'}",
                  f"{len(breaks)} internal break(s)",
                  f"{nmax - 1}, and ends . ! ?")
        check(len(ms) == 1, f"#{did} has one media slot", len(ms), "== 1")

    # 6 — the cube slicer
    sl = next((n for n in nodes if n.tag == "section"
               and n.attrs.get("id") == "slicer"), None)
    if sl is not None:
        sub = list(sl.walk())
        eb = [n for n in sub if "mars-eyebrow" in n.classes]
        ti = [n for n in sub if n.attrs.get("id") == "slicer-title"]
        gd = [n for n in sub if "mars-slicer__guide" in n.classes]
        ms = [n for n in sub if "data-media-slot" in n.attrs]
        prose = len(words(text_of(sl)))
        ui = len(words(text_of(sl, ui_only=True)))
        print(f"\n  cube slicer #slicer: {prose} prose word(s), {ui} UI word(s)")
        check(len(eb) == 1, "#slicer has one eyebrow", len(eb), "== 1")
        tiw = len(words(text_of(ti[0]))) if ti else 0
        check(len(ti) == 1 and tiw <= DEMO_TITLE_MAX, "#slicer title words",
              tiw, f"<= {DEMO_TITLE_MAX}")
        gw = len(words(text_of(gd[0]))) if gd else 0
        check(len(gd) == 1 and gw <= DEMO_SENTENCE_MAX,
              "#slicer guiding text words (guide 0.7, 3 sentences)", gw,
              f"<= {DEMO_SENTENCE_MAX}")
        check(len(ms) == 1, "#slicer has one media slot", len(ms), "== 1")

    print()
    if fails:
        print(f"FAIL — {len(fails)} budget breach(es): " + "; ".join(fails))
        return 1
    print("PASS — every guide 0.1 / 0.6 / 0.7 budget holds on " + args.page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
