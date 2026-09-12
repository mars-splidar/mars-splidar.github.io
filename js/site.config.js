/* MaRS project site — every external / asset URL in one place.
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * The launch-blocking open questions (arXiv ID, code release + licence, video
 * hosting, whether the paper PDF is cleared for public posting) are all just
 * URLs. Keeping them here means stage 06 resolves them by editing ONE file
 * instead of hunting through markup.
 *
 * THE NULL RULE — this is a non-negotiable, not a convenience
 * -----------------------------------------------------------
 * A `null` URL renders a NON-CLICKABLE, muted, outlined pill with ` · soon`
 * appended to its label. It never renders `href="#"` and never renders a link
 * to a missing file. `tools/audit_claims.py` greps for `href="#"` and fails if
 * it finds any.
 *
 * Status of each field is recorded below. Update the status comment when you
 * change a value, so the next session can tell decided-null from not-yet-asked.
 *
 * THE STUB GATE (added stage 1.5)
 * ------------------------------
 * `sections` is the ordered registry of the six content bands that stage 02
 * fills. `sectionsLive` is the subset that is FINISHED and therefore rendered.
 * A section not in `sectionsLive` has BOTH its band and its nav anchor removed
 * from the DOM by js/mars-sections.js — it is never merely display:none'd with
 * a heading left floating, and it never leaves a nav link scrolling to nothing.
 *
 * TO TURN A SECTION ON (this is the whole procedure):
 *   1. write the section's content into its <section> in index.html;
 *   2. add its id to `sectionsLive` below.
 * Nothing else. The nav anchor comes back on its own.
 */
window.MARS_CONFIG = {
  /* paperPdf — WIRED UP 2026-09-07 (stage 1.5). `paper/main.pdf` arrived at
     25.26 MB, which is far too heavy for the hero's primary button on
     conference wifi, so it gets the same two-copy treatment as the poster:
     a 2.97 MB web copy (300 dpi, lossless — see build_web_assets.py for why
     not JPEG) as the primary target, and the untouched original behind a
     secondary full-resolution link. Setting this non-null is also what makes
     the Paper button the hero's filled AGED primary again. */
  paperPdf: "assets/docs/mars_paper.pdf",
  paperPdfFull: "assets/docs/mars_paper_full.pdf",
  paperPdfFullLabel: "paper (25 MB)",

  /* arxivUrl — open question E4. Null until an ID exists AND posting is cleared. */
  arxivUrl: null,

  /* codeUrl — open question E5. Null until the release + licence are decided. */
  codeUrl: null,

  /* Poster: web copy is the primary target (3.0 MB, 150 dpi raster); the
     full-resolution 15.3 MB original is offered as a secondary link. */
  posterPdf: "assets/docs/mars_poster_web.pdf",
  posterPdfFull: "assets/docs/mars_poster_full.pdf",
  posterPdfFullLabel: "poster (15 MB)",

  /* Video: open question E3. "self" serves the 24 MB local copy in a lightbox;
     switching to "youtube" is a two-field change (videoMode + videoYoutubeId)
     and needs no markup edit. */
  videoMode: "self",                               // "self" | "youtube"
  videoSelfUrl: "assets/docs/mars_5min.mp4",
  videoYoutubeId: null,
  videoSrtUrl: "assets/docs/mars_5min.srt",

  /* videoVttUrl — ADDED 2026-09-12 (stage 04 task 0). Same cues as the .srt,
     in the one subtitle format a browser can actually render. `videoSrtUrl`
     stays: it is the sidecar people download. This one is wired into the
     player as <track kind="captions">, so the CC button in the video controls
     works. Keep the two in step — tools/retime_srt.py writes both. */
  videoVttUrl: "assets/docs/mars_5min.vtt",

  /* ---- stub gate (stage 1.5) — see the note above ---- */

  /* The six gate-able content bands, in document order. Each has a matching
     `data-mars-section="<id>"` on its <section> in index.html AND on its <li>
     in the nav. This registry exists so the head-time style that hides the
     gated bands can be written before the DOM is parsed — that is what stops
     an unfinished band from flashing on screen during load. */
  sections: ["motivation", "approach", "contributions",
             "theory", "simulator", "utility"],

  /* Finished and rendered. Empty at the 2026-09-07 conference launch: stage 01
     built these six as shells and stage 02 writes their content. */
  sectionsLive: [],

  /* ---- media gate (stage 1.5) ----
     The same idea one level down, and it exists for one concrete reason: a
     <video poster="..."> pointing at a file that is not there yet is fetched
     by the browser's preload scanner during parsing — before any script can
     intervene — and 404s. Five empty slots meant five 404s on every page load.

     So index.html carries the poster and source URLs as `data-poster` and
     `data-src`, and js/mars-media.js promotes them to real attributes only for
     the basenames listed here. A slot that is not listed keeps its labelled
     16:9 placeholder and requests nothing at all.

     STAGES 04 AND 05: drop your files into assets/media/ AND add the basename
     here. Both, or the slot stays a placeholder. The five contract basenames
     are anim_motivation_scaling, anim_theory_countlaw, anim_theory_covariance,
     anim_sim_pipeline and anim_sim_lut. */
  mediaAvailable: [],

  projectPage: "https://mars-splidar.github.io/",
  demoLabUrl: "demos/",
  contactEmail: "zhan5056@purdue.edu"
};
