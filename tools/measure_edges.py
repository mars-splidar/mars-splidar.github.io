#!/usr/bin/env python3
"""Visible-edge harness for the one-column layout (stage v2.1-A, T1/T5).

NOT A GATE. It measures, it does not judge the design: guide 0.6 item 1 says
every block on `/` and `/details/` shares one column — 960 px on desktop,
viewport - 32 px below — judged by the VISIBLE edge of each block (the ink of
a line of text, a frame's border, the first non-background column of an
image), not by its CSS box. This script prints those edges so a reviewer can
see them, before and after a layout change.

    python tools/measure_edges.py http://127.0.0.1:8741/ out.txt
    python tools/measure_edges.py BASE out.txt --widths 390,1280 --pages /

Needs Playwright (Python) and Google Chrome (`channel="chrome"`); stage 10's
harness venv has both. Everything else is the standard library plus Pillow.

HOW AN EDGE IS MEASURED. Each page is loaded at DPR 1 with reduced motion (so
the teaser is its static poster), fonts awaited, the page scrolled end to end
so lazy media lands, then one full-page screenshot is taken. For each block,
the screenshot is cropped to the block's rows and to its box +/- 8 px, and
compared against the background of the block's nearest PAINTED ANCESTOR (not
the crop's mode colour, which a row of gold plates would win). A column is
"ink" if any pixel in it differs from that background by more than 10 in any
channel (10, not 20: a table wrapper's rule-grey border on a mint band
differs from the band by only 16). The first and last ink columns are the visible left and right edges.

THREE KINDS OF BLOCK, because A1's +/- 2 px cannot mean the same thing for
all of them (stage v2.1-A handoff):
    F  fills the column: title, media frames, gains strip, code block. Both
       visible edges are judged against the column edges.
    L  flush-left ragged text (prose, captions, button row). The left edge is
       judged; the right edge must not pass the column, and the shortfall of
       the longest line is reported, not judged.
    C  centred (workload line, tagline, footer lines). Judged for symmetry
       inside the column.
    X  reported only: the teaser's label row is three columns, each centred
       under its own cube, so neither edge is meant to touch the column.
Column edges are computed from the target column (960 px, 16 px gutters), so
a "before" run prints how far the old layout was from the new target.
"""
from __future__ import annotations

import argparse
import io
import math
import sys
import time

from PIL import Image

COLUMN, GUTTER = 960, 16
WIDTHS = [320, 375, 390, 430, 600, 768, 1024, 1280, 1440, 1920]
THRESH = 10

# (label, selector, kind). Every visible match is measured; `all` = each match.
MAIN = [
    ("nav wordmark", ".mars-nav__brand", "Lnav"),
    ("nav pill", ".mars-nav__pill", "Rnav"),
    ("nav burger", ".mars-nav__burger", "Rnav"),
    ("badge", ".mars-badge", "L"),
    ("title (one line)", ".mars-hero__title", "F"),
    ("title narrow: line 1", ".mars-hero__line1", "L"),
    ("title narrow: line 2", ".mars-hero__line2", "F"),
    ("subhead", ".mars-hero__subhead", "L"),
    ("authors", ".mars-hero__authors", "L"),
    ("affiliation", ".mars-hero__affil", "L"),
    ("button row", "#mars-hero-buttons", "L"),
    ("teaser cubes", ".mars-teaser__frame", "F"),
    ("teaser labels", ".mars-teaser__cols", "X"),
    ("teaser workload", ".mars-teaser__workload", "C"),
    ("tagline", ".mars-teaser__tagline", "C"),
    ("teaser guide", ".mars-teaser__guide", "C"),
    # the cube slicer (v2.1-C): presets and readout are ragged rows, the
    # three images and the chart frame fill the column
    ("slicer eyebrow", "#slicer .mars-eyebrow", "L"),
    ("slicer title", "#slicer-title", "L"),
    ("slicer guide", ".mars-slicer__guide", "L"),
    ("slicer presets", ".mars-slicer__presets", "L"),
    ("slicer images", ".mars-slicer__trio", "F"),
    ("slicer readout", ".mars-slicer__readout", "L"),
    ("slicer chart frame", ".mars-slicer__chartbox", "F"),
    ("slicer controls", ".mars-slicer__controls", "L"),
    ("slicer note", ".mars-slicer__note", "L"),
    # v2.2-A: the In short band (heading, prose, the Fig. 1 card) replaces
    # v2.1's question above the teaser and the gains strip
    ("In short heading", "#in-short-heading", "L"),
    ("In short prose", ".mars-inshort", "L"),
    # The card is the judged block. Its image spans the card's full width,
    # but its painted ancestor is the WHITE card, so this script's +/- 8 px
    # crop reaches the card's ring and the mint beyond it and reports -8/+9:
    # the image and the caption (inset 14 px inside the card) are reported
    # only. v2.2-A measures the image box from the DOM instead.
    ("Fig. 1 card", ".mars-context", "F"),
    ("Fig. 1 image", ".mars-context__pic", "X"),
    ("Fig. 1 caption", ".mars-context__caption", "X"),
    ("Demo 2 eyebrow", "#demo-accuracy .mars-eyebrow", "L"),
    ("Demo 2 title", "#demo-accuracy-title", "L"),
    ("Demo 2 sentence", "#demo-accuracy .mars-demo__sentence", "L"),
    ("Demo 2 chart frame", ".mars-count-fig__frame", "F"),
    ("Demo 2 note", "#demo-accuracy .mars-demo__note", "L"),
    ("Demo 3 eyebrow", "#demo-downstream .mars-eyebrow", "L"),
    ("Demo 3 title", "#demo-downstream-title", "L"),
    ("Demo 3 sentence", "#demo-downstream .mars-demo__sentence", "L"),
    # v2.1-D: square + framed side panel; the toggle, the numbers and the
    # note sit inside the panel, so only the block's outer edges are judged
    ("Demo 3 block", ".mars-compare__body", "F"),
    ("Demo 3 square", ".mars-compare__stage", "X"),
    ("Demo 3 panel", ".mars-compare__panel", "X"),
    ("film heading", "#video-heading", "L"),
    ("film", ".mars-video__frame", "F"),
    ("film meta", ".mars-video__meta", "L"),
    ("Go deeper eyebrow", "#deeper-heading", "L"),
    ("Go deeper links", ".mars-deeper", "L"),
    ("originals line", "#mars-originals", "L"),
    ("limitations line", ".mars-deeper__limits", "L"),
    ("BibTeX heading", ".mars-closing__title", "L"),
    ("BibTeX block", ".mars-code", "F"),
    ("BibTeX note", ".mars-closing__note", "L"),
    ("footer rule", ".mars-closing__rule", "F"),
    ("footer links", ".mars-closing__links", "C"),
    ("footer funding", ".mars-closing__footer", "C"),
]
DETAILS = [
    ("nav wordmark", ".mars-nav__brand", "Lnav"),
    ("nav pill", ".mars-nav__pill", "Rnav"),
    ("nav burger", ".mars-nav__burger", "Rnav"),
    ("page title", ".mars-pagehead__title", "L"),
    ("page lede", ".mars-pagehead__lede", "L"),
    ("eyebrow", ".mars-band__inner > .mars-eyebrow", "Lall"),
    ("section title", ".mars-section__title", "Lall"),
    ("section lede", ".mars-band__inner > .mars-section__lede, .mars-subsection > .mars-section__lede", "Lall"),
    ("subhead", ".mars-subhead", "Lall"),
    ("switch bar", ".mars-switch", "Lall"),
    ("panel title", ".mars-panel:not([hidden]) .mars-panel__title", "Lall"),
    ("panel text", ".mars-panel:not([hidden]) .mars-panel__desc", "Lall"),
    ("cards", ".mars-cards", "Fall"),
    ("media frame", ".mars-media__frame", "Fall"),
    ("figure (single)", ".mars-band__inner > .mars-figure > img, .mars-band__inner > .mars-figure > picture, .mars-subsection > .mars-figure > img, .mars-subsection > .mars-figure > picture, .mars-panel > .mars-figure > img, .mars-panel > .mars-figure > picture", "Fall"),
    ("figure row", ".mars-figrow", "Fall"),
    ("table wrapper", ".mars-table-wrap", "Fall"),
    ("equation", ".mars-eq", "Fall"),
    ("tiles", ".mars-tiles", "Fall"),
    ("limitations", ".mars-limitations__body", "Lall"),
    ("footer links", ".mars-closing__links", "C"),
    ("footer funding", ".mars-closing__footer", "C"),
]

JS_BOXES = r"""
(sel) => {
  const out = [];
  const vis = (el) => {
    if (el.closest('[hidden]')) return false;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    if (el.closest('.mars-visually-hidden')) return false;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 1) return false;
    // the stage-06 visually-hidden <h1> below 467 px
    if (cs.position === 'absolute' && cs.clip && cs.clip.startsWith('rect(0')) return false;
    return true;
  };
  const bgOf = (el) => {
    for (let a = el.parentElement; a; a = a.parentElement) {
      const c = getComputedStyle(a).backgroundColor;
      const m = c.match(/rgba?\(([^)]+)\)/);
      if (m) { const p = m[1].split(',').map(Number); if (p.length < 4 || p[3] > 0.5) return p.slice(0, 3); }
    }
    return [250, 251, 250];
  };
  for (const el of document.querySelectorAll(sel)) {
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect();
    out.push({x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height, bg: bgOf(el)});
  }
  return out;
}
"""


def ink_edges(img, box, W):
    """First and last ink column of `box` in the full-page image."""
    x0 = max(0, int(box["x"]) - 8)
    x1 = min(W, int(box["x"] + box["w"]) + 9)
    y0 = max(0, math.floor(box["y"]))        # floor/ceil: a 1 px rule at a
    y1 = min(img.height, math.ceil(box["y"] + box["h"]))   # fractional y
    if x1 <= x0 or y1 <= y0:
        return None
    crop = img.crop((x0, y0, x1, y1))
    bg = box["bg"]
    px = crop.load()
    cw, ch = crop.size
    cols = []
    for x in range(cw):
        for y in range(ch):
            r, g, b = px[x, y][:3]
            if max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2])) > THRESH:
                cols.append(x)
                break
    if not cols:
        return None
    return x0 + cols[0], x0 + cols[-1] + 1     # right edge exclusive


def column(W):
    cw = min(COLUMN, W - 2 * GUTTER)
    left = (W - cw) / 2
    return left, left + cw, cw


def verdict(kind, l, r, cl, cr):
    dl, dr = l - cl, r - cr
    k = kind[0]          # "Fall" / "Lall" judge like F / L
    if kind == "Lnav":
        return dl, dr, ("ok" if abs(dl) <= 2 else "OFF"), "left edge judged"
    if kind == "Rnav":
        return dl, dr, ("ok" if abs(dr) <= 2 else "OFF"), "right edge judged"
    if k == "F":
        return dl, dr, ("ok" if abs(dl) <= 2 and abs(dr) <= 2 else "OFF"), ""
    if k == "L":
        ok = abs(dl) <= 2 and dr <= 2
        return dl, dr, ("ok" if ok else "OFF"), f"short by {-dr:.0f}" if dr < -2 else ""
    if k == "C":
        asym = (l - cl) - (cr - r)
        ok = abs(asym) <= 2 and dl >= -2 and dr <= 2
        return dl, dr, ("ok" if ok else "OFF"), f"asym {asym:+.0f}"
    return dl, dr, "—", "reported, not judged"


def measure(pg, url, W, blocks, log):
    pg.set_viewport_size({"width": W, "height": 900})
    pg.goto(url, wait_until="load")
    pg.evaluate("document.fonts.ready.then(()=>1)")
    h = pg.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h + 900, 600):
        pg.evaluate(f"window.scrollTo(0,{y})")
        pg.wait_for_timeout(40)
    pg.wait_for_timeout(800)
    pg.evaluate("window.scrollTo(0,0)")
    pg.wait_for_timeout(300)
    png = pg.screenshot(full_page=True)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    cl, cr, cw = column(W)
    ovf = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    log(f"\n  {W} px  column {cl:.0f}-{cr:.0f} ({cw} px)  page overflow {ovf} px")
    log(f"    {'block':<26}{'kind':<5}{'vis L':>7}{'vis R':>7}{'dL':>6}{'dR':>6}  verdict")
    rows = []
    for label, sel, kind in blocks:
        boxes = pg.evaluate(JS_BOXES, sel)
        for i, b in enumerate(boxes):
            e = ink_edges(img, b, W)
            name = label if len(boxes) == 1 else f"{label} {i + 1}"
            if e is None:
                log(f"    {name:<26}{kind[0]:<5}{'—':>7}{'—':>7}            no ink found")
                continue
            l, r = e
            dl, dr, v, note = verdict(kind, l, r, cl, cr)
            rows.append((name, kind, l, r, dl, dr, v))
            log(f"    {name:<26}{kind[0]:<5}{l:>7}{r:>7}{dl:>+6.0f}{dr:>+6.0f}  {v:<4} {note}")
    return rows, ovf


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--widths", default=",".join(map(str, WIDTHS)))
    ap.add_argument("--pages", default="/,/details/")
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright

    base = args.base.rstrip("/")
    widths = [int(w) for w in args.widths.split(",")]
    lines = []

    def log(s=""):
        lines.append(s)
        print(s, flush=True)

    summary = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        log(f"Visible edges — {time.strftime('%Y-%m-%d %H:%M %Z')} — Chrome {b.version}, DPR 1, reduced motion, "
            f"fonts awaited, ink threshold {THRESH}/255. Target column {COLUMN} px, {GUTTER} px gutters.")
        log("dL/dR = visible edge minus column edge (px). F judged both sides +/-2; L: left +/-2 and "
            "right <= column; C: symmetric within +/-2; nav: wordmark left, pill/burger right.")
        for page in args.pages.split(","):
            blocks = MAIN if page.strip("/") == "" else DETAILS
            log(f"\n=== {page} ===")
            ctx = b.new_context(device_scale_factor=1, reduced_motion="reduce",
                                viewport={"width": 1280, "height": 900})
            pg = ctx.new_page()
            for W in widths:
                rows, ovf = measure(pg, base + page, W, blocks, log)
                off = [r[0] for r in rows if r[6] not in ("ok", "—")]
                summary.append((page, W, len(rows), off, ovf))
            ctx.close()
        b.close()
    log("\n=== summary ===")
    for page, W, n, off, ovf in summary:
        log(f"  {page:<10}{W:>5} px  {n:>3} blocks  off: {len(off):>2}  overflow {ovf}  "
            + (", ".join(off) if off else ""))
    open(args.out, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
