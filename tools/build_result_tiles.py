#!/usr/bin/env python3
"""Every result tile on `/` — stage v2.3-B, T1 (guide 0.8, "Result images").

    python3 tools/build_result_tiles.py           # build in a temp dir, copy in
    python3 tools/build_result_tiles.py --check   # writes nothing; the gate form

Writes `assets/img/res/`:

  {refl,depth}_{sbr06,sbr10}_{gt,poisson,renewal,zhang,mars}.webp
        20 tiles, 200 x 200, lossless WebP, RGB. sbr06 is the SBR 0.6 test
        scene (library, sample 00357), sbr10 the SBR 1.0 one (kitchen, 00767).
  provenance.json
        source paths and sha256, the tile and crop boxes, the depth ranges and
        clip fractions, the colormap, this generator's version, the Pillow /
        libwebp / numpy versions, and the sha256 of every output.

SOURCES (READ ONLY; WEBSITE_BUILD_STATUS 3.7, v2.3 amendments — nothing is
ever written under ~/OneDrive/MaRS/):

  depth   ~/OneDrive/MaRS/Figs/main/downstream_visuals/depth_visuals_eccv2026/
          sbr0.6_00357/ and sbr1.0_00767/, one folder per training simulator:
          poisson, renewal, icip (= Zhang et al.), ours (= MaRS). Each holds
          *_pred.npz and *_gt.npz with a 200 x 200 float32 `depth` map in
          metres: the network's native output, so no crop and no resize. The
          four *_gt.npz of a scene must hold the same array.
  refl    ~/OneDrive/MaRS/Figs/main/mars_cvpr2026-Page-1.drawio.png, 2565 x
          1028 RGBA, lossless: the image paper/Figs/main/
          Fig7_reflectivity_visual_results.pdf embeds. No native reflectivity
          maps survive, so the tiles are cut from it. NEVER
          Fig6_reflectivity_visual_results.* (an older figure: a different
          column order, an unknown run).

FINDING THE REFLECTIVITY TILES — by script, never by hand. The tiles are
opaque squares on a transparent ground (alpha 0), separated by transparent
gaps. Background is decided by ALPHA ONLY: the ground is (0, 0, 0, 0) and the
Poisson tile is near-black, so no RGB test can tell them apart.
  1. mask = alpha >= 128 (majority coverage). drawio placed the SBR 1.0 tiles
     at a sub-pixel x, so each has 199 fully opaque columns, one column at
     alpha 229 on its left and one at alpha 26 on its right. The 229 column is
     tile (its RGB is the tile's own, un-premultiplied: 65 next to 67), the 26
     column is not. Nothing here resamples; the figure's own placement did.
  2. Connected components of the mask; a tile is a component whose box is
     190-215 px on both sides and >= 99 % filled. A colour bar is one at
     least 150 px tall and at most 40 px wide.
  3. Each half of the figure (SBR 0.6 left, SBR 1.0 right) has exactly five
     tiles in its top row: GT, then the Output row Poisson, Renewal, Zhang
     et al., MaRS, left to right, with a wide gap after the GT. The script
     asserts that order of gaps and prints every box.
  4. Crop the tile's box at native size, then centre-crop to exactly
     200 x 200 (the SBR 0.6 GT is 202 x 202 in the figure). No resampling,
     no sharpening, no colour change: the output pixels ARE the figure's
     pixels (asserted on the decoded WebP).
  5. Asserted: every crop pixel belongs to its own tile component (so no
     background and no colour bar), and no crop meets a colour-bar box.
The GT tile keeps its burned-in "GT" (guide 0.8).

DEPTH COLOURING — one linear mapping per scene, the same for all five tiles
of that scene: viridis (matplotlib's 256-entry table, embedded below with its
sha256), index = round(255 * (d - lo) / (hi - lo)) clipped to [0, 255], with
lo, hi = that scene's GT min and max. NO per-method stretch: it would hide
the Poisson failure (non-negotiable on honest rendering). The fraction of
each map clipped below lo / above hi is recorded. Orientation is asserted:
each prediction's map must correlate >= 0.98 with the luminance of the same
method's depth Output tile in the paper figure (the figure is used only for
this check, never for depth pixels).

--check rebuilds everything in a temp dir and compares, byte for byte, every
tile and provenance.json with the committed ones; it also decodes every
committed tile and asserts it equals its source pixels exactly. Byte equality
needs the same encoder: run it with the interpreter that built the tiles
(provenance.json records Pillow and libwebp; this repo's gates use the base
`python3`, Pillow 10.4.0 / libwebp 1.3.2).

The SBR 0.6 crops are compared with the older `assets/img/res_refl_*.webp`
(v2.2, cut from a rasterised Fig. 7 PDF at 720 px) after downscaling those to
200 px: printed, not gated, and not in provenance.json (v2.3-C removes them).
The old tiles carry a few pixels of white page border from that raster, so
the interior 180 x 180 is reported too. The Poisson tile is black to within
2 grey levels (std ~0.07), so its correlation means nothing.

OneDrive rule (WEBSITE_BUILD_STATUS 3.7, v2.1): everything is built in a temp
dir outside OneDrive, each final file is copied in once, and its md5 is
verified after the copy.

Needs numpy and Pillow (with WebP); standard library otherwise.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import PIL
from PIL import Image, features

VERSION = 1
STAGE = "v2.3-B"
REPO = Path(__file__).resolve().parent.parent
OUT_REL = "assets/img/res"
HOME = Path.home()
MAIN = HOME / "OneDrive" / "MaRS" / "Figs" / "main"
REFL_PNG = MAIN / "mars_cvpr2026-Page-1.drawio.png"
DEPTH_ROOT = MAIN / "downstream_visuals" / "depth_visuals_eccv2026"
TILE = 200

# (site key, depth folder, label, scene) — left half of the figure first
SCENES = [("sbr06", "sbr0.6_00357", "SBR 0.6", "library, test sample 00357"),
          ("sbr10", "sbr1.0_00767", "SBR 1.0", "kitchen, test sample 00767")]
# (site key, depth folder) in the figure's column order
METHODS = [("poisson", "poisson"), ("renewal", "renewal"),
           ("zhang", "icip"), ("mars", "ours")]
KEYS = ["gt"] + [k for k, _ in METHODS]

# matplotlib 3.9.2 colormaps["viridis"], its 256 entries as 8-bit RGB
# (round(255 * c)); embedded so the gate needs no matplotlib.
VIRIDIS_HEX = (
    "44015444025645045745055946075a46085c460a5d460b5e470d60470e6147106347"
    "116447136548146748166848176948186a481a6c481b6d481c6e481d6f481f704820"
    "71482173482374482475482576482677482878482979472a7a472c7a472d7b472e7c"
    "472f7d46307e46327e46337f463480453581453781453882443983443a83443b8443"
    "3d84433e85423f854240864241864142874144874045884046883f47883f48893e49"
    "893e4a893e4c8a3d4d8a3d4e8a3c4f8a3c508b3b518b3b528b3a538b3a548c39558c"
    "39568c38588c38598c375a8c375b8d365c8d365d8d355e8d355f8d34608d34618d33"
    "628d33638d32648e32658e31668e31678e31688e30698e306a8e2f6b8e2f6c8e2e6d"
    "8e2e6e8e2e6f8e2d708e2d718e2c718e2c728e2c738e2b748e2b758e2a768e2a778e"
    "2a788e29798e297a8e297b8e287c8e287d8e277e8e277f8e27808e26818e26828e26"
    "828e25838e25848e25858e24868e24878e23888e23898e238a8d228b8d228c8d228d"
    "8d218e8d218f8d21908d21918c20928c20928c20938c1f948c1f958b1f968b1f978b"
    "1f988b1f998a1f9a8a1e9b8a1e9c891e9d891f9e891f9f881fa0881fa1881fa1871f"
    "a28720a38620a48621a58521a68522a78522a88423a98324aa8325ab8225ac8226ad"
    "8127ad8128ae8029af7f2ab07f2cb17e2db27d2eb37c2fb47c31b57b32b67a34b679"
    "35b77937b87838b9773aba763bbb753dbc743fbc7340bd7242be7144bf7046c06f48"
    "c16e4ac16d4cc26c4ec36b50c46a52c56954c56856c66758c7655ac8645cc8635ec9"
    "6260ca6063cb5f65cb5e67cc5c69cd5b6ccd5a6ece5870cf5773d05675d05477d153"
    "7ad1517cd2507fd34e81d34d84d44b86d54989d5488bd6468ed64590d74393d74195"
    "d84098d83e9bd93c9dd93ba0da39a2da37a5db36a8db34aadc32addc30b0dd2fb2dd"
    "2db5de2bb8de29bade28bddf26c0df25c2df23c5e021c8e020cae11fcde11dd0e11c"
    "d2e21bd5e21ad8e219dae319dde318dfe318e2e418e5e419e7e419eae51aece51bef"
    "e51cf1e51df4e61ef6e620f8e621fbe723fde725")
VIRIDIS = np.frombuffer(bytes.fromhex(VIRIDIS_HEX), dtype=np.uint8).reshape(256, 3)
VIRIDIS_SHA256 = "18545f7c72a02f02a54f2e3f6ff9dcf357e0190ab9117a1f8fae44c6eaf179e0"

WEBP = dict(format="WEBP", lossless=True, quality=100, method=6)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rel_home(p: Path) -> str:
    return "~/" + str(p.relative_to(HOME))


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


# ---------------------------------------------------------------- tiles ----

def components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """4-connected components of a boolean mask, by row runs + union-find
    (numpy and the standard library only)."""
    h, w = mask.shape
    parent: list[int] = []

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    rows = []
    prev: list[tuple[int, int, int]] = []
    for y in range(h):
        v = np.concatenate(([0], mask[y].astype(np.int8), [0]))
        d = np.diff(v)
        starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        cur = []
        k = 0
        for s, e in zip(starts.tolist(), ends.tolist()):
            lab = len(parent)
            parent.append(lab)
            while k < len(prev) and prev[k][1] <= s:
                k += 1
            kk = k
            while kk < len(prev) and prev[kk][0] < e:
                ra, rb = find(lab), find(prev[kk][2])
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
                kk += 1
            cur.append((s, e, lab))
        rows.append(cur)
        prev = cur
    labels = np.zeros((h, w), dtype=np.int32)
    roots: dict[int, int] = {}
    for y, cur in enumerate(rows):
        for s, e, lab in cur:
            r = find(lab)
            labels[y, s:e] = roots.setdefault(r, len(roots) + 1)
    return labels, len(roots)


def find_tiles(rgba: np.ndarray) -> dict:
    """The reflectivity GT + Output tiles of both halves, and the colour bars."""
    mask = rgba[..., 3] >= 128
    labels, n = components(mask)
    tiles, bars = [], []
    # boxes from the label image in one pass
    flat = labels.ravel()
    idx = np.flatnonzero(flat)
    lab_of = flat[idx]
    yy, xx = np.divmod(idx, labels.shape[1])
    order = np.argsort(lab_of, kind="stable")
    lab_of, yy, xx = lab_of[order], yy[order], xx[order]
    cuts = np.flatnonzero(np.diff(lab_of)) + 1
    for g_l, g_y, g_x in zip(np.split(lab_of, cuts), np.split(yy, cuts), np.split(xx, cuts)):
        lab = int(g_l[0])
        x0, x1, y0, y1 = int(g_x.min()), int(g_x.max()) + 1, int(g_y.min()), int(g_y.max()) + 1
        w, h = x1 - x0, y1 - y0
        fill = len(g_l) / (w * h)
        box = {"label": lab, "box": [x0, y0, x1, y1], "w": w, "h": h, "fill": fill}
        if 190 <= w <= 215 and 190 <= h <= 215 and fill >= 0.99:
            tiles.append(box)
        elif h >= 150 and w <= 40:
            bars.append(box)
    W = rgba.shape[1]
    found = {}
    for half, (key, _, label, _) in enumerate(SCENES):
        mine = [t for t in tiles if (t["box"][0] + t["box"][2]) / 2 >= W / 2] if half \
            else [t for t in tiles if (t["box"][0] + t["box"][2]) / 2 < W / 2]
        if not mine:
            fail(f"{label}: no tile found")
        top = min(t["box"][1] for t in mine)
        row = sorted([t for t in mine if t["box"][1] - top <= 10], key=lambda t: t["box"][0])
        if len(row) != 5:
            fail(f"{label}: expected 5 tiles in the top row (GT + 4 outputs), found "
                 f"{[t['box'] for t in row]}")
        gaps = [row[i + 1]["box"][0] - row[i]["box"][2] for i in range(4)]
        if not (gaps[0] >= 50 and max(gaps[1:]) <= 20):
            fail(f"{label}: gaps {gaps} are not GT | Poisson Renewal Zhang MaRS")
        # the depth Output row: same columns as the reflectivity outputs, 3rd row
        depth_row = []
        for t in row[1:]:
            col = sorted([u for u in mine if abs(u["box"][0] - t["box"][0]) <= 3],
                         key=lambda u: u["box"][1])
            if len(col) != 4:
                fail(f"{label}: column at x={t['box'][0]} has {len(col)} tiles, expected 4 "
                     "(refl output, refl error, depth output, depth error)")
            depth_row.append(col[2])
        found[key] = {"row": dict(zip(KEYS, row)), "gaps": gaps,
                      "depth_row": dict(zip(KEYS[1:], depth_row))}
    return {"labels": labels, "bars": bars, "found": found}


def centre_crop(box: list[int]) -> list[int]:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if w < TILE or h < TILE:
        fail(f"tile {box} is {w} x {h}, smaller than {TILE}")
    dx, dy = (w - TILE) // 2, (h - TILE) // 2
    return [x0 + dx, y0 + dy, x0 + dx + TILE, y0 + dy + TILE]


def overlaps(a: list[int], b: list[int]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


# ---------------------------------------------------------------- build ----

def encode(rgb: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(rgb, "RGB").save(buf, **WEBP)
    return buf.getvalue()


def decode(b: bytes) -> np.ndarray:
    im = Image.open(io.BytesIO(b))
    return np.asarray(im.convert("RGB"))


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a.astype(np.float64).ravel(), b.astype(np.float64).ravel()
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def luminance(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., :3].astype(np.float64) @ np.array([0.299, 0.587, 0.114])


def build(verbose: bool = True) -> tuple[dict[str, bytes], dict[str, np.ndarray], dict]:
    if not REFL_PNG.exists() or not DEPTH_ROOT.exists():
        fail(f"sources not found under {MAIN} (this gate needs the author's "
             "OneDrive MaRS folder)")
    if sha(VIRIDIS.tobytes()) != VIRIDIS_SHA256:
        fail("the embedded viridis table does not match its sha256")
    say = print if verbose else (lambda *a, **k: None)

    png_bytes = REFL_PNG.read_bytes()
    im = Image.open(io.BytesIO(png_bytes))
    if im.size != (2565, 1028) or im.mode != "RGBA":
        fail(f"{REFL_PNG.name} is {im.size} {im.mode}, expected (2565, 1028) RGBA")
    rgba = np.asarray(im)
    det = find_tiles(rgba)
    labels, bars = det["labels"], det["bars"]
    say(f"colour bars (alpha >= 128 components >= 150 px tall, <= 40 px wide): "
        f"{[b['box'] for b in bars]}")

    files: dict[str, bytes] = {}
    pixels: dict[str, np.ndarray] = {}
    prov_refl, prov_depth, prov_src_depth = {}, {}, {}

    for key, folder, label, scene in SCENES:
        f = det["found"][key]
        say(f"\n{label} ({scene}) — reflectivity tiles, boxes [x0, y0, x1, y1) in "
            f"{REFL_PNG.name}; gaps {f['gaps']} px")
        prov_refl[key] = {"scene": scene, "gaps_px": f["gaps"], "tiles": {}}
        for k in KEYS:
            t = f["row"][k]
            crop = centre_crop(t["box"])
            x0, y0, x1, y1 = crop
            own = labels[y0:y1, x0:x1] == t["label"]
            if not own.all():
                fail(f"{label} {k}: crop {crop} holds {int((~own).sum())} px outside its tile")
            for b in bars:
                if overlaps(crop, b["box"]):
                    fail(f"{label} {k}: crop {crop} meets the colour bar {b['box']}")
            a = rgba[y0:y1, x0:x1, 3]
            partial_cols = int((a.min(axis=0) < 255).sum())
            partial_rows = int((a.min(axis=1) < 255).sum())
            rgb = np.ascontiguousarray(rgba[y0:y1, x0:x1, :3])
            name = f"refl_{key}_{k}.webp"
            files[name] = encode(rgb)
            pixels[name] = rgb
            prov_refl[key]["tiles"][k] = {
                "tile_box": t["box"], "tile_size": [t["w"], t["h"]], "crop_box": crop,
                "min_alpha": int(a.min()), "partial_alpha_columns": partial_cols,
                "partial_alpha_rows": partial_rows}
            say(f"  {k:8s} tile {t['box']} {t['w']}x{t['h']}  crop {crop}  "
                f"min alpha {int(a.min())}  partial-alpha cols/rows {partial_cols}/{partial_rows}")

        # depth
        base = DEPTH_ROOT / folder
        gts, preds, src = [], {}, {"dir": rel_home(base), "gt": {}, "pred": {}}
        for k, sub in METHODS:
            g = sorted(glob.glob(str(base / sub / "*_gt.npz")))
            p = sorted(glob.glob(str(base / sub / "*_pred.npz")))
            if len(g) != 1 or len(p) != 1:
                fail(f"{base / sub}: expected one *_gt.npz and one *_pred.npz, found {g} {p}")
            for path, store in ((g[0], "gt"), (p[0], "pred")):
                raw = Path(path).read_bytes()
                arr = np.load(io.BytesIO(raw))["depth"]
                if arr.shape != (TILE, TILE) or arr.dtype != np.float32 or not np.isfinite(arr).all():
                    fail(f"{path}: depth {arr.shape} {arr.dtype}, expected finite 200 x 200 float32")
                src[store][k] = {"file": f"{sub}/{Path(path).name}", "sha256": sha(raw)}
                (gts.append(arr) if store == "gt" else preds.__setitem__(k, arr))
        for i, g in enumerate(gts[1:], 1):
            if not np.array_equal(g, gts[0]):
                fail(f"{label}: {METHODS[i][1]}'s *_gt.npz differs from {METHODS[0][1]}'s")
        gt = gts[0]
        lo, hi = float(gt.min()), float(gt.max())
        maps = {"gt": gt, **preds}
        prov_depth[key] = {"scene": scene, "range_m": [lo, hi], "gt_files_identical": True,
                           "clip_fraction": {}, "figure_luminance_corr": {}}
        say(f"{label} depth: GT range {lo:.4f} .. {hi:.4f} m (one mapping for all five)")
        for k in KEYS:
            d = maps[k].astype(np.float64)
            below, above = float((d < lo).mean()), float((d > hi).mean())
            idx = np.clip(np.rint((d - lo) / (hi - lo) * 255.0), 0, 255).astype(np.uint8)
            rgb = np.ascontiguousarray(VIRIDIS[idx])
            name = f"depth_{key}_{k}.webp"
            files[name] = encode(rgb)
            pixels[name] = rgb
            prov_depth[key]["clip_fraction"][k] = {"below": round(below, 6), "above": round(above, 6)}
            line = (f"  {k:8s} {float(d.min()):.4f} .. {float(d.max()):.4f} m  "
                    f"clipped below {below:.4f} above {above:.4f}")
            if k != "gt":
                fx0, fy0, fx1, fy1 = f["depth_row"][k]["box"]
                fig = luminance(rgba[fy0:fy0 + TILE, fx0:fx0 + TILE])
                r = corr(d[: fig.shape[0], : fig.shape[1]], fig)
                if not r >= 0.98:
                    fail(f"{label} {k}: depth map vs the figure's depth tile, r = {r:.3f} < 0.98 "
                         "(orientation or file mix-up)")
                prov_depth[key]["figure_luminance_corr"][k] = round(r, 4)
                line += f"  r(figure) {r:.4f}"
            say(line)
        prov_src_depth[key] = src

    prov = {
        "generator": {"script": "tools/build_result_tiles.py", "version": VERSION, "stage": STAGE,
                      "pillow": PIL.__version__, "libwebp": features.version("webp"),
                      "numpy": np.__version__, "webp": {k: v for k, v in WEBP.items() if k != "format"}},
        "sources": {
            "reflectivity": {"path": rel_home(REFL_PNG), "sha256": sha(png_bytes),
                             "size": list(im.size), "mode": im.mode,
                             "note": "the image paper/Figs/main/Fig7_reflectivity_visual_results.pdf embeds"},
            "depth": prov_src_depth,
        },
        "reflectivity": {
            "rule": "alpha >= 128 components, 190-215 px square and >= 99 % filled; top row of each "
                    "half = GT, Poisson, Renewal, Zhang et al., MaRS; native crop, centre-cropped to "
                    "200 x 200; RGB taken as is (un-premultiplied); no resampling",
            "colour_bars": [b["box"] for b in bars],
            **prov_refl},
        "depth": {
            "colormap": "viridis, matplotlib 3.9.2, 256 entries, 8-bit (embedded)",
            "colormap_sha256": VIRIDIS_SHA256,
            "mapping": "index = clip(round(255 * (d - lo) / (hi - lo)), 0, 255); lo, hi = the scene's "
                       "GT min and max; the same mapping for all five tiles of a scene",
            **prov_depth},
        "outputs": {f"{OUT_REL}/{n}": {"sha256": sha(b), "bytes": len(b), "size": [TILE, TILE]}
                    for n, b in sorted(files.items())},
    }
    files["provenance.json"] = (json.dumps(prov, indent=2, sort_keys=False) + "\n").encode()
    return files, pixels, prov


def old_tile_report(pixels: dict[str, np.ndarray]) -> None:
    """SBR 0.6 crops vs the v2.2 tiles, downscaled to 200 px. Printed only."""
    old_dir = REPO / "assets" / "img"
    print("\nsanity: SBR 0.6 reflectivity crops vs assets/img/res_refl_*.webp "
          "(720 px, LANCZOS to 200; not gated)")
    try:
        from PIL import ImageFilter
    except ImportError:  # pragma: no cover
        return
    for k in KEYS:
        p = old_dir / f"res_refl_{k}.webp"
        if not p.exists():
            print(f"  {k:8s} (no old tile)")
            continue
        old = Image.open(p).convert("L").resize((TILE, TILE), Image.LANCZOS)
        new = Image.fromarray(pixels[f"refl_sbr06_{k}.webp"], "RGB").convert("L")
        o, n = np.asarray(old, np.float64), np.asarray(new, np.float64)
        ob = np.asarray(old.filter(ImageFilter.GaussianBlur(1.5)), np.float64)
        nb = np.asarray(new.filter(ImageFilter.GaussianBlur(1.5)), np.float64)
        c = slice(10, TILE - 10)   # the old tiles carry a white page border
        print(f"  {k:8s} r {corr(n, o):.4f}  r(blur 1.5) {corr(nb, ob):.4f}  "
              f"interior 180 px: r {corr(n[c, c], o[c, c]):.4f}  "
              f"mean |diff| {np.abs(n[c, c] - o[c, c]).mean():.2f}  "
              f"std new/old {n[c, c].std():.2f}/{o[c, c].std():.2f}")


def check() -> int:
    files, pixels, _ = build(verbose=True)
    out = REPO / OUT_REL
    bad = 0
    with tempfile.TemporaryDirectory(prefix="mars_tiles_check_") as tmp:
        tmp = Path(tmp)
        for name, b in files.items():
            (tmp / name).write_bytes(b)
        print(f"\n--check: rebuilt into a temp dir ({len(files)} files), compared with the committed files")
        bad = _compare(tmp, out, pixels)
    old_tile_report(pixels)
    print(f"\n{'FAIL' if bad else 'PASS'}: {bad} problem(s), {len(files)} file(s)")
    return 1 if bad else 0


def _compare(tmp: Path, out: Path, pixels: dict[str, np.ndarray]) -> int:
    bad = 0
    files = {p.name: p.read_bytes() for p in sorted(tmp.iterdir())}
    for name, b in sorted(files.items()):
        live = out / name
        if not live.exists():
            print(f"  MISSING  {OUT_REL}/{name}")
            bad += 1
            continue
        lb = live.read_bytes()
        if lb != b:
            print(f"  DIFFERS  {OUT_REL}/{name}  (committed sha256 {sha(lb)[:16]}…, "
                  f"rebuilt {sha(b)[:16]}…)")
            bad += 1
            continue
        if name.endswith(".webp"):
            got = decode(lb)
            if got.shape != (TILE, TILE, 3) or not np.array_equal(got, pixels[name]):
                print(f"  PIXELS   {OUT_REL}/{name}  decoded tile is not its source pixels")
                bad += 1
                continue
        print(f"  ok  {OUT_REL}/{name}  sha256 {sha(lb)[:16]}…")
    extra = sorted(p.name for p in out.iterdir() if p.name not in files) if out.exists() else []
    for name in extra:
        print(f"  EXTRA    {OUT_REL}/{name} (not built by this script)")
        bad += 1
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="rebuild and compare; write nothing")
    args = ap.parse_args()
    if args.check:
        return check()
    files, pixels, _ = build(verbose=True)
    for name, b in files.items():
        if name.endswith(".webp") and not np.array_equal(decode(b), pixels[name]):
            fail(f"{name}: the encoded tile does not decode to its source pixels")
    out = REPO / OUT_REL
    with tempfile.TemporaryDirectory(prefix="mars_tiles_") as tmp:
        tmp = Path(tmp)
        for name, b in files.items():
            (tmp / name).write_bytes(b)
        out.mkdir(parents=True, exist_ok=True)
        for name, b in sorted(files.items()):
            shutil.copyfile(tmp / name, out / name)
            if hashlib.md5((out / name).read_bytes()).digest() != hashlib.md5(b).digest():
                fail(f"md5 mismatch after copying {name}")
            print(f"  wrote {OUT_REL}/{name}  ({len(b)} B, md5 ok)")
    old_tile_report(pixels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
