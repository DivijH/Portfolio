/* LATENT — full-viewport reactive fog. Raw WebGL, no dependencies.
   A domain-warped noise field in ultraviolet: the "latent space" every page
   floats in. Reacts to the pointer (a lens of structure), drifts with scroll,
   and blooms from noise into form after the boot sequence. */
(function () {
    'use strict';

    var canvas = document.getElementById('latent');
    if (!canvas) return;

    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var gl = canvas.getContext('webgl', { antialias: false, alpha: false, depth: false, stencil: false });
    if (!gl) return; // CSS gradient fallback stays visible

    var VERT = [
        'attribute vec2 a;',
        'void main(){ gl_Position = vec4(a, 0., 1.); }'
    ].join('\n');

    var FRAG = [
        'precision highp float;',
        'uniform vec2 u_res;',
        'uniform float u_time;',
        'uniform vec2 u_mouse;',   // pixels
        'uniform float u_scroll;', // scrollY / viewportH
        'uniform float u_intro;',  // 0 -> 1 boot bloom
        'uniform vec2 u_core;',    // pixels — the traveling light
        'uniform float u_coreK;',  // its intensity, 0..~1.2

        'float hash(vec2 p){ p = fract(p*vec2(234.34, 435.345)); p += dot(p, p+34.23); return fract(p.x*p.y); }',
        'float noise(vec2 p){',
        '  vec2 i = floor(p), f = fract(p);',
        '  f = f*f*(3.-2.*f);',
        '  float a = hash(i), b = hash(i+vec2(1.,0.)), c = hash(i+vec2(0.,1.)), d = hash(i+vec2(1.,1.));',
        '  return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);',
        '}',
        'float fbm(vec2 p){',
        '  float v = 0., amp = .5;',
        '  mat2 rot = mat2(1.6, 1.2, -1.2, 1.6);',
        '  for (int i = 0; i < 4; i++){ v += amp*noise(p); p = rot*p; amp *= .5; }',
        '  return v;',
        '}',

        'void main(){',
        '  vec2 uv = (gl_FragCoord.xy - .5*u_res) / min(u_res.x, u_res.y);',
        '  float t = u_time*.045;',
        // field settles (zooms out slightly) as the boot completes
        '  vec2 p = uv * mix(2.9, 2.05, u_intro);',
        '  p.y += u_scroll*.42;',

        // pointer as a lens: local warp + light
        '  vec2 m = (u_mouse - .5*u_res) / min(u_res.x, u_res.y);',
        '  float md = length(uv - m);',
        '  float lens = smoothstep(.6, 0., md);',

        // the core condenses the fog around itself
        '  vec2 c = (u_core - .5*u_res) / min(u_res.x, u_res.y);',
        '  float cd = length(uv - c);',
        '  float condense = smoothstep(.65, 0., cd) * u_coreK;',

        // domain warp: q warps p, r warps again — fog with anatomy
        '  vec2 q = vec2(fbm(p + t), fbm(p + vec2(5.2, 1.3) - t*.8));',
        '  vec2 r = vec2(fbm(p + 2.4*q + vec2(1.7, 9.2) + .32*t), fbm(p + 2.4*q + vec2(8.3, 2.8) - .26*t));',
        '  float f = fbm(p + 2.1*r + lens*.5 + condense*.4);',

        '  vec3 cVoid  = vec3(.026, .022, .07);',
        '  vec3 cDeep  = vec3(.16, .125, .46);',  // deep ultraviolet
        '  vec3 cBright= vec3(.545, .486, 1.0);', // ultraviolet
        '  vec3 cEmber = vec3(1.0, .36, .22);',

        '  vec3 col = cVoid;',
        '  col = mix(col, cDeep, smoothstep(.26, .84, f));',
        '  col = mix(col, cBright*.42, smoothstep(.56, .98, f));',

        // rare ember veins: a narrow ridge, gated by a second field so they only
        // surface in patches — heat inside the structure
        '  float ridge = smoothstep(.6, .68, f) * smoothstep(.76, .68, f);',
        '  float gate = smoothstep(.55, .8, fbm(p*.5 - t*.6));',
        '  col = mix(col, cEmber*.5, ridge*gate*.5);',

        '  col += cBright * lens * .085;',

        // the traveling light: soft inverse-square star with a hot center
        '  float glow = u_coreK * .017 / (cd*cd + .02);',
        '  col += vec3(.6, .53, 1.0) * glow;',
        '  col += vec3(1.0, .97, .95) * glow * glow * .05;',
        '  col *= 1. + condense * .16;',

        // settle-in bloom + gentle dim as you scroll into the document
        '  col *= (.15 + .85*u_intro);',
        '  col *= 1. / (1. + u_scroll*.05);',
        '  col = min(col, vec3(1.08));',

        // vignette + dither (kills banding in the dark ranges)
        '  col *= 1. - .42*dot(uv, uv);',
        '  col += (hash(gl_FragCoord.xy + u_time) - .5) * .0045;',

        '  gl_FragColor = vec4(col, 1.);',
        '}'
    ].join('\n');

    function compile(type, src) {
        var s = gl.createShader(type);
        gl.shaderSource(s, src);
        gl.compileShader(s);
        if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) return null;
        return s;
    }

    var vs = compile(gl.VERTEX_SHADER, VERT);
    var fs = compile(gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return;
    var prog = gl.createProgram();
    gl.attachShader(prog, vs); gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
    gl.useProgram(prog);

    // fullscreen triangle
    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, 'a');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    var U = {
        res: gl.getUniformLocation(prog, 'u_res'),
        time: gl.getUniformLocation(prog, 'u_time'),
        mouse: gl.getUniformLocation(prog, 'u_mouse'),
        scroll: gl.getUniformLocation(prog, 'u_scroll'),
        intro: gl.getUniformLocation(prog, 'u_intro'),
        core: gl.getUniformLocation(prog, 'u_core'),
        coreK: gl.getUniformLocation(prog, 'u_coreK')
    };

    // fog is soft — render at reduced resolution, scale up for free
    var SCALE = 0.5;
    var W = 0, H = 0;
    function size() {
        var dpr = Math.min(window.devicePixelRatio || 1, 1.5) * SCALE;
        W = Math.max(2, Math.floor(window.innerWidth * dpr));
        H = Math.max(2, Math.floor(window.innerHeight * dpr));
        canvas.width = W; canvas.height = H;
        gl.viewport(0, 0, W, H);
    }
    size();
    window.addEventListener('resize', size);

    // pointer lens — lerped; touch devices get a slow autopilot orbit
    var finePointer = window.matchMedia('(pointer: fine)').matches;
    var mx = window.innerWidth * .7, my = window.innerHeight * .3;
    var tx = mx, ty = my;
    if (finePointer) {
        window.addEventListener('mousemove', function (e) { tx = e.clientX; ty = e.clientY; }, { passive: true });
    }

    // boot bloom: intro eases 0 -> 1 (skips straight to 1 when there's no boot)
    var intro = document.documentElement.hasAttribute('data-boot') ? 0 : 1;
    var introTarget = intro;
    window.addEventListener('latent:bloom', function () { introTarget = 1; });
    setTimeout(function () { introTarget = 1; }, 3500); // failsafe

    // the traveling light — scroll choreography (base.js) publishes targets via
    // window.LATENT_CORE = {x, y, k} in CSS pixels; without it, a slow drift
    var ccx = window.innerWidth * .72, ccy = window.innerHeight * .44, cck = 0;

    var scroll = 0;
    var timeAcc = 0, last = performance.now();
    var raf = null;

    function frame(now) {
        timeAcc += Math.min(now - last, 100); // clamp gaps so time pauses, never jumps
        last = now;
        var t = timeAcc / 1000;

        if (!finePointer) { // autopilot orbit for touch
            tx = window.innerWidth * (0.5 + 0.34 * Math.sin(t * 0.21));
            ty = window.innerHeight * (0.4 + 0.3 * Math.cos(t * 0.17));
        }
        mx += (tx - mx) * 0.055;
        my += (ty - my) * 0.055;
        scroll += ((window.scrollY / Math.max(1, window.innerHeight)) - scroll) * 0.08;
        intro += (introTarget - intro) * 0.028;

        var L = window.LATENT_CORE;
        var lx, ly, lk;
        if (L) { lx = L.x; ly = L.y; lk = L.k; }
        else { // ambient drift when no choreography is running
            lx = window.innerWidth * (0.68 + 0.16 * Math.sin(t * 0.13));
            ly = window.innerHeight * (0.42 + 0.2 * Math.cos(t * 0.1));
            lk = 0.55;
        }
        ccx += (lx - ccx) * 0.06;
        ccy += (ly - ccy) * 0.06;
        cck += (lk * intro - cck) * 0.05;

        gl.uniform2f(U.res, W, H);
        gl.uniform1f(U.time, t);
        // canvas Y is flipped relative to client coords
        gl.uniform2f(U.mouse, mx * (W / window.innerWidth), H - my * (H / window.innerHeight));
        gl.uniform1f(U.scroll, scroll);
        gl.uniform1f(U.intro, intro);
        gl.uniform2f(U.core, ccx * (W / window.innerWidth), H - ccy * (H / window.innerHeight));
        gl.uniform1f(U.coreK, cck);
        gl.drawArrays(gl.TRIANGLES, 0, 3);

        raf = requestAnimationFrame(frame);
    }

    if (reduce) {
        // a single still frame of the field — atmosphere without motion
        intro = 1;
        gl.uniform2f(U.res, W, H);
        gl.uniform1f(U.time, 14.0);
        gl.uniform2f(U.mouse, W * .7, H * .65);
        gl.uniform1f(U.scroll, 0);
        gl.uniform1f(U.intro, 1);
        gl.uniform2f(U.core, W * .72, H * .56);
        gl.uniform1f(U.coreK, 0.5);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        window.addEventListener('resize', function () {
            gl.uniform2f(U.res, W, H);
            gl.drawArrays(gl.TRIANGLES, 0, 3);
        });
        return;
    }

    raf = requestAnimationFrame(frame);
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) { cancelAnimationFrame(raf); raf = null; }
        else if (!raf) { last = performance.now(); raf = requestAnimationFrame(frame); }
    });
})();
