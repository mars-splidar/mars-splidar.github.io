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
 */
window.MARS_CONFIG = {
  /* paperPdf — as of 2026-09-07: `paper/main.pdf` has NOT arrived, so
     tools/build_web_assets.py wrote no assets/docs/mars_paper.pdf and this
     stays null. When the author drops the compiled PDF at paper/main.pdf,
     re-run the asset script and set this to the string below. The Paper button
     automatically becomes the filled primary button once this is non-null. */
  paperPdf: null,                                  // "assets/docs/mars_paper.pdf"

  /* arxivUrl — open question E4. Null until an ID exists AND posting is cleared. */
  arxivUrl: null,

  /* codeUrl — open question E5. Null until the release + licence are decided. */
  codeUrl: null,

  /* Poster: web copy is the primary target (3.0 MB, 150 dpi raster); the
     full-resolution 15.3 MB original is offered as a secondary link. */
  posterPdf: "assets/docs/mars_poster_web.pdf",
  posterPdfFull: "assets/docs/mars_poster_full.pdf",
  posterPdfFullLabel: "full resolution (15 MB)",

  /* Video: open question E3. "self" serves the 24 MB local copy in a lightbox;
     switching to "youtube" is a two-field change (videoMode + videoYoutubeId)
     and needs no markup edit. */
  videoMode: "self",                               // "self" | "youtube"
  videoSelfUrl: "assets/docs/mars_5min.mp4",
  videoYoutubeId: null,
  videoSrtUrl: "assets/docs/mars_5min.srt",

  projectPage: "https://mars-splidar.github.io/",
  demoLabUrl: "demos/",
  contactEmail: "zhan5056@purdue.edu"
};
