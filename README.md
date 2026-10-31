# mars-splidar.github.io

Project page for **MaRS — Markov-Renewal Single-Photon LiDAR Simulator**
(ECCV 2026, Malmö, Sweden).

Weijian Zhang · Prateek Chennuri · Hashan K. Weerasooriya · Bole Ma ·
Stanley H. Chan — Elmore Family School of Electrical and Computer Engineering,
Purdue University.

## What this is and where it deploys

A static, dependency-free site: plain HTML, one CSS file, a handful of small
vanilla-JS modules. No build step, no framework, no bundler.

- **Deploys to:** GitHub Pages at <https://mars-splidar.github.io/>, from the
  `main` branch of `git@github.com:mars-splidar/mars-splidar.github.io.git`.
- `.nojekyll` is present so Pages skips Jekyll — that both speeds up deploys
  and stops it silently dropping any path beginning with `_`.
- No `CNAME`: the site lives on the default `github.io` domain. Do not add one.

Three pages (v2, `v2.0`, 2026-10-23; one 960 px column since `v2.1`, 2026-10-27;
demo first since `v2.2`, 2026-10-29; the results at SBR 0.6 and SBR 1.0
since `v2.3`, 2026-10-30; independent sliders and the Ablation's originals and
zoom rows since `v2.4`, 2026-10-31):

| Path | What it is |
|---|---|
| `index.html` | The lean main page, demo first (v2.2, v2.3, v2.4): the compact hero with the teaser, the cube slicer with preset notes, *In short* with the paper's Fig. 1 top half and its caption, then Accuracy, Efficiency (an animated schematic), Downstream (Poisson- vs MaRS-trained, SBR 0.6 and SBR 1.0, two independent sliders) and the count-model ablation (two-panel chart, then per SBR a row of originals and a row of 2× zooms), the film inline, Go deeper, BibTeX |
| `details/index.html` | Method and full results: v1's seven technical bands, moved verbatim |
| `demos/index.html` | The demo lab, all four panels "coming soon"; **unlinked from every public page** until the playground ships |

**v2.3 in one paragraph (live 2026-10-30, tag `v2.3`).** The teaser keeps
only its guide (two lines at ≥ 900 px). The slicer presets carry hints (*Try
a pixel* / *or a moment*), set Pool to 3 × 3, and show one note per preset
whose claims `build_slicer_data.py --check` tests on the data. *In short* is
now the Fig. 1 card with a new caption, then the paragraph. The paper's
results appear at SBR 0.6 and SBR 1.0, the two SBRs of its main results
table (the supplement adds reflectivity at SBR 5.0 and 10.0, not shown):
`tools/build_result_tiles.py` builds
20 native 200 px tiles from the paper's own sources (depth from the `.npz`
maps with one viridis mapping per scene, reflectivity cropped losslessly from
the Fig. 7 image) with a provenance file, and its `--check` is the tenth
gate. Downstream shows SBR 0.6 (library) and SBR 1.0 (kitchen) with linked
sliders (independent since v2.4-A). The Ablation has a new lead, *The MaRS count model gives the best
results on gold-standard data at both SBR levels*, which `audit_claims.py`
checks on all four test numbers, a two-panel chart and InvProp-style zoom
rows (a draggable window on the ground truth, three panes at 2×). Budgets:
609/609 prose words, 8/9 media.

**v2.4 in one paragraph (2026-10-31, tag `v2.4`; built by v2.4-A, reviewed
and merged by v2.4-B).** Guide §0.9, the author's final changes. The two Downstream sliders move independently, and
the note *Values are test-set averages.* sits under the module. The
Ablation's image captions are names only (the chart keeps the values), and
its footnote ends with the same sentence. Each SBR block of the Ablation is a
row of the four originals (only the ground truth carries the draggable
window), the label *2× zoom of the box*, then a row of the four 2× zooms (the
ground truth's included) under them; on phones each method is one row,
original | zoom. Each tile is fetched once. Budgets: 605/605 prose words,
8/9 media.

**v2.2 in one paragraph (live 2026-10-29, tag `v2.2`).** `/` now leads with
the demos: a compact hero whose teaser and labels fit the first 1280 x 800
screen, the cube slicer, and a mint *In short* band with the paper's Fig. 1
top half (its question removed from the vector PDF). Three result modules
follow: Accuracy (*The first analytic photon-count distribution under dead
time*, with Demo 2), Efficiency (`js/mars-efficiency.js`: the gold standard's
per-photon loop beside MaRS's lookup, shift and sample; no clock and no
runtime number), and Downstream (slider and ground truth at one size, test-set
chips, *Hold to see ground truth* on phones) with the count-model ablation
(`js/mars-ablation.js`). The four gains strip is gone. `/` has no em dash,
en dash or semicolon outside code. Budgets: 598/598 prose words, 8/9 media.

## Source assets live outside this repo and are never modified

Everything in `assets/` is **generated** from the project folder:

```
/home/weijianz399/OneDrive/MaRS_presentations/
```

That folder is **read-only input**. `tools/build_web_assets.py` only ever reads
from it.

- Canonical poster-graphic directory: `poster&slides/assets/`.
- **`poster&slides/MaRS_poster_v2_bundle/` is a stale duplicate. Never read
  from it.** It is missing several files and three of its graphics are older
  than the live ones.

## How to regenerate the web assets

```bash
python tools/build_web_assets.py
```

Prints a source → output table (source px, output px, output bytes) and exits
non-zero if a source asset is missing. Idempotent — a second run reuses
everything that is already current.

Useful flags while iterating:

```bash
python tools/build_web_assets.py --skip-pdf --skip-video
```

`--skip-pdf` reuses the existing downsampled poster (the ghostscript pass is
the slow step); `--skip-video` reuses the existing copy of the 24 MB overview
video; `--force` rebuilds everything.

Requires **Pillow**, and **ghostscript** (`gs`) for the poster downsample. If
`gs` is missing, the script says so and writes no `mars_poster_web.pdf` — point
the Poster button at `mars_poster_full.pdf` and label its size in the button
rather than shipping a 16 MB file behind an unlabelled link.

## How to run the claim audit

```bash
python tools/audit_claims.py
```

Standard library only. Walks every `.html` file and mechanises the project's
claim-hygiene non-negotiables (`WEBSITE_BUILD_STATUS.md` §4 items 1–5 and 11)
plus a canonical-number check against `PROJECT_BRIEF.md` §3.4. Reports every
failure as `file:line` and exits non-zero if there are any.

Two escape hatches, both documented at the top of the script:

- `SANCTIONED_ROUNDINGS` — rounded forms of canonical numbers that approved
  copy genuinely uses (for example the demo lab's "MaRS 1.01 s vs. gold
  standard 40.8 s"). Add to it only for copy that has actually been approved,
  and record why.
- `TITLE_CONTEXTS` — strings containing "Simulator" that must not count as the
  "simulat" half of the 85 ns / 75 ns conflation check, since the paper's own
  title ends in "Simulator".

`--quiet` skips the coverage report and prints failures only.

Since stage 07 the site has **two public pages**, `/` and `/details/`, and the
audit says so: both must exist, neither may link to `/demos/`, 85 ns and
75 ns may not share a band on `/details/`, the gain order is read from the
gains strip on `/`, and "exactly one `.mars-eq`" counts across both.

Since v2.2-D non-negotiable #1's phrase must be **contiguous** on `/`: every
"one table per sensor configuration" is followed at once by ", reused for
every pixel and depth", in visible text and in alt / aria / meta strings, and
the Efficiency module carries it in both schematics and in its screen-reader
note. The old split form ("… configuration is 105 MB instead of 108 GB,
reused for …") fails.

### The two v2 gates (stage 07)

```bash
python tools/page_budget.py          # the main page's budgets, guide 0.1 / 0.6 / 0.7
python tools/details_move_diff.py    # /details/ vs v1.0-launch, band by band
```

`page_budget.py` measures `/` against `MARS_WEBSITE_BUILD_GUIDE.md` §0.1, with
§0.7's limits since v2.2-A — visible words ≤ 605 since v2.4-A, re-pinned at
the measured total after guide §0.9 (the two "Values are test-set averages."
notes +8, the six Ablation caption values −12; the label "2× zoom of the box"
is `.mars-ui`); 609 from v2.3-C, re-pinned at
the measured total after guide §0.8's Ablation with SBR 1.0 and the zoom rows
(the footnote's last sentence −9, the old tile captions −23, two zoom-row
headers +4, two "Ground truth drag the box" captions +10 and six count-model
captions +28; the lead swapped one 15-word sentence for another); 599 from
v2.3-B, re-pinned at the measured total after guide §0.8's two-scene Downstream (the note under the
module −17, the old image chips −8, the two SBR headers, two "Ground truth"
captions and four slider captions +20); 604 from v2.3-A, re-pinned at
the measured total after guide §0.8's copy (the teaser tagline removed −8, the
new Fig. 1 caption +14); 598 from v2.2-D, re-pinned after the author's copy
changes (the slicer eyebrow +3, the BibTeX "Provisional entry" note removed
−5); 600 from v2.2-P, re-pinned when
Demo 2's 12 chart words became schematic text (612 from v2.2-C, pinned at that stage's measured total by the author; 520 from
v2.2-A, 420 from v2.1-A, 350 before), at most nine media slots above BibTeX (six from v2.1-A, exactly four
before), zero switch bars, zero
display equations, and each demo's title and single sentence — and exits
non-zero on a breach. Its docstring defines exactly what counts as a word and
as a media item. Since v2.1-C it counts PROSE only: text inside a `.mars-ui`
element (control labels, legends, axis text) is reported
separately as "UI words" and is not held against the 420; it also checks the
cube slicer's title, guiding text and media slot. Since v2.2-B text inside a
`.mars-schematic` element (the Efficiency diagram's SVG labels) is reported
the same way, once per SVG, and `#demo-efficiency` may hold its three-sentence,
38-word lead (the limit is pinned at that approved length). Since v2.2-C
`#demo-downstream` may hold three sentences and `#demo-ablation` two (the
stage doc's verbatim leads). Since v2.2-P Demo 2's two charts sit in
`.mars-schematic` wrappers too, so their words are reported, not counted. `details_move_diff.py` extracts each of the seven bands,
banner comment included, from `git show v1.0-launch:index.html` and from
`details/index.html`, undoes the `../` path prefix and diffs them; the only
allowed difference is the Simulator card's demo-lab link.

### The Demo 2 graphic (stage 09)

```bash
python tools/build_demo_count.py            # needs the Dead_time env
python tools/build_demo_count.py --check    # writes nothing; the gate form
```

Regenerates `assets/img/demo_count.svg` from the repo's stored count results
(through `video/data.py::count_distributions()`, at S = B = 8.2,
t_d = 75 ns) and splices the same SVG into `index.html` between the
`demo_count:start` / `demo_count:end` markers, so never edit it by hand.
It prints the operating point, the realization count and every model's
stored vs plotted mean and variance, asserts that no `<text>` node or the
`aria-label` carries a digit, and exits non-zero on any mismatch or, with
`--check`, on drift between the script, the file and the inline copy.
Since v2.2-P it also draws the phone chart (`assets/img/demo_count_phone.svg`,
340 x 240 units, spliced between the `demo_count_phone:` markers, shown at
≤ 600 px) from the same arrays and runs the same text checks on it; the
desktop SVG is unchanged, byte for byte.

### The cube slicer (stage v2.1-C)

```bash
python3 tools/build_slicer_data.py            # numpy only; writes assets/data/slicer/
python3 tools/build_slicer_data.py --check    # writes nothing; the gate form
python3 tools/build_slicer_placeholder.py     # Playwright + Chrome; the four stills
```

`build_slicer_data.py` exports the paper's Fig. 1 cubes from the project folder's
`video/web/hero/out/cubes.npz` (read only, sha256-pinned) to
`assets/data/slicer/`: three gzip cubes, the delay map and `meta.json`
(brightness constant from the gold cube, the four data-picked presets, provenance).
It fails if the bright preset does not show gold and MaRS 2-3 ns earlier than
Poisson, and splices the default readout into `index.html`
(`slicer_readout` markers); `--check` fails on any drift, including that text.
Since v2.3-A it also holds the four preset notes (guide §0.8; `NOTES`, the only
place they are written): it writes them to `meta.json` for `js/mars-slicer.js`,
splices the default (bright) note and four aria-hidden height-reserving copies
into `index.html` (`slicer_note` markers), and turns every claim in a note into
a rule on the data (photons over 3 × 3 pixels × 3 bins around the preset):
`--check` fails if a rule no longer holds at 3 × 3, or if the shipped block
drifts. The same rules are reported, not gated, at 1 × 1 and 5 × 5.
`build_slicer_placeholder.py` re-captures the placeholder stills
(`assets/img/slicer_ph_*.webp`) from the live module; re-run it after any
change to the module's drawing, the data or the fonts. Never edit either output
by hand. `js/mars-slicer.js` is fetched by `js/mars-main.js` only when the
reader scrolls near the block (never on a cold load).

### The result tiles (stage v2.3-B)

```bash
python3 tools/build_result_tiles.py            # numpy + Pillow; writes assets/img/res/
python3 tools/build_result_tiles.py --check    # writes nothing; the gate form
```

Builds every Downstream and Ablation tile, both test scenes (SBR 0.6, library 00357; SBR
1.0, kitchen 00767) and both maps, into `assets/img/res/`:
`{refl,depth}_{sbr06,sbr10}_{gt,poisson,renewal,zhang,mars}.webp` (20 files,
200 × 200, lossless) and `provenance.json`. Sources are read only, outside the
repo, in `~/OneDrive/MaRS/Figs/main/`: depth from the networks' native 200 × 200
`.npz` maps (one viridis mapping per scene, the GT's min to max, the same for
every method), reflectivity cropped at native size from
`mars_cvpr2026-Page-1.drawio.png`, the lossless image the paper's Fig. 7
embeds (tile boxes found by script from the alpha channel and printed; never
`Fig6_*`). No resampling and no sharpening; `--check` rebuilds everything,
compares bytes and `provenance.json`, and decodes every tile against its
source pixels. Byte equality needs the same encoder: run it with the base
`python3` (Pillow 10.4.0, libwebp 1.3.2, both recorded in the provenance).
The old `assets/img/res_*` tiles stay for `/details/` only (the main page no
longer uses them since v2.3-C; stage 11 decides).

### The hero teaser (stages 08, 09b)

`assets/media/anim_hero_cubes{,_960}.{webm,mp4,jpg}` are built **outside this
repo**, in the project folder's `video/web/hero/`, from the paper's own Fig. 1
cubes. To rebuild them, run this in the `Dead_time` env (about 2-3 min):

```bash
cd /home/weijianz399/OneDrive/MaRS_presentations/video/web/hero
python final.py
```

That writes `out/anim_hero_cubes{,_960}.*` and `out/provenance.json`, and runs
every `WEBSITE_BUILD_STATUS.md` §3.7 check. Then copy the six files into
`assets/media/` byte for byte, and confirm the copy with md5 against
`provenance.json`. `video/web/hero/README.md` is the full reference. No
`mediaAvailable` entry is needed: the teaser is not a `.mars-media` slot.

### The other three checks

```bash
python tools/check_links.py https://mars-splidar.github.io
```

**The base URL is a required argument** — run bare, `check_links.py` tracebacks
rather than printing usage. Stages 04, 05 and 06 each hit that; it is recorded
here so the next session does not. It resolves every `href`, `src` and
`srcset` on both pages plus the URLs `js/site.config.js` injects, and reports
external links without following them. With no page arguments it checks `/`
and `/details/`; since stage 07 it also HEAD-checks every `data-src` /
`data-poster` whose basename is declared in `mediaAvailable`, resolved against
the page that carries it — the by-path sweep stage 06 asked for, because a
missing animation file otherwise renders as a blank frame that nothing
reports. Point it at `http://localhost:8731`
to check a working tree before pushing.

```bash
python ../../build_instructions/reference/w6_table_diff.py    # run from HERE, the repo root
python ../../video/web/provenance.py                          # needs the Dead_time env
```

`w6_table_diff.py` parses the expected values straight out of
`PROJECT_BRIEF.md` §3.4/§3.5/§3.6 and diffs them against the rendered cells of
all four HTML tables plus the runtime caption's stage breakdown; an empty diff
is the pass. It reads `index.html` and `details/index.html` from the current
directory (all four tables live on `/details/` since stage 07, and each must
appear exactly once across the two), so run it from the repo root, not from
`build_instructions/`. `provenance.py` recomputes every
number burned into all five animation frames and exits non-zero on drift —
neither script can see numbers burned into the twelve static poster graphics,
which is why stage 06's handoff carries a hand-built provenance table for
those.

## How to preview locally

```bash
python -m http.server 8731 --bind 127.0.0.1
```

then open <http://127.0.0.1:8731/index.html>. Serve it rather than opening the
file directly — `file://` breaks the clipboard API and relative asset paths.

## Repository layout

```
index.html              main page — the lean v2 pitch (stage 07)
details/index.html      the seven v1 technical bands, moved verbatim (stage 07)
demos/index.html        demo lab — unlinked from public pages since v2
css/mars.css            design tokens + every component
js/site.config.js       EVERY external URL, in one object (resolved against
                        the site root, so it works from /details/ too)
js/mars-redirect.js     old /#<band> anchors -> /details/#<band> (stage 07)
js/mars-nav.js          sticky nav, hamburger, hero button row
js/mars-main.js         main page only: teaser, video poster, BibTeX copy
js/mars-compare.js      main page only: Downstream before/after slider (stage 09),
                        hold to see ground truth on phones (v2.2-C), several
                        sliders in one figure (v2.3-B), independent (v2.4-A)
js/mars-ablation.js     main page only: the count-model ablation (v2.2-C): the
                        two-panel chart and the zoom rows (v2.3-C), originals
                        row + zoom row per SBR (v2.4-A)
js/mars-slicer.js       main page only: the cube slicer, loaded on demand (v2.1-C)
js/mars-efficiency.js   main page only: the Efficiency schematic's animation (v2.2-B)
js/mars-sections.js     the stub gate (now loaded by /details/ only)
js/mars-switchbar.js    the switch-bar (tab) pattern (/details/)
js/mars-media.js        scroll-triggered animation slots (/details/)
assets/img/             generated *.webp + *.png, + video_poster.jpg
assets/media/           the five section animations (stages 04, 05) + the
                        hero teaser anim_hero_cubes (stage 08, landed 09)
assets/docs/            poster PDFs, paper PDF, overview video + captions
tools/build_web_assets.py
tools/audit_claims.py   claim hygiene, both public pages
tools/check_links.py    every reference, both public pages
tools/page_budget.py    the main page's guide-0.1/0.6 budgets (stage 07, v2.1-A)
tools/build_fig1_context.py  Fig. 1's top half without the question, + the two
                        tight phone crops, from the paper PDF; --dry-run compares
                        by md5 (v2.2-A; build_fig1_question.py retired in v2.2-D)
tools/measure_edges.py  visible edges vs the column, both pages; not a gate (v2.1-A)
tools/build_demo_count.py  Demo 2's SVG from video/data.py, + provenance (stage 09)
tools/build_slicer_data.py  the slicer's data + default readout, --check gate (v2.1-C)
tools/build_slicer_placeholder.py  the slicer's placeholder stills (v2.1-C)
assets/data/slicer/     the slicer's cubes, delay map and meta.json (v2.1-C)
tools/build_result_tiles.py  the 20 result tiles (Downstream, Ablation) + provenance, --check gate (v2.3-B)
assets/img/res/         the result tiles, both SBRs, both maps (v2.3-B)
tools/details_move_diff.py  proves /details/ is v1's bands verbatim (stage 07)
```

## Editing rules that are not obvious from the code

- **`js/site.config.js` is the only place a URL belongs.** A `null` URL renders
  nothing clickable: since v2.2-A, plain grey text "<Label> coming soon" after
  the hero buttons (it was a `· soon` pill). Never `href="#"`, never a link to
  a missing file — the audit greps for it.
- **Eyebrows on `/` are sentence case** (v2.2-A): `body.mars-home` drops the
  uppercase transform and the tracking, so write the label as it should read.
  `/details/` keeps its uppercase eyebrows until stage 11.
- **`--gold` (#CFB991) is ONLY EVER A FILL** — background, pill, bar,
  underline, border. Never a text colour, at any size; the "display numeral ≥
  2rem" exemption was removed in stage 1.5 because gold on mint measures
  1.73:1, failing even the large-text bar. Gold-coloured *text* on a light
  surface uses `var(--aged-fg)`, which resolves to `--aged` on paper (4.51:1)
  and `--aged-text` #806438 on any mint surface (5.00:1). Gold text on **ink**
  is legitimate at 9.36:1 and has its own token, `--ink-accent`.
  `tools/audit_claims.py` fails on any `--gold` used as a `color:`, and checks
  every other pair at 4.5:1.
- **Unfinished sections are gated, not stubbed.** `sectionsLive` in
  `js/site.config.js` lists the content bands that are finished; anything not
  listed has its band *and* its nav anchor removed from the DOM. Same idea for
  animations: `mediaAvailable` lists the media basenames that actually exist,
  and a slot not listed requests nothing (a `<video poster>` pointing at a
  missing file is fetched by the preload scanner and 404s).
- **`--ink` appears in exactly two places on the main page:** the sticky nav
  strip and the closing BibTeX/footer band. The demo lab's dark sidebar is the
  third, sanctioned use, and it is deliberate — do not "fix" it.
- **Exactly one display equation on the whole site**, the CLT count law, in a
  `.mars-eq` container. The audit fails on a second one.
- **The BibTeX entry is final** (author, 2026-10-29: the ECCV camera-ready is
  settled), so `/` no longer carries a "Provisional entry" note under it. It
  has no page numbers or volume. Do not invent them.
- **The hero title's gold letters are `MaRS`, `Ma`, `R`, and the `S` of
  *Simulator*** — not the `S` of *Single-Photon*. `MaRS` = **Ma**rkov-**R**enewal
  **S**imulator.
- **The hero title fills the column exactly** (v2.1-A): one line above 600 px;
  at 600 px and below (v2.1-D) two lines of one size, *MaRS: Markov-Renewal* /
  *Single-Photon LiDAR Simulator*, the second filling the column. All sized in
  `cqi` from a measured INK width (`--title-em`, `--line2-em` and the side
  bearings in `css/mars.css`). Re-measure with `tools/measure_edges.py` if you change the
  font, a weight, the tracking, the wording or `--column`.
- **One column** (v2.1-A): `--column` 960 px and `--gutter` 16 px. A box that
  carries the column is `max-width: calc(var(--column) + 2 * var(--gutter))`
  with the gutter as padding. Do not add prose caps (`ch` max-widths).

Full context: `PROJECT_BRIEF.md` (facts and claim hygiene),
`MARS_WEBSITE_BUILD_GUIDE.md` (structure, copy, design) and
`WEBSITE_BUILD_STATUS.md` (contracts, filenames, stage scope) in the project
folder.

## Stage log

Each build stage appends one line here.

- **Stage 01 — foundation (2026-09-07).** Replaced the placeholder page. Site
  tree, `css/mars.css` design system, `js/site.config.js`, the four JS modules,
  `tools/build_web_assets.py` (31 outputs), `tools/audit_claims.py`, a finished
  `index.html` shell (nav, hero, four gains, Limitations, BibTeX/footer band,
  six stubbed content bands, five empty animation slots) and the
  `demos/index.html` shell. 27 of 28 verification checks pass; the 28th (V22)
  is expected to fail on the `mars-todo` stubs until stage 02.
- **Stage 1.5 — conference launch (2026-09-07).** First push to production, for
  the ECCV poster's QR code. Made `--gold` fill-only and re-treated the four
  gains as dark numerals on gold plates (8.64:1); added `--aged-text` #806438
  and the `--aged-fg` per-surface indirection; added a contrast pass to
  `tools/audit_claims.py`, which now exits 0 for the first time. Added the
  `sectionsLive` stub gate (`js/mars-sections.js`) and the `mediaAvailable`
  media gate, removing the six unfinished bands, their nav anchors and all
  five missing-poster 404s. Added the three-cube hook figure, an inline SVG
  favicon, and the paper as a 2.97 MB web copy (300 dpi, lossless) plus the
  25.3 MB original. Added `tools/check_links.py`, which resolves every
  reference a page actually makes — including the URLs injected at
  runtime from `site.config.js` — against a live URL; that is what caught
  the poster 404s. All 17 W-checks pass. FCP on Slow 3G is 6.2 s against
  the guide's 1.5 s budget; stage 06 owns it, the diagnosis is in the
  stage 1.5 handoff.
- **Stage 02 — main-page content (2026-09-08).** Wrote the six content bands —
  Motivation, Approach, Contributions, Theory, Simulator, Utility — with final
  copy, twelve static figures, four real HTML tables (count accuracy,
  cube runtime, capability matrix, val→test transfer, all cell-checked against
  `PROJECT_BRIEF.md`), five working switch bars over twelve panels, the ten
  SBR 0.6 result tiles, and the site's single display equation as marked-up
  text rather than an image. The five animation slots moved into their Method
  panels unchanged. **`sectionsLive` is deliberately still empty: the bands are
  written but not published, and turning them on is the author's call.**
  Pushed separately and first, on its own: the render-blocking-font fix — the
  Tabler stylesheet is now `media="print"` with an `onload` flip, which took
  FCP on Slow 3G from 6.17 s to 4.94 s. It did **not** shrink total load; the
  801 KB Tabler webfont is still fetched and is 20.5 s of the 26.6 s load, so
  inlining the 16 glyphs as SVG is the remaining win. `audit_claims.py` still
  exits 0, with `CANONICAL` completed from the brief's §3.5 table and the
  stage-01 placeholder grep narrowed so it stops matching the phrase
  "high flux". All 17 W-checks pass.
- **Stage 04 — web-loop harness + Theory animations (2026-09-12).** Pushed, on
  its own and first: the Video button now serves the author-narrated
  `v3_voice_0.9x` cut (24.70 MB, 4:30.9) in place of the v1 one, with captions
  scaled from the un-slowed v3-voice `.srt` by exactly 10/9 — a ratio that is
  exact by construction, since both files decode to the same 7316 frames at
  30 fps and 27 fps, and was checked against frame alignment and 77 detected
  speech onsets before it was trusted. `tools/retime_srt.py` is the script.
  The `.srt` is now accompanied by a `.vtt` wired into the lightbox as
  `<track kind="captions">`, because SRT is not a format any browser renders
  and the player had no CC button at all. Committed but **not** published: the
  two Theory animations, `anim_theory_countlaw` (6.5 s) and
  `anim_theory_covariance` (6.0 s), built from the film's `s06_clt` and
  `s07_covariance` by the new harness in `video/web/` — `mediaAvailable` is
  still empty, so nothing on the rendered page requests them yet. Every number
  in them recomputes from `video/data.py`; the count-law animation contains no
  equation, by construction rather than by inspection.
- **Stage 05 — simulator + motivation animations (2026-09-13).** Pushed, first
  and on its own: **the site's first real content.** `sectionsLive` now carries
  `approach`, `contributions`, `theory`, `simulator` and `utility`, and
  `mediaAvailable` the two Theory animations — so the page grew from a hero,
  four gains and a citation to five bands, seven nav anchors and two playing
  loops. Before publishing, the §3.2 type floor was split in two — meaning-
  bearing text (title, callout) to 5.5% of frame height, plot furniture
  unchanged at 2.5% — because the media frame is only 343 CSS px wide on a
  375 px phone; both Theory animations were re-rendered against it, which moved
  their callouts from 32/37 px to 47 px and cost `anim_theory_countlaw`'s two
  words. Each slot's `<figcaption>` now repeats its animation's title as **real
  text**, since text burned into a video cannot be selected, translated or read
  by a screen reader. Committed but **not** published: the last three
  animations — `anim_motivation_scaling` (6.0 s, both measured runtime curves
  from `runtime_scaling_num_pixels.npz`), `anim_sim_pipeline` (6.0 s, the three
  vectorized stages with their measured costs and their `our_sim.py` entry
  points) and `anim_sim_lut` (7.0 s, the delay axis leaving the table,
  108 GB → 105 MB). None compresses time, so none carries a badge.
  `motivation` stays gated until they go live, because its slot is the whole
  band. `audit_claims.py` exits 0 and `check_links.py` reports zero broken
  against the live URL — note it takes that URL as an argument:
  `python tools/check_links.py https://mars-splidar.github.io`.
- **Stage 06 — integration, claim audit, performance, accessibility, launch
  (2026-09-14). THE SITE IS COMPLETE.** Deliberately a different session from
  every build stage, so that one independent pass checked every headline
  number and interactive claim before publishing. Six commits.
  **Published the rest:** `sectionsLive` is all six bands (`motivation`, the
  first one, was the last hold-out) and `mediaAvailable` is all five
  animations. **Q14:** `js/mars-media.js` no longer promotes `data-poster` /
  `data-src` or calls `video.load()` at init — that cost a measured 1.52 MB
  at `scrollY === 0`, five posters and five *entire* `.webm` files, including
  for a slot in a `hidden` tab panel. Promotion moved to a second
  IntersectionObserver at threshold 0 with a 300 px `rootMargin`, so a cold
  load now fetches **zero bytes** of media and the 35 % play/pause rule is
  untouched. **Q10:** the Tabler icon webfont is gone — 801 KB in one request,
  20.5 s of a 26.6 s Slow-3G load, for **nine** glyphs in **eleven** elements,
  now inline `<svg class="mars-ico">` with `stroke="currentColor"`. Every doc
  predicted a class-wide rename; it was three files and one CSS rule.
  **Q16:** the demo lab was advertising the dead-time playground as **Live**,
  over an empty div whose body read "Stage 03 supplies
  `demos/js/playground.js`" — a false capability claim plus a leaked build
  note on a page public since stage 1.5. All four panels now read "Coming
  soon" and the playground panel describes what it will do.
  **Q11:** `sim_lut.png`'s burned-in headline was "A depth change only shifts
  the registered histogram", the unqualified form the brief rejects;
  regenerated to "At fixed signal and background, a delay change only shifts
  the histogram". The **printed** poster still carries the old line.
  **The runtime axis:** the resolution sweep and the 40.831 s cube are
  different benchmarks, and both the Motivation animation's figcaption and
  `sim_pixels.png`'s caption now say so. **Accessibility:** the hero had no
  `<h1>` in the accessibility tree below 380 px (the fallback used
  `display:none` and its visible replacement is `aria-hidden`), and the
  fallback's breakpoint was 10 px narrower than an iPhone, so the title
  rendered at 13.3 px on a 390 px phone. Both fixed. **E4 resolved** — arXiv
  2512.04924, verified against arxiv.org before wiring. **E5 deferred** —
  `Code · soon` is the one hero button still a pill. Gates: `audit_claims.py`
  exits 0, `check_links.py` zero broken, `w6_table_diff.py` empty,
  `video/web/provenance.py` exits 0, no body overflow at 320 px with every
  tab open, `prefers-reduced-motion` suppresses all five loops.
  **One method note that matters for anyone verifying this site in a headless
  or non-compositing browser:** `requestAnimationFrame` never fires there, so
  the nav's *measured* tightening silently does not apply and a width sweep
  will report a phantom 59–136 px overflow at 741–919 px. Shim rAF to
  `setTimeout` before trusting any layout measurement. Same root cause as the
  `IntersectionObserver` failure that cost three earlier sessions.
  Also fixed: `tools/build_web_assets.py` was **unrunnable** — it resolved the
  v1 video filenames that stage 04 superseded, through a check that fired
  before `--skip-video` could spare it, so the whole script exited 1.
  **One consequence of the media deferral to know before adding a sixth
  animation:** `.has-media` is now set at init for every basename in
  `mediaAvailable`, so a *missing* file no longer falls back to the labelled
  placeholder — it renders as an empty white 16:9 frame, permanently, and
  nothing catches it. A cold load requests nothing from `assets/media/` by
  design, and `check_links.py` cannot see those URLs because they ship as
  `data-poster` / `data-src`. **Verify `assets/media/` by path.** All 15 files
  were confirmed 200 with byte-exact sizes against production at launch.
- **Stage 07 — v2 restructure: a lean `/` and a `/details/` page
  (2026-10-23).** On branch `v2-redesign`, not pushed. The seven technical
  bands moved **verbatim** to `details/index.html` (`tools/details_move_diff.py`
  proves it: six bands identical, one allowed edit — the Simulator card's
  demo-lab link now reads *See the simulator ↓*). `/` was rebuilt to guide §0.3
  with interim media: hero + teaser slot (`hook_tradeoff` as the LCP image;
  stage 09 drops in `anim_hero_cubes` with no other edit, and a missing file
  leaves the raster showing rather than a blank box), *In short* + the four
  gains, two result demos (`theory_count`; a Poisson-/MaRS-trained two-up),
  the film inline with a deferred title-card poster and `.vtt` captions, *Go
  deeper*, BibTeX. 343 visible words against v1's ≈2,440 — counted in
  the final state, with the teaser's label row that stage 09 un-hides (303 as
  rendered today); `tools/page_budget.py` gates it at 350. Old `/#theory`-style
  anchors redirect to `/details/` (`js/mars-redirect.js`). `site.config.js`
  now resolves its URLs against the site root, which is what makes "Read the
  paper" work from `/details/`. Fixed a v1 defect stage 06 could not see: the
  tables' visually-hidden `<caption>` leaked 206 px of body overflow at 320 px
  in real Chrome. New gate `tools/page_budget.py`; `audit_claims.py`,
  `check_links.py` and `w6_table_diff.py` now cover both pages. All
  measurements came from real headless Google Chrome 154 via Playwright, with
  no rAF shim; they are in `build_instructions/review/stage07/`.
- **Stage 07h — live hotfix, mobile horizontal overflow (2026-10-23),
  `v1.0.1`.** Every phone had the whole page scrolling sideways — 206 px of
  overflow at 320 px, 151 at 375, 136 at 390, 96 at 430 — because each table's
  visually-hidden `<caption>` is `position: absolute` and its scroll wrapper
  `.mars-table-wrap` was not its containing block, so the caption's box leaked
  to the page (the default Utility panel, the capability matrix, triggered it
  with no tab opened). One declaration, `position: relative` on
  `.mars-table-wrap`; 0 overflow at all eight widths from 320 to 1440 with
  every panel open, tables still scroll inside their wrappers, captions still
  visually hidden. Stage 06 had measured 0 here through iframe probes in a
  non-compositing pane; stage 07 found it in real Chrome. The same line is on
  `v2-redesign`.
- **Stage 09 — v2 core demos (2026-10-23).** On `v2-redesign`, not pushed;
  `main` (07h) merged in first. `/` is now content-complete: the hero shows
  stage 08's `anim_hero_cubes` over its own poster (the LCP; the video is
  started by `js/mars-main.js`, never under reduced motion or Save-Data, and
  a missing file leaves the poster and the HTML label row on screen); Demo 2
  is a generated, inlined count-distribution SVG with no number inside it
  (`tools/build_demo_count.py`, which reads `video/data.py` and checks its
  own provenance); Demo 3 is a keyboard-operable before/after slider
  (`js/mars-compare.js`) with the test-set numbers on each side.
  `js/mars-lightbox.js` deleted; the head descriptions attach the 128×128×1024
  workload to the 40×. 348/350 words. All gates exit 0; review pack in
  `build_instructions/review/stage09/`.
- **Stage 09b — polish (2026-10-23).** Demo 2 now leads with the reference:
  gold-standard bars as the anchor, MaRS the strongest line on top, the two
  prior models lighter and thinner (Zhang et al. dashed). The teaser is
  cropped to 1920 × 448 from the unchanged render, so the label row ends on
  the first 1280 × 800 screen (773 px), and phones load
  `anim_hero_cubes_960.*` (a 390-px cold load fell from 1.75 MB to 660 KB).
  348/350 words; all gates exit 0; review pack in
  `build_instructions/review/stage09b/`.
- **Stage 10 — independent review, merge and launch (2026-10-23), `v2.0`.**
  A session that built none of v2 re-measured it:
  - every gate, on both pages;
  - the twelve non-negotiables, page by page;
  - a number-provenance table for `/`;
  - the teaser stepped frame by frame, and Demo 2's SVG grepped;
  - real headless Chrome and Firefox, at eight widths;
  - Lighthouse, mobile and desktop.

  It found no rule violation. One fix: the hero button row now reserves its
  space while it is empty, so `js/mars-nav.js` filling it no longer pushes the
  teaser down; mobile CLS on `/` fell from 0.11-0.27 to 0.05-0.20.
  `v2-redesign` was merged into `main` and tagged `v2.0`. The review pack and
  the author's phone checklist are in `build_instructions/review/stage10/`.
- **Stage 10b — post-launch polish (2026-10-26), `v2.0.1`.** Six of stage
  10's non-blocking items, each in its own commit:
  - **Share card.** `tools/build_og_card.py` builds it from the teaser's
    frame 0, with no timing or speed number. `build_web_assets.py` no longer
    builds a card.
  - **Fonts.** Self-hosted in `assets/fonts/` (latin Poppins + Inter, OFL),
    preloaded, with metric-matched fallbacks. There are now zero third-party
    requests, and `audit_claims.py` checks that. Lighthouse mobile CLS on `/`
    is 0.000 in 5 of 5 runs.
  - **Demo 3 on touch.** The slider moves only once a sideways drag is
    recognised.
  - **`/details/`** honours Save-Data, with 0 video bytes.
  - **Poster size label** is now decimal: 16 MB.
  - **Film poster** is the Four gains card.

  Review pack: `build_instructions/review/stage10b/`.
- **Stage v2.1-A — one column and the question (2026-10-26).** On branch
  `v2.1`, not pushed. Every block on `/` and `/details/` now shares one
  960 px column (viewport − 32 px below), judged by visible edges
  (`tools/measure_edges.py`); the title's ink meets both column edges at every
  width, the narrow fallback's two lines too. The top half of the paper's
  Fig. 1 sits between the buttons and the teaser (two stacked crops on
  phones, `tools/build_fig1_question.py`). `/details/` fetches no video under
  reduced motion. Budgets 420 words / 6 media. Review pack:
  `build_instructions/review/v21A/`.
- **Stage v2.1-C — the cube slicer (2026-10-26).** On branch `v2.1`, not
  pushed. Directly under the teaser, in its own band (`#slicer`): three linked
  time slices of the Fig. 1 cubes (one brightness mapping, fixed from the gold
  cube) over one raw-count histogram, four data-picked presets, pooling and
  range. Nothing of it loads until the reader scrolls near it; a pixel-exact
  still stands in until then; Save-Data gets a button. `page_budget.py` now
  reports `.mars-ui` control text separately (prose 420/420, media 6/6);
  `build_slicer_data.py --check` joins the gates. Review pack:
  `build_instructions/review/v21C/`.
- **Stage v2.1-D — land the teaser, guiding sentence, layout fixes
  (2026-10-26).** On branch `v2.1`, not pushed. v2.1-B's re-cut teaser
  (1920 x 484 / 960 x 242; the cubes reach the column edges, the label row is
  centred under them; the share card rebuilt from its frame 0, `?v=3`); the
  teaser's guiding sentence; a balanced two-line title at <= 600 px; Demo 3 as
  a 400 px slider beside a side panel (toggle, test-set numbers, ground truth);
  Demo 2's chart about 376 px tall. In short and the BibTeX note trimmed: prose
  419/420. Review pack: `build_instructions/review/v21D/`.
- **Stage v2.1-E — independent review, merge and launch (2026-10-27),
  `v2.1`.** A session that built none of v2.1 re-measured it: the twelve
  non-negotiables per page (Fig. 1's burned-in text, the teaser labels, both
  guiding sentences, the slicer, the trimmed In short, the share card); a
  number-provenance table for `/`; the slicer's readouts recomputed from
  `assets/data/slicer/` with independent code (four presets, three pools, and
  six further pixels incl. border and corners: all match); the teaser stepped
  every 0.5 s in all four encodes; all nine gates; Chrome and Firefox at
  twelve widths on both pages; Lighthouse mobile and desktop. No rule
  violation and no defect needing a fix. `v2.1` was merged into `main`
  (`--no-ff`) and tagged `v2.1`. Review pack and the author's v2.1 phone
  checklist: `build_instructions/review/v21E/`.
- **Stage v2.2-A — compact hero, demo-first order, the In short band
  (2026-10-28).** On branch `v2.2-dev`, not pushed. The hero is the approved
  "Compact" mock (smaller buttons with icons, "Code coming soon" as plain
  text), so the teaser's label row ends at 653 px at 1280 x 800. Order: hero,
  teaser, slicer, then a mint In short band holding the 63-word paragraph and
  the paper's Fig. 1 top half without its question (removed from the vector
  PDF by `tools/build_fig1_context.py`: 0 px changed outside that region),
  lazy by script. The four gains strip is gone (`audit_claims.py` retires its
  order check for `/`). New copy from guide §0.7. Prose 458/520, media 6/9.
  Review pack: `build_instructions/review/v22A/`.
- **Stage v2.2-B — the Efficiency module (2026-10-28).** On branch
  `v2.2-dev`, not pushed. `article#demo-efficiency` sits between Accuracy and
  Downstream: the approved concept as two inline SVGs (wide, and a stacked
  phone layout at ≤ 600 px), animated by `js/mars-efficiency.js` only while on
  screen and the tab is visible; reduced motion draws the end state once. Its
  note carries 105 MB / 108 GB, the "one table per sensor configuration"
  phrase and "At fixed S and B", all checked by `audit_claims.py`. Smallest
  text 12.5 px at the 960 px column, 12.5 px at 375. CLS 0. Prose 502/520,
  media 7/9. Review pack: `build_instructions/review/v22B/`.
- **Stage v2.2-C — Downstream and the count-model ablation (2026-10-28).**
  On branch `v2.2-dev`, not pushed. `#demo-downstream` is now *Ignoring dead
  time biases downstream networks*: the Poisson-trained vs MaRS-trained slider
  and the ground truth as two equal squares, the test-set numbers as chips on
  the image corners, and on phones a *Hold to see ground truth* button
  (pointer, touch, Space / Enter; a screen reader's click toggles it). New
  `#demo-ablation`, *Why an accurate count model matters*: a dumbbell chart
  (val vs test for the Renewal, Zhang et al. and MaRS count models, drawn by
  `js/mars-ablation.js` from a visually hidden table) and four tiles, with
  the footnote that there is no separate Renewal or Zhang et al. simulator.
  `audit_claims.py` checks the table, captions and chips against
  PROJECT_BRIEF §3.5 and requires the footnote. Prose 612/612 (limit pinned
  by the author), media 8/9. CLS 0. Review pack:
  `build_instructions/review/v22C/`.
- **Stage v2.2-P — the phone pass (2026-10-28).** On branch `v2.2-dev`, not
  pushed. `/` at ≤ 600 px takes the approved phone mock's scale: leads and In
  short 16 px, smaller hero and module buttons, 1.6rem bands, teaser labels as
  name + time (descriptors visually hidden, still read and counted), the Fig. 1
  inference crop re-cut tight (`fig1_context_infer_tight*`, no arrow, no blank
  band) at 68 % of the card. Efficiency: the stacked SVG up to 971 px (the wide
  one's text reaches 12 px only from there), 914 units tall (was 1116), 30
  drawn frames/s. Demo 2: a phone chart (`demo_count_phone.svg`, ≥ 200 px) and
  its words now schematic, so the word limit is re-pinned at 600. Ablation:
  each val ring drawn above its test dot. No copy changed; desktop pixel-
  identical outside the dumbbell. Page at 390 px 8149 → 7182 px. Review pack:
  `build_instructions/review/v22P/`.
- **Stage v2.2-D — copy pass and cleanup (2026-10-29).** On branch
  `v2.2-dev`, not pushed. The author's copy: the Accuracy title loses its full
  stop, the slicer eyebrow is *Cube slicer · Visualize dead-time effects*, the
  Efficiency note reads *So one table per sensor configuration, reused for
  every pixel and depth, is 105 MB instead of 108 GB.* (`audit_claims.py` now
  requires #1's phrase contiguous on `/`), and the BibTeX note is gone (the
  entry is final). Every "—", "–" and ";" outside code on `/` (title, meta,
  alt, aria, the slicer's load-failure text, the Accuracy caption and the
  limitations line) became a full stop or comma. Word limit re-pinned
  at 598. Removed: the unused `.mars-btn.is-soon` / `.mars-btn__soon` and
  `.mars-closing__note` CSS, `fig1_question*`, v2.2-A's `fig1_context_acq*` and
  `fig1_context_infer*`, `tools/build_fig1_question.py`. The phone acquisition
  crop is re-cut before the arrow (`fig1_context_acq_tight*`). Review pack:
  `build_instructions/review/v22D/`.
- **Stage v2.2-E — independent review, merge and launch (2026-10-29),
  `v2.2`.** A session that built none of v2.2 re-measured it: the twelve
  non-negotiables on `/` with the Accuracy title's "first analytic",
  Downstream's "fails / works" and the ablation's "closer to the truth"
  traced to paper lines; a number-provenance table; the slicer readouts
  recomputed from the shipped data (exact); the Efficiency schematic stepped
  every 0.5 s under a fake clock in both layouts (no number, no clock, steps
  in order); all nine gates; Chrome and Firefox at twelve widths on both
  pages; keyboard, touch and the hold button; cold-load bytes; Lighthouse.
  Two commits: the page title with a colon (author-approved) and a visible
  focus ring on the film player (`.mars-video__player:focus-visible`, the
  frame's `overflow: hidden` had clipped it). Merged into `main` (`--no-ff`)
  and tagged `v2.2`. Review pack and the author's v2.2 phone checklist:
  `build_instructions/review/v22E/`.
- **Stage v2.3-A — teaser caption, slicer preset hints and notes, In short
  reordered (2026-10-30).** On branch `v2.3-dev`, not pushed. Guide §0.8's
  copy: the teaser tagline is gone and its guide is the whole caption (two
  lines at ≥ 900 px, one sentence each); the slicer presets read *Try a pixel*
  [Bright surface] [Dim surface] *or a moment* [Just after the peak] [Before
  the peak], with one aria-live note under them that follows the selected
  preset and empties, keeping its height, on a manual pick
  (`build_slicer_data.py` holds the four sentences and checks each claim on
  the data); *In short* is heading → Fig. 1 card with its new three-sentence
  caption → the paragraph. Word limit re-pinned at 604 (tagline −8, caption
  +14). Review pack: `build_instructions/review/v23A/`.
- **Stage v2.3-B — result tiles pipeline, Downstream with SBR 1.0, the slicer
  pool fix (2026-10-30).** On branch `v2.3-dev`, not pushed. A slicer preset
  now also sets Pool to 3 × 3 (the view its note was checked at), and a real
  pool change empties the note. `tools/build_result_tiles.py` builds all 20
  result tiles (both SBRs, both maps) from the paper's own sources into
  `assets/img/res/` with a provenance file; its `--check` is the tenth gate.
  Downstream shows SBR 0.6 and SBR 1.0 side by side (guide §0.8): each a
  header with a dark rule, a ground-truth square and a Poisson | MaRS slider
  with its test-set numbers as captions; the two sliders are linked; phones
  show the two sliders side by side with one *Hold to see ground truth*. The
  note under the module and the image chips are gone. `audit_claims.py` parses
  both PROJECT_BRIEF §3.5 tables and checks all eight caption values. Word
  limit re-pinned at 599. Review pack: `build_instructions/review/v23B/`.
- **Stage v2.3-C — the Ablation with SBR 1.0 and the zoom rows (2026-10-30).**
  On branch `v2.3-dev`, not pushed. Guide §0.8: the new lead (*The MaRS count
  model gives the best results on gold-standard data at both SBR levels.*),
  which `audit_claims.py` checks as a rule on all four test numbers; a
  two-panel dumbbell (SBR 0.6 | SBR 1.0, stacked on phones) drawn from two
  visually hidden tables; one zoom row per SBR in the style of InvProp's
  "Baseline Comparisons": the ground truth holds a draggable window of ¼ of
  its area (mouse, touch and keyboard) and the Renewal, Zhang et al. and MaRS
  count panes show that window at 2× from `assets/img/res/`, with their test
  values. Phones show one zoom row at a time behind an SBR toggle, 2 × 2. The
  footnote loses its last sentence; the old tiles and their CSS are gone from
  `/`. Word limit re-pinned at 609. Review pack:
  `build_instructions/review/v23C/`.
- **Stage v2.3-D — independent review, merge and launch (2026-10-30),
  `v2.3`.** A session that built none of v2.3 re-measured it: the twelve
  non-negotiables on `/`, with the Ablation lead (all four test numbers) and
  Downstream's "fails / works" at both SBRs traced to paper lines; the four
  slicer notes' counts recomputed from the shipped data with independent code
  (814 / 282 / 293, 355 / 158 / 160, 69 / 0 / 0, 4 / 4 / 5: exact); every
  SBR 1.0 value read off the rendered page in both modes; the 20 result tiles
  checked independently against the read-only sources (reflectivity equal to
  the figure's pixels, depth equal to matplotlib's viridis with one GT range
  per scene) and the zoom panes pixel-sampled; a number-provenance table; all
  ten gates; Chrome and Firefox at twelve widths on both pages; keyboard,
  touch and the hold button; cold-load bytes; Lighthouse. No rule violation
  and no defect to fix. Merged into `main` (`--no-ff`) and tagged `v2.3`.
  Review pack and the author's v2.3 phone checklist:
  `build_instructions/review/v23D/`.
- **Stage v2.4-A — independent sliders, averages notes, Ablation originals and
  zoom rows (2026-10-31).** On branch `v2.4-dev`, not pushed. Guide §0.9: the
  Downstream sliders are unlinked (mouse, touch and keyboard each move one);
  *Values are test-set averages.* under Downstream and at the end of the
  Ablation footnote; the Ablation captions are names only, and
  `audit_claims.py` now fails on a number in any image caption; each SBR block
  is a row of the four originals (the window on the ground truth only), the
  `.mars-ui` label *2× zoom of the box*, and a row of four 2× zooms in the same
  columns; phones pair each original with its zoom (CSS grid `order`). The
  README's SBR wording now names SBR 0.6 and SBR 1.0. Word limit re-pinned at
  605. Review pack: `build_instructions/review/v24A/`.
- **Stage v2.4-B — independent review, merge and launch (2026-10-31),
  `v2.4`.** A session that built none of v2.4 re-measured it: the twelve
  non-negotiables on `/`, with both *Values are test-set averages.* notes
  traced to the paper (the supplement's 14-scene test set; 7 of the 8 pictured
  depth maps' own RMSEs differ from the values shown) and the unchanged Ablation lead
  re-checked on the four test numbers; no digit under any Ablation image, both
  modes; the rendered text of `/` diffed against `v2.3` (only the §0.9
  changes); the zoom panes pixel-sampled with independent code (10 window
  positions per block, 1280 and 390, every pane closest to its own method's
  window region); sliders, hold, window, swipes, phone pairs and toggle by
  mouse, touch and keyboard; the accessibility tree after `display: contents`
  (the originals stay a list of four); one request per tile, 0 on a cold
  load; all ten gates; Chrome and Firefox at thirteen widths on both pages;
  Lighthouse. Merged into `main` (`--no-ff`) and tagged `v2.4`. Review pack
  and the author's v2.4 phone checklist: `build_instructions/review/v24B/`.
