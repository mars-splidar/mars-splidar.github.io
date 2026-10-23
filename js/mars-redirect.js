/* Old in-page anchors -> /details/ — stage 07 (v2, guide 0.2).
 *
 * v1 carried seven technical bands on the main page. v2 moved them, verbatim,
 * to /details/. Links and bookmarks to /#theory, /#simulator and the rest are
 * in the paper's abstract, on the poster's QR landing, in slides and in
 * people's history, so each of the seven ids sends the reader to the same
 * band on /details/. Any other hash — #results, #video, #bibtex, an unknown
 * one, or none — stays on this page untouched.
 *
 * Loaded FIRST in <head>, before the stylesheets, so the redirect happens
 * before the main page paints. No dependencies; location.replace() so the
 * dead URL does not linger in the back-button history. Also listens for
 * `hashchange`, which covers an old link followed while already on `/`.
 */
(function () {
  "use strict";

  var MOVED = ["motivation", "approach", "contributions", "theory",
               "simulator", "utility", "limitations"];

  function check() {
    var id = location.hash.slice(1);
    try { id = decodeURIComponent(id); } catch (e) { /* keep it raw */ }
    if (MOVED.indexOf(id) !== -1) {
      location.replace("details/#" + encodeURIComponent(id));
    }
  }

  check();
  window.addEventListener("hashchange", check);
})();
