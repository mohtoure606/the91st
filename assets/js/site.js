/* The 91st Foundation — site behaviour (no dependencies) */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.remove("no-js");

  /* ---------- Mobile menu ---------- */
  var toggle = document.querySelector(".menu-toggle");
  var menu = document.getElementById("mobile-menu");
  function setMenu(open) {
    document.body.classList.toggle("menu-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.querySelector(".label").textContent = open ? "Close" : "Menu";
    if (open) { var first = menu.querySelector("a"); if (first) first.focus(); }
  }
  if (toggle && menu) {
    toggle.addEventListener("click", function () { setMenu(!document.body.classList.contains("menu-open")); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && document.body.classList.contains("menu-open")) { setMenu(false); toggle.focus(); }
    });
    menu.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    window.addEventListener("resize", function () { if (window.innerWidth >= 1120) setMenu(false); });
  }

  /* ---------- Reveal on scroll ---------- */
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- YouTube click-to-load (privacy-enhanced, faster pages) ---------- */
  document.querySelectorAll(".yt[data-id]").forEach(function (btn) {
    var id = btn.getAttribute("data-id");
    btn.style.backgroundImage = "url('https://i.ytimg.com/vi/" + id + "/hqdefault.jpg')";
    btn.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1&rel=0";
      f.title = btn.getAttribute("aria-label") || "Video";
      f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      f.allowFullscreen = true;
      var wrap = document.createElement("div");
      wrap.className = "yt";
      wrap.appendChild(f);
      btn.replaceWith(wrap);
    });
  });

  /* ---------- Pre-select a role on the Get Involved form (?role=mentor) ---------- */
  var params = new URLSearchParams(window.location.search);
  var role = params.get("role");
  if (role) {
    var sel = document.querySelector('select[name="role"]');
    if (sel) {
      Array.prototype.forEach.call(sel.options, function (o) { if (o.value === role || o.getAttribute("data-key") === role) sel.value = o.value; });
    }
  }
  var orgType = params.get("type");
  if (orgType) {
    var ot = document.querySelector('select[name="organization_type"]');
    if (ot) Array.prototype.forEach.call(ot.options, function (o) { if (o.value === orgType || o.getAttribute("data-key") === orgType) ot.value = o.value; });
  }

  /* ---------- Forms (Formspree) ---------- */
  var MESSAGES = {
    valueMissing: "This field is required.",
    typeMismatchEmail: "Enter a valid email address, like name@example.com.",
    typeMismatchUrl: "Enter a full web address, like https://example.org.",
    tooShort: "Please add a little more detail."
  };

  function fieldOf(el) { return el.closest(".field"); }
  function messageFor(el) {
    var v = el.validity;
    if (v.valueMissing) return el.getAttribute("data-msg") || MESSAGES.valueMissing;
    if (v.typeMismatch && el.type === "email") return MESSAGES.typeMismatchEmail;
    if (v.typeMismatch && el.type === "url") return MESSAGES.typeMismatchUrl;
    if (v.tooShort) return MESSAGES.tooShort;
    return el.validationMessage;
  }
  function showError(el) {
    var f = fieldOf(el); if (!f) return;
    var err = f.querySelector(".err");
    f.classList.add("invalid");
    el.setAttribute("aria-invalid", "true");
    if (err) err.textContent = messageFor(el);
  }
  function clearError(el) {
    var f = fieldOf(el); if (!f) return;
    f.classList.remove("invalid");
    el.removeAttribute("aria-invalid");
  }
  function normaliseUrl(el) {
    if (el.type === "url" && el.value && !/^https?:\/\//i.test(el.value.trim())) {
      el.value = "https://" + el.value.trim();
    }
  }

  document.querySelectorAll("form[data-form]").forEach(function (form) {
    form.setAttribute("novalidate", "");
    var controls = form.querySelectorAll("input:not([type=hidden]):not(.hp input), select, textarea");
    controls.forEach(function (el) {
      el.addEventListener("blur", function () { normaliseUrl(el); if (el.value) { el.checkValidity() ? clearError(el) : showError(el); } });
      el.addEventListener("input", function () { if (fieldOf(el) && fieldOf(el).classList.contains("invalid") && el.checkValidity()) clearError(el); });
      el.addEventListener("change", function () { if (el.checkValidity()) clearError(el); });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var status = form.querySelector(".form-status");
      if (status) { status.className = "form-status"; status.textContent = ""; }

      var firstBad = null;
      controls.forEach(function (el) {
        normaliseUrl(el);
        if (!el.checkValidity()) { showError(el); if (!firstBad) firstBad = el; } else { clearError(el); }
      });
      // checkbox groups with data-required-group
      form.querySelectorAll("[data-required-group]").forEach(function (group) {
        var ok = group.querySelector("input:checked");
        var f = group.closest(".field");
        if (!ok) { f.classList.add("invalid"); f.querySelector(".err").textContent = "Choose at least one option."; if (!firstBad) firstBad = group.querySelector("input"); }
        else f.classList.remove("invalid");
      });
      if (firstBad) { firstBad.focus(); return; }

      var btn = form.querySelector("button[type=submit]");
      var label = btn ? btn.innerHTML : "";
      if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }

      fetch(form.action, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } })
        .then(function (res) {
          if (res.ok) return { ok: true };
          return res.json().then(function (d) { return { ok: false, data: d }; }, function () { return { ok: false }; });
        })
        .then(function (r) {
          if (r.ok) {
            var success = document.getElementById(form.getAttribute("data-success"));
            form.hidden = true;
            if (success) { success.classList.add("show"); success.setAttribute("tabindex", "-1"); success.focus(); }
            form.reset();
          } else {
            var msg = "Something went wrong and your message was not sent.";
            if (r.data && r.data.errors && r.data.errors.length) msg += " (" + r.data.errors.map(function (x) { return x.message; }).join(" ") + ")";
            fail(msg);
          }
        })
        .catch(function () { fail("We couldn't reach our form service. Check your connection and try again."); });

      function fail(msg) {
        if (btn) { btn.disabled = false; btn.innerHTML = label; }
        if (status) {
          status.className = "form-status error show";
          status.innerHTML = msg + ' You can also email us directly at <a href="mailto:team@the91st.org">team@the91st.org</a>.';
          status.setAttribute("role", "alert");
        }
      }
    });
  });

  /* ---------- Year ---------- */
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
