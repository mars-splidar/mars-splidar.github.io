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
 *
 *  4. THE CUBE SLICER'S LOADER (stage v2.1-C). A cold load fetches NOTHING
 *     of the slicer — not js/mars-slicer.js, not its 1.75 MB of data, not
 *     even its placeholder stills. At 1280 x 800 the block starts only a few
 *     hundred px below the fold, so a plain "within 600 px" observer would
 *     fire on every cold load; instead the 600 px rule applies once the
 *     reader has SCROLLED (or the block is genuinely on screen, or they touch,
 *     click or focus inside it). The placeholder stills come first, from
 *     1500 px away, so they are in place before the block is reached.
 *     Save-Data or prefers-reduced-data: the stills only, plus a button that
 *     loads the module on request.
 *
 *  5. FIG. 1 IN THE IN SHORT BAND (stage v2.2-A). Below the first screen
 *     now, so it ships as data-srcset / data-src and is promoted by the same
 *     rule as the slicer's stills: within 1500 px once the reader has
 *     scrolled, or as soon as it is on screen (a tall window). A cold load
 *     at the top of the page fetches none of it. Native loading="lazy" would
 *     not do: Chrome fetches lazy images 1250-2500 px ahead of the viewport.
 *     Save-Data does not hold it back: it is a 27-87 KB still, and the band's
 *     one picture.
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

  /* ---------------- 4. cube slicer loader ---------------- */

  function initSlicer() {
    var fig = document.getElementById("mars-slicer");
    if (!fig) return;
    var status = fig.querySelector(".mars-slicer__status");
    var saver = saveData() || !!(window.matchMedia &&
      window.matchMedia("(prefers-reduced-data: reduce)").matches);
    var stillsDone = false, moduleDone = false, scrolled = false, io = null;

    function msg(which) {           /* show one status line, or none */
      if (!status) return;
      Array.prototype.slice.call(status.querySelectorAll("[data-msg]"))
        .forEach(function (el) { el.hidden = el.getAttribute("data-msg") !== which; });
      status.hidden = !which;
    }

    function stills() {
      if (stillsDone) return;
      stillsDone = true;
      Array.prototype.slice.call(fig.querySelectorAll("source[data-srcset]"))
        .forEach(function (s) { s.srcset = s.getAttribute("data-srcset"); });
      Array.prototype.slice.call(fig.querySelectorAll("img[data-src]"))
        .forEach(function (i) { i.src = i.getAttribute("data-src"); });
    }

    function failed() {
      fig.setAttribute("data-slicer-state", "error");
      msg("error");
    }

    function load() {
      stills();
      if (moduleDone) return;
      moduleDone = true;
      detach();
      fig.setAttribute("data-slicer-state", "loading");
      if (onScreen(0)) msg("loading");
      var s = document.createElement("script");
      s.src = fig.getAttribute("data-slicer-script") || "js/mars-slicer.js";
      s.async = true;
      s.onerror = failed;
      document.body.appendChild(s);
    }

    function onScreen(margin) {
      var r = fig.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      return r.top < vh + margin && r.bottom > -margin;
    }

    var ticking = false;
    function check() {
      ticking = false;
      if (onScreen(1500)) stills();
      if (!saver && scrolled && onScreen(600)) load();
    }
    function onScroll() {
      scrolled = true;
      if (!ticking) { ticking = true; window.requestAnimationFrame(check); }
    }

    /* First touch, click, key or focus inside the block: load now, and
       remember a control that was pressed so the module can replay it. */
    function onFirst(e) {
      var b = e.target && e.target.closest ? e.target.closest("button") : null;
      if (b && b.classList.contains("mars-slicer__load")) return;
      if (b) fig._marsSlicerPending = b;
      if (saver) { stills(); return; }
      load();
    }

    function detach() {
      window.removeEventListener("scroll", onScroll);
      if (io) io.disconnect();
      ["pointerdown", "focusin", "keydown"].forEach(function (t) {
        fig.removeEventListener(t, onFirst, true);
      });
    }

    if (saver) {
      fig.setAttribute("data-slicer-state", "saver");
      msg("saver");
      var btn = fig.querySelector(".mars-slicer__load");
      if (btn) btn.addEventListener("click", function () {
        saver = false;
        load();
        msg("loading");
      });
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    ["pointerdown", "focusin", "keydown"].forEach(function (t) {
      fig.addEventListener(t, onFirst, true);
    });
    /* On screen without any scroll (a tall window): load, after the page's
       own load so it never competes with the first screen. */
    if ("IntersectionObserver" in window) {
      io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          stills();
          if (saver) return;
          if (document.readyState === "complete") load();
          else window.addEventListener("load", load);
        });
      }, { threshold: 0 });
      io.observe(fig);
    }
  }

  /* ---------------- 5. Fig. 1 context (lazy) ---------------- */

  function initContext() {
    var fig = document.getElementById("mars-context");
    if (!fig) return;
    var done = false, ticking = false, io = null;

    function promote() {
      if (done) return;
      done = true;
      window.removeEventListener("scroll", onScroll);
      if (io) io.disconnect();
      /* Sources first, then the <img>: a <source> gaining srcset makes the
         <picture> re-select, and the <img>'s own src is only the fallback. */
      Array.prototype.slice.call(fig.querySelectorAll("source[data-srcset]"))
        .forEach(function (el) {
          el.srcset = el.getAttribute("data-srcset");
          el.removeAttribute("data-srcset");
        });
      Array.prototype.slice.call(fig.querySelectorAll("img[data-src]"))
        .forEach(function (el) {
          el.src = el.getAttribute("data-src");
          el.removeAttribute("data-src");
        });
    }

    function near(margin) {
      var r = fig.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      return r.top < vh + margin && r.bottom > -margin;
    }
    function check() {
      ticking = false;
      if (near(1500)) promote();
    }
    function onScroll() {
      if (!ticking) { ticking = true; window.requestAnimationFrame(check); }
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    if ("IntersectionObserver" in window) {
      io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) promote(); });
      }, { threshold: 0 });
      io.observe(fig);
    } else {
      promote();
    }
  }

  ready(function () {
    initTeaser();
    initVideo();
    initCopy();
    initSlicer();
    initContext();
  });
})();
