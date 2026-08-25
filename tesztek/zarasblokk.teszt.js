const { BASE, jo, inditas, vege } = require('./kozos');
// A "Zarasi valtozasok" panel a PL fooldalon (zarasok.json).
//
// Amit rogzit: a panel csak adat mellett latszik; a harom nezet (Mind /
// Pontvaltozas / Cserek) kulon-kulon es egyutt is mukodik; a fordulok kozott
// lapozni lehet; ures nezethez ertelmes uzenet jar; a ki/be KULON sorokban
// all (parositast nem allitunk, mert a pad-jelzobol nem tudhato).
(async () => {
  const br = await inditas();
  const p = await br.newPage({ viewport: { width: 900, height: 1200 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  const pl = require(require('path').join(__dirname, '..', 'draft_players.json'));
  const azon = Object.keys(pl.players).slice(0, 3).map(Number);
  const hist = require(require('path').join(__dirname, '..', 'draft_history.json'));
  const csapatok = Object.keys(Object.values(hist.rounds)[0]);
  const [csA, csB] = csapatok;

  // ket fordulo: az 1-ben pont- ES csere-valtozas, a 2-ben SEMMI (ures dict)
  await p.route('**/zarasok.json*', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ updated: 'x', rounds: {
      1: { [csA]: { pont: [{ e: azon[0], elott: 5, utan: 7 }] },
           [csB]: { ki: [{ e: azon[1], pts: 0 }], be: [{ e: azon[2], pts: 6 }] } },
      2: {},
    } }),
  }));
  await p.route('**premierleague.com/**', route => route.fulfill({
    status: 200, contentType: 'application/json', body: '{}' }));
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => {
    const el = document.getElementById('zarasPanel');
    return el && el.style.display !== 'none';
  }, null, { timeout: 20000 });

  const allapot = () => p.evaluate(() => ({
    valaszto: document.getElementById('selZaras').value,
    csapatok: [...document.querySelectorAll('#zarasBody .zcsapat h3')].map(x => x.textContent),
    sorok: [...document.querySelectorAll('#zarasBody .zsor')].map(x =>
      x.textContent.trim().replace(/\s+/g, ' ')),
    ures: (document.querySelector('#zarasBody .loading') || {}).textContent || null,
    aktivChip: (document.querySelector('#zarasSzuro .vlt-chip.on') || {}).textContent,
  }));

  console.log('--- Mind nézet, legfrissebb forduló elöl ---');
  let a = await allapot();
  console.log('   forduló: ' + a.valaszto + ' | csapatok: ' + JSON.stringify(a.csapatok));
  jo(a.valaszto === '2', 'a legfrissebb forduló nyílik meg elsőnek');
  // Ugyanaz a szoveg, mint az NB1 panelen - a ketto egy renderert hasznal.
  jo(/Nem történt változás/.test(a.ures || ''), 'változás nélküli fordulónál ezt meg is mondja');

  await p.click('[data-znav="1"]');           // vissza az 1. fordulora
  a = await allapot();
  console.log('   1. forduló sorai: ' + JSON.stringify(a.sorok));
  jo(a.valaszto === '1' && a.csapatok.length === 2, 'lapozás az 1. fordulóra, két érintett csapat');
  jo(a.sorok.some(x => /5 → 7/.test(x) && /\+2/.test(x)), 'a pontváltozás sora: előtte → utána (+diff)');
  jo(a.sorok.some(x => /kikerült/.test(x)) && a.sorok.some(x => /beállt/.test(x)),
     'a csere két külön sor: kikerült / beállt — nincs hamis párosítás');
  jo(a.sorok.some(x => /6 pont.*beállt/.test(x)),
     'a beállt játékosnál ott a pontja: ' + JSON.stringify(a.sorok.filter(x => /beállt/.test(x))));

  console.log('--- szűrés ---');
  await p.click('[data-znezet="pont"]');
  a = await allapot();
  jo(a.csapatok.length === 1 && a.sorok.every(x => !/kikerült|beállt/.test(x)),
     'Pontváltozás nézetben csak a pontos csapat marad');
  await p.click('[data-znezet="csere"]');
  a = await allapot();
  jo(a.csapatok.length === 1 && a.sorok.every(x => /kikerült|beállt/.test(x)),
     'Cserék nézetben csak a cserés csapat marad');
  await p.click('[data-znav="-1"]');          // vissza a 2. fordulora, csere nezetben
  a = await allapot();
  jo(/nem történt automatikus csere/.test(a.ures || ''),
     'üres csere-nézethez saját üzenet jár: ' + JSON.stringify(a.ures));
  await p.click('[data-znezet="mind"]');
  a = await allapot();
  jo(a.aktivChip === 'Mind', 'a Mind visszakapcsolható');

  console.log('--- adat nélkül nincs panel ---');
  const p2 = await br.newPage();
  await p2.route('**/zarasok.json*', route => route.fulfill({ status: 404, body: '' }));
  await p2.route('**premierleague.com/**', route => route.fulfill({
    status: 200, contentType: 'application/json', body: '{}' }));
  await p2.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p2.waitForSelector('#table tr', { timeout: 20000 });
  await p2.waitForTimeout(400);
  jo(await p2.$eval('#zarasPanel', el => el.style.display === 'none'),
     'zarasok.json nélkül a panel rejtve marad');

  jo(perr.length === 0, 'nincs JS-hiba: ' + JSON.stringify(perr));
  await vege(br);
})();
