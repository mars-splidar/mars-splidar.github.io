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

  function initMedia() {
    var figs = Array.prototype.slice.call(
      document.querySelectorAll(".mars-media"));
    if (!figs.length) return;

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
