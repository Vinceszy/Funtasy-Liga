const { BASE, check, failures, launch, finish, rewriteJson, blockApis } = require('./common');
// The change log page: two filters, and the league behaves as a TAG.
//
// The league tag matters because not everybody plays in every league: if an
// entry affects both, it must show up when filtering on EITHER. The real
// data has no such entry today, so the test produces one - following the
// repository's principles, on the fly, not from a stored fixture.

const title = t => t.replace(/\s+/g, ' ').trim();
// The expected values are computed from the REAL data, not written in as
// numbers: otherwise every new log entry would break the test.
const DATA = require(require('path').join(__dirname, '..', 'valtozasok.json')).bejegyzesek;
const EXTRA = { datum: '2999-01-01', tipus: 'funkcio', ligak: ['nb1', 'pl'],
                cim: 'MINDKETTO', leiras: 'Mindkét ligát érinti.' };
const ALL = [EXTRA].concat(DATA);
const howMany = f => ALL.filter(f).length;
const titlesOf = f => ALL.filter(f).map(b => title(b.cim));
const plOnly  = titlesOf(b => b.ligak.includes('pl')  && !b.ligak.includes('nb1'));
const nb1Only = titlesOf(b => b.ligak.includes('nb1') && !b.ligak.includes('pl'));

(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 1000, height: 900 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  // add an entry that affects both leagues
  await rewriteJson(p, '**/valtozasok.json*', j => {
    j.bejegyzesek.unshift(EXTRA);
    return j;
  });
  await p.goto(BASE + 'valtozasok/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('.vlt-tetel');

  const titles = async () => (await p.locator('.vlt-tetel h3').allInnerTexts()).map(title);
  const chip = async (row, text) => {
    await p.locator(`#${row} .vlt-chip`, { hasText: new RegExp('^' + text + '$') }).first().click();
    await p.waitForTimeout(60);
  };

  console.log('--- initial state ---');
  const all = await titles();
  console.log('   ' + all.length + ' entries:', JSON.stringify(all.map(x => x.slice(0, 28))));
  check(all.length === ALL.length,
    `without filtering every entry is shown (${ALL.length})`);
  check(all[0] === 'MINDKETTO', 'the most recent date comes first');
  // innerText also applies the CSS text-transform:uppercase, hence the /i
  const dates = await p.locator('.vlt-datum').allInnerTexts();
  console.log('   date headings:', JSON.stringify(dates.map(title)));
  check(dates.some(t => /augusztus 24/i.test(t)),
    'the date appears in Hungarian, as a group heading');
  check(dates.length === new Set(ALL.map(b => b.datum)).size,
    'there are as many date groups as distinct days');

  // .panel has no inner padding of its own, its children provide it - if a
  // strip forgets it, the text touches the border. This went wrong once.
  const paddings = await p.evaluate(() => {
    const left = s => parseFloat(getComputedStyle(document.querySelector(s)).paddingLeft);
    return { filters: left('.vlt-szurok'), date: left('.vlt-datum'), item: left('.vlt-tetel') };
  });
  console.log('   left inner paddings:', JSON.stringify(paddings));
  check(Object.values(paddings).every(x => x >= 12),
    'every strip has inner padding (the text does not touch the border)');

  console.log('\n--- by type ---');
  await chip('tipusSzuro', 'Javítás');
  const fixes = await titles();
  console.log('   fixes:', JSON.stringify(fixes.map(x => x.slice(0, 28))));
  check(fixes.length === howMany(b => b.tipus === 'bugfix') && !fixes.includes('MINDKETTO'),
    'the Javítás filter keeps only the fixes');
  await chip('tipusSzuro', 'Új funkció');
  check((await titles()).includes('MINDKETTO'), 'the Új funkció filter keeps the new features');
  await chip('tipusSzuro', 'Mind');
  check((await titles()).length === ALL.length, 'Mind gives back all of them');

  console.log('\n--- league: does it behave as a TAG ---');
  await chip('ligaSzuro', 'NB1');
  const nb1 = await titles();
  console.log('   NB1:', JSON.stringify(nb1.map(x => x.slice(0, 28))));
  check(nb1.includes('MINDKETTO'), 'the entry affecting both leagues shows up when filtering on NB1');
  // Matching on titles would silently pass if the text changed (it did
  // happen): so the expected titles are taken from the DATA, and we require
  // that there be something to check.
  check(plOnly.length > 0 && !plOnly.some(c => nb1.includes(c)),
    `PL-only entries do not show up when filtering on NB1 (${plOnly.length} of them)`);
  await chip('ligaSzuro', 'NB1');        // off
  await chip('ligaSzuro', 'PL');
  const pl = await titles();
  console.log('   PL:', JSON.stringify(pl.map(x => x.slice(0, 28))));
  check(pl.includes('MINDKETTO'), 'the same entry shows up when filtering on PL too');
  check(nb1Only.length > 0 && !nb1Only.some(c => pl.includes(c)),
    `NB1-only entries do not show up when filtering on PL (${nb1Only.length} of them)`);

  console.log('\n--- the leagues can be toggled SEPARATELY (for those who play in several) ---');
  await chip('ligaSzuro', 'NB1');        // next to PL
  const both = await titles();
  console.log('   NB1 + PL:', JSON.stringify(both.map(x => x.slice(0, 28))));
  check(both.length === howMany(b => b.ligak.some(x => x === 'nb1' || x === 'pl')),
    'with two leagues selected the entries of both are shown');
  const active = await p.locator('#ligaSzuro .vlt-chip.on').allInnerTexts();
  console.log('   highlighted league buttons:', JSON.stringify(active));
  check(active.length === 2 && !active.some(t => /Mind/.test(t)),
    'both league buttons are highlighted, Mind is not');
  await chip('ligaSzuro', 'Mind');       // clear
  check((await titles()).length === ALL.length, 'Mind clears the selection');
  const allActive = await p.locator('#ligaSzuro .vlt-chip.on').allInnerTexts();
  check(allActive.length === 1 && /Mind/.test(allActive[0]),
    'without a selection Mind is highlighted');

  console.log('\n--- the two filters together ---');
  await chip('ligaSzuro', 'PL');
  await chip('tipusSzuro', 'Javítás');
  const none = await titles();
  console.log('   PL + Javítás:', JSON.stringify(none));
  const plFixes = howMany(b => b.tipus === 'bugfix' && b.ligak.includes('pl'));
  if (plFixes === 0)
    check(none.length === 0 && /nincs bejegyzés/.test(await p.locator('#lista').innerText()),
      'PL + Javítás: there is none, and it says so');
  else
    check(none.length === plFixes, `PL + Javítás: ${plFixes} entries`);

  await chip('ligaSzuro', 'PL');     // off
  await chip('ligaSzuro', 'NB1');
  check((await titles()).length === howMany(b => b.tipus === 'bugfix' && b.ligak.includes('nb1')),
    'NB1 + Javítás: the NB1 fixes');

  console.log('\n--- entry points ---');
  check(perr.length === 0, 'no JS error on the log page: ' + JSON.stringify(perr));
  check((await p.locator('.lablec').count()) === 0, 'the log page has no footer (it would point to itself)');
  await p.close();

  for (const [path, root] of [['', ''], ['nb1/', '../'], ['pl/', '../']]) {
    const o = await br.newPage();
    await blockApis(o);
    await o.goto(BASE + path, { waitUntil: 'domcontentloaded' });
    await o.waitForSelector('.lablec a', { timeout: 15000 });
    // The footer can hold SEVERAL links (the magazine opens from there too),
    // so the log's link is looked for specifically - earlier the test
    // assumed a single link here, and failed when the second one appeared.
    const hrefs = await o.$$eval('.lablec a', n => n.map(x => x.getAttribute('href')));
    check(hrefs.indexOf(root + 'valtozasok/') >= 0,
       `the footer of /${path || ''} has the log's link (${JSON.stringify(hrefs)})`);
    // The home page can have SEVERAL highlighted rows (the paper opens from
    // there too), so the log's row is looked for specifically - not the
    // number of rows.
    if (!path) check((await o.locator('a.ujdonsagsor[href="valtozasok/"]').count()) === 1,
      'on the home page a separate row points to it too');
    await o.close();
  }

  await finish(br);
})();
