# mars-splidar.github.io

Project page for **MaRS — Markov-Renewal Single-Photon LiDAR Simulator**
(ECCV 2026, Malmö, Sweden).

Weijian Zhang · Prateek Chennuri · Hashan K. Weerasooriya · Bole Ma ·
Stanley H. Chan — Elmore Family School of Electrical and Computer Engineering,
Purdue University.

## What this is and where it deploys

A static, dependency-free site: plain HTML, one CSS file, four small vanilla-JS
modules. No build step, no framework, no bundler.

- **Deploys to:** GitHub Pages at <https://mars-splidar.github.io/>, from the
  `main` branch of `git@github.com:mars-splidar/mars-splidar.github.io.git`.
- `.nojekyll` is present so Pages skips Jekyll — that both speeds up deploys
  and stops it silently dropping any path beginning with `_`.
- No `CNAME`: the site lives on the default `github.io` domain. Do not add one.

Two pages:

| Path | What it is |
|---|---|
| `index.html` | The main page — one long scroll with a sticky nav |
| `demos/index.html` | The demo lab — heavier interactive work, kept off the main page so the main page's first contentful paint stays fast |

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
rather than shipping a 15 MB file behind an unlabelled link.

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

## How to preview locally

```bash
python -m http.server 8731 --bind 127.0.0.1
```

then open <http://127.0.0.1:8731/index.html>. Serve it rather than opening the
file directly — `file://` breaks the clipboard API and relative asset paths.

## Repository layout

```
index.html              main page
demos/index.html        demo lab
css/mars.css            design tokens + every component
js/site.config.js       EVERY external URL, in one object
js/mars-nav.js          sticky nav, hamburger, hero button row
js/mars-switchbar.js    the switch-bar (tab) pattern
js/mars-media.js        scroll-triggered animation slots
js/mars-lightbox.js     video lightbox + BibTeX copy button
assets/img/             generated *.webp + *.png
assets/media/           the five section animations (stages 04, 05)
assets/docs/            poster PDFs, paper PDF, overview video + captions
tools/build_web_assets.py
tools/audit_claims.py
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
- **The hero title must stay on one line** down to ~380 px. Its `clamp()` is
  derived from a measured em-width; the CSS comment carries the arithmetic.
  Re-measure if you change the font, the tracking, or `--measure`.

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
