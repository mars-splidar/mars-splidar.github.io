/* The Efficiency schematic — stage v2.2-B.
 *
 * Production version of build_instructions/review/concepts/v22/
 * efficiency_concept_v3.html: one loop of 11 s, two rows.
 *
 *   Gold standard   the playhead sweeps one pixel's photons every 2.6 s; each
 *                   detection opens a blind window and the photons inside it
 *                   turn grey. The three 8 x 8 grids fill one cell at a time
 *                   (12 cells a second), the current cell in gold.
 *   MaRS            0.6 s   step 1: the table entry lights up, the entry card
 *                           opens with the PDF at the reference delay;
 *                   3.2 s   step 2: the PDF slides to the pixel's delay τ
 *                           (1.6 s, eased), a circular shift;
 *                   5.6 s   step 3: sampled bars appear under the curve and
 *                           all three grids fill at once;
 *                   10.2 s  the MaRS side clears; the loop restarts at 11 s.
 *
 * It is a schematic, not data: no timer, clock or runtime number is drawn
 * (non-negotiable #6 stays moot). The cell shades are a fixed pattern with a
 * small per-realization jitter, different for the two simulators, so no two
 * realizations are pixel-identical.
 *
 * The markup holds both layouts (two SVGs) and all of their text; this script
 * draws the grids, the photon strip, the table cells and the PDF into each
 * from its data-* geometry. Which layout is shown follows ONE media query,
 * the figure's data-eff-stack (v2.2-P: "(max-width: 971px)", the stacked
 * layout up to where the wide one's labels reach 12 px); css/mars.css uses
 * the same query. Until v2.2-P it was the site's 600/601 pair.
 *
 * HYGIENE. One requestAnimationFrame loop, and only while it has work: the
 * figure is on screen (IntersectionObserver), the tab is visible and motion
 * is allowed. Otherwise no frame is scheduled at all. The clock advances only
 * while running (a resume continues where it stopped; a long frame is clamped
 * to 0.1 s). v2.2-P: it DRAWS at most 30 frames a second. Every rAF tick
 * still advances the clock by real time, so the loop's length and motion are
 * unchanged; the ticks in between draw nothing (half the style and layout
 * work on a 60 Hz screen). Only the SVG that is shown is updated, and only attributes whose
 * value changed are written; nothing is read back from layout.
 * prefers-reduced-motion: the end state is drawn once (step 3 done, the PDF
 * at τ, the strip fully swept, the gold grids part filled) and no frame is
 * ever requested. The figure's data-eff-state is "running", "paused" or
 * "static", for the stage's measurements.
 */
(function () {
  "use strict";

  var fig = document.getElementById("demo-efficiency-media");
  if (!fig || !window.SVGElement) return;

  var NS = "http://www.w3.org/2000/svg";
  var LOOP = 11, SWEEP = 2.6, GOLD_RATE = 12;
  var T1 = 0.6, T2 = 3.2, T3 = 5.6, T4 = 10.2, SLIDE = 1.6, FADE = 0.25;
  var STATIC_T = 8.6;                       // the reduced-motion frame
  var STACK = fig.getAttribute("data-eff-stack") || "(max-width: 600px)";
  var FRAME_MS = 1000 / 30;                 // v2.2-P: at most 30 drawn frames/s

  var C_EMPTY = "#eef0ee", C_GOLD = "#CFB991", C_DROP = "#c8c8c8",
      C_AGED = "#8E6F3E";

  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function nums(s) { return (s || "").trim().split(/\s+/).map(Number); }
  function clamp01(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
  function ease(x) { return 0.5 - 0.5 * Math.cos(Math.PI * clamp01(x)); }

  /* A cached attribute writer: touches the DOM only on change. */
  function setter(node) {
    var last = {};
    return function (name, value) {
      if (last[name] !== value) { last[name] = value; node.setAttribute(name, value); }
    };
  }

  /* Cell shades: the concept's pattern, plus a small jitter per cell that
     differs per realization and per simulator. */
  function shade(i, seed) {
    var p = i % 64, r = Math.floor(p / 8), c = p % 8;
    var base = 0.35 + 0.6 * Math.abs(Math.sin(r * 0.9 + c * 0.55));
    var h = Math.sin((i + 1) * 12.9898 + seed * 78.233) * 43758.5453;
    var j = (h - Math.floor(h) - 0.5) * 0.24;
    return Math.max(0.2, Math.min(0.95, base + j));
  }

  /* The concept's temporal PDF, in its own units (a 176-wide plot, the
     reference delay at 40): a baseline, the peak just before the delay, then
     the dead-time shadow that recovers over the next 56 units. */
  function pdfAt(u) {
    var g = Math.exp(-0.5 * Math.pow((u + 2) / 5, 2));
    var tail = (u > 4 && u < 60) ? 0.06 * (1 - Math.exp(-(u - 4) / 22)) : 0.10;
    return (u > 4 ? tail : 0.10) + 0.85 * g;
  }

  /* ---------------- one layout ---------------- */

  function Layout(svg) {
    this.svg = svg;

    /* grids: 3 realizations x 64 pixels */
    function grids(g, seed) {
      var pitch = +g.getAttribute("data-pitch"), gap = +g.getAttribute("data-gap");
      var cells = [];
      for (var r = 0; r < 3; r++) {
        var ox = r * (8 * pitch + gap);
        var t = el("text", { x: ox, y: -7, "class": "mars-eff__small" }, g);
        t.textContent = "#" + (r + 1);
        for (var i = 0; i < 8; i++) for (var j = 0; j < 8; j++) {
          var rc = el("rect", { x: ox + j * pitch, y: i * pitch, width: pitch - 1,
                                height: pitch - 1, rx: 1.2, fill: C_EMPTY }, g);
          cells.push({ set: setter(rc), s: shade(r * 64 + i * 8 + j, seed) });
        }
      }
      return cells;
    }
    this.gold = grids(svg.querySelector(".mars-eff__grids.is-gold"), 1);
    this.mars = grids(svg.querySelector(".mars-eff__grids.is-mars"), 2);

    /* the photon strip of one pixel */
    var st = svg.querySelector(".mars-eff__strip");
    var W = +st.getAttribute("data-w"), blind = +st.getAttribute("data-blind");
    this.stripW = W;
    el("line", { x1: 0, y1: 26, x2: W, y2: 26, "class": "mars-eff__axis" }, st);
    var last = -1e9;
    this.photons = nums(st.getAttribute("data-photons")).map(function (x) {
      var reg = x - last >= blind;
      if (reg) last = x;
      return { x: x, reg: reg,
               band: reg ? setter(el("rect", { x: x, y: 12, height: 28, width: 0,
                                                "class": "mars-eff__blind" }, st)) : null,
               bmax: Math.min(blind, W - x) };
    });
    this.photons.forEach(function (p) {
      p.dot = setter(el("circle", { cx: p.x, cy: 26, r: 5.5, opacity: 0,
                                    fill: p.reg ? C_AGED : C_DROP }, st));
    });
    this.head = setter(el("line", { x1: 0, y1: 6, x2: 0, y2: 46,
                                    "class": "mars-eff__playhead" }, st));

    /* the lookup table, the highlighted entry and the lead to its card */
    var lut = svg.querySelector(".mars-eff__lut");
    var cols = +lut.getAttribute("data-cols"), rows = +lut.getAttribute("data-rows"),
        lp = +lut.getAttribute("data-pitch"), hi = nums(lut.getAttribute("data-hi"));
    for (var i = 0; i < rows; i++) for (var j = 0; j < cols; j++) {
      var c = el("rect", { x: j * lp, y: i * lp, width: lp - 1, height: lp - 1, rx: 1.5,
                           "class": "mars-eff__cell" }, lut);
      if (i === hi[0] && j === hi[1]) this.hiCell = setter(c);
    }
    var hy = hi[0] * lp + (lp - 1) / 2, hx = hi[1] * lp + lp - 1;
    var to = +lut.getAttribute("data-to");
    var m = lut.getAttribute("transform").match(/translate\(([-\d.]+)[ ,]+([-\d.]+)\)/);
    var lx = +m[1], ly = +m[2];
    this.lead = setter(el("path", { d: "M" + (lx + hx) + " " + (ly + hy) + "H" + to,
                                    "class": "mars-eff__lead", opacity: 0 }, lut.parentNode));

    /* the entry card and its PDF */
    this.entry = setter(svg.querySelector(".mars-eff__entry"));
    this.entry("opacity", "0");
    var pg = svg.querySelector(".mars-eff__pdf");
    var pw = +pg.getAttribute("data-w"), ph = +pg.getAttribute("data-h");
    var ref = +pg.querySelector(".mars-eff__ref").getAttribute("x1");
    var tau = +pg.querySelector(".mars-eff__tau").getAttribute("x1");
    this.pdf = { w: pw, h: ph, ref: ref, shift: tau - ref, k: 176 / pw };
    this.tauLine = setter(pg.querySelector(".mars-eff__tau"));
    this.tauLbl = setter(pg.querySelector(".mars-eff__taulbl"));
    this.tauLine("opacity", "0"); this.tauLbl("opacity", "0");
    var bars = el("g", {}, pg);          // under the curve
    this.path = setter(el("path", { "class": "mars-eff__pdfpath" }, pg));
    this.bars = [];
    var nb = 22, bw = pw / nb;
    for (var b = 0; b < nb; b++) {
      this.bars.push({ x: (b + 0.5) * bw, f: 0.65 + 0.7 * ((b * 37) % 11) / 11,
                       set: setter(el("rect", { x: (b * bw + 1).toFixed(1), y: ph - 2,
                                                 width: (bw - 2).toFixed(1), height: 0,
                                                 "class": "mars-eff__bar" }, bars)) });
    }
    this.steps = [].slice.call(svg.querySelectorAll(".mars-eff__step")).map(function (t) {
      return { node: t, on: null };
    });
    this.lastShift = null;
  }

  /* y of the PDF at plot x, shifted by d plot units (circularly) */
  Layout.prototype.pdfY = function (x, d) {
    var P = this.pdf, u = x - P.ref - d;
    u = ((u + P.ref) % P.w + P.w) % P.w - P.ref;   // circular shift
    return P.h - 2 - pdfAt(u * P.k) * (P.h - 12);
  };

  Layout.prototype.render = function (s, sweptAll) {
    var self = this, P = this.pdf;

    /* gold standard: one cell at a time */
    var n = Math.min(this.gold.length, Math.floor(s * GOLD_RATE));
    for (var i = 0; i < this.gold.length; i++) {
      var g = this.gold[i];
      g.set("fill", i < n ? "rgba(58,58,58," + g.s.toFixed(3) + ")"
                          : i === n ? C_GOLD : C_EMPTY);
    }

    /* the strip: playhead, photons, blind windows growing behind detections */
    var p = sweptAll ? this.stripW : (s % SWEEP) / SWEEP * this.stripW;
    var px = p.toFixed(1);
    this.head("x1", px); this.head("x2", px);
    this.head("opacity", sweptAll ? "0" : "1");
    this.photons.forEach(function (ph) {
      var vis = ph.x <= p;
      ph.dot("opacity", vis ? "1" : "0");
      if (ph.band) ph.band("width", vis ? Math.min(ph.bmax, p - ph.x).toFixed(1) : "0");
    });

    /* MaRS: which step */
    var step = s < T1 ? 0 : s < T2 ? 1 : s < T3 ? 2 : s < T4 ? 3 : 0;
    this.steps.forEach(function (t, k) {
      var on = k + 1 === step;
      if (t.on !== on) { t.on = on; t.node.classList.toggle("is-on", on); }
    });
    var cardA = s < T1 ? 0 : s < T4 ? clamp01((s - T1) / FADE) : clamp01(1 - (s - T4) / 0.3);
    var ca = cardA.toFixed(2);
    this.entry("opacity", ca); this.lead("opacity", ca);
    this.hiCell("class", "mars-eff__cell" + (cardA > 0 ? " is-hi" : ""));

    var tauA = s < T2 ? 0 : s < T4 ? clamp01((s - T2) / FADE) : cardA;
    this.tauLine("opacity", tauA.toFixed(2)); this.tauLbl("opacity", tauA.toFixed(2));
    var d = s < T2 ? 0 : s < T4 ? P.shift * ease((s - T2) / SLIDE) : P.shift;
    var dk = d.toFixed(1);
    if (dk !== this.lastShift) {
      this.lastShift = dk;
      var pts = [];
      for (var x = 0; x <= P.w; x += 2) pts.push(x + " " + this.pdfY(x, d).toFixed(1));
      this.path("d", "M0 " + (P.h - 2) + "L" + pts.join("L") + "L" + P.w + " " + (P.h - 2) + "Z");
    }

    /* step 3: sampled bars under the curve, every grid cell at once */
    var a = s < T3 ? 0 : s < T4 ? clamp01((s - T3) / FADE) : clamp01(1 - (s - T4) / 0.3);
    this.bars.forEach(function (b) {
      var h = a > 0 ? (P.h - 2 - self.pdfY(b.x, P.shift)) * b.f * a : 0;
      b.set("height", h.toFixed(1)); b.set("y", (P.h - 2 - h).toFixed(1));
    });
    this.mars.forEach(function (c) {
      c.set("fill", a > 0 ? "rgba(14,122,70," + (a * c.s).toFixed(3) + ")" : C_EMPTY);
    });
  };

  /* ---------------- driver ---------------- */

  var layouts = {
    wide: new Layout(fig.querySelector(".mars-eff__svg.is-wide")),
    tall: new Layout(fig.querySelector(".mars-eff__svg.is-tall"))
  };
  var mq = window.matchMedia(STACK);
  function active() { return mq.matches ? layouts.tall : layouts.wide; }

  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (reduce) {
    layouts.wide.render(STATIC_T, true);
    layouts.tall.render(STATIC_T, true);
    fig.setAttribute("data-eff-state", "static");
    return;                                  // never a frame requested
  }

  var t = 0, prev = null, lastDraw = null, raf = 0, onScreen = false;
  active().render(0, false);

  function frame(now) {
    raf = 0;
    if (prev !== null) t = (t + Math.min(0.1, (now - prev) / 1000)) % LOOP;
    prev = now;
    /* draw on every other tick at 60 Hz (every 4th at 120 Hz); the 1 ms
       slack absorbs vsync jitter, and a late frame does not shift the grid */
    var since = lastDraw === null ? Infinity : now - lastDraw;
    if (since >= FRAME_MS - 1) {
      lastDraw = since > 2 * FRAME_MS ? now : lastDraw + FRAME_MS;
      active().render(t, false);
    }
    if (running()) raf = requestAnimationFrame(frame);
  }
  function running() { return onScreen && !document.hidden; }
  function update() {
    if (running()) {
      if (!raf) { prev = null; lastDraw = null; raf = requestAnimationFrame(frame); }
      fig.setAttribute("data-eff-state", "running");
    } else {
      if (raf) { cancelAnimationFrame(raf); raf = 0; }
      fig.setAttribute("data-eff-state", "paused");
    }
  }

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      onScreen = entries[entries.length - 1].isIntersecting;
      update();
    }).observe(fig);
  } else {
    onScreen = true;
  }
  document.addEventListener("visibilitychange", update);
  var onChange = function () { active().render(t, false); };
  if (mq.addEventListener) mq.addEventListener("change", onChange);
  else if (mq.addListener) mq.addListener(onChange);
  update();
})();
