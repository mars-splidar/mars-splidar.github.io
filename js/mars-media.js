/* Media slots — scroll-triggered autoplay for the five section animations.
 *
 * CONTRACT ADDITION (stage 01): WEBSITE_BUILD_STATUS.md section 3.1 lists
 * mars-nav.js, mars-switchbar.js and v1's lightbox script but no home for the
 * IntersectionObserver behaviour that section 3.3 requires. This file is that
 * home. It is purely additive — nothing in section 3 was renamed. Flagged in
 * the stage 01 handoff entry.
 *
 * Behaviour:
 *  - fetch nothing at all until a slot is within 300px of the viewport;
 *  - play when >= 35% of the slot is in view, pause when it leaves;
 *  - `prefers-reduced-motion: reduce` -> never play, show the poster only;
 *  - Save-Data (`navigator.connection.saveData`, stage 10b) -> the same;
 *  - under EITHER, `preload="none"` and no load(), so not one video byte is
 *    fetched until the reader presses play on the controls (the teaser on /
 *    has done this since stage 09). Save-Data got this in stage 10b; reduced
 *    motion only in v2.1-A — until then it promoted the sources and called
 *    load() with preload="metadata", which Chrome ignores: the in-view
 *    loops on /details/ downloaded whole (stage 10b's correction to stage 10);
 *  - a slot whose sources are missing keeps its labelled 16:9 placeholder.
 *
 * THE MEDIA GATE — CONTRACT CHANGE, STAGE 1.5. READ THIS IF YOU ARE STAGE 04
 * OR 05.
 * -------------------------------------------------------------------------
 * Stage 01 shipped the slots with real `poster` and `<source src>` attributes
 * pointing into an empty assets/media/. That produced five 404s on every page
 * load, because a <video poster> is fetched by the browser's PRELOAD SCANNER
 * during HTML parsing — before any script exists to stop it, and regardless of
 * `preload="none"`. Stage 1.5 had to get that to zero before pushing to
 * production, so the URLs now ship as `data-poster` and `data-src`, and this
 * file promotes them to real attributes ONLY for the basenames listed in
 * `MARS_CONFIG.mediaAvailable`.
 *
 * So there are now TWO steps to landing an animation, not one:
 *     1. drop anim_x.{mp4,webm,jpg} into assets/media/
 *     2. add "anim_x" to `mediaAvailable` in js/site.config.js
 * A slot that is not listed requests nothing and keeps its placeholder, which
 * is the correct failure mode: no 404, no broken frame. Everything else in
 * WEBSITE_BUILD_STATUS.md section 3.2 — 1280x720, 30 fps, 4-10 s (target
 * 5-8 s), no audio, seamless loop, byte budgets, PAPER background — is
 * unchanged.
 *
 * WHY PROMOTION IS DEFERRED — Q14, RESOLVED IN STAGE 06
 * ----------------------------------------------------
 * Until stage 06 this file promoted the URLs and called video.load() inside
 * initMedia(), for every listed basename, at page load. Measured on the live
 * site with all five slots enabled: 1.52 MB fetched at scrollY === 0 before
 * any interaction — five posters (538 KB) and five ENTIRE .webm files
 * (984 KB), not metadata ranges, because load() on a promoted <source>
 * ignores `preload="none"`. Worse in kind than in size:
 * anim_theory_covariance sits in a `hidden` switch panel with a zero-size
 * bounding box, and its poster and whole video came down anyway, for a panel
 * most visitors never open.
 *
 * Promotion now happens on the first IntersectionObserver hit instead, so a
 * cold page load fetches ZERO bytes of media and a closed tab panel fetches
 * nothing until it is both opened and scrolled to. Three details make that
 * work without a visible regression:
 *
 *  1. TWO observers, not one. `prepObserver` promotes and loads with a 300px
 *     rootMargin at threshold 0 — early enough that the poster is usually
 *     painted before the frame is on screen. `playObserver` keeps section
 *     3.3's 35% play/pause rule exactly as it was.
 *  2. `prepObserver` runs even under `prefers-reduced-motion`. It is what
 *     puts the poster and the `controls` bar there; only playObserver is
 *     gated on the media query.
 *  3. `.has-media` is added at INIT for every available basename, not on
 *     `loadeddata`. The class only means "this slot has media" — it hides the
 *     "Animation coming soon" placeholder and turns the dashed frame solid.
 *     Adding it at init is what stops an available slot from reading "coming
 *     soon" for the second before its poster arrives. The frame's
 *     `aspect-ratio` reserves the box either way, so nothing reflows.
 */
(function () {
  "use strict";

  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  /* Save-Data (stage 10b) is treated like reduced motion: poster and
     controls, never autoplay, and — for both, since v2.1-A — preload="none"
     with no load(), so no video bytes at all until play is pressed. */
  var saveData = !!(navigator.connection && navigator.connection.saveData);
  var still = reduce || saveData;

  /* Promote data-poster / data-src to the real attributes and start the
     fetch. Called from the prepare observer on first approach, never at init,
     and guarded so it runs at most once per slot. */
  function prepare(fig, video) {
    if (fig.getAttribute("data-media-ready")) return;
    fig.setAttribute("data-media-ready", "1");

    var poster = video.getAttribute("data-poster");
    if (poster) {
      video.setAttribute("poster", poster);
      video.removeAttribute("data-poster");
    }
    var sources = fig.querySelectorAll(".mars-media__video source[data-src]");
    if (still) video.preload = "none";      /* before any source has a src */
    for (var i = 0; i < sources.length; i++) {
      if (still) {
        /* Reduced motion / Save-Data: Chrome's load() fetches the whole file
           whatever `preload` says (measured, stage 10b). Re-inserting each
           <source> with its src instead resumes the source selection the
           parser left waiting, picks a file and fetches nothing until play
           is pressed. */
        var fresh = sources[i].cloneNode(false);
        fresh.setAttribute("src", fresh.getAttribute("data-src"));
        fresh.removeAttribute("data-src");
        sources[i].parentNode.replaceChild(fresh, sources[i]);
      } else {
        sources[i].setAttribute("src", sources[i].getAttribute("data-src"));
        sources[i].removeAttribute("data-src");
      }
    }
    if (sources.length && !still) video.load();
  }

  function initMedia() {
    var figs = Array.prototype.slice.call(
      document.querySelectorAll(".mars-media"));
    if (!figs.length) return;

    var cfg = window.MARS_CONFIG || {};
    var available = cfg.mediaAvailable || [];
    var hasIO = "IntersectionObserver" in window;

    /* Promotion observer — fires before the slot is on screen so the poster
       has a head start, and fires under reduced motion too. */
    var prepObserver = null;
    if (hasIO) {
      prepObserver = new IntersectionObserver(function (entries, obs) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var video = entry.target.querySelector(".mars-media__video");
          if (!video) return;
          prepare(entry.target, video);
          obs.unobserve(entry.target);
        });
      }, { rootMargin: "300px 0px", threshold: 0 });
    }

    /* Play/pause observer — section 3.3's 35% rule, unchanged. */
    var playObserver = null;
    if (!still && hasIO) {
      playObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var video = entry.target.querySelector(".mars-media__video");
          if (!video) return;
          if (entry.isIntersecting) {
            /* prepare() has run by now in every ordinary case, since this
               observer's threshold is stricter than the prepare one's. Call it
               anyway: the two callbacks can coalesce into one frame on a fast
               scroll, and prepare() is idempotent. */
            prepare(entry.target, video);
            var p = video.play();
            if (p && p.catch) p.catch(function () { /* autoplay policy */ });
          } else if (!video.paused) {
            video.pause();
          }
        });
      }, { threshold: 0.35 });
    }

    figs.forEach(function (fig) {
      var video = fig.querySelector(".mars-media__video");
      if (!video) return;

      /* Not declared available: leave the placeholder and request nothing.
         Do not observe either — the observers promote data-src, and a missing
         file would 404. */
      if (available.indexOf(fig.getAttribute("data-media-id")) === -1) return;

      /* Declared available, so the frame is a real media frame from now on
         even though nothing has been fetched yet. See note 3 in the header. */
      fig.classList.add("has-media");

      /* Reduced motion or Save-Data: no autoplay at all. The poster plus
         manual controls, preload="none", and sources re-inserted rather than
         load()ed (prepare()), so nothing is fetched until play is pressed.
         v2.1-A: reduced motion used preload="metadata" + load(), and fetched
         the whole file. */
      if (still) {
        video.removeAttribute("autoplay");
        video.controls = true;
        video.preload = "none";
      }

      /* No IntersectionObserver at all (very old browser): fall back to the
         pre-stage-06 behaviour and promote immediately, so the slot still
         works. Costs the eager fetch, which is the right trade on a browser
         that cannot tell us what is on screen. */
      if (!hasIO) {
        prepare(fig, video);
        if (!still) {
          var p = video.play();
          if (p && p.catch) p.catch(function () { /* autoplay policy */ });
        }
        return;
      }

      prepObserver.observe(fig);
      if (playObserver) playObserver.observe(fig);
    });
  }

  window.marsInitMedia = initMedia;

  if (document.readyState !== "loading") initMedia();
  else document.addEventListener("DOMContentLoaded", initMedia);
})();
