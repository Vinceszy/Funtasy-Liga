const { BASE, check, launch, finish, rewriteJson } = require('./common');
// The "Zárási változások" panel on the PL home page (zarasok.json).
//
// What it pins down: the panel is shown only when there is data; the three
// views (Mind / Pontváltozás / Cserék) work separately and together; the
// rounds can be paged; an empty view gets a meaningful message; out/in stand
// in SEPARATE rows (we claim no pairing, because it cannot be known from
// the bench flag).
(async () => {
  const br = await launch();
  const p = await br.newPage({ viewport: { width: 900, height: 1200 } });
  const perr = []; p.on('pageerror', e => perr.push(e.message));

  const pl = require(require('path').join(__dirname, '..', 'draft_players.json'));
  const ids = Object.keys(pl.players).slice(0, 3).map(Number);
  const hist = require(require('path').join(__dirname, '..', 'draft_history.json'));
  const teams = Object.keys(Object.values(hist.rounds)[0]);
  const [teamA, teamB] = teams;

  // WE STATE THE PRECONDITION. The panel opens on the MOST RECENTLY CLOSED
  // round, and that is decided by the `veglegesek` list of
  // `draft_history.json` - not by zarasok.json. If we faked only the latter
  // (rounds 1 and 2), the page would open a later closed round taken from
  // the real data, for which the faked file has no row: the panel would
  // stand empty, and the test would blame reality. As the season went on,
  // exactly that happened. The two go together, so we set them up together.
  await rewriteJson(p, '**/draft_history.json*', j => {
    j.veglegesek = [1, 2];
    return j;
  });
  // two rounds: round 1 has a points AND a substitution change, round 2 NOTHING (empty dict)
  await p.route('**/zarasok.json*', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ updated: 'x', rounds: {
      1: { [teamA]: { pont: [{ e: ids[0], elott: 5, utan: 7 }] },
           [teamB]: { ki: [{ e: ids[1], pts: 0 }], be: [{ e: ids[2], pts: 6 }] } },
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

  const state = () => p.evaluate(() => ({
    selected: document.getElementById('selZaras').value,
    teams: [...document.querySelectorAll('#zarasBody .zcsapat h3')].map(x => x.textContent),
    rows: [...document.querySelectorAll('#zarasBody .zsor')].map(x =>
      x.textContent.trim().replace(/\s+/g, ' ')),
    empty: (document.querySelector('#zarasBody .loading') || {}).textContent || null,
    activeChip: (document.querySelector('#zarasSzuro .vlt-chip.on') || {}).textContent,
  }));

  console.log('--- Mind view, most recent round first ---');
  let a = await state();
  console.log('   round: ' + a.selected + ' | teams: ' + JSON.stringify(a.teams));
  check(a.selected === '2', 'the most recent round opens first');
  // The same text as on the NB1 panel - the two use one renderer.
  check(/Nem történt változás/.test(a.empty || ''), 'for a round without changes it says so');

  await p.click('[data-znav="-1"]');          // back to round 1
  a = await state();
  console.log('   rows of round 1: ' + JSON.stringify(a.rows));
  check(a.selected === '1' && a.teams.length === 2, 'paging to round 1, two teams affected');
  check(a.rows.some(x => /5 → 7/.test(x) && /\+2/.test(x)), 'the points change row: before → after (+diff)');
  check(a.rows.some(x => /kikerült/.test(x)) && a.rows.some(x => /beállt/.test(x)),
     'the substitution is two separate rows: kikerült / beállt — no false pairing');
  check(a.rows.some(x => /6 pont.*beállt/.test(x)),
     'the player who came in has his points shown: ' + JSON.stringify(a.rows.filter(x => /beállt/.test(x))));

  console.log('--- filtering ---');
  await p.click('[data-znezet="pont"]');
  a = await state();
  check(a.teams.length === 1 && a.rows.every(x => !/kikerült|beállt/.test(x)),
     'in the Pontváltozás view only the team with the points change remains');
  await p.click('[data-znezet="csere"]');
  a = await state();
  check(a.teams.length === 1 && a.rows.every(x => /kikerült|beállt/.test(x)),
     'in the Cserék view only the team with the substitution remains');
  await p.click('[data-znav="1"]');           // forward to round 2, in the substitution view
  a = await state();
  check(/nem történt automatikus csere/.test(a.empty || ''),
     'an empty substitution view gets its own message: ' + JSON.stringify(a.empty));
  await p.click('[data-znezet="mind"]');
  a = await state();
  check(a.activeChip === 'Mind', 'Mind can be switched back on');

  console.log('--- no panel without data ---');
  const p2 = await br.newPage();
  await p2.route('**/zarasok.json*', route => route.fulfill({ status: 404, body: '' }));
  await p2.route('**premierleague.com/**', route => route.fulfill({
    status: 200, contentType: 'application/json', body: '{}' }));
  await p2.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p2.waitForSelector('#table tr', { timeout: 20000 });
  await p2.waitForTimeout(400);
  check(await p2.$eval('#zarasPanel', el => el.style.display === 'none'),
     'without zarasok.json the panel stays hidden');

  check(perr.length === 0, 'no JS error: ' + JSON.stringify(perr));
  await finish(br);
})();
