#!/usr/bin/env python3
"""Fig. 1, top half — "the question" above the teaser on `/` (stage v2.1-A, T3).

    python3 tools/build_fig1_question.py          # write the images, print sizes
    python3 tools/build_fig1_question.py --sizes  # print the text-size table only

The paper's Fig. 1 top half — the SP-LiDAR acquisition process, the 3-D photon
timestamp histogram, data-driven inference of reflectivity and depth, and
"Can we simulate this process? Fast and Precise?" — exported from the vector
`paper/Figs/main/Fig1_teaser.pdf` (read only; nothing in paper/ is touched).
The teaser below it on `/` is the answer, and replaces Fig. 1's bottom row.

DEPENDENCIES: poppler's `pdftocairo` and `pdftotext` on PATH, and Pillow with
WebP support. Standard library otherwise.

WHAT THE PDF CONTAINS (pdfimages -list, pdffonts, and a Ghostscript render
with -dFILTERIMAGE / -dFILTERTEXT -dFILTERVECTOR, v2.1-A measurements.txt):
  * VECTOR: every label (Aptos Display: "Scene", "Laser", "SPAD", "TCSPC",
    "3D Photon Timestamp Histogram", "Reflectivity", "Single Photon LiDAR Data
    Acquisition Process", the question), the grey rounded panel, the arrows,
    the bow-tie network shape, the brace and the x/y/z axes.
  * RASTER (150 ppi JPEG + soft mask): the scene, the laser/SPAD/TCSPC
    drawings, the depth and reflectivity tiles, and THE HISTOGRAM CUBE — its
    red edges are pixels of that image. Per the author (2026-10-26) raster red
    edges stay red, so nothing is recoloured. "Data-Driven Inference" and
    "Depth" are raster text too (a 60 ppi image over the vector bow-tie).

THE CROPS are boxes in PDF points (top-left origin, as pdftotext reports),
found as the non-white bounding box of the top half (rows 11-983 pt; the
bottom half starts at 1099 pt):
  whole  x 21-3789   the desktop image, 1920 and 960 px wide (>= 601 px)
  acq    x 21-2467   phones (<= 600 px), first: the grey acquisition panel
  infer  x 2468-3789 phones, second: inference, outputs, the question. It
         starts at the panel's right edge, so the black arrow's first 17 pt,
         drawn over the panel, stay with the panel crop.
Each image is rendered at twice its output width and downsampled (Lanczos),
then written as WebP (q 82); the largest image of each crop also as the PNG
that index.html names for a browser without WebP.

TEXT SIZE ON SCREEN. A label's CSS font-size equivalent is its PDF size in pt
x (displayed px per pt). PDF size = pdftotext bbox height / 1.221, Aptos'
ascent - descent per em (FontDescriptor 939 / -282). --sizes prints the
table for the columns that matter, and the column each label needs for 10 px.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
PDF = REPO.parent.parent / "paper" / "Figs" / "main" / "Fig1_teaser.pdf"
OUT = REPO / "assets" / "img"

Y0, Y1 = 11, 984                         # the top half, in pt
CROPS = {                                 # name: (x0, x1) in pt
    "whole": (21, 3789),
    "acq": (21, 2467),
    "infer": (2468, 3789),
}
FILES = [                                 # (crop, basename, width px, PNG too?)
    ("whole", "fig1_question", 1920, True),
    ("whole", "fig1_question_960", 960, False),
    ("acq", "fig1_question_acq", 1200, True),
    ("acq", "fig1_question_acq_600", 600, False),
    ("infer", "fig1_question_infer", 1200, True),
    ("infer", "fig1_question_infer_600", 600, False),
]
ASC_DESC = 1.221                          # Aptos Display, (939 + 282) / 1000
WEBP_Q = 82
# Text that is pixels, not glyphs: size equivalent from its cap height
# (measured at 144 dpi; Aptos cap height 0.657 em) — v2.1-A measurements.txt.
RASTER_TEXT = [("Data-Driven Inference", 2890, 68.0), ("Depth", 3600, 66.0)]


def render(x0, x1, width):
    """Render the crop at 2x `width`, then downsample to `width` exactly."""
    wpt, hpt = x1 - x0, Y1 - Y0
    height = round(width * hpt / wpt)
    dpi = 2 * width / wpt * 72
    s = dpi / 72
    with tempfile.TemporaryDirectory() as td:
        stem = Path(td) / "r"
        subprocess.run(["pdftocairo", "-png", "-singlefile", "-r", f"{dpi:.4f}",
                        "-x", str(round(x0 * s)), "-y", str(round(Y0 * s)),
                        "-W", str(round(wpt * s)), "-H", str(round(hpt * s)),
                        str(PDF), str(stem)], check=True)
        im = Image.open(str(stem) + ".png").convert("RGB")
        im.load()
    return im.resize((width, height), Image.LANCZOS)


def words():
    """(text, x_center_pt, size_pt) for every vector word in the top half."""
    html = subprocess.run(["pdftotext", "-bbox", str(PDF), "-"], check=True,
                          capture_output=True, text=True).stdout
    out = []
    for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" '
                         r'yMax="([\d.]+)">([^<]*)</word>', html):
        x0, y0, x1, y1 = map(float, m.groups()[:4])
        if y1 <= Y1:
            out.append((m.group(5), (x0 + x1) / 2, (y1 - y0) / ASC_DESC))
    return out


def size_table():
    ws = words() + [(t, x, s) for t, x, s in RASTER_TEXT]
    cols = [("375 phone", 343, "acq/infer"), ("390 phone", 358, "acq/infer"),
            ("600", 568, "acq/infer"), ("601", 569, "whole"),
            ("768", 736, "whole"), ("960 desktop", 960, "whole")]
    print("Smallest text on screen, CSS px (= pt x displayed px / crop pt):")
    for crop in ("whole", "acq", "infer"):
        x0, x1 = CROPS[crop]
        inside = [w for w in ws if x0 <= w[1] <= x1]
        smallest = min(s for _, _, s in inside)
        labels = sorted({round(s, 1) for _, _, s in inside})
        print(f"  {crop:<6} {x1 - x0:>5} pt wide; text sizes {labels} pt; "
              f"smallest {smallest:.1f} pt")
        for name, colw, which in cols:
            if crop in which.split("/"):
                k = colw / (x1 - x0)
                print(f"      {name:<12} column {colw:>4} px: smallest "
                      f"{smallest * k:5.1f} px; 66.1 pt labels {66.1 * k:5.1f} px")
        print(f"      10 px needs a column of {10 / smallest * (x1 - x0):.0f} px "
              f"(smallest), {10 / 66.1 * (x1 - x0):.0f} px (66.1 pt labels)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sizes", action="store_true")
    args = ap.parse_args()
    if not PDF.exists():
        print(f"missing {PDF}")
        return 1
    if not args.sizes:
        for crop, base, width, png in FILES:
            im = render(*CROPS[crop], width)
            im.save(OUT / f"{base}.webp", "WEBP", quality=WEBP_Q, method=6)
            line = (f"  {base:<26} {im.width} x {im.height}   "
                    f"webp {(OUT / f'{base}.webp').stat().st_size:>8,} B")
            if png:
                im.save(OUT / f"{base}.png", "PNG", optimize=True)
                line += f"   png {(OUT / f'{base}.png').stat().st_size:>9,} B"
            print(line)
    size_table()
    return 0


if __name__ == "__main__":
    sys.exit(main())
