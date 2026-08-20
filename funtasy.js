/* FunTasy Liga - kozos megjelenito mag.
   Hasznalja: index.html (NB I Fantasy), draft.html (FPL Draft).

   Miert van kulon fajlban: a tabella, a matrix es a meccspanelek logikaja
   mindket oldalon ugyanaz volt, szo szerint lemasolva. Igy nem tudnak
   elcsuszni egymastol. Nincs build lepes - sima statikus fajl.

   A ket oldal adata azonos alaku:
     schedule = { "1": [[hazai, vendeg, hazai_pont, vendeg_pont], ...], ... }
   ahol a pont null, amig a meccs nincs lezarva. A resztvevok kulcsai
   tetszolegesek (az NB I-nel becenev, a Draftnal szam), a megjelenitendo
   nevet a hivo `label` fuggvenye adja.

   ELO EREDMENY: a `live` overlay ugyanilyen alaku, de a benne levo
   eredmenyek NEM szamitanak bele a tabellaba es a matrixba - csak a
   meccspanelen jelennek meg, "elo" jelolessel. Igy a meg le nem zart
   fordulo nem latszik veglegesnek. */
(function (global) {
  'use strict';

  var esc = function (s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  var fmt = function (x) {
    return (Math.round(x * 100) / 100).toLocaleString('hu-HU', { maximumFractionDigits: 2 });
  };
  var played = function (m) { return m && m[2] != null && m[3] != null; };

  function create(opts) {
    var el = function (id) { return document.getElementById(id); };
    var ids = opts.els || {};
    var label = opts.label || function (k) { return k; };

    var api = {
      rPast: opts.firstRound || 1,
      rNext: opts.firstRound || 1
    };

    // A fordulotartomany lehet fix szam vagy fuggveny - a Draftnal csak a
    // draft.json betoltese utan derul ki, hany fordulo van.
    var ertek = function (v, alap) {
      var x = (typeof v === 'function') ? v() : v;
      return x || alap;
    };
    var elso = function () { return ertek(opts.firstRound, 1); };
    var utolso = function () { return ertek(opts.lastRound, 1); };
    var kor = function () {
      var a = [];
      for (var r = elso(); r <= utolso(); r++) a.push(r);
      return a;
    };
    // A lezart fordulok meccsei - EZEKBOL szamol a tabella es a matrix.
    var vegleges = function (r) { return (opts.schedule && opts.schedule[r]) || []; };
    // Az elo overlay ugyanannak a fordulonak a meccseirol, ha van.
    var eloMeccs = function (r, i) {
      var L = opts.live && opts.live[r];
      return L && L[i] ? L[i] : null;
    };

    api.lastPlayedRound = function () {
      var r = 0;
      kor().forEach(function (i) { if (vegleges(i).some(played)) r = i; });
      return r || elso();
    };
    api.nextRound = function () {
      var l = api.lastPlayedRound();
      return Math.min(utolso(), vegleges(l).every(played) ? l + 1 : l);
    };

    // ---------- tabella ----------
    api.computeTable = function () {
      var T = {};
      (opts.entries() || []).forEach(function (n) {
        T[n] = { M: 0, GY: 0, D: 0, V: 0, RG: 0, KG: 0, form: [] };
      });
      kor().forEach(function (r) {
        vegleges(r).forEach(function (m) {
          if (!played(m)) return;
          var h = m[0], v = m[1], hp = m[2], vp = m[3];
          if (!T[h] || !T[v]) return;
          T[h].M++; T[v].M++;
          T[h].RG += hp; T[h].KG += vp; T[v].RG += vp; T[v].KG += hp;
          if (hp > vp) { T[h].GY++; T[v].V++; T[h].form.push('GY'); T[v].form.push('V'); }
          else if (vp > hp) { T[v].GY++; T[h].V++; T[v].form.push('GY'); T[h].form.push('V'); }
          else { T[h].D++; T[v].D++; T[h].form.push('D'); T[v].form.push('D'); }
        });
      });
      return Object.keys(T).map(function (n) {
        var s = T[n];
        return { name: n, M: s.M, GY: s.GY, D: s.D, V: s.V, RG: s.RG, KG: s.KG,
                 form: s.form, GK: s.RG - s.KG, Pont: s.GY * 3 + s.D };
      }).sort(function (a, b) {
        return b.Pont - a.Pont || b.GK - a.GK || b.RG - a.RG ||
               label(a.name).localeCompare(label(b.name), 'hu');
      });
    };

    api.renderTable = function () {
      var h = '<tr><th></th><th>' + esc(opts.nameHeader || 'Szakvezető') +
        '</th><th>M</th><th>GY</th><th>D</th><th>V</th><th>RG</th><th>KG</th>' +
        '<th>GK</th><th>Pont</th><th>Forma</th></tr>';
      api.computeTable().forEach(function (r, i) {
        var form = r.form.slice(-5).map(function (f) {
          return '<span class="dot ' + f + '"></span>';
        }).join('');
        var nev = esc(label(r.name));
        // A nev csak ott kattinthato, ahol van mit megnyitni (keret-modal).
        var cella = opts.nameAttr
          ? '<span class="clickable" ' + opts.nameAttr(r.name) + '>' + nev + '</span>'
          : nev;
        h += '<tr class="' + (i === 0 ? 'leader' : '') + '"><td class="rank">' + (i + 1) + '.</td>' +
          '<td class="name">' + cella + '</td>' +
          '<td>' + r.M + '</td><td>' + r.GY + '</td><td>' + r.D + '</td><td>' + r.V + '</td>' +
          '<td>' + fmt(r.RG) + '</td><td>' + fmt(r.KG) + '</td>' +
          '<td class="' + (r.GK >= 0 ? 'pos' : 'neg') + '">' + fmt(r.GK) + '</td>' +
          '<td class="pont">' + r.Pont + '</td>' +
          '<td style="text-align:left"><span class="form">' + form + '</span></td></tr>';
      });
      el(ids.table).innerHTML = h;
    };

    // ---------- meccspanelek ----------
    function fillSelect(sel) {
      if (sel.options.length) return;
      kor().forEach(function (r) {
        var o = document.createElement('option');
        o.value = r; o.textContent = r + '. forduló';
        sel.appendChild(o);
      });
    }
    api.renderMatches = function (which) {
      var r = which === 'past' ? api.rPast : api.rNext;
      var sel = el(which === 'past' ? ids.selPast : ids.selNext);
      fillSelect(sel); sel.value = r;
      var h = '';
      vegleges(r).forEach(function (m, i) {
        var hp = m[2], vp = m[3], p = played(m), elo = false;
        if (!p) {                       // nincs vegleges eredmeny -> nezzuk az elot
          var L = eloMeccs(r, i);
          if (played(L)) { hp = L[2]; vp = L[3]; elo = true; }
        }
        var van = p || elo;
        var attr = opts.matchAttr ? ' ' + opts.matchAttr(m[0], m[1]) : '';
        h += '<div class="match' + (elo ? ' elo' : '') + '"' + attr + '>' +
          '<div class="h ' + (van && hp > vp ? 'winner' : '') + '">' + esc(label(m[0])) + '</div>' +
          '<div class="score">' +
            (van ? fmt(hp) + ' <span style="color:var(--dim)">:</span> ' + fmt(vp) +
                   (elo ? '<span class="elojel">élő</span>' : '')
                 : '<span class="na">— : —</span>') +
          '</div>' +
          '<div class="v ' + (van && vp > hp ? 'winner' : '') + '">' + esc(label(m[1])) + '</div></div>';
      });
      el(which === 'past' ? ids.mPast : ids.mNext).innerHTML = h;
    };

    // ---------- mátrix ----------
    api.renderMatrix = function () {
      var names = opts.matrixOrder ? opts.matrixOrder()
                                   : api.computeTable().map(function (x) { return x.name; });
      var M = {};
      names.forEach(function (a) { M[a] = {}; names.forEach(function (b) { M[a][b] = [0, 0, 0]; }); });
      kor().forEach(function (r) {
        vegleges(r).forEach(function (m) {
          if (!played(m)) return;
          var h = m[0], v = m[1], hp = m[2], vp = m[3];
          if (!M[h] || !M[v]) return;
          if (hp > vp) { M[h][v][0]++; M[v][h][2]++; }
          else if (vp > hp) { M[v][h][0]++; M[h][v][2]++; }
          else { M[h][v][1]++; M[v][h][1]++; }
        });
      });
      var t = '<table><tr><th></th>' + names.map(function (n) {
        return '<th>' + esc(label(n).slice(0, 4)) + '</th>';
      }).join('') + '</tr>';
      names.forEach(function (a) {
        t += '<tr><th style="text-align:left">' + esc(label(a)) + '</th>';
        names.forEach(function (b) {
          if (a === b) { t += '<td class="x">—</td>'; return; }
          var c = M[a][b], n = c[0] + c[1] + c[2];
          t += '<td class="' + (n ? (c[0] > c[2] ? 'w' : (c[2] > c[0] ? 'l' : 'd')) : 'x') + '">' +
            (n ? c[0] + '/' + c[1] + '/' + c[2] : '·') + '</td>';
        });
        t += '</tr>';
      });
      el(ids.matrix).innerHTML = t + '</table>';
    };

    // ---------- navigáció ----------
    api.nav = function (which, d) {
      if (which === 'past') api.rPast = Math.min(utolso(), Math.max(elso(), api.rPast + d));
      else api.rNext = Math.min(utolso(), Math.max(elso(), api.rNext + d));
      api.renderMatches(which);
    };
    api.setRound = function (which, r) {
      if (which === 'past') api.rPast = r; else api.rNext = r;
      api.renderMatches(which);
    };
    api.renderAll = function () {
      api.renderTable(); api.renderMatrix();
      api.renderMatches('past'); api.renderMatches('next');
    };
    // A ‹ › gombokat es a fordulovalasztot mindket oldal ugyanugy hasznalja.
    api.bindNav = function () {
      document.addEventListener('click', function (e) {
        var b = e.target.closest('[data-nav]');
        if (b) api.nav(b.dataset.nav, +b.dataset.d);
      });
      document.addEventListener('change', function (e) {
        if (e.target.id === ids.selPast) api.setRound('past', +e.target.value);
        if (e.target.id === ids.selNext) api.setRound('next', +e.target.value);
      });
    };
    return api;
  }

  global.FunTasy = { create: create, esc: esc, fmt: fmt, played: played };
})(window);
