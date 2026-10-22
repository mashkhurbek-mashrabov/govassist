/**
 * GovAssist prototype: journey navigation and timed streaming playback (j1.html … j6.html).
 * Prototype only; the React app does not use this file.
 *
 * Markup it understands:
 *   <section class="flow-step" id="x" data-title="…" [data-auto="ms"]>  one step; the URL hash picks the step
 *   href="#step-id" or data-go="step-id"                                 go to a step
 *   <form data-go="step-id">                                              submit shows a short busy state, then goes
 *   [data-type]                                                           text that types itself out during an auto step
 *   [data-drawer="open|close"]                                            phone history drawer
 *   [data-flow-prev|next|pause|pos]                                       the journey bar
 * URL flags: ?shot  freezes the page for screenshots (no timers, no typing, no busy delay).
 * Reduced motion: steps still advance on their timer, but text appears at once (the stages jump).
 */
(function () {
  "use strict";

  var SUBMIT_DELAY_MS = 700;
  var TYPE_SHARE = 0.8; // typing uses 80 % of an auto step, so the full text shows before it advances
  var MIN_CHAR_MS = 16;

  var steps = Array.prototype.slice.call(document.querySelectorAll(".flow-step"));
  if (!steps.length) return;

  var shot = new URLSearchParams(location.search).has("shot");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var paused = false;
  var timers = [];

  var pos = document.querySelector("[data-flow-pos]");
  var prevBtn = document.querySelector("[data-flow-prev]");
  var nextBtn = document.querySelector("[data-flow-next]");
  var pauseBtn = document.querySelector("[data-flow-pause]");

  /** @param {string} id @returns {HTMLElement|undefined} the step with this id */
  function stepById(id) {
    return steps.filter(function (s) { return s.id === id; })[0];
  }

  /** @returns {HTMLElement} the step named by the URL hash, else the first */
  function currentStep() {
    return stepById(decodeURIComponent(location.hash.slice(1))) || steps[0];
  }

  /** Cancels pending auto-advance and typing timers. */
  function clearTimers() {
    timers.forEach(function (t) { clearTimeout(t); clearInterval(t); });
    timers = [];
  }

  /** @param {string} id Navigates to a step (no-op for unknown ids). */
  function go(id) {
    if (stepById(id)) location.hash = id;
  }

  /** @param {number} delta Moves relative to the current step. */
  function move(delta) {
    var next = steps[steps.indexOf(currentStep()) + delta];
    if (next) go(next.id);
  }

  /**
   * Types an element's text out over `ms`; shows it at once in shot or reduced-motion mode.
   * @param {HTMLElement} el
   * @param {number} ms
   */
  function typeOut(el, ms) {
    var full = el.getAttribute("data-full") || el.textContent;
    el.setAttribute("data-full", full);
    if (shot || reduced || paused) { el.textContent = full; return; }
    var shown = 0;
    el.textContent = "";
    var t = setInterval(function () {
      shown += 1;
      el.textContent = full.slice(0, shown);
      if (shown >= full.length) clearInterval(t);
    }, Math.max(MIN_CHAR_MS, ms / full.length));
    timers.push(t);
  }

  /** Starts the auto-advance timer for a step that has data-auto. @param {HTMLElement} step */
  function scheduleAuto(step) {
    var ms = Number(step.getAttribute("data-auto") || 0);
    if (!ms || shot || paused) return;
    timers.push(setTimeout(function () { move(1); }, ms));
  }

  /** Shows one step, updates the bar, moves focus and starts playback. @param {HTMLElement} step */
  function show(step) {
    clearTimers();
    steps.forEach(function (s) { s.hidden = s !== step; });
    document.body.classList.remove("drawer-open");
    var i = steps.indexOf(step);
    if (pos) pos.textContent = "Step " + (i + 1) + " of " + steps.length + ": " + step.getAttribute("data-title");
    if (prevBtn) prevBtn.disabled = i === 0;
    if (nextBtn) nextBtn.disabled = i === steps.length - 1;
    var anchor = step.querySelector("[data-flow-scroll]");
    if (anchor && !shot) anchor.scrollIntoView({ block: "start" }); else window.scrollTo(0, 0);
    var heading = step.querySelector("h1, h2");
    if (heading && !shot) { heading.setAttribute("tabindex", "-1"); heading.focus({ preventScroll: true }); }
    var auto = Number(step.getAttribute("data-auto") || 0);
    step.querySelectorAll("[data-type]").forEach(function (el) { typeOut(el, (auto || 1500) * TYPE_SHARE); });
    scheduleAuto(step);
  }

  /** Highlights an in-step anchor target (citation badge → source) without changing the step. @param {string} id */
  function highlight(id) {
    var target = currentStep().querySelector("#" + CSS.escape(id));
    if (!target) return;
    if (!target.classList.contains("source")) {
      target.setAttribute("tabindex", "-1");
      target.focus();
      return;
    }
    currentStep().querySelectorAll(".is-highlighted").forEach(function (el) { el.classList.remove("is-highlighted"); });
    target.classList.add("is-highlighted");
    target.scrollIntoView({ block: "center" });
  }

  /** Shows a short busy state on the submit button, then goes to the form's target. @param {HTMLFormElement} form */
  function submit(form) {
    var button = form.querySelector("[type=submit]");
    var target = form.getAttribute("data-go");
    if (!button || shot || reduced) { go(target); return; }
    var label = button.innerHTML;
    button.setAttribute("aria-busy", "true");
    button.disabled = true;
    button.innerHTML = '<span class="spinner" aria-hidden="true"></span>' + label.replace(/<svg[\s\S]*?<\/svg>/, "");
    timers.push(setTimeout(function () {
      button.innerHTML = label;
      button.disabled = false;
      button.removeAttribute("aria-busy");
      go(target);
    }, SUBMIT_DELAY_MS));
  }

  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-flow-prev], [data-flow-next], [data-flow-pause], [data-drawer], [data-go], a[href^='#']");
    if (!el || el.closest("form[data-go]") && el.type === "submit") return;
    if (el.hasAttribute("data-flow-prev")) { move(-1); return; }
    if (el.hasAttribute("data-flow-next")) { move(1); return; }
    if (el.hasAttribute("data-flow-pause")) {
      paused = !paused;
      el.setAttribute("aria-pressed", String(paused));
      el.textContent = paused ? "Play" : "Pause";
      if (paused) clearTimers(); else scheduleAuto(currentStep());
      return;
    }
    if (el.hasAttribute("data-drawer")) {
      e.preventDefault();
      document.body.classList.toggle("drawer-open", el.getAttribute("data-drawer") === "open");
      return;
    }
    if (el.hasAttribute("data-go")) {
      if (el.target !== "_blank") e.preventDefault();
      go(el.getAttribute("data-go"));
      return;
    }
    var id = el.getAttribute("href").slice(1);
    if (!stepById(id)) { e.preventDefault(); highlight(id); }
  });

  document.addEventListener("submit", function (e) {
    var form = e.target.closest("form");
    e.preventDefault();
    if (form && form.hasAttribute("data-go")) submit(form);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") document.body.classList.remove("drawer-open");
  });

  window.addEventListener("hashchange", function () { show(currentStep()); });
  show(currentStep());
})();
