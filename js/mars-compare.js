/* Before/after slider — Demo 3 on the main page (stage 09).
 *
 * Markup: figure[data-compare] in index.html (#demo-downstream-media). Two
 * stacked tiles of the same gold-standard test scene: Poisson-trained
 * underneath (seen LEFT of the divider), MaRS-trained on top (seen RIGHT of
 * it, via clip-path at --pos). Vanilla, no dependencies.
 *
 * THE CONTROL IS A REAL <input type="range">, so arrow keys, Page Up/Down,
 * Home/End and screen readers work natively; its value is the divider's
 * position in percent from the left. Mouse, pen and touch drags on the stage
 * set the same input, through Pointer Events with pointer capture;
 * touch-action: pan-y in the CSS keeps vertical swipes scrolling the page.
 * Default 50 %. No intro animation, ever — so prefers-reduced-motion needs
 * nothing switched off.
 *
 * THE TOGGLE is two aria-pressed buttons (Reflectivity / Depth). It is a
 * control inside one demo, not a [data-switch] bar of panels. Switching
 * swaps the three image sources, their alt text, the two side labels and the
 * note — the depth strings ride in data-depth attributes beside the
 * reflectivity text, so every number on screen is in index.html.
 *
 * LAZY: nothing loads until the figure is within 300 px of the viewport;
 * depth tiles load only when Depth is first chosen.
 */
(function () {
  "use strict";

  function initOne(fig) {
    var stage = fig.querySelector(".mars-compare__stage");
    var range = fig.querySelector(".mars-compare__range");
    if (!stage || !range) return;
    var imgs = Array.prototype.slice.call(fig.querySelectorAll("img[data-src-refl]"));
    var swaps = Array.prototype.slice.call(fig.querySelectorAll("[data-depth]"));
    var buttons = Array.prototype.slice.call(fig.querySelectorAll(".mars-compare__mode"));
    var mode = fig.getAttribute("data-mode") || "refl";
    var loaded = false;

    /* the reflectivity strings are whatever the HTML ships */
    swaps.forEach(function (el) { el.setAttribute("data-refl", el.innerHTML); });

    function setPos(v) {
      v = Math.max(0, Math.min(100, Math.round(v)));
      range.value = String(v);
      stage.style.setProperty("--pos", v + "%");
      range.setAttribute("aria-valuetext",
        v + "% Poisson-trained, " + (100 - v) + "% MaRS-trained");
    }

    function loadImages() {
      imgs.forEach(function (img) {
        var src = img.getAttribute("data-src-" + mode);
        if (src && img.getAttribute("src") !== src) img.setAttribute("src", src);
        img.setAttribute("alt", img.getAttribute("data-alt-" + mode) || "");
      });
    }

    function setMode(m) {
      if (m === mode) return;
      mode = m;
      fig.setAttribute("data-mode", m);
      buttons.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-mode") === m ? "true" : "false");
      });
      swaps.forEach(function (el) {
        el.innerHTML = el.getAttribute(m === "depth" ? "data-depth" : "data-refl");
      });
      if (loaded) loadImages();
    }

    buttons.forEach(function (b) {
      b.addEventListener("click", function () { setMode(b.getAttribute("data-mode")); });
    });

    range.addEventListener("input", function () { setPos(+range.value); });

    /* pointer drag (mouse, pen, touch) */
    var dragging = null;
    function fromEvent(e) {
      var r = stage.getBoundingClientRect();
      return (e.clientX - r.left) / r.width * 100;
    }
    stage.addEventListener("pointerdown", function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      dragging = e.pointerId;
      try { stage.setPointerCapture(e.pointerId); } catch (err) { /* noop */ }
      setPos(fromEvent(e));
      range.focus({ preventScroll: true });
      e.preventDefault();
    });
    stage.addEventListener("pointermove", function (e) {
      if (dragging !== e.pointerId) return;
      setPos(fromEvent(e));
    });
    function end(e) {
      if (dragging !== e.pointerId) return;
      dragging = null;
      try { stage.releasePointerCapture(e.pointerId); } catch (err) { /* noop */ }
    }
    stage.addEventListener("pointerup", end);
    stage.addEventListener("pointercancel", end);

    setPos(+range.value || 50);

    function reveal() { loaded = true; loadImages(); }
    if (!("IntersectionObserver" in window)) { reveal(); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { reveal(); io.disconnect(); }
      });
    }, { rootMargin: "300px 0px", threshold: 0 });
    io.observe(fig);
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    Array.prototype.slice
      .call(document.querySelectorAll("[data-compare]"))
      .forEach(initOne);
  });
})();
