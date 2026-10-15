const { BASE, check, failures, launch, finish, rewriteJson, blockApis } = require('./common');
// A valtozasnaplo: ket szuro, es a liga CIMKEKENT viselkedik.
//
// A ligacimke azert fontos, mert nem mindenki jatszik minden ligaban: ha egy
// bejegyzes mindkettot erinti, BARMELYIKRE szurve elo kell jonnie. A valos
// adatban ma nincs ilyen bejegyzes, ezert a teszt allitja elo - a repo
// elvei szerint menet kozben, nem tarolt fixturabol.

const cim = t => t.replace(/\s+/g, ' ').trim();
// A varhato ertekeket a VALODI adatbol szamoljuk, nem irjuk be szamkent:
// kulonben minden uj naplobejegyzes megbuktatna a tesztet.
const ADAT = require(require('path').join(__dirname, '..', 'valtozasok.json')).bejegyzesek;
const PLUSZ = { datum: '2999-01-01', tipus: 'funkcio', ligak: ['nb1', 'pl'],
                cim: 'MINDKETTO', leiras: 'Mindkét ligát érinti.' };
const OSSZES = [PLUSZ].concat(ADAT);
const hany = f => OSSZES.filter(f).length;
const cimekEbbol = f => OSSZES.filter(f).map(b => cim(b.cim));
const csakPl  = cimekEbbol(b => b.ligak.includes('pl')  && !b.ligak.includes('nb1'));
const csakNb1 = cimekEbbol(b => b.ligak.includes('nb1') && !b.ligak.includes('pl'));

(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 1000, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  // egy mindket ligat erinto bejegyzes hozzaadasa
  await rewriteJson(p, '**/valtozasok.json*', j => {
    j.bejegyzesek.unshift(PLUSZ);
    return j;
  });
  await p.goto(BASE + 'valtozasok/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('.vlt-tetel');

  const cimek = async () => (await p.locator('.vlt-tetel h3').allInnerTexts()).map(cim);
  const chip = async (sor, szoveg) => {
    await p.locator(`#${sor} .vlt-chip`, { hasText: new RegExp('^' + szoveg + '$') }).first().click();
    await p.waitForTimeout(60);
  };

  console.log('--- alapállapot ---');
  const mind = await cimek();
  console.log('   ' + mind.length + ' bejegyzés:', JSON.stringify(mind.map(x => x.slice(0, 28))));
  check(mind.length === OSSZES.length,
    `szűrés nélkül minden bejegyzés látszik (${OSSZES.length})`);
  check(mind[0] === 'MINDKETTO', 'a legfrissebb dátum van elöl');
  // az innerText a CSS text-transform:uppercase-t is visszaadja, ezert /i
  const datumok = await p.locator('.vlt-datum').allInnerTexts();
  console.log('   dátumfejlécek:', JSON.stringify(datumok.map(cim)));
  check(datumok.some(t => /augusztus 24/i.test(t)),
    'a dátum magyarul, csoportfejlécként jelenik meg');
  check(datumok.length === new Set(OSSZES.map(b => b.datum)).size,
    'annyi dátumcsoport van, ahány különböző nap');

  // A .panel-nek nincs sajat belso margoja, a gyerekei adjak - ha egy sav
  // kifelejti, a szoveg a keretnek er. Ezt egyszer mar elrontottam.
  const margok = await p.evaluate(() => {
    const bal = s => parseFloat(getComputedStyle(document.querySelector(s)).paddingLeft);
    return { szuro: bal('.vlt-szurok'), datum: bal('.vlt-datum'), tetel: bal('.vlt-tetel') };
  });
  console.log('   bal belső margók:', JSON.stringify(margok));
  check(Object.values(margok).every(x => x >= 12),
    'minden sávnak van belső margója (a szöveg nem ér a kerethez)');

  console.log('\n--- típus szerint ---');
  await chip('tipusSzuro', 'Javítás');
  const javitasok = await cimek();
  console.log('   javítások:', JSON.stringify(javitasok.map(x => x.slice(0, 28))));
  check(javitasok.length === hany(b => b.tipus === 'bugfix') && !javitasok.includes('MINDKETTO'),
    'a Javítás szűrő csak a javításokat hagyja meg');
  await chip('tipusSzuro', 'Új funkció');
  check((await cimek()).includes('MINDKETTO'), 'az Új funkció szűrő az új funkciókat hagyja meg');
  await chip('tipusSzuro', 'Mind');
  check((await cimek()).length === OSSZES.length, 'a Mind visszaadja az összeset');

  console.log('\n--- liga: CÍMKEKÉNT viselkedik-e ---');
  await chip('ligaSzuro', 'NB1');
  const nb1 = await cimek();
  console.log('   NB1:', JSON.stringify(nb1.map(x => x.slice(0, 28))));
  check(nb1.includes('MINDKETTO'), 'a mindkét ligát érintő bejegyzés NB1-re szűrve is előjön');
  // A cimekre illesztes nemán atmenne, ha a szoveg valtozik (meg is tortent):
  // a varhato cimeket ezert az ADATBOL szedjuk, es megkoveteljuk, hogy legyen
  // mit ellenoriznie.
  check(csakPl.length > 0 && !csakPl.some(c => nb1.includes(c)),
    `a csak PL-es bejegyzések NB1-re szűrve nem jönnek elő (${csakPl.length} ilyen)`);
  await chip('ligaSzuro', 'NB1');        // kikapcs
  await chip('ligaSzuro', 'PL');
  const pl = await cimek();
  console.log('   PL:', JSON.stringify(pl.map(x => x.slice(0, 28))));
  check(pl.includes('MINDKETTO'), 'ugyanaz a bejegyzés PL-re szűrve is előjön');
  check(csakNb1.length > 0 && !csakNb1.some(c => pl.includes(c)),
    `a csak NB1-es bejegyzések PL-re szűrve nem jönnek elő (${csakNb1.length} ilyen)`);

  console.log('\n--- a ligák KÜLÖN kapcsolhatók (aki több ligában játszik) ---');
  await chip('ligaSzuro', 'NB1');        // a PL mellé
  const ketto = await cimek();
  console.log('   NB1 + PL:', JSON.stringify(ketto.map(x => x.slice(0, 28))));
  check(ketto.length === hany(b => b.ligak.some(x => x === 'nb1' || x === 'pl')),
    'két ligát kijelölve mindkettő bejegyzései látszanak');
  const aktivak = await p.locator('#ligaSzuro .vlt-chip.on').allInnerTexts();
  console.log('   kiemelt liga-gombok:', JSON.stringify(aktivak));
  check(aktivak.length === 2 && !aktivak.some(t => /Mind/.test(t)),
    'mindkét liga gombja ki van emelve, a Mind nem');
  await chip('ligaSzuro', 'Mind');       // torles
  check((await cimek()).length === OSSZES.length, 'a Mind törli a kijelöléseket');
  const mindAktiv = await p.locator('#ligaSzuro .vlt-chip.on').allInnerTexts();
  check(mindAktiv.length === 1 && /Mind/.test(mindAktiv[0]),
    'kijelölés nélkül a Mind van kiemelve');

  console.log('\n--- a két szűrő együtt ---');
  await chip('ligaSzuro', 'PL');
  await chip('tipusSzuro', 'Javítás');
  const ures = await cimek();
  console.log('   PL + Javítás:', JSON.stringify(ures));
  const plJavitas = hany(b => b.tipus === 'bugfix' && b.ligak.includes('pl'));
  if (plJavitas === 0)
    check(ures.length === 0 && /nincs bejegyzés/.test(await p.locator('#lista').innerText()),
      'PL + Javítás: nincs ilyen, és ezt ki is írja');
  else
    check(ures.length === plJavitas, `PL + Javítás: ${plJavitas} bejegyzés`);

  await chip('ligaSzuro', 'PL');     // kikapcs
  await chip('ligaSzuro', 'NB1');
  check((await cimek()).length === hany(b => b.tipus === 'bugfix' && b.ligak.includes('nb1')),
    'NB1 + Javítás: az NB1-es javítások');

  console.log('\n--- elérési pontok ---');
  check(perr.length === 0, 'nincs JS-hiba a naplón: ' + JSON.stringify(perr));
  check((await p.locator('.lablec').count()) === 0, 'a naplón nincs lábléc (önmagára mutatna)');
  await p.close();

  for (const [ut, gyoker] of [['', ''], ['nb1/', '../'], ['pl/', '../']]) {
    const o = await br.newPage();
    await blockApis(o);
    await o.goto(BASE + ut, { waitUntil: 'domcontentloaded' });
    await o.waitForSelector('.lablec a', { timeout: 15000 });
    // A lablecben TOBB link is allhat (a magazin is onnan nyilik), ezert a
    // naplo linkjet celzottan keressuk - korabban itt egyetlen linket
    // feltetelezett a teszt, es a masodik megjelenesekor bukott.
    const hrefek = await o.$$eval('.lablec a', n => n.map(x => x.getAttribute('href')));
    check(hrefek.indexOf(gyoker + 'valtozasok/') >= 0,
       `/${ut || ''} láblécében a napló linkje (${JSON.stringify(hrefek)})`);
    // A kezdolapon TOBB kiemelt sor is allhat (az ujsag is onnan nyilik),
    // ezert a naplo sorat celzottan keressuk - nem a sorok szamat.
    if (!ut) check((await o.locator('a.ujdonsagsor[href="valtozasok/"]').count()) === 1,
      'a kezdőlapon külön sor is mutat rá');
    await o.close();
  }

  await finish(br);
})();
