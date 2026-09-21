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

   A create-en kivul ket nevter-szintu segito is exportalodik a
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

  /* ===== SZEMELYEK - ugyanaz az ember ket liganeven =====
     A ket liga mas neven ismeri ugyanazt az embert: az NB1-ben becenev
     (MLSZ-felhasznalonev), a PL-ben csapatnev. Ahol a ket liga egy lapon
     talalkozik, ez ketszer kinalta oket, ket kulon szakvezetokent - pedig
     egy ember. Itt all EGY helyen, ki kicsoda.

     A PL oldalt AZONOSITO koti be (league_entry "id", NEM az FPL
     "entry_id"): a csapatnevet a tulajdonos barmikor atirhatja, az
     azonosito marad - a nevet a draft.json entries listajabol olvassuk
     hozza. Aki csak az egyik ligaban jatszik, annak nincs sora: o egy
     neven szerepel, osszekotni nincs mivel. */
  var SZEMELYEK = [
    { nb1: 'Ádám',   pl: 254960 },
    { nb1: 'Bazsa',  pl: 267607 },
    { nb1: 'Bence',  pl: 254810 },
    { nb1: 'Csendi', pl: 267857 },
    { nb1: 'Csongi', pl: 277905 },
    { nb1: 'Katyul', pl: 267429 },
    { nb1: 'Vince',  pl: 268988 }
  ];

  /* Nevrol emberre. A `plNevek` a draft.json `entries` tombje ({id, name});
     nelkule - vagy amig meg nem jott - mindenki a sajat neven marad, a lap
     ettol mukodik, csak nem vonja ossze a ket ligat.
     A visszaadott fuggveny minden nevre ad embert: akit nem ismerunk, az
     onmaga, a sajat neven. A `kulcs` az azonossag: ket nev akkor ugyanaz az
     ember, ha a kulcsuk egyezik. */
  function szemelyTar(plNevek) {
    var idNev = {}, nevhez = {};
    (plNevek || []).forEach(function (e) {
      if (e && e.id != null && e.name) idNev[e.id] = e.name;
    });
    SZEMELYEK.forEach(function (sz) {
      var plNev = idNev[sz.pl];
      if (!plNev) return;
      var ember = { kulcs: 'sz' + sz.pl, nevek: [sz.nb1, plNev],
                    felirat: sz.nb1 + ' · ' + plNev };
      nevhez[sz.nb1] = ember;
      nevhez[plNev] = ember;
    });
    return function (nev) {
      return nevhez[nev] ||
             { kulcs: 'n:' + nev, nevek: [nev], felirat: String(nev) };
    };
  }

  // Az ujsag neve es mottoja EGY helyen all: a fejlecben, a felso savban es
  // a lablecben ugyanaz a szo kell hogy alljon.
  var UJSAG_NEV = 'Nemzethy Sport';
  var UJSAG_MOTTO = 'Heti Funtasy Magazin';

  /* ===== KOZOS UZENETEK =====
     Ugyanaz a jelenseg a ket ligaban ugyanazt a mondatot kapja. Ket
     peldanyban alltak, es mar el is kezdtek elcsuszni egymastol: a meccs
     kozbeni mondat "vege" fele a ket oldal mast mondott ugyanarrol.
     Amelyik mondat ligankent MAS (mert a szabaly mas), az fuggveny, es a
     ligat kerdezi meg - nem az oldal dont rola helyben. */
  var UZENET = {
    nemLepettPalyara: 'Nem lépett pályára ebben a fordulóban.',
    esemenyNelkul: 'Lejátszotta a meccset, pontot érő esemény nélkül.',
    nincsValtozas: 'Nem történt változás ebben a fordulóban.',
    /* Meccs kozben a 0 nem mindenhol jelenti ugyanazt: az FPL percrol percre
       ad pontot (eloPontok), tehat ott a 0 tenyleg annyit tesz, hogy eddig
       nem volt pontot ero esemenye. Az MLSZ a pontokat a meccs UTAN rogziti,
       tehat ott ilyet allitani hazugsag volna. */
    meccsKozben: function (ligaId) {
      return (liga(ligaId) || {}).eloPontok
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
    // A folyo fordulo hibauzenetenek rogzitett szovege - ne irjuk at.
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
  /* ===== Felso sav: ket szint, es mindig EGY vilagit =====
     A ligak (NB1, PL) egymas ALTERNATIVAI - ez az elso szint. Az ujsag nem
     a testverei, hanem AZ ADOTT LIGA egyik resze: a masodik szint.

     Korabban ez osszekeveredett. Az ujsag lapjan a liga pottye vilagitott -
     mintha a liga oldalan allnal -, az ujsag gombja pedig eltunt, tehat a
     visszaut maga az a potty volt, ami nem nezett ki visszautnak.

     Most: KITOLTVE az all, AHOL VAGY. A liga oldalan a liga pottye, az
     ujsagban az ujsag gombja - es a liga pottye ilyenkor sima hivatkozas,
     vagyis lathatoan az ut vissza a liga oldalara. A gomb sosem tunik el.

     opts.szakasz: 'ujsag', ha eppen az ujsagot nezed; barmi mas a liga
     oldala. opts.ujsag === false teljesen elhagyja a gombot. */
  function navHTML(aktiv, gyoker, opts) {
    gyoker = gyoker || '';
    opts = opts || {};
    var ujsagban = opts.szakasz === 'ujsag';
    var h = '<a class="markanev" href="' + gyoker + '">FunTasy</a><span class="ligak">';
    for (var i = 0; i < LIGAK.length; i++) {
      var l = LIGAK[i];
      h += '<a class="ligalink' + (l.id === aktiv && !ujsagban ? ' on' : '') +
           '" href="' + gyoker + l.mappa + '" title="' + esc(l.cim) + '">' +
           esc(l.nev) + '</a>';
    }
    h += '</span>';
    if (opts.ujsag !== false)
      // A liga neve kulon elemben all: keskeny kepernyon a CSS elrejti, es a
      // gomb elfer egy sorban. Enelkul a felso sav harom sorba tort.
      h += '<a class="ujsaglink' + (ujsagban ? ' on' : '') + '" href="' + gyoker +
           'nemzethy/' + (aktiv ? '?liga=' + encodeURIComponent(aktiv) : '') + '">' +
           UJSAG_NEV + (aktiv ? '<span class="ujsagliga"> ' + esc(liga(aktiv).nev) +
           '</span>' : '') + '</a>';
    return h;
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

  /* A fordulo ara, es mellette az elozohoz kepesti valtozas. Csak salary
     cap ligaban van ertelme, es csak ott all ki, ahol tudjuk: az arnaplo a
     szezon kozben indult, az azelotti fordulokrol nincs megfigyelesunk, es
     a legkozelebbi kesobbi ar NEM azoke. Ures hely helyett ezert semmi. */
  function arHTML(s, elozoAr, salaryCap) {
    if (!salaryCap || s.ar == null) return '';
    var d = elozoAr == null ? null : Math.round((s.ar - elozoAr) * 10) / 10;
    return '<span class="par">' + fmt(s.ar)
      + (d ? '<span class="pardl ' + (d > 0 ? 'pos' : 'neg') + '">'
             + (d > 0 ? '+' : '\u2212') + fmt(Math.abs(d)) + '</span>' : '')
      + '</span>';
  }

  function profilSorHTML(s, senkinel, salaryCap, elozoAr) {
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
      arHTML(s, elozoAr, salaryCap) +
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
    var elozoAr = null;
    return profilFejHTML(adat) +
      '<div class="proflista">' + sorok.map(function (s) {
        var ki = profilSorHTML(s, adat.senkinel, salaryCap, elozoAr);
        if (s.ar != null) elozoAr = s.ar;
        return ki;
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
     `adat` fuggvenyt, ami a mar betoltott fajlokbol osszerakja a listat,
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

  /* 'itt' az EPPEN NYITOTT oldal azonositoja: onmagara mutato linket nem
     teszunk ki. A valtozasnaplo ezt ugy oldotta meg, hogy egyaltalan nem
     kert lablecet - ket oldalnal mar az sem jo, mert a masikra kellene. */
  var LABLEC = [{ id: 'nemzethy', ut: 'nemzethy/', nev: UJSAG_NEV },
                { id: 'valtozasok', ut: 'valtozasok/', nev: 'Mi újult meg?' }];
  function lablecHTML(gyoker, itt) {
    gyoker = gyoker || '';
    return LABLEC.filter(function (x) { return x.id !== itt; })
      .map(function (x) { return '<a href="' + gyoker + x.ut + '">' + esc(x.nev) + '</a>'; })
      .join('');
  }
  function renderLablec(gyoker, itt) {
    var el = document.getElementById('lablec');
    if (el) el.innerHTML = lablecHTML(gyoker, itt);
  }

  /* Egy hivas beallitja a kozos fejlec-reszeket: a ligavalto savot, a liga
     tipusat (body-osztalykent, hogy CSS-bol es JS-bol is fogodzo legyen) es
     az alcimet. Igy a liga neve/leirasa egyetlen helyen, a LIGAK listaban
     el; az oldal sajat, adatbol szamolt alcimet ezutan is felulirhat. */
  function renderNav(aktiv, gyoker, opts) {
    var el = document.getElementById('liganav');
    if (el) el.innerHTML = navHTML(aktiv, gyoker, opts);
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
     A KIZART HIBA (PL): a nyitva hagyott lap a BETOLTESKORI
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

  /* ===== A FOLYO FORDULO KERETEI, AMIG A GYUJTO MEG NEM IRTA BE OKET =====
     A KIZART HIBA (PL 5. fordulo): elo meccs alatt a lap nem
     frissult. A gyujto 3 orankent fut, a fordulo viszont a nevezesi
     hataridovel indul: a 16:43 UTC-s futas MEG a 4. fordulot latta (a log
     szerint "fordulonkenti keret: GW4"), a kovetkezo 23:47-re volt idozitve.
     Kozben elindult az 5., es a repoban EGYALTALAN nem letezett hozza keret.
     A lap kiment az API-ra, meg is kapta az elo pontokat - csak nem volt
     kire raterite oket, igy elo allas helyett "Naprakesz" allt a
     statuszsavban egy futo meccs alatt.

     A potlas a bongeszo dolga: a hianyzo kereteket fordulonkent EGYSZER
     lekeri. Azert KOZOS, mert a helyzet mindket ligan ugyanez (a gyujto
     ritkabban fut, mint ahogy a fordulo indul); csak a vegpont mas, azt a
     hivo adja. Az NB1 ma azert nem eszleli, mert ott a gyujto MINDEN
     futasban kiirja a teljes aktualis keretet (squads.json) - ha az a fajl
     valaha lemarad, ugyanez a potlas all ide is.

     - `fordulo`: amelyik fordulo kereteirol van szo (a gyorsitotar kulcsa)
     - `kulcsok`: akiknek a keretet le kell kerni (PL: liga-id, NB1: nev)
     - `lekero(kulcs)`: Promise<keret|null>

     Ami mar megjott, azt megjegyzi: a kovetkezo hivas CSAK a meg hianyzokat
     keri le ujra, tehat egy elhasalt lekeres magatol gyogyul a kovetkezo
     percben, es a sikeresek nem mennek ki masodszor. A visszaadott terkep
     ezert lehet RESZLEGES - a hivonak kell eldontenie, mit kezd azzal, akie
     meg nincs meg; nulla pontkent mutatni NEM szabad (futo meccsen hamis
     allas lenne belole). */
  var POTKERET = {};
  function potKeretek(fordulo, kulcsok, lekero) {
    var r = String(fordulo);
    var kesz = POTKERET[r] || (POTKERET[r] = {});
    var kell = (kulcsok || []).filter(function (k) {
      return !(kesz[k] && kesz[k].length);
    });
    if (!kell.length) {
      return Promise.resolve(Object.keys(kesz).length ? kesz : null);
    }
    return Promise.all(kell.map(function (k) {
      return Promise.resolve().then(function () { return lekero(k); })
                    .catch(function () { return null; });
    })).then(function (jott) {
      kell.forEach(function (k, i) {
        if (jott[i] && jott[i].length) kesz[k] = jott[i];
      });
      return Object.keys(kesz).length ? kesz : null;
    });
  }
  /* Fordulohataron a potolt kereteket el kell dobni - kulonben a memoriaban
     maradnanak, es egy kesobbi fordulo felig kesz terkepe mellol az ELOZO
     fordulo keretei nezhetnenek vissza. Parameter nelkul mindent urit. */
  function potKeretekUrit(fordulo) {
    if (fordulo == null) POTKERET = {};
    else delete POTKERET[String(fordulo)];
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
      be in the way of anything. The reader's own click always wins.

      'draft' marks a text that is only visible because the gate was
      lifted for testing - it must look different from a published one. */
  function articleStrip(article, key, label, defaultOpen, draft) {
    if (!article || !article.text || !article.text.length) return '';
    watchArticles();
    watchRating();
    var isOpen = OPEN_ARTICLES.hasOwnProperty(key) ? OPEN_ARTICLES[key] : !!defaultOpen;
    var lead = article.short || article.text[0];
    var body = article.text.map(function (p) { return '<p>' + esc(p) + '</p>'; }).join('');
    return '<details class="artstrip' + (draft ? ' draft' : '') +
      '" data-art="' + esc(key) + '"' +
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
  function articleDraftMode() {
    return /(^|[?&])draft=1(&|$)/.test(location.search);
  }

  /* ===== The magazine: every article in one list =====
     The strip on a match page answers "what happened in THIS match". On a
     Monday someone wants the other thing: read the lot in one sitting,
     without opening eight match pages. Same texts, same gate - the
     selection lives here so the two views cannot drift apart on what may
     be shown.

     'zartE(liga, fordulo)' answers whether a round is final. Each page
     knows that from its own data; the magazine loads the two small files
     it needs. Same rule as the strip: an unfinished round shows only its
     preview. */
  function articleList(store, zartE) {
    var ki = [];
    var L = (store && store.leagues) || {};
    for (var i = 0; i < LIGAK.length; i++) {
      var lg = LIGAK[i].id;
      var fordulok = Object.keys(L[lg] || {}).map(Number).sort(function (a, b) { return b - a; });
      for (var j = 0; j < fordulok.length; j++) {
        var r = fordulok[j], zart = !!(zartE && zartE(lg, r));
        // A HETI ROVAT nem parharchoz tartozik, hanem a fordulohoz, es nincs
        // rajta kapu: elore is nezhet, vissza is. Ezert all a lista elen, es
        // ezert nem fugg attol, lezart-e a fordulo. A kulcsa a sajat cime, `|`
        // nelkul - onnan tudni, hogy nincs ellenfele.
        var fajtak = ['elemzes'].concat(zart ? ['summary', 'preview'] : ['preview']);
        for (var k = 0; k < fajtak.length; k++) {
          var m = L[lg][r][fajtak[k]] || {};
          for (var par in m) {
            var felek = par.split('|');
            ki.push({ liga: lg, fordulo: r, fajta: fajtak[k], par: par,
                      hazai: felek[0], vendeg: felek.length > 1 ? felek[1] : null,
                      cikk: m[par],
                      kulcs: lg + '|' + r + '|' + fajtak[k] + '|' + par,
                      cimke: ARTICLE_LABEL[fajtak[k]] });
          }
        }
      }
    }
    // MEGJELENESI SORRENDBEN, a legfrissebb elol. Az ujsag nem a forduloval
    // halad, hanem az idovel: ami ma keszult el, az van felul, akkor is, ha
    // egy regebbi fordulorol szol. A `kozzetett` az elesbe kerules ideje; ami
    // meg vazlat, annak nincs ilyen, es a lista aljara kerul a korabbi rend
    // szerint (fordulo csokkenoen, azon belul rovat, osszefoglalo, beharangozo).
    var rang = { elemzes: 0, summary: 1, preview: 2 };
    ki.sort(function (a, b) {
      var ai = a.cikk && a.cikk.kozzetett, bi = b.cikk && b.cikk.kozzetett;
      if (ai && !bi) return -1;
      if (bi && !ai) return 1;
      // Egy commitban tobb iras is kimegy, tehat az AZONOS idobelyeg gyakori.
      // Ilyenkor a rendezes nem bizhato a beillesztes sorrendjere: a csoporton
      // belul a frissebb fordulo all elol, azon belul rovat, osszefoglalo,
      // beharangozo - kulonben egy egyutt kikerult adag sorrendje esetleges.
      if (ai && bi && ai !== bi) return ai < bi ? 1 : -1;
      return (b.fordulo - a.fordulo) || (rang[a.fajta] - rang[b.fajta]);
    });
    return ki;
  }

  /** One article in full - the magazine shows the text, not a teaser.

      Ujsagszeru sorrend: felul a rovat (kicsi, halk), alatta a parharc
      CIMKENT, aztan a rovid valtozat FELUTESKENT - ugyanaz a mondat, ami a
      meccs adatlapjan a becsukott savban all, itt a bevezeto szerepet
      jatssza. A torzs csak ezutan jon. Igy a lapon vegiggorgetve is el
      lehet donteni, mit akar elolvasni az ember. */
  function articleCardHTML(be) {
    var body = (be.cikk.text || []).map(function (p) {
      return '<p>' + esc(p) + '</p>';
    }).join('');
    var azon = 'c-' + be.kulcs.replace(/[^A-Za-z0-9]+/g, '-');
    return '<article class="magcikk" id="' + esc(azon) + '">' +
      '<div class="magkicker">' +
        '<span class="magrovat">' + esc(be.cimke) + '</span>' +
        '<span class="magfordulo">' + esc(liga(be.liga).nev) + ' · ' +
          be.fordulo + '. forduló</span>' +
        '<button class="magmaso" data-maso="' + esc(azon) + '" ' +
          'data-szoveg="' + esc((be.cikk.text || []).join('\n\n')) +
          '">Másolom</button>' +
      '</div>' +
      '<h3 class="magpar">' + esc(be.hazai) +
        (be.vendeg ? '<span class="magvs">–</span>' + esc(be.vendeg) : '') + '</h3>' +
      (be.cikk.short ? '<p class="maglead">' + esc(be.cikk.short) + '</p>' : '') +
      '<div class="magtest">' + body + '</div>' +
      rateBar(be.kulcs) + '</article>';
  }

  /* A "Masolom" A CIKKET es a ra mutato hivatkozast teszi a vagolapra.
     Korabban a rovid valtozat ment - az viszont a felutes, nem az iras: aki
     a gombot megnyomja, a szoveget akarja beilleszteni valahova, nem az egy
     mondatos ajanlot. A regi execCommand-os utat is meghagyjuk - a navigator
     API nem biztonsagos kontextusban (http://) nem letezik. */
  var magWatched = false;
  function watchMagazine() {
    if (magWatched) return;
    magWatched = true;
    document.addEventListener('click', function (e) {
      var g = e.target.closest && e.target.closest('.magmaso');
      if (!g) return;
      var szoveg = (g.getAttribute('data-szoveg') || '') + '\n\n' +
                   location.href.split('#')[0] + '#' + g.getAttribute('data-maso');
      var kesz = function (ok) {
        g.textContent = ok ? 'Kimásolva' : 'Nem sikerült';
        setTimeout(function () { g.textContent = 'Másolom'; }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText)
        navigator.clipboard.writeText(szoveg).then(function () { kesz(true); },
                                                   function () { kesz(false); });
      else {
        var t = document.createElement('textarea');
        t.value = szoveg; t.style.position = 'fixed'; t.style.opacity = '0';
        document.body.appendChild(t); t.select();
        var ok = false;
        try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
        document.body.removeChild(t);
        kesz(ok);
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

  /* Egy eszkoz egy irast egyszer ertekel. Az azonositot a bongeszo tarolja,
     nem mi adjuk ki: nem szemely azonositasara valo, hanem arra, hogy az
     ujraertekeles a sajat korabbit irja felul, ne halmozzon. */
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

  /* 'uzenet' a most elkuldott ertekeles nyugtazasa; nelkule a korabbi
     ertekelesre emlekezik. MINDKET allapot ugyanazt a kiutat kinalja: aki
     epp most adott pontot, ugyanugy meggondolhatja magat, mint aki egy hete. */
  function rateBar(key, uzenet) {
    var volt = rateRemembered(key);
    if (uzenet || volt)
      return '<div class="artrate" data-art="' + esc(key) + '">' +
             '<span class="artratedone">' +
             esc(uzenet || ('Köszi, ' + volt + '-esre értékelted.')) + '</span>' +
             '<button class="artrateagain" data-ujra="1">Mégis mást gondolok</button></div>';
    var g = '';
    for (var i = 1; i <= 4; i++)
      g += '<button class="artrateg" data-pont="' + i + '" title="' + esc(RATE_LABEL[i]) +
           '">' + i + '</button>';
    return '<div class="artrate" data-art="' + esc(key) + '">' +
           '<span class="artratekerdes">Milyen lett?</span>' + g +
           '<span class="artratesegit">1 = rossz · 4 = nagyon jó</span></div>';
  }

  function rateReasonHTML(pont) {
    return '<div class="artreason">' +
      '<div class="artreasonq">' + (pont === 1 ? 'Ennyire rossz? Mondd meg, mi a baj vele.'
                                               : 'Mi hiányzott belőle?') + '</div>' +
      '<textarea class="artreasont" rows="3" maxlength="600" ' +
      'placeholder="A saját szavaddal — egy mondat is elég. Ebből lesz jobb a következő."' +
      '></textarea>' +
      '<div class="artreasonb">' +
        '<button class="artsend" disabled>Elküldöm</button>' +
        '<button class="artskip">Kötekszem, de indokolni már nem fogok</button>' +
      '</div></div>';
  }

  function rateSend(key, pont, indok) {
    var eszkoz = rateDevice();
    if (!eszkoz) return Promise.resolve(false);
    return fetch(SAJAT_PROXY + '/ertekeles', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cikk: key, eszkoz: eszkoz, pont: pont, indok: indok || '' }),
    }).then(function (r) { return r.ok; }).catch(function () { return false; });
  }

  function rateThanks(sav, key, pont, indokolt) {
    try { localStorage.setItem('funtasy-ert:' + key, String(pont)); } catch (e) {}
    sav.outerHTML = rateBar(key, indokolt ? 'Köszi — ebből tényleg tanulunk.'
                                          : 'Köszi, megjegyeztük.');
  }

  var rateWatched = false;
  function watchRating() {
    if (rateWatched) return;
    rateWatched = true;
    document.addEventListener('click', function (e) {
      var sav = e.target.closest && e.target.closest('.artrate');
      if (!sav) return;
      var key = sav.getAttribute('data-art');
      var g = e.target.closest('button');
      if (!g || !key) return;
      // a sav a cikken BELUL van: a kattintas ne csukja be a <details>-t
      e.preventDefault();
      e.stopPropagation();
      if (g.hasAttribute('data-ujra')) {
        try { localStorage.removeItem('funtasy-ert:' + key); } catch (err) {}
        sav.outerHTML = rateBar(key);
        return;
      }
      if (g.classList.contains('artsend') || g.classList.contains('artskip')) {
        var p = +sav.getAttribute('data-pont');
        var t = sav.querySelector('.artreasont');
        // A kiuttal kuldott ertekeles mellol az indok AKKOR SEM megy el, ha
        // mar beirta: meggondolta magat, nem a hata mogott kuldozgetunk.
        var indok = g.classList.contains('artskip') ? '' : ((t && t.value) || '').trim();
        g.disabled = true;
        rateSend(key, p, indok).then(function (ok) {
          if (ok) rateThanks(sav, key, p, !!indok);
          else { g.disabled = false;
                 sav.querySelector('.artreasonq').textContent =
                   'Nem sikerült elküldeni. Próbáld meg még egyszer.'; }
        });
        return;
      }
      var pont = +g.getAttribute('data-pont');
      if (!(pont >= 1 && pont <= 4)) return;
      // HARMAS-NEGYES: egy koppintas, semmi tovabbi kerdes.
      if (pont >= 3) {
        sav.innerHTML = '<span class="artratedone">Küldjük…</span>';
        rateSend(key, pont, '').then(function (ok) {
          if (ok) rateThanks(sav, key, pont, false);
          else sav.innerHTML = '<span class="artratedone">Nem sikerült elküldeni.</span>';
        });
        return;
      }
      // EGYES-KETTES: itt kerjuk az indokot.
      sav.setAttribute('data-pont', String(pont));
      sav.innerHTML = rateReasonHTML(pont);
      var t = sav.querySelector('.artreasont');
      if (t) t.focus();
    }, false);
    // Az "Elkuldom" indokot var: amig nincs, nem is kinalja magat. A kiut
    // vegig elerheto marad, tehat ez nem csapda, hanem az, hogy a ket gomb
    // ket kulonbozo dolgot jelent.
    document.addEventListener('input', function (e) {
      if (!e.target.classList || !e.target.classList.contains('artreasont')) return;
      var sav = e.target.closest('.artrate');
      var kuld = sav && sav.querySelector('.artsend');
      if (kuld) kuld.disabled = !e.target.value.trim();
    }, false);
  }

  /** The published store with the draft one laid over it.

      Unpublished text lives in its own file, which the pages fetch only in
      draft mode - so nothing half-finished can reach a visitor by a
      forgotten flag. This merges the two down to the fixture, rather than
      letting the draft file replace the published one wholesale: in draft
      mode we want to see everything that exists, not only the new part. */
  function mergeArticles(published, draft) {
    if (!draft || !draft.leagues) return published;
    var ki = { updated: draft.updated || (published && published.updated) || null,
               leagues: {} };
    var be = [published, draft];
    for (var i = 0; i < be.length; i++) {
      var L = (be[i] && be[i].leagues) || {};
      for (var lg in L) {
        ki.leagues[lg] = ki.leagues[lg] || {};
        for (var r in L[lg]) {
          ki.leagues[lg][r] = ki.leagues[lg][r] || {};
          for (var k in L[lg][r]) {
            ki.leagues[lg][r][k] = ki.leagues[lg][r][k] || {};
            for (var par in L[lg][r][k]) ki.leagues[lg][r][k][par] = L[lg][r][k][par];
          }
        }
      }
    }
    return ki;
  }

  /** The strip for one fixture, straight from a loaded articles.json.

      A round can hold both kinds at once - the preview is written before it
      and the summary after - and then the summary wins: it is the one that
      knows how the match ended.

      The two sides are looked up in BOTH orders. Which name is the home one
      is a property of the fixture list, not of the article, so a reversed
      pair must not silently drop the text.

      opts.closed     - is this round final? (see the gate above)
      opts.defaultOpen - open the strip up front
      ?draft=1 in the URL lifts the gate, and then the held-back summary is
      labelled as a draft so it can never be mistaken for a published one. */
  /* A rovat neve EGY helyen all: a meccs adatlapjan, a magazin kartyajan es
     a magazin tipus-szurojeben ugyanaz a szo kell hogy alljon. */
  var ARTICLE_LABEL = { summary: 'Összefoglaló', preview: 'Beharangozó',
                        elemzes: 'Kele Janek elemez' };
  function rovatNev(fajta) { return ARTICLE_LABEL[fajta] || fajta; }
  function matchArticle(store, league, round, a, b, opts) {
    opts = opts || {};
    var r = store && store.leagues && store.leagues[league] &&
            store.leagues[league][round];
    if (!r) return '';
    var lifted = !opts.closed && articleDraftMode();
    var kinds = (opts.closed || lifted) ? ['summary', 'preview'] : ['preview'];
    // MINDKETTO kint marad a lezart fordulon, az osszefoglalo elol. A
    // beharangozo nem avul el a lefujassal: az mondja meg, mi volt a kerdes,
    // az osszefoglalo meg azt, mi lett a valasz - egymas mellett a ketto
    // tobbet er, mint kulon. Nyitva viszont csak az elso all.
    var ki = '';
    for (var i = 0; i < kinds.length; i++) {
      var m = r[kinds[i]];
      if (!m) continue;
      var k = m[a + '|' + b] ? a + '|' + b : (m[b + '|' + a] ? b + '|' + a : null);
      if (!k) continue;
      var held = lifted && kinds[i] === 'summary';
      ki += articleStrip(m[k], league + '|' + round + '|' + kinds[i] + '|' + k,
                         ARTICLE_LABEL[kinds[i]] + (held ? ' · vázlat' : ''),
                         opts.defaultOpen && !ki, held);
    }
    return ki;
  }

  /* ===== Nezet-verem: egy modal, amiben lapozni lehet =====
     NAVIGACIOT egy feluleten belul valtunk: a tartalom cserelodik, es a
     "vissza" gomb az elozo nezetre lep. Az x / felrekattintas / Escape
     mindig mindent zar. A belepesi pont 'root', a fulvaltas 'replace', a
     listabol nyilo nezet 'push'; a 'noop' a verembol ujrarajzolt nezet
     (nem tolunk ra semmit).

     Ez a szabaly korabban ugy szolt, hogy "modalba nem nyitunk modalt" -
     ennel szukebb az igazsag, es a szeles valtozat rossz helyen allitott
     volna meg. Amit ved, az a navigacio: ket egymasra csuszo nezet kozt a
     nezo elveszti, hol jar, es melyik x-et nyomja. Egy REteg (megerosites,
     rovid urlap) attol meg nyilhat egy modal folott - de csak akkor, ha az
     alatta levo tartalom elvesztese nem szamit. Ahol szamit - peldaul a
     cikk ertekelesenel, ahol epp arrol kerunk velemenyt, ami alatta all -,
     ott helyben nyilo panel jar, nem uj reteg.

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

  /* SAJAT proxy (Cloudflare Worker, tartalek/proxy-worker.js): ha be van
     allitva, ez az elso ut minden elo lekeresnel - a sajat fiok alatt fut,
     senki nem kapcsolja le, es az ingyenes kerete (100k/nap) a forgalmunk
     sokszorosa. Amig ures, a lekero kihagyja, es a publikus proxyk viszik. */
  var SAJAT_PROXY = 'https://funtasy-liga.swick00.workers.dev';

  /* ===== AZ UTOLSO ISMERT ALLAS =====
     A problema : "ha valaki mar lekerdezte, lassam azt -
     ne lassak regebbi adatot, mint a legutobbi lekerdezes". A lap elso kepe
     eddig a repobol jott, amit a gyujto 3 orankent frissit; ha a telefonod
     tiz perce mar lekerte a friss allast, a gepen megis a regit lattad, es
     meg is kellett varnod, amig a lekeresek ujra lefutnak.

     Gyorsitotarral ez NEM oldhato meg: az lejar es eldob, tehat aki a
     lejarat utan erkezik, ugyanott van. A Worker ezert MEGJEGYZI, amit o
     maga lekert (lasd tartalek/proxy-worker.js), es itt egyetlen keresben
     vissza is adja - barhany cel-URL-re egyszerre.

     Visszaad: Promise<{<url>: {ido, adat}} | null>. `adat` a nyers valasz
     szovege, `ido` a lekerese. Hianyzo vagy meg nem tarolt URL egyszeruen
     nincs benne a valaszban - a hivo ilyenkor az elo utra tamaszkodik.
     SOSEM dob: ez egy gyorsito lepes, nem lehet belole hiba. */
  function taroltak(urlok) {
    if (!SAJAT_PROXY || !urlok || !urlok.length) return Promise.resolve(null);
    var q = urlok.map(function (u) { return 'url=' + encodeURIComponent(u); }).join('&');
    return fetch(SAJAT_PROXY + '/tarolt?' + q,
                 { cache: 'no-store', headers: { 'Accept': 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { return (j && Object.keys(j).length) ? j : null; })
      .catch(function () { return null; });
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
    /* Az ut-sorrend MERT megbizhatosag, nem izles (naplo/proxy-meres.txt):
       egy napon a corsproxy.io 401-re valtott (regisztraciohoz
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
      // a meresben pont ez ment, amikor a /raw eppen nem. A kibont bontja ki.
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
             + '<span class="vanev">' + esc(cs.osszCim || 'Összesen') + '</span>'
             + '<span class="vacimke"></span>'
             + '<span class="vaert"></span><span class="zdiff '
             + (cs.guard > 0 ? 'pos' : cs.guard < 0 ? 'neg' : '') + '">'
             + guardJelol(cs.guard) + '</span></div>'
           : '')
        + '</div>';
    }).join('') + '</div>';
  }

  /* ===== FORDULO-LAPOZO =====
     Egy legordulo es ket nyil: ugyanaz a vezerlo all a ket liga zarasi
     panelje folott. Ket peldanyban allt, ket kulon allapotmodellel - az
     egyik a valasztott ERTEKBOL szamolta a kovetkezo fordulot, a masik az
     INDEXBOL -, es a ket panel lapozoja mar el is csuszott egymastol.
     A hivo annyit ad meg, hova rajzoljon, es mi tortenjen valtaskor.

     A muveletek: `tolt(ertekek, aktiv)` feltolti a legordulot, `ertek()`
     megmondja, melyik fordulon all. Egy legordulohoz EGY lapozo tartozik:
     ujabb hivasra ugyanazt adja vissza, nem koti be megegyszer az
     esemenyeket (a betolto ut tobbszor is lefuthat). */
  function forduloLapozo(opts) {
    var sel = document.getElementById(opts.sel);
    if (!sel) return null;
    if (sel.__lapozo) return sel.__lapozo;
    var valt = opts.valt || function () {};
    function lep(irany) {
      var i = sel.selectedIndex + irany;
      if (i < 0 || i >= sel.options.length) return;
      sel.selectedIndex = i;
      valt(+sel.value);
    }
    sel.addEventListener('change', function () { valt(+sel.value); });
    // A nyilak a legordulo MELLETT allnak, nem benne; a kozos szulojukre
    // figyelunk, igy a ket lap sajat elrendezese valtozatlan maradhat.
    var sav = sel.parentNode;
    if (sav) sav.addEventListener('click', function (e) {
      var g = e.target.closest && e.target.closest('[data-znav]');
      if (g) lep(+g.getAttribute('data-znav'));
    });
    sel.__lapozo = {
      tolt: function (ertekek, aktiv) {
        sel.innerHTML = ertekek.map(function (r) {
          return '<option value="' + r + '">' + r + '. forduló</option>';
        }).join('');
        sel.value = String(aktiv != null ? aktiv : ertekek[ertekek.length - 1]);
      },
      ertek: function () { return +sel.value; }
    };
    return sel.__lapozo;
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
      // A `location.reload()` a HTTP-gyorsitotarat NEM keruli meg: a lap
      // ugyanazt a REGI HTML-t kaphatja vissza (a kiszolgalo tiz percre adja
      // ki), a hurok-vedelem pedig utana mar nem probalkozik - a nezo ott
      // ragad a regi lapon, es csak kezi frissitessel jut tovabb. Ezert
      // eloszor FRISSEN lehuzzuk magat a dokumentumot: a `cache: 'reload'`
      // felulirja a tarolt peldanyt, es az utana kovetkezo toltes mar az ujat
      // kapja. Ha a lehuzas elhasal, akkor is toltunk - rosszabb nem lesz
      // tole, mint a regi viselkedes.
      var ujra = function (){ location.reload(); };
      fetch(location.href, { cache: 'reload' }).then(ujra, ujra);
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
                     UZENET: UZENET,
                     SZEMELYEK: SZEMELYEK, szemelyTar: szemelyTar,
                     lablecHTML: lablecHTML, renderLablec: renderLablec,
                     bontasMeccsSor: bontasMeccsSor,
                     zarasLista: zarasLista, forduloLapozo: forduloLapozo,
                     verzioOr: verzioOr,
                     valtoztatasLista: valtoztatasLista,
                     profilHTML: profilHTML, profilFejHTML: profilFejHTML,
                     jatekosKereso: jatekosKereso, ekezetlen: ekezetlen,
                     profilNyitoHTML: profilNyitoHTML, profilNezo: profilNezo,
                     kezdSzazalek: kezdSzazalek, KEZD_CIM: KEZD_CIM,
                     kezdParHTML: kezdParHTML,
                     matchArticle: matchArticle,
                     articleDraftMode: articleDraftMode,
                     mergeArticles: mergeArticles, rovatNev: rovatNev,
                     articleList: articleList, articleCardHTML: articleCardHTML,
                     watchMagazine: watchMagazine,
                     UJSAG_NEV: UJSAG_NEV, UJSAG_MOTTO: UJSAG_MOTTO,
                     statusz: statusz, ujraLathatokor: ujraLathatokor,
                     eloFrissito: eloFrissito, taroltak: taroltak,
                     potKeretek: potKeretek, potKeretekUrit: potKeretekUrit,
                     lassuJelzo: lassuJelzo, allasHTML: allasHTML,
                     nezetVerem: nezetVerem, lekero: lekero,
                     eloKereso: eloKereso, hibajelzo: hibajelzo, h2hNezo: h2hNezo };
})(window);
