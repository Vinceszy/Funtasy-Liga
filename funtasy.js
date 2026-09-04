/* FunTasy Liga - kozos megjelenito mag.
   Hasznalja: nb1/index.html (NB I Fantasy), pl/index.html (FPL Draft) es a
   kezdolap (index.html, ligavalaszto).

   Miert van kulon fajlban: a tabella, a matrix es a meccspanelek logikaja
   mindket oldalon ugyanaz volt, szo szerint lemasolva. Igy nem tudnak
   elcsuszni egymastol. Nincs build lepes - sima statikus fajl.

   A ket oldal adata azonos alaku:
     schedule = { "1": [[hazai, vendeg, hazai_pont, vendeg_pont], ...], ... }
   ahol a pont null, amig a meccs nincs lezarva. A resztvevok kulcsai
   tetszolegesek (az NB1-nel becenev, a PL-nel szam); a megjelenitest a
   hivo opcioi adjak: `label` (nev), `tag` (monogram a nev mogott),
   `matrixLabel` (a matrix tengelyei), `tiebreak` ('rg' = holtversenynel
   a szerzett pont dont, alapertelmezetten a pontkulonbseg),
   `onMatrixClick(a,b)` (a matrix-cella kattintasa - a hivo nyitja ra a
   sajat modaljat, tipikusan a h2hHTML(a,b) kimenetevel).

   ELO EREDMENY: a `live` overlay ugyanilyen alaku, de a benne levo
   eredmenyek NEM szamitanak bele a tabellaba es a matrixba - csak a
   meccspanelen jelennek meg, "elo" jelolessel. Igy a meg le nem zart
   fordulo nem latszik veglegesnek.

   A create()-en kivul ket nevter-szintu segito is exportalodik a
   pont-bontas accordionhoz (FunTasy.accToggle, FunTasy.accTable) -
   reszletek a fajl vegen. */
(function (global) {
  'use strict';

  /* ===== LIGAK - a bovites EGYETLEN helye =====
     Uj liga felvetele: egy uj bejegyzes ide + egy uj mappa a sajat
     index.html-jevel. A ligavalto sav (minden liga-oldal tetejen) es a
     kezdolap kartyai is ebbol a listabol keszulnek, tehat sehol mashol
     nem kell hozzanyulni. A `mappa` a webhely gyokeretol szamit; a
     `tema` a body-ra kerulo osztaly (funtasy.css liga-temai). */
  /* A `tipus` a liga JATEKMODJA, nem cimke: ez donti el, milyen szabalyok
     szerint mukodik a liga, es az oldalak ez alapjan adhatnak kulon
     megoldast (a body-ra `tipus-<ertek>` osztaly kerul, JS-bol pedig
     FunTasy.liga(id).tipus kerdezheto le).
       salary-cap - kozos jatekospiac arkerettel; ugyanaz a jatekos tobb
                    csapatban is lehet; van kapitany es cserepad-felezes
       draft      - kizarolagos tulajdon (egy jatekos egy csapatban);
                    nincs kapitany, a pad pontjai nem szamitanak */
  /* Az `eloPontok` azt mondja meg, hogy a liga forrasa MECCS KOZBEN is ad-e
     mar pontot, vagy csak a meccs vegen. Nem kozmetika: ettol fugg, mit
     szabad irni a 0 pontos jatekosrol a meccs alatt.
       true  (FPL) - percrol percre jon a pont, tehat a 0 azt jelenti, hogy
                     eddig nem volt pontot ero esemenye
       false (MLSZ) - a pontok csak a meccs utan kerulnek be, tehat a 0 meccs
                     kozben semmit nem jelent; nem szabad ugy fogalmazni,
                     mintha "eddig" nem szerzett volna pontot */
  var LIGAK = [
    { id: 'nb1', nev: 'NB1', mappa: 'nb1/', cim: 'NB1 salary cap fantasy',
      leiras: 'privát head-to-head · 8 csapat · 33 forduló',
      tipus: 'salary-cap', tipusNev: 'Salary cap', tema: 'liga-nb1',
      eloPontok: false },
    { id: 'pl', nev: 'PL', mappa: 'pl/', cim: 'PL draft fantasy',
      leiras: 'privát head-to-head · 10 csapat · 38 forduló',
      tipus: 'draft', tipusNev: 'Draft', tema: 'liga-pl',
      eloPontok: true }
  ];
  function liga(id) {
    for (var i = 0; i < LIGAK.length; i++) if (LIGAK[i].id === id) return LIGAK[i];
    return null;
  }

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
    // Monogram a nev mogott (pl. "Vince VS", "HolVanSalah?! VS") - ez a
    // resztvevo egyedi azonositoja, mindket ligaban ugyanaz a szemelyhez.
    var tag = opts.tag || function () { return ''; };
    var mgr = function (k) {
      var t = tag(k);
      return t ? ' <span class="mgr">' + esc(t) + '</span>' : '';
    };
    /* Nev + monogram egy sorban. A NEV kap ellipszist (.nv zsugorodik), a
       monogram sosem: korabban a levagas a sor vegen tortent, tehat eppen a
       monogramot ette meg - pedig szuk helyen az azonositja a csapatot.
       `belso`: a nev korule keruljon-e kattinthato burok. */
    var nevMgr = function (k, belso) {
      var nev = '<span class="nv">' + esc(label(k)) + '</span>';
      return (belso ? belso(nev) : nev) + mgr(k);
    };

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
        // Holtverseny: az NB1-nel a pontkulonbseg (KUL) dont, utana a
        // szerzett pont (SP); a PL-nel az FPL alappontozasa szerint a
        // szerzett pont az elso (tiebreak: 'rg').
        var t = (opts.tiebreak === 'rg')
          ? (b.Pont - a.Pont || b.RG - a.RG || b.GK - a.GK)
          : (b.Pont - a.Pont || b.GK - a.GK || b.RG - a.RG);
        return t || label(a.name).localeCompare(label(b.name), 'hu');
      });
    };

    // Csapatonkent osszesitett hatekonysag a LEZART meccsek forduloira -
    // ugyanabbol a korbol, amibol a tabella is szamol, tehat a ketto nem
    // csuszhat szet (elo/ideiglenes fordulo egyikbe sem szamit bele).
    function kezdOsszesito() {
      if (!opts.kezd) return null;
      var t = {};
      kor().forEach(function (r) {
        vegleges(r).forEach(function (m) {
          if (!played(m)) return;
          [m[0], m[1]].forEach(function (n) {
            var v = opts.kezd(n, r);
            if (!v) return;
            var c = t[n] || (t[n] = { sz: 0, le: 0 });
            c.sz += v.sz; c.le += v.le;
          });
        });
      });
      return t;
    }

    // Kumulalt Guardiola mutato UGYANARRA a korre, amibol a tabella szamol -
    // igy a ket szam nem csuszhat szet (elo/ideiglenes fordulo egyikbe sem
    // szamit bele). Az elso fordulora fogalmilag nincs ertek.
    function guardOsszesito() {
      if (!opts.guard) return null;
      var t = {};
      kor().forEach(function (r) {
        vegleges(r).forEach(function (m) {
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
      var kezd = kezdOsszesito(), guard = guardOsszesito();
      var h = '<tr><th></th><th>' + esc(opts.nameHeader || 'Szakvezető') +
        '</th><th>M</th><th>GY</th><th>D</th><th>V</th>' +
        '<th title="szerzett pont">SP</th><th title="kapott pont">KP</th>' +
        '<th title="pontkülönbség">KÜL</th><th>Pont</th>' +
        (kezd ? '<th title="' + KEZD_CIM + '">KEZD%</th>' : '') +
        (guard ? '<th title="' + esc(GUARD_CIM) + '">GUA</th>' : '') +
        '<th>Forma</th></tr>';
      api.computeTable().forEach(function (r, i) {
        var form = r.form.slice(-5).map(function (f) {
          return '<span class="dot ' + f + '"></span>';
        }).join('');
        // A nev csak ott kattinthato, ahol van mit megnyitni (keret-modal).
        var cella = nevMgr(r.name, opts.nameAttr && function (nev) {
          return '<span class="clickable" ' + opts.nameAttr(r.name) + '>' + nev + '</span>';
        });
        h += '<tr class="' + (i === 0 ? 'leader' : '') + '"><td class="rank">' + (i + 1) + '.</td>' +
          '<td class="name"><span class="nevsor">' + cella + '</span></td>' +
          '<td>' + r.M + '</td><td>' + r.GY + '</td><td>' + r.D + '</td><td>' + r.V + '</td>' +
          '<td>' + fmt(r.RG) + '</td><td>' + fmt(r.KG) + '</td>' +
          '<td class="' + (r.GK >= 0 ? 'pos' : 'neg') + '">' + fmt(r.GK) + '</td>' +
          '<td class="pont">' + r.Pont + '</td>' +
          (kezd ? (function () {
            var v = kezd[r.name], pc = v ? kezdSzazalek(v.sz, v.le) : null;
            return '<td class="kezdpc" title="' + (v ? fmt(v.sz) + ' / ' + fmt(v.le) + ' pont' : '') +
                   '">' + (pc == null ? '–' : pc + '%') + '</td>';
          })() : '') +
          (guard ? (function () {
            var g = guard[r.name];
            return '<td class="guard ' + (g == null ? '' : (g > 0 ? 'pos' : g < 0 ? 'neg' : '')) +
                   '" title="' + esc(GUARD_CIM) + '">' +
                   (g == null ? '–' : guardJelol(g)) + '</td>';
          })() : '') +
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
        var attr = opts.matchAttr ? ' ' + opts.matchAttr(m[0], m[1], r) : '';
        h += '<div class="match' + (elo ? ' elo' : '') + '"' + attr + '>' +
          '<div class="h ' + (van && hp > vp ? 'winner' : '') + '">' + nevMgr(m[0]) + '</div>' +
          '<div class="score">' +
            (van ? fmt(hp) + ' <span style="color:var(--dim)">:</span> ' + fmt(vp) +
                   (elo ? '<span class="elojel">élő</span>' : '')
                 : '<span class="na">— : —</span>') +
          '</div>' +
          '<div class="v ' + (van && vp > hp ? 'winner' : '') + '">' + nevMgr(m[1]) + '</div></div>';
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
      // matrixLabel: ha meg van adva (pl. monogram), az megy MINDKET
      // tengelyre; kulonben oszlopra a nev eleje, sorra a teljes nev.
      var mCim = function (n, sor) {
        if (opts.matrixLabel) return opts.matrixLabel(n);
        return sor ? label(n) : label(n).slice(0, 4);
      };
      var t = '<table><tr><th></th>' + names.map(function (n) {
        return '<th>' + esc(mCim(n, false)) + '</th>';
      }).join('') + '</tr>';
      names.forEach(function (a) {
        t += '<tr><th style="text-align:left">' + esc(mCim(a, true)) + '</th>';
        names.forEach(function (b) {
          if (a === b) { t += '<td class="x">—</td>'; return; }
          var c = M[a][b], n = c[0] + c[1] + c[2];
          // az egesz cella kattinthato: megnyitja a ket csapat egymas
          // elleni meccseinek listajat (opts.onMatrixClick)
          t += '<td class="mx ' + (n ? (c[0] > c[2] ? 'w' : (c[2] > c[0] ? 'l' : 'd')) : 'x') + '"' +
            ' data-mxa="' + esc(a) + '" data-mxb="' + esc(b) + '"' +
            ' title="' + esc(label(a)) + ' vs ' + esc(label(b)) + '">' +
            (n ? c[0] + '/' + c[1] + '/' + c[2] : '·') + '</td>';
        });
        t += '</tr>';
      });
      el(ids.matrix).innerHTML = t + '</table>';
    };

    // ---------- egymas elleni lista ----------
    // A ket csapat osszes egymas elleni parositasa a menetrendbol: lejatszott
    // meccsek eredmennyel es GY/D/V-vel (az "a" szemszogebol), elo meccs elo
    // jelolessel, jovobeliek "— : —"-mal. A sorok data-mh/mv/mr attributumot
    // kapnak: kattintasra a meccs-nezet nyilik a modalon belul (vissza
    // gombbal), mindket oldal sajat kezelojevel.
    // kis szurke % a h2h pontja mellett - elo meccsre nem, az meg valtozik
    function kezdJel(n, r, elo) {
      if (!opts.kezd || elo) return '';
      var v = opts.kezd(n, r), pc = v && kezdSzazalek(v.sz, v.le);
      return pc == null ? ''
        : ' <span class="kezdjel" title="' + KEZD_CIM + ': ' +
          fmt(v.sz) + ' / ' + fmt(v.le) + ' pont">' + pc + '%</span>';
    }

    // ugyanez a Guardiola mutatora. Elo meccsre nem irjuk ki: a fordulo
    // bontasa meg nincs meg, tehat ertek sincs.
    function guardJel(n, r, elo) {
      if (!opts.guard || elo) return '';
      var v = opts.guard(n, r);
      return !v ? '' : ' <span class="guardjel ' + (v.guard > 0 ? 'pos' : v.guard < 0 ? 'neg' : '')
        + '" title="' + esc(GUARD_CIM) + ' (a múlt heti kerettel ' + fmt(v.alt) + ')">'
        + guardJelol(v.guard) + '</span>';
    }

    /* Van-e Guardiola ertek egy szakvezetonek egy forduloban - EGY HELYEN.

       A feltetel nem trivialis: az ELO fordulora es a meg le nem zartra
       NINCS ertek (a fordulo kozbeni reszeredmenybol szamolt mutato hamis
       lenne, es a tabella sem szamol belole). Ezt a feltetelt HAROM hely
       hasznalja - a Fordulok ful oszlopa es mindket liga "Valtoztatasok"
       fule -, es ha barmelyik maskepp dontene, ugyanaz a fordulo az egyik
       helyen latszana, a masikon nem. Elesben pontosan ez allt elo: a
       PL 2. forduloja a Fordulok fulon meg ures volt, a Valtoztatasok fulon
       viszont mar allt benne szam. */
    api.guardErtek = function (name, r) {
      if (!opts.guard) return null;
      var ki = null;
      vegleges(r).forEach(function (m, i) {
        var own;
        if (m[0] === name) own = m[2];
        else if (m[1] === name) own = m[3];
        else return;
        var elo = false;
        if (own == null) {
          var L = eloMeccs(r, i);
          if (played(L)) { elo = true; own = m[0] === name ? L[2] : L[3]; }
        }
        ki = (!elo && own != null) ? opts.guard(name, r) : null;
      });
      return ki;
    };

    /* Egy szakvezeto fordulonkenti eredmenyei (a "Fordulok" ful) - KOZOS:
       a PL es az NB1 korabban ket majdnem azonos peldanyban tartotta.
       A sorra kattintva a meccs nyilik (data-mh/mv/mr, mint a h2h-ban). */
    api.fordulokHTML = function (name) {
      var h = '<table><tr><th>F</th><th>Ellenfél</th><th>Pont</th><th>Ell.</th>' +
        (opts.kezd ? '<th title="' + esc(KEZD_CIM) + '">KEZD%</th>' : '') +
        (opts.guard ? '<th title="' + esc(GUARD_CIM) + '">GUARD</th>' : '') +
        '<th>Eredm.</th></tr>';
      var gy = 0, d = 0, v = 0;
      kor().forEach(function (r) {
        vegleges(r).forEach(function (m, i) {
          var opp, own, ov, elo = false;
          if (m[0] === name) { opp = m[1]; own = m[2]; ov = m[3]; }
          else if (m[1] === name) { opp = m[0]; own = m[3]; ov = m[2]; }
          else return;
          // a folyo fordulo allasa az elo retegben van, nem a menetrendben
          if (own == null) {
            var L = eloMeccs(r, i);
            if (played(L)) { elo = true; own = m[0] === name ? L[2] : L[3]; ov = m[0] === name ? L[3] : L[2]; }
          }
          var res = '—', cls = '';
          if (own != null && ov != null) {
            if (own > ov) { res = 'GY'; cls = 'pos'; }
            else if (own < ov) { res = 'V'; cls = 'neg'; }
            else res = 'D';
            if (!elo) { if (res === 'GY') gy++; else if (res === 'V') v++; else d++; }
          }
          var kezdCella = '';
          if (opts.kezd) {
            var pc = null;
            if (!elo && own != null) {
              var kv = opts.kezd(name, r);
              pc = kv && kezdSzazalek(kv.sz, kv.le);
            }
            kezdCella = '<td class="kezdpc">' +
              (elo || own == null ? '' : (pc == null ? '—' : pc + '%')) + '</td>';
          }
          var guardCella = '';
          if (opts.guard) {
            // ugyanaz a feltetel, mint a Valtoztatasok fulon - lasd guardErtek
            var gv = api.guardErtek(name, r);
            guardCella = '<td class="guard ' +
              (gv ? (gv.guard > 0 ? 'pos' : gv.guard < 0 ? 'neg' : '') : '') + '">' +
              (gv ? guardJelol(gv.guard) : (elo || own == null ? '' : '—')) + '</td>';
          }
          h += '<tr class="clickable" data-mh="' + esc(m[0]) + '" data-mv="' + esc(m[1]) +
            '" data-mr="' + r + '"><td class="rank">' + r + '.</td>' +
            '<td class="name"><span class="nevsor">' + esc(label(opp)) + '</span></td>' +
            '<td>' + (own != null ? fmt(own) : '—') + '</td>' +
            '<td>' + (ov != null ? fmt(ov) : '—') + '</td>' + kezdCella + guardCella +
            '<td class="' + cls + '">' + res +
            (elo ? '<span class="elojel">élő</span>' : '') + '</td></tr>';
        });
      });
      return '<div style="font-size:13px;color:var(--dim);margin-bottom:8px">Mérleg: <b class="pos">' +
        gy + ' GY</b> · ' + d + ' D · <b class="neg">' + v + ' V</b> — ' + (gy * 3 + d) +
        ' pont</div>' + h + '</table>';
    };

    api.h2hHTML = function (a, b) {
      var sorok = '', gy = 0, d = 0, v = 0, jatszott = 0;
      kor().forEach(function (r) {
        vegleges(r).forEach(function (m, i) {
          var eleje = (m[0] === a && m[1] === b), vege = (m[0] === b && m[1] === a);
          if (!eleje && !vege) return;
          var ap = eleje ? m[2] : m[3], bp = eleje ? m[3] : m[2];
          var elo = false;
          if (ap == null) {
            var L = eloMeccs(r, i);
            if (played(L)) { ap = eleje ? L[2] : L[3]; bp = eleje ? L[3] : L[2]; elo = true; }
          }
          var res = '—', cls = '';
          if (ap != null && !elo) {
            jatszott++;
            if (ap > bp) { res = 'GY'; cls = 'pos'; gy++; }
            else if (ap < bp) { res = 'V'; cls = 'neg'; v++; }
            else { res = 'D'; d++; }
          }
          sorok += '<tr class="clickable" data-mh="' + esc(m[0]) + '" data-mv="' + esc(m[1]) +
            '" data-mr="' + r + '"><td class="rank">' + r + '.</td>' +
            '<td>' + (ap != null ? fmt(ap) : '—') + kezdJel(a, r, elo) + guardJel(a, r, elo) +
            (elo ? ' <span class="elojel">élő</span>' : '') + '</td>' +
            '<td>' + (bp != null ? fmt(bp) : '—') + kezdJel(b, r, elo) + guardJel(b, r, elo) + '</td>' +
            '<td class="' + cls + '">' + (elo ? 'élő' : res) + '</td></tr>';
        });
      });
      var merleg = jatszott
        ? '<div style="font-size:13px;color:var(--dim);margin-bottom:8px">' +
          esc(label(a)) + ' mérlege ' + esc(label(b)) + ' ellen: <b class="pos">' + gy +
          ' GY</b> · ' + d + ' D · <b class="neg">' + v + ' V</b></div>'
        : '<div style="font-size:13px;color:var(--dim);margin-bottom:8px">Még nem játszottak egymással.</div>';
      // a 2. fejlec-oszlopot a kozos CSS balra igazitja (nevoszlopnak), itt
      // viszont szamok vannak alatta jobbra igazitva - inline igazitas kell
      return merleg + '<table><tr><th>F</th><th style="text-align:right">' + esc(label(a)) +
        '</th><th style="text-align:right">' + esc(label(b)) +
        '</th><th>Eredm.</th></tr>' + sorok + '</table>';
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

  /* PONT-BONTAS ACCORDION - kozos mechanika mindket oldalnak.
     A keret-nezetek jatekos-soran (.plr[data-acc]) kattintva a sor ala
     nyilik egy panel, ami megmutatja, mibol allt ossze a jatekos heti
     pontja. A tartalom oldalfuggo (az NB1 az MLSZ game-player-stats
     vegpontjat, a PL az FPL event/{gw}/live explain mezojet hasznalja),
     ezert a hivo ad egy async `tolt` fuggvenyt, ami a kesz HTML-t adja.
     Itt csak a viselkedes kozos: egyszerre egy panel lehet nyitva,
     ujrakattintas zar, masik sorra kattintas oda nyit at. */
  function accToggle(row, tolt) {
    var nyitva = row.classList.contains('open');
    document.querySelectorAll('.accpanel').forEach(function (x) { x.remove(); });
    document.querySelectorAll('.plr.open').forEach(function (x) { x.classList.remove('open'); });
    if (nyitva) return;
    row.classList.add('open');
    var p = document.createElement('div');
    p.className = 'accpanel';
    // A panel ALLAPOTA jelzoben all, nem a szovegebol talaljuk ki: az
    // ujrarajzolas (accOrzo) ez alapjan dont, hogy megorizze-e. Csak a
    // 'kesz' panelt szabad valtozatlanul visszatenni.
    p.dataset.allapot = 'tolt';
    p.innerHTML = '<div class="accload">Bontás betöltése…</div>';
    row.insertAdjacentElement('afterend', p);
    Promise.resolve().then(tolt).then(function (html) {
      if (!row.classList.contains('open') || !p.isConnected) return;
      p.dataset.allapot = html ? 'kesz' : 'hiba';
      p.innerHTML = html || '<div class="accload">A pontok bontása nem érhető el ehhez a játékoshoz.</div>';
    }, function (hiba) {
      if (!row.classList.contains('open') || !p.isConnected) return;
      p.dataset.allapot = 'hiba';
      // Az OKOT is kiirjuk. A lekero (FunTasy.lekero) mindharom utat
      // megprobalja - direkt, corsproxy, allorigins -, es a hibauzenetbe
      // beleirja, melyik miert nem ment ("corsproxy:HTTP 429",
      // "direkt:CORS", "allorigins:idotullepes"). Enelkul a felhasznalo es
      // a fejleszto is csak annyit lat, hogy "nem sikerult", es nem lehet
      // eldonteni, halozat-e, proxy-e, vagy az API valtozott.
      var ok = hiba && hiba.message ? String(hiba.message) : '';
      p.innerHTML = '<div class="accload">A bontás lekérése nem sikerült.'
        + (ok ? '<br><span class="accmiert">' + esc(ok) + '</span>' : '') + '</div>';
    });
  }

  /* Bontas-tabla: sorok = [{name, value, points}]. A points lehet szam
     vagy kesz szoveg (pl. "×2" a kapitanynal). A 0 pontos sorokat a hivo
     szuri ki - az MLSZ felulete is csak a pontot ero esemenyeket mutatja.
     Ha nincs egyetlen pontot ero sor sem, az `ures` szoveg jelenik meg: azt
     a hivo szamolja ki, mert az ok oldalanként mas adatbol derul ki (meg nem
     kezdodott a meccs / zajlik / lejatszotta pont nelkul / nem lepett palyara). */
  /* Egy sor kaphat allapot-jelzest: `jelzes` a szinosztaly toldaleka
     (pl. "valtozik" -> b-valtozik), `megjegyzes` a nev melle kerulo rovid
     szoveg. A PL-oldal bonusz-sora hasznalja: az FPL a bonuszt a meccs
     alatt is szamolja, es csak kesobb veglegesiti. A szin egyedul nem
     ertheto, ezert mindig szoveg is tartozik hozza. */
  /* Ujrarajzolas a NYITOTT bontas megorzesevel.

     A meccs- es keret-nezetek utolag frissulnek: beer a percre friss keret,
     a jatszott percek, az elo pontok - ilyenkor a #mBody teljes tartalma
     ujra keszul, es a nyitott accordion eltunt alola. A felhasznalonak ugy
     nezett ki, mintha a "Bontas betoltese..." utan magatol visszazarodott
     volna, es ujra meg kellett nyitnia. (Bejelentett hiba.)

     A sort a data-* jelzoibol kepzett kulcs azonositja (rendezve, tehat a
     sorrend nem szamit), a panel tartalmat pedig valtozatlanul visszatesszuk
     - igy nincs se villanas, se ujabb lekeres. */
  function accKulcs(el) {
    var d = el.dataset, k = [], x;
    for (x in d) k.push(x + '=' + d[x]);
    return k.sort().join('|');
  }
  function accOrzo(rajzol) {
    var nyitva = document.querySelector('.plr.open[data-acc]');
    var panel = nyitva && nyitva.nextElementSibling;
    if (panel && !panel.classList.contains('accpanel')) panel = null;
    var kulcs = nyitva ? accKulcs(nyitva) : null;
    var allapot = panel ? panel.dataset.allapot : null;
    var html = (allapot === 'kesz') ? panel.innerHTML : null;
    rajzol();
    if (kulcs == null) return;
    var sorok = document.querySelectorAll('.plr[data-acc]'), i;
    for (i = 0; i < sorok.length; i++) {
      if (accKulcs(sorok[i]) !== kulcs) continue;
      // KESZ tartalom: valtozatlanul visszateheto - se villanas, se ujabb keres.
      if (html != null) {
        sorok[i].classList.add('open');
        var uj = document.createElement('div');
        uj.className = 'accpanel';
        uj.dataset.allapot = 'kesz';
        uj.innerHTML = html;
        sorok[i].insertAdjacentElement('afterend', uj);
        return;
      }
      // MEG TOLT: a regi keres az elavult sorra fut ki, tehat ujra kell inditani.
      if (allapot === 'tolt') { sorok[i].click(); return; }
      // HIBA: NEM orizzuk meg. Egy atmeneti hiba igy ragadt volna be, es a
      // sor nyitva maradt volna - a kovetkezo kattintas becsukta volna
      // ahelyett, hogy ujraprobalja. (Bejelentett hiba: "a pontok bontasa
      // nem erheto el" / "a bontas lekerese nem sikerult" ott maradt.)
      return;
    }
  }

  function accTable(sorok, ures) {
    if (!sorok || !sorok.length)
      return '<div class="accload">' + esc(ures || 'Ehhez a fordulóhoz nincs rögzített esemény.') + '</div>';
    var h = '<table class="acctable"><tr><th>Esemény</th><th>Érték</th><th>Pont</th></tr>';
    for (var i = 0; i < sorok.length; i++) {
      var s = sorok[i];
      var szam = (typeof s.points === 'number');
      var cls = szam ? (s.points > 0 ? 'pos' : (s.points < 0 ? 'neg' : '')) : '';
      var jel = s.jelzes ? ' b-' + s.jelzes : '';
      if (jel) cls += jel;
      var megj = s.megjegyzes
        ? ' <span class="sormegj' + jel + '">(' + esc(s.megjegyzes) + ')</span>' : '';
      h += '<tr><td class="ev">' + esc(s.name) + megj + '</td>' +
           '<td>' + (s.value == null || s.value === '' ? '' :
                     (typeof s.value === 'number' ? fmt(s.value) : esc(String(s.value)))) + '</td>' +
           '<td class="' + cls + '">' + (szam ? fmt(s.points) : esc(String(s.points))) + '</td></tr>';
    }
    return h + '</table>';
  }

  /* ===== Statuszsav-szovegek (a fejlec alatti sor) =====
     Mindket oldal INNEN veszi a mondatait, kulonben ugyanarra az allapotra
     ketfele megfogalmazas kerulne ki. Korabban a "Frissitve" szo a ket
     oldalon mast jelentett: az NB1-en az ellenorzes idejet, a PL-en a
     tarolt fajl korat - ez volt a legfelrevezetobb.
     Negy allapot van: lekeres alatt / elo fordulo friss adattal / nincs
     folyo fordulo / az elo lekeres nem sikerult. */
  var ora = function (d) {
    return new Date(d).toLocaleTimeString('hu-HU', { hour: '2-digit', minute: '2-digit' });
  };
  var datumOra = function (d) {
    return new Date(d).toLocaleString('hu-HU',
      { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };
  var statusz = {
    keres: function (reszlet) { return 'Élő állás lekérése…' + (reszlet ? ' ' + reszlet : ''); },
    elo: function (fordulo, mikor) {
      return 'Élő állás — ' + fordulo + '. forduló · frissítve ' + ora(mikor) +
             ' (a tabella csak lezárt fordulókból számol)';
    },
    naprakesz: function (mikor) { return 'Naprakész · ellenőrizve ' + ora(mikor); },
    // Ezt a szoveget a folyo fordulora Vince fogalmazta - ne irjuk at.
    hibaElo: 'Automata lekérés hiba: az állások a forduló végén frissülnek.',
    hibaNyugodt: function (mentve) {
      return 'Az élő frissítés most nem elérhető — a tárolt állás látható' +
             (mentve ? ' (mentve: ' + datumOra(mentve) + ')' : '') + '.';
    },
    betoltesHiba: function (mi, hiba) {
      return 'Nem sikerült betölteni a liga adatait (' + mi + '): ' + hiba;
    },
    datumOra: datumOra
  };

  /* Ligavalto sav. `aktiv` az eppen nyitott liga id-je (a kezdolapon null),
     `gyoker` a webhely gyokerehez vezeto relativ ut ('../' egy liga-oldalrol,
     '' a kezdolaprol) - a GitHub Pages aloldalon szolgal ki, ezert nem lehet
     abszolut '/' utakat hasznalni. */
  function navHTML(aktiv, gyoker) {
    gyoker = gyoker || '';
    var h = '<a class="markanev" href="' + gyoker + '">FunTasy</a><span class="ligak">';
    for (var i = 0; i < LIGAK.length; i++) {
      var l = LIGAK[i];
      h += '<a class="ligalink' + (l.id === aktiv ? ' on' : '') + '" href="' + gyoker + l.mappa +
           '" title="' + esc(l.cim) + '">' + esc(l.nev) + '</a>';
    }
    return h + '</span>';
  }
  /* ===== Lablec =====
     Minden oldal aljan ugyanaz a sor. Azert kozos, mert harom oldalra
     lemasolva a kovetkezo linknel mar biztosan elcsuszna valamelyik. */
  /* A jatekos meccse a pont-bontas folott: "ARS 2-1 BRE" + jobbra egy
     allapot ("70. perc" / "vege" / "meg nem kezdodott"). KOZOS a ligak
     kozott - az adat (honnan jon az allas es mi a jobb oldali cimke)
     ligankenti adapter dolga. 0-0-t sosem talalunk ki: ha nincs eredmeny
     (hp == null), csak a ket klub nevet irjuk ki. */
  /* ===== Kezdoallitasi hatekonysag =====
     Mennyit hozott a felallitott kezdo abbol, amennyit a keretbol ki
     lehetett volna hozni. A SZAMITAS ligankenti adapter dolga (NB1: a
     gyujto szamolja a fix pad-szaballyal es a kapitannyal; PL: a bongeszo
     a formacio-szabalyokkal) - itt csak a kozos megjelenites el.
     A hook: opts.kezd(name, fordulo) -> {sz, le} | null. */
  var KEZD_CIM = 'Kezdőállítási hatékonyság — a keretből elérhető pontok ' +
                 'hány százalékát hozta a beállított kezdő';

  /* A "Guardiola mutato": mennyivel lett tobb/kevesebb pont a keret-
     valtoztatas utan. guard = a MOSTANI keret pontja MINUSZ a MULT HETI
     kerete UGYANEBBEN a forduloban - vagyis "mi lett volna, ha hozza sem
     nyulok". Negativ ertek: a valtoztatas pontba kerult.
     A hook: opts.guard(name, fordulo) -> {teny, alt, guard} | null. */
  var GUARD_CIM = 'Guardiola mutató — mennyivel hozott többet a keretváltoztatás,'
                + ' mint ha a múlt heti kerethez hozzá sem nyúlsz';
  var guardJelol = function (g) { return (g > 0 ? '+' : '') + fmt(g); };
  function kezdSzazalek(sz, le) {
    return le > 0 ? Math.round(100 * sz / le) : null;
  }

  /* A meccs-fejlec hatekonysag-sora: a ket ertek a SAJAT terfelehez
     igazodik (bal/jobb), ahogy a fejlec minden mas adata - kozepen a
     cimke. Ures, ha egyik oldalon sincs ertek. */
  function kezdParHTML(va, vb, elo) {
    var egy = function (x) {
      var pc = x && kezdSzazalek(x.sz, x.le);
      return pc == null ? '–'
        : pc + '% <span class="kezdresz">(' + fmt(x.sz) + '/' + fmt(x.le) + ')</span>';
    };
    var a = egy(va), b = egy(vb);
    if (a === '–' && b === '–') return '';
    return '<div class="kezdsor" title="' + esc(KEZD_CIM) + '">' +
      '<span class="kezdbal">' + a + '</span>' +
      '<span class="kezdcim">kezdőállítás' +
      (elo ? ' <span class="elojel">élő</span>' : '') + '</span>' +
      '<span class="kezdjobb">' + b + '</span></div>';
  }

  /* ===== Jatekosprofil (kozos reteg) =====
     A profil szerkezete a ket ligaban ugyanaz: egy fejlec (ki ez a jatekos)
     es egy fordulonkenti lista (ellenfel, allas, pont, es hogy KINEL volt).
     Ami ligankent mas, az kizarolag az adat FORRASA - ezert a hivo egy kesz
     `adat` objektumot ad at, a megjelenites pedig itt, egyetlen helyen el.
     Igy a ket oldal nem irhat ugyanarrol ketfelet.

     adat = {
       nev, klub, poszt,
       cimkek: ['U21', ...],              // a nev melle kerulo rovid jelolok
       tenyek: [{cimke, ertek}],          // fejlec-adatok (osszpont, ar, ...)
       sorok: [{
         r,                               // a fordulo szama
         ellenfel,                        // az ellenfel klub rovidneve (vagy null)
         hazai,                           // true = otthon, false = idegenben, null = nem tudjuk
         hp, vp,                          // a meccs allasa, MINDIG hazai-vendeg sorrendben
         pont,                            // a jatekos alappontja (null = nincs adat)
         jegyzet,                         // a pont helyett kiirando szoveg, ha nincs pont
         tulajok: [{nev, szerep}]         // kinel volt; ures tomb = senkinel
       }],
       senkinel                           // mit irjunk ki ures `tulajok` eseten
     }

     A sorok lenyithatok: a hivo a `.plr[data-acc]` kattintast a sajat
     bontas-toltojere koti (accToggle), pont ugy, mint a keret-nezetben. */
  /* A pont-bontas aljan allo sor, ami a teljes profilt nyitja meg. A hivo
     adja az adat-attributumokat, mert ligankent mas kell hozza (az NB1-nek
     a cp-azonosito es a nev, a PL-nek az elem-azonosito) - a szoveg es a
     kinezet viszont kozos. A profilon BELUL nem tesszuk ki: ott mar ott
     vagy. */
  function profilNyitoHTML(attrs) {
    return '<div class="profnyito"' + (attrs || '') + '>Teljes játékosprofil <span>›</span></div>';
  }

  function profilFejHTML(adat) {
    // ugyanazok a jelolok, mint a keret-soraiban: a magyar jatekost zaszlo
    // jelzi, a tobbi rovid cimke a kek chip - kulonben ugyanaz az informacio
    // ket helyen ketfelekeppen nezne ki
    var cimkek = (adat.magyar ? '<span class="flag" title="magyar"></span>' : '')
      + (adat.cimkek || []).map(function (c) {
          return '<span class="u21">' + esc(c) + '</span>';
        }).join('');
    var tenyek = (adat.tenyek || []).map(function (t) {
      return '<div class="ptny"><span>' + esc(t.cimke) + '</span><b>' +
             (typeof t.ertek === 'number' ? fmt(t.ertek) : esc(String(t.ertek))) + '</b></div>';
    }).join('');
    return '<div class="proffej">' +
      '<div class="profnev">' +
        (adat.poszt ? '<span class="ppos">' + esc(adat.poszt) + '</span>' : '') +
        '<b>' + esc(adat.nev || '') + '</b>' +
        (adat.klub ? '<span class="tm">' + esc(adat.klub) + '</span>' : '') + cimkek +
      '</div>' + (tenyek ? '<div class="ptenyek">' + tenyek + '</div>' : '') + '</div>';
  }

  /* A tulajdonos szerepenek NEVE egy helyen. A hivo strukturaltan adja at
     (kezdo / kapitany logikai mezok), nem kesz magyar szoveget - igy a
     szohasznalat egy helyen all, es az aranyokat is ebbol lehet szamolni,
     nem szoveg-egyeztetessel. A kapitany egyben kezdo is. */
  function szerepNev(t) {
    return t.kapitany ? 'kapitány' : (t.kezdo ? 'kezdő' : 'pad');
  }

  /* A ligara vetitett aranyok - CSAK SALARY CAP ligaban.
     DRAFT ligaban ennek nincs ertelme: ott egy jatekos pontosan egy
     szakvezetonel lehet (vagy senkinel), tehat a "keret %" mindig 1/N vagy
     0 lenne, a kapitany pedig nem is letezik. Ez nem az NB1 es a PL
     kulonbsege, hanem a liga TIPUSAe - ezert a `tipus` mezo donti el
     (funtasy.js -> LIGAK), nem a liga azonositoja.
     A nevezo a fordulo TENYLEGES keretszama, nem beegetett szam: ha egy
     fordulobol hianyzik valakinek a kerete, a beegetett szam lefele
     torzitana. A harom szam egymasba agyazodik: keret >= kezdo >= kapitany. */
  function aranyHTML(s, salaryCap) {
    var t = s.tulajok || [];
    if (!salaryCap || !s.keretszam || !t.length) return '';
    var kezdo = 0, kap = 0;
    for (var i = 0; i < t.length; i++) {
      if (t[i].kezdo || t[i].kapitany) kezdo++;
      if (t[i].kapitany) kap++;
    }
    var pc = function (x) { return Math.round(100 * x / s.keretszam) + '%'; };
    return '<span class="parany" title="a forduló ' + s.keretszam +
      ' keretére vetítve — a kapitány is kezdő">' +
      'keret <b>' + pc(t.length) + '</b> · kezdő <b>' + pc(kezdo) +
      '</b> · kapitány <b>' + pc(kap) + '</b></span>';
  }

  /* Egy fordulo sora. Az allast MINDIG hazai-vendeg sorrendben kapjuk, a
     "(h)" / "(i)" jeloli, melyik oldalon allt a jatekos klubja - igy az
     eredmeny ugyanugy olvashato, mint barhol maskul az oldalon, es nem kell
     fejben forgatni. */
  /* Egy fordulo meccse(i) a sor nev-cellajaban. Rendes esetben egy meccs
     van: ilyenkor az ellenfel es a palya a nev-cellaban, az allas a sajat
     oszlopaban all - igy a szamok egymas ala igazodnak. DUPLA FORDULOBAN
     (a PL-ben elofordul) egy klub ketszer jatszik: ott a ket meccs egymas
     mellett, allassal egyutt a nev-cellaba kerul, es az allas-oszlop ures
     marad. Inkabb legyen a ritka eset kicsit maskepp tordelve, mint hogy a
     masodik meccs eltunjon. */
  function profilMeccsekHTML(mk) {
    if (!mk.length) return { nev: '—', allas: '' };
    var egy = function (m) {
      var hol = m.hazai == null ? '' : (m.hazai ? '(h)' : '(i)');
      var all = (m.hp == null || m.vp == null) ? '' : ' ' + fmt(m.hp) + '–' + fmt(m.vp);
      return esc(m.ellenfel || '—') + (hol ? ' ' + hol : '') + all;
    };
    if (mk.length > 1)
      return { nev: mk.map(egy).join(' <span class="pelval">·</span> '), allas: '' };
    var m = mk[0];
    return {
      nev: esc(m.ellenfel || '—') +
        (m.hazai == null ? '' : ' <span class="tm">' + (m.hazai ? 'otthon' : 'idegenben') + '</span>'),
      allas: (m.hp == null || m.vp == null) ? ''
        : '<span class="pallas">' + fmt(m.hp) + '–' + fmt(m.vp) + '</span>'
    };
  }

  function profilSorHTML(s, senkinel, salaryCap) {
    var mk = s.meccsek || [];
    var m = profilMeccsekHTML(mk);
    // JOVOBELI fordulonal a tulajdonos-sor URES marad: azt, hogy kinel lesz,
    // nem tudjuk - a "senkinel" / "szabadugynok" ott allitas lenne, nem adat.
    var tulaj = (s.tulajok && s.tulajok.length)
      ? s.tulajok.map(function (t) {
          return '<span class="ptul"><b>' + esc(t.nev) + '</b> · ' + esc(szerepNev(t)) + '</span>';
        }).join('')
      : (s.jovo ? '' : '<span class="ptul nincs">' + esc(senkinel || '–') + '</span>');
    var arany = aranyHTML(s, salaryCap);
    var pont = (s.pont == null)
      ? '<span class="pjegyzet">' + esc(s.jegyzet || '—') + '</span>'
      : fmt(s.pont);
    return '<div class="plr profsor" data-acc="1" data-pr="' + s.r + '">' +
      '<span class="ppos">' + s.r + '.</span>' +
      '<span class="nm">' + m.nev + '<span class="accarr">▼</span></span>' +
      m.allas +
      '<span class="pts">' + pont + '</span>' +
      '<span class="ptulajok">' + tulaj + arany + '</span>' +
    '</div>';
  }

  function profilHTML(adat) {
    var sorok = adat.sorok || [];
    if (!sorok.length)
      return profilFejHTML(adat) +
        '<div class="loading">Ehhez a játékoshoz még nincs fordulónkénti adat.</div>';
    var l = liga(adat.liga), salaryCap = !!l && l.tipus === 'salary-cap';
    return profilFejHTML(adat) +
      '<div class="proflista">' + sorok.map(function (s) {
        return profilSorHTML(s, adat.senkinel, salaryCap);
      }).join('') + '</div>';
  }

  function bontasMeccsSor(m) {
    if (!m || !m.hazai || !m.vendeg) return '';
    var allas = (m.hp == null || m.vp == null)
      ? esc(m.hazai) + '\u2013' + esc(m.vendeg)
      : esc(m.hazai) + ' <b>' + fmt(m.hp) + '\u2013' + fmt(m.vp) + '</b> ' + esc(m.vendeg);
    return '<div class="bontasmeccs"><span>' + allas + '</span>' +
           '<span class="ora">' + esc(m.jobb || '') + '</span></div>';
  }

  /* ===== Fooldali jatekoslista: kereso + oszlop-szuro + rendezes =====
     Mindket ligaban ugyanaz a viselkedes, csak az adat mas: a hivo ad egy
     `adat()` fuggvenyt, ami a mar betoltott fajlokbol osszerakja a listat,
     es egy `nyit(id)`-t, ami a profilt megnyitja.

     Harom fele szukites, mert harom fele kerdes van:
       - a KERESO a nevben es a klubban is keres (nem kell elore tudni,
         melyikre gondolsz), es ekezet nelkul is talal;
       - a KLUB/POSZT szuro egy oszlop tartalmara szurit (pl. "csak az MTK");
       - a FEJLEC-re kattintva at lehet rendezni barmelyik oszlop szerint.
     A lista alapbol a legjobb `limit` sort mutatja - a teljes mezony 385-612
     sor, azt feleslegesen a DOM-ba tenni -, de a szures es a kereses MINDIG
     a teljes mezonyben fut, kulonben pont arra lenne alkalmatlan, amire kell. */
  function ekezetlen(x) {
    return String(x == null ? '' : x).toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  /* Kinel van MOST. Salary cap ligaban tobb szakvezetonel is lehet, es a
     nevek nem fernek ki egy sorba - a "+2" viszont pont a legfontosabb
     resze, ezert az KULON all es SOSEM vagodik le; a nevek rovidulnek
     helyette. (Elobb egyben volt, es a CSS pont a darabszamot nyelte el.) */
  /* A szakvezetot MONOGRAMMAL jeloljuk (ugyanaz a `.tag` cimke, mint a
     tabellaban): igy negy is kifér oda, ahova ket teljes nev sem fert. A
     teljes nev a `title`-ben marad, es a profil ugyis kiirja.
     A hivo `{nev, jel}` parokat ad; ha nincs monogram, a nev a tartalek. */
  function tulajHTML(tulajok, szabadSzo) {
    var t = tulajok || [];
    // Senkinel: rovid jel, nem szo. Az oszlop szuk, es a "szabadugynok"
    // ott csak helyet foglalt; a szuro legorduloben marad az olvashato szoveg.
    if (!t.length)
      return '<span class="jltulaj nincs">' + esc(szabadSzo || '–') + '</span>';
    var mutat = t.slice(0, 4), tobb = t.length - mutat.length;
    return '<span class="jltulaj"><span class="jlnev">' + mutat.map(function (x) {
      return x.jel
        ? '<span class="tag" title="' + esc(x.nev) + '">' + esc(x.jel) + '</span>'
        : esc(x.nev);
    }).join(' ') + '</span>' +
      (tobb ? '<span class="jltobb">+' + tobb + '</span>' : '') + '</span>';
  }

  /* Az oszlopok egy helyen: a fejlec, a rendezes es a sor is ebbol keszul,
     tehat nem tud szetcsuszni. `szam: true` -> elso kattintasra csokkeno. */
  var JL_OSZLOP = [
    { kulcs: 'poszt', cim: 'Poszt', oszt: 'ppos', szuro: 'lista', szuroCim: 'Minden poszt',
      cella: function (p) {
        return p.poszt ? '<span class="ppos">' + esc(p.poszt) + '</span>' : '<span class="ppos"></span>'; } },
    // a nevre a kereso szur (reszlet-egyezessel, ekezet nelkul is) - egy
    // legordulo 400-600 nevvel hasznalhatatlan lenne
    { kulcs: 'nev',   cim: 'Játékos', oszt: 'nm', cella: function (p) {
        return '<span class="nm">' + esc(p.nev) +
          (p.u21 ? ' <span class="u21">U21</span>' : '') + '</span>'; } },
    { kulcs: 'klub',  cim: 'Klub', oszt: 'jlklub', szuro: 'lista', szuroCim: 'Minden klub',
      cella: function (p) {
        return '<span class="jlklub">' + esc(p.klub || '') + '</span>'; } },
    { kulcs: 'tulaj', cim: 'Kinél van', oszt: 'jltulaj', szuro: 'tulaj', szuroCim: 'Mindegy',
      cella: function (p, o) { return tulajHTML(p.tulajok, o.szabad); } },
    // Keret%: a kereteknek hany szazalekaban van benne MOST. Csak salary cap
    // ligaban van ertelme (draftban mindig 1/N vagy 0), ezert a hivo keri.
    { kulcs: 'kpc',   cim: 'Keret%', oszt: 'jlkpc', szam: true, szuro: 'min', szuroCim: 'Min. keret%',
      cella: function (p) {
        return '<span class="jlkpc">' + (p.kpc == null ? '' : Math.round(p.kpc) + '%') + '</span>'; } },
    // Ar: csak salary cap ligaban van ertelme (a draftban nem veszel
    // jatekost). A szuro itt FELSO korlat - a kerdes az, hogy mi fer bele
    // a kerembe, nem az, hogy mi a draga.
    { kulcs: 'ar',    cim: 'Ár', oszt: 'jlar', szam: true, szuro: 'max', szuroCim: 'Max. ár',
      cella: function (p) {
        return '<span class="jlar">' + (p.ar == null ? '' : fmt(p.ar)) + '</span>'; } },
    { kulcs: 'pts',   cim: 'Pont', oszt: 'pts', szam: true, szuro: 'min', szuroCim: 'Min. pont',
      cella: function (p) {
        return '<span class="pts">' + fmt(p.pts || 0) + '</span>'; } }
  ];
  // A ket kulonleges szuroertek. NEM vezerlokarakterrel jeloljuk: a NUL-t a
  // HTML-elemzo kicsereli, es a legordulo erteke sosem egyezne meg azzal,
  // amit a szuro var - a "Valakinel" nemán ures listat adott tole.
  // A "@@" elotag viszont szakvezeto-nevkent nem fordulhat elo.
  var JL_SZABAD = '@@szabad';           // senkinel sincs
  var JL_VALAKI = '@@valaki';           // legalabb egy tulajdonos

  function jlErtek(p, kulcs) {
    if (kulcs === 'pts' || kulcs === 'ar' || kulcs === 'kpc') return p[kulcs] || 0;
    if (kulcs === 'tulaj') return (p.tulajok && p.tulajok[0] && p.tulajok[0].nev) || '';
    return p[kulcs] || '';
  }

  /* Lapozo oldalszamokkal. Egyesevel kattintgatni 10 oldalon at nem
     hasznalhato, ezert az elso es az utolso oldal MINDIG latszik, koztuk az
     aktualis kornyezete, a kihagyott reszen egy "…". Igy barhova ket
     kattintasbol el lehet jutni, es latszik, hany oldal van osszesen. */
  function lapozoHTML(lap, lapok) {
    if (lapok <= 1) return '';
    var jel = {}, i;
    jel[0] = jel[lapok - 1] = 1;
    for (i = lap - 2; i <= lap + 2; i++) if (i >= 0 && i < lapok) jel[i] = 1;
    var szamok = Object.keys(jel).map(Number).sort(function (a, b) { return a - b; });
    var h = '<button class="jllapoz nyil" data-ugras="' + (lap - 1) +
      '" type="button"' + (lap === 0 ? ' disabled' : '') + ' title="Előző">‹</button>';
    var elozo = null;
    for (i = 0; i < szamok.length; i++) {
      var n = szamok[i];
      if (elozo !== null && n > elozo + 1) h += '<span class="jlkihagy">…</span>';
      h += '<button class="jllapoz' + (n === lap ? ' most' : '') +
        '" data-ugras="' + n + '" type="button">' + (n + 1) + '</button>';
      elozo = n;
    }
    return h + '<button class="jllapoz nyil" data-ugras="' + (lap + 1) +
      '" type="button"' + (lap >= lapok - 1 ? ' disabled' : '') + ' title="Következő">›</button>';
  }

  function jatekosKereso(opts) {
    var doboz = document.getElementById(opts.doboz);
    if (!doboz) return null;
    var limit = opts.limit || 40;
    // A hivo megmondhatja, mely oszlopokat kéri (pl. a PL draftban nincs ar).
    // Alapbol mind, az ar nelkul - azt kerni kell.
    var oszlopok = JL_OSZLOP.filter(function (o) {
      return opts.oszlopok ? opts.oszlopok.indexOf(o.kulcs) >= 0 : o.kulcs !== 'ar';
    });
    var rend = { kulcs: 'pts', irany: -1 };
    var szuro = {};                       // oszlop-kulcs -> szuroertek
    var lap = 0;                          // hanyadik oldal (0-tol)

    // egyszeri vaz: a keresomezot NEM rajzoljuk ujra, kulonben minden
    // leutesnel elveszne a fokusz
    // A legordulok ertekei magabol az ADATBOL jonnek, nem beegetett listabol:
    // igy egy uj klub vagy egy uj szakvezeto magatol megjelenik bennuk.
    // ertek -> felirat. A tulajdonos-szuroben a MONOGRAM a felirat (ugyanaz,
    // mint az oszlopban), a teljes nev a title-be kerul; a szurt ERTEK
    // viszont marad a nev, mert az azonosit.
    var ertekek = function (o) {
      var h = {}, mind = opts.adat() || [], i, j;
      for (i = 0; i < mind.length; i++) {
        if (o.szuro === 'tulaj') {
          var t = mind[i].tulajok || [];
          for (j = 0; j < t.length; j++) h[t[j].nev] = t[j].jel || t[j].nev;
        } else if (mind[i][o.kulcs]) h[mind[i][o.kulcs]] = mind[i][o.kulcs];
      }
      return Object.keys(h).sort(function (a, b) { return a.localeCompare(b, 'hu'); })
        .map(function (k) { return { ertek: k, felirat: h[k] }; });
    };
    var vezerlo = function (o) {
      if (o.szuro === 'min' || o.szuro === 'max')
        return '<input class="jlszam" type="number" min="0" step="any" ' +
               'data-szuro="' + o.kulcs + '" placeholder="' + esc(o.szuroCim) + '">';
      // A "Mindegy" a szuro kikapcsolasa; a "Valakinel" azt kerdezi, hogy
      // van-e egyaltalan gazdaja - ez ket kulonbozo kerdes, ezert ket sor.
      var extra = o.szuro === 'tulaj'
        ? '<option value="' + JL_VALAKI + '">Valakinél</option>' +
          '<option value="' + JL_SZABAD + '">Senkinél</option>' : '';
      return '<select class="jlszuro" data-szuro="' + o.kulcs + '"><option value="">' +
        esc(o.szuroCim) + '</option>' + extra + ertekek(o).map(function (v) {
          return '<option value="' + esc(v.ertek) + '" title="' + esc(v.ertek) + '">' +
                 esc(v.felirat) + '</option>';
        }).join('') + '</select>';
    };
    doboz.innerHTML =
      '<div class="jlvezerlo">' +
        '<input class="kereso" type="search" autocomplete="off" ' +
          'placeholder="Keresés játékosra vagy klubra…">' +
        oszlopok.filter(function (o) { return o.szuro; }).map(vezerlo).join('') +
        '<button class="jltorol" type="button">Szűrők törlése</button>' +
      '</div>' +
      '<div class="plr plrfej jlfej"><span class="rank"></span>' +
        oszlopok.map(function (o) {
          // ugyanaz a layout-osztaly, mint az adatcellan: enelkul a fejlec
          // nem az oszlopok folott all, hanem osszecsuszva a sor elejen
          return '<span class="jlfejcella ' + o.oszt + '" data-rend="' + o.kulcs + '">' +
                 esc(o.cim) + '<i></i></span>';
        }).join('') + '<span class="jltores"></span></div>' +
      '<div class="jllista"></div>' +
      '<div class="jllabsor"><span class="note jllab"></span>' +
        '<select class="jlmeret" title="Hány sor egy oldalon">' +
          [20, 40, 100, 0].map(function (n) {
            return '<option value="' + n + '"' + (n === limit ? ' selected' : '') + '>' +
                   (n ? n + ' / oldal' : 'mind') + '</option>';
          }).join('') +
        '</select><span class="jllapozo"></span></div>';

    var mezo = doboz.querySelector('.kereso');
    var lista = doboz.querySelector('.jllista');
    var lab = doboz.querySelector('.jllab');
    var lapozo = doboz.querySelector('.jllapozo');

    function rajzol() {
      var mind = opts.adat() || [];
      var q = ekezetlen(mezo.value).trim();
      var talalat = mind.filter(function (p) {
        for (var i = 0; i < oszlopok.length; i++) {
          var o = oszlopok[i], v = szuro[o.kulcs];
          if (!o.szuro || v === undefined || v === '') continue;
          if (o.szuro === 'min') { if ((p[o.kulcs] || 0) < +v) return false; continue; }
          if (o.szuro === 'max') {
            if (p[o.kulcs] == null || p[o.kulcs] > +v) return false;
            continue;
          }
          if (o.szuro === 'tulaj') {
            var t = p.tulajok || [];
            if (v === JL_SZABAD) { if (t.length) return false; continue; }
            if (v === JL_VALAKI) { if (!t.length) return false; continue; }
            var van = false;
            for (var k = 0; k < t.length; k++) if (t[k].nev === v) van = true;
            if (!van) return false;
            continue;
          }
          if (p[o.kulcs] !== v) return false;
        }
        if (!q) return true;
        return ekezetlen(p.nev).indexOf(q) >= 0 || ekezetlen(p.klub).indexOf(q) >= 0;
      });
      talalat.sort(function (a, b) {
        var x = jlErtek(a, rend.kulcs), y = jlErtek(b, rend.kulcs), c;
        if (typeof x === 'number' || typeof y === 'number') c = (x || 0) - (y || 0);
        else c = String(x).localeCompare(String(y), 'hu');
        // azonos ertekeknel a pont dont, hogy a sorrend ne ugraljon
        return c * rend.irany || (b.pts || 0) - (a.pts || 0);
      });
      // a szures/rendezes utan az oldalszam nem lehet a lista vegen tul
      var lapok = Math.max(1, Math.ceil(talalat.length / limit));
      if (lap >= lapok) lap = lapok - 1;
      if (lap < 0) lap = 0;
      var mutat = talalat.slice(lap * limit, lap * limit + limit);
      lista.innerHTML = mutat.length ? mutat.map(function (p, i) {
        return '<div class="plr jlsor" data-jl="' + esc(p.id) + '">' +
          '<span class="rank">' + (lap * limit + i + 1) + '.</span>' +
          oszlopok.map(function (o) { return o.cella(p, opts); }).join('') +
          // telefonon ez tori ket sorra a sort (gepen rejtve); az `order`
          // maga nem tor sort, ahhoz kell egy teljes szelessegu elem
          '<span class="jltores"></span>' +
        '</div>';
      }).join('') : '<div class="loading">Nincs találat erre: „' + esc(mezo.value) + '”</div>';

      doboz.querySelectorAll('.jlfejcella').forEach(function (c) {
        c.classList.toggle('rendez', c.dataset.rend === rend.kulcs);
        c.querySelector('i').textContent =
          c.dataset.rend === rend.kulcs ? (rend.irany < 0 ? '▼' : '▲') : '';
      });
      var szurve = !!q;
      for (var sk in szuro) if (szuro[sk] !== '' && szuro[sk] !== undefined) szurve = true;
      var tol = talalat.length ? lap * limit + 1 : 0;
      lab.textContent = !mind.length ? ''
        : !talalat.length ? 'Nincs találat'
        : (tol + '–' + (lap * limit + mutat.length) + ' / ' + talalat.length +
           (szurve ? ' találat' : ' játékos'));
      lapozo.innerHTML = lapozoHTML(lap, lapok);
    }

    var ujrarajzol = function () { lap = 0; rajzol(); };
    mezo.addEventListener('input', ujrarajzol);
    doboz.addEventListener('input', function (e) {
      var sz = e.target.closest('.jlszam');
      if (sz) { szuro[sz.dataset.szuro] = sz.value; ujrarajzol(); }
    });
    doboz.addEventListener('change', function (e) {
      var m = e.target.closest('.jlmeret');
      // "mind": nagy szam, nem kulon ag - igy a lapozo magatol eltunik
      if (m) { limit = +m.value || 100000; ujrarajzol(); return; }
      var sz = e.target.closest('.jlszuro');
      if (sz) { szuro[sz.dataset.szuro] = sz.value; ujrarajzol(); }
    });
    doboz.addEventListener('click', function (e) {
      if (e.target.closest('.jltorol')) {
        szuro = {}; mezo.value = '';
        doboz.querySelectorAll('.jlszuro').forEach(function (x) { x.value = ''; });
        doboz.querySelectorAll('.jlszam').forEach(function (x) { x.value = ''; });
        ujrarajzol();
        return;
      }
      var fej = e.target.closest('.jlfejcella');
      if (fej) {
        var o = null;
        for (var i = 0; i < oszlopok.length; i++)
          if (oszlopok[i].kulcs === fej.dataset.rend) o = oszlopok[i];
        if (rend.kulcs === fej.dataset.rend) rend.irany = -rend.irany;
        else rend = { kulcs: fej.dataset.rend, irany: (o && o.szam) ? -1 : 1 };
        ujrarajzol();
        return;
      }
      var lapoz = e.target.closest('.jllapoz');
      if (lapoz) { lap = +lapoz.dataset.ugras; rajzol(); return; }
      var sor = e.target.closest('.jlsor');
      if (sor && opts.nyit) opts.nyit(sor.dataset.jl);
    });
    rajzol();
    return { rajzol: rajzol };
  }

  function lablecHTML(gyoker) {
    gyoker = gyoker || '';
    return '<a href="' + gyoker + 'valtozasok/">Mi újult meg?</a>';
  }
  function renderLablec(gyoker) {
    var el = document.getElementById('lablec');
    if (el) el.innerHTML = lablecHTML(gyoker);
  }

  /* Egy hivas beallitja a kozos fejlec-reszeket: a ligavalto savot, a liga
     tipusat (body-osztalykent, hogy CSS-bol es JS-bol is fogodzo legyen) es
     az alcimet. Igy a liga neve/leirasa egyetlen helyen, a LIGAK listaban
     el; az oldal sajat, adatbol szamolt alcimet ezutan is felulirhat. */
  function renderNav(aktiv, gyoker) {
    var el = document.getElementById('liganav');
    if (el) el.innerHTML = navHTML(aktiv, gyoker);
    var l = liga(aktiv);
    if (!l) return;
    if (document.body) document.body.classList.add('tipus-' + l.tipus);
    var sub = document.querySelector('.sub');
    if (sub) sub.textContent = l.cim + ' · ' + l.leiras;
  }

  /* ===== Ujrafrissites, amikor a lap ismet lathatova valik =====
     Az oldalak az elo allast a betolteskor kerik le, egyszer. Asztali gepen
     ez eleg, mert oda altalaban friss betoltessel terunk vissza. Mobilon
     viszont nem toltunk ujra, csak visszavaltunk a lapra: a bongeszo
     memoriabol allitja vissza, tehat a betolteskori allas befagy. Igy allt
     elo, hogy a fooldali meccslista meg a regi pontot mutatta, mikozben a
     meccs-adatlap - aminek sajat, nyitaskori lekerese van - mar a frisset.

     Ez a segito ujra lefuttatja a kapott frissitest, amikor a lap ismet
     lathatova valik. Ket vedelme van: legfeljebb minKoz ezredmasodpercenkent
     indul (kulonben a lapok kozti kapkodas lekeresekkel verne a proxykat),
     es sosem fut belole ketto egyszerre. A percenkenti frissitest lasd
     lentebb (eloFrissito) - az csak ELO fordulo alatt jar. */
  function ujraLathatokor(fn, minKoz) {
    minKoz = (minKoz == null) ? 30000 : minKoz;
    var utolso = Date.now(), fut = false;
    function inditsd() {
      if (fut || document.visibilityState === 'hidden') return;
      if (Date.now() - utolso < minKoz) return;
      fut = true;
      Promise.resolve().then(fn).catch(function () {}).then(function () {
        fut = false;
        utolso = Date.now();          // a kovetkezo ablak a BEFEJEZESTOL jar
      });
    }
    document.addEventListener('visibilitychange', inditsd);
    // iOS Safariban a bfcache-bol visszaallo lapnal nem mindig jon
    // visibilitychange, pageshow (persisted) viszont igen.
    window.addEventListener('pageshow', function (e) { if (e.persisted) inditsd(); });
    // asztali gepen az ablakra visszakattintas sem valt visibilitychange-t
    window.addEventListener('focus', inditsd);
    return inditsd;
  }

  /* ===== Idozitett frissites, AMIG A FORDULO EL =====
     BEJELENTETT HIBA (2026-08-30, PL): a nyitva hagyott lap a BETOLTESKORI
     allast mutatta. A LEE-BRE meccs a 9. percnel allt, amikor a lap
     betoltodott, es a sorok ott is maradtak - percek, meccsora, pontok
     egyarant. A lenyilo bontas viszont KATTINTASKOR sajat, friss lekerest
     indit, ezert az mar 90 percet mutatott: ugyanazon a kepernyon mondott
     ellent egymasnak a sor (9 perc, 1 pont) es a panelje (90 perc, 2 pont).
     A panel volt a helyes.

     Eddig ez SZANDEKOS volt, es akkor helyes is: publikus kozvetitokon
     mentunk, es egy nyitva hagyott lap percenkenti lekeresekkel verte volna
     oket. A sajat Cloudflare Workerunk 60 masodperces peremgyorsitotaraval
     ez az indok megszunt - akarhanyan nezik ugyanazt a fordulot, az API
     fele percenkent egy keres megy ki.

     Harom vedelme van: REJTETT lapon nem fut (es lapvaltaskor azonnal all),
     sosem fut belole ketto egyszerre, es csak akkor jar, ha a hivo elindtja
     - vagyis fordulok kozott egyetlen keres sem megy ki. */
  function eloFrissito(fn, koz) {
    koz = koz || 60000;
    var id = null, fut = false, kert = false;
    function tick() {
      if (fut || document.visibilityState === 'hidden') return;
      fut = true;
      Promise.resolve().then(fn).catch(function () {}).then(function () { fut = false; });
    }
    function oraAll() { if (id) { clearInterval(id); id = null; } }
    function oraIndul() {
      if (!id && kert && document.visibilityState !== 'hidden') id = setInterval(tick, koz);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden') oraAll(); else oraIndul();
    });
    return {
      indit: function () { kert = true; oraIndul(); },
      allj:  function () { kert = false; oraAll(); }
    };
  }

  /* ===== Lassu lekeres jelzese =====
     A meccs-adatlap es a keret-nezet eloszor a tarolt szamokkal rajzol, es
     amikor a percre friss lekeres megjon, kicsereli oket. Gyors halon ez
     eszre sem veheto; lassun viszont ugy nez ki, mintha a lap regi adatot
     mutatna - vagy ami rosszabb, a szamok magutol atugranak az orrod elott.

     Fix kuszobot nem lehet jol megvalasztani (a lekeres ideje halozattol es
     a CORS-proxytol fugg, ugyanazon a keszuleken is szor), ezert a jelzes
     MAGAT MERI: csak akkor jelenik meg, ha a lekeres tenyleg elhuzodik
     (alapertelmezesben fel masodperc), es kiirja, mennyi ideje tart. Gyors
     valasznal soha nem latszik, tehat nem villog feleslegesen.

     A visszaadott fuggveny leveszi a jelzest, es visszaadja az eltelt idot
     ezredmasodpercben. Mindig meg kell hivni - hibas agon is. */
  /* ===== Eredmenysor (a meccs-adatlap tetejen) =====
     Ugyanaz a doboz, mint a fooldali meccspanelen, hogy a ket helyen ne
     nezhessen ki maskepp. A neveket mar feloldva varja: a PL-en azonositobol
     kell nevet csinalni, az NB1-en a nev maga a kulcs. */
  function allasHTML(h, v, hp, vp, elo) {
    var sz = function (x) { return x != null ? fmt(x) : '—'; };
    return '<div class="mscore' + (elo ? ' elo' : '') + '">' +
      '<span class="csapat">' + esc(h) + '</span>' +
      '<span class="score">' + sz(hp) + ' <span style="color:var(--dim)">:</span> ' + sz(vp) +
      (elo ? '<span class="elojel">élő</span>' : '') + '</span>' +
      '<span class="csapat">' + esc(v) + '</span></div>';
  }

  /* ===== Nezet-verem: egy modal, amiben lapozni lehet =====
     Nem nyitunk modalt a modalban: a tartalom cserelodik, es a "vissza" gomb
     az elozo nezetre lep. Az x / felrekattintas / Escape mindig mindent zar.
     A belepesi pont 'root', a fulvaltas 'replace', a listabol nyilo nezet
     'push'; a 'noop' a verembol ujrarajzolt nezet (nem tolunk ra semmit).

     Mindket liga-oldal ugyanezt hasznalta, kulon-kulon lemasolva - egy uj
     liga harmadszor is lemasolta volna. */
  function nezetVerem(azon) {
    var verem = [];
    function gomb() {
      var b = document.getElementById(azon.vissza);
      if (b) b.style.display = verem.length > 1 ? '' : 'none';
    }
    function nyit() {
      var o = document.getElementById(azon.ov);
      if (o) o.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    return {
      verem: verem,
      mutat: function (thunk, mod) {
        if (mod === 'noop') return;
        if (!mod || mod === 'root') verem.length = 0;
        if (mod === 'replace' && verem.length) verem[verem.length - 1] = thunk;
        else verem.push(thunk);
        gomb();
      },
      vissza: function () {
        if (verem.length > 1) { verem.pop(); gomb(); verem[verem.length - 1](); }
      },
      nyit: nyit,
      zar: function () {
        var o = document.getElementById(azon.ov);
        if (o) o.classList.remove('open');
        document.body.style.overflow = '';
        verem.length = 0;
        gomb();
      }
    };
  }

  /* ===== Lekeres CORS-proxyn at =====
     Harom utvonalat probal sorban (direkt -> corsproxy -> allorigins), es
     megjegyzi, melyik valt be: a munkamenet tobbi kerese mar azzal indul.

     Gyorsitotar-tores harom retegben, mert enelkul iPhone-on befagyott az
     allas: `cache:'no-store'` a bongeszonek, `&_=<ido>` a proxynak (az a
     SAJAT gyorsitotarabol szolgalt ki, es az megosztott - ezert nem segitett
     az ujratoltes), es opcionalisan a belso URL-en is idobelyeg.

     Beallitasok:
       belsoBelyeg  parameter neve a BELSO (cel) URL-en, vagy ures. Az FPL
                    turi az ismeretlen parametert; az MLSZ-nel ez nincs
                    igazolva, ezert ott nem hasznaljuk.
       ervenyes(j)  mikor fogadjuk el a valaszt (az MLSZ-nel kell a data tomb)
       hiba         'dob' -> kivetel, kulonben null a visszateres
       jelez(cimke) opcionalis: statuszsav-frissites probalkozas kozben */
  function lekero(be) {
    be = be || {};
    var belyeg = function (u) {
      return be.belsoBelyeg ? u + (u.indexOf('?') < 0 ? '?' : '&') +
        be.belsoBelyeg + '=' + Date.now() : u;
    };
    /* SAJAT proxy (Cloudflare Worker, tartalek/proxy-worker.js): ha be van
       allitva, ez az elso ut - a sajat fiok alatt fut, senki nem kapcsolja
       le, es az ingyenes kerete (100k/nap) a forgalmunk sokszorosa. Amig
       ures, a lekero kihagyja, es a publikus proxyk viszik (backup). */
    var SAJAT_PROXY = 'https://funtasy-liga.swick00.workers.dev';

    /* Az ut-sorrend MERT megbizhatosag, nem izles (naplo/proxy-meres.txt,
       2026-08-27): aznap a corsproxy.io 401-re valtott (regisztraciohoz
       kotottek), az allorigins tulterhelt volt - es mivel minden elo lekeres
       ezen a ketton mult, MINDKET liga elo resze egyszerre halt meg. A
       tanulsag beepitve: tobb fuggetlen ut, es az elso siker utan a lekero
       ugyis a bevalt uton marad. */
    var utak = [
      // a sajat ut a direkt ELOTT all: a ket API-nk direkt utja bongeszobol
      // sosem megy (nincs CORS-fejlecuk), folosleges elorobalkozas lenne
      SAJAT_PROXY && { n: 'sajat', f: function (u) {
        return SAJAT_PROXY + '/?url=' + encodeURIComponent(belyeg(u)); } },
      { n: 'direkt', f: function (u) { return belyeg(u); } },
      // path-stilusu proxy: a cel-URL valtozatlanul fuzodik a vegere
      { n: 'cors.sh', f: function (u) { return 'https://proxy.cors.sh/' + belyeg(u); } },
      { n: 'allorigins', f: function (u) {
          return 'https://api.allorigins.win/raw?url=' + encodeURIComponent(belyeg(u)) + '&_=' + Date.now(); } },
      // az allorigins masik utja CSOMAGOLVA adja a valaszt ({contents: "..."}) -
      // a meresben pont ez ment, amikor a /raw eppen nem. A kibont() bontja ki.
      { n: 'allorigins-get', f: function (u) {
          return 'https://api.allorigins.win/get?url=' + encodeURIComponent(belyeg(u)) + '&_=' + Date.now(); },
        kibont: function (j) { return JSON.parse(j.contents); } },
      { n: 'cors.lol', f: function (u) {
          return 'https://api.cors.lol/?url=' + encodeURIComponent(belyeg(u)) + '&_=' + Date.now(); } },
      // 401 a meres napjan - a sor vegen marad, hatha visszaengedik
      { n: 'corsproxy', f: function (u) {
          return 'https://corsproxy.io/?url=' + encodeURIComponent(belyeg(u)) + '&_=' + Date.now(); } }
    ].filter(Boolean);
    var ervenyes = be.ervenyes || function (j) { return j && typeof j === 'object'; };
    var bevalt = null;
    return async function (url, cimke, ms) {
      ms = ms || 9000;
      var sorrend = bevalt ? [bevalt].concat(utak.filter(function (r) { return r !== bevalt; })) : utak;
      var hibak = [];
      for (var i = 0; i < sorrend.length; i++) {
        var rt = sorrend[i];
        try {
          if (cimke && be.jelez) be.jelez(cimke);
          var c = new AbortController();
          var t = setTimeout(function () { c.abort(); }, ms);
          var res = await fetch(rt.f(url), { signal: c.signal, cache: 'no-store',
                                             headers: { 'Accept': 'application/json' } })
            .finally(function () { clearTimeout(t); });
          if (!res.ok) { hibak.push(rt.n + ':HTTP ' + res.status); continue; }
          var j = JSON.parse(await res.text());
          if (rt.kibont) {
            try { j = rt.kibont(j); }
            catch (e2) { hibak.push(rt.n + ':csomagolt válasz hibás'); continue; }
          }
          if (!ervenyes(j)) { hibak.push(rt.n + ':rossz formátum'); continue; }
          bevalt = rt;
          return j;
        } catch (e) {
          hibak.push(rt.n + ':' + (e.name === 'AbortError' ? 'időtúllépés'
                     : e.name === 'TypeError' ? 'CORS' : e.message));
        }
      }
      if (be.hiba === 'dob') throw new Error(hibak.join(' · '));
      return null;
    };
  }

  /* ===== Elo allas kikeresese =====
     A folyo fordulo allasa nem a menetrendben van, hanem az elo retegben
     (hogy a tabellaba ne szamitson bele) - a fordulo-listanak es a
     meccs-adatlapnak viszont onnan kell elovennie. */
  function eloKereso(live) {
    return function (r, h, v) {
      var l = live[r] || [];
      for (var i = 0; i < l.length; i++) {
        if (l[i] && l[i][0] === h && l[i][1] === v) return l[i];
      }
      return null;
    };
  }

  /* ===== Statuszsav hibauzenet =====
     Ha epp fordulo van folyamatban, a felhasznalot az erdekli, hogy az elo
     allas nem frissul. Nyugalmi idoszakban a tarolt allas amugy is naprakesz,
     ott csak annyit mondunk, mikori. A "van-e folyo fordulo" kerdest a hivo
     oldal dönti el, mert mindenhol masbol latszik. */
  function hibajelzo(be) {
    return function () {
      var st = document.getElementById(be.statusz || 'status');
      if (!st) return;
      st.className = 'err';
      st.textContent = be.eloE() ? statusz.hibaElo : statusz.hibaNyugodt(be.taroltIdo());
    };
  }

  /* ===== Jatekosprofil-nezo (mindket liga) =====
     A vaz ugyanaz: cim, felirat, betoltes-jelzes, elavultsag-vedelem,
     hibauzenet. A ket oldal csak abban ter el, hogy a kulcsbol hogyan lesz
     NEV es ADAT, es hogy a kirajzolas utan van-e meg potolnivalo (az NB1-en
     a hianyzo pontok utolag, sorban toltodnek).

     Az elavultsag-vedelem nem diszites: amig a profil tolt, a felhasznalo
     nyithat masikat - a kesobb beero valasz nem irhatja felul az ujabbat.
     Ezert nem a hivas ideje szamit, hanem hogy ez-e MEG az aktualis kulcs. */
  function profilNezo(be) {
    var aktualis = null;
    function mutat(kulcs, mod) {
      be.nezet.mutat(function () { mutat(kulcs, 'noop'); }, mod);
      aktualis = kulcs;
      if (be.jelol) be.jelol(kulcs);
      be.nezet.nyit();
      document.getElementById('mTitle').textContent = be.nev(kulcs);
      document.getElementById('mSub').textContent =
        'Fordulónkénti teljesítmény — a sorra kattintva a pontok bontása';
      document.getElementById('mTabs').innerHTML = '';
      var test = document.getElementById('mBody');
      test.innerHTML = '<div class="loading">Profil betöltése…</div>';
      Promise.resolve().then(function () { return be.adat(kulcs); }).then(function (adat) {
        if (aktualis !== kulcs) return;
        test.innerHTML = profilHTML(adat);
        if (be.utan) be.utan(kulcs, adat);
      }, function (hiba) {
        if (aktualis !== kulcs) return;
        test.innerHTML = '<div class="loading" style="color:var(--lose)">' +
          'Nem sikerült betölteni — ' + esc(hiba && hiba.message) + '</div>';
      });
    }
    return mutat;
  }

  /* ===== Egymas elleni nezet =====
     A matrix cellajara kattintva nyilik. A ket oldal csak abban ter el, hogy
     az azonositobol hogyan lesz nev, es hogy nyitaskor mit kell nullazni. */
  function h2hNezo(be) {
    function mutat(a, b, mod) {
      be.nezet.mutat(function () { mutat(a, b, 'noop'); }, mod);
      if (be.elokeszit) be.elokeszit(a, b);
      be.nezet.nyit();
      var nv = be.nev || function (x) { return x; };
      document.getElementById('mTitle').textContent = nv(a) + '  vs  ' + nv(b);
      document.getElementById('mSub').textContent =
        'Egymás elleni meccsek — sorra kattintva a meccs részletei';
      document.getElementById('mTabs').innerHTML = '';
      document.getElementById('mBody').innerHTML =
        '<div class="sqwrap one" style="max-width:none">' + be.tartalom(a, b) + '</div>';
    }
    return mutat;
  }

  var aktivJelzok = new WeakMap();
  function lassuJelzo(cel, kesleltetes) {
    kesleltetes = (kesleltetes == null) ? 500 : kesleltetes;
    // Egy helyen csak EGY jelzes lehet: ha ket meccs kozott gyorsan valtunk,
    // kulonben ket "frissites..." cimke allna egymas mellett ugyanazon az
    // alcimen, es a regi ora tovabb ketyegne.
    if (cel) { var elozo = aktivJelzok.get(cel); if (elozo) elozo(); }
    var kezdet = Date.now(), el = null, tick = null;
    var idozit = setTimeout(function () {
      if (!cel || !cel.isConnected) return;
      el = document.createElement('span');
      el.className = 'frissjel';
      var ir = function () {
        el.textContent = 'frissítés… ' +
          ((Date.now() - kezdet) / 1000).toFixed(1).replace('.', ',') + ' mp';
      };
      ir();
      cel.appendChild(el);
      tick = setInterval(ir, 100);
    }, kesleltetes);
    function vege() {
      clearTimeout(idozit);
      if (tick) clearInterval(tick);
      if (el && el.parentNode) el.parentNode.removeChild(el);
      if (cel && aktivJelzok.get(cel) === vege) aktivJelzok['delete'](cel);
      return Date.now() - kezdet;
    }
    if (cel) aktivJelzok.set(cel, vege);
    return vege;
  }

  /* ---------- zarasi valtozasok (mindket liga) ----------
     A ket panel UGYANAZT mutatja ugyanugy: a PL-en a zaras pillanataban tortent
     valtozast, az NB1-en a fordulo veglegesitesekor tortentet. A HTML ezert itt
     keszul, egy helyen - kulon-kulon megirva egyszer mar szetcsuszott (mas cim,
     mas elrendezes, mas ures-szoveg).

     A ket oldal NORMALIZALT sorokat ad at:
       {poszt, nev, klub, prof, elott, utan, dl}       - pontvaltozas
       {tip:'csere', poszt, nev, klub, prof, irany, ert} - automatikus csere (PL)
     `prof` az a jelzo-keszlet, amitol a nev kattinthato lesz; ha nincs (pl. az
     NB1 elso forduloinal, ahol a jatekos nem ismert), a nev sima szoveg.
     `dl` a kulonbseg, ha az "elotte -> utana" nem ismert, csak a valtozas. */
  function jelzokHTML(a){
    var s = '', k;
    for (k in (a || {})) if (a[k] != null && a[k] !== '') s += ' ' + k + '="' + esc(String(a[k])) + '"';
    return s;
  }
  function zarasSorHTML(x){
    var d = (x.dl != null) ? x.dl : (x.utan - x.elott);
    return '<div class="zsor">'
      + (x.poszt ? '<span class="ppos">' + esc(x.poszt) + '</span>' : '')
      + (x.prof
          ? '<span class="znev kattint"' + jelzokHTML(x.prof) + '>' + esc(x.nev)
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
  function zarasLista(csoportok, ures){
    var blokkok = [];
    (csoportok || []).forEach(function (cs){
      if (!cs || !cs.sorok || !cs.sorok.length) return;
      blokkok.push('<div class="zcsapat"><h3 class="kattint"' + jelzokHTML(cs.jelzok) + '>'
        + esc(cs.nev) + '</h3>' + cs.sorok.map(zarasSorHTML).join('') + '</div>');
    });
    if (!blokkok.length) return '<div class="loading">' + esc(ures) + '</div>';
    return '<div class="zlista">' + blokkok.join('') + '</div>';
  }

  /* ---------- "Valtoztatasok" ful (mindket liga) ----------
     Mit valtoztatott a szakvezeto fordulonkent, es MENNYIT ERT: minden sor
     mellett ott a pontkulonbseg, a blokk aljan pedig az osszeguk - ami
     PONTOSAN a Guardiola mutato arra a fordulora. Ez a ful egesz ertelme:
     a tabellaban allo szam levezetheto legyen, ne kelljen elhinni.

     A LAP EGY OSZLOP, es a fordulok NOVEKVO sorrendben allnak - ugyanugy,
     mint a Fordulok fulon es mindenutt mashol. Az elso valtozat ket
     oszlopba tordelte a blokkokat es a legfrissebbel kezdett: attol a
     szem cikcakkban ugralt, es a sorrend is szembement a tobbi nezettel.

     A soron belul a ket jobb szeli oszlop FIX SZELES, tehat a szamok
     egymas alatt allnak - enelkul minden sorban mashol volt a
     pontkulonbseg, es az egesz olvashatatlanna valt.

     A sorok NORMALIZALT alakban jonnek a lapoktol (a szamitas a gyujtoben
     el, keretvaltozasok.json / draft_keretvaltozasok.json):
       {poszt, nev, klub, prof, cimke, elott, utan, ert, dl}
     `prof` a nevet kattinthatova tevo jelzo-keszlet; `cimke` a magyarazat
     (pl. "kapitany" vagy "kezdo -> pad"); `elott`/`utan` a ket ertek,
     amibol a kulonbseg lett; `ert` egyetlen ertek, ha nincs ket oldal;
     `dl` maga a kulonbseg. */
  function vaErtek(x){
    if (x.elott != null) return fmt(x.elott) + ' → ' + fmt(x.utan);
    return x.ert != null ? fmt(x.ert) : '';
  }
  function vaSorHTML(x){
    // `dl` HIANYOZHAT: a meg le nem zart fordulonal a valtoztatas mar ismert,
    // a pontja viszont meg nem. Ilyenkor URES a kulonbseg-cella - nem "0",
    // mert az azt allitana, hogy nem ert semmit.
    if (x.dl == null)
      return '<div class="vasor' + (x.oszt ? ' ' + x.oszt : '') + '">'
        + (x.poszt ? '<span class="ppos">' + esc(x.poszt) + '</span>' : '<span class="ppos ures"></span>')
        + '<span class="vanev' + (x.prof ? ' kattint' : '') + '"' + (x.prof ? jelzokHTML(x.prof) : '') + '>'
        + esc(x.nev) + (x.klub ? ' <span class="tm">' + esc(x.klub) + '</span>' : '') + '</span>'
        + (x.cimke ? '<span class="vacimke">' + esc(x.cimke) + '</span>' : '')
        + '<span class="vaert"></span><span class="zdiff"></span></div>';
    var d = x.dl || 0;
    return '<div class="vasor' + (x.oszt ? ' ' + x.oszt : '') + '">'
      + (x.poszt ? '<span class="ppos">' + esc(x.poszt) + '</span>' : '<span class="ppos ures"></span>')
      + '<span class="vanev' + (x.prof ? ' kattint' : '') + '"' + (x.prof ? jelzokHTML(x.prof) : '') + '>'
      + esc(x.nev) + (x.klub ? ' <span class="tm">' + esc(x.klub) + '</span>' : '') + '</span>'
      + (x.cimke ? '<span class="vacimke">' + esc(x.cimke) + '</span>' : '')
      + '<span class="vaert">' + vaErtek(x) + '</span>'
      + '<span class="zdiff ' + (d > 0 ? 'pos' : d < 0 ? 'neg' : '') + '">'
      + (d > 0 ? '+' : '') + fmt(d) + '</span></div>';
  }
  /* csoport: {nev, guard, reszek:[{cim, sorok}], zaro:[sor], ures}
     `reszek` a cimkezett szakaszok (Eladva / Megveve / Szerepvaltas), `zaro`
     a lezaro sorok (a PL-en "A te donteseid" es a gepi csere).

     Az URES CSOPORT IS KILATSZIK: az a fordulo, amelyikhez nem nyult hozza,
     ugyanolyan valasz a kerdesre, mint a tobbi - es a mutatoja is pont
     ezert 0. Ha kihagynank, a nezo azt hinne, hogy hianyzik az adat. */
  function valtoztatasLista(csoportok, ures){
    if (!csoportok || !csoportok.length)
      return '<div class="loading">' + esc(ures) + '</div>';
    return '<div class="valtlista">' + csoportok.map(function (cs){
      // A CIMKEZETLEN, EGYBEN ATADOTT `sorok` IS ERVENYES ALAK. Nem
      // kenyelmi kiterjesztes: a `?v=` csak a funtasy.js/css gyorsitotarat
      // tori, az nb1/index.html-et NEM - es a kiszolgalo a ?v=68-as kerésre
      // is a MOSTANI funtasy.js-t adja. Elesben elo is allt, hogy a bongeszo
      // regi lapja (ami meg `sorok`-at adott at) az UJ megjelenitovel
      // talalkozott: a fordulo fejlecben ott allt a GUARD, alatta viszont
      // "Nem valtoztatott a kereten." - holott harom jatekost cserelt.
      // Amig a ket alak egyutt el, ez nem fordulhat elo.
      var reszek = (cs.reszek || (cs.sorok ? [{ cim: '', sorok: cs.sorok }] : []))
        .filter(function (r){ return r.sorok && r.sorok.length; });
      var db = reszek.reduce(function (n, r){ return n + r.sorok.length; }, 0);
      return '<div class="vakor">'
        + '<div class="vafej"><span>' + esc(cs.nev) + '</span>'
        + (cs.guard == null
           ? (cs.megj ? '<span class="vamegj">' + esc(cs.megj) + '</span>' : '')
           : '<span class="guardjel ' + (cs.guard > 0 ? 'pos' : cs.guard < 0 ? 'neg' : '') + '">'
             + guardJelol(cs.guard) + '</span>') + '</div>'
        + (db ? reszek.map(function (r){
              return (r.cim ? '<div class="varescim">' + esc(r.cim) + '</div>' : '')
                     + r.sorok.map(vaSorHTML).join('');
            }).join('')
              : '<div class="vasor vaures"><span class="vanev">'
                + esc(cs.ures || 'Nem változtatott a keretén.') + '</span></div>')
        + (cs.zaro || []).map(vaSorHTML).join('')
        + (db && cs.guard != null
           ? '<div class="vasor vaossz"><span class="ppos ures"></span>'
             + '<span class="vanev">Összesen</span><span class="vacimke"></span>'
             + '<span class="vaert"></span><span class="zdiff '
             + (cs.guard > 0 ? 'pos' : cs.guard < 0 ? 'neg' : '') + '">'
             + guardJelol(cs.guard) + '</span></div>'
           : '')
        + '</div>';
    }).join('') + '</div>';
  }

  /* ---------- ELAVULT LAP FELISMERESE ----------
     A `?v=` a funtasy.js/css gyorsitotarat tori - a LAP SAJAT HTML-jet NEM.
     Az nb1/index.html-ben viszont eles logika van (kozos jatekosok, elo
     keret-rekordok, meccsallapot), es egy regi HTML ezeket a regi szabaly
     szerint futtatja. Ketszer allt elo egy nap alatt: a javitas kint volt,
     a nezo megis a regi viselkedest latta - es semmi nem jelezte.

     Ezert a lap megkerdezi, mi a MOSTANI verzio (verzio.json), es ha o
     regebbi, EGYSZER ujratolt. A sessionStorage-os kapu vedi a hurkot: ha
     az ujratoltes utan is regi marad (pl. kozvetito gyorsitotar), tobbszor
     nem probalja - inkabb csendben marad, mint hogy oda-vissza toltsön. */
  function verzioOr(){
    var sc = document.querySelector('script[src*="funtasy.js?v="]');
    var sajat = sc && +((sc.getAttribute('src').split('v=')[1] || '').split('&')[0]);
    if (!sajat) return;
    fetch('verzio.json?t=' + Date.now()).catch(function(){
      return fetch('../verzio.json?t=' + Date.now());
    }).then(function (r){ return r && r.ok ? r.json() : null; }).then(function (j){
      if (!j || !j.v || +j.v <= sajat) return;
      var k = 'funtasy-ujratoltes';
      try { if (sessionStorage.getItem(k) === String(j.v)) return;
            sessionStorage.setItem(k, String(j.v)); } catch (e) {}
      location.reload();
    }).catch(function(){});
  }

  /* A kivitel egy resze ma csak BELUL hasznalt (navHTML, lablecHTML,
     profilFejHTML, ekezetlen, kezdSzazalek, KEZD_CIM). Szandekosan maradnak
     kint: a tervezett osszesito oldal es a toplistak pont ezeket ternek ujra
     (ugyanaz a KEZD%-kerekites es ugyanaz a magyarazo szoveg, ugyanaz az
     ekezet-fuggetlen kereses) - ha ott ujra megirodnanak, megint ket
     igazsag lenne belole. A kolstseg ~100 byte, a haszon az, hogy nem kell
     majd kettozni. */
  global.FunTasy = { create: create, esc: esc, fmt: fmt, played: played,
                     accToggle: accToggle, accTable: accTable, accOrzo: accOrzo,
                     LIGAK: LIGAK, liga: liga, navHTML: navHTML, renderNav: renderNav,
                     lablecHTML: lablecHTML, renderLablec: renderLablec,
                     bontasMeccsSor: bontasMeccsSor,
                     zarasLista: zarasLista, verzioOr: verzioOr,
                     valtoztatasLista: valtoztatasLista,
                     profilHTML: profilHTML, profilFejHTML: profilFejHTML,
                     jatekosKereso: jatekosKereso, ekezetlen: ekezetlen,
                     profilNyitoHTML: profilNyitoHTML, profilNezo: profilNezo,
                     kezdSzazalek: kezdSzazalek, KEZD_CIM: KEZD_CIM,
                     kezdParHTML: kezdParHTML,
                     statusz: statusz, ujraLathatokor: ujraLathatokor,
                     eloFrissito: eloFrissito,
                     lassuJelzo: lassuJelzo, allasHTML: allasHTML,
                     nezetVerem: nezetVerem, lekero: lekero,
                     eloKereso: eloKereso, hibajelzo: hibajelzo, h2hNezo: h2hNezo };
})(window);
