/* Media slots — scroll-triggered autoplay for the five section animations.
 *
 * CONTRACT ADDITION (stage 01): WEBSITE_BUILD_STATUS.md section 3.1 lists
 * mars-nav.js, mars-switchbar.js and mars-lightbox.js but no home for the
 * IntersectionObserver behaviour that section 3.3 requires. This file is that
 * home. It is purely additive — nothing in section 3 was renamed. Flagged in
 * the stage 01 handoff entry.
 *
 * Behaviour:
 *  - play when >= 35% of the slot is in view, pause when it leaves;
 *  - `prefers-reduced-motion: reduce` -> never play, show the poster only;
 *  - a slot whose sources are missing keeps its labelled 16:9 placeholder.
 *    `.has-media` is added only once the browser reports real dimensions, so
 *    with assets/media/ empty there is no broken-media icon and no reflow.
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
 * WEBSITE_BUILD_STATUS.md section 3.2 — 1280x720, 30 fps, 12-18 s, no audio,
 * seamless loop, byte budgets, PAPER background — is unchanged.
 */
(function () {
  "use strict";

  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function markLoaded(fig, video) {
    if (video.videoWidth > 0 && video.videoHeight > 0) {
      fig.classList.add("has-media");
      return true;
    }
    return false;
  }

  /* Promote data-poster / data-src to the real attributes. Called only for
     slots whose media is declared available, so nothing is ever requested for
     a file that is not there. */
  function activate(fig, video) {
    var poster = video.getAttribute("data-poster");
    if (poster) {
      video.setAttribute("poster", poster);
      video.removeAttribute("data-poster");
    }
    var sources = fig.querySelectorAll(".mars-media__video source[data-src]");
    for (var i = 0; i < sources.length; i++) {
      sources[i].setAttribute("src", sources[i].getAttribute("data-src"));
      sources[i].removeAttribute("data-src");
    }
    if (sources.length) video.load();
  }

  function initMedia() {
    var figs = Array.prototype.slice.call(
      document.querySelectorAll(".mars-media"));
    if (!figs.length) return;

    var cfg = window.MARS_CONFIG || {};
    var available = cfg.mediaAvailable || [];

    var observer = null;
    if (!reduce && "IntersectionObserver" in window) {
      observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var video = entry.target.querySelector(".mars-media__video");
          if (!video) return;
          if (entry.isIntersecting) {
            /* preload="none" means nothing has been fetched yet; play() is
               what triggers the load. A rejected promise (no sources, or
               autoplay policy) is expected and harmless. */
            var p = video.play();
            if (p && p.catch) p.catch(function () { /* no sources yet */ });
          } else if (!video.paused) {
            video.pause();
          }
        });
      }, { threshold: 0.35 });
    }

    figs.forEach(function (fig) {
      var video = fig.querySelector(".mars-media__video");
      if (!video) return;

      /* Not declared available: leave the placeholder, request nothing, and
         do not observe — an IntersectionObserver callback would call play(),
         which is what would fetch the missing sources. */
      if (available.indexOf(fig.getAttribute("data-media-id")) === -1) return;
      activate(fig, video);

      /* Reduced motion: no autoplay at all. Show the poster if there is one
         and give the visitor manual controls instead. */
      if (reduce) {
        video.removeAttribute("autoplay");
        video.controls = true;
        video.preload = "metadata";
      }

      if (!markLoaded(fig, video)) {
        video.addEventListener("loadeddata", function () {
          markLoaded(fig, video);
        });
        /* A poster image alone is enough to count as "has media" — the frame
           should stop looking provisional as soon as anything renders. */
        var poster = video.getAttribute("poster");
        if (poster) {
          var probe = new Image();
          probe.onload = function () { fig.classList.add("has-media"); };
          probe.src = poster;
        }
      }

      if (observer) observer.observe(fig);
    });
  }

  window.marsInitMedia = initMedia;

  if (document.readyState !== "loading") initMedia();
  else document.addEventListener("DOMContentLoaded", initMedia);
})();
