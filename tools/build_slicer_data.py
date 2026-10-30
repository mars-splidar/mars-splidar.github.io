#!/usr/bin/env python3
"""The cube slicer's data — stage v2.1-C, T1 (guide 0.6 item 5).

    python3 tools/build_slicer_data.py           # build, copy in, splice the readout
    python3 tools/build_slicer_data.py --check   # writes nothing; the gate form

Reads the paper's own Fig. 1 cubes from the project folder's
`video/web/hero/out/cubes.npz` (READ ONLY; stage 08 recovered them, Q18; the
teaser is rendered from the same file) and writes `assets/data/slicer/`:

  poisson.u8.gz  gold.u8.gz  mars.u8.gz
        the three 128 x 128 x 256 uint8 cubes, C order (row i, column j, bin),
        gzip level 9 with mtime 0. Served as plain files and inflated in the
        browser with DecompressionStream('gzip') — js/mars-slicer.js does not
        rely on GitHub Pages' Content-Encoding (and copes if a server has
        already inflated them).
  tau.f32.gz
        each pixel's true delay, ns modulo t_r, float32 little-endian, 128 x 128.
  meta.json
        shape, t_r, bin width and bin-time convention, the brightness constant,
        the readout window, the four presets with their readouts, and
        provenance: the sha256 of cubes.npz and of every output (both the .gz
        bytes and the inflated payload), the Fig. 1 workload, this generator.

HONESTY RULES this script fixes in data, so the page cannot drift from them:
  * ONE brightness mapping for all three images: K = the 99.7th percentile of
    the GOLD cube's 4-bin window sums (the prototype's rule), shown as
    L = 1 - exp(-3 v / K). No per-image normalisation anywhere.
  * PRESETS ARE DATA-DRIVEN, exactly the prototype's rule: the pixel whose
    5 x 5 neighbourhood is most homogeneous in S and tau, among S > 7.6
    (bright) and 1.2 < S < 2.0 (dim); times relative to that pixel's true
    delay: bright -2.3 ns, dim -1.0, just after the peak +5, before the peak
    -25 (the last two on the bright pixel). The bright preset MUST show gold
    and MaRS earlier than Poisson by 2-3 ns and within 0.3 ns of each other;
    if it does not, this script fails rather than search for a pixel that does.
  * THE READOUT is the "return centre" (WEBSITE_BUILD_STATUS 2, 2026-10-26):
    the count-weighted mean arrival time of the photons within +-10 ns of the
    pixel's true delay, over the pooled n x n patch. BIN TIME CONVENTION: bin
    b is timed at its CENTRE, (b + 0.5) * t_r / 256. (v2.1-B's B6 numbers use
    the same convention; section 2's earlier -2.69 / -2.78 did not record one,
    which is why they differ by about 0.4 ns.)

The page's default readout (the bright preset at 3 x 3) ships as static HTML
so it is right before the module loads; this script splices it into
index.html between the `slicer_readout:start` / `:end` markers, and --check
fails if the shipped text differs from what the data gives.

PRESET NOTES (stage v2.3-A, guide 0.8). Each preset carries one sentence,
verbatim from guide 0.8, shown under the chips while that preset is selected
(js/mars-slicer.js reads it from meta.json; NOTES below is the only place the
sentences are written). The default (bright) note ships as static HTML,
spliced between the `slicer_note:start` / `:end` markers together with four
aria-hidden copies that reserve the tallest note's height, and --check fails
if the shipped block differs from what this script would write.
Every factual claim in a note is a rule in claims(), evaluated on the data
over 3 x 3 pixels x 3 bins (the preset's bin and one either side) at the
default pooling; --check fails if any rule does not hold. The same rules are
evaluated at 1 x 1 and 5 x 5 and reported, not gated (a preset keeps the
reader's pooling, so the note can be read at either):
  bright  near its return (|t - tau| <= 1.5 sigma_t); gold and MaRS return
          centres earlier than Poisson's; "dead time is strongest here": the
          gold standard keeps a smaller share of Poisson's photons than at
          the dim preset.
  dim     a dimmer pixel (S below the bright pixel's) where fewer photons
          arrive (Poisson's window count below the bright preset's); the
          shift, Poisson's return centre minus gold's (and minus MaRS's), is
          positive and smaller than at the bright preset.
  shadow  just after the return (0 < t - tau < t_d); gold and MaRS each at
          most 2 % of Poisson's count; Poisson still registers (>= 5).
  before  before the return, where only background reaches the pixel
          (t - tau <= -5 sigma_t); all three counts within 2 photons
          (max - min <= 2).

OneDrive rule (WEBSITE_BUILD_STATUS 3.7, v2.1): everything is built in a temp
dir outside OneDrive, each final file is copied in once, and its md5 is
verified after the copy.

Needs numpy; standard library otherwise.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

VERSION = "2"
REPO = Path(__file__).resolve().parent.parent
NPZ = REPO.parent.parent / "video" / "web" / "hero" / "out" / "cubes.npz"
NPZ_SHA256 = "cb30c2030fb25e93f52a4b99a9e3f37fdfc631546cc6a6a7b51998a9faebb81e"
OUT = REPO / "assets" / "data" / "slicer"
INDEX = REPO / "index.html"

KEYS = ("poisson", "gold", "mars")
TR = 100.0                   # ns, laser period (provenance.json params)
NB = 256
DT = TR / NB                 # 0.390625 ns
WIN = 4                      # time-slice window, bins (1.56 ns, "1.6 ns")
READ_HALF = 10.0             # readout window, +- ns around the true delay
POOL_DEFAULT = 1             # radius: 3 x 3
PRESET_RULE = [              # id, label, which pixel, t relative to its delay
    ("bright", "Bright surface", "bright", -2.3),
    ("dim", "Dim surface", "dim", -1.0),
    ("shadow", "Just after the peak", "bright", +5.0),
    ("before", "Before the peak", "bright", -25.0),
]
MARKS = ("<!-- slicer_readout:start -->", "<!-- slicer_readout:end -->")
NOTE_MARKS = ("<!-- slicer_note:start -->", "<!-- slicer_note:end -->")
SIGMA_T = 2.0                # ns, pulse width (provenance workload)
T_D = 75.0                   # ns, dead time (provenance workload)
POOLS = (0, 1, 2)            # radii: 1 x 1, 3 x 3, 5 x 5 (the page's three)
# The four preset notes, verbatim from guide 0.8 (stage v2.3-A). The ONLY
# place they are written: meta.json carries them to js/mars-slicer.js, and the
# default one is spliced into index.html. Each claim is a rule in claims().
NOTES = {
    "bright": "A bright pixel near its return. Dead time is strongest here, "
              "so the gold standard and MaRS peak earlier than Poisson.",
    "dim": "A dim pixel. Fewer photons arrive, so the shift is smaller.",
    "shadow": "Just after the return. The detector is still blind, so the "
              "gold standard and MaRS register almost nothing here. Poisson "
              "still does.",
    "before": "Before the return. Only background light reaches this pixel, "
              "and all three agree.",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pick(S, tau_raw, cond):
    """The prototype's rule, verbatim: among pixels meeting `cond` and at
    least 5 px from the border, the one whose 5 x 5 neighbourhood has the
    smallest std(S) + std(tau). Ties keep the first in row-major order."""
    best, bs = None, 1e9
    for i, j in zip(*np.where(cond)):
        if 4 < i < 123 and 4 < j < 123:
            v = S[i-2:i+3, j-2:j+3].std() + tau_raw[i-2:i+3, j-2:j+3].std()
            if v < bs:
                bs, best = v, (int(i), int(j))
    return best


def pooled(cube, i, j, r):
    """n x n patch sum with edge clamping — the same as js/mars-slicer.js."""
    h = np.zeros(NB, dtype=np.float64)
    H, W = cube.shape[:2]
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            ii = min(H - 1, max(0, i + di))
            jj = min(W - 1, max(0, j + dj))
            h += cube[ii, jj]
    return h


def return_centre(h, tau):
    tc = (np.arange(NB) + 0.5) * DT
    rel = ((tc - tau + TR / 2) % TR + TR) % TR - TR / 2
    m = np.abs(rel) < READ_HALF
    n = h[m].sum()
    return float((h[m] * rel[m]).sum() / n) if n else 0.0


def window(cube, i, j, r, b):
    """Photons in the pooled patch over bins b - 1, b, b + 1 (3 bins)."""
    h = pooled(cube, i, j, r)
    return int(round(h[(b - 1) % NB] + h[b] + h[(b + 1) % NB]))


def claims(cubes, tau, S, presets, r):
    """Every factual claim of NOTES as a rule on the data, at pool radius r.
    Pure: arrays and presets in, [(preset id, rule, ok, detail)] out, so a
    test can hand it mutated data (review/v23A/harness/mutate_notes.py)."""
    P = {p["id"]: p for p in presets}
    w, rc = {}, {}
    for pid, p in P.items():
        i, j = p["px"]
        w[pid] = {k: window(cubes[k], i, j, r, p["bin"]) for k in KEYS}
        rc[pid] = {k: return_centre(pooled(cubes[k], i, j, r), float(tau[i, j]))
                   for k in KEYS}
    out = []

    def rule(pid, name, ok, detail):
        out.append((pid, name, bool(ok), detail))

    b, d, a, f = P["bright"], P["dim"], P["shadow"], P["before"]
    wb, wd, wa, wf = w["bright"], w["dim"], w["shadow"], w["before"]
    rb, rd = rc["bright"], rc["dim"]
    # bright
    rule("bright", "near its return: |t - tau| <= 1.5 sigma_t",
         abs(b["t_rel_ns"]) <= 1.5 * SIGMA_T, f"t - tau = {b['t_rel_ns']:+.1f} ns")
    rule("bright", "gold and MaRS peak earlier than Poisson (return centre)",
         rb["gold"] < rb["poisson"] and rb["mars"] < rb["poisson"],
         f"Poisson {rb['poisson']:+.3f}, gold {rb['gold']:+.3f}, MaRS {rb['mars']:+.3f} ns")
    fb, fd = wb["gold"] / max(wb["poisson"], 1), wd["gold"] / max(wd["poisson"], 1)
    rule("bright", "dead time strongest: gold keeps a smaller share of Poisson than at dim",
         fb < fd, f"gold/Poisson {wb['gold']}/{wb['poisson']} = {fb:.3f} vs dim {fd:.3f}")
    # dim
    rule("dim", "a dimmer pixel: S below the bright pixel's",
         d["S"] < b["S"], f"S {d['S']:.3f} vs {b['S']:.3f}")
    rule("dim", "fewer photons arrive: Poisson window below the bright preset's",
         wd["poisson"] < wb["poisson"], f"Poisson {wd['poisson']} vs {wb['poisson']}")
    sb = {k: rb["poisson"] - rb[k] for k in ("gold", "mars")}
    sd = {k: rd["poisson"] - rd[k] for k in ("gold", "mars")}
    rule("dim", "the shift is smaller: 0 < (Poisson - gold, Poisson - MaRS) < bright's",
         all(0 < sd[k] < sb[k] for k in sd),
         f"gold {sd['gold']:.3f} vs {sb['gold']:.3f}, MaRS {sd['mars']:.3f} vs {sb['mars']:.3f} ns")
    # just after the peak
    rule("shadow", "just after the return: 0 < t - tau < t_d",
         0 < a["t_rel_ns"] < T_D, f"t - tau = {a['t_rel_ns']:+.1f} ns")
    rule("shadow", "gold and MaRS register almost nothing: each <= 2 % of Poisson",
         wa["gold"] <= 0.02 * wa["poisson"] and wa["mars"] <= 0.02 * wa["poisson"],
         f"{wa['poisson']} / {wa['gold']} / {wa['mars']}")
    rule("shadow", "Poisson still does: >= 5 photons",
         wa["poisson"] >= 5, f"Poisson {wa['poisson']}")
    # before the peak
    rule("before", "only background: t - tau <= -5 sigma_t",
         f["t_rel_ns"] <= -5 * SIGMA_T, f"t - tau = {f['t_rel_ns']:+.1f} ns")
    rule("before", "all three agree: max - min <= 2 photons",
         max(wf.values()) - min(wf.values()) <= 2,
         f"{wf['poisson']} / {wf['gold']} / {wf['mars']}")
    return out, w


def note_html(meta) -> str:
    """The static note block: the live <p> holding the default preset's note,
    then one aria-hidden copy of each note in the same grid cell, so the box
    is as tall as the tallest note at every width (css/mars.css)."""
    dflt = meta["default"]["preset"]
    by = {p["id"]: p["note"] for p in meta["presets"]}
    lines = [f'<p class="mars-slicer__pnote-live" aria-live="polite">{by[dflt]}</p>']
    lines += [f'<span class="mars-slicer__pnote-size" aria-hidden="true">{by[p["id"]]}</span>'
              for p in meta["presets"]]
    return lines


def fmt(v: float) -> str:
    """'+0.1 ns' / '−2.7 ns' (U+2212), as the page prints it. Rounded first,
    so a value that rounds to zero prints '0.0', never '−0.0'."""
    r = round(abs(v) * 10) / 10
    if r == 0:
        return "0.0&nbsp;ns"
    return ("+" if v > 0 else "&minus;") + f"{r:.1f}&nbsp;ns"


def readout_html(off) -> str:
    """The readout's inner HTML. Same structure js/mars-slicer.js writes."""
    return ('<span class="mars-slicer__ro-lead">Return centre vs. true '
            'delay:</span> '
            f'<span class="is-poisson">Poisson <b>{fmt(off["poisson"])}</b></span>'
            ' <span class="sep" aria-hidden="true">·</span> '
            f'<span class="is-gold">Gold standard <b>{fmt(off["gold"])}</b></span>'
            ' <span class="sep" aria-hidden="true">·</span> '
            f'<span class="is-mars">MaRS <b>{fmt(off["mars"])}</b></span>')


def build(tmp: Path) -> dict:
    raw = NPZ.read_bytes()
    got = sha(raw)
    if got != NPZ_SHA256:
        sys.exit(f"FAIL: {NPZ} sha256 {got}, expected {NPZ_SHA256} — the Fig. 1 "
                 "cubes changed under this script; stop and find out why.")
    d = np.load(NPZ)
    cubes = {k: np.ascontiguousarray(d[k]) for k in KEYS}
    for k, c in cubes.items():
        assert c.shape == (128, 128, NB) and c.dtype == np.uint8, (k, c.shape, c.dtype)
    S = d["S_img"]
    tau_raw = d["tau_img"]
    tau = (tau_raw % TR).astype("<f4")

    files = {}
    for name, payload in [(k, cubes[k].tobytes()) for k in KEYS] + \
                         [("tau", tau.tobytes())]:
        fn = f"{name}.f32.gz" if name == "tau" else f"{name}.u8.gz"
        gz = gzip.compress(payload, compresslevel=9, mtime=0)
        (tmp / fn).write_bytes(gz)
        files[name] = {"path": fn, "bytes": len(gz),
                       "sha256_gz": sha(gz), "sha256_raw": sha(payload),
                       "raw_bytes": len(payload)}

    # brightness constant, fixed from GOLD (prototype rule)
    g = cubes["gold"].astype(np.float32)
    k = np.cumsum(g, axis=2)
    sums = k[:, :, WIN:] - k[:, :, :-WIN]
    K = float(np.percentile(sums, 99.7))

    px = {"bright": pick(S, tau_raw, S > 7.6),
          "dim": pick(S, tau_raw, (S > 1.2) & (S < 2.0))}
    presets = []
    for pid, label, which, trel in PRESET_RULE:
        i, j = px[which]
        t_abs = (float(tau[i, j]) + trel) % TR
        b = int(np.floor(t_abs / DT)) % NB
        off = {kk: return_centre(pooled(cubes[kk], i, j, POOL_DEFAULT),
                                 float(tau[i, j])) for kk in KEYS}
        presets.append({
            "id": pid, "label": label, "px": [i, j],
            "S": round(float(S[i, j]), 4), "tau_ns": round(float(tau[i, j]), 4),
            "t_rel_ns": trel, "t_ns": round(t_abs, 4), "bin": b,
            "readout_3x3_ns": {kk: round(v, 4) for kk, v in off.items()},
            "note": NOTES[pid],
        })
    notes = {}
    for r in POOLS:
        res, w = claims(cubes, tau, S, presets, r)
        n = f"{2 * r + 1}x{2 * r + 1}"
        notes[n] = {"window_3bins": w,
                    "rules": [{"preset": pid, "rule": name, "ok": ok, "detail": det}
                              for pid, name, ok, det in res]}

    meta = {
        "generator": {"script": "tools/build_slicer_data.py", "version": VERSION,
                      "stage": "v2.3-A"},
        "shape": [128, 128, NB], "order": "C: row i, column j, bin",
        "t_r_ns": TR, "bin_ns": DT,
        "bin_time": "bin b is timed at its centre, (b + 0.5) * bin_ns",
        "files": files,
        "brightness": {
            "K": round(K, 6),
            "rule": "99.7th percentile of the GOLD cube's 4-bin window sums",
            "map": "L = 1 - exp(-3 v / K), v = photons in the 4-bin window; "
                   "one mapping for all three images",
            "window_bins": WIN},
        "readout": {"half_window_ns": READ_HALF,
                    "name": "return centre: count-weighted mean arrival time of "
                            "the photons within +-10 ns of the pixel's true "
                            "delay, over the pooled patch"},
        "default": {"preset": "bright", "pool": 3, "range": "peak"},
        "presets": presets,
        "notes_check": {
            "what": "each note's claims as rules on the data (tools/build_slicer_data.py "
                    "claims()), photons over n x n pixels x 3 bins around the preset; "
                    "gated at 3x3 (the default), reported at 1x1 and 5x5",
            "gated_pool": "3x3",
            "pools": notes},
        "provenance": {
            "source": "video/web/hero/out/cubes.npz (project folder, read only)",
            "source_sha256": NPZ_SHA256,
            "what": "the paper's own Fig. 1 cubes (stage 08, Q18): Poisson, "
                    "sequential gold standard, MaRS; one realization each, "
                    "independent",
            "workload": {"pixels": [128, 128], "bins": NB, "N_cycles": 100,
                         "t_r_ns": TR, "t_d_ns": 75.0, "sigma_t_ns": 2.0,
                         "B": 0.5},
        },
    }
    (tmp / "meta.json").write_text(
        json.dumps(meta, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return meta


def report(meta) -> bool:
    print(f"brightness K = {meta['brightness']['K']}  (gold, 99.7th pct of 4-bin sums)")
    tot = 0
    for name, f in meta["files"].items():
        tot += f["bytes"]
        print(f"  {f['path']:<16} {f['bytes']:>9,} B gz   raw {f['raw_bytes']:>9,} B")
    print(f"  cubes + tau gz total {tot:,} B")
    print("\npresets (readout = return centre vs true delay, 3 x 3 pooled, bin centres):")
    for p in meta["presets"]:
        r = p["readout_3x3_ns"]
        print(f"  {p['id']:<7} px (i={p['px'][0]}, j={p['px'][1]})  S {p['S']:.3f}  "
              f"tau {p['tau_ns']:.3f} ns  t = tau {p['t_rel_ns']:+.1f} = {p['t_ns']:.3f} ns "
              f"(bin {p['bin']})   Poisson {r['poisson']:+.3f}  gold {r['gold']:+.3f}  "
              f"MaRS {r['mars']:+.3f} ns")
    b = next(p for p in meta["presets"] if p["id"] == "bright")["readout_3x3_ns"]
    lead_g, lead_m = b["poisson"] - b["gold"], b["poisson"] - b["mars"]
    ok = 2.0 <= lead_g <= 3.0 and 2.0 <= lead_m <= 3.0 and abs(b["gold"] - b["mars"]) <= 0.3
    print("\npreset notes, claims on the data (n x n pixels x 3 bins; gated at 3x3):")
    gate_ok = True
    for n, blk in meta["notes_check"]["pools"].items():
        gated = n == meta["notes_check"]["gated_pool"]
        ws = blk["window_3bins"]
        print(f"  {n}{' (gated)' if gated else ' (reported)'}  windows P/G/M: " +
              "  ".join(f"{pid} {v['poisson']}/{v['gold']}/{v['mars']}" for pid, v in ws.items()))
        for x in blk["rules"]:
            tag = "ok  " if x["ok"] else ("FAIL" if gated else "warn")
            print(f"    {tag} {x['preset']:<7} {x['rule']}  [{x['detail']}]")
            if gated and not x["ok"]:
                gate_ok = False
    print(f"  notes -> {'PASS' if gate_ok else 'FAIL — a note claims something the data does not show'}")
    print(f"\nC2 bright: gold {lead_g:.3f} ns and MaRS {lead_m:.3f} ns earlier than "
          f"Poisson; |gold - MaRS| = {abs(b['gold'] - b['mars']):.3f} ns  "
          f"-> {'PASS' if ok else 'FAIL — stop and report, do not re-pick'}")
    return ok and gate_ok


def shipped_readout() -> str | None:
    s = INDEX.read_text(encoding="utf-8")
    if MARKS[0] not in s:
        return None
    return s.split(MARKS[0], 1)[1].split(MARKS[1], 1)[0].strip()


def expected_readout(meta) -> str:
    p = next(p for p in meta["presets"] if p["id"] == meta["default"]["preset"])
    return readout_html(p["readout_3x3_ns"])


def shipped_note() -> list[str] | None:
    s = INDEX.read_text(encoding="utf-8")
    if NOTE_MARKS[0] not in s:
        return None
    body = s.split(NOTE_MARKS[0], 1)[1].split(NOTE_MARKS[1], 1)[0]
    return [ln.strip() for ln in body.strip().splitlines()]


def splice(s: str, marks, lines) -> str:
    """Replace what sits between the two markers, one line each, keeping the
    indentation of the line the end marker sits on."""
    head, rest = s.split(marks[0], 1)
    _, tail = rest.split(marks[1], 1)
    indent = head[head.rfind("\n") + 1:]
    body = "".join(f"\n{indent}{ln}" for ln in lines)
    return f"{head}{marks[0]}{body}\n{indent}{marks[1]}{tail}"


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="regenerate in a temp dir and compare; write nothing")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="mars_slicer_") as td:
        tmp = Path(td)
        meta = build(tmp)
        ok = report(meta)
        names = sorted(p.name for p in tmp.iterdir())
        exp_ro = expected_readout(meta)

        if args.check:
            bad = 0
            for n in names:
                live = OUT / n
                if not live.exists():
                    print(f"  ** missing {live.relative_to(REPO)}")
                    bad += 1
                elif live.read_bytes() != (tmp / n).read_bytes():
                    # a different zlib can change the .gz bytes for the same
                    # payload; say which, so it is not mistaken for data drift
                    if n.endswith(".gz") and gzip.decompress(live.read_bytes()) \
                            == gzip.decompress((tmp / n).read_bytes()):
                        print(f"  ** {n}: same payload, different gzip bytes "
                              "(zlib build) — rebuild, then meta.json matches")
                    else:
                        print(f"  ** DRIFT {live.relative_to(REPO)}")
                    bad += 1
                else:
                    print(f"  ok  {live.relative_to(REPO)}  sha256 {sha(live.read_bytes())[:16]}…")
            got = shipped_readout()
            if got != exp_ro:
                print("  ** index.html readout differs from the data:\n"
                      f"     shipped:  {got}\n     expected: {exp_ro}")
                bad += 1
            else:
                print("  ok  index.html default readout matches the data")
            got_n = shipped_note()
            if got_n != note_html(meta):
                print("  ** index.html preset note block differs from the data:\n"
                      f"     shipped:  {got_n}\n     expected: {note_html(meta)}")
                bad += 1
            else:
                print("  ok  index.html default preset note and its sizers match the data")
            print(f"\n{'FAIL' if bad or not ok else 'PASS'} — build_slicer_data --check")
            return 1 if bad or not ok else 0

        if not ok:
            print("\nNOT WRITTEN — the bright preset fails C2.")
            return 1
        OUT.mkdir(parents=True, exist_ok=True)
        for n in names:
            src, dst = tmp / n, OUT / n
            if dst.exists() and dst.read_bytes() == src.read_bytes():
                print(f"  unchanged {dst.relative_to(REPO)}")
                continue
            shutil.copyfile(src, dst)
            if md5(dst) != md5(src):
                sys.exit(f"FAIL: md5 mismatch after copying {n} (OneDrive?)")
            print(f"  wrote     {dst.relative_to(REPO)}  md5 {md5(dst)}")

        s = new = INDEX.read_text(encoding="utf-8")
        for marks, lines, what in ((MARKS, [exp_ro], "default readout"),
                                   (NOTE_MARKS, note_html(meta), "preset note block")):
            if marks[0] in new:
                new = splice(new, marks, lines)
            else:
                print(f"  (index.html has no {marks[0]} marker; {what} not spliced)")
        if new != s:
            INDEX.write_text(new, encoding="utf-8")
            print("  spliced the default readout and preset note into index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
