#!/usr/bin/env python3
"""Main-page budget gate — MARS_WEBSITE_BUILD_GUIDE.md section 0.1 (stage 07).

v1's main page measured about 2,440 visible words, 21 images, 5 animations and
12 switch-bar tabs. v2's rule is that `/` answers "what is this, why does it
matter, and is it real" in about 30 seconds. This script measures the built
index.html against the guide's budget table and exits non-zero on any breach,
so the page cannot quietly grow back.

    python tools/page_budget.py            # measure index.html, print, gate
    python tools/page_budget.py --words    # also print every counted word

Budgets (guide 0.1), and exactly how each is measured:

  1. VISIBLE WORDS <= 350, excluding the nav, the BibTeX code block and the
     funding line. "Visible" means what a sighted reader sees on the built
     page, so these are also EXCLUDED: anything inside an element with the
     `hidden` attribute, `aria-hidden="true"` or class `mars-visually-hidden`;
     <script>, <style>, <template>, comments; attribute text (alt, title,
     aria-label). These are INCLUDED even though they are not in the HTML
     source: the hero button labels and the "Full-resolution originals" line,
     which js/mars-nav.js renders from js/site.config.js — read here from
     those two files, so a new button is counted.
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
     A WORD is a whitespace-separated token containing at least one letter or
     digit. So "—", "·", "→" and "↓" are not words; a hyphenated or
     ×-joined compound ("single-photon", "128×128×1024") is one word; "40×"
     and "+17dB" are one word each.
  2. MEDIA ITEMS above the BibTeX band == 4 — the three demos and the video.
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
     AMBIGUITY, flagged rather than resolved: the guide writes "eyebrow +
     title <= 8 words". Read as a combined limit, the guide's own approved
     Demo 3 title ("Train on wrong physics, fail on real physics.", 8 words)
     fails with its eyebrow. So the gate applies 8 to the TITLE and prints the
     eyebrow + title total beside it for the record.
  Also gated, from guide 0.3 ②: the "In short" paragraph (`.mars-inshort`)
  is at most 70 words.

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

WORD_LIMIT = 350
MEDIA_ITEMS = 4
SWITCH_MAX = 0
EQ_MAX = 0
DEMO_TITLE_MAX = 8
DEMO_SENTENCE_MAX = 35
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


def excluded(n: Node) -> bool:
    """Not visible text, or outside the word budget by the guide's rule."""
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


def text_of(n: Node, respect_exclusions=True) -> str:
    out = []
    def rec(x):
        if respect_exclusions and excluded(x):
            return
        for c in x.children:
            if isinstance(c, str):
                out.append(c)
            else:
                rec(c)
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
            out.append("· soon")
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

    print(f"MaRS main-page budget — {args.page}  (MARS_WEBSITE_BUILD_GUIDE.md 0.1)\n")

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
    check(total <= WORD_LIMIT, "visible words (nav, BibTeX code, funding excluded)",
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
    check(len(slots) == MEDIA_ITEMS, "media items above the BibTeX band",
          len(slots), f"== {MEDIA_ITEMS}")
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
            check(sw_ <= DEMO_SENTENCE_MAX, f"#{did} sentence words", sw_,
                  f"<= {DEMO_SENTENCE_MAX}")
            check(not breaks and s.rstrip()[-1:] in ".!?",
                  f"#{did} is ONE sentence", f"{len(breaks)} internal break(s)",
                  "0, and ends . ! ?")
        check(len(ms) == 1, f"#{did} has one media slot", len(ms), "== 1")

    print()
    if fails:
        print(f"FAIL — {len(fails)} budget breach(es): " + "; ".join(fails))
        return 1
    print("PASS — every guide 0.1 budget holds on " + args.page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
