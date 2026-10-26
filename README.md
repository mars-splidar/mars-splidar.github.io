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

Three pages (v2, `v2.0`, 2026-10-23):

| Path | What it is |
|---|---|
| `index.html` | The lean main page: the hero teaser, *In short* + four gains, two result demos, the film inline, BibTeX |
| `details/index.html` | Method and full results: v1's seven technical bands, moved verbatim |
| `demos/index.html` | The demo lab, all four panels "coming soon"; **unlinked from every public page** until the playground ships |

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

### The two v2 gates (stage 07)

```bash
python tools/page_budget.py          # the main page's budgets, guide 0.1 / 0.6
python tools/details_move_diff.py    # /details/ vs v1.0-launch, band by band
```

`page_budget.py` measures `/` against `MARS_WEBSITE_BUILD_GUIDE.md` §0.1, with
§0.6 item 6's limits since v2.1-A — visible words ≤ 420 (was 350), at most six
media slots above BibTeX (was exactly four), zero switch bars, zero
display equations, and each demo's title and single sentence — and exits
non-zero on a breach. Its docstring defines exactly what counts as a word and
as a media item. Since v2.1-C it counts PROSE only: text inside a `.mars-ui`
element (control labels, legends, axis text) is reported
separately as "UI words" and is not held against the 420; it also checks the
cube slicer's title, guiding text and media slot. `details_move_diff.py` extracts each of the seven bands,
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
`build_slicer_placeholder.py` re-captures the placeholder stills
(`assets/img/slicer_ph_*.webp`) from the live module; re-run it after any
change to the module's drawing, the data or the fonts. Never edit either output
by hand. `js/mars-slicer.js` is fetched by `js/mars-main.js` only when the
reader scrolls near the block (never on a cold load).

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
js/mars-compare.js      main page only: Demo 3 before/after slider (stage 09)
js/mars-slicer.js       main page only: the cube slicer, loaded on demand (v2.1-C)
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
tools/build_fig1_question.py  Fig. 1's top half from the paper PDF (v2.1-A)
tools/measure_edges.py  visible edges vs the column, both pages; not a gate (v2.1-A)
tools/build_demo_count.py  Demo 2's SVG from video/data.py, + provenance (stage 09)
tools/build_slicer_data.py  the slicer's data + default readout, --check gate (v2.1-C)
tools/build_slicer_placeholder.py  the slicer's placeholder stills (v2.1-C)
assets/data/slicer/     the slicer's cubes, delay map and meta.json (v2.1-C)
tools/details_move_diff.py  proves /details/ is v1's bands verbatim (stage 07)
```

## Editing rules that are not obvious from the code

- **`js/site.config.js` is the only place a URL belongs.** A `null` URL renders
  a non-clickable `· soon` pill. Never `href="#"`, never a link to a missing
  file — the audit greps for it.
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
- **The BibTeX entry is provisional.** Page numbers and the exact proceedings
  title are unknown until ECCV camera-ready is processed. Do not invent them.
- **The hero title's gold letters are `MaRS`, `Ma`, `R`, and the `S` of
  *Simulator*** — not the `S` of *Single-Photon*. `MaRS` = **Ma**rkov-**R**enewal
  **S**imulator.
- **The hero title fills the column exactly** (v2.1-A): one line above 467 px,
  the two-line fallback below, all sized in `cqi` from a measured INK width
  (`--title-em`, `--acronym-em`, `--full-em` and their side bearings in
  `css/mars.css`). Re-measure with `tools/measure_edges.py` if you change the
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
