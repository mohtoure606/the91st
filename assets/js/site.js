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
      if (firstBad) { var dt = firstBad.closest("details"); if (dt) dt.open = true; firstBad.focus(); return; }

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
      wrap.classList.toggle("no-overflow", max <= 2);
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


  /* ---------- Tabs (profile sections, partner types) ---------- */
  function setupTabs(tablist, onSelect) {
    var tabs = Array.prototype.slice.call(tablist.querySelectorAll('[role="tab"]'));
    function select(tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) panel.hidden = !on;
      });
      if (focus) tab.focus();
      if (onSelect) onSelect(tab);
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(t, false); });
      t.addEventListener("keydown", function (e) {
        var n = null;
        if (e.key === "ArrowRight") n = tabs[(i + 1) % tabs.length];
        if (e.key === "ArrowLeft") n = tabs[(i - 1 + tabs.length) % tabs.length];
        if (e.key === "Home") n = tabs[0];
        if (e.key === "End") n = tabs[tabs.length - 1];
        if (n) { e.preventDefault(); select(n, true); }
      });
    });
    return { select: select, byPanel: function (id) { return tabs.filter(function (t) { return t.getAttribute("aria-controls") === id; })[0]; } };
  }
  var profileTabs = document.querySelector("[data-tabs] [role=tablist]");
  if (profileTabs) {
    var bar = document.querySelector("[data-tabs]");
    var pt = setupTabs(profileTabs, function () {
      var top = bar.getBoundingClientRect().top + window.scrollY - 72;
      if (window.scrollY > top) window.scrollTo({ top: top, behavior: reduce ? "auto" : "smooth" });
    });
    function openFromHash() {
      var t = pt.byPanel(location.hash.slice(1));
      if (t) { pt.select(t, false); bar.scrollIntoView({ behavior: reduce ? "auto" : "smooth" }); }
    }
    document.querySelectorAll("[data-open-tab]").forEach(function (a) {
      a.addEventListener("click", function (e) {
        var t = pt.byPanel(a.getAttribute("data-open-tab"));
        if (t) { e.preventDefault(); pt.select(t, false); bar.scrollIntoView({ behavior: reduce ? "auto" : "smooth" }); }
      });
    });
    if (location.hash) openFromHash();
    window.addEventListener("hashchange", openFromHash);
  }
  document.querySelectorAll("[data-ptabs]").forEach(function (list) { setupTabs(list); });

  /* ---------- Resource category filter ---------- */
  var catBtns = document.querySelectorAll(".cat[data-cat]");
  if (catBtns.length) {
    var cats = document.querySelectorAll(".dir-cat");
    catBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        var on = b.getAttribute("aria-pressed") !== "true";
        catBtns.forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", String(on));
        cats.forEach(function (c) { c.hidden = on && c.id !== b.getAttribute("data-cat"); });
      });
    });
  }

  /* ---------- Player form: pre-check an interest (?need=football) ---------- */
  var need = params.get("need");
  if (need) {
    var map = { football: "Football opportunities", education: "Education and scholarships", career: "Career development", wellbeing: "Health and wellbeing" };
    var box = document.querySelector('input[name="interests"][value="' + map[need] + '"]');
    if (box) box.checked = true;
  }

  /* ---------- Featured player rotation ---------- */
  document.querySelectorAll("[data-feature]").forEach(function (root) {
    var slides = Array.prototype.slice.call(root.querySelectorAll(".feat-slide"));
    var dots = Array.prototype.slice.call(root.querySelectorAll(".feat-dot"));
    var pauseBtn = root.querySelector(".feat-pause");
    if (slides.length < 2) return;
    var i = 0, timer = null, paused = reduce, hold = false;
    function show(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) {
        var on = k === i;
        s.classList.toggle("is-active", on);
        if (on) s.removeAttribute("aria-hidden"); else s.setAttribute("aria-hidden", "true");
      });
      dots.forEach(function (d, k) { d.setAttribute("aria-current", k === i ? "true" : "false"); });
    }
    function schedule() {
      clearTimeout(timer);
      root.classList.remove("run");
      void root.offsetWidth; // restart the progress bar
      if (!paused && !hold) {
        root.classList.add("run");
        timer = setTimeout(function () { show(i + 1); schedule(); }, 7000);
      }
    }
    function setPaused(v) {
      paused = v;
      pauseBtn.setAttribute("aria-pressed", v ? "true" : "false");
      pauseBtn.setAttribute("aria-label", v ? "Play rotation" : "Pause rotation");
      schedule();
    }
    dots.forEach(function (d, k) { d.addEventListener("click", function () { show(k); schedule(); }); });
    root.querySelectorAll("[data-feat]").forEach(function (b) {
      b.addEventListener("click", function () { show(i + parseInt(b.getAttribute("data-feat"), 10)); schedule(); });
    });
    pauseBtn.addEventListener("click", function () { setPaused(!paused); });
    root.addEventListener("mouseenter", function () { hold = true; schedule(); });
    root.addEventListener("mouseleave", function () { hold = false; schedule(); });
    root.addEventListener("focusin", function () { hold = true; schedule(); });
    root.addEventListener("focusout", function (e) { if (!root.contains(e.relatedTarget)) { hold = false; schedule(); } });
    document.addEventListener("visibilitychange", function () { hold = document.hidden; schedule(); });
    // Start on a different player each visit so every player gets featured.
    show(Math.floor(Math.random() * slides.length));
    setPaused(paused);
  });

  /* ---------- Find a player ---------- */
  document.querySelectorAll("[data-finder]").forEach(function (input) {
    var root = input.closest(".finder");
    var empty = root.querySelector(".finder-empty");
    var count = document.getElementById("find-count");
    var items = Array.prototype.slice.call(document.querySelectorAll(".finder-results li, .lineup [data-search], .glance-table tr[data-search]"));
    function run() {
      var words = input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
      var shown = 0;
      items.forEach(function (el) {
        var text = el.getAttribute("data-search") || "";
        var ok = words.every(function (w) { return text.indexOf(w) > -1; });
        el.hidden = !ok;
        if (ok && el.tagName === "LI") shown++;
      });
      empty.hidden = shown > 0;
      if (count) count.textContent = words.length ? shown + (shown === 1 ? " player found" : " players found") : "";
      document.querySelectorAll(".rail-wrap").forEach(function (w) { var r = w.querySelector(".rail"); if (r) r.dispatchEvent(new Event("scroll")); });
    }
    input.addEventListener("input", run);
    input.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      var first = root.querySelector(".finder-results li:not([hidden]) a");
      if (first) { e.preventDefault(); window.location.href = first.getAttribute("href"); }
    });
    if (location.hash === "#find") { input.focus({ preventScroll: true }); }
  });

  /* ---------- Home banner: rotating player photos ---------- */
  document.querySelectorAll("[data-rotator]").forEach(function (root) {
    var slides = Array.prototype.slice.call(root.querySelectorAll(".rot-slide"));
    var bgs = Array.prototype.slice.call(document.querySelectorAll("[data-rotator-bg] .rot-bg"));
    if (slides.length < 2) return;
    var i = 0, timer = null, paused = reduce, hold = false;
    function show(n) {
      i = (n + slides.length) % slides.length;
      var len = slides.length;
      slides.forEach(function (s, k) {
        var d = (k - i + len) % len, on = d === 0;
        s.classList.toggle("is-active", on);
        s.classList.toggle("is-next", d === 1);
        s.classList.toggle("is-next2", d === 2 && len > 3);
        s.classList.toggle("is-prev", d === len - 1 && len > 2);
        if (on) { s.removeAttribute("aria-hidden"); s.removeAttribute("tabindex"); }
        else { s.setAttribute("aria-hidden", "true"); s.setAttribute("tabindex", "-1"); }
      });
      bgs.forEach(function (b, k) { b.classList.toggle("is-active", k === i); });
    }
    function schedule() {
      clearTimeout(timer);
      if (!paused && !hold) timer = setTimeout(function () { show(i + 1); schedule(); }, 5000);
    }
    root.addEventListener("mouseenter", function () { hold = true; schedule(); });
    root.addEventListener("mouseleave", function () { hold = false; schedule(); });
    root.addEventListener("focusin", function () { hold = true; schedule(); });
    root.addEventListener("focusout", function (e) { if (!root.contains(e.relatedTarget)) { hold = false; schedule(); } });
    document.addEventListener("visibilitychange", function () { hold = document.hidden; schedule(); });
    show(0);
    schedule();
  });

  /* ---------- Year ---------- */
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
