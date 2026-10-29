#!/usr/bin/env python3
"""Fig. 1, top half WITHOUT the question — the In short band on `/` (stage v2.2-A, T4).

    python tools/build_fig1_context.py            # build, compare, copy into assets/img/
    python tools/build_fig1_context.py --dry-run  # build and compare only, write nothing

v2.1 showed the paper's Fig. 1 top half above the teaser as "the question",
ending in "Can we simulate this process? Fast and Precise?" and a yellow arrow
pointing at it (tools/build_fig1_question.py, files fig1_question*; both
retired in v2.2-D, see git history at tag v2.1). In v2.2 the figure moves
below the demos as context (guide 0.7), so those two elements go.

HOW THEY ARE REMOVED — from the PDF, not painted over. Both are vector in
`paper/Figs/main/Fig1_teaser.pdf` (read only; nothing in paper/ is touched):
  * the arrow is ONE filled path (shaft + head, two subpaths, one `f`) in the
    gold fill 0.823529 0.627451 0 — the only use of that colour on the page;
  * the question is TWO text blocks (q … BT … ET … Q) right after it, in the
    same fill: "Can we simulate this process?" (TT10, Aptos Display) and "Fast
    and Precise?" (TT12, Aptos Display Bold), whose `cm` origins are
    QUESTION_ORIGINS below.
The script finds that run of operators BY CONTENT (the gold `scn`, through the
second text block's `Q`), asserts it is exactly that — one path fill, two text
blocks at those origins, q/Q balanced, and the very next operator sets a new
fill colour so nothing after it inherits the gold — and writes the page
without it to a temporary PDF. pdftotext on the result must lose exactly the
nine question words and nothing else.

RENDERING is v2.1-A's pipeline (build_fig1_question.py), unchanged:
pdftocairo at 2x the output width, Lanczos down to the output width, WebP
q 82, the largest image of each crop also as PNG. Desktop shows the whole top
half, x 21-3789 pt: fig1_context (1920, + PNG) and fig1_context_960. Phones
show two tight crops, each cut from the ink (below).
Retired in v2.2-D (git history): v2.2-A's acq (x 21-2467 pt) and trimmed
infer (x 2468-3789 pt) crops, fig1_context_acq*, fig1_context_infer*, and
the diff against the fig1_question* exports (v2.2-A's one-time proof that
only the question's pixels changed: review/v22A, fig1_build).

THE TIGHT INFERENCE CROP (stage v2.2-P, T3): fig1_context_infer_tight (1200,
+ PNG) and _infer_tight_600, what phones show since v2.2-P, at 68 % of the
card. The box is found from the ink of the question-free PDF, not by eye:
the inference panel's region (x 2468-3789 pt) holds four runs of ink
columns — the black arrow coming in from the cube (it starts on the crop's
left edge), the inference shape, the bracket and the two output tiles. The
tight box starts INFER_TIGHT_MARGIN_PT left of the shape, ends at the
panel's right edge (the tiles run to the figure's edge), and spans the ink
of shape, bracket and tiles plus the same margin above and below. Asserted:
the arrow's last ink column is left of the box, and the box's left column
and its top and bottom rows hold no ink in every output file (the edge
check is printed). It is rendered by the same pipeline (pdftocairo at 2x,
Lanczos down), so every pixel is the PDF's.

THE TIGHT ACQUISITION CROP (stage v2.2-D, T3): fig1_context_acq_tight (1200,
+ PNG) and _acq_tight_600, what phones show above the inference crop since
v2.2-D. v2.2-A's acq crop ended at x 2467 pt, the grey panel's right edge,
and so kept the tail of the black arrow to the inference panel, which starts
at x 2448.25 pt ON the grey panel. No right edge can be white there: left of
2467 pt is the panel, right of it the arrow runs to 2631 pt. So the box keeps
v2.2-A's left edge and vertical range and ends ACQ_TIGHT_MARGIN_PT right of
the last ink of the panel's content (the cube's red edge, 2429.5 pt),
cutting the panel's flat grey fill. Found from the render, not by eye: in
the band x 2300-2700 pt the dark ink (< 60 grey: cube, arrows, text) forms
runs, the last of which is the arrow; the content's last column is the last
dark or red (cube edge) column left of it. Asserted: the arrow's first
column is right of the box, and the box's right edge holds no dark ink and
no red in every output file (only the panel's fill, >= 100 grey; the
printed check counts pixels < 100 on the last two columns, and red ones).

THE COMPARISON (stdout). Every output is built in a temp dir and compared,
by md5, with the committed file of the same name: "unchanged", "NEW", or
"CHANGED". A changed file fails the run (re-cutting a crop means a new file
name, as v2.2-P and v2.2-D did), so the desktop fig1_context* files are
proven byte-identical on every run.

OUTPUT FILES are built in a temp dir outside OneDrive and copied into
assets/img/ once each, with the md5 checked after the copy (WEBSITE_BUILD_STATUS
3.7, the OneDrive write rule). Unchanged files are not rewritten.

DEPENDENCIES: pikepdf, Pillow with WebP, numpy; poppler's pdftocairo and
pdftotext on PATH.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import numpy as np
import pikepdf
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
PDF = REPO.parent.parent / "paper" / "Figs" / "main" / "Fig1_teaser.pdf"
OUT = REPO / "assets" / "img"

# v2.1-A's constants (build_fig1_question.py, retired in v2.2-D).
Y0, Y1 = 11, 984
CROPS = {"whole": (21, 3789), "acq": (21, 2467), "infer": (2468, 3789)}
WEBP_Q = 82
FILES = [                     # desktop, the whole top half: (basename, width, PNG?)
    ("fig1_context", 1920, True),
    ("fig1_context_960", 960, False),
]

GOLD = (Decimal("0.823529"), Decimal("0.627451"), Decimal("0"))
QUESTION_ORIGINS = [(2718.77, -867.654), (2894.95, -954.054)]   # the two cm e, f
QUESTION_WORDS = ["Can", "we", "simulate", "this", "process?", "Fast", "and",
                  "Precise?"]
PAGE_H = 2157                 # MediaBox height, pt: user space is y-up
INFER_TIGHT_MARGIN_PT = 8     # v2.2-P: white kept around the tight crop's ink
TIGHT_FILES = [               # v2.2-P (T3): (basename, width, PNG?)
    ("fig1_context_infer_tight", 1200, True),
    ("fig1_context_infer_tight_600", 600, False),
]
ACQ_TIGHT_MARGIN_PT = 8       # v2.2-D: panel kept right of the cube's last ink
ACQ_TIGHT_FILES = [           # v2.2-D (T3): (basename, width, PNG?)
    ("fig1_context_acq_tight", 1200, True),
    ("fig1_context_acq_tight_600", 600, False),
]


def strip_question(src: Path, dst: Path) -> tuple[list[float], list[float]]:
    """Write `src` without the arrow and the question to `dst`. Returns the
    arrow's bbox in top-left pt (x0, y0, x1, y1) and the run's op indices."""
    pdf = pikepdf.open(src)
    page = pdf.pages[0]
    ops = pikepdf.parse_content_stream(page)

    def name(i):
        return str(ops[i].operator)

    gold = [i for i in range(len(ops)) if name(i) == "scn"
            and tuple(Decimal(str(x)) for x in ops[i].operands) == GOLD]
    assert len(gold) == 1, f"expected one gold fill, found {len(gold)}"
    start = gold[0]
    end = next(i for i in range(start + 1, len(ops))
               if name(i) in ("scn", "sc", "rg", "g", "k", "cs"))
    run = list(range(start, end))           # gold scn .. last Q, inclusive

    names = [name(i) for i in run]
    assert names.count("f") == 1, names
    assert names.count("BT") == 2 and names.count("ET") == 2, names
    assert names.count("q") == names.count("Q") == 2, names
    depth = 0
    for n in names:
        depth += (n == "q") - (n == "Q")
        assert depth >= 0
    assert depth == 0, "q/Q not balanced inside the removed run"
    origins = [tuple(float(x) for x in ops[i].operands[4:6])
               for i in run if name(i) == "cm"]
    assert len(origins) == 2 and all(
        abs(a - c) < 0.01 and abs(b - d) < 0.01
        for (a, b), (c, d) in zip(origins, QUESTION_ORIGINS)), origins
    assert name(end) == "scn" and tuple(Decimal(str(x)) for x in ops[end].operands) != GOLD

    pts = [tuple(float(x) for x in ops[i].operands)
           for i in run if name(i) in ("m", "l")]
    xs, ys = [p[0] for p in pts], [PAGE_H - p[1] for p in pts]
    arrow = [min(xs), min(ys), max(xs), max(ys)]

    kept = [op for i, op in enumerate(ops) if i not in set(run)]
    page.Contents = pdf.make_stream(pikepdf.unparse_content_stream(kept))
    pdf.save(dst)
    return arrow, [run[0], run[-1]]


def words(pdf: Path) -> list[tuple[str, float, float, float, float]]:
    html = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], check=True,
                          capture_output=True, text=True).stdout
    out = []
    for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
                         r'yMax="([\d.]+)">([^<]*)</word>', html):
        out.append((m.group(5), *map(float, m.groups()[:4])))
    return out


def render(pdf: Path, x0, x1, width, y0=Y0, y1=Y1) -> Image.Image:
    """build_fig1_question.py's render(), with the PDF as an argument (and,
    since v2.2-P, an optional vertical range; the default is the old one)."""
    wpt, hpt = x1 - x0, y1 - y0
    height = round(width * hpt / wpt)
    dpi = 2 * width / wpt * 72
    s = dpi / 72
    with tempfile.TemporaryDirectory() as td:
        stem = Path(td) / "r"
        subprocess.run(["pdftocairo", "-png", "-singlefile", "-r", f"{dpi:.4f}",
                        "-x", str(round(x0 * s)), "-y", str(round(y0 * s)),
                        "-W", str(round(wpt * s)), "-H", str(round(hpt * s)),
                        str(pdf), str(stem)], check=True)
        im = Image.open(str(stem) + ".png").convert("RGB")
        im.load()
    return im.resize((width, height), Image.LANCZOS)


def tight_box(clean: Path) -> tuple[float, float, float, float]:
    """v2.2-P: the tight inference box (x0, x1, y0, y1) in pt, from the ink."""
    x0, x1 = CROPS["infer"]
    width = 2400
    a = np.asarray(render(clean, x0, x1, width).convert("L"))
    k = width / (x1 - x0)
    ink = a < 250
    cols = np.nonzero(ink.any(axis=0))[0]
    runs, start = [], cols[0]
    for c, nxt in zip(cols, list(cols[1:]) + [None]):
        if nxt is None or nxt != c + 1:
            runs.append((int(start), int(c)))
            start = nxt
    assert len(runs) == 4 and runs[0][0] == 0, runs     # arrow, shape, bracket, tiles
    arrow_end = x0 + (runs[0][1] + 1) / k
    shape_start = x0 + runs[1][0] / k
    rows = np.nonzero(ink[:, runs[1][0]:].any(axis=1))[0]
    m = INFER_TIGHT_MARGIN_PT
    box = (round(shape_start - m, 1), x1,
           round(max(Y0, Y0 + rows[0] / k - m), 1),
           round(min(Y1, Y0 + (rows[-1] + 1) / k + m), 1))
    assert box[0] > arrow_end + 2, (box, arrow_end)
    print(f"Tight inference crop (v2.2-P): ink runs in x 2468-3789 pt: "
          + ", ".join(f"{x0 + r0 / k:.1f}-{x0 + (r1 + 1) / k:.1f}" for r0, r1 in runs)
          + f" pt (arrow, shape, bracket, tiles).")
    print(f"  box x {box[0]}-{box[1]}, y {box[2]}-{box[3]} pt; the arrow ends at "
          f"{arrow_end:.1f} pt, {box[0] - arrow_end:.1f} pt left of the box.")
    return box


def acq_box(clean: Path) -> tuple[float, float, float, float]:
    """v2.2-D: the tight acquisition box (x0, x1, y0, y1) in pt, from the ink."""
    bx0, bx1 = 2300, 2700                  # the cube's right side .. past the arrow
    width = 1600                           # 4 px per pt
    rgb = np.asarray(render(clean, bx0, bx1, width)).astype(int)
    k = width / (bx1 - bx0)
    dark = rgb.mean(axis=2) < 60           # cube, arrows, text
    red = (rgb[..., 0] > 150) & (rgb[..., 1] < 90) & (rgb[..., 2] < 90)
    cols = np.nonzero(dark.any(axis=0))[0]
    runs, start = [], cols[0]
    for c, nxt in zip(cols, list(cols[1:]) + [None]):
        if nxt is None or nxt != c + 1:
            runs.append((int(start), int(c)))
            start = nxt
    arrow = runs[-1]
    rows = np.nonzero(dark[:, arrow[0]:arrow[1] + 1].any(axis=1))[0]
    arrow_pt = (bx0 + arrow[0] / k, bx0 + (arrow[1] + 1) / k)
    assert arrow_pt[0] < 2467 < arrow_pt[1] and (rows[-1] - rows[0]) / k < 60, \
        (arrow_pt, rows[[0, -1]] / k)      # it crosses the panel's edge; one arrow tall
    content = np.nonzero((dark | red)[:, :arrow[0]].any(axis=0))[0]
    content_end = bx0 + (content[-1] + 1) / k
    x1 = round(content_end + ACQ_TIGHT_MARGIN_PT, 1)
    assert arrow_pt[0] > x1 + 2, (x1, arrow_pt)
    print(f"Tight acquisition crop (v2.2-D): in x {bx0}-{bx1} pt the dark-ink runs end "
          f"with the arrow, {arrow_pt[0]:.2f}-{arrow_pt[1]:.2f} pt (rows "
          f"{Y0 + rows[0] / k:.1f}-{Y0 + (rows[-1] + 1) / k:.1f} pt); the content left of "
          f"it (cube, red edge) ends at {content_end:.2f} pt.")
    print(f"  box x {CROPS['acq'][0]}-{x1}, y {Y0}-{Y1} pt; the arrow starts "
          f"{arrow_pt[0] - x1:.2f} pt right of the box (v2.2-A's box ended at "
          f"{CROPS['acq'][1]} pt).")
    return CROPS["acq"][0], x1, Y0, Y1


def acq_right_edge(im: Image.Image) -> dict[str, int]:
    """v2.2-D: the tight acquisition crop's right edge (its last two columns)
    may hold only the grey panel: no dark ink (< 100) and no red."""
    a = np.asarray(im.convert("RGB")).astype(int)[:, -2:]
    red = (a[..., 0] > 150) & (a[..., 1] < 90) & (a[..., 2] < 90)
    return {"dark (<100) px": int((a.mean(axis=2) < 100).sum()), "red px": int(red.sum()),
            "lightest-darkest grey": f"{int(a.mean(axis=2).max())}-{int(a.mean(axis=2).min())}"}


def edge_check(im: Image.Image) -> dict[str, int]:
    """Ink pixels (< 250 grey) on each edge: left/top/bottom must be 0."""
    a = np.asarray(im.convert("L")) < 250
    return {"left": int(a[:, :2].sum()), "top": int(a[:2].sum()),
            "bottom": int(a[-2:].sum()), "right": int(a[:, -2:].sum())}


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def save(im: Image.Image, td: Path, base: str, png: bool) -> str:
    im.save(td / f"{base}.webp", "WEBP", quality=WEBP_Q, method=6)
    line = (f"  {base:<28} {im.width:>4} x {im.height:<4} "
            f"webp {(td / f'{base}.webp').stat().st_size:>7,} B")
    if png:
        im.save(td / f"{base}.png", "PNG", optimize=True)
        line += f"   png {(td / f'{base}.png').stat().st_size:>9,} B"
    return line


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not PDF.exists():
        print(f"missing {PDF}")
        return 1

    with tempfile.TemporaryDirectory(prefix="fig1ctx_") as td:
        td = Path(td)
        clean = td / "fig1_context.pdf"
        arrow, span = strip_question(PDF, clean)

        before = words(PDF)
        after = words(clean)
        gone = [w for w in before if w not in after]
        assert [w[0] for w in gone] == QUESTION_WORDS, [w[0] for w in gone]
        assert all(w in before for w in after)
        print(f"Removed content-stream operators {span[0]}-{span[1]} "
              f"(the gold arrow fill and the two question text blocks).")
        print(f"  pdftotext: {len(before)} words before, {len(after)} after; "
              f"removed exactly: {' '.join(w[0] for w in gone)}\n")

        print("Files (built in a temp dir):")
        for base, width, png in FILES:
            print(save(render(clean, *CROPS["whole"], width), td, base, png))

        tb = tight_box(clean)
        for base, width, png in TIGHT_FILES:
            im = render(clean, tb[0], tb[1], width, tb[2], tb[3])
            e = edge_check(im)
            assert e["left"] == 0 and e["top"] == 0 and e["bottom"] == 0, (base, e)
            print(save(im, td, base, png) + f"   edge ink px {e}")
        print("  (left, top and bottom edges hold no ink; the right edge is the "
              "tiles, which run to the figure's edge)")

        ab = acq_box(clean)
        for base, width, png in ACQ_TIGHT_FILES:
            im = render(clean, ab[0], ab[1], width, ab[2], ab[3])
            e = acq_right_edge(im)
            assert e["dark (<100) px"] == 0 and e["red px"] == 0, (base, e)
            print(save(im, td, base, png) + f"   right edge {e}")
        print("  (the right edge cuts the grey panel's fill only: no arrow, no cube; "
              "left edge and vertical range are v2.2-A's)")

        print("\nAgainst the committed files (md5):")
        built = sorted(f for f in td.glob("fig1_context*.*") if f.suffix != ".pdf")
        status = {}
        for f in built:
            dst = OUT / f.name
            status[f.name] = ("NEW" if not dst.exists() else
                              "unchanged" if md5(dst) == md5(f) else "CHANGED")
            print(f"  {f.name:<34} {md5(f)}  {status[f.name]}")
        if "CHANGED" in status.values():
            print("\nFAIL: a committed file would change. Re-cutting a crop means "
                  "a new file name.")
            return 1

        if args.dry_run:
            print("\n--dry-run: nothing copied.")
            return 0
        print("\nCopied into assets/img/ (md5 after the copy):")
        for f in built:
            if status[f.name] != "NEW":
                continue
            dst = OUT / f.name
            shutil.copyfile(f, dst)
            assert md5(dst) == md5(f), f"md5 mismatch after copy: {dst}"
            print(f"  {f.name:<34} {md5(dst)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
