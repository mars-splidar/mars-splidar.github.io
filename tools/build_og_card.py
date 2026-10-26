#!/usr/bin/env python3
"""Build the Open Graph / Twitter share card, assets/img/og_card.{png,webp} — stage 10b.

    python tools/build_og_card.py            # writes both files
    python tools/build_og_card.py --check    # writes nothing; exit 1 if the committed card differs

WHY THIS REPLACES build_web_assets.py's card. The v1 card letterboxed the poster's
`f1_tradeoff` art, which burns in 0.2 / 16.1 / 0.3 s per cube — while the og:/twitter:
description beside it says "40x faster for a 128x128x1024 cube". Two different experiments,
shown together on every share with nothing saying so. This card carries NO timing and NO
speed number at all: the paper's title, "ECCV 2026", the teaser's own frame 0
(assets/media/anim_hero_cubes.jpg — the paper's Fig. 1 cubes, gold edges, one tone curve)
and the three simulator names with the site's label-row words, which carry no number.

HOW. A tiny HTML page using the site's own self-hosted fonts and colour tokens is rendered
at 1200 x 630 by headless Google Chrome (`--screenshot`), so the type is exactly the
site's. Pillow then writes the optimised PNG (what the meta tags point at — several
crawlers still do not decode WebP cards) and a WebP twin. Needs: google-chrome on PATH
(or $CHROME), Pillow.
"""
import argparse, hashlib, os, shutil, subprocess, sys, tempfile
from pathlib import Path

from PIL import Image, ImageChops

REPO = Path(__file__).resolve().parent.parent
OUT_PNG = REPO / "assets/img/og_card.png"
OUT_WEBP = REPO / "assets/img/og_card.webp"
POSTER = REPO / "assets/media/anim_hero_cubes.jpg"
FONTS = REPO / "assets/fonts"
W, H = 1200, 630

# Tokens copied from css/mars.css :root (WEBSITE_BUILD_STATUS 3.6). GOLD is never text.
PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: "Poppins"; font-weight: 400; src: url("{fonts}/poppins-400-latin.woff2") format("woff2"); }}
@font-face {{ font-family: "Poppins"; font-weight: 500; src: url("{fonts}/poppins-500-latin.woff2") format("woff2"); }}
@font-face {{ font-family: "Poppins"; font-weight: 600; src: url("{fonts}/poppins-600-latin.woff2") format("woff2"); }}
@font-face {{ font-family: "Inter"; font-weight: 400 600; src: url("{fonts}/inter-latin.woff2") format("woff2"); }}
:root {{ --aged: #8E6F3E; --dark: #1F1F1F; --green: #0E7A46; --grey: #5A5A5A; --paper: #FAFBFA; }}
html, body {{ margin: 0; width: {w}px; height: {h}px; background: var(--paper); overflow: hidden; }}
body {{ display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-family: Inter, sans-serif; color: var(--dark); }}
.badge {{ background: var(--aged); color: #fff; font: 600 17px Poppins; letter-spacing: 0.03em;
          padding: 6px 18px; border-radius: 999px; }}
h1 {{ font: 400 40px Poppins; letter-spacing: -0.02em; margin: 22px 0 18px; white-space: nowrap; }}
.hl {{ color: var(--aged); font-weight: 500; }}
img {{ width: 1100px; height: auto; display: block; }}
dl {{ display: grid; grid-template-columns: repeat(3, 1fr); width: 1100px; margin: 8px 0 0; text-align: center; }}
dt {{ font: 600 22px Poppins; }}
dt.ours {{ color: var(--green); }}
dd {{ margin: 2px 0 0; font: 400 17px Inter; color: var(--grey); }}
</style></head><body>
<div class="badge">ECCV 2026</div>
<h1><span class="hl">MaRS</span>: <span class="hl">Ma</span>rkov-<span class="hl">R</span>enewal Single-Photon LiDAR <span class="hl">S</span>imulator</h1>
<img src="{poster}" alt="">
<dl>
  <div><dt>Poisson</dt><dd>fast &middot; ignores dead time</dd></div>
  <div><dt>Sequential gold standard</dt><dd>correct &middot; the reference</dd></div>
  <div><dt class="ours">MaRS</dt><dd>correct and fast</dd></div>
</dl>
</body></html>"""


def chrome() -> str:
    for c in (os.environ.get("CHROME"), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if c and shutil.which(c):
            return shutil.which(c)
    sys.exit("ERROR: no Chrome/Chromium found (set $CHROME)")


def render() -> Image.Image:
    with tempfile.TemporaryDirectory() as td:
        page = Path(td) / "card.html"
        page.write_text(PAGE.format(w=W, h=H, fonts=FONTS.as_uri(), poster=POSTER.as_uri()), encoding="utf-8")
        shot = Path(td) / "card.png"
        subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--allow-file-access-from-files",
                        f"--window-size={W},{H}", "--virtual-time-budget=5000",
                        f"--screenshot={shot}", page.as_uri()],
                       check=True, capture_output=True, timeout=120)
        with Image.open(shot) as im:
            im = im.convert("RGB")
            if im.size != (W, H):
                sys.exit(f"ERROR: screenshot is {im.size}, expected {(W, H)}")
            return im.copy()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="write nothing; compare with the committed card")
    args = ap.parse_args()
    card = render()
    if args.check:
        if not OUT_PNG.exists():
            print("FAIL: assets/img/og_card.png missing"); return 1
        with Image.open(OUT_PNG) as cur:
            diff = ImageChops.difference(cur.convert("RGB"), card)
            worst = max(hi for _, hi in diff.getextrema())
        # rasterisation may differ by a level or two between Chrome versions; layout may not
        ok = worst <= 24 and sum(1 for px in diff.getdata() if max(px) > 24) == 0
        print(f"og_card.png vs a fresh render: max channel difference {worst} -> {'OK' if ok else 'DRIFT'}")
        return 0 if ok else 1
    card.save(OUT_PNG, "PNG", optimize=True)
    card.save(OUT_WEBP, "WEBP", quality=85, method=6)
    for p in (OUT_PNG, OUT_WEBP):
        print(f"wrote {p.relative_to(REPO)}  {W}x{H}  {p.stat().st_size:,} B  md5 {hashlib.md5(p.read_bytes()).hexdigest()[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
