const { BASE, jo, hibak, inditas, vege, jsonAtir, apiKi } = require('./kozos');
// A valtozasnaplo: ket szuro, es a liga CIMKEKENT viselkedik.
//
// A ligacimke azert fontos, mert nem mindenki jatszik minden ligaban: ha egy
// bejegyzes mindkettot erinti, BARMELYIKRE szurve elo kell jonnie. A valos
// adatban ma nincs ilyen bejegyzes, ezert a teszt allitja elo - a repo
// elvei szerint menet kozben, nem tarolt fixturabol.

const cim = t => t.replace(/\s+/g, ' ').trim();

(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 1000, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await apiKi(p);
  // egy mindket ligat erinto bejegyzes hozzaadasa
  await jsonAtir(p, '**/valtozasok.json*', j => {
    j.bejegyzesek.unshift({
      datum: '2026-08-24', tipus: 'funkcio', ligak: ['nb1', 'pl'],
      cim: 'MINDKETTO', leiras: 'Mindkét ligát érinti.',
    });
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
  jo(mind.length === 4, 'szűrés nélkül minden bejegyzés látszik');
  jo(mind[0] === 'MINDKETTO', 'a legfrissebb dátum van elöl');
  // az innerText a CSS text-transform:uppercase-t is visszaadja, ezert /i
  const datumok = await p.locator('.vlt-datum').allInnerTexts();
  console.log('   dátumfejlécek:', JSON.stringify(datumok.map(cim)));
  jo(datumok.some(t => /augusztus 24/i.test(t)),
    'a dátum magyarul, csoportfejlécként jelenik meg');
  jo(datumok.length === 2, 'a két nap külön csoportban van');

  // A .panel-nek nincs sajat belso margoja, a gyerekei adjak - ha egy sav
  // kifelejti, a szoveg a keretnek er. Ezt egyszer mar elrontottam.
  const margok = await p.evaluate(() => {
    const bal = s => parseFloat(getComputedStyle(document.querySelector(s)).paddingLeft);
    return { szuro: bal('.vlt-szurok'), datum: bal('.vlt-datum'), tetel: bal('.vlt-tetel') };
  });
  console.log('   bal belső margók:', JSON.stringify(margok));
  jo(Object.values(margok).every(x => x >= 12),
    'minden sávnak van belső margója (a szöveg nem ér a kerethez)');

  console.log('\n--- típus szerint ---');
  await chip('tipusSzuro', 'Javítás');
  const javitasok = await cimek();
  console.log('   javítások:', JSON.stringify(javitasok.map(x => x.slice(0, 28))));
  jo(javitasok.length === 2 && !javitasok.includes('MINDKETTO'),
    'a Javítás szűrő csak a javításokat hagyja meg');
  await chip('tipusSzuro', 'Új funkció');
  jo((await cimek()).includes('MINDKETTO'), 'az Új funkció szűrő az új funkciókat hagyja meg');
  await chip('tipusSzuro', 'Mind');
  jo((await cimek()).length === 4, 'a Mind visszaadja az összeset');

  console.log('\n--- liga: CÍMKEKÉNT viselkedik-e ---');
  await chip('ligaSzuro', 'NB1');
  const nb1 = await cimek();
  console.log('   NB1:', JSON.stringify(nb1.map(x => x.slice(0, 28))));
  jo(nb1.includes('MINDKETTO'), 'a mindkét ligát érintő bejegyzés NB1-re szűrve is előjön');
  jo(!nb1.some(x => /bónuszpontokról/i.test(x)), 'a csak PL-es bejegyzés NB1-re szűrve nem jön elő');
  await chip('ligaSzuro', 'NB1');        // kikapcs
  await chip('ligaSzuro', 'PL');
  const pl = await cimek();
  console.log('   PL:', JSON.stringify(pl.map(x => x.slice(0, 28))));
  jo(pl.includes('MINDKETTO'), 'ugyanaz a bejegyzés PL-re szűrve is előjön');
  jo(!pl.some(x => /elmaradt meccsek/i.test(x)), 'a csak NB1-es bejegyzés PL-re szűrve nem jön elő');

  console.log('\n--- a ligák KÜLÖN kapcsolhatók (aki több ligában játszik) ---');
  await chip('ligaSzuro', 'NB1');        // a PL mellé
  const ketto = await cimek();
  console.log('   NB1 + PL:', JSON.stringify(ketto.map(x => x.slice(0, 28))));
  jo(ketto.length === 4, 'két ligát kijelölve mindkettő bejegyzései látszanak');
  const aktivak = await p.locator('#ligaSzuro .vlt-chip.on').allInnerTexts();
  console.log('   kiemelt liga-gombok:', JSON.stringify(aktivak));
  jo(aktivak.length === 2 && !aktivak.some(t => /Mind/.test(t)),
    'mindkét liga gombja ki van emelve, a Mind nem');
  await chip('ligaSzuro', 'Mind');       // torles
  jo((await p.locator('#ligaSzuro .vlt-chip.on')).count && (await cimek()).length === 4,
    'a Mind törli a kijelöléseket');
  const mindAktiv = await p.locator('#ligaSzuro .vlt-chip.on').allInnerTexts();
  jo(mindAktiv.length === 1 && /Mind/.test(mindAktiv[0]),
    'kijelölés nélkül a Mind van kiemelve');

  console.log('\n--- a két szűrő együtt ---');
  await chip('ligaSzuro', 'PL');
  await chip('tipusSzuro', 'Javítás');
  const ures = await cimek();
  console.log('   PL + Javítás:', JSON.stringify(ures));
  jo(ures.length === 0 && /nincs bejegyzés/.test(await p.locator('#lista').innerText()),
    'PL + Javítás: nincs ilyen, és ezt ki is írja');

  await chip('ligaSzuro', 'PL');     // kikapcs
  await chip('ligaSzuro', 'NB1');
  jo((await cimek()).length === 2, 'NB1 + Javítás: a két NB1-es javítás');

  console.log('\n--- elérési pontok ---');
  jo(perr.length === 0, 'nincs JS-hiba a naplón: ' + JSON.stringify(perr));
  jo((await p.locator('.lablec').count()) === 0, 'a naplón nincs lábléc (önmagára mutatna)');
  await p.close();

  for (const [ut, gyoker] of [['', ''], ['nb1/', '../'], ['pl/', '../']]) {
    const o = await br.newPage();
    await apiKi(o);
    await o.goto(BASE + ut, { waitUntil: 'domcontentloaded' });
    await o.waitForSelector('.lablec a', { timeout: 15000 });
    const href = await o.locator('.lablec a').getAttribute('href');
    jo(href === gyoker + 'valtozasok/', `/${ut || ''} láblécében a napló linkje (${href})`);
    if (!ut) jo((await o.locator('a.ujdonsagsor').count()) === 1,
      'a kezdőlapon külön sor is mutat rá');
    await o.close();
  }

  await vege(br);
})();
