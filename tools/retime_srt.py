"""
retime_srt.py — rescale a subtitle file's timestamps by a constant ratio, and
emit WebVTT beside it.

Written for stage 04 task 0, and kept because the same job recurs whenever the
film is re-cut at a different pace.

`MaRS_ECCV2026_5min_v3_voice_0.9x.mp4` — the cut this site serves — is a pure
retime of `MaRS_ECCV2026_5min_v3_voice.mp4`: identical frame COUNT (7316), 30
fps against 27 fps, so the two clocks differ by exactly 30/27 = 10/9
everywhere, and the existing SRT can be scaled rather than regenerated.  That
was verified three ways before it was trusted — frame n of the 0.9x cut has its
minimum pixel distance against frame n of the original (not n±1); all 77
silence-detected speech onsets map by 1.1101 ± 0.005 with a worst residual of
0.11 s against exact 10/9; and both audio streams decode to sizes in the same
ratio.  Regenerating through the film's `captions.py` would in fact have been
*wrong*: it reads `video/timing.json`, which describes the 30 fps track.

    python tools/retime_srt.py in.srt out.srt --ratio 10/9 [--vtt out.vtt]

The exact invocation that produced what is in assets/docs/:

    python tools/retime_srt.py \
        ../../video/out/MaRS_ECCV2026_5min_v3_voice.srt \
        assets/docs/mars_5min.srt --ratio 10/9 --vtt assets/docs/mars_5min.vtt

The `.vtt` is a straight transcode of the scaled cues: same text, same times,
`.` instead of `,` as the decimal mark, plus the `WEBVTT` header.  Browsers
render WebVTT in a <track>; they render SRT in nothing at all.
"""
import argparse
import re
from fractions import Fraction

CUE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*$")


def to_seconds(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def to_stamp(t, sep=","):
    if t < 0:
        t = 0.0
    ms = int(round(t * 1000.0))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def rescale(text, ratio):
    """Return (scaled_srt_lines, [(old_start, new_start), ...])."""
    out, marks = [], []
    for line in text.splitlines():
        m = CUE.match(line)
        if not m:
            out.append(line)
            continue
        a = to_seconds(*m.group(1, 2, 3, 4))
        b = to_seconds(*m.group(5, 6, 7, 8))
        na, nb = a * ratio, b * ratio
        marks.append((a, na, b, nb))
        out.append(f"{to_stamp(na)} --> {to_stamp(nb)}")
    return out, marks


def to_vtt(srt_lines):
    body = []
    for line in srt_lines:
        body.append(line.replace(",", ".", 2) if " --> " in line else line)
    return "WEBVTT\n\n" + "\n".join(body).lstrip("\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--ratio", default="10/9",
                   help="new_clock / old_clock, e.g. 10/9 or 1.1111")
    p.add_argument("--vtt", default=None, help="also write this WebVTT file")
    a = p.parse_args()

    ratio = float(Fraction(a.ratio))
    text = open(a.src, encoding="utf-8").read()
    lines, marks = rescale(text, ratio)
    srt = "\n".join(lines)
    if not srt.endswith("\n"):
        srt += "\n"
    open(a.dst, "w", encoding="utf-8").write(srt)
    if a.vtt:
        open(a.vtt, "w", encoding="utf-8").write(to_vtt(lines))

    print(f"ratio {a.ratio} = {ratio:.9f}   cues {len(marks)}")
    for label, i in (("first", 0), ("mid", len(marks) // 2),
                     ("last", len(marks) - 1)):
        oa, na, ob, nb = marks[i]
        print(f"  {label:5s} cue {i+1:3d}: {oa:8.3f} -> {na:8.3f} s   "
              f"(end {ob:8.3f} -> {nb:8.3f} s)")


if __name__ == "__main__":
    main()
