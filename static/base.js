/* Latent Space — global interactions */
(function () {
    'use strict';

    // ---- Theme toggle ----------------------------------------------------
    var toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.addEventListener('click', function () {
            var root = document.documentElement;
            var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', next);
            try { localStorage.setItem('theme', next); } catch (e) {}
            window.dispatchEvent(new CustomEvent('themechange', { detail: next }));
        });
    }

    // ---- Mobile nav ------------------------------------------------------
    var burger = document.getElementById('hamburger');
    var links = document.getElementById('nav-links');
    if (burger && links) {
        burger.addEventListener('click', function () {
            var open = links.classList.toggle('open');
            burger.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
        links.querySelectorAll('a').forEach(function (a) {
            a.addEventListener('click', function () {
                links.classList.remove('open');
                burger.setAttribute('aria-expanded', 'false');
            });
        });
    }

    // ---- Nav shadow on scroll -------------------------------------------
    var nav = document.getElementById('nav');
    if (nav) {
        var onScroll = function () { nav.classList.toggle('scrolled', window.scrollY > 8); };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    // ---- Scroll reveal ---------------------------------------------------
    var revealables = document.querySelectorAll('.reveal');
    var noanim = new URLSearchParams(window.location.search).has('noanim');
    if (noanim) {
        document.documentElement.classList.add('noanim');
        revealables.forEach(function (el) { el.classList.add('in'); });
    } else if ('IntersectionObserver' in window && revealables.length) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in');
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
        revealables.forEach(function (el) { io.observe(el); });
    } else {
        revealables.forEach(function (el) { el.classList.add('in'); });
    }

    // ---- Publication abstract / bibtex toggles --------------------------
    document.querySelectorAll('.pub-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var target = document.getElementById(btn.getAttribute('data-target'));
            if (!target) return;
            var open = target.classList.toggle('open');
            var label = btn.getAttribute(open ? 'data-open' : 'data-closed');
            if (label) btn.textContent = label;
        });
    });

    // ---- Copy bibtex -----------------------------------------------------
    document.querySelectorAll('[data-copy]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var el = document.getElementById(btn.getAttribute('data-copy'));
            if (!el || !navigator.clipboard) return;
            navigator.clipboard.writeText(el.textContent.trim()).then(function () {
                var prev = btn.textContent;
                btn.textContent = 'copied ✓';
                setTimeout(function () { btn.textContent = prev; }, 1400);
            });
        });
    });

    // ---- Agent-lifecycle stepper ----------------------------------------
    var rail = document.querySelector('.lc-rail');
    if (rail) {
        var nodes = Array.prototype.slice.call(rail.querySelectorAll('.lc-node'));
        var panels = Array.prototype.slice.call(document.querySelectorAll('.lc-panel'));
        var select = function (idx) {
            nodes.forEach(function (n, i) {
                n.classList.toggle('active', i === idx);
                n.classList.toggle('done', i < idx);
                n.setAttribute('aria-selected', i === idx ? 'true' : 'false');
                n.tabIndex = i === idx ? 0 : -1;
            });
            panels.forEach(function (p, i) { p.classList.toggle('active', i === idx); });
            rail.style.setProperty('--p', nodes.length > 1 ? idx / (nodes.length - 1) : 0);
        };
        nodes.forEach(function (n, i) {
            n.addEventListener('click', function () { select(i); });
            n.addEventListener('keydown', function (e) {
                var dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
                if (!dir) return;
                e.preventDefault();
                var next = (i + dir + nodes.length) % nodes.length;
                nodes[next].focus();
                select(next);
            });
        });
        select(0);
    }

    // ---- Footer year -----------------------------------------------------
    var yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
