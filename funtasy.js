/* FunTasy Liga - the shared rendering core.
   Used by: nb1/index.html (NB I Fantasy), pl/index.html (FPL Draft) and the
   home page (index.html, league picker).

   Why it is a separate file: the table, matrix and match panel logic was
   the same on both pages, copied word for word. Here they cannot drift
   apart. There is no build step - it is a plain static file.

   Both pages hand over data of the same shape:
     schedule = { "1": [[home, away, home_points, away_points], ...], ... }
   where the points are null until the match is closed. The participant
   keys are arbitrary (a nickname on NB1, a number on PL); the display is
   set by the caller's options: `label` (name), `tag` (monogram after the
   name), `matrixLabel` (the matrix axes), `tiebreak` ('rg' = points scored
   decide a tie, the point difference by default),
   `onMatrixClick(a,b)` (a click on a matrix cell - the caller opens its
   own modal on it, typically with the output of h2hHTML(a,b)).

   LIVE RESULT: the `live` overlay has the same shape, but its results do
   NOT count in the table or the matrix - they only appear on the match
   panel, marked "live". That way a round that is not closed yet never
   looks final.

   Besides create, two namespace-level helpers are exported for the points
   breakdown accordion (FunTasy.accToggle, FunTasy.accTable) - details at
   the end of the file. */
(function (global) {
  'use strict';

  /* ===== LEAGUES - the ONLY place to extend =====
     Adding a league: one new entry here + one new folder with its own
     index.html. The league switcher bar (at the top of every league page)
     and the home page cards are built from this list too, so nothing else
     needs touching. `path` is relative to the site root; `theme` is the
     class put on the body (the league themes in funtasy.css). */
  /* `type` is the league's GAME MODE, not a label: it decides which rules
     the league runs by, and the pages can handle it separately on that
     basis (the body gets a `tipus-<value>` class, and from JS it can be read
     as FunTasy.leagueById(id).type).
       salary-cap - shared player market with a budget; the same player can
                    be in several teams; there is a captain and bench halving
       draft      - exclusive ownership (one player in one team);
                    no captain, bench points do not count */
  /* `livePoints` says whether the league's source gives points DURING A
     MATCH already, or only at its end. Not cosmetic: it decides what may be
     said about a player on 0 points during the match.
       true  (FPL) - points come minute by minute, so 0 means there has been
                     no scoring event so far
       false (MLSZ) - points only arrive after the match, so a 0 during the
                     match means nothing; it must not be phrased as if the
                     player had scored nothing "so far" */
  var LEAGUES = [
    { id: 'nb1', name: 'NB1', path: 'nb1/', title: 'NB1 salary cap fantasy',
      description: 'privát head-to-head · 8 csapat · 33 forduló', teams: 8,
      type: 'salary-cap', typeName: 'Salary cap', theme: 'liga-nb1',
      livePoints: false,
      /* The MLSZ writes MIDNIGHT when the exact kick-off is not set yet. It
         is not a real time: printing it with a clock time would be false. The
         FPL gives no time at all in that case, so there midnight would be a
         real hour - which is why this is a league trait, not a general rule. */
      midnightPlaceholder: true },
    { id: 'pl', name: 'PL', path: 'pl/', title: 'PL draft fantasy',
      description: 'privát head-to-head · 10 csapat · 38 forduló', teams: 10,
      type: 'draft', typeName: 'Draft', theme: 'liga-pl',
      livePoints: true, midnightPlaceholder: false }
  ];
  /* Kick-off time in human form. BOTH leagues use this: there used to be
     two versions, and the second misbehaved at the edges - it printed
     "Invalid Date" for an empty or bad value and a made-up date
     ("jan. 1. 00:00") for null. What we do not understand is returned
     unchanged: a raw timestamp on the page is awkward, a made-up date is a
     lie.

     The league decides the midnight handling (`midnightPlaceholder`),
     because that is the MLSZ's marking for an unscheduled match. The date
     is read from the TEXT, not from a Date: in another time zone midnight
     would slip into the previous day. */
  function formatKickoff(s, leagueId) {
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(s || '');
    if (!m) return s == null ? '' : String(s);
    var l = leagueById(leagueId);
    if (l && l.midnightPlaceholder && m[4] === '00' && m[5] === '00')
      return new Date(+m[1], +m[2] - 1, +m[3])
               .toLocaleDateString('hu-HU', { month: 'short', day: 'numeric' })
             + ' (időpont még nincs kitűzve)';
    var d = new Date(s);
    if (isNaN(d.getTime())) return String(s);
    return d.toLocaleDateString('hu-HU', { month: 'short', day: 'numeric' }) + ' '
         + d.toLocaleTimeString('hu-HU', { hour: '2-digit', minute: '2-digit' });
  }

  function leagueById(id) {
    for (var i = 0; i < LEAGUES.length; i++) if (LEAGUES[i].id === id) return LEAGUES[i];
    return null;
  }

  /* ===== PEOPLE - the same person under two league names =====
     The two leagues know the same person by different names: a nickname
     in NB1 (the MLSZ user name), a team name in PL. Where the two leagues
     meet on one page, this offered them twice, as two separate managers -
     yet it is one person. Who is who is kept here, in ONE place.

     The PL side is linked by ID (the league_entry "id", NOT the FPL
     "entry_id"): the owner can rename the team at any time, the ID stays -
     the name is read from the entries list of draft.json. Someone who plays
     in only one league has no row: they appear under one name, there is
     nothing to link. */
  var PEOPLE = [
    { nb1: 'Ádám',   pl: 254960 },
    { nb1: 'Bazsa',  pl: 267607 },
    { nb1: 'Bence',  pl: 254810 },
    { nb1: 'Csendi', pl: 267857 },
    { nb1: 'Csongi', pl: 277905 },
    { nb1: 'Katyul', pl: 267429 },
    { nb1: 'Vince',  pl: 268988 }
  ];

  /* From name to person. `plNames` is the `entries` array of draft.json
     ({id, name}); without it - or until it arrives - everyone keeps their
     own name, the page still works, it just does not merge the two leagues.
     The returned function gives a person for every name: someone we do not
     know is themselves, under their own name. `key` is the identity: two
     names are the same person when their keys match. */
  function personLookup(plNames) {
    var nameById = {}, byName = {};
    (plNames || []).forEach(function (e) {
      if (e && e.id != null && e.name) nameById[e.id] = e.name;
    });
    PEOPLE.forEach(function (entry) {
      var plName = nameById[entry.pl];
      if (!plName) return;
      var person = { key: 'sz' + entry.pl, names: [entry.nb1, plName],
                    label: entry.nb1 + ' · ' + plName };
      byName[entry.nb1] = person;
      byName[plName] = person;
    });
    return function (name) {
      return byName[name] ||
             { key: 'n:' + name, names: [name], label: String(name) };
    };
  }

  // The magazine's name and motto live in ONE place: the header, the top
  // bar and the footer must show the same words.
  var MAGAZINE_NAME = 'Nemzethy Sport';
  var MAGAZINE_MOTTO = 'Heti Funtasy Magazin';

  /* ===== SHARED MESSAGES =====
     The same situation gets the same sentence in both leagues. They used to
     exist in two copies, and had already started to drift: the two pages
     ended the during-the-match sentence differently about the same thing.
     A sentence that DIFFERS by league (because the rule differs) is a
     function that asks the league - the page does not decide it locally. */
  var MESSAGES = {
    didNotPlay: 'Nem lépett pályára ebben a fordulóban.',
    noScoringEvent: 'Lejátszotta a meccset, pontot érő esemény nélkül.',
    noChange: 'Nem történt változás ebben a fordulóban.',
    /* During a match a 0 does not mean the same everywhere: the FPL gives
       points minute by minute (livePoints), so there a 0 really means there
       has been no scoring event so far. The MLSZ records the points AFTER the
       match, so claiming that there would be a lie. */
    duringMatch: function (leagueId) {
      return (leagueById(leagueId) || {}).livePoints
        ? 'A meccs zajlik — eddig nincs pontot érő eseménye.'
        : 'A meccs zajlik — a pontok csak a meccs végén kerülnek be.';
    }
  };

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
    // Monogram after the name (e.g. "Vince VS", "HolVanSalah?! VS") - this is
    // the participant's unique identifier, the same for the person in both leagues.
    var tag = opts.tag || function () { return ''; };
    var tagHTML = function (k) {
      var t = tag(k);
      return t ? ' <span class="mgr">' + esc(t) + '</span>' : '';
    };
    /* Name + monogram on one line. The NAME gets the ellipsis (.nv shrinks),
       the monogram never does: cutting at the end of the line would eat
       exactly the monogram - and in a narrow space that is what identifies
       the team.
       `wrap`: whether the name gets a clickable wrapper around it. */
    var nameTagHTML = function (k, wrap) {
      var nameHtml = '<span class="nv">' + esc(label(k)) + '</span>';
      return (wrap ? wrap(nameHtml) : nameHtml) + tagHTML(k);
    };

    var api = {
      rPast: opts.firstRound || 1,
      rNext: opts.firstRound || 1
    };

    // The round range can be a fixed number or a function - for the Draft the
    // number of rounds is only known after draft.json has loaded.
    var pick = function (v, fallback) {
      var x = (typeof v === 'function') ? v() : v;
      return x || fallback;
    };
    var first = function () { return pick(opts.firstRound, 1); };
    var last = function () { return pick(opts.lastRound, 1); };
    var roundList = function () {
      var a = [];
      for (var r = first(); r <= last(); r++) a.push(r);
      return a;
    };
    // The matches of the closed rounds - the table and the matrix count FROM THESE.
    var finalMatches = function (r) { return (opts.schedule && opts.schedule[r]) || []; };
    // The live overlay for the same round's matches, if there is one.
    var liveMatch = function (r, i) {
      var L = opts.live && opts.live[r];
      return L && L[i] ? L[i] : null;
    };

    api.lastPlayedRound = function () {
      var r = 0;
      roundList().forEach(function (i) { if (finalMatches(i).some(played)) r = i; });
      return r || first();
    };
    api.nextRound = function () {
      var l = api.lastPlayedRound();
      return Math.min(last(), finalMatches(l).every(played) ? l + 1 : l);
    };

    // ---------- table ----------
    api.computeTable = function () {
      var T = {};
      (opts.entries() || []).forEach(function (n) {
        T[n] = { M: 0, GY: 0, D: 0, V: 0, RG: 0, KG: 0, form: [] };
      });
      roundList().forEach(function (r) {
        finalMatches(r).forEach(function (m) {
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
        // Tiebreak: on NB1 the point difference (KÜL) decides, then points
        // scored (SP); on PL, following the FPL's base scoring, points scored
        // come first (tiebreak: 'rg').
        var t = (opts.tiebreak === 'rg')
          ? (b.Pont - a.Pont || b.RG - a.RG || b.GK - a.GK)
          : (b.Pont - a.Pont || b.GK - a.GK || b.RG - a.RG);
        return t || label(a.name).localeCompare(label(b.name), 'hu');
      });
    };

    // Line-up efficiency summed per team over the rounds of the CLOSED
    // matches - from the same range the table counts from, so the two cannot
    // drift apart (a live/provisional round counts in neither).
    function lineupTotals() {
      if (!opts.lineup) return null;
      var t = {};
      roundList().forEach(function (r) {
        finalMatches(r).forEach(function (m) {
          if (!played(m)) return;
          [m[0], m[1]].forEach(function (n) {
            var v = opts.lineup(n, r);
            if (!v) return;
            var c = t[n] || (t[n] = { sz: 0, le: 0 });
            c.sz += v.sz; c.le += v.le;
          });
        });
      });
      return t;
    }

    // The cumulative Guardiola measure over the SAME range the table counts
    // from - so the two numbers cannot drift apart (a live/provisional round
    // counts in neither). The first round has no value by definition.
    function guardTotals() {
      if (!opts.guard) return null;
      var t = {};
      roundList().forEach(function (r) {
        finalMatches(r).forEach(function (m) {
          if (!played(m)) return;
          [m[0], m[1]].forEach(function (n) {
            var v = opts.guard(n, r);
            if (!v) return;
            t[n] = (t[n] || 0) + v.guard;
          });
        });
      });
      return t;
    }

    api.renderTable = function () {
      var rows = api.computeTable();
      /* Until the data arrives, the table stands with as many empty rows as
         there are teams: otherwise the whole page jumps down when the rows
         arrive (clearly visible on a phone while loading). */
      // NB1 knows its managers and pairings before any result, so its rows
      // would read as a real table of zeros: a page tells through `ready`
      // whether its data has arrived.
      var noData = !rows.length || (opts.ready ? !opts.ready()
                                               : !Object.keys(opts.schedule || {}).length);
      if (noData && opts.placeholderRows) {
        var empty = '<tr><th></th><th>' + esc(opts.nameHeader || 'Szakvezető') + '</th>' +
          '<th>M</th><th>GY</th><th>D</th><th>V</th><th>SP</th><th>KP</th>' +
          '<th>KÜL</th><th>Pont</th><th>Forma</th></tr>';
        for (var u = 0; u < opts.placeholderRows; u++)
          empty += '<tr class="placeholder"><td class="rank">' + (u + 1) + '.</td>' +
            // the same inner structure as a real name cell, so the row is
            // exactly as tall as the one that replaces it
            '<td class="name"><span class="nevsor"><span class="nv">&nbsp;</span>' +
            ' <span class="mgr">&nbsp;</span></span></td>' +
            new Array(8).join('<td>&nbsp;</td>') + '<td class="pont">&nbsp;</td>' +
            '<td><span class="form"><span class="dot"></span></span></td></tr>';
        el(ids.table).innerHTML = empty;
        return;
      }
      var lineup = lineupTotals(), guard = guardTotals();
      var h = '<tr><th></th><th>' + esc(opts.nameHeader || 'Szakvezető') +
        '</th><th>M</th><th>GY</th><th>D</th><th>V</th>' +
        '<th title="szerzett pont">SP</th><th title="kapott pont">KP</th>' +
        '<th title="pontkülönbség">KÜL</th><th>Pont</th>' +
        (lineup ? '<th title="' + LINEUP_TITLE + '">KEZD%</th>' : '') +
        (guard ? '<th title="' + esc(GUARD_TITLE) + '">GUA</th>' : '') +
        '<th>Forma</th></tr>';
      rows.forEach(function (r, i) {
        var form = r.form.slice(-5).map(function (f) {
          return '<span class="dot ' + f + '"></span>';
        }).join('');
        // The name is only clickable where there is something to open (squad modal).
        var nameCell = nameTagHTML(r.name, opts.nameAttr && function (inner) {
          return '<span class="clickable" ' + opts.nameAttr(r.name) + '>' + inner + '</span>';
        });
        h += '<tr class="' + (i === 0 ? 'leader' : '') + '"><td class="rank">' + (i + 1) + '.</td>' +
          '<td class="name"><span class="nevsor">' + nameCell + '</span></td>' +
          '<td>' + r.M + '</td><td>' + r.GY + '</td><td>' + r.D + '</td><td>' + r.V + '</td>' +
          '<td>' + fmt(r.RG) + '</td><td>' + fmt(r.KG) + '</td>' +
          '<td class="' + (r.GK >= 0 ? 'pos' : 'neg') + '">' + fmt(r.GK) + '</td>' +
          '<td class="pont">' + r.Pont + '</td>' +
          (lineup ? (function () {
            var v = lineup[r.name], pc = v ? lineupPercent(v.sz, v.le) : null;
            return '<td class="kezdpc" title="' + (v ? fmt(v.sz) + ' / ' + fmt(v.le) + ' pont' : '') +
                   '">' + (pc == null ? '–' : pc + '%') + '</td>';
          })() : '') +
          (guard ? (function () {
            var g = guard[r.name];
            return '<td class="guard ' + (g == null ? '' : (g > 0 ? 'pos' : g < 0 ? 'neg' : '')) +
                   '" title="' + esc(GUARD_TITLE) + '">' +
                   (g == null ? '–' : signed(g)) + '</td>';
          })() : '') +
          '<td style="text-align:left"><span class="form">' + form + '</span></td></tr>';
      });
      el(ids.table).innerHTML = h;
    };

    // ---------- match panels ----------
    function fillSelect(sel) {
      if (sel.options.length) return;
      roundList().forEach(function (r) {
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
      finalMatches(r).forEach(function (m, i) {
        var hp = m[2], vp = m[3], p = played(m), live = false;
        if (!p) {                       // no final result -> look at the live one
          var L = liveMatch(r, i);
          if (played(L)) { hp = L[2]; vp = L[3]; live = true; }
        }
        var hasScore = p || live;
        var attr = opts.matchAttr ? ' ' + opts.matchAttr(m[0], m[1], r) : '';
        h += '<div class="match' + (live ? ' elo' : '') + '"' + attr + '>' +
          '<div class="h ' + (hasScore && hp > vp ? 'winner' : '') + '">' + nameTagHTML(m[0]) + '</div>' +
          '<div class="score">' +
            (hasScore ? fmt(hp) + ' <span style="color:var(--dim)">:</span> ' + fmt(vp) +
                   (live ? '<span class="elojel">élő</span>' : '')
                 : '<span class="na">— : —</span>') +
          '</div>' +
          '<div class="v ' + (hasScore && vp > hp ? 'winner' : '') + '">' + nameTagHTML(m[1]) + '</div></div>';
      });
      el(which === 'past' ? ids.mPast : ids.mNext).innerHTML = h;
    };

    // ---------- matrix ----------
    api.renderMatrix = function () {
      var names = opts.matrixOrder ? opts.matrixOrder()
                                   : api.computeTable().map(function (x) { return x.name; });
      var M = {};
      names.forEach(function (a) { M[a] = {}; names.forEach(function (b) { M[a][b] = [0, 0, 0]; }); });
      roundList().forEach(function (r) {
        finalMatches(r).forEach(function (m) {
          if (!played(m)) return;
          var h = m[0], v = m[1], hp = m[2], vp = m[3];
          if (!M[h] || !M[v]) return;
          if (hp > vp) { M[h][v][0]++; M[v][h][2]++; }
          else if (vp > hp) { M[v][h][0]++; M[h][v][2]++; }
          else { M[h][v][1]++; M[v][h][1]++; }
        });
      });
      // matrixLabel: if given (e.g. monogram), it goes on BOTH axes;
      // otherwise the start of the name for columns, the full name for rows.
      var axisLabel = function (n, isRow) {
        if (opts.matrixLabel) return opts.matrixLabel(n);
        return isRow ? label(n) : label(n).slice(0, 4);
      };
      var t = '<table><tr><th></th>' + names.map(function (n) {
        return '<th>' + esc(axisLabel(n, false)) + '</th>';
      }).join('') + '</tr>';
      names.forEach(function (a) {
        t += '<tr><th style="text-align:left">' + esc(axisLabel(a, true)) + '</th>';
        names.forEach(function (b) {
          if (a === b) { t += '<td class="x">—</td>'; return; }
          var c = M[a][b], n = c[0] + c[1] + c[2];
          // the whole cell is clickable: it opens the list of the two teams'
          // matches against each other (opts.onMatrixClick)
          t += '<td class="mx ' + (n ? (c[0] > c[2] ? 'w' : (c[2] > c[0] ? 'l' : 'd')) : 'x') + '"' +
            ' data-mxa="' + esc(a) + '" data-mxb="' + esc(b) + '"' +
            ' title="' + esc(label(a)) + ' vs ' + esc(label(b)) + '">' +
            (n ? c[0] + '/' + c[1] + '/' + c[2] : '·') + '</td>';
        });
        t += '</tr>';
      });
      el(ids.matrix).innerHTML = t + '</table>';
    };

    // ---------- head-to-head list ----------
    // Every pairing of the two teams from the schedule: played matches with
    // the score and W/D/L (GY/D/V, from "a"'s point of view), a live match
    // marked live, future ones with "— : —". The rows get data-mh/mv/mr
    // attributes: a click opens the match view inside the modal (with a back
    // button), each page with its own handler.
    // small grey % next to the h2h points - not for a live match, that still changes
    function lineupBadge(n, r, live) {
      if (!opts.lineup || live) return '';
      var v = opts.lineup(n, r), pc = v && lineupPercent(v.sz, v.le);
      return pc == null ? ''
        : ' <span class="kezdjel" title="' + LINEUP_TITLE + ': ' +
          fmt(v.sz) + ' / ' + fmt(v.le) + ' pont">' + pc + '%</span>';
    }

    // the same for the Guardiola measure. Not shown for a live match: the
    // round's breakdown does not exist yet, so neither does a value.
    function guardBadge(n, r, live) {
      if (!opts.guard || live) return '';
      var v = opts.guard(n, r);
      return !v ? '' : ' <span class="guardjel ' + (v.guard > 0 ? 'pos' : v.guard < 0 ? 'neg' : '')
        + '" title="' + esc(GUARD_TITLE) + ' (a múlt heti kerettel ' + fmt(v.alt) + ')">'
        + signed(v.guard) + '</span>';
    }

    /* Whether a manager has a Guardiola value in a round - decided in ONE PLACE.

       The condition is not trivial: the LIVE round and one not closed yet
       have NO value (a measure computed from a partial in-round result would
       be false, and the table does not count it either). THREE places use
       this condition - the column on the Rounds tab and the "Changes" tab of
       both leagues - and if any of them decided differently, the same round
       would show in one place and not in the other. That exact thing
       happened: PL round 2 was still empty on the Rounds tab while the
       Changes tab already showed a number. */
    api.guardValue = function (name, r) {
      if (!opts.guard) return null;
      var out = null;
      finalMatches(r).forEach(function (m, i) {
        var own;
        if (m[0] === name) own = m[2];
        else if (m[1] === name) own = m[3];
        else return;
        var live = false;
        if (own == null) {
          var L = liveMatch(r, i);
          if (played(L)) { live = true; own = m[0] === name ? L[2] : L[3]; }
        }
        out = (!live && own != null) ? opts.guard(name, r) : null;
      });
      return out;
    };

    /* A manager's results round by round (the "Rounds" tab) - SHARED by PL
       and NB1, which would otherwise keep two almost identical copies.
       Clicking a row opens the match (data-mh/mv/mr, as in the h2h). */
    api.roundsHTML = function (name) {
      var h = '<table><tr><th>F</th><th>Ellenfél</th><th>Pont</th><th>Ell.</th>' +
        (opts.lineup ? '<th title="' + esc(LINEUP_TITLE) + '">KEZD%</th>' : '') +
        (opts.guard ? '<th title="' + esc(GUARD_TITLE) + '">GUARD</th>' : '') +
        '<th>Eredm.</th></tr>';
      var gy = 0, d = 0, v = 0;
      roundList().forEach(function (r) {
        finalMatches(r).forEach(function (m, i) {
          var opp, own, ov, live = false;
          if (m[0] === name) { opp = m[1]; own = m[2]; ov = m[3]; }
          else if (m[1] === name) { opp = m[0]; own = m[3]; ov = m[2]; }
          else return;
          // the current round's score is in the live layer, not in the schedule
          if (own == null) {
            var L = liveMatch(r, i);
            if (played(L)) { live = true; own = m[0] === name ? L[2] : L[3]; ov = m[0] === name ? L[3] : L[2]; }
          }
          var res = '—', cls = '';
          if (own != null && ov != null) {
            if (own > ov) { res = 'GY'; cls = 'pos'; }
            else if (own < ov) { res = 'V'; cls = 'neg'; }
            else res = 'D';
            if (!live) { if (res === 'GY') gy++; else if (res === 'V') v++; else d++; }
          }
          var lineupCell = '';
          if (opts.lineup) {
            var pc = null;
            if (!live && own != null) {
              var kv = opts.lineup(name, r);
              pc = kv && lineupPercent(kv.sz, kv.le);
            }
            lineupCell = '<td class="kezdpc">' +
              (live || own == null ? '' : (pc == null ? '—' : pc + '%')) + '</td>';
          }
          var guardCell = '';
          if (opts.guard) {
            // the same condition as on the Changes tab - see guardValue
            var gv = api.guardValue(name, r);
            guardCell = '<td class="guard ' +
              (gv ? (gv.guard > 0 ? 'pos' : gv.guard < 0 ? 'neg' : '') : '') + '">' +
              (gv ? signed(gv.guard) : (live || own == null ? '' : '—')) + '</td>';
          }
          h += '<tr class="clickable" data-mh="' + esc(m[0]) + '" data-mv="' + esc(m[1]) +
            '" data-mr="' + r + '"><td class="rank">' + r + '.</td>' +
            '<td class="name"><span class="nevsor">' + esc(label(opp)) + '</span></td>' +
            '<td>' + (own != null ? fmt(own) : '—') + '</td>' +
            '<td>' + (ov != null ? fmt(ov) : '—') + '</td>' + lineupCell + guardCell +
            '<td class="' + cls + '">' + res +
            (live ? '<span class="elojel">élő</span>' : '') + '</td></tr>';
        });
      });
      return '<div style="font-size:13px;color:var(--dim);margin-bottom:8px">Mérleg: <b class="pos">' +
        gy + ' GY</b> · ' + d + ' D · <b class="neg">' + v + ' V</b> — ' + (gy * 3 + d) +
        ' pont</div>' + h + '</table>';
    };

    api.h2hHTML = function (a, b) {
      var rows = '', gy = 0, d = 0, v = 0, playedCount = 0;
      roundList().forEach(function (r) {
        finalMatches(r).forEach(function (m, i) {
          var aHome = (m[0] === a && m[1] === b), bHome = (m[0] === b && m[1] === a);
          if (!aHome && !bHome) return;
          var ap = aHome ? m[2] : m[3], bp = aHome ? m[3] : m[2];
          var live = false;
          if (ap == null) {
            var L = liveMatch(r, i);
            if (played(L)) { ap = aHome ? L[2] : L[3]; bp = aHome ? L[3] : L[2]; live = true; }
          }
          var res = '—', cls = '';
          if (ap != null && !live) {
            playedCount++;
            if (ap > bp) { res = 'GY'; cls = 'pos'; gy++; }
            else if (ap < bp) { res = 'V'; cls = 'neg'; v++; }
            else { res = 'D'; d++; }
          }
          rows += '<tr class="clickable" data-mh="' + esc(m[0]) + '" data-mv="' + esc(m[1]) +
            '" data-mr="' + r + '"><td class="rank">' + r + '.</td>' +
            '<td>' + (ap != null ? fmt(ap) : '—') + lineupBadge(a, r, live) + guardBadge(a, r, live) +
            (live ? ' <span class="elojel">élő</span>' : '') + '</td>' +
            '<td>' + (bp != null ? fmt(bp) : '—') + lineupBadge(b, r, live) + guardBadge(b, r, live) + '</td>' +
            '<td class="' + cls + '">' + (live ? 'élő' : res) + '</td></tr>';
        });
      });
      var record = playedCount
        ? '<div style="font-size:13px;color:var(--dim);margin-bottom:8px">' +
          esc(label(a)) + ' mérlege ' + esc(label(b)) + ' ellen: <b class="pos">' + gy +
          ' GY</b> · ' + d + ' D · <b class="neg">' + v + ' V</b></div>'
        : '<div style="font-size:13px;color:var(--dim);margin-bottom:8px">Még nem játszottak egymással.</div>';
      // the shared CSS aligns the 2nd header column left (as a name column),
      // but here numbers stand under it, aligned right - needs inline alignment
      return record + '<table><tr><th>F</th><th style="text-align:right">' + esc(label(a)) +
        '</th><th style="text-align:right">' + esc(label(b)) +
        '</th><th>Eredm.</th></tr>' + rows + '</table>';
    };

    // ---------- navigation ----------
    api.nav = function (which, d) {
      if (which === 'past') api.rPast = Math.min(last(), Math.max(first(), api.rPast + d));
      else api.rNext = Math.min(last(), Math.max(first(), api.rNext + d));
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
    // Both pages use the ‹ › buttons and the round selector the same way.
    api.bindNav = function () {
      document.addEventListener('click', function (e) {
        var b = e.target.closest('[data-nav]');
        if (b) { api.nav(b.dataset.nav, +b.dataset.d); return; }
        var mx = e.target.closest('.matrix td.mx');
        if (mx && opts.onMatrixClick) opts.onMatrixClick(mx.dataset.mxa, mx.dataset.mxb);
      });
      document.addEventListener('change', function (e) {
        if (e.target.id === ids.selPast) api.setRound('past', +e.target.value);
        if (e.target.id === ids.selNext) api.setRound('next', +e.target.value);
      });
    };
    return api;
  }

  /* POINTS BREAKDOWN ACCORDION - shared mechanics for both pages.
     Clicking a player row in a squad view (.plr[data-acc]) opens a panel
     under the row that shows what the player's weekly points were made of.
     The content depends on the page (NB1 uses the MLSZ game-player-stats
     endpoint, PL the explain field of the FPL event/{gw}/live), so the
     caller passes an async `load` function that returns the finished HTML.
     Only the behaviour is shared here: one panel can be open at a time, a
     second click closes it, a click on another row moves it there. */
  function accToggle(row, load) {
    var wasOpen = row.classList.contains('open');
    document.querySelectorAll('.accpanel').forEach(function (x) { x.remove(); });
    document.querySelectorAll('.plr.open').forEach(function (x) { x.classList.remove('open'); });
    if (wasOpen) return;
    row.classList.add('open');
    var p = document.createElement('div');
    p.className = 'accpanel';
    // The panel's STATE is kept in a flag, not guessed from its text:
    // redrawing (accPreserve) decides from it whether to keep the panel. Only
    // a 'kesz' (done) panel may be put back unchanged.
    p.dataset.allapot = 'tolt';
    p.innerHTML = '<div class="accload">Bontás betöltése…</div>';
    row.insertAdjacentElement('afterend', p);
    Promise.resolve().then(load).then(function (html) {
      if (!row.classList.contains('open') || !p.isConnected) return;
      p.dataset.allapot = html ? 'kesz' : 'hiba';
      p.innerHTML = html || '<div class="accload">A pontok bontása nem érhető el ehhez a játékoshoz.</div>';
    }, function (err) {
      if (!row.classList.contains('open') || !p.isConnected) return;
      p.dataset.allapot = 'hiba';
      // The REASON is shown too. The fetcher (FunTasy.makeFetcher) tries all
      // three routes - direct, corsproxy, allorigins - and writes into the error
      // message which one failed and why ("corsproxy:HTTP 429",
      // "direkt:CORS", "allorigins:időtúllépés"). Without it the user and the
      // developer only see "it failed", and there is no telling whether it is
      // the network, the proxy, or a change in the API.
      var why = err && err.message ? String(err.message) : '';
      p.innerHTML = '<div class="accload">A bontás lekérése nem sikerült.'
        + (why ? '<br><span class="accmiert">' + esc(why) + '</span>' : '') + '</div>';
    });
  }

  /* Breakdown table: rows = [{name, value, points}]. points can be a number
     or ready text (e.g. "×2" for the captain). The caller filters out the
     0-point rows - the MLSZ's own interface also shows only scoring events.
     If there is not a single scoring row, the `emptyText` is shown: the
     caller works it out, because on each page the reason comes from
     different data (the match has not started / is under way / played
     without points / did not take the field). */
  /* A row can carry a state flag: `jelzes` is the suffix of its colour
     class (e.g. "valtozik" -> b-valtozik), `megjegyzes` a short text next
     to the name. The PL page's bonus row uses it: the FPL computes the
     bonus during the match too and only finalises it later. Colour alone
     is not understandable, so a text always comes with it. */
  /* Redrawing while keeping the OPEN breakdown.

     The match and squad views update after the first draw: the
     minute-fresh squad, the minutes played and the live points arrive -
     each time the whole content of #mBody is rebuilt, and the open
     accordion vanished from under the user. To them it looked as if it had
     closed by itself after "Bontás betöltése…", and they had to open it
     again.

     The row is identified by a key built from its data-* flags (sorted, so
     the order does not matter), and the panel's content is put back
     unchanged - so there is no flicker and no new request. */
  function accKey(el) {
    var d = el.dataset, k = [], x;
    for (x in d) k.push(x + '=' + d[x]);
    return k.sort().join('|');
  }
  function accPreserve(draw) {
    var openRow = document.querySelector('.plr.open[data-acc]');
    var panel = openRow && openRow.nextElementSibling;
    if (panel && !panel.classList.contains('accpanel')) panel = null;
    var key = openRow ? accKey(openRow) : null;
    var state = panel ? panel.dataset.allapot : null;
    var html = (state === 'kesz') ? panel.innerHTML : null;
    draw();
    if (key == null) return;
    var rows = document.querySelectorAll('.plr[data-acc]'), i;
    for (i = 0; i < rows.length; i++) {
      if (accKey(rows[i]) !== key) continue;
      // DONE content: can be put back unchanged - no flicker, no new request.
      if (html != null) {
        rows[i].classList.add('open');
        var fresh = document.createElement('div');
        fresh.className = 'accpanel';
        fresh.dataset.allapot = 'kesz';
        fresh.innerHTML = html;
        rows[i].insertAdjacentElement('afterend', fresh);
        return;
      }
      // STILL LOADING: the old request finishes on the stale row, so it has to be started again.
      if (state === 'tolt') { rows[i].click(); return; }
      // ERROR: NOT kept. A transient error would otherwise get stuck and the
      // row would stay open - the next click would close it instead of retrying
      // ("a pontok bontása nem érhető el" / "a bontás lekérése nem sikerült"
      // would stay on screen).
      return;
    }
  }

  function accTable(rows, emptyText) {
    if (!rows || !rows.length)
      return '<div class="accload">' + esc(emptyText || 'Ehhez a fordulóhoz nincs rögzített esemény.') + '</div>';
    var h = '<table class="acctable"><tr><th>Esemény</th><th>Érték</th><th>Pont</th></tr>';
    for (var i = 0; i < rows.length; i++) {
      var s = rows[i];
      var isNum = (typeof s.points === 'number');
      var cls = isNum ? (s.points > 0 ? 'pos' : (s.points < 0 ? 'neg' : '')) : '';
      var flagCls = s.jelzes ? ' b-' + s.jelzes : '';
      if (flagCls) cls += flagCls;
      var note = s.megjegyzes
        ? ' <span class="sormegj' + flagCls + '">(' + esc(s.megjegyzes) + ')</span>' : '';
      h += '<tr><td class="ev">' + esc(s.name) + note + '</td>' +
           '<td>' + (s.value == null || s.value === '' ? '' :
                     (typeof s.value === 'number' ? fmt(s.value) : esc(String(s.value)))) + '</td>' +
           '<td class="' + cls + '">' + (isNum ? fmt(s.points) : esc(String(s.points))) + '</td></tr>';
    }
    return h + '</table>';
  }

  /* ===== Status bar texts (the line under the header) =====
     Both pages take their sentences FROM HERE, otherwise the same state
     would be put in two different ways. The word "Frissítve" (updated) used
     to mean different things on the two pages: the time of the check on
     NB1, the age of the stored file on PL - that was the most misleading.
     There are four states: fetching / live round with fresh data / no
     round in progress / the live fetch failed. */
  var clockTime = function (d) {
    return new Date(d).toLocaleTimeString('hu-HU', { hour: '2-digit', minute: '2-digit' });
  };
  var dateTime = function (d) {
    return new Date(d).toLocaleString('hu-HU',
      { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };
  var statusLine = {
    fetching: function (detail) { return 'Élő állás lekérése…' + (detail ? ' ' + detail : ''); },
    live: function (round, when) {
      return 'Élő állás — ' + round + '. forduló · frissítve ' + clockTime(when) +
             ' (a tabella csak lezárt fordulókból számol)';
    },
    // Idle state. Showing the time of the CHECK is not enough: during an
    // international break this stood on the page for three weeks, and there
    // was no telling whether the stored data was old or simply nothing had
    // happened. So the last closed round and the last CHANGE of the stored
    // data are shown too.
    upToDate: function (when, closed, stored) {
      return 'Naprakész' +
             (closed ? ' · utolsó lezárt: ' + closed + '. forduló' +
                       (stored ? ' (rögzítve: ' + dateTime(stored) + ')' : '') : '') +
             ' · ellenőrizve ' + clockTime(when);
    },
    // The closed round's result is not in the stored data yet.
    closedRoundMissing: function (round, stored) {
      return round + '. forduló lezárult — az eredmények a következő adatfrissítéssel kerülnek be' +
             (stored ? ' (tárolt állás: ' + dateTime(stored) + ')' : '');
    },
    // The fixed text of the current round's error message - do not reword it.
    errorLive: 'Automata lekérés hiba: az állások a forduló végén frissülnek.',
    errorIdle: function (savedAt) {
      return 'Az élő frissítés most nem elérhető — a tárolt állás látható' +
             (savedAt ? ' (mentve: ' + dateTime(savedAt) + ')' : '') + '.';
    },
    loadError: function (what, err) {
      return 'Nem sikerült betölteni a liga adatait (' + what + '): ' + err;
    },
    dateTime: dateTime
  };

  /* League switcher bar. `active` is the id of the league currently open
     (null on the home page), `root` the relative path to the site root
     ('../' from a league page, '' from the home page) - GitHub Pages serves
     the site from a subpath, so absolute '/' paths cannot be used. */
  /* ===== Top bar: two levels, and always ONE lit =====
     The leagues (NB1, PL) are ALTERNATIVES to each other - that is the first
     level. The magazine is not their sibling but part of THE GIVEN LEAGUE:
     the second level.

     It used to be mixed up: on the magazine page the league's dot was lit -
     as if you were on the league page - and the magazine button
     disappeared, so the way back was that very dot, which did not look like
     a way back.

     The rule: what is FILLED is WHERE YOU ARE. On the league page the
     league's dot, in the magazine the magazine button - and the league's
     dot is then a plain link, visibly the way back to the league page. The
     button never disappears.

     opts.section: 'ujsag' when you are looking at the magazine; anything
     else is the league page. opts.magazine === false leaves the button out
     entirely. */
  function navHTML(active, root, opts) {
    root = root || '';
    opts = opts || {};
    var inMagazine = opts.section === 'ujsag';
    var h = '<a class="markanev" href="' + root + '">FunTasy</a><span class="ligak">';
    for (var i = 0; i < LEAGUES.length; i++) {
      var l = LEAGUES[i];
      h += '<a class="ligalink' + (l.id === active && !inMagazine ? ' on' : '') +
           '" href="' + root + l.path + '" title="' + esc(l.title) + '">' +
           esc(l.name) + '</a>';
    }
    h += '</span>';
    if (opts.magazine !== false)
      // The league name is in a separate element: on a narrow screen the CSS
      // hides it and the button fits on one line. Without it the top bar broke
      // into three lines.
      h += '<a class="ujsaglink' + (inMagazine ? ' on' : '') + '" href="' + root +
           'nemzethy/' + (active ? '?liga=' + encodeURIComponent(active) : '') + '">' +
           MAGAZINE_NAME + (active ? '<span class="ujsagliga"> ' + esc(leagueById(active).name) +
           '</span>' : '') + '</a>';
    return h;
  }
  /* ===== Footer =====
     The same line at the bottom of every page. It is shared because copied
     onto three pages one of them would surely drift at the next link. */
  /* The player's match above the points breakdown: "ARS 2-1 BRE" + a state
     on the right ("70. perc" / "vége" / "még nem kezdődött"). SHARED by the
     leagues - the data (where the score comes from and what the right-hand
     label is) is the job of each league's adapter. A 0-0 is never made up:
     if there is no result (hp == null), only the two club names are shown. */
  /* ===== Line-up efficiency =====
     How much the chosen starting line-up brought of what the squad could
     have brought. The CALCULATION is each league's adapter's job (NB1: the
     collector computes it with the fixed bench rule and the captain; PL: the
     browser, with the formation rules) - only the shared display lives here.
     The hook: opts.lineup(name, round) -> {sz, le} | null. */
  var LINEUP_TITLE = 'Kezdőállítási hatékonyság — a keretből elérhető pontok ' +
                 'hány százalékát hozta a beállított kezdő';

  /* The "Guardiola measure": how many points more/fewer came after the
     squad change. guard = the CURRENT squad's points MINUS LAST WEEK's
     squad's points IN THE SAME round - that is, "what would have happened
     if I had not touched it". A negative value: the change cost points.
     The hook: opts.guard(name, round) -> {teny, alt, guard} | null. */
  var GUARD_TITLE = 'Guardiola mutató — mennyivel hozott többet a keretváltoztatás,'
                + ' mint ha a múlt heti kerethez hozzá sem nyúlsz';
  var signed = function (g) { return (g > 0 ? '+' : '') + fmt(g); };
  function lineupPercent(scored, possible) {
    return possible > 0 ? Math.round(100 * scored / possible) : null;
  }

  /* The efficiency row of the match header: the two values align with
     their OWN half (left/right), like every other datum of the header - the
     label in the middle. Empty when neither side has a value. */
  function lineupPairHTML(va, vb, live) {
    var one = function (x) {
      var pc = x && lineupPercent(x.sz, x.le);
      return pc == null ? '–'
        : pc + '% <span class="kezdresz">(' + fmt(x.sz) + '/' + fmt(x.le) + ')</span>';
    };
    var a = one(va), b = one(vb);
    if (a === '–' && b === '–') return '';
    return '<div class="kezdsor" title="' + esc(LINEUP_TITLE) + '">' +
      '<span class="kezdbal">' + a + '</span>' +
      '<span class="kezdcim">kezdőállítás' +
      (live ? ' <span class="elojel">élő</span>' : '') + '</span>' +
      '<span class="kezdjobb">' + b + '</span></div>';
  }

  /* ===== Player profile (shared layer) =====
     The profile has the same structure in both leagues: a header (who this
     player is) and a list by round (opponent, score, points, and WHO had
     the player). What differs by league is only the SOURCE of the data - so
     the caller passes a ready `data` object, and the rendering lives here,
     in a single place. That way the two pages cannot say two different
     things about the same thing.

     data = {
       nev, klub, poszt,                  // name, club, position
       cimkek: ['U21', ...],              // short tags shown next to the name
       tenyek: [{cimke, ertek}],          // header facts (total points, price, ...)
       sorok: [{
         r,                               // the round number
         ellenfel,                        // the opponent club's short name (or null)
         hazai,                           // true = home, false = away, null = unknown
         hp, vp,                          // the match score, ALWAYS in home-away order
         pont,                            // the player's base points (null = no data)
         jegyzet,                         // text shown instead of the points, if there are none
         tulajok: [{nev, szerep}]         // who had the player; empty array = nobody
       }],
       senkinel                           // what to show for an empty `tulajok`
     }

     The rows can be expanded: the caller binds the `.plr[data-acc]` click
     to its own breakdown loader (accToggle), just as in the squad view. */
  /* The row at the bottom of the points breakdown that opens the full
     profile. The caller supplies the data attributes, because each league
     needs different ones (NB1 the cp id and the name, PL the element id) -
     the text and the look are shared. It is not shown INSIDE the profile:
     you are already there. */
  function profileLinkHTML(attrs) {
    return '<div class="profnyito"' + (attrs || '') + '>Teljes játékosprofil <span>›</span></div>';
  }

  function profileHeaderHTML(data) {
    // the same markers as in the squad rows: a flag marks a Hungarian player,
    // the other short tags are the blue chip - otherwise the same information
    // would look different in two places
    var tags = (data.magyar ? '<span class="flag" title="magyar"></span>' : '')
      + (data.cimkek || []).map(function (c) {
          return '<span class="u21">' + esc(c) + '</span>';
        }).join('');
    var facts = (data.tenyek || []).map(function (t) {
      return '<div class="ptny"><span>' + esc(t.cimke) + '</span><b>' +
             (typeof t.ertek === 'number' ? fmt(t.ertek) : esc(String(t.ertek))) + '</b></div>';
    }).join('');
    return '<div class="proffej">' +
      '<div class="profnev">' +
        (data.poszt ? '<span class="ppos">' + esc(data.poszt) + '</span>' : '') +
        '<b>' + esc(data.nev || '') + '</b>' +
        (data.klub ? '<span class="tm">' + esc(data.klub) + '</span>' : '') + tags +
      '</div>' + (facts ? '<div class="ptenyek">' + facts + '</div>' : '') + '</div>';
  }

  /* The NAME of the owner's role, in one place. The caller passes it
     structured (starter / captain booleans), not as ready Hungarian text -
     so the wording lives in one place, and the shares can be computed from
     it too, without matching text. The captain is also a starter. */
  function roleName(t) {
    return t.kapitany ? 'kapitány' : (t.kezdo ? 'kezdő' : 'pad');
  }

  /* Shares across the league - ONLY IN A SALARY CAP league.
     In a DRAFT league this makes no sense: there a player belongs to
     exactly one manager (or nobody), so "squad %" would always be 1/N or 0,
     and there is no captain at all. This is not a difference between NB1
     and PL but the league's TYPE - so the `type` field decides it
     (funtasy.js -> LEAGUES), not the league id.
     The denominator is the round's ACTUAL number of squads, not a hard-coded
     number: if someone's squad is missing from a round, a hard-coded number
     would skew it downwards. The three numbers nest: squad >= starter >= captain. */
  function shareHTML(s, salaryCap) {
    var t = s.tulajok || [];
    if (!salaryCap || !s.keretszam || !t.length) return '';
    var starters = 0, captains = 0;
    for (var i = 0; i < t.length; i++) {
      if (t[i].kezdo || t[i].kapitany) starters++;
      if (t[i].kapitany) captains++;
    }
    var pc = function (x) { return Math.round(100 * x / s.keretszam) + '%'; };
    return '<span class="parany" title="a forduló ' + s.keretszam +
      ' keretére vetítve — a kapitány is kezdő">' +
      'keret <b>' + pc(t.length) + '</b> · kezdő <b>' + pc(starters) +
      '</b> · kapitány <b>' + pc(captains) + '</b></span>';
  }

  /* One round's row. The score ALWAYS comes in home-away order, and
     "(h)" / "(i)" (home / away) marks which side the player's club was on - so
     the result reads the same as everywhere else on the page, and nobody has
     to flip it in their head. */
  /* One round's match(es) in the row's name cell. Normally there is one
     match: then the opponent and the venue are in the name cell and the
     score in its own column - so the numbers line up under each other. In a
     DOUBLE ROUND (it happens in the PL) a club plays twice: then both
     matches go side by side, with their scores, into the name cell, and the
     score column stays empty. Better to lay out the rare case a bit
     differently than to lose the second match. */
  function profileGamesHTML(games) {
    if (!games.length) return { nev: '—', allas: '' };
    var one = function (m) {
      var venue = m.hazai == null ? '' : (m.hazai ? '(h)' : '(i)');
      var scoreTxt = (m.hp == null || m.vp == null) ? '' : ' ' + fmt(m.hp) + '–' + fmt(m.vp);
      return esc(m.ellenfel || '—') + (venue ? ' ' + venue : '') + scoreTxt;
    };
    if (games.length > 1)
      return { nev: games.map(one).join(' <span class="pelval">·</span> '), allas: '' };
    var m = games[0];
    return {
      nev: esc(m.ellenfel || '—') +
        (m.hazai == null ? '' : ' <span class="tm">' + (m.hazai ? 'otthon' : 'idegenben') + '</span>'),
      allas: (m.hp == null || m.vp == null) ? ''
        : '<span class="pallas">' + fmt(m.hp) + '–' + fmt(m.vp) + '</span>'
    };
  }

  /* The round's price, and next to it the change from the previous one.
     It only makes sense in a salary cap league, and is only shown where we
     know it: the price log started during the season, there is no
     observation for earlier rounds, and the nearest later price is NOT
     theirs. So nothing instead of an empty slot. */
  /* `column`: whether the profile has a price column at all. The price log
     starts later than the season, so the early rounds have no price - those
     rows get an EMPTY cell of the same width, otherwise the points column
     would jump sideways between rows. */
  function priceHTML(s, prevPrice, column) {
    if (!column) return '';
    if (s.ar == null) return '<span class="par"></span>';
    var d = prevPrice == null ? null : Math.round((s.ar - prevPrice) * 10) / 10;
    return '<span class="par">' + fmt(s.ar)
      + (d ? '<span class="pardl ' + (d > 0 ? 'pos' : 'neg') + '">'
             + (d > 0 ? '+' : '\u2212') + fmt(Math.abs(d)) + '</span>' : '')
      + '</span>';
  }

  function profileRowHTML(s, nobody, salaryCap, prevPrice, priceColumn) {
    var games = s.meccsek || [];
    var m = profileGamesHTML(games);
    // For a FUTURE round the owner line stays EMPTY: who will have the player
    // is unknown - "senkinél" / "szabadügynök" (nobody / free agent) there
    // would be a claim, not data.
    var owners = (s.tulajok && s.tulajok.length)
      ? s.tulajok.map(function (t) {
          return '<span class="ptul"><b>' + esc(t.nev) + '</b> · ' + esc(roleName(t)) + '</span>';
        }).join('')
      : (s.jovo ? '' : '<span class="ptul nincs">' + esc(nobody || '–') + '</span>');
    var share = shareHTML(s, salaryCap);
    var pts = (s.pont == null)
      ? '<span class="pjegyzet">' + esc(s.jegyzet || '—') + '</span>'
      : fmt(s.pont);
    return '<div class="plr profsor" data-acc="1" data-pr="' + s.r + '">' +
      '<span class="ppos">' + s.r + '.</span>' +
      '<span class="nm">' + m.nev + '<span class="accarr">▼</span></span>' +
      m.allas +
      priceHTML(s, prevPrice, priceColumn) +
      '<span class="pts">' + pts + '</span>' +
      '<span class="ptulajok">' + owners + share + '</span>' +
    '</div>';
  }

  function profileHTML(data) {
    var rows = data.sorok || [];
    if (!rows.length)
      return profileHeaderHTML(data) +
        '<div class="loading">Ehhez a játékoshoz még nincs fordulónkénti adat.</div>';
    var l = leagueById(data.liga), salaryCap = !!l && l.type === 'salary-cap';
    var prevPrice = null;
    var priceColumn = salaryCap && rows.some(function (s) { return s.ar != null; });
    return profileHeaderHTML(data) +
      '<div class="proflista">' + rows.map(function (s) {
        var out = profileRowHTML(s, data.senkinel, salaryCap, prevPrice, priceColumn);
        if (s.ar != null) prevPrice = s.ar;
        return out;
      }).join('') + '</div>';
  }

  function breakdownMatchRow(m) {
    if (!m || !m.hazai || !m.vendeg) return '';
    var score = (m.hp == null || m.vp == null)
      ? esc(m.hazai) + '\u2013' + esc(m.vendeg)
      : esc(m.hazai) + ' <b>' + fmt(m.hp) + '\u2013' + fmt(m.vp) + '</b> ' + esc(m.vendeg);
    return '<div class="bontasmeccs"><span>' + score + '</span>' +
           '<span class="ora">' + esc(m.jobb || '') + '</span></div>';
  }

  /* ===== Home page player list: search + column filter + sorting =====
     The same behaviour in both leagues, only the data differs: the caller
     passes a `data` function that builds the list from the files already
     loaded, and an `open(id)` that opens the profile.

     Three kinds of narrowing, because there are three kinds of question:
       - the SEARCH looks in the name and the club too (you need not know in
         advance which one you mean), and also matches without accents;
       - the CLUB/POSITION filter narrows to one column's content (e.g. "only MTK");
       - clicking the HEADER sorts by any column.
     By default the list shows the best `limit` rows - the whole field is
     385-612 rows, no point putting all of it in the DOM - but filtering and
     searching ALWAYS run over the whole field, otherwise they would fail at
     exactly what they are for. */
  function stripAccents(x) {
    return String(x == null ? '' : x).toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  /* Who has the player NOW. In a salary cap league that can be several
     managers, and the names do not fit on one line - but the "+2" is the
     most important part, so it stands SEPARATELY and is NEVER cut; the
     names get shortened instead. (When they were one piece, the CSS
     swallowed exactly the count.) */
  /* Managers are shown by MONOGRAM (the same `.tag` label as in the
     table): that way four fit where two full names did not. The full name
     stays in the `title`, and the profile shows it anyway.
     The caller passes `{nev, jel}` pairs (name, monogram); without a
     monogram the name is the fallback. */
  function ownersHTML(owners, nobodyText) {
    var t = owners || [];
    // Nobody: a short sign, not a word. The column is narrow and
    // "szabadügynök" only took up room there; the filter dropdown keeps the
    // readable text.
    if (!t.length)
      return '<span class="jltulaj nincs">' + esc(nobodyText || '–') + '</span>';
    var shown = t.slice(0, 4), more = t.length - shown.length;
    return '<span class="jltulaj"><span class="jlnev">' + shown.map(function (x) {
      return x.jel
        ? '<span class="tag" title="' + esc(x.nev) + '">' + esc(x.jel) + '</span>'
        : esc(x.nev);
    }).join(' ') + '</span>' +
      (more ? '<span class="jltobb">+' + more + '</span>' : '') + '</span>';
  }

  /* The columns in one place: the header, the sorting and the row are all
     built from this, so they cannot drift apart. `numeric: true` -> the
     first click sorts descending. */
  var LIST_COLUMNS = [
    { key: 'poszt', title: 'Poszt', cls: 'ppos', filter: 'lista', filterTitle: 'Minden poszt',
      cell: function (p) {
        return p.poszt ? '<span class="ppos">' + esc(p.poszt) + '</span>' : '<span class="ppos"></span>'; } },
    // the search filters on the name (partial match, also without accents) -
    // a dropdown with 400-600 names would be useless
    { key: 'nev',   title: 'Játékos', cls: 'nm', cell: function (p) {
        return '<span class="nm">' + esc(p.nev) +
          (p.u21 ? ' <span class="u21">U21</span>' : '') + '</span>'; } },
    { key: 'klub',  title: 'Klub', cls: 'jlklub', filter: 'lista', filterTitle: 'Minden klub',
      cell: function (p) {
        return '<span class="jlklub">' + esc(p.klub || '') + '</span>'; } },
    { key: 'tulaj', title: 'Kinél van', cls: 'jltulaj', filter: 'tulaj', filterTitle: 'Mindegy',
      cell: function (p, o) { return ownersHTML(p.tulajok, o.nobodyText); } },
    // Keret%: in what percentage of the squads the player is NOW. Only
    // meaningful in a salary cap league (in a draft always 1/N or 0), so the
    // caller asks for it.
    { key: 'kpc',   title: 'Keret%', cls: 'jlkpc', numeric: true, filter: 'min', filterTitle: 'Min. keret%',
      cell: function (p) {
        return '<span class="jlkpc">' + (p.kpc == null ? '' : Math.round(p.kpc) + '%') + '</span>'; } },
    // Ár (price): only meaningful in a salary cap league (in a draft you do
    // not buy players). The filter here is an UPPER limit - the question is
    // what fits in my budget, not what is expensive.
    { key: 'ar',    title: 'Ár', cls: 'jlar', numeric: true, filter: 'max', filterTitle: 'Max. ár',
      cell: function (p) {
        return '<span class="jlar">' + (p.ar == null ? '' : fmt(p.ar)) + '</span>'; } },
    { key: 'pts',   title: 'Pont', cls: 'pts', numeric: true, filter: 'min', filterTitle: 'Min. pont',
      cell: function (p) {
        return '<span class="pts">' + fmt(p.pts || 0) + '</span>'; } }
  ];
  // The two special filter values. They are NOT marked with a control
  // character: the HTML parser replaces NUL, and the dropdown's value would
  // never match what the filter expects - "Valakinél" (somebody) silently
  // gave an empty list because of it.
  // The "@@" prefix, on the other hand, cannot occur in a manager name.
  var LIST_NOBODY = '@@szabad';           // nobody has the player
  var LIST_ANYBODY = '@@valaki';           // at least one owner

  function listSortValue(p, key) {
    if (key === 'pts' || key === 'ar' || key === 'kpc') return p[key] || 0;
    if (key === 'tulaj') return (p.tulajok && p.tulajok[0] && p.tulajok[0].nev) || '';
    return p[key] || '';
  }

  /* Pager with page numbers. Clicking through 10 pages one by one is not
     usable, so the first and the last page are ALWAYS shown, with the
     neighbourhood of the current one between them and a "…" over the
     skipped part. That way any page is two clicks away, and the total
     number of pages is visible. */
  function pagerHTML(page, pages) {
    if (pages <= 1) return '';
    var marks = {}, i;
    marks[0] = marks[pages - 1] = 1;
    for (i = page - 2; i <= page + 2; i++) if (i >= 0 && i < pages) marks[i] = 1;
    var nums = Object.keys(marks).map(Number).sort(function (a, b) { return a - b; });
    var h = '<button class="jllapoz nyil" data-ugras="' + (page - 1) +
      '" type="button"' + (page === 0 ? ' disabled' : '') + ' title="Előző">‹</button>';
    var prev = null;
    for (i = 0; i < nums.length; i++) {
      var n = nums[i];
      if (prev !== null && n > prev + 1) h += '<span class="jlkihagy">…</span>';
      h += '<button class="jllapoz' + (n === page ? ' most' : '') +
        '" data-ugras="' + n + '" type="button">' + (n + 1) + '</button>';
      prev = n;
    }
    return h + '<button class="jllapoz nyil" data-ugras="' + (page + 1) +
      '" type="button"' + (page >= pages - 1 ? ' disabled' : '') + ' title="Következő">›</button>';
  }

  function playerSearch(opts) {
    var box = document.getElementById(opts.box);
    if (!box) return null;
    var limit = opts.limit || 40;
    // The caller can say which columns it wants (e.g. the PL draft has no
    // price). By default all of them except the price - that one has to be asked for.
    var columns = LIST_COLUMNS.filter(function (o) {
      return opts.columns ? opts.columns.indexOf(o.key) >= 0 : o.key !== 'ar';
    });
    var order = { key: 'pts', dir: -1 };
    var filters = {};                       // column key -> filter value
    var page = 0;                          // which page (from 0)

    // the skeleton is drawn once: the search field is NOT redrawn, otherwise
    // it would lose focus on every keystroke
    // The dropdown values come from the DATA itself, not a hard-coded list:
    // so a new club or a new manager shows up in them by itself.
    // value -> label. In the owner filter the label is the MONOGRAM (the same
    // as in the column) and the full name goes into the title; the filtered
    // VALUE stays the name, because that is what identifies.
    var optionsFor = function (o) {
      var h = {}, allRows = opts.data() || [], i, j;
      for (i = 0; i < allRows.length; i++) {
        if (o.filter === 'tulaj') {
          var t = allRows[i].tulajok || [];
          for (j = 0; j < t.length; j++) h[t[j].nev] = t[j].jel || t[j].nev;
        } else if (allRows[i][o.key]) h[allRows[i][o.key]] = allRows[i][o.key];
      }
      return Object.keys(h).sort(function (a, b) { return a.localeCompare(b, 'hu'); })
        .map(function (k) { return { value: k, label: h[k] }; });
    };
    var controlHTML = function (o) {
      if (o.filter === 'min' || o.filter === 'max')
        return '<input class="jlszam" type="number" min="0" step="any" ' +
               'data-szuro="' + o.key + '" placeholder="' + esc(o.filterTitle) + '">';
      // "Mindegy" (any) switches the filter off; "Valakinél" (somebody) asks
      // whether the player has an owner at all - two different questions, so
      // two rows.
      var extra = o.filter === 'tulaj'
        ? '<option value="' + LIST_ANYBODY + '">Valakinél</option>' +
          '<option value="' + LIST_NOBODY + '">Senkinél</option>' : '';
      return '<select class="jlszuro" data-szuro="' + o.key + '"><option value="">' +
        esc(o.filterTitle) + '</option>' + extra + optionsFor(o).map(function (v) {
          return '<option value="' + esc(v.value) + '" title="' + esc(v.value) + '">' +
                 esc(v.label) + '</option>';
        }).join('') + '</select>';
    };
    box.innerHTML =
      '<div class="jlvezerlo">' +
        '<input class="kereso" type="search" autocomplete="off" ' +
          'placeholder="Keresés játékosra vagy klubra…">' +
        columns.filter(function (o) { return o.filter; }).map(controlHTML).join('') +
        '<button class="jltorol" type="button">Szűrők törlése</button>' +
      '</div>' +
      '<div class="plr plrfej jlfej"><span class="rank"></span>' +
        columns.map(function (o) {
          // the same layout class as on the data cell: without it the header does
          // not stand above the columns but squashed at the start of the row
          return '<span class="jlfejcella ' + o.cls + '" data-rend="' + o.key + '">' +
                 esc(o.title) + '<i></i></span>';
        }).join('') + '<span class="jltores"></span></div>' +
      '<div class="jllista"></div>' +
      '<div class="jllabsor"><span class="note jllab"></span>' +
        '<select class="jlmeret" title="Hány sor egy oldalon">' +
          [20, 40, 100, 0].map(function (n) {
            return '<option value="' + n + '"' + (n === limit ? ' selected' : '') + '>' +
                   (n ? n + ' / oldal' : 'mind') + '</option>';
          }).join('') +
        '</select><span class="jllapozo"></span></div>';

    var input = box.querySelector('.kereso');
    var listEl = box.querySelector('.jllista');
    var footerEl = box.querySelector('.jllab');
    var pagerEl = box.querySelector('.jllapozo');

    function draw() {
      var allRows = opts.data() || [];
      var q = stripAccents(input.value).trim();
      var hits = allRows.filter(function (p) {
        for (var i = 0; i < columns.length; i++) {
          var o = columns[i], v = filters[o.key];
          if (!o.filter || v === undefined || v === '') continue;
          if (o.filter === 'min') { if ((p[o.key] || 0) < +v) return false; continue; }
          if (o.filter === 'max') {
            if (p[o.key] == null || p[o.key] > +v) return false;
            continue;
          }
          if (o.filter === 'tulaj') {
            var t = p.tulajok || [];
            if (v === LIST_NOBODY) { if (t.length) return false; continue; }
            if (v === LIST_ANYBODY) { if (!t.length) return false; continue; }
            var found = false;
            for (var k = 0; k < t.length; k++) if (t[k].nev === v) found = true;
            if (!found) return false;
            continue;
          }
          if (p[o.key] !== v) return false;
        }
        if (!q) return true;
        return stripAccents(p.nev).indexOf(q) >= 0 || stripAccents(p.klub).indexOf(q) >= 0;
      });
      hits.sort(function (a, b) {
        var x = listSortValue(a, order.key), y = listSortValue(b, order.key), c;
        if (typeof x === 'number' || typeof y === 'number') c = (x || 0) - (y || 0);
        else c = String(x).localeCompare(String(y), 'hu');
        // on equal values the points decide, so the order does not jump around
        return c * order.dir || (b.pts || 0) - (a.pts || 0);
      });
      // after filtering/sorting the page number cannot be past the end of the list
      var pages = Math.max(1, Math.ceil(hits.length / limit));
      if (page >= pages) page = pages - 1;
      if (page < 0) page = 0;
      var shown = hits.slice(page * limit, page * limit + limit);
      listEl.innerHTML = shown.length ? shown.map(function (p, i) {
        return '<div class="plr jlsor" data-jl="' + esc(p.id) + '">' +
          '<span class="rank">' + (page * limit + i + 1) + '.</span>' +
          columns.map(function (o) { return o.cell(p, opts); }).join('') +
          // on a phone this breaks the row into two lines (hidden on desktop); the
          // `order` itself does not break a line, that needs a full-width element
          '<span class="jltores"></span>' +
        '</div>';
      }).join('') : '<div class="loading">Nincs találat erre: „' + esc(input.value) + '”</div>';

      box.querySelectorAll('.jlfejcella').forEach(function (c) {
        c.classList.toggle('rendez', c.dataset.rend === order.key);
        c.querySelector('i').textContent =
          c.dataset.rend === order.key ? (order.dir < 0 ? '▼' : '▲') : '';
      });
      var filtered = !!q;
      for (var sk in filters) if (filters[sk] !== '' && filters[sk] !== undefined) filtered = true;
      var from = hits.length ? page * limit + 1 : 0;
      footerEl.textContent = !allRows.length ? ''
        : !hits.length ? 'Nincs találat'
        : (from + '–' + (page * limit + shown.length) + ' / ' + hits.length +
           (filtered ? ' találat' : ' játékos'));
      pagerEl.innerHTML = pagerHTML(page, pages);
    }

    var redraw = function () { page = 0; draw(); };
    input.addEventListener('input', redraw);
    box.addEventListener('input', function (e) {
      var ctl = e.target.closest('.jlszam');
      if (ctl) { filters[ctl.dataset.szuro] = ctl.value; redraw(); }
    });
    box.addEventListener('change', function (e) {
      var m = e.target.closest('.jlmeret');
      // "mind" (all): a large number, not a separate branch - so the pager disappears by itself
      if (m) { limit = +m.value || 100000; redraw(); return; }
      var ctl = e.target.closest('.jlszuro');
      if (ctl) { filters[ctl.dataset.szuro] = ctl.value; redraw(); }
    });
    box.addEventListener('click', function (e) {
      if (e.target.closest('.jltorol')) {
        filters = {}; input.value = '';
        box.querySelectorAll('.jlszuro').forEach(function (x) { x.value = ''; });
        box.querySelectorAll('.jlszam').forEach(function (x) { x.value = ''; });
        redraw();
        return;
      }
      var head = e.target.closest('.jlfejcella');
      if (head) {
        var o = null;
        for (var i = 0; i < columns.length; i++)
          if (columns[i].key === head.dataset.rend) o = columns[i];
        if (order.key === head.dataset.rend) order.dir = -order.dir;
        else order = { key: head.dataset.rend, dir: (o && o.numeric) ? -1 : 1 };
        redraw();
        return;
      }
      var pageBtn = e.target.closest('.jllapoz');
      if (pageBtn) { page = +pageBtn.dataset.ugras; draw(); return; }
      var row = e.target.closest('.jlsor');
      if (row && opts.open) opts.open(row.dataset.jl);
    });
    draw();
    return { draw: draw };
  }

  /* 'here' is the id of the page CURRENTLY OPEN: no link to itself is
     shown. The changelog used to solve this by not asking for a footer at
     all - with two such pages that no longer works, as each must link to
     the other. */
  var FOOTER_LINKS = [{ id: 'nemzethy', path: 'nemzethy/', name: MAGAZINE_NAME },
                { id: 'valtozasok', path: 'valtozasok/', name: 'Mi újult meg?' }];
  function footerHTML(root, here) {
    root = root || '';
    return FOOTER_LINKS.filter(function (x) { return x.id !== here; })
      .map(function (x) { return '<a href="' + root + x.path + '">' + esc(x.name) + '</a>'; })
      .join('');
  }
  function renderFooter(root, here) {
    var el = document.getElementById('lablec');
    if (el) el.innerHTML = footerHTML(root, here);
  }

  /* One call sets up the shared header parts: the league switcher bar, the
     league type (as a body class, so both CSS and JS have a handle on it)
     and the subtitle. So the league's name/description lives in a single
     place, the LEAGUES list; the page may still overwrite the subtitle with
     its own, computed from data. */
  function renderNav(active, root, opts) {
    var el = document.getElementById('liganav');
    if (el) el.innerHTML = navHTML(active, root, opts);
    var l = leagueById(active);
    if (!l) return;
    if (document.body) document.body.classList.add('tipus-' + l.type);
    var sub = document.querySelector('.sub');
    if (sub) sub.textContent = l.title + ' · ' + l.description;
  }

  /* ===== Refresh when the page becomes visible again =====
     The pages fetch the live score once, on load. On a desktop that is
     enough, because one usually comes back to a freshly loaded page. On a
     phone, however, the page is not reloaded, just switched back to: the
     browser restores it from memory, so the score from load time freezes.
     That is how the home page match list could still show the old points
     while the match page - which has its own fetch on opening - already
     showed the fresh ones.

     This helper re-runs the given refresh when the page becomes visible
     again. It has two guards: it starts at most once every minGap
     milliseconds (otherwise flicking between tabs would hammer the proxies
     with requests), and two of them never run at the same time. For the
     per-minute refresh see below (liveRefresher) - that one only runs
     during a LIVE round. */
  function onVisibleAgain(fn, minGap) {
    minGap = (minGap == null) ? 30000 : minGap;
    var lastRun = Date.now(), running = false;
    function trigger() {
      if (running || document.visibilityState === 'hidden') return;
      if (Date.now() - lastRun < minGap) return;
      running = true;
      Promise.resolve().then(fn).catch(function () {}).then(function () {
        running = false;
        lastRun = Date.now();          // the next window counts from the END of the run
      });
    }
    document.addEventListener('visibilitychange', trigger);
    // In iOS Safari a page restored from the bfcache does not always get
    // visibilitychange, but it does get pageshow (persisted).
    window.addEventListener('pageshow', function (e) { if (e.persisted) trigger(); });
    // on a desktop, clicking back onto the window does not fire visibilitychange either
    window.addEventListener('focus', trigger);
    return trigger;
  }

  /* ===== Timed refresh WHILE THE ROUND IS LIVE =====
     The failure this prevents (PL): a page left open showed the score from
     LOAD TIME. The LEE-BRE match was at minute 9 when the page loaded, and
     the rows stayed there - minutes, match clock and points alike. The
     expanding breakdown, however, starts its own fresh fetch ON CLICK, so it
     already showed 90 minutes: on the same screen the row (9 minutes, 1
     point) and its panel (90 minutes, 2 points) contradicted each other.
     The panel was right.

     Polling every minute from an open page would hammer public proxies; our
     own Cloudflare Worker, with its 60-second edge cache, removes that
     concern - however many people watch the same round, one request a
     minute goes out to the API.

     It has three guards: it does not run on a HIDDEN page (and stops at
     once when the tab is switched), two of them never run at the same time,
     and it only runs when the caller starts it - so not a single request
     goes out between rounds. */
  function liveRefresher(fn, interval) {
    interval = interval || 60000;
    var id = null, running = false, wanted = false;
    function tick() {
      if (running || document.visibilityState === 'hidden') return;
      running = true;
      Promise.resolve().then(fn).catch(function () {}).then(function () { running = false; });
    }
    function stopClock() { if (id) { clearInterval(id); id = null; } }
    function startClock() {
      if (!id && wanted && document.visibilityState !== 'hidden') id = setInterval(tick, interval);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') stopClock(); else startClock();
    });
    return {
      start: function () { wanted = true; startClock(); },
      stop:  function () { wanted = false; stopClock(); }
    };
  }

  /* ===== THE CURRENT ROUND'S SQUADS, UNTIL THE COLLECTOR HAS WRITTEN THEM =====
     The failure this prevents (PL round 5): during a live match the page
     did not update. The collectors run at best hourly (NB1 on match days,
     PL between 07:00 and 13:00 UTC) and every 3 hours otherwise, but the
     round starts at the entry deadline: the 16:43 UTC run STILL saw round 4
     (the log said "fordulonkenti keret: GW4"), the next one was due at
     23:47. Meanwhile round 5 started, and the repository had NO squads for
     it at all. The page went to the API and got the live points - it just
     had nobody to apply them to, so instead of a live score the status bar said
     "Naprakész" (up to date) during a running match.

     The backfill is the browser's job: it fetches the missing squads ONCE
     per round. It is SHARED because the situation is the same in both
     leagues (the collector runs less often than a round starts); only the
     endpoint differs, and the caller supplies that. NB1 does not run into
     it today because there the collector writes the full current squads
     (squads.json) on EVERY run - should that file ever fall behind, the
     same backfill applies there too.

     - `round`: the round whose squads these are (the cache key)
     - `keys`: whose squads to fetch (PL: league id, NB1: name)
     - `fetchOne(key)`: Promise<squad|null>

     What has arrived is remembered: the next call fetches ONLY the ones
     still missing, so a failed fetch heals by itself the next minute, and
     the successful ones are not requested twice. The returned map can
     therefore be PARTIAL - the caller decides what to do about those still
     missing; showing them as zero points is NOT allowed (on a running match
     that would be a false score). */
  var BACKFILLED = {};
  function backfillSquads(round, keys, fetchOne) {
    var r = String(round);
    var have = BACKFILLED[r] || (BACKFILLED[r] = {});
    var missing = (keys || []).filter(function (k) {
      return !(have[k] && have[k].length);
    });
    if (!missing.length) {
      return Promise.resolve(Object.keys(have).length ? have : null);
    }
    return Promise.all(missing.map(function (k) {
      return Promise.resolve().then(function () { return fetchOne(k); })
                    .catch(function () { return null; });
    })).then(function (got) {
      missing.forEach(function (k, i) {
        if (got[i] && got[i].length) have[k] = got[i];
      });
      return Object.keys(have).length ? have : null;
    });
  }
  /* At a round boundary the backfilled squads must be dropped - otherwise
     they would stay in memory, and the PREVIOUS round's squads could look
     out from behind a later round's half-filled map. Without an argument
     it clears everything. */
  function clearBackfill(round) {
    if (round == null) BACKFILLED = {};
    else delete BACKFILLED[String(round)];
  }

  /* ===== Slow fetch indicator =====
     The match page and the squad view first draw with the stored numbers,
     and replace them when the minute-fresh fetch arrives. On a fast network
     this is not even noticeable; on a slow one, however, it looks as if the
     page showed old data - or, worse, the numbers jump by themselves before
     your eyes.

     No fixed threshold can be chosen well (the fetch time depends on the
     network and the CORS proxy, and varies even on the same device), so
     the indicator MEASURES ITSELF: it only appears when the fetch really
     drags on (half a second by default), and shows how long it has been
     running. With a fast response it never shows, so it does not flash for
     nothing.

     The returned function removes the indicator and returns the elapsed
     time in milliseconds. It must always be called - on the error path too. */
  /* ===== Score line (at the top of the match page) =====
     The same box as on the home page match panel, so the two places cannot
     look different. It expects the names already resolved: on PL a name
     has to be made from an id, on NB1 the name is the key itself. */
  function scoreHTML(h, v, hp, vp, live) {
    var num = function (x) { return x != null ? fmt(x) : '—'; };
    return '<div class="mscore' + (live ? ' elo' : '') + '">' +
      '<span class="csapat">' + esc(h) + '</span>' +
      '<span class="score">' + num(hp) + ' <span style="color:var(--dim)">:</span> ' + num(vp) +
      (live ? '<span class="elojel">élő</span>' : '') + '</span>' +
      '<span class="csapat">' + esc(v) + '</span></div>';
  }

  /* ===== Article strip (round preview / round summary) =====
     A short piece of writing about one fixture, shown on the match page
     above the squad columns. It renders COLLAPSED, one line high: reading
     it is a one-off pleasure, while the numbers underneath are what people
     open the page for - the text must never push them down the screen.

     A <details> element carries the open/closed state itself, so there is
     no click handler, no class juggling and keyboard access comes free. */

  /* Which strips the reader has opened, by article key. The match body is
     redrawn while a round is live (fresh points arrive every few seconds),
     and without this the text would snap shut mid-sentence under them. */
  var OPEN_ARTICLES = {};
  var articleWatched = false;
  function watchArticles() {
    if (articleWatched) return;
    articleWatched = true;
    // 'toggle' does not bubble, so a delegated listener must capture
    document.addEventListener('toggle', function (e) {
      var d = e.target;
      if (!d || !d.classList || !d.classList.contains('artstrip')) return;
      var k = d.getAttribute('data-art');
      if (!k) return;
      // the reader's choice is remembered BOTH ways: a strip that opens by
      // default must stay shut once they shut it
      OPEN_ARTICLES[k] = !!d.open;
    }, true);
  }

  /** One article as a collapsed strip. Empty string when there is none:
      a fixture nobody wrote about must look exactly as it did before.

      'defaultOpen' opens it up front. That is for the one case where it
      is all there is - a round with no squads yet, where the text cannot
      be in the way of anything. The reader's own click always wins. */
  function articleStrip(article, key, label, defaultOpen) {
    if (!article || !article.text || !article.text.length) return '';
    watchArticles();
    watchRating();
    var isOpen = OPEN_ARTICLES.hasOwnProperty(key) ? OPEN_ARTICLES[key] : !!defaultOpen;
    var lead = article.short || article.text[0];
    var body = article.text.map(function (p) { return '<p>' + esc(p) + '</p>'; }).join('');
    return '<details class="artstrip" data-art="' + esc(key) + '"' +
      (isOpen ? ' open' : '') + '>' +
      '<summary class="artstriphead">' +
        '<span class="artstriptag">' + esc(label) + '</span>' +
        '<span class="artstriplead">' + esc(lead) + '</span>' +
        '<span class="accarr">▼</span>' +
      '</summary>' +
      '<div class="artstripbody">' + body + rateBar(key) + '</div></details>';
  }

  /* A SUMMARY IS HELD BACK UNTIL ITS ROUND IS CLOSED.

     Until then the numbers can still move under it: the NB1 carries
     post-match point adjustments, the Draft finalises a round in a
     separate step. A text that says who won by how much, published while
     that can still change, is simply wrong - and it would be wrong in the
     one place the reader trusts. A preview has no such problem: it talks
     about what is coming, so it shows from the moment it is written.

     The gate defaults to CLOSED-NO: a caller that does not say cannot leak
     an early summary by forgetting. */
  /* ===== The magazine: every article in one list =====
     The strip on a match page answers "what happened in THIS match". On a
     Monday someone wants the other thing: read the lot in one sitting,
     without opening eight match pages. Same texts, same gate - the
     selection lives here so the two views cannot drift apart on what may
     be shown.

     'isClosed(league, round)' answers whether a round is final. Each page
     knows that from its own data; the magazine loads the two small files
     it needs. Same rule as the strip: an unfinished round shows only its
     preview. */
  function articleList(store, isClosed) {
    var out = [];
    var L = (store && store.leagues) || {};
    for (var i = 0; i < LEAGUES.length; i++) {
      var lg = LEAGUES[i].id;
      var roundNos = Object.keys(L[lg] || {}).map(Number).sort(function (a, b) { return b - a; });
      for (var j = 0; j < roundNos.length; j++) {
        var r = roundNos[j], closed = !!(isClosed && isClosed(lg, r));
        // The WEEKLY COLUMN (`elemzes`) does not belong to a fixture but to the
        // round, and has no gate: it may look ahead as well as back. That is why
        // it heads the list, and why it does not depend on whether the round is
        // closed. Its key is its own title, without `|` - that is how one can
        // tell it has no opponent.
        var kinds = ['elemzes'].concat(closed ? ['summary', 'preview'] : ['preview']);
        for (var k = 0; k < kinds.length; k++) {
          var m = L[lg][r][kinds[k]] || {};
          for (var pair in m) {
            var sides = pair.split('|');
            out.push({ liga: lg, fordulo: r, fajta: kinds[k], par: pair,
                      hazai: sides[0], vendeg: sides.length > 1 ? sides[1] : null,
                      cikk: m[pair],
                      kulcs: lg + '|' + r + '|' + kinds[k] + '|' + pair,
                      cimke: ARTICLE_LABEL[kinds[k]] });
          }
        }
      }
    }
    // In ORDER OF PUBLICATION, newest first. The magazine does not follow the
    // rounds but time: what was finished today is on top, even if it is
    // about an older round. `kozzetett` is the time it went live (D15: no
    // published piece may lack it); anything that still comes without a
    // stamp goes to the bottom of the list, by round descending.
    var rank = { elemzes: 0, summary: 1, preview: 2 };
    out.sort(function (a, b) {
      var ai = a.cikk && a.cikk.kozzetett, bi = b.cikk && b.cikk.kozzetett;
      if (ai && !bi) return -1;
      if (bi && !ai) return 1;
      // Several pieces go out in one commit, so an IDENTICAL timestamp is
      // common. Then the sort cannot rely on insertion order: within the group
      // the newer round comes first, and within that the column, the summary,
      // then the preview - otherwise the order of a batch published together
      // would be arbitrary.
      if (ai && bi && ai !== bi) return ai < bi ? 1 : -1;
      return (b.fordulo - a.fordulo) || (rank[a.fajta] - rank[b.fajta]);
    });
    return out;
  }

  /** One article in full - the magazine shows the text, not a teaser.

      Newspaper-like order: on top the column (small, quiet), below it the
      fixture AS A HEADLINE, then the short version AS THE LEAD - the same
      sentence that stands in the collapsed strip on the match page plays
      the role of the introduction here. Only then comes the body. That way,
      scrolling down the page, one can decide what to read. */
  function articleCardHTML(entry) {
    var body = (entry.cikk.text || []).map(function (p) {
      return '<p>' + esc(p) + '</p>';
    }).join('');
    var anchor = 'c-' + entry.kulcs.replace(/[^A-Za-z0-9]+/g, '-');
    return '<article class="magcikk" id="' + esc(anchor) + '">' +
      '<div class="magkicker">' +
        '<span class="magrovat">' + esc(entry.cimke) + '</span>' +
        '<span class="magfordulo">' + esc(leagueById(entry.liga).name) + ' · ' +
          entry.fordulo + '. forduló</span>' +
        '<button class="magmaso" data-maso="' + esc(anchor) + '" ' +
          'data-szoveg="' + esc((entry.cikk.text || []).join('\n\n')) +
          '">Másolom</button>' +
      '</div>' +
      '<h3 class="magpar">' + esc(entry.hazai) +
        (entry.vendeg ? '<span class="magvs">–</span>' + esc(entry.vendeg) : '') + '</h3>' +
      (entry.cikk.short ? '<p class="maglead">' + esc(entry.cikk.short) + '</p>' : '') +
      '<div class="magtest">' + body + '</div>' +
      rateBar(entry.kulcs) + '</article>';
  }

  /* "Másolom" (copy) puts THE ARTICLE and the link to it on the clipboard.
     Not the short version: that is the lead, not the piece - whoever
     presses the button wants to paste the text somewhere, not the
     one-sentence teaser. The old execCommand route is kept too - the
     navigator API does not exist in an insecure context (http://). */
  var magWatched = false;
  function watchMagazine() {
    // The magazine's cards carry the same rating bar as the match page's
    // strip, and need the same listener - without it the buttons did nothing.
    watchRating();
    if (magWatched) return;
    magWatched = true;
    document.addEventListener('click', function (e) {
      var g = e.target.closest && e.target.closest('.magmaso');
      if (!g) return;
      var text = (g.getAttribute('data-szoveg') || '') + '\n\n' +
                   location.href.split('#')[0] + '#' + g.getAttribute('data-maso');
      var done = function (ok) {
        g.textContent = ok ? 'Kimásolva' : 'Nem sikerült';
        setTimeout(function () { g.textContent = 'Másolom'; }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText)
        navigator.clipboard.writeText(text).then(function () { done(true); },
                                                   function () { done(false); });
      else {
        var t = document.createElement('textarea');
        t.value = text; t.style.position = 'fixed'; t.style.opacity = '0';
        document.body.appendChild(t); t.select();
        var ok = false;
        try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
        document.body.removeChild(t);
        done(ok);
      }
    }, false);
  }

  /* ===== Rating an article =====
     Why it exists: the writing gets better from knowing WHY something did
     not land. A bare "two" says nothing we can act on, so the two lower
     scores ask for a reason - IN THE READER'S OWN WORDS. There is no menu
     of ready answers on purpose: a menu hands back our own categories, and
     the sentence we have not thought of yet is exactly the one worth
     having.

     The pressure is honest, not a trap. "Elküldöm" wants a reason and
     stays out of reach until there is one; beside it the way out is always
     on screen, and says out loud what taking it means. The top two scores
     go through in one tap and ask nothing - somebody who liked it should
     not be made to work for it. */
  var RATE_LABEL = { 1: 'Rossz', 2: 'Gyenge', 3: 'Jó', 4: 'Nagyon jó' };

  /* One device rates one piece once. The browser keeps the id, we do not
     hand it out: it is not for identifying a person, but so that a
     re-rating overwrites one's own earlier rating instead of piling up. */
  function rateDevice() {
    try {
      var d = localStorage.getItem('funtasy-eszkoz');
      if (!d) {
        d = (Date.now().toString(36) + Math.random().toString(36).slice(2, 10))
              .replace(/[^a-z0-9]/g, '').slice(0, 24);
        localStorage.setItem('funtasy-eszkoz', d);
      }
      return d;
    } catch (e) { return null; }
  }
  function rateRemembered(key) {
    try { return localStorage.getItem('funtasy-ert:' + key); } catch (e) { return null; }
  }

  /* 'message' acknowledges the rating just sent; without it the bar
     recalls the earlier rating. BOTH states offer the same way out: someone
     who scored it just now can change their mind just like someone who did
     a week ago. */
  function rateBar(key, message) {
    var previous = rateRemembered(key);
    if (message || previous)
      return '<div class="artrate" data-art="' + esc(key) + '">' +
             '<span class="artratedone">' +
             esc(message || ('Köszi, ' + previous + '-esre értékelted.')) + '</span>' +
             '<button class="artrateagain" data-ujra="1">Mégis mást gondolok</button></div>';
    var g = '';
    for (var i = 1; i <= 4; i++)
      g += '<button class="artrateg" data-pont="' + i + '" title="' + esc(RATE_LABEL[i]) +
           '">' + i + '</button>';
    return '<div class="artrate" data-art="' + esc(key) + '">' +
           '<span class="artratekerdes">Milyen lett?</span>' + g +
           '<span class="artratesegit">1 = rossz · 4 = nagyon jó</span></div>';
  }

  function rateReasonHTML(score) {
    return '<div class="artreason">' +
      '<div class="artreasonq">' + (score === 1 ? 'Ennyire rossz? Mondd meg, mi a baj vele.'
                                               : 'Mi hiányzott belőle?') + '</div>' +
      '<textarea class="artreasont" rows="3" maxlength="600" ' +
      'placeholder="A saját szavaddal — egy mondat is elég. Ebből lesz jobb a következő."' +
      '></textarea>' +
      '<div class="artreasonb">' +
        '<button class="artsend" disabled>Elküldöm</button>' +
        '<button class="artskip">Kötekszem, de indokolni már nem fogok</button>' +
      '</div></div>';
  }

  function rateSend(key, score, reason) {
    var device = rateDevice();
    if (!device) return Promise.resolve(false);
    return fetch(OWN_PROXY + '/ertekeles', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cikk: key, eszkoz: device, pont: score, indok: reason || '' }),
    }).then(function (r) { return r.ok; }).catch(function () { return false; });
  }

  function rateThanks(bar, key, score, withReason) {
    try { localStorage.setItem('funtasy-ert:' + key, String(score)); } catch (e) {}
    bar.outerHTML = rateBar(key, withReason ? 'Köszi — ebből tényleg tanulunk.'
                                          : 'Köszi, megjegyeztük.');
  }

  var rateWatched = false;
  function watchRating() {
    if (rateWatched) return;
    rateWatched = true;
    document.addEventListener('click', function (e) {
      var bar = e.target.closest && e.target.closest('.artrate');
      if (!bar) return;
      var key = bar.getAttribute('data-art');
      var g = e.target.closest('button');
      if (!g || !key) return;
      // the bar is INSIDE the article: the click must not close the <details>
      e.preventDefault();
      e.stopPropagation();
      if (g.hasAttribute('data-ujra')) {
        try { localStorage.removeItem('funtasy-ert:' + key); } catch (err) {}
        bar.outerHTML = rateBar(key);
        return;
      }
      if (g.classList.contains('artsend') || g.classList.contains('artskip')) {
        var p = +bar.getAttribute('data-pont');
        var t = bar.querySelector('.artreasont');
        // A rating sent through the way out does NOT carry the reason even if
        // one was typed: the reader changed their mind, we do not send it behind
        // their back.
        var reason = g.classList.contains('artskip') ? '' : ((t && t.value) || '').trim();
        g.disabled = true;
        rateSend(key, p, reason).then(function (ok) {
          if (ok) rateThanks(bar, key, p, !!reason);
          else { g.disabled = false;
                 bar.querySelector('.artreasonq').textContent =
                   'Nem sikerült elküldeni. Próbáld meg még egyszer.'; }
        });
        return;
      }
      var score = +g.getAttribute('data-pont');
      if (!(score >= 1 && score <= 4)) return;
      // THREE-FOUR: one tap, no further question.
      if (score >= 3) {
        bar.innerHTML = '<span class="artratedone">Küldjük…</span>';
        rateSend(key, score, '').then(function (ok) {
          if (ok) rateThanks(bar, key, score, false);
          // a failed send must leave a way to try again, not a dead end
          else bar.outerHTML = rateBar(key, 'Nem sikerült elküldeni. Próbáld meg még egyszer.');
        });
        return;
      }
      // ONE-TWO: this is where the reason is asked for.
      bar.setAttribute('data-pont', String(score));
      bar.innerHTML = rateReasonHTML(score);
      var t = bar.querySelector('.artreasont');
      if (t) t.focus();
    }, false);
    // "Elküldöm" (send) waits for a reason: until there is one, it does not
    // offer itself. The way out stays reachable throughout, so this is not a
    // trap - the two buttons simply mean two different things.
    document.addEventListener('input', function (e) {
      if (!e.target.classList || !e.target.classList.contains('artreasont')) return;
      var bar = e.target.closest('.artrate');
      var sendBtn = bar && bar.querySelector('.artsend');
      if (sendBtn) sendBtn.disabled = !e.target.value.trim();
    }, false);
  }

  /** The strip for one fixture, straight from a loaded articles.json.

      A round can hold both kinds at once - the preview is written before it
      and the summary after - and then the summary wins: it is the one that
      knows how the match ended.

      The two sides are looked up in BOTH orders. Which name is the home one
      is a property of the fixture list, not of the article, so a reversed
      pair must not silently drop the text.

      opts.closed     - is this round final? (see the gate above)
      opts.defaultOpen - open the strip up front */
  /* The column name lives in ONE place: the match page, the magazine card
     and the magazine's type filter must show the same word. */
  var ARTICLE_LABEL = { summary: 'Összefoglaló', preview: 'Beharangozó',
                        elemzes: 'Kele Janek elemez' };
  function articleKindName(kind) { return ARTICLE_LABEL[kind] || kind; }
  function matchArticle(store, league, round, a, b, opts) {
    opts = opts || {};
    var r = store && store.leagues && store.leagues[league] &&
            store.leagues[league][round];
    if (!r) return '';
    var kinds = opts.closed ? ['summary', 'preview'] : ['preview'];
    // BOTH stay up on a closed round, the summary first. The preview does not
    // go stale at the final whistle: it says what the question was, the
    // summary what the answer turned out to be - side by side the two are
    // worth more than apart. Only the first one is open, though.
    var out = '';
    for (var i = 0; i < kinds.length; i++) {
      var m = r[kinds[i]];
      if (!m) continue;
      var k = m[a + '|' + b] ? a + '|' + b : (m[b + '|' + a] ? b + '|' + a : null);
      if (!k) continue;
      out += articleStrip(m[k], league + '|' + round + '|' + kinds[i] + '|' + k,
                         ARTICLE_LABEL[kinds[i]], opts.defaultOpen && !out);
    }
    return out;
  }

  /* ===== View stack: one modal that can be navigated =====
     NAVIGATION happens within one surface: the content is replaced, and the
     "back" button steps to the previous view. The x / a click outside /
     Escape always closes everything. The entry point is 'root', a tab
     switch is 'replace', a view opened from a list is 'push'; 'noop' is a
     view redrawn from the stack (nothing is pushed).

     The rule is not "never open a modal inside a modal" - that is broader
     than the truth and would stop things in the wrong place. What it
     protects is navigation: between two views sliding over each other the
     viewer loses track of where they are and which x to press. A LAYER
     (a confirmation, a short form) may still open over a modal - but only
     when losing the content underneath does not matter. Where it does
     matter - for example when rating an article, where we ask for an
     opinion about exactly what is underneath - an in-place panel is used,
     not a new layer.

     Both league pages used this, each with its own copy - a new league
     would have copied it a third time. */
  function viewStack(els) {
    var stack = [];
    function syncBack() {
      var b = document.getElementById(els.back);
      if (b) b.style.display = stack.length > 1 ? '' : 'none';
    }
    function open() {
      var o = document.getElementById(els.overlay);
      if (o) o.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    return {
      stack: stack,
      show: function (thunk, mode) {
        if (mode === 'noop') return;
        if (!mode || mode === 'root') stack.length = 0;
        if (mode === 'replace' && stack.length) stack[stack.length - 1] = thunk;
        else stack.push(thunk);
        syncBack();
      },
      back: function () {
        if (stack.length > 1) { stack.pop(); syncBack(); stack[stack.length - 1](); }
      },
      open: open,
      close: function () {
        var o = document.getElementById(els.overlay);
        if (o) o.classList.remove('open');
        document.body.style.overflow = '';
        stack.length = 0;
        syncBack();
      }
    };
  }

  /* OWN proxy (Cloudflare Worker, tartalek/proxy-worker.js): when set, it
     is the first route for every live fetch - it runs under our own
     account, nobody switches it off, and its free allowance (100k/day) is a
     multiple of our traffic. While it is empty, the fetcher skips it and
     the public proxies carry the load. */
  var OWN_PROXY = 'https://funtasy-liga.swick00.workers.dev';

  /* ===== THE LAST KNOWN SCORE =====
     The requirement: "if someone has already fetched it, let me see that -
     let me not see data older than the latest fetch". The page's first
     picture used to come from the repository, which the collectors update
     at best hourly (NB1 on match days, PL between 07:00 and 13:00 UTC) and
     every 3 hours otherwise; if your phone had fetched the fresh score ten
     minutes earlier, the computer still showed the old one, and you also had to
     wait for the fetches to run again.

     A cache CANNOT solve this: it expires and discards, so whoever arrives
     after the expiry is back to square one. So the Worker REMEMBERS what it
     fetched itself (see tartalek/proxy-worker.js), and here returns it in a
     single request - for any number of target URLs at once.

     Returns: Promise<{<url>: {ido, adat}} | null>. `adat` is the raw
     response text, `ido` the time it was fetched. A missing or not yet
     stored URL is simply absent from the response - the caller then relies
     on the live route. NEVER throws: this is a speed-up step, it cannot be
     the source of an error. */
  function storedResponses(urls) {
    if (!OWN_PROXY || !urls || !urls.length) return Promise.resolve(null);
    var q = urls.map(function (u) { return 'url=' + encodeURIComponent(u); }).join('&');
    return fetch(OWN_PROXY + '/tarolt?' + q,
                 { cache: 'no-store', headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { return (j && Object.keys(j).length) ? j : null; })
      .catch(function () { return null; });
  }

  /* ===== Fetching through a CORS proxy =====
     Tries the routes in order (direct -> corsproxy -> allorigins), and
     remembers which one worked: the rest of the session's requests start
     with that one.

     Cache busting in three layers, because without it the score froze on
     iPhone: `cache:'no-store'` for the browser, `&_=<time>` for the proxy
     (it served from its OWN cache, which is shared - that is why reloading
     did not help), and optionally a timestamp on the inner URL too.

     Settings:
       innerStamp     name of the parameter on the INNER (target) URL, or
                      empty. The FPL tolerates an unknown parameter; for the
                      MLSZ this is not verified, so it is not used there.
       isValid(j)     when to accept the response (the MLSZ needs the data array)
       onFail         'dob' (throw) -> an exception, otherwise null is returned
       onTry(label)   optional: status bar update while trying */
  function makeFetcher(cfg) {
    cfg = cfg || {};
    var stamp = function (u) {
      return cfg.innerStamp ? u + (u.indexOf('?') < 0 ? '?' : '&') +
        cfg.innerStamp + '=' + Date.now() : u;
    };
    /* The route order is MEASURED reliability, not taste
       (naplo/proxy-probe.txt): on one day corsproxy.io switched to 401 (it
       was tied to registration) and allorigins was overloaded - and since
       every live fetch depended on those two, the live part of BOTH leagues
       died at once. The lesson is built in: several independent routes, and
       after the first success the fetcher stays on the proven route anyway. */
    var routes = [
      // our own route comes BEFORE the direct one: the direct route to our two
      // APIs never works from a browser (they send no CORS headers), trying it
      // first would be wasted
      OWN_PROXY && { n: 'sajat', f: function (u) {
        return OWN_PROXY + '/?url=' + encodeURIComponent(stamp(u)); } },
      { n: 'direkt', f: function (u) { return stamp(u); } },
      // path-style proxy: the target URL is appended unchanged
      { n: 'cors.sh', f: function (u) { return 'https://proxy.cors.sh/' + stamp(u); } },
      { n: 'allorigins', f: function (u) {
          return 'https://api.allorigins.win/raw?url=' + encodeURIComponent(stamp(u)) + '&_=' + Date.now(); } },
      // allorigins' other route returns the response WRAPPED ({contents: "..."}) -
      // in the measurement exactly this one worked when /raw did not. unwrap
      // unpacks it.
      { n: 'allorigins-get', f: function (u) {
          return 'https://api.allorigins.win/get?url=' + encodeURIComponent(stamp(u)) + '&_=' + Date.now(); },
        unwrap: function (j) { return JSON.parse(j.contents); } },
      { n: 'cors.lol', f: function (u) {
          return 'https://api.cors.lol/?url=' + encodeURIComponent(stamp(u)) + '&_=' + Date.now(); } },
      // 401 on the day of the measurement - it stays at the end of the list, in case it comes back
      { n: 'corsproxy', f: function (u) {
          return 'https://corsproxy.io/?url=' + encodeURIComponent(stamp(u)) + '&_=' + Date.now(); } }
    ].filter(Boolean);
    var isValid = cfg.isValid || function (j) { return j && typeof j === 'object'; };
    var proven = null;
    return async function (url, label, ms) {
      ms = ms || 9000;
      var order = proven ? [proven].concat(routes.filter(function (r) { return r !== proven; })) : routes;
      var errors = [];
      for (var i = 0; i < order.length; i++) {
        var rt = order[i];
        try {
          if (label && cfg.onTry) cfg.onTry(label);
          var c = new AbortController();
          var t = setTimeout(function () { c.abort(); }, ms);
          var res = await fetch(rt.f(url), { signal: c.signal, cache: 'no-store',
                                             headers: { 'Accept': 'application/json' } })
            .finally(function () { clearTimeout(t); });
          if (!res.ok) { errors.push(rt.n + ':HTTP ' + res.status); continue; }
          var j = JSON.parse(await res.text());
          if (rt.unwrap) {
            try { j = rt.unwrap(j); }
            catch (e2) { errors.push(rt.n + ':csomagolt válasz hibás'); continue; }
          }
          if (!isValid(j)) { errors.push(rt.n + ':rossz formátum'); continue; }
          proven = rt;
          return j;
        } catch (e) {
          errors.push(rt.n + ':' + (e.name === 'AbortError' ? 'időtúllépés'
                     : e.name === 'TypeError' ? 'CORS' : e.message));
        }
      }
      if (cfg.onFail === 'dob') throw new Error(errors.join(' · '));
      return null;
    };
  }

  /* ===== Looking up the live score =====
     The current round's score is not in the schedule but in the live layer
     (so that it does not count in the table) - the round list and the
     match page, however, have to take it from there. */
  function liveLookup(live) {
    return function (r, h, v) {
      var l = live[r] || [];
      for (var i = 0; i < l.length; i++) {
        if (l[i] && l[i][0] === h && l[i][1] === v) return l[i];
      }
      return null;
    };
  }

  /* ===== Status bar error message =====
     When a round is in progress, the user cares that the live score is not
     updating. In a quiet period the stored score is up to date anyway, so
     there we only say how old it is. The question "is there a round in
     progress" is decided by the calling page, because each sees it from
     different data. */
  function errorReporter(cfg) {
    return function () {
      var st = document.getElementById(cfg.statusId || 'status');
      if (!st) return;
      st.className = 'err';
      st.textContent = cfg.isLive() ? statusLine.errorLive : statusLine.errorIdle(cfg.storedAt());
    };
  }

  /* ===== Player profile viewer (both leagues) =====
     The skeleton is the same: title, subtitle, loading indicator, staleness
     guard, error message. The two pages differ only in how a key becomes a
     NAME and DATA, and whether anything is left to fill in after drawing
     (on NB1 the missing points load afterwards, one by one).

     The staleness guard is not decoration: while the profile loads, the
     user may open another one - a response arriving later must not
     overwrite the newer one. So what counts is not the time of the call but
     whether this is STILL the current key. */
  function profileViewer(cfg) {
    var current = null;
    function show(key, mode) {
      cfg.view.show(function () { show(key, 'noop'); }, mode);
      current = key;
      if (cfg.mark) cfg.mark(key);
      cfg.view.open();
      document.getElementById('mTitle').textContent = cfg.name(key);
      document.getElementById('mSub').textContent =
        'Fordulónkénti teljesítmény — a sorra kattintva a pontok bontása';
      document.getElementById('mTabs').innerHTML = '';
      var body = document.getElementById('mBody');
      body.innerHTML = '<div class="loading">Profil betöltése…</div>';
      Promise.resolve().then(function () { return cfg.data(key); }).then(function (data) {
        if (current !== key) return;
        body.innerHTML = profileHTML(data);
        if (cfg.after) cfg.after(key, data);
      }, function (err) {
        if (current !== key) return;
        body.innerHTML = '<div class="loading" style="color:var(--lose)">' +
          'Nem sikerült betölteni — ' + esc(err && err.message) + '</div>';
      });
    }
    return show;
  }

  /* ===== Head-to-head view =====
     Opens on a click on a matrix cell. The two pages differ only in how an
     id becomes a name, and what has to be reset on opening. */
  function h2hViewer(cfg) {
    function show(a, b, mode) {
      cfg.view.show(function () { show(a, b, 'noop'); }, mode);
      if (cfg.prepare) cfg.prepare(a, b);
      cfg.view.open();
      var nameOf = cfg.name || function (x) { return x; };
      document.getElementById('mTitle').textContent = nameOf(a) + '  vs  ' + nameOf(b);
      document.getElementById('mSub').textContent =
        'Egymás elleni meccsek — sorra kattintva a meccs részletei';
      document.getElementById('mTabs').innerHTML = '';
      document.getElementById('mBody').innerHTML =
        '<div class="sqwrap one" style="max-width:none">' + cfg.content(a, b) + '</div>';
    }
    return show;
  }

  var activeIndicators = new WeakMap();
  function slowIndicator(target, delay) {
    delay = (delay == null) ? 500 : delay;
    // Only ONE indicator per place: when switching quickly between two
    // matches, two "frissítés…" labels would otherwise stand side by side on
    // the same subtitle, and the old clock would keep ticking.
    if (target) { var prev = activeIndicators.get(target); if (prev) prev(); }
    var startedAt = Date.now(), el = null, tick = null;
    var timer = setTimeout(function () {
      if (!target || !target.isConnected) return;
      el = document.createElement('span');
      el.className = 'frissjel';
      var write = function () {
        el.textContent = 'frissítés… ' +
          ((Date.now() - startedAt) / 1000).toFixed(1).replace('.', ',') + ' mp';
      };
      write();
      target.appendChild(el);
      tick = setInterval(write, 100);
    }, delay);
    function finish() {
      clearTimeout(timer);
      if (tick) clearInterval(tick);
      if (el && el.parentNode) el.parentNode.removeChild(el);
      if (target && activeIndicators.get(target) === finish) activeIndicators['delete'](target);
      return Date.now() - startedAt;
    }
    if (target) activeIndicators.set(target, finish);
    return finish;
  }

  /* ---------- closing changes (both leagues) ----------
     The two panels show THE SAME THING THE SAME WAY: on PL the change made
     at the moment of the closing, on NB1 the one made when the round was
     finalised. So the HTML is built here, in one place - written separately
     it had already drifted apart once (different title, different layout,
     different empty text).

     Both pages pass NORMALISED rows:
       {poszt, nev, klub, prof, elott, utan, dl}       - points change
       {tip:'csere', poszt, nev, klub, prof, irany, ert} - automatic substitution (PL)
     `prof` is the set of flags that makes the name clickable; without it
     (e.g. NB1's first rounds, where the player is not known) the name is
     plain text. `dl` is the difference, when "before -> after" is not
     known, only the change. */
  function attrsHTML(a){
    var s = '', k;
    for (k in (a || {})) if (a[k] != null && a[k] !== '') s += ' ' + k + '="' + esc(String(a[k])) + '"';
    return s;
  }
  function closingRowHTML(x){
    var d = (x.dl != null) ? x.dl : (x.utan - x.elott);
    return '<div class="zsor">'
      + (x.poszt ? '<span class="ppos">' + esc(x.poszt) + '</span>' : '')
      + (x.prof
          ? '<span class="znev kattint"' + attrsHTML(x.prof) + '>' + esc(x.nev)
            + (x.klub ? ' <span class="tm">' + esc(x.klub) + '</span>' : '') + '</span>'
          : '<span class="znev">' + esc(x.nev) + '</span>')
      + (x.tip === 'csere'
          ? (x.ert != null ? '<span class="zert">' + fmt(x.ert) + ' pont</span>' : '')
            + '<span class="zirany' + (x.irany === 'be' ? ' pos' : '') + '">'
            + (x.irany === 'be' ? 'beállt' : 'kikerült') + '</span>'
          : (x.elott != null ? '<span class="zert">' + fmt(x.elott) + ' → ' + fmt(x.utan) + '</span>' : '')
            + '<span class="zdiff ' + (d > 0 ? 'pos' : 'neg') + '">'
            + (d > 0 ? '+' : '') + fmt(d) + '</span>')
      + '</div>';
  }
  function closingList(groups, emptyText){
    var blocks = [];
    (groups || []).forEach(function (group){
      if (!group || !group.sorok || !group.sorok.length) return;
      blocks.push('<div class="zcsapat"><h3 class="kattint"' + attrsHTML(group.jelzok) + '>'
        + esc(group.nev) + '</h3>' + group.sorok.map(closingRowHTML).join('') + '</div>');
    });
    if (!blocks.length) return '<div class="loading">' + esc(emptyText) + '</div>';
    return '<div class="zlista">' + blocks.join('') + '</div>';
  }

  /* ---------- "Changes" tab (both leagues) ----------
     What the manager changed round by round, and HOW MUCH IT WAS WORTH:
     every row carries its points difference, and the bottom of the block
     their sum - which is EXACTLY the Guardiola measure for that round. That
     is the whole point of this tab: the number in the table can be derived,
     it does not have to be taken on trust.

     THE PAGE IS ONE COLUMN, and the rounds are in ASCENDING order - just as
     on the Rounds tab and everywhere else. Two columns of blocks starting
     with the newest made the eye zigzag, and the order went against every
     other view.

     Within a row the two right-hand columns have a FIXED WIDTH, so the
     numbers stand under each other - without it the points difference was
     somewhere else in every row, and the whole became unreadable.

     The rows come from the pages in NORMALISED form (the calculation lives
     in the collector, keretvaltozasok.json / draft_keretvaltozasok.json):
       {poszt, nev, klub, prof, cimke, elott, utan, ert, dl}
     `prof` is the set of flags that makes the name clickable; `cimke` the
     explanation (e.g. "kapitány" or "kezdő -> pad"); `elott`/`utan` the
     two values the difference came from; `ert` a single value when there
     are not two sides; `dl` the difference itself. */
  function changeValueHTML(x){
    if (x.elott != null) return fmt(x.elott) + ' → ' + fmt(x.utan);
    return x.ert != null ? fmt(x.ert) : '';
  }
  function changeRowHTML(x){
    // `dl` MAY BE MISSING: for a round not closed yet the change is already
    // known, but its points are not. Then the difference cell is EMPTY - not
    // "0", because that would claim it was worth nothing.
    if (x.dl == null)
      return '<div class="vasor' + (x.oszt ? ' ' + x.oszt : '') + '">'
        + (x.poszt ? '<span class="ppos">' + esc(x.poszt) + '</span>' : '<span class="ppos ures"></span>')
        + '<span class="vanev' + (x.prof ? ' kattint' : '') + '"' + (x.prof ? attrsHTML(x.prof) : '') + '>'
        + esc(x.nev) + (x.klub ? ' <span class="tm">' + esc(x.klub) + '</span>' : '') + '</span>'
        + (x.cimke ? '<span class="vacimke">' + esc(x.cimke) + '</span>' : '')
        + '<span class="vaert"></span><span class="zdiff"></span></div>';
    var d = x.dl || 0;
    return '<div class="vasor' + (x.oszt ? ' ' + x.oszt : '') + '">'
      + (x.poszt ? '<span class="ppos">' + esc(x.poszt) + '</span>' : '<span class="ppos ures"></span>')
      + '<span class="vanev' + (x.prof ? ' kattint' : '') + '"' + (x.prof ? attrsHTML(x.prof) : '') + '>'
      + esc(x.nev) + (x.klub ? ' <span class="tm">' + esc(x.klub) + '</span>' : '') + '</span>'
      + (x.cimke ? '<span class="vacimke">' + esc(x.cimke) + '</span>' : '')
      + '<span class="vaert">' + changeValueHTML(x) + '</span>'
      + '<span class="zdiff ' + (d > 0 ? 'pos' : d < 0 ? 'neg' : '') + '">'
      + (d > 0 ? '+' : '') + fmt(d) + '</span></div>';
  }
  /* group: {nev, guard, reszek:[{cim, sorok}], zaro:[sor], ures}
     `reszek` are the labelled sections (Eladva / Megvéve / Szerepváltás -
     sold / bought / role change), `zaro` the closing rows (on PL "A te
     döntéseid" and the automatic substitution).

     AN EMPTY GROUP IS SHOWN TOO: a round the manager did not touch is just
     as much an answer to the question as the others - and that is exactly
     why its measure is 0. If it were left out, the viewer would think the
     data was missing. */
  function changesList(groups, emptyText){
    if (!groups || !groups.length)
      return '<div class="loading">' + esc(emptyText) + '</div>';
    return '<div class="valtlista">' + groups.map(function (group){
      // An UNLABELLED `sorok` passed in one piece IS A VALID SHAPE TOO. Not a
      // convenience extension: the `?v=` only busts the cache of funtasy.js/css,
      // NOT of nb1/index.html - and the server answers a request for an old
      // `?v=` with the CURRENT funtasy.js. So an old page in a browser (one that
      // still passes `sorok`) can meet the NEW renderer: the round header would
      // show the GUARD, and under it "Nem változtatott a keretén." (no change) -
      // although three players were changed. While both shapes are accepted,
      // this cannot happen.
      var sections = (group.reszek || (group.sorok ? [{ cim: '', sorok: group.sorok }] : []))
        .filter(function (r){ return r.sorok && r.sorok.length; });
      var count = sections.reduce(function (n, r){ return n + r.sorok.length; }, 0);
      return '<div class="vakor">'
        + '<div class="vafej"><span>' + esc(group.nev) + '</span>'
        + (group.guard == null
           ? (group.megj ? '<span class="vamegj">' + esc(group.megj) + '</span>' : '')
           : '<span class="guardjel ' + (group.guard > 0 ? 'pos' : group.guard < 0 ? 'neg' : '') + '">'
             + signed(group.guard) + '</span>') + '</div>'
        + (count ? sections.map(function (r){
              return (r.cim ? '<div class="varescim">' + esc(r.cim) + '</div>' : '')
                     + r.sorok.map(changeRowHTML).join('');
            }).join('')
              : '<div class="vasor vaures"><span class="vanev">'
                + esc(group.ures || 'Nem változtatott a keretén.') + '</span></div>')
        + (group.zaro || []).map(changeRowHTML).join('')
        + (count && group.guard != null
           ? '<div class="vasor vaossz"><span class="ppos ures"></span>'
             + '<span class="vanev">' + esc(group.osszCim || 'Összesen') + '</span>'
             + '<span class="vacimke"></span>'
             + '<span class="vaert"></span><span class="zdiff '
             + (group.guard > 0 ? 'pos' : group.guard < 0 ? 'neg' : '') + '">'
             + signed(group.guard) + '</span></div>'
           : '')
        + '</div>';
    }).join('') + '</div>';
  }

  /* ===== ROUND PAGER =====
     One dropdown and two arrows: the same control stands above the closing
     panel of both leagues. It existed in two copies, with two separate
     state models - one computed the next round from the selected VALUE,
     the other from the INDEX - and the two panels' pagers had already
     drifted apart.
     The caller only says where to draw and what to do on a change.

     The operations: `fill(values, current)` fills the dropdown, `value()`
     says which round it is on. A dropdown has ONE pager: a repeated call
     returns the same one and does not bind the events again (the loading
     path may run more than once). */
  function roundPager(opts) {
    var sel = document.getElementById(opts.sel);
    if (!sel) return null;
    if (sel.__pager) return sel.__pager;
    var onChange = opts.onChange || function () {};
    function step(dir) {
      var i = sel.selectedIndex + dir;
      if (i < 0 || i >= sel.options.length) return;
      sel.selectedIndex = i;
      onChange(+sel.value);
    }
    sel.addEventListener('change', function () { onChange(+sel.value); });
    // The arrows stand NEXT TO the dropdown, not inside it; we listen on their
    // common parent, so each page's own layout can stay unchanged.
    var bar = sel.parentNode;
    if (bar) bar.addEventListener('click', function (e) {
      var g = e.target.closest && e.target.closest('[data-znav]');
      if (g) step(+g.getAttribute('data-znav'));
    });
    sel.__pager = {
      fill: function (values, current) {
        sel.innerHTML = values.map(function (r) {
          return '<option value="' + r + '">' + r + '. forduló</option>';
        }).join('');
        sel.value = String(current != null ? current : values[values.length - 1]);
      },
      value: function () { return +sel.value; }
    };
    return sel.__pager;
  }

  /* ---------- DETECTING A STALE PAGE ----------
     The `?v=` busts the cache of funtasy.js/css - NOT of THE PAGE'S OWN
     HTML. nb1/index.html, however, contains live logic (shared players,
     live squad records, match state), and an old HTML runs it by the old
     rules: a fix can be out while the viewer still sees the old behaviour -
     with nothing to tell them.

     So the page asks what the CURRENT version is (verzio.json), and if the
     page is older, it reloads ONCE. A sessionStorage gate protects against
     a loop: if the page is still old after the reload (e.g. an intermediate
     cache), it does not try again - better to stay quiet than to reload
     back and forth. */
  function reloadIfStale(){
    var sc = document.querySelector('script[src*="funtasy.js?v="]');
    var own = sc && +((sc.getAttribute('src').split('v=')[1] || '').split('&')[0]);
    if (!own) return;
    // verzio.json sits next to funtasy.js: its path is the script's own.
    // (A 404 resolves, it does not reject - a fallback chained on the
    // rejection never ran, and no subpage ever saw the version.)
    var base = sc.getAttribute('src').split('funtasy.js')[0];
    fetch(base + 'verzio.json?t=' + Date.now())
    .then(function (r){ return r && r.ok ? r.json() : null; }).then(function (j){
      if (!j || !j.v || +j.v <= own) return;
      var k = 'funtasy-ujratoltes';
      try { if (sessionStorage.getItem(k) === String(j.v)) return;
            sessionStorage.setItem(k, String(j.v)); } catch (e) {}
      // `location.reload()` does NOT bypass the HTTP cache: the page may get the
      // same OLD HTML back (the server hands it out for ten minutes), and the
      // loop guard then does not try again - the viewer is stuck on the old
      // page and only gets further with a manual refresh. So first the document
      // itself is fetched FRESH: `cache: 'reload'` overwrites the stored copy,
      // and the load that follows gets the new one. If that fetch fails, the
      // page is reloaded anyway - it cannot get worse than the old behaviour.
      var reload = function (){ location.reload(); };
      fetch(location.href, { cache: 'reload' }).then(reload, reload);
    }).catch(function(){});
  }

  /* Some of these helpers are only used INTERNALLY today (navHTML,
     footerHTML, profileHeaderHTML, stripAccents, lineupPercent,
     LINEUP_TITLE). They are deliberately kept in this shared layer: the
     planned summary page and the leaderboards will reuse exactly these
     (the same KEZD% rounding and the same explanatory text, the same
     accent-insensitive search) - written again there, there would be two
     truths again. The cost is ~100 bytes, the gain is not having to
     duplicate them later. */
    global.FunTasy = { create: create, esc: esc, fmt: fmt, played: played,
                     formatKickoff: formatKickoff, accToggle: accToggle,
                     accTable: accTable, accPreserve: accPreserve, LEAGUES: LEAGUES,
                     leagueById: leagueById, renderNav: renderNav, MESSAGES: MESSAGES,
                     PEOPLE: PEOPLE, personLookup: personLookup,
                     renderFooter: renderFooter,
                     breakdownMatchRow: breakdownMatchRow, closingList: closingList,
                     roundPager: roundPager, reloadIfStale: reloadIfStale,
                     changesList: changesList,
                     profileHTML: profileHTML, playerSearch: playerSearch,
                     profileLinkHTML: profileLinkHTML,
                     profileViewer: profileViewer, lineupPairHTML: lineupPairHTML,
                     matchArticle: matchArticle,
                     articleKindName: articleKindName,
                     articleList: articleList,
                     articleCardHTML: articleCardHTML,
                     watchMagazine: watchMagazine, MAGAZINE_NAME: MAGAZINE_NAME,
                     MAGAZINE_MOTTO: MAGAZINE_MOTTO, statusLine: statusLine,
                     onVisibleAgain: onVisibleAgain,
                     liveRefresher: liveRefresher, storedResponses: storedResponses,
                     backfillSquads: backfillSquads, clearBackfill: clearBackfill,
                     slowIndicator: slowIndicator, scoreHTML: scoreHTML,
                     viewStack: viewStack, makeFetcher: makeFetcher,
                     liveLookup: liveLookup, errorReporter: errorReporter,
                     h2hViewer: h2hViewer,
                     /* The previous names of what a page calls BEFORE its
                        reloadIfStale() line. The `?v=` busts the cache of this
                        file but not of the page's own HTML, so for a while a
                        cached older page can meet this newer file. With these
                        it still reaches reloadIfStale, which then reloads it
                        to the current page; without them it would stop at its
                        first call and never reload. */
                     LIGAK: LEAGUES, liga: leagueById, renderLablec: renderFooter,
                     SZEMELYEK: PEOPLE,
                     verzioOr: reloadIfStale };
})(window);
