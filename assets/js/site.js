/* bathypinto — site.js
   Vanilla, no dependencies. Every feature degrades to working HTML without it. */
(function () {
  'use strict';

  var root = document.documentElement;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- 1. Theme toggle -------------------------------------------------- */
  var btn = document.getElementById('theme');

  function currentTheme() {
    var set = root.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function syncToggleLabel() {
    if (!btn) return;
    var dark = currentTheme() === 'dark';
    btn.setAttribute('aria-pressed', String(dark));
    btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
  }

  if (btn) {
    btn.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* private mode, blocked storage */ }
      syncToggleLabel();
    });
    syncToggleLabel();
  }

  /* Follow the system if the user has never made an explicit choice. */
  var sysDark = window.matchMedia('(prefers-color-scheme: dark)');
  var onSysChange = function () {
    var stored = null;
    try { stored = localStorage.getItem('theme'); } catch (e) {}
    if (!stored) syncToggleLabel();
  };
  if (sysDark.addEventListener) sysDark.addEventListener('change', onSysChange);

  /* ---- 2. Sticky nav state --------------------------------------------- */
  var nav = document.getElementById('nav');
  if (nav) {
    var onScroll = function () { nav.classList.toggle('is-stuck', window.scrollY > 40); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---- 3. Reveal on scroll + active nav link ---------------------------- */
  var supportsIO = 'IntersectionObserver' in window;

  /* The `js` class was set pre-paint in the inline head script; if the reveal
     cannot run after all, drop it so nothing stays hidden. */
  if (!supportsIO || reduced) {
    root.classList.remove('js');
  } else {
    var revealIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add('is-visible');
        revealIO.unobserve(en.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });

    document.querySelectorAll('.reveal').forEach(function (el) { revealIO.observe(el); });
  }

  if (supportsIO) {
    var links = {};
    document.querySelectorAll('.nav__links a[href^="#"]').forEach(function (a) {
      links[a.getAttribute('href').slice(1)] = a;
    });
    var navIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = links[en.target.id];
        if (a) a.classList.toggle('is-current', en.isIntersecting);
      });
    }, { rootMargin: '-45% 0px -45% 0px' });

    Object.keys(links).forEach(function (id) {
      var sec = document.getElementById(id);
      if (sec) navIO.observe(sec);
    });
  }

  /* ---- 4. Stat count-up ------------------------------------------------- */
  if (supportsIO && !reduced) {
    var statIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        statIO.unobserve(el);

        var raw = el.getAttribute('data-count') || el.textContent;
        var target = parseFloat(String(raw).replace(/[^0-9.]/g, ''));
        if (!isFinite(target) || target === 0) return;

        var suffix = String(raw).replace(/[0-9.,]/g, '');
        var decimals = (String(raw).split('.')[1] || '').replace(/\D/g, '').length;
        var start = performance.now();
        var DUR = 900;

        (function step(now) {
          var p = Math.min((now - start) / DUR, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = (target * eased).toFixed(decimals) + suffix;
          if (p < 1) requestAnimationFrame(step);
        })(start);
      });
    }, { threshold: 0.6 });

    document.querySelectorAll('[data-count]').forEach(function (el) { statIO.observe(el); });
  }

  /* ---- 5. Testimonial slider ------------------------------------------- */
  var quotes = Array.prototype.slice.call(document.querySelectorAll('.q'));
  if (quotes.length > 1) {
    var i = 0;
    var now = document.getElementById('q-now');
    var all = document.getElementById('q-all');
    if (all) all.textContent = String(quotes.length);

    var show = function (n) {
      i = (n + quotes.length) % quotes.length;
      quotes.forEach(function (q, k) { q.classList.toggle('is-on', k === i); });
      if (now) now.textContent = String(i + 1);
    };

    document.querySelectorAll('[data-q]').forEach(function (b) {
      b.addEventListener('click', function () {
        show(i + (b.getAttribute('data-q') === 'next' ? 1 : -1));
      });
    });
    show(0);
  }

  /* ---- 6. Odds and ends ------------------------------------------------- */
  var yr = document.getElementById('yr');
  if (yr) yr.textContent = String(new Date().getFullYear());
})();
