const { BASE, jo, inditas, vege, apiKi } = require('./kozos');
// Kezdoallitasi hatekonysag: mennyit hozott a felallitott kezdo abbol,
// amennyit a keretbol ki lehetett volna hozni.
//
// PL: a bongeszo szamol (plHatekonysag) - a legjobb ERVENYES formacio
// (1 kapus, 3-5 vedo, 1-3 csatar) a 15-bol. A teszt kezzel kiszamolt
// keretre allit, es rogziti, hogy az ervenytelen formacio (6 vedo) nem
// szamit lehetonek.
// NB1: a gyujto szamol (gyujto_hatekonysag.py teszteli); itt azt merjuk,
// hogy a tabella oszlopa a hatekonysag.json-bol toltodik, es a szazalek
// a lezart fordulok osszesitese.
(async () => {
  const br = await inditas();

  // ---------------- PL: a szamitas maga ----------------
  console.log('--- PL: plHatekonysag ---');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await apiKi(p);
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof plHatekonysag === 'function'
    && Object.keys(PLAYERS).length > 0, null, { timeout: 20000 });

  const szamol = (osszetetel) => p.evaluate(([osszetetel]) => {
    // valodi jatekosok posztonkent, determinisztikus sorrendben
    const poszt = { GKP: [], DEF: [], MID: [], FWD: [] };
    Object.keys(PLAYERS).map(Number).sort((a, b) => a - b)
      .forEach(e => { const pz = PLAYERS[e].p; if (poszt[pz]) poszt[pz].push(e); });
    const sq = [];
    for (const [pz, db, pts, pad] of osszetetel)
      for (let i = 0; i < db; i++)
        sq.push({ e: poszt[pz][sq.filter(x => PLAYERS[x.e].p === pz).length],
                  b: pad, pts: pts[i] });
    return plHatekonysag(sq);
  }, [osszetetel]);

  // 2 GKP (8,2), 5 DEF (6,5,4,1,0), 5 MID (9,7,3,2,0), 3 FWD (10,4,1)
  // legjobb formacio: 1-3-4-3? DEF top3=15, MID top4=21, FWD top3=15, GKP 8
  //   3-4-3: 8+15+21+15 = 59;  3-5-2: 8+15+21+14=58;  4-4-2: 8+16+21+14=59;
  //   4-3-3: 8+16+19+15 = 58;  5-3-2: 8+16+19+14=57;  4-5-1: 8+16+21+10=55;
  //   5-4-1: 8+16+21+10=55 -> a maximum 59
  const v = await szamol([
    ['GKP', 1, [8], false], ['GKP', 1, [2], true],
    ['DEF', 4, [6, 5, 4, 1], false], ['DEF', 1, [0], true],
    ['MID', 4, [9, 7, 3, 2], false], ['MID', 1, [0], true],
    ['FWD', 2, [10, 4], false], ['FWD', 1, [1], true],
  ]);
  console.log('   szerzett/leheto: ' + JSON.stringify(v));
  jo(v && v.le === 59, 'a lehető a legjobb ÉRVÉNYES formáció (59): ' + (v && v.le));
  jo(v && v.sz === 8 + 16 + 21 + 14, 'a szerzett a kezdők összege (' + (v && v.sz) + ')');

  // ervenytelen formaciot nem szamolunk lehetonek: 6 vedos "legjobb" tiltott
  const v2 = await szamol([
    ['GKP', 1, [8], false], ['GKP', 1, [0], true],
    ['DEF', 6, [9, 9, 9, 9, 9, 9], false],
    ['MID', 4, [1, 1, 0, 0], false], ['MID', 1, [0], true],
    ['FWD', 1, [1], false], ['FWD', 1, [0], true],
  ]);
  jo(v2 && v2.le === 8 + 45 + 2 + 1,
     'legfeljebb 5 védő számolható, a hatodik helyére középpályás jön: ' + (v2 && v2.le));

  // a tabella oszlopa valodi adaton: minden sorban van % vagy kotojel
  const oszlop = await p.evaluate(() => {
    T.renderTable();
    return { fej: !!document.querySelector('#table th[title*="Kezdőállítási"]'),
             cellak: [...document.querySelectorAll('#table td.kezdpc')].map(x => x.textContent) };
  });
  console.log('   tabella: ' + JSON.stringify(oszlop.cellak));
  jo(oszlop.fej, 'a PL tabellának van KEZD% oszlopa (title-lel)');
  jo(oszlop.cellak.length === 10 && oszlop.cellak.every(x => /^\d+%$|^–$/.test(x)),
     'minden sorban százalék (vagy kötőjel) áll');
  jo(perr.length === 0, 'nincs JS-hiba a PL-oldalon: ' + JSON.stringify(perr));
  await p.close();

  // ---------------- NB1: a json-bol toltodo oszlop ----------------
  console.log('--- NB1: tabella a hatekonysag.json-ból ---');
  const p2 = await br.newPage();
  const perr2 = []; p2.on('pageerror', e => perr2.push(e.message));
  await apiKi(p2);
  // sajat adat, hogy az elvart szazalek kezzel szamolhato legyen:
  // 1. fordulo (lezart): sz=40 le=50; 2. fordulo (lezart): sz=50 le=50
  // -> osszesitve 90/100 = 90%. Az 5. IDEIGLENES fordulo (sz=0 le=100)
  // SZANDEKOSAN kimarad; a 3-4. lezart, de nincs hozzajuk kezd-ertek ->
  // az is kimarad (nem szamit 0-nak).
  // A forgatokonyv a VALOSAGOT koveti: ideiglenesnek olyan fordulot
  // jelolunk, aminek meg nincs eredmenye - a lap beegetett SCHEDULE-jeben
  // az 5. fordulo null-null, tehat nem szamit lejatszottnak.
  let nevek;
  await p2.route('**/hatekonysag.json*', async route => {
    const r = await fetch(BASE + 'results.json');
    const j = await r.json();
    nevek = [...new Set(j.schedule['1'].flat().filter(x => typeof x === 'string'))];
    const sor = (sz, le) => Object.fromEntries(nevek.map(n => [n, { sz, le }]));
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ rounds: { 1: sor(40, 50), 2: sor(50, 50), 5: sor(0, 100) } }) });
  });
  await p2.route('**/results.json*', async route => {
    const v3 = await route.fetch(); const j = await v3.json();
    j.provisional = [5];             // az 5. fordulo ideiglenes...
    j.schedule['5'] = (j.schedule['5'] || []).map(m => [m[0], m[1], null, null]);
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(j) });
  });
  await p2.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p2.waitForFunction(() => document.querySelector('#table td.kezdpc'), null, { timeout: 20000 });
  const nb1 = await p2.evaluate(() => ({
    cellak: [...document.querySelectorAll('#table td.kezdpc')].map(x => x.textContent),
    cim: (document.querySelector('#table td.kezdpc') || {}).title,
  }));
  console.log('   cellák: ' + JSON.stringify(nb1.cellak) + ' | title: ' + JSON.stringify(nb1.cim));
  jo(nb1.cellak.length > 0 && nb1.cellak.every(x => x === '90%'),
     'az összesítés a LEZÁRT fordulókból számol (40+50)/(50+50)=90% — az ideiglenes kimarad');
  jo(/40|90/.test(nb1.cim || ''), 'a cella title-je a pont-párt mutatja: ' + JSON.stringify(nb1.cim));

  // a Fordulok ful KOZOS renderelobol jon (T.fordulokHTML) - az NB1-en is
  // ott a KEZD% oszlop, fordulonkent (1.: 40/50=80%, 2.: 50/50=100%)
  const fordulok = await p2.evaluate(([nev]) => {
    const d = document.createElement('div');
    d.innerHTML = T.fordulokHTML(nev);
    return { fej: !!d.querySelector('th[title*="Kezdőállítási"]'),
             cellak: [...d.querySelectorAll('td.kezdpc')].map(x => x.textContent).slice(0, 4) };
  }, [nevek[0]]);
  console.log('   NB1 Fordulók fül: ' + JSON.stringify(fordulok.cellak));
  jo(fordulok.fej, 'az NB1 Fordulók fülén is van KEZD% oszlop (közös renderelő)');
  jo(fordulok.cellak[0] === '80%' && fordulok.cellak[1] === '100%',
     'fordulónkénti értékek: 1.=80%, 2.=100% — ' + JSON.stringify(fordulok.cellak));

  // a meccs-fejlec sora KETOLDALT igazit: a bal ertek a bal szelhez, a
  // jobb a jobbhoz - ahogy a fejlec minden mas adata
  const igazitas = await p2.evaluate(() => {
    const d = document.createElement('div');
    d.style.cssText = 'width:400px';
    d.innerHTML = FunTasy.kezdParHTML({ sz: 40, le: 50 }, { sz: 45, le: 50 }, false);
    document.body.appendChild(d);
    const k = d.querySelector('.kezdsor').getBoundingClientRect();
    const bal = d.querySelector('.kezdbal').getBoundingClientRect();
    const jobb = d.querySelector('.kezdjobb').getBoundingClientRect();
    const cim = d.querySelector('.kezdcim').textContent.trim();
    d.remove();
    return { balOK: Math.abs(bal.left - k.left) <= 1, jobbOK: Math.abs(jobb.right - k.right) <= 1, cim };
  });
  jo(igazitas.balOK && igazitas.jobbOK,
     'a két érték a saját térfeléhez igazodik (bal a bal szélen, jobb a jobbon)');
  jo(/kezdőállítás/.test(igazitas.cim), 'középen a címke: ' + JSON.stringify(igazitas.cim));

  jo(perr2.length === 0, 'nincs JS-hiba az NB1-oldalon: ' + JSON.stringify(perr2));
  await vege(br);
})();
