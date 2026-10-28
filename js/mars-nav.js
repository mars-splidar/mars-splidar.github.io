/* Sticky nav: hamburger toggle under 740px, a MEASURED mid-width tightening,
 * plus the button row rendered from window.MARS_CONFIG so that a null URL can
 * never become a dead link.
 *
 * THE NULL RULE (stage_01_foundation.md 3.2): a null URL never becomes a
 * link. Since v2.2-A it renders as plain text, "<Label> coming soon", after
 * the buttons (it was a non-clickable <span> pill with " · soon"). Plain text
 * rather than a styled <a href="#"> is deliberate — there is nothing to
 * click, nothing to focus, and nothing for tools/audit_claims.py's href="#"
 * grep to find.
 */
(function () {
  "use strict";

  var cfg = window.MARS_CONFIG || {};

  /* ---------------- hamburger ---------------- */

  function initNav() {
    var burger = document.querySelector(".mars-nav__burger");
    var links = document.getElementById("mars-nav-links");
    if (!burger || !links) return;

    /* Must match the hamburger breakpoint in css/mars.css. See the
       "NAV BREAKPOINTS" comment there for why it is 740px and not the
       guide's ~600px. */
    var mq = window.matchMedia("(max-width: 740px)");

    /* MEASURED MID-WIDTH TIGHTENING — stage 1.5.
       Stage 01 triggered the tightened nav from a fixed 741-919px media query,
       derived from a fixed list of eight anchors. The stub gate makes that
       list variable, so the trigger is now the actual fit: tighten only when
       the row genuinely overflows. Runs on load, on resize, and again once
       the webfonts land, because Poppins is wider than the fallback stack and
       the first measurement would otherwise be taken against the wrong font. */
    var nav = burger.closest(".mars-nav");
    var inner = nav ? nav.querySelector(".mars-nav__inner") : null;
    var pending = false;

    function fitNav() {
      pending = false;
      if (!nav || !inner) return;
      if (mq.matches) { nav.classList.remove("is-tight"); return; }
      nav.classList.remove("is-tight");
      if (inner.scrollWidth > inner.clientWidth + 1) {
        nav.classList.add("is-tight");
      }
    }

    function scheduleFit() {
      if (pending) return;
      pending = true;
      window.requestAnimationFrame(fitNav);
    }

    window.addEventListener("resize", scheduleFit);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(scheduleFit).catch(function () {});
    }

    function apply() {
      if (mq.matches) {
        links.hidden = true;
        burger.setAttribute("aria-expanded", "false");
      } else {
        links.hidden = false;                 // always visible on wide screens
        burger.setAttribute("aria-expanded", "false");
      }
      scheduleFit();
    }

    burger.addEventListener("click", function () {
      var open = links.hidden;
      links.hidden = !open;
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });

    // collapse after an in-page jump on mobile
    links.addEventListener("click", function (ev) {
      if (mq.matches && ev.target.closest("a")) {
        links.hidden = true;
        burger.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && mq.matches && !links.hidden) {
        links.hidden = true;
        burger.setAttribute("aria-expanded", "false");
        burger.focus();
      }
    });

    if (mq.addEventListener) mq.addEventListener("change", apply);
    else if (mq.addListener) mq.addListener(apply);
    apply();
  }

  /* ---------------- hero button row ---------------- */

  /* Each entry: label, the config key holding its URL, and how to behave when
   * that URL is present. `kind` "link" navigates, "anchor" is an in-page jump
   * that always exists.
   *
   * STAGE 07 (v2): `Video` is an "anchor" to the inline #video band
   * (guide 0.3). v1's "lightbox" kind went with its script in stage 09.
   *
   * STAGE v2.2-A ("Compact" hero, guide 0.7): smaller buttons, each with a
   * 16 px stroke icon drawn from ICONS below (aria-hidden, not focusable; the
   * label is the accessible name). THE NULL RULE, restated: a null URL
   * renders NOTHING clickable. It is no longer a dashed `· soon` pill but
   * plain grey text, "<Label> coming soon", in its own <li> AFTER the real
   * buttons, so the row reads as five buttons and a note. It is a text node
   * in an <li>: not a link, not a button, not focusable. When the URL is set,
   * the same entry renders as an ordinary button in its own slot. */
  var BUTTONS = [
    { label: "Paper",   key: "paperPdf",  kind: "link",   icon: "paper",
      newTab: true, primaryWhenReady: true },
    { label: "arXiv",   key: "arxivUrl",  kind: "link",   icon: "arxiv",
      newTab: true },
    { label: "Code",    key: "codeUrl",   kind: "link",   icon: "code",
      newTab: true },
    { label: "Video",   kind: "anchor", href: "#video",   icon: "video" },
    { label: "Poster",  key: "posterPdf", kind: "link",   icon: "poster",
      newTab: true },
    { label: "BibTeX",  kind: "anchor", href: "#bibtex",  icon: "bibtex" }
  ];

  /* 24 x 24 stroke paths (the approved mock's, hero_refinements.html "2 ·
     Compact"; Code is Tabler's outline "code", for the day codeUrl is set). */
  var ICONS = {
    paper:  ["M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z",
             "M14 3v6h6"],
    arxiv:  ["M5 19 12 5l7 14", "M8.5 13h7"],
    code:   ["M7 8l-4 4l4 4", "M17 8l4 4l-4 4", "M14 4l-4 16"],
    video:  ["M8 5v14l11-7z"],
    poster: ["M6 3h12a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z",
             "M4 15l5-5 4 4 3-3 4 4"],
    bibtex: ["M8 4c-2 0-2 2-2 4s-1 4-3 4c2 0 3 2 3 4s0 4 2 4",
             "M16 4c2 0 2 2 2 4s1 4 3 4c-2 0-3 2-3 4s0 4-2 4"]
  };
  var SVGNS = "http://www.w3.org/2000/svg";

  function icon(name) {
    var svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("class", "mars-btn__ico");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "16");
    svg.setAttribute("height", "16");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    (ICONS[name] || []).forEach(function (d) {
      var path = document.createElementNS(SVGNS, "path");
      path.setAttribute("d", d);
      svg.appendChild(path);
    });
    return svg;
  }

  function button(el, spec) {
    el.appendChild(icon(spec.icon));
    el.appendChild(document.createTextNode(spec.label));
    return el;
  }

  function buildButtons() {
    var host = document.getElementById("mars-hero-buttons");
    if (!host) return;
    host.textContent = "";
    var soon = [];

    BUTTONS.forEach(function (spec) {
      if (spec.kind === "anchor") {
        var a = document.createElement("a");
        a.className = "mars-btn is-outline";
        a.href = spec.href;
        var li0 = document.createElement("li");
        li0.appendChild(button(a, spec));
        host.appendChild(li0);
        return;
      }

      var url = cfg[spec.key];
      if (!url) { soon.push(spec.label); return; }   /* the null rule */
      var link = document.createElement("a");
      link.className = "mars-btn " +
        (spec.primaryWhenReady ? "is-primary" : "is-outline");
      link.href = url;
      if (spec.newTab) {
        link.target = "_blank";
        link.rel = "noopener";
      }
      var li = document.createElement("li");
      li.appendChild(button(link, spec));
      host.appendChild(li);
    });

    soon.forEach(function (label) {
      var li = document.createElement("li");
      li.className = "mars-hero__soon";
      li.textContent = label + " coming soon";
      host.appendChild(li);
    });
  }

  /* Secondary full-resolution links.
   *
   * Both the paper and the poster ship as a compressed web copy behind the
   * button plus an untouched original behind a link here, so nobody is
   * forced to pull 25 MB over conference wifi to read the paper and nobody
   * who wants the print-resolution file is denied it. A pair only appears
   * when BOTH of its copies exist, so a half-configured pair can never
   * become a dead link. Since v2.2-A the line sits in Go deeper
   * (#mars-originals), not under the hero buttons (guide 0.7). */
  function buildOriginals() {
    var note = document.getElementById("mars-originals");
    if (!note) return;

    var pairs = [
      { label: cfg.paperPdfFullLabel || "paper", url: cfg.paperPdfFull,
        web: cfg.paperPdf },
      { label: cfg.posterPdfFullLabel || "poster", url: cfg.posterPdfFull,
        web: cfg.posterPdf }
    ].filter(function (x) { return x.url && x.web; });

    if (!pairs.length) return;

    note.textContent = "";
    note.appendChild(document.createTextNode("Full-resolution originals: "));
    pairs.forEach(function (x, i) {
      if (i) note.appendChild(document.createTextNode(" \u00b7 "));
      var full = document.createElement("a");
      full.href = x.url;
      full.target = "_blank";
      full.rel = "noopener";
      full.textContent = x.label;
      note.appendChild(full);
    });
    note.hidden = false;
  }

  /* Fill the closing band's "Read the paper / Contact the authors" line and
   * the demo-lab URLs from the same config, for the same reason. */
  function buildClosingLinks() {
    var paper = document.getElementById("mars-closing-paper");
    if (paper) {
      if (cfg.paperPdf) {
        var a = document.createElement("a");
        a.href = cfg.paperPdf;
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = "Read the paper";
        paper.replaceWith(a);
      } else {
        paper.textContent = "Paper · soon";
      }
    }
    var contact = document.getElementById("mars-closing-contact");
    if (contact && cfg.contactEmail) {
      contact.href = "mailto:" + cfg.contactEmail;
    }
  }

  /* Any in-page link whose destination lives in MARS_CONFIG carries
   * data-mars-config-href="<key>" alongside a real fallback href. Stage 02's
   * `Try the demo lab` card link is the first user. The fallback is what the
   * null rule needs: an unset key leaves the hand-written href alone rather
   * than blanking it, so the link is never dead. */
  function applyConfigHrefs() {
    var nodes = document.querySelectorAll("[data-mars-config-href]");
    for (var i = 0; i < nodes.length; i++) {
      var key = nodes[i].getAttribute("data-mars-config-href");
      if (key && cfg[key]) nodes[i].setAttribute("href", cfg[key]);
    }
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    initNav();
    buildButtons();
    buildOriginals();
    buildClosingLinks();
    applyConfigHrefs();
  });
})();
