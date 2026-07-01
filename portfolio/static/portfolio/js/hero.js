/* Hero: neural constellation + LLM token-stream typing */
(function () {
    'use strict';

    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ====================================================================
    //  Token-stream typing — mimics a model streaming a completion
    // ====================================================================
    var stream = document.getElementById('token-stream');
    if (stream) {
        var phrases = [];
        var src = document.getElementById('stream-phrases');
        try {
            phrases = JSON.parse((src ? src.textContent : stream.getAttribute('data-phrases')) || '[]') || [];
        } catch (e) { phrases = []; }
        if (!phrases.length) phrases = ['large language models'];

        if (reduce) {
            stream.textContent = phrases[0];
        } else {
            var pi = 0, ci = 0, deleting = false;
            var tick = function () {
                var phrase = phrases[pi];
                if (!deleting) {
                    // Stream a small group of characters at a time → "tokens".
                    ci = Math.min(phrase.length, ci + (1 + Math.floor(Math.random() * 2)));
                    stream.textContent = phrase.slice(0, ci);
                    if (ci >= phrase.length) {
                        deleting = true;
                        return setTimeout(tick, 1700);
                    }
                    return setTimeout(tick, 45 + Math.random() * 55);
                } else {
                    ci = Math.max(0, ci - 2);
                    stream.textContent = phrase.slice(0, ci);
                    if (ci <= 0) {
                        deleting = false;
                        pi = (pi + 1) % phrases.length;
                        return setTimeout(tick, 320);
                    }
                    return setTimeout(tick, 24);
                }
            };
            setTimeout(tick, 700);
        }
    }

    // ====================================================================
    //  Neural constellation
    // ====================================================================
    var canvas = document.getElementById('neural-canvas');
    if (!canvas || reduce) return;

    var ctx = canvas.getContext('2d');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W = 0, H = 0, nodes = [], linkDist = 150;
    var mouse = { x: -9999, y: -9999 };
    var palette = ['99,102,241', '168,85,247', '34,211,238']; // indigo / violet / cyan

    // Cursor interaction — raise these for a stronger effect.
    var MOUSE_RADIUS = 250;   // px — how far the cursor's influence reaches
    var MOUSE_PULL = 0.006;   // how strongly nodes are drawn toward the cursor

    function size() {
        var rect = canvas.getBoundingClientRect();
        W = rect.width; H = rect.height;
        canvas.width = W * dpr; canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        var target = Math.round((W * H) / 16000);
        var count = Math.max(28, Math.min(92, target));
        nodes = [];
        for (var i = 0; i < count; i++) {
            nodes.push({
                x: Math.random() * W,
                y: Math.random() * H,
                vx: (Math.random() - 0.5) * 0.35,
                vy: (Math.random() - 0.5) * 0.35,
                r: Math.random() * 1.6 + 1,
                c: palette[i % palette.length]
            });
        }
    }

    function frame() {
        ctx.clearRect(0, 0, W, H);
        for (var i = 0; i < nodes.length; i++) {
            var n = nodes[i];
            n.x += n.vx; n.y += n.vy;
            if (n.x < 0 || n.x > W) n.vx *= -1;
            if (n.y < 0 || n.y > H) n.vy *= -1;

            // pull toward cursor — strongest up close, fading out at MOUSE_RADIUS
            var dxm = mouse.x - n.x, dym = mouse.y - n.y;
            var dm = Math.sqrt(dxm * dxm + dym * dym);
            var near = dm < MOUSE_RADIUS ? (1 - dm / MOUSE_RADIUS) : 0;
            if (near) { n.x += dxm * MOUSE_PULL * near; n.y += dym * MOUSE_PULL * near; }

            for (var j = i + 1; j < nodes.length; j++) {
                var m = nodes[j];
                var dx = n.x - m.x, dy = n.y - m.y;
                var d = Math.sqrt(dx * dx + dy * dy);
                if (d < linkDist) {
                    var a = (1 - d / linkDist) * 0.5;
                    ctx.strokeStyle = 'rgba(' + n.c + ',' + a + ')';
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(n.x, n.y); ctx.lineTo(m.x, m.y); ctx.stroke();
                }
            }

            // link to cursor — brighter and thicker as nodes get closer
            if (near) {
                ctx.strokeStyle = 'rgba(160,175,255,' + near * 0.55 + ')';
                ctx.lineWidth = 1.3; ctx.beginPath();
                ctx.moveTo(n.x, n.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
            }

            // node — swells slightly when the cursor is near
            ctx.fillStyle = 'rgba(' + n.c + ',0.95)';
            ctx.beginPath(); ctx.arc(n.x, n.y, n.r + near * 2.4, 0, Math.PI * 2); ctx.fill();
        }
        raf = requestAnimationFrame(frame);
    }

    var raf;
    function start() { cancelAnimationFrame(raf); raf = requestAnimationFrame(frame); }

    size();
    start();

    window.addEventListener('resize', function () { size(); });
    window.addEventListener('mousemove', function (e) {
        var rect = canvas.getBoundingClientRect();
        mouse.x = e.clientX - rect.left; mouse.y = e.clientY - rect.top;
    });
    window.addEventListener('mouseleave', function () { mouse.x = -9999; mouse.y = -9999; });
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) cancelAnimationFrame(raf); else start();
    });
})();
