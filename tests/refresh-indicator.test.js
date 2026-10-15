const { BASE, check, section, failures, launch, finish, blockApis, rewriteJson } = require('./common');
// The "frissítés…" indicator: shown on a slow fetch, does not flash on a fast one.

// Does the indicator appear within the given time? (Looking at the final
// state would not be enough: the indicator disappears at the end of the fetch.)
async function waitForIndicator(p, ms){
  try {
    const el = await p.waitForSelector('.frissjel', { timeout: ms, state: 'attached' });
    await p.waitForTimeout(350);                   // let it tick a little
    return (await el.textContent()) || '';
  } catch (e) { return null; }
}

async function plMatch(br, delay){
  const p = await br.newPage();
  const perr = []; p.on('pageerror', x => perr.push(x.message));
  // Our own proxy (workers.dev) cannot be reached from the test environment,
  // and its real network attempt takes ~300 ms - with that delay the LIVEGW
  // response would arrive ONLY AFTER THE CLICK, and the non-live branch would
  // run, without the indicator. (In production our own path is the fastest,
  // there is no such delay there.)
  await p.route('**workers.dev/**', r => r.abort());
  const hist = require(require('path').join(__dirname,'..','draft_history.json'));
  // WE STATE THE PRECONDITION: the indicator only starts on a match of the
  // LIVE round (pl/index.html's showMatch fetches live for `r === LIVEGW`).
  // Earlier the test made THE FIRST of the stored rounds live, and clicked
  // the FIRST match of the list - while there was a single round, the two
  // were the same. With the closing of round 2 they diverged: the page listed
  // round 2, the mock made round 1 live, so the non-live branch ran, without
  // the indicator. From now on the MOST RECENT stored round is the live one,
  // and the click goes to that round too.
  const GW = Object.keys(hist.rounds).map(Number).sort((a, b) => b - a)[0] + '';
  const elements = [...new Set(Object.values(hist.rounds[GW]).flat().map(x => x.e))];
  let firstDone = false;
  await p.route('**premierleague.com/api/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    // the daily points close (classic FPL) - the PL page fetches this too
    if (/event-status/.test(u)) return json({ status: [] });
    if (/\/api\/game/.test(u)) return json({ current_event: +GW, current_event_finished: false });
    if (/\/live/.test(u)){
      // the fetch on load is not slowed down, only the one started from the modal
      if (delay && firstDone) await new Promise(r => setTimeout(r, delay));
      firstDone = true;
      const el = {};
      elements.forEach(id => { el[id] = { stats: { total_points: 4, minutes: 90 }, explain: [] }; });
      return json({ elements: el });
    }
    if (/\/fixtures/.test(u)) return json([]);
    return route.fulfill({ status: 404, body: '' });
  });
  await p.goto(BASE + 'pl/', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => document.querySelector('.match .score') &&
    /\d/.test(document.querySelector('.match .score').textContent), null, { timeout: 40000 });
  await p.locator(`.match[data-r="${GW}"]`).first().click();
  // On the SLOW branch we wait generously: the indicator appears 500 ms after
  // the fetch STARTS, but before that the page still loads the round's squad
  // from the local server - under the parallel load of the full suite that
  // alone could exceed 2.5 s, and the test measured "no indicator".
  // (The FAST branch stays short: there we claim the ABSENCE of the indicator.)
  const text = await waitForIndicator(p, delay ? 8000 : 1500);
  await p.waitForTimeout((delay || 0) + 800);
  const remaining = await p.locator('.frissjel').count();
  await p.close();
  return { text, remaining, perr };
}

(async () => {
  const br = await launch();

  console.log('--- PL: slow fetch (3 s) ---');
  const slow = await plMatch(br, 3000);
  console.log('   indicator text:', JSON.stringify(slow.text));
  check(slow.text !== null, 'on a slow fetch the indicator appears');
  check(/^frissítés… \d+,\d mp$/.test(slow.text || ''), 'the indicator shows the elapsed time');
  check(slow.remaining === 0, 'it disappears at the end of the fetch');
  check(slow.perr.length === 0, 'no JS error: ' + JSON.stringify(slow.perr.slice(0, 2)));

  console.log('\n--- PL: fast fetch ---');
  const fast = await plMatch(br, 0);
  console.log('   indicator text:', JSON.stringify(fast.text));
  check(fast.text === null, 'on a fast fetch it does not flash (no noise)');

  // ---------------- NB1 ----------------
  console.log('\n--- NB1: slow live squad fetch (3 s) ---');
  const p = await br.newPage();
  const perr = []; p.on('pageerror', x => perr.push(x.message));
  await p.route('**workers.dev/**', r => r.abort());   // see above: plMatch
  // We STATE the precondition instead of hoping for it from the refresh on
  // load: round 5 being live used to depend on whether the mocked ranking
  // responses arrived BEFORE the click - if not, the live squad fetch did
  // not even start, and the test failed without the indicator, with a
  // misleading error (a flake, about every third run).
  // live-text-and-cache.test.js pins it down the same way.
  await rewriteJson(p, '**/results.json*', j => Object.assign(j, { provisional: [5] }));
  const start = new Date(Date.now() - 1800000).toISOString();
  await p.route('**fantasy-api.mlsz.hu/**', async route => {
    const u = decodeURIComponent(route.request().url());
    const json = b => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(b) });
    if (/game-player-stats/.test(u)) return json({ data: [] });
    if (/user-team-players-history/.test(u)){
      await new Promise(r => setTimeout(r, 3000));
      return json({ data: [{ id: 1, is_captain: false, type: 'starter', position: { monogram: 'CS' },
        summary_statistics: { weekly_points: 0, competition_points: 0 },
        competition_player: { id: 1249, first_name: 'Teszt', last_name: 'Jatekos', is_u21: false,
          team: { short_name: 'MTK' }, countries: [{ code: 'HUN' }],
          current_round: { is_played: true, market_price: 5, first_played_at: start,
            games: [{ start_at: start, status: 'scheduled' }] } } }] });
    }
    const m = /filter\[search\]=([^&]+)/.exec(u);
    return json({ data: [{ user_team: { user: { id: 1, username: m ? m[1] : '' },
      round_statistics: [{ round_number: 5, points: 30 }] } }] });
  });
  await p.goto(BASE + 'nb1/', { waitUntil: 'domcontentloaded' });
  await p.waitForSelector('#table tr', { timeout: 30000 });
  // WE STATE THE PRECONDITION, as live-text-and-cache.test.js does too:
  // liveSquad works from USER_IDS ("if(!uid) return null"), which the refresh on load fills
  // from the ranking responses. If the call comes before that, the live squad
  // fetch DOES NOT EVEN START - there is nothing to signal, and the test
  // measures "no indicator" while nothing is wrong with the indicator. This
  // was the remaining flake: run alone 6/6 green, but under the load of the
  // full suite it failed. (With typeof: USER_IDS is a const, not on window.)
  await p.waitForFunction(() => typeof USER_IDS !== 'undefined'
    && USER_IDS['Bazsa'] && USER_IDS['Vince'], null, { timeout: 20000 });
  // NOT awaited: showLiveMatch is async, and if we waited for all of it to
  // run, it would already have taken the indicator down
  await p.evaluate(() => { showLiveMatch('Bazsa', 'Vince', 5); });
  const nb1Text = await waitForIndicator(p, 8000);   // see above: under load less was not enough
  console.log('   indicator text:', JSON.stringify(nb1Text));
  check(nb1Text !== null, 'NB1: it appears on a slow live squad fetch too');
  await p.waitForTimeout(4000);
  check(await p.locator('.frissjel').count() === 0, 'NB1: it disappears at the end');
  check(perr.length === 0, 'no JS error: ' + JSON.stringify(perr.slice(0, 2)));
  await p.close();

  await br.close();
  process.exit(failures.length ? 1 : 0);
})();
