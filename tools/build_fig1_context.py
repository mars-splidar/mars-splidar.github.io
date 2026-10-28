#!/usr/bin/env python3
"""Fig. 1, top half WITHOUT the question — the In short band on `/` (stage v2.2-A, T4).

    python tools/build_fig1_context.py            # build, diff, copy into assets/img/
    python tools/build_fig1_context.py --dry-run  # build and diff only, write nothing

v2.1 showed the paper's Fig. 1 top half above the teaser as "the question",
ending in "Can we simulate this process? Fast and Precise?" and a yellow arrow
pointing at it (tools/build_fig1_question.py, files fig1_question*). In v2.2 the
figure moves below the demos as context (guide 0.7), so those two elements go.

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

RENDERING is build_fig1_question.py's pipeline, unchanged (pdftocairo at 2x
the output width, Lanczos down to the output width, WebP q 82, the largest
image of each crop also as PNG), on the same crop boxes:
  whole  x 21-3789 pt   fig1_context (1920, + PNG), fig1_context_960
  acq    x 21-2467 pt   fig1_context_acq (1200, + PNG), _acq_600
  infer  x 2468-3789 pt fig1_context_infer (1200, + PNG), _infer_600
The acquisition crop does not reach the arrow (it starts at x 2488.65 pt), so
its files come out byte-identical to the fig1_question_acq* ones; they are
written under the new name so v2.2-D can retire fig1_question* as a set. The
inference crop is rendered exactly as before and THEN trimmed in pixel space
below its lowest remaining ink (the depth tile), so every pixel it keeps is a
pixel of the old export, and the phone does not scroll past a blank block.

THE DIFF (written to stdout; the stage keeps it as fig1_diff.txt). For each
PNG: (1) the ORIGINAL PDF re-rendered through this pipeline vs the committed
fig1_question*.png, which shows the pipeline is deterministic here; (2) the
new image vs the committed fig1_question*.png, counting changed pixels inside
the removed region (the arrow's and the question's bounding boxes, in px,
grown by LANCZOS_PAD px for the 3-lobe filter's reach) and outside it. Outside
must be 0. WebP is lossy and block-coded, so only PNGs are compared.

OUTPUT FILES are built in a temp dir outside OneDrive and copied into
assets/img/ once each, with the md5 checked after the copy (WEBSITE_BUILD_STATUS
3.7, the OneDrive write rule). The fig1_question* files are read, never written.

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

# Same constants as tools/build_fig1_question.py — the two must agree.
Y0, Y1 = 11, 984
CROPS = {"whole": (21, 3789), "acq": (21, 2467), "infer": (2468, 3789)}
WEBP_Q = 82
FILES = [                     # (crop, new basename, old basename, width, PNG?)
    ("whole", "fig1_context", "fig1_question", 1920, True),
    ("whole", "fig1_context_960", "fig1_question_960", 960, False),
    ("acq", "fig1_context_acq", "fig1_question_acq", 1200, True),
    ("acq", "fig1_context_acq_600", "fig1_question_acq_600", 600, False),
    ("infer", "fig1_context_infer", "fig1_question_infer", 1200, True),
    ("infer", "fig1_context_infer_600", "fig1_question_infer_600", 600, False),
]

GOLD = (Decimal("0.823529"), Decimal("0.627451"), Decimal("0"))
QUESTION_ORIGINS = [(2718.77, -867.654), (2894.95, -954.054)]   # the two cm e, f
QUESTION_WORDS = ["Can", "we", "simulate", "this", "process?", "Fast", "and",
                  "Precise?"]
PAGE_H = 2157                 # MediaBox height, pt: user space is y-up
LANCZOS_PAD = 3               # output px; Lanczos-3 at a 2x downsample reaches 3
INFER_MARGIN_PT = 12          # white kept under the depth tile's lowest ink


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


def render(pdf: Path, x0, x1, width) -> Image.Image:
    """build_fig1_question.py's render(), with the PDF as an argument."""
    wpt, hpt = x1 - x0, Y1 - Y0
    height = round(width * hpt / wpt)
    dpi = 2 * width / wpt * 72
    s = dpi / 72
    with tempfile.TemporaryDirectory() as td:
        stem = Path(td) / "r"
        subprocess.run(["pdftocairo", "-png", "-singlefile", "-r", f"{dpi:.4f}",
                        "-x", str(round(x0 * s)), "-y", str(round(Y0 * s)),
                        "-W", str(round(wpt * s)), "-H", str(round(hpt * s)),
                        str(pdf), str(stem)], check=True)
        im = Image.open(str(stem) + ".png").convert("RGB")
        im.load()
    return im.resize((width, height), Image.LANCZOS)


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not PDF.exists():
        print(f"missing {PDF}")
        return 1
    old_md5 = {p.name: md5(p) for p in sorted(OUT.glob("fig1_question*"))}

    with tempfile.TemporaryDirectory(prefix="fig1ctx_") as td:
        td = Path(td)
        clean = td / "fig1_context.pdf"
        arrow, span = strip_question(PDF, clean)

        before = words(PDF)
        after = words(clean)
        gone = [w for w in before if w not in after]
        assert [w[0] for w in gone] == QUESTION_WORDS, [w[0] for w in gone]
        assert all(w in before for w in after)
        q = [min(w[1] for w in gone), min(w[2] for w in gone),
             max(w[3] for w in gone), max(w[4] for w in gone)]
        print(f"Removed content-stream operators {span[0]}-{span[1]} "
              f"(the gold arrow fill and the two question text blocks).")
        print(f"  arrow    bbox x {arrow[0]:.2f}-{arrow[2]:.2f}, "
              f"y {arrow[1]:.2f}-{arrow[3]:.2f} pt (top-left origin)")
        print(f"  question bbox x {q[0]:.2f}-{q[2]:.2f}, y {q[1]:.2f}-{q[3]:.2f} pt "
              f"(pdftotext word boxes)")
        print(f"  pdftotext: {len(before)} words before, {len(after)} after; "
              f"removed exactly: {' '.join(w[0] for w in gone)}\n")

        # The infer crop's trim row: lowest ink once the question is gone.
        infer_full = render(clean, *CROPS["infer"], 1200)
        a = np.asarray(infer_full.convert("L"))
        ink_rows = np.nonzero((a < 250).any(axis=1))[0]
        k = 1200 / (CROPS["infer"][1] - CROPS["infer"][0])
        trim1200 = min(a.shape[0], int(ink_rows[-1]) + 1 + round(INFER_MARGIN_PT * k))

        built = {}
        print("Files (built in a temp dir):")
        for crop, base, old, width, png in FILES:
            im = render(clean, *CROPS[crop], width)
            if crop == "infer":
                im = im.crop((0, 0, im.width, round(trim1200 * width / 1200)))
            im.save(td / f"{base}.webp", "WEBP", quality=WEBP_Q, method=6)
            built[base] = (im, crop, old, width, png)
            line = (f"  {base:<24} {im.width:>4} x {im.height:<4} "
                    f"webp {(td / f'{base}.webp').stat().st_size:>7,} B")
            if png:
                im.save(td / f"{base}.png", "PNG", optimize=True)
                line += f"   png {(td / f'{base}.png').stat().st_size:>9,} B"
            print(line)

        print("\nPixel diff, PNG only (WebP is lossy). Region = the arrow's and the "
              f"question's boxes in px, grown by {LANCZOS_PAD} px.")
        ok = True
        for base, (im, crop, old, width, png) in built.items():
            if not png:
                continue
            x0, x1 = CROPS[crop]
            sc = width / (x1 - x0)
            ref = np.asarray(Image.open(OUT / f"{old}.png").convert("RGB")).astype(int)
            redo = np.asarray(render(PDF, x0, x1, width)).astype(int)
            new = np.asarray(im).astype(int)
            h = new.shape[0]
            same_pipe = int((redo != ref).any(axis=2).sum())
            mask = np.zeros(ref.shape[:2], bool)
            for bx in (arrow, q):
                c0 = max(0, int(np.floor((bx[0] - x0) * sc)) - LANCZOS_PAD)
                c1 = min(mask.shape[1], int(np.ceil((bx[2] - x0) * sc)) + LANCZOS_PAD)
                r0 = max(0, int(np.floor((bx[1] - Y0) * sc)) - LANCZOS_PAD)
                r1 = min(mask.shape[0], int(np.ceil((bx[3] - Y0) * sc)) + LANCZOS_PAD)
                if c0 < c1 and r0 < r1:
                    mask[r0:r1, c0:c1] = True
            diff = (new != ref[:h]).any(axis=2)
            inside = int((diff & mask[:h]).sum())
            outside = int((diff & ~mask[:h]).sum())
            region = int(mask.sum())
            ok &= outside == 0 and same_pipe == 0
            print(f"  {base}.png vs {old}.png ({ref.shape[1]} x {ref.shape[0]}"
                  + (f", compared on the kept top {h} rows" if h != ref.shape[0] else "")
                  + f"): re-render of the original = committed: "
                  f"{same_pipe} px differ; new vs committed: {inside} px changed "
                  f"inside the region ({region} px), {outside} OUTSIDE")
            if h != ref.shape[0]:
                cut = ref[h:]
                print(f"      rows {h}-{ref.shape[0] - 1} trimmed; their only ink in "
                      f"the old export is the question: "
                      f"{int(((cut < 250).any(axis=2) & ~mask[h:]).sum())} ink px "
                      f"outside the region")
        if not ok:
            print("\nFAIL — a pixel outside the removed region changed, or the "
                  "pipeline does not reproduce the committed export.")
            return 1

        if args.dry_run:
            print("\n--dry-run: nothing copied.")
            return 0
        print("\nCopied into assets/img/ (md5 after the copy):")
        for f in sorted(td.glob("fig1_context*.*")):
            if f.suffix == ".pdf":
                continue
            dst = OUT / f.name
            shutil.copyfile(f, dst)
            assert md5(dst) == md5(f), f"md5 mismatch after copy: {dst}"
            print(f"  {f.name:<30} {md5(dst)}")

    after_md5 = {p.name: md5(p) for p in sorted(OUT.glob("fig1_question*"))}
    assert after_md5 == old_md5, "a fig1_question* file changed"
    print(f"\nfig1_question*: {len(old_md5)} files, md5 unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
