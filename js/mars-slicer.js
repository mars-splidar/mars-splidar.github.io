/* The cube slicer — main page, under the teaser (stage v2.1-C).
 *
 * Loaded on demand by js/mars-main.js (section 4); never by markup. Markup:
 * figure#mars-slicer in index.html. Data: assets/data/slicer/, written by
 * tools/build_slicer_data.py from the paper's own Fig. 1 cubes. Vanilla, no
 * dependencies.
 *
 * WHAT IT SHOWS. Pick a pixel (click or tap an image, or arrow keys on a
 * focused image) and a moment (drag on the chart, or the Time range input):
 *   - three 128 x 128 time slices, Poisson · gold standard · MaRS, each the
 *     photons registered in a 4-bin (1.6 ns) window around the selected
 *     time, under ONE brightness mapping fixed from the gold cube
 *     (meta.brightness.K) — never normalised per image;
 *   - one chart of the pixel's (n x n pooled) arrival histogram: gold-
 *     standard bars, MaRS and Poisson as step lines, RAW COUNTS on one shared
 *     axis, the true delay dashed, the selected time as a cursor + band;
 *   - the readout: each simulator's return centre (count-weighted mean
 *     arrival within +-10 ns of the true delay), relative to the true delay.
 *     It is the same computation as tools/build_slicer_data.py, which ships
 *     the default state's text in the HTML.
 *
 * INPUT. Mouse/pen: press or drag on an image sets the pixel; press or drag on
 * the chart sets the time. Touch: a TAP on an image sets the pixel (a swipe
 * scrolls the page, touch-action: manipulation); on the chart the cursor moves
 * only after a sideways drag of more than 8 px (stage 10b's rule, as in
 * js/mars-compare.js), and touch-action: pan-y hands vertical swipes to the
 * page. Keyboard: images are focusable, arrows move the pixel (Shift: 8 px);
 * the Time input is a real <input type="range">; presets, pooling and range
 * are aria-pressed buttons. The readout is aria-live="polite"; its text is
 * rewritten at most every 400 ms while a drag is under way.
 *
 * PRESET NOTE (stage v2.3-A, guide 0.8). The aria-live <p> under the chips
 * shows the selected preset's sentence, read from meta.presets[].note (the
 * sentences live only in tools/build_slicer_data.py, which also ships the
 * default one as static HTML). A manual pixel or time pick clears the preset
 * and so empties the note; its box keeps its height (css/mars.css). Pooling
 * and range keep the preset, and so the note. Written only when it changes.
 *
 * FAILURE. A missing file, a failed inflate or no DecompressionStream leaves
 * the placeholder stills in place with a one-line message.
 */
(function () {
  "use strict";

  var fig = document.getElementById("mars-slicer");
  if (!fig || fig._marsSlicer) return;
  fig._marsSlicer = true;

  var KEYS = ["poisson", "gold", "mars"];
  var BASE = fig.getAttribute("data-slicer-base") || "assets/data/slicer/";
  var WIN = 2;              /* bins either side: a 4-bin (1.56 ns) window */
  var ZOOM_NS = 15;         /* "Around the peak": +-15 ns of the true delay */
  var RO_HALF = 10;         /* readout window, +-ns (meta overrides) */
  var INTENT = 8;           /* touch: px of sideways travel before a drag */
  var RO_THROTTLE = 400;    /* ms between readout writes during a drag */

  var meta, cube = {}, tau, H, W, NB, TR, DT, K;
  var st = { i: 64, j: 64, t: 128, r: 1, zoom: 1, preset: null };
  var geom = null;          /* the chart's last x mapping, for pointer input */

  var cvs = Array.prototype.slice.call(fig.querySelectorAll(".mars-slicer__cv"));
  var chart = fig.querySelector(".mars-slicer__chartcv");
  var readout = fig.querySelector(".mars-slicer__readout");
  var range = fig.querySelector(".mars-slicer__range");
  var tval = fig.querySelector(".mars-slicer__tval");
  var status = fig.querySelector(".mars-slicer__status");
  var pnote = fig.querySelector(".mars-slicer__pnote-live");
  var chips = Array.prototype.slice.call(fig.querySelectorAll("[data-preset]"));
  var pools = Array.prototype.slice.call(fig.querySelectorAll("[data-pool]"));
  var zooms = Array.prototype.slice.call(fig.querySelectorAll("[data-zoom]"));

  function msg(which) {
    if (!status) return;
    Array.prototype.slice.call(status.querySelectorAll("[data-msg]"))
      .forEach(function (el) { el.hidden = el.getAttribute("data-msg") !== which; });
    status.hidden = !which;
  }

  function fail(err) {
    fig.setAttribute("data-slicer-state", "error");
    msg("error");
    if (window.console && console.warn) console.warn("MaRS slicer:", err);
  }

  /* ---------------- data ---------------- */

  function fetchBytes(name) {
    return fetch(BASE + name).then(function (r) {
      if (!r.ok) throw new Error(name + ": HTTP " + r.status);
      return r.arrayBuffer();
    }).then(function (buf) {
      var u8 = new Uint8Array(buf);
      /* gzip magic 1f 8b. If a server already inflated the file (it sent
         Content-Encoding: gzip), the bytes are the payload itself. */
      if (u8.length < 2 || u8[0] !== 0x1f || u8[1] !== 0x8b) return u8;
      if (typeof DecompressionStream === "undefined")
        throw new Error("no DecompressionStream");
      var s = new Blob([u8]).stream().pipeThrough(new DecompressionStream("gzip"));
      return new Response(s).arrayBuffer().then(function (b) { return new Uint8Array(b); });
    });
  }

  function load() {
    return fetch(BASE + "meta.json").then(function (r) {
      if (!r.ok) throw new Error("meta.json: HTTP " + r.status);
      return r.json();
    }).then(function (m) {
      meta = m;
      H = m.shape[0]; W = m.shape[1]; NB = m.shape[2];
      TR = m.t_r_ns; DT = m.bin_ns; K = m.brightness.K;
      RO_HALF = (m.readout && m.readout.half_window_ns) || RO_HALF;
      var names = KEYS.concat(["tau"]);
      return Promise.all(names.map(function (k) { return fetchBytes(m.files[k].path); }))
        .then(function (arr) {
          KEYS.forEach(function (k, n) {
            if (arr[n].length !== H * W * NB) throw new Error(k + ": wrong size " + arr[n].length);
            cube[k] = arr[n];
          });
          var tb = arr[3];
          if (tb.length !== H * W * 4) throw new Error("tau: wrong size " + tb.length);
          /* float32 little-endian; copy so the view is aligned */
          var dv = new DataView(tb.buffer, tb.byteOffset, tb.byteLength);
          tau = new Float32Array(H * W);
          for (var q = 0; q < H * W; q++) tau[q] = dv.getFloat32(q * 4, true);
        });
    });
  }

  /* ---------------- maths (same as tools/build_slicer_data.py) ---------------- */

  function pooled(key) {
    var c = cube[key], h = new Float64Array(NB), r = st.r;
    for (var di = -r; di <= r; di++) for (var dj = -r; dj <= r; dj++) {
      var i = Math.min(H - 1, Math.max(0, st.i + di));
      var j = Math.min(W - 1, Math.max(0, st.j + dj));
      var o = (i * W + j) * NB;
      for (var b = 0; b < NB; b++) h[b] += c[o + b];
    }
    return h;
  }
  function rel(tns, t0) { return ((tns - t0 + TR / 2) % TR + TR) % TR - TR / 2; }
  function centre(h, t0) {
    var s = 0, n = 0;
    for (var b = 0; b < NB; b++) {
      var rv = rel((b + 0.5) * DT, t0);
      if (Math.abs(rv) < RO_HALF) { s += h[b] * rv; n += h[b]; }
    }
    return n ? s / n : 0;
  }
  function fmtNs(v) {                       /* '+0.1', '−2.7', '0.0' */
    var r = Math.round(Math.abs(v) * 10) / 10;
    if (r === 0) return "0.0 ns";
    return (v > 0 ? "+" : "−") + r.toFixed(1) + " ns";
  }
  function binTime(b) { return (b + 0.5) * DT; }

  /* ---------------- drawing ---------------- */

  var css = getComputedStyle(document.documentElement);
  function tok(name, fb) { var v = css.getPropertyValue(name).trim(); return v || fb; }
  var C = {
    red: tok("--red", "#B03A2E"), green: tok("--green", "#0E7A46"),
    gold: tok("--gold", "#CFB991"), aged: tok("--aged", "#8E6F3E"),
    grey: tok("--grey", "#5A5A5A"), rule: "#D5D9D5", bars: "#9AA09A",
    delay: "#555555"
  };
  var FONT = tok("--font-body", "Inter, Arial, sans-serif");

  function drawImages() {
    for (var k = 0; k < 3; k++) {
      var cv = cvs[k], ctx = cv.getContext("2d"), img = ctx.createImageData(W, H);
      var c = cube[cv.getAttribute("data-cube")], d = img.data;
      for (var i = 0; i < H; i++) for (var j = 0; j < W; j++) {
        var v = 0, o = (i * W + j) * NB;
        for (var b = st.t - WIN; b < st.t + WIN; b++) v += c[o + ((b + NB) % NB)];
        var L = 1 - Math.exp(-3 * v / K), p = (i * W + j) * 4;
        d[p] = 20 + L * 226; d[p + 1] = 24 + L * 216; d[p + 2] = 26 + L * 200; d[p + 3] = 255;
      }
      ctx.putImageData(img, 0, 0);
      /* the pooling box and a broken crosshair, in gold */
      var r = st.r;
      ctx.strokeStyle = C.gold; ctx.lineWidth = 1;
      ctx.strokeRect(st.j - r - 0.5, st.i - r - 0.5, 2 * r + 2, 2 * r + 2);
      ctx.globalAlpha = 0.55; ctx.beginPath();
      ctx.moveTo(st.j + 0.5, 0); ctx.lineTo(st.j + 0.5, st.i - r - 1.5);
      ctx.moveTo(st.j + 0.5, st.i + r + 2.5); ctx.lineTo(st.j + 0.5, H);
      ctx.moveTo(0, st.i + 0.5); ctx.lineTo(st.j - r - 1.5, st.i + 0.5);
      ctx.moveTo(st.j + r + 2.5, st.i + 0.5); ctx.lineTo(W, st.i + 0.5);
      ctx.stroke(); ctx.globalAlpha = 1;
    }
  }

  var hs = null;            /* pooled histograms, recomputed on pixel/pool change */
  function recompute() {
    hs = {};
    KEYS.forEach(function (k) { hs[k] = pooled(k); });
  }

  function drawChart() {
    var dpr = window.devicePixelRatio || 1;
    var w = chart.clientWidth, h = chart.clientHeight;
    if (!w || !h) return;
    var pw0 = Math.round(w * dpr), ph0 = Math.round(h * dpr);
    if (chart.width !== pw0 || chart.height !== ph0) { chart.width = pw0; chart.height = ph0; }
    var ctx = chart.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var t0 = tau[st.i * W + st.j];
    var small = w < 520;
    var fs = 12;
    var L = small ? 44 : 52, R = small ? 12 : 16, T = 8, Bm = small ? 34 : 36;
    var pw = w - L - R, ph = h - T - Bm;
    var x0 = st.zoom ? -ZOOM_NS : -t0, x1 = st.zoom ? ZOOM_NS : TR - t0;
    function X(v) { return L + (v - x0) / (x1 - x0) * pw; }
    var bins = [];
    for (var b = 0; b < NB; b++) {
      var rv = st.zoom ? rel(binTime(b), t0) : binTime(b) - t0;
      if (rv >= x0 && rv <= x1) bins.push([b, rv]);
    }
    bins.sort(function (a, c) { return a[1] - c[1]; });
    var ymax = 1;
    bins.forEach(function (e) { KEYS.forEach(function (k) { ymax = Math.max(ymax, hs[k][e[0]]); }); });
    var top = niceTop(ymax);
    function Y(v) { return T + ph - v / top * ph; }

    /* grid + y ticks: raw counts, one shared axis */
    ctx.font = fs + "px " + FONT;
    ctx.lineWidth = 1; ctx.strokeStyle = C.rule; ctx.fillStyle = C.grey;
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    for (var g = 0; g <= 4; g++) {
      var yv = top * g / 4, y = Math.round(Y(yv)) + 0.5;
      ctx.beginPath(); ctx.moveTo(L, y); ctx.lineTo(L + pw, y); ctx.stroke();
      ctx.fillText(String(Math.round(yv)), L - 6, y);
    }
    /* x ticks */
    ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
    /* ticks: relative ns around the peak; ABSOLUTE ns (0, 10, ... 100) over
       the full period, each placed at its true position */
    var step = st.zoom ? 5 : (small ? 20 : 10), v;
    if (st.zoom) {
      for (v = Math.ceil(x0 / step) * step; v <= x1 + 1e-9; v += step)
        ctx.fillText((v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v), X(v), T + ph + 15);
    } else {
      for (v = 0; v <= TR + 1e-9; v += step) ctx.fillText(String(v), X(v - t0), T + ph + 15);
    }
    ctx.fillText(st.zoom ? "time relative to this pixel’s true delay (ns)"
                         : "time in the laser period (ns)", L + pw / 2, T + ph + 31);
    ctx.save(); ctx.translate(8, T + ph / 2); ctx.rotate(-Math.PI / 2);
    ctx.textBaseline = "middle";
    ctx.fillText("photons per bin", 0, 0); ctx.restore();

    /* the selected time's window band */
    var trv = st.zoom ? rel(binTime(st.t), t0) : binTime(st.t) - t0;
    var cursorIn = trv >= x0 && trv <= x1;
    if (cursorIn) {
      ctx.fillStyle = "rgba(207,185,145,0.28)";
      ctx.fillRect(X(trv - WIN * DT), T, X(trv + WIN * DT) - X(trv - WIN * DT), ph);
    }
    /* gold-standard bars */
    var bw = Math.max(1, pw / ((x1 - x0) / DT) - 0.6);
    ctx.fillStyle = C.bars;
    bins.forEach(function (e) {
      var y = Y(hs.gold[e[0]]);
      ctx.fillRect(X(e[1]) - bw / 2, y, bw, T + ph - y);
    });
    /* step lines */
    function line(k, col, wd) {
      ctx.strokeStyle = col; ctx.lineWidth = wd; ctx.lineJoin = "miter";
      ctx.beginPath();
      var prev = null;
      bins.forEach(function (e, n) {
        var xa = X(e[1] - DT / 2), xb = X(e[1] + DT / 2), y = Y(hs[k][e[0]]);
        /* a wrap in "around the peak" never happens (+-15 < t_r / 2); in
           "full period" bins are contiguous */
        if (n === 0 || (prev !== null && e[1] - prev > DT * 1.5)) ctx.moveTo(xa, y);
        else ctx.lineTo(xa, y);
        ctx.lineTo(xb, y);
        prev = e[1];
      });
      ctx.stroke();
    }
    line("poisson", C.red, 1.6);
    line("mars", C.green, 2.6);
    /* the true delay */
    ctx.setLineDash([4, 3]); ctx.strokeStyle = C.delay; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(Math.round(X(0)) + 0.5, T); ctx.lineTo(Math.round(X(0)) + 0.5, T + ph);
    ctx.stroke(); ctx.setLineDash([]);
    /* the cursor */
    if (cursorIn) {
      ctx.strokeStyle = C.aged; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(X(trv), T); ctx.lineTo(X(trv), T + ph); ctx.stroke();
      ctx.fillStyle = C.gold; ctx.beginPath(); ctx.arc(X(trv), T + 4, 5, 0, 2 * Math.PI); ctx.fill();
    }
    geom = { x0: x0, x1: x1, L: L, pw: pw, t0: t0 };
  }

  function niceTop(v) {         /* a round top for 4 even gridlines */
    var raw = v * 1.08 / 4, p = Math.pow(10, Math.floor(Math.log10(raw)));
    var m = raw / p, s = m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10;
    return Math.max(4, Math.ceil(s * p) * 4);
  }

  /* ---------------- readout + state sync ---------------- */

  var roText = "", roTimer = null, roLast = 0, dragging = false;
  function readoutHTML() {
    var t0 = tau[st.i * W + st.j], off = {};
    KEYS.forEach(function (k) { off[k] = centre(hs[k], t0); });
    return '<span class="mars-slicer__ro-lead">Return centre vs. true delay:</span> ' +
      '<span class="is-poisson">Poisson <b>' + fmtNs(off.poisson) + '</b></span>' +
      ' <span class="sep" aria-hidden="true">·</span> ' +
      '<span class="is-gold">Gold standard <b>' + fmtNs(off.gold) + '</b></span>' +
      ' <span class="sep" aria-hidden="true">·</span> ' +
      '<span class="is-mars">MaRS <b>' + fmtNs(off.mars) + '</b></span>';
  }
  function plain(s) { return s.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim(); }
  function writeReadout(force) {
    var html = readoutHTML();
    /* compared as text, so the first write — the same values the HTML
       already ships — touches nothing and announces nothing */
    if (!roText) roText = plain(readout.textContent);
    if (plain(html) === roText) { clearTimeout(roTimer); return; }
    var now = Date.now();
    clearTimeout(roTimer);
    if (force || !dragging || now - roLast >= RO_THROTTLE) {
      roText = plain(html); roLast = now;
      readout.innerHTML = html;
    } else {
      roTimer = setTimeout(function () { writeReadout(true); }, RO_THROTTLE - (now - roLast));
    }
  }

  function syncControls() {
    chips.forEach(function (c) {
      c.setAttribute("aria-pressed", String(c.getAttribute("data-preset") === st.preset));
    });
    pools.forEach(function (b) { b.setAttribute("aria-pressed", String(+b.getAttribute("data-pool") === st.r)); });
    zooms.forEach(function (b) { b.setAttribute("aria-pressed", String(+b.getAttribute("data-zoom") === st.zoom)); });
    if (pnote) {
      var note = "";
      if (st.preset) meta.presets.forEach(function (q) { if (q.id === st.preset) note = q.note || ""; });
      if (pnote.textContent !== note) pnote.textContent = note;
    }
    var tt = binTime(st.t).toFixed(1) + " ns";
    range.value = String(st.t);
    range.setAttribute("aria-valuetext", tt.replace(" ", " "));
    if (tval) tval.textContent = tt;
  }

  var raf = 0, dirtyPx = false;
  function render(pixelChanged) {
    if (pixelChanged) dirtyPx = true;
    if (raf) return;
    raf = window.requestAnimationFrame(function () {
      raf = 0;
      if (dirtyPx || !hs) { recompute(); dirtyPx = false; }
      drawImages(); drawChart(); syncControls(); writeReadout(false);
    });
  }
  function renderNow() {           /* synchronous, for the first paint */
    recompute(); dirtyPx = false;
    drawImages(); drawChart(); syncControls(); writeReadout(true);
  }

  function setPixel(i, j) {
    i = Math.max(0, Math.min(H - 1, i)); j = Math.max(0, Math.min(W - 1, j));
    if (i === st.i && j === st.j) return;
    st.i = i; st.j = j; st.preset = null; render(true);
  }
  function setBin(b) {
    b = ((b % NB) + NB) % NB;
    if (b === st.t) return;
    st.t = b; st.preset = null; render(false);
  }
  function applyPreset(id) {
    var p = null;
    meta.presets.forEach(function (q) { if (q.id === id) p = q; });
    if (!p) return;
    st.i = p.px[0]; st.j = p.px[1]; st.t = p.bin; st.zoom = 1; st.preset = p.id;
    render(true);
  }

  /* ---------------- input ---------------- */

  function bind() {
    chips.forEach(function (c) {
      c.addEventListener("click", function () { applyPreset(c.getAttribute("data-preset")); });
    });
    pools.forEach(function (b) {
      b.addEventListener("click", function () { st.r = +b.getAttribute("data-pool"); render(true); });
    });
    zooms.forEach(function (b) {
      b.addEventListener("click", function () { st.zoom = +b.getAttribute("data-zoom"); render(false); });
    });
    range.addEventListener("input", function () { setBin(+range.value); });

    cvs.forEach(function (cv) {
      function at(e) {
        var r = cv.getBoundingClientRect();
        return [Math.floor((e.clientY - r.top) / r.height * H),
                Math.floor((e.clientX - r.left) / r.width * W)];
      }
      var tap = null, cap = null;
      cv.addEventListener("pointerdown", function (e) {
        if (e.button !== undefined && e.button !== 0) return;
        if (e.pointerType === "touch") { tap = { id: e.pointerId, x: e.clientX, y: e.clientY }; return; }
        cap = e.pointerId; dragging = true;
        try { cv.setPointerCapture(e.pointerId); } catch (err) { /* noop */ }
        var p = at(e); setPixel(p[0], p[1]);
        e.preventDefault(); cv.focus({ preventScroll: true });
      });
      cv.addEventListener("pointermove", function (e) {
        if (tap && tap.id === e.pointerId &&
            Math.abs(e.clientX - tap.x) + Math.abs(e.clientY - tap.y) > INTENT) tap = null;
        if (cap !== e.pointerId) return;
        var p = at(e); setPixel(p[0], p[1]);
      });
      function end(e) {
        if (tap && tap.id === e.pointerId) {
          if (e.type === "pointerup") { var p = at(e); setPixel(p[0], p[1]); }
          tap = null;
        }
        if (cap === e.pointerId) {
          cap = null; dragging = false;
          try { cv.releasePointerCapture(e.pointerId); } catch (err) { /* noop */ }
          writeReadout(true);
        }
      }
      cv.addEventListener("pointerup", end);
      cv.addEventListener("pointercancel", end);
      cv.addEventListener("keydown", function (e) {
        var m = { ArrowLeft: [0, -1], ArrowRight: [0, 1], ArrowUp: [-1, 0], ArrowDown: [1, 0] }[e.key];
        if (!m) return;
        e.preventDefault();
        var n = e.shiftKey ? 8 : 1;
        setPixel(st.i + m[0] * n, st.j + m[1] * n);
      });
    });

    /* chart: mouse/pen press-and-drag; touch only after a sideways drag */
    var cdrag = null, pending = null;
    function timeAt(e) {
      var r = chart.getBoundingClientRect(), g = geom;
      var v = g.x0 + (e.clientX - r.left - g.L) / g.pw * (g.x1 - g.x0);
      v = Math.max(g.x0, Math.min(g.x1, v));
      var tns = (((g.t0 + v) % TR) + TR) % TR;
      setBin(Math.floor(tns / DT));
    }
    function begin(e) {
      cdrag = e.pointerId; dragging = true;
      try { chart.setPointerCapture(e.pointerId); } catch (err) { /* noop */ }
      timeAt(e);
    }
    chart.addEventListener("pointerdown", function (e) {
      if (!geom || (e.button !== undefined && e.button !== 0)) return;
      if (e.pointerType === "touch") { pending = { id: e.pointerId, x: e.clientX, y: e.clientY }; return; }
      begin(e); e.preventDefault();
    });
    chart.addEventListener("pointermove", function (e) {
      if (pending && pending.id === e.pointerId) {
        var dx = Math.abs(e.clientX - pending.x), dy = Math.abs(e.clientY - pending.y);
        if (dx < INTENT || dx <= dy) return;
        pending = null; begin(e); return;
      }
      if (cdrag === e.pointerId) timeAt(e);
    });
    function cend(e) {
      if (pending && pending.id === e.pointerId) pending = null;
      if (cdrag !== e.pointerId) return;
      cdrag = null; dragging = false;
      try { chart.releasePointerCapture(e.pointerId); } catch (err) { /* noop */ }
    }
    chart.addEventListener("pointerup", cend);
    chart.addEventListener("pointercancel", cend);

    if ("ResizeObserver" in window) {
      new ResizeObserver(function () { if (hs) drawChart(); }).observe(chart);
    } else {
      window.addEventListener("resize", function () { if (hs) drawChart(); });
    }
  }

  /* ---------------- go ---------------- */

  var t0 = (window.performance && performance.now) ? performance.now() : 0;
  load().then(function () {
    var def = (meta.default && meta.default.preset) || "bright";
    var p = null;
    meta.presets.forEach(function (q) { if (q.id === def) p = q; });
    st.i = p.px[0]; st.j = p.px[1]; st.t = p.bin; st.zoom = 1; st.r = 1; st.preset = p.id;
    bind();
    /* the Time input, if it was moved before the module arrived */
    var userT = range.value !== range.defaultValue ? +range.value : null;
    var go = function () {
      renderNow();
      fig.setAttribute("data-slicer-state", "live");
      msg(null);
      fig._marsSlicerReadyMs = ((window.performance && performance.now) ? performance.now() : 0) - t0;
      /* a control pressed before the module arrived (js/mars-main.js kept it) */
      var pend = fig._marsSlicerPending;
      fig._marsSlicerPending = null;
      if (pend && fig.contains(pend) && pend.tagName === "BUTTON" &&
          !pend.classList.contains("mars-slicer__load")) pend.click();
      else if (userT !== null) setBin(userT);
    };
    /* draw with the page's own fonts, never a fallback that then swaps */
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(go, go);
    else go();
  }).catch(fail);
})();
