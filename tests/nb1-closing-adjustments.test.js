const { BASE, check, section, launch, finish, blockApis } = require('./common');
// Post-match points adjustment panel (NB1). What it pins down:
//   - the panel is shown ONLY when there is data (in production this is a
//     rare event, and a box that is always empty would suggest that
//     something is missing);
//   - the drop-down lists EVERY round played: where there was no change,
//     the news is that there was none;
//   - by default it stands on the LATEST round (even if there was no change
//     in it), and it can be paged;
//   - the direction of the change is shown (sign and colour), with the
//     player's OWN points;
//   - the display is THE SAME as the PL "Zárási változások" panel: grouped
//     by manager, with clickable names.
const DATA = { updated: 'x', rounds: {
  '2': { Bazsa: { pont: [
          { n: 'Egyik Elek', cp: 1, pos: 'MF', tm: 'MTK', elott: 5, utan: 6, d: '2026-08-20' }] } },
  // Unknown player: only the size of the change is known, not the player
  '3': { Csendi: { pont: [
          { n: '', cp: null, pos: '', tm: '', elott: null, utan: null, dl: -2.5, d: '2026-08-20', nk: 1 }] } },
  '4': { Bazsa: { pont: [
          { n: 'Teszt Elek', cp: 2, pos: 'DF', tm: 'FTC', elott: 9.25, utan: 6.75, d: '2026-08-24' }] },
         Csendi: { pont: [
          { n: 'Másik Elek', cp: 3, pos: 'FW', tm: 'DVSC', elott: 1, utan: 2, d: '2026-08-24' }] } } } };

(async () => {
  const br = await launch();

  // ---- no data: the panel stays hidden ----
  section('No panel without data');
  const empty = await br.newPage();
  await blockApis(empty);
  await empty.route('**/zarasok_nb1.json*', r => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ updated: 'x', rounds: {} }) }));
  await empty.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await empty.waitForSelector('#table tr', { timeout: 20000 });
  check(await empty.locator('#znPanel').isVisible() === false,
     'with empty data the panel does not appear');
  await empty.close();

  // ---- a missing file must not break anything either ----
  const missing = await br.newPage();
  const nerr = []; missing.on('pageerror', e => nerr.push(e.message));
  await blockApis(missing);
  await missing.route('**/zarasok_nb1.json*', r => r.fulfill({ status: 404, body: '' }));
  await missing.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await missing.waitForSelector('#table tr', { timeout: 20000 });
  check(await missing.locator('#znPanel').isVisible() === false && nerr.length === 0,
     'with a missing file there is no panel and no JS error either' + (nerr.length ? ': ' + nerr.join(' | ') : ''));
  await missing.close();

  // ---- with data ----
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  await p.route('**/zarasok_nb1.json*', r => r.fulfill({
    status: 200, contentType: 'application/json', body: JSON.stringify(DATA) }));
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#znPanel:not([style*="none"])', { timeout: 20000 });

  section('Content');
  // THE EXPECTED ROUND IS COMPUTED FROM THE DATA, not hard-coded. Earlier "5"
  // stood here - that was the last round played at the time -, and with the
  // closing of round 6 the test started to fail, although nothing was wrong
  // with the product. A constant that depends on the calendar always goes
  // stale sooner or later.
  const last = await p.evaluate(() => T.lastPlayedRound());
  // In the mocked data there is NO change in the last round played: the
  // pager still stands there, because it is news too that nothing happened.
  check((await p.$eval('#selZaras', e => e.value)) === String(last),
     'by default the pager stands on the last round (' + last + '.)');
  check(/Nem történt változás/.test(await p.$eval('#znBody', e => e.innerText)),
     'for a round without changes it says so');
  await p.selectOption('#selZaras', '4'); await p.waitForTimeout(200);
  const heads = await p.$$eval('#znBody .zcsapat h3', a => a.map(x => x.textContent.trim()));
  check(JSON.stringify(heads) === JSON.stringify(['Bazsa', 'Csendi']),
     'grouped by manager, in alphabetical order (' + heads.join(', ') + ')');
  const rows = await p.$$eval('#znBody .zsor', a => a.map(x => x.innerText.replace(/\n/g, ' ')));
  check(rows.length === 2, 'every change of the round is shown (' + rows.length + ')');
  check(/Teszt Elek/.test(rows[0]) && /FTC/.test(rows[0]),
     'the specific player\'s name and club are there (' + rows[0] + ')');
  check(/9,25\s*→\s*6,75/.test(rows[0]) && /-2,5/.test(rows[0]),
     'the old and the new value, and the signed difference too, are there (' + rows[0] + ')');
  check((await p.$$eval('#znBody .zdiff.neg', a => a.length)) === 1
     && (await p.$$eval('#znBody .zdiff.pos', a => a.length)) === 1,
     'a decrease and an increase get separate colours');
  check((await p.$$eval('#znBody .ppos', a => a.map(x => x.textContent.trim()))).length === 2,
     'every row starts with the position tag');

  section('Clickable names');
  // The player's name opens the profile, the manager's name the squad - the
  // same as on the PL panel (data-team there, data-member here).
  check((await p.$eval('#znBody .zsor .znev', e => e.dataset.prof)) === 'Teszt Elek'
     && (await p.$eval('#znBody .zsor .znev', e => e.dataset.pcp)) === '2',
     'the player\'s name points to the profile');
  check((await p.$eval('#znBody .zcsapat h3', e => e.dataset.member)) === 'Bazsa',
     'the manager\'s name points to the squad');
  await p.click('#znBody .zsor .znev');
  await p.waitForSelector('#ov.open', { timeout: 5000 });
  check(/Teszt Elek/.test(await p.$eval('#mTitle', e => e.textContent)),
     'clicking the player\'s name opens his profile');
  await p.click('#ovClose'); await p.waitForTimeout(200);

  section('Paging');
  const rounds = await p.$$eval('#selZaras option', a => a.map(o => +o.value));
  // The same: the EXPECTED list also comes from the page's own data - every
  // round that already has a result.
  const expected = await p.evaluate(() => ROUNDS.filter(r => (SCHEDULE[r] || []).some(m => m[2] != null)));
  check(JSON.stringify(rounds) === JSON.stringify(expected),
     'every round played is in the drop-down (' + rounds.join(', ')
     + (JSON.stringify(rounds) === JSON.stringify(expected) ? '' : ' — expected: ' + expected.join(', ')) + ')');
  await p.selectOption('#selZaras', '3'); await p.waitForTimeout(200);
  await p.click('[data-znav="-1"]');
  await p.waitForFunction(() => document.querySelector('#selZaras').value === '2',
                          null, { timeout: 5000 });
  check(/Egyik Elek/.test(await p.$eval('#znBody', e => e.innerText)),
     'the arrow steps to the earlier round');
  // round 1 is the first round: stepping back from there may lead nowhere
  await p.selectOption('#selZaras', '1'); await p.waitForTimeout(200);
  await p.click('[data-znav="-1"]');
  check((await p.$eval('#selZaras', e => e.value)) === '1',
     'at the first round stepping back leads nowhere (it does not fall off the list)');

  section('Unknown player');
  // Where only the SIZE of the change is known: there is no "before -> after",
  // the name is not clickable, and a written explanation stands below it.
  await p.selectOption('#selZaras', '3'); await p.waitForTimeout(200);
  const unknownRow = await p.$eval('#znBody .zsor', e => e.innerText.replace(/\n/g, ' '));
  check(/Ismeretlen játékos/.test(unknownRow) && /-2,5/.test(unknownRow) && !/→/.test(unknownRow),
     'only the size of the change stands there, no before → after (' + unknownRow + ')');
  check((await p.$$eval('#znBody .zsor .znev.kattint', a => a.length)) === 0,
     'the unknown player\'s name is not clickable');
  check(/nem gyűjtött játékos-szintű adatot/.test(await p.$eval('#znBody', e => e.innerText)),
     'a written explanation stands below it');

  check(perr.length === 0, 'no JS error' + (perr.length ? ': ' + perr.join(' | ') : ''));
  await finish(br);
})();
