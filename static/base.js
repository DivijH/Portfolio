/* LATENT SPACE — global interactions
   loader · custom cursor · magnetic buttons · menu overlay ·
   token stream · reveals · lifecycle stepper */
(function () {
    'use strict';

    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var finePointer = window.matchMedia('(pointer: fine)').matches;
    var noanim = new URLSearchParams(window.location.search).has('noanim');
    var root = document.documentElement;

    // =====================================================================
    // Loader — first visit each session (attr set pre-paint in head)
    // =====================================================================
    (function boot() {
        var el = document.getElementById('boot');
        var hasBoot = root.hasAttribute('data-boot');
        if (!el || !hasBoot || noanim) {
            if (hasBoot) root.removeAttribute('data-boot');
            window.dispatchEvent(new CustomEvent('latent:bloom'));
            return;
        }
        var count = el.querySelector('.boot-count');
        var bar = el.querySelector('.boot-bar i');
        var t0 = performance.now();
        var DURATION = 1250;
        function tick(now) {
            var x = Math.min(1, (now - t0) / DURATION);
            var p = Math.floor(100 * (1 - Math.pow(1 - x, 3)));
            if (count) count.textContent = String(p).padStart(3, '0');
            if (bar) bar.style.width = p + '%';
            if (x < 1) return requestAnimationFrame(tick);
            window.dispatchEvent(new CustomEvent('latent:bloom'));
            el.classList.add('done');
            setTimeout(function () { root.removeAttribute('data-boot'); }, 550);
        }
        requestAnimationFrame(tick);
        try { sessionStorage.setItem('booted', '1'); } catch (e) {}
    })();

    // =====================================================================
    // Custom cursor — a single ring with contextual labels
    // =====================================================================
    (function cursor() {
        if (!finePointer || reduce || noanim) return;
        var ring = document.getElementById('cur-ring');
        if (!ring) return;
        document.body.classList.add('has-cursor');

        var label = ring.querySelector('.cur-label');
        var x = -100, y = -100, rx = -100, ry = -100, seen = false;

        window.addEventListener('mousemove', function (e) {
            x = e.clientX; y = e.clientY;
            if (!seen) { rx = x; ry = y; seen = true; }
        }, { passive: true });

        document.addEventListener('mouseleave', function () { ring.style.opacity = '0'; });
        document.addEventListener('mouseenter', function () { ring.style.opacity = '1'; });
        window.addEventListener('mousedown', function () { ring.classList.add('down'); });
        window.addEventListener('mouseup', function () { ring.classList.remove('down'); });

        var HOVER = 'a, button, summary, [role="tab"], .lc-node, input[type="submit"]';
        document.addEventListener('mouseover', function (e) {
            var t = e.target.closest ? e.target.closest(HOVER) : null;
            if (t) {
                ring.classList.add('on');
                var src = e.target.closest('[data-cursor]');
                if (label) label.textContent = src ? src.getAttribute('data-cursor') : '';
            }
        });
        document.addEventListener('mouseout', function (e) {
            if (e.target.closest && e.target.closest(HOVER)) {
                ring.classList.remove('on');
                if (label) label.textContent = '';
            }
        });

        (function loop() {
            rx += (x - rx) * 0.3;
            ry += (y - ry) * 0.3;
            ring.style.transform = 'translate(' + rx + 'px,' + ry + 'px)';
            requestAnimationFrame(loop);
        })();
    })();

    // =====================================================================
    // Magnetic buttons
    // =====================================================================
    (function magnetic() {
        if (!finePointer || reduce || noanim) return;
        document.querySelectorAll('[data-magnetic]').forEach(function (el) {
            var strength = 0.25;
            el.addEventListener('mousemove', function (e) {
                var r = el.getBoundingClientRect();
                var dx = e.clientX - (r.left + r.width / 2);
                var dy = e.clientY - (r.top + r.height / 2);
                el.style.transform = 'translate(' + dx * strength + 'px,' + dy * strength + 'px)';
            });
            el.addEventListener('mouseleave', function () {
                el.style.transition = 'transform .45s cubic-bezier(.22,.7,.16,1)';
                el.style.transform = '';
                setTimeout(function () { el.style.transition = ''; }, 460);
            });
        });
    })();

    // =====================================================================
    // Nav state + fullscreen menu
    // =====================================================================
    var nav = document.getElementById('nav');
    if (nav) {
        var onScrollNav = function () { nav.classList.toggle('scrolled', window.scrollY > 20); };
        window.addEventListener('scroll', onScrollNav, { passive: true });
        onScrollNav();
    }

    var burger = document.getElementById('hamburger');
    var menu = document.getElementById('menu');
    if (burger && menu) {
        var setMenu = function (open) {
            menu.classList.toggle('open', open);
            burger.setAttribute('aria-expanded', open ? 'true' : 'false');
            root.classList.toggle('menu-open', open);
        };
        burger.addEventListener('click', function () { setMenu(!menu.classList.contains('open')); });
        menu.querySelectorAll('a').forEach(function (a) {
            a.addEventListener('click', function () { setMenu(false); });
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && menu.classList.contains('open')) { setMenu(false); burger.focus(); }
        });
    }

    // =====================================================================
    // Research-focus typewriter (phrases come from the Profile tagline)
    // =====================================================================
    (function stream() {
        var el = document.getElementById('token-stream');
        if (!el) return;
        var phrases = [];
        var src = document.getElementById('stream-phrases');
        try { phrases = JSON.parse((src ? src.textContent : '[]') || '[]') || []; } catch (e) { phrases = []; }
        if (!phrases.length) phrases = ['large language models'];
        if (reduce || noanim) { el.textContent = phrases[0]; return; }

        var pi = 0, ci = 0, deleting = false;
        var tick = function () {
            var phrase = phrases[pi];
            if (!deleting) {
                ci = Math.min(phrase.length, ci + (1 + Math.floor(Math.random() * 2)));
                el.textContent = phrase.slice(0, ci);
                if (ci >= phrase.length) { deleting = true; return setTimeout(tick, 1900); }
                return setTimeout(tick, 42 + Math.random() * 55);
            }
            ci = Math.max(0, ci - 2);
            el.textContent = phrase.slice(0, ci);
            if (ci <= 0) { deleting = false; pi = (pi + 1) % phrases.length; return setTimeout(tick, 350); }
            return setTimeout(tick, 22);
        };
        setTimeout(tick, 900);
    })();

    // =====================================================================
    // Scroll reveal
    // =====================================================================
    (function reveal() {
        var els = document.querySelectorAll('.reveal');
        if (noanim) {
            root.classList.add('noanim');
            els.forEach(function (el) { el.classList.add('in'); });
            return;
        }
        if ('IntersectionObserver' in window && els.length) {
            var io = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) { entry.target.classList.add('in'); io.unobserve(entry.target); }
                });
            }, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' });
            els.forEach(function (el) { io.observe(el); });
        } else {
            els.forEach(function (el) { el.classList.add('in'); });
        }
    })();

    // =====================================================================
    // Publication abstract / bibtex toggles + copy
    // =====================================================================
    document.querySelectorAll('.pub-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var target = document.getElementById(btn.getAttribute('data-target'));
            if (!target) return;
            var open = target.classList.toggle('open');
            var label = btn.getAttribute(open ? 'data-open' : 'data-closed');
            if (label) btn.textContent = label;
        });
    });
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

    // =====================================================================
    // Agent-lifecycle stepper (+ gentle auto-advance until first interaction)
    // =====================================================================
    (function stepper() {
        var rail = document.querySelector('.lc-rail');
        if (!rail) return;
        var beam = document.querySelector('.lc-beam');
        var nodes = Array.prototype.slice.call(rail.querySelectorAll('.lc-node'));
        var panels = Array.prototype.slice.call(document.querySelectorAll('.lc-panel'));
        var current = 0;

        var select = function (idx) {
            current = idx;
            nodes.forEach(function (n, i) {
                n.classList.toggle('active', i === idx);
                n.classList.toggle('done', i < idx);
                n.setAttribute('aria-selected', i === idx ? 'true' : 'false');
                n.tabIndex = i === idx ? 0 : -1;
            });
            panels.forEach(function (p, i) { p.classList.toggle('active', i === idx); });
            if (beam) beam.style.setProperty('--p', nodes.length > 1 ? idx / (nodes.length - 1) : 0);
        };

        var auto = null;
        var visible = false;
        var stopAuto = function () { if (auto) { clearInterval(auto); auto = null; } };
        if (!reduce && !noanim && 'IntersectionObserver' in window) {
            var io = new IntersectionObserver(function (entries) {
                entries.forEach(function (en) { visible = en.isIntersecting; });
            }, { threshold: 0.35 });
            io.observe(rail);
            auto = setInterval(function () {
                if (visible && !document.hidden) select((current + 1) % nodes.length);
            }, 5200);
        }

        nodes.forEach(function (n, i) {
            n.addEventListener('click', function () { stopAuto(); select(i); });
            n.addEventListener('keydown', function (e) {
                var dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
                if (!dir) return;
                e.preventDefault();
                stopAuto();
                var next = (i + dir + nodes.length) % nodes.length;
                nodes[next].focus();
                select(next);
            });
        });
        select(0);
    })();

    // =====================================================================
    // Smooth scrolling — wheel input glides instead of stepping.
    // Eases the real scroll position (no transform hijack), so sticky
    // pinning and every scroll-driven effect stay native. Touch devices,
    // keyboard, scrollbar drags and nested scrollables keep default
    // behavior; reduced motion turns this off entirely.
    // =====================================================================
    (function smoothScroll() {
        if (!finePointer || reduce || noanim) return;

        var target = window.scrollY, cur = target, raf = null;

        function maxScroll() {
            return Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        }

        // let wheel events through when something inside can consume them
        function nestedScrolls(el, dy) {
            while (el && el !== document.body && el.nodeType === 1) {
                if (el.scrollHeight > el.clientHeight + 1) {
                    var o = getComputedStyle(el).overflowY;
                    if (o === 'auto' || o === 'scroll') {
                        if (dy < 0 ? el.scrollTop > 0
                                   : el.scrollTop + el.clientHeight < el.scrollHeight - 1) return true;
                    }
                }
                el = el.parentElement;
            }
            return false;
        }

        function loop() {
            cur += (target - cur) * 0.095;
            if (Math.abs(target - cur) < 0.5) { cur = target; raf = null; }
            else raf = requestAnimationFrame(loop);
            window.scrollTo({ top: cur, behavior: 'instant' });
        }

        window.addEventListener('wheel', function (e) {
            if (e.ctrlKey || e.defaultPrevented) return; // browser zoom
            if (root.hasAttribute('data-boot') || root.classList.contains('menu-open')) return;
            if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return; // horizontal → native
            if (nestedScrolls(e.target, e.deltaY)) return;
            e.preventDefault();
            var dy = e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? window.innerHeight : 1);
            if (!raf) { cur = window.scrollY; target = cur; }
            target = Math.min(maxScroll(), Math.max(0, target + dy));
            if (!raf) raf = requestAnimationFrame(loop);
        }, { passive: false });

        // keyboard / scrollbar / anchor scrolls happen natively — resync
        window.addEventListener('scroll', function () {
            if (!raf && Math.abs(window.scrollY - cur) > 2) { cur = target = window.scrollY; }
        }, { passive: true });
    })();

    // =====================================================================
    // Nav tucks away on scroll down, returns on scroll up
    // =====================================================================
    (function navHide() {
        if (!nav || reduce || noanim) return;
        var last = window.scrollY;
        window.addEventListener('scroll', function () {
            var y = window.scrollY;
            var dy = y - last;
            last = y;
            if (root.classList.contains('menu-open')) return;
            if (y > 300 && dy > 4) nav.classList.add('hide');
            else if (dy < -4 || y <= 300) nav.classList.remove('hide');
        }, { passive: true });
    })();

    // =====================================================================
    // Scroll choreography (desktop, fine pointer):
    //  · the traveling light journeys through the page
    //  · the hero name splits apart as you leave it
    //  · the lifecycle chapter pins and scrolls sideways with 3D depth
    //  · the footer wordmark rises into view
    // =====================================================================
    (function scrollFX() {
        if (reduce || noanim) return;
        var mq = window.matchMedia('(min-width: 900px) and (pointer: fine)');

        var hero = document.querySelector('.hero');
        var heroBits = hero ? hero.querySelectorAll('.hero-status, .hero-stream, .hero-sub, .hero-cta, .socials, .scroll-cue') : [];
        var lcH = document.querySelector('.lc-h');
        var track = lcH ? lcH.querySelector('.lc-h-track') : null;
        var slides = lcH ? Array.prototype.slice.call(lcH.querySelectorAll('.lc-slide')) : [];
        var lcProgress = lcH ? lcH.querySelector('.lc-h-progress') : null;
        var footer = document.querySelector('.footer');
        var wordmark = document.querySelector('.footer-wordmark');

        var on = false, raf = null;
        var sy = window.scrollY;
        var m = { slideOff: [] };
        var coreKeys = [];

        function docTop(el) {
            var r = el.getBoundingClientRect();
            return r.top + window.scrollY;
        }

        function measure() {
            m.vw = window.innerWidth;
            m.vh = window.innerHeight;
            m.doc = document.documentElement.scrollHeight;
            m.heroH = hero ? hero.offsetHeight : 0;
            if (lcH) {
                m.lcTop = docTop(lcH);
                m.lcH = lcH.offsetHeight;
                m.pinLen = Math.max(1, m.lcH - m.vh);
                m.trackMax = track ? Math.max(0, track.scrollWidth - m.vw) : 0;
                m.slideOff = slides.map(function (s) { return s.offsetLeft + s.offsetWidth / 2; });
            }
            m.footTop = footer ? docTop(footer) : 0;
            mMeasureWins();
            // geometry changed — an in-flight morph holds stale positions,
            // so rebuild it from fresh rects on the next frame
            mTeardown();

            // the light's journey, in document coordinates
            coreKeys = [{ at: 0, x: .8 * m.vw, y: .36 * m.vh, k: .9 }];
            if (m.heroH) coreKeys.push({ at: m.heroH * .75, x: .5 * m.vw, y: .85 * m.vh, k: .75 });
            if (lcH) {
                coreKeys.push({ at: m.lcTop, x: .12 * m.vw, y: .8 * m.vh, k: .9 });
                coreKeys.push({ at: m.lcTop + m.pinLen, x: .88 * m.vw, y: .8 * m.vh, k: .9 });
                coreKeys.push({ at: m.lcTop + m.lcH, x: .9 * m.vw, y: .3 * m.vh, k: .45 });
            }
            if (m.footTop) {
                coreKeys.push({ at: m.footTop - m.vh * 1.4, x: .1 * m.vw, y: .45 * m.vh, k: .45 });
                coreKeys.push({ at: Math.max(1, m.doc - m.vh), x: .5 * m.vw, y: .52 * m.vh, k: 1.0 });
            }
            coreKeys.sort(function (a, b) { return a.at - b.at; });
        }

        function coreAt(y) {
            // riding the pinned chapter: the light travels with the stages
            if (lcH && y >= m.lcTop && y <= m.lcTop + m.pinLen) {
                var pp = (y - m.lcTop) / m.pinLen;
                return { x: (0.12 + 0.76 * pp) * m.vw, y: .8 * m.vh, k: .9 };
            }
            var a = coreKeys[0], b = coreKeys[coreKeys.length - 1];
            if (y <= a.at) return { x: a.x, y: a.y, k: a.k };
            if (y >= b.at) return { x: b.x, y: b.y, k: b.k };
            for (var i = 0; i < coreKeys.length - 1; i++) {
                if (y >= coreKeys[i].at && y <= coreKeys[i + 1].at) { a = coreKeys[i]; b = coreKeys[i + 1]; break; }
            }
            var x = (y - a.at) / Math.max(1, b.at - a.at);
            x = x * x * (3 - 2 * x);
            return { x: a.x + (b.x - a.x) * x, y: a.y + (b.y - a.y) * x, k: a.k + (b.k - a.k) * x };
        }

        function clamp01(v) { return Math.min(1, Math.max(0, v)); }

        function apply(y) {
            // hero: everything but the name fades as the page moves on
            // (the name itself leaves via the title morph)
            if (hero && heroBits.length) {
                var hp = clamp01(y / Math.max(1, m.heroH * .85));
                var op = String(clamp01(1 - hp * 1.15));
                for (var hb = 0; hb < heroBits.length; hb++) heroBits[hb].style.opacity = op;
            }

            // lifecycle: vertical scroll becomes sideways travel
            if (lcH && track) {
                var p = clamp01((y - m.lcTop) / m.pinLen);
                var tx = p * m.trackMax;
                track.style.transform = 'translate3d(' + (-tx) + 'px,0,0)';
                if (lcProgress) lcProgress.style.setProperty('--p', p);
                for (var i = 0; i < slides.length; i++) {
                    var d = (m.slideOff[i] - tx - m.vw / 2) / m.vw; // -.. 0 ..+ across screen
                    slides[i].style.transform =
                        'rotateY(' + (d * -7).toFixed(2) + 'deg) translateZ(' + (-Math.abs(d) * 110).toFixed(1) + 'px)';
                }
            }

            // footer wordmark rises into place
            if (wordmark && m.footTop) {
                var fp = clamp01((y + m.vh - m.footTop) / Math.max(1, (m.doc - m.footTop)));
                wordmark.style.transform = 'translate3d(0,' + ((1 - fp) * 34).toFixed(2) + '%,0)';
            }

            morphUpdate(y);
            window.LATENT_CORE = coreAt(y);
        }

        // -----------------------------------------------------------------
        // Title morph: between consecutive headings, each letter flies its
        // own curved path from its slot in the old title to its slot in the
        // new one. Shared letters travel; leftovers drift out; new ones
        // drift in. Purely scroll-driven, works in both directions.
        // -----------------------------------------------------------------
        var mTitles = Array.prototype.slice.call(document.querySelectorAll('[data-morph]'));
        var mWins = [];
        var mLayer = null;
        var mAct = null; // { idx, chars: [...] }

        function mHash(n) { return (((n + 7) * 2654435761) >>> 0) % 1000 / 1000; }
        function mEase(x) { return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }

        // wrap every visible character of each title in a span (done once)
        mTitles.forEach(function (t) {
            var walk = function (node) {
                if (node.nodeType === 3) {
                    var frag = document.createDocumentFragment();
                    var text = node.textContent;
                    for (var i = 0; i < text.length; i++) {
                        if (/\s/.test(text[i])) { frag.appendChild(document.createTextNode(text[i])); }
                        else {
                            var s = document.createElement('span');
                            s.className = 'mchar';
                            s.textContent = text[i];
                            frag.appendChild(s);
                        }
                    }
                    node.parentNode.replaceChild(frag, node);
                } else if (node.nodeType === 1) {
                    Array.prototype.slice.call(node.childNodes).forEach(walk);
                }
            };
            walk(t);
        });

        // a heading inside the pinned chapter reports a scroll-dependent
        // document position while stuck — anchor it to the chapter start
        function mDocTop(el) {
            if (lcH && lcH.contains(el)) {
                var sticky = lcH.querySelector('.lc-h-sticky');
                return m.lcTop + (el.getBoundingClientRect().top - sticky.getBoundingClientRect().top);
            }
            return docTop(el);
        }

        function mMeasureWins() {
            mWins = [];
            for (var i = 1; i < mTitles.length; i++) {
                var A = mTitles[i - 1];
                var aTop = mDocTop(A), bTop = mDocTop(mTitles[i]);
                // letters break early — while the old heading is still mid-frame —
                // so the flight gets a long, unhurried stretch of scroll
                var start = aTop - m.vh * .55;
                // …though the pinned chapter's heading only leaves near pin release
                if (lcH && lcH.contains(A)) start = m.lcTop + m.pinLen - m.vh * .35;
                // never active at page load — flight begins only once you scroll
                start = Math.max(start, m.vh * .15);
                // short sections: never overlap the previous flight
                if (mWins.length) start = Math.max(start, mWins[mWins.length - 1].end + 10);
                // …and land while the new heading is entering the frame, with a
                // long minimum flight — but never later than the upper third
                var end = Math.max(bTop - m.vh * .8, start + m.vh * 1.15);
                end = Math.min(end, bTop - m.vh * .3);
                if (end - start > 40) mWins.push({ a: i - 1, b: i, start: start, end: end });
            }
        }

        function mSnapshot(el) {
            // rendered glyphs + style of every char, relative to the title box
            var base = el.getBoundingClientRect();
            var styleCache = new Map();
            return Array.prototype.map.call(el.querySelectorAll('.mchar'), function (ch) {
                var r = ch.getBoundingClientRect();
                var parent = ch.parentNode;
                if (!styleCache.has(parent)) {
                    var cs = getComputedStyle(parent);
                    styleCache.set(parent, {
                        size: parseFloat(cs.fontSize), weight: cs.fontWeight, color: cs.color,
                        stroke: cs.webkitTextStrokeWidth && parseFloat(cs.webkitTextStrokeWidth) > 0
                            ? cs.webkitTextStrokeWidth + ' ' + cs.webkitTextStrokeColor : '',
                        upper: cs.textTransform === 'uppercase'
                    });
                }
                var st = styleCache.get(parent);
                var c = ch.textContent;
                return { dx: r.left - base.left, dy: r.top - base.top, st: st,
                         c: st.upper ? c.toUpperCase() : c, key: c.toLowerCase() };
            });
        }

        function mApplyStyle(span, st, c) {
            span.textContent = c;
            span.style.fontSize = st.size + 'px';
            span.style.fontWeight = st.weight;
            span.style.color = st.stroke ? 'transparent' : st.color;
            span.style.webkitTextStroke = st.stroke || '0';
        }

        function mBuild(idx) {
            mTeardown();
            if (!mLayer) {
                mLayer = document.createElement('div');
                mLayer.id = 'morph';
                mLayer.setAttribute('aria-hidden', 'true');
                document.body.appendChild(mLayer);
            }
            var A = mTitles[mWins[idx].a], B = mTitles[mWins[idx].b];
            var src = mSnapshot(A), tgt = mSnapshot(B);

            // pair letters: same letter, closest relative position
            var used = [];
            var chars = [];
            tgt.forEach(function (tc, j) {
                var best = -1, bestD = 1e9;
                src.forEach(function (sc, i) {
                    if (used[i] || sc.key !== tc.key) return;
                    var d = Math.abs(i / src.length - j / tgt.length);
                    if (d < bestD) { bestD = d; best = i; }
                });
                if (best >= 0) { used[best] = true; chars.push({ s: src[best], t: tc, kind: 'move' }); }
                else { chars.push({ s: null, t: tc, kind: 'in' }); }
            });
            src.forEach(function (sc, i) { if (!used[i]) chars.push({ s: sc, t: null, kind: 'out' }); });

            var frag = document.createDocumentFragment();
            chars.forEach(function (c, i) {
                var span = document.createElement('span');
                var st = (c.s || c.t).st;
                mApplyStyle(span, st, (c.s || c.t).c);
                c.el = span;
                c.amp = (mHash(i) - .5) * m.vh * .7;         // path bow — wide, loopy
                c.rot = (mHash(i + 13) - .5) * 44;           // wiggle tilt
                c.d = mHash(i + 7) * .32;                    // stagger
                c.swing = mHash(i + 3);                      // S-curve reach, first leg
                c.swing2 = mHash(i + 41);                    // S-curve reach, second leg
                c.flip = mHash(i + 53) < .4 ? -1 : 1;        // some loop the other way
                c.spin = mHash(i + 29) < .28 ? (mHash(i + 31) < .5 ? -1 : 1) : 0; // full 360s
                c.freq = 1.5 + mHash(i + 17) * 2;            // wave cycles along the path
                c.phase = mHash(i + 23) * 6.283;
                c.wob = m.vh * (.03 + .06 * mHash(i + 37));  // wave amplitude
                c.swapped = false;
                frag.appendChild(span);
            });
            mLayer.appendChild(frag);
            mLayer.style.display = 'block';
            // both headings stay as hollow outlines the letters leave/fill
            A.classList.add('m-ghost');
            B.classList.add('m-ghost');
            mAct = { idx: idx, chars: chars, A: A, B: B };
        }

        function mTeardown() {
            if (!mAct) return;
            mAct.A.classList.remove('m-ghost');
            mAct.B.classList.remove('m-ghost');
            mAct.A.style.opacity = '';
            mAct.B.style.opacity = '';
            if (mLayer) { mLayer.style.display = 'none'; mLayer.innerHTML = ''; }
            mAct = null;
        }

        function mRender(p) {
            var ra = mAct.A.getBoundingClientRect();
            var rb = mAct.B.getBoundingClientRect();
            // the departed outline dissolves; the destination outline
            // materializes, waiting to be filled
            mAct.A.style.opacity = String(clamp01(1 - p * 1.1));
            mAct.B.style.opacity = String(clamp01(.18 + p * .82));
            mAct.chars.forEach(function (c) {
                var cp = clamp01((p - c.d) / (1 - c.d));
                var e = mEase(cp);
                var sx, sy2, tx, ty, op = 1;

                if (c.kind === 'move') {
                    sx = ra.left + c.s.dx; sy2 = ra.top + c.s.dy;
                    tx = rb.left + c.t.dx; ty = rb.top + c.t.dy;
                } else if (c.kind === 'out') {
                    sx = ra.left + c.s.dx; sy2 = ra.top + c.s.dy;
                    tx = sx + (mHash(c.rot * 97) - .5) * m.vw * .4; ty = sy2 - m.vh * .3;
                    op = clamp01(1 - cp / .6);
                } else { // in
                    tx = rb.left + c.t.dx; ty = rb.top + c.t.dy;
                    sx = tx + (mHash(c.rot * 89) - .5) * m.vw * .4; sy2 = ty + m.vh * .3;
                    op = clamp01((cp - .4) / .5);
                }

                // cubic S-curve: one leg sweeps toward one side of the screen,
                // the other leg swings back — then a sine meander on top, so
                // paths wander up-down and left-right instead of simple arcs
                var mx = (sx + tx) / 2;
                var side = (mx < m.vw * .5 ? 1 : -1) * c.flip;
                var c1x = m.vw * (.5 + side * (.12 + .36 * c.swing));
                var c2x = m.vw * (.5 - side * (.12 + .36 * c.swing2));
                var c1y = sy2 + (ty - sy2) * .3 + c.amp;
                var c2y = sy2 + (ty - sy2) * .7 - c.amp * .8;
                var q = 1 - e;
                var x = q * q * q * sx + 3 * q * q * e * c1x + 3 * q * e * e * c2x + e * e * e * tx;
                var y2 = q * q * q * sy2 + 3 * q * q * e * c1y + 3 * q * e * e * c2y + e * e * e * ty;

                var env = Math.sin(e * Math.PI); // 0 at both ends — landings stay exact
                x += Math.sin(e * Math.PI * c.freq + c.phase) * c.wob * env;
                y2 += Math.cos(e * Math.PI * c.freq * .8 + c.phase * 1.7) * c.wob * .85 * env;

                // adopt the destination glyph mid-flight
                if (c.kind === 'move') {
                    if (!c.swapped && e >= .5) { mApplyStyle(c.el, c.t.st, c.t.c); c.swapped = true; }
                    else if (c.swapped && e < .5) { mApplyStyle(c.el, c.s.st, c.s.c); c.swapped = false; }
                }
                var s0 = (c.s || c.t).st.size;
                var s1 = (c.t || c.s).st.size;
                var scale = (s0 + (s1 - s0) * e) / ((c.kind === 'move' && c.swapped) ? s1 : s0);
                scale *= 1 + env * .12; // slight swell mid-air

                // some letters pirouette a full turn; the rest wiggle-tilt
                var rot = c.spin
                    ? e * 360 * c.spin
                    : Math.sin(e * Math.PI * 2) * c.rot;
                c.el.style.opacity = op;
                c.el.style.transform = 'translate3d(' + x.toFixed(1) + 'px,' + y2.toFixed(1) + 'px,0)' +
                                       ' rotate(' + rot.toFixed(1) + 'deg) scale(' + scale.toFixed(3) + ')';
            });
        }

        function morphUpdate(y) {
            if (!mTitles.length || mTitles.length < 2 || !mWins.length) return;
            try {
                var active = -1, p = 0;
                for (var i = 0; i < mWins.length; i++) {
                    var w = mWins[i];
                    var pi = (y - w.start) / Math.max(1, w.end - w.start);
                    if (pi > 0 && pi < 1) { active = i; p = pi; break; }
                }
                if (active === -1) { mTeardown(); return; }
                if (!mAct || mAct.idx !== active) mBuild(active);
                mRender(p);
            } catch (e) {
                // never leave a heading invisible
                mTeardown();
                mTitles.forEach(function (t) { t.classList.remove('m-ghost'); t.style.opacity = ''; });
                mWins = [];
            }
        }

        var lastFrame = 0;
        function loop(now) {
            // starved frames (background/occluded tab) snap instead of lerping,
            // so positions always match the real scroll when a frame does land
            if (now - lastFrame > 200) sy = window.scrollY;
            lastFrame = now;
            // page scroll is already eased by the smooth scroller — track it
            // tightly so choreography stays coherent with the content
            sy += (window.scrollY - sy) * 0.3;
            if (Math.abs(window.scrollY - sy) > 0.2) {
                apply(sy);
                raf = requestAnimationFrame(loop);
            } else {
                sy = window.scrollY;
                apply(sy);
                raf = null;
            }
        }
        function kick() { if (on && !raf) raf = requestAnimationFrame(loop); }

        function reset() {
            [track, wordmark].forEach(function (el) {
                if (el) el.style.transform = '';
            });
            slides.forEach(function (s) { s.style.transform = ''; });
            Array.prototype.forEach.call(heroBits, function (el) { el.style.opacity = ''; });
            if (lcProgress) lcProgress.style.setProperty('--p', 0);
            mTeardown();
            mTitles.forEach(function (t) { t.classList.remove('m-ghost'); t.style.opacity = ''; });
            window.LATENT_CORE = null;
        }

        function setOn(v) {
            if (on === v) return;
            on = v;
            root.classList.toggle('fx', v);
            if (v) { measure(); sy = window.scrollY; apply(sy); }
            else { reset(); }
        }

        if (mq.addEventListener) mq.addEventListener('change', function (e) { setOn(e.matches); });
        window.addEventListener('scroll', kick, { passive: true });
        window.addEventListener('resize', function () { if (on) { measure(); apply(sy); } });
        window.addEventListener('load', function () { if (on) { measure(); apply(sy); } });
        // re-measure once the display font arrives (glyph metrics change) and
        // once the hero name finishes rising (its transform pollutes rects)
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(function () { if (on) { measure(); apply(sy); } });
        }
        document.querySelectorAll('.hero-name .row-in').forEach(function (el) {
            el.addEventListener('animationend', function () { if (on) { measure(); apply(sy); } });
        });
        setOn(mq.matches);
    })();

    // =====================================================================
    // Footer year
    // =====================================================================
    var yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
