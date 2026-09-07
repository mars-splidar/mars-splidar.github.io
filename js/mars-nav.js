/* Sticky nav: hamburger toggle under 600px, plus the button row rendered from
 * window.MARS_CONFIG so that a null URL can never become a dead link.
 *
 * THE NULL RULE (stage_01_foundation.md 3.2): a null URL renders as a
 * NON-CLICKABLE <span> pill with " · soon" appended. Rendering a <span> rather
 * than a styled <a href="#"> is deliberate — there is nothing to click, nothing
 * to focus, and nothing for tools/audit_claims.py's href="#" grep to find.
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

    function apply() {
      if (mq.matches) {
        links.hidden = true;
        burger.setAttribute("aria-expanded", "false");
      } else {
        links.hidden = false;                 // always visible on wide screens
        burger.setAttribute("aria-expanded", "false");
      }
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
   * that URL is present. `kind` "link" navigates, "lightbox" defers to
   * mars-lightbox.js, "anchor" is an in-page jump that always exists. */
  var BUTTONS = [
    { label: "Paper",   key: "paperPdf",  kind: "link",     newTab: true,
      primaryWhenReady: true },
    { label: "arXiv",   key: "arxivUrl",  kind: "link",     newTab: true },
    { label: "Code",    key: "codeUrl",   kind: "link",     newTab: true },
    { label: "Video",   key: "videoSelfUrl", kind: "lightbox" },
    { label: "Poster",  key: "posterPdf", kind: "link",     newTab: true },
    { label: "BibTeX ↓", kind: "anchor", href: "#bibtex" }
  ];

  function soonPill(label) {
    var span = document.createElement("span");
    span.className = "mars-btn is-soon";
    span.setAttribute("aria-disabled", "true");
    span.appendChild(document.createTextNode(label + " "));
    var s = document.createElement("span");
    s.className = "mars-btn__soon";
    s.textContent = "· soon";
    span.appendChild(s);
    return span;
  }

  function videoAvailable() {
    if (cfg.videoMode === "youtube") return !!cfg.videoYoutubeId;
    return !!cfg.videoSelfUrl;
  }

  function buildButtons() {
    var host = document.getElementById("mars-hero-buttons");
    if (!host) return;
    host.textContent = "";

    BUTTONS.forEach(function (spec) {
      var li = document.createElement("li");

      if (spec.kind === "anchor") {
        var a = document.createElement("a");
        a.className = "mars-btn is-outline";
        a.href = spec.href;
        a.textContent = spec.label;
        li.appendChild(a);
        host.appendChild(li);
        return;
      }

      if (spec.kind === "lightbox") {
        if (!videoAvailable()) {
          li.appendChild(soonPill(spec.label));
        } else {
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "mars-btn is-outline";
          btn.setAttribute("data-mars-lightbox", "video");
          btn.textContent = spec.label;
          li.appendChild(btn);
        }
        host.appendChild(li);
        return;
      }

      var url = cfg[spec.key];
      if (!url) {
        li.appendChild(soonPill(spec.label));
      } else {
        var link = document.createElement("a");
        link.className = "mars-btn " +
          (spec.primaryWhenReady ? "is-primary" : "is-outline");
        link.href = url;
        if (spec.newTab) {
          link.target = "_blank";
          link.rel = "noopener";
        }
        link.textContent = spec.label;
        li.appendChild(link);
      }
      host.appendChild(li);
    });

    /* Secondary full-resolution poster link, only when both copies exist. */
    var note = document.getElementById("mars-hero-note");
    if (note && cfg.posterPdf && cfg.posterPdfFull) {
      note.textContent = "";
      note.appendChild(document.createTextNode("Poster also available at "));
      var full = document.createElement("a");
      full.href = cfg.posterPdfFull;
      full.target = "_blank";
      full.rel = "noopener";
      full.textContent = cfg.posterPdfFullLabel || "full resolution";
      note.appendChild(full);
      note.appendChild(document.createTextNode("."));
      note.hidden = false;
    }
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

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    initNav();
    buildButtons();
    buildClosingLinks();
  });
})();
