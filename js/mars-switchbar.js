/* The switch-bar pattern — the site's signature interaction.
 *
 * Markup contract: WEBSITE_BUILD_STATUS.md section 3.4. One initialiser binds
 * EVERY [data-switch] on the page; a switch bar named `foo` drives the panel
 * group `[data-panels="foo"]`, and each pill's `data-target` is the id of the
 * panel it shows.
 *
 * Panels are toggled with the `hidden` attribute plus the `is-active` class —
 * NEVER style.display. Stage 02 relies on that: `hidden` is what keeps an
 * inactive panel out of the accessibility tree and out of find-in-page.
 *
 * Keyboard: arrow keys move between pills (roving tabindex, the standard
 * tablist pattern), Home/End jump to the ends.
 */
(function () {
  "use strict";

  function activate(bar, panels, pill) {
    var pills = Array.prototype.slice.call(
      bar.querySelectorAll(".mars-switch__pill"));

    pills.forEach(function (p) {
      var on = p === pill;
      p.classList.toggle("is-active", on);
      p.setAttribute("aria-selected", on ? "true" : "false");
      p.tabIndex = on ? 0 : -1;
    });

    if (!panels) return;
    var targets = Array.prototype.slice.call(
      panels.querySelectorAll(".mars-panel"));
    var wanted = pill.getAttribute("data-target");

    targets.forEach(function (panel) {
      var on = panel.id === wanted;
      panel.classList.toggle("is-active", on);
      panel.hidden = !on;
    });
  }

  function initOne(bar) {
    var name = bar.getAttribute("data-switch");
    var panels = name
      ? document.querySelector('[data-panels="' + name + '"]')
      : null;
    var pills = Array.prototype.slice.call(
      bar.querySelectorAll(".mars-switch__pill"));
    if (!pills.length) return;

    pills.forEach(function (pill, i) {
      if (!pill.hasAttribute("role")) pill.setAttribute("role", "tab");
      pill.tabIndex = pill.classList.contains("is-active") ? 0 : -1;

      pill.addEventListener("click", function () {
        activate(bar, panels, pill);
      });

      pill.addEventListener("keydown", function (ev) {
        var next = null;
        if (ev.key === "ArrowRight" || ev.key === "ArrowDown") {
          next = pills[(i + 1) % pills.length];
        } else if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") {
          next = pills[(i - 1 + pills.length) % pills.length];
        } else if (ev.key === "Home") {
          next = pills[0];
        } else if (ev.key === "End") {
          next = pills[pills.length - 1];
        }
        if (!next) return;
        ev.preventDefault();
        activate(bar, panels, next);
        next.focus();
      });
    });

    /* Normalise the initial state from whichever pill the markup marked
       active, so a hand-written page and a JS-driven one agree. */
    var initial = bar.querySelector(".mars-switch__pill.is-active") || pills[0];
    activate(bar, panels, initial);
  }

  function initSwitchBars(root) {
    var scope = root || document;
    Array.prototype.slice
      .call(scope.querySelectorAll("[data-switch]"))
      .forEach(initOne);
  }

  /* Exposed so a later stage can re-bind after injecting markup. */
  window.marsInitSwitchBars = initSwitchBars;

  if (document.readyState !== "loading") initSwitchBars();
  else document.addEventListener("DOMContentLoaded", function () {
    initSwitchBars();
  });
})();
