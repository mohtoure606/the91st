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


  /* ---------- 3D tilt (pointer devices only) ---------- */
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  if (!reduce && finePointer) {
    document.querySelectorAll(".tilt").forEach(function (el) {
      var max = parseFloat(el.getAttribute("data-tilt-max")) || 9;
      var raf = 0;
      el.addEventListener("pointermove", function (e) {
        var r = el.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(function () {
          el.classList.add("is-tilting");
          el.style.setProperty("--ry", ((x - 0.5) * 2 * max).toFixed(2) + "deg");
          el.style.setProperty("--rx", ((0.5 - y) * 2 * max).toFixed(2) + "deg");
          el.style.setProperty("--gx", (x * 100).toFixed(1) + "%");
          el.style.setProperty("--gy", (y * 100).toFixed(1) + "%");
        });
      });
      el.addEventListener("pointerleave", function () {
        cancelAnimationFrame(raf);
        el.classList.remove("is-tilting");
        el.style.setProperty("--rx", "0deg");
        el.style.setProperty("--ry", "0deg");
      });
    });
  }

  /* ---------- Player rail arrows ---------- */
  document.querySelectorAll(".rail-wrap").forEach(function (wrap) {
    var rail = wrap.querySelector(".rail");
    var btns = wrap.querySelectorAll(".rail-btn");
    function update() {
      var max = rail.scrollWidth - rail.clientWidth - 2;
      btns[0].disabled = rail.scrollLeft <= 2;
      btns[1].disabled = rail.scrollLeft >= max;
    }
    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        var card = rail.firstElementChild;
        var step = card ? card.getBoundingClientRect().width + 20 : 320;
        rail.scrollBy({ left: step * parseInt(b.getAttribute("data-dir"), 10), behavior: reduce ? "auto" : "smooth" });
      });
    });
    rail.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  });

  /* ---------- Roster filters ---------- */
  var filterBtns = document.querySelectorAll(".filter");
  if (filterBtns.length) {
    var cards = document.querySelectorAll(".roster .pcard");
    var countEl = document.querySelector("[data-count]");
    filterBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var f = btn.getAttribute("data-filter"), n = 0;
        filterBtns.forEach(function (b) { var on = b === btn; b.classList.toggle("is-on", on); b.setAttribute("aria-pressed", String(on)); });
        cards.forEach(function (c) {
          var show = f === "all" || (" " + c.getAttribute("data-level") + " ").indexOf(f) > -1;
          c.hidden = !show;
          if (show) { n++; c.classList.remove("pop"); void c.offsetWidth; c.classList.add("pop"); }
        });
        if (countEl) countEl.textContent = n;
      });
    });
  }

  /* ---------- Profile tab bar: highlight current section ---------- */
  var tabLinks = document.querySelectorAll(".tabbar a");
  if (tabLinks.length && "IntersectionObserver" in window) {
    var map = {};
    tabLinks.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          tabLinks.forEach(function (a) { a.classList.remove("is-active"); a.removeAttribute("aria-current"); });
          var a = map[en.target.id];
          if (a) { a.classList.add("is-active"); a.setAttribute("aria-current", "true"); a.scrollIntoView({ block: "nearest", inline: "nearest" }); }
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    Object.keys(map).forEach(function (id) { var s = document.getElementById(id); if (s) spy.observe(s); });
  }

  /* ---------- Count-up numbers ---------- */
  var counters = document.querySelectorAll("[data-count-to]");
  if (counters.length && "IntersectionObserver" in window && !reduce) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        cio.unobserve(en.target);
        var el = en.target, txt = el.getAttribute("data-count-to");
        var m = txt.match(/^(\D*)([\d,]+)(.*)$/);
        if (!m) return;
        var target = parseInt(m[2].replace(/,/g, ""), 10), comma = m[2].indexOf(",") > -1, t0 = performance.now();
        (function tick(now) {
          var p = Math.min((now - t0) / 1200, 1), v = Math.round(target * (1 - Math.pow(1 - p, 3)));
          el.textContent = m[1] + (comma ? v.toLocaleString("en-US") : v) + m[3];
          if (p < 1) requestAnimationFrame(tick);
        })(t0);
      });
    }, { threshold: 0.6 });
    counters.forEach(function (c) { cio.observe(c); });
  }

  /* ---------- Share / print ---------- */
  document.querySelectorAll("[data-print]").forEach(function (b) { b.addEventListener("click", function () { window.print(); }); });
  document.querySelectorAll("[data-share]").forEach(function (b) {
    b.addEventListener("click", function () {
      var data = { title: document.title, url: location.href.split("#")[0] };
      if (navigator.share) { navigator.share(data).catch(function () {}); return; }
      if (navigator.clipboard) {
        navigator.clipboard.writeText(data.url).then(function () {
          var old = b.textContent; b.textContent = "Link copied"; setTimeout(function () { b.textContent = old; }, 2000);
        });
      }
    });
  });

  /* ---------- Pre-fill player of interest (?player=Name) ---------- */
  var player = params.get("player");
  var pf = document.querySelector('input[name="player_of_interest"]');
  if (player && pf) pf.value = player;

  /* ---------- Year ---------- */
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
