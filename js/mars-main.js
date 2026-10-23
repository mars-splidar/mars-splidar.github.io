/* Main-page behaviour — stage 07 (v2).
 *
 * Three small jobs that only the lean main page needs:
 *
 *  1. THE TEASER SWAP. The hero's teaser slot ships showing the
 *     `hook_tradeoff` raster. Stage 09 adds a <video class="mars-teaser__video">
 *     beside it (the exact markup is in the comment above the slot in
 *     index.html). This module swaps the slot to the video only after it has
 *     OBSERVED the video work — `loadeddata`, or, under
 *     prefers-reduced-motion, the poster image genuinely loading. Until then,
 *     and permanently if a file is missing, the raster stays on screen.
 *     That is the opposite of how .mars-media slots behave since stage 06,
 *     where `.has-media` is set by declaration and a 404 renders as a blank
 *     white frame (WEBSITE_BUILD_STATUS.md 5, stage 06, section 9). The label
 *     row is un-hidden in the same step, so the timings never appear twice
 *     (burned into the raster AND in HTML) and never appear over nothing.
 *     With no video in the markup — stage 07's interim state — this does
 *     nothing at all.
 *
 *  2. THE INLINE VIDEO'S POSTER. The film ships `preload="none"` and its
 *     poster as `data-poster`, promoted when the player comes within 300 px
 *     of the viewport, or on play. So a cold load at the top of the page
 *     fetches neither the 24.7 MB film nor its poster frame.
 *
 *  3. THE BIBTEX COPY BUTTON. Moved here from js/mars-lightbox.js, which the
 *     main page no longer loads now that the film plays inline. The code is
 *     unchanged; mars-lightbox.js still contains its own copy, unused.
 */
(function () {
  "use strict";

  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------- 1. teaser swap ---------------- */

  function initTeaser() {
    var fig = document.getElementById("mars-teaser");
    if (!fig) return;
    var video = fig.querySelector(".mars-teaser__video");
    if (!video) return;                       /* interim: raster only */
    var labels = fig.querySelector(".mars-teaser__labels");

    function show() {
      if (fig.getAttribute("data-teaser-state") === "video") return;
      fig.setAttribute("data-teaser-state", "video");
      if (labels) labels.hidden = false;
    }

    if (reduce) {
      /* Poster only, never motion (contract 3.7: "Reduced motion — poster
         only"). Stop any autoplay and swap only once the poster has loaded. */
      video.removeAttribute("autoplay");
      video.autoplay = false;
      video.preload = "none";
      if (!video.paused) video.pause();
      var poster = video.getAttribute("poster");
      if (!poster) return;
      var probe = new Image();
      probe.onload = show;
      probe.src = poster;
      return;
    }

    if (video.readyState >= 2) show();
    else video.addEventListener("loadeddata", show);
    var p = video.play();
    if (p && p.catch) p.catch(function () { /* autoplay policy: stays raster
                                              until a frame actually loads */ });
  }

  /* ---------------- 2. inline video poster ---------------- */

  function initVideo() {
    var v = document.querySelector(".mars-video__player[data-poster]");
    if (!v) return;

    function promote() {
      var url = v.getAttribute("data-poster");
      if (!url) return;
      v.setAttribute("poster", url);
      v.removeAttribute("data-poster");
    }

    v.addEventListener("play", promote);
    if (!("IntersectionObserver" in window)) { promote(); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { promote(); io.disconnect(); }
      });
    }, { rootMargin: "300px 0px", threshold: 0 });
    io.observe(v);
  }

  /* ---------------- 3. BibTeX copy button ---------------- */

  function initCopy() {
    Array.prototype.slice
      .call(document.querySelectorAll("[data-mars-copy]"))
      .forEach(function (btn) {
        btn.addEventListener("click", function () {
          var sel = btn.getAttribute("data-mars-copy");
          var src = document.querySelector(sel);
          if (!src) return;
          var text = src.textContent;

          function done() {
            var was = btn.textContent;
            btn.textContent = "Copied";
            btn.classList.add("is-done");
            window.setTimeout(function () {
              btn.textContent = was;
              btn.classList.remove("is-done");
            }, 1600);
          }

          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(done, fallback);
          } else {
            fallback();
          }

          function fallback() {
            /* execCommand path for non-secure contexts, e.g. opening the
               built page over file:// while checking it locally. */
            var ta = document.createElement("textarea");
            ta.value = text;
            ta.setAttribute("readonly", "");
            ta.style.position = "fixed";
            ta.style.left = "-9999px";
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand("copy"); done(); } catch (e) { /* noop */ }
            document.body.removeChild(ta);
          }
        });
      });
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    initTeaser();
    initVideo();
    initCopy();
  });
})();
