#!/usr/bin/env python3
"""Build web-ready assets for the MaRS project site.

Reads source graphics and documents from the OneDrive project folder (which is
NEVER modified) and writes web-optimised copies into `assets/img/` and
`assets/docs/`.

Re-runnable and idempotent: running it twice produces byte-identical outputs
(modulo PDF timestamps, see `--force`). Prints a table of everything it wrote
and exits non-zero if a source is missing.

Usage:
    python tools/build_web_assets.py [--force] [--skip-pdf] [--skip-video]

Source of truth for the source list: `build_instructions/stage_01_foundation.md`
section 3.3.  Canonical poster-graphic directory is `poster&slides/assets/`.
`poster&slides/MaRS_poster_v2_bundle/` is a stale duplicate and is never read.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required:  python -m pip install Pillow")

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
PROJECT = REPO.parent.parent                     # .../MaRS_presentations
POSTER_ASSETS = PROJECT / "poster&slides" / "assets"
IMG_OUT = REPO / "assets" / "img"
DOC_OUT = REPO / "assets" / "docs"

WEBP_QUALITY = 85
OG_SIZE = (1200, 630)
PAPER_RGB = (0xFA, 0xFB, 0xFA)                   # PAPER #FAFBFA

# --------------------------------------------------------------------------
# Image jobs:  (source basename, output basename, mode, size)
#   mode "w"      -> scale to max width, preserve aspect, never upscale
#   mode "square" -> resize to exactly (size, size)
# --------------------------------------------------------------------------

IMAGE_JOBS: list[tuple[str, str, str, int]] = [
    ("f1_tradeoff.png",     "hook_tradeoff",       "w", 1600),
    ("f2_decouple.png",     "approach_decouple",   "w", 1600),
    ("f3_mrp.png",          "theory_mrp",          "w", 1600),
    ("f4a_covdecay.png",    "theory_covdecay",     "w", 1400),
    ("f4b_accuracy.png",    "theory_covaccuracy",  "w", 1400),
    ("f5_count.png",        "theory_count",        "w", 1600),
    ("f6_runtime.png",      "sim_runtime",         "w", 1600),
    ("f6_pixels.png",       "sim_pixels",          "w", 1400),
    ("f_real.png",          "theory_real",         "w", 1600),
    ("g_clt.png",           "theory_clt",          "w", 1600),
    ("g_lut.png",           "sim_lut",             "w", 1600),
    ("g_alg.png",           "sim_alg",             "w", 1600),
]

# Result tiles are normalised to one square size so the reflectivity set
# (721 px, and three tiles that are 713-714 px wide) and the depth set
# (900 px) line up in a side-by-side or wipe component.  GAP_REPORT.md #4.
for _v in ("gt", "poisson", "renewal", "zhang", "mars"):
    IMAGE_JOBS.append((f"f7_{_v}.png",  f"res_refl_{_v}",  "square", 720))
    IMAGE_JOBS.append((f"f7d_{_v}.png", f"res_depth_{_v}", "square", 720))

for _i in ("accuracy", "table", "speed", "downstream"):
    IMAGE_JOBS.append((f"icon_{_i}.png", f"icon_{_i}", "w", 240))

# Deliberately NOT converted: g_table.png, g_capability.png, g_transfer.png.
# Those three are PNG pictures of data tables; stage 02 rebuilds them as real
# HTML tables inside `.mars-table-wrap` containers.  GAP_REPORT.md #17.

# --------------------------------------------------------------------------


class Missing(Exception):
    pass


def _need(path: Path) -> Path:
    if not path.exists():
        raise Missing(str(path))
    return path


def _size_str(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / 1024 / 1024:.2f} MB"


def build_images(rows: list[list[str]], force: bool) -> None:
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    for src_name, out_base, mode, size in IMAGE_JOBS:
        src = _need(POSTER_ASSETS / src_name)
        png_out = IMG_OUT / f"{out_base}.png"
        webp_out = IMG_OUT / f"{out_base}.webp"

        if not force and png_out.exists() and webp_out.exists() \
                and png_out.stat().st_mtime >= src.stat().st_mtime \
                and webp_out.stat().st_mtime >= src.stat().st_mtime:
            with Image.open(png_out) as done:
                out_size = done.size
            rows.append([src_name, f"{out_base}.{{png,webp}}", "cached",
                         f"{out_size[0]}x{out_size[1]}",
                         f"{_size_str(png_out.stat().st_size)} / "
                         f"{_size_str(webp_out.stat().st_size)}"])
            continue

        with Image.open(src) as im:
            src_size = im.size
            has_alpha = im.mode in ("RGBA", "LA", "P") and "transparency" in im.info \
                or im.mode in ("RGBA", "LA")
            im = im.convert("RGBA" if has_alpha else "RGB")

            if mode == "square":
                target = (size, size)
            else:
                w, h = im.size
                if w <= size:                      # never upscale
                    target = (w, h)
                else:
                    target = (size, max(1, round(h * size / w)))

            out = im if target == im.size else im.resize(target, Image.LANCZOS)
            out.save(png_out, "PNG", optimize=True)
            out.save(webp_out, "WEBP", quality=WEBP_QUALITY, method=6)

        rows.append([src_name, f"{out_base}.{{png,webp}}",
                     f"{src_size[0]}x{src_size[1]}",
                     f"{target[0]}x{target[1]}",
                     f"{_size_str(png_out.stat().st_size)} / "
                     f"{_size_str(webp_out.stat().st_size)}"])


def build_og_card(rows: list[list[str]], force: bool) -> None:
    """Letterbox the three-cube hook onto a PAPER field at 1200x630."""
    src = _need(POSTER_ASSETS / "f1_tradeoff.png")
    out = IMG_OUT / "og_card.png"
    twin = IMG_OUT / "og_card.webp"
    if not force and out.exists() and twin.exists() \
            and out.stat().st_mtime >= src.stat().st_mtime:
        rows.append(["f1_tradeoff.png", "og_card.{png,webp}", "cached",
                     "1200x630",
                     _size_str(out.stat().st_size) + " / " +
                     _size_str(twin.stat().st_size)])
        return

    with Image.open(src) as im:
        im = im.convert("RGB")
        src_size = im.size
        scale = min(OG_SIZE[0] / im.width, OG_SIZE[1] / im.height)
        fitted = im.resize((max(1, round(im.width * scale)),
                            max(1, round(im.height * scale))), Image.LANCZOS)
    card = Image.new("RGB", OG_SIZE, PAPER_RGB)
    card.paste(fitted, ((OG_SIZE[0] - fitted.width) // 2,
                        (OG_SIZE[1] - fitted.height) // 2))
    card.save(out, "PNG", optimize=True)
    # A .webp twin is written for format parity with every other image, but
    # the og: and twitter: meta tags point at the PNG ON PURPOSE — several
    # social crawlers still do not decode WebP card images.
    card.save(IMG_OUT / "og_card.webp", "WEBP", quality=WEBP_QUALITY, method=6)
    rows.append(["f1_tradeoff.png", "og_card.{png,webp}",
                 f"{src_size[0]}x{src_size[1]}", "1200x630",
                 _size_str(out.stat().st_size) + " / " +
                 _size_str((IMG_OUT / "og_card.webp").stat().st_size)])


def _gs_downsample(src: Path, dst: Path, dpi: int) -> bool:
    gs = shutil.which("gs")
    if gs is None:
        return False
    cmd = [
        gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
        "-dNOPAUSE", "-dBATCH", "-dQUIET", "-dSAFER",
        "-dDetectDuplicateImages=true",
        "-dDownsampleColorImages=true", "-dColorImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={dpi}",
        "-dDownsampleGrayImages=true", "-dGrayImageDownsampleType=/Bicubic",
        f"-dGrayImageResolution={dpi}",
        "-dDownsampleMonoImages=true", "-dMonoImageDownsampleType=/Subsample",
        f"-dMonoImageResolution={dpi * 4}",
        "-dAutoFilterColorImages=false", "-dColorImageFilter=/DCTEncode",
        "-dAutoFilterGrayImages=false", "-dGrayImageFilter=/DCTEncode",
        f"-sOutputFile={dst}", str(src),
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def build_docs(rows: list[list[str]], notes: list[str],
               force: bool, skip_pdf: bool, skip_video: bool) -> None:
    DOC_OUT.mkdir(parents=True, exist_ok=True)

    # ---- poster --------------------------------------------------------
    poster = _need(PROJECT / "poster&slides" / "ECCV_poster_Weijian.pdf")
    full = DOC_OUT / "mars_poster_full.pdf"
    web = DOC_OUT / "mars_poster_web.pdf"

    if force or not full.exists() or full.stat().st_size != poster.stat().st_size:
        shutil.copy2(poster, full)
    rows.append(["ECCV_poster_Weijian.pdf", "mars_poster_full.pdf", "—", "—",
                 _size_str(full.stat().st_size)])

    if skip_pdf and web.exists():
        rows.append(["ECCV_poster_Weijian.pdf", "mars_poster_web.pdf", "—",
                     "150 dpi", f"{_size_str(web.stat().st_size)} (skipped)"])
    elif force or not web.exists():
        ok = _gs_downsample(poster, web, 150)
        if not ok:
            notes.append(
                "WARNING: ghostscript not available or failed. No downsampled "
                "poster was produced. Point the Poster button at "
                "mars_poster_full.pdf and label its size (16 MB) in the button."
            )
            if web.exists():
                web.unlink()
        else:
            rows.append(["ECCV_poster_Weijian.pdf", "mars_poster_web.pdf", "—",
                         "150 dpi", _size_str(web.stat().st_size)])
            if web.stat().st_size > 4 * 1024 * 1024:
                notes.append(
                    f"WARNING: mars_poster_web.pdf is "
                    f"{_size_str(web.stat().st_size)}, over the 4 MB target."
                )
    else:
        rows.append(["ECCV_poster_Weijian.pdf", "mars_poster_web.pdf", "—",
                     "150 dpi", f"{_size_str(web.stat().st_size)} (cached)"])

    # ---- paper ---------------------------------------------------------
    paper_src = PROJECT / "paper" / "main.pdf"
    paper_out = DOC_OUT / "mars_paper.pdf"
    if paper_src.exists():
        if force or not paper_out.exists() \
                or paper_out.stat().st_size != paper_src.stat().st_size:
            shutil.copy2(paper_src, paper_out)
        rows.append(["paper/main.pdf", "mars_paper.pdf", "—", "—",
                     _size_str(paper_out.stat().st_size)])
        notes.append(
            "paper/main.pdf FOUND and copied. Set "
            '`paperPdf: "assets/docs/mars_paper.pdf"` in js/site.config.js.'
        )
    else:
        if paper_out.exists():
            paper_out.unlink()
        notes.append(
            "WARNING: paper/main.pdf is ABSENT. No assets/docs/mars_paper.pdf "
            "was written. `paperPdf` must stay `null` in js/site.config.js so "
            "the Paper button renders as `Paper · soon` rather than a dead link."
        )

    # ---- video ---------------------------------------------------------
    vid_src = _need(PROJECT / "video" / "out" / "MaRS_ECCV2026_5min.mp4")
    srt_src = _need(PROJECT / "video" / "out" / "MaRS_ECCV2026_5min.srt")
    vid_out = DOC_OUT / "mars_5min.mp4"
    srt_out = DOC_OUT / "mars_5min.srt"

    if skip_video and vid_out.exists():
        rows.append(["MaRS_ECCV2026_5min.mp4", "mars_5min.mp4", "—", "—",
                     f"{_size_str(vid_out.stat().st_size)} (skipped)"])
    else:
        if force or not vid_out.exists() \
                or vid_out.stat().st_size != vid_src.stat().st_size:
            shutil.copy2(vid_src, vid_out)
        rows.append(["MaRS_ECCV2026_5min.mp4", "mars_5min.mp4", "—", "—",
                     _size_str(vid_out.stat().st_size)])

    if force or not srt_out.exists() \
            or srt_out.stat().st_size != srt_src.stat().st_size:
        shutil.copy2(srt_src, srt_out)
    rows.append(["MaRS_ECCV2026_5min.srt", "mars_5min.srt", "—", "—",
                 _size_str(srt_out.stat().st_size)])


def _print_table(rows: list[list[str]]) -> None:
    head = ["source", "output", "source px", "output px", "output bytes"]
    widths = [max(len(head[i]), *(len(r[i]) for r in rows)) for i in range(5)] \
        if rows else [len(h) for h in head]
    line = "  ".join(h.ljust(w) for h, w in zip(head, widths))
    print(line)
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                    help="rebuild every output even if it looks current")
    ap.add_argument("--skip-pdf", action="store_true",
                    help="reuse an existing downsampled poster (ghostscript is slow)")
    ap.add_argument("--skip-video", action="store_true",
                    help="reuse an existing copy of the 25 MB overview video")
    args = ap.parse_args()

    print(f"project source : {PROJECT}")
    print(f"poster assets  : {POSTER_ASSETS}")
    print(f"site repo      : {REPO}")
    print("(source assets are read-only and are never modified)\n")

    rows: list[list[str]] = []
    notes: list[str] = []
    try:
        build_images(rows, args.force)
        build_og_card(rows, args.force)
        build_docs(rows, notes, args.force, args.skip_pdf, args.skip_video)
    except Missing as exc:
        print(f"\nERROR: missing source asset: {exc}", file=sys.stderr)
        return 1

    _print_table(rows)

    total = sum(p.stat().st_size for p in
                list(IMG_OUT.glob("*")) + list(DOC_OUT.glob("*")) if p.is_file())
    print(f"\n{len(rows)} jobs. assets/img + assets/docs total: {_size_str(total)}")

    if notes:
        print()
        for n in notes:
            print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
