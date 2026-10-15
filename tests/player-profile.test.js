const { BASE, check, section, launch, finish, blockApis, blockStoredBreakdowns, rewriteJson } = require('./common');
// Player profile. What it pins down (NB1 + PL):
//   - the rows of "Szezon játékosai" open the profile, and carry the
//     cp id (without it the breakdown could not be fetched);
//   - a round row shows the OPPONENT, the SCORE and the player's OWN points -
//     that is, the base points without captaincy and bench;
//   - the base points recomputed from a BENCH value do NOT drift by 0.01
//     (the API rounds to two decimals after halving: 0.75 -> 0.38; multiplying
//     back would give 0.76) - this is the detail that breaks most easily;
//   - SEVERAL managers can appear in one round (salary cap league);
//   - where nobody had the player, we say that nobody had him;
//   - expanding a row shows the game-player-stats breakdown;
//   - the back button returns to the "Szezon játékosai" tab.
//
// The test BUILDS the precondition itself (rewriteJson) instead of relying on
// the repository's current data: that way a change of round does not break it.
const CP = 424242;
const PLAYER = { name: 'Teszt Elek', team: 'PAKS', pos: 'CS', u21: false, hun: true,
                 price: 8, total: 30, id: CP, played: true, vege: true };

(async () => {
  const br = await launch();
  const p = await br.newPage();
  const perr = []; p.on('pageerror', e => perr.push(e.message));
  await blockApis(p);
  // This part measures the BACKFILL path: the profile appears at once with
  // dashes, and the points arrive one by one, in order (concurrency = 1,
  // because the proxy dropped requests fired at the same time). This path is
  // the case of a missing stored breakdown - our made-up player is not in the
  // 385-player roster anyway, but the round totals could also come from a
  // stored file, so we state it explicitly.
  await blockStoredBreakdowns(p);

  // ---- precondition: a made-up player with known roles ----
  //  round 1: nobody had him
  //  round 2: on Katyul's BENCH, week=0.38  -> base points 0.75 (not 0.76!)
  //  round 3: Katyul's CAPTAIN (week=19) and Bence's starter (week=9.5) -> 9.5
  await rewriteJson(p, '**/squad_history.json*', j => {
    const R = j.rounds;
    for (const r of Object.keys(R))
      for (const mgr of Object.keys(R[r]))
        R[r][mgr] = R[r][mgr].filter(x => x.id !== CP);
    R['2'].Katyul.push(Object.assign({}, PLAYER, { cap: false, sub: true,  week: 0.38 }));
    R['3'].Katyul.push(Object.assign({}, PLAYER, { cap: true,  sub: false, week: 19 }));
    R['3'].Bence .push(Object.assign({}, PLAYER, { cap: false, sub: false, week: 9.5 }));
    return j;
  });
  // PAKS's matches, so that the opponent and the score are deterministic.
  // The KICK-OFF is needed too: the per-round price is tied to when the
  // round's first match was played - without it there is no telling which
  // price record was in force at the time.
  await rewriteJson(p, '**/meccsek.json*', j => {
    j.rounds['1'] = [{ id: 1, h: 'PAKS', v: 'FTC', hp: 1, vp: 3, vege: true,
                       start: '2026-08-01T19:00:00+02:00' }];
    j.rounds['2'] = [{ id: 2, h: 'ZTE',  v: 'PAKS', hp: 0, vp: 2, vege: true,
                       start: '2026-08-08T19:00:00+02:00' }];
    j.rounds['3'] = [{ id: 3, h: 'PAKS', v: 'DVSC', hp: 2, vp: 2, vege: true,
                       start: '2026-08-15T19:00:00+02:00' }];
    return j;
  });
  // The PRIMARY price source is the player data sheet: it gives a price per
  // round, including the start of the season. A row carries the ROUND's id
  // (75 + 2 x round), not its own id - if the two were swapped, every price
  // would land in the wrong round, and the page would still look plausible.
  // The request goes through our own proxy, where the target URL is ENCODED
  // in the query string - a plain glob would therefore not match it. So a
  // function decides whether this is the data-sheet request.
  await p.route(u => /players(\/|%2F)424242/.test(u.href), route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ id: CP, rounds: [
      { id: 32499, round_id: 77, market_price: 7.5, is_played: true },
      { id: 33435, round_id: 79, market_price: 7.5, is_played: true },
      { id: 34365, round_id: 81, market_price: 8.4, is_played: true }] }) }));
  // Fallback: our own price log, if the data sheet does not arrive. It holds
  // only the CHANGES, so for round 2 the first record is still in force.
  await rewriteJson(p, '**/arak.json*', j => {
    j.arak = j.arak || {};
    j.arak[String(CP)] = [['2026-07-20', 8], ['2026-08-12', 8.4]];
    return j;
  });
  // the breakdown endpoint: set up after blockApis, so this one wins
  await p.route('**game-player-stats**', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ data: [
      { value: 1,  points: 6, competition_stat_config: { name: 'Gól' } },
      { value: 78, points: 0, competition_stat_config: { name: 'Játszott perc' } },
      { value: 1,  points: 3, competition_stat_config: { name: 'Győzelem' } }] }) }));

  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => typeof showProfile === 'function', null, { timeout: 20000 });
  // meccsek.json loads on a NON-blocking path, and the profile rows are drawn
  // once: whoever opens the profile too early does not yet have the opponent
  // and the score in the row, and the test fails on that - in measurements,
  // every second run. The rewriteJson above made the DATA deterministic, but
  // not the TIMING; so we wait for it to arrive.
  await p.waitForFunction(() => typeof GAMES !== 'undefined' && GAMES !== null,
                          null, { timeout: 20000 });
  await p.waitForFunction(() => typeof PRICES !== 'undefined' && PRICES !== null,
                          null, { timeout: 20000 });

  // ---- the entry point: "Szezon játékosai" ----
  section('Entry point');
  await p.evaluate(() => showSquad(['Katyul'], 'players'));
  await p.waitForSelector('[data-prof]', { timeout: 20000 });
  const row = await p.$(`[data-prof="Teszt Elek"]`);
  check(!!row, 'the made-up player\'s row is in the "Szezon játékosai" list');
  check(await p.$eval(`[data-prof="Teszt Elek"]`, e => e.dataset.pcp) === String(CP),
     'the row carries the cp id (without it the breakdown could not be fetched)');

  await row.click();
  await p.waitForSelector('.proflista', { timeout: 20000 });

  // ---- header ----
  section('Header');
  const head = await p.$eval('.proffej', e => e.innerText);
  check(/Teszt Elek/.test(head) && /PAKS/.test(head), 'the header shows the name and the club');
  check(await p.$$eval('.proffej .flag', a => a.length) === 1,
     'a Hungarian player is marked by a flag (not a blue tag)');

  // ---- the round rows ----
  section('Per-round rows');
  const rows = await p.$$eval('.profsor', a => a.map(x => ({
    r: x.querySelector('.ppos').textContent.trim(),
    nm: x.querySelector('.nm').textContent.trim(),
    score: (x.querySelector('.pallas') || {}).textContent || '',
    pts: x.querySelector('.pts').textContent.trim(),
    owners: (x.querySelector('.ptulajok') || {}).innerText || '',
    ratio: (x.querySelector('.parany') || {}).textContent || '',
    priceRow: (x.querySelector('.par') || {}).textContent || ''
  })));
  const f = n => rows.find(s => s.r === n + '.');

  check(f('1') && /–/.test(f('1').owners), 'round 1: a short mark shows that nobody had him');
  check(f('1') && /FTC/.test(f('1').nm) && /idegenben|otthon/.test(f('1').nm),
     'round 1: the opponent and the venue are shown');
  check(f('1') && f('1').score.replace(/\s/g, '') === '1–3',
     'round 1: the score in home–away order (1–3), not reversed');

  check(f('2') && f('2').pts === '0,75',
     'BENCH: the weekly value 0.38 gives 0.75 base points — not 0.76 '
     + '(rounding to the quarter undoes the rounding after halving)'
     + (f('2') ? ' — got: ' + f('2').pts : ''));
  check(f('2') && /Katyul/.test(f('2').owners) && /pad/.test(f('2').owners),
     'round 2: he was on Katyul\'s bench');

  // ---- per-round price ----
  section('Per-round price');
  // The data sheet gives 7.5 for rounds 1-2, the price log gives 8: the number
  // shown tells which source won. If we computed the round from the row's own
  // id instead of round_id, there would be no price here at all.
  check(f('1') && f('1').priceRow.replace(/\s/g, '') === '7,5',
     'round 1: the per-round price of the DATA SHEET is shown, not the price log\'s'
     + (f('1') ? ' — got: ' + JSON.stringify(f('1').priceRow) : ''));
  check(f('2') && f('2').priceRow.replace(/\s/g, '') === '7,5',
     'round 2: with an unchanged price no difference is shown');
  check(f('3') && /^8,4/.test(f('3').priceRow.replace(/\s/g, '')),
     'round 3: the raised price is shown'
     + (f('3') ? ' — got: ' + JSON.stringify(f('3').priceRow) : ''));
  check(f('3') && /\+0,9/.test(f('3').priceRow.replace(/\s/g, '')),
     'round 3: the change against the previous round is shown too (+0.9)');

  check(f('3') && f('3').pts === '9,5',
     'CAPTAIN: the weekly value 19 gives 9.5 base points (without the doubling)');
  check(f('3') && /Katyul/.test(f('3').owners) && /kapitány/.test(f('3').owners)
            && /Bence/.test(f('3').owners) && /kezdő/.test(f('3').owners),
     'round 3: BOTH managers appear, each with his own role');

  // ---- ratios across the league ----
  // The league's 8 squads are the denominator. In round 2 he was only on
  // Katyul's bench (1/8 = 13%, starter 0), in round 3 Katyul's captain AND
  // Bence's starter (2/8 = 25%) - the latter pins down that the CAPTAIN ALSO
  // COUNTS AS A STARTER, otherwise 13% would come out here.
  section('NB1: only the rounds played');
  // MLSZ has no fixtures endpoint, so for a future row we could show neither
  // an opponent nor a time - and we do not put out empty rows. (The PL
  // profile, by contrast, goes ahead too: the data is there.)
  check(!f('10') && !f('33'),
     'no future, empty round rows (' + rows.length + ' rows, the last is '
     + (rows.length ? rows[rows.length - 1].r : '?') + ')');

  section('Ratios across the league');
  check(f('2') && /keret\s*13%/.test(f('2').ratio) && /kezdő\s*0%/.test(f('2').ratio)
            && /kapitány\s*0%/.test(f('2').ratio),
     'round 2: 1 squad of the 8, on the bench — squad 13%, starter 0%, captain 0%'
     + (f('2') ? ' — got: ' + f('2').ratio : ''));
  check(f('3') && /keret\s*25%/.test(f('3').ratio) && /kezdő\s*25%/.test(f('3').ratio)
            && /kapitány\s*13%/.test(f('3').ratio),
     'round 3: the captain is a starter too — squad 25%, starter 25%, captain 13%'
     + (f('3') ? ' — got: ' + f('3').ratio : ''));
  check(f('1') && !f('1').ratio, 'round 1: where nobody had him, there is no ratio block');

  // ---- expanding breakdown ----
  section('Expanding breakdown');
  await p.click('.profsor[data-pr="3"]');
  await p.waitForSelector('.accpanel .acctable', { timeout: 20000 });
  const acc = await p.$eval('.accpanel', e => e.innerText);
  check(/Gól/.test(acc) && /Győzelem/.test(acc), 'the breakdown shows the events worth points');
  check(/Játszott perc/.test(acc), 'minutes played are shown despite the 0 points');
  check(/PAKS/.test(acc) && /DVSC/.test(acc), 'the club\'s match is above the breakdown');

  // ---- back ----
  section('Going back');
  await p.click('#ovBack');
  await p.waitForSelector('[data-prof]', { timeout: 20000 });
  check(await p.$('.proflista') === null, 'the back button returns to the "Szezon játékosai" list');

  // ---- draft league: the ratio is meaningless there ----
  // It does not depend on NB1 vs PL, but on the league TYPE: in a draft a
  // player can be with exactly one manager, so "squad %" would always be 1/N
  // or 0. We have the same data drawn with both kinds of league.
  section('Draft league: no ratio');
  const twoKinds = await p.evaluate(() => {
    const row = { r: 1, ellenfel: 'ARS', hazai: true, hp: 2, vp: 1, pont: 7,
                  keretszam: 8,
                  tulajok: [{ nev: 'A', kezdo: true, kapitany: true },
                            { nev: 'B', kezdo: false, kapitany: false }] };
    const draw = l => FunTasy.profileHTML({ liga: l, nev: 'X', sorok: [row] });
    return { nb1: draw('nb1'), pl: draw('pl') };
  });
  check(/class="parany"/.test(twoKinds.nb1), 'in a salary cap league the ratio block is there');
  check(!/class="parany"/.test(twoKinds.pl), 'in a DRAFT league there is no ratio block (always 1 or 0 squads)');
  check(/kapitány/.test(twoKinds.pl) && /pad/.test(twoKinds.pl),
     'the role name is shown in a draft league too (only the ratio is left out)');

  // ---- home page player list + search ----
  section('NB1: home page list and search');
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('.jlsor', { timeout: 20000 });
  const count = await p.$$eval('.jlsor', a => a.length);
  check(count > 0 && count <= 40, 'the list shows the best, not the whole field (' + count + ' rows)');
  // It must find WITHOUT ACCENTS too: the field is full of accented and South
  // Slavic names, and nobody will type a c with a caron into the search. We
  // look for a PLAYER name in the list that has an accent, and search for its
  // unaccented form.
  const target = await p.$$eval('.jlsor .nm', a => {
    for (const x of a) {
      const name = x.childNodes[0].textContent.trim();      // the club is a separate span
      const word = name.split(/\s+/).filter(w => w.normalize('NFD')
        .replace(/[̀-ͯ]/g, '') !== w)[0];
      if (word) return word;
    }
    return null;
  });
  if (target){
    const targetPlain = target.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    await p.fill('#jlDoboz .kereso', targetPlain);
    await p.waitForFunction(n => document.querySelectorAll('.jlsor').length < n,
                            count, { timeout: 5000 }).catch(() => {});
    const found = await p.$$eval('.jlsor .nm', a => a.map(x => x.textContent));
    check(targetPlain !== target.toLowerCase() && found.some(x => x.includes(target)),
       'it finds the name typed without accents too („' + targetPlain + '” → „' + target + '”)');
  } else {
    check(false, 'found no accented name in the list — the accent test did not run');
  }
  // the search must run over the WHOLE field, not only the rendered rows:
  // we search for someone who is not even at the end of the list
  await p.fill('#jlDoboz .kereso', 'zzzznincsilyen');
  await p.waitForSelector('#jlDoboz .jllista .loading', { timeout: 5000 });
  check(/Nincs találat/.test(await p.$eval('#jlDoboz .jllista', e => e.innerText)),
     'a non-existent name gets its own message, not an empty box');
  await p.fill('#jlDoboz .kereso', '');
  await p.waitForSelector('.jlsor', { timeout: 5000 });

  // The "+N" must NEVER be cut off: the names get shorter instead. (Earlier
  // the two parts were one, and the CSS swallowed exactly the count.)
  section('NB1: the „kinél van” column');
  const multi = await p.$$eval('.jltobb', a => a.map(x => x.textContent));
  check(!multi.length || multi.every(x => /^\+\d+$/.test(x)),
     'where several own him, the „+N” stands apart and is shown in full'
     + (multi.length ? ' — e.g. ' + multi[0] : ' (no such row right now)'));
  const clipped = await p.$$eval('.jltobb', a => a.some(x => x.scrollWidth > x.clientWidth + 1));
  check(!clipped, 'the „+N” is not cut off');

  // ---- filters, sorting, paging ----
  section('NB1: filtering, sorting, paging');
  const filters = await p.$$eval('.jlszuro,.jlszam', a => a.map(x => x.dataset.szuro));
  check(['poszt','klub','tulaj','kpc','ar','pts'].every(k => filters.includes(k)),
     'every column has a filter (' + filters.join(', ') + ')');

  // "Valakinél": the option value must NOT contain a control character - the
  // HTML parser replaces it, and the filter silently returns an empty list
  // (that is what happened)
  await p.selectOption('[data-szuro="tulaj"]', { label: 'Valakinél' });
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0,
                          null, { timeout: 5000 }).catch(() => {});
  const ownerless = await p.$$eval('.jlsor .jltulaj', a => a.filter(x => /nincs/.test(x.className)).length);
  const owned = await p.$$eval('.jlsor', a => a.length);
  check(owned > 0 && ownerless === 0,
     '„Valakinél”: only those who have an owner (' + owned + ' rows, ' + ownerless + ' without owner)');
  await p.selectOption('[data-szuro="tulaj"]', { label: 'Senkinél' });
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0,
                          null, { timeout: 5000 }).catch(() => {});
  check((await p.$$eval('.jlsor .jltulaj', a => a.every(x => /nincs/.test(x.className)))),
     '„Senkinél”: only those without an owner');
  await p.click('.jltorol');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 1, null, { timeout: 5000 });

  check((await p.$$eval('.jlsor .jlkpc', a => a.every(x => /^\d+%$/.test(x.textContent)))),
     'the Keret% column shows a percentage');

  const footer1 = await p.$eval('.jllab', e => e.textContent);
  check(/^1–\d+ \/ \d+/.test(footer1), 'the footer shows the current range (' + footer1 + ')');
  const pageButtons = await p.$$eval('.jllapozo > *', a => a.map(x => x.textContent));
  check(pageButtons[0] === '‹' && pageButtons[pageButtons.length - 1] === '›'
     && pageButtons.includes('1') && pageButtons.some(x => /^\d+$/.test(x) && +x > 2),
     'the pager has PAGE NUMBERS, not only arrows (' + pageButtons.join(' ') + ')');
  check(await p.$eval('.jllapozo > button', e => e.disabled),
     'on the first page the back arrow is disabled');
  // the LAST page is always reachable with one click - paging through ten
  // pages one by one is not usable
  const lastNumber = Math.max(...pageButtons.filter(x => /^\d+$/.test(x)).map(Number));
  await p.click('[data-ugras="' + (lastNumber - 1) + '"]');
  await p.waitForFunction(() => /\/ \d+ játékos$/.test(document.querySelector('.jllab').textContent),
                          null, { timeout: 5000 });
  check(await p.$eval('.jllapozo > button:last-child', e => e.disabled),
     'the last page is reachable with one click, and there the forward arrow is disabled');
  // from the last page the button of page 2 is no longer shown (only the
  // neighbours and the first/last) - first back to the first, then on
  await p.click('[data-ugras="0"]');
  await p.waitForFunction(() => /^1–/.test(document.querySelector('.jllab').textContent),
                          null, { timeout: 5000 });
  await p.click('[data-ugras="1"]');
  await p.waitForFunction(() => /^41–/.test(document.querySelector('.jllab').textContent),
                          null, { timeout: 5000 });
  check((await p.$eval('.jlsor .rank', e => e.textContent)) === '41.',
     'page 2 starts with row 41 (the row number continues, it does not reset)');

  // page size: "mind" removes the pager
  await p.selectOption('.jlmeret', '0');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 100,
                          null, { timeout: 8000 });
  check((await p.$$eval('.jllapozo > *', a => a.length)) === 0,
     'with the „mind” page size there is no pager (nothing to page)');
  await p.selectOption('.jlmeret', '40');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length === 40,
                          null, { timeout: 8000 });
  // after filtering/searching we must NOT stay on a page that does not exist
  await p.fill('#jlDoboz .kereso', 'a');
  await p.waitForFunction(() => /^1–/.test(document.querySelector('.jllab').textContent),
                          null, { timeout: 5000 });
  check(true, 'a search jumps back to the first page');
  await p.click('.jltorol');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 1, null, { timeout: 5000 });

  section('NB1: the profile opens from the list');
  await p.click('.jlsor');
  await p.waitForSelector('.proflista', { timeout: 20000 });
  check(true, 'clicking a list row opens the profile');
  // The price log starts later than the season, so the early rounds have no
  // price. Their rows still need the price cell (empty), otherwise the
  // match score column jumps sideways between the rounds with and without one.
  const scoreRight = await p.$$eval('.profsor .pallas', a => a.map(x =>
    Math.round(x.getBoundingClientRect().right)));
  check(scoreRight.length > 1 && new Set(scoreRight).size === 1,
     'the match score column is aligned in every round row: '
     + JSON.stringify([...new Set(scoreRight)]));
  await p.click('#ovClose');

  // ---- a never-owned player: the profile must not wait for the API ----
  // THE EXCLUDED BUG: for such a player one proxied request per round went
  // out, all AT ONCE - the proxy dropped them, the profile loaded for minutes,
  // the expanding breakdown failed. The rule since then: the profile appears
  // AT ONCE with dashes, the points are backfilled IN ORDER.
  section('NB1: profile of a never-owned player');
  let inFlight = 0, peak = 0;
  await p.route('**game-player-stats**', async route => {
    inFlight++; peak = Math.max(peak, inFlight);
    await new Promise(r => setTimeout(r, 400));       // slow proxy
    inFlight--;
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ data: [{ value: 1, points: 2,
        competition_stat_config: { name: 'Gól' } }] }) });
  });
  await p.selectOption('[data-szuro="tulaj"]', { label: 'Senkinél' });
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0, null, { timeout: 5000 });
  // WE STATE THE PRECONDITION instead of trusting the order of the list: the
  // "Senkinél" filter looks at the CURRENT owner, while this test is about
  // the NEVER-owned player - who has no stored points from any round, so all
  // of them have to be backfilled from the API. The two are not the same, and
  // the difference did show up: once the round-6 squad came in, the first
  // "Senkinél" player in the list had already been with someone earlier, so
  // his points were there at once, and the test measured ZERO requests (both
  // of its assertions failed).
  const neverOwned = await p.evaluate(async () => {
    const h = await (await fetch('../squad_history.json?t=' + Date.now())).json();
    const ever = new Set();
    for (const per of Object.values(h.rounds || {}))
      for (const squad of Object.values(per))
        for (const x of squad) ever.add(String(x.id));
    const row = [...document.querySelectorAll('.jlsor')]
      .find(s => !ever.has(s.dataset.jl));
    return row ? row.dataset.jl : null;
  });
  check(!!neverOwned, 'the list has a never-owned player (the test\'s precondition)');
  const t0 = Date.now();
  await p.click('.jlsor[data-jl="' + neverOwned + '"]');
  await p.waitForSelector('.proflista', { timeout: 20000 });
  check(Date.now() - t0 < 3000,
     'the profile appears WITHOUT waiting for the slow API (' + (Date.now() - t0) + ' ms)');
  // where there was a match, a dash; where not (postponed round), its own
  // label - but there may not be a number anywhere yet
  check((await p.$$eval('.profsor .pts', a => a.every(x => !/\d/.test(x.textContent)))),
     'no number stands in place of the points not yet fetched (a dash or „nincs meccs”)');
  await p.waitForFunction(() => [...document.querySelectorAll('.profsor .pts')]
    .every(x => x.textContent.trim() !== '—'), null, { timeout: 20000 });
  check(true, 'the points are backfilled in the background');
  check(peak === 1, 'the requests go IN ORDER, not at once (peak: ' + peak + ')');
  // unroute would also remove the mock set up at the START of the test - the
  // delayed response stays, that is fine for the later sections too
  await p.click('#ovClose');
  await p.click('.jltorol');
  await p.waitForFunction(() => document.querySelectorAll('.jlsor').length > 1, null, { timeout: 5000 });

  // ---- entry from the bottom of the points breakdown ----
  section('NB1: entry from the bottom of the expanding panel');
  await p.evaluate(() => showSquad(['Katyul']));
  await p.waitForSelector('.plr[data-acc]', { timeout: 20000 });
  await p.click('.plr[data-acc]');
  await p.waitForSelector('.accpanel .profnyito', { timeout: 20000 });
  check(/Teljes játékosprofil/.test(await p.$eval('.accpanel .profnyito', e => e.innerText)),
     'at the bottom of the breakdown there is the „Teljes játékosprofil” row');
  await p.click('.accpanel .profnyito');
  await p.waitForSelector('.proflista', { timeout: 20000 });
  const head2 = await p.$eval('.proffej', e => e.innerText);
  check(/[A-ZÁÉÍÓÖŐÚÜŰ]/.test(head2.split('\n')[0]),
     'the header of a profile opened from the panel is filled in too (the position is taken from the squad history)');
  check(await p.$('.accpanel .profnyito') === null,
     'INSIDE the profile there is no „Teljes játékosprofil” row any more');

  await p.close();

  // ================= PL (draft league) =================
  // We supply the element-summary response: FPL cannot be reached from the
  // container, and this way the test is deterministic too. The route
  // registered LATER wins, so first we cut off everything, then comes the
  // targeted mock.
  const q = await br.newPage();
  const qerr = []; q.on('pageerror', x => qerr.push(x.message));
  for (const m of ['**mlsz.hu/**', '**premierleague.com/**',
                   '**corsproxy.io/**', '**allorigins**']) await q.route(m, r => r.abort());
  await q.route('**element-summary**', r => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ history: [
      { event: 1, total_points: 17, detail: 'AVL (H) 4-0', minutes: 77 },
      // DOUBLE GAMEWEEK: the same round with two matches
      { event: 2, total_points: 3,  detail: 'FUL (A) 2-3', minutes: 90 },
      { event: 2, total_points: 6,  detail: 'BRE (H) 1-0', minutes: 90 }
    ], fixtures: [
      // remaining matches: with opponent id and home/away flag
      { event: 3, opponent: 1, is_home: true,  kickoff_time: '2026-09-01T13:00:00Z' },
      { event: 4, opponent: 6, is_home: false, kickoff_time: '2026-09-08T13:00:00Z' }
    ] }) }));

  // WE STATE THE PRECONDITION: round 3 is in the FUTURE here - the mock gives
  // it as such too (fixtures: event 3). The collector, however, also stores
  // the squads of the CURRENT round as soon as FPL moves on, and then round 3
  // already HAS an owner - the claim "a future round has no owner" failed
  // because of that, although nothing was wrong with the product. So we drop
  // round 3 and the ones after it from the stored history on the fly.
  await rewriteJson(q, '**/draft_history.json*', j => {
    for (const k of Object.keys(j.rounds || {})) if (+k >= 3) delete j.rounds[k];
    j.veglegesek = (j.veglegesek || []).filter(x => +x < 3);
    return j;
  });
  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForFunction(() => typeof showProfile === 'function'
    && Object.keys(HIST).length > 0, null, { timeout: 20000 });

  section('PL: entry point');
  const team = await q.evaluate(() => Object.keys(HIST[Object.keys(HIST)[0]])[0]);
  await q.evaluate(id => showTeam(+id, 'jatekosok'), team);
  await q.waitForSelector('#mBody [data-prof]', { timeout: 20000 });
  check(/^\d+$/.test(await q.$eval('#mBody [data-prof]', e => e.dataset.prof)),
     'the "Szezon játékosai" row carries the player\'s id');
  await q.click('#mBody [data-prof]');
  await q.waitForSelector('.proflista', { timeout: 20000 });

  const plRows = await q.$$eval('.profsor', a => a.map(x => ({
    r: x.querySelector('.ppos').textContent.trim(),
    nm: x.querySelector('.nm').textContent.trim(),
    score: (x.querySelector('.pallas') || {}).textContent || '',
    pts: x.querySelector('.pts').textContent.trim(),
    owners: (x.querySelector('.ptulajok') || {}).innerText || ''
  })));
  const g = n => plRows.find(x => x.r === n + '.');

  section('PL: the order of the result');
  // The score in `detail` is in HOME-AWAY order (measured: naplo/fpl-profile.txt,
  // 25 of 25 away matches). The two readings differ on an away match:
  // "FUL (A) 2-3" means the HOME side FUL scored 2, the player's team 3 -
  // read the other way round, 3-2 would stand here.
  check(g('2') && /FUL \(i\) 2–3/.test(g('2').nm),
     'away match: "FUL (A) 2-3" -> FUL (i) 2–3, not reversed'
     + (g('2') ? ' — got: ' + g('2').nm : ''));
  check(g('1') && /AVL/.test(g('1').nm) && /otthon/.test(g('1').nm)
            && g('1').score.replace(/\s/g, '') === '4–0',
     'with one match the score stands in its own column (4–0)');

  section('PL: double gameweek');
  check(g('2') && /FUL/.test(g('2').nm) && /BRE/.test(g('2').nm),
     'in a double gameweek BOTH matches are shown (the second does not vanish)');
  check(g('2') && g('2').pts === '9',
     'in a double gameweek the points add up (3 + 6 = 9)'
     + (g('2') ? ' — got: ' + g('2').pts : ''));
  check(g('2') && !g('2').score,
     'in a double gameweek the score column is empty (the scores stand next to the matches)');

  section('PL: lists the rounds ahead too');
  check(plRows.length >= 38,
     'the profile lists EVERY round, not only the ones played (' + plRows.length + ')');
  check(g('3') && /ARS/.test(g('3').nm) && /otthon/.test(g('3').nm),
     'a future round shows the opponent too (from the remaining fixtures)'
     + (g('3') ? ' — got: ' + g('3').nm : ''));
  check(g('3') && !g('3').score && g('3').pts === '—',
     'a future round has no score and no points, only the opponent');
  check(g('3') && !g('3').owners.trim(),
     'for a future round the owner is EMPTY — we do not know who will have him, so '
     + 'we do not write „szabadügynök” there either'
     + (g('3') ? ' — got: ' + JSON.stringify(g('3').owners) : ''));
  check(g('38') && !/nincs meccs/.test(g('38').pts + g('38').nm),
     'a distant round does not get „nincs meccs” (that would mean a postponement)');

  section('PL: owner');
  check(g('1') && /kezdő/.test(g('1').owners), 'round 1: the manager and the role are shown');
  // "szabadügynök" is a claim only when we KNOW that nobody had him - that
  // is, we have a squad history for that round. We measure it on the shared
  // layer, because there we can set up both cases.
  const ownerlessRow = await q.evaluate(() => {
    const base = { r: 1, ellenfel: 'ARS', hazai: true, hp: 2, vp: 1, tulajok: [] };
    const draw = x => FunTasy.profileHTML(
      { liga: 'pl', nev: 'X', senkinel: '–', sorok: [Object.assign({}, base, x)] });
    return { past: draw({ pont: 0 }), future: draw({ jovo: true }) };
  });
  check(/ptul nincs/.test(ownerlessRow.past),
     'for a played round where we know he was nobody\'s: a short mark stands there');
  check(!/ptul nincs/.test(ownerlessRow.future),
     'for a future round, though, nothing — that cannot be known in advance');
  check(await q.$$eval('.parany', a => a.length) === 0,
     'in a draft league there is no ratio block on the real page either');

  section('PL: home page list');
  // the filter drop-down must show monograms too, like the column
  await q.waitForSelector('.jlsor', { timeout: 20000 });
  const options = await q.$$eval('[data-szuro="tulaj"] option',
    a => a.slice(3).map(x => ({ value: x.value, label: x.textContent, title: x.title })));
  check(options.length > 0 && options.every(x => x.label.length <= 4 && x.title.length > x.label.length),
     'the „Kinél van” filter shows monograms, the full name is in the title'
     + (options.length ? ' — e.g. ' + JSON.stringify(options[0]) : ''));
  check(options.every(x => x.value === x.title),
     'the filtered value stays the full name (that identifies, not the monogram)');
  await q.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await q.waitForSelector('.jlsor', { timeout: 20000 });
  check((await q.$$eval('.jlsor', a => a.length)) > 0, 'the PL home page has the player list too');
  check((await q.$$eval('.jltobb', a => a.length)) === 0,
     'a draft league never has a „+N”: a player is in at most one squad');
  // The search matches NAME AND CLUB - so "ars" brings Arsenal's players AND
  // those with "ars" in their name. This is deliberate: the hits should be
  // generous, you should not need to know in advance what you are searching.
  await q.fill('#jlDoboz .kereso', 'ars');
  await q.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0, null, { timeout: 5000 });
  const arsRows = await q.$$eval('.jlsor', a => a.map(x => x.innerText.replace(/\n/g, ' ')));
  check(arsRows.length > 0 && arsRows.every(x => /ars/i.test(x)),
     'searching for a club, every hit contains the searched word (in the name or the club)');
  check(arsRows.some(x => /\bARS\b/.test(x)), 'the ARS club\'s players are among them');
  await q.click('.jlsor');
  await q.waitForSelector('.proflista', { timeout: 20000 });
  check(true, 'the profile opens from the PL list too');

  check(qerr.length === 0, 'no JS error on the PL page'
     + (qerr.length ? ': ' + qerr.join(' | ') : ''));

  // ---- PL: the FPL request fails, but the STORED points are shown anyway ----
  // Earlier every row of the profile was a dash in this case, and "Pont
  // összesen" was 0 - although the per-round points are in
  // draft_history.json. The opponent we still do not know (that only comes
  // from element-summary).
  section('PL: on an FPL outage the stored points are shown');
  const off = await br.newPage();
  const oerr = []; off.on('pageerror', e => oerr.push(e.message));
  await blockApis(off);
  await off.route('**draft.premierleague.com/**', r => r.abort());
  await off.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await off.waitForSelector('.jlsor', { timeout: 20000 });
  // we look for a player who has stored round points
  const targetPts = await off.evaluate(async () => {
    const h = await (await fetch('../draft_history.json')).json();
    for (const gw of Object.keys(h.rounds || {}))
      for (const lid of Object.keys(h.rounds[gw]))
        for (const x of h.rounds[gw][lid])
          if (x.pts) return { e: x.e, pts: x.pts, gw: +gw };
    return null;
  });
  if (!targetPts) {
    check(false, 'found no stored points in draft_history.json — the test did not run');
  } else {
    // First we filter by NAME, so that the player is surely on the first
    // page; the click goes from evaluate, so that nothing intercepts it.
    const name = await off.evaluate(async e => {
      const j = await (await fetch('../draft_players.json')).json();
      return (j.players[e] || {}).n || '';
    }, targetPts.e);
    await off.fill('#jlDoboz .kereso', name);
    await off.waitForFunction(() => document.querySelectorAll('.jlsor').length > 0,
                              null, { timeout: 5000 });
    const found = await off.evaluate(e => {
      const s = [...document.querySelectorAll('.jlsor')].find(x => +x.dataset.jl === e);
      if (s) { s.click(); return true; }
      return false;
    }, targetPts.e);
    check(found, 'the player searched for is in the list (id=' + targetPts.e + ', „' + name + '”)');
    await off.waitForSelector('.proflista', { timeout: 20000 });
    const shown = await off.$$eval('.profsor', (a, gw) => {
      const x = a.find(y => y.querySelector('.ppos').textContent.trim() === gw + '.');
      return x ? x.querySelector('.pts').textContent.trim() : null;
    }, targetPts.gw);
    check(shown === String(targetPts.pts),
       'on an FPL outage the row still shows the stored points (round ' + targetPts.gw + ': '
       + shown + ', stored: ' + targetPts.pts + ')');
    const total = await off.$eval('.ptenyek', e => e.innerText.replace(/\n/g, ' ')).catch(() => '');
    check(/Pont összesen/.test(total) && !/Pont összesen\s*0\b/.test(total),
       '„Pont összesen” is not 0 when there are stored points (' + total.slice(0, 60) + ')');
  }
  check(oerr.length === 0, 'no JS error on an FPL outage either'
     + (oerr.length ? ': ' + oerr.join(' | ') : ''));
  await off.close();

  check(perr.length === 0, 'no JS error' + (perr.length ? ': ' + perr.join(' | ') : ''));
  await finish(br);
})();
