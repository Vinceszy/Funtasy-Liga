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
  var LIGAK = [
    { id: 'nb1', nev: 'NB1', mappa: 'nb1/', cim: 'NB1 salary cap fantasy',
      leiras: 'privát head-to-head · 8 csapat · 33 forduló',
      tipus: 'salary-cap', tipusNev: 'Salary cap', tema: 'liga-nb1' },
    { id: 'pl', nev: 'PL', mappa: 'pl/', cim: 'PL draft fantasy',
      leiras: 'privát head-to-head · 10 csapat · 38 forduló',
      tipus: 'draft', tipusNev: 'Draft', tema: 'liga-pl' }
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

    api.renderTable = function () {
      var h = '<tr><th></th><th>' + esc(opts.nameHeader || 'Szakvezető') +
        '</th><th>M</th><th>GY</th><th>D</th><th>V</th>' +
        '<th title="szerzett pont">SP</th><th title="kapott pont">KP</th>' +
        '<th title="pontkülönbség">KÜL</th><th>Pont</th><th>Forma</th></tr>';
      api.computeTable().forEach(function (r, i) {
        var form = r.form.slice(-5).map(function (f) {
          return '<span class="dot ' + f + '"></span>';
        }).join('');
        var nev = esc(label(r.name));
        // A nev csak ott kattinthato, ahol van mit megnyitni (keret-modal).
        var cella = (opts.nameAttr
          ? '<span class="clickable" ' + opts.nameAttr(r.name) + '>' + nev + '</span>'
          : nev) + mgr(r.name);
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
        var attr = opts.matchAttr ? ' ' + opts.matchAttr(m[0], m[1], r) : '';
        h += '<div class="match' + (elo ? ' elo' : '') + '"' + attr + '>' +
          '<div class="h ' + (van && hp > vp ? 'winner' : '') + '">' + esc(label(m[0])) + mgr(m[0]) + '</div>' +
          '<div class="score">' +
            (van ? fmt(hp) + ' <span style="color:var(--dim)">:</span> ' + fmt(vp) +
                   (elo ? '<span class="elojel">élő</span>' : '')
                 : '<span class="na">— : —</span>') +
          '</div>' +
          '<div class="v ' + (van && vp > hp ? 'winner' : '') + '">' + esc(label(m[1])) + mgr(m[1]) + '</div></div>';
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
            '<td>' + (ap != null ? fmt(ap) : '—') +
            (elo ? ' <span class="elojel">élő</span>' : '') + '</td>' +
            '<td>' + (bp != null ? fmt(bp) : '—') + '</td>' +
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
    p.innerHTML = '<div class="accload">Bontás betöltése…</div>';
    row.insertAdjacentElement('afterend', p);
    Promise.resolve().then(tolt).then(function (html) {
      if (!row.classList.contains('open') || !p.isConnected) return;
      p.innerHTML = html || '<div class="accload">A pontok bontása nem érhető el ehhez a játékoshoz.</div>';
    }, function () {
      if (!row.classList.contains('open') || !p.isConnected) return;
      p.innerHTML = '<div class="accload">A bontás lekérése nem sikerült.</div>';
    });
  }

  /* Bontas-tabla: sorok = [{name, value, points}]. A points lehet szam
     vagy kesz szoveg (pl. "×2" a kapitanynal). A 0 pontos sorokat a hivo
     szuri ki - az MLSZ felulete is csak a pontot ero esemenyeket mutatja.
     Ha nincs egyetlen pontot ero sor sem, az `ures` szoveg jelenik meg: azt
     a hivo szamolja ki, mert az ok oldalanként mas adatbol derul ki (meg nem
     kezdodott a meccs / zajlik / lejatszotta pont nelkul / nem lepett palyara). */
  function accTable(sorok, ures) {
    if (!sorok || !sorok.length)
      return '<div class="accload">' + esc(ures || 'Ehhez a fordulóhoz nincs rögzített esemény.') + '</div>';
    var h = '<table class="acctable"><tr><th>Esemény</th><th>Érték</th><th>Pont</th></tr>';
    for (var i = 0; i < sorok.length; i++) {
      var s = sorok[i];
      var szam = (typeof s.points === 'number');
      var cls = szam ? (s.points > 0 ? 'pos' : (s.points < 0 ? 'neg' : '')) : '';
      h += '<tr><td class="ev">' + esc(s.name) + '</td>' +
           '<td>' + (s.value == null || s.value === '' ? '' :
                     (typeof s.value === 'number' ? fmt(s.value) : esc(String(s.value)))) + '</td>' +
           '<td class="' + cls + '">' + (szam ? fmt(s.points) : esc(String(s.points))) + '</td></tr>';
    }
    return h + '</table>';
  }

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

  global.FunTasy = { create: create, esc: esc, fmt: fmt, played: played,
                     accToggle: accToggle, accTable: accTable,
                     LIGAK: LIGAK, liga: liga, navHTML: navHTML, renderNav: renderNav };
})(window);
