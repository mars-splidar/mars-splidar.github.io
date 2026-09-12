/* Video lightbox + the BibTeX copy button.
 *
 * ONE configurable video source. GAP_REPORT.md #16: the hosting decision (E3,
 * self-hosted 24 MB vs. a YouTube embed) is still open, so the player is built
 * from window.MARS_CONFIG at open time. Switching to YouTube later is
 * `videoMode: "youtube"` + `videoYoutubeId` in js/site.config.js — no markup
 * change, no rebuild.
 *
 * Nothing is fetched until the visitor actually opens the lightbox, which is
 * what keeps a 24 MB file off the critical path.
 */
(function () {
  "use strict";

  var cfg = window.MARS_CONFIG || {};
  var lastFocus = null;

  function box() { return document.getElementById("mars-lightbox"); }

  function buildPlayer() {
    var body = document.getElementById("mars-lightbox-body");
    if (!body) return;
    body.textContent = "";

    if (cfg.videoMode === "youtube" && cfg.videoYoutubeId) {
      var frame = document.createElement("iframe");
      frame.src = "https://www.youtube-nocookie.com/embed/" +
        cfg.videoYoutubeId + "?autoplay=1&rel=0";
      frame.title = "MaRS — five-minute overview";
      frame.allow = "accelerometer; autoplay; clipboard-write; encrypted-media;" +
        " gyroscope; picture-in-picture";
      frame.allowFullscreen = true;
      body.appendChild(frame);
      return;
    }

    if (!cfg.videoSelfUrl) return;
    var video = document.createElement("video");
    video.controls = true;
    video.preload = "metadata";
    video.setAttribute("playsinline", "");
    video.src = cfg.videoSelfUrl;
    if (cfg.videoSrtUrl) {
      /* .srt is not a browser-native track format, so it stays what it always
         was: a sidecar offered for download beside the player. */
      video.setAttribute("data-captions", cfg.videoSrtUrl);
    }
    if (cfg.videoVttUrl) {
      /* ADDED stage 04 task 0. WebVTT is the format a <track> can render, so
         this is what puts a working CC button in the controls. Same cues as
         the .srt; both are written by tools/retime_srt.py from one source.
         `default` is deliberately NOT set — captions are offered, not forced.
         Note this only works same-origin or with CORS; the file sits beside
         the video, so on GitHub Pages it always is. */
      var track = document.createElement("track");
      track.kind = "captions";
      track.label = "English";
      track.srclang = "en";
      track.src = cfg.videoVttUrl;
      video.appendChild(track);
    }
    body.appendChild(video);
    var p = video.play();
    if (p && p.catch) p.catch(function () { /* autoplay policy; controls shown */ });
  }

  function open() {
    var lb = box();
    if (!lb) return;
    lastFocus = document.activeElement;
    buildPlayer();
    lb.hidden = false;
    document.body.style.overflow = "hidden";
    var close = document.getElementById("mars-lightbox-close");
    if (close) close.focus();
  }

  function close() {
    var lb = box();
    if (!lb) return;
    lb.hidden = true;
    var body = document.getElementById("mars-lightbox-body");
    if (body) body.textContent = "";        // stops playback, frees the stream
    document.body.style.overflow = "";
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function initLightbox() {
    var lb = box();
    if (lb) {
      var srt = document.getElementById("mars-lightbox-srt");
      if (srt && cfg.videoSrtUrl) {
        srt.href = cfg.videoSrtUrl;
        srt.hidden = false;
      }
      lb.addEventListener("click", function (ev) {
        if (ev.target === lb) close();
      });
      var btn = document.getElementById("mars-lightbox-close");
      if (btn) btn.addEventListener("click", close);
      document.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && !lb.hidden) close();
      });
    }

    /* Delegated, because mars-nav.js builds the Video button after load. */
    document.addEventListener("click", function (ev) {
      var trigger = ev.target.closest && ev.target.closest("[data-mars-lightbox]");
      if (!trigger) return;
      ev.preventDefault();
      open();
    });
  }

  /* ---------------- BibTeX copy button ---------------- */

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
    initLightbox();
    initCopy();
  });
})();
