/* Main-page behaviour — stage 07 (v2).
 *
 * Three small jobs that only the lean main page needs:
 *
 *  1. THE TEASER. The hero's slot ships the animation's own poster
 *     (anim_hero_cubes.jpg, frame 0, the LCP image) with the label row
 *     visible, and a <video class="mars-teaser__video"> on top of it at
 *     opacity 0 with preload="none" and no `autoplay` attribute — so markup
 *     alone fetches no video. This module starts it (preload + play()) when
 *     the slot is on screen, and shows it only after it has OBSERVED a frame
 *     play (`playing`). Until then, and permanently if a file is missing or
 *     fails to decode, the poster stays on screen: never a blank box. That is
 *     the opposite of how .mars-media slots behave since stage 06, where
 *     `.has-media` is set by declaration and a 404 renders as a blank white
 *     frame (WEBSITE_BUILD_STATUS.md 5, stage 06, section 9).
 *     Under prefers-reduced-motion, and under Save-Data
 *     (navigator.connection.saveData), it never starts it: poster only,
 *     zero video bytes (stage 09, T1.4). Off screen the loop is paused.
 *
 *  2. THE INLINE VIDEO'S POSTER. The film ships `preload="none"` and its
 *     poster as `data-poster`, promoted when the player comes within 300 px
 *     of the viewport, or on play. So a cold load at the top of the page
 *     fetches neither the 24.7 MB film nor its poster frame.
 *
 *  3. THE BIBTEX COPY BUTTON. The site's only copy of this routine (it
 *     moved here in stage 07 from the v1 lightbox script, which stage 09
 *     deleted).
 */
(function () {
  "use strict";

  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------- 1. teaser ---------------- */

  function saveData() {
    var c = navigator.connection;
    return !!(c && c.saveData);
  }

  function initTeaser() {
    var fig = document.getElementById("mars-teaser");
    if (!fig) return;
    var video = fig.querySelector(".mars-teaser__video");
    if (!video) return;

    /* Poster only, never motion and never a byte of video (contract 3.7:
       "Reduced motion — poster only"; stage 09: the same under Save-Data). */
    if (reduce || saveData()) {
      fig.setAttribute("data-teaser-state", "poster");
      return;
    }

    var started = false;
    var visible = true;

    video.addEventListener("playing", function () {
      fig.setAttribute("data-teaser-state", "video");
    });

    function play() {
      var p = video.play();
      if (p && p.catch) p.catch(function () { /* autoplay refused or the file
                                                 failed: the poster stays */ });
    }

    function start() {
      if (started) return;
      started = true;
      /* Raising preload resumes the resource selection that preload="none"
         suspended, and play() needs nothing more; an extra load() here
         would abort that first request and start a second one. */
      video.preload = "auto";
      play();
    }

    if (!("IntersectionObserver" in window)) { start(); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        visible = e.isIntersecting;
        if (!visible) { if (started && !video.paused) video.pause(); return; }
        if (!started) start();
        else if (video.paused) play();
      });
    }, { threshold: 0 });
    io.observe(fig);
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
