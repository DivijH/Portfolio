/* ElectionBench: sortable leaderboard + head-to-head explorer */
(function () {
    'use strict';

    var strip = function (m) { return (m && m.indexOf('cand_') === 0) ? m.slice(5) : m; };
    var fmtMargin = function (m) {
        return (m == null) ? '—' : (m > 0 ? '+' : '') + (m * 100).toFixed(1) + '%';
    };

    // ---- Sortable leaderboard -------------------------------------------
    var table = document.getElementById('eb-leaderboard');
    if (table && table.tHead) {
        var ths = table.tHead.rows[0].cells;
        var tbody = table.tBodies[0];
        var KEY = 'eb-sort';
        var cellVal = function (td) {
            var t = (td.textContent || '').trim();
            var n = parseFloat(t.replace('%', '').replace(/,/g, ''));
            return isNaN(n) ? t.toLowerCase() : n;
        };
        var sortBy = function (idx, dir, toggle) {
            var cur = ths[idx].getAttribute('data-dir');
            if (dir == null) dir = toggle ? (cur === 'asc' ? 'desc' : 'asc') : (cur || 'asc');
            var rows = Array.prototype.slice.call(tbody.rows);
            rows.sort(function (r1, r2) {
                var a = cellVal(r1.cells[idx]), b = cellVal(r2.cells[idx]);
                return a < b ? (dir === 'asc' ? -1 : 1) : a > b ? (dir === 'asc' ? 1 : -1) : 0;
            });
            rows.forEach(function (r) { tbody.appendChild(r); });
            Array.prototype.forEach.call(ths, function (t) { t.removeAttribute('data-dir'); });
            ths[idx].setAttribute('data-dir', dir);
            try { localStorage.setItem(KEY, idx + ':' + dir); } catch (e) {}
        };
        Array.prototype.forEach.call(ths, function (th, idx) {
            th.classList.add('eb-th-sort');
            th.addEventListener('click', function () { sortBy(idx, null, true); });
        });
        try {  // restore sort across the 10-min auto-refresh
            var s = (localStorage.getItem(KEY) || '').split(':');
            if (s.length === 2 && ths[+s[0]]) sortBy(+s[0], s[1], false);
        } catch (e) {}
    }

    // ---- Head-to-head explorer ------------------------------------------
    var selA = document.getElementById('eb-a'), selB = document.getElementById('eb-b');
    if (!selA || !selB) return;
    var models = [];
    try { models = JSON.parse(document.getElementById('eb-models').textContent) || []; } catch (e) {}
    models.slice().sort().forEach(function (m) {
        [selA, selB].forEach(function (sel) {
            var o = document.createElement('option');
            o.value = m; o.textContent = strip(m); sel.appendChild(o);
        });
    });
    if (models.length > 1) { selA.selectedIndex = 0; selB.selectedIndex = 1; }

    var h2hBox = document.getElementById('eb-h2h');
    var gameBox = document.getElementById('eb-game');
    var pre = document.getElementById('eb-transcript');
    var gameTitle = document.getElementById('eb-game-title');
    document.getElementById('eb-game-close').addEventListener('click', function () { gameBox.hidden = true; });

    function renderH2H(d) {
        if (!d.ok) { h2hBox.innerHTML = '<p class="eb-note">' + (d.error || 'error') + '</p>'; return; }
        var A = strip(d.a), B = strip(d.b);
        if (!d.n) { h2hBox.innerHTML = '<div class="empty-state">No recorded games between ' + A + ' and ' + B + '.</div>'; return; }
        var summary = '<div class="eb-h2h-summary">' +
            '<span class="eb-score"><strong>' + A + '</strong> ' + d.a_wins + ' – ' + d.b_wins + ' <strong>' + B + '</strong></span>' +
            '<span class="eb-h2h-meta">' + d.n + ' games · ' + A + ' win ' + d.a_win_pct + '%' +
            (d.draws ? ' · ' + d.draws + ' draw' + (d.draws > 1 ? 's' : '') : '') +
            ' · avg margin ' + fmtMargin(d.avg_margin_a) + ' toward ' + A + '</span></div>';
        var rows = d.games.map(function (g) {
            var w = g.winner === 'draw' ? 'draw' : strip(g.winner);
            return '<tr data-id="' + g.id + '" class="eb-game-row">' +
                '<td>' + g.seed + '/' + g.game_idx + '</td>' +
                '<td>' + w + '</td>' +
                '<td>' + fmtMargin(g.margin_a) + '</td>' +
                '<td>' + g.states_a + '–' + g.states_b + '</td>' +
                '<td class="eb-open">view →</td></tr>';
        }).join('');
        h2hBox.innerHTML = summary +
            '<div class="eb-table-wrap" style="margin-top:1rem"><table class="eb-table eb-games">' +
            '<thead><tr><th>Seed/mirror</th><th>Winner</th><th>Margin→' + A + '</th><th>States ' + A + '–' + B + '</th><th></th></tr></thead>' +
            '<tbody>' + rows + '</tbody></table></div>';
        Array.prototype.forEach.call(h2hBox.querySelectorAll('.eb-game-row'), function (tr) {
            tr.addEventListener('click', function () { openGame(tr.getAttribute('data-id')); });
        });
    }

    function openGame(id) {
        gameTitle.textContent = 'Loading transcript…';
        gameBox.hidden = false;
        pre.textContent = '';
        gameBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        fetch('/electionbench/game/' + id + '/', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (!d.ok) { pre.textContent = d.error || 'error'; return; }
                gameTitle.textContent = strip(d.model_a) + ' vs ' + strip(d.model_b) + ' · seed ' + d.seed +
                    ' · winner ' + (d.winner_model ? strip(d.winner_model) : 'draw');
                pre.textContent = d.transcript || '(no transcript)';
            })
            .catch(function () { pre.textContent = 'Failed to load.'; });
    }

    function fetchH2H() {
        var a = selA.value, b = selB.value;
        gameBox.hidden = true;
        if (!a || !b || a === b) { h2hBox.innerHTML = '<p class="eb-note">Pick two different models.</p>'; return; }
        h2hBox.innerHTML = '<p class="eb-note">Loading…</p>';
        fetch('/electionbench/h2h/?a=' + encodeURIComponent(a) + '&b=' + encodeURIComponent(b),
              { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(renderH2H)
            .catch(function () { h2hBox.innerHTML = '<p class="eb-note">Failed to load.</p>'; });
    }
    selA.addEventListener('change', fetchH2H);
    selB.addEventListener('change', fetchH2H);
    fetchH2H();
})();
