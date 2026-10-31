/* The count-model ablation — #demo-ablation on the main page (stage v2.2-C;
 * rebuilt in v2.3-C with SBR 1.0 and the zoom rows, guide 0.8).
 *
 * Markup: figure[data-ablation] in index.html. Vanilla, no dependencies.
 *
 * ONE SOURCE OF NUMBERS: the figure's two visually hidden tables
 * (table.mars-abl__data[data-sbr="sbr06" | "sbr10"]). Each body row is one
 * count model (data-k renewal / zhang / mars) with four cells: reflectivity
 * PSNR val, test (dB), depth RMSE val, test (m). "val" is tested on data from
 * the row's own count model, "test" on gold-standard data. This script reads
 * the tables and draws from them: the two-panel dumbbell chart and its
 * aria-label. Nothing here holds a number. tools/audit_claims.py asserts
 * each table equals PROJECT_BRIEF 3.5 for its SBR. Since v2.4-A (guide 0.9)
 * the image captions are names only and this script never writes them.
 *
 * THE CHART is an inline SVG whose viewBox is its own CSS width, so 1 unit
 * is 1 px and the 12-14 px text stays 12-14 px at every width. Two panels,
 * SBR 0.6 and SBR 1.0, each with a header over a dark rule and its own axis
 * (reflectivity 0-40 dB; depth 0-0.15 m, since Zhang et al. tests at 0.119 m
 * at SBR 1.0) and "higher / lower is better" under it.
 *   - Wider than 600 px: side by side, the row labels drawn once at the
 *     left. From 601 to 767 px a panel is narrower than the axis title, so
 *     the title takes two lines there.
 *   - Phones (<= 600 px): the panels stack, each with its own row labels.
 * Its height is reserved in css/mars.css from the same constants (LAYOUTS)
 * and the same media queries, so drawing it shifts nothing. Hollow circle =
 * val, filled = test, joined by a line in the row colour (renewal --red,
 * Zhang et al. --blue, MaRS --green; MaRS's name bold). v2.2-P's rule holds:
 * the hollow val ring is drawn ABOVE the filled test dot, with a white
 * hairline just inside it, so a pair that nearly coincides reads as a ring
 * around a dot. Value labels: val on the outer side of its dot, test on the
 * inner side, so the two of a row never collide. Tick labels that would
 * touch are dropped, working leftwards from the last one (which carries the
 * unit and always stays). Colours are read from the CSS tokens.
 *
 * THE SBR BLOCKS (.mars-abl__zrow; v2.4-A, guide 0.9), one per SBR: a row
 * of the four originals (ground truth, Renewal, Zhang et al., MaRS count;
 * only the ground truth holds the window, 50 % x 50 % of its square), then
 * a row of four zoom panes in the same columns, each showing the window's
 * region of its own tile at 2x (the GT's own zoom included). Phones pair
 * each original with its zoom (css/mars.css, grid order). The block's
 * custom properties --u and --v (the window's position as fractions of
 * its travel, 0..1, clamped) place the window and translate each pane's
 * <img> (css/mars.css); this script only sets them. Each tile URL is used
 * twice (original and zoom), and both <img>s get it in the same pass, so
 * it is fetched once. The window moves by:
 *   - pointer (mouse, touch, pen): a press or drag anywhere on the GT square
 *     centres the window on the pointer (pointer capture, so a drag may
 *     leave the square). The GT square alone has touch-action: none, so the
 *     rest of the page scrolls as usual;
 *   - keyboard: the window is focusable (role slider); the arrow keys move
 *     it by 5 % of its travel, Home centres it.
 * The two blocks move independently. Defaults are in the markup (the concept's:
 * SBR 0.6 (0.62, 0.30), SBR 1.0 (0.25, 0.22)).
 *
 * THE TOGGLES. Reflectivity PSNR / Depth RMSE swaps the chart and every
 * tile. On phones a second toggle, SBR 0.6 / SBR 1.0, shows one block at a
 * time (figure[data-sbr-sel]; CSS hides the other).
 *
 * LAZY: no tile is requested until the figure comes within 300 px of the
 * viewport. Then only the blocks on screen load (both on wider screens, the
 * chosen one on phones), and only the current mode's tiles: depth tiles on
 * the first switch to Depth, SBR 1.0 tiles on a phone's first switch to it.
 */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";
  var SBRS = [{ k: "sbr06", name: "SBR 0.6" }, { k: "sbr10", name: "SBR 1.0" }];
  var ROWS = [
    { k: "renewal", name: "Renewal count", tok: "--red", fb: "#B03A2E" },
    { k: "zhang", name: "Zhang et al. count", tok: "--blue", fb: "#2E6DA4" },
    { k: "mars", name: "MaRS count", tok: "--green", fb: "#0E7A46", bold: true }
  ];
  var MODES = {
    refl: { col: 0, unit: "dB", dp: 2, tdp: 0, hi: 40, ticks: [0, 10, 20, 30, 40], best: 1,
            axis: ["Reflectivity PSNR,", "higher is better"], name: "Reflectivity PSNR" },
    depth: { col: 2, unit: "m", dp: 3, tdp: 2, hi: 0.15, ticks: [0, 0.05, 0.1, 0.15], best: -1,
             axis: ["Depth RMSE,", "lower is better"], name: "Depth RMSE" }
  };
  /* geometry per layout; css/mars.css reserves the height each gives. The
     row-label column (label) is fixed per layout, not measured, so a web
     font arriving late never moves the plot ("Zhang et al. count", the
     widest name, is 120 / 112 / 108 px at 14 / 13 / 12.5 px in Poppins):
     wide  (>= 768 px)  34 + 3 x 38 + 42 = 190
     mid   (601-767 px) 34 + 3 x 38 + 58 = 206 (two-line axis title)
     phone (<= 600 px)  2 x (32 + 3 x 34 + 42) + 14 = 366 */
  var LAYOUTS = {
    wide:  { q: "(min-width: 768px)", top: 34, row: 38, foot: 42, label: 138, name: 14, val: 13, title: 13, gap: 28 },
    mid:   { q: "(min-width: 601px) and (max-width: 767px)", top: 34, row: 38, foot: 58, label: 130, name: 13, val: 12.5, title: 13, gap: 24, twoLine: true },
    phone: { q: "(max-width: 600px)", top: 32, row: 34, foot: 42, label: 122, name: 12.5, val: 12, title: 13, stack: 14 }
  };
  var PAD_L = 12, PAD_R = 28;   /* inside each panel, around the plot */
  var STEP = 0.05;              /* keyboard step, as a fraction of the travel */

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

  function mq(q) { return window.matchMedia ? window.matchMedia(q) : { matches: false }; }

  function readTables(fig) {
    var data = {};
    Array.prototype.slice.call(fig.querySelectorAll("table.mars-abl__data"))
      .forEach(function (tb) {
        var rows = data[tb.getAttribute("data-sbr")] = {};
        Array.prototype.slice.call(tb.querySelectorAll("tbody tr")).forEach(function (tr) {
          rows[tr.getAttribute("data-k")] = Array.prototype.slice
            .call(tr.querySelectorAll("td"))
            .map(function (td) { return parseFloat(td.textContent); });
        });
      });
    return data;
  }

  function clamp01(x) { return Math.max(0, Math.min(1, x)); }

  function initOne(fig) {
    var svg = fig.querySelector(".mars-abl__chart");
    if (!svg) return;
    var data = readTables(fig);
    var modeBtns = Array.prototype.slice.call(fig.querySelectorAll(".mars-abl__modes [data-mode]"));
    var sbrBtns = Array.prototype.slice.call(fig.querySelectorAll(".mars-abl__sbrs [data-sbr]"));
    var zrows = Array.prototype.slice.call(fig.querySelectorAll(".mars-abl__zrow"));
    var mode = fig.getAttribute("data-mode") || "refl";
    var sbrSel = fig.getAttribute("data-sbr-sel") || "sbr06";
    var revealed = false, lastW = -1;
    var Q = { wide: mq(LAYOUTS.wide.q), mid: mq(LAYOUTS.mid.q), phone: mq(LAYOUTS.phone.q) };

    function fmt(v, m) { return v.toFixed(MODES[m].dp); }
    function layout() { return Q.phone.matches ? "phone" : Q.mid.matches ? "mid" : "wide"; }

    /* ---- the chart ---------------------------------------------------- */
    function draw() {
      var m = MODES[mode], lk = layout(), G = LAYOUTS[lk];
      var W = Math.round(svg.getBoundingClientRect().width);
      if (!W) return;
      lastW = W;
      var grey = token("--grey", "#5A5A5A"), dark = token("--dark", "#1F1F1F");
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      svg.setAttribute("font-family", "Inter, Helvetica Neue, Arial, sans-serif");
      var ph = G.top + ROWS.length * G.row + G.foot;          /* one panel's height */
      var H = lk === "phone" ? 2 * ph + G.stack : ph;
      svg.setAttribute("viewBox", "0 0 " + W + " " + H);

      /* row names, once at the left (phones: once per panel) */
      function names(oy) {
        ROWS.forEach(function (r, i) {
          el("text", { x: 0, y: oy + G.top + i * G.row + G.row / 2 + 5, "font-size": G.name,
                       fill: dark, "font-weight": r.bold ? 700 : 500,
                       "class": "mars-abl__name" }, svg, r.name);
        });
      }

      var L = G.label, pw, boxes = [];
      names(0);
      if (lk === "phone") {
        names(ph + G.stack);
        pw = W - L;
        SBRS.forEach(function (s, i) { boxes.push({ s: s, ox: L, oy: i * (ph + G.stack), lo: 0, hi: W }); });
      } else {
        pw = (W - L - G.gap) / 2;
        SBRS.forEach(function (s, i) {
          var ox = L + i * (pw + G.gap);
          boxes.push({ s: s, ox: ox, oy: 0, lo: i ? ox - G.gap / 2 : 0, hi: i ? W : ox + pw + G.gap / 2 });
        });
      }

      boxes.forEach(function (b) {
        var ox = b.ox, oy = b.oy, x0 = ox + PAD_L, x1 = ox + pw - PAD_R;
        var X = function (v) { return x0 + Math.min(v, m.hi) / m.hi * (x1 - x0); };
        var rows = data[b.s.k], base = oy + G.top + ROWS.length * G.row;
        /* header and its dark rule */
        el("text", { x: ox + pw / 2, y: oy + 14, "font-size": 13, "font-weight": 600, fill: dark,
                     "text-anchor": "middle", "font-family": "Poppins, Inter, sans-serif",
                     "class": "mars-abl__head" }, svg, b.s.name);
        el("line", { x1: ox, y1: oy + 22, x2: ox + pw, y2: oy + 22, stroke: dark, "stroke-width": 2 }, svg);
        /* grid and ticks; labels thinned right to left so none touch */
        var kept = null;
        for (var i = m.ticks.length - 1; i >= 0; i--) {
          var t = m.ticks[i], x = X(t);
          el("line", { x1: x, y1: oy + G.top - 6, x2: x, y2: base, stroke: "#e6e9e7", "stroke-width": 1 }, svg);
          var lab = el("text", { x: x, y: base + 17, "font-size": 12, fill: grey, "text-anchor": "middle",
                                 "class": "mars-abl__tick" }, svg,
                       t.toFixed(m.tdp) + (i === m.ticks.length - 1 ? " " + m.unit : ""));
          var w = lab.getComputedTextLength ? lab.getComputedTextLength() : 30;
          if (kept !== null && x + w / 2 > kept - 6) { svg.removeChild(lab); continue; }
          kept = x - w / 2;
        }
        /* the axis title under its own plot, kept inside its panel */
        var lines = G.twoLine ? m.axis : [m.axis.join(" ")];
        lines.forEach(function (txt, j) {
          var a = el("text", { x: (x0 + x1) / 2, y: base + 35 + j * 16, "font-size": G.title, fill: grey,
                               "text-anchor": "middle", "class": "mars-abl__axis" }, svg, txt);
          var tw = a.getComputedTextLength ? a.getComputedTextLength() : 0;
          if (tw) a.setAttribute("x", Math.max(b.lo + tw / 2, Math.min(b.hi - tw / 2, (x0 + x1) / 2)));
        });
        /* the dumbbells */
        ROWS.forEach(function (r, i) {
          var y = oy + G.top + i * G.row + G.row / 2;
          var v = rows[r.k][m.col], t = rows[r.k][m.col + 1];
          var c = token(r.tok, r.fb);
          el("line", { x1: X(v), y1: y, x2: X(t), y2: y, stroke: c,
                       "stroke-width": 2.5, "stroke-opacity": 0.85 }, svg);
          el("circle", { cx: X(v), cy: y, r: 7, fill: "#fff" }, svg);
          el("circle", { cx: X(t), cy: y, r: 7, fill: c, "class": "mars-abl__dotc" }, svg);
          el("circle", { cx: X(v), cy: y, r: 5, fill: "none", stroke: "#fff", "stroke-width": 1.5 }, svg);
          el("circle", { cx: X(v), cy: y, r: 7, fill: "none", stroke: c, "stroke-width": 2.5,
                         "class": "mars-abl__ring" }, svg);
          /* val on the outer side, test on the inner side */
          var valLeft = v <= t;
          el("text", { x: X(v) + (valLeft ? -12 : 12), y: y + 4.5, "font-size": G.val,
                       fill: grey, "text-anchor": valLeft ? "end" : "start",
                       "class": "mars-abl__val", "data-k": r.k, "data-sbr": b.s.k }, svg, fmt(v, mode));
          el("text", { x: X(t) + (valLeft ? 12 : -12), y: y + 4.5, "font-size": G.val,
                       fill: c, "font-weight": 700, "text-anchor": valLeft ? "start" : "end",
                       "class": "mars-abl__test", "data-k": r.k, "data-sbr": b.s.k }, svg, fmt(t, mode));
        });
      });

      /* the finding, in words, from the same numbers */
      var parts = SBRS.map(function (s) {
        return s.name + ": " + ROWS.map(function (r) {
          var row = data[s.k][r.k];
          return r.name + " " + fmt(row[m.col], mode) + " on its own data, " +
                 fmt(row[m.col + 1], mode) + " " + m.unit + " on gold-standard data";
        }).join(", ");
      });
      var best = SBRS.map(function (s) {
        return ROWS.reduce(function (a, r) {
          return (data[s.k][r.k][m.col + 1] - data[s.k][a.k][m.col + 1]) * m.best > 0 ? r : a;
        }, ROWS[0]);
      });
      var finding = best[0] === best[1]
        ? "The " + best[0].name.replace(" count", "") + " count gives the best result on gold-standard data at both SBR levels."
        : SBRS.map(function (s, i) {
            return "At " + s.name + " the " + best[i].name.replace(" count", "") +
                   " count gives the best result on gold-standard data.";
          }).join(" ");
      svg.setAttribute("aria-label", m.name + " (" + m.axis[1] + ") for each count model " +
        "at SBR 0.6 and SBR 1.0, tested on data from its own count model and on " +
        "gold-standard data. " + parts.join(". ") + ". " + finding);
    }

    /* ---- lazy tiles: only the rows on screen, only the current mode --- */
    function rowShown(zr) { return !Q.phone.matches || zr.getAttribute("data-sbr") === sbrSel; }
    function loadImages() {
      if (!revealed) return;
      zrows.forEach(function (zr) {
        if (!rowShown(zr)) return;
        Array.prototype.slice.call(zr.querySelectorAll("img[data-src-refl]")).forEach(function (img) {
          var src = img.getAttribute("data-src-" + mode);
          if (src && img.getAttribute("src") !== src) img.setAttribute("src", src);
          img.setAttribute("alt", img.getAttribute("data-alt-" + mode) || "");
        });
      });
    }

    /* ---- the window --------------------------------------------------- */
    zrows.forEach(function (zr) {
      var gt = zr.querySelector(".mars-abl__gt"), win = zr.querySelector(".mars-abl__win");
      if (!gt || !win) return;
      var cs = getComputedStyle(zr);
      var u = parseFloat(cs.getPropertyValue("--u")) || 0, v = parseFloat(cs.getPropertyValue("--v")) || 0;
      var drag = null;

      function set(nu, nv) {
        u = Math.round(clamp01(nu) * 1e4) / 1e4;
        v = Math.round(clamp01(nv) * 1e4) / 1e4;
        zr.style.setProperty("--u", String(u));
        zr.style.setProperty("--v", String(v));
        win.setAttribute("aria-valuenow", String(Math.round(u * 100)));
        win.setAttribute("aria-valuetext", Math.round(u * 100) + "% across, " + Math.round(v * 100) + "% down");
      }
      /* centre the window on the pointer: its left edge is a quarter of the
         square to the left of the pointer, and it travels half the square */
      function at(e) {
        var r = gt.getBoundingClientRect();
        set((e.clientX - r.left - r.width / 4) / (r.width / 2),
            (e.clientY - r.top - r.height / 4) / (r.height / 2));
      }
      gt.addEventListener("pointerdown", function (e) {
        if (e.pointerType === "mouse" && e.button !== 0) return;
        e.preventDefault();
        drag = e.pointerId;
        try { gt.setPointerCapture(e.pointerId); } catch (err) { /* synthetic */ }
        at(e);
      });
      gt.addEventListener("pointermove", function (e) { if (drag === e.pointerId) at(e); });
      ["pointerup", "pointercancel", "lostpointercapture"].forEach(function (t) {
        gt.addEventListener(t, function (e) { if (drag === e.pointerId) drag = null; });
      });
      gt.addEventListener("dragstart", function (e) { e.preventDefault(); });
      win.addEventListener("keydown", function (e) {
        var d = { ArrowLeft: [-STEP, 0], ArrowRight: [STEP, 0], ArrowUp: [0, -STEP], ArrowDown: [0, STEP] }[e.key];
        if (d) { e.preventDefault(); set(u + d[0], v + d[1]); }
        else if (e.key === "Home") { e.preventDefault(); set(0.5, 0.5); }
      });
      set(u, v);
    });

    /* ---- toggles ------------------------------------------------------ */
    function setMode(m) {
      if (m === mode || !MODES[m]) return;
      mode = m;
      fig.setAttribute("data-mode", m);
      modeBtns.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-mode") === m ? "true" : "false");
      });
      draw();
      loadImages();
    }
    function setSbr(s) {
      if (s === sbrSel) return;
      sbrSel = s;
      fig.setAttribute("data-sbr-sel", s);
      sbrBtns.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-sbr") === s ? "true" : "false");
      });
      loadImages();
    }
    modeBtns.forEach(function (b) {
      b.addEventListener("click", function () { setMode(b.getAttribute("data-mode")); });
    });
    sbrBtns.forEach(function (b) {
      b.addEventListener("click", function () { setSbr(b.getAttribute("data-sbr")); });
    });

    draw();
    if ("ResizeObserver" in window) {
      new ResizeObserver(function () {
        if (Math.round(svg.getBoundingClientRect().width) !== lastW) draw();
      }).observe(svg);
    } else {
      window.addEventListener("resize", draw);
    }
    Object.keys(Q).forEach(function (k) {
      var q = Q[k];
      var on = function () { draw(); loadImages(); };   /* a widened phone shows both rows */
      if (q.addEventListener) q.addEventListener("change", on);
      else if (q.addListener) q.addListener(on);
    });
    /* web fonts change the tick labels' widths, which the thinning reads */
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw);

    function reveal() { revealed = true; loadImages(); }
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
