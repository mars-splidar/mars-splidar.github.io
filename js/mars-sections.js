/* The stub gate — stage 1.5.
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * Stage 01 shipped six content bands as shells for stage 02 to fill. Pushing
 * them to production unchanged would show six headings with nothing under
 * them, which reads as broken rather than pending. This module renders only
 * the sections listed in `MARS_CONFIG.sectionsLive` and removes the rest —
 * band AND nav anchor together, so there is never a heading floating above
 * nothing and never a nav link that scrolls nowhere.
 *
 * TO TURN A SECTION ON: write its content, then add its id to `sectionsLive`
 * in js/site.config.js. That is the whole procedure.
 *
 * WHY IT LOADS IN <head> AND NOT WITH THE OTHER SCRIPTS
 * ----------------------------------------------------
 * The other modules run at DOMContentLoaded, which is too late here: the
 * gated bands would paint and then vanish. So this file does its work in two
 * passes.
 *
 *   Pass 1, at parse time, in <head>: inject a <style> that hides exactly the
 *   gated ids. It names only the NOT-live ids, so a live section is never
 *   hidden even for a frame, and a visitor with JavaScript disabled still
 *   sees every finished section. That is why site.config.js carries the full
 *   `sections` registry as well as `sectionsLive` — the DOM does not exist
 *   yet at this point, so the list cannot be discovered from it.
 *
 *   Pass 2, at DOMContentLoaded: actually remove the gated elements from the
 *   DOM, so nothing gated is reachable by screen readers, by tab order, or by
 *   in-page anchors.
 *
 * The markup contract is one attribute: `data-mars-section="<id>"`, present
 * on the <section> band and on its nav <li>. Both are removed together.
 */
(function () {
  "use strict";

  var cfg = window.MARS_CONFIG || {};
  var all = cfg.sections || [];
  var live = cfg.sectionsLive || [];

  function isLive(id) { return live.indexOf(id) !== -1; }

  var gated = all.filter(function (id) { return !isLive(id); });

  /* ---- pass 1: hide gated ids before they can paint ---- */
  if (gated.length) {
    var sel = gated.map(function (id) {
      return '[data-mars-section="' + id + '"]';
    }).join(",");
    var style = document.createElement("style");
    style.setAttribute("data-mars-section-gate", "");
    style.textContent = sel + "{display:none !important}";
    (document.head || document.documentElement).appendChild(style);
  }

  /* ---- pass 2: remove them outright ---- */
  function prune() {
    var removed = [];
    var nodes = document.querySelectorAll("[data-mars-section]");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var id = el.getAttribute("data-mars-section");
      if (isLive(id)) {
        /* Live: drop the attribute so no stale gate style can ever match it. */
        el.removeAttribute("data-mars-section");
      } else {
        removed.push(id);
        el.parentNode.removeChild(el);
      }
    }
    /* Any section id NOT in the registry at all is a wiring mistake — a band
       that will never be gate-able. Say so rather than failing silently. */
    var orphan = document.querySelectorAll(
      "section.mars-band[id]:not([data-mars-section])");
    for (var j = 0; j < orphan.length; j++) {
      var oid = orphan[j].id;
      if (all.indexOf(oid) !== -1 && !isLive(oid) && removed.indexOf(oid) === -1
          && window.console) {
        console.warn("mars-sections: #" + oid + " is in MARS_CONFIG.sections "
                     + "but its <section> carries no data-mars-section "
                     + "attribute, so it cannot be gated.");
      }
    }
  }

  if (document.readyState !== "loading") prune();
  else document.addEventListener("DOMContentLoaded", prune);
})();
