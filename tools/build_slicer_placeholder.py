#!/usr/bin/env python3
"""The cube slicer's placeholder stills — stage v2.1-C, T3.

    python3 tools/build_slicer_placeholder.py

Until js/mars-slicer.js and its data arrive, `/` shows a still of the slicer's
DEFAULT state (the bright-surface preset, 3 x 3 pooling, around the peak)
under the four canvases, so the block is never empty and nothing shifts when
the live module paints over it. The stills are taken FROM THE LIVE MODULE
running on the real data, so they cannot disagree with it:

  assets/img/slicer_ph_{poisson,gold,mars}.webp
        each image canvas's own 128 x 128 pixels (canvas.toDataURL), as
        lossless WebP; the page shows them nearest-neighbour, like the canvas,
        so the swap is pixel-exact.
  assets/img/slicer_ph_chart_960.webp
        the chart canvas at the 960 px column (viewport 1280), device scale 2;
        used above 600 px, where the chart box is 3 : 1.
  assets/img/slicer_ph_chart_390.webp
        the same at a 390 px viewport, device scale 2; used at <= 600 px, where
        the chart box is 16 : 10.
  Between those widths the chart still is scaled to its box, so its text is
  slightly smaller or larger than the live chart's until the module lands
  (v2.1-C measurements.txt reports the difference).

HOW: serves this repo on a free local port, drives real Chrome through
Playwright (headless, the nav hidden so it never covers the canvas), scrolls
to the slicer, waits for data-slicer-state="live" and the webfonts, then
reads the pixels. Re-run it whenever the module's drawing, the data or the
site fonts change. Built in a temp dir outside OneDrive; each file is copied
in once and its md5 checked (WEBSITE_BUILD_STATUS 3.7, v2.1).

Needs: Playwright for Python with Chrome (`channel="chrome"`), Pillow with WebP.
Not a gate (it needs a browser); tools/check_links.py checks the files exist.
"""
from __future__ import annotations

import base64
import functools
import hashlib
import http.server
import io
import shutil
import socket
import sys
import tempfile
import threading
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "assets" / "img"
SHOTS = [("960", 1280, 900), ("390", 390, 844)]   # name, viewport w, h
DPR = 2


def serve():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quiet, directory=str(REPO))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


def live(pg, url):
    pg.goto(url, wait_until="load")
    pg.add_style_tag(content=".mars-nav{visibility:hidden!important}")
    pg.evaluate("document.getElementById('slicer').scrollIntoView({block:'start'})")
    pg.mouse.wheel(0, 40)                       # a real scroll arms the loader
    pg.wait_for_function(
        "document.getElementById('mars-slicer').getAttribute('data-slicer-state')==='live'",
        timeout=30000)
    pg.evaluate("document.fonts.ready.then(()=>1)")
    pg.wait_for_timeout(300)


def main() -> int:
    from playwright.sync_api import sync_playwright
    srv, port = serve()
    url = f"http://127.0.0.1:{port}/index.html"
    with tempfile.TemporaryDirectory(prefix="mars_slicer_ph_") as td, sync_playwright() as p:
        tmp = Path(td)
        b = p.chromium.launch(channel="chrome")
        slices = {}
        for name, w, h in SHOTS:
            ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=DPR)
            pg = ctx.new_page()
            live(pg, url)
            got = pg.evaluate("""() => Array.from(document.querySelectorAll('.mars-slicer__cv'))
                .map(c => [c.dataset.cube, c.toDataURL('image/png')])""")
            for cube, durl in got:
                im = Image.open(io.BytesIO(base64.b64decode(durl.split(",", 1)[1]))).convert("RGB")
                assert im.size == (128, 128), im.size
                if cube in slices:
                    assert slices[cube].tobytes() == im.tobytes(), \
                        f"{cube}: slice differs between viewports"
                slices[cube] = im
            el = pg.locator(".mars-slicer__chartcv")
            box = el.bounding_box()
            png = el.screenshot(type="png")
            im = Image.open(io.BytesIO(png)).convert("RGB")
            im.save(tmp / f"slicer_ph_chart_{name}.webp", "WEBP", quality=90, method=6)
            print(f"  chart {name}: viewport {w}, CSS {box['width']:.1f} x {box['height']:.1f}, "
                  f"image {im.size[0]} x {im.size[1]}")
            ctx.close()
        for cube, im in slices.items():
            im.save(tmp / f"slicer_ph_{cube}.webp", "WEBP", lossless=True, method=6)
        b.close()
        srv.shutdown()

        # lossless round-trip check for the slices
        for cube, im in slices.items():
            back = Image.open(tmp / f"slicer_ph_{cube}.webp").convert("RGB")
            assert back.tobytes() == im.tobytes(), f"{cube}: WebP not lossless"

        for f in sorted(tmp.iterdir()):
            dst = OUT / f.name
            if dst.exists() and dst.read_bytes() == f.read_bytes():
                print(f"  unchanged {dst.relative_to(REPO)}  ({f.stat().st_size:,} B)")
                continue
            shutil.copyfile(f, dst)
            if hashlib.md5(dst.read_bytes()).hexdigest() != hashlib.md5(f.read_bytes()).hexdigest():
                sys.exit(f"FAIL: md5 mismatch after copying {f.name} (OneDrive?)")
            print(f"  wrote     {dst.relative_to(REPO)}  ({f.stat().st_size:,} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
