/* The count-model ablation — #demo-ablation on the main page (stage v2.2-C).
 *
 * Markup: figure[data-ablation] in index.html. Vanilla, no dependencies.
 *
 * ONE SOURCE OF NUMBERS: the figure's visually hidden table
 * (table.mars-abl__data). Each body row is one count model (data-k renewal /
 * zhang / mars) with four cells: reflectivity PSNR val, test (dB), depth
 * RMSE val, test (m). "val" is tested on data from the row's own count
 * model, "test" on gold-standard data. This script reads the table and draws
 * from it: the dumbbell chart, its aria-label and the tile captions. Nothing
 * here holds a number. tools/audit_claims.py asserts the table equals
 * PROJECT_BRIEF 3.5 and that the captions the HTML ships equal the table.
 *
 * THE CHART is an inline SVG whose viewBox is its own CSS width, so 1 unit
 * is 1 px and the 12-14 px text stays 12-14 px at every width (the concept's
 * fixed 360-unit minimum would shrink it below 12 px on a 343 px column).
 * Its height is reserved in css/mars.css from the same constants as WIDE /
 * NARROW below, so drawing it shifts nothing. The layout switches on the
 * site's breakpoint, (max-width: 600px), the same query as the CSS. Hollow
 * circle = val, filled = test, joined by a line in the row colour (renewal
 * --red, Zhang et al. --blue, MaRS --green; MaRS's name bold). Value labels:
 * val on the outer side of its dot, test on the inner side, so the two of a
 * row never collide. Colours are read from the CSS tokens.
 *
 * THE TOGGLE (Reflectivity PSNR / Depth RMSE) drives chart and tiles
 * together. LAZY: the tiles load when the figure comes within 300 px of the
 * viewport; the depth tiles only when Depth RMSE is first chosen.
 */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var ROWS = [
    { k: "renewal", name: "Renewal count", tok: "--red", fb: "#B03A2E" },
    { k: "zhang", name: "Zhang et al. count", tok: "--blue", fb: "#2E6DA4" },
    { k: "mars", name: "MaRS count", tok: "--green", fb: "#0E7A46", bold: true }
  ];
  var MODES = {
    refl: { col: 0, unit: "dB", dp: 2, hi: 40, ticks: [0, 10, 20, 30, 40],
            axis: "Reflectivity PSNR, higher is better", name: "Reflectivity PSNR" },
    depth: { col: 2, unit: "m", dp: 3, hi: 0.12, ticks: [0, 0.03, 0.06, 0.09, 0.12],
             axis: "Depth RMSE, lower is better", name: "Depth RMSE" }
  };
  /* geometry, per layout. css/mars.css reserves TOP + 3 * ROW_H + FOOT. */
  var WIDE = { top: 14, row: 42, foot: 44, label: 190, right: 64, name: 14, val: 13 };
  var NARROW = { top: 14, row: 40, foot: 44, label: 122, right: 50, name: 12.5, val: 12 };

  function el(tag, attrs, parent, text) {
    var e = document.createElementNS(NS, tag);
    for (var a in attrs) e.setAttribute(a, attrs[a]);
    if (text !== undefined) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }

  function token(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function readTable(fig) {
    var data = {};
    Array.prototype.slice.call(fig.querySelectorAll(".mars-abl__data tbody tr"))
      .forEach(function (tr) {
        data[tr.getAttribute("data-k")] = Array.prototype.slice
          .call(tr.querySelectorAll("td"))
          .map(function (td) { return parseFloat(td.textContent); });
      });
    return data;
  }

  function initOne(fig) {
    var svg = fig.querySelector(".mars-abl__chart");
    if (!svg) return;
    var data = readTable(fig);
    var buttons = Array.prototype.slice.call(fig.querySelectorAll(".mars-compare__mode"));
    var imgs = Array.prototype.slice.call(fig.querySelectorAll("img[data-src-refl]"));
    var caps = Array.prototype.slice.call(fig.querySelectorAll(".mars-abl__cap b[data-k]"));
    var mode = fig.getAttribute("data-mode") || "refl";
    var loaded = false, lastW = -1;
    var narrowQ = window.matchMedia ? window.matchMedia("(max-width: 600px)") : null;

    function fmt(v, m) { return v.toFixed(MODES[m].dp); }

    function draw() {
      var m = MODES[mode];
      var G = narrowQ && narrowQ.matches ? NARROW : WIDE;
      var W = Math.round(svg.getBoundingClientRect().width);
      if (!W) return;
      lastW = W;
      var H = G.top + ROWS.length * G.row + G.foot;
      var x0 = G.label, x1 = W - G.right;
      var X = function (v) { return x0 + v / m.hi * (x1 - x0); };
      var grey = token("--grey", "#5A5A5A"), dark = token("--dark", "#1F1F1F");
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      svg.setAttribute("viewBox", "0 0 " + W + " " + H);
      svg.setAttribute("font-family", "Inter, Helvetica Neue, Arial, sans-serif");

      var ph = ROWS.length * G.row;
      /* a narrow plot (viewports below ~360 px) labels every other tick, so
         "0.09" and "0.12 m" never touch; the grid lines stay */
      var thin = x1 - x0 < 190;
      m.ticks.forEach(function (t, i) {
        el("line", { x1: X(t), y1: G.top - 6, x2: X(t), y2: G.top + ph,
                     stroke: "#e6e9e7", "stroke-width": 1 }, svg);
        if (thin && i % 2) return;
        el("text", { x: X(t), y: G.top + ph + 18, "font-size": 12, fill: grey,
                     "text-anchor": "middle" }, svg,
           t + (i === m.ticks.length - 1 ? "\u00a0" + m.unit : ""));
      });
      /* the axis title is centred on the plot, but never runs off the SVG */
      var ax = el("text", { x: (x0 + x1) / 2, y: G.top + ph + 38, "font-size": 13, fill: grey,
                            "text-anchor": "middle" }, svg, m.axis);
      var tw = ax.getComputedTextLength ? ax.getComputedTextLength() : 0;
      if (tw) ax.setAttribute("x", Math.max(tw / 2, Math.min(W - tw / 2, (x0 + x1) / 2)));

      ROWS.forEach(function (r, i) {
        var y = G.top + i * G.row + G.row / 2;
        var v = data[r.k][m.col], t = data[r.k][m.col + 1];
        var c = token(r.tok, r.fb);
        el("text", { x: 0, y: y + 5, "font-size": G.name, fill: dark,
                     "font-weight": r.bold ? 700 : 500, "class": "mars-abl__name" }, svg, r.name);
        el("line", { x1: X(v), y1: y, x2: X(t), y2: y, stroke: c,
                     "stroke-width": 2.5, "stroke-opacity": 0.85 }, svg);
        el("circle", { cx: X(v), cy: y, r: 7, fill: "#fff", stroke: c, "stroke-width": 2.5 }, svg);
        el("circle", { cx: X(t), cy: y, r: 7, fill: c }, svg);
        /* val on the outer side, test on the inner side */
        var valLeft = v <= t;
        el("text", { x: X(v) + (valLeft ? -12 : 12), y: y + 4.5, "font-size": G.val,
                     fill: grey, "text-anchor": valLeft ? "end" : "start",
                     "class": "mars-abl__val", "data-k": r.k }, svg, fmt(v, mode));
        el("text", { x: X(t) + (valLeft ? 12 : -12), y: y + 4.5, "font-size": G.val,
                     fill: c, "font-weight": 700, "text-anchor": valLeft ? "start" : "end",
                     "class": "mars-abl__test", "data-k": r.k }, svg, fmt(t, mode));
      });

      /* the finding, in words, from the same numbers */
      var parts = ROWS.map(function (r) {
        var v = data[r.k][m.col], t = data[r.k][m.col + 1];
        return r.name + " " + fmt(v, mode) + " on its own data, " + fmt(t, mode) +
               " " + m.unit + " on gold-standard data";
      });
      svg.setAttribute("aria-label", m.name + " (" + m.axis.split(", ")[1] +
        ") for each count model, tested on data from its own count model and on " +
        "gold-standard data. " + parts.join(". ") +
        ". The MaRS count gives the best result on gold-standard data.");
    }

    function captions() {
      var m = MODES[mode];
      caps.forEach(function (b) {
        b.textContent = fmt(data[b.getAttribute("data-k")][m.col + 1], mode) + "\u00a0" + m.unit;
      });
    }

    function loadImages() {
      imgs.forEach(function (img) {
        var src = img.getAttribute("data-src-" + mode);
        if (src && img.getAttribute("src") !== src) img.setAttribute("src", src);
        img.setAttribute("alt", img.getAttribute("data-alt-" + mode) || "");
      });
    }

    function setMode(m) {
      if (m === mode || !MODES[m]) return;
      mode = m;
      fig.setAttribute("data-mode", m);
      buttons.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-mode") === m ? "true" : "false");
      });
      draw();
      captions();
      if (loaded) loadImages();
    }
    buttons.forEach(function (b) {
      b.addEventListener("click", function () { setMode(b.getAttribute("data-mode")); });
    });

    draw();
    captions();
    if ("ResizeObserver" in window) {
      new ResizeObserver(function () {
        if (Math.round(svg.getBoundingClientRect().width) !== lastW) draw();
      }).observe(svg);
    } else {
      window.addEventListener("resize", draw);
    }
    if (narrowQ) {
      if (narrowQ.addEventListener) narrowQ.addEventListener("change", draw);
      else if (narrowQ.addListener) narrowQ.addListener(draw);
    }

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
      .call(document.querySelectorAll("[data-ablation]"))
      .forEach(initOne);
  });
})();
